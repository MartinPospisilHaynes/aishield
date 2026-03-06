"""
AIshield.cz — CZ Domain Prober

Získá seznam .cz domén z veřejných zdrojů a probuje, které jsou aktivní:

Zdroje:
  1. Certificate Transparency (crt.sh) — veřejné API, ZDARMA
     Obsahuje všechny .cz domény s vydaným SSL certifikátem.
  2. DNS A/MX probing — ověří, že doména žije a přijímá email.

Pipeline:
  crt.sh → deduplikace → DNS A check → HTTP check → uložení do DB
  (smart_email_finder pak doplní emaily)

Post-processing:
  Protože nemáme kontext (nevíme jestli web má AI), prioritizaci řešíme:
  - Kombinací s Google Search queries (kdo z nich má AI na webu)
  - Nebo rychlým HTTP fetch homepage + regex hledání AI indikátorů

Použití:
    from backend.prospecting.cz_domain_prober import phase_probe_cz_domains
    stats = await phase_probe_cz_domains(limit=1000)
"""

import asyncio
import logging
import re
import socket
from datetime import datetime, timezone
from typing import Optional

import httpx

logger = logging.getLogger("aishield.prospecting.cz_domain_prober")


# ── AI indikátory na webových stránkách ──
# Používáme pro rychlou prioritizaci — weby s těmito patterny cílíme přednostně

AI_INDICATORS = [
    # Chatbot frameworky
    r"smartsupp", r"tidio", r"intercom", r"livechat", r"drift\.com",
    r"zendesk", r"freshchat", r"crisp\.chat", r"tawk\.to",
    # AI doporučování
    r"recombee", r"algolia", r"personalizace", r"doporučujeme",
    r"doporucene.produkty", r"recommended",
    # AI content
    r"ai.generated", r"umělou.inteligencí", r"ChatGPT", r"OpenAI",
    r"midjourney", r"dall-e", r"stable.diffusion",
    # E-commerce platformy s AI funkcemi
    r"shoptet", r"woocommerce", r"prestashop", r"magento",
    # Obecné AI signály
    r"chatbot", r"virtuální.asistent", r"ai.asistent",
]

AI_PATTERN = re.compile("|".join(AI_INDICATORS), re.IGNORECASE)


async def fetch_crt_sh_domains(
    query: str = "%.cz",
    limit: int = 5000,
) -> set[str]:
    """
    Stáhni .cz domény z Certificate Transparency logů (crt.sh).

    Args:
        query: SQL LIKE pattern pro domény (default: všechny .cz)
        limit: Max počet záznamů z API

    Returns:
        Set unikátních domén
    """
    domains: set[str] = set()

    async with httpx.AsyncClient(timeout=60) as client:
        # crt.sh JSON API — vrací certifikáty s common_name matching pattern
        try:
            resp = await client.get(
                "https://crt.sh/",
                params={
                    "q": query,
                    "output": "json",
                    # Omezíme na nedávné certifikáty (aktivní weby)
                },
            )

            if resp.status_code != 200:
                logger.error(f"[crt.sh] HTTP {resp.status_code}")
                return domains

            data = resp.json()

            for entry in data[:limit]:
                cn = entry.get("common_name", "").lower().strip()
                # Filtruj wildcard certifikáty
                cn = cn.lstrip("*.")
                # Jen .cz domény
                if cn.endswith(".cz") and "." in cn:
                    # Odstraň subdomény — chceme jen hlavní doménu
                    parts = cn.split(".")
                    if len(parts) == 2:
                        domains.add(cn)
                    elif len(parts) == 3 and parts[0] == "www":
                        domains.add(".".join(parts[1:]))
                    else:
                        # Hlavní doména = poslední 2 části
                        domains.add(".".join(parts[-2:]))

            logger.info(f"[crt.sh] Staženo {len(domains)} unikátních .cz domén")

        except httpx.TimeoutException:
            logger.warning("[crt.sh] Timeout — server je pomalý, zkus menší query")
        except Exception as e:
            logger.error(f"[crt.sh] Chyba: {e}")

    return domains


