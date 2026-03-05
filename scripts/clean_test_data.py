"""Vyčistí testovací záznamy z DB — chirurgicky smaže jen test data."""
import os, sys, json
sys.path.insert(0, '/opt/aishield')
for line in open('/opt/aishield/.env'):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, _, v = line.partition('=')
        os.environ.setdefault(k.strip(), v.strip())

from backend.database import get_supabase
sb = get_supabase()

TEST_EMAIL = "bc.pospa@gmail.com"

print(f"=== ČIŠTĚNÍ TESTOVACÍCH ZÁZNAMŮ PRO {TEST_EMAIL} ===")
print()

# 1. Najdi company
r = sb.table("companies").select("id,name,url").eq("email", TEST_EMAIL).execute()
companies = r.data or []
print(f"1. Companies: {len(companies)}")
for c in companies:
    print(f"   {c['id']} | {c['name']} | {c.get('url','')}")
company_ids = [c["id"] for c in companies]

# 2. Najdi orders
r = sb.table("orders").select("id,order_number,plan,status,payment_gateway").eq("email", TEST_EMAIL).execute()
orders = r.data or []
print(f"2. Orders: {len(orders)}")
for o in orders:
    print(f"   {o['id']} | {o['order_number']} | {o['plan']} | {o['status']} | {o.get('payment_gateway','')}")

# 3. Najdi scans
scans = []
for cid in company_ids:
    r = sb.table("scans").select("id,url,status").eq("company_id", cid).execute()
    scans.extend(r.data or [])
print(f"3. Scans: {len(scans)}")
scan_ids = [s["id"] for s in scans]

# 4. Najdi findings
findings = []
for sid in scan_ids:
    r = sb.table("findings").select("id").eq("scan_id", sid).execute()
    findings.extend(r.data or [])
print(f"4. Findings: {len(findings)}")

# 5. Najdi documents
documents = []
for cid in company_ids:
    r = sb.table("documents").select("id,template_key").eq("company_id", cid).execute()
    documents.extend(r.data or [])
print(f"5. Documents: {len(documents)}")

# 6. Questionnaire responses
quest = []
for cid in company_ids:
    r = sb.table("questionnaire_responses").select("id").eq("company_id", cid).execute()
    quest.extend(r.data or [])
print(f"6. Questionnaire responses: {len(quest)}")

# 7. Pipeline runs
pipeline = []
for cid in company_ids:
    r = sb.table("pipeline_runs").select("id").eq("company_id", cid).execute()
    pipeline.extend(r.data or [])
print(f"7. Pipeline runs: {len(pipeline)}")

print()
print("=== MAZÁNÍ ===")

# Smazat v pořadí: findings → scans → documents → pipeline_runs → questionnaire_responses → orders → companies
for f in findings:
    sb.table("findings").delete().eq("id", f["id"]).execute()
print(f"  ✓ Smazáno {len(findings)} findings")

for s in scan_ids:
    sb.table("scans").delete().eq("id", s).execute()
print(f"  ✓ Smazáno {len(scans)} scans")

for d in documents:
    sb.table("documents").delete().eq("id", d["id"]).execute()
print(f"  ✓ Smazáno {len(documents)} documents")

for p in pipeline:
    sb.table("pipeline_runs").delete().eq("id", p["id"]).execute()
print(f"  ✓ Smazáno {len(pipeline)} pipeline_runs")

for q in quest:
    sb.table("questionnaire_responses").delete().eq("id", q["id"]).execute()
print(f"  ✓ Smazáno {len(quest)} questionnaire_responses")

for o in orders:
    sb.table("orders").delete().eq("id", o["id"]).execute()
print(f"  ✓ Smazáno {len(orders)} orders")

for c in companies:
    sb.table("companies").delete().eq("id", c["id"]).execute()
print(f"  ✓ Smazáno {len(companies)} companies")

# Reset voucher used count
sb.table("voucher_codes").update({"used_count": 0}).eq("code", "PIONEER-TEST-001").execute()
print(f"  ✓ Reset voucher PIONEER-TEST-001 used_count → 0")

print()
print("✅ Hotovo — čistý štít!")
