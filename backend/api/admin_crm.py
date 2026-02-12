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