async def fetch_crt_sh_by_org(org_patterns: list[str]) -> set[str]:
    """
    Cílenější varianta — hledej certifikáty dle organizace.
    Např. "shoptet" → všechny Shoptet e-shopy s SSL.
    """
    domains: set[str] = set()

    async with httpx.AsyncClient(timeout=30) as client:
        for pattern in org_patterns:
            try:
                resp = await client.get(
                    "https://crt.sh/",
                    params={"q": pattern, "output": "json"},
                )
                if resp.status_code == 200:
                    for entry in resp.json()[:1000]:
                        cn = entry.get("common_name", "").lower().strip().lstrip("*.")
                        if cn and "." in cn:
                            parts = cn.split(".")
                            if len(parts) >= 2:
                                domains.add(".".join(parts[-2:]) if len(parts) > 2 else cn)

                await asyncio.sleep(2.0)

            except Exception as e:
                logger.debug(f"[crt.sh] Org query '{pattern}': {e}")

    logger.info(f"[crt.sh] Org search: {len(domains)} domén z {len(org_patterns)} queries")
    return domains


async def check_domain_alive(domain: str) -> bool:
    """Rychlý DNS A záznam check — žije doména?"""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: socket.getaddrinfo(domain, 80, socket.AF_INET, socket.SOCK_STREAM),
        )
        return bool(result)
    except (socket.gaierror, OSError):
        return False


async def check_domain_has_web(domain: str) -> Optional[str]:
    """HTTP check — vrátí finální URL pokud web odpovídá, jinak None."""
    urls_to_try = [f"https://{domain}", f"https://www.{domain}"]

    async with httpx.AsyncClient(timeout=8, follow_redirects=True, verify=False) as client:
        for url in urls_to_try:
            try:
                resp = await client.get(url)
                if resp.status_code < 400:
                    return str(resp.url)
            except Exception:
                continue

    return None


async def quick_ai_check(url: str) -> tuple[bool, list[str]]:
    """
    Rychlý check homepage — obsahuje AI indikátory?
    Stáhne jen prvních 50KB HTML a hledá patterny.

    Returns:
        (has_ai_indicators, list_of_found_indicators)
    """
    found: list[str] = []

    async with httpx.AsyncClient(timeout=10, follow_redirects=True, verify=False) as client:
        try:
            resp = await client.get(url)
            # Omez na prvních 50KB
            html = resp.text[:50000].lower()

            for match in AI_PATTERN.finditer(html):
                indicator = match.group(0)
                if indicator not in found:
                    found.append(indicator)

        except Exception:
            pass

    return bool(found), found


