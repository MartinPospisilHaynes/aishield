"""
AIshield.cz — Stripe platební brána
Integrace přes Stripe Checkout Session API.
Podporuje: karty (Visa, Mastercard, Maestro), Apple Pay, Google Pay, bankovní převody.
"""

import stripe
import logging
from dataclasses import dataclass
from backend.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class StripePayment:
    """Výsledek vytvoření Stripe Checkout Session."""
    payment_id: str       # Stripe Checkout Session ID (cs_...)
    gateway_url: str      # URL pro přesměrování zákazníka
    state: str            # "CREATED"


class StripeClient:
    """
    Klient pro Stripe Checkout Session API.

    Flow:
    1. Vytvoří Checkout Session → vrátí URL
    2. Zákazník zaplatí na Stripe stránce
    3. Stripe pošle webhook → ověříme podpis → aktualizujeme stav
    4. Zákazník se vrátí na return_url

    Konfigurace:
    - STRIPE_SECRET_KEY: sk_test_... nebo sk_live_...
    - STRIPE_PUBLISHABLE_KEY: pk_test_... nebo pk_live_...
    - STRIPE_WEBHOOK_SECRET: whsec_...
    """

    def __init__(self):
        settings = get_settings()
        self.secret_key = settings.stripe_secret_key
        self.webhook_secret = settings.stripe_webhook_secret
        self.is_configured = bool(self.secret_key)

        if self.is_configured:
            stripe.api_key = self.secret_key
            logger.info("[Stripe] Klient inicializován")
        else:
            logger.warning("[Stripe] Chybí STRIPE_SECRET_KEY — Stripe platby nebudou fungovat")

    async def create_payment(
        self,
        amount: int,
        order_number: str,
        description: str,
        email: str,
        return_url: str,
        notify_url: str,
    ) -> StripePayment:
        """
        Vytvoří Stripe Checkout Session pro jednorázovou platbu.

        Args:
            amount: Částka v CZK (celé koruny)
            order_number: Unikátní číslo objednávky
            description: Popis platby
            email: Email zákazníka
            return_url: URL kam se vrátí po platbě (přidá ?session_id={CHECKOUT_SESSION_ID})
            notify_url: URL pro webhook notifikaci (nepoužívá se — Stripe webhook se nastavuje v Dashboard)
        """
        if not self.is_configured:
            raise RuntimeError("Stripe není nakonfigurován (chybí STRIPE_SECRET_KEY)")

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "czk",
                    "product_data": {
                        "name": description,
                    },
                    "unit_amount": amount * 100,  # CZK → haléře
                },
                "quantity": 1,
            }],
            mode="payment",
            customer_email=email,
            client_reference_id=order_number,
            success_url=return_url,
            cancel_url=return_url,
            metadata={
                "order_number": order_number,
            },
        )

        logger.info(f"[Stripe] Checkout Session vytvořena: {session.id} ({amount} CZK)")

        return StripePayment(
            payment_id=session.id,
            gateway_url=session.url,
            state="CREATED",
        )

    def verify_webhook(self, payload: bytes, sig_header: str) -> dict:
        """
        Ověří podpis Stripe webhooku a vrátí event data.

        Args:
            payload: Raw body requestu
            sig_header: Hodnota hlavičky 'Stripe-Signature'

        Returns:
            Stripe Event objekt jako dict
        """
        if not self.webhook_secret:
            raise RuntimeError("Chybí STRIPE_WEBHOOK_SECRET")

        event = stripe.Webhook.construct_event(
            payload, sig_header, self.webhook_secret
        )
        return event

    async def get_payment_status(self, session_id: str) -> dict:
        """
        Zjistí stav Stripe Checkout Session.

        Returns:
            Dict s klíči: state, payment_id, order_number, amount
        """
        if not self.is_configured:
            raise RuntimeError("Stripe není nakonfigurován")

        session = stripe.checkout.Session.retrieve(session_id)

        # Mapování Stripe stavů na naše interní stavy
        state_map = {
            "complete": "PAID",
            "open": "CREATED",
            "expired": "TIMEOUTED",
        }

        state = state_map.get(session.status, "UNKNOWN")

        return {
            "state": state,
            "payment_id": session.id,
            "order_number": session.client_reference_id or "",
            "amount": (session.amount_total or 0) // 100,  # haléře → CZK
            "stripe_payment_intent": session.payment_intent,
        }

    def is_paid(self, state: str) -> bool:
        """Kontrola, zda je platba zaplacená."""
        return state in ("PAID", "AUTHORIZED")


# ── Singleton ──
_stripe_client: StripeClient | None = None


def get_stripe() -> StripeClient:
    """Vrátí singleton Stripe klienta."""
    global _stripe_client
    if _stripe_client is None:
        _stripe_client = StripeClient()
    return _stripe_client
