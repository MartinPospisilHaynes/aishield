"""
AIshield.cz — Outbound Orchestrátor v2 (Continuous Mode)
=========================================================
Běží NONSTOP jako daemon — ne jednorázový cron.

Cyklus (každé 2 hodiny v pracovní dny):
  1. PROSPECTING: Načti nové firmy z ARES/Shoptet/Heureka
  2. SCANNING: Skenuj nové firmy
  3. QUALIFY + SCORE: Kvalifikuj a ohodnoť leady
  4. FIND EMAILS: Najdi emaily pro kvalifikované firmy
  5. EMAILING: Pošli dávku emailů (s náhodným zpožděním)
  6. WAIT: Počkej do dalšího cyklu

Email rozesílka: průběžně 8:00-17:00 CET (Po-Pá)
Prospecting/scanning: 24/7 (neomezeno pracovní dobou)
"""

import asyncio
from datetime import datetime, timedelta

from backend.database import get_supabase
from backend.prospecting.pipeline import run_prospecting, get_companies_to_scan
from backend.prospecting.smart_pipeline import (
    phase_gather_companies,
    phase_scan_websites,
    phase_qualify_leads,
    phase_find_emails,
)
from backend.outbound.email_engine import run_email_campaign, is_sending_allowed
from backend.outbound.response_checker import run_response_check

# ══════════════════════════════════════════════════════════════
# ⛔ PIPELINE POZASTAVENA — zapnout až bude celá pipeline hotová
# Nastavit na True pro spuštění prospectingu, scanningu a emailů.
# ══════════════════════════════════════════════════════════════
PIPELINE_ENABLED = True

# ── AGRESIVNÍ LIMITY ──

# Prospecting: kolik firem načíst za cyklus (z každého zdroje)
PROSPECT_PER_SOURCE = 50         # 50 × 3 zdroje = 150/cyklus
PROSPECT_SOURCES = ["heureka", "ares", "firmy", "zbozi"]  # 4 aktivní zdroje

# Scanning: kolik webů skenovat za cyklus
SCAN_LIMIT = 30                  # 30/cyklus × ~8 cyklů = 240/den

# Email finding: kolik emailů hledat za cyklus
EMAIL_FIND_LIMIT = 25            # 25/cyklus × ~8 cyklů = 200/den

# Emailing: kolik emailů odeslat za cyklus
EMAIL_BATCH_SIZE = 40            # Adaptivní limit toto dále omezí

# Cyklus: jak často opakovat (minuty)
CYCLE_INTERVAL_MINUTES = 90      # Každých 90 minut = ~6× za pracovní den

# Noční cyklus (prospecting + scanning bez emailů)
NIGHT_CYCLE_MINUTES = 180        # Každé 3 hodiny v noci


# ── Statistiky ──


async def get_stats() -> dict:
    """Vrátí přehledové statistiky pro admin dashboard."""
    supabase = get_supabase()
    today = datetime.utcnow().date().isoformat()
    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()

    # Celkové počty
    companies_res = supabase.table("companies").select(
        "id", count="exact"
    ).execute()

    scanned_res = supabase.table("companies").select(
        "id", count="exact"
    ).eq("scan_status", "scanned").execute()

    emails_today_res = supabase.table("email_log").select(
        "id", count="exact"
    ).gte("sent_at", today).execute()

    emails_total_res = supabase.table("email_log").select(
        "id", count="exact"
    ).execute()

    orders_res = supabase.table("orders").select(
        "id", count="exact"
    ).eq("status", "paid").execute()

    # Konverzní poměr (emaily → objednávky)
    total_emails = emails_total_res.count or 0
    total_orders = orders_res.count or 0
    conversion = (total_orders / total_emails * 100) if total_emails > 0 else 0

    # Poslední logy
    logs_res = supabase.table("orchestrator_log").select(
        "*"
    ).order("started_at", desc=True).limit(20).execute()

    return {
        "companies_total": companies_res.count or 0,
        "companies_scanned": scanned_res.count or 0,
        "emails_today": emails_today_res.count or 0,
        "emails_total": total_emails,
        "orders_paid": total_orders,
        "conversion_pct": round(conversion, 2),
        "recent_logs": logs_res.data or [],
    }


