"""
AIshield.cz — Admin CRM Dashboard API
Pipeline management, company detail, activity timeline,
dashboard statistics, and admin authentication.
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from backend.api.auth import AuthUser, require_admin
from backend.api.rate_limit import admin_limiter
from backend.config import get_settings


async def _check_admin_rate_limit(request: Request):
    """Admin rate limit per IP."""
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    ip = ip.split(",")[0].strip()
    allowed, retry_after = admin_limiter.check(ip)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Příliš mnoho požadavků. Zkuste za {retry_after}s.",
            headers={"Retry-After": str(retry_after)},
        )

# ── XSS sanitizace & validace ──
MAX_TITLE_LENGTH = 500
MAX_DESCRIPTION_LENGTH = 10_000
MAX_FIELD_LENGTH = 1_000

def _strip_html(text: str) -> str:
    """Odstraní HTML tagy z textu (prevence XSS)."""
    if not text:
        return text
    return re.sub(r"<[^>]+>", "", text).strip()

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Hardcoded admin password (match supabase_db_password) ──
_ADMIN_PASSWORD = "Rc_732716141"


# ─────────────────────────────────────────────
# 1. POST /login — Admin login
# ─────────────────────────────────────────────

@router.post("/crm/login")
async def admin_crm_login(request: Request):
    """
    Admin CRM login — vrátí jednoduchý token.
    Hardcoded: username=ADMIN, password=supabase_db_password.
    """
    body = await request.json()
    username = (body.get("username") or "").strip()
    password = (body.get("password") or "").strip()

    if username != "ADMIN" or password != _ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Neplatné přihlašovací údaje")

    # Jednoduchý token: admin_ + SHA256 hash (prvních 32 znaků)
    token = "admin_" + hashlib.sha256(password.encode()).hexdigest()[:32]

    return {
        "token": token,
        "expires_in": 86400,
        "username": "ADMIN",
        "message": "Přihlášení úspěšné",
    }


# ─────────────────────────────────────────────
# 2. GET /crm/company/{company_id} — Full company detail
# ─────────────────────────────────────────────

@router.get("/crm/company/{company_id}")
async def crm_company_detail(
    company_id: str,
    user: AuthUser = Depends(require_admin),
):
    """Vrátí kompletní detail firmy pro CRM — se skeny, findings, emaily, objednávkami."""
    from backend.database import get_supabase
    supabase = get_supabase()

    try:
        # ── Company ──
        company_res = supabase.table("companies").select("*").eq("id", company_id).execute()
        if not company_res.data:
            raise HTTPException(status_code=404, detail="Firma nenalezena")

        company = company_res.data[0]

        # ── Latest scan ──
        latest_scan = None
        findings_count = 0
        try:
            scan_res = (
                supabase.table("scans")
                .select("*")
                .eq("company_id", company_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            if scan_res.data:
                latest_scan = scan_res.data[0]
                # Count findings for this scan
                scan_id = latest_scan["id"]
                findings_res = (
                    supabase.table("findings")
                    .select("id", count="exact")
                    .eq("scan_id", scan_id)
                    .execute()
                )
                findings_count = findings_res.count or len(findings_res.data or [])
        except Exception as e:
            logger.warning(f"[CRM] Scans/findings fetch error: {e}")

        # ── Email log ──
        email_log = []
        try:
            email = company.get("email")
            if email:
                email_res = (
                    supabase.table("email_log")
                    .select("*")
                    .eq("to_email", email)
                    .order("sent_at", desc=True)
                    .limit(20)
                    .execute()
                )
                email_log = email_res.data or []
        except Exception as e:
            logger.warning(f"[CRM] Email log fetch error: {e}")

        # ── Questionnaire responses count ──
        questionnaire_count = 0
        try:
            clients_res = (
                supabase.table("clients")
                .select("id")
                .eq("company_id", company_id)
                .execute()
            )
            client_ids = [c["id"] for c in (clients_res.data or [])]
            for cid in client_ids:
                qr_res = (
                    supabase.table("questionnaire_responses")
                    .select("id", count="exact")
                    .eq("client_id", cid)
                    .execute()
                )
                questionnaire_count += qr_res.count or len(qr_res.data or [])
        except Exception as e:
            logger.warning(f"[CRM] Questionnaire count error: {e}")

        # ── Orders / payments ──
        orders = []
        try:
            email = company.get("email")
            if email:
                orders_res = (
                    supabase.table("orders")
                    .select("*")
                    .eq("email", email)
                    .order("created_at", desc=True)
                    .execute()
                )
                orders = orders_res.data or []
        except Exception as e:
            logger.warning(f"[CRM] Orders fetch error: {e}")

        # ── Company activities ──
        activities = []
        try:
            act_res = (
                supabase.table("company_activities")
                .select("*")
                .eq("company_id", company_id)
                .order("created_at", desc=True)
                .limit(50)
                .execute()
            )
            activities = act_res.data or []
        except Exception as e:
            logger.warning(f"[CRM] Activities fetch error: {e}")

        return {
            "company": company,
            "latest_scan": latest_scan,
            "findings_count": findings_count,
            "email_log": email_log,
            "questionnaire_count": questionnaire_count,
            "orders": orders,
            "activities": activities,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chyba při načítání detailu firmy: {str(e)}")


# ─────────────────────────────────────────────
# 3. PATCH /crm/company/{company_id}/status — Update workflow status
# ─────────────────────────────────────────────

@router.patch("/crm/company/{company_id}/status")
async def crm_update_company_status(
    company_id: str,
    request: Request,
    user: AuthUser = Depends(require_admin),
):
    """Aktualizuje workflow status firmy a zapíše aktivitu."""
    from backend.database import get_supabase
    supabase = get_supabase()

    body = await request.json()

    # Ověříme že firma existuje
    company_res = supabase.table("companies").select("id, name, workflow_status").eq("id", company_id).execute()
    if not company_res.data:
        raise HTTPException(status_code=404, detail="Firma nenalezena")

    old_company = company_res.data[0]

    # Povolené atributy k aktualizaci
    allowed_fields = {
        "workflow_status", "payment_status", "priority",
        "next_action", "next_action_at", "assigned_to",
    }
    update_data = {k: v for k, v in body.items() if k in allowed_fields and v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="Žádná platná pole k aktualizaci")

    # ── XSS sanitizace textových polí ──
    for field in ("next_action", "assigned_to", "workflow_status", "payment_status", "priority"):
        if field in update_data and isinstance(update_data[field], str):
            update_data[field] = _strip_html(update_data[field])
            if len(update_data[field]) > MAX_FIELD_LENGTH:
                raise HTTPException(status_code=400, detail=f"{field} max {MAX_FIELD_LENGTH} znaků")

    try:
        # Update company
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        updated_res = (
            supabase.table("companies")
            .update(update_data)
            .eq("id", company_id)
            .execute()
        )

        # Zapsat aktivitu (status change)
        changes_description = ", ".join(f"{k}: {v}" for k, v in update_data.items() if k != "updated_at")
        old_status = old_company.get("workflow_status", "unknown")

        try:
            supabase.table("company_activities").insert({
                "company_id": company_id,
                "activity_type": "status_change",
                "title": f"Status změněn",
                "description": f"Změna: {changes_description} (předchozí stav: {old_status})",
                "actor": user.email,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
        except Exception as e:
            logger.warning(f"[CRM] Activity insert error: {e}")

        return {
            "status": "updated",
            "company_id": company_id,
            "updated_fields": update_data,
            "company": updated_res.data[0] if updated_res.data else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chyba při aktualizaci: {str(e)}")


# ─────────────────────────────────────────────
# 4. POST /crm/company/{company_id}/note — Add a note/activity
# ─────────────────────────────────────────────

@router.post("/crm/company/{company_id}/note")
async def crm_add_note(
    company_id: str,
    request: Request,
    user: AuthUser = Depends(require_admin),
):
    """Přidá poznámku / aktivitu ke firmě."""
    from backend.database import get_supabase
    supabase = get_supabase()

    body = await request.json()

    activity_type = body.get("activity_type", "note")
    title = _strip_html(body.get("title", ""))
    description = _strip_html(body.get("description", ""))

    if not title:
        raise HTTPException(status_code=400, detail="title je povinný")

    # ── Limity velikosti (DoS prevence) ──
    if len(title) > MAX_TITLE_LENGTH:
        raise HTTPException(status_code=400, detail=f"title max {MAX_TITLE_LENGTH} znaků")
    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise HTTPException(status_code=400, detail=f"description max {MAX_DESCRIPTION_LENGTH} znaků")

    # Ověříme že firma existuje
    company_res = supabase.table("companies").select("id").eq("id", company_id).execute()
    if not company_res.data:
        raise HTTPException(status_code=404, detail="Firma nenalezena")

    try:
        activity = {
            "company_id": company_id,
            "activity_type": activity_type,
            "title": title,
            "description": description,
            "actor": user.email,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        res = supabase.table("company_activities").insert(activity).execute()

        return {
            "status": "created",
            "activity": res.data[0] if res.data else activity,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chyba při ukládání poznámky: {str(e)}")


# ─────────────────────────────────────────────
# 5. GET /crm/company/{company_id}/timeline — Activity timeline
# ─────────────────────────────────────────────

@router.get("/crm/company/{company_id}/timeline")
async def crm_company_timeline(
    company_id: str,
    user: AuthUser = Depends(require_admin),
):
    """Vrátí timeline aktivit firmy (max 100, od nejnovějších)."""
    from backend.database import get_supabase
    supabase = get_supabase()

    try:
        res = (
            supabase.table("company_activities")
            .select("*")
            .eq("company_id", company_id)
            .order("created_at", desc=True)
            .limit(100)
            .execute()
        )

        return {
            "company_id": company_id,
            "activities": res.data or [],
            "total": len(res.data or []),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chyba při načítání timeline: {str(e)}")


# ─────────────────────────────────────────────
# 6. GET /crm/pipeline — Pipeline/funnel statistics
# ─────────────────────────────────────────────

@router.get("/crm/pipeline")
async def crm_pipeline(user: AuthUser = Depends(require_admin)):
    """Pipeline statistiky — funnel vizualizace."""
    from backend.database import get_supabase
    supabase = get_supabase()

    try:
        # ── All companies ──
        companies_res = (
            supabase.table("companies")
            .select("id, workflow_status, payment_status, priority")
            .execute()
        )
        companies = companies_res.data or []

        # Count by workflow_status
        by_workflow = {}
        for c in companies:
            ws = c.get("workflow_status") or "unknown"
            by_workflow[ws] = by_workflow.get(ws, 0) + 1

        # Count by payment_status
        by_payment = {}
        for c in companies:
            ps = c.get("payment_status") or "unknown"
            by_payment[ps] = by_payment.get(ps, 0) + 1

        # Count by priority
        by_priority = {}
        for c in companies:
            pr = c.get("priority") or "unknown"
            by_priority[pr] = by_priority.get(pr, 0) + 1

        # ── Revenue from orders ──
        revenue_stats = {"total_orders": 0, "paid_amount": 0, "pending_amount": 0}
        try:
            orders_res = supabase.table("orders").select("*").execute()
            orders = orders_res.data or []
            revenue_stats["total_orders"] = len(orders)
            for o in orders:
                amount = o.get("amount") or 0
                if o.get("status") == "paid":
                    revenue_stats["paid_amount"] += amount
                else:
                    revenue_stats["pending_amount"] += amount
        except Exception as e:
            logger.warning(f"[CRM] Revenue stats error: {e}")

        return {
            "total_companies": len(companies),
            "by_workflow_status": by_workflow,
            "by_payment_status": by_payment,
            "by_priority": by_priority,
            "revenue": revenue_stats,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chyba při načítání pipeline: {str(e)}")


# ─────────────────────────────────────────────
# 7. GET /crm/dashboard-stats — Enhanced dashboard statistics
# ─────────────────────────────────────────────

@router.get("/crm/dashboard-stats")
async def crm_dashboard_stats(
    request: Request,
    user: AuthUser = Depends(require_admin),
    _rl=Depends(_check_admin_rate_limit),
):
    """Rozšířené statistiky pro CRM dashboard."""
    from backend.database import get_supabase
    supabase = get_supabase()

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    # Pondělí tohoto týdne
    import calendar
    week_start = (now.replace(hour=0, minute=0, second=0, microsecond=0)).__class__(
        now.year, now.month, now.day - now.weekday(),
        tzinfo=timezone.utc,
    ).isoformat()

    stats: dict = {}

    try:
        # ── Companies ──
        companies_res = supabase.table("companies").select("id, workflow_status").execute()
        companies = companies_res.data or []
        by_workflow = {}
        for c in companies:
            ws = c.get("workflow_status") or "unknown"
            by_workflow[ws] = by_workflow.get(ws, 0) + 1

        stats["companies"] = {
            "total": len(companies),
            "by_workflow_status": by_workflow,
        }
    except Exception as e:
        logger.warning(f"[CRM] Companies stats error: {e}")
        stats["companies"] = {"total": 0, "by_workflow_status": {}}

    # ── Emails ──
    try:
        all_emails_res = supabase.table("email_log").select("id, sent_at, status, opened_at, clicked_at").execute()
        all_emails = all_emails_res.data or []

        total_emails = len(all_emails)
        emails_today = sum(1 for e in all_emails if (e.get("sent_at") or "") >= today_start)
        emails_this_week = sum(1 for e in all_emails if (e.get("sent_at") or "") >= week_start)
        opened = sum(1 for e in all_emails if e.get("opened_at"))
        clicked = sum(1 for e in all_emails if e.get("clicked_at"))

        stats["emails"] = {
            "total": total_emails,
            "today": emails_today,
            "this_week": emails_this_week,
            "open_rate": round(opened / total_emails * 100, 1) if total_emails > 0 else 0,
            "click_rate": round(clicked / total_emails * 100, 1) if total_emails > 0 else 0,
        }
    except Exception as e:
        logger.warning(f"[CRM] Emails stats error: {e}")
        stats["emails"] = {"total": 0, "today": 0, "this_week": 0, "open_rate": 0, "click_rate": 0}

    # ── Scans ──
    try:
        scans_res = supabase.table("scans").select("id, created_at").execute()
        all_scans = scans_res.data or []

        stats["scans"] = {
            "total": len(all_scans),
            "today": sum(1 for s in all_scans if (s.get("created_at") or "") >= today_start),
            "this_week": sum(1 for s in all_scans if (s.get("created_at") or "") >= week_start),
        }
    except Exception as e:
        logger.warning(f"[CRM] Scans stats error: {e}")
        stats["scans"] = {"total": 0, "today": 0, "this_week": 0}

    # ── Questionnaires ──
    try:
        qr_res = supabase.table("questionnaire_responses").select("id", count="exact").execute()
        stats["questionnaires"] = {
            "total": qr_res.count or len(qr_res.data or []),
        }
    except Exception as e:
        logger.warning(f"[CRM] Questionnaires stats error: {e}")
        stats["questionnaires"] = {"total": 0}

    # ── Orders / Revenue ──
    try:
        orders_res = supabase.table("orders").select("*").execute()
        orders = orders_res.data or []
        paid_amount = sum((o.get("amount") or 0) for o in orders if o.get("status") == "paid")

        stats["orders"] = {
            "total": len(orders),
            "paid_amount": paid_amount,
        }
    except Exception as e:
        logger.warning(f"[CRM] Orders stats error: {e}")
        stats["orders"] = {"total": 0, "paid_amount": 0}

    # ── Companies needing attention (next_action_at < NOW) ──
    try:
        now_iso = now.isoformat()
        attention_res = (
            supabase.table("companies")
            .select("id, name, url, email, workflow_status, next_action, next_action_at")
            .lt("next_action_at", now_iso)
            .order("next_action_at", desc=False)
            .limit(20)
            .execute()
        )
        stats["needing_attention"] = attention_res.data or []
    except Exception as e:
        logger.warning(f"[CRM] Attention stats error: {e}")
        stats["needing_attention"] = []

    # ── Recent activity ──
    try:
        recent_res = (
            supabase.table("company_activities")
            .select("*")
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )
        stats["recent_activity"] = recent_res.data or []
    except Exception as e:
        logger.warning(f"[CRM] Recent activity error: {e}")
        stats["recent_activity"] = []

    return stats


# ─────────────────────────────────────────────
# 8. GET /crm/client-management — All paying clients + fulfillment overview
# ─────────────────────────────────────────────

@router.get("/crm/client-management")
async def crm_client_management(
    user: AuthUser = Depends(require_admin),
    _rl=Depends(_check_admin_rate_limit),
):
    """
    Vrátí kompletní přehled platících klientů:
    - Objednané služby, zaplacené platby
    - Stav předplatného (monitoring) + kontrola přijetí platby
    - Stav plnění (poslední scan, dokumenty, potřeba re-scanu)
    """
    from backend.database import get_supabase
    supabase = get_supabase()

    clients_list = []
    summary = {
        "total_clients": 0,
        "total_revenue": 0,
        "active_subscriptions": 0,
        "overdue_subscriptions": 0,
        "needs_rescan": 0,
    }

    try:
        # ── 1. All orders (paid or subscription) ──
        orders_res = supabase.table("orders").select("*").order("created_at", desc=True).execute()
        all_orders = orders_res.data or []

        # Group orders by email
        orders_by_email: dict[str, list] = {}
        for o in all_orders:
            email = (o.get("email") or o.get("user_email") or "").lower().strip()
            if email:
                orders_by_email.setdefault(email, []).append(o)

        # ── 2. All subscriptions ──
        subs_res = supabase.table("subscriptions").select("*").order("created_at", desc=True).execute()
        all_subs = subs_res.data or []
        subs_by_email: dict[str, list] = {}
        for s in all_subs:
            email = (s.get("email") or "").lower().strip()
            if email:
                subs_by_email.setdefault(email, []).append(s)

        # ── 3. All unique client emails (from orders + subscriptions) ──
        all_emails = set(orders_by_email.keys()) | set(subs_by_email.keys())

        # ── 4. Prefetch companies, scans, documents, clients ──
        companies_res = supabase.table("companies").select("*").execute()
        companies_by_email: dict[str, dict] = {}
        companies_by_id: dict[str, dict] = {}
        for c in (companies_res.data or []):
            email = (c.get("email") or "").lower().strip()
            if email:
                companies_by_email[email] = c
            companies_by_id[c["id"]] = c

        clients_res = supabase.table("clients").select("*").execute()
        clients_by_email: dict[str, dict] = {}
        for cl in (clients_res.data or []):
            email = (cl.get("email") or "").lower().strip()
            if email:
                clients_by_email[email] = cl

        # ── 5. Build client records ──
        now = datetime.now(timezone.utc)

        for email in sorted(all_emails):
            client_orders = orders_by_email.get(email, [])
            client_subs = subs_by_email.get(email, [])

            # Find company
            company = companies_by_email.get(email)
            client = clients_by_email.get(email)
            company_id = None
            company_name = email
            company_url = ""

            if company:
                company_id = company["id"]
                company_name = company.get("name") or email
                company_url = company.get("url") or ""
            elif client and client.get("company_id"):
                company_id = client["company_id"]
                comp = companies_by_id.get(company_id)
                if comp:
                    company_name = comp.get("name") or email
                    company_url = comp.get("url") or ""

            # Orders summary
            paid_orders = [o for o in client_orders if o.get("status") in ("PAID", "paid")]
            total_paid = sum(o.get("amount", 0) for o in paid_orders)

            # Latest plan from paid orders (non-subscription)
            one_time_orders = [
                o for o in paid_orders
                if o.get("order_type", "one_time") in ("one_time", None)
            ]
            latest_plan = one_time_orders[0].get("plan") if one_time_orders else None

            # Active subscription
            active_sub = None
            sub_payment_ok = True
            for s in client_subs:
                if s.get("status") == "active":
                    active_sub = s
                    # Check if payment is overdue (next_charge_at is past)
                    next_charge = s.get("next_charge_at")
                    if next_charge:
                        try:
                            nca = datetime.fromisoformat(next_charge.replace("Z", "+00:00"))
                            # Allow 5-day grace period
                            if now > nca + __import__("datetime").timedelta(days=5):
                                sub_payment_ok = False
                        except Exception:
                            pass
                    break

            # Last scan for this company
            last_scan = None
            scan_age_days = None
            if company_id:
                try:
                    scan_res = (
                        supabase.table("scans")
                        .select("id, status, total_findings, created_at, finished_at, url_scanned")
                        .eq("company_id", company_id)
                        .eq("status", "done")
                        .order("created_at", desc=True)
                        .limit(1)
                        .execute()
                    )
                    if scan_res.data:
                        last_scan = scan_res.data[0]
                        try:
                            scan_dt = datetime.fromisoformat(
                                last_scan["created_at"].replace("Z", "+00:00")
                            )
                            scan_age_days = (now - scan_dt).days
                        except Exception:
                            pass
                except Exception as e:
                    logger.warning(f"[ClientMgmt] Scan fetch error for {email}: {e}")

            # Documents count + last generated
            documents_count = 0
            documents_last_at = None
            if company_id:
                try:
                    docs_res = (
                        supabase.table("documents")
                        .select("id, created_at")
                        .eq("company_id", company_id)
                        .order("created_at", desc=True)
                        .execute()
                    )
                    documents_count = len(docs_res.data or [])
                    if docs_res.data:
                        documents_last_at = docs_res.data[0].get("created_at")
                except Exception as e:
                    logger.warning(f"[ClientMgmt] Docs fetch error for {email}: {e}")

            # Questionnaire completed?
            questionnaire_done = False
            if company_id:
                try:
                    qr_res = (
                        supabase.table("questionnaire_responses")
                        .select("id", count="exact")
                        .eq("company_id", company_id)
                        .execute()
                    )
                    questionnaire_done = (qr_res.count or len(qr_res.data or [])) > 0
                except Exception:
                    pass

            # Scan diffs (last comparison)
            last_diff = None
            if company_id:
                try:
                    diff_res = (
                        supabase.table("scan_diffs")
                        .select("*")
                        .eq("company_id", company_id)
                        .order("created_at", desc=True)
                        .limit(1)
                        .execute()
                    )
                    if diff_res.data:
                        last_diff = diff_res.data[0]
                except Exception:
                    pass

            # Determine fulfillment status
            # For subscription clients: need periodic rescan (every 30 days)
            client_plan_info = clients_by_email.get(email)
            scan_frequency = 30  # default days
            if client_plan_info:
                scan_frequency = client_plan_info.get("scan_frequency") or 30

            needs_rescan = False
            if active_sub and last_scan and scan_age_days is not None:
                needs_rescan = scan_age_days >= scan_frequency
            elif active_sub and not last_scan:
                needs_rescan = True

            fulfillment = "ok"  # up to date
            if not last_scan:
                fulfillment = "no_scan"
            elif needs_rescan:
                fulfillment = "needs_rescan"
            elif documents_count == 0:
                fulfillment = "needs_documents"

            # Summary accumulators
            summary["total_revenue"] += total_paid
            if active_sub:
                summary["active_subscriptions"] += 1
                if not sub_payment_ok:
                    summary["overdue_subscriptions"] += 1
            if needs_rescan:
                summary["needs_rescan"] += 1

            clients_list.append({
                "email": email,
                "company_name": company_name,
                "company_id": company_id,
                "company_url": company_url,
                "plan": latest_plan,
                "orders": [
                    {
                        "id": o.get("id"),
                        "order_number": o.get("order_number"),
                        "plan": o.get("plan"),
                        "amount": o.get("amount"),
                        "status": o.get("status"),
                        "order_type": o.get("order_type", "one_time"),
                        "paid_at": o.get("paid_at"),
                        "created_at": o.get("created_at"),
                    }
                    for o in client_orders
                ],
                "subscription": {
                    "id": active_sub.get("id"),
                    "plan": active_sub.get("plan"),
                    "amount": active_sub.get("amount"),
                    "status": active_sub.get("status"),
                    "cycle": active_sub.get("cycle"),
                    "last_charged_at": active_sub.get("last_charged_at"),
                    "next_charge_at": active_sub.get("next_charge_at"),
                    "total_charged": active_sub.get("total_charged", 0),
                    "activated_at": active_sub.get("activated_at"),
                    "payment_ok": sub_payment_ok,
                } if active_sub else None,
                "last_scan": last_scan,
                "scan_age_days": scan_age_days,
                "documents_count": documents_count,
                "documents_last_at": documents_last_at,
                "questionnaire_done": questionnaire_done,
                "last_diff": {
                    "has_changes": last_diff.get("has_changes"),
                    "added": last_diff.get("added_count", 0),
                    "removed": last_diff.get("removed_count", 0),
                    "changed": last_diff.get("changed_count", 0),
                    "summary": last_diff.get("summary", ""),
                    "created_at": last_diff.get("created_at"),
                } if last_diff else None,
                "fulfillment": fulfillment,
                "needs_rescan": needs_rescan,
            })

        summary["total_clients"] = len(clients_list)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ClientMgmt] Error loading client management data: {e}")
        raise HTTPException(status_code=500, detail=f"Chyba: {str(e)}")

    return {"clients": clients_list, "summary": summary}


# ─────────────────────────────────────────────
# 9. POST /crm/client/{email}/rescan — Trigger monitoring rescan
# ─────────────────────────────────────────────

@router.post("/crm/client/{email}/rescan")
async def crm_client_rescan(
    email: str,
    user: AuthUser = Depends(require_admin),
):
    """
    Admin-triggered rescan for a client:
    1. Find the client's company + URL
    2. Run a new scan
    3. Compare with previous scan (scan_diffs)
    4. If changes detected → regenerate documents → send email
    """
    from backend.database import get_supabase
    from backend.scanner.pipeline import run_scan_pipeline
    from backend.documents.pipeline import generate_compliance_kit
    from backend.outbound.email_engine import send_email

    supabase = get_supabase()

    # ── Find company ──
    company = None
    company_res = supabase.table("companies").select("*").ilike("email", email).limit(1).execute()
    if company_res.data:
        company = company_res.data[0]
    else:
        # Try via clients table
        client_res = supabase.table("clients").select("company_id").ilike("email", email).limit(1).execute()
        if client_res.data and client_res.data[0].get("company_id"):
            cid = client_res.data[0]["company_id"]
            comp_res = supabase.table("companies").select("*").eq("id", cid).limit(1).execute()
            if comp_res.data:
                company = comp_res.data[0]

    if not company:
        raise HTTPException(status_code=404, detail=f"Firma pro {email} nenalezena")

    company_id = company["id"]
    url = company.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="Firma nemá nastavenou URL pro scanování")

    # ── Get previous scan's findings for comparison ──
    prev_findings_set = set()
    try:
        prev_scan_res = (
            supabase.table("scans")
            .select("id, total_findings")
            .eq("company_id", company_id)
            .eq("status", "done")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if prev_scan_res.data:
            prev_scan_id = prev_scan_res.data[0]["id"]
            prev_f_res = (
                supabase.table("findings")
                .select("name, category, risk_level")
                .eq("scan_id", prev_scan_id)
                .execute()
            )
            for f in (prev_f_res.data or []):
                prev_findings_set.add(
                    f"{f.get('name','')}__{f.get('category','')}__{f.get('risk_level','')}"
                )
    except Exception as e:
        logger.warning(f"[Rescan] Previous findings fetch error: {e}")

    # ── Run new scan ──
    now = datetime.now(timezone.utc).isoformat()
    new_scan = supabase.table("scans").insert({
        "company_id": company_id,
        "url_scanned": url,
        "status": "queued",
        "triggered_by": "monitoring",
        "started_at": now,
    }).execute()

    scan_id = new_scan.data[0]["id"]

    try:
        await run_scan_pipeline(scan_id)
    except Exception as e:
        logger.error(f"[Rescan] Scan pipeline failed for {email}: {e}")
        raise HTTPException(status_code=500, detail=f"Sken selhal: {str(e)}")

    # ── Compare findings ──
    new_findings_set = set()
    try:
        new_f_res = (
            supabase.table("findings")
            .select("name, category, risk_level")
            .eq("scan_id", scan_id)
            .execute()
        )
        for f in (new_f_res.data or []):
            new_findings_set.add(
                f"{f.get('name','')}__{f.get('category','')}__{f.get('risk_level','')}"
            )
    except Exception:
        pass

    added = new_findings_set - prev_findings_set
    removed = prev_findings_set - new_findings_set
    changes_detected = len(added) > 0 or len(removed) > 0

    # ── Save diff record ──
    try:
        prev_scan_id_val = prev_scan_res.data[0]["id"] if prev_scan_res.data else None
        supabase.table("scan_diffs").insert({
            "company_id": company_id,
            "previous_scan_id": prev_scan_id_val,
            "current_scan_id": scan_id,
            "has_changes": changes_detected,
            "added_count": len(added),
            "removed_count": len(removed),
            "changed_count": 0,
            "unchanged_count": len(new_findings_set & prev_findings_set),
            "summary": f"Přidáno: {len(added)}, Odebráno: {len(removed)}"
                       + (" — beze změn" if not changes_detected else " — ZMĚNY DETEKOVÁNY"),
        }).execute()
    except Exception as e:
        logger.warning(f"[Rescan] Diff insert error: {e}")

    # ── If changes → regenerate docs + send email ──
    docs_regenerated = False
    email_sent = False

    if changes_detected:
        # Find client_id for document generation (can be company_id)
        doc_target_id = company_id
        try:
            client_rec = supabase.table("clients").select("id").ilike("email", email).limit(1).execute()
            if client_rec.data:
                doc_target_id = client_rec.data[0]["id"]
        except Exception:
            pass

        # Regenerate documents
        try:
            kit_result = await generate_compliance_kit(doc_target_id)
            docs_regenerated = kit_result.success_count > 0
            logger.info(f"[Rescan] Documents regenerated for {email}: {kit_result.success_count} docs")
        except Exception as e:
            logger.error(f"[Rescan] Document generation failed for {email}: {e}")

        # Send notification email
        try:
            company_name = company.get("name", "Vaše firma")
            html_body = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #0f172a, #1e293b); border-radius: 16px; padding: 32px; color: white;">
                    <h1 style="color: #22d3ee; margin-bottom: 8px;">🛡️ AIshield.cz</h1>
                    <h2 style="color: white; margin-top: 0;">Aktualizace AI Act compliance</h2>

                    <p style="color: #94a3b8;">Dobrý den,</p>

                    <p style="color: #e2e8f0;">
                        Při pravidelném monitoringu webu <strong>{url}</strong> jsme zaznamenali
                        <strong style="color: #fbbf24;">změny v používaných AI systémech</strong>.
                    </p>

                    <div style="background: rgba(255,255,255,0.1); border-radius: 12px; padding: 20px; margin: 20px 0;">
                        <p style="color: #22d3ee; font-weight: bold; margin-top: 0;">📊 Výsledky srovnání:</p>
                        <ul style="color: #e2e8f0; list-style: none; padding: 0;">
                            <li style="padding: 4px 0;">➕ Nově detekováno: <strong>{len(added)}</strong> AI systémů</li>
                            <li style="padding: 4px 0;">➖ Odebráno: <strong>{len(removed)}</strong> AI systémů</li>
                        </ul>
                    </div>

                    {"<p style='color: #e2e8f0;'>Na základě těchto změn jsme vám <strong>vygenerovali aktualizované compliance dokumenty</strong>, které naleznete ve svém dashboardu.</p>" if docs_regenerated else ""}

                    <a href="https://aishield.cz/dashboard"
                       style="display: inline-block; background: linear-gradient(135deg, #06b6d4, #8b5cf6); color: white; text-decoration: none; padding: 14px 32px; border-radius: 12px; font-weight: bold; margin-top: 16px;">
                        Zobrazit dashboard →
                    </a>

                    <p style="color: #64748b; font-size: 12px; margin-top: 32px;">
                        Toto je automatická zpráva z monitorovacího systému AIshield.cz.
                    </p>
                </div>
            </div>
            """

            await send_email(
                to=email,
                subject=f"AIshield — Změny AI systémů na webu {company_name}",
                html=html_body,
                from_email="info@aishield.cz",
                from_name="AIshield.cz",
            )
            email_sent = True
            logger.info(f"[Rescan] Notification email sent to {email}")
        except Exception as e:
            logger.error(f"[Rescan] Email send error for {email}: {e}")

    # ── Log activity ──
    try:
        supabase.table("company_activities").insert({
            "company_id": company_id,
            "activity_type": "monitoring_rescan",
            "title": f"Admin rescan — {'změny' if changes_detected else 'beze změn'}",
            "description": (
                f"Rescan dokončen. Přidáno: {len(added)}, Odebráno: {len(removed)}."
                + (f" Dokumenty přegenerovány." if docs_regenerated else "")
                + (f" Email odeslán." if email_sent else "")
            ),
            "actor": user.email,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception:
        pass

    # Update company last_scanned_at
    try:
        supabase.table("companies").update({
            "last_scanned_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", company_id).execute()
    except Exception:
        pass

    return {
        "status": "completed",
        "email": email,
        "company_name": company.get("name"),
        "scan_id": scan_id,
        "changes_detected": changes_detected,
        "added_count": len(added),
        "removed_count": len(removed),
        "documents_regenerated": docs_regenerated,
        "email_sent": email_sent,
    }


# ─────────────────────────────────────────────
# 10. GET /crm/business-overview — Complete business overview for admin dashboard
# ─────────────────────────────────────────────

@router.get("/crm/business-overview")
async def crm_business_overview(
    request: Request,
    user: AuthUser = Depends(require_admin),
):
    """
    Kompletní obchodní přehled — VŠECHNO co admin potřebuje vědět na jednom místě:
    - Revenue timeline (denní) pro graf
    - Konverzní funnel (sken → dotazník → objednávka → platba → dokumenty)
    - Všechny objednávky s detaily (platební metoda, stav, stáří)
    - Fulfillment tracking s deadliny
    - Outreach statistiky (osloveno, reagovalo, koupilo)
    - Subscription přehled
    """
    await _check_admin_rate_limit(request)
    from backend.database import get_supabase
    supabase = get_supabase()

    now = datetime.now(timezone.utc)

    # ── 1. All orders ──
    orders = []
    try:
        res = supabase.table("orders").select("*").order("created_at", desc=True).execute()
        orders = res.data or []
    except Exception as e:
        logger.error(f"business-overview orders: {e}")

    # ── 2. All subscriptions ──
    subscriptions = []
    try:
        res = supabase.table("subscriptions").select("*").order("created_at", desc=True).execute()
        subscriptions = res.data or []
    except Exception as e:
        logger.error(f"business-overview subscriptions: {e}")

    # ── 3. All scans ──
    scans = []
    try:
        res = supabase.table("scans").select("id,company_id,url_scanned,status,triggered_by,started_at,finished_at,total_findings,created_at").order("created_at", desc=True).limit(500).execute()
        scans = res.data or []
    except Exception as e:
        logger.error(f"business-overview scans: {e}")

    # ── 4. All companies ──
    companies = []
    try:
        res = supabase.table("companies").select("id,name,url,email,scan_status,workflow_status,payment_status,emails_sent,last_email_at,last_scanned_at,created_at,source").order("created_at", desc=True).execute()
        companies = res.data or []
    except Exception as e:
        logger.error(f"business-overview companies: {e}")

    # ── 5. All documents ──
    documents = []
    try:
        res = supabase.table("documents").select("id,company_id,created_at").execute()
        documents = res.data or []
    except Exception as e:
        logger.error(f"business-overview documents: {e}")

    # ── 6. Questionnaire responses ──
    questionnaires = []
    try:
        res = supabase.table("questionnaire_responses").select("id,client_id,company_id,created_at").execute()
        questionnaires = res.data or []
    except Exception as e:
        logger.error(f"business-overview questionnaires: {e}")

    # ── 7. Email log for outreach stats ──
    email_stats = {"total": 0, "delivered": 0, "opened": 0, "clicked": 0, "bounced": 0}
    try:
        res = supabase.table("email_log").select("id,status,to_email,sent_at").execute()
        email_log = res.data or []
        email_stats["total"] = len(email_log)
        unique_emails = set()
        for e_entry in email_log:
            st = e_entry.get("status", "")
            unique_emails.add(e_entry.get("to_email"))
            if st == "delivered":
                email_stats["delivered"] += 1
            elif st == "opened":
                email_stats["opened"] += 1
            elif st == "clicked":
                email_stats["clicked"] += 1
            elif st == "bounced":
                email_stats["bounced"] += 1
        email_stats["unique_recipients"] = len(unique_emails)
    except Exception as e:
        logger.error(f"business-overview email_log: {e}")

    # ── COMPUTED METRICS ──

    # Revenue timeline (daily, last 90 days)
    revenue_timeline = {}
    for o in orders:
        if o.get("status") == "PAID" and o.get("paid_at"):
            try:
                day = o["paid_at"][:10]  # YYYY-MM-DD
                revenue_timeline[day] = revenue_timeline.get(day, 0) + (o.get("amount") or 0)
            except Exception:
                pass

    # Sort timeline
    sorted_timeline = sorted(revenue_timeline.items(), key=lambda x: x[0])
    revenue_chart = [{"date": d, "amount": a} for d, a in sorted_timeline[-90:]]

    # Revenue summary
    total_revenue = sum(o.get("amount", 0) for o in orders if o.get("status") == "PAID")
    pending_revenue = sum(o.get("amount", 0) for o in orders if o.get("status") in ("CREATED", "PAYMENT_METHOD_CHOSEN", "AUTHORIZED"))
    refunded_revenue = sum(o.get("refund_amount", 0) or o.get("amount", 0) for o in orders if o.get("status") in ("REFUNDED", "PARTIALLY_REFUNDED"))

    # Revenue this month
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    revenue_this_month = sum(
        o.get("amount", 0) for o in orders
        if o.get("status") == "PAID" and (o.get("paid_at") or "") >= month_start
    )

    # Orders breakdown
    order_breakdown = {
        "total": len(orders),
        "paid": len([o for o in orders if o.get("status") == "PAID"]),
        "pending": len([o for o in orders if o.get("status") in ("CREATED", "PAYMENT_METHOD_CHOSEN", "AUTHORIZED")]),
        "canceled": len([o for o in orders if o.get("status") in ("CANCELED", "TIMEOUTED")]),
        "refunded": len([o for o in orders if o.get("status") in ("REFUNDED", "PARTIALLY_REFUNDED")]),
    }

    # Orders by plan
    plan_breakdown = {}
    for o in orders:
        plan = o.get("plan", "unknown")
        if plan not in plan_breakdown:
            plan_breakdown[plan] = {"count": 0, "paid": 0, "revenue": 0}
        plan_breakdown[plan]["count"] += 1
        if o.get("status") == "PAID":
            plan_breakdown[plan]["paid"] += 1
            plan_breakdown[plan]["revenue"] += o.get("amount", 0)

    # Orders by type (one_time vs subscription)
    type_breakdown = {}
    for o in orders:
        ot = o.get("order_type", "one_time")
        if ot not in type_breakdown:
            type_breakdown[ot] = {"count": 0, "paid": 0, "revenue": 0}
        type_breakdown[ot]["count"] += 1
        if o.get("status") == "PAID":
            type_breakdown[ot]["paid"] += 1
            type_breakdown[ot]["revenue"] += o.get("amount", 0)

    # Subscription summary
    active_subs = [s for s in subscriptions if s.get("status") == "active"]
    sub_summary = {
        "total": len(subscriptions),
        "active": len(active_subs),
        "cancelled": len([s for s in subscriptions if s.get("status") == "cancelled"]),
        "monthly_recurring_revenue": sum(s.get("amount", 0) for s in active_subs),
        "total_charged": sum(s.get("total_charged", 0) for s in subscriptions),
    }

    # Conversion funnel
    total_companies = len(companies)
    scanned_companies = len([c for c in companies if c.get("scan_status") == "scanned"])
    companies_with_questionnaire = len(set(q.get("company_id") for q in questionnaires if q.get("company_id")))
    companies_with_orders = len(set(o.get("email") for o in orders))
    companies_paid = len(set(o.get("email") for o in orders if o.get("status") == "PAID"))
    companies_with_docs = len(set(d.get("company_id") for d in documents if d.get("company_id")))

    funnel = {
        "total_companies": total_companies,
        "scanned": scanned_companies,
        "questionnaire_filled": companies_with_questionnaire,
        "ordered": companies_with_orders,
        "paid": companies_paid,
        "documents_delivered": companies_with_docs,
    }

    # Fulfillment tracking — for each paid order, check delivery status
    # Build company lookup
    company_by_id = {c["id"]: c for c in companies if c.get("id")}
    company_by_email = {}
    for c in companies:
        if c.get("email"):
            company_by_email[c["email"].lower()] = c

    doc_by_company = {}
    for d in documents:
        cid = d.get("company_id")
        if cid:
            if cid not in doc_by_company:
                doc_by_company[cid] = []
            doc_by_company[cid].append(d)

    scan_by_company = {}
    for s in scans:
        cid = s.get("company_id")
        if cid and cid not in scan_by_company:
            scan_by_company[cid] = s  # latest scan (already sorted desc)

    # Detailed orders list with fulfillment
    DELIVERY_DEADLINE_DAYS = 5  # 5 working days ~ 7 calendar days
    detailed_orders = []
    for o in orders:
        email = (o.get("email") or o.get("user_email") or "").lower()
        company = company_by_email.get(email)
        company_id = company["id"] if company else None
        company_name = company.get("name", "") if company else ""

        # Calculate days since order
        created = o.get("created_at", "")
        days_since_order = 0
        if created:
            try:
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                days_since_order = (now - created_dt).days
            except Exception:
                pass

        # Paid date
        paid_at = o.get("paid_at")
        days_since_payment = 0
        if paid_at:
            try:
                paid_dt = datetime.fromisoformat(paid_at.replace("Z", "+00:00"))
                days_since_payment = (now - paid_dt).days
            except Exception:
                pass

        # Fulfillment status
        has_scan = company_id in scan_by_company if company_id else False
        has_docs = company_id in doc_by_company if company_id else False
        docs_count = len(doc_by_company.get(company_id, [])) if company_id else 0

        if o.get("status") != "PAID":
            fulfillment = "not_paid"
            deadline_status = "n/a"
            days_remaining = None
        elif has_docs and docs_count >= 7:
            fulfillment = "delivered"
            deadline_status = "ok"
            days_remaining = None
        elif o.get("order_type") in ("subscription", "subscription_recurrence"):
            fulfillment = "subscription"
            deadline_status = "ok"
            days_remaining = None
        else:
            fulfillment = "pending"
            days_remaining = max(0, DELIVERY_DEADLINE_DAYS - days_since_payment)
            deadline_status = "ok" if days_remaining > 1 else ("warning" if days_remaining > 0 else "overdue")

        detailed_orders.append({
            "id": o.get("id"),
            "order_number": o.get("order_number"),
            "plan": o.get("plan"),
            "amount": o.get("amount"),
            "email": email,
            "company_name": company_name,
            "status": o.get("status"),
            "order_type": o.get("order_type", "one_time"),
            "gopay_payment_id": o.get("gopay_payment_id"),
            "created_at": created,
            "paid_at": paid_at,
            "days_since_order": days_since_order,
            "days_since_payment": days_since_payment,
            "fulfillment": fulfillment,
            "deadline_status": deadline_status,
            "days_remaining": days_remaining,
            "docs_count": docs_count,
            "has_scan": has_scan,
            "refund_amount": o.get("refund_amount"),
            "refunded_at": o.get("refunded_at"),
        })

    # Fulfillment summary
    fulfillment_summary = {
        "delivered": len([o for o in detailed_orders if o["fulfillment"] == "delivered"]),
        "pending": len([o for o in detailed_orders if o["fulfillment"] == "pending"]),
        "overdue": len([o for o in detailed_orders if o["deadline_status"] == "overdue"]),
        "warning": len([o for o in detailed_orders if o["deadline_status"] == "warning"]),
        "not_paid": len([o for o in detailed_orders if o["fulfillment"] == "not_paid"]),
    }

    # Outreach funnel (companies from email campaigns)
    emailed_companies = set()
    for c in companies:
        if (c.get("emails_sent") or 0) > 0:
            emailed_companies.add(c.get("id"))

    outreach = {
        "total_in_database": total_companies,
        "emailed": len(emailed_companies),
        "emails_sent_total": email_stats["total"],
        "emails_delivered": email_stats["delivered"],
        "emails_opened": email_stats["opened"],
        "emails_clicked": email_stats["clicked"],
        "emails_bounced": email_stats["bounced"],
        "unique_recipients": email_stats.get("unique_recipients", 0),
        "registered_from_outreach": 0,  # TODO: track source=outreach on registration
        "purchased_from_outreach": 0,   # TODO: track conversion source
        "open_rate": round(email_stats["opened"] / max(email_stats["delivered"], 1), 3),
        "click_rate": round(email_stats["clicked"] / max(email_stats["opened"], 1), 3),
    }

    # Scans summary
    scan_summary = {
        "total": len(scans),
        "done": len([s for s in scans if s.get("status") == "done"]),
        "error": len([s for s in scans if s.get("status") == "error"]),
        "by_trigger": {},
    }
    for s in scans:
        trigger = s.get("triggered_by", "unknown")
        scan_summary["by_trigger"][trigger] = scan_summary["by_trigger"].get(trigger, 0) + 1

    # Recent activity (last 20 orders + subscriptions merged, sorted by date)
    recent_events = []
    for o in orders[:20]:
        recent_events.append({
            "type": "order",
            "date": o.get("created_at"),
            "email": o.get("email") or o.get("user_email"),
            "detail": f"{o.get('plan', '?')} — {o.get('status', '?')} — {fmtAmount(o.get('amount', 0))}",
            "status": o.get("status"),
        })
    for s in subscriptions[:10]:
        recent_events.append({
            "type": "subscription",
            "date": s.get("created_at"),
            "email": s.get("email"),
            "detail": f"{s.get('plan', '?')} — {s.get('status', '?')} — {s.get('amount', 0)} Kč/měsíc",
            "status": s.get("status"),
        })
    recent_events.sort(key=lambda x: x.get("date") or "", reverse=True)

    return {
        "generated_at": now.isoformat(),
        "revenue": {
            "total": total_revenue,
            "pending": pending_revenue,
            "refunded": refunded_revenue,
            "this_month": revenue_this_month,
            "chart": revenue_chart,
        },
        "orders": {
            "breakdown": order_breakdown,
            "by_plan": plan_breakdown,
            "by_type": type_breakdown,
            "detailed": detailed_orders,
        },
        "subscriptions": sub_summary,
        "funnel": funnel,
        "fulfillment": fulfillment_summary,
        "outreach": outreach,
        "scans": scan_summary,
        "recent_events": recent_events[:30],
    }


def fmtAmount(amount: int | float) -> str:
    """Format amount for display."""
    return f"{int(amount):,} Kč".replace(",", " ")
