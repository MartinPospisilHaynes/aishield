"""
AIshield.cz — Outbound Email Engine
Posílání personalizovaných compliance emailů přes Resend API.
S ochranou domény: warm-up, bounce/complaint tracking, spam rate monitoring.
"""

import httpx
import random
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

# Max emailů na jednu firmu (1. email + 2 follow-upy)
MAX_EMAILS_PER_COMPANY = 3
FOLLOWUP_DAYS = 7


async def send_email(
    to: str,
    subject: str,
    html: str,
) -> dict:
    """Odešle email přes Resend API."""
    settings = get_settings()

    if not settings.resend_api_key:
        print(f"[Email] RESEND_API_KEY není nastaven — email neodesílán: {to}")
        return {"id": "dry_run", "status": "skipped"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": f"AIshield.cz <{settings.email_from}>",
                "to": [to],
                "subject": subject,
                "html": html,
            },
        )
        response.raise_for_status()
        return response.json()


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
    Hlavní email kampaň s ochranou domény:
    1. Zkontroluj zdraví domény (spam rate, bounce rate)
    2. Zjisti warm-up limit (kolik můžeme dnes poslat)
    3. Najdi firmy ke kontaktování
    4. Pro každou zkontroluj blacklist + domain limit
    5. Sestav personalizovaný email
    6. Odešli + zaloguj
    """
    supabase = get_supabase()
    stats = {
        "total_candidates": 0,
        "emails_sent": 0,
        "followups_sent": 0,
        "skipped_blacklisted": 0,
        "skipped_domain_limit": 0,
        "errors": 0,
        "daily_limit_reached": False,
        "campaign_stopped": False,
    }

    # 1. Kontrola zdraví domény
    health = await get_email_health()

    if not health["is_healthy"]:
        stats["campaign_stopped"] = True
        stats["warnings"] = health["warnings"]
        print(f"[Email] 🚨 Kampaň ZASTAVENA — doména nezdravá: {health['warnings']}")
        return stats

    if not health["can_send"]:
        stats["daily_limit_reached"] = True
        print(f"[Email] Denní warm-up limit dosažen ({health['sent_today']}/{health['warmup_limit']})")
        return stats

    remaining = health["remaining_today"]
    actual_limit = min(limit, remaining)

    # 2. Načíst firmy
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
            )
        else:
            email_data = get_followup_email(
                company_name=name,
                company_url=url,
                days_since=FOLLOWUP_DAYS * emails_sent,
            )

        # Odeslat
        try:
            if dry_run:
                result = {"id": "dry_run", "status": "skipped"}
                print(f"[Email DRY RUN] {email} — {email_data.subject}")
            else:
                result = await send_email(
                    to=email,
                    subject=email_data.subject,
                    html=email_data.body_html,
                )

            # Zalogovat
            supabase.table("email_log").insert({
                "company_ico": ico,
                "to_email": email,
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

        except Exception as e:
            print(f"[Email] Chyba pro {email}: {e}")
            stats["errors"] += 1

    print(f"[Email] Kampaň hotova: {stats}")
    return stats
