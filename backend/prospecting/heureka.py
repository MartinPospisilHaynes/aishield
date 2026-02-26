"""
AIshield.cz — Heureka Obchody Scraper
Stahuje e-shopy z veřejného adresáře obchody.heureka.cz.
Tisíce ověřených e-shopů s URL, ratingu a kontakty.
Výhoda: rating nám pomůže prioritizovat větší/aktivnější obchody.
"""

import httpx
import asyncio
import re
from dataclasses import dataclass
from typing import Optional
from bs4 import BeautifulSoup


@dataclass
class HeurekaShop:
    """E-shop nalezený na Heurece."""
    name: str
    url: str
    category: str = ""
    rating: float = 0.0       # Heureka skóre (0-100%)
    review_count: int = 0     # Počet recenzí — indikátor velikosti
    heureka_url: str = ""     # Profil na Heurece


# Kategorie na Heurece — ty s nejvyšší pravděpodobností AI
HEUREKA_CATEGORIES = [
    "elektronika",
    "pocitace-a-kancelar",
    "mobilni-telefony",
    "bile-zbozi",
    "dum-byt-a-zahrada",
    "obleceni-a-moda",
    "sport",
    "auto-moto",
    "zdravi-a-krasa",
    "hobby-a-zabava",
    "detske-zbozi",
    "jidlo-a-napoje",
    "knihy-filmy-hudba",
    "chovatelstvi",
    "stavebniny",
    "sexualni-a-eroticke-pomucky",
]

HEUREKA_BASE = "https://obchody.heureka.cz"


async def scrape_heureka_category(
    category: str = "",
    page: int = 1,
    max_pages: int = 10,
) -> list[HeurekaShop]:
    """
    Stáhne e-shopy z jedné kategorie Heureka adresáře.
    """
    shops: list[HeurekaShop] = []

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
            url = f"{HEUREKA_BASE}/{category}/" if category else f"{HEUREKA_BASE}/"
            if p > 1:
                url += f"?f={p}"

            try:
                response = await client.get(url)
                if response.status_code != 200:
                    break

                soup = BeautifulSoup(response.text, "html.parser")

                # Heureka shop karty — adaptivní selektory
                shop_cards = (
                    soup.select(".shop-list__item")
                    or soup.select(".c-shop-row")
                    or soup.select("[class*='shop'] [class*='item']")
                    or soup.select("article")
                )

                if not shop_cards:
                    break

                page_found = 0
                for card in shop_cards:
                    shop_name = ""
                    shop_url = ""
                    rating = 0.0
                    reviews = 0
                    heureka_profile = ""

                    # Název e-shopu
                    name_el = card.find(["h2", "h3", "a", "strong"])
                    if name_el:
                        shop_name = name_el.get_text(strip=True)

                    # Odkaz na profil / přímo na e-shop
                    for link in card.find_all("a", href=True):
                        href = link["href"]
                        # Přímý odkaz na e-shop (http:// mimo heureka.cz)
                        if href.startswith("http") and "heureka.cz" not in href:
                            shop_url = href.rstrip("/")
                        # Profil na Heurece
                        elif "heureka.cz" in href and "/recenze/" in href:
                            heureka_profile = href

                    # Rating
                    rating_el = card.find(
                        class_=re.compile(r"rating|score|stars", re.I)
                    )
                    if rating_el:
                        rating_text = rating_el.get_text(strip=True)
                        rating_match = re.search(r"(\d+[.,]?\d*)\s*%?", rating_text)
                        if rating_match:
                            rating = float(rating_match.group(1).replace(",", "."))

                    # Počet recenzí
                    review_el = card.find(
                        string=re.compile(r"\d+\s*(recenz|hodnocen)", re.I)
                    )
                    if review_el:
                        review_match = re.search(r"(\d+)", str(review_el))
                        if review_match:
                            reviews = int(review_match.group(1))

                    if shop_name and (shop_url or heureka_profile):
                        shops.append(HeurekaShop(
                            name=shop_name,
                            url=shop_url,
                            category=category,
                            rating=rating,
                            review_count=reviews,
                            heureka_url=heureka_profile,
                        ))
                        page_found += 1

                if page_found == 0:
                    break

                await asyncio.sleep(1.0)

            except Exception as e:
                print(f"[Heureka] Chyba kategorie={category}, stránka={p}: {e}")
                break

    return shops


