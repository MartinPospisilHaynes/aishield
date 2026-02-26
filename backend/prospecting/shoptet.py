"""
AIshield.cz — Shoptet Katalog Scraper
Stahuje e-shopy z veřejného katalogu shoptet.cz/katalog-obchodu.
40 000+ českých e-shopů — naše nejcennější cílová skupina.
E-shopy masivně používají AI (chatboty, recommendation engines, GA4).
"""

import httpx
import asyncio
import re
from dataclasses import dataclass
from typing import Optional
from bs4 import BeautifulSoup


@dataclass
class ShoptetShop:
    """E-shop nalezený v Shoptet katalogu."""
    name: str
    url: str
    category: str = ""
    description: str = ""


# Kategorie katalogu — nejrelevantější pro AI Act
SHOPTET_CATEGORIES = [
    "elektronika",
    "obleceni-a-moda",
    "dum-a-zahrada",
    "sport-a-outdoor",
    "zdravi-a-krasa",
    "auto-moto",
    "hobby-a-volny-cas",
    "jidlo-a-napoje",
    "deti-a-hracky",
    "kancelar-a-skola",
    "zvířata",
    "darky",
    "kultura-a-zabava",
    "stavebnictvi",
    "prumysl",
]

# Base URL katalogu
KATALOG_URL = "https://www.shoptet.cz/katalog-obchodu"


async def scrape_shoptet_category(
    category: str = "",
    page: int = 1,
    max_pages: int = 10,
) -> list[ShoptetShop]:
    """
    Stáhne e-shopy z jedné kategorie Shoptet katalogu.
    Vrací název, URL a kategorii.
    """
    shops: list[ShoptetShop] = []

    async with httpx.AsyncClient(
        timeout=15.0,
        follow_redirects=True,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "cs-CZ,cs;q=0.9",
        },
    ) as client:
        for p in range(page, page + max_pages):
            url = f"{KATALOG_URL}/{category}/" if category else f"{KATALOG_URL}/"
            params = {"page": p} if p > 1 else {}

            try:
                response = await client.get(url, params=params)
                if response.status_code != 200:
                    break

                soup = BeautifulSoup(response.text, "html.parser")

                # Najdi karty e-shopů - adaptivní selektor
                shop_cards = (
                    soup.select(".catalog-item")
                    or soup.select(".shop-item")
                    or soup.select("[class*='catalog'] a[href]")
                    or soup.select("article a[href]")
                )

                if not shop_cards:
                    # Zkus fallback — najdi všechny externí odkazy
                    shop_cards = []
                    for link in soup.find_all("a", href=True):
                        href = link["href"]
                        if (
                            href.startswith("http")
                            and "shoptet.cz" not in href
                            and "facebook" not in href
                            and "twitter" not in href
                            and "instagram" not in href
                        ):
                            shop_cards.append(link)

                if not shop_cards:
                    break  # Žádné další obchody

                page_shops = 0
                for card in shop_cards:
                    # Extrakce URL e-shopu
                    shop_url = None
                    shop_name = ""

                    if isinstance(card, str):
                        continue

                    # Hledáme odkaz na e-shop
                    link = card if card.name == "a" else card.find("a", href=True)
                    if link and link.get("href"):
                        href = link["href"]
                        if href.startswith("http") and "shoptet.cz" not in href:
                            shop_url = href

                    # Hledáme název
                    title_el = card.find(["h2", "h3", "h4", "strong", "span"])
                    if title_el:
                        shop_name = title_el.get_text(strip=True)
                    elif link:
                        shop_name = link.get_text(strip=True)

                    # Popis
                    desc_el = card.find("p")
                    desc = desc_el.get_text(strip=True) if desc_el else ""

                    if shop_url and shop_name:
                        shops.append(ShoptetShop(
                            name=shop_name,
                            url=shop_url.rstrip("/"),
                            category=category,
                            description=desc[:200],
                        ))
                        page_shops += 1

                if page_shops == 0:
                    break  # Stránka bez výsledků

                await asyncio.sleep(1.0)  # Rate limit

            except Exception as e:
                print(f"[Shoptet] Chyba kategorie={category}, stránka={p}: {e}")
                break

    return shops


async def scrape_all_categories(
    categories: list[str] | None = None,
    max_pages_per_category: int = 5,
) -> list[ShoptetShop]:
    """
    Stáhne e-shopy ze všech kategorií.
    Deduplikuje podle URL.
    """
    cats = categories or SHOPTET_CATEGORIES
    all_shops: dict[str, ShoptetShop] = {}

    for cat in cats:
        print(f"[Shoptet] Stahuji kategorii: {cat}...")
        shops = await scrape_shoptet_category(
            category=cat,
            max_pages=max_pages_per_category,
        )
        for shop in shops:
            url_key = shop.url.lower().rstrip("/")
            if url_key not in all_shops:
                all_shops[url_key] = shop

        await asyncio.sleep(0.5)

    result = list(all_shops.values())
    print(f"[Shoptet] Celkem nalezeno: {len(result)} unikátních e-shopů")
    return result


async def import_shoptet_to_db(
    max_pages_per_category: int = 3,
    skip_existing: bool = True,
) -> dict:
    """
    Stáhne e-shopy ze Shoptet katalogu a uloží do DB.
    Vrací statistiky.
    """
    from backend.database import get_supabase
    from datetime import datetime

    supabase = get_supabase()
    stats = {
        "scraped": 0,
        "new": 0,
        "skipped_existing": 0,
        "errors": 0,
    }

    shops = await scrape_all_categories(
        max_pages_per_category=max_pages_per_category,
    )
    stats["scraped"] = len(shops)

    for shop in shops:
        # Zkontroluj jestli URL už nemáme
        if skip_existing:
            existing = supabase.table("companies").select(
                "id"
            ).eq("url", shop.url).limit(1).execute()
            if existing.data:
                stats["skipped_existing"] += 1
                continue

        try:
            supabase.table("companies").insert({
                "name": shop.name,
                "url": shop.url,
                "ico": "",  # Doplní se později z ARES reverse lookup
                "email": "",  # Doplní se web scrapingem
                "source": "shoptet_catalog",
                "nace_codes": ["4791"],  # E-commerce
                "prospecting_status": "found",
                "scan_status": "pending",
                "category": shop.category,
                "description": shop.description,
                "created_at": datetime.utcnow().isoformat(),
            }).execute()
            stats["new"] += 1
        except Exception as e:
            # Pravděpodobně duplicita
            stats["errors"] += 1

    print(f"[Shoptet] Import hotov: {stats}")
    return stats
