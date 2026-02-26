"""
AIshield.cz — Enterprise Inquiry API
Přijímá poptávky z enterprise formuláře a odesílá notifikační email.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from backend.outbound.email_engine import send_email

router = APIRouter()


class EnterpriseInquiry(BaseModel):
    company_name: str
    ico: Optional[str] = ""
    website: Optional[str] = ""
    industry: str
    company_size: str
    contact_name: str
    contact_role: Optional[str] = ""
    contact_email: EmailStr
    contact_phone: Optional[str] = ""
    ai_systems: list[str]
    services_needed: list[str]
    urgency: str
    budget: Optional[str] = ""
    notes: Optional[str] = ""


URGENCY_MAP = {
    "asap": "🔴 Co nejdříve — mají deadline",
    "month": "🟠 Do 1 měsíce",
    "quarter": "🟡 Do 3 měsíců",
    "exploring": "🟢 Zatím mapují možnosti",
}


def _build_html(data: EnterpriseInquiry) -> str:
    ai_list = "".join(f"<li>{s}</li>" for s in data.ai_systems)
    svc_list = "".join(f"<li>{s}</li>" for s in data.services_needed)
    urgency_label = URGENCY_MAP.get(data.urgency, data.urgency)

    return f"""
    <div style="font-family: -apple-system, Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: linear-gradient(135deg, #7c3aed 0%, #db2777 100%); padding: 24px 32px; border-radius: 12px 12px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 22px;">🏢 Nová ENTERPRISE poptávka</h1>
            <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0; font-size: 14px;">{data.company_name}</p>
        </div>

        <div style="background: #1e1e2e; padding: 24px 32px; color: #e2e8f0;">
            <h2 style="color: #c084fc; font-size: 16px; margin-top: 0;">📋 Firma</h2>
            <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <tr><td style="color: #94a3b8; padding: 4px 0; width: 120px;">Název:</td><td style="color: white;">{data.company_name}</td></tr>
                <tr><td style="color: #94a3b8; padding: 4px 0;">IČO:</td><td>{data.ico or '—'}</td></tr>
                <tr><td style="color: #94a3b8; padding: 4px 0;">Web:</td><td><a href="{data.website}" style="color: #c084fc;">{data.website or '—'}</a></td></tr>
                <tr><td style="color: #94a3b8; padding: 4px 0;">Odvětví:</td><td>{data.industry}</td></tr>
                <tr><td style="color: #94a3b8; padding: 4px 0;">Velikost:</td><td>{data.company_size}</td></tr>
            </table>

            <h2 style="color: #c084fc; font-size: 16px; margin-top: 20px;">👤 Kontakt</h2>
            <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                <tr><td style="color: #94a3b8; padding: 4px 0; width: 120px;">Jméno:</td><td style="color: white;">{data.contact_name}</td></tr>
                <tr><td style="color: #94a3b8; padding: 4px 0;">Pozice:</td><td>{data.contact_role or '—'}</td></tr>
                <tr><td style="color: #94a3b8; padding: 4px 0;">Email:</td><td><a href="mailto:{data.contact_email}" style="color: #c084fc;">{data.contact_email}</a></td></tr>
                <tr><td style="color: #94a3b8; padding: 4px 0;">Telefon:</td><td>{data.contact_phone or '—'}</td></tr>
            </table>

            <h2 style="color: #c084fc; font-size: 16px; margin-top: 20px;">🤖 AI systémy</h2>
            <ul style="margin: 0; padding-left: 20px; font-size: 14px;">{ai_list}</ul>

            <h2 style="color: #c084fc; font-size: 16px; margin-top: 20px;">🎯 Požadované služby</h2>
            <ul style="margin: 0; padding-left: 20px; font-size: 14px;">{svc_list}</ul>

            <h2 style="color: #c084fc; font-size: 16px; margin-top: 20px;">⏰ Urgence</h2>
            <p style="font-size: 14px; margin: 4px 0;">{urgency_label}</p>

            {"<h2 style='color: #c084fc; font-size: 16px; margin-top: 20px;'>💰 Budget</h2><p style='font-size: 14px; margin: 4px 0;'>" + data.budget + "</p>" if data.budget else ""}

            {"<h2 style='color: #c084fc; font-size: 16px; margin-top: 20px;'>📝 Poznámka</h2><p style='font-size: 14px; margin: 4px 0;'>" + data.notes + "</p>" if data.notes else ""}
        </div>

        <div style="background: #0f0f1a; padding: 16px 32px; border-radius: 0 0 12px 12px; text-align: center;">
            <p style="color: #64748b; font-size: 12px; margin: 0;">
                Odesláno z enterprise formuláře na aishield.cz
            </p>
        </div>
    </div>
    """


@router.post("/enterprise-inquiry")
async def enterprise_inquiry(data: EnterpriseInquiry):
    """Přijme enterprise poptávku a odešle notifikační email."""
    try:
        html = _build_html(data)

        # Odeslat notifikaci na info@aishield.cz
        await send_email(
            to="info@aishield.cz",
            subject=f"🏢 ENTERPRISE poptávka: {data.company_name} ({data.industry})",
            html=html,
            from_email="info@aishield.cz",
            from_name="AIshield Enterprise",
        )

        return {
            "status": "ok",
            "message": "Poptávka byla úspěšně odeslána. Ozveme se do 24 hodin.",
        }

    except Exception as e:
        print(f"[Enterprise] Chyba při odesílání poptávky: {e}")
        raise HTTPException(
            status_code=500,
            detail="Nepodařilo se odeslat poptávku. Zkuste to prosím znovu.",
        )
