"""
AIshield.cz — Shoptet Addon: API klient
Komunikace se Shoptet REST API — OAuth, eshop info, pages, webhooks.
Docs: https://developers.shoptet.com/, https://api.docs.shoptet.com/
"""

import hashlib
import hmac
import logging
import os
from typing import Optional

import httpx

from backend.shoptet.crypto import encrypt_token, decrypt_token

logger = logging.getLogger("shoptet.client")

SHOPTET_API_BASE = "https://api.myshoptet.com/api"
SHOPTET_OAUTH_URL = "https://api.myshoptet.com/oauth/token"

# Rate limit: max 50 concurrent / IP, max 3 concurrent / token
_REQUEST_TIMEOUT = 10.0


def _get_client_id() -> str:
    return os.environ["SHOPTET_CLIENT_ID"]


def _get_client_secret() -> str:
    return os.environ["SHOPTET_CLIENT_SECRET"]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# OAuth
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def exchange_code_for_token(code: str) -> dict:
    """
    Vyměnit instalační code za OAuth access token.
    Shoptet dává 5 sekund na celý install flow — musí být rychle.
    Vrací {"access_token": "...", "expires_in": ...}
    """
    async with httpx.AsyncClient(timeout=4.0) as client:
        resp = await client.post(
            SHOPTET_OAUTH_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": _get_client_id(),
                "client_secret": _get_client_secret(),
                "code": code,
                "scope": "basic_eshop pages",
            },
        )
        resp.raise_for_status()
        return resp.json()


async def get_api_access_token(oauth_access_token: str) -> str:
    """
    Shoptet 2-úrovňový token systém:
    OAuth token → API Access Token (krátkodobý, pro API volání).
    Endpoint: POST /api/token s Authorization: Bearer <oauth_token>.
    """
    async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
        resp = await client.post(
            f"{SHOPTET_API_BASE}/token",
            headers={"Authorization": f"Bearer {oauth_access_token}"},
        )
        resp.raise_for_status()
        data = resp.json()
        return data["access_token"]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API volání (s API Access Token)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _api_request(
    method: str,
    path: str,
    api_access_token: str,
    json_data: Optional[dict] = None,
) -> dict:
    """Generický Shoptet API request s API Access Token."""
    headers = {
        "Shoptet-Access-Token": api_access_token,
        "Content-Type": "application/vnd.shoptet.v1.0",
    }
    async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
        resp = await client.request(
            method,
            f"{SHOPTET_API_BASE}{path}",
            headers=headers,
            json=json_data,
        )
        resp.raise_for_status()
        return resp.json()


async def get_eshop_info(api_access_token: str) -> dict:
    """GET /api/eshop — základní info o eshopu."""
    data = await _api_request("GET", "/eshop", api_access_token)
    return data.get("data", {}).get("eshop", {})


async def create_page(api_access_token: str, title: str, slug: str, html_content: str) -> dict:
    """
    POST /api/pages — vytvořit compliance stránku.
    Shoptet Pages API vytvoří stránku na eshop.cz/<slug>.
    """
    payload = {
        "data": {
            "title": title,
            "slug": slug,
            "content": html_content,
            "visible": True,
        }
    }
    return await _api_request("POST", "/pages", api_access_token, json_data=payload)


async def update_page(api_access_token: str, page_id: int, html_content: str) -> dict:
    """PATCH /api/pages/<id> — aktualizovat existující stránku."""
    payload = {
        "data": {
            "content": html_content,
        }
    }
    return await _api_request("PATCH", f"/pages/{page_id}", api_access_token, json_data=payload)


async def register_webhooks(api_access_token: str, callback_url: str) -> dict:
    """
    Registruje webhooky pro sledování:
    - addon:suspend / addon:uninstall / addon:prolong
    """
    events = ["addon:suspend", "addon:uninstall", "addon:prolong"]
    payload = {
        "data": [
            {"event": event, "url": callback_url}
            for event in events
        ]
    }
    return await _api_request("POST", "/webhooks", api_access_token, json_data=payload)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Webhook HMAC verifikace
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """
    Shoptet podepíše webhook payloady přes HMAC SHA-1.
    Header: Shoptet-Webhook-Signature
    Secret: SHOPTET_CLIENT_SECRET
    """
    secret = _get_client_secret().encode()
    expected = hmac.new(secret, body, hashlib.sha1).hexdigest()
    return hmac.compare_digest(expected, signature)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Helper: kompletní API volání s DB tokenem
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def get_api_token_for_installation(encrypted_oauth_token: str) -> str:
    """
    Dešifruje OAuth token z DB a získá krátkodobý API access token.
    Používat ve všech business-logic funkcích.
    """
    oauth_token = decrypt_token(encrypted_oauth_token)
    if not oauth_token:
        raise ValueError("Nelze dešifrovat OAuth token instalace")
    return await get_api_access_token(oauth_token)
