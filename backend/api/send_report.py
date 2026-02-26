"""
AIshield.cz — Send Report API endpoint
Přijme email + scan_id, vygeneruje branded HTML report a odešle ho.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from backend.database import get_supabase
from backend.outbound.email_engine import send_email
from backend.outbound.report_email import generate_report_email_html, generate_zero_findings_email_html
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class SendReportRequest(BaseModel):
    """Požadavek na odeslání reportu."""
    email: str


@router.post("/scan/{scan_id}/send-report")
async def send_scan_report(scan_id: str, request: SendReportRequest):
    """
    Odešle branded HTML report na zadaný email.
    1. Načte scan data z DB
    2. Vygeneruje HTML email
    3. Odešle přes Resend
    """
    supabase = get_supabase()

    try:
        # 1. Načteme scan
        scan_result = supabase.table("scans").select(
            "id, url_scanned, status, company_id"
        ).eq("id", scan_id).limit(1).execute()

        if not scan_result.data:
            raise HTTPException(status_code=404, detail="Sken nenalezen")

        scan = scan_result.data[0]

        if scan["status"] != "done":
            raise HTTPException(status_code=400, detail="Sken ještě není dokončen")

        # 2. Načteme firmu
        company = supabase.table("companies").select("name").eq(
            "id", scan["company_id"]
        ).limit(1).execute()
        company_name = company.data[0]["name"] if company.data else "Neznámá firma"

        # 3. Načteme findings (jen deployed, ne false positives)
        findings_result = supabase.table("findings").select(
            "name, category, risk_level, ai_act_article, action_required, "
            "ai_classification_text, source"
        ).eq("scan_id", scan_id).execute()

        deployed = [
            f for f in findings_result.data
            if f.get("source") != "ai_classified_fp"
        ]
        # Deduplikace — prefer deep_scan source over ai_classified
        seen_names = {}
        for f in deployed:
            fname = f.get("name", "")
            existing = seen_names.get(fname)
            if existing is None:
                seen_names[fname] = f
            elif f.get("source", "").startswith("deep_scan"):
                seen_names[fname] = f
        deployed = list(seen_names.values())


        # 4. Vygenerujeme HTML — jiný template pro 0 nálezů
        if len(deployed) == 0:
            html = generate_zero_findings_email_html(
                url=scan["url_scanned"],
                company_name=company_name,
                scan_id=scan_id,
            )
        else:
            html = generate_report_email_html(
                url=scan["url_scanned"],
                company_name=company_name,
                findings=deployed,
                scan_id=scan_id,
            )

        # 5. Odešleme email
        subject = f"AIshield.cz — Výsledky AI Act skenu pro {scan['url_scanned']}"
        result = await send_email(
            to=request.email,
            subject=subject,
            html=html,
            from_email="info@aishield.cz",
            from_name="AIshield.cz",
        )

        logger.info(f"Report sent to {request.email} for scan {scan_id}")

        # 6. Uložíme lead do DB (volitelné - pro CRM)
        try:
            supabase.table("report_leads").insert({
                "scan_id": scan_id,
                "email": request.email,
                "company_id": scan["company_id"],
            }).execute()
        except Exception:
            # Tabulka nemusí existovat — nevadí
            pass

        return {"status": "sent", "email": request.email}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Chyba při odesílání reportu: {str(e)}",
        )
