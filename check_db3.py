#!/usr/bin/env python3
"""Check questionnaire_responses and documents tables, and deep scan data."""
import json
from supabase import create_client

env = {}
for envfile in ["/opt/aishield/.env", "/opt/aishield/backend/.env"]:
    try:
        with open(envfile) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env[k] = v.strip().strip('"')
    except FileNotFoundError:
        pass

sb = create_client(env["SUPABASE_URL"], env["SUPABASE_SERVICE_ROLE_KEY"])

scan_id = "837ed6a5-0be5-4878-a3de-08d8c046a734"
company_id = "3900ae47-25d5-42fb-af4d-0d06623bc8cc"

# 1. questionnaire_responses
print("=== QUESTIONNAIRE_RESPONSES ===")
try:
    qr = sb.table("questionnaire_responses").select("*").eq("company_id", company_id).order("created_at", desc=True).limit(1).execute()
    if qr.data:
        r = qr.data[0]
        for k, v in r.items():
            if k in ("answers", "responses"):
                if isinstance(v, (dict, list)):
                    print(f"  {k}: {type(v).__name__} with {len(v)} items")
                    if isinstance(v, dict):
                        for ak in list(v.keys())[:8]:
                            print(f"    {ak}: {str(v[ak])[:100]}")
                    elif isinstance(v, list):
                        for item in v[:5]:
                            print(f"    {str(item)[:120]}")
                else:
                    print(f"  {k}: {str(v)[:200]}")
            else:
                val = str(v)[:120] if v else "None"
                print(f"  {k}: {val}")
    else:
        print("  No responses found!")
except Exception as e:
    print(f"  Error: {e}")

# 2. documents table - check without scan_id filter
print("\n=== DOCUMENTS (all for company) ===")
try:
    docs = sb.table("documents").select("*").eq("company_id", company_id).execute()
    if docs.data:
        for d in docs.data:
            for k, v in d.items():
                val = str(v)[:120] if v else "None"
                print(f"  {k}: {val}")
            print("  ---")
    else:
        print("  No documents found")
except Exception as e:
    print(f"  Documents error: {e}")
    # Try without company filter
    try:
        docs = sb.table("documents").select("*").limit(3).execute()
        if docs.data:
            print(f"  Table exists, columns: {list(docs.data[0].keys())}")
        else:
            print("  Table exists but empty")
    except Exception as e2:
        print(f"  Table check error: {e2}")

# 3. scan deep scan data (trackers_json full, findings)
print("\n=== DEEP SCAN DATA IN SCAN ===")
scan = sb.table("scans").select("*").eq("id", scan_id).execute()
if scan.data:
    s = scan.data[0]
    print(f"  deep_scan_status: {s.get('deep_scan_status')}")  
    print(f"  deep_scan_total_findings: {s.get('deep_scan_total_findings')}")
    trackers = s.get("trackers_json") or []
    print(f"  trackers_json: {len(trackers)} trackers")
    for t in trackers[:3]:
        print(f"    {t.get('name', '?')} [{t.get('category', '?')}]")
    # check for any deep scan json fields
    for k in s.keys():
        if "deep" in k.lower() or "finding" in k.lower() or "cookie" in k.lower():
            val = str(s[k])[:100]
            print(f"  {k}: {val}")

# 4. Check findings table
print("\n=== FINDINGS ===")
for tname in ["findings", "scan_findings", "cookie_findings", "tracker_findings"]:
    try:
        r = sb.table(tname).select("*").eq("scan_id", scan_id).limit(3).execute()
        if r.data:
            print(f"  {tname}: {len(r.data)} rows")
            print(f"    keys: {list(r.data[0].keys())}")
        else:
            print(f"  {tname}: empty for scan")
    except Exception as e:
        pass  # table doesn't exist

# 5. Check all scans - maybe there's a deep scan record
print("\n=== ALL SCANS FOR COMPANY ===")
scans = sb.table("scans").select("id, scan_type, status, deep_scan_status, created_at").eq("company_id", company_id).execute()
for s in scans.data:
    print(f"  {s['id']} | type={s.get('scan_type')} | status={s.get('status')} | deep={s.get('deep_scan_status')} | {s['created_at']}")
