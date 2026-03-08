"""
AIshield.cz — Shoptet Addon: Self-Assessment Wizard v2
20-otázkový dotazník pro e-shopy, klasifikace AI systémů,
ukládání do DB, výpočet compliance skóre.
"""

import logging
from datetime import datetime, timezone

from backend.database import get_supabase
from backend.shoptet.models import (
    AI_ACT_CLASSIFICATION,
    QuestionnaireRequest,
    QuestionnaireResponse,
    WizardRequest,
    WizardResponse,
)

logger = logging.getLogger("shoptet.wizard")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AI systémy z dotazníku
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _extract_ai_systems(data: QuestionnaireRequest) -> list[dict]:
    """Extrahuje AI systémy z odpovědí dotazníku."""
    systems = []

    # Chatboty (Art. 50)
    if data.uses_ai_chatbot != "ne":
        for provider in (data.chatbot_providers or ["Nespecifikováno"]):
            systems.append({
                "provider": provider,
                "ai_type": "chatbot",
                "ai_act_article": "art50",
                "risk_level": "limited",
                "description_cs": "AI chatbot — přímá komunikace se zákazníkem",
            })

    # AI emaily (Art. 50)
    if data.uses_ai_email_auto != "ne":
        for provider in (data.email_providers or ["Nespecifikováno"]):
            systems.append({
                "provider": provider,
                "ai_type": "chatbot",
                "ai_act_article": "art50",
                "risk_level": "limited",
                "description_cs": "AI automatizace emailů zákazníkům",
            })

    # ChatGPT/Claude (Art. 4)
    if data.uses_chatgpt != "ne":
        for provider in (data.chatgpt_providers or ["ChatGPT"]):
            systems.append({
                "provider": provider,
                "ai_type": "content",
                "ai_act_article": "art4",
                "risk_level": "minimal",
                "description_cs": "AI asistent pro interní práci",
            })

    # AI obsah (Art. 50 pokud publikovaný)
    if data.uses_ai_content != "ne":
        systems.append({
            "provider": "AI generátor obsahu",
            "ai_type": "content",
            "ai_act_article": "art50",
            "risk_level": "limited",
            "description_cs": "AI-generovaný obsah viditelný zákazníkům",
        })

    # AI obrázky (Art. 50)
    if data.uses_ai_images != "ne":
        for provider in (data.image_providers or ["Nespecifikováno"]):
            systems.append({
                "provider": provider,
                "ai_type": "content",
                "ai_act_article": "art50",
                "risk_level": "limited",
                "description_cs": "AI-generované obrázky/videa",
            })

    # Dynamické ceny (Art. 4)
    if data.uses_dynamic_pricing != "ne":
        systems.append({
            "provider": "Dynamické ceny",
            "ai_type": "pricing",
            "ai_act_article": "art4",
            "risk_level": "minimal",
            "description_cs": "AI řízení cen — transparentnost vůči zákazníkům",
        })

    # Doporučovací systém (Art. 4)
    if data.uses_ai_recommendation != "ne":
        for provider in (data.recommendation_providers or ["Nespecifikováno"]):
            systems.append({
                "provider": provider,
                "ai_type": "recommendation",
                "ai_act_article": "art4",
                "risk_level": "minimal",
                "description_cs": "Doporučovací systém produktů",
            })

    # AI vyhledávání (Art. 4)
    if data.uses_ai_search != "ne":
        for provider in (data.search_providers or ["Nespecifikováno"]):
            systems.append({
                "provider": provider,
                "ai_type": "search",
                "ai_act_article": "art4",
                "risk_level": "minimal",
                "description_cs": "AI vyhledávání na e-shopu",
            })

    # AI rozhodování (Art. 4, potenciálně vyšší riziko)
    if data.uses_ai_decision != "ne":
        systems.append({
            "provider": "AI rozhodovací systém",
            "ai_type": "other",
            "ai_act_article": "art4",
            "risk_level": "limited",
            "description_cs": "AI automatické rozhodování o objednávkách/zákaznících",
        })

    # AI pro děti (Annex III — vysoké riziko)
    if data.uses_ai_for_children != "ne":
        systems.append({
            "provider": "AI systém cílený na děti",
            "ai_type": "other",
            "ai_act_article": "annex3",
            "risk_level": "high",
            "description_cs": "AI interagující s dětmi — vysoce rizikový systém",
        })

    return systems


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Compliance skóre — nový výpočet
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def calculate_compliance_score(
    data: QuestionnaireRequest,
    ai_systems: list[dict],
    scan_completed: bool = False,
    scan_clean: bool = False,
    compliance_page_published: bool = False,
) -> tuple[int, dict]:
    """
    Compliance skóre 0-100 s rozpadem.
    Vrací (score, breakdown).
    """
    breakdown = {
        "scan": 0,
        "scan_max": 15,
        "detection": 0,
        "detection_max": 25,
        "governance": 0,
        "governance_max": 30,
        "transparency": 0,
        "transparency_max": 30,
    }

    # ── Scan (max 15) ──
    if scan_completed:
        breakdown["scan"] += 10
    if scan_clean:
        breakdown["scan"] += 5

    # ── Detekce AI (max 25) ──
    # Body za identifikované systémy (max 15)
    system_points = min(len(ai_systems) * 3, 15)
    breakdown["detection"] += system_points

    # Art. 50 compliance (max 10)
    art50_systems = [s for s in ai_systems if s.get("ai_act_article") == "art50"]
    if not art50_systems:
        breakdown["detection"] += 10  # Žádné Art. 50 = plné body
    elif data.has_transparency_page != "ne":
        breakdown["detection"] += 5  # Mají stránku

    # ── Governance (max 30) ──
    if data.has_ai_training != "ne":
        breakdown["governance"] += 8
    if data.has_ai_guidelines != "ne":
        breakdown["governance"] += 6
    if data.has_ai_register != "ne":
        breakdown["governance"] += 6
    if data.has_oversight_person != "ne":
        breakdown["governance"] += 5
    if data.can_override_ai in ("ano", "ano — vždy", "ano — u důležitých"):
        breakdown["governance"] += 5

    # ── Transparentnost (max 30) ──
    if data.has_transparency_page != "ne":
        breakdown["transparency"] += 15
    if compliance_page_published:
        breakdown["transparency"] += 15

    total = (
        breakdown["scan"]
        + breakdown["detection"]
        + breakdown["governance"]
        + breakdown["transparency"]
    )
    return min(total, 100), breakdown


