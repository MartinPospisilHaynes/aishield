"""
AIshield.cz — Email Deliverability Guard (Adaptivní)
Ochrana domény před spam blacklistem — plně autonomní.

Princip:
- ŽÁDNÝ fixní warm-up schedule
- Adaptivní throttling dle reálných metrik (bounce, complaint, open rate)
- Pokud je doména čistá → agresivně škáluje nahoru (2x/den)
- Pokud přijde stížnost → okamžitá brzda (30-50% snížení)
- Pokud spam rate překročí práh → STOP (0 emailů)

Při čistém startu: 50 → 100 → 200 → 400 → 800 → 1000 (max za ~6 dní)
"""

from datetime import datetime, timedelta
from backend.database import get_supabase


# ── Konfigurace ──

START_LIMIT = 50             # Startovací denní limit (nová kampaň)
MIN_LIMIT = 10               # Minimum (i při brzdění)
MAX_LIMIT = 1000             # Maximum (Resend Pro ≈ 1600/den, necháváme rezervu)

# Per-domain limit (aby to nevypadalo jako spam na jednu firmu)
MAX_EMAILS_PER_DOMAIN_PER_DAY = 5

# Thresholdy pro EMERGENCY STOP
SPAM_RATE_STOP = 0.001       # 0.1% → STOP kompletně
SPAM_RATE_BRAKE = 0.0005     # 0.05% → brzda na 30%
BOUNCE_RATE_HARD_BRAKE = 0.05  # 5% → brzda na 50%
BOUNCE_RATE_SOFT_BRAKE = 0.03  # 3% → brzda na 80%


# ── Adaptivní Limit ──


async def get_campaign_start_date() -> str | None:
    """Zjistí kdy byla odeslána první kampaň."""
    supabase = get_supabase()
    res = supabase.table("email_log").select(
        "sent_at"
    ).eq("status", "sent").order(
        "sent_at", desc=False
    ).limit(1).execute()

    if res.data:
        return res.data[0]["sent_at"]
    return None


