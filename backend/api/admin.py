"""
AIshield.cz — Admin API
Přehledový dashboard a manuální ovládání orchestrátoru.
"""

from fastapi import APIRouter, HTTPException
from backend.outbound.orchestrator import get_stats, run_task, SCHEDULE

router = APIRouter()


@router.get("/stats")
async def admin_stats():
    """Vrátí přehledové statistiky pro admin dashboard."""
    try:
        stats = await get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run/{task_name}")
async def admin_run_task(task_name: str):
    """Manuálně spustí úlohu orchestrátoru."""
    if task_name not in SCHEDULE:
        raise HTTPException(
            status_code=400,
            detail=f"Neznámá úloha: {task_name}. Dostupné: {list(SCHEDULE.keys())}",
        )
    result = await run_task(task_name)
    return result


@router.get("/email-log")
async def admin_email_log(limit: int = 50):
    """Vrátí posledních N odeslaných emailů."""
    from backend.database import get_supabase
    supabase = get_supabase()

    res = supabase.table("email_log").select(
        "*"
    ).order("sent_at", desc=True).limit(limit).execute()

    return {"emails": res.data or [], "total": len(res.data or [])}


@router.get("/companies")
async def admin_companies(status: str = "all", limit: int = 50):
    """Vrátí přehled firem z prospecting DB."""
    from backend.database import get_supabase
    supabase = get_supabase()

    query = supabase.table("companies").select("*")

    if status != "all":
        query = query.eq("scan_status", status)

    res = query.order("created_at", desc=True).limit(limit).execute()

    return {"companies": res.data or [], "total": len(res.data or [])}