def _generate_recommendations(data: QuestionnaireRequest, ai_systems: list[dict]) -> list[str]:
    """Generuje konkrétní doporučení na základě dotazníku."""
    recs = []

    art50_systems = [s for s in ai_systems if s.get("ai_act_article") == "art50"]
    if art50_systems and data.has_transparency_page == "ne":
        recs.append(
            "Máte AI systémy spadající pod Article 50 (chatbot, AI obsah), "
            "ale nemáte na webu informaci o používání AI. "
            "Vytvořte compliance stránku — Standard plán to udělá automaticky."
        )

    if data.has_ai_training == "ne":
        recs.append(
            "Článek 4 AI Act vyžaduje AI gramotnost personálu. "
            "Proškolte zaměstnance o AI nástrojích, které používají."
        )

    if data.has_ai_guidelines == "ne":
        recs.append(
            "Nemáte interní pravidla pro AI. Sepište základní směrnici: "
            "kdo smí AI používat, k čemu, jaká data se nesmí vkládat."
        )

    if data.has_ai_register == "ne" and ai_systems:
        recs.append(
            "Nemáte evidenci AI systémů. Registr je základ compliance — "
            "náš Standard plán ho vygeneruje jako PDF automaticky."
        )

    if data.has_oversight_person == "ne":
        recs.append(
            "Určete odpovědnou osobu za AI ve firmě. "
            "Nemusí to být nová pozice — stačí přidat odpovědnost stávajícímu manažerovi."
        )

    if data.ai_processes_personal_data != "ne" and data.ai_data_stored_eu in ("nevim", "ne"):
        recs.append(
            "Zpracováváte osobní údaje přes AI, ale nevíte, zda jsou data v EU. "
            "Ověřte u poskytovatelů AI nástrojů lokaci serverů."
        )

    if data.uses_ai_for_children != "ne":
        recs.append(
            "AI systémy cílené na děti jsou dle Přílohy III AI Act vysoce rizikové. "
            "Doporučujeme konzultaci s právníkem a rozšířenou dokumentaci."
        )

    if not recs:
        recs.append("Gratulujeme — váš e-shop je na dobré cestě ke compliance.")

    return recs