async def log_task(
    task_name: str,
    status: str,
    result: dict | None = None,
    error: str | None = None,
) -> None:
    """Zaloguje běh úlohy do DB."""
    supabase = get_supabase()
    supabase.table("orchestrator_log").insert({
        "task_name": task_name,
        "status": status,
        "result": result,
        "error": error,
        "started_at": datetime.utcnow().isoformat(),
    }).execute()


# ── Jednotlivé úlohy ──


async def task_monitoring():
    """Skenuj nasmluvné klienty + diff + alerty. (Jednou denně stačí)"""
    from backend.monitoring.alert_system import run_monitoring_with_alerts
    return await run_monitoring_with_alerts()


async def task_prospecting():
    """Načti nové firmy ze VŠECH zdrojů — každý cyklus."""
    result = await phase_gather_companies(
        sources=PROSPECT_SOURCES,
        max_per_source=PROSPECT_PER_SOURCE,
    )
    return result


async def task_scanning():
    """Skenuj nové firmy + kvalifikuj + score — každý cyklus."""
    scan_result = await phase_scan_websites(limit=SCAN_LIMIT)
    qualify_result = await phase_qualify_leads()
    from backend.prospecting.lead_scoring import score_all_leads
    scoring_result = await score_all_leads()
    return {
        "scan": scan_result,
        "qualify": qualify_result,
        "scoring": scoring_result,
    }


async def task_find_emails():
    """Najdi emaily pro kvalifikované firmy — každý cyklus."""
    result = await phase_find_emails(
        use_playwright=True,
        use_vision=False,
        limit=EMAIL_FIND_LIMIT,
    )
    return result


async def task_emailing():
    """Pošli dávku emailů — POUZE v pracovní hodiny."""
    can_send, reason = is_sending_allowed()
    if not can_send:
        return {"skipped": True, "reason": reason}
    result = await run_email_campaign(dry_run=False, limit=EMAIL_BATCH_SIZE)
    return result


async def task_check_responses():
    """Zkontroluj příchozí odpovědi — IMAP + Resend eventy."""
    result = await run_response_check()
    return result


async def task_reporting():
    """20:00 — Měsíční reporty (1. den v měsíci)."""
    today = datetime.utcnow()
    if today.day != 1:
        return {"skipped": True, "reason": "Not 1st day of month"}

    from backend.monitoring.alert_system import send_monthly_report
    supabase = get_supabase()

    # Všichni platící klienti
    orders = supabase.table("orders").select(
        "user_email"
    ).eq("status", "paid").execute()

    unique_emails = list(set(row["user_email"] for row in (orders.data or [])))
    sent = 0

    for email in unique_emails:
        comp = supabase.table("companies").select("id").eq(
            "email", email
        ).limit(1).execute()
        if comp.data:
            await send_monthly_report(comp.data[0]["id"], email)
            sent += 1

    return {"monthly_reports_sent": sent}


# ── Hlavní orchestrátor ──

SCHEDULE = {
    "monitoring": task_monitoring,
    "prospecting": task_prospecting,
    "scanning": task_scanning,
    "find_emails": task_find_emails,
    "emailing": task_emailing,
    "reporting": task_reporting,
    "check_responses": task_check_responses,
}


