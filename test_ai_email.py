import asyncio
import json

async def main():
    from backend.scanner.web_scanner import WebScanner
    from backend.scanner.detector import detect_ai_systems
    from backend.outbound.company_info import get_company_info, extract_ico_from_html
    from backend.outbound.email_writer import write_email

    # 1. Scan webu
    print("=== 1. Skenování webu ===")
    scanner = WebScanner(wait_after_load_ms=8000)
    page = await scanner.scan("https://www.desperados-design.cz")
    print(f"HTML: {len(page.html)} znaků, Scripts: {len(page.scripts)}, Network: {len(page.network_requests)}")

    # 2. Detekce AI systémů
    print("\n=== 2. Detekce AI ===")
    detections = detect_ai_systems(page)
    print(f"Nalezeno {len(detections)} AI systémů")
    for d in detections[:5]:
        print(f"  - {d.name} ({d.risk_level}, conf={d.confidence})")

    # 3. Company info (ARES + web)
    print("\n=== 3. Company info ===")
    ico = extract_ico_from_html(page.html)
    print(f"IČO z HTML: {ico}")
    info = await get_company_info(
        url="desperados-design.cz",
        html=page.html,
        ico=ico,
    )
    print(f"Firma: {info.company_name}")
    print(f"Právní forma: {info.legal_form} ({info.legal_form_code})")
    print(f"Kontakt: {info.contact_person} ({info.contact_role})")
    print(f"Email: {info.contact_email}")
    print(f"Telefon: {info.contact_phone}")
    print(f"Adresa: {info.address}")

    # 4. Gemini píše email
    print("\n=== 4. Gemini píše email ===")
    findings_dicts = [
        {
            "name": d.name,
            "category": d.category,
            "risk_level": d.risk_level,
            "ai_act_article": d.ai_act_article,
            "action_required": d.action_required,
            "description": d.description_cs,
        }
        for d in detections[:6]
    ]

    email = await write_email(
        company_name=info.company_name,
        company_url="desperados-design.cz",
        contact_person=info.contact_person,
        contact_role=info.contact_role,
        legal_form=info.legal_form,
        findings=findings_dicts,
        scan_id="d8d43f59-83dd-4cdd-bd9b-6d81819fd77d",
        extra_context="Web otevřeně přiznává, že obsah je generován AI. Web nabízí chatbot služby.",
    )

    print(f"\nSubject: {email.subject}")
    print(f"Tokens: {email.tokens_used}")
    print(f"\n--- BODY (raw) ---")
    import re
    body_text = re.sub(r'<[^>]+>', '', email.body_html)
    body_text = body_text.strip()
    lines = [l.strip() for l in body_text.split('\n') if l.strip()]
    for line in lines[:30]:
        print(line)

asyncio.run(main())
