"""
AIshield.cz — LinkedIn Publisher
OAuth 2.0 + Posts API v2 (https://api.linkedin.com/rest/posts)

Funkce:
- OAuth 2.0 3-legged flow (authorization code → access token → refresh)
- Publikování text postů (osobní profil i firemní stránka)
- Multi-image carousel posty (PNG slides)
- First-comment s UTM odkazem (obejít -83% penalty za link v těle)
- Stahování metrik přes LinkedIn Marketing API

Bezpečnost:
- Access token šifrován Fernet AES-128 v DB
- Refresh token šifrován Fernet AES-128 v DB
- Žádná LinkedIn member data se neukládají (ToS compliance)
"""

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

import httpx

from backend.config import get_settings
from backend.database import get_supabase

logger = logging.getLogger(__name__)

# ── LinkedIn API konstanty ──
LI_AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
LI_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LI_API_BASE = "https://api.linkedin.com"
LI_POSTS_URL = f"{LI_API_BASE}/rest/posts"
LI_IMAGES_URL = f"{LI_API_BASE}/rest/images"
LI_COMMENTS_URL = f"{LI_API_BASE}/rest/socialActions"

# LinkedIn-Version header — povinný od 2024
LI_VERSION = "202402"

# ── Scopes ──
# Osobní profil: w_member_social, r_liteprofile
# Firemní stránka: w_organization_social, r_organization_social
SCOPES_PERSONAL = "openid profile w_member_social"
SCOPES_COMPANY = "w_organization_social r_organization_social"


# ══════════════════════════════════════════════════════════════════════
# OAUTH 2.0
# ══════════════════════════════════════════════════════════════════════

def get_oauth_url(target: str = "personal") -> str:
    """
    Vygeneruje OAuth 2.0 authorization URL.
    target: "personal" nebo "company"
    """
    settings = get_settings()
    client_id = os.getenv("LINKEDIN_CLIENT_ID", "")
    redirect_uri = f"{settings.api_url}/api/admin/linkedin/oauth/callback"
    scopes = SCOPES_PERSONAL if target == "personal" else SCOPES_COMPANY
    state = f"aishield_{target}_{int(time.time())}"

    return (
        f"{LI_AUTH_URL}"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scopes}"
        f"&state={state}"
    )


async def exchange_code_for_token(code: str) -> dict[str, Any]:
    """
    Výměna authorization code za access + refresh token.
    Vrací: {"access_token": ..., "expires_in": ..., "refresh_token": ...}
    """
    client_id = os.getenv("LINKEDIN_CLIENT_ID", "")
    client_secret = os.getenv("LINKEDIN_CLIENT_SECRET", "")
    settings = get_settings()
    redirect_uri = f"{settings.api_url}/api/admin/linkedin/oauth/callback"

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            LI_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": client_id,
                "client_secret": client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        return resp.json()


async def refresh_access_token(refresh_token: str) -> dict[str, Any]:
    """Obnoví access token pomocí refresh tokenu."""
    client_id = os.getenv("LINKEDIN_CLIENT_ID", "")
    client_secret = os.getenv("LINKEDIN_CLIENT_SECRET", "")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            LI_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        return resp.json()


async def store_tokens(
    target: str, access_token: str, refresh_token: str, expires_in: int
) -> None:
    """
    Uloží šifrované tokeny do Supabase tabulky linkedin_tokens.
    Fernet AES-128 šifrování — PII ochrana.
    """
    from cryptography.fernet import Fernet

    fernet_key = os.getenv("LINKEDIN_FERNET_KEY", "")
    if not fernet_key:
        raise ValueError("LINKEDIN_FERNET_KEY není nastavený v .env")

    f = Fernet(fernet_key.encode())
    enc_access = f.encrypt(access_token.encode()).decode()
    enc_refresh = f.encrypt(refresh_token.encode()).decode()

    sb = get_supabase()
    expires_at = datetime.now(timezone.utc).isoformat()

    # Upsert — vždy jen 1 řádek na target
    sb.table("linkedin_tokens").upsert({
        "target": target,
        "access_token_enc": enc_access,
        "refresh_token_enc": enc_refresh,
        "expires_in": expires_in,
        "updated_at": expires_at,
    }, on_conflict="target").execute()

    logger.info(f"LinkedIn tokeny uloženy pro target={target}")


