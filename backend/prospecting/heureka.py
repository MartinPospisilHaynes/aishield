"""
AIshield.cz — Heureka Obchody Scraper v2 (Playwright)
Playwright obchází Cloudflare. Stahuje e-shopy z obchody.heureka.cz.
Tabulka: c-shops-table, řádky: c-shops-table__row.
URL obchodu: heureka.cz/exit/{slug}/ redirect link → a.c-shops-table__name href.
Slug: alza-cz → alza.cz (heuristika).
30 000+ e-shopů registrovaných na Heurece.
"""

import asyncio
import re
from dataclasses import dataclass
from typing import Optional
from playwright.async_api import async_playwright


@dataclass
class HeurekaShop:
    """E-shop z Heureka katalogu."""
    name: str
    url: str  # Skutečná URL e-shopu (z exit linku / heuristika)
    heureka_slug: str = ""
    category: str = ""
    rating: float = 0.0
    review_count: int = 0
    description: str = ""


# Kategorie na obchody.heureka.cz
HEUREKA_CATEGORIES = [
    "elektronika",
    "auto-moto",
    "bydleni-doplnky",
    "detske-zbozi",
    "dum-zahrada",
    "male-spotrebice",
    "drogerie",
    "sex-erotika",
    "filmy-hudba-knihy",
    "gaming",
    "hobby",
    "hracky",
    "chovatelstvi",
    "jidlo-a-napoje",
    "kancelar-papirnictvi",
    "kosmetika-zdravi",
    "moda",
    "sport",
    "velke-spotrebice",
    "zdravi",
]


def _slug_to_url(slug: str) -> str:
    """
    Převede Heureka slug na pravděpodobnou URL obchodu.
    alza-cz → https://www.alza.cz
    datart-cz → https://www.datart.cz
    imobily-eu → https://www.imobily.eu
    softcom-cz-eshop-default-asp → https://www.softcom.cz
    """
    if not slug:
        return ""
    # Odstraň suffixy jako -eshop-default-asp
    clean = re.sub(r'-(eshop|default|asp|shop|obchod|store|www).*$', '', slug)
    # Nahraď poslední -cz / -com / -eu / -sk za .cz / .com / .eu / .sk
    for tld in ["-cz", "-com", "-eu", "-sk", "-net", "-org", "-shop", "-store"]:
        if clean.endswith(tld):
            domain = clean[:-len(tld)] + tld.replace("-", ".")
            return f"https://www.{domain}"
    # Fallback: prostě přidej .cz
    return f"https://www.{clean}.cz"


async def _dismiss_heureka_cookies(page) -> None:
    """Zavři cookie dialog na Heurece."""
    try:
        btn = page.locator("#didomi-notice-agree-button")
        if await btn.count() > 0:
            await btn.first.click(timeout=5000)
            await page.wait_for_timeout(1000)
    except Exception:
        pass


async def _extract_shops_from_page(page) -> list[dict]:
    """
    Extrahuje obchody z aktuální Heureka stránky.
    Klíčové selektory:
    - tr.c-shops-table__row = řádek
    - a.c-shops-table__name = jméno obchodu (href je /exit/{slug}/)
    - a.e-button "Do obchodu" = odkaz na obchod (taky /exit/{slug}/)
    - a.c-shops-table__rating = rating link (/slug/recenze/overene)
    - li.c-shops-table__reviews-count = počet recenzí
    - p v --info buňce = popis
    """
    return await page.evaluate("""() => {
        const results = [];
        const rows = document.querySelectorAll('tr.c-shops-table__row');
        for (const row of rows) {
            const nameEl = row.querySelector('a.c-shops-table__name');
            if (!nameEl) continue;

            const name = nameEl.textContent.trim();
            const nameHref = nameEl.href || '';

            // Slug z exit linku: heureka.cz/exit/alza-cz/
            let slug = '';
            const exitMatch = nameHref.match(/\\/exit\\/([^\\/\\?]+)/);
            if (exitMatch) {
                slug = exitMatch[1];
            } else {
                // Fallback: z recenze linku
                const ratingEl = row.querySelector('a.c-shops-table__rating');
                if (ratingEl && ratingEl.href) {
                    const rm = ratingEl.href.match(/obchody\\.heureka\\.cz\\/([^\\/]+)/);
                    if (rm) slug = rm[1];
                }
            }

            // Rating
            const ratingEl = row.querySelector('.c-rating-widget__value');
            const ratingText = ratingEl ? ratingEl.textContent.trim() : '0';

            // Recenze
            const reviewsEl = row.querySelector('li.c-shops-table__reviews-count');
            const reviewsText = reviewsEl ? reviewsEl.textContent.trim() : '0';

            // Popis
            const descEl = row.querySelector('.c-shops-table__cell--info p');
            const desc = descEl ? descEl.textContent.trim() : '';

            results.push({
                name: name,
                slug: slug,
                rating: parseFloat(ratingText.replace(',', '.')) || 0,
                reviewCount: parseInt(reviewsText.replace(/[^0-9]/g, '')) || 0,
                description: desc.substring(0, 300),
            });
        }
        return results;
    }""")


