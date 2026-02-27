"""
AIshield.cz — Payments API
Multi-gateway: Stripe + bankovní převod.
GoPay — zakomentováno (čekáme na vyjádření).
Comgate — odstraněno (žádost zamítnuta).
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
import uuid
import logging
import random
from typing import Literal

from backend.config import get_settings
from backend.database import get_supabase
# GOPAY — zakomentováno (čekáme na vyjádření)
# from backend.payments import get_gopay, PaymentState, RecurrenceCycle
from backend.payments.stripe_client import get_stripe
# COMGATE — odstraněno (žádost zamítnuta)
# from backend.payments.comgate_client import get_comgate
from backend.api.auth import AuthUser, get_current_user, get_optional_user
from backend.outbound.payment_emails import (
    build_bank_transfer_email,
    build_payment_received_email,
    build_payment_confirmation_email,
    generate_variable_symbol,
    generate_payment_qr_png,
)
from backend.outbound.email_engine import send_email
from backend.api.analytics import track_server_event

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Cenové balíčky ──
PLANS = {
    "basic": {
        "name": "BASIC",
        "description": "AI Act Compliance Kit — dokumenty ke stažení",
        "price_field": "price_basic",
    },
    "pro": {
        "name": "PRO",
        "description": "Compliance Kit + implementace na klíč + 30 dní podpora",
        "price_field": "price_pro",
    },
    "enterprise": {
        "name": "ENTERPRISE",
        "description": "Komplexní řešení pro větší firmy + 2 roky průběžné péče",
        "price_field": "price_enterprise",
    },
    "coffee": {
        "name": "Kafé",
        "description": "Pozvi nás na kafé ☕",
        "price_field": "price_coffee",
    },
    "monitoring": {
        "name": "Monitoring",
        "description": "1× měsíčně 24h hloubkový sken webu + compliance report",
        "price_field": "price_monitoring",
    },
    "monitoring_plus": {
        "name": "Monitoring Plus",
        "description": "2× měsíčně 24h hloubkový sken + aktualizace dokumentů + implementace změn",
        "price_field": "price_monitoring_plus",
    },
}

# ── Monitoring předplatné (měsíční) — ZAKOMENTOVÁNO (vyžaduje GoPay) ──
# SUBSCRIPTION_PLANS = {
#     "monitoring": {
#         "name": "Monitoring",
#         "description": "1× měsíčně automatický sken webu + compliance report",
#         "price": 299,  # CZK/měsíc
#         "cycle": RecurrenceCycle.MONTH,
#         "period": 1,
#     },
#     "monitoring_plus": {
#         "name": "Monitoring Plus",
#         "description": "2× měsíčně sken + implementace změn + prioritní podpora",
#         "price": 599,  # CZK/měsíc
#         "cycle": RecurrenceCycle.MONTH,
#         "period": 1,
#     },
# }


class BillingInfo(BaseModel):
    """Fakturační údaje zákazníka."""
    company: str = ""
    ico: str = ""
    dic: str = ""
    street: str = ""
    city: str = ""
    zip: str = ""
    phone: str = ""
    email: str = ""


class CheckoutRequest(BaseModel):
    """Request pro vytvoření platby."""
    plan: str  # "basic" nebo "pro"
    email: str
    gateway: Literal["stripe", "bank_transfer"] = "stripe"
    billing: BillingInfo | None = None


class CheckoutResponse(BaseModel):
    """Response s URL na platební bránu."""
    payment_id: str  # Stripe session ID nebo interní ID
    gateway_url: str
    order_number: str
    gateway: str = "stripe"


class SubscriptionRequest(BaseModel):
    """Request pro vytvoření subscription."""
    plan: str  # "monitoring" nebo "monitoring_plus"
    email: str


class SubscriptionChargeRequest(BaseModel):
    """Request pro stržení další platby ze subscription."""
    subscription_id: str  # ID subscription v naší DB
    amount: int | None = None  # Částka v CZK, None = stejná jako předchozí


class RefundRequest(BaseModel):
    """Request pro refundaci platby."""
    payment_id: int
    amount: int | None = None  # Částka v CZK, None = plná refundace
    reason: str = ""


# ────────────────────────────────────────────────────────────
# GATEWAY HELPER — vytvoří platbu přes zvolenou bránu
# ────────────────────────────────────────────────────────────

# Dostupné brány a jejich popisky
AVAILABLE_GATEWAYS = {
    "stripe": "Stripe",
    # "gopay": "GoPay",  # ZAKOMENTOVÁNO — čekáme na vyjádření
}

# Příjemci notifikací o nových objednávkách
ORDER_NOTIFY_EMAILS = ["info@aishield.cz", "bc.pospa@gmail.com"]


async def _notify_new_order(
    order_number: str,
    plan: str,
    amount: int,
    email: str,
    gateway: str,
    status: str,
    order_type: str = "one_time",
    billing: dict | None = None,
):
    """Pošle notifikaci o nové objednávce na provozní emaily."""
    plan_info = PLANS.get(plan, {})
    plan_name = plan_info.get("name", plan)

    billing_html = ""
    if billing:
        billing_rows = []
        labels = {
            "company": "Firma", "ico": "IČO", "dic": "DIČ",
            "street": "Ulice", "city": "Město", "zip": "PSČ",
            "phone": "Telefon", "email": "Email",
        }
        for key, label in labels.items():
            val = billing.get(key, "")
            if val:
                billing_rows.append(f"<tr><td style='padding:4px 12px 4px 0;color:#94a3b8;'>{label}</td><td style='padding:4px 0;color:#f1f5f9;font-weight:600;'>{val}</td></tr>")
        if billing_rows:
            billing_html = f"""
            <div style="margin-top:20px;">
                <h3 style="color:#e879f9;font-size:16px;margin:0 0 8px;">Fakturační údaje</h3>
                <table style="border-collapse:collapse;">{''.join(billing_rows)}</table>
            </div>"""

    html = f"""
    <div style="font-family:Inter,system-ui,sans-serif;background:#0f172a;color:#f1f5f9;padding:32px;border-radius:16px;max-width:600px;">
        <div style="text-align:center;margin-bottom:24px;">
            <h1 style="color:#e879f9;font-size:24px;margin:0;">🎉 Nová objednávka!</h1>
        </div>

        <div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:12px;padding:20px;">
            <table style="width:100%;border-collapse:collapse;">
                <tr>
                    <td style="padding:8px 12px 8px 0;color:#94a3b8;">Číslo objednávky</td>
                    <td style="padding:8px 0;color:#f1f5f9;font-weight:700;font-size:16px;">{order_number}</td>
                </tr>
                <tr>
                    <td style="padding:8px 12px 8px 0;color:#94a3b8;">Balíček</td>
                    <td style="padding:8px 0;color:#e879f9;font-weight:700;font-size:16px;">{plan_name}</td>
                </tr>
                <tr>
                    <td style="padding:8px 12px 8px 0;color:#94a3b8;">Částka</td>
                    <td style="padding:8px 0;color:#22d3ee;font-weight:700;font-size:18px;">{amount:,} Kč</td>
                </tr>
                <tr>
                    <td style="padding:8px 12px 8px 0;color:#94a3b8;">Email zákazníka</td>
                    <td style="padding:8px 0;color:#f1f5f9;font-weight:600;">{email}</td>
                </tr>
                <tr>
                    <td style="padding:8px 12px 8px 0;color:#94a3b8;">Platební brána</td>
                    <td style="padding:8px 0;color:#f1f5f9;">{AVAILABLE_GATEWAYS.get(gateway, gateway).upper()}</td>
                </tr>
                <tr>
                    <td style="padding:8px 12px 8px 0;color:#94a3b8;">Stav</td>
                    <td style="padding:8px 0;color:#fbbf24;font-weight:600;">{status}</td>
                </tr>
                <tr>
                    <td style="padding:8px 12px 8px 0;color:#94a3b8;">Typ</td>
                    <td style="padding:8px 0;color:#f1f5f9;">{order_type}</td>
                </tr>
                <tr>
                    <td style="padding:8px 12px 8px 0;color:#94a3b8;">Čas</td>
                    <td style="padding:8px 0;color:#f1f5f9;">{datetime.utcnow().strftime('%d.%m.%Y %H:%M UTC')}</td>
                </tr>
            </table>
        </div>
        {billing_html}
        <div style="margin-top:20px;text-align:center;">
            <a href="https://aishield.cz/admin" style="display:inline-block;background:linear-gradient(135deg,#c026d3,#7c3aed);color:white;padding:12px 24px;border-radius:12px;text-decoration:none;font-weight:600;font-size:14px;">
                Otevřít Admin Dashboard →
            </a>
        </div>
        <p style="margin-top:16px;color:#64748b;font-size:12px;text-align:center;">
            AIshield.cz — automatická notifikace
        </p>
    </div>
    """

    for notify_email in ORDER_NOTIFY_EMAILS:
        try:
            await send_email(
                to=notify_email,
                subject=f"🎉 Nová objednávka {order_number} — {plan_name} ({amount:,} Kč)",
                html=html,
                from_email="info@aishield.cz",
                from_name="AIshield.cz Notifikace",
            )
            logger.info(f"[Payments] Order notification sent to {notify_email} for {order_number}")
        except Exception as e:
            logger.error(f"[Payments] Failed to send order notification to {notify_email}: {e}")


async def _create_payment_via_gateway(
    gateway: str,
    amount: int,
    order_number: str,
    description: str,
    email: str,
    return_url: str,
    notify_url: str,
) -> dict:
    """
    Univerzální helper: vytvoří platbu přes zvolenou bránu.

    Returns:
        dict s klíči: payment_id (str), gateway_url, state, gateway
    """
    if gateway == "stripe":
        stripe_client = get_stripe()
        if not stripe_client.is_configured:
            raise HTTPException(
                status_code=503,
                detail="Stripe platby nejsou momentálně nakonfigurované. Použijte bankovní převod.",
            )
        payment = await stripe_client.create_payment(
            amount=amount,
            order_number=order_number,
            description=description,
            email=email,
            return_url=return_url,
            notify_url=notify_url,
        )
        return {
            "payment_id": str(payment.payment_id),
            "gateway_url": payment.gateway_url,
            "state": payment.state,
            "gateway": "stripe",
        }

    # GOPAY — zakomentováno (čekáme na vyjádření)
    # else:
    #     gopay = get_gopay()
    #     payment = await gopay.create_payment(
    #         amount=amount,
    #         order_number=order_number,
    #         description=description,
    #         email=email,
    #         return_url=return_url,
    #         notify_url=notify_url,
    #     )
    #     return {
    #         "payment_id": str(payment.payment_id),
    #         "gateway_url": payment.gateway_url,
    #         "state": payment.state,
    #         "gateway": "gopay",
    #     }

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Nepodporovaná platební brána: {gateway}. Použijte 'stripe' nebo 'bank_transfer'.",
        )


@router.get("/payment-qr/{variable_symbol}.png")
async def get_payment_qr(variable_symbol: str, amount: float = 4999, order: str = ""):
    """
    Generuje platební QR kód jako PNG obrázek.
    Používáno v emailech pro zobrazení QR kódu (místo data: URI, které blokuje Gmail).
    """
    png_bytes = generate_payment_qr_png(int(amount), variable_symbol, order or variable_symbol)
    if not png_bytes:
        raise HTTPException(status_code=500, detail="QR code generation not available")
    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={
            "Cache-Control": "public, max-age=31536000, immutable",
        },
    )


@router.get("/gateways")
async def list_available_gateways():
    """
    Vrátí seznam dostupných platebních bran.
    Frontend použije pro zobrazení gateway selectoru.
    """
    settings = get_settings()
    gateways = []

    # GOPAY — zakomentováno (čekáme na vyjádření)
    # gateways.append({
    #     "id": "gopay",
    #     "name": "GoPay",
    #     "description": "Karty, bankovní převod, Apple Pay, Google Pay",
    #     "available": True,
    #     "default": settings.default_payment_gateway == "gopay",
    # })

    # Stripe
    stripe_client = get_stripe()
    gateways.append({
        "id": "stripe",
        "name": "Stripe",
        "description": "Visa, Mastercard, Apple Pay, Google Pay",
        "available": stripe_client.is_configured,
        "default": settings.default_payment_gateway == "stripe",
    })

    # COMGATE — odstraněno (žádost zamítnuta)

    # Bankovní převod — vždy dostupný
    gateways.append({
        "id": "bank_transfer",
        "name": "Bankovní převod",
        "description": "Faktura s platebními údaji na email",
        "available": True,
        "default": False,
    })

    return {"gateways": gateways}


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(req: CheckoutRequest, user: AuthUser = Depends(get_current_user)):
    """
    Vytvoří jednorázovou platbu přes Stripe
    nebo objednávku s bankovním převodem.
    Vyžaduje přihlášení.
    """
    if req.plan not in PLANS:
        raise HTTPException(status_code=400, detail=f"Neznámý balíček: {req.plan}")

    settings = get_settings()
    plan = PLANS[req.plan]
    amount = getattr(settings, plan["price_field"])
    gateway = req.gateway or settings.default_payment_gateway

    _numeric_suffix = str(random.randint(10000000, 99999999))
    order_number = f"AS-{req.plan.upper()}-{_numeric_suffix}"

    # ── Resolve company_id by email ──
    _company_id = None
    try:
        _sb = get_supabase()
        _comp_res = _sb.table("companies").select("id").eq("email", req.email).limit(1).execute()
        if _comp_res.data:
            _company_id = _comp_res.data[0]["id"]
            logger.info(f"[Checkout] Resolved company_id={_company_id} for email={req.email}")
        else:
            logger.warning(f"[Checkout] No company found for email={req.email}")
    except Exception as _e:
        logger.error(f"[Checkout] Failed to resolve company_id: {_e}")

    frontend_url = settings.app_url if settings.environment == "production" else "http://localhost:3000"
    api_url = settings.api_url if settings.environment == "production" else "http://localhost:8000"

    # ── Bankovní převod — speciální flow ──
    if gateway == "bank_transfer":
        variable_symbol = generate_variable_symbol(order_number)
        due_date = (datetime.utcnow() + timedelta(days=7)).strftime("%d. %m. %Y")

        supabase = get_supabase()
        order_data = {
            "order_number": order_number,
            "gopay_payment_id": f"BT-{variable_symbol}",
            "plan": req.plan,
            "amount": amount,
            "email": req.email,
            "user_email": req.email,
            "status": "AWAITING_PAYMENT",
            "order_type": "one_time",
            "payment_gateway": "bank_transfer",
            "created_at": datetime.utcnow().isoformat(),
        }
        if _company_id:
            order_data["company_id"] = _company_id
        if req.billing:
            order_data["billing_data"] = req.billing.model_dump()
        supabase.table("orders").insert(order_data).execute()

        # Notifikace o nové objednávce
        await _notify_new_order(
            order_number=order_number, plan=req.plan, amount=amount,
            email=req.email, gateway="bank_transfer", status="AWAITING_PAYMENT",
            billing=req.billing.model_dump() if req.billing else None,
        )

        # Odeslat email s platebními údaji + QR kód jako příloha
        try:
            html, qr_attachments = build_bank_transfer_email(
                order_number=order_number,
                plan=req.plan,
                amount=amount,
                email=req.email,
                variable_symbol=variable_symbol,
                due_date=due_date,
            )
            await send_email(
                to=req.email,
                subject=f"AIshield.cz — Objednávka {order_number} — platební údaje",
                html=html,
                from_email="info@aishield.cz",
                from_name="AIshield.cz",
                attachments=qr_attachments if qr_attachments else None,
            )
            logger.info(f"[Payments] Bank transfer email sent to {req.email} for {order_number}")
        except Exception as e:
            logger.error(f"[Payments] Failed to send bank transfer email: {e}")

        # Vrátíme URL na success stránku (ne na platební bránu)
        return CheckoutResponse(
            payment_id=f"BT-{variable_symbol}",
            gateway_url=f"{frontend_url}/platba/stav?id=BT-{variable_symbol}&gateway=bank_transfer",
            order_number=order_number,
            gateway="bank_transfer",
        )

    # ── Online platba (Stripe) ──
    # Return URL
    if gateway == "stripe":
        return_url = f"{frontend_url}/platba/stav?session_id={{CHECKOUT_SESSION_ID}}&gateway=stripe"
        notify_url = f"{api_url}/api/payments/webhook/stripe"
    # GOPAY — zakomentováno (čekáme na vyjádření)
    # else:
    #     return_url = f"{frontend_url}/platba/stav?id={{paymentId}}&gateway=gopay"
    #     notify_url = f"{api_url}/api/payments/webhook"
    else:
        raise HTTPException(status_code=400, detail=f"Nepodporovaná brána: {gateway}")

    try:
        result = await _create_payment_via_gateway(
            gateway=gateway,
            amount=amount,
            order_number=order_number,
            description=f"AIshield.cz — {plan['name']}: {plan['description']}",
            email=req.email,
            return_url=return_url,
            notify_url=notify_url,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Payments] Chyba při vytváření platby ({gateway}): {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Chyba při komunikaci s {AVAILABLE_GATEWAYS.get(gateway, gateway)}: {str(e)}",
        )

    supabase = get_supabase()
    _stripe_order = {
        "order_number": order_number,
        "gopay_payment_id": result["payment_id"],
        "plan": req.plan,
        "amount": amount,
        "email": req.email,
        "user_email": req.email,
        "status": result["state"],
        "order_type": "one_time",
        "payment_gateway": gateway,
        "created_at": datetime.utcnow().isoformat(),
    }
    if _company_id:
        _stripe_order["company_id"] = _company_id
    supabase.table("orders").insert(_stripe_order).execute()

    # Notifikace o nové objednávce
    await _notify_new_order(
        order_number=order_number, plan=req.plan, amount=amount,
        email=req.email, gateway=gateway, status=result["state"],
        billing=req.billing.model_dump() if req.billing else None,
    )

    return CheckoutResponse(
        payment_id=result["payment_id"],
        gateway_url=result["gateway_url"],
        order_number=order_number,
        gateway=gateway,
    )


# ── Guest checkout (bez přihlášení, pouze coffee) ──

class GuestCheckoutRequest(BaseModel):
    """Request pro guest platbu (bez přihlášení). Pouze coffee."""
    plan: str = "coffee"
    email: str = ""
    gateway: Literal["stripe"] = "stripe"


@router.post("/checkout-guest", response_model=CheckoutResponse)
async def create_guest_checkout(req: GuestCheckoutRequest):
    """
    Vytvoří platbu bez přihlášení — povoleno pouze pro plán 'coffee'.
    Podporuje Stripe.
    """
    if req.plan != "coffee":
        raise HTTPException(status_code=403, detail="Guest checkout je povolen pouze pro plán 'coffee'.")

    if req.plan not in PLANS:
        raise HTTPException(status_code=400, detail=f"Neznámý balíček: {req.plan}")

    settings = get_settings()
    plan = PLANS[req.plan]
    amount = getattr(settings, plan["price_field"])
    gateway = req.gateway or settings.default_payment_gateway

    _numeric_suffix = str(random.randint(10000000, 99999999))
    order_number = f"AS-{req.plan.upper()}-{_numeric_suffix}"

    frontend_url = settings.app_url if settings.environment == "production" else "http://localhost:3000"
    api_url = settings.api_url if settings.environment == "production" else "http://localhost:8000"

    guest_email = req.email or "guest@aishield.cz"

    # Return URL
    return_url = f"{frontend_url}/platba/stav?session_id={{CHECKOUT_SESSION_ID}}&gateway=stripe"
    notify_url = f"{api_url}/api/payments/webhook/stripe"

    try:
        result = await _create_payment_via_gateway(
            gateway=gateway,
            amount=amount,
            order_number=order_number,
            description=f"AIshield.cz — {plan['name']}: {plan['description']}",
            email=guest_email,
            return_url=return_url,
            notify_url=notify_url,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Payments] Chyba při guest checkout ({gateway}): {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Chyba při komunikaci s {AVAILABLE_GATEWAYS.get(gateway, gateway)}: {str(e)}",
        )

    supabase = get_supabase()
    supabase.table("orders").insert({
        "order_number": order_number,
        "gopay_payment_id": result["payment_id"],
        "plan": req.plan,
        "amount": amount,
        "email": guest_email,
        "user_email": guest_email,
        "status": result["state"],
        "order_type": "one_time",
        "payment_gateway": gateway,
        "created_at": datetime.utcnow().isoformat(),
    }).execute()

    # Notifikace o nové objednávce (guest)
    await _notify_new_order(
        order_number=order_number, plan=req.plan, amount=amount,
        email=guest_email, gateway=gateway, status=result["state"],
    )

    return CheckoutResponse(
        payment_id=result["payment_id"],
        gateway_url=result["gateway_url"],
        order_number=order_number,
        gateway=gateway,
    )


# ────────────────────────────────────────────────────────────
# MONITORING ELIGIBILITY (kontrola, zda klient může aktivovat monitoring)
# ────────────────────────────────────────────────────────────

async def _check_monitoring_eligibility(email: str) -> dict:
    """
    Zkontroluje, zda klient splňuje podmínky pro aktivaci monitoringu.
    Požadavky:
    1. Zaplacený jednorázový balíček (BASIC/PRO/ENTERPRISE)
    2. Proběhlý sken webu (status=done)
    3. Vyplněný dotazník
    4. Vygenerované dokumenty (alespoň 1)
    5. Nemá už aktivní monitoring subscription
    """
    supabase = get_supabase()

    # 1. Zaplacená jednorázová objednávka
    orders = supabase.table("orders").select("plan, status, order_type").eq(
        "email", email
    ).execute()
    has_paid_order = any(
        o["status"] == "PAID" and o["order_type"] == "one_time"
        for o in (orders.data or [])
    )
    paid_plan = next(
        (o["plan"] for o in (orders.data or [])
         if o["status"] == "PAID" and o["order_type"] == "one_time"),
        None,
    )

    # 2. Firma + sken
    company = None
    company_res = supabase.table("companies").select("id").eq(
        "email", email
    ).limit(1).execute()
    if company_res.data:
        company = company_res.data[0]

    scan_completed = False
    if company:
        scans = supabase.table("scans").select("status").eq(
            "company_id", company["id"]
        ).eq("status", "done").limit(1).execute()
        scan_completed = bool(scans.data)

    # 3. Dotazník
    questionnaire_done = False
    if company:
        client_res = supabase.table("clients").select("id").eq(
            "company_id", company["id"]
        ).limit(1).execute()
        if client_res.data:
            quest_res = supabase.table("questionnaire_responses").select("id").eq(
                "client_id", client_res.data[0]["id"]
            ).limit(1).execute()
            questionnaire_done = bool(quest_res.data)

    # 4. Dokumenty
    documents_generated = False
    if company:
        docs = supabase.table("documents").select("id").eq(
            "company_id", company["id"]
        ).limit(1).execute()
        documents_generated = bool(docs.data)

    # 5. Aktivní subscription
    active_subs = supabase.table("subscriptions").select("id, plan, status").eq(
        "email", email
    ).eq("status", "active").execute()
    has_active_subscription = bool(active_subs.data)
    active_plan = active_subs.data[0]["plan"] if active_subs.data else None

    # Enterprise má 2 roky monitoringu v ceně
    is_enterprise = paid_plan == "enterprise"

    eligible = (
        has_paid_order
        and scan_completed
        and questionnaire_done
        and documents_generated
        and not has_active_subscription
    )

    checks = {
        "has_paid_order": has_paid_order,
        "paid_plan": paid_plan,
        "scan_completed": scan_completed,
        "questionnaire_done": questionnaire_done,
        "documents_generated": documents_generated,
        "has_active_subscription": has_active_subscription,
        "active_plan": active_plan,
        "is_enterprise": is_enterprise,
    }

    if not eligible:
        missing = []
        if not has_paid_order:
            missing.append("Nejdříve je nutné zakoupit balíček (BASIC, PRO nebo ENTERPRISE)")
        if not scan_completed:
            missing.append("Sken webu musí být dokončen")
        if not questionnaire_done:
            missing.append("Dotazník musí být vyplněn")
        if not documents_generated:
            missing.append("Compliance dokumenty musí být vygenerovány")
        if has_active_subscription:
            missing.append(f"Již máte aktivní monitoring ({active_plan})")
        reason = "; ".join(missing)
    else:
        reason = "Splňujete všechny podmínky pro aktivaci monitoringu"

    return {
        "eligible": eligible,
        "reason": reason,
        "checks": checks,
    }


@router.get("/monitoring-eligibility")
async def check_monitoring_eligibility(user: AuthUser = Depends(get_current_user)):
    """
    Zkontroluje, zda přihlášený uživatel splňuje podmínky pro monitoring.
    Vrátí detailed checks pro frontend.
    """
    return await _check_monitoring_eligibility(user.email)

# ════════════════════════════════════════════════════════════
# P6: MONITORING SUBSCRIPTIONS (Stripe + FIO trvalý příkaz)
# ════════════════════════════════════════════════════════════

from backend.payments.subscription_manager import (
    MONITORING_PLANS,
    create_subscription as _create_sub,
    cancel_subscription as _cancel_sub,
    generate_monitoring_vs,
    get_scan_days_for_plan,
)


class SubscribeRequest(BaseModel):
    """Request pro aktivaci měsíčního monitoringu."""
    plan: str  # "monitoring" nebo "monitoring_plus"
    email: str
    gateway: Literal["stripe", "bank_transfer"] = "stripe"
    billing: BillingInfo | None = None


class SubscribeCancelRequest(BaseModel):
    subscription_id: str


@router.post("/subscribe")
async def create_monitoring_subscription(req: SubscribeRequest, user: AuthUser = Depends(get_current_user)):
    """
    Aktivace měsíčního monitoringu.
    GUARD: Vyžaduje zaplacený balíček + sken + dotazník + dokumenty.
    Gateway: stripe (karta) nebo bank_transfer (FIO trvalý příkaz).
    Min. doba: 3 měsíce.
    """
    if req.plan not in MONITORING_PLANS:
        raise HTTPException(
            status_code=400,
            detail=f"Neznámý monitoring plán: {req.plan}. Dostupné: {', '.join(MONITORING_PLANS.keys())}",
        )

    # Eligibility check
    eligibility = await _check_monitoring_eligibility(req.email)
    if not eligibility["eligible"]:
        raise HTTPException(status_code=403, detail=f"Monitoring nelze aktivovat: {eligibility['reason']}")

    settings = get_settings()
    plan_info = MONITORING_PLANS[req.plan]
    amount = getattr(settings, plan_info["price_field"])

    # Resolve company_id
    _company_id = None
    try:
        _sb = get_supabase()
        _comp = _sb.table("companies").select("id").eq("email", req.email).limit(1).execute()
        if _comp.data:
            _company_id = _comp.data[0]["id"]
    except Exception:
        pass

    if req.gateway == "bank_transfer":
        # ── FIO trvalý příkaz flow ──
        sub_result = await _create_sub(
            email=req.email,
            plan=req.plan,
            gateway="bank_transfer",
            company_id=_company_id,
        )

        # Poslat email s instrukcemi pro trvalý příkaz
        vs = sub_result["variable_symbol"]
        min_end = sub_result["min_end_date"]

        html = f"""
        <div style="font-family:system-ui;max-width:600px;margin:0 auto;padding:24px;">
            <div style="background:linear-gradient(135deg,#0f172a,#1e1b4b);padding:32px;border-radius:16px;color:#f1f5f9;">
                <h1 style="color:#e879f9;margin:0 0 8px;">AIshield.cz</h1>
                <h2 style="color:#fff;margin:0 0 20px;">Nastavte si trvalý příkaz pro monitoring</h2>

                <p style="color:#cbd5e1;line-height:1.6;">
                    Děkujeme za objednání monitoringu <strong style="color:#22d3ee;">{plan_info['name']}</strong>.
                    Pro aktivaci služby si prosím nastavte trvalý příkaz v internetovém bankovnictví:
                </p>

                <div style="background:rgba(124,58,237,0.1);border:1px solid rgba(124,58,237,0.3);border-radius:12px;padding:20px;margin:20px 0;">
                    <table style="width:100%;border-collapse:collapse;">
                        <tr><td style="padding:8px 0;color:#94a3b8;">Číslo účtu:</td>
                            <td style="padding:8px 0;color:#fff;font-weight:700;">2503446206/2010</td></tr>
                        <tr><td style="padding:8px 0;color:#94a3b8;">Banka:</td>
                            <td style="padding:8px 0;color:#fff;">Fio banka</td></tr>
                        <tr><td style="padding:8px 0;color:#94a3b8;">Částka:</td>
                            <td style="padding:8px 0;color:#22c55e;font-weight:800;font-size:18px;">{amount} Kč</td></tr>
                        <tr><td style="padding:8px 0;color:#94a3b8;">Variabilní symbol:</td>
                            <td style="padding:8px 0;color:#e879f9;font-weight:800;font-size:18px;">{vs}</td></tr>
                        <tr><td style="padding:8px 0;color:#94a3b8;">Periodicita:</td>
                            <td style="padding:8px 0;color:#fff;">Měsíčně</td></tr>
                        <tr><td style="padding:8px 0;color:#94a3b8;">IBAN:</td>
                            <td style="padding:8px 0;color:#fff;font-size:12px;">CZ8720100000002503446206</td></tr>
                    </table>
                </div>

                <p style="color:#94a3b8;font-size:13px;line-height:1.5;">
                    Minimální doba: 3 měsíce (do {min_end}). Výpověď: 1 měsíc.<br>
                    Monitoring se aktivuje automaticky po přijetí první platby.
                </p>
            </div>
        </div>
        """

        try:
            await send_email(
                to=req.email,
                subject=f"AIshield.cz — Monitoring {plan_info['name']} — platební údaje",
                html=html,
                from_email="info@aishield.cz",
                from_name="AIshield.cz",
            )
        except Exception as e:
            logger.error(f"[Subscribe] Failed to send FIO instructions: {e}")

        # Notifikace adminovi
        await _notify_new_order(
            order_number=sub_result["order_number"],
            plan=req.plan, amount=amount, email=req.email,
            gateway="bank_transfer", status="PENDING_FIRST_PAYMENT",
            order_type="subscription",
            billing=req.billing.model_dump() if req.billing else None,
        )

        return {
            "subscription_id": sub_result["subscription_id"],
            "order_number": sub_result["order_number"],
            "variable_symbol": vs,
            "gateway": "bank_transfer",
            "status": "pending_first_payment",
            "message": "Nastavte si trvalý příkaz. Monitoring se aktivuje po přijetí platby.",
        }

    elif req.gateway == "stripe":
        # ── Stripe Subscription flow ──
        stripe_client = get_stripe()
        if not stripe_client.is_configured:
            raise HTTPException(status_code=503, detail="Stripe není nakonfigurován.")

        import stripe
        stripe.api_key = settings.stripe_secret_key

        frontend_url = settings.app_url if settings.environment == "production" else "http://localhost:3000"

        # Create Stripe Checkout Session with mode=subscription
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "czk",
                    "product_data": {
                        "name": f"AIshield.cz — {plan_info['name']}",
                        "description": plan_info["description"],
                    },
                    "unit_amount": amount * 100,  # CZK → haléře
                    "recurring": {"interval": "month"},
                },
                "quantity": 1,
            }],
            mode="subscription",
            customer_email=req.email,
            metadata={
                "plan": req.plan,
                "email": req.email,
                "company_id": _company_id or "",
                "type": "monitoring_subscription",
            },
            success_url=f"{frontend_url}/platba/stav?session_id={{CHECKOUT_SESSION_ID}}&gateway=stripe&type=subscription",
            cancel_url=f"{frontend_url}/dashboard#monitoring",
        )

        # Pre-create subscription record (will be activated by webhook)
        sub_result = await _create_sub(
            email=req.email,
            plan=req.plan,
            gateway="stripe",
            company_id=_company_id,
            stripe_subscription_id=session.id,  # Will be updated by webhook
        )
        # Override status to pending (activated by webhook)
        supabase = get_supabase()
        supabase.table("subscriptions").update({
            "status": "pending_stripe",
        }).eq("id", sub_result["subscription_id"]).execute()

        # Notifikace
        await _notify_new_order(
            order_number=sub_result["order_number"],
            plan=req.plan, amount=amount, email=req.email,
            gateway="stripe", status="CREATED",
            order_type="subscription",
            billing=req.billing.model_dump() if req.billing else None,
        )

        return {
            "subscription_id": sub_result["subscription_id"],
            "order_number": sub_result["order_number"],
            "gateway_url": session.url,
            "gateway": "stripe",
            "status": "pending_stripe",
        }

    else:
        raise HTTPException(status_code=400, detail="Nepodporovaná brána. Použijte 'stripe' nebo 'bank_transfer'.")


@router.post("/subscribe/cancel")
async def cancel_monitoring_subscription(req: SubscribeCancelRequest, user: AuthUser = Depends(get_current_user)):
    """Zruší monitoring subscription. Min. 3 měsíce, výpověď 1 měsíc."""
    supabase = get_supabase()

    # Verify ownership
    sub = supabase.table("subscriptions").select("*").eq(
        "id", req.subscription_id
    ).limit(1).execute()
    if not sub.data:
        raise HTTPException(status_code=404, detail="Subscription nenalezena")
    if sub.data[0]["email"] != user.email:
        raise HTTPException(status_code=403, detail="Nemáte oprávnění")

    s = sub.data[0]

    # If Stripe, also cancel in Stripe
    if s.get("stripe_subscription_id") and s.get("payment_gateway") == "stripe":
        try:
            import stripe
            stripe.api_key = get_settings().stripe_secret_key
            # Cancel at period end (not immediately)
            stripe.Subscription.modify(
                s["stripe_subscription_id"],
                cancel_at_period_end=True,
            )
        except Exception as e:
            logger.error(f"[Subscribe] Stripe cancel failed: {e}")

    result = await _cancel_sub(req.subscription_id)
    return result


@router.get("/monitoring-status")
async def get_monitoring_status(user: AuthUser = Depends(get_current_user)):
    """Vrátí stav monitoring subscription pro přihlášeného uživatele."""
    supabase = get_supabase()

    subs = supabase.table("subscriptions").select("*").eq(
        "email", user.email
    ).in_("status", ["active", "pending_first_payment", "pending_stripe", "suspended"]).order(
        "created_at", desc=True
    ).limit(1).execute()

    if not subs.data:
        # Check enterprise
        enterprise = supabase.table("orders").select("paid_at").eq(
            "email", user.email
        ).eq("plan", "enterprise").eq("status", "PAID").limit(1).execute()

        if enterprise.data:
            from datetime import timedelta
            paid_at = datetime.fromisoformat(enterprise.data[0]["paid_at"].replace("Z", "+00:00"))
            expires_at = paid_at + timedelta(days=730)
            remaining = (expires_at - datetime.now(timezone.utc)).days

            if remaining > 0:
                return {
                    "active": True,
                    "plan": "enterprise_included",
                    "plan_name": "ENTERPRISE (monitoring v ceně)",
                    "remaining_days": remaining,
                    "expires_at": expires_at.isoformat(),
                    "scans_per_month": 1,
                }

        return {"active": False, "plan": None}

    sub = subs.data[0]
    plan_info = MONITORING_PLANS.get(sub["plan"], {})

    return {
        "active": sub["status"] == "active",
        "subscription_id": sub["id"],
        "plan": sub["plan"],
        "plan_name": plan_info.get("name", sub["plan"]),
        "status": sub["status"],
        "gateway": sub.get("payment_gateway"),
        "amount": sub["amount"],
        "next_scan_at": sub.get("next_scan_at"),
        "next_charge_at": sub.get("next_charge_at"),
        "scans_this_period": sub.get("scans_this_period", 0),
        "scans_per_month": plan_info.get("scans_per_month", 1),
        "last_diff_has_changes": sub.get("last_diff_has_changes", False),
        "min_end_date": sub.get("min_end_date"),
        "created_at": sub.get("created_at"),
    }



# ========================================================
# SUBSCRIPTIONS + REFUNDACE — ZAKOMENTOVANO (vyzaduje GoPay)
# Po schvaleni GoPay odkomentujte.
# ========================================================

# # ────────────────────────────────────────────────────────────
# # SUBSCRIPTIONS (OPAKOVANÉ PLATBY)
# # ────────────────────────────────────────────────────────────
#
# @router.post("/subscribe", response_model=CheckoutResponse)
# async def create_subscription(req: SubscriptionRequest, user: AuthUser = Depends(get_current_user)):
#     """
#     Vytvoří subscription (opakované platby) v GoPay.
#
#     Zákazník zaplatí první platbu přes gateway.
#     Další platby se strhávají automaticky (ON_DEMAND nebo MONTH).
#
#     Po zaplacení se vytvoří záznam v tabulce 'subscriptions'.
#
#     GUARD: Vyžaduje splnění všech podmínek (zaplacený balíček, sken, dotazník, dokumenty).
#     """
#     if req.plan not in SUBSCRIPTION_PLANS:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Neznámý subscription balíček: {req.plan}. "
#                    f"Dostupné: {', '.join(SUBSCRIPTION_PLANS.keys())}",
#         )
#
#     # ── Eligibility guard ──
#     eligibility = await _check_monitoring_eligibility(req.email)
#     if not eligibility["eligible"]:
#         raise HTTPException(
#             status_code=403,
#             detail=f"Monitoring nelze aktivovat: {eligibility['reason']}",
#         )
#
#     settings = get_settings()
#     plan = SUBSCRIPTION_PLANS[req.plan]
#
#     order_number = f"AS-SUB-{req.plan.upper()}-{uuid.uuid4().hex[:8].upper()}"
#
#     frontend_url = settings.app_url if settings.environment == "production" else "http://localhost:3000"
#     api_url = settings.api_url if settings.environment == "production" else "http://localhost:8000"
#
#     gopay = get_gopay()
#
#     try:
#         payment = await gopay.create_subscription(
#             amount=plan["price"],
#             order_number=order_number,
#             description=f"AIshield.cz — {plan['name']}: {plan['description']}",
#             email=req.email,
#             return_url=f"{frontend_url}/platba/stav?id={{paymentId}}&type=subscription",
#             notify_url=f"{api_url}/api/payments/webhook",
#             cycle=plan["cycle"],
#             recurrence_period=plan["period"],
#         )
#     except Exception as e:
#         logger.error(f"[Payments] Chyba při vytváření subscription: {e}")
#         raise HTTPException(
#             status_code=502,
#             detail=f"Chyba při komunikaci s GoPay: {str(e)}",
#         )
#
#     # Uložit do orders
#     supabase = get_supabase()
#     supabase.table("orders").insert({
#         "order_number": order_number,
#         "gopay_payment_id": payment.payment_id,
#         "plan": req.plan,
#         "amount": plan["price"],
#         "email": req.email,
#         "user_email": req.email,
#         "status": payment.state,
#         "order_type": "subscription",
#         "created_at": datetime.utcnow().isoformat(),
#     }).execute()
#
#     # Vytvořit subscription záznam (aktivuje se po zaplacení v webhooku)
#     subscription_id = str(uuid.uuid4())
#     supabase.table("subscriptions").insert({
#         "id": subscription_id,
#         "email": req.email,
#         "plan": req.plan,
#         "gopay_parent_payment_id": payment.payment_id,
#         "amount": plan["price"],
#         "cycle": plan["cycle"].value,
#         "status": "pending",
#         "order_number": order_number,
#         "created_at": datetime.utcnow().isoformat(),
#     }).execute()
#
#     logger.info(f"[Payments] Subscription vytvořena: {subscription_id} ({req.plan})")
#
#     return CheckoutResponse(
#         payment_id=payment.payment_id,
#         gateway_url=payment.gateway_url,
#         order_number=order_number,
#     )
#
#
# @router.post("/subscribe/charge")
# async def charge_subscription(req: SubscriptionChargeRequest, user: AuthUser = Depends(get_current_user)):
#     """
#     Strhne další platbu z existující subscription.
#
#     Používá se pro ON_DEMAND cyklus — tuto metodu volá náš
#     cron job nebo admin manuálně.
#     """
#     supabase = get_supabase()
#
#     # Najít subscription
#     sub = supabase.table("subscriptions").select("*").eq(
#         "id", req.subscription_id
#     ).single().execute()
#
#     if not sub.data:
#         raise HTTPException(status_code=404, detail="Subscription nenalezena")
#
#     if sub.data["status"] != "active":
#         raise HTTPException(
#             status_code=400,
#             detail=f"Subscription není aktivní (status: {sub.data['status']})",
#         )
#
#     amount = req.amount or sub.data["amount"]
#     order_number = f"AS-REC-{uuid.uuid4().hex[:8].upper()}"
#
#     gopay = get_gopay()
#
#     try:
#         payment = await gopay.charge_subscription(
#             parent_payment_id=sub.data["gopay_parent_payment_id"],
#             amount=amount,
#             order_number=order_number,
#             description=f"AIshield.cz — opakovaná platba {sub.data['plan']}",
#         )
#     except Exception as e:
#         logger.error(f"[Payments] Chyba při stržení subscription: {e}")
#         raise HTTPException(
#             status_code=502,
#             detail=f"Chyba při stržení platby: {str(e)}",
#         )
#
#     # Zalogovat platbu
#     supabase.table("orders").insert({
#         "order_number": order_number,
#         "gopay_payment_id": payment.payment_id,
#         "plan": sub.data["plan"],
#         "amount": amount,
#         "email": sub.data["email"],
#         "user_email": sub.data["email"],
#         "status": payment.state,
#         "order_type": "subscription_recurrence",
#         "subscription_id": req.subscription_id,
#         "created_at": datetime.utcnow().isoformat(),
#     }).execute()
#
#     # Aktualizovat subscription
#     supabase.table("subscriptions").update({
#         "last_charged_at": datetime.utcnow().isoformat(),
#         "total_charged": (sub.data.get("total_charged") or 0) + amount,
#     }).eq("id", req.subscription_id).execute()
#
#     logger.info(
#         f"[Payments] Subscription platba stržena: {req.subscription_id} ({amount} CZK)"
#     )
#
#     return {
#         "status": "ok",
#         "payment_id": payment.payment_id,
#         "amount": amount,
#         "order_number": order_number,
#     }
#
#
# @router.post("/subscribe/cancel")
# async def cancel_subscription(subscription_id: str, user: AuthUser = Depends(get_current_user)):
#     """
#     Zruší subscription — přestane strhávat platby.
#     Aktuální předplacené období zůstává platné.
#     """
#     supabase = get_supabase()
#
#     sub = supabase.table("subscriptions").select("*").eq(
#         "id", subscription_id
#     ).single().execute()
#
#     if not sub.data:
#         raise HTTPException(status_code=404, detail="Subscription nenalezena")
#
#     if sub.data["status"] in ("cancelled", "expired"):
#         raise HTTPException(
#             status_code=400,
#             detail=f"Subscription je již {sub.data['status']}",
#         )
#
#     gopay = get_gopay()
#
#     try:
#         await gopay.cancel_subscription(sub.data["gopay_parent_payment_id"])
#     except Exception as e:
#         logger.error(f"[Payments] Chyba při rušení subscription: {e}")
#         raise HTTPException(
#             status_code=502,
#             detail=f"Chyba při rušení subscription: {str(e)}",
#         )
#
#     supabase.table("subscriptions").update({
#         "status": "cancelled",
#         "cancelled_at": datetime.utcnow().isoformat(),
#     }).eq("id", subscription_id).execute()
#
#     logger.info(f"[Payments] Subscription zrušena: {subscription_id}")
#
#     return {"status": "cancelled", "subscription_id": subscription_id}
#
#
# @router.get("/subscribe/{subscription_id}")
# async def get_subscription_detail(subscription_id: str, user: AuthUser = Depends(get_current_user)):
#     """Vrátí detail subscription včetně GoPay recurrence info."""
#     supabase = get_supabase()
#
#     sub = supabase.table("subscriptions").select("*").eq(
#         "id", subscription_id
#     ).single().execute()
#
#     if not sub.data:
#         raise HTTPException(status_code=404, detail="Subscription nenalezena")
#
#     # Volitelně stáhnout stav z GoPay
#     gopay = get_gopay()
#     recurrence_info = None
#     try:
#         recurrence_info = await gopay.get_recurrence_info(
#             sub.data["gopay_parent_payment_id"]
#         )
#     except Exception:
#         pass  # GoPay nedostupné, vrátíme z DB
#
#     return {
#         **sub.data,
#         "gopay_recurrence": {
#             "cycle": recurrence_info.recurrence_cycle,
#             "end_date": recurrence_info.recurrence_date_to,
#             "state": recurrence_info.recurrence_state,
#         } if recurrence_info else None,
#     }
#
#
# # ────────────────────────────────────────────────────────────
# # REFUNDACE
# # ────────────────────────────────────────────────────────────
#
# @router.post("/refund")
# async def refund_payment(req: RefundRequest, user: AuthUser = Depends(get_current_user)):
#     """
#     Vrátí peníze zákazníkovi — plná nebo částečná refundace.
#
#     Pro plnou refundaci nevyplňujte amount.
#     Pro částečnou zadejte konkrétní částku v CZK.
#     """
#     gopay = get_gopay()
#     supabase = get_supabase()
#
#     # Ověřit, že objednávka existuje
#     order = supabase.table("orders").select("*").eq(
#         "gopay_payment_id", req.payment_id
#     ).single().execute()
#
#     if not order.data:
#         raise HTTPException(status_code=404, detail="Objednávka nenalezena")
#
#     if order.data["status"] in ("REFUNDED", "CANCELED"):
#         raise HTTPException(
#             status_code=400,
#             detail=f"Objednávka je již {order.data['status']}",
#         )
#
#     try:
#         result = await gopay.refund_payment(
#             payment_id=req.payment_id,
#             amount=req.amount,
#         )
#     except Exception as e:
#         logger.error(f"[Payments] Chyba při refundaci: {e}")
#         raise HTTPException(
#             status_code=502,
#             detail=f"Chyba při refundaci: {str(e)}",
#         )
#
#     refund_result = result.get("result", "UNKNOWN")
#
#     if refund_result == "FINISHED":
#         # Aktualizovat objednávku
#         new_status = "REFUNDED" if req.amount is None else "PARTIALLY_REFUNDED"
#         supabase.table("orders").update({
#             "status": new_status,
#             "refunded_at": datetime.utcnow().isoformat(),
#             "refund_amount": req.amount or order.data["amount"],
#             "refund_reason": req.reason,
#         }).eq("gopay_payment_id", req.payment_id).execute()
#
#         logger.info(
#             f"[Payments] Refundace úspěšná: payment={req.payment_id}, "
#             f"částka={req.amount or order.data['amount']} CZK"
#         )
#     else:
#         logger.warning(
#             f"[Payments] Refundace neúspěšná: payment={req.payment_id}, "
#             f"result={refund_result}"
#         )
#
#     return {
#         "status": refund_result,
#         "payment_id": req.payment_id,
#         "refund_amount": req.amount or order.data["amount"],
#         "reason": req.reason,
#     }
#
#

