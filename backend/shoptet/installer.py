"""
AIshield.cz — Shoptet Addon: Instalační endpoint
GET /shoptet/install?code=<CODE> — Shoptet volá po kliknutí "Instalovat".
KRITICKÉ: Shoptet dává MAX 5 SEKUND na celý flow.
"""

import logging
from datetime import datetime, timezone

from backend.database import get_supabase
from backend.shoptet.client import (
    exchange_code_for_token,
    get_api_access_token,
    get_eshop_info,
    register_webhooks,
)
from backend.shoptet.crypto import encrypt_email, encrypt_token

logger = logging.getLogger("shoptet.installer")

WEBHOOK_CALLBACK_URL = "https://api.aishield.cz/shoptet/webhook"


async def handle_install(code: str) -> dict:
    """
    Instalační flow — musí proběhnout do 5 sekund:
    1. Vyměnit code za OAuth token
    2. Získat API Access Token
    3. Načíst eshop info
    4. Uložit instalaci do DB (s šifrovaným tokenem)
    5. Registrovat webhooky (async — může doběhnout později)
    """
    sb = get_supabase()

    # 1. OAuth token exchange
    token_data = await exchange_code_for_token(code)
    oauth_token = token_data["access_token"]

    # 2. API Access Token
    api_token = await get_api_access_token(oauth_token)

    # 3. Eshop info
    eshop = await get_eshop_info(api_token)
    eshop_id = eshop.get("id")
    eshop_url = eshop.get("url", "")
    eshop_name = eshop.get("name", "")
    contact_email = eshop.get("contactInformation", {}).get("email", "")
    language = eshop.get("language", "cs")

    # 4. Uložit do DB — šifrovat citlivé údaje
    encrypted_token = encrypt_token(oauth_token)
    encrypted_email = encrypt_email(contact_email) if contact_email else None

    now = datetime.now(timezone.utc).isoformat()

    # Upsert — pokud eshop reinstaluje addon
    existing = sb.table("shoptet_installations").select("id").eq(
        "eshop_id", eshop_id,
    ).execute()

    if existing.data:
        # Reinstalace — aktualizovat token
        installation_id = existing.data[0]["id"]
        sb.table("shoptet_installations").update({
            "oauth_access_token": encrypted_token,
            "contact_email": encrypted_email,
            "eshop_url": eshop_url,
            "eshop_name": eshop_name,
            "language": language,
            "status": "active",
            "updated_at": now,
        }).eq("id", installation_id).execute()
        logger.info(f"Shoptet reinstalace: eshop_id={eshop_id}, url={eshop_url}")
    else:
        # Nová instalace
        result = sb.table("shoptet_installations").insert({
            "eshop_id": eshop_id,
            "eshop_url": eshop_url,
            "eshop_name": eshop_name,
            "oauth_access_token": encrypted_token,
            "contact_email": encrypted_email,
            "language": language,
            "status": "active",
            "plan": "basic",
            "installed_at": now,
        }).execute()
        installation_id = result.data[0]["id"]
        logger.info(f"Shoptet nová instalace: eshop_id={eshop_id}, url={eshop_url}")

    # 5. Registrace webhooků — best-effort (nesmí blokovat instalaci)
    try:
        await register_webhooks(api_token, WEBHOOK_CALLBACK_URL)
    except Exception as e:
        logger.warning(f"Webhook registrace selhala (neblokující): {e}")

    return {
        "status": "ok",
        "installation_id": installation_id,
        "eshop_id": eshop_id,
        "eshop_name": eshop_name,
    }
