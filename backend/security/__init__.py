"""
AIshield.cz — Audit Log
Sledování přístupu k zákaznickým datům (GDPR compliance).
"""

import logging
from datetime import datetime, timezone

from fastapi import Request

from backend.database import get_supabase

logger = logging.getLogger(__name__)


async def log_access(
    *,
    actor_email: str,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    resource_detail: str | None = None,
    actor_role: str = "admin",
    request: Request | None = None,
    metadata: dict | None = None,
) -> None:
    """
    Zaloguj přístup k datům do tabulky data_access_log.

    Akce: view, export, delete, edit
    Resource types: company, questionnaire, scan, finding, user
    """
    ip = "unknown"
    ua = ""

    if request:
        ip = (
            request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or request.headers.get("x-real-ip", "")
            or (request.client.host if request.client else "unknown")
        )
        ua = request.headers.get("user-agent", "")[:500]

    try:
        supabase = get_supabase()
        supabase.table("data_access_log").insert({
            "actor_email": actor_email,
            "actor_role": actor_role,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "resource_detail": resource_detail,
            "ip_address": ip,
            "user_agent": ua,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception as e:
        # Audit log nesmí rozbít hlavní flow
        logger.warning(f"[AuditLog] Chyba při zápisu: {e}")
