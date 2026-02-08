"""
AIshield.cz — Payments API
Endpointy pro vytváření plateb přes GoPay a zpracování webhook notifikací.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime
import uuid

from backend.config import get_settings
from backend.database import get_supabase
from backend.payments import get_gopay, PaymentState

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


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(req: CheckoutRequest):
    """
    Vytvoří platbu v GoPay a vrátí URL na platební bránu.
    Zákazník je přesměrován na GoPay checkout s Apple Pay, Google Pay,
    kartou nebo bankovním převodem.
    """
    if req.plan not in PLANS:
        raise HTTPException(status_code=400, detail=f"Neznámý balíček: {req.plan}")

    settings = get_settings()
    plan = PLANS[req.plan]
    amount = getattr(settings, plan["price_field"])

    # Unikátní číslo objednávky
    order_number = f"AS-{req.plan.upper()}-{uuid.uuid4().hex[:8].upper()}"

    # Frontend URL pro návrat po platbě
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
        raise HTTPException(
            status_code=502,
            detail=f"Chyba při komunikaci s GoPay: {str(e)}",
        )

    # Uložit objednávku do Supabase
    supabase = get_supabase()
    supabase.table("orders").insert({
        "order_number": order_number,
        "gopay_payment_id": payment.payment_id,
        "plan": req.plan,
        "amount": amount,
        "email": req.email,
        "status": payment.state,
        "created_at": datetime.utcnow().isoformat(),
    }).execute()

    return CheckoutResponse(
        payment_id=payment.payment_id,
        gateway_url=payment.gateway_url,
        order_number=order_number,
    )


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

    # Aktualizovat stav v DB
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
    }


@router.post("/webhook")
async def gopay_webhook(request: Request):
    """
    GoPay webhook — notifikace o změně stavu platby.
    GoPay posílá POST s id platby, my si stáhneme stav sami.
    """
    # GoPay posílá form-encoded: id=<payment_id>
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

    # Aktualizovat objednávku
    supabase = get_supabase()
    update_data = {"status": state}
    if is_paid:
        update_data["paid_at"] = datetime.utcnow().isoformat()

    supabase.table("orders").update(update_data).eq(
        "gopay_payment_id", int(payment_id)
    ).execute()

    # Pokud zaplaceno → aktivovat klienta
    if is_paid:
        order = supabase.table("orders").select("*").eq(
            "gopay_payment_id", int(payment_id)
        ).single().execute()

        if order.data:
            # Nastavit uživatele jako platícího
            supabase.table("orders").update({
                "activated": True,
            }).eq("gopay_payment_id", int(payment_id)).execute()

            # TODO: Spustit pipeline pro generování dokumentů
            # await generate_compliance_kit(order.data["client_id"])

    return {"status": "ok"}
