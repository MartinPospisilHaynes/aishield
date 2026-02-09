"""E2E test: scan + company info + template v5 email + send."""
import asyncio
import json
import os

from backend.scanner.web_scanner import scan_url
from backend.scanner.detector import detect_ai_systems
from backend.outbound.company_info import get_company_info
from backend.outbound.email_writer import write_email
from backend.outbound.email_engine import send_email


async def main():
    print("[1] Sken desperados-design.cz...")
    page = await scan_url("https://www.desperados-design.cz")
    detections = detect_ai_systems(page)
    print(f"    {len(detections)} AI systemu")

    print("[2] Company info...")
    ci = await get_company_info("https://www.desperados-design.cz", page.html)
    print(f"    {ci.company_name}, {ci.contact_person}")

    findings = [
        {
            "name": d.name,
            "category": d.category,
            "risk_level": d.risk_level,
            "ai_act_article": d.ai_act_article,
            "action_required": d.action_required,
            "description": d.description_cs,
        }
        for d in detections
    ]

    print("[3] Gemini skloňuje jméno + šablona sestavuje email...")
    result = await write_email(
        company_name=ci.company_name or "Desperados Design",
        company_url="https://www.desperados-design.cz",
        contact_person=ci.contact_person,
        contact_role=ci.contact_role,
        legal_form=ci.legal_form,
        findings=findings,
    )

    print(f"    subject: {result.subject}")
    print(f"    html: {len(result.body_html)} znaku")
    print(f"    model: {result.model}, tokens: {result.tokens_used}")

    # Ulož HTML do souboru pro kontrolu
    with open("/tmp/email_v5_preview.html", "w") as f:
        f.write(result.body_html)
    print("    HTML uložen do /tmp/email_v5_preview.html")

    print("[4] Odesilam email na info@desperados-design.cz...")
    send_result = await send_email(
        to="info@desperados-design.cz",
        subject=result.subject,
        html=result.body_html,
    )
    print(f"    Vysledek: {send_result}")
    print("\nHOTOVO!")


if __name__ == "__main__":
    asyncio.run(main())
