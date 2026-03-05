"""
AIshield.cz — Zboží.cz Scraper v2
Extrahuje e-shopy (prodejce) přes Zboží.cz Product API.
Strategie: Playwright najde produkty v kategorii → Product API vrátí nabídky s e-shopy.
"""

import re
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("aishield.prospecting.zbozi")


@dataclass
class ZboziShop:
    """E-shop nalezený na Zboží.cz."""
    name: str
    shop_id: str = ""
    url: Optional[str] = None
    rating_count: int = 0
    source: str = "zbozi.cz"


# Kategorie pro scraping prodejců
ZBOZI_CATEGORIES = [
    "pocitace/notebooky",
    "pocitace/monitory",
    "elektronika/televize",
    "elektronika/mobilni-telefony",
    "pocitace/tiskarny",
    "foto-a-kamery/fotoaparaty",
    "elektro/pracky",
    "elektro/lednice",
    "elektro/mycky-nadobi",
    "sport/fitness",
    "auto-moto/autodiagnostika",
    "dum-a-byt/vysavace",
    "hracky/stavebnice",
    "zdravi/masazni-pristroje",
]


def _extract_sellers_from_product_api(slug: str) -> list[ZboziShop]:
    """
    Zavolej Zboží.cz Product API a extrahuj všechny prodejce z nabídek.
    
    Struktura: product.bestOffers.offers[].shop + product.cheapestOffers.offers[].shop
    Každý shop má: displayName, id, recensionCount, rating
    """
    import httpx

    shops = {}
    try:
        url = (
            f"https://www.zbozi.cz/api/v3/product/{slug}/"
            f"?limitTopOffers=4&limitCheapOffers=-1"
            f"&filterFields=$all$&showEroticDocument=true"
        )
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                              "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
                "Referer": "https://www.zbozi.cz/",
            })
            if resp.status_code != 200:
                return []

            data = resp.json()
            product = data.get("product", {})

            # Kombinuj bestOffers + cheapestOffers
            best = product.get("bestOffers", {}).get("offers", [])
            cheap = product.get("cheapestOffers", {}).get("offers", [])

            for offer in best + cheap:
                shop = offer.get("shop", {})
                if not shop:
                    continue

                name = shop.get("displayName", "")
                if not name or name in shops:
                    continue

                shops[name] = ZboziShop(
                    name=name,
                    shop_id=str(shop.get("id", "")),
                    rating_count=shop.get("recensionCount", 0),
                    source="zbozi.cz",
                )

    except Exception as e:
        logger.debug(f"Zboží.cz product API error for {slug}: {e}")

    return list(shops.values())


def _get_product_slugs_from_category(category: str, max_slugs: int = 10) -> list[str]:
    """
    Použij Playwright k nalezení product slugů v kategorii.
    Přistupuje přes homepage → kategorie (obejde CMP consent).
    """
    from playwright.sync_api import sync_playwright

    slugs = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) "
                           "AppleWebKit/537.36 Chrome/120.0.0.0",
            )

            page.route("**/*.png", lambda route: route.abort())
            page.route("**/*.jpg", lambda route: route.abort())
            page.route("**/*.gif", lambda route: route.abort())

            # Homepage first (session cookies, consent acceptance)
            page.goto("https://www.zbozi.cz/", wait_until="domcontentloaded",
                      timeout=30000)
            page.wait_for_timeout(2000)

            # Naviguj do kategorie
            page.goto(f"https://www.zbozi.cz/{category}/",
                      wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)

            # Extrahuj product slugy
            product_links = page.query_selector_all('a[href*="/vyrobek/"]')
            seen = set()
            for pl in product_links:
                href = pl.get_attribute("href") or ""
                match = re.search(r'/vyrobek/([^/]+)/', href)
                if match and match.group(1) not in seen:
                    seen.add(match.group(1))
                    slugs.append(match.group(1))
                    if len(slugs) >= max_slugs:
                        break

            browser.close()

    except Exception as e:
        logger.error(f"Zboží.cz Playwright error for {category}: {e}")

    return slugs


