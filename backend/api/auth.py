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

import logging
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

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
    """
    Supabase JWT secret = supabase_anon_key pro HS256 ověření.
    Supabase podepisuje tokeny pomocí JWT secret z jejich dashboardu.
    Pro ověření na backendu potřebujeme buď:
    - JWT Secret z Supabase dashboardu (Settings → API → JWT Secret)
    - nebo anon key (pro HS256, pokud je to stejný klíč)

    V praxi: Supabase JWT secret je SEPARÁTNÍ od anon key.
    Doporučeno: přidat SUPABASE_JWT_SECRET do .env
    Fallback: dekódujeme bez ověření podpisu + validujeme issuer/exp.
    """
    settings = get_settings()
    # Preferujeme dedikovaný JWT secret
    jwt_secret = getattr(settings, "supabase_jwt_secret", None)
    if jwt_secret:
        return jwt_secret
    # Fallback — anon key NENÍ JWT secret, ale můžeme validovat strukturu
    return ""


def _decode_token(token: str) -> dict:
    """
    Dekóduje a validuje Supabase JWT token.

    Strategie:
    1. Pokud máme JWT secret → ověříme HS256 podpis
    2. Pokud nemáme → dekódujeme bez ověření podpisu,
       ale validujeme issuer, expiration a strukturu
    """
    settings = get_settings()
    jwt_secret = _get_supabase_jwt_secret()

    # Očekávaný issuer = supabase_url + /auth/v1
    expected_issuer = f"{settings.supabase_url}/auth/v1"

    if jwt_secret:
        # Plná validace s ověřením podpisu
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
            logger.warning(f"[Auth] JWT verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Neplatný nebo expirovaný token",
            )
    else:
        # Bez JWT secret — dekódujeme a validujeme strukturu
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

        # Validujeme issuer manuálně
        iss = payload.get("iss", "")
        if not iss.startswith(settings.supabase_url):
            logger.warning(f"[Auth] Invalid issuer: {iss}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Neplatný token — nesprávný issuer",
            )

        # Musí mít sub (user ID) a email
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