async def compute_adaptive_limit() -> dict:
    """
    Adaptivní throttling — limit se mění dle zdraví domény.
    Vrací {"limit": int, "reason": str, "mode": str, "metrics": dict}
    """
    supabase = get_supabase()
    today = datetime.utcnow().date()
    today_str = today.isoformat()

    # Kdy jsme začali posílat?
    campaign_start = await get_campaign_start_date()
    if not campaign_start:
        return {
            "limit": START_LIMIT,
            "reason": "Nová kampaň — startovní limit",
            "mode": "startup",
            "metrics": {},
        }

    start_date = datetime.fromisoformat(campaign_start).date()
    days_active = (today - start_date).days + 1

    # Prvních 2 dny: opatrně
    if days_active <= 2:
        return {
            "limit": START_LIMIT,
            "reason": f"Den {days_active} — startovní fáze",
            "mode": "startup",
            "metrics": {"days_active": days_active},
        }

    # Kolik jsme poslali včera?
    yesterday = (today - timedelta(days=1)).isoformat()
    yesterday_res = supabase.table("email_log").select(
        "id", count="exact"
    ).gte("sent_at", yesterday).lt(
        "sent_at", today_str
    ).in_("status", ["sent", "delivered", "opened", "clicked"]).execute()
    yesterday_sent = yesterday_res.count or 0

    # Base: včerejší objem (nebo START_LIMIT pokud jsme nic neposlali)
    base = max(yesterday_sent, START_LIMIT)

    # 7-day rolling metrics
    week_ago = (today - timedelta(days=7)).isoformat()

    sent_7d_res = supabase.table("email_log").select(
        "id", count="exact"
    ).gte("sent_at", week_ago).in_(
        "status", ["sent", "delivered", "opened", "clicked"]
    ).execute()
    sent_7d = sent_7d_res.count or 0

    bounces_7d_res = supabase.table("email_events").select(
        "id", count="exact"
    ).eq("event_type", "bounce").gte("created_at", week_ago).execute()
    bounces_7d = bounces_7d_res.count or 0

    complaints_7d_res = supabase.table("email_events").select(
        "id", count="exact"
    ).eq("event_type", "complaint").gte("created_at", week_ago).execute()
    complaints_7d = complaints_7d_res.count or 0

    # "opened" statuses = opened + clicked
    opens_7d_res = supabase.table("email_log").select(
        "id", count="exact"
    ).gte("sent_at", week_ago).in_(
        "status", ["opened", "clicked"]
    ).execute()
    opens_7d = opens_7d_res.count or 0

    # Rates
    bounce_rate = bounces_7d / sent_7d if sent_7d > 0 else 0
    complaint_rate = complaints_7d / sent_7d if sent_7d > 0 else 0
    open_rate = opens_7d / sent_7d if sent_7d > 0 else 0

    metrics = {
        "days_active": days_active,
        "yesterday_sent": yesterday_sent,
        "sent_7d": sent_7d,
        "bounced_7d": bounces_7d,
        "complained_7d": complaints_7d,
        "opened_7d": opens_7d,
        "bounce_rate": round(bounce_rate, 4),
        "complaint_rate": round(complaint_rate, 4),
        "open_rate": round(open_rate, 4),
    }

    # ── Rozhodovací strom ──

    # 1. EMERGENCY STOP — spam rate >= 0.1%
    if complaint_rate >= SPAM_RATE_STOP:
        return {
            "limit": 0,
            "reason": f"🚨 EMERGENCY STOP — spam rate {complaint_rate:.2%} >= {SPAM_RATE_STOP:.2%}",
            "mode": "stopped",
            "metrics": metrics,
        }

    # 2. HARD BRAKE — spam rate >= 0.05%
    if complaint_rate >= SPAM_RATE_BRAKE:
        new_limit = max(MIN_LIMIT, int(base * 0.3))
        return {
            "limit": new_limit,
            "reason": f"⚠️ Stížnosti {complaint_rate:.2%} — brzda na 30% ({new_limit})",
            "mode": "braking",
            "metrics": metrics,
        }

    # 3. HARD BRAKE — bounce rate >= 5%
    if bounce_rate >= BOUNCE_RATE_HARD_BRAKE:
        new_limit = max(MIN_LIMIT, int(base * 0.5))
        return {
            "limit": new_limit,
            "reason": f"⚠️ Bounce rate {bounce_rate:.2%} — brzda na 50% ({new_limit})",
            "mode": "braking",
            "metrics": metrics,
        }

    # 4. SOFT BRAKE — bounce rate >= 3%
    if bounce_rate >= BOUNCE_RATE_SOFT_BRAKE:
        new_limit = max(MIN_LIMIT, int(base * 0.8))
        return {
            "limit": new_limit,
            "reason": f"Bounce rate {bounce_rate:.2%} — mírná brzda ({new_limit})",
            "mode": "braking",
            "metrics": metrics,
        }

    # 5. BOOST — bounce < 1%, 0 stížností, open rate > 20%
    if bounce_rate < 0.01 and complaints_7d == 0 and open_rate > 0.20:
        new_limit = min(MAX_LIMIT, int(base * 2.0))
        return {
            "limit": new_limit,
            "reason": f"🚀 Výborné metriky (open {open_rate:.0%}, bounce {bounce_rate:.1%}) — 2x boost → {new_limit}",
            "mode": "accelerating",
            "metrics": metrics,
        }

    # 6. ACCELERATE — bounce < 2%, 0 stížností, open rate > 10%
    if bounce_rate < 0.02 and complaints_7d == 0 and open_rate > 0.10:
        new_limit = min(MAX_LIMIT, int(base * 1.5))
        return {
            "limit": new_limit,
            "reason": f"✅ Zdravé metriky (open {open_rate:.0%}) — 1.5x → {new_limit}",
            "mode": "accelerating",
            "metrics": metrics,
        }

    # 7. MILD ACCELERATE — bounce < 3%, 0 stížností
    if bounce_rate < 0.03 and complaints_7d == 0:
        new_limit = min(MAX_LIMIT, int(base * 1.3))
        return {
            "limit": new_limit,
            "reason": f"OK metriky — 1.3x → {new_limit}",
            "mode": "cruising",
            "metrics": metrics,
        }

    # 8. HOLD — udržet aktuální úroveň
    return {
        "limit": base,
        "reason": "Udržuji aktuální úroveň",
        "mode": "cruising",
        "metrics": metrics,
    }