def scrape_zbozi_category(category: str, max_products: int = 5) -> list[ZboziShop]:
    """
    Scrapuj jednu kategorii Zboží.cz:
    1. Playwright: najdi produkty v kategorii
    2. Product API: pro každý produkt extrahuj e-shopy z nabídek
    """
    logger.info(f"Zboží.cz: scrapuji kategorii '{category}'")

    # Krok 1: Najdi produkty
    slugs = _get_product_slugs_from_category(category, max_slugs=max_products)
    logger.info(f"Zboží.cz: nalezeno {len(slugs)} produktů v '{category}'")

    if not slugs:
        return []

    # Krok 2: Pro každý produkt extrahuj e-shopy
    all_shops = {}
    for slug in slugs:
        sellers = _extract_sellers_from_product_api(slug)
        for s in sellers:
            if s.name not in all_shops:
                all_shops[s.name] = s
        logger.debug(f"Zboží.cz: {slug} → {len(sellers)} prodejců")

    result = list(all_shops.values())
    logger.info(f"Zboží.cz: celkem {len(result)} unikátních e-shopů pro '{category}'")
    return result


def scrape_all_categories(max_products_per_cat: int = 3) -> list[ZboziShop]:
    """Projdi všechny kategorie a vrať deduplikovaný seznam e-shopů."""
    all_shops = {}

    for category in ZBOZI_CATEGORIES:
        shops = scrape_zbozi_category(category, max_products=max_products_per_cat)
        for s in shops:
            if s.name not in all_shops:
                all_shops[s.name] = s
            else:
                # Aktualizuj rating_count pokud vyšší
                if s.rating_count > all_shops[s.name].rating_count:
                    all_shops[s.name].rating_count = s.rating_count

    result = list(all_shops.values())
    logger.info(f"Zboží.cz: celkem {len(result)} unikátních e-shopů napříč kategoriemi")
    return result


async def import_zbozi_to_db(categories: list[str] | None = None,
                              max_products: int = 5) -> dict:
    """
    Hlavní vstupní bod: scrapuj Zboží.cz a importuj e-shopy do Supabase.
    """
    from backend.core.supabase_client import get_supabase

    cats = categories or ZBOZI_CATEGORIES[:5]
    all_shops = {}

    for cat in cats:
        shops = scrape_zbozi_category(cat, max_products=max_products)
        for s in shops:
            if s.name not in all_shops:
                all_shops[s.name] = s

    logger.info(f"Zboží.cz: importuji {len(all_shops)} e-shopů do DB")

    supabase = get_supabase()
    imported = 0
    skipped = 0
    errors = 0

    for shop in all_shops.values():
        try:
            shop_url = shop.url or f"https://www.zbozi.cz/obchod/{shop.shop_id}/"

            # Kontrola duplicity — URL i název
            existing = supabase.table("companies").select("id").or_(
                f"name.eq.{shop.name},url.eq.{shop_url}"
            ).limit(1).execute()

            if existing.data:
                skipped += 1
                continue

            supabase.table("companies").insert({
                "name": shop.name,
                "url": shop_url,
                "source": shop.source,
                "prospecting_status": "new",
                "metadata": {
                    "zbozi_shop_id": shop.shop_id,
                    "zbozi_rating_count": shop.rating_count,
                },
            }).execute()
            imported += 1

        except Exception as e:
            logger.error(f"Zboží.cz import error for {shop.name}: {e}")
            errors += 1

    result = {"imported": imported, "skipped": skipped, "errors": errors}
    logger.info(f"Zboží.cz import: {result}")
    return result


# ── Standalone test ──
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test 1: Product API
    print("=== TEST: Product API sellers ===")
    sellers = _extract_sellers_from_product_api(
        "apple-macbook-air-13-6-m4-2025-mc6t4cz-a"
    )
    print(f"Prodejců: {len(sellers)}")
    for s in sellers[:10]:
        print(f"  {s.name} (id={s.shop_id}, reviews={s.rating_count})")

    # Test 2: Full category scrape
    print("\n=== TEST: Full category scrape ===")
    shops = scrape_zbozi_category("pocitace/notebooky", max_products=3)
    print(f"E-shopů celkem: {len(shops)}")
    for s in shops[:20]:
        print(f"  {s.name} (reviews={s.rating_count})")

    print("\nDONE")
