"""
AIshield.cz — ARES Lookup Service
Automatické vytažení údajů o firmě z Administrativního registru ekonomických subjektů (ARES).

API: https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ico}
Docs: https://ares.gov.cz/swagger-ui/

Extrahuje:
- Obchodní jméno (název firmy / jméno OSVČ)
- Sídlo (textovaAdresa)
- Právní forma (OSVČ / s.r.o. / a.s. / ...)
- CZ-NACE kódy (odvětví)
- DIČ (pokud existuje)
- Datum vzniku
- Jméno a příjmení podnikatele (u OSVČ z RZP)
"""

import logging
import asyncio
from typing import Optional
from dataclasses import dataclass, field
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import json

logger = logging.getLogger(__name__)

ARES_BASE = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest"
ARES_TIMEOUT = 8  # seconds

# Právní formy — hlavní typy
PRAVNI_FORMY = {
    "101": "OSVČ (fyzická osoba podnikající)",
    "111": "Veřejná obchodní společnost (v.o.s.)",
    "112": "Společnost s ručením omezeným (s.r.o.)",
    "121": "Akciová společnost (a.s.)",
    "141": "Obecně prospěšná společnost (o.p.s.)",
    "205": "Družstvo",
    "301": "Státní podnik",
    "325": "Organizační složka státu",
    "331": "Příspěvková organizace",
    "421": "Zahraniční FO",
    "422": "Zahraniční PO",
    "706": "Spolek",
    "736": "Pobočný spolek",
    "751": "Zájmové sdružení PO",
    "801": "Obec",
    "804": "Kraj",
    "906": "Zahraniční pobočka",
}

# CZ-NACE sekce → lidsky čitelné odvětví
NACE_SECTIONS = {
    "A": "Zemědělství, lesnictví a rybářství",
    "B": "Těžba a dobývání",
    "C": "Zpracovatelský průmysl",
    "D": "Výroba a rozvod elektřiny, plynu, tepla",
    "E": "Zásobování vodou, odpady",
    "F": "Stavebnictví",
    "G": "Velkoobchod a maloobchod",
    "H": "Doprava a skladování",
    "I": "Ubytování, stravování a pohostinství",
    "J": "Informační a komunikační činnosti",
    "K": "Peněžnictví a pojišťovnictví",
    "L": "Činnosti v oblasti nemovitostí",
    "M": "Profesní, vědecké a technické činnosti",
    "N": "Administrativní a podpůrné činnosti",
    "O": "Veřejná správa a obrana",
    "P": "Vzdělávání",
    "Q": "Zdravotní a sociální péče",
    "R": "Kulturní, zábavní a rekreační činnosti",
    "S": "Ostatní činnosti",
}


@dataclass
class AresResult:
    """Výsledek ARES lookupu."""
    ico: str = ""
    name: str = ""                    # obchodniJmeno
    address: str = ""                 # textovaAdresa ze sídla
    legal_form: str = ""              # lidsky čitelná právní forma
    legal_form_code: str = ""         # kód právní formy (101, 112, 121...)
    dic: str = ""                     # DIČ (pokud existuje)
    nace_codes: list[str] = field(default_factory=list)  # CZ-NACE kódy
    nace_description: str = ""        # lidsky čitelné odvětví
    date_created: str = ""            # datum vzniku
    person_name: str = ""             # jméno a příjmení (u OSVČ)
    city: str = ""                    # město
    region: str = ""                  # kraj
    found: bool = False               # zda IČO existuje v ARES
    error: str = ""                   # chybová zpráva


def _fetch_json(url: str) -> dict | None:
    """Synchronní HTTP GET → JSON. Vrátí None při chybě."""
    try:
        req = Request(url, headers={"Accept": "application/json"})
        resp = urlopen(req, timeout=ARES_TIMEOUT)
        if resp.status == 200:
            return json.loads(resp.read())
    except HTTPError as e:
        if e.code == 404:
            return None  # IČO neexistuje
        logger.warning(f"[ARES] HTTP {e.code} for {url}")
    except (URLError, json.JSONDecodeError, TimeoutError) as e:
        logger.warning(f"[ARES] Request error: {e}")
    except Exception as e:
        logger.warning(f"[ARES] Unexpected error: {e}")
    return None


