"""
AIshield.cz — URL Finder
Pro každou firmu z ARES najde webovou stránku a kontaktní email.
Zdroje: Firmy.cz, Google, heuristika (ico.cz, rejstřík).
"""

import httpx
import asyncio
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class CompanyWebInfo:
    """Výsledek hledání webu a emailu firmy."""
    ico: str
    url: Optional[str] = None
    email: Optional[str] = None
    source: str = ""


# ── Heuristické patterny pro email ──
EMAIL_REGEX = re.compile(
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    re.IGNORECASE,
)

# Blacklist emailových domén (ne firemní)
EMAIL_BLACKLIST = {
    "example.com", "gmail.com", "yahoo.com", "hotmail.com",
    "outlook.com", "seznam.cz", "email.cz", "post.cz",
    "centrum.cz", "volny.cz",
}


async def find_url_firmy_cz(company_name: str, ico: str) -> Optional[str]:
    """Najdi web firmy na Firmy.cz podle názvu/IČO."""
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(
                f"https://www.firmy.cz/hledej?what={ico}",
                headers={
                    "User-Agent": "AIshield.cz Compliance Scanner/1.0",
                },
            )
            if response.status_code != 200:
                return None

            # Hledáme odkaz na web firmy v HTML
            html = response.text
            # Firmy.cz zobrazuje URL firmy v profilu
            url_match = re.search(
                r'href="(https?://(?!www\.firmy\.cz)[^"]+)"[^>]*class="[^"]*web',
                html,
            )
            if url_match:
                return url_match.group(1)

            # Fallback: hledáme jakýkoliv externí odkaz
            urls = re.findall(
                r'href="(https?://(?!www\.firmy\.cz|www\.google|facebook|twitter)[^"]+)"',
                html,
            )
            for url in urls[:5]:
                if any(part in url.lower() for part in [company_name.lower().split()[0]]):
                    return url

    except Exception:
        pass
    return None


async def find_url_heuristic(company_name: str, ico: str) -> Optional[str]:
    """
    Heuristika: zkus typické domény.
    Např. "Alza.cz a.s." → zkus alza.cz
    """
    # Vyčistit název firmy
    clean = company_name.lower()
    for suffix in [
        " s.r.o.", " a.s.", " s. r. o.", " a. s.",
        " spol. s r.o.", " v.o.s.", " k.s.",
        " se", " z.s.", " z. s.",
    ]:
        clean = clean.replace(suffix, "")
    clean = clean.strip().strip(",").strip()

    # Zkusit přímou doménu
    # "Super Firma" → superfirma.cz
    slug = re.sub(r'[^a-z0-9]', '', clean)
    if not slug or len(slug) < 3:
        return None

    domains_to_try = [
        f"https://www.{slug}.cz",
        f"https://{slug}.cz",
    ]

    async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
        for domain in domains_to_try:
            try:
                response = await client.head(domain)
                if response.status_code < 400:
                    return domain
            except Exception:
                continue

    return None


async def find_email_from_url(url: str) -> Optional[str]:
    """Načte web a hledá kontaktní email."""
    pages_to_check = [
        url,
        f"{url.rstrip('/')}/kontakt",
        f"{url.rstrip('/')}/contact",
        f"{url.rstrip('/')}/o-nas",
    ]

    async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
        for page_url in pages_to_check:
            try:
                response = await client.get(
                    page_url,
                    headers={"User-Agent": "AIshield.cz Compliance Scanner/1.0"},
                )
                if response.status_code != 200:
                    continue

                # Najdi emaily v HTML
                emails = EMAIL_REGEX.findall(response.text)
                for email in emails:
                    domain = email.split("@")[1].lower()
                    if domain not in EMAIL_BLACKLIST:
                        # Preferovat info@, kontakt@, obchod@
                        return email.lower()

            except Exception:
                continue

    return None


async def find_company_web(
    ico: str,
    company_name: str,
) -> CompanyWebInfo:
    """
    Hlavní funkce — najdi web a email pro firmu.
    Zkouší postupně: Firmy.cz → heuristiku → email z webu.
    """
    result = CompanyWebInfo(ico=ico)

    # 1. Firmy.cz
    url = await find_url_firmy_cz(company_name, ico)
    if url:
        result.url = url
        result.source = "firmy.cz"
    else:
        # 2. Heuristika
        url = await find_url_heuristic(company_name, ico)
        if url:
            result.url = url
            result.source = "heuristic"

    # 3. Email z webu
    if result.url:
        email = await find_email_from_url(result.url)
        if email:
            result.email = email

    return result


async def batch_find_urls(
    companies: list[dict],
    concurrency: int = 5,
) -> list[CompanyWebInfo]:
    """
    Najde weby a emaily pro seznam firem (paralelně s limitem).
    companies: [{"ico": "...", "name": "..."}]
    """
    semaphore = asyncio.Semaphore(concurrency)
    results: list[CompanyWebInfo] = []

    async def process(company: dict) -> CompanyWebInfo:
        async with semaphore:
            result = await find_company_web(
                ico=company["ico"],
                company_name=company["name"],
            )
            await asyncio.sleep(0.5)  # Rate limit
            return result

    tasks = [process(c) for c in companies]
    results = await asyncio.gather(*tasks)

    found = sum(1 for r in results if r.url)
    print(f"[URL Finder] {found}/{len(companies)} firem s nalezeným webem")
    return list(results)