async def resolve_shop_url(shop: HeurekaShop) -> str:
    """
    Pokud nemáme přímý URL eshopu, zkusíme ho získat z Heureka profilu.
    """
    if shop.url:
        return shop.url

    if not shop.heureka_url:
        return ""

    try:
        async with httpx.AsyncClient(
            timeout=10.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"},
        ) as client:
            response = await client.get(shop.heureka_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                # Najdi "Přejít do obchodu" odkaz
                shop_link = soup.find("a", href=True, string=re.compile(
                    r"(přejít|navštívit|otevřít|obchod)", re.I
                ))
                if shop_link:
                    href = shop_link["href"]
                    if href.startswith("http") and "heureka.cz" not in href:
                        return href.rstrip("/")

                # Fallback: jakýkoliv externí odkaz
                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    if (
                        href.startswith("http")
                        and "heureka.cz" not in href
                        and "facebook" not in href
                        and "twitter" not in href
                    ):
                        return href.rstrip("/")
    except Exception:
        pass

    return ""


async def scrape_all_categories(
    categories: list[str] | None = None,
    max_pages_per_category: int = 5,
) -> list[HeurekaShop]:
    """Stáhne e-shopy ze všech kategorií, deduplikuje."""
    cats = categories or HEUREKA_CATEGORIES
    all_shops: dict[str, HeurekaShop] = {}

    for cat in cats:
        print(f"[Heureka] Stahuji kategorii: {cat}...")
        shops = await scrape_heureka_category(
            category=cat,
            max_pages=max_pages_per_category,
        )
        for shop in shops:
            key = shop.url.lower().rstrip("/") if shop.url else shop.name.lower()
            if key not in all_shops:
                all_shops[key] = shop
            elif shop.review_count > all_shops[key].review_count:
                all_shops[key] = shop  # Preferuj verzi s více recenzemi

        await asyncio.sleep(0.5)

    result = list(all_shops.values())
    print(f"[Heureka] Celkem nalezeno: {len(result)} unikátních e-shopů")
    return result


async def import_heureka_to_db(
    max_pages_per_category: int = 3,
    skip_existing: bool = True,
    min_reviews: int = 0,
) -> dict:
    """
    Stáhne e-shopy z Heureky a uloží do DB.
    min_reviews: minimální počet recenzí (filtr na aktivní obchody).
    """
    from backend.database import get_supabase
    from datetime import datetime

    supabase = get_supabase()
    stats = {
        "scraped": 0,
        "resolved_urls": 0,
        "new": 0,
        "skipped_existing": 0,
        "skipped_no_url": 0,
        "errors": 0,
    }

    shops = await scrape_all_categories(
        max_pages_per_category=max_pages_per_category,
    )
    stats["scraped"] = len(shops)

    # Resolve URL pro shopy bez přímého odkazu (max 5 paralelně)
    sem = asyncio.Semaphore(5)

    async def resolve(shop: HeurekaShop):
        async with sem:
            if not shop.url and shop.heureka_url:
                shop.url = await resolve_shop_url(shop)
                if shop.url:
                    stats["resolved_urls"] += 1
                await asyncio.sleep(0.5)

    await asyncio.gather(*[resolve(s) for s in shops if not s.url])

    # Filtrace a import
    for shop in shops:
        if not shop.url:
            stats["skipped_no_url"] += 1
            continue

        if shop.review_count < min_reviews:
            continue

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
                "ico": "",
                "email": "",
                "source": "heureka_catalog",
                "nace_codes": ["4791"],
                "prospecting_status": "found",
                "scan_status": "pending",
                "category": shop.category,
                "heureka_rating": shop.rating,
                "heureka_reviews": shop.review_count,
                "created_at": datetime.utcnow().isoformat(),
            }).execute()
            stats["new"] += 1
        except Exception:
            stats["errors"] += 1

    print(f"[Heureka] Import hotov: {stats}")
    return stats
