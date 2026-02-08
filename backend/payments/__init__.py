"""
AIshield.cz — GoPay REST API klient
Kompletní integrace s GoPay platební bránou.
Podporuje: karty, bankovní převody, Apple Pay, Google Pay.
"""

import httpx
import base64
from dataclasses import dataclass
from enum import Enum
from backend.config import get_settings

# ── GoPay API URLs ──
GOPAY_SANDBOX_URL = "https://gw.sandbox.gopay.com/api"
GOPAY_PRODUCTION_URL = "https://gw.gopay.com/api"


class PaymentState(str, Enum):
    """Stavy platby v GoPay."""
    CREATED = "CREATED"
    PAYMENT_METHOD_CHOSEN = "PAYMENT_METHOD_CHOSEN"
    PAID = "PAID"
    AUTHORIZED = "AUTHORIZED"
    CANCELED = "CANCELED"
    TIMEOUTED = "TIMEOUTED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"


@dataclass
class GoPayPayment:
    """Výsledek vytvoření platby."""
    payment_id: int
    gateway_url: str
    state: str


class GoPayClient:
    """REST klient pro GoPay API."""

    def __init__(self):
        settings = get_settings()
        self.go_id = settings.gopay_go_id
        self.client_id = settings.gopay_client_id
        self.client_secret = settings.gopay_client_secret
        self.base_url = (
            GOPAY_PRODUCTION_URL if settings.gopay_is_production
            else GOPAY_SANDBOX_URL
        )
        self._access_token: str | None = None

    async def _get_token(self) -> str:
        """Získá OAuth2 access token z GoPay API."""
        if self._access_token:
            return self._access_token

        credentials = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/oauth2/token",
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                },
                data={"scope": "payment-create", "grant_type": "client_credentials"},
            )
            response.raise_for_status()
            data = response.json()
            self._access_token = data["access_token"]
            return self._access_token

    async def create_payment(
        self,
        amount: int,
        order_number: str,
        description: str,
        email: str,
        return_url: str,
        notify_url: str,
    ) -> GoPayPayment:
        """
        Vytvoří platbu v GoPay.

        Args:
            amount: Částka v CZK (celé koruny, GoPay chce v haléřích)
            order_number: Unikátní číslo objednávky
            description: Popis platby
            email: Email zákazníka
            return_url: URL kam se vrátí po platbě
            notify_url: URL pro webhook notifikaci
        """
        token = await self._get_token()

        payment_data = {
            "payer": {
                "default_payment_instrument": "PAYMENT_CARD",
                "allowed_payment_instruments": [
                    "PAYMENT_CARD",
                    "BANK_ACCOUNT",
                    "APPLE_PAY",
                    "GOOGLE_PAY",
                ],
                "contact": {
                    "email": email,
                },
            },
            "amount": amount * 100,  # GoPay chce haléře
            "currency": "CZK",
            "order_number": order_number,
            "order_description": description,
            "callback": {
                "return_url": return_url,
                "notification_url": notify_url,
            },
            "target": {
                "type": "ACCOUNT",
                "goid": int(self.go_id),
            },
            "lang": "CS",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/payments/payment",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=payment_data,
            )
            response.raise_for_status()
            data = response.json()

            return GoPayPayment(
                payment_id=data["id"],
                gateway_url=data["gw_url"],
                state=data["state"],
            )

    async def get_payment_status(self, payment_id: int) -> dict:
        """Zjistí stav platby."""
        token = await self._get_token()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/payments/payment/{payment_id}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
            )
            response.raise_for_status()
            return response.json()

    def is_paid(self, state: str) -> bool:
        """Kontrola, zda je platba zaplacená."""
        return state in (PaymentState.PAID, PaymentState.AUTHORIZED)


# ── Singleton ──
_gopay_client: GoPayClient | None = None


def get_gopay() -> GoPayClient:
    """Vrátí singleton GoPay klienta."""
    global _gopay_client
    if _gopay_client is None:
        _gopay_client = GoPayClient()
    return _gopay_client
