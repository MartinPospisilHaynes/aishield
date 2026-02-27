"""
AIshield.cz — Subscription Manager
Správa monitoring předplatných (Stripe + FIO trvalý příkaz).
Min. doba: 3 měsíce. Výpověď: 1 měsíc.

Plans:
  monitoring      — 299 Kč/měs, 1× deep scan/měsíc
  monitoring_plus — 599 Kč/měs, 2× deep scan/měsíc + implementace změn
"""

import hashlib
import logging
import uuid
from datetime import datetime, timezone, timedelta, date

from backend.config import get_settings
from backend.database import get_supabase

logger = logging.getLogger("subscription_manager")

MONITORING_PLANS = {
    "monitoring": {
        "name": "Monitoring",
        "description": "1× měsíčně 24h hloubkový sken webu + compliance report",
        "scans_per_month": 1,
        "price_field": "price_monitoring",
    },
    "monitoring_plus": {
        "name": "Monitoring Plus",
        "description": "2× měsíčně 24h hloubkový sken + aktualizace dokumentů + implementace změn",
        "scans_per_month": 2,
        "price_field": "price_monitoring_plus",
    },
}


def generate_monitoring_vs(order_number: str) -> str:
    """Generuje variabilní symbol pro monitoring (prefix MON, 10 číslic)."""
    h = hashlib.sha256(order_number.encode()).hexdigest()[:8]
    numeric = int(h, 16) % 10_000_000_000
    return f"{numeric:010d}"


def get_scan_days_for_plan(company_id: str, plan: str) -> list[int]:
    """
    Vrátí dny v měsíci kdy se má spustit deep scan.
    Monitoring: 1 den (hash-based), Monitoring Plus: 2 dny.
    """
    h = int(hashlib.md5(company_id.encode()).hexdigest()[:8], 16)
    if plan == "monitoring_plus":
        day1 = (h % 14) + 1       # den 1-14
        day2 = (h % 14) + 15      # den 15-28
        return [day1, day2]
    else:
        return [(h % 28) + 1]


