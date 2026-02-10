"""
AIshield.cz — Auth Middleware
Ověření Supabase JWT tokenů pro ochranu API endpointů.

Použití v routerech:
    from backend.api.auth import get_current_user, require_admin

    @router.get("/protected")
    async def protected(user: AuthUser = Depends(get_current_user)):
        return {"email": user.email}

    @router.get("/admin-only")
    async def admin_only(user: AuthUser = Depends(require_admin)):
        return {"admin": True}
"""

from __future__ import annotations

import json as _json
import logging
import time
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt, jwk

from backend.config import get_settings

logger = logging.getLogger(__name__)

# ── Security scheme (Authorization: Bearer <token>) ──
_bearer = HTTPBearer(auto_error=False)

# Admin emails — rozšiřte dle potřeby
ADMIN_EMAILS: set[str] = {
    "martin@desperados-design.cz",
    "info@aishield.cz",
    "info@desperados-design.cz",
}

# Test emails — mohou být smazány a znovu registrovány přes admin endpoint
TEST_EMAILS: set[str] = {
    "info@desperados-design.cz",
}


@dataclass
class AuthUser:
    """Ověřený uživatel z JWT tokenu."""
    id: str           # Supabase user UUID
    email: str
    role: str         # "authenticated" | "anon"
    metadata: dict    # user_metadata z JWT


def _get_supabase_jwt_secret() -> str:
    """Get HS256 JWT secret (for legacy tokens / anon/service keys)."""
    settings = get_settings()
    jwt_secret = getattr(settings, "supabase_jwt_secret", None)
    if jwt_secret:
        return jwt_secret
    return ""


# ── JWKS cache for ES256 verification ──
_jwks_cache: dict = {"keys": {}, "fetched_at": 0}
_JWKS_TTL = 3600  # re-fetch every hour


def _fetch_jwks() -> dict[str, dict]:
    """
    Fetch JWKS (JSON Web Key Set) from Supabase Auth.
    Supabase nové projekty (2025+) podepisují access tokeny pomocí ES256.
    Veřejné klíče jsou na /.well-known/jwks.json.
    """
    import urllib.request

    now = time.time()
    if _jwks_cache["keys"] and (now - _jwks_cache["fetched_at"]) < _JWKS_TTL:
        return _jwks_cache["keys"]

    settings = get_settings()
    url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"

    try:
        req = urllib.request.Request(url, headers={
            "apikey": settings.supabase_anon_key,
        })
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = _json.loads(resp.read())

        keys_by_kid: dict[str, dict] = {}
        for k in data.get("keys", []):
            kid = k.get("kid")
            if kid:
                keys_by_kid[kid] = k

        _jwks_cache["keys"] = keys_by_kid
        _jwks_cache["fetched_at"] = now
        logger.info(f"[Auth] JWKS fetched: {len(keys_by_kid)} key(s)")
        return keys_by_kid

    except Exception as e:
        logger.warning(f"[Auth] JWKS fetch failed: {e}")
        return _jwks_cache.get("keys", {})


def _decode_token(token: str) -> dict:
    """
    Dekóduje a validuje Supabase JWT token.

    Podporuje:
    - ES256 (nové Supabase projekty 2025+) — ověření JWKS veřejným klíčem
    - HS256 (starší projekty) — ověření JWT secret
    - Fallback: dekódování bez podpisu s validací issuer/exp
    """
    settings = get_settings()
    expected_issuer = f"{settings.supabase_url}/auth/v1"

    # 1. Peek at token header to determine algorithm
    try:
        headers = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Neplatný token",
        )

    alg = headers.get("alg", "")
    kid = headers.get("kid", "")

    # 2. ES256 — verify with JWKS public key
    if alg == "ES256" and kid:
        jwks = _fetch_jwks()
        key_data = jwks.get(kid)
        if not key_data:
            # Force refresh JWKS — key might have rotated
            _jwks_cache["fetched_at"] = 0
            jwks = _fetch_jwks()
            key_data = jwks.get(kid)

        if key_data:
            try:
                public_key = jwk.construct(key_data, algorithm="ES256")
                payload = jwt.decode(
                    token,
                    public_key,
                    algorithms=["ES256"],
                    audience="authenticated",
                    issuer=expected_issuer,
                )
                return payload
            except JWTError as e:
                logger.warning(f"[Auth] ES256 verification failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Neplatný nebo expirovaný token",
                )
        else:
            logger.warning(f"[Auth] JWKS key not found for kid={kid}")

    # 3. HS256 — verify with JWT secret
    jwt_secret = _get_supabase_jwt_secret()
    if alg == "HS256" and jwt_secret:
        try:
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
                issuer=expected_issuer,
            )
            return payload
        except JWTError as e:
            logger.warning(f"[Auth] HS256 verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Neplatný nebo expirovaný token",
            )

    # 4. Fallback — decode without signature, validate structure
    try:
        payload = jwt.decode(
            token,
            options={
                "verify_signature": False,
                "verify_exp": True,
                "verify_aud": False,
            },
        )
    except JWTError as e:
        logger.warning(f"[Auth] JWT decode failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Neplatný nebo expirovaný token",
        )

    # Validate issuer
    iss = payload.get("iss", "")
    if not iss.startswith(settings.supabase_url):
        logger.warning(f"[Auth] Invalid issuer: {iss}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Neplatný token — nesprávný issuer",
        )

    if not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Neplatný token — chybí user ID",
        )

    return payload


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthUser:
    """
    FastAPI dependency — vrátí ověřeného uživatele.

    Hledá token v:
    1. Authorization: Bearer <token> header
    2. Cookie 'sb-access-token' (fallback pro SSR)
    """
    token: str | None = None

    # 1. Authorization header
    if credentials and credentials.credentials:
        token = credentials.credentials

    # 2. Cookie fallback (Supabase SSR ukládá do cookies)
    if not token:
        # Supabase SSR cookie pattern: sb-<project-ref>-auth-token
        for cookie_name, cookie_value in request.cookies.items():
            if cookie_name.startswith("sb-") and cookie_name.endswith("-auth-token"):
                # Cookie může obsahovat JSON s access_token
                try:
                    import json
                    cookie_data = json.loads(cookie_value)
                    if isinstance(cookie_data, list) and len(cookie_data) > 0:
                        # Supabase SSR ukládá [access_token, refresh_token]
                        token = cookie_data[0] if isinstance(cookie_data[0], str) else None
                    elif isinstance(cookie_data, dict):
                        token = cookie_data.get("access_token")
                except (json.JSONDecodeError, TypeError):
                    # Cookie může být přímo token string
                    token = cookie_value

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Přihlášení je vyžadováno",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = _decode_token(token)

    return AuthUser(
        id=payload.get("sub", ""),
        email=payload.get("email", ""),
        role=payload.get("role", "anon"),
        metadata=payload.get("user_metadata", {}),
    )


async def get_optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthUser | None:
    """
    Volitelná auth — nehodí 401, ale vrátí None pokud token chybí.
    Užitečné pro endpointy kde přihlášení je bonus (např. sken).
    """
    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None


async def require_admin(
    user: AuthUser = Depends(get_current_user),
) -> AuthUser:
    """
    Vyžaduje admin roli. Kontroluje email proti ADMIN_EMAILS.
    """
    if user.email not in ADMIN_EMAILS:
        logger.warning(f"[Auth] Non-admin access attempt by {user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Přístup pouze pro administrátory",
        )
    return user