async def _upsert_domain(
    supabase,
    domain: str,
    url: str,
    ai_indicators: list[str],
) -> str:
    """Vlož doménu do DB. Vrátí 'new', 'exists', nebo 'error'."""
    try:
        # Deduplikace dle domény
        existing = supabase.table("companies").select("id").ilike(
            "url", f"%{domain}%"
        ).limit(1).execute()

        if existing.data:
            return "exists"
    except Exception:
        pass

    try:
        insert_data = {
            "name": domain.split(".")[0].replace("-", " ").title(),
            "url": url,
            "scan_status": "pending",
            "prospecting_status": "found",
            "prospecting_source": "crt.sh",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        if ai_indicators:
            insert_data["prospecting_snippet"] = f"AI indikátory: {', '.join(ai_indicators[:5])}"
            # Priorita: weby s AI indikátory scanujeme dřív
            insert_data["prospecting_status"] = "ai_detected"

        supabase.table("companies").insert(insert_data).execute()
        return "new"

    except Exception as e:
        error_msg = str(e)
        if "duplicate" in error_msg.lower() or "409" in error_msg or "23505" in error_msg:
            return "exists"
        return "error"


async def phase_probe_cz_domains(
    limit: int = 1000,
    ai_only: bool = False,
    batch_size: int = 20,
) -> dict:
    """
    Hlavní fáze: stáhni .cz domény z crt.sh, probuj živé, ulož do DB.

    Args:
        limit: Max nových domén k přidání
        ai_only: Pokud True, uloží jen weby s AI indikátory
        batch_size: Počet souběžných DNS/HTTP kontrol

    Returns:
        dict se statistikami
    """
    from backend.database import get_supabase

    supabase = get_supabase()
    stats = {
        "domains_fetched": 0,
        "alive": 0,
        "has_web": 0,
        "has_ai": 0,
        "new_companies": 0,
        "duplicates": 0,
        "errors": 0,
    }

    # 1. Stáhni domény z crt.sh
    logger.info("[CZ Prober] Stahuji .cz domény z crt.sh...")

    # Používáme cílenější queries místo %.cz (ten vrací příliš mnoho)
    targeted_queries = [
        "%.shoptet.cz",       # Shoptet e-shopy
        "%.webnode.cz",       # Webnode weby
        "%.estranky.cz",      # eStránky weby
        "%.wz.cz",            # WZ hosting
        "%.ic.cz",            # IC hosting
    ]

    all_domains: set[str] = set()

    # Cílené queries (kvalitněji)
    for query in targeted_queries:
        batch = await fetch_crt_sh_domains(query, limit=2000)
        all_domains.update(batch)
        await asyncio.sleep(3.0)

    # Obecný .cz query (objemově)
    if len(all_domains) < limit * 2:
        general = await fetch_crt_sh_domains("%.cz", limit=limit * 3)
        all_domains.update(general)

    stats["domains_fetched"] = len(all_domains)
    logger.info(f"[CZ Prober] Celkem {len(all_domains)} unikátních domén")

    # 2. Probuj po dávkách
    domains_list = list(all_domains)
    new_count = 0

    for i in range(0, len(domains_list), batch_size):
        if new_count >= limit:
            break

        batch = domains_list[i:i + batch_size]

        # DNS check paralelně
        alive_tasks = [check_domain_alive(d) for d in batch]
        alive_results = await asyncio.gather(*alive_tasks, return_exceptions=True)

        alive_domains = [
            d for d, alive in zip(batch, alive_results)
            if alive is True
        ]
        stats["alive"] += len(alive_domains)

        # HTTP check paralelně
        web_tasks = [check_domain_has_web(d) for d in alive_domains]
        web_results = await asyncio.gather(*web_tasks, return_exceptions=True)

        for domain, web_url in zip(alive_domains, web_results):
            if new_count >= limit:
                break

            if not isinstance(web_url, str) or not web_url:
                continue

            stats["has_web"] += 1

            # Quick AI check
            has_ai, indicators = await quick_ai_check(web_url)
            if has_ai:
                stats["has_ai"] += 1

            if ai_only and not has_ai:
                continue

            outcome = await _upsert_domain(supabase, domain, web_url, indicators)
            if outcome == "new":
                stats["new_companies"] += 1
                new_count += 1
                tag = " [AI]" if has_ai else ""
                logger.info(f"[CZ Prober] NOVÁ: {domain}{tag}")
            elif outcome == "exists":
                stats["duplicates"] += 1
            else:
                stats["errors"] += 1

        # Loguj progress
        if (i // batch_size) % 10 == 0:
            logger.info(
                f"[CZ Prober] Progress: {i}/{len(domains_list)} domén, "
                f"{stats['new_companies']} nových, {stats['has_ai']} s AI"
            )

        await asyncio.sleep(0.5)

    logger.info(
        f"[CZ Prober] Hotovo: {stats['domains_fetched']} staženo, "
        f"{stats['alive']} živých, {stats['has_web']} s webem, "
        f"{stats['has_ai']} s AI, {stats['new_companies']} nových v DB"
    )
    return stats


async def import_cz_domains_to_db(limit: int = 500) -> dict:
    """Wrapper pro orchestrator."""
    return await phase_probe_cz_domains(limit=limit)
