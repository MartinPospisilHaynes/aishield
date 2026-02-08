"""
AIshield.cz — Prospecting Pipeline
Kompletní pipeline: ARES → URL finder → uložení do DB.
Plní databázi firmami připravenými ke skenování.
"""

import asyncio
from datetime import datetime
from backend.database import get_supabase
from backend.prospecting.ares import batch_search, RELEVANT_NACE
from backend.prospecting.url_finder import batch_find_urls


async def run_prospecting(
    nace_codes: list[str] | None = None,
    max_per_nace: int = 50,
    skip_existing: bool = True,
) -> dict:
    """
    Hlavní prospecting pipeline:
    1. ARES → firmy podle NACE kódů
    2. URL Finder → najdi web + email
    3. Ulož do Supabase (tabulka companies)

    Returns:
        Statistiky běhu (nalezeno, nové, s_webem, s_emailem)
    """
    supabase = get_supabase()
    stats = {
        "ares_found": 0,
        "new_companies": 0,
        "with_url": 0,
        "with_email": 0,
        "skipped_existing": 0,
        "errors": 0,
    }

    # 1. Hledání v ARES
    print("[Prospecting] Fáze 1: Hledání firem v ARES...")
    ares_companies = await batch_search(
        nace_codes=nace_codes or RELEVANT_NACE[:5],  # Začni s prvními 5 NACE
        max_per_nace=max_per_nace,
    )
    stats["ares_found"] = len(ares_companies)

    if not ares_companies:
        print("[Prospecting] Žádné firmy nalezeny v ARES")
        return stats

    # Filtrovat existující
    if skip_existing:
        existing_icos = set()
        for i in range(0, len(ares_companies), 100):
            batch_icos = [c.ico for c in ares_companies[i:i+100]]
            res = supabase.table("companies").select("ico").in_(
                "ico", batch_icos
            ).execute()
            existing_icos.update(r["ico"] for r in (res.data or []))

        new_companies = [c for c in ares_companies if c.ico not in existing_icos]
        stats["skipped_existing"] = len(ares_companies) - len(new_companies)
    else:
        new_companies = ares_companies

    if not new_companies:
        print("[Prospecting] Všechny firmy už jsou v DB")
        return stats

    print(f"[Prospecting] Fáze 2: Hledání webů pro {len(new_companies)} firem...")

    # 2. URL Finder (po dávkách)
    batch_size = 20
    all_web_infos = []

    for i in range(0, len(new_companies), batch_size):
        batch = new_companies[i:i+batch_size]
        company_dicts = [{"ico": c.ico, "name": c.name} for c in batch]
        web_infos = await batch_find_urls(company_dicts, concurrency=3)
        all_web_infos.extend(web_infos)
        print(f"  [{i+len(batch)}/{len(new_companies)}] zpracováno")

    # 3. Uložit do DB
    print("[Prospecting] Fáze 3: Ukládání do databáze...")
    web_info_map = {w.ico: w for w in all_web_infos}

    for company in new_companies:
        web = web_info_map.get(company.ico)
        url = web.url if web else None
        email = web.email if web else None

        if url:
            stats["with_url"] += 1
        if email:
            stats["with_email"] += 1

        try:
            supabase.table("companies").upsert({
                "ico": company.ico,
                "name": company.name,
                "url": url or "",
                "email": email or "",
                "legal_form": company.legal_form,
                "nace_codes": company.nace,
                "address": company.address,
                "region": company.region,
                "source": "ares_prospecting",
                "prospecting_status": "found" if url else "no_url",
                "scan_status": "pending" if url else "skipped",
                "created_at": datetime.utcnow().isoformat(),
            }, on_conflict="ico").execute()
            stats["new_companies"] += 1
        except Exception as e:
            print(f"[Prospecting] Chyba při ukládání {company.ico}: {e}")
            stats["errors"] += 1

    print(f"[Prospecting] Hotovo: {stats}")
    return stats


async def get_companies_to_scan(limit: int = 50) -> list[dict]:
    """Vrátí firmy z DB, které mají URL ale ještě nebyly skenovány."""
    supabase = get_supabase()
    res = supabase.table("companies").select("*").eq(
        "scan_status", "pending"
    ).neq("url", "").limit(limit).execute()
    return res.data or []


async def mark_company_scanned(ico: str, scan_id: str):
    """Označí firmu jako naskenovanou."""
    supabase = get_supabase()
    supabase.table("companies").update({
        "scan_status": "scanned",
        "last_scan_id": scan_id,
        "scanned_at": datetime.utcnow().isoformat(),
    }).eq("ico", ico).execute()
