"""
AIshield.cz — Google Custom Search Engine (CSE) scraper
Používá Google CSE API pro vyhledávání firem na site:firmy.cz nebo přímo.
Vyžaduje GOOGLE_CSE_API_KEY a GOOGLE_CSE_ID v env.

Bez API klíče fallback: přímé Google scraping přes Playwright (riskantní).
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("aishield.prospecting.google_cse")

GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY", "")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID", "")


@dataclass
class GoogleSearchResult:
    """Výsledek z Google Custom Search."""
    title: str
    url: str
    snippet: str = ""
    source: str = "google_cse"


def search_google_cse(query: str, site_filter: str = "",
                       num_results: int = 10) -> list[GoogleSearchResult]:
    """
    Hledej přes Google Custom Search API.
    
    Args:
        query: Hledaný výraz
        site_filter: Volitelný site: filtr (např. "firmy.cz")
        num_results: Počet výsledků (max 10 per request, max 100 total)
    """
    if not GOOGLE_CSE_API_KEY or not GOOGLE_CSE_ID:
        logger.warning(
            "Google CSE: chybí GOOGLE_CSE_API_KEY nebo GOOGLE_CSE_ID. "
            "Nastav v env: GOOGLE_CSE_API_KEY=... GOOGLE_CSE_ID=..."
        )
        return []

    import httpx

    results = []
    search_query = f"site:{site_filter} {query}" if site_filter else query

    # Google CSE API: max 10 per request, stránkování přes start
    for start in range(1, min(num_results, 100) + 1, 10):
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params={
                        "key": GOOGLE_CSE_API_KEY,
                        "cx": GOOGLE_CSE_ID,
                        "q": search_query,
                        "start": start,
                        "num": min(10, num_results - len(results)),
                        "gl": "cz",
                        "lr": "lang_cs",
                    },
                )
                if resp.status_code != 200:
                    logger.error(f"Google CSE API error: {resp.status_code}")
                    break

                data = resp.json()
                items = data.get("items", [])

                for item in items:
                    results.append(GoogleSearchResult(
                        title=item.get("title", ""),
                        url=item.get("link", ""),
                        snippet=item.get("snippet", ""),
                    ))

                if not items:
                    break

        except Exception as e:
            logger.error(f"Google CSE error: {e}")
            break

    logger.info(f"Google CSE: nalezeno {len(results)} výsledků pro '{query}'")
    return results


def search_firms_via_google(keyword: str, region: str = "",
                            num_results: int = 20) -> list[GoogleSearchResult]:
    """
    Hledej firmy přes Google CSE s filtrem na firmy.cz.
    """
    query = f"{keyword} {region}".strip()
    return search_google_cse(query, site_filter="firmy.cz", num_results=num_results)


def search_eshops_via_google(keyword: str,
                              num_results: int = 20) -> list[GoogleSearchResult]:
    """
    Hledej e-shopy přes Google CSE.
    """
    return search_google_cse(
        f"{keyword} e-shop obchod",
        num_results=num_results,
    )


async def import_google_results_to_db(keyword: str, region: str = "") -> dict:
    """
    Vyhledej firmy přes Google CSE a importuj do Supabase.
    """
    if not GOOGLE_CSE_API_KEY:
        return {"imported": 0, "error": "GOOGLE_CSE_API_KEY not set"}

    from backend.core.supabase_client import get_supabase

    results = search_firms_via_google(keyword, region, num_results=50)
    supabase = get_supabase()

    imported = 0
    skipped = 0

    for r in results:
        try:
            # Extrahuj název firmy z title
            name = r.title.split("•")[0].split("|")[0].strip()
            if not name:
                continue

            existing = supabase.table("companies").select("id").eq(
                "name", name
            ).execute()
            if existing.data:
                skipped += 1
                continue

            supabase.table("companies").insert({
                "name": name,
                "url": r.url,
                "source": "google_cse",
                "prospecting_status": "new",
                "metadata": {"snippet": r.snippet},
            }).execute()
            imported += 1

        except Exception as e:
            logger.error(f"Google CSE import error: {e}")

    return {"imported": imported, "skipped": skipped}


# ── Standalone test ──
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    if GOOGLE_CSE_API_KEY:
        print("=== Google CSE Test ===")
        results = search_firms_via_google("software", "olomouc")
        print(f"Výsledků: {len(results)}")
        for r in results[:5]:
            print(f"  {r.title} → {r.url}")
    else:
        print("Google CSE: GOOGLE_CSE_API_KEY není nastaven")
        print("Pro aktivaci:")
        print("  1. Vytvoř CSE na https://cse.google.com/cse/create/new")
        print("  2. Získej API klíč na https://console.cloud.google.com/apis/credentials")
        print("  3. Nastav env: export GOOGLE_CSE_API_KEY=... GOOGLE_CSE_ID=...")
        print("  4. Cena: $5 / 1000 queries (prvních 100/den zdarma)")
