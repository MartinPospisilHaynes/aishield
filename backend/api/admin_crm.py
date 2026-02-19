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
from datetime import datetime, timedelta, timezone

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

# ── Admin password from environment ──
def _get_admin_password() -> str:
    from backend.config import get_settings
    pw = get_settings().admin_password
    if not pw:
        raise RuntimeError("ADMIN_PASSWORD not configured in .env")
    return pw

# ── Brute-force protection ──
_MAX_LOGIN_ATTEMPTS = 5          # max pokusy v okně
_LOGIN_LOCKOUT_SECONDS = 900     # 15 minut lockout
_login_attempts: dict[str, tuple[int, float]] = {}   # {ip: (count, first_attempt_timestamp)}


# ─────────────────────────────────────────────
# 1. POST /login — Admin login
# ─────────────────────────────────────────────

@router.post("/crm/login")
async def admin_crm_login(request: Request):
    """
    Admin CRM login — vrátí jednoduchý token.
    Hardcoded: username=ADMIN, password=supabase_db_password.
    Brute-force protection: max 5 pokusů za 15 minut per IP.
    Honeypot: pokud je vyplněné pole "website", odmítneme (bot).
    """
    # ── Rate limit per IP ──
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    ip = ip.split(",")[0].strip()

    # Check brute-force lockout
    now = time.time()
    key = f"admin_login_{ip}"
    if key in _login_attempts:
        attempts, first_attempt = _login_attempts[key]
        window = now - first_attempt
        if window < _LOGIN_LOCKOUT_SECONDS and attempts >= _MAX_LOGIN_ATTEMPTS:
            remaining = int(_LOGIN_LOCKOUT_SECONDS - window)
            logger.warning(f"[Auth] Brute-force lockout for IP {ip} — {remaining}s remaining")
            raise HTTPException(
                status_code=429,
                detail=f"Příliš mnoho neúspěšných pokusů. Zkuste znovu za {remaining} sekund.",
                headers={"Retry-After": str(remaining)},
            )
        # Reset window if expired
        if window >= _LOGIN_LOCKOUT_SECONDS:
            del _login_attempts[key]

    body = await request.json()

    # ── Honeypot check ── (bot detector — toto pole je v UI skryté, člověk ho nevyplní)
    honeypot = (body.get("website") or "").strip()
    if honeypot:
        logger.warning(f"[Auth] Honeypot triggered from IP {ip}: {honeypot}")
        # Vrátíme fake "success" aby bot nevěděl že byl odhalený
        raise HTTPException(status_code=401, detail="Neplatné přihlašovací údaje")

    username = (body.get("username") or "").strip()
    password = (body.get("password") or "").strip()

    if username != "ADMIN" or password != _get_admin_password():
        # Record failed attempt
        if key in _login_attempts:
            attempts, first_attempt = _login_attempts[key]
            _login_attempts[key] = (attempts + 1, first_attempt)
        else:
            _login_attempts[key] = (1, now)

        remaining_attempts = _MAX_LOGIN_ATTEMPTS - _login_attempts[key][0]
        if remaining_attempts <= 0:
            logger.warning(f"[Auth] Admin login locked out for IP {ip}")
            raise HTTPException(
                status_code=429,
                detail=f"Příliš mnoho neúspěšných pokusů. Účet uzamčen na {_LOGIN_LOCKOUT_SECONDS // 60} minut.",
            )

        logger.warning(f"[Auth] Failed admin login from IP {ip} (attempt {_login_attempts[key][0]}/{_MAX_LOGIN_ATTEMPTS})")
        raise HTTPException(status_code=401, detail="Neplatné přihlašovací údaje")

    # ── Success — clear failed attempts ──
    if key in _login_attempts:
        del _login_attempts[key]

    # Jednoduchý token: admin_ + SHA256 hash (prvních 32 znaků)
    token = "admin_" + hashlib.sha256(password.encode()).hexdigest()[:32]

    logger.info(f"[Auth] Admin login successful from IP {ip}")

    return {
        "token": token,
        "expires_in": 86400,
        "username": "ADMIN",
        "message": "Přihlášení úspěšné",
    }


# ─────────────────────────────────────────────
# 1b. GET /crm/verify — Ověření platnosti admin tokenu
# ─────────────────────────────────────────────

@router.get("/crm/verify")
async def admin_verify_token(
    user: AuthUser = Depends(require_admin),
):
    """Ověří, zda je admin token stále platný."""
    return {"ok": True, "username": "ADMIN"}


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


# ── Helper: send payment status email to client ──

