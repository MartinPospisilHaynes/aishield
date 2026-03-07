"""
AIshield.cz — Shoptet Addon: Self-Assessment Wizard
Zpracování odpovědí z frontend wizardu, klasifikace AI systémů,
ukládání do DB, výpočet compliance skóre.
"""

import logging
from datetime import datetime, timezone

from backend.database import get_supabase
from backend.shoptet.models import (
    AI_ACT_CLASSIFICATION,
    WizardRequest,
    WizardResponse,
)

logger = logging.getLogger("shoptet.wizard")


def _classify_ai_system(ai_type: str) -> dict:
    """Klasifikuje AI systém podle AI Act pravidel."""
    return AI_ACT_CLASSIFICATION.get(ai_type, AI_ACT_CLASSIFICATION["other"])


def _calculate_compliance_score(ai_systems: list[dict]) -> int:
    """
    Compliance skóre 0-100.
    Logika:
    - Základní body za vyplnění wizardu (40)
    - Body za každý evidovaný systém (+10 za systém, max 30)
    - Body za compliance stránku (30) — přidá se až po publikaci
    """
    base = 40  # wizard dokončen
    systems_bonus = min(len(ai_systems) * 10, 30)
    return base + systems_bonus  # max 70 bez compliance stránky


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
