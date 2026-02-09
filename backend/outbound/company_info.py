"""
AIshield.cz — Company Info Extractor
Vytáhne informace o firmě z:
1. ARES (Administrativní registr ekonomických subjektů) — IČO, jméno, adresa, právní forma
2. Webové stránky firmy — kontaktní jméno, telefon, pozice
3. Justice.cz — jednatel/statutár (pro s.r.o./a.s.)
"""

import re
import httpx
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CompanyInfo:
    """Informace o firmě z veřejných zdrojů."""
    # Z ARES
    ico: str = ""
    company_name: str = ""
    legal_form: str = ""          # "OSVČ", "s.r.o.", "a.s.", ...
    legal_form_code: str = ""     # "101", "112", "121", ...
    address: str = ""
    city: str = ""
    nace: str = ""                # Odvětví

    # Z webu / registrů
    contact_person: str = ""      # Jméno kontaktní osoby
    contact_role: str = ""        # "jednatel", "majitel", "CEO", ...
    contact_email: str = ""
    contact_phone: str = ""

    # Metadata
    source: str = ""              # Odkud jsme info získali


# ── Právní formy (kód → lidský název) ──
LEGAL_FORMS = {
    "101": "OSVČ",
    "111": "v.o.s.",
    "112": "s.r.o.",
    "121": "a.s.",
    "141": "o.p.s.",
    "205": "družstvo",
    "301": "státní podnik",
    "325": "organizační složka státu",
    "331": "příspěvková organizace",
    "701": "spolek",
    "706": "ústav",
    "736": "nadace",
}


async def lookup_ares(ico: str) -> CompanyInfo:
    """
    Vyhledá firmu v ARES podle IČO.
    Vrátí CompanyInfo s údaji.
    """
    info = CompanyInfo(ico=ico, source="ares")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            url = f"https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/{ico}"
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

            info.company_name = data.get("obchodniJmeno", "")
            info.legal_form_code = data.get("pravniForma", "")
            info.legal_form = LEGAL_FORMS.get(info.legal_form_code, "")

            # Adresa
            sidlo = data.get("sidlo", {})
            info.address = sidlo.get("textovaAdresa", "")
            info.city = sidlo.get("nazevObce", "")

            # NACE odvětví
            nace_list = data.get("czNace", [])
            info.nace = ", ".join(nace_list) if nace_list else ""

            # Pro OSVČ: obchodní jméno = jméno osoby
            if info.legal_form_code == "101":
                info.contact_person = info.company_name
                info.contact_role = "OSVČ / živnostník"

            logger.info(f"ARES lookup OK: {info.company_name} ({info.legal_form})")

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.warning(f"ARES: IČO {ico} nenalezeno")
        else:
            logger.error(f"ARES HTTP error: {e}")
    except Exception as e:
        logger.error(f"ARES lookup failed: {e}")

    return info


async def lookup_ares_by_name(company_name: str) -> CompanyInfo:
    """
    Vyhledá firmu v ARES podle názvu.
    Vrátí první nejvhodnější výsledek.
    """
    info = CompanyInfo(source="ares_search")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            url = "https://ares.gov.cz/ekonomicke-subjekty-v-be/rest/ekonomicke-subjekty/vyhledat"
            params = {"obchodniJmeno": company_name, "pocet": 3}
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

            # Vezmeme první aktivní výsledek
            subjects = data.get("ekonomickeSubjekty", [])
            if subjects:
                first = subjects[0]
                info.ico = first.get("ico", "")
                info.company_name = first.get("obchodniJmeno", "")
                info.legal_form_code = first.get("pravniForma", "")
                info.legal_form = LEGAL_FORMS.get(info.legal_form_code, "")

                sidlo = first.get("sidlo", {})
                info.address = sidlo.get("textovaAdresa", "")
                info.city = sidlo.get("nazevObce", "")

                if info.legal_form_code == "101":
                    info.contact_person = info.company_name
                    info.contact_role = "OSVČ / živnostník"

                logger.info(f"ARES search OK: {info.company_name} (IČO: {info.ico})")

    except Exception as e:
        logger.error(f"ARES search failed: {e}")

    return info


