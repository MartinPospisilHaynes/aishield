"""
AIshield.cz — Shoptet Addon: Webhook handler
POST /shoptet/webhook — přijímá události od Shoptet (install, suspend, uninstall).
IP whitelist: 185.184.254.0/24
HMAC SHA-1 verifikace přes Shoptet-Webhook-Signature header.
"""

import ipaddress
import logging
from datetime import datetime, timezone

from backend.database import get_supabase
from backend.shoptet.client import verify_webhook_signature

logger = logging.getLogger("shoptet.webhooks")

# Shoptet webhook IP range
SHOPTET_WEBHOOK_NETWORK = ipaddress.ip_network("185.184.254.0/24")


def is_shoptet_ip(ip: str) -> bool:
    """Ověří, že request přichází z Shoptet IP rozsahu."""
    try:
        return ipaddress.ip_address(ip) in SHOPTET_WEBHOOK_NETWORK
    except ValueError:
        return False


async def handle_webhook(event: str, eshop_id: int, body: bytes, signature: str, client_ip: str) -> dict:
    """
    Zpracuje webhook událost od Shoptet.
    Verifikuje HMAC podpis + IP whitelist.
    
    Podporované události:
    - addon:suspend — deaktivace addonu
    - addon:uninstall — odinstalace
    - addon:prolong — prodloužení licence
    """
    # IP whitelist
    if not is_shoptet_ip(client_ip):
        logger.warning(f"Webhook z neznámé IP: {client_ip}")
        raise PermissionError(f"IP {client_ip} není v Shoptet whitelist")

    # HMAC verifikace
    if not verify_webhook_signature(body, signature):
        logger.warning(f"Neplatný HMAC podpis pro eshop_id={eshop_id}")
        raise PermissionError("Neplatný webhook podpis")

    sb = get_supabase()
    now = datetime.now(timezone.utc).isoformat()

    if event == "addon:uninstall":
        # Soft-delete: mark as uninstalled
        sb.table("shoptet_installations").update({
            "status": "uninstalled",
            "updated_at": now,
        }).eq("eshop_id", eshop_id).execute()
        logger.info(f"Addon odinstalován: eshop_id={eshop_id}")
        return {"status": "uninstalled"}

    elif event == "addon:suspend":
        sb.table("shoptet_installations").update({
            "status": "suspended",
            "updated_at": now,
        }).eq("eshop_id", eshop_id).execute()
        logger.info(f"Addon pozastaven: eshop_id={eshop_id}")
        return {"status": "suspended"}

    elif event == "addon:prolong":
        sb.table("shoptet_installations").update({
            "status": "active",
            "updated_at": now,
        }).eq("eshop_id", eshop_id).execute()
        logger.info(f"Addon prodloužen: eshop_id={eshop_id}")
        return {"status": "prolonged"}

    else:
        logger.info(f"Neznámý webhook event: {event}, eshop_id={eshop_id}")
        return {"status": "ignored", "event": event}
