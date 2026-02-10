"""
AIshield.cz — ARES IČO lookup endpoint
Veřejný endpoint pro předvyplnění registrace z ARES.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.prospecting.ares import search_ares_company

router = APIRouter()


class AresLookupResponse(BaseModel):
    ico: str
    name: str
    legal_form: str
    address: str


@router.get("/ares/{ico}", response_model=AresLookupResponse)
async def ares_lookup(ico: str):
    """
    Vyhledá firmu v ARES podle IČO.
    Používá se pro auto-fill v registračním formuláři.
    """
    # Validace — musí být přesně 8 číslic
    cleaned = ico.strip().replace(" ", "")
    if not cleaned.isdigit() or len(cleaned) != 8:
        raise HTTPException(status_code=400, detail="IČO musí být 8 číslic")

    company = await search_ares_company(cleaned)
    if not company:
        raise HTTPException(status_code=404, detail="Firma nebyla v ARES nalezena")

    return AresLookupResponse(
        ico=company.ico,
        name=company.name,
        legal_form=company.legal_form,
        address=company.address,
    )
