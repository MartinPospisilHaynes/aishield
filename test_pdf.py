"""Test PDF generatoru."""
from backend.documents.templates import render_compliance_report
from backend.documents.pdf_generator import html_to_pdf

data = {
    "company_name": "TestFirma s.r.o.",
    "url": "https://testfirma.cz",
    "findings": [
        {"name": "ChatGPT Widget", "category": "chatbot", "risk_level": "limited", "ai_act_article": "cl. 50", "action_required": "Pridat oznaceni"},
    ],
    "risk_breakdown": {"high": 0, "limited": 1, "minimal": 0},
    "overall_risk": "limited",
    "recommendations": [],
    "questionnaire_ai_systems": 1,
    "contact_email": "info@testfirma.cz",
    "action_items": [],
}

html = render_compliance_report(data)
print(f"HTML: {len(html)} znaku")

pdf = html_to_pdf(html)
print(f"PDF: {len(pdf)} bytes")

with open("/tmp/test_aishield.pdf", "wb") as f:
    f.write(pdf)
print("PDF ulozen: /tmp/test_aishield.pdf")