def _resolve_nace(codes_2008: list[str] | None, codes_full: list[str] | None) -> tuple[list[str], str]:
    """Převede CZ-NACE kódy na lidsky čitelné odvětví."""
    all_codes = list(set((codes_full or []) + (codes_2008 or [])))
    if not all_codes:
        return [], ""

    # Extrahuj sekce (první písmeno) + plné kódy
    sections = set()
    for code in all_codes:
        if code and code[0].isalpha():
            sections.add(code[0].upper())
        elif code and code[0].isdigit():
            # Mapuj číselný NACE na sekci
            num = int(code[:2]) if len(code) >= 2 else 0
            if 1 <= num <= 3: sections.add("A")
            elif 5 <= num <= 9: sections.add("B")
            elif 10 <= num <= 33: sections.add("C")
            elif 35 <= num <= 35: sections.add("D")
            elif 36 <= num <= 39: sections.add("E")
            elif 41 <= num <= 43: sections.add("F")
            elif 45 <= num <= 47: sections.add("G")
            elif 49 <= num <= 53: sections.add("H")
            elif 55 <= num <= 56: sections.add("I")
            elif 58 <= num <= 63: sections.add("J")
            elif 64 <= num <= 66: sections.add("K")
            elif 68 <= num <= 68: sections.add("L")
            elif 69 <= num <= 75: sections.add("M")
            elif 77 <= num <= 82: sections.add("N")
            elif 84 <= num <= 84: sections.add("O")
            elif 85 <= num <= 85: sections.add("P")
            elif 86 <= num <= 88: sections.add("Q")
            elif 90 <= num <= 93: sections.add("R")
            elif 94 <= num <= 96: sections.add("S")

    descriptions = [NACE_SECTIONS[s] for s in sorted(sections) if s in NACE_SECTIONS]
    return all_codes, "; ".join(descriptions) if descriptions else ""


def lookup_ico(ico: str) -> AresResult:
    """
    Synchronní ARES lookup podle IČO.
    Vrátí AresResult se všemi nalezenými údaji.
    """
    result = AresResult(ico=ico)

    # Validace IČO (8 číslic)
    clean_ico = ico.strip().replace(" ", "")
    if not clean_ico.isdigit() or len(clean_ico) != 8:
        result.error = f"Neplatné IČO: {ico}"
        return result

    # Doplň nuly na začátek
    clean_ico = clean_ico.zfill(8)
    result.ico = clean_ico

    # ── Hlavní endpoint ──
    data = _fetch_json(f"{ARES_BASE}/ekonomicke-subjekty/{clean_ico}")
    if not data:
        result.error = "IČO nenalezeno v ARES"
        return result

    result.found = True
    result.name = data.get("obchodniJmeno", "")
    result.dic = data.get("dic", "")
    result.date_created = data.get("datumVzniku", "")

    # Právní forma
    pf_code = data.get("pravniForma", "")
    result.legal_form_code = pf_code
    result.legal_form = PRAVNI_FORMY.get(pf_code, f"Kód {pf_code}")

    # Sídlo
    sidlo = data.get("sidlo", {})
    result.address = sidlo.get("textovaAdresa", "")
    result.city = sidlo.get("nazevObce", "")
    result.region = sidlo.get("nazevKraje", "")

    # CZ-NACE
    result.nace_codes, result.nace_description = _resolve_nace(
        data.get("czNace2008"), data.get("czNace")
    )

    # ── RZP endpoint (živnostenský rejstřík) — pro jméno OSVČ ──
    if pf_code == "101":  # OSVČ
        rzp = _fetch_json(f"{ARES_BASE}/ekonomicke-subjekty-rzp/{clean_ico}")
        if rzp and rzp.get("zaznamy"):
            zaznam = rzp["zaznamy"][0]
            osoba = zaznam.get("osobaPodnikatel", {})
            jmeno = osoba.get("jmeno", "")
            prijmeni = osoba.get("prijmeni", "")
            if jmeno and prijmeni:
                result.person_name = f"{jmeno} {prijmeni}"

    logger.info(
        f"[ARES] Lookup {clean_ico}: {result.name} | {result.address} | "
        f"forma={result.legal_form} | NACE={result.nace_description[:50]}"
    )

    return result


async def async_lookup_ico(ico: str) -> AresResult:
    """Async wrapper — runs synchronní lookup v thread poolu."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lookup_ico, ico)
