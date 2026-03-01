"""
AIshield.cz — Smart Prospecting Pipeline v3

NOVÉ POŘADÍ (v3):
  1. GATHER    — Sesbírej firmy z katalogů (ARES, Heureka, Firmy.cz, Zboží.cz)
  2. EMAIL     — Najdi email (httpx regex → Playwright → Vision kaskáda)
  3. FILTR     — Nemá email? → SKIP. Nebudeme plýtvat scanem.
  4. SCAN      — Naskenuj web POUZE firmám, které mají email
  5. SCORE     — Ohodnoť lead (findings × závažnost)

Princip: Nejdřív ověř, že máme kam poslat. Pak teprve investuj do analýzy.

SLOUPCE V DB:
  email_source  — "regex" | "playwright" | "vision" | "not_found" | null
                  null = ještě nezkoušeno, "not_found" = zkoušeno bez výsledku
"""

import asyncio
from datetime import datetime
from backend.database import get_supabase


# ── Fáze 1: Získání firem z více zdrojů ──

async def phase_gather_companies(
    sources: list[str] | None = None,
    max_per_source: int = 100,
) -> dict:
    """
    Fáze 1: Stáhne firmy z katalogů.
    Uloží do DB se statusem scan_status='pending', prospecting_status='found'.
    """
    available_sources = sources or ["heureka", "ares", "firmy", "zbozi"]
    stats = {"total_new": 0, "by_source": {}}

    for source in available_sources:
        print(f"[Pipeline v3] Fáze 1 — zdroj: {source}")
        source_stats = {}

        try:
            if source == "shoptet":
                from backend.prospecting.shoptet import import_shoptet_to_db
                source_stats = await import_shoptet_to_db(max_pages_per_category=2)
            elif source == "heureka":
                from backend.prospecting.heureka import import_heureka_to_db
                source_stats = await import_heureka_to_db(max_pages_per_category=3)
            elif source == "ares":
                from backend.prospecting.pipeline import run_prospecting
                source_stats = await run_prospecting(max_per_nace=max_per_source // 5)
            elif source == "firmy":
                from backend.prospecting.firmy import import_firmy_to_db
                source_stats = await import_firmy_to_db(max_pages=2)
            elif source == "zbozi":
                from backend.prospecting.zbozi import import_zbozi_to_db
                source_stats = await import_zbozi_to_db(max_products=3)
        except Exception as e:
            print(f"[Pipeline v3] Chyba zdroje {source}: {e}")
            source_stats = {"error": str(e)}

        stats["by_source"][source] = source_stats
        stats["total_new"] += source_stats.get("new", 0) + source_stats.get("new_companies", 0)

    print(f"[Pipeline v3] Fáze 1 hotova: {stats['total_new']} nových firem")
    return stats


# ── Fáze 2: Najdi email — LEVNÉ (httpx + Playwright) ──

async def phase_find_emails(
    use_playwright: bool = True,
    use_vision: bool = False,
    limit: int = 100,
) -> dict:
    """
    Fáze 2: Pro VŠECHNY firmy s URL a bez emailu — najdi email.
    Kaskáda: regex scan → Playwright render → Claude Vision.

    LEVNÁ operace. Děláme PŘED scanem, protože nemá smysl
    skenovat web firmě, které pak nemáme kam poslat výsledek.

    email_source sleduje stav:
      null          → ještě nezkoušeno
      "not_found"   → zkoušeno, email nenalezen → PŘESKOČ
      "regex"/"playwright"/"vision" → nalezeno
    """
    from backend.prospecting.smart_email_finder import find_email_smart

    supabase = get_supabase()
    stats = {"searched": 0, "found": 0, "not_found": 0, "no_url": 0}

    # Firmy s URL, kde jsme ještě email NEHLEDALI (email_source je null)
    res = supabase.table("companies").select(
        "ico, url, name"
    ).is_(
        "email_source", "null"
    ).neq(
        "url", ""
    ).limit(limit).execute()

    companies = res.data or []
    print(f"[Pipeline v3] Fáze 2 — hledám emaily pro {len(companies)} firem...")

    for company in companies:
        url = company.get("url", "")
        ico = company.get("ico", "")
        name = company.get("name", "?")

        if not url:
            stats["no_url"] += 1
            continue

        stats["searched"] += 1

        try:
            result = await find_email_smart(
                url,
                use_playwright=use_playwright,
            )

            if result.email:
                update = {
                    "email": result.email,
                    "email_source": result.source,
                    "email_confidence": result.confidence,
                }
                if ico:
                    supabase.table("companies").update(update).eq("ico", ico).execute()
                else:
                    supabase.table("companies").update(update).eq("url", url).execute()
                stats["found"] += 1
                print(f"  ✅ {name} → {result.email} ({result.source}, {result.confidence:.0%})")
            else:
                update = {"email_source": "not_found"}
                if ico:
                    supabase.table("companies").update(update).eq("ico", ico).execute()
                else:
                    supabase.table("companies").update(update).eq("url", url).execute()
                stats["not_found"] += 1
                print(f"  ❌ {name} ({url}) — email nenalezen")

        except Exception as e:
            print(f"  ⚠️  {name}: chyba — {e}")
            stats["not_found"] += 1

        await asyncio.sleep(0.3)

    pct = f"{stats['found']}/{stats['searched']}" if stats["searched"] else "0/0"
    print(f"[Pipeline v3] Fáze 2 hotova: {pct} emailů nalezeno | {stats}")
    return stats


# ── Fáze 3: Skenování webů — JEN pro firmy S emailem ──

async def phase_scan_websites(limit: int = 50) -> dict:
    """
    Fáze 3: Naskenuj web POUZE firmám s potvrzeným emailem.
    DRAHÁ operace (Playwright + AI analýza) → jen pro kontaktovatelné firmy.
    """
    from backend.scanner.pipeline import run_scan_pipeline

    supabase = get_supabase()
    stats = {"scanned": 0, "with_findings": 0, "errors": 0}

    # KLÍČOVÉ: vyžadujeme email!
    res = supabase.table("companies").select(
        "id, ico, name, url, email"
    ).eq(
        "scan_status", "pending"
    ).neq(
        "url", ""
    ).neq(
        "email", ""
    ).not_.is_(
        "email", "null"
    ).limit(limit).execute()

    companies = res.data or []
    print(f"[Pipeline v3] Fáze 3 — skenování {len(companies)} webů (jen s emailem)...")

    for company in companies:
        url = company["url"]
        ico = company.get("ico", "")
        name = company.get("name", "?")
        email = company.get("email", "")

        try:
            # Vytvoř scan záznam v DB
            import uuid
            company_db_id = company.get("id", "")
            if not company_db_id:
                print(f"  ⚠️  {name}: chybí companies.id — přeskakuji")
                stats["errors"] += 1
                continue

            scan_id = str(uuid.uuid4())
            scan_insert = {
                "id": scan_id,
                "url_scanned": url,
                "url": url,
                "company_id": company_db_id,
                "status": "pending",
                "triggered_by": "lovec_pipeline",
            }
            supabase.table("scans").insert(scan_insert).execute()

            # Timeout ochrana — max 120s na jeden scan, aby se pipeline nezasekla
            try:
                scan_result = await asyncio.wait_for(
                    run_scan_pipeline(scan_id, url, company_db_id),
                    timeout=120.0,
                )
            except asyncio.TimeoutError:
                print(f"  ⏰ {name} ({url}): scan timeout po 120s — přeskakuji")
                supabase.table("scans").update({
                    "status": "error",
                    "error": "Timeout 120s — scan trval příliš dlouho",
                }).eq("id", scan_id).execute()
                supabase.table("companies").update({
                    "scan_status": "error",
                }).eq("id", company_db_id).execute()
                stats["errors"] += 1
                continue
            total_findings = scan_result.get("total_findings", 0)

            update = {
                "scan_status": "scanned",
                "last_scan_id": scan_id,
                "scanned_at": datetime.utcnow().isoformat(),
                "total_findings": total_findings,
            }

            if ico:
                supabase.table("companies").update(update).eq("ico", ico).execute()
            else:
                supabase.table("companies").update(update).eq("url", url).execute()

            stats["scanned"] += 1
            if total_findings > 0:
                stats["with_findings"] += 1
                print(f"  🔍 {name} — {total_findings} findings → email: {email}")
            else:
                print(f"  ✓  {name} — čistý web")

        except Exception as e:
            print(f"  ⚠️  {name} ({url}): scan chyba — {e}")
            stats["errors"] += 1
            update = {"scan_status": "scan_failed"}
            if ico:
                supabase.table("companies").update(update).eq("ico", ico).execute()
            else:
                supabase.table("companies").update(update).eq("url", url).execute()

    print(f"[Pipeline v3] Fáze 3 hotova: {stats}")
    return stats


# ── Fáze 4: Kvalifikace + Lead scoring ──

async def phase_qualify_leads() -> dict:
    """
    Fáze 4: Kvalifikuj naskenované firmy.
    qualified_hot = má AI findings
    qualified     = čistý web, ale AI Act se týká i interních nástrojů
    """
    supabase = get_supabase()
    stats = {"qualified": 0, "qualified_hot": 0}

    res = supabase.table("companies").select(
        "ico, url, total_findings"
    ).eq(
        "scan_status", "scanned"
    ).eq(
        "prospecting_status", "found"
    ).execute()

    companies = res.data or []

    for company in companies:
        ico = company.get("ico", "")
        url = company.get("url", "")
        findings = company.get("total_findings", 0)

        if findings > 0:
            new_status = "qualified_hot"
            stats["qualified_hot"] += 1
        else:
            new_status = "qualified"
            stats["qualified"] += 1

        if ico:
            supabase.table("companies").update({
                "prospecting_status": new_status,
            }).eq("ico", ico).execute()
        else:
            supabase.table("companies").update({
                "prospecting_status": new_status,
            }).eq("url", url).execute()

    total = stats["qualified"] + stats["qualified_hot"]
    print(f"[Pipeline v3] Fáze 4 hotova: {total} kvalifikovaných ({stats['qualified_hot']} hot)")
    return stats


# ── Kompletní pipeline v3 ──

async def run_smart_pipeline(
    gather: bool = True,
    find_emails: bool = True,
    scan: bool = True,
    qualify: bool = True,
    sources: list[str] | None = None,
    scan_limit: int = 50,
    email_limit: int = 100,
) -> dict:
    """
    Kompletní smart pipeline v3:
      1. GATHER     → sesbírej firmy z katalogů
      2. FIND EMAIL → najdi email (levné: regex + Playwright)
      3. SCAN       → skenuj web JEN firmám s emailem (drahé)
      4. QUALIFY    → ohodnoť leady (scoring)

    Princip: Nejdřív ověř kontakt, pak investuj do analýzy.
    """
    results = {}

    if gather:
        print("=" * 60)
        print("[Pipeline v3] FÁZE 1: Shromažďování firem z katalogů")
        print("=" * 60)
        results["gather"] = await phase_gather_companies(sources=sources)

    if find_emails:
        print("=" * 60)
        print("[Pipeline v3] FÁZE 2: Hledání emailů (levné)")
        print("=" * 60)
        results["emails"] = await phase_find_emails(limit=email_limit)

    if scan:
        print("=" * 60)
        print("[Pipeline v3] FÁZE 3: Skenování webů (jen s emailem)")
        print("=" * 60)
        results["scan"] = await phase_scan_websites(limit=scan_limit)

    if qualify:
        print("=" * 60)
        print("[Pipeline v3] FÁZE 4: Kvalifikace + scoring")
        print("=" * 60)
        results["qualify"] = await phase_qualify_leads()
        try:
            from backend.prospecting.lead_scoring import score_all_leads
            results["scoring"] = await score_all_leads()
        except ImportError:
            print("[Pipeline v3] Lead scoring modul nenalezen, přeskakuji")

    print("=" * 60)
    print(f"[Pipeline v3] HOTOVO: {results}")
    print("=" * 60)
    return results
