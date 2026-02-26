import asyncio
from backend.outbound.payment_emails import build_bank_transfer_email
from backend.outbound.email_engine import send_email

async def main():
    html, attachments = build_bank_transfer_email(
        order_number="AS-BASIC-TEST01",
        plan="basic",
        amount=4999,
        email="pospa69@seznam.cz",
        variable_symbol="1234567890",
        due_date="22. 02. 2026",
    )
    print(f"QR attachments count: {len(attachments)}")
    if attachments:
        print(f"Attachment: {attachments[0].get('filename')}, len={len(attachments[0].get('content', ''))}")

    result = await send_email(
        to="pospa69@seznam.cz",
        subject="AIshield.cz — Testovací email s QR kódem",
        html=html,
        from_email="info@aishield.cz",
        from_name="AIshield.cz",
        attachments=attachments if attachments else None,
    )
    print(f"Result: {result}")

asyncio.run(main())
