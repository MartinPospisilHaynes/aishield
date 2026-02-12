"""
AIshield.cz — Data Retention & Automatic Cleanup
Automatické mazání starých dat dle GDPR data minimization.

Spouští se cronem denně:
  0 4 * * * cd /opt/aishield && venv/bin/python3 -m backend.security.data_cleanup

Politika:
  - Nekompletní registrace (bez skenu): smazat po 30 dnech
  - Starý orchestrator_log: smazat po 30 dnech (existující)
  - Staré email_events: smazat po 90 dnech
  - Audit log: smazat po 365 dnech

Zákaznická data (dotazníky, skeny, findings) se NEMAŽOU automaticky.
Ty spravuje admin přes export + manuální smazání.
"""

import logging
from datetime import datetime, timedelta, timezone

from backend.database import get_supabase
from backend.security import log_access

logger = logging.getLogger(__name__)


async def run_cleanup() -> dict:
    """
    Spustí všechny cleanup úlohy. Vrátí report.
    """
    supabase = get_supabase()
    now = datetime.now(timezone.utc)
    report = {}

    # 1. Orchestrator log > 30 dní
    cutoff_30d = (now - timedelta(days=30)).isoformat()
    try:
        res = supabase.table("orchestrator_log").delete().lt("started_at", cutoff_30d).execute()
        count = len(res.data) if res.data else 0
        report["orchestrator_log"] = f"smazáno {count} záznamů starších 30 dní"
        logger.info(f"[Cleanup] orchestrator_log: {count} smazáno")
    except Exception as e:
        report["orchestrator_log"] = f"chyba: {e}"
        logger.warning(f"[Cleanup] orchestrator_log error: {e}")

    # 2. Email events > 90 dní
    cutoff_90d = (now - timedelta(days=90)).isoformat()
    try:
        res = supabase.table("email_events").delete().lt("created_at", cutoff_90d).execute()
        count = len(res.data) if res.data else 0
        report["email_events"] = f"smazáno {count} záznamů starších 90 dní"
        logger.info(f"[Cleanup] email_events: {count} smazáno")
    except Exception as e:
        report["email_events"] = f"chyba: {e}"
        logger.warning(f"[Cleanup] email_events error: {e}")

    # 3. Audit log > 365 dní (samotný audit log musí mít retenci)
    cutoff_365d = (now - timedelta(days=365)).isoformat()
    try:
        res = supabase.table("data_access_log").delete().lt("created_at", cutoff_365d).execute()
        count = len(res.data) if res.data else 0
        report["data_access_log"] = f"smazáno {count} záznamů starších 365 dní"
        logger.info(f"[Cleanup] data_access_log: {count} smazáno")
    except Exception as e:
        report["data_access_log"] = f"chyba: {e}"
        logger.warning(f"[Cleanup] data_access_log error: {e}")

    # 4. Neaktivní firmy bez skenu > 30 dní (registrace bez aktivity)
    try:
        # Firmy, které nemají žádný sken a jsou starší 30 dní
        old_companies = supabase.table("companies") \
            .select("id, name, url, email, created_at") \
            .is_("last_scanned_at", "null") \
            .lt("created_at", cutoff_30d) \
            .execute()

        inactive_count = 0
        for comp in (old_companies.data or []):
            cid = comp["id"]
            # Ověř, že opravdu nemá skeny
            scans = supabase.table("scans").select("id").eq("company_id", cid).limit(1).execute()
            if scans.data:
                continue  # má sken, přeskočit

            # Smaž dependentní záznamy
            clients = supabase.table("clients").select("id").eq("company_id", cid).execute()
            for cl in (clients.data or []):
                supabase.table("questionnaire_responses").delete().eq("client_id", cl["id"]).execute()
            supabase.table("clients").delete().eq("company_id", cid).execute()
            supabase.table("companies").delete().eq("id", cid).execute()
            inactive_count += 1

        report["inactive_companies"] = f"smazáno {inactive_count} neaktivních firem (bez skenu, >30 dní)"
        logger.info(f"[Cleanup] inactive companies: {inactive_count} smazáno")
    except Exception as e:
        report["inactive_companies"] = f"chyba: {e}"
        logger.warning(f"[Cleanup] inactive companies error: {e}")

    # Zalogovat cleanup do audit logu
    try:
        await log_access(
            actor_email="system@aishield.cz",
            action="delete",
            resource_type="cleanup",
            resource_detail="Automatický data retention cleanup",
            actor_role="system",
            metadata=report,
        )
    except Exception:
        pass

    return {
        "status": "completed",
        "timestamp": now.isoformat(),
        "report": report,
    }


# CLI entry point: python3 -m backend.security.data_cleanup
if __name__ == "__main__":
    import asyncio

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    result = asyncio.run(run_cleanup())
    print(f"\n✅ Cleanup dokončen:")
    for key, val in result["report"].items():
        print(f"  {key}: {val}")
