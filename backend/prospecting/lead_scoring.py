"""
AIshield.cz — Lead Scoring Engine
Hodnotí leady podle pravděpodobnosti konverze.

Skóre 0-100:
  80-100 = 🔥 HOT   (poslat email ihned, priorita)
  50-79  = 🟡 WARM  (poslat email)
  20-49  = 🔵 COOL  (follow-up za týden)
  0-19   = ⚪ COLD  (neposílat, neplýtvat)

Faktory:
  - Počet AI findings na webu (víc = víc potřebují pomoc)
  - Závažnost findings (vysoké riziko > minimální)
  - Typ firmy (e-shop > služby > ostatní)
  - Velikost (Heureka recenze, zaměstnanci)
  - Zdroj kontaktu (Shoptet/Heureka > ARES)
  - Kvalita emailu (firemní doména > freemail)
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LeadScore:
    """Výsledek scoringu."""
    total_score: int           # 0-100
    tier: str                  # HOT / WARM / COOL / COLD
    breakdown: dict            # Detailní rozpad bodů
    recommendation: str        # Co s leadem dělat


# ── Bodové tabulky ──

# AI Findings skóre
FINDINGS_SCORE = {
    0: 0,      # Žádné findings = nerelevantní
    1: 15,     # 1 finding
    2: 25,     # 2 findings
    3: 35,     # 3+ findings
}

# Rizikovost findings
RISK_SCORE = {
    "zakázané": 30,     # Zakázaný AI systém = urgentní
    "vysoké": 25,       # Vysoké riziko
    "omezené": 15,      # Transparenční povinnosti
    "minimální": 5,     # Minimální riziko
}

# Zdroj firmy
SOURCE_SCORE = {
    "shoptet_catalog": 15,   # E-shop na Shoptetu = jistě má web + AI
    "heureka_catalog": 15,   # E-shop na Heurece = aktivní obchod
    "ares_prospecting": 5,   # ARES = nevíme jistě jestli mají web
}

# NACE kódy — bonusy za obor
NACE_BONUS = {
    "4791": 10,   # E-commerce (nejpravděpodobněji používají AI)
    "4799": 8,    # Jiný maloobchod
    "6201": 7,    # Programování (znají AI, ale potřebují compliance)
    "6202": 7,    # IT poradenství
    "6311": 6,    # Hosting/zpracování dat
    "6312": 6,    # Webové portály
    "7311": 5,    # Reklamní agentury
    "6419": 5,    # Banky/fintech
    "6910": 4,    # Právní činnosti
}

# Kvalita emailu
EMAIL_QUALITY_SCORE = {
    "vision": 8,       # Claude Vision = ověřený email
    "playwright": 10,  # Playwright render = spolehlivý
    "regex": 7,        # Regex = OK
    "firmy.cz": 6,     # Firmy.cz = může být starý
    "heuristic": 3,    # Heuristika = nespolehlivý
}


def calculate_lead_score(
    total_findings: int = 0,
    highest_risk: str = "",
    source: str = "",
    nace_codes: list[str] | None = None,
    email: str = "",
    email_source: str = "",
    email_confidence: float = 0.0,
    heureka_reviews: int = 0,
    heureka_rating: float = 0.0,
) -> LeadScore:
    """
    Vypočítá skóre leadu 0-100.
    """
    breakdown = {}
    score = 0

    # 1. Findings (0-35 bodů)
    findings_pts = FINDINGS_SCORE.get(
        min(total_findings, 3), FINDINGS_SCORE[3]
    )
    breakdown["findings"] = findings_pts
    score += findings_pts

    # 2. Rizikovost (0-30 bodů)
    risk_pts = RISK_SCORE.get(highest_risk.lower(), 0)
    breakdown["risk"] = risk_pts
    score += risk_pts

    # 3. Zdroj (0-15 bodů)
    source_pts = SOURCE_SCORE.get(source, 3)
    breakdown["source"] = source_pts
    score += source_pts

    # 4. NACE bonus (0-10 bodů)
    nace_pts = 0
    for code in (nace_codes or []):
        nace_pts = max(nace_pts, NACE_BONUS.get(code, 0))
    breakdown["nace"] = nace_pts
    score += nace_pts

    # 5. Email quality (0-10 bodů)
    email_pts = 0
    if email:
        email_pts = EMAIL_QUALITY_SCORE.get(email_source, 5)
        # Bonus za confidence
        email_pts = int(email_pts * max(email_confidence, 0.5))
    breakdown["email"] = email_pts
    score += email_pts

    # 6. Velikost firmy — Heureka recenze jako proxy (0-10 bodů)
    size_pts = 0
    if heureka_reviews >= 100:
        size_pts = 10
    elif heureka_reviews >= 50:
        size_pts = 7
    elif heureka_reviews >= 10:
        size_pts = 4
    elif heureka_reviews > 0:
        size_pts = 2
    breakdown["size"] = size_pts
    score += size_pts

    # Ořízni na 0-100
    score = max(0, min(100, score))

    # Tier
    if score >= 40:
        tier = "HOT"
        recommendation = "Poslat email ihned — vysoká šance na konverzi"
    elif score >= 20:
        tier = "WARM"
        recommendation = "Poslat email — solidní lead"
    elif score >= 10:
        tier = "COOL"
        recommendation = "Follow-up za týden — nízká priorita"
    else:
        tier = "COLD"
        recommendation = "Neposílat — pravděpodobně nekonvertuje"

    return LeadScore(
        total_score=score,
        tier=tier,
        breakdown=breakdown,
        recommendation=recommendation,
    )


async def score_all_leads() -> dict:
    """
    Přepočítá skóre pro všechny kvalifikované leady v DB.
    Uloží lead_score + lead_tier do tabulky companies.
    """
    from backend.database import get_supabase

    supabase = get_supabase()
    stats = {"scored": 0, "hot": 0, "warm": 0, "cool": 0, "cold": 0}

    res = supabase.table("companies").select(
        "id, ico, url, total_findings, source, nace_codes, email, "
        "email_source, email_confidence, heureka_reviews, heureka_rating"
    ).in_("prospecting_status", ["qualified", "qualified_hot"]).execute()

    companies = res.data or []

    for company in companies:
        # Najdi nejvyšší riziko z findings
        highest_risk = ""
        ico = company.get("ico", "")
        url = company.get("url", "")

        company_id = company.get("id", "")
        if company_id:
            findings_res = supabase.table("findings").select(
                "risk_level"
            ).eq("company_id", company_id).execute()
        else:
            findings_res = None

        if findings_res and findings_res.data:
            risk_priority = {"zakázané": 4, "vysoké": 3, "omezené": 2, "minimální": 1}
            for f in findings_res.data:
                rl = f.get("risk_level", "").lower()
                if risk_priority.get(rl, 0) > risk_priority.get(highest_risk, 0):
                    highest_risk = rl

        lead = calculate_lead_score(
            total_findings=company.get("total_findings", 0),
            highest_risk=highest_risk,
            source=company.get("source", ""),
            nace_codes=company.get("nace_codes", []),
            email=company.get("email", ""),
            email_source=company.get("email_source", ""),
            email_confidence=company.get("email_confidence") or 0.0,
            heureka_reviews=company.get("heureka_reviews") or 0,
            heureka_rating=company.get("heureka_rating") or 0.0,
        )

        update = {
            "lead_score": lead.total_score,
            "lead_tier": lead.tier,
        }

        if ico:
            supabase.table("companies").update(update).eq("ico", ico).execute()
        elif url:
            supabase.table("companies").update(update).eq("url", url).execute()

        stats["scored"] += 1
        stats[lead.tier.lower()] = stats.get(lead.tier.lower(), 0) + 1

    print(f"[LeadScoring] Hotovo: {stats}")
    return stats
