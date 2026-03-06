"""
AIshield.cz — Google Search Scraper pro LOVEC pipeline

Hledá české weby s AI systémy (chatboty, doporučování, AI content)
přes Google Custom Search API (zdarma 100 dotazů/den) nebo SerpAPI.

Cílí na MICRO segment — freelancery, bloggery, e-shopy, agentury —
tedy weby, které ARES vůbec nepokrývá.

Použití:
    from backend.prospecting.google_search import phase_google_search
    stats = await phase_google_search(limit=50)
"""

import asyncio
import hashlib
import logging
import re
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

import httpx

logger = logging.getLogger("aishield.prospecting.google_search")


# ── AI-specifické vyhledávací dotazy ──
# Každý dotaz cílí na weby, které mají reálnou AI Act povinnost

SEARCH_QUERIES = [
    # Chatboty na českých webech (čl. 50 AI Act — transparenční povinnost)
    '"Powered by Tidio" site:.cz',
    '"Powered by Intercom" site:.cz',
    '"Powered by Smartsupp" site:.cz',
    '"Powered by LiveChat" site:.cz',
    '"Powered by Drift" site:.cz',
    '"chatbot" "kontaktujte nás" site:.cz',
    '"AI asistent" site:.cz',
    '"virtuální asistent" site:.cz',
    # AI doporučovací systémy
    '"doporučujeme vám" "na základě" site:.cz',
    '"AI doporučování" site:.cz',
    '"personalizovaná nabídka" site:.cz',
    # AI-generovaný obsah
    '"vytvořeno pomocí AI" site:.cz',
    '"generováno umělou inteligencí" site:.cz',
    '"AI generated" site:.cz',
    # E-shopy s AI funkcemi
    '"Shoptet" kontakt email site:.cz',
    '"WooCommerce" "chatbot" site:.cz',
    '"doporučené produkty" "e-shop" site:.cz',
    # Webdesign agentury (multiplikátor — 1 agentura = 20-100 klientů)
    '"webdesign" "agentura" kontakt site:.cz',
    '"tvorba webových stránek" kontakt site:.cz',
    '"WordPress" "na míru" kontakt site:.cz',
    # Obecné weby s kontaktem (široký záběr)
    'inurl:kontakt "chatbot" site:.cz',
    'inurl:kontakt "AI" site:.cz',
    # Blogeři a tvůrci obsahu
    '"blog" "AI" "obrázky" site:.cz',
    '"Midjourney" OR "DALL-E" site:.cz',
]

# Dotazy pro .com/.eu české weby
SEARCH_QUERIES_INTL = [
    '"Powered by Smartsupp" site:.com inurl:cz',
    '"chatbot" "kontakt" "Praha" OR "Brno" OR "Ostrava"',
    '"AI compliance" "Czech" OR "Česko"',
]


def _normalize_url(url: str) -> str:
    """Normalizuj URL — odstraň trailing slash, query parametry, fragment."""
    parsed = urlparse(url)
    # Odstraň www prefix pro deduplikaci
    host = parsed.hostname or ""
    if host.startswith("www."):
        host = host[4:]
    # Vrať čistou doménu + cestu
    path = parsed.path.rstrip("/")
    return f"{host}{path}".lower()


