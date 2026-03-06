"""
AIshield.cz -- Crawling ceskych firemnich katalogu v2

Zdroje:
  - Firmy.cz Suggest API (hlavni, rychly, spolehlivy, s detail enrichment)
  - Zivefirmy.cz (httpx + regex, overeny HTML pattern)

Najisto.cz ODSTRANEN (vraci 404, mrtvy katalog).

Pouziti:
    from backend.prospecting.catalog_crawler import phase_crawl_catalogs
    stats = await phase_crawl_catalogs(max_per_catalog=500)
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

import httpx

logger = logging.getLogger("aishield.prospecting.catalog_crawler")


@dataclass
class CatalogEntry:
    """Zaznam z firemniho katalogu."""
    name: str
    url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    category: Optional[str] = None
    source: str = ""
    detail_url: Optional[str] = None


EMAIL_RE = re.compile(
    r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
    re.IGNORECASE,
)

BLACKLIST_EMAILS = {
    "woocommerce", "wordpress", "example", "test", "noreply", "no-reply",
    "mailer-daemon", "postmaster", "unsubscribe", "donotreply",
}

SKIP_DOMAINS = {
    "facebook.", "google.", "mapy.", "twitter.", "instagram.", "linkedin.",
    "youtube.", "seznam.cz", "firmy.cz", "zivefirmy.", "damezbozi.",
    "sdzp.cz", "maxcdn", "fonts.", "cdnjs.", "unpkg.", "leaflet",
    "bootstrap", "jquery", "cloudflare", "gstatic",
    "justice.cz", "isir.justice", "or.justice", "rzp.cz",
    "gov.cz", "mfcr.cz", "cssz.cz", "szif.cz",
}


def _clean_email(email: str) -> Optional[str]:
    email = email.strip().lower()
    local = email.split("@")[0]
    if any(bl in local for bl in BLACKLIST_EMAILS):
        return None
    if email.endswith((".png", ".jpg", ".gif", ".svg", ".css", ".js")):
        return None
    return email


def _is_external_url(href: str, skip_hosts: set) -> bool:
    """Zjisti zda URL je externi (ne katalog/CDN/socialni sit)."""
    parsed = urlparse(href)
    host = (parsed.hostname or "").lower()
    if not host:
        return False
    return not any(skip in host for skip in skip_hosts)


# ============================================================
# FIRMY.CZ SUGGEST API -- hlavni zdroj
# ============================================================

FIRMY_SEARCH_QUERIES = [
    # IT a web
    "webdesign", "tvorba webu", "e-shop", "marketing", "SEO",
    "graficke studio", "IT sluzby", "software", "hosting",
    "mobilni aplikace", "programovani",
    # Sluzby
    "ucetnictvi", "pravni sluzby", "advokat", "auditor",
    "realitni kancelar", "pojisteni", "financni poradenstvi",
    "cestovni kancelar", "jazykova skola", "autoeskola",
    # Gastro a ubytovani
    "restaurace", "hotel", "penzion", "kavarna", "cukrarna",
    "catering", "pizzerie",
    # Zdravi a krasa
    "lekar", "zubar", "veterinar", "lekarna",
    "kadernictvi", "kosmetika", "fitness", "masaze",
    # Remesla
    "instalater", "elektrikar", "klempir", "malir",
    "truhlarna", "zamecnictvi", "cistirna", "uklid",
    # Obchod a auto
    "autoservis", "pneuservis", "autolakovny", "autodily",
    "kvetinarstvi", "zahradnictvi",
    # Stavebnictvi
    "stavebni firma", "architektura", "projekt",
    "zatepleni", "strechy", "okna dvere",
    # Vzdelavani
    "skoleni", "skolka", "kurz", "tanecni",
    "fotografove", "videoprodukce",
    # Prumysl
    "tiskarna", "obalovy material", "doprava",
    "logistika", "sklad", "strojirenstvi",
]


async def crawl_firmy_suggest(
    query: str,
    limit: int = 10,
) -> list[CatalogEntry]:
    """Firmy.cz Suggest API -- rychle, bez Playwright."""
    entries = []

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(
                "https://www.firmy.cz/suggest",
                params={"phrase": query, "highlight": "0"},
                headers={"User-Agent": "AIshield.cz/1.0"},
            )
            if resp.status_code != 200:
                return entries

            data = resp.json()
            for item in data.get("result", []):
                if item.get("category") != "premise":
                    continue

                ud = item.get("userData", {})
                name = item.get("sentence", "").strip()
                detail_id = ud.get("id", "")

                if not name or len(name) < 2:
                    continue

                entry = CatalogEntry(
                    name=name,
                    address=ud.get("loc", ""),
                    category=query,
                    source="firmy.cz",
                )

                if detail_id:
                    entry.detail_url = f"https://www.firmy.cz/detail/{detail_id}"

                entries.append(entry)
                if len(entries) >= limit:
                    break

        except Exception as e:
            logger.error(f"[Firmy.cz] Suggest API chyba pro '{query}': {e}")

    return entries


async def enrich_firmy_detail(entry: CatalogEntry) -> CatalogEntry:
    """Navstiv detail Firmy.cz a extrahuj web URL + email."""
    if not entry.detail_url:
        return entry

    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        try:
            resp = await client.get(
                entry.detail_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                    "Accept": "text/html",
                },
            )
            if resp.status_code != 200:
                return entry

            html = resp.text

            # Externi web linky (ne firmy.cz/seznam.cz)
            web_links = re.findall(
                r'href="(https?://(?!(?:www\.)?firmy\.cz)[^"]+)"',
                html,
            )
            for link in web_links:
                if _is_external_url(link, SKIP_DOMAINS):
                    entry.url = link
                    break

            # Email
            for email in EMAIL_RE.findall(html):
                cleaned = _clean_email(email)
                if cleaned and "firmy.cz" not in cleaned and "seznam.cz" not in cleaned:
                    entry.email = cleaned
                    break

            # Telefon
            phone_match = re.search(r'(?:\+420\s?)?(\d{3}\s?\d{3}\s?\d{3})', html)
            if phone_match:
                entry.phone = phone_match.group(0).strip()

        except Exception as e:
            logger.debug(f"[Firmy.cz] Detail chyba pro {entry.name}: {e}")

    return entry


# ============================================================
# ZIVEFIRMY.CZ -- httpx crawler
# Overeny HTML pattern:
#   <div class="company-item reg" id="cf{ID}" ...>
#     <a href="/{slug}_f{ID}?cz={cat_id}" title="{Nazev}">{Nazev}</a>
# ============================================================

# Kategorie: slug -> cislo  (URL: /{slug}_o{cislo})
ZIVEFIRMY_CATEGORIES = {
    "it-sluzby": 14,
    "graficke-prace-a-sluzby": 110,
    "reklama-a-marketing": 94,
    "ucetnictvi-a-dane": 46,
    "advokati-a-pravni-sluzby": 72,
    "restaurace": 1,
    "hotely-a-penziony": 55,
    "autoservisy-a-pneuservisy": 83,
    "kadernictvi-a-holistvi": 18,
    "kosmetika-a-estetika": 19,
    "lekari": 4,
    "stavebni-firmy": 25,
    "reality": 47,
    "e-shopy": 102,
    "fotografove": 112,
    "tisk-a-polygrafie": 111,
    "doprava-a-logistika": 65,
    "jazykove-skoly": 35,
}

# Regex: <a href="/slug_fID?cz=XX" title="Nazev">
ZIVEFIRMY_FIRM_RE = re.compile(
    r'<a\s+href="/([^"]+_f(\d+))\?cz=\d+"[^>]*title="([^"]+)"',
    re.IGNORECASE,
)

# Externi HTTP linky
ZIVEFIRMY_EXT_RE = re.compile(
    r'href="(https?://[^"]+)"',
    re.IGNORECASE,
)


async def crawl_zivefirmy_category(
    category: str,
    cat_id: int,
    max_pages: int = 5,
) -> list[CatalogEntry]:
    """Crawluj kategorii na Zivefirmy.cz."""
    entries: list[CatalogEntry] = []
    seen_ids: set[str] = set()

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html",
        "Accept-Language": "cs",
    }

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        for page_num in range(1, max_pages + 1):
            # URL: /slug_oID  (kategorie) s paginaci ?page=N
            url = f"https://www.zivefirmy.cz/{category}_o{cat_id}"
            if page_num > 1:
                url = f"{url}?page={page_num}"

            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    break

                html = resp.text
                page_count = 0

                for match in ZIVEFIRMY_FIRM_RE.finditer(html):
                    slug = match.group(1)       # napr. "extremwork_f434294"
                    firm_id = match.group(2)     # napr. "434294"
                    name = match.group(3).strip()

                    if firm_id in seen_ids or not name:
                        continue
                    seen_ids.add(firm_id)

                    entry = CatalogEntry(
                        name=name,
                        source="zivefirmy.cz",
                        category=category,
                        detail_url=f"https://www.zivefirmy.cz/{slug}",
                    )

                    # Hledej externi web URL v okoli zaznamu (800 znaku za matchem)
                    pos = match.start()
                    context = html[pos:pos + 800]

                    for ext_match in ZIVEFIRMY_EXT_RE.finditer(context):
                        href = ext_match.group(1)
                        if _is_external_url(href, SKIP_DOMAINS):
                            entry.url = href
                            break

                    # Hledej email v kontextu
                    for email in EMAIL_RE.findall(context):
                        cleaned = _clean_email(email)
                        if cleaned and "zivefirmy" not in cleaned:
                            entry.email = cleaned
                            break

                    entries.append(entry)
                    page_count += 1

                if page_count == 0:
                    break

                logger.debug(
                    f"[Zivefirmy] {category} strana {page_num}: {page_count} firem"
                )

            except Exception as e:
                logger.error(f"[Zivefirmy] {category} strana {page_num}: {e}")
                break

            await asyncio.sleep(2.0)

    return entries


async def enrich_zivefirmy_detail(entry: CatalogEntry) -> CatalogEntry:
    """Navstiv detail Zivefirmy.cz a extrahuj web URL + email."""
    if not entry.detail_url:
        return entry

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        try:
            resp = await client.get(
                entry.detail_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                    "Accept": "text/html",
                    "Accept-Language": "cs",
                },
            )
            if resp.status_code != 200:
                return entry

            html = resp.text

            # Externi web linky
            for ext_match in ZIVEFIRMY_EXT_RE.finditer(html):
                href = ext_match.group(1)
                if _is_external_url(href, SKIP_DOMAINS):
                    entry.url = href
                    break

            # Email
            for email in EMAIL_RE.findall(html):
                cleaned = _clean_email(email)
                if cleaned and "zivefirmy" not in cleaned:
                    entry.email = cleaned
                    break

        except Exception as e:
            logger.debug(f"[Zivefirmy] Detail chyba pro {entry.name}: {e}")

    return entry


# ============================================================
# DB UPSERT
# ============================================================

async def _upsert_catalog_entry(supabase, entry: CatalogEntry) -> str:
    """Vloz zaznam z katalogu do DB. Vrati 'new', 'exists', nebo 'error'."""
    if not entry.name or len(entry.name) < 2:
        return "error"

    try:
        domain = ""
        if entry.url:
            parsed = urlparse(entry.url)
            domain = (parsed.hostname or "").replace("www.", "").lower()

        if domain:
            existing = supabase.table("companies").select("id").ilike(
                "url", f"%{domain}%"
            ).limit(1).execute()
            if existing.data:
                return "exists"

        existing_name = supabase.table("companies").select("id").eq(
            "name", entry.name
        ).limit(1).execute()
        if existing_name.data:
            return "exists"

    except Exception:
        pass

    try:
        insert_data = {
            "name": entry.name,
            "scan_status": "pending",
            "prospecting_status": "found",
            "source": entry.source,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        if entry.url:
            insert_data["url"] = entry.url
        if entry.email:
            insert_data["email"] = entry.email
            insert_data["email_source"] = "catalog"
            insert_data["email_confidence"] = 0.7
        if entry.phone:
            insert_data["phone"] = entry.phone

        supabase.table("companies").insert(insert_data).execute()
        return "new"

    except Exception as e:
        error_msg = str(e)
        if "duplicate" in error_msg.lower() or "409" in error_msg or "23505" in error_msg:
            return "exists"
        logger.debug(f"[Catalog] DB chyba pro {entry.name}: {e}")
        return "error"


# ============================================================
# HLAVNI FAZE
# ============================================================

async def phase_crawl_catalogs(
    max_per_catalog: int = 500,
    catalogs: Optional[list[str]] = None,
    enrich_details: bool = True,
) -> dict:
    """
    Hlavni faze: crawluj ceske firemni katalogy a uloz do DB.

    Args:
        max_per_catalog: Max novych firem z jednoho katalogu
        catalogs: Ktere katalogy ("firmy", "zivefirmy")
        enrich_details: Navstivit detail stranku pro URL/email (pomalejsi)
    """
    from backend.database import get_supabase

    supabase = get_supabase()
    active_catalogs = catalogs or ["firmy", "zivefirmy"]
    stats = {
        "total_new": 0,
        "total_exists": 0,
        "total_errors": 0,
        "total_with_url": 0,
        "total_with_email": 0,
        "by_catalog": {},
    }

    for catalog in active_catalogs:
        cat_stats = {"new": 0, "exists": 0, "errors": 0, "crawled": 0, "enriched": 0}

        if catalog == "firmy":
            logger.info(
                f"[Catalog] Firmy.cz Suggest API -- {len(FIRMY_SEARCH_QUERIES)} queries"
            )

            for query in FIRMY_SEARCH_QUERIES:
                if cat_stats["new"] >= max_per_catalog:
                    break

                entries = await crawl_firmy_suggest(query, limit=10)
                cat_stats["crawled"] += len(entries)

                # Firmy.cz detail je JS-renderovany, httpx enrichment nedava data.
                # Importujeme jen jmena+adresy, smart_email_finder dohle da zbytek.
                for entry in entries:
                    if cat_stats["new"] >= max_per_catalog:
                        break

                    outcome = await _upsert_catalog_entry(supabase, entry)
                    if outcome == "new":
                        cat_stats["new"] += 1
                    elif outcome == "exists":
                        cat_stats["exists"] += 1
                    else:
                        cat_stats["errors"] += 1

                await asyncio.sleep(1.0)

        elif catalog == "zivefirmy":
            logger.info(
                f"[Catalog] Zivefirmy.cz -- {len(ZIVEFIRMY_CATEGORIES)} kategorii"
            )

            for cat_name, cat_id in ZIVEFIRMY_CATEGORIES.items():
                if cat_stats["new"] >= max_per_catalog:
                    break

                entries = await crawl_zivefirmy_category(cat_name, cat_id, max_pages=3)
                cat_stats["crawled"] += len(entries)

                for entry in entries:
                    if cat_stats["new"] >= max_per_catalog:
                        break

                    # Detail enrichment pro URL a email
                    if enrich_details and not entry.url and not entry.email:
                        entry = await enrich_zivefirmy_detail(entry)
                        cat_stats["enriched"] += 1
                        await asyncio.sleep(1.0)

                    outcome = await _upsert_catalog_entry(supabase, entry)
                    if outcome == "new":
                        cat_stats["new"] += 1
                        if entry.url:
                            stats["total_with_url"] += 1
                        if entry.email:
                            stats["total_with_email"] += 1
                    elif outcome == "exists":
                        cat_stats["exists"] += 1
                    else:
                        cat_stats["errors"] += 1

                await asyncio.sleep(3.0)

        else:
            logger.warning(f"[Catalog] Neznamy katalog: {catalog}")
            continue

        stats["by_catalog"][catalog] = cat_stats
        stats["total_new"] += cat_stats["new"]
        stats["total_exists"] += cat_stats["exists"]
        stats["total_errors"] += cat_stats["errors"]
        logger.info(f"[Catalog] {catalog} hotovo: {cat_stats}")

    logger.info(
        f"[Catalog] Celkem: {stats['total_new']} novych, "
        f"{stats['total_with_url']} s URL, {stats['total_with_email']} s emailem"
    )
    return stats


async def import_catalogs_to_db(max_per_catalog: int = 500) -> dict:
    """Wrapper pro orchestrator."""
    return await phase_crawl_catalogs(max_per_catalog=max_per_catalog)