async def run_task(task_name: str) -> dict:
    """Spustí konkrétní úlohu a zaloguje výsledek."""
    if not PIPELINE_ENABLED:
        return {"task": task_name, "status": "skipped", "reason": "Pipeline pozastavena (PIPELINE_ENABLED=False)"}

    if task_name not in SCHEDULE:
        return {"error": f"Neznámá úloha: {task_name}"}

    task_fn = SCHEDULE[task_name]
    print(f"[Orchestrátor] Spouštím: {task_name}")
    await log_task(task_name, "running")

    try:
        result = await task_fn()
        await log_task(task_name, "completed", result=result)
        print(f"[Orchestrátor] Hotovo: {task_name} → {result}")
        return {"task": task_name, "status": "completed", "result": result}
    except Exception as e:
        error_msg = str(e)
        await log_task(task_name, "failed", error=error_msg)
        print(f"[Orchestrátor] Chyba: {task_name} → {error_msg}")

        # Alert email při selhání pipeline fáze
        try:
            from backend.outbound.email_engine import send_email
            await send_email(
                to="martin@aishield.cz",
                subject=f"⚠️ LOVEC pipeline selhání: {task_name}",
                html=(
                    f"<h3>Pipeline úloha <code>{task_name}</code> selhala</h3>"
                    f"<p><strong>Chyba:</strong> {error_msg}</p>"
                    f"<p><strong>Čas:</strong> {datetime.utcnow().isoformat()} UTC</p>"
                    f"<hr><small>Automatická zpráva z LOVEC orchestrátoru</small>"
                ),
                from_email="info@aishield.cz",
                from_name="AIshield LOVEC",
            )
        except Exception:
            pass  # Selhání alertu nesmí shodit pipeline

        return {"task": task_name, "status": "failed", "error": error_msg}


async def run_all_tasks():
    """Spustí všechny úlohy v pořadí (pro manuální spuštění)."""
    results = []
    for name in ["monitoring", "prospecting", "scanning", "find_emails", "emailing", "reporting"]:
        result = await run_task(name)
        results.append(result)
    return results


# ── Continuous Pipeline Cycle ──


async def run_cycle() -> dict:
    """
    Jeden cyklus pipeline v3:
    1. GATHER     — Sesbírej firmy z katalogů
    2. FIND EMAIL — Najdi emaily (levné: httpx + Perplexity + Playwright)
    3. SCAN       — Skenuj web JEN firmám s emailem (drahé)
    4. QUALIFY    — Ohodnoť leady (scoring)
    5. EMAILING   — Pošli dávku emailů (jen v pracovní hodiny)

    v3 princip: Nejdřív ověř kontakt, pak investuj do analýzy.
    """
    # ⛔ DOUBLE SAFETY: Pipeline musí být explicitně povolena
    if not PIPELINE_ENABLED:
        print("[Cyklus] ⛔ PIPELINE_ENABLED = False → přeskakuji celý cyklus")
        return {"skipped": True, "reason": "PIPELINE_ENABLED = False"}

    cycle_start = datetime.utcnow()
    cycle_results = {}

    # Fáze 1: GATHER — Sesbírej firmy z katalogů
    print("\n" + "=" * 60)
    print(f"[Cyklus {cycle_start.strftime('%H:%M')}] Fáze 1/5: GATHER (prospecting)")
    print("=" * 60)
    cycle_results["prospecting"] = await run_task("prospecting")

    # Fáze 2: FIND EMAIL — Levná operace PŘED scanem
    print(f"[Cyklus] Fáze 2/5: FIND EMAILS (kaskáda)")
    cycle_results["find_emails"] = await run_task("find_emails")

    # Fáze 3: SCAN — Jen firmy s emailem (drahé → šetříme)
    print(f"[Cyklus] Fáze 3/5: SCANNING + QUALIFY")
    cycle_results["scanning"] = await run_task("scanning")

    # Fáze 4: QUALIFY + SCORE
    # (task_scanning() už volá phase_qualify_leads + score_all_leads)

    # Fáze 5: EMAILING (jen v pracovní hodiny)
    print(f"[Cyklus] Fáze 4/5: EMAILING")
    cycle_results["emailing"] = await run_task("emailing")

    # Fáze 6: RESPONSE CHECK
    print(f"[Cyklus] Fáze 6/6: RESPONSE CHECK")
    cycle_results["check_responses"] = await run_task("check_responses")

    # Shrnutí
    cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()
    print(f"\n[Cyklus] Dokončen za {cycle_duration:.0f}s")

    return {
        "cycle_start": cycle_start.isoformat(),
        "duration_seconds": cycle_duration,
        "results": cycle_results,
    }


