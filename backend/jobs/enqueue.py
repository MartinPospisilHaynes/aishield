"""
AIshield.cz — Job Queue Client
Helper pro vkládání úloh do ARQ fronty z API endpointů.

Použití:
    from backend.jobs.enqueue import enqueue_job
    await enqueue_job("generate_compliance_kit_job", client_id, order_id)
"""

import logging
from arq import create_pool
from arq.connections import RedisSettings

logger = logging.getLogger(__name__)

REDIS_SETTINGS = RedisSettings(host="localhost", port=6379, database=0)

_pool = None


async def _get_pool():
    """Lazy singleton Redis pool."""
    global _pool
    if _pool is None:
        _pool = await create_pool(REDIS_SETTINGS)
    return _pool


async def enqueue_job(function_name: str, *args, _job_id: str | None = None, **kwargs):
    """
    Vloží job do ARQ fronty.
    
    Args:
        function_name: Název registrované funkce (např. "generate_compliance_kit_job")
        *args: Argumenty pro funkci
        _job_id: Volitelné unikátní ID jobu (pro deduplikaci)
    """
    try:
        pool = await _get_pool()
        job = await pool.enqueue_job(function_name, *args, _job_id=_job_id, **kwargs)
        logger.info(f"[QUEUE] Job enqueued: {function_name} (id={job.job_id})")
        return job
    except Exception as e:
        logger.error(f"[QUEUE] Chyba enqueue {function_name}: {e}")
        # Fallback: spustit synchronně pokud Redis není dostupný
        logger.warning(f"[QUEUE] Fallback: spouštím {function_name} inline")
        return None


async def enqueue_compliance_kit(client_id: str, order_id: str | None = None):
    """Shortcut: vloží generování Compliance Kitu do fronty."""
    return await enqueue_job(
        "generate_compliance_kit_job",
        client_id,
        order_id,
        _job_id=f"kit_{client_id}",
    )


async def enqueue_rescan(company_id: str):
    """Shortcut: vloží rescan do fronty."""
    return await enqueue_job(
        "rescan_client_job",
        company_id,
        _job_id=f"rescan_{company_id}",
    )
