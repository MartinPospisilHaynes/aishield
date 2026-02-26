"""
AIshield.cz — ARES IČO lookup endpoint
Veřejný endpoint pro předvyplnění registrace / objednávky z ARES.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import httpx
import logging

from backend.prospecting.ares import search_ares_company

logger = logging.getLogger(__name__)
router = APIRouter()

ARES_BASE_URL = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest"


class AresLookupResponse(BaseModel):
    ico: str
    name: str
    legal_form: str
    address: str
    street: str = ""
    city: str = ""
    zip: str = ""
    dic: str = ""


@router.get("/ares/{ico}", response_model=AresLookupResponse)
async def ares_lookup(ico: str):
    """
    Vyhledá firmu v ARES podle IČO.
    Vrací rozložené údaje (ulice, město, PSČ, DIČ) pro předvyplnění formulářů.
    """
    cleaned = ico.strip().replace(" ", "")
    if not cleaned.isdigit() or len(cleaned) != 8:
        raise HTTPException(status_code=400, detail="IČO musí být 8 číslic")

    # Přímý ARES dotaz pro kompletní údaje včetně DIČ
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{ARES_BASE_URL}/ekonomicke-subjekty/{cleaned}",
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            item = response.json()
    except Exception as e:
        logger.error(f"[ARES] Chyba pro IČO {cleaned}: {e}")
        raise HTTPException(status_code=404, detail="Firma nebyla v ARES nalezena")

    sidlo = item.get("sidlo", {})
    street_parts = []
    if sidlo.get("nazevUlice"):
        num = sidlo.get("cisloDomovni", "")
        orient = sidlo.get("cisloOrientacni", "")
        if num and orient:
            street_parts.append(f"{sidlo['nazevUlice']} {num}/{orient}")
        elif num:
            street_parts.append(f"{sidlo['nazevUlice']} {num}")
        else:
            street_parts.append(sidlo["nazevUlice"])
    street = " ".join(street_parts)
    city = sidlo.get("nazevObce", "")
    psc = str(sidlo.get("psc", ""))
    if len(psc) == 5:
        psc = f"{psc[:3]} {psc[3:]}"

    address_parts = [p for p in [street, city, psc] if p]

    # DIČ
    dic = ""
    dic_list = item.get("dic", []) if isinstance(item.get("dic"), list) else []
    if dic_list:
        dic = dic_list[0] if isinstance(dic_list[0], str) else ""
    elif isinstance(item.get("dic"), str):
        dic = item["dic"]
    # Některé subjekty mají DIČ jako CZxxxxxxxx
    if not dic and item.get("czNace"):
        dic = f"CZ{cleaned}"  # Výchozí pokus

    return AresLookupResponse(
        ico=item.get("ico", cleaned),
        name=item.get("obchodniJmeno", ""),
        legal_form=item.get("pravniForma", {}).get("nazev", "") if isinstance(item.get("pravniForma"), dict) else str(item.get("pravniForma", "")),
        address=", ".join(address_parts),
        street=street,
        city=city,
        zip=psc,
        dic=dic,
    )