async def _send_payment_status_email(
    to_email: str,
    company_name: str,
    company_id: str,
    new_status: str,
) -> None:
    """Send branded email to client when admin changes payment_status."""
    from backend.outbound.email_engine import send_email
    from backend.outbound.payment_emails import (
        _email_wrapper,
        PLAN_NAMES,
        build_status_pending_email,
        build_status_overdue_email,
        build_status_refunded_email,
        build_status_free_trial_email,
        generate_variable_symbol,
    )
    from backend.database import get_supabase

    supabase = get_supabase()

    # Fetch latest order for this company (provides context for emails)
    order = {}
    try:
        order_res = (
            supabase.table("orders")
            .select("order_number, plan, amount, due_date")
            .eq("company_id", company_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if order_res.data:
            order = order_res.data[0]
    except Exception:
        pass

    order_number = order.get("order_number", "")
    plan = order.get("plan", "")
    amount = order.get("amount", 0) or 0
    due_date = order.get("due_date", "")
    vs = generate_variable_symbol(order_number) if order_number else ""

    # ── Build email by status ──
    subject_map = {
        "paid":       "AIshield.cz — Platba přijata ✅",
        "pending":    "AIshield.cz — Čekáme na platbu 💳",
        "overdue":    "AIshield.cz — Upomínka: platba po splatnosti ⏰",
        "refunded":   "AIshield.cz — Platba vrácena 💸",
        "free_trial": "AIshield.cz — Zkušební přístup aktivován 🎁",
    }

    if new_status == "paid":
        # Use the inline template for paid (already proven)
        plan_label = PLAN_NAMES.get(plan, plan.upper()) if plan else ""
        order_block = ""
        if order_number:
            order_block = f"""
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           style="background:rgba(34,197,94,0.06);border:1px solid rgba(34,197,94,0.2);border-radius:12px;margin-bottom:24px;">
    <tr><td style="padding:20px 24px;">
        <p style="margin:0 0 4px 0;font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:1px;">Objednávka</p>
        <p style="margin:0 0 16px 0;font-size:16px;font-weight:700;color:#ffffff;font-family:monospace;">{order_number}</p>
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        {'<tr><td style="padding:6px 0;font-size:13px;color:#94a3b8;width:40%;">Služba:</td><td style="padding:6px 0;font-size:13px;color:#ffffff;font-weight:600;">' + plan_label + '</td></tr>' if plan_label else ''}
        <tr>
            <td style="padding:6px 0;font-size:13px;color:#94a3b8;">Uhrazeno:</td>
            <td style="padding:6px 0;font-size:16px;color:#22c55e;font-weight:800;">{amount:,} Kč</td>
        </tr>
        </table>
    </td></tr>
    </table>
"""
        content = f"""
    <h1 style="margin:0 0 8px 0;font-size:24px;font-weight:800;color:#ffffff;">Platba přijata ✅</h1>
    <p style="margin:0 0 24px 0;font-size:14px;color:#94a3b8;">
        Dobrý den, potvrzujeme přijetí platby{(', ' + company_name) if company_name else ''}. Děkujeme!
    </p>
    {order_block}
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:12px;margin-bottom:24px;">
    <tr><td style="padding:24px;">
        <p style="margin:0 0 12px 0;font-size:13px;color:#94a3b8;line-height:1.6;">
            Nyní prosím vyplňte dotazník, abychom vám připravili dokumenty přesně na míru.
        </p>
        <p style="margin:0;font-size:13px;color:#94a3b8;line-height:1.6;">
            Hotové dílo odevzdáváme <strong style="color:#ffffff;">do 7 pracovních dní</strong>.
        </p>
    </td></tr>
    </table>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:8px 0 0 0;">
        <a href="https://aishield.cz/dotaznik"
           style="display:inline-block;padding:14px 32px;background:linear-gradient(135deg,#7c3aed,#d946ef);color:#ffffff;font-size:14px;font-weight:700;text-decoration:none;border-radius:12px;">
            Vyplnit dotazník
        </a>
    </td></tr>
    <tr><td align="center" style="padding:12px 0 0 0;">
        <a href="https://aishield.cz/dashboard"
           style="display:inline-block;padding:12px 28px;border:1px solid rgba(255,255,255,0.15);color:#ffffff;font-size:13px;font-weight:600;text-decoration:none;border-radius:12px;">
            Přejít na Dashboard
        </a>
    </td></tr>
    </table>
        """
        html = _email_wrapper(content)

    elif new_status == "pending":
        html = build_status_pending_email(
            company_name=company_name,
            order_number=order_number,
            plan=plan,
            amount=amount,
            variable_symbol=vs,
            due_date=due_date,
        )
    elif new_status == "overdue":
        html = build_status_overdue_email(
            company_name=company_name,
            order_number=order_number,
            plan=plan,
            amount=amount,
            variable_symbol=vs,
        )
    elif new_status == "refunded":
        html = build_status_refunded_email(
            company_name=company_name,
            order_number=order_number,
            plan=plan,
            amount=amount,
        )
    elif new_status == "free_trial":
        html = build_status_free_trial_email(
            company_name=company_name,
        )
    else:
        return  # no email for 'none' or unknown statuses

    subject = subject_map.get(new_status, f"AIshield.cz — Změna stavu platby")

    await send_email(
        to=to_email,
        subject=subject,
        html=html,
        from_email="info@aishield.cz",
        from_name="AIshield.cz",
    )


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
    company_res = supabase.table("companies").select("id, name, email, workflow_status, payment_status").eq("id", company_id).execute()
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

        # ── Send email to client when payment_status changes ──
        old_payment = old_company.get("payment_status", "none")
        new_payment = update_data.get("payment_status")
        client_email = old_company.get("email")
        company_name = old_company.get("name", "")

        if new_payment and new_payment != old_payment and new_payment != "none" and client_email:
            try:
                await _send_payment_status_email(
                    to_email=client_email,
                    company_name=company_name,
                    company_id=company_id,
                    new_status=new_payment,
                )
                logger.info(f"[CRM] Payment status email ({new_payment}) sent to {client_email} (company: {company_name})")
            except Exception as e:
                logger.warning(f"[CRM] Payment status email ({new_payment}) failed for {client_email}: {e}")

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
# 3b. POST /crm/company/{company_id}/approve-docs — Admin schválí dokumenty k odeslání
# ─────────────────────────────────────────────

@router.post("/crm/company/{company_id}/approve-docs")
async def crm_approve_documents(
    company_id: str,
    user: AuthUser = Depends(require_admin),
):
    """
    BEZPEČNOSTNÍ GATE: Admin schválí vygenerované dokumenty.
    Teprve po schválení se klientovi odešle email s oznámením.
    Žádný dokument se klientovi nedoručí bez admin schválení.
    """
    from backend.database import get_supabase
    from backend.outbound.email_engine import send_email

    supabase = get_supabase()

    # Najdi firmu
    company_res = supabase.table("companies").select(
        "id, name, email, workflow_status"
    ).eq("id", company_id).execute()

    if not company_res.data:
        raise HTTPException(status_code=404, detail="Firma nenalezena")

    company = company_res.data[0]

    # Najdi objednávku ve stavu awaiting_approval
    orders_res = supabase.table("orders").select(
        "id, workflow_status, user_email"
    ).eq("company_id", company_id).eq(
        "workflow_status", "awaiting_approval"
    ).execute()

    if not orders_res.data:
        raise HTTPException(
            status_code=400,
            detail="Žádné dokumenty nečekají na schválení (workflow_status != awaiting_approval)"
        )

    order = orders_res.data[0]
    client_email = company.get("email") or order.get("user_email", "")
    company_name = company.get("name", "")

    # Update workflow → documents_ready
    supabase.table("orders").update({
        "workflow_status": "documents_ready",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", order["id"]).execute()

    # Zapiš aktivitu
    try:
        supabase.table("company_activities").insert({
            "company_id": company_id,
            "activity_type": "documents_approved",
            "title": "Dokumenty schváleny adminem",
            "description": f"Admin {user.email} schválil dokumenty k odeslání klientovi.",
            "actor": user.email,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception:
        pass

    # Teď odeslat email klientovi
    email_sent = False
    if client_email:
        try:
            settings = get_settings()
            dashboard_url = f"{settings.app_url}/dashboard?company={company_id}"

            html = f"""
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
    <div style="background:linear-gradient(135deg,#0f172a,#1e1b4b,#312e81);border-radius:12px 12px 0 0;padding:30px 24px;text-align:center;">
        <h1 style="color:white;margin:0;font-size:22px;">AIshield.cz</h1>
    </div>
    <div style="background:white;padding:28px 24px;border:1px solid #e2e8f0;border-top:none;">
        <h2 style="color:#1e293b;font-size:18px;margin:0 0 16px;">📄 Vaše dokumenty jsou připraveny</h2>
        <p style="color:#1e293b;font-size:15px;line-height:1.6;">
            S radostí vám oznamujeme, že vaše compliance dokumentace pro firmu
            <strong>{company_name}</strong> byla zkontrolována a je připravena ke stažení.
        </p>
        <div style="text-align:center;margin:24px 0;">
            <a href="{dashboard_url}" style="display:inline-block;background:#7c3aed;color:white;text-decoration:none;padding:14px 32px;border-radius:8px;font-size:15px;font-weight:600;">
                Otevřít dashboard a stáhnout dokumenty →
            </a>
        </div>
    </div>
    <div style="background:#0f172a;border-radius:0 0 12px 12px;padding:20px 24px;text-align:center;">
        <p style="color:#94a3b8;font-size:12px;margin:0;">AIshield.cz — AI compliance pro české firmy</p>
    </div>
</div>"""

            await send_email(
                to=client_email,
                subject=f"📄 Vaše dokumenty jsou připraveny — {company_name}",
                html=html,
                from_email="info@aishield.cz",
            )
            email_sent = True
            logger.info(f"[CRM] Dokumenty schváleny + email odeslán: {client_email} ({company_name})")
        except Exception as e:
            logger.error(f"[CRM] Schválení OK, ale email selhal: {e}")

    return {
        "status": "approved",
        "company_id": company_id,
        "company_name": company_name,
        "email_sent": email_sent,
        "email": client_email,
        "workflow_status": "documents_ready",
    }


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
                    answered = qr_res.count or len(qr_res.data or [])
                    from backend.api.questionnaire import QUESTIONNAIRE_SECTIONS
                    all_qkeys = {q["key"] for s in QUESTIONNAIRE_SECTIONS for q in s["questions"]}
                    questionnaire_done = answered >= len(all_qkeys)
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


# ── Czech business days helper ──
_CZECH_HOLIDAYS = {
    # 2025
    "2025-01-01", "2025-04-18", "2025-04-21", "2025-05-01", "2025-05-08",
    "2025-07-05", "2025-07-06", "2025-09-28", "2025-10-28", "2025-11-17",
    "2025-12-24", "2025-12-25", "2025-12-26",
    # 2026
    "2026-01-01", "2026-04-03", "2026-04-06", "2026-05-01", "2026-05-08",
    "2026-07-05", "2026-07-06", "2026-09-28", "2026-10-28", "2026-11-17",
    "2026-12-24", "2026-12-25", "2026-12-26",
}

def _count_business_days(start_dt: datetime, end_dt: datetime) -> int:
    """Count business days (Mon-Fri, excluding CZ holidays) between two datetimes."""
    if end_dt <= start_dt:
        return 0
    count = 0
    current = start_dt.date() + timedelta(days=1)
    end_date = end_dt.date()
    while current <= end_date:
        if current.weekday() < 5 and current.isoformat() not in _CZECH_HOLIDAYS:
            count += 1
        current += timedelta(days=1)
    return count

def _add_business_days(start_dt: datetime, days: int) -> datetime:
    """Add N business days to a datetime."""
    current = start_dt
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5 and current.date().isoformat() not in _CZECH_HOLIDAYS:
            added += 1
    return current


# ── Business overview cache (60s TTL) ──
_biz_overview_cache: dict = {"data": None, "expires": 0}
_BIZ_CACHE_TTL = 60  # seconds

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
    import time as _time
    cache_now = _time.time()
    if _biz_overview_cache["data"] and cache_now < _biz_overview_cache["expires"]:
        return _biz_overview_cache["data"]
    from backend.database import get_supabase
    supabase = get_supabase()

    now = datetime.now(timezone.utc)

    # ── 1. All orders ──
    orders = []
    try:
        res = supabase.table("orders").select("*").order("created_at", desc=True).limit(1000).execute()
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
        res = supabase.table("documents").select("id,company_id,created_at").limit(5000).execute()
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
        res = supabase.table("email_log").select("id,status,to_email,sent_at").order("sent_at", desc=True).limit(5000).execute()
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

    # Churn rate (last 30 days)
    thirty_days_ago = (now - timedelta(days=30)).isoformat()
    cancelled_last_30 = len([s for s in subscriptions if s.get("status") == "cancelled" and (s.get("cancelled_at") or s.get("updated_at") or "") >= thirty_days_ago])
    active_at_start = len(active_subs) + cancelled_last_30  # approximate
    churn_rate = round(cancelled_last_30 / max(active_at_start, 1), 4)

    # Active paying customers
    active_customers = len(set(
        o.get("email") for o in orders
        if o.get("status") == "PAID" and o.get("email")
    ))

    # Conversion funnel
    total_companies = len(companies)
    scanned_companies = len([c for c in companies if c.get("scan_status") == "scanned"])
    companies_with_questionnaire = 0
    if questionnaires:
        from backend.api.questionnaire import QUESTIONNAIRE_SECTIONS
        required_count = len({q["key"] for s in QUESTIONNAIRE_SECTIONS for q in s["questions"]})
        responses_per_company: dict[str, int] = {}
        for q in questionnaires:
            cid = q.get("company_id")
            if cid:
                responses_per_company[cid] = responses_per_company.get(cid, 0) + 1
        companies_with_questionnaire = sum(1 for cnt in responses_per_company.values() if cnt >= required_count)
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
    DELIVERY_DEADLINE_DAYS = 7  # 7 business days (Czech SLA)
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
            # Count actual business days elapsed since payment
            try:
                _paid_dt = datetime.fromisoformat(paid_at.replace("Z", "+00:00"))
                biz_days_elapsed = _count_business_days(_paid_dt, now)
                days_remaining = max(0, DELIVERY_DEADLINE_DAYS - biz_days_elapsed)
            except Exception:
                days_remaining = max(0, DELIVERY_DEADLINE_DAYS - days_since_payment)
            deadline_status = "ok" if days_remaining > 2 else ("warning" if days_remaining > 0 else "overdue")

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

    result = {
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
        "health": {
            "active_customers": active_customers,
            "churn_rate": churn_rate,
            "cancelled_last_30d": cancelled_last_30,
        },
        "funnel": funnel,
        "fulfillment": fulfillment_summary,
        "outreach": outreach,
        "scans": scan_summary,
        "recent_events": recent_events[:30],
    }
    _biz_overview_cache["data"] = result
    _biz_overview_cache["expires"] = _time.time() + _BIZ_CACHE_TTL
    return result


def fmtAmount(amount: int | float) -> str:
    """Format amount for display."""
    return f"{int(amount):,} Kč".replace(",", " ")


# ─────────────────────────────────────────────
# CLIENT DETAIL: Questionnaire Responses + Findings
# ─────────────────────────────────────────────

@router.get("/crm/client/{email}/questionnaire")
async def crm_client_questionnaire(
    email: str,
    user: AuthUser = Depends(require_admin),
):
    """Get questionnaire responses for a client by email."""
    sb = _get_sb()
    # Find client by email
    client = sb.table("clients").select("id,company_id").eq("email", email).execute()
    if not client.data:
        # Try finding company by email
        company = sb.table("companies").select("id").eq("email", email).execute()
        if not company.data:
            return {"responses": [], "summary": {}}
        company_id = company.data[0]["id"]
        # Find client linked to this company
        client = sb.table("clients").select("id,company_id").eq("company_id", company_id).execute()
        if not client.data:
            return {"responses": [], "summary": {}}

    client_id = client.data[0]["id"]

    responses = (
        sb.table("questionnaire_responses")
        .select("*")
        .eq("client_id", client_id)
        .order("submitted_at", desc=False)
        .execute()
    )

    # Group by section
    sections: dict[str, list] = {}
    for r in responses.data:
        section = r.get("section", "unknown")
        if section not in sections:
            sections[section] = []
        sections[section].append({
            "question_key": r.get("question_key"),
            "answer": r.get("answer"),
            "details": r.get("details"),
            "tool_name": r.get("tool_name"),
            "submitted_at": r.get("submitted_at"),
        })

    return {
        "client_id": client_id,
        "total_responses": len(responses.data),
        "sections": sections,
        "responses": responses.data,
    }


@router.get("/crm/client/{email}/findings")
async def crm_client_findings(
    email: str,
    user: AuthUser = Depends(require_admin),
):
    """Get scan findings for a client by email."""
    sb = _get_sb()

    # Find company by email
    company = sb.table("companies").select("id,name").eq("email", email).execute()
    if not company.data:
        # Try via client -> company
        client = sb.table("clients").select("company_id").eq("email", email).execute()
        if not client.data or not client.data[0].get("company_id"):
            return {"findings": [], "total": 0}
        company_id = client.data[0]["company_id"]
        company = sb.table("companies").select("id,name").eq("id", company_id).execute()
        if not company.data:
            return {"findings": [], "total": 0}

    company_id = company.data[0]["id"]
    company_name = company.data[0].get("name", "")

    findings = (
        sb.table("findings")
        .select("*")
        .eq("company_id", company_id)
        .order("created_at", desc=True)
        .execute()
    )

    return {
        "company_id": company_id,
        "company_name": company_name,
        "total": len(findings.data),
        "findings": [
            {
                "id": f.get("id"),
                "name": f.get("name"),
                "category": f.get("category"),
                "risk_level": f.get("risk_level"),
                "ai_act_article": f.get("ai_act_article"),
                "action_required": f.get("action_required"),
                "ai_classification_text": f.get("ai_classification_text"),
                "evidence_html": f.get("evidence_html"),
                "status": f.get("status"),
                "source": f.get("source"),
                "created_at": f.get("created_at"),
            }
            for f in findings.data
        ],
    }


# ══════════════════════════════════════════════════════════════
# Subscriptions management
# ══════════════════════════════════════════════════════════════

@router.get("/crm/subscriptions")
async def get_subscriptions(
    request: Request,
    user: AuthUser = Depends(require_admin),
    _rl=Depends(_check_admin_rate_limit),
):
    """List all subscriptions with company info and overdue calculation."""
    from backend.database import get_supabase
    supabase = get_supabase()

    try:
        subs_res = supabase.table("subscriptions").select("*").order("created_at", desc=True).execute()
        subs = subs_res.data or []
    except Exception as e:
        logger.error(f"subscriptions load: {e}")
        subs = []

    # Get all companies for name/email lookup
    try:
        companies_res = supabase.table("companies").select("id,name,email,ico").execute()
        companies = {c["id"]: c for c in (companies_res.data or [])}
    except Exception:
        companies = {}

    now = datetime.now(timezone.utc)
    result = []

    for s in subs:
        company = companies.get(s.get("company_id", ""), {})

        # Calculate days overdue
        days_overdue = 0
        next_payment = s.get("next_payment_date")
        if next_payment and s.get("status") == "active":
            try:
                npd = datetime.fromisoformat(next_payment.replace("Z", "+00:00"))
                if npd < now:
                    days_overdue = (now - npd).days
            except Exception:
                pass

        # Check if reminder was sent
        reminder_sent = False
        try:
            pr = supabase.table("subscription_payments").select("id").eq(
                "subscription_id", s.get("id", "")
            ).eq("status", "reminder_sent").limit(1).execute()
            reminder_sent = bool(pr.data)
        except Exception:
            pass

        result.append({
            "id": s.get("id", ""),
            "company_id": s.get("company_id", ""),
            "company_name": company.get("name", s.get("company_name", "—")),
            "company_email": company.get("email", s.get("email", "")),
            "plan": s.get("plan", s.get("plan_name", "—")),
            "amount": s.get("amount", s.get("price", 0)),
            "currency": s.get("currency", "CZK"),
            "status": s.get("status", "unknown"),
            "started_at": s.get("created_at", ""),
            "next_payment_date": next_payment,
            "last_payment_at": s.get("last_payment_at"),
            "days_overdue": days_overdue,
            "reminder_sent": reminder_sent,
        })

    return {"subscriptions": result}


@router.post("/crm/subscriptions/{subscription_id}/reminder")
async def send_subscription_reminder(
    subscription_id: str,
    request: Request,
    user: AuthUser = Depends(require_admin),
    _rl=Depends(_check_admin_rate_limit),
):
    """Send a payment reminder for overdue subscription."""
    from backend.database import get_supabase
    supabase = get_supabase()

    # Get subscription
    sub_res = supabase.table("subscriptions").select("*").eq("id", subscription_id).limit(1).execute()
    if not sub_res.data:
        raise HTTPException(status_code=404, detail="Předplatné nenalezeno")

    sub = sub_res.data[0]
    company_id = sub.get("company_id", "")

    # Get company info
    company = {}
    if company_id:
        try:
            cr = supabase.table("companies").select("*").eq("id", company_id).limit(1).execute()
            if cr.data:
                company = cr.data[0]
        except Exception:
            pass

    email = company.get("email", sub.get("email", ""))
    if not email:
        raise HTTPException(status_code=400, detail="Firma nemá email")

    # Record reminder in subscription_payments
    try:
        supabase.table("subscription_payments").insert({
            "company_id": company_id,
            "subscription_id": subscription_id,
            "expected_date": sub.get("next_payment_date"),
            "amount": sub.get("amount", sub.get("price", 0)),
            "currency": sub.get("currency", "CZK"),
            "status": "reminder_sent",
            "reminder_sent_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception as e:
        logger.error(f"subscription_payments insert: {e}")

    # Send reminder email (using existing outbound email system if available)
    company_name = company.get("name", "")
    plan = sub.get("plan", sub.get("plan_name", ""))
    amount = sub.get("amount", sub.get("price", 0))
    currency = sub.get("currency", "CZK")

    logger.info(f"Payment reminder sent: {email} for subscription {subscription_id} ({company_name}, {plan}, {amount} {currency})")

    return {"status": "ok", "email": email, "message": f"Upomínka odeslána na {email}"}


# ── Invoices Admin ──────────────────────────────────────────────

@router.get("/invoices", dependencies=[Depends(require_admin), Depends(_check_admin_rate_limit)])
async def get_admin_invoices(limit: int = 100):
    """Vrátí seznam všech faktur pro admin panel."""
    from backend.database import get_supabase
    supabase = get_supabase()
    result = supabase.table("invoices").select("*").order(
        "created_at", desc=True
    ).limit(limit).execute()
    return {"invoices": result.data or []}


# ── LLM Usage Monitoring ──────────────────────────────────────────────

@router.get("/llm-usage", dependencies=[Depends(require_admin), Depends(_check_admin_rate_limit)])
async def get_llm_usage():
    """Vrátí souhrn spotřeby LLM API (tokeny, náklady, stav klíčů)."""
    from backend.monitoring.llm_usage_tracker import usage_tracker
    return await usage_tracker.get_usage_summary()


@router.post("/llm-usage/check-keys", dependencies=[Depends(require_admin), Depends(_check_admin_rate_limit)])
async def check_llm_keys():
    """Ověří funkčnost API klíčů (Anthropic, Gemini) a vrátí stav."""
    from backend.monitoring.llm_usage_tracker import usage_tracker
    # Force fresh check
    usage_tracker._last_health_check = 0
    return await usage_tracker.check_api_keys()


# ═══════════════════════════════════════════════════════════════
# FACTORY RESET — Kompletní výmaz všech dat (pouze pro testování)
# ═══════════════════════════════════════════════════════════════

@router.post("/crm/factory-reset")
async def crm_factory_reset(
    request: Request,
    user: AuthUser = Depends(require_admin),
):
    """
    Kompletní výmaz VŠECH dat — factory reset.
    Smaže Auth uživatele, všechny tabulky, Storage soubory.
    Ponechá ai_act_chunks (RAG knowledge base).
    Vyžaduje potvrzení: body {"confirm": "VYMAZ"}
    """
    body = await request.json()
    confirm = body.get("confirm", "")
    if confirm != "VYMAZ":
        raise HTTPException(
            status_code=400,
            detail="Pro potvrzení factory resetu odešlete {\"confirm\": \"VYMAZ\"}"
        )

    import httpx
    import psycopg2
    from backend.database import get_supabase

    settings = get_settings()
    results = {"auth": None, "db": None, "storage": None, "errors": []}

    # ── 1. Smazání Auth uživatelů ──
    try:
        sb_url = settings.supabase_url
        sb_key = settings.supabase_service_role_key
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{sb_url}/auth/v1/admin/users?per_page=100",
                headers={"Authorization": f"Bearer {sb_key}", "apikey": sb_key},
            )
            resp.raise_for_status()
            users = resp.json().get("users", [])
            deleted_users = 0
            for u in users:
                uid = u["id"]
                del_resp = await client.delete(
                    f"{sb_url}/auth/v1/admin/users/{uid}",
                    headers={"Authorization": f"Bearer {sb_key}", "apikey": sb_key},
                )
                if del_resp.status_code < 300:
                    deleted_users += 1
            results["auth"] = f"Smazáno {deleted_users}/{len(users)} uživatelů"
    except Exception as e:
        results["auth"] = f"CHYBA: {e}"
        results["errors"].append(f"auth: {e}")

    # ── 2. Výmaz DB tabulek (FK pořadí) ──
    try:
        import os
        db_pass = os.environ.get("SUPABASE_DB_PASSWORD", "")
        sb_url_raw = settings.supabase_url  # https://xxx.supabase.co
        project_ref = sb_url_raw.split("//")[1].split(".")[0]
        db_host = f"db.{project_ref}.supabase.co"

        conn = psycopg2.connect(
            host=db_host, port=5432, dbname="postgres",
            user="postgres", password=db_pass,
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Zjisti existující tabulky
        cur.execute("""SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'""")
        existing = {r[0] for r in cur.fetchall()}

        # FK-ordered deletion — ai_act_chunks záměrně VYNECHÁNO
        layers = [
            ["findings", "questionnaire_responses", "documents", "alerts", "scan_diffs",
             "chat_messages", "company_activities", "data_access_log", "orchestrator_log",
             "mart1n_conversations"],
            ["subscription_payments", "invoices", "orders", "subscriptions", "payments"],
            ["email_events", "email_log", "email_logs", "email_blacklist", "outbound_emails"],
            ["analytics_events", "analytics_daily_summary"],
            ["llm_usage_daily"],
            ["contact_submissions", "report_leads"],
            ["scans", "scan_results", "clients", "widget_configs"],
            ["companies"],
            ["agency_batches"],
        ]
        db_report = []
        for layer in layers:
            for table in layer:
                if table not in existing:
                    continue
                try:
                    cur.execute(f"DELETE FROM {table}")
                    if cur.rowcount > 0:
                        db_report.append(f"{table}: {cur.rowcount}")
                except Exception as e:
                    db_report.append(f"{table}: CHYBA {e}")
                    conn.rollback()
                    conn.autocommit = True

        # Verifikace
        non_empty = []
        for t in sorted(existing):
            if t == "ai_act_chunks":
                continue
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            cnt = cur.fetchone()[0]
            if cnt > 0:
                non_empty.append(f"{t}:{cnt}")
        conn.close()

        results["db"] = {
            "tables": len(existing),
            "deleted": db_report if db_report else "Všechny tabulky již prázdné",
            "verification": "OK" if not non_empty else f"NEPRÁZDNÉ: {non_empty}",
        }
    except Exception as e:
        results["db"] = f"CHYBA: {e}"
        results["errors"].append(f"db: {e}")

    # ── 3. Storage cleanup ──
    try:
        supabase = get_supabase()
        files_resp = supabase.storage.from_("documents").list(path="", options={"limit": 1000})
        if files_resp:
            paths = [f["name"] for f in files_resp]
            if paths:
                supabase.storage.from_("documents").remove(paths)
            results["storage"] = f"Smazáno {len(paths)} souborů"
        else:
            results["storage"] = "Bucket prázdný"
    except Exception as e:
        results["storage"] = f"CHYBA: {e}"
        results["errors"].append(f"storage: {e}")

    success = len(results["errors"]) == 0
    logger.warning(f"[FACTORY RESET] {'OK' if success else 'ERRORS'}: {results}")

    return {
        "status": "ok" if success else "partial",
        "message": "Factory reset dokončen" if success else "Factory reset s chybami",
        "results": results,
    }


# ─────────────────────────────────────────────
# SCAN MONITORING — přehled běžících 24h testů
# ─────────────────────────────────────────────

@router.get("/crm/scan-monitor")
async def admin_scan_monitor(
    user: AuthUser = Depends(require_admin),
    _rl=Depends(_check_admin_rate_limit),
):
    """
    Vrátí kompletní přehled všech skenů — aktivní, probíhající deep scany,
    dokončené i chybové. Pro admin monitoring panel.
    """
    from backend.database import get_supabase
    supabase = get_supabase()

    try:
        # ── 1. Aktivní deep scany (running/pending) ──
        active_deep = supabase.table("scans").select(
            "id, company_id, url_scanned, status, scan_type, "
            "deep_scan_status, deep_scan_started_at, deep_scan_finished_at, "
            "deep_scan_total_findings, geo_countries_scanned, "
            "started_at, finished_at, total_findings, created_at, error_message"
        ).in_("deep_scan_status", ["pending", "running"]).order(
            "created_at", desc=True
        ).limit(50).execute()

        # ── 2. Dokončené deep scany (posledních 365 dní) ──
        thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=365)).isoformat()
        completed_deep = supabase.table("scans").select(
            "id, company_id, url_scanned, status, scan_type, "
            "deep_scan_status, deep_scan_started_at, deep_scan_finished_at, "
            "deep_scan_total_findings, geo_countries_scanned, "
            "started_at, finished_at, total_findings, created_at, error_message"
        ).in_("deep_scan_status", ["done", "error", "cancelled"]).gte(
            "deep_scan_finished_at", thirty_days_ago
        ).order("deep_scan_finished_at", desc=True).limit(100).execute()

        # ── 3. Aktivní quick scany (queued/running) ──
        active_quick = supabase.table("scans").select(
            "id, company_id, url_scanned, status, scan_type, "
            "started_at, total_findings, created_at, error_message"
        ).in_("status", ["queued", "running"]).order(
            "created_at", desc=True
        ).limit(50).execute()

        # ── 4. Doplnit company info ke skenům ──
        all_scans = (active_deep.data or []) + (completed_deep.data or []) + (active_quick.data or [])
        company_ids = list(set(s.get("company_id") for s in all_scans if s.get("company_id")))

        company_map = {}
        if company_ids:
            # Batch fetch companies (max 100 at a time)
            for i in range(0, len(company_ids), 100):
                batch = company_ids[i:i+100]
                companies_res = supabase.table("companies").select(
                    "id, name, email, url"
                ).in_("id", batch).execute()
                for c in (companies_res.data or []):
                    company_map[c["id"]] = c

        def _enrich_scan(scan: dict) -> dict:
            """Přidej company info + vypočítej progress."""
            cid = scan.get("company_id")
            company = company_map.get(cid, {})
            scan["company_name"] = company.get("name", "—")
            scan["company_email"] = company.get("email", "—")
            scan["company_url"] = company.get("url", "—")

            # Odhad progressu deep scanu (6 kol po ~4h = ~24h)
            if scan.get("deep_scan_status") == "running" and scan.get("deep_scan_started_at"):
                try:
                    started = datetime.fromisoformat(scan["deep_scan_started_at"].replace("Z", "+00:00"))
                    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
                    # 24h = 86400s → progress jako procenta
                    progress = min(round((elapsed / 86400) * 100), 99)
                    scan["deep_scan_progress"] = progress
                    scan["elapsed_hours"] = round(elapsed / 3600, 1)

                    # ── Detailní rozpis kol (round schedule) ──
                    ROUND_INTERVAL = 4 * 3600  # 4h
                    DEEP_ROUNDS = 6
                    GEO_ALL = ["cz", "gb", "us", "br", "jp", "za", "au"]
                    COUNTRIES_PER = 4
                    # Nemůžeme znát shuffle pořadí → použijeme fixní rotaci
                    round_schedule = []
                    countries_done = scan.get("geo_countries_scanned") or []
                    for rn in range(DEEP_ROUNDS):
                        round_start = started + timedelta(seconds=rn * ROUND_INTERVAL)
                        round_end = started + timedelta(seconds=(rn + 1) * ROUND_INTERVAL)
                        # Rotující výběr zemí (simulace)
                        start_idx = (rn * COUNTRIES_PER) % len(GEO_ALL)
                        round_countries = []
                        for ci in range(COUNTRIES_PER):
                            idx = (start_idx + ci) % len(GEO_ALL)
                            round_countries.append(GEO_ALL[idx])
                        now_utc = datetime.now(timezone.utc)
                        if now_utc >= round_end:
                            status = "done"
                        elif now_utc >= round_start:
                            status = "running"
                        else:
                            status = "scheduled"
                        round_schedule.append({
                            "round": rn + 1,
                            "status": status,
                            "countries": round_countries,
                            "starts_at": round_start.isoformat(),
                            "ends_at": round_end.isoformat(),
                        })
                    scan["round_schedule"] = round_schedule
                except Exception:
                    scan["deep_scan_progress"] = 0
                    scan["elapsed_hours"] = 0
            elif scan.get("deep_scan_status") == "done":
                scan["deep_scan_progress"] = 100
                if scan.get("deep_scan_started_at") and scan.get("deep_scan_finished_at"):
                    try:
                        started = datetime.fromisoformat(scan["deep_scan_started_at"].replace("Z", "+00:00"))
                        finished = datetime.fromisoformat(scan["deep_scan_finished_at"].replace("Z", "+00:00"))
                        scan["elapsed_hours"] = round((finished - started).total_seconds() / 3600, 1)
                    except Exception:
                        scan["elapsed_hours"] = 0

            return scan

        enriched_active_deep = [_enrich_scan(s) for s in (active_deep.data or [])]
        enriched_completed_deep = [_enrich_scan(s) for s in (completed_deep.data or [])]
        enriched_active_quick = [_enrich_scan(s) for s in (active_quick.data or [])]

        # ── 5. Zjistit, zda byl odeslán email po deep scanu ──
        completed_scan_ids = [s["id"] for s in enriched_completed_deep]
        email_status_map: dict[str, dict] = {}
        if completed_scan_ids:
            # Zkusíme outbound_emails tabulku
            for scan_id in completed_scan_ids:
                try:
                    email_res = supabase.table("outbound_emails").select(
                        "id, email_to, subject, sent_at, opened_at, clicked_at"
                    ).eq("scan_id", scan_id).order("sent_at", desc=True).limit(1).execute()
                    if email_res.data:
                        email_status_map[scan_id] = {
                            "sent": True,
                            "email_to": email_res.data[0].get("email_to"),
                            "sent_at": email_res.data[0].get("sent_at"),
                            "opened_at": email_res.data[0].get("opened_at"),
                            "clicked_at": email_res.data[0].get("clicked_at"),
                        }
                except Exception:
                    pass

        for scan in enriched_completed_deep:
            email_info = email_status_map.get(scan["id"])
            if email_info:
                scan["email_status"] = email_info
            else:
                scan["email_status"] = {"sent": False}

        # ── 6. Statistiky ──
        stats = {
            "active_deep_scans": len(enriched_active_deep),
            "completed_deep_scans_year": len(enriched_completed_deep),
            "active_quick_scans": len(enriched_active_quick),
            "total_deep_done": len([s for s in enriched_completed_deep if s.get("deep_scan_status") == "done"]),
            "total_deep_error": len([s for s in enriched_completed_deep if s.get("deep_scan_status") == "error"]),
            "total_deep_cancelled": len([s for s in enriched_completed_deep if s.get("deep_scan_status") == "cancelled"]),
        }

        return {
            "stats": stats,
            "active_deep": enriched_active_deep,
            "completed_deep": enriched_completed_deep,
            "active_quick": enriched_active_quick,
        }

    except Exception as e:
        logger.error(f"[Admin] Scan monitor error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crm/scan/{scan_id}/cancel")
async def admin_cancel_deep_scan(
    scan_id: str,
    user: AuthUser = Depends(require_admin),
):
    """
    Zruší probíhající deep scan. Nastaví deep_scan_status na 'cancelled'.
    Worker si to přečte při dalším checku a gracefully se zastaví.
    """
    from backend.database import get_supabase
    supabase = get_supabase()

    try:
        # Ověřit, že scan existuje a je running/pending
        scan_res = supabase.table("scans").select(
            "id, deep_scan_status, url_scanned, company_id"
        ).eq("id", scan_id).limit(1).execute()

        if not scan_res.data:
            raise HTTPException(status_code=404, detail="Sken nenalezen")

        scan = scan_res.data[0]
        current_status = scan.get("deep_scan_status")

        if current_status not in ("running", "pending"):
            raise HTTPException(
                status_code=400,
                detail=f"Nelze zrušit — aktuální status: {current_status}. Lze zrušit pouze running/pending."
            )

        # Nastavit status na cancelled
        finished = datetime.now(timezone.utc).isoformat()
        supabase.table("scans").update({
            "deep_scan_status": "cancelled",
            "deep_scan_finished_at": finished,
        }).eq("id", scan_id).execute()

        logger.info(f"[Admin] Deep scan {scan_id} ZRUŠEN adminem ({scan.get('url_scanned')})")

        return {
            "status": "cancelled",
            "scan_id": scan_id,
            "url": scan.get("url_scanned"),
            "previous_status": current_status,
            "message": "Deep scan byl úspěšně zrušen. Worker se zastaví při dalším checku (do ~5 minut).",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] Cancel deep scan error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crm/scan/{scan_id}/findings")
async def admin_scan_findings(
    scan_id: str,
    user: AuthUser = Depends(require_admin),
):
    """Vrátí detailní findings pro konkrétní sken (pro admin rozbalení)."""
    from backend.database import get_supabase
    supabase = get_supabase()

    try:
        findings = supabase.table("findings").select(
            "id, name, category, risk_level, ai_act_article, "
            "action_required, ai_classification_text, source, "
            "confirmed_by_client, created_at"
        ).eq("scan_id", scan_id).order("risk_level").execute()

        deployed = [f for f in (findings.data or []) if f.get("source") != "ai_classified_fp"]
        false_positives = [f for f in (findings.data or []) if f.get("source") == "ai_classified_fp"]

        return {
            "scan_id": scan_id,
            "deployed": deployed,
            "false_positives": false_positives,
            "total_deployed": len(deployed),
            "total_fp": len(false_positives),
        }
    except Exception as e:
        logger.error(f"[Admin] Scan findings error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crm/scan/{scan_id}/resend-report")
async def admin_resend_report(
    scan_id: str,
    request: Request,
    user: AuthUser = Depends(require_admin),
):
    """
    Znovu odešle report email klientovi pro daný sken.
    Body (volitelné): { "email": "custom@email.cz" }
    Pokud email není zadán, použije se email firmy.
    """
    from backend.database import get_supabase
    from backend.outbound.email_engine import send_email
    from backend.outbound.report_email import generate_report_email_html

    supabase = get_supabase()

    try:
        body = {}
        try:
            body = await request.json()
        except Exception:
            pass

        # Načteme sken
        scan_res = supabase.table("scans").select(
            "id, url_scanned, status, company_id, deep_scan_status, "
            "total_findings, deep_scan_total_findings"
        ).eq("id", scan_id).limit(1).execute()

        if not scan_res.data:
            raise HTTPException(status_code=404, detail="Sken nenalezen")

        scan = scan_res.data[0]

        # Načteme firmu
        company_res = supabase.table("companies").select(
            "name, email"
        ).eq("id", scan["company_id"]).limit(1).execute()

        if not company_res.data:
            raise HTTPException(status_code=404, detail="Firma nenalezena")

        company = company_res.data[0]
        email_to = body.get("email") or company.get("email")

        if not email_to:
            raise HTTPException(status_code=400, detail="Žádný email — firma nemá email a nebyl zadán")

        # Načteme findings
        findings_res = supabase.table("findings").select(
            "name, category, risk_level, ai_act_article, action_required, "
            "ai_classification_text, source"
        ).eq("scan_id", scan_id).execute()

        deployed = [f for f in (findings_res.data or []) if f.get("source") != "ai_classified_fp"]

        # Generujeme HTML
        html = generate_report_email_html(
            url=scan["url_scanned"],
            company_name=company.get("name", "Neznámá firma"),
            findings=deployed,
            scan_id=scan_id,
        )

        total = scan.get("deep_scan_total_findings") or scan.get("total_findings") or len(deployed)
        subject = f"AIshield.cz — Výsledky AI Act skenu pro {scan['url_scanned']} ({total} nálezů)"

        result = await send_email(
            to=email_to,
            subject=subject,
            html=html,
            from_email="info@aishield.cz",
            from_name="AIshield.cz",
        )

        logger.info(f"[Admin] Resend report scan={scan_id} to={email_to} by={user.email}")

        return {
            "status": "sent",
            "email_to": email_to,
            "subject": subject,
            "scan_id": scan_id,
            "findings_count": len(deployed),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] Resend report error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crm/scan/{scan_id}/preview-report")
async def admin_preview_report(
    scan_id: str,
    user: AuthUser = Depends(require_admin),
):
    """
    Vrátí HTML náhled reportu, který by se odeslal klientovi.
    Neposílá žádný email — jen renderuje HTML.
    """
    from backend.database import get_supabase
    from backend.outbound.report_email import generate_report_email_html
    from fastapi.responses import HTMLResponse

    supabase = get_supabase()

    try:
        # Načteme sken
        scan_res = supabase.table("scans").select(
            "id, url_scanned, status, company_id, deep_scan_status, "
            "total_findings, deep_scan_total_findings"
        ).eq("id", scan_id).limit(1).execute()

        if not scan_res.data:
            raise HTTPException(status_code=404, detail="Sken nenalezen")

        scan = scan_res.data[0]

        # Načteme firmu
        company_res = supabase.table("companies").select(
            "name, email"
        ).eq("id", scan["company_id"]).limit(1).execute()

        company = company_res.data[0] if company_res.data else {"name": "Neznámá firma", "email": "—"}

        # Načteme findings
        findings_res = supabase.table("findings").select(
            "name, category, risk_level, ai_act_article, action_required, "
            "ai_classification_text, source"
        ).eq("scan_id", scan_id).execute()

        deployed = [f for f in (findings_res.data or []) if f.get("source") != "ai_classified_fp"]

        # Generujeme HTML
        html = generate_report_email_html(
            url=scan["url_scanned"],
            company_name=company.get("name", "Neznámá firma"),
            findings=deployed,
            scan_id=scan_id,
        )

        logger.info(f"[Admin] Preview report scan={scan_id} by={user.email}")

        return HTMLResponse(content=html, status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] Preview report error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crm/scans/stop-all")
async def admin_stop_all_scans(
    request: Request,
    user: AuthUser = Depends(require_admin),
):
    """
    Zastaví VŠECHNY probíhající a čekající 24h deep scany.
    Vyžaduje potvrzení: { "confirm": "STOP" }
    """
    from backend.database import get_supabase
    supabase = get_supabase()

    try:
        body = {}
        try:
            body = await request.json()
        except Exception:
            pass

        if body.get("confirm") != "STOP":
            raise HTTPException(status_code=400, detail="Vyžadováno potvrzení: confirm=STOP")

        # Najít všechny running/pending deep scany
        active = supabase.table("scans").select(
            "id, url_scanned, deep_scan_status, company_id"
        ).in_("deep_scan_status", ["pending", "running"]).execute()

        active_scans = active.data or []

        if not active_scans:
            return {
                "status": "ok",
                "message": "Žádné aktivní deep scany k zastavení.",
                "stopped_count": 0,
                "scans": [],
            }

        finished = datetime.now(timezone.utc).isoformat()
        stopped = []
        errors = []

        for scan in active_scans:
            try:
                supabase.table("scans").update({
                    "deep_scan_status": "cancelled",
                    "deep_scan_finished_at": finished,
                }).eq("id", scan["id"]).execute()

                stopped.append({
                    "id": scan["id"],
                    "url": scan.get("url_scanned", "?"),
                    "previous_status": scan.get("deep_scan_status", "?"),
                })
                logger.info(f"[Admin] STOP-ALL: cancelled scan {scan['id']} ({scan.get('url_scanned')})")
            except Exception as e:
                errors.append(f"{scan['id']}: {e}")
                logger.error(f"[Admin] STOP-ALL: error cancelling {scan['id']}: {e}")

        logger.warning(
            f"[Admin] STOP ALL SCANS by {user.email}: "
            f"{len(stopped)} stopped, {len(errors)} errors"
        )

        return {
            "status": "ok",
            "message": f"Zastaveno {len(stopped)} deep scanů.",
            "stopped_count": len(stopped),
            "scans": stopped,
            "errors": errors if errors else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Admin] Stop all scans error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
