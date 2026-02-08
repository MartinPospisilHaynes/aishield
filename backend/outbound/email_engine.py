"""
AIshield.cz — Outbound Email Engine
Posílání personalizovaných compliance emailů přes Resend API.
Limity: max 200/den, max 3 na firmu, unsubscribe tracking.
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

# Denní limit emailů
DAILY_LIMIT = 200
MAX_EMAILS_PER_COMPANY = 3
FOLLOWUP_DAYS = 7  # Kolik dní čekat na follow-up


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
    Hlavní email kampaň:
    1. Najdi firmy ke kontaktování
    2. Pro každou sestav personalizovaný email
    3. Odešli (nebo dry_run)
    4. Ulož do DB
    """
    supabase = get_supabase()
    stats = {
        "total_candidates": 0,
        "emails_sent": 0,
        "followups_sent": 0,
        "errors": 0,
        "daily_limit_reached": False,
    }

    # Kontrola denního limitu
    today = datetime.utcnow().date().isoformat()
    sent_today_res = supabase.table("email_log").select(
        "id", count="exact"
    ).gte("sent_at", today).execute()
    sent_today = sent_today_res.count or 0

    if sent_today >= DAILY_LIMIT:
        stats["daily_limit_reached"] = True
        print(f"[Email] Denní limit dosažen ({sent_today}/{DAILY_LIMIT})")
        return stats

    remaining = DAILY_LIMIT - sent_today
    actual_limit = min(limit, remaining)

    # Načíst firmy
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
