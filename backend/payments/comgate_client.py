"""
AIshield.cz — Comgate platební brána
Integrace přes Comgate Merchant REST API v1.0.
Podporuje: karty, bankovní převody, Apple Pay, Google Pay.
Populární česká platební brána s lokální podporou.
"""

import httpx
import logging
from dataclasses import dataclass
from backend.config import get_settings

logger = logging.getLogger(__name__)

# ── Comgate API URLs ──
COMGATE_API_URL = "https://payments.comgate.cz/v1.0"


@dataclass
class ComgatePayment:
    """Výsledek vytvoření Comgate platby."""
    payment_id: str       # Comgate transId
    gateway_url: str      # URL pro přesměrování zákazníka
    state: str            # "CREATED"


class ComgateClient:
    """
    REST klient pro Comgate API.

    Flow:
    1. POST /create → vytvoří platbu, vrátí transId a redirect URL
    2. Zákazník je přesměrován na Comgate platební stránku
    3. Comgate pošle POST callback na notify_url se stavem
    4. Zákazník se vrátí na return_url

    Konfigurace:
    - COMGATE_MERCHANT_ID: ID obchodníka z Comgate
    - COMGATE_SECRET: Tajný klíč z Comgate
    - COMGATE_IS_PRODUCTION: True pro produkci, False pro test mode

    Stavy plateb:
    - PENDING: Čeká na zaplacení
    - PAID: Zaplaceno
    - CANCELLED: Zrušeno
    - AUTHORIZED: Autorizováno (u karet)
    """

    def __init__(self):
        settings = get_settings()
        self.merchant_id = settings.comgate_merchant_id
        self.secret = settings.comgate_secret
        self.is_production = settings.comgate_is_production
        self.is_configured = bool(self.merchant_id and self.secret)

        if self.is_configured:
            logger.info(
                f"[Comgate] Klient inicializován "
                f"(merchant={self.merchant_id}, "
                f"{'PRODUCTION' if self.is_production else 'TEST'})"
            )
        else:
            logger.warning("[Comgate] Chybí COMGATE_MERCHANT_ID/SECRET — Comgate platby nebudou fungovat")

    async def create_payment(
        self,
        amount: int,
        order_number: str,
        description: str,
        email: str,
        return_url: str,
        notify_url: str,
    ) -> ComgatePayment:
        """
        Vytvoří platbu v Comgate.

        Args:
            amount: Částka v CZK (celé koruny — Comgate chce haléře × 100)
            order_number: Unikátní číslo objednávky (refId)
            description: Popis platby (label)
            email: Email zákazníka
            return_url: URL kam se vrátí zákazník po platbě
            notify_url: URL pro server-to-server callback

        Returns:
            ComgatePayment s transId a redirect URL
        """
        if not self.is_configured:
            raise RuntimeError("Comgate není nakonfigurován (chybí COMGATE_MERCHANT_ID/SECRET)")

        form_data = {
            "merchant": self.merchant_id,
            "secret": self.secret,
            "price": str(amount * 100),  # CZK → haléře
            "curr": "CZK",
            "label": description[:16],   # Comgate label max 16 znaků
            "refId": order_number,
            "email": email,
            "prepareOnly": "true",       # Vrátí transId + URL místo přesměrování
            "country": "CZ",
            "lang": "cs",
            "method": "ALL",             # Všechny dostupné metody
            "url": return_url,           # URL pro návrat zákazníka (Comgate přidá ?id=transId&refId=...)
            "urlc": notify_url,          # Callback URL pro server notifikace
        }

        # V test modu přidáme test=true
        if not self.is_production:
            form_data["test"] = "true"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{COMGATE_API_URL}/create",
                data=form_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()

        # Comgate vrací URL-encoded response: code=0&message=OK&transId=ABC-123&redirect=https://...
        result = dict(x.split("=", 1) for x in response.text.split("&") if "=" in x)

        code = result.get("code", "")
        if code != "0":
            error_msg = result.get("message", "Neznámá chyba")
            logger.error(f"[Comgate] Chyba při vytváření platby: {code} — {error_msg}")
            raise RuntimeError(f"Comgate chyba: {error_msg} (code={code})")

        trans_id = result.get("transId", "")
        redirect_url = result.get("redirect", "")

        logger.info(f"[Comgate] Platba vytvořena: {trans_id} ({amount} CZK)")

        return ComgatePayment(
            payment_id=trans_id,
            gateway_url=redirect_url,
            state="CREATED",
        )

    async def get_payment_status(self, trans_id: str) -> dict:
        """
        Zjistí stav platby v Comgate.

        Args:
            trans_id: ID transakce z Comgate

        Returns:
            Dict s klíči: state, payment_id, order_number, amount, email
        """
        if not self.is_configured:
            raise RuntimeError("Comgate není nakonfigurován")

        form_data = {
            "merchant": self.merchant_id,
            "secret": self.secret,
            "transId": trans_id,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{COMGATE_API_URL}/status",
                data=form_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()

        result = dict(x.split("=", 1) for x in response.text.split("&") if "=" in x)

        code = result.get("code", "")
        if code != "0":
            error_msg = result.get("message", "Neznámá chyba")
            raise RuntimeError(f"Comgate status chyba: {error_msg}")

        # Mapování Comgate stavů na naše interní stavy
        comgate_status = result.get("status", "PENDING")
        state_map = {
            "PAID": "PAID",
            "CANCELLED": "CANCELED",
            "AUTHORIZED": "AUTHORIZED",
            "PENDING": "CREATED",
        }

        return {
            "state": state_map.get(comgate_status, "UNKNOWN"),
            "comgate_status": comgate_status,
            "payment_id": trans_id,
            "order_number": result.get("refId", ""),
            "amount": int(result.get("price", "0")) // 100,  # haléře → CZK
            "email": result.get("email", ""),
        }

    def verify_callback(self, merchant: str, secret: str) -> bool:
        """
        Ověří, že callback pochází opravdu z Comgate.

        V callbacku přijde merchant + secret — porovnáme s naším.
        """
        return merchant == self.merchant_id and secret == self.secret

    def is_paid(self, state: str) -> bool:
        """Kontrola, zda je platba zaplacená."""
        return state in ("PAID", "AUTHORIZED")


# ── Singleton ──
_comgate_client: ComgateClient | None = None


def get_comgate() -> ComgateClient:
    """Vrátí singleton Comgate klienta."""
    global _comgate_client
    if _comgate_client is None:
        _comgate_client = ComgateClient()
    return _comgate_client
