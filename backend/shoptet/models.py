"""
AIshield.cz — Shoptet Addon: Pydantic modely
Datové struktury pro wizard, scan, compliance stránku a API komunikaci.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Wizard modely (v1 — zachováno pro kompatibilitu)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AISystemEntry(BaseModel):
    """Jeden AI systém zadaný ve wizardu."""
    provider: str = Field(..., min_length=1, max_length=200)
    ai_type: Literal["chatbot", "recommendation", "content", "pricing", "search", "other"]
    custom_note: str = ""


class WizardRequest(BaseModel):
    """Request z frontend wizardu — odpovědi e-shopaře (v1 legacy)."""
    chatbots: list[AISystemEntry] = []
    content_ai: list[AISystemEntry] = []
    other_ai: list[AISystemEntry] = []


class WizardResponse(BaseModel):
    """Response po zpracování wizardu."""
    installation_id: str
    ai_systems_count: int
    compliance_score: int
    art50_relevant: int
    art4_relevant: int
    compliance_page_url: str | None = None
    message: str


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Dotazník v2 — 20 otázek pro e-shopy
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class QuestionnaireAnswer(BaseModel):
    """Jedna odpověď v dotazníku."""
    question_key: str = Field(..., min_length=1, max_length=100)
    answer: str | list[str] | bool
    details: dict = {}


class QuestionnaireRequest(BaseModel):
    """20-otázkový dotazník pro Shoptet e-shopy."""
    # Sekce 1: AI komunikace
    uses_ai_chatbot: str = "ne"
    chatbot_providers: list[str] = []
    uses_ai_email_auto: str = "ne"
    email_providers: list[str] = []

    # Sekce 2: AI obsah
    uses_chatgpt: str = "ne"
    chatgpt_providers: list[str] = []
    chatgpt_purposes: list[str] = []
    uses_ai_content: str = "ne"
    content_types: list[str] = []
    uses_ai_images: str = "ne"
    image_providers: list[str] = []

    # Sekce 3: AI v provozu
    uses_dynamic_pricing: str = "ne"
    uses_ai_recommendation: str = "ne"
    recommendation_providers: list[str] = []
    uses_ai_search: str = "ne"
    search_providers: list[str] = []
    uses_ai_decision: str = "ne"
    decision_types: list[str] = []
    uses_ai_for_children: str = "ne"

    # Sekce 4: Zaměstnanci
    has_ai_training: str = "ne"
    informs_employees: str = "ne"

    # Sekce 5: Data a bezpečnost
    ai_processes_personal_data: str = "ne"
    personal_data_types: list[str] = []
    ai_data_stored_eu: str = "nevim"

    # Sekce 6: Governance
    has_ai_guidelines: str = "ne"
    has_ai_register: str = "ne"
    has_oversight_person: str = "ne"
    can_override_ai: str = "nevim"

    # Sekce 7: Transparentnost
    has_transparency_page: str = "ne"
    wants_compliance_page: str = "ano"


class QuestionnaireResponse(BaseModel):
    """Response po zpracování dotazníku."""
    installation_id: str
    ai_systems_count: int
    compliance_score: int
    score_breakdown: dict
    art50_relevant: int
    art4_relevant: int
    risk_areas: list[dict] = []
    recommendations: list[str] = []
    plan: str = "free"
    message: str


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AI systém v DB
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AISystemRecord(BaseModel):
    """AI systém uložený v DB."""
    id: str
    installation_id: str
    source: Literal["wizard", "scanner", "manual"]
    provider: str
    ai_type: str
    ai_act_article: Literal["art50", "art4", "annex3", "none"]
    risk_level: Literal["minimal", "limited", "high"]
    confidence: Literal["confirmed", "probable", "possible", "manual_review"]
    is_active: bool = True
    details: dict = {}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Instalace
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class InstallationInfo(BaseModel):
    """Informace o instalaci addonu."""
    id: str
    eshop_id: int
    eshop_url: str | None = None
    eshop_name: str | None = None
    language: str = "cs"
    plan: str = "basic"
    status: str = "active"
    wizard_completed_at: str | None = None
    compliance_page_slug: str = "ai-compliance"
    installed_at: str


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Dashboard
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class DashboardData(BaseModel):
    """Data pro admin dashboard."""
    installation: InstallationInfo
    ai_systems: list[AISystemRecord] = []
    compliance_score: int = 0
    score_breakdown: dict = {}
    compliance_page_published: bool = False
    scan_completed: bool = False
    documents: list[dict] = []
    art50_deadline: str = "2026-08-02"
    art4_active_since: str = "2025-02-02"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Shoptet API modely
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ShoptetEshopInfo(BaseModel):
    """Informace o eshopu ze Shoptet API."""
    eshop_id: int
    name: str
    url: str
    email: str | None = None
    template_name: str | None = None
    language: str = "cs"


class ShoptetTokenResponse(BaseModel):
    """Odpověď z Shoptet OAuth serveru."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Klasifikační pravidla
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Mapování AI typu → AI Act článek + risk level
AI_ACT_CLASSIFICATION: dict[str, dict] = {
    "chatbot": {
        "ai_act_article": "art50",
        "risk_level": "limited",
        "description_cs": "AI chatbot — přímá komunikace se zákazníkem",
    },
    "content": {
        "ai_act_article": "art50",
        "risk_level": "limited",
        "description_cs": "AI-generovaný obsah viditelný zákazníkům",
    },
    "recommendation": {
        "ai_act_article": "art4",
        "risk_level": "minimal",
        "description_cs": "Doporučovací systém — nespadá pod Article 50",
    },
    "search": {
        "ai_act_article": "art4",
        "risk_level": "minimal",
        "description_cs": "AI vyhledávání — nespadá pod Article 50",
    },
    "pricing": {
        "ai_act_article": "art4",
        "risk_level": "minimal",
        "description_cs": "Dynamické ceny — server-side, bez UI interakce",
    },
    "other": {
        "ai_act_article": "art4",
        "risk_level": "minimal",
        "description_cs": "Ostatní AI systém — vyžaduje evidenci",
    },
}
