"""
AIshield.cz — Admin API
Přehledový dashboard, manuální ovládání orchestrátoru,
email health monitoring.
"""

from fastapi import APIRouter, HTTPException, Request
from backend.outbound.orchestrator import get_stats, run_task, SCHEDULE
from backend.outbound.deliverability import (
    get_email_health,
    process_resend_webhook,
)

router = APIRouter()


@router.get("/stats")
async def admin_stats():
    """Vrátí přehledové statistiky pro admin dashboard."""
    try:
        stats = await get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run/{task_name}")
async def admin_run_task(task_name: str):
    """Manuálně spustí úlohu orchestrátoru."""
    if task_name not in SCHEDULE:
        raise HTTPException(
            status_code=400,
            detail=f"Neznámá úloha: {task_name}. Dostupné: {list(SCHEDULE.keys())}",
        )
    result = await run_task(task_name)
    return result


@router.get("/email-log")
async def admin_email_log(limit: int = 50):
    """Vrátí posledních N odeslaných emailů."""
    from backend.database import get_supabase
    supabase = get_supabase()

    res = supabase.table("email_log").select(
        "*"
    ).order("sent_at", desc=True).limit(limit).execute()

    return {"emails": res.data or [], "total": len(res.data or [])}


@router.get("/companies")
async def admin_companies(status: str = "all", limit: int = 50):
    """Vrátí přehled firem z prospecting DB."""
    from backend.database import get_supabase
    supabase = get_supabase()

    query = supabase.table("companies").select("*")

    if status != "all":
        query = query.eq("scan_status", status)

    res = query.order("created_at", desc=True).limit(limit).execute()

    return {"companies": res.data or [], "total": len(res.data or [])}


@router.get("/email-health")
async def admin_email_health():
    """Vrátí zdravotní metriky emailové kampaně."""
    try:
        health = await get_email_health()
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resend-webhook")
async def resend_webhook(request: Request):
    """
    Webhook od Resend — bounce, complaint, delivered, opened, clicked.
    Ověřuje HMAC-SHA256 podpis přes svapi_id header.
    """
    import hmac
    import hashlib
    from backend.config import get_settings

    settings = get_settings()
    body_bytes = await request.body()

    # Resend posílá podpis v hlavičce svix-signature
    signature_header = request.headers.get("svix-signature", "")
    svix_id = request.headers.get("svix-id", "")
    svix_timestamp = request.headers.get("svix-timestamp", "")

    if settings.resend_webhook_secret and signature_header:
        # Resend/Svix: sign = base64(HMAC-SHA256(secret, "{msg_id}.{timestamp}.{body}"))
        import base64
        secret = settings.resend_webhook_secret
        # Svix secrets start with whsec_ prefix, decode the base64 part after it
        if secret.startswith("whsec_"):
            secret_bytes = base64.b64decode(secret[6:])
        else:
            secret_bytes = secret.encode()

        to_sign = f"{svix_id}.{svix_timestamp}.{body_bytes.decode()}".encode()
        expected = base64.b64encode(
            hmac.new(secret_bytes, to_sign, hashlib.sha256).digest()
        ).decode()

        # Header contains space-separated versioned sigs: "v1,<sig1> v1,<sig2>"
        valid = any(
            part.split(",", 1)[1] == expected
            for part in signature_header.split(" ")
            if "," in part
        )
        if not valid:
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        import json
        body = json.loads(body_bytes)
        result = await process_resend_webhook(body)
        return result
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}
