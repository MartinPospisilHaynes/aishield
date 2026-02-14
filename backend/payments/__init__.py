"""
AIshield.cz — GoPay REST API klient
Kompletní integrace s GoPay platební bránou.
Podporuje: karty, bankovní převody, Apple Pay, Google Pay.
Subscriptions (opakované platby ON_DEMAND) + refundace.
"""

import httpx
import base64
import logging
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
from backend.config import get_settings

logger = logging.getLogger(__name__)

# ── GoPay API URLs ──
GOPAY_SANDBOX_URL = "https://gw.sandbox.gopay.com/api"
GOPAY_PRODUCTION_URL = "https://gate.gopay.cz/api"


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


class RecurrenceCycle(str, Enum):
    """Cykly opakování platby."""
    ON_DEMAND = "ON_DEMAND"       # Na požádání (my rozhodneme kdy)
    WEEK = "WEEK"
    MONTH = "MONTH"
    DAY = "DAY"


class RecurrenceState(str, Enum):
    """Stavy opakované platby."""
    REQUESTED = "REQUESTED"
    STARTED = "STARTED"
    STOPPED = "STOPPED"


@dataclass
class GoPayPayment:
    """Výsledek vytvoření platby."""
    payment_id: int
    gateway_url: str
    state: str


@dataclass
class GoPayRecurrence:
    """Informace o opakované platbě."""
    recurrence_cycle: str
    recurrence_date_to: str
    recurrence_state: str


