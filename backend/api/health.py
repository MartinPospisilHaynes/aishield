"""
AIshield.cz — Health Check endpoint
Ověření, že API běží a databáze je dostupná.
"""

from fastapi import APIRouter
from backend.database import get_supabase
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check — ověří:
    1. API běží
    2. Supabase databáze je dostupná
    """
    db_status = "error"
    db_message = ""

    try:
        supabase = get_supabase()
        # Testovací dotaz — počet tabulek
        result = supabase.table("companies").select("id", count="exact").limit(0).execute()
        db_status = "connected"
        db_message = f"companies table accessible"
    except Exception as e:
        db_status = "error"
        db_message = str(e)

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "api": "running",
        "database": db_status,
        "database_message": db_message,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
    }