async def scrape_heureka_category(
    category: str,
    max_pages: int = 10,
) -> list[HeurekaShop]:
    """
    Stáhne e-shopy z jedné Heureka kategorie.
    Stránkuje automaticky.
    """
    shops: list[HeurekaShop] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            locale="cs-CZ",
        )
        page = await ctx.new_page()

        for pg_num in range(1, max_pages + 1):
            url = f"https://obchody.heureka.cz/{category}/"
            if pg_num > 1:
                url += f"?page={pg_num}"

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_timeout(3000)

                if pg_num == 1:
                    await _dismiss_heureka_cookies(page)
                    await page.wait_for_timeout(1000)

                raw = await _extract_shops_from_page(page)
                if not raw:
                    print(f"[Heureka PW] {category}/{pg_num}: 0 obchodů — konec")
                    break

                for r in raw:
                    shop_url = _slug_to_url(r["slug"])
                    shops.append(HeurekaShop(
                        name=r["name"],
                        url=shop_url,
                        heureka_slug=r["slug"],
                        category=category,
                        rating=r["rating"],
                        review_count=r["reviewCount"],
                        description=r["description"],
                    ))

                print(f"[Heureka PW] {category}/{pg_num}: {len(raw)} obchodů")
                await asyncio.sleep(1.5)

            except Exception as e:
                print(f"[Heureka PW] Chyba {category}/{pg_num}: {e}")
                break

        await browser.close()

    return shops


async def resolve_shop_url(slug: str) -> Optional[str]:
    """
    Následuje Heureka exit redirect a zjistí skutečnou URL obchodu.
    Pomalejší, ale přesnější než heuristika.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(locale="cs-CZ")
        page = await ctx.new_page()

        try:
            url = f"https://www.heureka.cz/exit/{slug}/"
            resp = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            # Po redirectu page.url je skutečná URL
            final_url = page.url
            if final_url and "heureka" not in final_url:
                return final_url
            return None
        except Exception:
            return None
        finally:
            await browser.close()


async def scrape_all_categories(
    categories: list[str] | None = None,
    max_pages_per_category: int = 5,
) -> list[HeurekaShop]:
    """
    Stáhne obchody ze všech kategorií, deduplikuje dle slugu.
    """
    cats = categories or HEUREKA_CATEGORIES
    all_shops: dict[str, HeurekaShop] = {}

    for cat in cats:
        print(f"[Heureka PW] Stahuji kategorii: {cat}...")
        shops = await scrape_heureka_category(
            category=cat,
            max_pages=max_pages_per_category,
        )
        for shop in shops:
            key = shop.heureka_slug or shop.name.lower()
            if key not in all_shops:
                all_shops[key] = shop
            else:
                existing = all_shops[key]
                if cat not in existing.category:
                    existing.category += f",{cat}"

        await asyncio.sleep(2.0)

    result = list(all_shops.values())
    print(f"[Heureka PW] Celkem: {len(result)} unikátních obchodů")
    return result


async def import_heureka_to_db(
    max_pages_per_category: int = 3,
    skip_existing: bool = True,
) -> dict:
    """Stáhne obchody a uloží do DB."""
    from backend.database import get_supabase
    from datetime import datetime

    supabase = get_supabase()
    stats = {"scraped": 0, "new": 0, "skipped": 0, "errors": 0}

    shops = await scrape_all_categories(
        max_pages_per_category=max_pages_per_category,
    )
    stats["scraped"] = len(shops)

    for shop in shops:
        if not shop.url:
            stats["errors"] += 1
            continue

        if skip_existing:
            existing = supabase.table("companies").select(
                "id"
            ).eq("url", shop.url).limit(1).execute()
            if existing.data:
                stats["skipped"] += 1
                continue

        try:
            supabase.table("companies").upsert({
                "name": shop.name,
                "url": shop.url,
                "category": shop.category,
                "description": shop.description[:500] if shop.description else "",
                "source": "heureka",
                "prospecting_status": "found",
                "scan_status": "pending",
                "created_at": datetime.utcnow().isoformat(),
            }, on_conflict="url").execute()
            stats["new"] += 1
        except Exception as e:
            print(f"[Heureka PW] DB chyba {shop.url}: {e}")
            stats["errors"] += 1

    print(f"[Heureka PW] Import hotov: {stats}")
    return stats
