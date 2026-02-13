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

# ── Subscription balíčky (měsíční) ──
SUBSCRIPTION_PLANS = {
    "basic_monthly": {
        "name": "BASIC měsíční",
        "description": "AI Act monitoring + průběžné kontroly webu",
        "price": 999,  # CZK/měsíc
        "cycle": RecurrenceCycle.MONTH,
        "period": 1,
    },
    "pro_monthly": {
        "name": "PRO měsíční",
        "description": "Kompletní AI compliance služba + prioritní podpora",
        "price": 2999,  # CZK/měsíc
        "cycle": RecurrenceCycle.MONTH,
        "period": 1,
    },
    "basic_yearly": {
        "name": "BASIC roční",
        "description": "AI Act monitoring — roční předplatné (2 měsíce zdarma)",
        "price": 9990,  # CZK/rok (10×999)
        "cycle": RecurrenceCycle.ON_DEMAND,
        "period": None,
    },
    "pro_yearly": {
        "name": "PRO roční",
        "description": "Kompletní AI compliance — roční předplatné (2 měsíce zdarma)",
        "price": 29990,  # CZK/rok (10×2999)
        "cycle": RecurrenceCycle.ON_DEMAND,
        "period": None,
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
    plan: str  # "basic_monthly", "pro_monthly", "basic_yearly", "pro_yearly"
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
# SUBSCRIPTIONS (OPAKOVANÉ PLATBY)
# ────────────────────────────────────────────────────────────

@router.post("/subscribe", response_model=CheckoutResponse)
async def create_subscription(req: SubscriptionRequest, user: AuthUser = Depends(get_current_user)):
    """
    Vytvoří subscription (opakované platby) v GoPay.

    Zákazník zaplatí první platbu přes gateway.
    Další platby se strhávají automaticky (ON_DEMAND nebo MONTH).

    Po zaplacení se vytvoří záznam v tabulce 'subscriptions'.
    """
    if req.plan not in SUBSCRIPTION_PLANS:
        raise HTTPException(
            status_code=400,
            detail=f"Neznámý subscription balíček: {req.plan}. "
                   f"Dostupné: {', '.join(SUBSCRIPTION_PLANS.keys())}",
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