# ────────────────────────────────────────────────────────────
# STATUS + WEBHOOK (multi-gateway)
# ────────────────────────────────────────────────────────────

@router.get("/status/{payment_id}")
async def get_payment_status(payment_id: str, gateway: str = "stripe"):
    """
    Zkontroluje stav platby. Podporuje Stripe.
    GoPay — zakomentovano. Comgate — odstraneno.
    """
    if gateway == "stripe":
        stripe_client = get_stripe()
        try:
            status = await stripe_client.get_payment_status(payment_id)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Chyba pri overeni platby: {str(e)}")

        state = status.get("state", "UNKNOWN")
        is_paid = state == "PAID"

        supabase = get_supabase()
        supabase.table("orders").update({
            "status": state,
            "paid_at": datetime.utcnow().isoformat() if is_paid else None,
        }).eq("gopay_payment_id", payment_id).execute()

        return {
            "payment_id": payment_id,
            "state": state,
            "is_paid": is_paid,
            "order_number": status.get("order_number", ""),
            "gateway": "stripe",
        }

    # GOPAY — zakomentovano (cekame na vyjadreni)
    # else:
    #     gopay = get_gopay()
    #     try:
    #         status = await gopay.get_payment_status(int(payment_id))
    #     except Exception as e:
    #         raise HTTPException(status_code=502, detail=f"Chyba: {str(e)}")
    #     state = status.get("state", "UNKNOWN")
    #     is_paid = gopay.is_paid(state)
    #     ...

    else:
        raise HTTPException(status_code=400, detail=f"Nepodporovana brana: {gateway}")


