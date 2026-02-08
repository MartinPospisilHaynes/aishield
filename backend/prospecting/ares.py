"""
AIshield.cz — ARES API klient
Hledání firem v Administrativním registru ekonomických subjektů.
Filtruje podle NACE kódů (e-commerce, IT, služby).
"""

import httpx
import asyncio
from dataclasses import dataclass
from typing import Optional

# ARES REST API (nové V3)
ARES_BASE_URL = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest"

# NACE kódy relevantní pro AI Act (firmy používající AI/chatboty)
RELEVANT_NACE = [
    "4791",   # Maloobchod prostřednictvím internetu (e-shopy)
    "4799",   # Ostatní maloobchod mimo prodejny
    "6201",   # Programování
    "6202",   # Poradenství v oblasti IT
    "6209",   # Ostatní činnosti v oblasti IT
    "6311",   # Zpracování dat, hosting
    "6312",   # Webové portály
    "6399",   # Ostatní informační činnosti
    "7311",   # Reklamní agentury
    "7021",   # PR a komunikace
    "6910",   # Právní činnosti
    "6920",   # Účetnictví a audit
    "6511",   # Životní pojištění
    "6512",   # Neživotní pojištění
    "6419",   # Ostatní peněžní zprostředkování (banky)
    "8559",   # Ostatní vzdělávání (e-learning)
]


@dataclass
class AresCompany:
    """Firma nalezená v ARES."""
    ico: str
    name: str
    legal_form: str
    nace: list[str]
    address: str
    region: str


async def search_ares_by_nace(
    nace_code: str,
    region: str = "",
    start: int = 0,
    count: int = 100,
) -> list[AresCompany]:
    """
    Vyhledá firmy v ARES podle NACE kódu.
    Vrátí seznam firem s IČO, názvem a adresou.
    """
    params = {
        "czNace": nace_code,
        "start": start,
        "pocet": min(count, 1000),  # ARES max 1000 na dotaz
        "razeni": "ICO_ASC",
    }
    if region:
        params["obec"] = region

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{ARES_BASE_URL}/ekonomicke-subjekty/vyhledat",
                params=params,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        print(f"[ARES] Chyba pro NACE {nace_code}: {e}")
        return []

    companies = []
    for item in data.get("ekonomickeSubjekty", []):
        ico = item.get("ico", "")
        if not ico:
            continue

        address_parts = []
        sidlo = item.get("sidlo", {})
        if sidlo.get("nazevUlice"):
            address_parts.append(f"{sidlo['nazevUlice']} {sidlo.get('cisloDomovni', '')}")
        if sidlo.get("nazevObce"):
            address_parts.append(sidlo["nazevObce"])
        if sidlo.get("psc"):
            address_parts.append(str(sidlo["psc"]))

        companies.append(AresCompany(
            ico=ico,
            name=item.get("obchodniJmeno", ""),
            legal_form=item.get("pravniForma", {}).get("nazev", ""),
            nace=[nace_code],
            address=", ".join(address_parts),
            region=sidlo.get("nazevObce", ""),
        ))

    return companies


async def search_ares_company(ico: str) -> Optional[AresCompany]:
    """Načte detail jedné firmy podle IČO."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{ARES_BASE_URL}/ekonomicke-subjekty/{ico}",
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            item = response.json()
    except Exception:
        return None

    sidlo = item.get("sidlo", {})
    address_parts = []
    if sidlo.get("nazevUlice"):
        address_parts.append(f"{sidlo['nazevUlice']} {sidlo.get('cisloDomovni', '')}")
    if sidlo.get("nazevObce"):
        address_parts.append(sidlo["nazevObce"])

    return AresCompany(
        ico=item.get("ico", ico),
        name=item.get("obchodniJmeno", ""),
        legal_form=item.get("pravniForma", {}).get("nazev", ""),
        nace=item.get("czNace", []),
        address=", ".join(address_parts),
        region=sidlo.get("nazevObce", ""),
    )


async def batch_search(
    nace_codes: list[str] | None = None,
    max_per_nace: int = 100,
) -> list[AresCompany]:
    """
    Prohledá ARES pro všechny relevantní NACE kódy.
    Deduplikuje podle IČO.
    """
    codes = nace_codes or RELEVANT_NACE
    all_companies: dict[str, AresCompany] = {}

    for code in codes:
        print(f"[ARES] Hledám NACE {code}...")
        companies = await search_ares_by_nace(code, count=max_per_nace)
        for c in companies:
            if c.ico not in all_companies:
                all_companies[c.ico] = c
            else:
                # Přidej NACE kód
                all_companies[c.ico].nace.append(code)

        # Rate limit — ARES nemá rád spam
        await asyncio.sleep(1.0)

    result = list(all_companies.values())
    print(f"[ARES] Celkem nalezeno: {len(result)} unikátních firem")
    return result
