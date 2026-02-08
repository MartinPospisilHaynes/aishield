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
    environment: str = "development"
    debug: bool = True

    # ── Supabase ──
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str = ""

    # ── Claude API ──
    anthropic_api_key: str = ""

    # ── Stripe ──
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # ── Resend ──
    resend_api_key: str = ""
    email_from: str = "info@aishield.cz"

    class Config:
        env_file = "../../.env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Singleton — načte nastavení jednou a cachuje."""
    return Settings()
