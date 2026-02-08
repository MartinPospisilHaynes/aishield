"""
AIshield.cz — Outbound Orchestrátor
Cron schedule pro Wedos VPS:
  03:00 — PRIORITNÍ: Skenuj nasmlouvané klienty (monitoring)
  04:00 — PROSPECTING: Načti nové firmy z ARES
  05:00 — SCANNING: Skenuj nové firmy z prospecting fronty
  08:00 — EMAILING: Pošli emaily naskenovaným firmám
  20:00 — REPORTING: Měsíční reporty (1. den v měsíci)
"""

import asyncio
from datetime import datetime, timedelta

from backend.database import get_supabase
from backend.prospecting.pipeline import run_prospecting, get_companies_to_scan
from backend.outbound.email_engine import run_email_campaign


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
    """03:00 — Skenuj nasmlouvané klienty (rescan)."""
    from backend.scanner import run_scan
    supabase = get_supabase()

    # Najdi firmy s aktivním předplatným (paid orders)
    res = supabase.table("orders").select(
        "user_email"
    ).eq("status", "paid").execute()

    emails = list(set(row["user_email"] for row in (res.data or [])))
    scanned = 0

    for email in emails:
        comp_res = supabase.table("companies").select("url").eq(
            "email", email
        ).limit(1).execute()
        if comp_res.data and comp_res.data[0].get("url"):
            url = comp_res.data[0]["url"]
            try:
                await run_scan(url)
                scanned += 1
            except Exception as e:
                print(f"[Monitoring] Chyba při skenu {url}: {e}")

    return {"scanned_clients": scanned}


async def task_prospecting():
    """04:00 — Načti nové firmy z ARES."""
    result = await run_prospecting(max_companies=100)
    return result


async def task_scanning():
    """05:00 — Skenuj nové firmy z prospecting fronty."""
    from backend.scanner import run_scan
    companies = await get_companies_to_scan(limit=50)
    scanned = 0
    errors = 0

    for company in companies:
        url = company.get("url", "")
        if not url:
            continue
        try:
            await run_scan(url)
            # Označ jako naskenovanou
            supabase = get_supabase()
            supabase.table("companies").update({
                "scan_status": "scanned",
            }).eq("ico", company["ico"]).execute()
            scanned += 1
        except Exception as e:
            errors += 1
            print(f"[Scanning] Chyba při skenu {url}: {e}")

    return {"scanned": scanned, "errors": errors}


async def task_emailing():
    """08:00 — Pošli emaily naskenovaným firmám."""
    result = await run_email_campaign(dry_run=False, limit=100)
    return result


async def task_reporting():
    """20:00 — Měsíční reporty (1. den v měsíci)."""
    today = datetime.utcnow()
    if today.day != 1:
        return {"skipped": True, "reason": "Not 1st day of month"}

    stats = await get_stats()
    # TODO: odeslat měsíční report emailem adminovi
    return {"report_generated": True, "stats_snapshot": stats}


# ── Hlavní orchestrátor ──

SCHEDULE = {
    "monitoring": task_monitoring,
    "prospecting": task_prospecting,
    "scanning": task_scanning,
    "emailing": task_emailing,
    "reporting": task_reporting,
}


async def run_task(task_name: str) -> dict:
    """Spustí konkrétní úlohu a zaloguje výsledek."""
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
        return {"task": task_name, "status": "failed", "error": error_msg}


async def run_all_tasks():
    """Spustí všechny úlohy v pořadí (pro manuální spuštění)."""
    results = []
    for name in ["monitoring", "prospecting", "scanning", "emailing", "reporting"]:
        result = await run_task(name)
        results.append(result)
    return results


# ── CLI vstupní bod pro cron ──

def main():
    """
    Vstupní bod pro cron:
    python -m backend.outbound.orchestrator [task_name]

    Crontab na VPS:
    0 3 * * * cd /opt/aishield && python -m backend.outbound.orchestrator monitoring
    0 4 * * * cd /opt/aishield && python -m backend.outbound.orchestrator prospecting
    0 5 * * * cd /opt/aishield && python -m backend.outbound.orchestrator scanning
    0 8 * * * cd /opt/aishield && python -m backend.outbound.orchestrator emailing
    0 20 * * * cd /opt/aishield && python -m backend.outbound.orchestrator reporting
    """
    import sys

    if len(sys.argv) < 2:
        print("Použití: python -m backend.outbound.orchestrator <task_name>")
        print(f"Dostupné úlohy: {', '.join(SCHEDULE.keys())}")
        sys.exit(1)

    task_name = sys.argv[1]
    result = asyncio.run(run_task(task_name))
    print(result)


if __name__ == "__main__":
    main()
