"""
AIshield.cz — Firmy.cz Scraper v2
Playwright-based s route blockingem (mapy.cz) a Suggest API fallbackem.
"""

import asyncio
import re
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("aishield.prospecting.firmy")


@dataclass
class FirmyCzCompany:
    """Firma nalezená na Firmy.cz."""
    name: str
    detail_url: str
    address: str = ""
    category: str = ""
    web_url: Optional[str] = None
    phone: Optional[str] = None
    source: str = "firmy.cz"


# Kategorie pro cílený scraping
FIRMY_CATEGORIES = [
    "software olomouc",
    "e-shop",
    "webové stránky",
    "IT služby",
    "marketing",
    "účetnictví",
    "logistika",
    "výroba",
    "stavebnictví",
    "gastronomie",
    "zdravotnictví",
    "vzdělávání",
    "právní služby",
    "pojišťovnictví",
    "doprava",
]


def scrape_firmy_search(query: str, max_pages: int = 3) -> list[FirmyCzCompany]:
    """
    Vyhledej firmy na Firmy.cz přes Playwright s route blockingem.
    
    Args:
        query: Hledaný výraz (např. "software olomouc")
        max_pages: Maximální počet stránek výsledků
    
    Returns:
        Seznam nalezených firem
    """
    from playwright.sync_api import sync_playwright

    companies = []
    seen_urls = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="cs-CZ",
        )
        page = context.new_page()

        # Blokuj mapy.cz + těžké resources → stránka se načte bez timeoutu
        page.route("**/*mapy.cz*", lambda route: route.abort())
        page.route("**/*mapserver*", lambda route: route.abort())
        page.route("**/*.png", lambda route: route.abort())
        page.route("**/*.jpg", lambda route: route.abort())
        page.route("**/*.gif", lambda route: route.abort())
        page.route("**/*.woff2", lambda route: route.abort())

        # Načti homepage (nastaví session cookies)
        logger.info(f"Firmy.cz: načítám homepage + hledám '{query}'")
        page.goto("https://www.firmy.cz/", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)

        # Vyplň vyhledávání a stiskni Enter
        search_input = page.query_selector("input[name='q']")
        if not search_input:
            logger.error("Firmy.cz: nenalezen search input")
            browser.close()
            return companies

        search_input.click()
        page.wait_for_timeout(300)
        search_input.fill(query)
        page.wait_for_timeout(500)
        search_input.press("Enter")
        page.wait_for_timeout(4000)

        for page_num in range(max_pages):
            logger.info(f"Firmy.cz: stránka {page_num + 1}/{max_pages}, URL: {page.url}")

            # Extrahuj detail linky
            detail_links = page.query_selector_all('a[href*="/detail/"]')
            page_count = 0

            for link in detail_links:
                try:
                    href = link.get_attribute("href") or ""
                    name = link.inner_text().strip()

                    # Filtruj prázdné nebo duplicitní
                    if not name or len(name) < 2 or href in seen_urls:
                        continue
                    # Filtruj akční odkazy (obsahují #akce)
                    if "#akce" in href:
                        continue

                    seen_urls.add(href)

                    # Vytvoř absolutní URL
                    if not href.startswith("http"):
                        href = "https://www.firmy.cz" + href

                    company = FirmyCzCompany(
                        name=name,
                        detail_url=href,
                    )
                    companies.append(company)
                    page_count += 1
                except Exception as e:
                    logger.debug(f"Firmy.cz: chyba při zpracování linku: {e}")

            logger.info(f"Firmy.cz: stránka {page_num + 1} → {page_count} firem")

            if page_count == 0:
                break

            # Zkus najít tlačítko "Další" pro stránkování
            next_btn = page.query_selector(
                'a:has-text("Další"), a:has-text("další"), '
                'button:has-text("Další"), [aria-label="Další stránka"]'
            )
            if next_btn and page_num < max_pages - 1:
                try:
                    next_btn.click()
                    page.wait_for_timeout(3000)
                except Exception:
                    logger.info("Firmy.cz: nepodařilo se kliknout na Další")
                    break
            else:
                break

        browser.close()

    logger.info(f"Firmy.cz: celkem {len(companies)} firem pro '{query}'")
    return companies


