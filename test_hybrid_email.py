"""
AIshield — End-to-end test: scan → detect → ARES → Gemini 2.5 → hybrid email → send
"""
import asyncio
import sys
import os
import json

# Přidáme backend do PYTHONPATH
sys.path.insert(0, "/opt/aishield")
os.chdir("/opt/aishield")

# Načteme env
from dotenv import load_dotenv
load_dotenv("/opt/aishield/.env")


async def main():
    from backend.outbound.email_writer import generate_outbound_email, GEMINI_MODEL
    from backend.outbound.email_engine import send_email, check_delivery_status
    from backend.scanner.detector import detect_ai_systems
    from backend.scanner.web_scanner import ScannedPage
    import httpx

    TARGET_URL = "https://desperados-design.cz"
    TARGET_EMAIL = "info@desperados-design.cz"
    SCAN_ID = "d8d43f59-83dd-4cdd-bd9b-6d81819fd77d"
    SCREENSHOT_URL = "https://rsxwqcrkttlfnqbjgpgc.supabase.co/storage/v1/object/public/screenshots/scans/d8d43f59-83dd-4cdd-bd9b-6d81819fd77d/viewport.png"

    print(f"🚀 Gemini model: {GEMINI_MODEL}")
    print(f"🎯 Target: {TARGET_URL} → {TARGET_EMAIL}")
    print()

    # 1. Fetch HTML
    print("1️⃣  Fetching HTML...")
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(TARGET_URL)
        html = resp.text
    print(f"   HTML: {len(html)} chars")

    # 2. Detect AI systems
    print("2️⃣  Detecting AI systems...")
    page = ScannedPage(url=TARGET_URL, html=html, final_url=TARGET_URL)
    detections = detect_ai_systems(page)
    # Convert DetectedAI objects to dicts for email_writer
    findings = []
    for d in detections:
        findings.append({
            "name": d.name,
            "category": d.category,
            "risk_level": d.risk_level,
            "ai_act_article": d.ai_act_article,
            "description": d.description_cs,
            "action_required": d.action_required,
        })
    print(f"   Found: {len(findings)} AI systems")
    for i, f in enumerate(findings[:5], 1):
        print(f"   {i}. {f['name']} ({f['risk_level']})")
    if len(findings) > 5:
        print(f"   ... a {len(findings)-5} dalších")

    # 3. Generate hybrid email (ARES + Gemini 2.5 + template)
    print()
    print("3️⃣  Generating hybrid email (Gemini 2.5 + HTML template)...")
    email = await generate_outbound_email(
        company_url=TARGET_URL,
        html=html,
        findings=findings,
        scan_id=SCAN_ID,
        screenshot_url=SCREENSHOT_URL,
        to_email=TARGET_EMAIL,
    )

    print(f"   ✅ Subject: {email.subject}")
    print(f"   ✅ Model: {email.model}")
    print(f"   ✅ Tokens: {email.tokens_used}")
    print(f"   ✅ HTML size: {len(email.body_html)} chars")

    # Check HTML has expected elements
    html_content = email.body_html
    checks = {
        "Header (gradient)": "gradient" in html_content,
        "Shield icon": "128737" in html_content or "🛡" in html_content,
        "Risk table": "AI systém" in html_content and "Riziko" in html_content,
        "Semaphore badges": any(b in html_content for b in ["Minimální", "Omezené", "Vysoké"]),
        "Screenshot": SCREENSHOT_URL in html_content,
        "Deadline box": "2. srpna 2026" in html_content,
        "Checklist": "Co je potřeba udělat" in html_content,
        "USP box": "kompletní řešení" in html_content,
        "CTA button": "compliance report" in html_content.lower(),
        "CEO signature": "Bc. Martin Haynes" in html_content and "CEO" in html_content,
        "Contact info": "+420 732 716 141" in html_content,
        "Unsubscribe": "unsubscribe" in html_content.lower(),
        "Pricing": "4 999" in html_content,
    }

    print()
    print("4️⃣  Template element checks:")
    all_ok = True
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"   {status} {check}")
        if not result:
            all_ok = False

    if not all_ok:
        print("\n   ⚠️  Some elements missing! Check template.")

    # 5. Save HTML for local preview
    with open("/tmp/hybrid_email_preview.html", "w") as f:
        f.write(html_content)
    print(f"\n   💾 Preview saved to /tmp/hybrid_email_preview.html")

    # 6. Send email
    print()
    print(f"5️⃣  Sending email to {TARGET_EMAIL}...")
    result = await send_email(
        to=TARGET_EMAIL,
        subject=email.subject,
        html=email.body_html,
        from_name="AIshield.cz",
    )
    resend_id = result.get("id", "")
    print(f"   ✅ Sent! Resend ID: {resend_id}")

    # 7. Check delivery status (after short delay)
    if resend_id and resend_id != "dry_run":
        print()
        print("6️⃣  Checking delivery status (after 5s)...")
        await asyncio.sleep(5)
        status = await check_delivery_status(resend_id)
        print(f"   📬 Status: {status.get('status', 'unknown')}")
        print(f"   Last event: {status.get('last_event', 'N/A')}")

    print()
    print("=" * 60)
    print("🎉 DONE! Check inbox at info@desperados-design.cz")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
