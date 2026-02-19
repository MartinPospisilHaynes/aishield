"""
AIshield.cz — CLEANUP: Smazat VŠECHNA stará testovací data
- Supabase Storage (bucket 'documents')
- DB tabulky: documents, questionnaire_responses, findings, scans, orders, clients
- Lokální soubory v testovaci_dokumenty/
"""
import requests
import os
import shutil

SKEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJzeHdxY3JrdHRsZm5xYmpncGdjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDU3MTMxNywiZXhwIjoyMDg2MTQ3MzE3fQ.dxjnj7uQ3-uRRmqFa-MXnM6t3xL-Fci8A-xTqOvy-MU"
BASE = "https://rsxwqcrkttlfnqbjgpgc.supabase.co"
H = {"apikey": SKEY, "Authorization": f"Bearer {SKEY}"}

# All known client IDs from storage
STORAGE_CLIENT_IDS = [
    "b7a450a8-6f6b-40c6-aa61-31d6c996c3a1",
    "2450b82c-10a8-451d-bc85-43fba24db9d3",
    "91df7471-7756-480e-89cf-a31e5864a338",
    "390552e7-b0a9-426b-a73f-993a72c3ac37",
    "84aa2500-6e84-485b-98ed-bbcf8f62c122",
]

print("=" * 60)
print("  CLEANUP: Mazani vsech starych testovacich dat")
print("=" * 60)

# ── 1. Supabase Storage ──
print("\n[1/7] Supabase Storage (bucket 'documents')...")
for cid in STORAGE_CLIENT_IDS:
    r = requests.post(
        f"{BASE}/storage/v1/object/list/documents",
        headers={**H, "Content-Type": "application/json"},
        json={"prefix": cid, "limit": 200},
        timeout=15,
    )
    files = r.json()
    if not files:
        continue
    paths = [f"{cid}/{f['name']}" for f in files]
    dr = requests.delete(
        f"{BASE}/storage/v1/object/documents",
        headers={**H, "Content-Type": "application/json"},
        json={"prefixes": paths},
        timeout=30,
    )
    print(f"  {cid[:8]}... : {len(paths)} souboru smazano (HTTP {dr.status_code})")

# ── 2. DB: documents ──
print("\n[2/7] DB tabulka 'documents'...")
r = requests.delete(
    f"{BASE}/rest/v1/documents?id=gt.00000000-0000-0000-0000-000000000000",
    headers={**H, "Content-Type": "application/json", "Prefer": "return=representation"},
    timeout=15,
)
print(f"  Smazano: HTTP {r.status_code}, {len(r.json()) if r.status_code == 200 else 0} zaznamu")

# ── 3. DB: questionnaire_responses ──
print("\n[3/7] DB tabulka 'questionnaire_responses'...")
r = requests.delete(
    f"{BASE}/rest/v1/questionnaire_responses?id=gt.00000000-0000-0000-0000-000000000000",
    headers={**H, "Content-Type": "application/json", "Prefer": "return=representation"},
    timeout=15,
)
print(f"  Smazano: HTTP {r.status_code}, {len(r.json()) if r.status_code == 200 else 0} zaznamu")

# ── 4. DB: findings ──
print("\n[4/7] DB tabulka 'findings'...")
r = requests.delete(
    f"{BASE}/rest/v1/findings?id=gt.00000000-0000-0000-0000-000000000000",
    headers={**H, "Content-Type": "application/json", "Prefer": "return=representation"},
    timeout=15,
)
print(f"  Smazano: HTTP {r.status_code}, {len(r.json()) if r.status_code == 200 else 0} zaznamu")

# ── 5. DB: scans ──
print("\n[5/7] DB tabulka 'scans'...")
r = requests.delete(
    f"{BASE}/rest/v1/scans?id=gt.00000000-0000-0000-0000-000000000000",
    headers={**H, "Content-Type": "application/json", "Prefer": "return=representation"},
    timeout=15,
)
print(f"  Smazano: HTTP {r.status_code}, {len(r.json()) if r.status_code == 200 else 0} zaznamu")

# ── 6. DB: orders (only test orders) ──
print("\n[6/7] DB tabulka 'orders' (testovaci)...")
r = requests.delete(
    f"{BASE}/rest/v1/orders?order_number=like.AS-*-TEST*",
    headers={**H, "Content-Type": "application/json", "Prefer": "return=representation"},
    timeout=15,
)
print(f"  Smazano: HTTP {r.status_code}, {len(r.json()) if r.status_code == 200 else 0} zaznamu")

# ── 7. DB: clients (test clients only — not real desperados) ──
print("\n[7/7] DB tabulka 'clients' (testovaci)...")
# Get all clients, delete those that are test personas
r = requests.get(
    f"{BASE}/rest/v1/clients?select=id,email",
    headers=H,
    timeout=15,
)
if r.status_code == 200:
    clients = r.json()
    test_clients = [c for c in clients if "aishield.cz" in c.get("email", "") or "@" in c.get("email", "")]
    for c in test_clients:
        real_emails = ["info@desperados-design.cz", "e2e-test@aishield.cz"]
        if c["email"] in real_emails:
            continue
        dr = requests.delete(
            f"{BASE}/rest/v1/clients?id=eq.{c['id']}",
            headers={**H, "Prefer": "return=representation"},
            timeout=10,
        )
        print(f"  Smazano: {c['email']} (HTTP {dr.status_code})")

# ── 8. Lokalni soubory ──
print("\n[8/8] Lokalni testovaci soubory...")
local_base = "testovaci_dokumenty"
count = 0
for persona_dir in os.listdir(local_base):
    persona_path = os.path.join(local_base, persona_dir)
    if os.path.isdir(persona_path):
        for f in os.listdir(persona_path):
            fp = os.path.join(persona_path, f)
            if os.path.isfile(fp):
                os.remove(fp)
                count += 1
print(f"  Smazano {count} lokalnich souboru")

print("\n" + "=" * 60)
print("  CLEANUP DOKONCEN — ciste prostredi pro nove testy!")
print("=" * 60)
