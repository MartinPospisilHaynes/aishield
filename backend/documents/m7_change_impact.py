"""
AIshield.cz — M7 Change Impact Analyzer

Analyzuje dopad změny v dotazníku na rizikový profil firmy a dokumenty.
Kombinuje rule-based logiku (levné, deterministické) s LLM pro komplexní případy.

Vstup: staré odpovědi, nové odpovědi, aktuální risk_breakdown, seznam dokumentů
Výstup: impact_level, risk_change, affected_documents, summary
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════
# MAPOVÁNÍ: question_key → risk_level + affected document keys
# ══════════════════════════════════════════════════════════════════════

# Kontaktní klíče — změna nemá vliv na compliance
CONTACT_KEYS = {
    "company_legal_name", "company_ico", "company_address",
    "company_contact_email", "company_phone",
}

# Mapování otázek na rizikovou úroveň a dotčené dokumenty
QUESTION_IMPACT_MAP: dict[str, dict] = {
    # Zakázané praktiky — CRITICAL
    "uses_social_scoring": {
        "risk_hint": "unacceptable",
        "affected_docs": [
            "compliance_report", "action_plan", "ai_register",
            "incident_response_plan", "dpia_template",
        ],
    },
    "uses_subliminal_manipulation": {
        "risk_hint": "unacceptable",
        "affected_docs": [
            "compliance_report", "action_plan", "ai_register",
            "incident_response_plan", "dpia_template",
        ],
    },
    "uses_realtime_biometric": {
        "risk_hint": "high",
        "affected_docs": [
            "compliance_report", "action_plan", "ai_register",
            "dpia_template", "monitoring_plan", "transparency_human_oversight",
        ],
    },
    # AI nástroje ve firmě — LIMITED
    "uses_chatgpt": {
        "risk_hint": "limited",
        "affected_docs": [
            "compliance_report", "ai_register", "chatbot_notices",
            "ai_policy", "training_outline", "training_presentation",
        ],
    },
    "uses_copilot": {
        "risk_hint": "limited",
        "affected_docs": [
            "compliance_report", "ai_register", "ai_policy",
            "training_outline", "training_presentation",
        ],
    },
    "uses_ai_content": {
        "risk_hint": "limited",
        "affected_docs": [
            "compliance_report", "ai_register", "ai_policy",
            "chatbot_notices", "transparency_human_oversight",
        ],
    },
    "uses_deepfake": {
        "risk_hint": "high",
        "affected_docs": [
            "compliance_report", "action_plan", "ai_register",
            "chatbot_notices", "ai_policy", "dpia_template",
        ],
    },
    # HR
    "uses_ai_recruitment": {
        "risk_hint": "high",
        "affected_docs": [
            "compliance_report", "action_plan", "ai_register",
            "dpia_template", "transparency_human_oversight", "monitoring_plan",
        ],
    },
    "uses_ai_employee_monitoring": {
        "risk_hint": "high",
        "affected_docs": [
            "compliance_report", "action_plan", "ai_register",
            "dpia_template", "transparency_human_oversight", "monitoring_plan",
        ],
    },
    "uses_emotion_recognition": {
        "risk_hint": "high",
        "affected_docs": [
            "compliance_report", "action_plan", "ai_register",
            "dpia_template", "transparency_human_oversight",
        ],
    },
    # Finance
    "uses_ai_accounting": {
        "risk_hint": "limited",
        "affected_docs": [
            "compliance_report", "ai_register", "ai_policy",
            "vendor_checklist",
        ],
    },
    "uses_ai_creditscoring": {
        "risk_hint": "high",
        "affected_docs": [
            "compliance_report", "action_plan", "ai_register",
            "dpia_template", "transparency_human_oversight", "monitoring_plan",
        ],
    },
    "uses_ai_insurance": {
        "risk_hint": "high",
        "affected_docs": [
            "compliance_report", "action_plan", "ai_register",
            "dpia_template", "transparency_human_oversight",
        ],
    },
    # Zákaznický servis
    "uses_ai_chatbot": {
        "risk_hint": "limited",
        "affected_docs": [
            "compliance_report", "ai_register", "chatbot_notices",
            "transparency_page", "ai_policy",
        ],
    },
    "uses_ai_email_auto": {
        "risk_hint": "limited",
        "affected_docs": [
            "compliance_report", "ai_register", "chatbot_notices",
            "ai_policy",
        ],
    },
    "uses_ai_decision": {
        "risk_hint": "high",
        "affected_docs": [
            "compliance_report", "action_plan", "ai_register",
            "dpia_template", "transparency_human_oversight", "monitoring_plan",
        ],
    },
    "uses_dynamic_pricing": {
        "risk_hint": "limited",
        "affected_docs": [
            "compliance_report", "ai_register", "ai_policy",
            "chatbot_notices",
        ],
    },
    "uses_ai_for_children": {
        "risk_hint": "high",
        "affected_docs": [
            "compliance_report", "action_plan", "ai_register",
            "dpia_template", "transparency_human_oversight",
        ],
    },
    # Bezpečnost
    "uses_ai_critical_infra": {
        "risk_hint": "high",
        "affected_docs": [
            "compliance_report", "action_plan", "ai_register",
            "dpia_template", "incident_response_plan", "monitoring_plan",
        ],
    },
    "uses_ai_safety_component": {
        "risk_hint": "high",
        "affected_docs": [
            "compliance_report", "action_plan", "ai_register",
            "dpia_template", "monitoring_plan",
        ],
    },
    # Ochrana dat
    "ai_processes_personal_data": {
        "risk_hint": "limited",
        "affected_docs": [
            "compliance_report", "dpia_template", "ai_policy",
            "vendor_checklist",
        ],
    },
    "ai_data_stored_eu": {
        "risk_hint": "limited",
        "affected_docs": [
            "compliance_report", "dpia_template", "vendor_checklist",
        ],
    },
    "has_ai_vendor_contracts": {
        "risk_hint": "minimal",
        "affected_docs": ["vendor_checklist", "compliance_report"],
    },
    # AI gramotnost
    "has_ai_training": {
        "risk_hint": "minimal",
        "affected_docs": [
            "training_outline", "training_presentation", "compliance_report",
        ],
    },
    "has_ai_guidelines": {
        "risk_hint": "minimal",
        "affected_docs": ["ai_policy", "compliance_report"],
    },
    # Lidský dohled
    "has_oversight_person": {
        "risk_hint": "limited",
        "affected_docs": [
            "compliance_report", "transparency_human_oversight",
            "monitoring_plan",
        ],
    },
    "can_override_ai": {
        "risk_hint": "limited",
        "affected_docs": [
            "compliance_report", "transparency_human_oversight",
        ],
    },
    "ai_decision_logging": {
        "risk_hint": "limited",
        "affected_docs": [
            "compliance_report", "monitoring_plan",
            "transparency_human_oversight",
        ],
    },
    "has_ai_register": {
        "risk_hint": "minimal",
        "affected_docs": ["ai_register", "compliance_report"],
    },
    # Role v řetězci
    "develops_own_ai": {
        "risk_hint": "high",
        "affected_docs": [
            "compliance_report", "action_plan", "ai_register",
            "dpia_template", "monitoring_plan", "vendor_checklist",
        ],
    },
    "modifies_ai_purpose": {
        "risk_hint": "high",
        "affected_docs": [
            "compliance_report", "action_plan", "ai_register",
            "dpia_template",
        ],
    },
    "uses_gpai_api": {
        "risk_hint": "limited",
        "affected_docs": [
            "compliance_report", "ai_register", "vendor_checklist",
            "ai_policy",
        ],
    },
    # Incidenty
    "has_incident_plan": {
        "risk_hint": "limited",
        "affected_docs": [
            "incident_response_plan", "compliance_report",
        ],
    },
    "monitors_ai_outputs": {
        "risk_hint": "limited",
        "affected_docs": ["monitoring_plan", "compliance_report"],
    },
    "tracks_ai_changes": {
        "risk_hint": "limited",
        "affected_docs": ["monitoring_plan", "compliance_report"],
    },
    "has_ai_bias_check": {
        "risk_hint": "limited",
        "affected_docs": [
            "monitoring_plan", "compliance_report",
            "transparency_human_oversight",
        ],
    },
    # Transparenční stránka
    "transparency_page_implementation": {
        "risk_hint": "minimal",
        "affected_docs": ["transparency_page"],
    },
}

# Váhy rizikových úrovní
RISK_WEIGHT = {
    "unacceptable": 100,
    "high": 30,
    "limited": 10,
    "minimal": 3,
}


def analyze_change_impact(
    changes: list[dict],
    old_risk_breakdown: Optional[dict] = None,
) -> dict:
    """
    Analyzuje dopad změn v dotazníku.

    Args:
        changes: Seznam změn [{key, old_answer, new_answer, old_details, new_details}]
        old_risk_breakdown: Aktuální risk breakdown firmy

    Returns:
        {
            impact_level: "none" | "low" | "medium" | "high" | "critical",
            risk_change: "unchanged" | "escalated" | "de-escalated",
            affected_documents: ["compliance_report", ...],
            changes_detail: [...],
            summary_cz: "Popis změny...",
            needs_amendment: bool,
        }
    """
    if not changes:
        return {
            "impact_level": "none",
            "risk_change": "unchanged",
            "affected_documents": [],
            "changes_detail": [],
            "summary_cz": "Žádné změny nebyly detekovány.",
            "needs_amendment": False,
        }

    affected_docs_set: set[str] = set()
    changes_detail: list[dict] = []
    max_impact_score = 0
    risk_escalated = False
    risk_deescalated = False

    for change in changes:
        key = change["key"]
        old_val = change.get("old_answer", "")
        new_val = change.get("new_answer", "")

        # Kontaktní údaje — žádný dopad
        if key in CONTACT_KEYS:
            changes_detail.append({
                "key": key,
                "impact": "none",
                "risk_hint": None,
                "affected_docs": [],
                "description": f"Změna kontaktního údaje ({key})",
            })
            continue

        impact_info = QUESTION_IMPACT_MAP.get(key)

        if not impact_info:
            # Neznámá otázka — konzervativně medium
            changes_detail.append({
                "key": key,
                "impact": "medium",
                "risk_hint": "limited",
                "affected_docs": ["compliance_report"],
                "description": f"Změna odpovědi: {key}",
            })
            affected_docs_set.add("compliance_report")
            max_impact_score = max(max_impact_score, 10)
            continue

        risk_hint = impact_info["risk_hint"]
        docs = impact_info["affected_docs"]
        affected_docs_set.update(docs)

        # Určit impact score podle typu změny
        weight = RISK_WEIGHT.get(risk_hint, 5)

        if old_val == "no" and new_val == "yes":
            # Zapnutí AI systému — eskalace
            impact_score = weight * 2
            risk_escalated = True
            desc = f"Nasazení nového AI systému: {key} (ne → ano)"
        elif old_val == "yes" and new_val == "no":
            # Vypnutí AI systému — de-eskalace
            impact_score = weight
            risk_deescalated = True
            desc = f"Odstranění AI systému: {key} (ano → ne)"
        elif old_val == "unknown" and new_val == "yes":
            # Potvrzení "nevím" → ano
            impact_score = weight * 1.5
            risk_escalated = True
            desc = f"Potvrzení AI systému: {key} (nevím → ano)"
        elif old_val == "unknown" and new_val == "no":
            # Vyloučení "nevím" → ne
            impact_score = weight * 0.5
            risk_deescalated = True
            desc = f"Vyloučení AI systému: {key} (nevím → ne)"
        else:
            # Jiná změna (text, multi_select, ...)
            impact_score = weight * 0.7
            desc = f"Změna odpovědi: {key} ({old_val} → {new_val})"

        max_impact_score = max(max_impact_score, impact_score)
        changes_detail.append({
            "key": key,
            "impact": _score_to_level(impact_score),
            "risk_hint": risk_hint,
            "affected_docs": docs,
            "description": desc,
        })

    # Celkový impact level
    if max_impact_score >= 100:
        impact_level = "critical"
    elif max_impact_score >= 30:
        impact_level = "high"
    elif max_impact_score >= 10:
        impact_level = "medium"
    elif max_impact_score > 0:
        impact_level = "low"
    else:
        impact_level = "none"

    # Risk change
    if risk_escalated and not risk_deescalated:
        risk_change = "escalated"
    elif risk_deescalated and not risk_escalated:
        risk_change = "de-escalated"
    elif risk_escalated and risk_deescalated:
        risk_change = "escalated"  # konzervativní
    else:
        risk_change = "unchanged"

    # Souhrn
    affected_docs = sorted(affected_docs_set)
    substantive = [c for c in changes_detail if c["impact"] != "none"]

    if not substantive:
        summary = "Změna se týká pouze kontaktních údajů — dokumenty zůstávají v platnosti."
        needs_amendment = False
    else:
        parts = []
        for c in substantive:
            parts.append(c["description"])
        summary = " ".join(parts) + f" Dotčeno {len(affected_docs)} dokumentů."
        needs_amendment = True

    logger.info(
        f"[M7] Impact analysis: {impact_level}, risk_change={risk_change}, "
        f"affected_docs={len(affected_docs)}, changes={len(substantive)}"
    )

    return {
        "impact_level": impact_level,
        "risk_change": risk_change,
        "affected_documents": affected_docs,
        "changes_detail": changes_detail,
        "summary_cz": summary,
        "needs_amendment": needs_amendment,
    }


def _score_to_level(score: float) -> str:
    if score >= 100:
        return "critical"
    if score >= 30:
        return "high"
    if score >= 10:
        return "medium"
    if score > 0:
        return "low"
    return "none"