# ========================================================
# GOPAY WEBHOOK — ZAKOMENTOVANO (cekame na vyjadreni)
# ========================================================

# # ── GoPay Webhook ──
#
# @router.post("/webhook")
# @router.get("/webhook")
# async def gopay_webhook(request: Request):
#     """
#     GoPay webhook — notifikace o změně stavu platby.
#     GoPay posílá GET (s ?id=...) i POST (s id=... v body).
#     Zpracovává jednorázové platby, první subscription platby
#     i automatické opakované platby (recurrence).
#     """
#     # GoPay GET: ?id=123  |  POST: id=123 (form-urlencoded)
#     payment_id = request.query_params.get("id")
#     if not payment_id:
#         body = await request.body()
#         params = dict(x.split("=") for x in body.decode().split("&") if "=" in x)
#         payment_id = params.get("id")
#
#     if not payment_id:
#         raise HTTPException(status_code=400, detail="Chybí id platby")
#
#     gopay = get_gopay()
#
#     try:
#         status = await gopay.get_payment_status(int(payment_id))
#     except Exception:
#         raise HTTPException(status_code=502, detail="Nelze ověřit platbu")
#
#     state = status.get("state", "UNKNOWN")
#     is_paid = gopay.is_paid(state)
#
#     supabase = get_supabase()
#
#     # Zkusíme najít existující order
#     existing_order = supabase.table("orders").select("*").eq(
#         "gopay_payment_id", str(int(payment_id))
#     ).execute()
#
#     if existing_order.data:
#         # ── Známý payment — update existující order ──
#         update_data = {"status": state}
#         if is_paid:
#             update_data["paid_at"] = datetime.utcnow().isoformat()
#
#         supabase.table("orders").update(update_data).eq(
#             "gopay_payment_id", str(int(payment_id))
#         ).execute()
#
#         order = existing_order.data[0]
#
#         if is_paid:
#             supabase.table("orders").update({
#                 "activated": True,
#             }).eq("gopay_payment_id", str(int(payment_id))).execute()
#
#             # Server-side analytics: payment_completed (spolehlivější než frontend)
#             track_server_event(
#                 "payment_completed_server",
#                 properties={
#                     "gateway": "gopay",
#                     "payment_id": str(payment_id),
#                     "amount": order.get("amount"),
#                     "plan": order.get("plan"),
#                     "order_number": order.get("order_number"),
#                     "order_type": order.get("order_type"),
#                     "source": "webhook",
#                 },
#                 user_email=order.get("email") or order.get("user_email"),
#             )
#
#             # Aktivace první subscription platby
#             if order.get("order_type") == "subscription":
#                 now = datetime.utcnow()
#                 next_charge = (now + timedelta(days=30)).isoformat()
#                 supabase.table("subscriptions").update({
#                     "status": "active",
#                     "activated_at": now.isoformat(),
#                     "last_charged_at": now.isoformat(),
#                     "next_charge_at": next_charge,
#                     "total_charged": order.get("amount", 0),
#                 }).eq("gopay_parent_payment_id", str(int(payment_id))).execute()
#
#                 logger.info(f"[Payments] Subscription aktivována (payment={payment_id})")
#
#     else:
#         # ── Neznámý payment_id — pravděpodobně automatická recurrence od GoPay ──
#         parent_id = status.get("parent_id") or status.get("preauthorization", {}).get("parent_id")
#
#         if not parent_id:
#             order_number = status.get("order_number", "")
#             logger.info(
#                 f"[Payments] Webhook pro neznámý payment {payment_id}, "
#                 f"order={order_number}, state={state}"
#             )
#
#         sub = None
#         if parent_id:
#             sub_res = supabase.table("subscriptions").select("*").eq(
#                 "gopay_parent_payment_id", str(int(parent_id))
#             ).limit(1).execute()
#             sub = sub_res.data[0] if sub_res.data else None
#
#         if sub and is_paid:
#             rec_order_number = f"AS-REC-{uuid.uuid4().hex[:8].upper()}"
#             supabase.table("orders").insert({
#                 "order_number": rec_order_number,
#                 "gopay_payment_id": str(int(payment_id)),
#                 "plan": sub["plan"],
#                 "amount": sub["amount"],
#                 "email": sub["email"],
#                 "user_email": sub["email"],
#                 "status": state,
#                 "order_type": "subscription_recurrence",
#                 "subscription_id": sub["id"],
#                 "payment_gateway": "gopay",
#                 "activated": True,
#                 "paid_at": datetime.utcnow().isoformat(),
#                 "created_at": datetime.utcnow().isoformat(),
#             }).execute()
#
#             now = datetime.utcnow()
#             next_charge = (now + timedelta(days=30)).isoformat()
#             supabase.table("subscriptions").update({
#                 "last_charged_at": now.isoformat(),
#                 "next_charge_at": next_charge,
#                 "total_charged": (sub.get("total_charged") or 0) + sub["amount"],
#             }).eq("id", sub["id"]).execute()
#
#             # Server-side analytics: subscription recurrence
#             track_server_event(
#                 "payment_completed_server",
#                 properties={
#                     "gateway": "gopay",
#                     "payment_id": str(payment_id),
#                     "amount": sub["amount"],
#                     "plan": sub["plan"],
#                     "order_type": "subscription_recurrence",
#                     "source": "webhook",
#                 },
#                 user_email=sub.get("email"),
#             )
#
#             logger.info(
#                 f"[Payments] Recurrence platba zaznamenána: sub={sub['id']}, "
#                 f"payment={payment_id}, amount={sub['amount']} CZK"
#             )
#         elif not sub:
#             logger.warning(
#                 f"[Payments] Webhook: neznámý payment {payment_id} "
#                 f"bez mapování na order/subscription (state={state})"
#             )
#
#     return {"status": "ok"}
#
#

