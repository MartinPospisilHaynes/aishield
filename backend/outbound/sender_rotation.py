"""
AIshield.cz — Multi-Sender Rotation & Auto-Failover
=====================================================
3 nezávislé odesílací adresy, každá s vlastní reputací.
Pokud jedna spadne (blokace, příliš stížností) → automaticky přepne na další.

Odesílatelé:
  1. info@aishield.cz     — primární (výchozí)
  2. servis@aishield.cz   — záloha 1
  3. podpora@aishield.cz  — záloha 2

Strategie:
- Round-robin distribuce (rovnoměrné rozložení zátěže)
- Každý sender má vlastní denní limit (nezávislý warm-up)
- Pokud sender překročí bounce/complaint práh → automaticky pozastaven
- Pozastavení na 24h, pak se zkusí znovu
- Health index 0-100 pro každého sendera
"""

from datetime import datetime, timedelta
from backend.database import get_supabase

# ── Konfigurace senderů ──

# Všechny 3 adresy musejí být ověřeny v Resend dashboardu.
SENDERS = [
    {
        "email": "info@aishield.cz",
        "name": "AIshield.cz",
        "priority": 1,
    },
]

# Limity per sender (nezávislé na globálním limitu)
SENDER_START_LIMIT = 30          # Každý sender začíná na 30/den
SENDER_MAX_LIMIT = 300           # Max per sender = 300/den
SENDER_MIN_LIMIT = 5

# Prahy pro pozastavení senderu
SENDER_COMPLAINT_PAUSE = 0.001   # 0.1% stížností → pauza 24h
SENDER_BOUNCE_PAUSE = 0.08       # 8% bounce → pauza 24h
SENDER_PAUSE_HOURS = 24          # Jak dlouho je sender pozastaven

# Health index (0-100)
HEALTH_CRITICAL = 30             # Pod 30 → sender pozastaven
HEALTH_WARNING = 60              # Pod 60 → menší objem


# ── Sender Health ──


async def get_sender_stats(sender_email: str, days: int = 7) -> dict:
    """Vrátí statistiky odesílatele za posledních N dní."""
    supabase = get_supabase()
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    today = datetime.utcnow().date().isoformat()

    # Odesláno za období
    sent_res = supabase.table("email_log").select(
        "id", count="exact"
    ).eq("from_email", sender_email).gte(
        "sent_at", since
    ).in_("status", ["sent", "delivered", "opened", "clicked"]).execute()
    sent = sent_res.count or 0

    # Odesláno dnes
    today_res = supabase.table("email_log").select(
        "id", count="exact"
    ).eq("from_email", sender_email).gte("sent_at", today).execute()
    sent_today = today_res.count or 0

    # Bounces
    bounces_res = supabase.table("email_events").select(
        "id", count="exact"
    ).eq("from_email", sender_email).eq(
        "event_type", "bounce"
    ).gte("created_at", since).execute()
    bounces = bounces_res.count or 0

    # Complaints
    complaints_res = supabase.table("email_events").select(
        "id", count="exact"
    ).eq("from_email", sender_email).eq(
        "event_type", "complaint"
    ).gte("created_at", since).execute()
    complaints = complaints_res.count or 0

    # Opens
    opens_res = supabase.table("email_log").select(
        "id", count="exact"
    ).eq("from_email", sender_email).gte(
        "sent_at", since
    ).in_("status", ["opened", "clicked"]).execute()
    opens = opens_res.count or 0

    bounce_rate = bounces / sent if sent > 0 else 0
    complaint_rate = complaints / sent if sent > 0 else 0
    open_rate = opens / sent if sent > 0 else 0

    return {
        "sender": sender_email,
        "sent_7d": sent,
        "sent_today": sent_today,
        "bounces_7d": bounces,
        "complaints_7d": complaints,
        "opens_7d": opens,
        "bounce_rate": round(bounce_rate, 4),
        "complaint_rate": round(complaint_rate, 4),
        "open_rate": round(open_rate, 4),
    }


def compute_health_index(stats: dict) -> int:
    """
    Vypočítá Health Index senderu (0-100).

    100 = perfektní (0 bounces, 0 stížností, vysoký open rate)
    0   = katastrofa (hodně stížností)

    Výpočet:
    - Start: 100
    - Complaint rate 0.05%+ → -40
    - Complaint rate 0.1%+  → -80 (efektivně mrtvý)
    - Bounce rate 3%+       → -15
    - Bounce rate 5%+       → -30
    - Open rate < 10%       → -10
    - Open rate > 20%       → +5 (bonus)
    """
    score = 100
    complaint_rate = stats.get("complaint_rate", 0)
    bounce_rate = stats.get("bounce_rate", 0)
    open_rate = stats.get("open_rate", 0)

    # Stížnosti — nejvíc nebezpečné
    if complaint_rate >= 0.001:     # >= 0.1%
        score -= 80
    elif complaint_rate >= 0.0005:  # >= 0.05%
        score -= 40
    elif complaint_rate > 0:
        score -= 20

    # Bounce rate
    if bounce_rate >= 0.05:         # >= 5%
        score -= 30
    elif bounce_rate >= 0.03:       # >= 3%
        score -= 15
    elif bounce_rate >= 0.01:       # >= 1%
        score -= 5

    # Open rate
    if open_rate > 0.20:
        score += 5  # Bonus za vysoké otevírání
    elif open_rate < 0.10 and stats.get("sent_7d", 0) > 20:
        score -= 10  # Penalizace za nízké otevírání (pouze pokud máme dost dat)

    return max(0, min(100, score))


