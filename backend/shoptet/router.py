"""
AIshield.cz — Shoptet Addon: FastAPI Router
Všechny endpointy pro Shoptet addon.
Prefix: /shoptet (registruje se v main.py)
"""

import logging

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from backend.shoptet.compliance_page import publish_compliance_page
from backend.shoptet.installer import handle_install
from backend.shoptet.models import DashboardData, WizardRequest, WizardResponse
from backend.shoptet.webhooks import handle_webhook
from backend.shoptet.wizard import get_ai_systems, process_wizard
from backend.database import get_supabase

logger = logging.getLogger("shoptet.router")

router = APIRouter()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Instalace — Shoptet volá tento endpoint
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/install")
async def install_addon(code: str = Query(..., min_length=10)):
    """
    GET /shoptet/install?code=<CODE>
    Shoptet volá po kliknutí "Instalovat" v Addon marketu.
    Musí odpovědět do 5 sekund.
    """
    try:
        result = await handle_install(code)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Instalace selhala: {e}")
        raise HTTPException(status_code=500, detail="Instalace addonu selhala")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Webhook — Shoptet události
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.post("/webhook")
async def webhook_handler(request: Request):
    """
    POST /shoptet/webhook
    Shoptet posílá události: addon:suspend, addon:uninstall, addon:prolong.
    IP whitelist: 185.184.254.0/24
    HMAC SHA-1 verifikace.
    """
    body = await request.body()
    signature = request.headers.get("Shoptet-Webhook-Signature", "")
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Neplatný JSON")

    event = payload.get("event", "")
    eshop_id = payload.get("eshopId", 0)

    try:
        result = await handle_webhook(event, eshop_id, body, signature, client_ip)
        return JSONResponse(content=result)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Webhook chyba: {e}")
        raise HTTPException(status_code=500, detail="Webhook zpracování selhalo")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Wizard — vyplnění sebehodnocení
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.post("/wizard/{installation_id}", response_model=WizardResponse)
async def submit_wizard(installation_id: str, wizard_data: WizardRequest):
    """
    POST /shoptet/wizard/<installation_id>
    E-shopař vyplní wizard s AI systémy, backend klasifikuje a uloží.
    """
    # Ověřit, že instalace existuje
    sb = get_supabase()
    inst = sb.table("shoptet_installations").select("id, status").eq(
        "id", installation_id,
    ).execute()

    if not inst.data:
        raise HTTPException(status_code=404, detail="Instalace nenalezena")
    if inst.data[0].get("status") != "active":
        raise HTTPException(status_code=403, detail="Instalace není aktivní")

    try:
        return await process_wizard(installation_id, wizard_data)
    except Exception as e:
        logger.error(f"Wizard chyba: {e}")
        raise HTTPException(status_code=500, detail="Zpracování wizardu selhalo")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Compliance stránka — publikace
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.post("/compliance-page/{installation_id}")
async def publish_page(installation_id: str):
    """
    POST /shoptet/compliance-page/<installation_id>
    Vygeneruje a publikuje compliance stránku na Shoptet eshop.
    """
    sb = get_supabase()
    inst = sb.table("shoptet_installations").select("id, status").eq(
        "id", installation_id,
    ).execute()

    if not inst.data:
        raise HTTPException(status_code=404, detail="Instalace nenalezena")
    if inst.data[0].get("status") != "active":
        raise HTTPException(status_code=403, detail="Instalace není aktivní")

    try:
        result = await publish_compliance_page(installation_id)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Publikace compliance stránky selhala: {e}")
        raise HTTPException(status_code=500, detail="Publikace stránky selhala")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Dashboard — data pro admin panel
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@router.get("/dashboard/{installation_id}")
async def get_dashboard(installation_id: str):
    """
    GET /shoptet/dashboard/<installation_id>
    Vrátí kompletní data pro admin dashboard v Shoptet iframe.
    """
    sb = get_supabase()

    # Instalace
    inst = sb.table("shoptet_installations").select("*").eq(
        "id", installation_id,
    ).execute()

    if not inst.data:
        raise HTTPException(status_code=404, detail="Instalace nenalezena")

    installation = inst.data[0]

    # AI systémy
    ai_systems = await get_ai_systems(installation_id)

    # Compliance stránka
    page = sb.table("shoptet_compliance_pages").select("*").eq(
        "installation_id", installation_id,
    ).execute()
    page_published = bool(page.data and page.data[0].get("published_at"))

    # Dokumenty
    docs = sb.table("shoptet_documents").select("*").eq(
        "installation_id", installation_id,
    ).execute()

    # Compliance skóre
    base_score = 40 if installation.get("wizard_completed_at") else 0
    systems_bonus = min(len(ai_systems) * 10, 30)
    page_bonus = 30 if page_published else 0
    score = base_score + systems_bonus + page_bonus

    return {
        "installation": {
            "id": installation["id"],
            "eshop_id": installation.get("eshop_id"),
            "eshop_url": installation.get("eshop_url"),
            "eshop_name": installation.get("eshop_name"),
            "language": installation.get("language", "cs"),
            "plan": installation.get("plan", "basic"),
            "status": installation.get("status"),
            "wizard_completed_at": installation.get("wizard_completed_at"),
            "installed_at": installation.get("installed_at"),
        },
        "ai_systems": ai_systems,
        "compliance_score": score,
        "compliance_page_published": page_published,
        "documents": docs.data or [],
        "art50_deadline": "2026-08-02",
        "art4_active_since": "2025-02-02",
    }