# ── Stripe Webhook ──

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """
    Stripe webhook — notifikace o změně stavu platby.
    Stripe posílá POST s JSON body + Stripe-Signature header.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    stripe_client = get_stripe()

    try:
        event = stripe_client.verify_webhook(payload, sig_header)
    except Exception as e:
        logger.error(f"[Stripe Webhook] Chyba ověření podpisu: {e}")
        raise HTTPException(status_code=400, detail="Neplatný podpis webhooku")

    event_type = event.get("type", "") if isinstance(event, dict) else event.type

    if event_type == "checkout.session.completed":
        session = event.get("data", {}).get("object", {}) if isinstance(event, dict) else event.data.object

        session_id = session.get("id", "") if isinstance(session, dict) else session.id
        order_number = (
            session.get("client_reference_id", "")
            if isinstance(session, dict)
            else session.client_reference_id
        )
        payment_status = session.get("payment_status", "") if isinstance(session, dict) else session.payment_status

        is_paid = payment_status == "paid"
        state = "PAID" if is_paid else "CREATED"

        supabase = get_supabase()

        # Najít order podle payment_id (session.id)
        existing = supabase.table("orders").select("*").eq(
            "gopay_payment_id", session_id
        ).execute()

        if existing.data:
            update_data = {"status": state}
            if is_paid:
                update_data["paid_at"] = datetime.utcnow().isoformat()
                update_data["activated"] = True
            supabase.table("orders").update(update_data).eq(
                "gopay_payment_id", session_id
            ).execute()

            # Server-side analytics
            if is_paid:
                order = existing.data[0]
                track_server_event(
                    "payment_completed_server",
                    properties={
                        "gateway": "stripe",
                        "payment_id": session_id,
                        "amount": order.get("amount"),
                        "plan": order.get("plan"),
                        "order_number": order.get("order_number"),
                        "source": "webhook",
                    },
                    user_email=order.get("email") or order.get("user_email"),
                )

            logger.info(f"[Stripe Webhook] Platba aktualizována: {session_id} → {state}")
        else:
            logger.warning(f"[Stripe Webhook] Order nenalezen pro session {session_id}")

    elif event_type == "checkout.session.expired":
        session = event.get("data", {}).get("object", {}) if isinstance(event, dict) else event.data.object
        session_id = session.get("id", "") if isinstance(session, dict) else session.id

        supabase = get_supabase()
        supabase.table("orders").update({
            "status": "TIMEOUTED",
        }).eq("gopay_payment_id", session_id).execute()

        logger.info(f"[Stripe Webhook] Session expired: {session_id}")

    # ── Subscription events (P6) ──
    elif event_type == "customer.subscription.created":
        subscription_obj = event.get("data", {}).get("object", {}) if isinstance(event, dict) else event.data.object
        stripe_sub_id = subscription_obj.get("id", "") if isinstance(subscription_obj, dict) else subscription_obj.id
        customer_email = subscription_obj.get("customer_email", "") if isinstance(subscription_obj, dict) else getattr(subscription_obj, "customer_email", "")
        metadata = subscription_obj.get("metadata", {}) if isinstance(subscription_obj, dict) else (subscription_obj.metadata or {})
        plan = metadata.get("plan", "monitoring")
        email = metadata.get("email", customer_email)
        company_id = metadata.get("company_id", "")

        supabase = get_supabase()
        # Find pending subscription and activate it
        pending = supabase.table("subscriptions").select("id").eq(
            "email", email
        ).eq("status", "pending_stripe").order("created_at", desc=True).limit(1).execute()

        if pending.data:
            from datetime import timedelta
            now = datetime.utcnow()
            supabase.table("subscriptions").update({
                "status": "active",
                "stripe_subscription_id": stripe_sub_id,
                "activated_at": now.isoformat(),
                "last_charged_at": now.isoformat(),
                "next_charge_at": (now + timedelta(days=30)).strftime("%Y-%m-%d"),
                "updated_at": now.isoformat(),
            }).eq("id", pending.data[0]["id"]).execute()
            logger.info(f"[Stripe Webhook] Subscription activated: {stripe_sub_id} for {email}")
        else:
            logger.warning(f"[Stripe Webhook] No pending subscription for {email}")

    elif event_type == "invoice.paid":
        invoice_obj = event.get("data", {}).get("object", {}) if isinstance(event, dict) else event.data.object
        stripe_sub_id = invoice_obj.get("subscription", "") if isinstance(invoice_obj, dict) else getattr(invoice_obj, "subscription", "")
        amount_paid = (invoice_obj.get("amount_paid", 0) if isinstance(invoice_obj, dict) else getattr(invoice_obj, "amount_paid", 0)) // 100
        customer_email = invoice_obj.get("customer_email", "") if isinstance(invoice_obj, dict) else getattr(invoice_obj, "customer_email", "")

        if stripe_sub_id:
            supabase = get_supabase()
            sub = supabase.table("subscriptions").select("*").eq(
                "stripe_subscription_id", stripe_sub_id
            ).limit(1).execute()
            if sub.data:
                s = sub.data[0]
                from datetime import timedelta
                now = datetime.utcnow()
                supabase.table("subscriptions").update({
                    "last_charged_at": now.isoformat(),
                    "next_charge_at": (now + timedelta(days=30)).strftime("%Y-%m-%d"),
                    "total_charged": (s.get("total_charged") or 0) + amount_paid,
                    "scans_this_period": 0,  # Reset for new month
                    "reminder_sent_at": None,
                    "updated_at": now.isoformat(),
                }).eq("id", s["id"]).execute()

                # Generate monthly invoice
                try:
                    email = s.get("email", customer_email)
                    from backend.outbound.invoice_pdf import generate_invoice_pdf, build_invoice_email_html
                    from backend.outbound.payment_emails import generate_variable_symbol
                    import base64, os

                    pdf_bytes, inv_number = generate_invoice_pdf(
                        order_number=s.get("order_number", ""),
                        plan=s["plan"],
                        amount=amount_paid or s["amount"],
                        buyer_email=email,
                        paid_at=now.isoformat(),
                    )
                    inv_html = build_invoice_email_html(
                        invoice_number=inv_number, order_number=s.get("order_number", ""),
                        plan=s["plan"], amount=amount_paid or s["amount"],
                    )
                    pdf_b64 = base64.b64encode(pdf_bytes).decode("ascii")
                    pdf_filename = f"faktura-{inv_number}.pdf"

                    await send_email(
                        to=email,
                        subject=f"AIshield.cz — Faktura {inv_number} (monitoring)",
                        html=inv_html,
                        from_email="info@aishield.cz", from_name="AIshield.cz",
                        attachments=[{"filename": pdf_filename, "content": pdf_b64}],
                    )
                    # Save locally
                    year = now.strftime("%Y")
                    local_dir = f"/opt/aishield/invoices/{year}"
                    os.makedirs(local_dir, exist_ok=True)
                    with open(f"{local_dir}/{pdf_filename}", "wb") as f:
                        f.write(pdf_bytes)

                    # DB record
                    supabase.table("invoices").insert({
                        "invoice_number": inv_number,
                        "order_number": s.get("order_number", ""),
                        "company_id": s.get("company_id"),
                        "email": email,
                        "plan": s["plan"],
                        "amount": amount_paid or s["amount"],
                        "pdf_filename": pdf_filename,
                    }).execute()

                    logger.info(f"[Stripe Webhook] Monthly invoice {inv_number} sent for subscription {stripe_sub_id}")
                except Exception as e:
                    logger.error(f"[Stripe Webhook] Monthly invoice failed: {e}", exc_info=True)

    elif event_type == "invoice.payment_failed":
        invoice_obj = event.get("data", {}).get("object", {}) if isinstance(event, dict) else event.data.object
        stripe_sub_id = invoice_obj.get("subscription", "") if isinstance(invoice_obj, dict) else getattr(invoice_obj, "subscription", "")
        customer_email = invoice_obj.get("customer_email", "") if isinstance(invoice_obj, dict) else getattr(invoice_obj, "customer_email", "")

        if stripe_sub_id:
            supabase = get_supabase()
            sub = supabase.table("subscriptions").select("*").eq(
                "stripe_subscription_id", stripe_sub_id
            ).limit(1).execute()
            if sub.data:
                s = sub.data[0]
                await send_email(
                    to=s.get("email", customer_email),
                    subject="AIshield.cz — Platba za monitoring selhala",
                    html=f"<p>Platba za monitoring selhala. Prosím aktualizujte platební údaje v <a href='https://aishield.cz/dashboard#monitoring'>dashboardu</a>.</p>",
                    from_email="info@aishield.cz", from_name="AIshield.cz",
                )
                logger.warning(f"[Stripe Webhook] Payment failed for subscription {stripe_sub_id}")

    elif event_type == "customer.subscription.deleted":
        subscription_obj = event.get("data", {}).get("object", {}) if isinstance(event, dict) else event.data.object
        stripe_sub_id = subscription_obj.get("id", "") if isinstance(subscription_obj, dict) else subscription_obj.id

        supabase = get_supabase()
        supabase.table("subscriptions").update({
            "status": "cancelled",
            "cancelled_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("stripe_subscription_id", stripe_sub_id).execute()
        logger.info(f"[Stripe Webhook] Subscription deleted: {stripe_sub_id}")


    return {"status": "ok"}



# COMGATE WEBHOOK — odstraneno (zadost zamitnuta)

# ────────────────────────────────────────────────────────────
# ADMIN — správa objednávek a potvrzení plateb
# ────────────────────────────────────────────────────────────

@router.get("/admin/orders")
async def admin_list_orders(
    status: str | None = None,
    gateway: str | None = None,
    limit: int = 50,
):
    """
    Seznam všech objednávek pro admin dashboard.
    Volitelné filtry: status, gateway.
    """
    supabase = get_supabase()
    query = supabase.table("orders").select("*").order("created_at", desc=True).limit(limit)

    if status:
        query = query.eq("status", status)
    if gateway:
        query = query.eq("payment_gateway", gateway)

    result = query.execute()
    return {"orders": result.data or [], "total": len(result.data or [])}


@router.get("/admin/orders/stats")
async def admin_orders_stats():
    """
    Souhrn objednávek pro dashboard — celkové příjmy, počet objednávek, čekající platby.
    """
    supabase = get_supabase()
    all_orders = supabase.table("orders").select("*").execute()
    orders = all_orders.data or []

    total_revenue = sum(o["amount"] for o in orders if o.get("status") == "PAID")
    total_orders = len(orders)
    paid_orders = len([o for o in orders if o.get("status") == "PAID"])
    awaiting = [o for o in orders if o.get("status") == "AWAITING_PAYMENT"]
    pending = [o for o in orders if o.get("status") in ("CREATED", "PAYMENT_METHOD_CHOSEN")]

    # Per gateway breakdown
    gateway_stats = {}
    for o in orders:
        gw = o.get("payment_gateway", "unknown")
        if gw not in gateway_stats:
            gateway_stats[gw] = {"total": 0, "paid": 0, "revenue": 0}
        gateway_stats[gw]["total"] += 1
        if o.get("status") == "PAID":
            gateway_stats[gw]["paid"] += 1
            gateway_stats[gw]["revenue"] += o["amount"]

    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "paid_orders": paid_orders,
        "awaiting_payment": len(awaiting),
        "pending_online": len(pending),
        "awaiting_orders": awaiting,
        "gateway_stats": gateway_stats,
    }


class ConfirmPaymentRequest(BaseModel):
    """Request pro potvrzení bankovního převodu."""
    order_number: str
    note: str = ""


@router.post("/admin/orders/confirm-payment")
async def admin_confirm_bank_payment(req: ConfirmPaymentRequest):
    """
    Admin potvrdí, že bankovní převod dorazil.
    Změní status na PAID, odešle konfirmační email klientovi.
    """
    supabase = get_supabase()

    # Najít objednávku
    result = supabase.table("orders").select("*").eq(
        "order_number", req.order_number
    ).limit(1).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail=f"Objednávka {req.order_number} nenalezena")

    order = result.data[0]

    if order["status"] == "PAID":
        raise HTTPException(status_code=400, detail="Objednávka je již zaplacená")

    # Aktualizovat status
    supabase.table("orders").update({
        "status": "PAID",
        "paid_at": datetime.utcnow().isoformat(),
        "activated": True,
    }).eq("order_number", req.order_number).execute()

    # Odeslat email klientovi + fakturu PDF
    invoice_sent = False
    invoice_number = ""
    try:
        # 1) Generate invoice PDF
        from backend.outbound.invoice_pdf import (
            generate_invoice_pdf,
            build_invoice_email_html,
        )
        from backend.outbound.payment_emails import generate_variable_symbol

        billing = order.get("billing_data") or {}
        vs = generate_variable_symbol(order["order_number"])
        paid_at_str = datetime.utcnow().isoformat()

        pdf_bytes, invoice_number = generate_invoice_pdf(
            order_number=order["order_number"],
            plan=order["plan"],
            amount=order["amount"],
            buyer_name=billing.get("company", ""),
            buyer_ico=billing.get("ico", ""),
            buyer_dic=billing.get("dic", ""),
            buyer_street=billing.get("street", ""),
            buyer_city=billing.get("city", ""),
            buyer_zip=billing.get("zip", ""),
            buyer_email=order.get("email", ""),
            paid_at=paid_at_str,
            created_at=order.get("created_at"),
            variable_symbol=vs,
        )

        # 2) Build invoice email with PDF attachment
        invoice_html = build_invoice_email_html(
            invoice_number=invoice_number,
            order_number=order["order_number"],
            plan=order["plan"],
            amount=order["amount"],
        )

        import base64
        pdf_b64 = base64.b64encode(pdf_bytes).decode("ascii")
        attachments = [{
            "filename": f"faktura-{invoice_number}.pdf",
            "content": pdf_b64,
        }]

        await send_email(
            to=order["email"],
            subject=f"AIshield.cz — Faktura {invoice_number}",
            html=invoice_html,
            from_email="info@aishield.cz",
            from_name="AIshield.cz",
            attachments=attachments,
        )
        invoice_sent = True
        logger.info(f"[Admin] Invoice {invoice_number} sent to {order['email']} ({len(pdf_bytes)} bytes PDF)")

        # 3) Save PDF to Supabase Storage
        pdf_url = ""
        pdf_filename = f"faktura-{invoice_number}.pdf"
        try:
            from backend.documents.pdf_generator import save_pdf_to_supabase
            company_id = order.get("company_id") or "no-company"
            pdf_url = save_pdf_to_supabase(
                pdf_bytes=pdf_bytes,
                filename=pdf_filename,
                client_id=f"invoices/{company_id}",
                bucket="documents",
            )
            logger.info(f"[Admin] Invoice PDF saved to Supabase Storage: {pdf_url}")
        except Exception as e:
            logger.error(f"[Admin] Failed to save invoice to Supabase Storage: {e}")

        # 4) Save PDF locally on VPS disk
        try:
            import os
            year = datetime.utcnow().strftime("%Y")
            local_dir = f"/opt/aishield/invoices/{year}"
            os.makedirs(local_dir, exist_ok=True)
            local_path = f"{local_dir}/{pdf_filename}"
            with open(local_path, "wb") as f:
                f.write(pdf_bytes)
            logger.info(f"[Admin] Invoice PDF saved locally: {local_path}")
        except Exception as e:
            logger.error(f"[Admin] Failed to save invoice locally: {e}")

        # 5) Insert record into invoices table
        try:
            supabase.table("invoices").insert({
                "invoice_number": invoice_number,
                "order_number": order["order_number"],
                "company_id": order.get("company_id"),
                "email": order.get("email", ""),
                "plan": order.get("plan", ""),
                "amount": order.get("amount", 0),
                "buyer_name": billing.get("company", ""),
                "buyer_ico": billing.get("ico", ""),
                "pdf_url": pdf_url,
                "pdf_filename": pdf_filename,
            }).execute()
            logger.info(f"[Admin] Invoice record inserted: {invoice_number}")
        except Exception as e:
            logger.error(f"[Admin] Failed to insert invoice record: {e}")

        # 6) Send invoice copy to admin email
        try:
            await send_email(
                to="info@aishield.cz",
                subject=f"[KOPIE] Faktura {invoice_number} — {order.get('email', '')}",
                html=invoice_html,
                from_email="info@aishield.cz",
                from_name="AIshield.cz",
                attachments=attachments,
            )
            logger.info(f"[Admin] Invoice copy sent to info@aishield.cz")
        except Exception as e:
            logger.error(f"[Admin] Failed to send invoice copy to admin: {e}")

    except Exception as e:
        logger.error(f"[Admin] Failed to generate/send invoice: {e}", exc_info=True)

    # 7) Also send payment received email (without invoice)
    try:
        html = build_payment_received_email(
            order_number=order["order_number"],
            plan=order["plan"],
            amount=order["amount"],
        )
        await send_email(
            to=order["email"],
            subject=f"AIshield.cz — Platba přijata — {order['order_number']}",
            html=html,
            from_email="info@aishield.cz",
            from_name="AIshield.cz",
        )
        logger.info(f"[Admin] Payment received email sent to {order['email']} for {order['order_number']}")
    except Exception as e:
        logger.error(f"[Admin] Failed to send payment received email: {e}")

    return {
        "status": "confirmed",
        "order_number": req.order_number,
        "email_sent": True,
        "invoice_sent": invoice_sent,
        "invoice_number": invoice_number,
        "message": f"Objednávka {req.order_number} potvrzena, email odeslán na {order['email']}",
    }


# ── Order status update ──


class UpdateOrderStatusRequest(BaseModel):
    status: str


@router.patch("/admin/orders/{order_number}/status")
async def admin_update_order_status(order_number: str, req: UpdateOrderStatusRequest):
    """Admin změní status objednávky."""
    allowed = {"AWAITING_PAYMENT", "PAID", "CANCELLED", "REFUNDED", "EXPIRED"}
    if req.status not in allowed:
        raise HTTPException(status_code=400, detail=f"Nepovolený status. Povolené: {', '.join(sorted(allowed))}")

    supabase = get_supabase()
    result = supabase.table("orders").select("id").eq("order_number", order_number).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail=f"Objednávka {order_number} nenalezena")

    update_data: dict = {"status": req.status, "updated_at": datetime.utcnow().isoformat()}
    if req.status == "PAID":
        update_data["paid_at"] = datetime.utcnow().isoformat()
        update_data["activated"] = True

    supabase.table("orders").update(update_data).eq("order_number", order_number).execute()
    logger.info(f"[Admin] Order {order_number} status → {req.status}")
    return {"status": "updated", "order_number": order_number, "new_status": req.status}


@router.delete("/admin/orders/{order_number}")
async def admin_delete_order(order_number: str):
    """Admin smaže objednávku."""
    supabase = get_supabase()
    result = supabase.table("orders").select("id").eq("order_number", order_number).limit(1).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail=f"Objednávka {order_number} nenalezena")

    supabase.table("orders").delete().eq("order_number", order_number).execute()
    logger.info(f"[Admin] Order {order_number} deleted")
    return {"status": "deleted", "order_number": order_number}


# ── Resend invoice ──


@router.post("/admin/orders/{order_number}/resend-invoice")
async def admin_resend_invoice(order_number: str):
    """Admin znovu odešle fakturu emailem."""
    supabase = get_supabase()
    order_res = supabase.table("orders").select("*").eq("order_number", order_number).limit(1).execute()
    if not order_res.data:
        raise HTTPException(status_code=404, detail=f"Objednávka {order_number} nenalezena")

    order = order_res.data[0]
    if order["status"] not in ("PAID", "paid"):
        raise HTTPException(status_code=400, detail="Fakturu lze odeslat pouze pro zaplacené objednávky")

    # Find existing invoice
    inv_res = supabase.table("invoices").select("*").eq("order_number", order_number).limit(1).execute()
    if not inv_res.data:
        raise HTTPException(status_code=404, detail="Faktura nebyla nalezena. Zkuste nejprve potvrdit platbu.")

    inv = inv_res.data[0]
    pdf_url = inv.get("pdf_url", "")

    # Try to get PDF from storage
    pdf_bytes = None
    if pdf_url:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(pdf_url, timeout=15)
                if resp.status_code == 200:
                    pdf_bytes = resp.content
        except Exception as e:
            logger.warning(f"[Admin] Failed to download invoice PDF from storage: {e}")

    # Fallback: try local file
    if not pdf_bytes:
        try:
            import os
            year = order.get("created_at", "")[:4] or datetime.utcnow().strftime("%Y")
            local_path = f"/opt/aishield/invoices/{year}/{inv.get('pdf_filename', '')}"
            if os.path.exists(local_path):
                with open(local_path, "rb") as f:
                    pdf_bytes = f.read()
        except Exception as e:
            logger.warning(f"[Admin] Failed to read local invoice PDF: {e}")

    if not pdf_bytes:
        raise HTTPException(status_code=404, detail="PDF faktury nelze najít")

    import base64
    from backend.outbound.invoice_pdf import build_invoice_email_html

    invoice_html = build_invoice_email_html(
        invoice_number=inv.get("invoice_number", ""),
        order_number=order_number,
        plan=order.get("plan", ""),
        amount=order.get("amount", 0),
    )

    pdf_b64 = base64.b64encode(pdf_bytes).decode("ascii")
    attachments = [{
        "filename": f"faktura-{inv.get('invoice_number', order_number)}.pdf",
        "content": pdf_b64,
    }]

    from backend.outbound.email_engine import send_email
    await send_email(
        to=order["email"],
        subject=f"AIshield.cz — Faktura {inv.get('invoice_number', '')}",
        html=invoice_html,
        from_email="info@aishield.cz",
        from_name="AIshield.cz",
        attachments=attachments,
    )

    logger.info(f"[Admin] Invoice {inv.get('invoice_number')} resent to {order['email']}")
    return {"status": "sent", "email": order["email"], "invoice_number": inv.get("invoice_number")}
