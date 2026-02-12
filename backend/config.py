"""
AIshield.cz — Konfigurace aplikace
Načítá environment variables z .env souboru.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Centrální konfigurace — všechny API klíče a nastavení."""

    # ── App ──
    app_name: str = "AIshield.cz"
    app_url: str = "https://aishield.cz"
    api_url: str = "https://api.aishield.cz"
    environment: str = "production"
    debug: bool = False

    # ── Supabase ──
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""  # JWT Secret z Supabase Dashboard → Settings → API

    # ── Claude API ──
    anthropic_api_key: str = ""

    # ── GoPay ──
    gopay_go_id: str = ""
    gopay_client_id: str = ""
    gopay_client_secret: str = ""
    gopay_is_production: bool = False

    # ── Ceny balíčků (CZK) ──
    price_basic: int = 4999
    price_pro: int = 14999

    # ── Resend ──
    resend_api_key: str = ""
    email_from: str = "info@aishield.cz"
    resend_webhook_secret: str = ""

    class Config:
        env_file = "../../.env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Singleton — načte nastavení jednou a cachuje."""
    return Settings()
