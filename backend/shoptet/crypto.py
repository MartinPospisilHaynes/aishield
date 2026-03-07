"""
AIshield.cz — Shoptet Addon: Šifrování OAuth tokenů
Fernet AES-128 pro access tokeny a citlivé údaje.
Používá SHOPTET_ENCRYPTION_KEY z .env (nebo fallback na CHAT_ENCRYPTION_KEY).
"""

import os
from typing import Optional
from cryptography.fernet import Fernet


def _get_key() -> str:
    """Vrátí šifrovací klíč z env."""
    return os.environ.get("SHOPTET_ENCRYPTION_KEY") or os.environ.get("CHAT_ENCRYPTION_KEY", "")


def encrypt_token(value: str) -> Optional[str]:
    """Šifruje OAuth access token přes Fernet AES-128."""
    key = _get_key()
    if not key or not value:
        return None
    try:
        f = Fernet(key.encode())
        return f.encrypt(value.encode()).decode()
    except Exception:
        return None


def decrypt_token(encrypted: str) -> Optional[str]:
    """Dešifruje OAuth access token z Fernet tokenu."""
    key = _get_key()
    if not key or not encrypted:
        return None
    try:
        f = Fernet(key.encode())
        return f.decrypt(encrypted.encode()).decode()
    except Exception:
        return None


def encrypt_email(value: str) -> Optional[str]:
    """Šifruje kontaktní email e-shopaře."""
    return encrypt_token(value)


def decrypt_email(encrypted: str) -> Optional[str]:
    """Dešifruje kontaktní email."""
    return decrypt_token(encrypted)
