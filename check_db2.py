#!/usr/bin/env python3
"""Check scan table structure and data."""
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

# 1. Scan data
print("=== SCAN ===")
scan = sb.table("scans").select("*").eq("id", scan_id).execute()
if scan.data:
    s = scan.data[0]
    for k, v in s.items():
        val = str(v)[:150] if v else "None"
        print(f"  {k}: {val}")
else:
    print("  No scan found!")

# 2. Scan results (separate table?)
print("\n=== SCAN_RESULTS ===")
try:
    sr = sb.table("scan_results").select("*").eq("scan_id", scan_id).execute()
    if sr.data:
        print(f"  Found {len(sr.data)} results")
        for r in sr.data[:3]:
            for k, v in r.items():
                val = str(v)[:150] if v else "None"
                print(f"    {k}: {val}")
            print("    ---")
    else:
        print("  No scan_results found")
except Exception as e:
    print(f"  Error: {e}")

# 3. Questionnaire answers
print("\n=== QUESTIONNAIRE_ANSWERS ===")
try:
    qa = sb.table("questionnaire_answers").select("*").eq("company_id", company_id).order("created_at", desc=True).limit(1).execute()
    if qa.data:
        a = qa.data[0]
        for k, v in a.items():
            if k == "answers":
                if isinstance(v, dict):
                    print(f"  answers: {len(v)} entries")
                    for ak in list(v.keys())[:5]:
                        print(f"    {ak}: {str(v[ak])[:80]}")
                elif isinstance(v, list):
                    print(f"  answers: {len(v)} items")
                    for item in v[:3]:
                        print(f"    {str(item)[:100]}")
                else:
                    print(f"  answers: {str(v)[:200]}")
            else:
                val = str(v)[:150] if v else "None"
                print(f"  {k}: {val}")
    else:
        print("  No answers found")
except Exception as e:
    print(f"  Error: {e}")

# 4. Documents table
print("\n=== DOCUMENTS ===")
try:
    docs = sb.table("documents").select("*").eq("scan_id", scan_id).execute()
    if docs.data:
        for d in docs.data:
            for k, v in d.items():
                val = str(v)[:150] if v else "None"
                print(f"  {k}: {val}")
            print("  ---")
    else:
        print("  No documents found for this scan")
except Exception as e:
    print(f"  Error: {e}")

# 5. Check all tables in schema
print("\n=== ALL TABLES CHECK ===")
for table_name in ["deep_scan_results", "analysis_results", "risk_assessments", "ai_systems"]:
    try:
        r = sb.table(table_name).select("*").eq("scan_id", scan_id).limit(1).execute()
        if r.data:
            print(f"  {table_name}: {len(r.data)} rows, keys={list(r.data[0].keys())}")
        else:
            print(f"  {table_name}: exists but empty for this scan")
    except Exception as e:
        err = str(e)[:80]
        print(f"  {table_name}: {err}")
