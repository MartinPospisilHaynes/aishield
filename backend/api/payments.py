"""
AIshield.cz — Payments API
Endpointy pro GoPay: jednorázové platby, subscriptions (opakované platby), refundace.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime
import uuid
import logging

from backend.config import get_settings
from backend.database import get_supabase
from backend.payments import get_gopay, PaymentState, RecurrenceCycle
from backend.api.auth import AuthUser, get_current_user, get_optional_user

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Cenové balíčky ──
PLANS = {
    "basic": {
        "name": "BASIC",
        "description": "AI Act Compliance Kit — dokumenty ke stažení",
        "price_field": "price_basic",
    },
    "pro": {
        "name": "PRO",
        "description": "Compliance Kit + implementace na klíč + 30 dní podpora",
        "price_field": "price_pro",
    },
    "enterprise": {
        "name": "ENTERPRISE",
        "description": "Komplexní řešení pro větší firmy + 2 roky průběžné péče",
        "price_field": "price_enterprise",
    },
}

# ── Monitoring předplatné (měsíční) ──
SUBSCRIPTION_PLANS = {
    "monitoring": {
        "name": "Monitoring",
        "description": "1× měsíčně automatický sken webu + compliance report",
        "price": 299,  # CZK/měsíc
        "cycle": RecurrenceCycle.MONTH,
        "period": 1,
    },
    "monitoring_plus": {
        "name": "Monitoring Plus",
        "description": "2× měsíčně sken + implementace změn + prioritní podpora",
        "price": 599,  # CZK/měsíc
        "cycle": RecurrenceCycle.MONTH,
        "period": 1,
    },
}


class CheckoutRequest(BaseModel):
    """Request pro vytvoření platby."""
    plan: str  # "basic" nebo "pro"
    email: str


class CheckoutResponse(BaseModel):
    """Response s URL na platební bránu."""
    payment_id: int
    gateway_url: str
    order_number: str


class SubscriptionRequest(BaseModel):
    """Request pro vytvoření subscription."""
    plan: str  # "monitoring" nebo "monitoring_plus"
    email: str


class SubscriptionChargeRequest(BaseModel):
    """Request pro stržení další platby ze subscription."""
    subscription_id: str  # ID subscription v naší DB
    amount: int | None = None  # Částka v CZK, None = stejná jako předchozí


class RefundRequest(BaseModel):
    """Request pro refundaci platby."""
    payment_id: int
    amount: int | None = None  # Částka v CZK, None = plná refundace
    reason: str = ""


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(req: CheckoutRequest, user: AuthUser = Depends(get_current_user)):
    """
    Vytvoří jednorázovou platbu v GoPay a vrátí URL na platební bránu.
    Vyžaduje přihlášení.
    """
    if req.plan not in PLANS:
        raise HTTPException(status_code=400, detail=f"Neznámý balíček: {req.plan}")

    settings = get_settings()
    plan = PLANS[req.plan]
    amount = getattr(settings, plan["price_field"])

    order_number = f"AS-{req.plan.upper()}-{uuid.uuid4().hex[:8].upper()}"

    frontend_url = settings.app_url if settings.environment == "production" else "http://localhost:3000"
    api_url = settings.api_url if settings.environment == "production" else "http://localhost:8000"

    gopay = get_gopay()

    try:
        payment = await gopay.create_payment(
            amount=amount,
            order_number=order_number,
            description=f"AIshield.cz — {plan['name']}: {plan['description']}",
            email=req.email,
            return_url=f"{frontend_url}/platba/stav?id={{paymentId}}",
            notify_url=f"{api_url}/api/payments/webhook",
        )
    except Exception as e:
        logger.error(f"[Payments] Chyba při vytváření platby: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Chyba při komunikaci s GoPay: {str(e)}",
        )

    supabase = get_supabase()
    supabase.table("orders").insert({
        "order_number": order_number,
        "gopay_payment_id": payment.payment_id,
        "plan": req.plan,
        "amount": amount,
        "email": req.email,
        "user_email": req.email,
        "status": payment.state,
        "order_type": "one_time",
        "created_at": datetime.utcnow().isoformat(),
    }).execute()

    return CheckoutResponse(
        payment_id=payment.payment_id,
        gateway_url=payment.gateway_url,
        order_number=order_number,
    )


# ────────────────────────────────────────────────────────────
# MONITORING ELIGIBILITY (kontrola, zda klient může aktivovat monitoring)
# ────────────────────────────────────────────────────────────

async def _check_monitoring_eligibility(email: str) -> dict:
    """
    Zkontroluje, zda klient splňuje podmínky pro aktivaci monitoringu.
    Požadavky:
    1. Zaplacený jednorázový balíček (BASIC/PRO/ENTERPRISE)
    2. Proběhlý sken webu (status=done)
    3. Vyplněný dotazník
    4. Vygenerované dokumenty (alespoň 1)
    5. Nemá už aktivní monitoring subscription
    """
    supabase = get_supabase()

    # 1. Zaplacená jednorázová objednávka
    orders = supabase.table("orders").select("plan, status, order_type").eq(
        "email", email
    ).execute()
    has_paid_order = any(
        o["status"] == "PAID" and o["order_type"] == "one_time"
        for o in (orders.data or [])
    )
    paid_plan = next(
        (o["plan"] for o in (orders.data or [])
         if o["status"] == "PAID" and o["order_type"] == "one_time"),
        None,
    )

    # 2. Firma + sken
    company = None
    company_res = supabase.table("companies").select("id").eq(
        "email", email
    ).limit(1).execute()
    if company_res.data:
        company = company_res.data[0]

    scan_completed = False
    if company:
        scans = supabase.table("scans").select("status").eq(
            "company_id", company["id"]
        ).eq("status", "done").limit(1).execute()
        scan_completed = bool(scans.data)

    # 3. Dotazník
    questionnaire_done = False
    if company:
        client_res = supabase.table("clients").select("id").eq(
            "company_id", company["id"]
        ).limit(1).execute()
        if client_res.data:
            quest_res = supabase.table("questionnaire_responses").select("id").eq(
                "client_id", client_res.data[0]["id"]
            ).limit(1).execute()
            questionnaire_done = bool(quest_res.data)

    # 4. Dokumenty
    documents_generated = False
    if company:
        docs = supabase.table("documents").select("id").eq(
            "company_id", company["id"]
        ).limit(1).execute()
        documents_generated = bool(docs.data)

    # 5. Aktivní subscription
    active_subs = supabase.table("subscriptions").select("id, plan, status").eq(
        "email", email
    ).eq("status", "active").execute()
    has_active_subscription = bool(active_subs.data)
    active_plan = active_subs.data[0]["plan"] if active_subs.data else None

    # Enterprise má 2 roky monitoringu v ceně
    is_enterprise = paid_plan == "enterprise"

    eligible = (
        has_paid_order
        and scan_completed
        and questionnaire_done
        and documents_generated
        and not has_active_subscription
    )

    checks = {
        "has_paid_order": has_paid_order,
        "paid_plan": paid_plan,
        "scan_completed": scan_completed,
        "questionnaire_done": questionnaire_done,
        "documents_generated": documents_generated,
        "has_active_subscription": has_active_subscription,
        "active_plan": active_plan,
        "is_enterprise": is_enterprise,
    }

    if not eligible:
        missing = []
        if not has_paid_order:
            missing.append("Nejdříve je nutné zakoupit balíček (BASIC, PRO nebo ENTERPRISE)")
        if not scan_completed:
            missing.append("Sken webu musí být dokončen")
        if not questionnaire_done:
            missing.append("Dotazník musí být vyplněn")
        if not documents_generated:
            missing.append("Compliance dokumenty musí být vygenerovány")
        if has_active_subscription:
            missing.append(f"Již máte aktivní monitoring ({active_plan})")
        reason = "; ".join(missing)
    else:
        reason = "Splňujete všechny podmínky pro aktivaci monitoringu"

    return {
        "eligible": eligible,
        "reason": reason,
        "checks": checks,
    }


@router.get("/monitoring-eligibility")
async def check_monitoring_eligibility(user: AuthUser = Depends(get_current_user)):
    """
    Zkontroluje, zda přihlášený uživatel splňuje podmínky pro monitoring.
    Vrátí detailed checks pro frontend.
    """
    return await _check_monitoring_eligibility(user.email)


# ────────────────────────────────────────────────────────────
# SUBSCRIPTIONS (OPAKOVANÉ PLATBY)
# ────────────────────────────────────────────────────────────

@router.post("/subscribe", response_model=CheckoutResponse)
async def create_subscription(req: SubscriptionRequest, user: AuthUser = Depends(get_current_user)):
    """
    Vytvoří subscription (opakované platby) v GoPay.

    Zákazník zaplatí první platbu přes gateway.
    Další platby se strhávají automaticky (ON_DEMAND nebo MONTH).

    Po zaplacení se vytvoří záznam v tabulce 'subscriptions'.

    GUARD: Vyžaduje splnění všech podmínek (zaplacený balíček, sken, dotazník, dokumenty).
    """
    if req.plan not in SUBSCRIPTION_PLANS:
        raise HTTPException(
            status_code=400,
            detail=f"Neznámý subscription balíček: {req.plan}. "
                   f"Dostupné: {', '.join(SUBSCRIPTION_PLANS.keys())}",
        )

    # ── Eligibility guard ──
    eligibility = await _check_monitoring_eligibility(req.email)
    if not eligibility["eligible"]:
        raise HTTPException(
            status_code=403,
            detail=f"Monitoring nelze aktivovat: {eligibility['reason']}",
        )

    settings = get_settings()
    plan = SUBSCRIPTION_PLANS[req.plan]

    order_number = f"AS-SUB-{req.plan.upper()}-{uuid.uuid4().hex[:8].upper()}"

    frontend_url = settings.app_url if settings.environment == "production" else "http://localhost:3000"
    api_url = settings.api_url if settings.environment == "production" else "http://localhost:8000"

    gopay = get_gopay()

    try:
        payment = await gopay.create_subscription(
            amount=plan["price"],
            order_number=order_number,
            description=f"AIshield.cz — {plan['name']}: {plan['description']}",
            email=req.email,
            return_url=f"{frontend_url}/platba/stav?id={{paymentId}}&type=subscription",
            notify_url=f"{api_url}/api/payments/webhook",
            cycle=plan["cycle"],
            recurrence_period=plan["period"],
        )
    except Exception as e:
        logger.error(f"[Payments] Chyba při vytváření subscription: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Chyba při komunikaci s GoPay: {str(e)}",
        )

    # Uložit do orders
    supabase = get_supabase()
    supabase.table("orders").insert({
        "order_number": order_number,
        "gopay_payment_id": payment.payment_id,
        "plan": req.plan,
        "amount": plan["price"],
        "email": req.email,
        "user_email": req.email,
        "status": payment.state,
        "order_type": "subscription",
        "created_at": datetime.utcnow().isoformat(),
    }).execute()

    # Vytvořit subscription záznam (aktivuje se po zaplacení v webhooku)
    subscription_id = str(uuid.uuid4())
    supabase.table("subscriptions").insert({
        "id": subscription_id,
        "email": req.email,
        "plan": req.plan,
        "gopay_parent_payment_id": payment.payment_id,
        "amount": plan["price"],
        "cycle": plan["cycle"].value,
        "status": "pending",
        "order_number": order_number,
        "created_at": datetime.utcnow().isoformat(),
    }).execute()

    logger.info(f"[Payments] Subscription vytvořena: {subscription_id} ({req.plan})")

    return CheckoutResponse(
        payment_id=payment.payment_id,
        gateway_url=payment.gateway_url,
        order_number=order_number,
    )


@router.post("/subscribe/charge")
async def charge_subscription(req: SubscriptionChargeRequest, user: AuthUser = Depends(get_current_user)):
    """
    Strhne další platbu z existující subscription.

    Používá se pro ON_DEMAND cyklus — tuto metodu volá náš
    cron job nebo admin manuálně.
    """
    supabase = get_supabase()

    # Najít subscription
    sub = supabase.table("subscriptions").select("*").eq(
        "id", req.subscription_id
    ).single().execute()

    if not sub.data:
        raise HTTPException(status_code=404, detail="Subscription nenalezena")

    if sub.data["status"] != "active":
        raise HTTPException(
            status_code=400,
            detail=f"Subscription není aktivní (status: {sub.data['status']})",
        )

    amount = req.amount or sub.data["amount"]
    order_number = f"AS-REC-{uuid.uuid4().hex[:8].upper()}"

    gopay = get_gopay()

    try:
        payment = await gopay.charge_subscription(
            parent_payment_id=sub.data["gopay_parent_payment_id"],
            amount=amount,
            order_number=order_number,
            description=f"AIshield.cz — opakovaná platba {sub.data['plan']}",
        )
    except Exception as e:
        logger.error(f"[Payments] Chyba při stržení subscription: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Chyba při stržení platby: {str(e)}",
        )

    # Zalogovat platbu
    supabase.table("orders").insert({
        "order_number": order_number,
        "gopay_payment_id": payment.payment_id,
        "plan": sub.data["plan"],
        "amount": amount,
        "email": sub.data["email"],
        "user_email": sub.data["email"],
        "status": payment.state,
        "order_type": "subscription_recurrence",
        "subscription_id": req.subscription_id,
        "created_at": datetime.utcnow().isoformat(),
    }).execute()

    # Aktualizovat subscription
    supabase.table("subscriptions").update({
        "last_charged_at": datetime.utcnow().isoformat(),
        "total_charged": (sub.data.get("total_charged") or 0) + amount,
    }).eq("id", req.subscription_id).execute()

    logger.info(
        f"[Payments] Subscription platba stržena: {req.subscription_id} ({amount} CZK)"
    )

    return {
        "status": "ok",
        "payment_id": payment.payment_id,
        "amount": amount,
        "order_number": order_number,
    }


@router.post("/subscribe/cancel")
async def cancel_subscription(subscription_id: str, user: AuthUser = Depends(get_current_user)):
    """
    Zruší subscription — přestane strhávat platby.
    Aktuální předplacené období zůstává platné.
    """
    supabase = get_supabase()

    sub = supabase.table("subscriptions").select("*").eq(
        "id", subscription_id
    ).single().execute()

    if not sub.data:
        raise HTTPException(status_code=404, detail="Subscription nenalezena")

    if sub.data["status"] in ("cancelled", "expired"):
        raise HTTPException(
            status_code=400,
            detail=f"Subscription je již {sub.data['status']}",
        )

    gopay = get_gopay()

    try:
        await gopay.cancel_subscription(sub.data["gopay_parent_payment_id"])
    except Exception as e:
        logger.error(f"[Payments] Chyba při rušení subscription: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Chyba při rušení subscription: {str(e)}",
        )

    supabase.table("subscriptions").update({
        "status": "cancelled",
        "cancelled_at": datetime.utcnow().isoformat(),
    }).eq("id", subscription_id).execute()

    logger.info(f"[Payments] Subscription zrušena: {subscription_id}")

    return {"status": "cancelled", "subscription_id": subscription_id}


@router.get("/subscribe/{subscription_id}")
async def get_subscription_detail(subscription_id: str, user: AuthUser = Depends(get_current_user)):
    """Vrátí detail subscription včetně GoPay recurrence info."""
    supabase = get_supabase()

    sub = supabase.table("subscriptions").select("*").eq(
        "id", subscription_id
    ).single().execute()

    if not sub.data:
        raise HTTPException(status_code=404, detail="Subscription nenalezena")

    # Volitelně stáhnout stav z GoPay
    gopay = get_gopay()
    recurrence_info = None
    try:
        recurrence_info = await gopay.get_recurrence_info(
            sub.data["gopay_parent_payment_id"]
        )
    except Exception:
        pass  # GoPay nedostupné, vrátíme z DB

    return {
        **sub.data,
        "gopay_recurrence": {
            "cycle": recurrence_info.recurrence_cycle,
            "end_date": recurrence_info.recurrence_date_to,
            "state": recurrence_info.recurrence_state,
        } if recurrence_info else None,
    }


# ────────────────────────────────────────────────────────────
# REFUNDACE
# ────────────────────────────────────────────────────────────

@router.post("/refund")
async def refund_payment(req: RefundRequest, user: AuthUser = Depends(get_current_user)):
    """
    Vrátí peníze zákazníkovi — plná nebo částečná refundace.

    Pro plnou refundaci nevyplňujte amount.
    Pro částečnou zadejte konkrétní částku v CZK.
    """
    gopay = get_gopay()
    supabase = get_supabase()

    # Ověřit, že objednávka existuje
    order = supabase.table("orders").select("*").eq(
        "gopay_payment_id", req.payment_id
    ).single().execute()

    if not order.data:
        raise HTTPException(status_code=404, detail="Objednávka nenalezena")

    if order.data["status"] in ("REFUNDED", "CANCELED"):
        raise HTTPException(
            status_code=400,
            detail=f"Objednávka je již {order.data['status']}",
        )

    try:
        result = await gopay.refund_payment(
            payment_id=req.payment_id,
            amount=req.amount,
        )
    except Exception as e:
        logger.error(f"[Payments] Chyba při refundaci: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Chyba při refundaci: {str(e)}",
        )

    refund_result = result.get("result", "UNKNOWN")

    if refund_result == "FINISHED":
        # Aktualizovat objednávku
        new_status = "REFUNDED" if req.amount is None else "PARTIALLY_REFUNDED"
        supabase.table("orders").update({
            "status": new_status,
            "refunded_at": datetime.utcnow().isoformat(),
            "refund_amount": req.amount or order.data["amount"],
            "refund_reason": req.reason,
        }).eq("gopay_payment_id", req.payment_id).execute()

        logger.info(
            f"[Payments] Refundace úspěšná: payment={req.payment_id}, "
            f"částka={req.amount or order.data['amount']} CZK"
        )
    else:
        logger.warning(
            f"[Payments] Refundace neúspěšná: payment={req.payment_id}, "
            f"result={refund_result}"
        )

    return {
        "status": refund_result,
        "payment_id": req.payment_id,
        "refund_amount": req.amount or order.data["amount"],
        "reason": req.reason,
    }


# ────────────────────────────────────────────────────────────
# STATUS + WEBHOOK
# ────────────────────────────────────────────────────────────

@router.get("/status/{payment_id}")
async def get_payment_status(payment_id: int):
    """
    Zkontroluje stav platby v GoPay.
    Používá se po návratu zákazníka z platební brány.
    """
    gopay = get_gopay()

    try:
        status = await gopay.get_payment_status(payment_id)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Chyba při ověření platby: {str(e)}",
        )

    state = status.get("state", "UNKNOWN")
    is_paid = gopay.is_paid(state)

    supabase = get_supabase()
    supabase.table("orders").update({
        "status": state,
        "paid_at": datetime.utcnow().isoformat() if is_paid else None,
    }).eq("gopay_payment_id", payment_id).execute()

    return {
        "payment_id": payment_id,
        "state": state,
        "is_paid": is_paid,
        "order_number": status.get("order_number", ""),
        "recurrence": status.get("recurrence"),
    }


@router.post("/webhook")
async def gopay_webhook(request: Request):
    """
    GoPay webhook — notifikace o změně stavu platby.
    Zpracovává jednorázové platby i subscriptions.
    """
    body = await request.body()
    params = dict(x.split("=") for x in body.decode().split("&") if "=" in x)
    payment_id = params.get("id")

    if not payment_id:
        raise HTTPException(status_code=400, detail="Chybí id platby")

    gopay = get_gopay()

    try:
        status = await gopay.get_payment_status(int(payment_id))
    except Exception:
        raise HTTPException(status_code=502, detail="Nelze ověřit platbu")

    state = status.get("state", "UNKNOWN")
    is_paid = gopay.is_paid(state)

    supabase = get_supabase()
    update_data = {"status": state}
    if is_paid:
        update_data["paid_at"] = datetime.utcnow().isoformat()

    supabase.table("orders").update(update_data).eq(
        "gopay_payment_id", int(payment_id)
    ).execute()

    # Pokud zaplaceno → aktivovat klienta + subscription
    if is_paid:
        order = supabase.table("orders").select("*").eq(
            "gopay_payment_id", int(payment_id)
        ).single().execute()

        if order.data:
            supabase.table("orders").update({
                "activated": True,
            }).eq("gopay_payment_id", int(payment_id)).execute()

            # Aktivace subscription
            if order.data.get("order_type") == "subscription":
                supabase.table("subscriptions").update({
                    "status": "active",
                    "activated_at": datetime.utcnow().isoformat(),
                    "last_charged_at": datetime.utcnow().isoformat(),
                    "total_charged": order.data.get("amount", 0),
                }).eq("gopay_parent_payment_id", int(payment_id)).execute()

                logger.info(f"[Payments] Subscription aktivována (payment={payment_id})")

    return {"status": "ok"}
