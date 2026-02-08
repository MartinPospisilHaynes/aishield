"""
AIshield.cz — Supabase klient
Singleton pro připojení k databázi.
"""

from supabase import create_client, Client
from backend.config import get_settings

_supabase_client: Client | None = None


def get_supabase() -> Client:
    """Vrátí Supabase klienta (singleton)."""
    global _supabase_client
    if _supabase_client is None:
        settings = get_settings()
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_anon_key,
        )
    return _supabase_client