def extract_ico_from_html(html: str) -> str | None:
    """Najde IČO v HTML stránky."""
    # Typické vzory: "IČO: 12345678", "IČ: 12345678", "IC: 12345678"
    patterns = [
        r'I[ČC][OO]?\s*:?\s*(\d{8})',
        r'(?:ico|ic|ičo|ič)\s*:?\s*(\d{8})',
        r'(?:Company\s*ID|Registration\s*No\.?)\s*:?\s*(\d{8})',
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            ico = match.group(1)
            # Validace — IČO nemůže začínat 00000
            if not ico.startswith("00000"):
                return ico
    return None


def extract_contact_from_html(html: str) -> dict:
    """
    Extrahuje kontaktní údaje z HTML stránky.
    Hledá jména, telefony, emaily, pozice.
    """
    result = {
        "names": [],
        "emails": [],
        "phones": [],
        "roles": [],
    }

    html_lower = html.lower()

    # ── Emaily ──
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, html)
    # Filtr — vyřadíme generické a systémové
    skip_domains = {"example.com", "sentry.io", "w3.org", "schema.org", "wixpress.com"}
    skip_prefixes = {"noreply", "no-reply", "unsubscribe", "support@google", "privacy@"}
    for email in emails:
        domain = email.split("@")[1].lower()
        prefix = email.split("@")[0].lower()
        if domain not in skip_domains and not any(prefix.startswith(p) for p in skip_prefixes):
            if email not in result["emails"]:
                result["emails"].append(email)

    # ── Telefony ──
    phone_pattern = r'(?:\+420\s?)?(?:\d{3}\s?){3}'
    phones = re.findall(phone_pattern, html)
    result["phones"] = list(dict.fromkeys(phones))[:5]

    # ── Jména v kontaktní sekci ──
    # Hledáme české jméno + příjmení (velká písmena)
    name_patterns = [
        # "Ing. Jan Novák", "Mgr. Marie Nováková", "Jan Novák"
        r'(?:Ing\.|Mgr\.|Bc\.|PhDr\.|JUDr\.|MUDr\.|RNDr\.|doc\.|prof\.)\s+'
        r'([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+\s+'
        r'[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+)',
    ]

    for pattern in name_patterns:
        matches = re.findall(pattern, html)
        result["names"].extend(matches)

    # Hledáme jména poblíž klíčových slov
    role_keywords = [
        ("jednatel", "jednatel"),
        ("jednatele", "jednatel"),
        ("majitel", "majitel"),
        ("zakladatel", "zakladatel"),
        ("ředitel", "ředitel"),
        ("CEO", "CEO"),
        ("CTO", "CTO"),
        ("founder", "zakladatel"),
        ("owner", "majitel"),
        ("kontakt", "kontakt"),
    ]

    for keyword, role in role_keywords:
        # Hledáme jméno v okolí 100 znaků od klíčového slova
        keyword_positions = [m.start() for m in re.finditer(
            re.escape(keyword), html_lower
        )]
        for pos in keyword_positions:
            # Prohledáme okolí
            window = html[max(0, pos - 80):pos + 200]
            # Hledáme české jméno
            name_match = re.search(
                r'([A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+\s+'
                r'[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+)',
                window,
            )
            if name_match:
                name = name_match.group(1)
                # Filtr — vyřadíme generické řetězce
                skip_names = {
                    "Obchodní Podmínky", "Zásady Ochrany", "Přijmout Vše",
                    "Více Informací", "Velká Bystřice", "České Republiky",
                    "Google Analytics", "Meta Pixel", "Cookie Policy",
                }
                if name not in skip_names and name not in result["names"]:
                    result["names"].append(name)
                    if role not in result["roles"]:
                        result["roles"].append(role)

    # Deduplikace
    result["names"] = list(dict.fromkeys(result["names"]))[:5]
    result["emails"] = result["emails"][:5]

    return result


async def get_company_info(
    url: str,
    html: str = "",
    ico: str | None = None,
) -> CompanyInfo:
    """
    Kompletní lookup firmy — kombinuje ARES + web scraping.

    Args:
        url: URL webu firmy
        html: HTML obsah stránky (pokud už máme)
        ico: IČO firmy (pokud známe)
    """
    info = CompanyInfo()

    # 1. Pokud nemáme IČO, zkusíme ho najít v HTML
    if not ico and html:
        ico = extract_ico_from_html(html)
        if ico:
            logger.info(f"IČO nalezeno v HTML: {ico}")

    # 2. ARES lookup
    if ico:
        info = await lookup_ares(ico)

    # 3. Doplníme info z HTML
    if html:
        web_contacts = extract_contact_from_html(html)

        # Pokud nemáme jméno kontaktu z ARES (= firma je s.r.o./a.s.)
        if not info.contact_person and web_contacts["names"]:
            info.contact_person = web_contacts["names"][0]
            if web_contacts["roles"]:
                info.contact_role = web_contacts["roles"][0]
            info.source = (info.source or "") + "+web"

        # Email a telefon z webu
        if web_contacts["emails"]:
            info.contact_email = web_contacts["emails"][0]
        if web_contacts["phones"]:
            info.contact_phone = web_contacts["phones"][0]

    # 4. Fallback — extrahujeme název z URL
    if not info.company_name:
        domain = url.replace("https://", "").replace("http://", "").split("/")[0]
        domain = domain.replace("www.", "")
        info.company_name = domain.split(".")[0].title()

    return info