def _extract_domain(url: str) -> str:
    """Extrahuj čistou doménu z URL."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if host.startswith("www."):
        host = host[4:]
    return host.lower()


def _is_valid_target(domain: str) -> bool:
    """Filtruj domény, které nechceme (sociální sítě, portály, naše vlastní)."""
    skip_domains = {
        "facebook.com", "twitter.com", "instagram.com", "linkedin.com",
        "youtube.com", "tiktok.com", "pinterest.com",
        "google.com", "google.cz", "seznam.cz", "bing.com",
        "wikipedia.org", "wikipedie.cz",
        "firmy.cz", "najisto.cz", "zivefirmy.cz", "heureka.cz", "zbozi.cz",
        "aishield.cz",  # Naše vlastní doména
        "github.com", "stackoverflow.com",
        "novinky.cz", "idnes.cz", "aktualne.cz", "irozhlas.cz",
        "lupa.cz", "root.cz", "zive.cz",
    }
    return domain not in skip_domains and len(domain) > 3


async def search_google_cse(
    query: str,
    api_key: str,
    cx: str,
    start: int = 1,
) -> list[dict]:
    """
    Volej Google Custom Search API.

    Args:
        query: Vyhledávací dotaz
        api_key: Google API key
        cx: Custom Search Engine ID
        start: Offset výsledků (1-based, max 91)

    Returns:
        Seznam výsledků [{title, link, snippet, domain}]
    """
    results = []

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": api_key,
                "cx": cx,
                "q": query,
                "start": start,
                "num": 10,
                "gl": "cz",
                "lr": "lang_cs",
            },
        )

        if resp.status_code == 429:
            logger.warning("[GoogleSearch] Rate limit — denní kvóta vyčerpána")
            return results

        if resp.status_code != 200:
            logger.error(f"[GoogleSearch] HTTP {resp.status_code}: {resp.text[:200]}")
            return results

        data = resp.json()
        items = data.get("items", [])

        for item in items:
            link = item.get("link", "")
            domain = _extract_domain(link)
            if _is_valid_target(domain):
                results.append({
                    "title": item.get("title", ""),
                    "link": link,
                    "snippet": item.get("snippet", ""),
                    "domain": domain,
                })

    return results


async def search_serpapi(
    query: str,
    api_key: str,
    start: int = 0,
) -> list[dict]:
    """
    Volej SerpAPI jako alternativu ke Google CSE.

    Args:
        query: Vyhledávací dotaz
        api_key: SerpAPI key
        start: Offset výsledků

    Returns:
        Seznam výsledků [{title, link, snippet, domain}]
    """
    results = []

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            "https://serpapi.com/search.json",
            params={
                "q": query,
                "engine": "google",
                "gl": "cz",
                "hl": "cs",
                "start": start,
                "num": 10,
                "api_key": api_key,
            },
        )

        if resp.status_code != 200:
            logger.error(f"[SerpAPI] HTTP {resp.status_code}: {resp.text[:200]}")
            return results

        data = resp.json()
        for item in data.get("organic_results", []):
            link = item.get("link", "")
            domain = _extract_domain(link)
            if _is_valid_target(domain):
                results.append({
                    "title": item.get("title", ""),
                    "link": link,
                    "snippet": item.get("snippet", ""),
                    "domain": domain,
                })

    return results


async def _upsert_company(
    supabase,
    domain: str,
    url: str,
    title: str,
    snippet: str,
    query_used: str,
) -> Optional[str]:
    """
    Vlož nebo přeskoč firmu v DB. Vrátí 'new', 'exists', nebo None při chybě.
    Deduplikace dle URL (normalizované domény).
    """
    # Normalizuj URL
    if not url.startswith("http"):
        url = f"https://{url}"
    clean_url = f"https://{domain}"

    # Zkontroluj jestli doména už v DB existuje (dle url LIKE %domain%)
    try:
        existing = supabase.table("companies").select("id").ilike(
            "url", f"%{domain}%"
        ).limit(1).execute()

        if existing.data:
            return "exists"
    except Exception:
        pass

    # Název firmy z titulku (odstraň " - ..." suffxy)
    name = re.sub(r'\s*[-–|].*$', '', title).strip()
    if not name or len(name) < 2:
        name = domain

    # Vlož novou firmu
    try:
        insert_data = {
            "name": name,
            "url": clean_url,
            "scan_status": "pending",
            "prospecting_status": "found",
            "prospecting_source": "google_search",
            "prospecting_query": query_used[:200],
            "prospecting_snippet": snippet[:500] if snippet else None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        supabase.table("companies").insert(insert_data).execute()
        return "new"

    except Exception as e:
        error_msg = str(e)
        if "duplicate" in error_msg.lower() or "409" in error_msg or "23505" in error_msg:
            return "exists"
        logger.error(f"[GoogleSearch] DB insert chyba pro {domain}: {e}")
        return None


async def phase_google_search(
    limit: int = 50,
    api_key: str = "",
    cx: str = "",
    serpapi_key: str = "",
    queries: Optional[list[str]] = None,
) -> dict:
    """
    Hlavní fáze: Prohledej Google pro české weby s AI a ulož do DB.

    Priorita: Google CSE (zdarma) → SerpAPI (placený fallback).

    Args:
        limit: Max počet nových firem k přidání (ochrana proti přetížení)
        api_key: Google Custom Search API key
        cx: Google Custom Search Engine ID
        serpapi_key: SerpAPI key (alternativa)
        queries: Vlastní queries (default: SEARCH_QUERIES)

    Returns:
        dict se statistikami {searched_queries, results_total, new_companies, duplicates}
    """
    from backend.database import get_supabase

    supabase = get_supabase()
    stats = {
        "searched_queries": 0,
        "results_total": 0,
        "new_companies": 0,
        "duplicates": 0,
        "errors": 0,
    }

    # Rozhodnutí: Google CSE nebo SerpAPI?
    use_serpapi = bool(serpapi_key) and not (api_key and cx)

    if not api_key and not serpapi_key:
        # Zkus načíst z env
        import os
        api_key = os.environ.get("GOOGLE_CSE_API_KEY", "")
        cx = os.environ.get("GOOGLE_CSE_CX", "")
        serpapi_key = os.environ.get("SERPAPI_KEY", "")
        use_serpapi = bool(serpapi_key) and not (api_key and cx)

    if not api_key and not serpapi_key:
        logger.error("[GoogleSearch] Žádný API klíč! Nastav GOOGLE_CSE_API_KEY+GOOGLE_CSE_CX nebo SERPAPI_KEY")
        return stats

    search_queries = queries or SEARCH_QUERIES
    seen_domains: set[str] = set()

    for query in search_queries:
        if stats["new_companies"] >= limit:
            logger.info(f"[GoogleSearch] Dosažen limit {limit} nových firem — zastavuji")
            break

        logger.info(f"[GoogleSearch] Query: {query}")
        stats["searched_queries"] += 1

        try:
            if use_serpapi:
                results = await search_serpapi(query, serpapi_key)
            else:
                results = await search_google_cse(query, api_key, cx)
        except Exception as e:
            logger.error(f"[GoogleSearch] Chyba search: {e}")
            stats["errors"] += 1
            continue

        for result in results:
            domain = result["domain"]

            # Přeskoč domény, které jsme už v tomto běhu viděli
            if domain in seen_domains:
                continue
            seen_domains.add(domain)

            stats["results_total"] += 1

            outcome = await _upsert_company(
                supabase,
                domain=domain,
                url=result["link"],
                title=result["title"],
                snippet=result["snippet"],
                query_used=query,
            )

            if outcome == "new":
                stats["new_companies"] += 1
                logger.info(f"[GoogleSearch] NOVÁ: {domain} — {result['title'][:60]}")
            elif outcome == "exists":
                stats["duplicates"] += 1

        # Anti-rate-limit pauza mezi queries
        await asyncio.sleep(1.5)

    logger.info(
        f"[GoogleSearch] Hotovo: {stats['searched_queries']} queries, "
        f"{stats['results_total']} výsledků, {stats['new_companies']} nových, "
        f"{stats['duplicates']} duplikátů"
    )
    return stats


async def import_google_to_db(
    limit: int = 100,
) -> dict:
    """
    Wrapper pro orchestrator — volá phase_google_search s env proměnnými.
    """
    return await phase_google_search(limit=limit)
