"""
AIshield.cz — Dashboard API
Endpointy pro zákaznický portál — přehled compliance stavu,
dokumenty, skeny, akční plán.
"""

from fastapi import APIRouter, Depends, HTTPException
from backend.database import get_supabase
from backend.api.auth import AuthUser, get_current_user

router = APIRouter()


@router.get("/me")
async def get_my_dashboard(user: AuthUser = Depends(get_current_user)):
    """
    Vrátí kompletní data pro dashboard přihlášeného uživatele.
    Najde firmu podle emailu z JWT tokenu.
    """
    web_url = user.metadata.get("web_url", "") if user.metadata else ""
    return await _load_dashboard(user.email, web_url=web_url)


@router.get("/{user_email}")
async def get_dashboard_data(user_email: str, user: AuthUser = Depends(get_current_user)):
    """
    Vrátí dashboard data pro konkrétní email.
    Uživatel může přistoupit pouze ke svým datům (nebo admin k jakýmkoliv).
    """
    from backend.api.auth import ADMIN_EMAILS

    # Uživatel může vidět jen svá data, admin může vidět všechna
    if user.email != user_email and user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Přístup odepřen")

    web_url = user.metadata.get("web_url", "") if user.metadata else ""
    return await _load_dashboard(user_email, web_url=web_url)


async def _load_dashboard(user_email: str, web_url: str = ""):
    """Interní funkce — načte dashboard data pro daný email."""
    supabase = get_supabase()

    # 1. Najít firmu podle emailu
    company_res = supabase.table("companies").select("*").eq(
        "email", user_email
    ).execute()

    company = company_res.data[0] if company_res.data else None

    # 1b. Fallback: zkusit najít podle web_url z user_metadata
    #     (pro případ, že sken proběhl dříve než se propojil email)
    if not company and web_url:
        url_variants = [web_url]
        # Zkusit i varianty s/bez www
        if "://www." in web_url:
            url_variants.append(web_url.replace("://www.", "://"))
        else:
            url_variants.append(web_url.replace("://", "://www."))
        for url_v in url_variants:
            company_res2 = supabase.table("companies").select("*").eq(
                "url", url_v
            ).limit(1).execute()
            if company_res2.data:
                company = company_res2.data[0]
                # Propojíme — nastavíme email na company, aby příště fungovalo rovnou
                try:
                    supabase.table("companies").update(
                        {"email": user_email}
                    ).eq("id", company["id"]).execute()
                except Exception:
                    pass
                break

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

    # 3. Nálezy (z posledního skenu) — filtrujeme false positives
    findings = []
    # Nástroje, které NEJSOU AI systémy (pro zpětnou kompatibilitu se starými skeny)
    NON_AI_TOOLS = {"google tag manager", "google analytics 4", "seznam retargeting", "heureka"}
    if scans_res.data:
        latest_scan_id = scans_res.data[0]["id"]
        findings_res = supabase.table("findings").select("*").eq(
            "scan_id", latest_scan_id
        ).neq("source", "ai_classified_fp").neq(
            "risk_level", "none"
        ).order("risk_level", desc=True).execute()
        # Bezpečnostní filtr: vyřadíme i staré záznamy non-AI nástrojů
        findings = [
            f for f in (findings_res.data or [])
            if f.get("name", "").lower() not in NON_AI_TOOLS
        ]

    # 4. Dokumenty
    docs_res = supabase.table("documents").select("*").eq(
        "company_id", company_id
    ).order("created_at", desc=True).execute()

    # 5. Objednávky
    orders_res = supabase.table("orders").select("*").eq(
        "email", user_email
    ).order("created_at", desc=True).execute()

    # 6. Dotazník — přes tabulku clients (client.company_id → questionnaire_responses.client_id)
    questionnaire_status = "nevyplněn"
    try:
        # Najdi klienta pro tuto firmu
        client_res = supabase.table("clients").select("id").eq(
            "company_id", company_id
        ).limit(1).execute()
        if client_res.data:
            client_id = client_res.data[0]["id"]
            quest_res = supabase.table("questionnaire_responses").select("id").eq(
                "client_id", client_id
            ).limit(1).execute()
            questionnaire_status = "dokončen" if quest_res.data else "nevyplněn"
    except Exception:
        pass  # Tabulka nemusí existovat

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