def _identify_risk_areas(data: QuestionnaireRequest, ai_systems: list[dict]) -> list[dict]:
    """Identifikuje rizikové oblasti."""
    risks = []

    art50 = [s for s in ai_systems if s.get("ai_act_article") == "art50"]
    if art50 and data.has_transparency_page == "ne":
        risks.append({
            "area": "Transparentnost",
            "severity": "high",
            "description": f"{len(art50)} AI systémů vyžaduje informování zákazníků (Art. 50), ale nemáte transparentnostní stránku.",
            "deadline": "2026-08-02",
        })

    if data.has_ai_training == "ne":
        risks.append({
            "area": "AI gramotnost",
            "severity": "medium",
            "description": "Zaměstnanci nejsou proškoleni o AI (Article 4).",
            "deadline": "Platí od 2.2.2025",
        })

    high_risk = [s for s in ai_systems if s.get("risk_level") == "high"]
    if high_risk:
        risks.append({
            "area": "Vysoce rizikové AI",
            "severity": "critical",
            "description": f"{len(high_risk)} vysoce rizikových AI systémů vyžaduje rozšířenou dokumentaci.",
            "deadline": "2026-08-02",
        })

    if data.ai_processes_personal_data != "ne" and data.ai_data_stored_eu in ("nevim", "ne"):
        risks.append({
            "area": "GDPR + AI data",
            "severity": "medium",
            "description": "Osobní údaje zpracovávané AI mohou být mimo EU.",
        })

    return risks


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Hlavní handler — dotazník v2
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def process_questionnaire(
    installation_id: str,
    data: QuestionnaireRequest,
) -> QuestionnaireResponse:
    """
    Zpracuje 20-otázkový dotazník:
    1. Extrahuje AI systémy
    2. Klasifikuje dle AI Act
    3. Uloží do DB
    4. Spočítá compliance skóre
    5. Vygeneruje doporučení
    """
    sb = get_supabase()

    ai_systems = _extract_ai_systems(data)

    # Smazat staré záznamy (idempotence)
    sb.table("shoptet_ai_systems").delete().eq(
        "installation_id", installation_id,
    ).eq("source", "questionnaire").execute()

    # Uložit AI systémy
    if ai_systems:
        records = []
        for s in ai_systems:
            records.append({
                "installation_id": installation_id,
                "source": "questionnaire",
                "provider": s["provider"],
                "ai_type": s["ai_type"],
                "ai_act_article": s["ai_act_article"],
                "risk_level": s["risk_level"],
                "confidence": "confirmed",
                "is_active": True,
                "details": {"description_cs": s["description_cs"]},
            })
        sb.table("shoptet_ai_systems").insert(records).execute()

    # Uložit odpovědi dotazníku
    sb.table("shoptet_installations").update({
        "wizard_completed_at": datetime.now(timezone.utc).isoformat(),
        "questionnaire_data": data.model_dump(),
    }).eq("id", installation_id).execute()

    # Compliance skóre
    score, breakdown = calculate_compliance_score(data, ai_systems)

    # Doporučení
    recommendations = _generate_recommendations(data, ai_systems)
    risk_areas = _identify_risk_areas(data, ai_systems)

    art50_count = len([s for s in ai_systems if s.get("ai_act_article") == "art50"])
    art4_count = len([s for s in ai_systems if s.get("ai_act_article") != "art50"])

    # Zjistit plán
    inst = sb.table("shoptet_installations").select("plan").eq(
        "id", installation_id,
    ).execute()
    plan = inst.data[0].get("plan", "free") if inst.data else "free"

    logger.info(
        f"Dotazník dokončen: installation={installation_id}, "
        f"systems={len(ai_systems)}, score={score}, plan={plan}"
    )

    return QuestionnaireResponse(
        installation_id=installation_id,
        ai_systems_count=len(ai_systems),
        compliance_score=score,
        score_breakdown=breakdown,
        art50_relevant=art50_count,
        art4_relevant=art4_count,
        risk_areas=risk_areas,
        recommendations=recommendations,
        plan=plan,
        message=f"Identifikováno {len(ai_systems)} AI systémů. Compliance skóre: {score}/100.",
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Legacy wizard v1 (zachováno pro kompatibilitu)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


async def process_wizard(installation_id: str, wizard_data: WizardRequest) -> WizardResponse:
    """
    Hlavní wizard handler:
    1. Klasifikuje všechny AI systémy
    2. Uloží do DB (shoptet_ai_systems)
    3. Aktualizuje wizard_completed_at na instalaci
    4. Vrátí souhrnný response
    """
    sb = get_supabase()

    # Sesbírat všechny AI systémy z wizardu
    all_entries = []
    for entry in wizard_data.chatbots:
        all_entries.append(("chatbot", entry))
    for entry in wizard_data.content_ai:
        all_entries.append(("content", entry))
    for entry in wizard_data.other_ai:
        classification = _classify_ai_system(entry.ai_type)
        all_entries.append((entry.ai_type, entry))

    if not all_entries:
        # Žádné AI systémy — stále uložit wizard jako dokončený
        sb.table("shoptet_installations").update({
            "wizard_completed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", installation_id).execute()

        return WizardResponse(
            installation_id=installation_id,
            ai_systems_count=0,
            compliance_score=40,
            art50_relevant=0,
            art4_relevant=0,
            message="Wizard dokončen — žádné AI systémy nebyly identifikovány.",
        )

    # Smazat staré záznamy z předchozího vyplnění (idempotence)
    sb.table("shoptet_ai_systems").delete().eq(
        "installation_id", installation_id,
    ).eq("source", "wizard").execute()

    # Uložit nové AI systémy
    records = []
    art50_count = 0
    art4_count = 0

    for ai_type, entry in all_entries:
        classification = _classify_ai_system(ai_type)
        record = {
            "installation_id": installation_id,
            "source": "wizard",
            "provider": entry.provider,
            "ai_type": ai_type,
            "ai_act_article": classification["ai_act_article"],
            "risk_level": classification["risk_level"],
            "confidence": "confirmed",  # wizard = uživatel potvrdil
            "is_active": True,
            "details": {
                "custom_note": entry.custom_note,
                "description_cs": classification["description_cs"],
            },
        }
        records.append(record)

        if classification["ai_act_article"] == "art50":
            art50_count += 1
        else:
            art4_count += 1

    # Bulk insert
    sb.table("shoptet_ai_systems").insert(records).execute()

    # Aktualizovat instalaci
    sb.table("shoptet_installations").update({
        "wizard_completed_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", installation_id).execute()

    score = _calculate_compliance_score(records)

    logger.info(
        f"Wizard dokončen: installation={installation_id}, "
        f"systems={len(records)}, art50={art50_count}, art4={art4_count}, score={score}"
    )

    return WizardResponse(
        installation_id=installation_id,
        ai_systems_count=len(records),
        compliance_score=score,
        art50_relevant=art50_count,
        art4_relevant=art4_count,
        message=f"Identifikováno {len(records)} AI systémů. "
                f"{art50_count} vyžaduje Article 50 compliance (deadline 2.8.2026).",
    )


async def get_ai_systems(installation_id: str) -> list[dict]:
    """Vrátí všechny AI systémy pro danou instalaci."""
    sb = get_supabase()
    result = sb.table("shoptet_ai_systems").select("*").eq(
        "installation_id", installation_id,
    ).eq("is_active", True).execute()
    return result.data or []
