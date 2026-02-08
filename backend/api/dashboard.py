"""
AIshield.cz — Dashboard API
Endpointy pro zákaznický portál — přehled compliance stavu,
dokumenty, skeny, akční plán.
"""

from fastapi import APIRouter, HTTPException
from backend.database import get_supabase

router = APIRouter()


@router.get("/{user_email}")
async def get_dashboard_data(user_email: str):
    """
    Vrátí kompletní data pro dashboard jednoho zákazníka.
    Najde firmu podle emailu, načte skeny, nálezy, dokumenty, objednávky.
    """
    supabase = get_supabase()

    # 1. Najít firmu podle emailu (nebo vrátit prázdný stav)
    company_res = supabase.table("companies").select("*").eq(
        "email", user_email
    ).execute()

    company = company_res.data[0] if company_res.data else None

    if not company:
        # Zkusit najít podle objednávky
        order_res = supabase.table("orders").select("*").eq(
            "email", user_email
        ).order("created_at", desc=True).execute()

        return {
            "company": None,
            "scans": [],
            "findings": [],
            "documents": [],
            "orders": order_res.data or [],
            "questionnaire_status": "nevyplněn",
            "compliance_score": None,
        }

    company_id = company["id"]

    # 2. Skeny
    scans_res = supabase.table("scans").select("*").eq(
        "company_id", company_id
    ).order("created_at", desc=True).limit(10).execute()

    # 3. Nálezy (z posledního skenu)
    findings = []
    if scans_res.data:
        latest_scan_id = scans_res.data[0]["id"]
        findings_res = supabase.table("findings").select("*").eq(
            "scan_id", latest_scan_id
        ).order("risk_level", desc=True).execute()
        findings = findings_res.data or []

    # 4. Dokumenty
    docs_res = supabase.table("documents").select("*").eq(
        "company_id", company_id
    ).order("created_at", desc=True).execute()

    # 5. Objednávky
    orders_res = supabase.table("orders").select("*").eq(
        "email", user_email
    ).order("created_at", desc=True).execute()

    # 6. Dotazník
    quest_res = supabase.table("questionnaire_answers").select("id").eq(
        "company_id", company_id
    ).limit(1).execute()
    questionnaire_status = "dokončen" if quest_res.data else "nevyplněn"

    # 7. Compliance skóre
    total_findings = len(findings)
    resolved = sum(
        1 for f in findings
        if f.get("confirmed_by_client") == "false_positive"
        or f.get("status") == "resolved"
    )
    compliance_score = (
        round((resolved / total_findings) * 100) if total_findings > 0 else None
    )

    return {
        "company": {
            "id": company_id,
            "name": company.get("name", ""),
            "url": company.get("url", ""),
            "created_at": company.get("created_at", ""),
        },
        "scans": [
            {
                "id": s["id"],
                "url": s.get("url", ""),
                "status": s.get("status", ""),
                "total_findings": s.get("total_findings", 0),
                "created_at": s.get("created_at", ""),
                "finished_at": s.get("finished_at"),
            }
            for s in (scans_res.data or [])
        ],
        "findings": [
            {
                "id": f["id"],
                "name": f.get("name", ""),
                "category": f.get("category", ""),
                "risk_level": f.get("risk_level", ""),
                "ai_act_article": f.get("ai_act_article", ""),
                "action_required": f.get("action_required", ""),
                "confirmed_by_client": f.get("confirmed_by_client"),
                "status": f.get("status", "open"),
            }
            for f in findings
        ],
        "documents": [
            {
                "id": d["id"],
                "template_key": d.get("template_key", ""),
                "name": d.get("name", ""),
                "file_url": d.get("file_url", ""),
                "created_at": d.get("created_at", ""),
            }
            for d in (docs_res.data or [])
        ],
        "orders": [
            {
                "order_number": o.get("order_number", ""),
                "plan": o.get("plan", ""),
                "amount": o.get("amount", 0),
                "status": o.get("status", ""),
                "created_at": o.get("created_at", ""),
                "paid_at": o.get("paid_at"),
            }
            for o in (orders_res.data or [])
        ],
        "questionnaire_status": questionnaire_status,
        "compliance_score": compliance_score,
    }
