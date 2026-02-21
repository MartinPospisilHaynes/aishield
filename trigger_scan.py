#!/usr/bin/env python3
"""One-shot script to trigger a deep scan job via ARQ."""
import asyncio
import os
from arq import create_pool
from arq.connections import RedisSettings

async def main():
    pool = await create_pool(RedisSettings.from_dsn(os.getenv("REDIS_URL", "redis://localhost:6379")))

    scan_id = "3416749d-0696-413d-b526-567f3970f520"
    url = "https://www.desperados-design.cz"
    company_id = "1dcff719-1e15-4e24-ad25-c4d8cdb017a2"

    from backend.database import get_supabase
    s = get_supabase()
    s.table("scans").update({
        "deep_scan_status": "pending",
        "deep_scan_started_at": None,
        "deep_scan_finished_at": None,
        "deep_scan_total_findings": None,
        "geo_countries_scanned": None,
    }).eq("id", scan_id).execute()
    print("Scan status reset to pending")

    job = await pool.enqueue_job("deep_scan_job", scan_id, url, company_id)
    print(f"Job enqueued: {job.job_id}")
    await pool.aclose()

if __name__ == "__main__":
    asyncio.run(main())
