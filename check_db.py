#!/usr/bin/env python3
"""Check existing scan data and questionnaire answers in the database."""
import json, os
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

company_id = "3900ae47-25d5-42fb-af4d-0d06623bc8cc"
scan_id = "837ed6a5-0be5-4878-a3de-08d8c046a734"

# Companies
companies = sb.table("companies").select("id, name, created_at").execute()
print("=== COMPANIES ===")
for c in companies.data:
    print(f"  {c['id']} | {c['name']} | {c['created_at']}")

# Scan
scan = sb.table("scans").select("id, company_id, status, scan_type, created_at, results").eq("id", scan_id).execute()
print("\n=== SCAN ===")
if scan.data:
    s = scan.data[0]
    print(f"  ID: {s['id']}")
    print(f"  Status: {s['status']}")
    print(f"  Type: {s['scan_type']}")
    print(f"  Created: {s['created_at']}")
    results = s.get("results") or {}
    if isinstance(results, dict):
        print(f"  Results keys: {list(results.keys())}")
        if "risk_score" in results:
            print(f"  Risk score: {results['risk_score']}")
    else:
        print(f"  Results type: {type(results)}")

# Questionnaire
answers = sb.table("questionnaire_answers").select("id, company_id, answers, created_at").eq("company_id", company_id).order("created_at", desc=True).limit(1).execute()
print(f"\n=== QUESTIONNAIRE ANSWERS ===")
if answers.data:
    a = answers.data[0]
    print(f"  ID: {a['id']}")
    print(f"  Created: {a['created_at']}")
    ans = a.get("answers") or {}
    if isinstance(ans, dict):
        print(f"  Number of answers: {len(ans)}")
        for k in list(ans.keys())[:5]:
            val = str(ans[k])[:80]
            print(f"    {k}: {val}")
        print(f"    ... and {max(0, len(ans)-5)} more")
    elif isinstance(ans, list):
        print(f"  Number of answers: {len(ans)}")
        for item in ans[:3]:
            print(f"    {item}")
else:
    print("  No answers found!")

# Check documents table
docs = sb.table("documents").select("id, scan_id, doc_type, status, created_at, storage_path").eq("scan_id", scan_id).execute()
print(f"\n=== EXISTING DOCUMENTS ({len(docs.data)}) ===")
for d in docs.data:
    print(f"  {d['doc_type']} | {d['status']} | {d.get('storage_path', 'N/A')}")
