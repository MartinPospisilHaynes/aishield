"""
AIshield.cz — Outbound Email Engine v2
Agresivní outreach s multi-sender rotací a průběžným odesíláním.

Klíčové vlastnosti:
- 3 nezávislí odesílatelé (info@, ahoj@, podpora@aishield.cz)
- Automatický failover při blokaci
- Náhodné zpoždění mezi emaily (30-120s) — vypadá přirozeně
- Rozesílka průběžně 8:00-17:00, NE jednorázový batch
- Odesílání pouze v pracovní dny (Po-Pá)
"""

import httpx
import random
import asyncio
import logging
from datetime import datetime, timedelta
from backend.config import get_settings
from backend.database import get_supabase
from backend.outbound.email_templates import (
    get_outbound_email,
    get_followup_email,
)
from backend.outbound.deliverability import (
    get_email_health,
    check_domain_limit,
    is_email_blacklisted,
)
from backend.outbound.sender_rotation import (
    pick_sender,
    get_total_remaining,
    get_senders_dashboard,
)

logger = logging.getLogger(__name__)

# Max emailů na jednu firmu (1. email + 2 follow-upy)
MAX_EMAILS_PER_COMPANY = 3
FOLLOWUP_DAYS = 7

# Zpoždění mezi emaily (sekundy) — náhodné, vypadá přirozeně
MIN_DELAY_SECONDS = 30
MAX_DELAY_SECONDS = 120

# Pracovní hodiny (UTC) — v CET je to 8:00-17:00
SEND_HOUR_START = 7   # 8:00 CET
SEND_HOUR_END = 16    # 17:00 CET

# Nepracovní dny (0=Po, 6=Ne)
WEEKEND_DAYS = {5, 6}  # Sobota, Neděle


def is_sending_allowed() -> tuple[bool, str]:
    """Zkontroluje jestli je teď pracovní hodina a pracovní den."""
    now = datetime.utcnow()
    weekday = now.weekday()
    hour = now.hour

    if weekday in WEEKEND_DAYS:
        return False, f"Víkend (den {weekday}) — emaily se neposílají"

    if hour < SEND_HOUR_START:
        return False, f"Příliš brzy ({hour}:00 UTC) — start v {SEND_HOUR_START}:00"

    if hour >= SEND_HOUR_END:
        return False, f"Příliš pozdě ({hour}:00 UTC) — konec v {SEND_HOUR_END}:00"

    return True, "OK"


async def send_email(
    to: str,
    subject: str,
    html: str,
    from_email: str | None = None,
    from_name: str | None = None,
    attachments: list[dict] | None = None,
    text: str | None = None,
    sender_name: str | None = None,
) -> dict:
    """
    Odešle email přes Resend API.
    Pokud from_email není zadán, použije přiřazeného sendera z rotace.
    """
    settings = get_settings()

    if not settings.resend_api_key:
        print(f"[Email] RESEND_API_KEY není nastaven — email neodesílán: {to}")
        return {"id": "dry_run", "status": "skipped"}

    # Sender — buď specifikovaný, nebo z rotace
    sender_email = from_email or settings.email_from
    _sender_name = sender_name or from_name or "AIshield.cz"

    # Reply-To na existující email (Resend odesílá, odpovědi jdou jinam)
    reply_to = "info@desperados-design.cz"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": f"{_sender_name} <{sender_email}>",
                "to": [to],
                "reply_to": reply_to,
                "subject": subject,
                "html": html,
                **({"text": text} if text else {}),
                "headers": {
                    "List-Unsubscribe": f"<https://aishield.cz/api/unsubscribe?email={to}>",
                    "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
                },
                **({
                    "attachments": attachments,
                } if attachments else {}),
            },
        )
        response.raise_for_status()
        return response.json()


