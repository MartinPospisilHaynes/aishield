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

    # ── Stripe ──
    stripe_secret_key: str = ""          # sk_test_... nebo sk_live_...
    stripe_publishable_key: str = ""     # pk_test_... nebo pk_live_...
    stripe_webhook_secret: str = ""      # whsec_...

    # ── Comgate ──
    comgate_merchant_id: str = ""        # ID obchodníka z Comgate
    comgate_secret: str = ""             # Tajný klíč z Comgate
    comgate_is_production: bool = False  # True = produkce, False = test

    # ── Výchozí platební brána ──
    default_payment_gateway: str = "gopay"  # gopay | stripe | comgate

    # ── Ceny balíčků (CZK) ──
    price_basic: int = 4999
    price_pro: int = 14999
    price_enterprise: int = 39999
    price_coffee: int = 50

    # ── Resend ──
    resend_api_key: str = ""
    email_from: str = "info@aishield.cz"
    resend_webhook_secret: str = ""

    # ── Admin ──
    admin_password: str = ""  # Admin heslo pro CRM login (nastavte v .env jako ADMIN_PASSWORD)

    # ── FIO Banka API (pro automatické párování plateb) ──
    fio_api_token: str = ""  # Token z internetového bankovnictví FIO → Nastavení → API

    # ── Data Security ──
    data_export_key: str = ""  # Fernet klíč pro šifrovaný export (vygeneruj: python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')

    class Config:
        env_file = "../../.env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Singleton — načte nastavení jednou a cachuje."""
    return Settings()
