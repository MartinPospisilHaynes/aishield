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
from backend.api.rate_limit import scan_limiter, admin_limiter
from backend.security import log_access

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


# ── Test Account Reset (veřejný endpoint, ale jen pro TEST_EMAILS) ──


@router.post("/test-reset")
async def test_reset_user(request: Request):
    """
    Kompletní reset testovacího účtu:
      1. Smaže uživatele ze Supabase Auth (pokud existuje)
      2. Vyčistí VŠECHNA data v DB (skeny, dotazník, dokumenty, …)
      3. Vytvoří nového uživatele s auto-potvrzeným emailem
      4. Vyčistí rate-limit cache pro testovací doménu

    Endpoint je veřejný (bez JWT), ale funguje POUZE pro emaily
    v TEST_EMAILS — nelze zneužít pro produkční účty.

    Body: {"email": "...", "password": "...", "web_url": "..."}
    """
    import logging
    log = logging.getLogger("test-reset")

    body = await request.json()
    email = (body.get("email") or "").strip().lower()
    password = body.get("password", "")
    web_url = (body.get("web_url") or "").strip().lower()

    if not email or not password:
        raise HTTPException(status_code=400, detail="email a password jsou povinné")

    if email not in TEST_EMAILS:
        raise HTTPException(
            status_code=403,
            detail=f"Email {email} není testovací. Povolené: {', '.join(sorted(TEST_EMAILS))}",
        )

    from backend.database import get_supabase
    supabase = get_supabase()

    cleanup_log = []

    # ── 1. Najdi existujícího uživatele ──
    old_user_id = None
    try:
        users_response = supabase.auth.admin.list_users()
        for u in users_response:
            u_email = getattr(u, "email", None) or (u.get("email") if isinstance(u, dict) else None)
            u_id = getattr(u, "id", None) or (u.get("id") if isinstance(u, dict) else None)
            if u_email == email:
                old_user_id = str(u_id)
                break
    except Exception as e:
        log.warning(f"Nepodařilo se získat seznam uživatelů: {e}")

    # ── 2. Vyčisti DB data (pokud existuje starý účet) ──
    if old_user_id:
        # Najdi company_id podle emailu
        company_id = None
        try:
            comp = supabase.table("companies").select("id").eq("email", email).execute()
            if comp.data:
                company_id = comp.data[0]["id"]
        except Exception:
            pass

        if company_id:
            # Smaž závislé tabulky (children first)
            tables_by_company = [
                "findings",   # přes scan_id, ale smažeme přes company scan
                "scan_diffs",
                "questionnaire_responses",  # přes client_id
                "clients",
                "documents",
                "alerts",
                "widget_configs",
                "report_leads",
            ]

            # Findings — musíme najít scan_ids nejdřív
            try:
                scans = supabase.table("scans").select("id").eq("company_id", company_id).execute()
                scan_ids = [s["id"] for s in (scans.data or [])]
                if scan_ids:
                    for sid in scan_ids:
                        supabase.table("findings").delete().eq("scan_id", sid).execute()
                    cleanup_log.append(f"findings (pro {len(scan_ids)} skenů)")
            except Exception as e:
                log.warning(f"Čištění findings: {e}")

            # Questionnaire responses — přes clients
            try:
                clients = supabase.table("clients").select("id").eq("company_id", company_id).execute()
                client_ids = [c["id"] for c in (clients.data or [])]
                if client_ids:
                    for cid in client_ids:
                        supabase.table("questionnaire_responses").delete().eq("client_id", cid).execute()
                    cleanup_log.append(f"questionnaire_responses (pro {len(client_ids)} klientů)")
            except Exception as e:
                log.warning(f"Čištění questionnaire_responses: {e}")

            # Přímé tabulky s company_id
            for tbl in ["scan_diffs", "scans", "clients", "documents", "alerts", "widget_configs"]:
                try:
                    supabase.table(tbl).delete().eq("company_id", company_id).execute()
                    cleanup_log.append(tbl)
                except Exception as e:
                    log.warning(f"Čištění {tbl}: {e}")

            # report_leads — company_id nebo email
            try:
                supabase.table("report_leads").delete().eq("company_id", company_id).execute()
                supabase.table("report_leads").delete().eq("email", email).execute()
                cleanup_log.append("report_leads")
            except Exception:
                pass

            # Smaž samotnou company
            try:
                supabase.table("companies").delete().eq("id", company_id).execute()
                cleanup_log.append("companies")
            except Exception as e:
                log.warning(f"Čištění companies: {e}")

        # Tabulky přímo podle emailu (bez company_id)
        for tbl in ["orders", "subscriptions"]:
            try:
                supabase.table(tbl).delete().eq("email", email).execute()
                cleanup_log.append(tbl)
            except Exception:
                pass

        # ── 3. Smaž uživatele ze Supabase Auth ──
        try:
            supabase.auth.admin.delete_user(old_user_id)
            cleanup_log.append(f"auth user {old_user_id}")
        except Exception as e:
            log.warning(f"Smazání auth uživatele: {e}")

    # ── 4. Vytvoř nového uživatele s AUTO-POTVRZENÍM ──
    try:
        new_user = supabase.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,  # ← klíčové: přeskočí email verifikaci
            "user_metadata": {
                "company_name": "Test Firma s.r.o.",
                "web_url": web_url or "https://www.desperados-design.cz",
                "ico": "12345678",
                "gdpr_consent": True,
                "gdpr_consent_at": "2026-02-11T00:00:00Z",
                "test_account": True,
            },
        })
        new_user_id = getattr(new_user, "id", None) or (new_user.user.id if hasattr(new_user, "user") else "unknown")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Nepodařilo se vytvořit testovacího uživatele: {str(e)}",
        )

    # ── 5. Vyčisti rate-limit cache pro testovací doménu ──
    test_domain = (web_url or "desperados-design.cz").lower()
    for prefix in ("https://", "http://", "www."):
        if test_domain.startswith(prefix):
            test_domain = test_domain[len(prefix):]
    test_domain = test_domain.rstrip("/")

    rate_cleared = 0
    try:
        with scan_limiter._lock:
            to_del = [u for u in scan_limiter._url_cache if u == test_domain or u.startswith(test_domain + "/")]
            for u in to_del:
                del scan_limiter._url_cache[u]
                rate_cleared += 1
    except Exception:
        pass

    return {
        "status": "reset_complete",
        "email": email,
        "new_user_id": str(new_user_id),
        "auto_confirmed": True,
        "cleaned_tables": cleanup_log,
        "rate_limit_cleared": rate_cleared,
        "message": (
            f"✅ Testovací účet {email} byl kompletně resetován. "
            f"Vyčištěno: {', '.join(cleanup_log) if cleanup_log else 'žádná stará data'}. "
            f"Účet je auto-potvrzený — můžete se rovnou přihlásit."
        ),
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

    await log_access(
        actor_email=user.email,
        action="delete",
        resource_type="cleanup",
        resource_detail="Manuální spuštění data retention cleanup",
        request=request,
        metadata=result.get("report", {}),
    )

    return result