async def check_delivery_status(resend_id: str) -> dict:
    """
    Zkontroluje stav doručení emailu přes Resend API.
    Vrací: {"id": "...", "status": "delivered|bounced|...", "last_event": "..."}
    """
    settings = get_settings()
    if not settings.resend_api_key or not resend_id or resend_id == "dry_run":
        return {"id": resend_id, "status": "unknown", "reason": "no API key or dry run"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://api.resend.com/emails/{resend_id}",
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                },
            )
            response.raise_for_status()
            data = response.json()

            return {
                "id": resend_id,
                "status": data.get("last_event", "sent"),
                "to": data.get("to", []),
                "subject": data.get("subject", ""),
                "created_at": data.get("created_at", ""),
                "last_event": data.get("last_event", ""),
            }
    except httpx.HTTPStatusError as e:
        logger.error(f"Resend status check error: {e.response.status_code}")
        return {"id": resend_id, "status": "error", "error": str(e)}
    except Exception as e:
        logger.error(f"Delivery check failed: {e}")
        return {"id": resend_id, "status": "error", "error": str(e)}


async def get_delivery_report(hours: int = 24) -> dict:
    """
    Vrátí souhrnný report doručení za posledních N hodin.
    Kontroluje stav každého emailu přes Resend API.
    """
    supabase = get_supabase()
    since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

    res = supabase.table("email_log").select(
        "resend_id, to_email, subject, status, sent_at"
    ).gte("sent_at", since).order("sent_at", desc=True).execute()

    emails = res.data or []
    report = {
        "total": len(emails),
        "delivered": 0,
        "opened": 0,
        "clicked": 0,
        "bounced": 0,
        "pending": 0,
        "emails": [],
    }

    for email in emails:
        resend_id = email.get("resend_id", "")
        if resend_id and resend_id != "dry_run":
            status = await check_delivery_status(resend_id)
            last_event = status.get("last_event", "sent")

            # Update local status if changed
            if last_event in ("delivered", "opened", "clicked", "bounced", "complained"):
                supabase.table("email_log").update({
                    "status": last_event,
                }).eq("resend_id", resend_id).execute()
        else:
            last_event = email.get("status", "unknown")

        if last_event == "delivered":
            report["delivered"] += 1
        elif last_event in ("opened", "clicked"):
            report["opened"] += 1
        elif last_event in ("bounced", "complained"):
            report["bounced"] += 1
        else:
            report["pending"] += 1

        report["emails"].append({
            "to": email.get("to_email", ""),
            "subject": email.get("subject", ""),
            "status": last_event,
            "sent_at": email.get("sent_at", ""),
        })

    return report


async def get_companies_to_email(limit: int = 50) -> list[dict]:
    """
    Vrátí firmy, kterým je potřeba poslat email:
    - Jsou kvalifikované (mají AI findings)
    - Mají email
    - Lead tier je HOT nebo WARM (COOL a COLD přeskakujeme)
    - Ještě nedostaly max počet emailů
    - Nejsou unsubscribed
    Řazeno dle lead_score DESC (nejlepší leady první).
    """
    supabase = get_supabase()

    res = supabase.table("companies").select(
        "*, scans(id, total_findings), findings(name, risk_level, ai_act_article)"
    ).in_(
        "prospecting_status", ["qualified"]
    ).in_(
        "lead_tier", ["HOT", "WARM"]
    ).eq(
        "scan_status", "scanned"
    ).neq(
        "email", ""
    ).lt(
        "emails_sent", MAX_EMAILS_PER_COMPANY
    ).order(
        "lead_score", desc=True
    ).limit(limit).execute()

    return res.data or []


