"""
AIshield.cz — Documents API
Endpointy pro generování a stahování compliance dokumentů.
"""

import asyncio
import logging
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.documents.templates import TEMPLATE_NAMES
from backend.documents.pipeline_v3 import (
    generate_compliance_kit,
    generate_single_document,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents")

# Concurrent generation protection — one generation per client at a time
_generation_locks: dict[str, asyncio.Lock] = {}

def _get_client_lock(client_id: str) -> asyncio.Lock:
    if client_id not in _generation_locks:
        _generation_locks[client_id] = asyncio.Lock()
    return _generation_locks[client_id]


# ── Modely ──

class GenerateKitResponse(BaseModel):
    client_id: str
    company_name: str
    documents: list[dict]
    errors: list[str]
    generated_at: str
    summary: dict


class GenerateDocResponse(BaseModel):
    template_key: str
    template_name: str
    filename: str
    download_url: str
    size_bytes: int
    format: str
    generated_at: str


# ── Endpointy ──

@router.get("/templates")
async def list_templates():
    """Seznam dostupných šablon dokumentů."""
    return {
        "templates": [
            {"key": key, "name": name}
            for key, name in TEMPLATE_NAMES.items()
        ],
        "total": len(TEMPLATE_NAMES),
    }


@router.post("/generate/{client_id}", response_model=GenerateKitResponse)
async def generate_kit(client_id: str):
    """
    Vygeneruje kompletní AI Act Compliance Kit (dokumenty).
    Concurrent protection: pouze jedno generování na klienta současně.
    """
    lock = _get_client_lock(client_id)
    if lock.locked():
        logger.warning("[Documents] Generování již probíhá pro client_id=%s — odmítnuto", client_id)
        raise HTTPException(status_code=409, detail="Generování dokumentů pro tohoto klienta již probíhá. Zkuste to za chvíli.")

    async with lock:
        logger.info("[Documents] Generování Compliance Kitu pro client_id=%s", client_id)
        start = time.time()
        try:
            result = await generate_compliance_kit(client_id)
            elapsed = (time.time() - start) * 1000
            doc_count = len(result.to_dict().get("documents", []))
            logger.info(
                "[Documents] Compliance Kit vygenerován: client_id=%s, dokumentů=%d, čas=%.0fms",
                client_id, doc_count, elapsed,
            )
            return result.to_dict()
        except HTTPException:
            raise
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            logger.error(
                "[Documents] Chyba generování Compliance Kitu: client_id=%s, chyba=%s, čas=%.0fms",
                client_id, e, elapsed, exc_info=True,
            )
            raise HTTPException(
                status_code=500,
                detail=f"Chyba při generování Compliance Kitu: {str(e)}",
            )


@router.post("/generate/{client_id}/{template_key}", response_model=GenerateDocResponse)
async def generate_doc(client_id: str, template_key: str):
    """Vygeneruje jeden konkrétní dokument."""
    if template_key not in TEMPLATE_NAMES:
        logger.warning("[Documents] Neznámá šablona: %s (client_id=%s)", template_key, client_id)
        raise HTTPException(
            status_code=400,
            detail=f"Neznámá šablona: {template_key}. Dostupné: {list(TEMPLATE_NAMES.keys())}",
        )

    logger.info("[Documents] Generování dokumentu: client_id=%s, šablona=%s", client_id, template_key)
    start = time.time()
    try:
        doc = await generate_single_document(client_id, template_key)
        elapsed = (time.time() - start) * 1000
        logger.info(
            "[Documents] Dokument vygenerován: client_id=%s, šablona=%s, čas=%.0fms",
            client_id, template_key, elapsed,
        )
        return doc
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        logger.error(
            "[Documents] Chyba generování dokumentu: client_id=%s, šablona=%s, chyba=%s, čas=%.0fms",
            client_id, template_key, e, elapsed, exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Chyba při generování dokumentu: {str(e)}",
        )