async def get_access_token(target: str = "personal") -> str:
    """
    Načte a dešifruje access token. Pokud expiroval, automaticky refreshne.
    """
    from cryptography.fernet import Fernet

    fernet_key = os.getenv("LINKEDIN_FERNET_KEY", "")
    if not fernet_key:
        raise ValueError("LINKEDIN_FERNET_KEY není nastavený v .env")

    f = Fernet(fernet_key.encode())
    sb = get_supabase()

    result = sb.table("linkedin_tokens").select("*").eq("target", target).single().execute()
    if not result.data:
        raise ValueError(f"LinkedIn token pro '{target}' neexistuje. Proveďte OAuth autorizaci.")

    row = result.data
    access_token = f.decrypt(row["access_token_enc"].encode()).decode()

    # Kontrola expirace (s 5-minutovou rezervou)
    from datetime import timedelta
    updated = datetime.fromisoformat(row["updated_at"])
    if datetime.now(timezone.utc) > updated + timedelta(seconds=row["expires_in"] - 300):
        logger.info(f"LinkedIn token expiroval pro {target}, refreshuji...")
        refresh_token = f.decrypt(row["refresh_token_enc"].encode()).decode()
        new_tokens = await refresh_access_token(refresh_token)
        await store_tokens(
            target,
            new_tokens["access_token"],
            new_tokens.get("refresh_token", refresh_token),
            new_tokens["expires_in"],
        )
        access_token = new_tokens["access_token"]

    return access_token


# ══════════════════════════════════════════════════════════════════════
# PUBLISHING
# ══════════════════════════════════════════════════════════════════════

def _build_headers(access_token: str) -> dict[str, str]:
    """Standardní hlavičky pro LinkedIn REST API."""
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "LinkedIn-Version": LI_VERSION,
        "X-Restli-Protocol-Version": "2.0.0",
    }