class GoPayClient:
    """
    REST klient pro GoPay API.

    Podporuje:
    - Jednorázové platby (create_payment)
    - Opakované platby / subscriptions (create_subscription, charge_subscription)
    - Zrušení subscriptions (cancel_subscription)
    - Refundace (refund_payment)
    - Dotaz na stav platby (get_payment_status)
    """

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
        self._token_expires_at: datetime | None = None

    async def _get_token(self) -> str:
        """Získá OAuth2 access token z GoPay API. Cachuje do expirace."""
        if self._access_token and self._token_expires_at and datetime.utcnow() < self._token_expires_at:
            return self._access_token

        credentials = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        async with httpx.AsyncClient(timeout=15.0) as client:
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
            # GoPay tokeny vyprší za 30 minut, refreshneme po 25
            self._token_expires_at = datetime.utcnow() + timedelta(minutes=25)
            return self._access_token

    async def _api_call(self, method: str, path: str, json_data: dict | None = None) -> dict:
        """Pomocná metoda pro GoPay API volání s autorizací."""
        token = await self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method == "GET":
                response = await client.get(f"{self.base_url}{path}", headers=headers)
            elif method == "POST":
                response = await client.post(
                    f"{self.base_url}{path}", headers=headers, json=json_data or {}
                )
            else:
                raise ValueError(f"Neznámá HTTP metoda: {method}")

            if not response.is_success:
                body = response.text
                logger.error(f"[GoPay] API error {response.status_code}: {body}")
                logger.error(f"[GoPay] Request payload: {json_data}")
                response.raise_for_status()
            return response.json()

    # ────────────────────────────────────────────────────────────
    # JEDNORÁZOVÉ PLATBY
    # ────────────────────────────────────────────────────────────

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
        Vytvoří jednorázovou platbu v GoPay.

        Args:
            amount: Částka v CZK (celé koruny — konvertujeme na haléře)
            order_number: Unikátní číslo objednávky
            description: Popis platby
            email: Email zákazníka
            return_url: URL kam se vrátí po platbě
            notify_url: URL pro webhook notifikaci
        """
        payment_data = {
            "payer": {
                "default_payment_instrument": "PAYMENT_CARD",
                "allowed_payment_instruments": [
                    "PAYMENT_CARD",
                    "BANK_ACCOUNT",
                    "APPLE_PAY",
                    "GPAY",
                ],
                "contact": {"email": email},
            },
            "amount": amount * 100,  # CZK → haléře
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

        data = await self._api_call("POST", "/payments/payment", payment_data)
        logger.info(f"[GoPay] Platba vytvořena: {data['id']} ({amount} CZK)")

        return GoPayPayment(
            payment_id=data["id"],
            gateway_url=data["gw_url"],
            state=data["state"],
        )

    # ────────────────────────────────────────────────────────────
    # SUBSCRIPTIONS (OPAKOVANÉ PLATBY)
    # ────────────────────────────────────────────────────────────

    async def create_subscription(
        self,
        amount: int,
        order_number: str,
        description: str,
        email: str,
        return_url: str,
        notify_url: str,
        cycle: RecurrenceCycle = RecurrenceCycle.ON_DEMAND,
        recurrence_period: int | None = None,
        end_date: str | None = None,
    ) -> GoPayPayment:
        """
        Vytvoří opakovanou platbu (subscription) v GoPay.

        Zákazník zaplatí první platbu ručně (přes gateway).
        Další platby se strhávají automaticky pomocí charge_subscription().

        Args:
            amount: Částka první platby v CZK
            order_number: Unikátní číslo objednávky
            description: Popis předplatného
            email: Email zákazníka
            return_url: URL kam se vrátí po platbě
            notify_url: URL pro webhook notifikaci
            cycle: Cyklus opakování (ON_DEMAND = my rozhodneme kdy)
            recurrence_period: Perioda opakování (1 = každý cyklus, jen pro WEEK/MONTH/DAY)
            end_date: Datum ukončení opakování (YYYY-MM-DD), default: za 5 let
        """
        if not end_date:
            end_date = (datetime.utcnow() + timedelta(days=365 * 5)).strftime("%Y-%m-%d")

        recurrence = {
            "recurrence_cycle": cycle.value,
            "recurrence_date_to": end_date,
        }
        if recurrence_period and cycle != RecurrenceCycle.ON_DEMAND:
            recurrence["recurrence_period"] = recurrence_period

        payment_data = {
            "payer": {
                "default_payment_instrument": "PAYMENT_CARD",
                "allowed_payment_instruments": [
                    "PAYMENT_CARD",
                    "BANK_ACCOUNT",
                    "APPLE_PAY",
                    "GPAY",
                ],
                "contact": {"email": email},
            },
            "amount": amount * 100,  # CZK → haléře
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
            "recurrence": recurrence,
            "lang": "CS",
        }

        data = await self._api_call("POST", "/payments/payment", payment_data)
        logger.info(
            f"[GoPay] Subscription vytvořena: {data['id']} "
            f"({amount} CZK, cyklus={cycle.value})"
        )

        return GoPayPayment(
            payment_id=data["id"],
            gateway_url=data["gw_url"],
            state=data["state"],
        )

    async def charge_subscription(
        self,
        parent_payment_id: int,
        amount: int,
        order_number: str,
        description: str,
    ) -> GoPayPayment:
        """
        Strhne další platbu z existující subscription.

        Toto je klíčová metoda pro SaaS model — strhne platbu
        bez nutnosti zákazníkova zásahu (ON_DEMAND model).

        Args:
            parent_payment_id: ID původní (první) platby subscription
            amount: Částka v CZK (může být jiná než první platba)
            order_number: Unikátní číslo nové objednávky
            description: Popis platby
        """
        recurrence_data = {
            "amount": amount * 100,  # CZK → haléře
            "currency": "CZK",
            "order_number": order_number,
            "order_description": description,
        }

        data = await self._api_call(
            "POST",
            f"/payments/payment/{parent_payment_id}/create-recurrence",
            recurrence_data,
        )
        logger.info(
            f"[GoPay] Subscription platba: {data.get('id', 'N/A')} "
            f"(parent={parent_payment_id}, {amount} CZK)"
        )

        return GoPayPayment(
            payment_id=data.get("id", parent_payment_id),
            gateway_url=data.get("gw_url", ""),
            state=data.get("state", "CREATED"),
        )

    async def cancel_subscription(self, payment_id: int) -> dict:
        """
        Zruší opakovanou platbu (subscription).

        Po zrušení se už nebudou strhávat další platby.
        Aktuální předplacené období zůstává platné.

        Args:
            payment_id: ID původní (první) platby subscription
        """
        data = await self._api_call(
            "POST",
            f"/payments/payment/{payment_id}/void-recurrence",
            {},
        )
        logger.info(f"[GoPay] Subscription zrušena: {payment_id}")
        return data

    async def get_recurrence_info(self, payment_id: int) -> GoPayRecurrence | None:
        """Zjistí stav opakované platby."""
        status = await self.get_payment_status(payment_id)
        recurrence = status.get("recurrence")
        if not recurrence:
            return None
        return GoPayRecurrence(
            recurrence_cycle=recurrence.get("recurrence_cycle", ""),
            recurrence_date_to=recurrence.get("recurrence_date_to", ""),
            recurrence_state=recurrence.get("recurrence_state", ""),
        )

    # ────────────────────────────────────────────────────────────
    # REFUNDACE (VRÁCENÍ PENĚZ)
    # ────────────────────────────────────────────────────────────

    async def refund_payment(self, payment_id: int, amount: int | None = None) -> dict:
        """
        Vrátí peníze zákazníkovi (plná nebo částečná refundace).

        Args:
            payment_id: ID platby k refundaci
            amount: Částka k vrácení v CZK (None = plná refundace).
                    Pro částečnou refundaci zadejte konkrétní částku.

        Returns:
            dict s informací o refundaci (result: FINISHED/FAILED)

        Poznámky:
            - GoPay umožňuje i částečnou refundaci
            - Plná refundace: amount = None (stáhne celou částku z payment_id)
            - Částečná: amount < celková částka platby
            - Po refundaci se stav změní na REFUNDED nebo PARTIALLY_REFUNDED
        """
        # Pro plnou refundaci zjistíme celkovou částku
        if amount is None:
            status = await self.get_payment_status(payment_id)
            refund_amount = status["amount"]  # Už v haléřích
        else:
            refund_amount = amount * 100  # CZK → haléře

        data = await self._api_call(
            "POST",
            f"/payments/payment/{payment_id}/refund",
            {"amount": refund_amount},
        )
        logger.info(
            f"[GoPay] Refundace: payment={payment_id}, "
            f"částka={refund_amount // 100} CZK, result={data.get('result', 'N/A')}"
        )
        return data

    # ────────────────────────────────────────────────────────────
    # STATUS + HELPERS
    # ────────────────────────────────────────────────────────────

    async def get_payment_status(self, payment_id: int) -> dict:
        """Zjistí kompletní stav platby včetně subscription info."""
        return await self._api_call("GET", f"/payments/payment/{payment_id}")

    def is_paid(self, state: str) -> bool:
        """Kontrola, zda je platba zaplacená."""
        return state in (PaymentState.PAID, PaymentState.AUTHORIZED)

    def is_refunded(self, state: str) -> bool:
        """Kontrola, zda byla platba refundována."""
        return state in (PaymentState.REFUNDED, PaymentState.PARTIALLY_REFUNDED)

    def is_active(self, state: str) -> bool:
        """Kontrola, zda je platba v aktivním stavu (zaplacena nebo autorizována)."""
        return state in (
            PaymentState.PAID,
            PaymentState.AUTHORIZED,
            PaymentState.PAYMENT_METHOD_CHOSEN,
        )


# ── Singleton ──
_gopay_client: GoPayClient | None = None


def get_gopay() -> GoPayClient:
    """Vrátí singleton GoPay klienta."""
    global _gopay_client
    if _gopay_client is None:
        _gopay_client = GoPayClient()
    return _gopay_client
