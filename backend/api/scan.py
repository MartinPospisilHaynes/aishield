"""
AIshield.cz — Scan API endpoint (placeholder)
Bude plně implementován v úkolech 6-10.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ScanRequest(BaseModel):
    """Požadavek na skenování webu."""
    url: str


class ScanResponse(BaseModel):
    """Odpověď po spuštění skenu."""
    message: str
    url: str
    status: str


@router.post("/scan", response_model=ScanResponse)
async def scan_website(request: ScanRequest):
    """
    Spustí sken webu — najde AI systémy.
    ⚠️ PLACEHOLDER — plná implementace v úkolech 6-10.
    """
    return ScanResponse(
        message="🛡️ Scan endpoint připraven. Plná implementace přijde v Fázi B.",
        url=request.url,
        status="placeholder",
    )
