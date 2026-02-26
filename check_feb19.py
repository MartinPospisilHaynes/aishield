#!/usr/bin/env python3
"""Check what happened on Feb 19 — which components consumed tokens."""
import os, sys
sys.path.insert(0, ".")
from dotenv import load_dotenv
load_dotenv(".env")
from backend.config import get_settings
s = get_settings()
from supabase import create_client
sb = create_client(s.supabase_url, s.supabase_service_role_key)

# Scans on Feb 19
resp = sb.table("scans").select("id,company_id,status,created_at").gte("created_at", "2026-02-19T00:00:00").lt("created_at", "2026-02-20T00:00:00").order("created_at").execute()
print(f"=== Scans on Feb 19: {len(resp.data)} ===")
for r in resp.data:
    print(f"  {r['created_at'][:19]} | status={str(r.get('status','?')):12s} | company={r['company_id'][:36]}")

# MART1N conversations on Feb 19
resp2 = sb.table("mart1n_conversations").select("id,company_id,role,created_at").gte("created_at", "2026-02-19T00:00:00").lt("created_at", "2026-02-20T00:00:00").order("created_at").execute()
print(f"\n=== MART1N messages on Feb 19: {len(resp2.data)} ===")
for r in resp2.data:
    print(f"  {r['created_at'][:19]} | {r['role']:10s} | company={r['company_id'][:36]}")

# Findings on Feb 19
resp3 = sb.table("findings").select("id,scan_id,created_at,category,severity").gte("created_at", "2026-02-19T00:00:00").lt("created_at", "2026-02-20T00:00:00").order("created_at").execute()
print(f"\n=== Findings on Feb 19: {len(resp3.data)} ===")
for r in resp3.data:
    print(f"  {r['created_at'][:19]} | {r.get('category','?'):20s} | severity={r.get('severity','?')} | scan={r['scan_id'][:20]}")

# All scans ever
resp4 = sb.table("scans").select("id,company_id,status,created_at").order("created_at").execute()
print(f"\n=== All scans ever: {len(resp4.data)} ===")
for r in resp4.data:
    print(f"  {r['created_at'][:19]} | status={str(r.get('status','?')):12s} | company={r['company_id'][:36]}")