async def get_person_urn(access_token: str) -> str:
    """Získá person URN přihlášeného uživatele."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{LI_API_BASE}/v2/userinfo",
            headers=_build_headers(access_token),
        )
        resp.raise_for_status()
        data = resp.json()
        return f"urn:li:person:{data['sub']}"


async def publish_text_post(
    content: str,
    target: str = "personal",
    author_urn: str | None = None,
) -> dict[str, Any]:
    """
    Publikuje textový post na LinkedIn.

    Args:
        content: Text postu (max 3000 znaků)
        target: "personal" nebo "company"
        author_urn: Volitelný URN autora. Pokud None, načte se automaticky.

    Returns:
        {"post_urn": "urn:li:share:...", "status": "published"}
    """
    access_token = await get_access_token(target)

    if not author_urn:
        if target == "personal":
            author_urn = await get_person_urn(access_token)
        else:
            org_id = os.getenv("LINKEDIN_ORG_ID", "")
            if not org_id:
                raise ValueError("LINKEDIN_ORG_ID není nastavený v .env")
            author_urn = f"urn:li:organization:{org_id}"

    payload = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "visibility": "PUBLIC",
        "commentary": content[:3000],
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            LI_POSTS_URL,
            json=payload,
            headers=_build_headers(access_token),
        )
        resp.raise_for_status()

        # LinkedIn vrací post URN v hlavičce x-restli-id
        post_urn = resp.headers.get("x-restli-id", "")
        logger.info(f"LinkedIn post publikován: {post_urn}")

        return {"post_urn": post_urn, "status": "published"}


async def publish_image_post(
    content: str,
    image_urls: list[str],
    target: str = "personal",
    author_urn: str | None = None,
) -> dict[str, Any]:
    """
    Publikuje post s obrázky (carousel/multi-image).
    max 20 obrázků dle LinkedIn API.

    Flow: 1) Initialize upload → 2) Upload binary → 3) Create post s media
    """
    access_token = await get_access_token(target)

    if not author_urn:
        if target == "personal":
            author_urn = await get_person_urn(access_token)
        else:
            org_id = os.getenv("LINKEDIN_ORG_ID", "")
            author_urn = f"urn:li:organization:{org_id}"

    headers = _build_headers(access_token)
    uploaded_images = []

    async with httpx.AsyncClient(timeout=60) as client:
        for img_url in image_urls[:20]:
            # Krok 1: Initialize upload
            init_payload = {
                "initializeUploadRequest": {
                    "owner": author_urn,
                }
            }
            init_resp = await client.post(
                f"{LI_API_BASE}/rest/images?action=initializeUpload",
                json=init_payload,
                headers=headers,
            )
            init_resp.raise_for_status()
            init_data = init_resp.json()["value"]
            upload_url = init_data["uploadUrl"]
            image_urn = init_data["image"]

            # Krok 2: Stáhnout obrázek a uploadnout na LinkedIn
            img_resp = await client.get(img_url, timeout=30)
            img_resp.raise_for_status()

            upload_headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/octet-stream",
                "LinkedIn-Version": LI_VERSION,
            }
            await client.put(upload_url, content=img_resp.content, headers=upload_headers)
            uploaded_images.append(image_urn)

    # Krok 3: Vytvořit post s obrázky
    media_content = {
        "multiImage": {
            "images": [{"id": img_urn} for img_urn in uploaded_images],
        }
    }

    payload = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "visibility": "PUBLIC",
        "commentary": content[:3000],
        "content": media_content,
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            LI_POSTS_URL,
            json=payload,
            headers=_build_headers(access_token),
        )
        resp.raise_for_status()
        post_urn = resp.headers.get("x-restli-id", "")
        logger.info(f"LinkedIn image post publikován: {post_urn}")
        return {"post_urn": post_urn, "status": "published"}


async def post_first_comment(
    post_urn: str,
    comment_text: str,
    target: str = "personal",
) -> dict[str, Any]:
    """
    Přidá first-comment pod post (s UTM odkazem).
    """
    access_token = await get_access_token(target)

    if target == "personal":
        actor = await get_person_urn(access_token)
    else:
        org_id = os.getenv("LINKEDIN_ORG_ID", "")
        actor = f"urn:li:organization:{org_id}"

    payload = {
        "actor": actor,
        "object": post_urn,
        "message": {
            "text": comment_text[:1250],
        },
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{LI_API_BASE}/rest/socialActions/{post_urn}/comments",
            json=payload,
            headers=_build_headers(access_token),
        )
        resp.raise_for_status()
        comment_urn = resp.headers.get("x-restli-id", "")
        logger.info(f"First-comment přidán: {comment_urn}")
        return {"comment_urn": comment_urn}


# ══════════════════════════════════════════════════════════════════════
# METRICS
# ══════════════════════════════════════════════════════════════════════

async def fetch_post_metrics(post_urn: str, target: str = "personal") -> dict[str, Any]:
    """
    Stáhne metriky postu z LinkedIn (impressions, likes, comments, shares, clicks).
    Pozor: Marketing API vyžaduje r_organization_social scope pro company page metriky.
    """
    access_token = await get_access_token(target)
    headers = _build_headers(access_token)

    async with httpx.AsyncClient(timeout=15) as client:
        # Social actions — likes, comments, shares
        resp = await client.get(
            f"{LI_API_BASE}/rest/socialActions/{post_urn}",
            headers=headers,
        )
        resp.raise_for_status()
        social = resp.json()

    return {
        "likes": social.get("likesSummary", {}).get("totalLikes", 0),
        "comments": social.get("commentsSummary", {}).get("totalFirstLevelComments", 0),
        "shares": social.get("totalShareStatistics", 0),
        # Impressions a clicks vyžadují Organization Statistics API (company page)
        "impressions": 0,
        "clicks": 0,
    }


async def sync_post_metrics(post_id: int) -> None:
    """
    Synchronizuje metriky konkrétního postu z LinkedIn do DB.
    Spouští se přes arq worker (cron).
    """
    sb = get_supabase()
    post = sb.table("linkedin_posts").select("*").eq("id", post_id).single().execute()
    if not post.data or not post.data.get("linkedin_post_urn"):
        return

    urn = post.data["linkedin_post_urn"]
    target = post.data.get("target", "personal")

    try:
        metrics = await fetch_post_metrics(urn, target)
        total = metrics["likes"] + metrics["comments"] + metrics["shares"]
        impressions = metrics.get("impressions", 0)
        engagement_rate = (total / impressions * 100) if impressions > 0 else 0.0

        sb.table("linkedin_post_metrics").insert({
            "post_id": post_id,
            "impressions": impressions,
            "likes": metrics["likes"],
            "comments": metrics["comments"],
            "shares": metrics["shares"],
            "clicks": metrics.get("clicks", 0),
            "engagement_rate": round(engagement_rate, 2),
            "measured_at": datetime.now(timezone.utc).isoformat(),
        }).execute()

        logger.info(f"Metriky synchronizovány pro post #{post_id}: {metrics}")
    except Exception as e:
        logger.error(f"Chyba při syncu metrik postu #{post_id}: {e}")


async def sync_all_recent_metrics() -> int:
    """
    Synchronizuje metriky všech postů publikovaných v posledních 30 dnech.
    Volá se z arq cron jobu (1x denně).
    Vrací počet synchronizovaných postů.
    """
    sb = get_supabase()
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

    posts = sb.table("linkedin_posts").select("id").eq(
        "status", "published"
    ).gte("published_at", cutoff).execute()

    synced = 0
    for post in posts.data or []:
        try:
            await sync_post_metrics(post["id"])
            synced += 1
        except Exception as e:
            logger.error(f"Sync metrik selhal pro post #{post['id']}: {e}")

    return synced
