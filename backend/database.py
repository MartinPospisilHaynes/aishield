"""
AIshield.cz — Supabase klient
Singleton pro připojení k databázi.
"""

import logging
from supabase import create_client, Client
from backend.config import get_settings

logger = logging.getLogger(__name__)

_supabase_client: Client | None = None


def get_supabase() -> Client:
    """
    Vrátí Supabase klienta (singleton).
    Používá service_role key — obchází RLS.
    Backend je důvěryhodný, smí zapisovat do všech tabulek.
    """
    global _supabase_client
    if _supabase_client is None:
        settings = get_settings()
        # service_role key obchází RLS — standardní pro backend
        key = settings.supabase_service_role_key or settings.supabase_anon_key
        try:
            _supabase_client = create_client(
                settings.supabase_url,
                key,
            )
            logger.info("Supabase klient inicializován (URL=%s)", settings.supabase_url[:40])
        except Exception as e:
            logger.critical("Nelze inicializovat Supabase klienta: %s", e, exc_info=True)
            raise
    return _supabase_client
