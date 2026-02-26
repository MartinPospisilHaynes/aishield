import asyncio

async def main():
    from backend.scanner.web_scanner import WebScanner
    from backend.scanner.detector import detect_ai_systems
    from backend.outbound.company_info import get_company_info, extract_ico_from_html
    from backend.outbound.email_writer import write_email, _wrap_email_html
    from backend.outbound.email_engine import send_email

    # 1. Scan webu
    print("Skenování...")
    scanner = WebScanner(wait_after_load_ms=8000)
    page = await scanner.scan("https://www.desperados-design.cz")

    # 2. Detekce
    detections = detect_ai_systems(page)
    print(f"Nalezeno {len(detections)} AI systémů")

    # 3. Company info
    ico = extract_ico_from_html(page.html)
    info = await get_company_info(url="desperados-design.cz", html=page.html, ico=ico)
    print(f"Kontakt: {info.contact_person} ({info.legal_form})")

    # 4. Gemini píše email
    print("Gemini píše email...")
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
        extra_context="Web otevřeně přiznává, že obsah je generován AI. Web nabízí chatbot služby poháněné Gemini.",
    )

    # Re-wrap s unsubscribe linkem
    from urllib.parse import quote
    body_inner = email.body_html.split('<body')[1].split('>', 1)[1].rsplit('<hr', 1)[0]
    unsubscribe = f"https://api.aishield.cz/api/unsubscribe?email={quote('info@desperados-design.cz')}&company={quote('desperados-design.cz')}"
    
    final_html = f"""<!DOCTYPE html>
<html lang="cs">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #222; line-height: 1.6; font-size: 15px; background: #fff;">

{body_inner}

<hr style="border: none; border-top: 1px solid #ddd; margin: 32px 0 16px 0;">
<p style="font-size: 11px; color: #999; line-height: 1.4;">
    Jednorázové upozornění na základě veřejně dostupné analýzy webu desperados-design.cz.<br>
    AIshield.cz | Martin Haynes, IČO: 17889251 | Mlýnská 53, 783 53 Velká Bystřice<br>
    <a href="{unsubscribe}" style="color: #999;">Nechci dostávat další upozornění</a>
</p>

</body>
</html>"""

    # 5. Odeslat
    print(f"\nSubject: {email.subject}")
    print(f"Tokens: {email.tokens_used}")
    
    result = await send_email(
        to="info@desperados-design.cz",
        subject=email.subject,
        html=final_html,
    )
    print(f"\nOdesláno: {result}")

asyncio.run(main())