async def get_sender_daily_limit(sender_email: str) -> int:
    """
    Adaptivní denní limit pro konkrétního sendera.
    Stejný princip jako globální, ale per-sender.
    """
    stats = await get_sender_stats(sender_email)
    health = compute_health_index(stats)

    # Pokud je sender téměř mrtvý
    if health < HEALTH_CRITICAL:
        return 0  # Pozastaven

    sent_7d = stats["sent_7d"]

    # Nový sender (málo dat)
    if sent_7d < 20:
        return SENDER_START_LIMIT

    # Průměrný denní objem za týden
    avg_daily = sent_7d / 7

    # Škálování dle zdraví
    if health >= 90:
        multiplier = 2.0    # Perfektní → dvojnásobek
    elif health >= 70:
        multiplier = 1.5    # Dobrý → 1.5x
    elif health >= HEALTH_WARNING:
        multiplier = 1.2    # OK → mírný nárůst
    else:
        multiplier = 0.7    # Varování → snížit

    new_limit = int(max(avg_daily, SENDER_START_LIMIT) * multiplier)
    return max(SENDER_MIN_LIMIT, min(SENDER_MAX_LIMIT, new_limit))


# ── Sender Selection (Round-Robin s failover) ──


async def get_active_senders() -> list[dict]:
    """
    Vrátí seznam aktivních senderů seřazených dle priority.
    Pozastavení senderé jsou vyfiltrovaní.
    """
    active = []

    for sender in SENDERS:
        email = sender["email"]
        stats = await get_sender_stats(email)
        health = compute_health_index(stats)
        daily_limit = await get_sender_daily_limit(email)

        sender_info = {
            **sender,
            "health_index": health,
            "daily_limit": daily_limit,
            "sent_today": stats["sent_today"],
            "remaining": max(0, daily_limit - stats["sent_today"]),
            "is_active": health >= HEALTH_CRITICAL and daily_limit > 0,
            "stats": stats,
        }

        if sender_info["is_active"] and sender_info["remaining"] > 0:
            active.append(sender_info)

    # Řadit: nejzdravější a nejvíce remaining nahoře
    active.sort(key=lambda s: (-s["health_index"], -s["remaining"]))
    return active


async def pick_sender() -> dict | None:
    """
    Vybere nejlepšího dostupného sendera pro další email.
    Round-robin s preference zdravějšího sendera.

    Vrací dict s "email", "name", "health_index" nebo None pokud žádný není k dispozici.
    """
    active = await get_active_senders()

    if not active:
        return None

    # Vybrat sender s nejvíce remaining kapacity
    # (automaticky balancuje zátěž)
    return active[0]


async def get_total_remaining() -> int:
    """Celkový počet emailů, které ještě můžeme dnes poslat (všichni senderé)."""
    active = await get_active_senders()
    return sum(s["remaining"] for s in active)


# ── Dashboard Report ──


async def get_senders_dashboard() -> dict:
    """Kompletní přehled všech odesílatelů pro admin dashboard."""
    all_senders = []
    total_sent_today = 0
    total_limit = 0
    total_remaining = 0
    active_count = 0

    for sender in SENDERS:
        email = sender["email"]
        stats = await get_sender_stats(email)
        health = compute_health_index(stats)
        daily_limit = await get_sender_daily_limit(email)
        remaining = max(0, daily_limit - stats["sent_today"])
        is_active = health >= HEALTH_CRITICAL and daily_limit > 0

        sender_info = {
            "email": email,
            "name": sender["name"],
            "priority": sender["priority"],
            "health_index": health,
            "health_status": _health_label(health),
            "daily_limit": daily_limit,
            "sent_today": stats["sent_today"],
            "remaining": remaining,
            "is_active": is_active,
            "bounce_rate": stats["bounce_rate"],
            "complaint_rate": stats["complaint_rate"],
            "open_rate": stats["open_rate"],
            "sent_7d": stats["sent_7d"],
        }
        all_senders.append(sender_info)

        total_sent_today += stats["sent_today"]
        total_limit += daily_limit
        total_remaining += remaining
        if is_active:
            active_count += 1

    return {
        "senders": all_senders,
        "active_senders": active_count,
        "total_senders": len(SENDERS),
        "total_sent_today": total_sent_today,
        "total_daily_limit": total_limit,
        "total_remaining": total_remaining,
        "system_status": "healthy" if active_count >= 2 else
                         "degraded" if active_count == 1 else
                         "critical",
    }


def _health_label(health: int) -> str:
    if health >= 90:
        return "🟢 Výborný"
    elif health >= 70:
        return "🟡 Dobrý"
    elif health >= HEALTH_WARNING:
        return "🟠 Varování"
    elif health >= HEALTH_CRITICAL:
        return "🔴 Kritický"
    else:
        return "⛔ Pozastaven"
