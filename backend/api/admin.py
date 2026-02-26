"""
AIshield.cz — Admin API
Přehledový dashboard, manuální ovládání orchestrátoru,
email health monitoring.
"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from backend.outbound.orchestrator import get_stats, run_task, SCHEDULE
from backend.outbound.deliverability import (
    get_email_health,
    process_resend_webhook,
)
from backend.api.auth import AuthUser, require_admin
from backend.api.rate_limit import scan_limiter, admin_limiter
from backend.security import log_access

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Admin rate limit dependency ──
async def _check_admin_rate_limit(request: Request):
    """FastAPI dependency: kontroluje admin rate limit per IP."""
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    ip = ip.split(",")[0].strip()
    allowed, retry_after = admin_limiter.check(ip)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Příliš mnoho požadavků. Zkuste za {retry_after}s.",
            headers={"Retry-After": str(retry_after)},
        )


@router.get("/stats")
async def admin_stats(
    user: AuthUser = Depends(require_admin),
    _rl=Depends(_check_admin_rate_limit),
):
    """Vrátí přehledové statistiky pro admin dashboard."""
    logger.info(f"[Admin] GET /stats — user={user.email}")
    try:
        stats = await get_stats()
        return stats
    except Exception as e:
        logger.error(f"[Admin] GET /stats CHYBA: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run/{task_name}")
async def admin_run_task(task_name: str, user: AuthUser = Depends(require_admin)):
    """Manuálně spustí úlohu orchestrátoru."""
    logger.info(f"[Admin] POST /run/{task_name} — user={user.email}")
    if task_name not in SCHEDULE:
        logger.warning(f"[Admin] Neznámá úloha: {task_name}")
        raise HTTPException(
            status_code=400,
            detail=f"Neznámá úloha: {task_name}. Dostupné: {list(SCHEDULE.keys())}",
        )
    result = await run_task(task_name)
    logger.info(f"[Admin] Úloha {task_name} dokončena")
    return result


@router.get("/email-log")
async def admin_email_log(limit: int = 50, user: AuthUser = Depends(require_admin)):
    """Vrátí posledních N odeslaných emailů."""
    logger.info(f"[Admin] GET /email-log limit={limit} — user={user.email}")
    from backend.database import get_supabase
    supabase = get_supabase()

    res = supabase.table("email_log").select(
        "*"
    ).order("sent_at", desc=True).limit(limit).execute()

    return {"emails": res.data or [], "total": len(res.data or [])}


@router.get("/companies")
async def admin_companies(status: str = "all", limit: int = 50, user: AuthUser = Depends(require_admin)):
    """Vrátí přehled firem z prospecting DB."""
    logger.info(f"[Admin] GET /companies status={status}, limit={limit} — user={user.email}")
    from backend.database import get_supabase
    supabase = get_supabase()

    query = supabase.table("companies").select("*")

    if status != "all":
        query = query.eq("scan_status", status)

    res = query.order("created_at", desc=True).limit(limit).execute()

    return {"companies": res.data or [], "total": len(res.data or [])}


@router.get("/email-health")
async def admin_email_health(
    user: AuthUser = Depends(require_admin),
    _rl=Depends(_check_admin_rate_limit),
):
    """Vrátí zdravotní metriky emailové kampaně."""
    try:
        health = await get_email_health()
        # Přidáme top-level status pro E2E testy a dashboard
        is_healthy = health.get("is_healthy", False)
        health["status"] = "ok" if is_healthy else "warning"
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-reminders/{reminder_type}")
async def admin_send_reminders(
    reminder_type: str,
    user: AuthUser = Depends(require_admin),
):
    """
    Odešle připomínkové emaily uživatelům s neověřenými „Nevím" odpověďmi.
    reminder_type: "14_days" nebo "30_days"
    Volá se z cron jobu nebo ručně z admin dashboardu.
    """
    if reminder_type not in ("14_days", "30_days"):
        raise HTTPException(
            status_code=400,
            detail=f"Neplatný typ: {reminder_type}. Použijte '14_days' nebo '30_days'.",
        )
    try:
        from backend.outbound.reminder_emails import send_reminder_emails
        result = await send_reminder_emails(reminder_type)
        logger.info(f"[Admin] Reminders {reminder_type} odeslány: {result}")
        return result
    except Exception as e:
        logger.error(f"[Admin] Reminders {reminder_type} CHYBA: {e}", exc_info=True)
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

    logger.info("[Admin] POST /resend-webhook přijat")

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
            logger.warning("[Admin] Resend webhook: neplatný podpis")
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        import json
        body = json.loads(body_bytes)
        logger.info(f"[Admin] Resend webhook typ={body.get('type', '?')}, email={body.get('data', {}).get('to', ['?'])}")
        result = await process_resend_webhook(body)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] Resend webhook CHYBA: {e}", exc_info=True)
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

    logger.info(f"[Admin] POST /legislative-alert title='{title}' — user={user.email}")

    if not body_text:
        raise HTTPException(status_code=400, detail="body_text je povinný")

    result = await trigger_legislative_alert(title, body_text)
    logger.info(f"[Admin] Legislative alert odeslán: {result}")
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


@router.delete("/rate-limit-cache")
async def admin_clear_all_rate_limit_cache(user: AuthUser = Depends(require_admin)):
    """
    Vyčistí CELOU rate limit cache — in-memory limiter + resetuje recent
    skeny v DB (nastaví created_at starší než cooldown aby je DB-check ignoroval).
    Umožní okamžitý resken jakéhokoli webu bez čekání 1 hodiny.
    """
    from backend.database import get_supabase

    # 1. Clear in-memory rate limiter
    with scan_limiter._lock:
        url_count = len(scan_limiter._url_cache)
        ip_count = len(scan_limiter._ip_timestamps)
        scan_limiter._url_cache.clear()
        scan_limiter._ip_timestamps.clear()
        scan_limiter._global_timestamps.clear()

    # 2. Reset DB-backed cooldown: shift created_at of recent running/done scans
    #    so the DB check won't block future scans on the same domain
    db_reset = 0
    try:
        supabase = get_supabase()
        from backend.api.rate_limit import URL_COOLDOWN_SECONDS
        from datetime import timedelta
        one_hour_ago = (datetime.now(timezone.utc) - timedelta(seconds=URL_COOLDOWN_SECONDS)).isoformat()
        # Find recent scans that would trigger the cooldown
        recent = supabase.table("scans").select("id, created_at, status").gte(
            "created_at", one_hour_ago
        ).in_("status", ["done", "running", "queued"]).execute()
        if recent.data:
            # Push created_at back by 2 hours so they're outside the cooldown window
            old_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
            for row in recent.data:
                supabase.table("scans").update({"created_at": old_time}).eq("id", row["id"]).execute()
                db_reset += 1
    except Exception as e:
        logger.warning(f"[Admin] Rate limit DB reset partial failure: {e}")

    return {
        "status": "cleared",
        "memory": f"Vyčištěno {url_count} URL + {ip_count} IP záznamů",
        "db": f"Resetováno {db_reset} recentních skenů v DB",
        "message": f"✅ Veškeré rate limity vymazány. Můžete okamžitě skenovat.",
    }


# ── Audit Log & Data Purge ──


@router.get("/audit-log")
async def admin_audit_log(
    limit: int = 100,
    resource_type: str = "",
    user: AuthUser = Depends(require_admin),
):
    """Vrátí posledních N záznamů z audit logu."""
    from backend.database import get_supabase
    supabase = get_supabase()

    query = supabase.table("data_access_log").select("*")
    if resource_type:
        query = query.eq("resource_type", resource_type)
    res = query.order("created_at", desc=True).limit(limit).execute()

    return {"logs": res.data or [], "total": len(res.data or [])}


@router.delete("/company/{company_id}/purge")
async def admin_purge_company(
    company_id: str,
    request: Request,
    user: AuthUser = Depends(require_admin),
):
    """
    Kompletní smazání VŠECH dat firmy z DB (GDPR právo na výmaz).
    Doporučeno: nejprve exportovat přes GET /api/admin/export/{company_id}.
    """
    from backend.database import get_supabase
    supabase = get_supabase()

    # Ověříme že firma existuje
    company = supabase.table("companies").select("id, name, url, email").eq("id", company_id).execute()
    if not company.data:
        raise HTTPException(status_code=404, detail="Firma nenalezena")

    company_info = company.data[0]
    company_name = company_info.get("name", "?")

    logger.warning(
        f"[Admin] PURGE firmy: {company_name} (id={company_id}) — user={user.email}"
    )

    # Audit log PŘED smazáním
    await log_access(
        actor_email=user.email,
        action="delete",
        resource_type="company",
        resource_id=company_id,
        resource_detail=f"PURGE: {company_name} ({company_info.get('url', '')})",
        request=request,
        metadata={"company": company_info},
    )

    deleted = []

    # 1. Findings (přes scan_ids)
    scans = supabase.table("scans").select("id").eq("company_id", company_id).execute()
    for s in (scans.data or []):
        supabase.table("findings").delete().eq("scan_id", s["id"]).execute()
    if scans.data:
        deleted.append(f"findings ({len(scans.data)} skenů)")

    # 2. Questionnaire responses (přes client_ids)
    clients = supabase.table("clients").select("id").eq("company_id", company_id).execute()
    for c in (clients.data or []):
        supabase.table("questionnaire_responses").delete().eq("client_id", c["id"]).execute()
        supabase.table("documents").delete().eq("client_id", c["id"]).execute()
        supabase.table("alerts").delete().eq("client_id", c["id"]).execute()
    if clients.data:
        deleted.append(f"questionnaire + docs + alerts ({len(clients.data)} klientů)")

    # 3. Přímé tabulky
    for tbl in ["scan_diffs", "scans", "clients", "widget_configs"]:
        try:
            supabase.table(tbl).delete().eq("company_id", company_id).execute()
            deleted.append(tbl)
        except Exception:
            pass

    # 4. Objednávky podle emailu
    email = company_info.get("email")
    if email:
        for tbl in ["orders", "subscriptions"]:
            try:
                supabase.table(tbl).delete().eq("email", email).execute()
                deleted.append(tbl)
            except Exception:
                pass

    # 5. Smaž firmu samotnou
    supabase.table("companies").delete().eq("id", company_id).execute()
    deleted.append("companies")

    return {
        "status": "purged",
        "company_id": company_id,
        "company_name": company_name,
        "deleted": deleted,
        "message": f"Všechna data firmy {company_name} byla smazána (GDPR výmaz).",
    }


@router.post("/cleanup/run")
async def admin_run_cleanup(
    request: Request,
    user: AuthUser = Depends(require_admin),
):
    """Manuálně spustí data retention cleanup."""
    from backend.security.data_cleanup import run_cleanup

    result = await run_cleanup()

    logger.info(f"[Admin] Data cleanup spuštěn user={user.email}: {result.get('report', {})}")

    await log_access(
        actor_email=user.email,
        action="delete",
        resource_type="cleanup",
        resource_detail="Manuální spuštění data retention cleanup",
        request=request,
        metadata=result.get("report", {}),
    )

    return result