async def run_continuous():
    """
    🔄 NONSTOP DAEMON — hlavní smyčka orchestrátoru.

    - Ve dne (8-17 CET, Po-Pá): plný cyklus každých 90 minut
      (prospecting + scanning + emails)
    - V noci / víkend: jen prospecting + scanning každé 3 hodiny
      (budujeme zásobu leadů pro příští den)

    Monitoring: jednou denně ve 3:00
    Reporting: 1. den v měsíci ve 20:00
    """
    print("=" * 60)
    print("🚀 AIshield Orchestrátor v2 — CONTINUOUS MODE")
    if not PIPELINE_ENABLED:
        print("   ⛔ PIPELINE POZASTAVENA — žádné úlohy se nespouštějí")
        print("   → Zapnout: PIPELINE_ENABLED = True v orchestrator.py")
    print(f"   Cyklus: {CYCLE_INTERVAL_MINUTES}min (den) / {NIGHT_CYCLE_MINUTES}min (noc)")
    print(f"   Prospecting: {PROSPECT_PER_SOURCE}/zdroj × {len(PROSPECT_SOURCES)} zdroje")
    print(f"   Scanning: {SCAN_LIMIT}/cyklus")
    print(f"   Email batch: {EMAIL_BATCH_SIZE}/cyklus (adaptivní)")
    print("=" * 60)

    last_monitoring = None
    last_reporting = None

    while True:
        now = datetime.utcnow()
        hour = now.hour
        day = now.day

        # Monitoring: jednou denně kolem 3:00 UTC (4:00 CET)
        if (last_monitoring is None or
                (now - last_monitoring).total_seconds() > 86400) and hour == 3:
            print("\n[Daemon] 🔍 Spouštím denní monitoring...")
            await run_task("monitoring")
            last_monitoring = now

        # Reporting: 1. den v měsíci ve 20:00 UTC
        if (last_reporting is None or
                (now - last_reporting).total_seconds() > 86400) and day == 1 and hour == 20:
            print("\n[Daemon] 📊 Spouštím měsíční reporting...")
            await run_task("reporting")
            last_reporting = now

        # Hlavní cyklus
        try:
          can_send, _ = is_sending_allowed()
        except Exception as e:
          print(f"[Daemon] ⚠️ Chyba v is_sending_allowed: {e}")
          can_send = False
        if can_send:
            # Denní režim: plný cyklus (prospecting + scanning + emaily)
            print(f"\n[Daemon] ☀️  Denní cyklus ({now.strftime('%H:%M')} UTC)")
            await run_cycle()
            wait_minutes = CYCLE_INTERVAL_MINUTES
        else:
            # Noční režim v3: gather + find_emails + scanning (buduj zásobu)
            print(f"\n[Daemon] 🌙 Noční cyklus ({now.strftime('%H:%M')} UTC)")
            await run_task("prospecting")
            await run_task("find_emails")   # Před scanem — v3 pořadí
            await run_task("scanning")
            await run_task("check_responses")
            wait_minutes = NIGHT_CYCLE_MINUTES

        print(f"[Daemon] 💤 Čekám {wait_minutes} minut do dalšího cyklu...")
        try:
            await asyncio.sleep(wait_minutes * 60)
        except asyncio.CancelledError:
            print("[Daemon] ⛔ Daemon zastaven (CancelledError)")
            break


# ── CLI vstupní bod ──

def main():
    """
    Vstupní bod:
    python -m backend.outbound.orchestrator              → CONTINUOUS MODE (daemon)
    python -m backend.outbound.orchestrator <task_name>  → single task
    python -m backend.outbound.orchestrator cycle        → jeden cyklus
    python -m backend.outbound.orchestrator all          → všechny úlohy jednou
    """
    import sys

    if len(sys.argv) < 2:
        # Bez argumentu = CONTINUOUS MODE
        print("Spouštím CONTINUOUS MODE (daemon)...")
        asyncio.run(run_continuous())
        return

    task_name = sys.argv[1]

    if task_name == "cycle":
        result = asyncio.run(run_cycle())
        print(result)
    elif task_name == "all":
        results = asyncio.run(run_all_tasks())
        print(results)
    elif task_name == "continuous":
        asyncio.run(run_continuous())
    elif task_name in SCHEDULE:
        result = asyncio.run(run_task(task_name))
        print(result)
    else:
        print(f"Neznámá úloha: {task_name}")
        print(f"Dostupné: {', '.join(SCHEDULE.keys())}, cycle, all, continuous")
        sys.exit(1)


if __name__ == "__main__":
    main()