async def run_email_campaign(
    dry_run: bool = False,
    limit: int = 50,
) -> dict:
    """
    Hlavní email kampaň v2 — multi-sender s průběžným odesíláním:
    1. Zkontroluj pracovní dobu (Po-Pá, 8-17)
    2. Zkontroluj zdraví domény (globální emergency checks)
    3. Vyber sendera (round-robin, nejzdravější first)
    4. Najdi firmy ke kontaktování
    5. Pro každou: blacklist + domain limit check
    6. Sestav personalizovaný email
    7. Odešli přes vybraného sendera
    8. Počkej náhodné zpoždění (30-120s) — vypadá přirozeně
    """
    supabase = get_supabase()
    stats = {
        "total_candidates": 0,
        "emails_sent": 0,
        "followups_sent": 0,
        "skipped_blacklisted": 0,
        "skipped_domain_limit": 0,
        "skipped_no_sender": 0,
        "errors": 0,
        "daily_limit_reached": False,
        "campaign_stopped": False,
        "senders_used": {},
    }

    # 1. Kontrola pracovní doby
    can_send_now, reason = is_sending_allowed()
    if not can_send_now:
        stats["campaign_stopped"] = True
        stats["stop_reason"] = reason
        print(f"[Email] ⏸️  {reason}")
        return stats

    # 2. Kontrola globálního zdraví domény
    health = await get_email_health()

    if not health["is_healthy"]:
        stats["campaign_stopped"] = True
        stats["warnings"] = health["warnings"]
        print(f"[Email] 🚨 Kampaň ZASTAVENA — doména nezdravá: {health['warnings']}")
        return stats

    # 3. Kolik můžeme celkem poslat (všichni senderé dohromady)?
    total_remaining = await get_total_remaining()
    if total_remaining <= 0:
        stats["daily_limit_reached"] = True
        print("[Email] Denní limit VŠECH senderů dosažen")
        return stats

    actual_limit = min(limit, total_remaining)

    # 4. Načíst firmy
    companies = await get_companies_to_email(actual_limit)
    stats["total_candidates"] = len(companies)

    for company in companies:
        ico = company.get("ico", "")
        email = company.get("email", "")
        name = company.get("name", "")
        url = company.get("url", "")
        emails_sent = company.get("emails_sent", 0)

        if not email or not url:
            continue

        # Blacklist check
        if await is_email_blacklisted(email):
            stats["skipped_blacklisted"] += 1
            continue

        # Per-domain rate limit
        if not await check_domain_limit(email):
            stats["skipped_domain_limit"] += 1
            continue

        # Vyber sendera (round-robin s auto-failover)
        sender = await pick_sender()
        if not sender:
            stats["skipped_no_sender"] += 1
            print("[Email] ⚠️  Žádný sender dostupný — přeskakuji")
            break  # Nemá cenu pokračovat

        sender_email = sender["email"]
        sender_name = sender["name"]

        # Najdi top finding
        findings = company.get("findings", [])
        findings_count = len(findings)
        if findings_count == 0:
            continue

        top_finding = findings[0].get("name", "AI systém bez označení")

        # Rozhodnutí: první email nebo follow-up
        if emails_sent == 0:
            # A/B test: náhodně varianta A nebo B
            variant = random.choice(["A", "B"])
            email_data = get_outbound_email(
                company_name=name,
                company_url=url,
                findings_count=findings_count,
                top_finding=top_finding,
                variant=variant,
                to_email=email,
            )
        else:
            email_data = get_followup_email(
                company_name=name,
                company_url=url,
                days_since=FOLLOWUP_DAYS * emails_sent,
                to_email=email,
            )

        # Odeslat přes vybraného sendera
        try:
            if dry_run:
                result = {"id": "dry_run", "status": "skipped"}
                print(f"[Email DRY RUN] {sender_email} → {email} — {email_data.subject}")
            else:
                result = await send_email(
                    to=email,
                    subject=email_data.subject,
                    html=email_data.body_html,
                    from_email=sender_email,
                    from_name=sender_name,
                )

            # Zalogovat (s from_email pro sender tracking)
            supabase.table("email_log").insert({
                "company_ico": ico,
                "to_email": email,
                "from_email": sender_email,
                "subject": email_data.subject,
                "variant": email_data.variant_id,
                "resend_id": result.get("id", ""),
                "status": "sent" if not dry_run else "dry_run",
                "sent_at": datetime.utcnow().isoformat(),
            }).execute()

            # Aktualizovat counter na firmě
            supabase.table("companies").update({
                "emails_sent": emails_sent + 1,
                "last_email_at": datetime.utcnow().isoformat(),
            }).eq("ico", ico).execute()

            if emails_sent == 0:
                stats["emails_sent"] += 1
            else:
                stats["followups_sent"] += 1

            # Track sender usage
            stats["senders_used"][sender_email] = \
                stats["senders_used"].get(sender_email, 0) + 1

            # 🕐 Náhodné zpoždění — vypadá jako člověk, ne robot
            if not dry_run:
                delay = random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
                print(f"[Email] ✅ {sender_email} → {email} | čekám {delay:.0f}s...")
                await asyncio.sleep(delay)

        except Exception as e:
            print(f"[Email] ❌ Chyba {sender_email} → {email}: {e}")
            stats["errors"] += 1

    print(f"[Email] Kampaň hotova: {stats}")
    return stats