# ── Bounce & Complaint Tracking ──


async def process_resend_webhook(event: dict) -> dict:
    """
    Zpracuje webhook od Resend.
    Resend posílá: delivered, opened, clicked, bounced, complained, unsubscribed

    KRITICKÉ eventy:
    - bounced → označit email jako mrtvý
    - complained → blacklistovat firmu NAVŽDY
    """
    supabase = get_supabase()
    event_type = event.get("type", "")
    data = event.get("data", {})
    email_to = data.get("to", [""])[0] if isinstance(data.get("to"), list) else data.get("to", "")
    resend_id = data.get("email_id", "")

    result = {"event": event_type, "handled": False}

    if event_type == "email.bounced":
        # BOUNCE — email neexistuje nebo odmítnut
        bounce_type = data.get("bounce", {}).get("type", "")  # hard / soft

        # Zalogovat
        supabase.table("email_events").insert({
            "resend_id": resend_id,
            "to_email": email_to,
            "event_type": "bounce",
            "bounce_type": bounce_type,
            "raw_data": event,
            "created_at": datetime.utcnow().isoformat(),
        }).execute()

        if bounce_type == "hard":
            # Hard bounce = email neexistuje → nikdy znovu
            supabase.table("companies").update({
                "prospecting_status": "email_invalid",
                "email_valid": False,
            }).eq("email", email_to).execute()

        result["handled"] = True
        result["action"] = f"bounce_{bounce_type}"

    elif event_type == "email.complained":
        # COMPLAINT — příjemce klikl "spam" → BLACKLIST navždy
        supabase.table("email_events").insert({
            "resend_id": resend_id,
            "to_email": email_to,
            "event_type": "complaint",
            "raw_data": event,
            "created_at": datetime.utcnow().isoformat(),
        }).execute()

        # Blacklistovat firmu
        supabase.table("companies").update({
            "prospecting_status": "spam_reported",
        }).eq("email", email_to).execute()

        # Přidat do globálního blacklistu
        supabase.table("email_blacklist").insert({
            "email": email_to,
            "reason": "spam_complaint",
            "created_at": datetime.utcnow().isoformat(),
        }).execute()

        result["handled"] = True
        result["action"] = "blacklisted"

    elif event_type == "email.delivered":
        # Úspěšně doručeno
        supabase.table("email_log").update({
            "status": "delivered",
        }).eq("resend_id", resend_id).execute()

        result["handled"] = True

    elif event_type == "email.opened":
        # Otevřeno — zalogovat pro statistiky
        supabase.table("email_log").update({
            "status": "opened",
            "opened_at": datetime.utcnow().isoformat(),
        }).eq("resend_id", resend_id).execute()

        result["handled"] = True

    elif event_type == "email.clicked":
        # Kliknuto na odkaz
        supabase.table("email_log").update({
            "status": "clicked",
            "clicked_at": datetime.utcnow().isoformat(),
        }).eq("resend_id", resend_id).execute()

        result["handled"] = True

    return result


# ── Spam Rate Monitoring ──


