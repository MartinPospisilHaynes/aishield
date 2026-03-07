"""
AIshield.cz — Shoptet Addon: Pydantic modely
Datové struktury pro wizard, scan, compliance stránku a API komunikaci.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Wizard modely
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AISystemEntry(BaseModel):
    """Jeden AI systém zadaný ve wizardu."""
    provider: str = Field(..., min_length=1, max_length=200)
    ai_type: Literal["chatbot", "recommendation", "content", "pricing", "search", "other"]
    custom_note: str = ""


class WizardRequest(BaseModel):
    """Request z frontend wizardu — odpovědi e-shopaře."""
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
    compliance_page_published: bool = False
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
