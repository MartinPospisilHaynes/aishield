"""Test šablon dokumentů."""
from backend.documents.templates import TEMPLATE_RENDERERS, TEMPLATE_NAMES

data = {
    "company_name": "TestFirma s.r.o.",
    "url": "https://testfirma.cz",
    "findings": [
        {"name": "ChatGPT Widget", "category": "chatbot", "risk_level": "limited", "ai_act_article": "cl. 50", "action_required": "Pridat oznaceni"},
        {"name": "Google Analytics 4", "category": "analytics", "risk_level": "minimal", "ai_act_article": "cl. 52", "action_required": ""},
    ],
    "risk_breakdown": {"high": 0, "limited": 1, "minimal": 1},
    "overall_risk": "limited",
    "recommendations": [
        {"tool_name": "HR AI Screening", "risk_level": "high", "ai_act_article": "cl. 6", "recommendation": "Conformity assessment"},
    ],
    "questionnaire_ai_systems": 3,
    "contact_email": "info@testfirma.cz",
    "action_items": [],
}

print(f"Sablony: {len(TEMPLATE_RENDERERS)}")
for key, renderer in TEMPLATE_RENDERERS.items():
    html = renderer(data)
    print(f"  OK {TEMPLATE_NAMES[key]}: {len(html)} znaku")

print("\nVsech 7 sablon OK!")