async def get_email_health() -> dict:
    """
    Vrátí kompletní zdravotní report emailové kampaně.
    Používá adaptivní limit místo fixního warm-up schedule.
    """
    supabase = get_supabase()
    today = datetime.utcnow().date().isoformat()

    # Adaptivní limit
    adaptive = await compute_adaptive_limit()
    daily_limit = adaptive["limit"]

    # Odesláno dnes
    today_res = supabase.table("email_log").select(
        "id", count="exact"
    ).gte("sent_at", today).execute()
    sent_today = today_res.count or 0

    # Blacklisted count
    bl_res = supabase.table("email_blacklist").select(
        "id", count="exact"
    ).execute()
    blacklisted_count = bl_res.count or 0

    # Unsubscribed count
    unsub_res = supabase.table("companies").select(
        "id", count="exact"
    ).eq("prospecting_status", "unsubscribed").execute()
    unsubscribed_count = unsub_res.count or 0

    metrics = adaptive.get("metrics", {})
    bounce_rate = metrics.get("bounce_rate", 0)
    complaint_rate = metrics.get("complaint_rate", 0)
    open_rate = metrics.get("open_rate", 0)

    # Zdravotní status
    is_healthy = adaptive["mode"] != "stopped"
    can_send = is_healthy and (sent_today < daily_limit) and daily_limit > 0

    # Varování
    warnings = _get_warnings(adaptive, sent_today)

    return {
        # Adaptive info
        "mode": adaptive["mode"],
        "adjustment_reason": adaptive["reason"],
        "days_active": metrics.get("days_active", 0),
        # Limity
        "daily_limit": daily_limit,
        "sent_today": sent_today,
        "remaining_today": max(0, daily_limit - sent_today),
        # 7-day rolling metrics
        "sent_7d": metrics.get("sent_7d", 0),
        "bounced_7d": metrics.get("bounced_7d", 0),
        "complained_7d": metrics.get("complained_7d", 0),
        "opened_7d": metrics.get("opened_7d", 0),
        "bounce_rate": round(bounce_rate, 4),
        "complaint_rate": round(complaint_rate, 4),
        "open_rate": round(open_rate, 4),
        # Totals
        "blacklisted_count": blacklisted_count,
        "unsubscribed_count": unsubscribed_count,
        # Status
        "is_healthy": is_healthy,
        "can_send": can_send,
        "warnings": warnings,
    }


def _get_warnings(adaptive: dict, sent_today: int) -> list[str]:
    """Generuje varování pro admin dashboard."""
    warnings = []
    mode = adaptive["mode"]
    metrics = adaptive.get("metrics", {})
    bounce_rate = metrics.get("bounce_rate", 0)
    complaint_rate = metrics.get("complaint_rate", 0)
    limit = adaptive["limit"]

    if mode == "stopped":
        warnings.append(
            f"🚨 EMERGENCY STOP — spam rate {complaint_rate:.2%} → odesílání ZASTAVENO!"
        )
    elif mode == "braking":
        warnings.append(
            f"⚠️ {adaptive['reason']}"
        )

    if bounce_rate >= 0.03 and mode != "stopped":
        warnings.append(
            f"📊 Bounce rate {bounce_rate:.2%} — kontrolujte kvalitu emailových adres"
        )

    if sent_today >= limit and limit > 0:
        warnings.append(
            f"📊 Denní limit dosažen ({sent_today}/{limit})"
        )

    if mode == "accelerating":
        warnings.append(
            f"🚀 Adaptivní škálování — {adaptive['reason']}"
        )

    if not warnings:
        warnings.append(
            f"✅ Doména zdravá — režim: {mode}, limit: {limit}/den"
        )

    return warnings


# ── Per-domain rate limiting ──


async def check_domain_limit(email: str) -> bool:
    """
    Zkontroluje, jestli jsme nepřekročili limit emailů
    na stejnou emailovou doménu za den.
    Např. max 5 emailů na @firma.cz/den.
    """
    domain = email.split("@")[1].lower() if "@" in email else ""
    if not domain:
        return False

    supabase = get_supabase()
    today = datetime.utcnow().date().isoformat()

    res = supabase.table("email_log").select(
        "id", count="exact"
    ).ilike(
        "to_email", f"%@{domain}"
    ).gte("sent_at", today).execute()

    count = res.count or 0
    return count < MAX_EMAILS_PER_DOMAIN_PER_DAY


async def is_email_blacklisted(email: str) -> bool:
    """Zkontroluje jestli je email na blacklistu."""
    supabase = get_supabase()
    res = supabase.table("email_blacklist").select(
        "id"
    ).eq("email", email.lower()).limit(1).execute()
    return bool(res.data)
