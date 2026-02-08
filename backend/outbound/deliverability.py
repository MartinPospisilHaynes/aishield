"""
AIshield.cz — Email Deliverability Guard
Ochrana domény před spam blacklistem.

Systémy:
1. Bounce tracking — neposílat na mrtvé adresy
2. Complaint tracking — nikdy znovu firmě co nahlásila spam
3. Spam rate monitoring — auto-stop kampaně při rate > 0.1%
4. Domain warm-up — postupné zvyšování denního limitu
5. Per-domain rate limit — max N emailů na stejnou doménu/den
"""

from datetime import datetime, timedelta
from backend.database import get_supabase


# ── Konfigurace ──

# Spam rate threshold — nad tímto se kampaň zastaví
SPAM_RATE_THRESHOLD = 0.001    # 0.1% — Resend doporučuje max 0.3%
BOUNCE_RATE_THRESHOLD = 0.05   # 5% — příliš mnoho bounces = špatná data

# Per-domain limit (aby to nevypadalo jako spam na jednu firmu)
MAX_EMAILS_PER_DOMAIN_PER_DAY = 5

# Warm-up schedule: den → max emailů
# Nová doména potřebuje 4-6 týdnů warm-upu
WARMUP_SCHEDULE = {
    # Týden 1: opatrně
    1: 20, 2: 30, 3: 40, 4: 50, 5: 60, 6: 70, 7: 80,
    # Týden 2: zvyšujeme
    8: 100, 9: 120, 10: 140, 11: 160, 12: 180, 13: 200, 14: 250,
    # Týden 3: solidní objem
    15: 300, 16: 350, 17: 400, 18: 450, 19: 500, 20: 500, 21: 500,
    # Týden 4+: plný výkon
    22: 600, 23: 700, 24: 800, 25: 900, 26: 1000, 27: 1000, 28: 1000,
}
# Po 28. dni = max 1000/den (Resend Pro limit s rezervou)
MAX_DAILY_AFTER_WARMUP = 1000


def get_warmup_limit(campaign_start_date: str | None = None) -> int:
    """
    Vrátí aktuální denní limit na základě warm-up fáze.
    campaign_start_date: ISO datum kdy jsme začali posílat.
    """
    if not campaign_start_date:
        return WARMUP_SCHEDULE.get(1, 20)  # Den 1 default

    try:
        start = datetime.fromisoformat(campaign_start_date)
        days_active = (datetime.utcnow() - start).days + 1
    except (ValueError, TypeError):
        return 20

    if days_active <= 0:
        return 20
    if days_active > 28:
        return MAX_DAILY_AFTER_WARMUP

    return WARMUP_SCHEDULE.get(days_active, MAX_DAILY_AFTER_WARMUP)


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
    Vrátí zdravotní metriky emailové kampaně.
    Pokud jsou špatné → zastavit kampaň.
    """
    supabase = get_supabase()
    last_30_days = (datetime.utcnow() - timedelta(days=30)).isoformat()
    today = datetime.utcnow().date().isoformat()

    # Celkem odesláno za 30 dní
    sent_res = supabase.table("email_log").select(
        "id", count="exact"
    ).gte("sent_at", last_30_days).in_(
        "status", ["sent", "delivered", "opened", "clicked"]
    ).execute()
    total_sent = sent_res.count or 0

    # Bounces za 30 dní
    bounces_res = supabase.table("email_events").select(
        "id", count="exact"
    ).eq("event_type", "bounce").gte(
        "created_at", last_30_days
    ).execute()
    total_bounces = bounces_res.count or 0

    # Complaints za 30 dní
    complaints_res = supabase.table("email_events").select(
        "id", count="exact"
    ).eq("event_type", "complaint").gte(
        "created_at", last_30_days
    ).execute()
    total_complaints = complaints_res.count or 0

    # Odesláno dnes
    today_res = supabase.table("email_log").select(
        "id", count="exact"
    ).gte("sent_at", today).execute()
    sent_today = today_res.count or 0

    # Výpočet rates
    spam_rate = (total_complaints / total_sent) if total_sent > 0 else 0
    bounce_rate = (total_bounces / total_sent) if total_sent > 0 else 0

    # Warm-up limit
    campaign_start = await get_campaign_start_date()
    warmup_limit = get_warmup_limit(campaign_start)

    # Zdravotní status
    is_healthy = (
        spam_rate < SPAM_RATE_THRESHOLD
        and bounce_rate < BOUNCE_RATE_THRESHOLD
    )

    can_send = is_healthy and (sent_today < warmup_limit)

    return {
        "total_sent_30d": total_sent,
        "bounces_30d": total_bounces,
        "complaints_30d": total_complaints,
        "spam_rate": round(spam_rate, 4),
        "bounce_rate": round(bounce_rate, 4),
        "sent_today": sent_today,
        "warmup_limit": warmup_limit,
        "remaining_today": max(0, warmup_limit - sent_today),
        "campaign_start": campaign_start,
        "is_healthy": is_healthy,
        "can_send": can_send,
        "warnings": _get_warnings(spam_rate, bounce_rate, sent_today, warmup_limit),
    }


def _get_warnings(
    spam_rate: float,
    bounce_rate: float,
    sent_today: int,
    warmup_limit: int,
) -> list[str]:
    """Generuje varování pro admin dashboard."""
    warnings = []

    if spam_rate >= SPAM_RATE_THRESHOLD:
        warnings.append(
            f"🚨 KRITICKÉ: Spam rate {spam_rate:.2%} překročil threshold "
            f"{SPAM_RATE_THRESHOLD:.2%} — kampaň ZASTAVENA!"
        )
    elif spam_rate >= SPAM_RATE_THRESHOLD * 0.5:
        warnings.append(
            f"⚠️ Spam rate {spam_rate:.2%} se blíží limitu — sledovat!"
        )

    if bounce_rate >= BOUNCE_RATE_THRESHOLD:
        warnings.append(
            f"🚨 KRITICKÉ: Bounce rate {bounce_rate:.2%} překročil threshold "
            f"{BOUNCE_RATE_THRESHOLD:.2%} — zkontrolovat kvalitu dat!"
        )
    elif bounce_rate >= BOUNCE_RATE_THRESHOLD * 0.5:
        warnings.append(
            f"⚠️ Bounce rate {bounce_rate:.2%} se blíží limitu."
        )

    if sent_today >= warmup_limit:
        warnings.append(
            f"📊 Denní warm-up limit dosažen ({sent_today}/{warmup_limit})"
        )

    if not warnings:
        warnings.append("✅ Vše v pořádku — doména zdravá")

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
