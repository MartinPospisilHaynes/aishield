"""
AIshield.cz — Contact Form API
Přijme data z kontaktního formuláře, uloží do Supabase a odešle notifikaci.
"""

import logging
import os
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

logger = logging.getLogger(__name__)

router = APIRouter()


class ContactRequest(BaseModel):
    name: str
    email: str
    phone: str = ""
    company: str = ""
    message: str = ""


class ContactResponse(BaseModel):
    ok: bool
    message: str = ""


def _save_to_supabase(data: dict) -> bool:
    """Uloží kontakt do tabulky contact_submissions."""
    try:
        from supabase import create_client
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not url or not key:
            logger.warning("Supabase nedostupný — kontakt neuložen")
            return False
        sb = create_client(url, key)
        sb.table("contact_submissions").insert(data).execute()
        return True
    except Exception as e:
        logger.error(f"Supabase contact save error: {e}")
        return False


async def _send_notification(req: ContactRequest) -> bool:
    """Odešle notifikační email přes Resend API."""
    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key:
        logger.warning("RESEND_API_KEY chybí — notifikace neodeslána")
        return False

    # Notifikace na firemní email
    notify_to = os.environ.get("CONTACT_NOTIFY_EMAIL", "info@desperados-design.cz")

    subject = f"[AIshield] Nový kontakt: {req.name}"
    if req.company:
        subject += f" ({req.company})"

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #a855f7;">Nový kontakt z webu AIshield.cz</h2>
        <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 10px; font-weight: bold; width: 120px;">Jméno:</td>
                <td style="padding: 10px;">{req.name}</td>
            </tr>
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 10px; font-weight: bold;">E-mail:</td>
                <td style="padding: 10px;"><a href="mailto:{req.email}">{req.email}</a></td>
            </tr>
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 10px; font-weight: bold;">Telefon:</td>
                <td style="padding: 10px;">{req.phone or '—'}</td>
            </tr>
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 10px; font-weight: bold;">Firma/Web:</td>
                <td style="padding: 10px;">{req.company or '—'}</td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold; vertical-align: top;">Zpráva:</td>
                <td style="padding: 10px; white-space: pre-wrap;">{req.message or '—'}</td>
            </tr>
        </table>
        <p style="margin-top: 20px; color: #888; font-size: 12px;">
            Odesláno z kontaktního formuláře na aishield.cz
        </p>
    </div>
    """

    # Kdo je odesílatel — použít doménu, kde Resend funguje
    from_email = os.environ.get("EMAIL_FROM", "info@aishield.cz")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": f"AIshield.cz <{from_email}>",
                    "to": [notify_to],
                    "subject": subject,
                    "html": html_body,
                    "reply_to": req.email,
                },
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                logger.info(f"Contact notification sent: {data.get('id')}")
                return True
            else:
                logger.error(f"Resend error {resp.status_code}: {resp.text[:300]}")
                return False
    except Exception as e:
        logger.error(f"Contact notification error: {e}")
        return False


@router.post("/contact", response_model=ContactResponse)
async def contact(req: ContactRequest):
    """Kontaktní formulář — uloží data a pošle notifikaci."""

    # Validace
    if not req.name.strip() or not req.email.strip():
        raise HTTPException(status_code=400, detail="Jméno a e-mail jsou povinné.")

    if len(req.message) > 5000:
        raise HTTPException(status_code=400, detail="Zpráva je příliš dlouhá.")

    # Uložit do Supabase
    db_data = {
        "name": req.name.strip(),
        "email": req.email.strip(),
        "phone": req.phone.strip() if req.phone else None,
        "company": req.company.strip() if req.company else None,
        "message": req.message.strip() if req.message else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    saved = _save_to_supabase(db_data)

    # Poslat notifikaci
    notified = await _send_notification(req)

    if not saved and not notified:
        logger.error("Contact form: Ani uložení ani notifikace nefungovaly!")
        # I tak vrátíme OK — nechceme frustrovat uživatele
        # Data alespoň zalogujeme
        logger.warning(f"LOST CONTACT: {req.name} / {req.email} / {req.message[:200]}")

    return ContactResponse(ok=True, message="Děkujeme! Ozveme se vám co nejdříve.")
