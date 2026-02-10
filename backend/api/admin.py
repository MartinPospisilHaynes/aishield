"""
AIshield.cz — Admin API
Přehledový dashboard, manuální ovládání orchestrátoru,
email health monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from backend.outbound.orchestrator import get_stats, run_task, SCHEDULE
from backend.outbound.deliverability import (
    get_email_health,
    process_resend_webhook,
)
from backend.api.auth import AuthUser, require_admin, TEST_EMAILS
from backend.api.rate_limit import scan_limiter

router = APIRouter()


@router.get("/stats")
async def admin_stats(user: AuthUser = Depends(require_admin)):
    """Vrátí přehledové statistiky pro admin dashboard."""
    try:
        stats = await get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run/{task_name}")
async def admin_run_task(task_name: str, user: AuthUser = Depends(require_admin)):
    """Manuálně spustí úlohu orchestrátoru."""
    if task_name not in SCHEDULE:
        raise HTTPException(
            status_code=400,
            detail=f"Neznámá úloha: {task_name}. Dostupné: {list(SCHEDULE.keys())}",
        )
    result = await run_task(task_name)
    return result


@router.get("/email-log")
async def admin_email_log(limit: int = 50, user: AuthUser = Depends(require_admin)):
    """Vrátí posledních N odeslaných emailů."""
    from backend.database import get_supabase
    supabase = get_supabase()

    res = supabase.table("email_log").select(
        "*"
    ).order("sent_at", desc=True).limit(limit).execute()

    return {"emails": res.data or [], "total": len(res.data or [])}


@router.get("/companies")
async def admin_companies(status: str = "all", limit: int = 50, user: AuthUser = Depends(require_admin)):
    """Vrátí přehled firem z prospecting DB."""
    from backend.database import get_supabase
    supabase = get_supabase()

    query = supabase.table("companies").select("*")

    if status != "all":
        query = query.eq("scan_status", status)

    res = query.order("created_at", desc=True).limit(limit).execute()

    return {"companies": res.data or [], "total": len(res.data or [])}


@router.get("/email-health")
async def admin_email_health(user: AuthUser = Depends(require_admin)):
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


# ── Alert / Monitoring Admin ──


@router.get("/alerts")
async def admin_alerts(limit: int = 50, user: AuthUser = Depends(require_admin)):
    """Vrátí posledních N alertů."""
    from backend.database import get_supabase
    supabase = get_supabase()

    res = supabase.table("alerts").select(
        "*"
    ).order("created_at", desc=True).limit(limit).execute()

    return {"alerts": res.data or [], "total": len(res.data or [])}


@router.post("/legislative-alert")
async def admin_legislative_alert(request: Request, user: AuthUser = Depends(require_admin)):
    """
    Manuální trigger: Pošli legislativní alert VŠEM platícím klientům.
    Body: {"title": "...", "body_text": "..."}
    """
    from backend.monitoring.alert_system import trigger_legislative_alert

    body = await request.json()
    title = body.get("title", "Legislativní změna — AI Act")
    body_text = body.get("body_text", "")

    if not body_text:
        raise HTTPException(status_code=400, detail="body_text je povinný")

    result = await trigger_legislative_alert(title, body_text)
    return result


@router.get("/diffs")
async def admin_diffs(limit: int = 20, user: AuthUser = Depends(require_admin)):
    """Vrátí posledních N diffů (porovnání skenů)."""
    from backend.database import get_supabase
    supabase = get_supabase()

    res = supabase.table("scan_diffs").select(
        "*"
    ).order("created_at", desc=True).limit(limit).execute()

    return {"diffs": res.data or [], "total": len(res.data or [])}


# ── Test User Management ──


@router.delete("/test-user/{email}")
async def admin_delete_test_user(email: str, user: AuthUser = Depends(require_admin)):
    """
    Smaže testovacího uživatele ze Supabase Auth (umožní re-registraci).
    Funguje POUZE pro emaily v TEST_EMAILS — ochrana před smazáním produkčních účtů.
    """
    if email not in TEST_EMAILS:
        raise HTTPException(
            status_code=403,
            detail=f"Email {email} není v seznamu testovacích emailů. "
                   f"Povolené: {', '.join(sorted(TEST_EMAILS))}",
        )

    from backend.database import get_supabase
    supabase = get_supabase()

    try:
        # Najdi uživatele podle emailu v Supabase Auth (admin API)
        users_response = supabase.auth.admin.list_users()
        target_user = None
        for u in users_response:
            # supabase-py returns list of User objects
            user_email = getattr(u, "email", None) or (u.get("email") if isinstance(u, dict) else None)
            user_id = getattr(u, "id", None) or (u.get("id") if isinstance(u, dict) else None)
            if user_email == email:
                target_user = {"id": str(user_id), "email": user_email}
                break

        if not target_user:
            return {"status": "not_found", "message": f"Uživatel {email} nenalezen v Supabase Auth"}

        # Smazat uživatele
        supabase.auth.admin.delete_user(target_user["id"])

        return {
            "status": "deleted",
            "message": f"Uživatel {email} (ID: {target_user['id']}) byl smazán. "
                       f"Nyní se může znovu zaregistrovat.",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chyba při mazání uživatele: {str(e)}",
        )


@router.delete("/rate-limit-cache/{domain}")
async def admin_clear_rate_limit_cache(domain: str, user: AuthUser = Depends(require_admin)):
    """
    Vyčistí rate limit URL cache pro danou doménu.
    Umožní okamžitý resken webu bez čekání 24h.
    """
    normalized_domain = domain.lower().strip()
    for prefix in ("https://", "http://"):
        if normalized_domain.startswith(prefix):
            normalized_domain = normalized_domain[len(prefix):]
    if normalized_domain.startswith("www."):
        normalized_domain = normalized_domain[4:]
    normalized_domain = normalized_domain.rstrip("/")

    cleared = []
    with scan_limiter._lock:
        to_delete = [
            url for url in scan_limiter._url_cache
            if url == normalized_domain or url.startswith(normalized_domain + "/")
        ]
        for url in to_delete:
            del scan_limiter._url_cache[url]
            cleared.append(url)

    return {
        "status": "cleared",
        "domain": normalized_domain,
        "cleared_urls": cleared,
        "message": f"Vyčištěno {len(cleared)} záznamů z rate limit cache.",
    }