async def create_subscription(
    email: str,
    plan: str,
    gateway: str,  # "stripe" | "bank_transfer"
    company_id: str | None = None,
    stripe_subscription_id: str | None = None,
    stripe_customer_id: str | None = None,
) -> dict:
    """
    Vytvoří nový subscription záznam.
    Pro Stripe: status='active' (platba proběhla přes Checkout).
    Pro FIO: status='pending_first_payment' (čekáme na trvalý příkaz).
    """
    settings = get_settings()
    supabase = get_supabase()

    plan_info = MONITORING_PLANS.get(plan)
    if not plan_info:
        raise ValueError(f"Neznámý monitoring plán: {plan}")

    price = getattr(settings, plan_info["price_field"])
    order_number = f"AS-MON-{plan.upper().replace('_', '')}-{uuid.uuid4().hex[:8].upper()}"
    vs = generate_monitoring_vs(order_number)
    now = datetime.now(timezone.utc)
    min_end = (now + timedelta(days=90)).date().isoformat()  # 3 měsíce minimum

    if gateway == "stripe":
        status = "active"
        activated_at = now.isoformat()
        next_charge = (now + timedelta(days=30)).date().isoformat()
    else:
        status = "pending_first_payment"
        activated_at = None
        next_charge = None

    # Compute first scan date
    scan_days = get_scan_days_for_plan(company_id or email, plan)
    today = now.date()
    next_scan = None
    for d in sorted(scan_days):
        try:
            candidate = today.replace(day=d)
        except ValueError:
            candidate = today.replace(day=28)
        if candidate > today:
            next_scan = candidate.isoformat()
            break
    if not next_scan:
        # Next month
        next_month = (today.replace(day=1) + timedelta(days=32)).replace(day=min(scan_days[0], 28))
        next_scan = next_month.isoformat()

    sub_data = {
        "email": email,
        "plan": plan,
        "amount": price,
        "status": status,
        "order_number": order_number,
        "company_id": company_id,
        "payment_gateway": gateway,
        "variable_symbol": vs,
        "stripe_subscription_id": stripe_subscription_id,
        "stripe_customer_id": stripe_customer_id,
        "next_scan_at": next_scan,
        "scans_this_period": 0,
        "next_charge_at": next_charge,
        "min_end_date": min_end,
        "activated_at": activated_at,
        "cycle": "monthly",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    result = supabase.table("subscriptions").insert(sub_data).execute()
    sub_id = result.data[0]["id"] if result.data else None

    logger.info(
        f"[Subscription] Created: {sub_id} plan={plan} gateway={gateway} "
        f"email={email} VS={vs} status={status}"
    )

    return {
        "subscription_id": sub_id,
        "order_number": order_number,
        "variable_symbol": vs,
        "plan": plan,
        "amount": price,
        "status": status,
        "gateway": gateway,
        "min_end_date": min_end,
        "next_scan_at": next_scan,
    }


async def activate_fio_subscription(subscription_id: str, paid_amount: int) -> bool:
    """
    Aktivuje FIO subscription po první platbě.
    Voláno z bank_checker.py.
    """
    supabase = get_supabase()
    now = datetime.now(timezone.utc)

    supabase.table("subscriptions").update({
        "status": "active",
        "activated_at": now.isoformat(),
        "last_charged_at": now.isoformat(),
        "next_charge_at": (now + timedelta(days=30)).date().isoformat(),
        "total_charged": paid_amount,
        "updated_at": now.isoformat(),
    }).eq("id", subscription_id).execute()

    logger.info(f"[Subscription] FIO activated: {subscription_id}")
    return True


async def extend_fio_subscription(subscription_id: str, paid_amount: int) -> bool:
    """
    Prodlouží FIO subscription po opakované platbě (trvalý příkaz).
    """
    supabase = get_supabase()
    now = datetime.now(timezone.utc)

    sub = supabase.table("subscriptions").select("*").eq(
        "id", subscription_id
    ).limit(1).execute()
    if not sub.data:
        return False

    s = sub.data[0]
    total = (s.get("total_charged") or 0) + paid_amount

    supabase.table("subscriptions").update({
        "last_charged_at": now.isoformat(),
        "next_charge_at": (now + timedelta(days=30)).date().isoformat(),
        "total_charged": total,
        "scans_this_period": 0,  # Reset pro nový měsíc
        "grace_period_until": None,
        "reminder_sent_at": None,
        "updated_at": now.isoformat(),
    }).eq("id", subscription_id).execute()

    logger.info(f"[Subscription] FIO extended: {subscription_id} total={total}")
    return True


async def cancel_subscription(subscription_id: str, reason: str = "") -> dict:
    """
    Zruší subscription. Aktuální období zůstává platné.
    Musí se dodržet min. 3 měsíce.
    """
    supabase = get_supabase()
    now = datetime.now(timezone.utc)

    sub = supabase.table("subscriptions").select("*").eq(
        "id", subscription_id
    ).limit(1).execute()

    if not sub.data:
        return {"error": "Subscription nenalezena"}

    s = sub.data[0]
    if s["status"] in ("cancelled", "expired"):
        return {"error": f"Subscription je již {s['status']}"}

    # Check min 3-month period
    min_end = s.get("min_end_date")
    today = now.date()
    if min_end and today < date.fromisoformat(min_end):
        effective_end = min_end
    else:
        # 1 month notice
        effective_end = (today + timedelta(days=30)).isoformat()

    supabase.table("subscriptions").update({
        "status": "cancelled",
        "cancelled_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }).eq("id", subscription_id).execute()

    logger.info(f"[Subscription] Cancelled: {subscription_id}, effective_end={effective_end}")

    return {
        "status": "cancelled",
        "subscription_id": subscription_id,
        "effective_end": effective_end,
    }


async def get_active_monitoring_subscriptions() -> list[dict]:
    """Vrátí všechny aktivní monitoring subscription."""
    supabase = get_supabase()
    result = supabase.table("subscriptions").select("*").eq(
        "status", "active"
    ).in_("plan", ["monitoring", "monitoring_plus"]).execute()
    return result.data or []


async def get_enterprise_monitoring_clients() -> list[dict]:
    """
    Vrátí Enterprise klienty, kteří mají monitoring v ceně (do 2 let od zaplacení).
    """
    supabase = get_supabase()
    two_years_ago = (datetime.now(timezone.utc) - timedelta(days=730)).isoformat()

    orders = supabase.table("orders").select(
        "id, email, company_id, plan, paid_at"
    ).eq("plan", "enterprise").eq("status", "PAID").gte(
        "paid_at", two_years_ago
    ).execute()

    return orders.data or []


async def check_enterprise_expiry():
    """
    Kontroluje Enterprise klienty, jejichž 2 roky monitoringu vypršely.
    Deaktivuje je a pošle nabídkový email.
    """
    supabase = get_supabase()
    now = datetime.now(timezone.utc)
    two_years_ago = (now - timedelta(days=730)).isoformat()

    # Enterprise objednávky starší 2 let, PAID
    expired = supabase.table("orders").select(
        "id, email, company_id, plan, paid_at"
    ).eq("plan", "enterprise").eq("status", "PAID").lt(
        "paid_at", two_years_ago
    ).execute()

    if not expired.data:
        return 0

    from backend.outbound.email_engine import send_email

    count = 0
    for order in expired.data:
        email = order.get("email", "")
        company_id = order.get("company_id")
        if not email:
            continue

        # Check if we already processed (look for existing subscription)
        existing = supabase.table("subscriptions").select("id").eq(
            "email", email
        ).in_("status", ["active", "cancelled", "expired_enterprise_notified"]).execute()
        if existing.data:
            continue

        # Najít firmu
        company_name = ""
        if company_id:
            comp = supabase.table("companies").select("name").eq(
                "id", company_id
            ).limit(1).execute()
            if comp.data:
                company_name = comp.data[0].get("name", "")

        # Poslat email s nabídkou monitoringu
        settings = get_settings()
        html = f"""
        <div style="font-family:system-ui,sans-serif;max-width:600px;margin:0 auto;padding:24px;">
            <div style="background:linear-gradient(135deg,#0f172a,#1e1b4b);padding:32px;border-radius:16px;color:#f1f5f9;">
                <h1 style="color:#e879f9;margin:0 0 16px;">AIshield.cz</h1>
                <h2 style="color:#fff;margin:0 0 20px;">Váš ENTERPRISE monitoring dosáhl konce dvouletého období</h2>

                <p style="color:#cbd5e1;line-height:1.6;">
                    Dobrý den,<br><br>
                    rádi bychom Vás informovali, že dvouleté období monitoringu zahrnutého
                    v balíčku ENTERPRISE{f' pro firmu <strong>{company_name}</strong>' if company_name else ''}
                    právě skončilo.
                </p>

                <p style="color:#cbd5e1;line-height:1.6;">
                    Vaše compliance dokumentace zůstává platná, ale automatický monitoring
                    a aktualizace dokumentů byly pozastaveny.
                </p>

                <div style="background:rgba(124,58,237,0.1);border:1px solid rgba(124,58,237,0.3);border-radius:12px;padding:20px;margin:20px 0;">
                    <h3 style="color:#a78bfa;margin:0 0 12px;">Pokračujte v monitoringu</h3>

                    <div style="display:flex;gap:16px;flex-wrap:wrap;">
                        <div style="flex:1;min-width:200px;background:rgba(0,0,0,0.2);border-radius:8px;padding:16px;">
                            <h4 style="color:#22d3ee;margin:0 0 8px;">Monitoring</h4>
                            <p style="color:#fff;font-size:24px;font-weight:800;margin:0 0 4px;">{settings.price_monitoring} Kč<span style="font-size:14px;color:#94a3b8;">/měsíc</span></p>
                            <p style="color:#94a3b8;font-size:13px;margin:0;">1× hloubkový sken/měsíc</p>
                        </div>
                        <div style="flex:1;min-width:200px;background:rgba(0,0,0,0.2);border-radius:8px;padding:16px;">
                            <h4 style="color:#e879f9;margin:0 0 8px;">Monitoring Plus</h4>
                            <p style="color:#fff;font-size:24px;font-weight:800;margin:0 0 4px;">{settings.price_monitoring_plus} Kč<span style="font-size:14px;color:#94a3b8;">/měsíc</span></p>
                            <p style="color:#94a3b8;font-size:13px;margin:0;">2× sken/měsíc + aktualizace dokumentů</p>
                        </div>
                    </div>

                    <p style="color:#94a3b8;font-size:13px;margin:16px 0 0;">
                        Stačí odpovědět na tento email nebo se přihlásit do
                        <a href="https://aishield.cz/dashboard#monitoring" style="color:#a78bfa;">dashboardu</a>.
                    </p>
                </div>

                <p style="color:#64748b;font-size:12px;margin-top:24px;">
                    AIshield.cz — AI Act compliance pro české firmy<br>
                    Bc. Martin Haynes | IČO: 17889251 |
                    <a href="mailto:info@aishield.cz" style="color:#a78bfa;">info@aishield.cz</a>
                </p>
            </div>
        </div>
        """

        try:
            await send_email(
                to=email,
                subject="AIshield.cz — Váš ENTERPRISE monitoring skončil — nabídka pokračování",
                html=html,
                from_email="info@aishield.cz",
                from_name="AIshield.cz",
            )
            # Also notify admin
            await send_email(
                to="info@aishield.cz",
                subject=f"[ENTERPRISE EXPIRY] {company_name or email} — 2 roky uplynuly",
                html=f"<p>Enterprise monitoring pro <strong>{company_name or email}</strong> vypršel. Nabídkový email odeslán.</p>",
                from_email="info@aishield.cz",
            )

            # Mark as notified (insert dummy subscription record)
            supabase.table("subscriptions").insert({
                "email": email,
                "plan": "enterprise_expired",
                "amount": 0,
                "status": "expired_enterprise_notified",
                "company_id": company_id,
                "payment_gateway": "none",
                "created_at": now.isoformat(),
            }).execute()

            count += 1
            logger.info(f"[Subscription] Enterprise expiry notified: {email}")
        except Exception as e:
            logger.error(f"[Subscription] Failed to notify enterprise expiry: {e}")

    return count


async def check_overdue_subscriptions():
    """
    Kontroluje neplatby FIO subscription.
    D+3: první upomínka
    D+7: druhá upomínka
    D+14: deaktivace
    """
    supabase = get_supabase()
    now = datetime.now(timezone.utc)
    today = now.date()

    # Active FIO subscriptions
    subs = supabase.table("subscriptions").select("*").eq(
        "status", "active"
    ).eq("payment_gateway", "bank_transfer").execute()

    if not subs.data:
        return

    from backend.outbound.email_engine import send_email

    for sub in subs.data:
        next_charge = sub.get("next_charge_at")
        if not next_charge:
            continue

        charge_date = date.fromisoformat(next_charge)
        days_overdue = (today - charge_date).days

        if days_overdue < 3:
            continue  # Ještě v toleranci

        reminder_sent = sub.get("reminder_sent_at")
        email = sub["email"]
        plan_name = MONITORING_PLANS.get(sub["plan"], {}).get("name", sub["plan"])

        if days_overdue >= 14:
            # DEAKTIVACE
            supabase.table("subscriptions").update({
                "status": "suspended",
                "updated_at": now.isoformat(),
            }).eq("id", sub["id"]).execute()

            await send_email(
                to=email,
                subject=f"AIshield.cz — Monitoring {plan_name} pozastaven",
                html=f"""
                <div style="font-family:system-ui;max-width:600px;margin:0 auto;padding:24px;">
                    <h2>Monitoring pozastaven</h2>
                    <p>Nezaznamenali jsme platbu za měsíční monitoring <strong>{plan_name}</strong>
                    po dobu 14 dní. Služba byla pozastavena.</p>
                    <p>Pro obnovení služby prosím uhraďte dlužnou částku
                    <strong>{sub['amount']} Kč</strong> na účet 2503446206/2010,
                    VS: <strong>{sub.get('variable_symbol', '---')}</strong>.</p>
                    <p>Nebo nás kontaktujte na <a href="mailto:info@aishield.cz">info@aishield.cz</a>.</p>
                </div>
                """,
                from_email="info@aishield.cz",
                from_name="AIshield.cz",
            )
            await send_email(
                to="info@aishield.cz",
                subject=f"[SUSPENDED] {email} — monitoring pozastaven (14d neplatba)",
                html=f"<p>Monitoring pro {email} pozastaven kvůli neplatbě.</p>",
                from_email="info@aishield.cz",
            )
            logger.info(f"[Subscription] SUSPENDED: {sub['id']} ({email}) — 14d overdue")

        elif days_overdue >= 7 and (not reminder_sent or reminder_sent < (now - timedelta(days=3)).isoformat()):
            # Druhá upomínka (D+7)
            await send_email(
                to=email,
                subject=f"⚠️ AIshield.cz — Monitoring bude pozastaven za 7 dní",
                html=f"""
                <div style="font-family:system-ui;max-width:600px;margin:0 auto;padding:24px;">
                    <h2>Nezaznamenali jsme platbu</h2>
                    <p>Platba za monitoring <strong>{plan_name}</strong> ({sub['amount']} Kč)
                    je 7 dní po splatnosti.</p>
                    <p><strong>Pokud platbu neobdržíme do 7 dní, monitoring bude pozastaven.</strong></p>
                    <p>Účet: 2503446206/2010 | VS: {sub.get('variable_symbol', '---')}</p>
                </div>
                """,
                from_email="info@aishield.cz",
                from_name="AIshield.cz",
            )
            supabase.table("subscriptions").update({
                "reminder_sent_at": now.isoformat(),
            }).eq("id", sub["id"]).execute()
            logger.info(f"[Subscription] Reminder D+7: {email}")

        elif days_overdue >= 3 and not reminder_sent:
            # První upomínka (D+3)
            await send_email(
                to=email,
                subject=f"AIshield.cz — Připomínka platby za monitoring",
                html=f"""
                <div style="font-family:system-ui;max-width:600px;margin:0 auto;padding:24px;">
                    <h2>Nezaznamenali jsme platbu</h2>
                    <p>Platba za monitoring <strong>{plan_name}</strong> ({sub['amount']} Kč)
                    měla přijít {next_charge}.</p>
                    <p>Pokud jste již platbu odeslali, ignorujte prosím tuto zprávu —
                    převod může trvat 1-2 pracovní dny.</p>
                    <p>Účet: 2503446206/2010 | VS: {sub.get('variable_symbol', '---')}</p>
                </div>
                """,
                from_email="info@aishield.cz",
                from_name="AIshield.cz",
            )
            supabase.table("subscriptions").update({
                "reminder_sent_at": now.isoformat(),
            }).eq("id", sub["id"]).execute()
            logger.info(f"[Subscription] Reminder D+3: {email}")