def enrich_firmy_detail(company: FirmyCzCompany) -> FirmyCzCompany:
    """
    Navštiv detail stránku firmy a extrahuj web URL + telefon.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.route("**/*mapy.cz*", lambda route: route.abort())
        page.route("**/*.png", lambda route: route.abort())
        page.route("**/*.jpg", lambda route: route.abort())

        try:
            page.goto(company.detail_url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(2000)

            # Hledej web odkaz
            web_links = page.query_selector_all('a[href]:not([href*="firmy.cz"])')
            for wl in web_links:
                href = wl.get_attribute("href") or ""
                text = wl.inner_text().strip().lower()
                if href.startswith("http") and ("web" in text or "www" in href):
                    company.web_url = href
                    break

            # Hledej telefon
            body_text = page.evaluate("() => document.body.innerText")
            phone_match = re.search(r'(?:\+420\s?)?(\d{3}\s?\d{3}\s?\d{3})', body_text)
            if phone_match:
                company.phone = phone_match.group(0).strip()

            # Hledej adresu a kategorii z meta
            address_el = page.query_selector('[class*="address"], [class*="Address"]')
            if address_el:
                company.address = address_el.inner_text().strip()

        except Exception as e:
            logger.debug(f"Firmy.cz detail error for {company.name}: {e}")
        finally:
            browser.close()

    return company


def scrape_firmy_suggest_api(query: str, limit: int = 10) -> list[FirmyCzCompany]:
    """
    Fallback: použij Firmy.cz Suggest API (rychlé, bez Playwright).
    """
    import httpx
    
    companies = []
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(
                "https://www.firmy.cz/suggest",
                params={"phrase": query, "highlight": "0"},
                headers={"User-Agent": "AIshield.cz/1.0"},
            )
            if resp.status_code != 200:
                return companies

            data = resp.json()
            for item in data.get("result", []):
                if item.get("category") != "premise":
                    continue
                
                ud = item.get("userData", {})
                name = item.get("sentence", "")
                detail_id = ud.get("id", "")
                
                if name and detail_id:
                    companies.append(FirmyCzCompany(
                        name=name,
                        detail_url=f"https://www.firmy.cz/detail/{detail_id}",
                        address=ud.get("loc", ""),
                        category=ud.get("type", ""),
                        source="firmy.cz/suggest",
                    ))
                    
                    if len(companies) >= limit:
                        break

    except Exception as e:
        logger.error(f"Firmy.cz Suggest API error: {e}")

    return companies


def scrape_all_categories(max_pages: int = 2) -> list[FirmyCzCompany]:
    """Projdi všechny kategorie a vrať souhrnný seznam firem."""
    all_companies = []
    seen_urls = set()

    for category in FIRMY_CATEGORIES:
        logger.info(f"Firmy.cz: kategorie '{category}'")
        firms = scrape_firmy_search(category, max_pages=max_pages)
        for f in firms:
            if f.detail_url not in seen_urls:
                seen_urls.add(f.detail_url)
                all_companies.append(f)

    logger.info(f"Firmy.cz: celkem {len(all_companies)} unikátních firem")
    return all_companies


async def import_firmy_to_db(categories: list[str] | None = None,
                              max_pages: int = 2) -> dict:
    """
    Hlavní vstupní bod: scrapuj Firmy.cz a importuj do Supabase.
    
    Returns:
        {"imported": int, "skipped": int, "errors": int}
    """
    from backend.core.supabase_client import get_supabase

    cats = categories or FIRMY_CATEGORIES[:5]  # výchozí: prvních 5 kategorií
    all_companies = []
    seen = set()

    for cat in cats:
        firms = scrape_firmy_search(cat, max_pages=max_pages)
        for f in firms:
            if f.detail_url not in seen:
                seen.add(f.detail_url)
                all_companies.append(f)

    logger.info(f"Firmy.cz: importuji {len(all_companies)} firem do DB")

    supabase = get_supabase()
    imported = 0
    skipped = 0
    errors = 0

    for company in all_companies:
        try:
            # Zkontroluj duplicitu
            existing = supabase.table("companies").select("id").eq(
                "name", company.name
            ).execute()

            if existing.data:
                skipped += 1
                continue

            # Vlož nový záznam
            supabase.table("companies").insert({
                "name": company.name,
                "url": company.web_url or company.detail_url,
                "source": company.source,
                "prospecting_status": "new",
                "metadata": {
                    "firmy_cz_detail": company.detail_url,
                    "address": company.address,
                    "category": company.category,
                    "phone": company.phone,
                },
            }).execute()
            imported += 1

        except Exception as e:
            logger.error(f"Firmy.cz import error for {company.name}: {e}")
            errors += 1

    result = {"imported": imported, "skipped": skipped, "errors": errors}
    logger.info(f"Firmy.cz import: {result}")
    return result


# ── Standalone test ──
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test 1: Playwright search
    print("=== TEST: Playwright search ===")
    firms = scrape_firmy_search("software olomouc", max_pages=1)
    print(f"Nalezeno: {len(firms)} firem")
    for f in firms[:5]:
        print(f"  {f.name} → {f.detail_url}")

    # Test 2: Suggest API
    print("\n=== TEST: Suggest API ===")
    suggest = scrape_firmy_suggest_api("software")
    print(f"Suggest: {len(suggest)} výsledků")
    for s in suggest[:5]:
        print(f"  {s.name} | {s.address}")

    print("\nDONE")
