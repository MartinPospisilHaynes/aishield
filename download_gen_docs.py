#!/usr/bin/env python3
"""
Download all documents from latest Gen19 from Supabase storage.
Saves to /opt/aishield/gen_output/<timestamp>/
"""

import os
import json
import requests
from datetime import datetime

COMPANY_ID = "62e22b1d-dbc3-486d-8aad-c495732049c8"

# Load env from .env
env_path = "/opt/aishield/.env"
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "") or os.environ.get("SUPABASE_ANON_KEY", "")

print(f"Supabase URL: {SUPABASE_URL[:30]}...")

# Query latest documents from client_documents table
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

# Get latest documents
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/documents?company_id=eq.{COMPANY_ID}&order=created_at.desc&limit=20",
    headers=headers,
)

if resp.status_code != 200:
    print(f"ERROR: {resp.status_code} {resp.text[:200]}")
    exit(1)

docs = resp.json()
print(f"Found {len(docs)} documents")

# Group by generation (same approximate timestamp)
if not docs:
    print("No documents found!")
    exit(1)

# Use latest document's created_at as generation marker
latest_ts = docs[0].get("created_at", "")[:19].replace(":", "-")
output_dir = f"/opt/aishield/gen_output/{latest_ts}"
os.makedirs(output_dir, exist_ok=True)

# Find all docs from this generation (within 3 hours of latest)
from datetime import timezone
latest_dt = datetime.fromisoformat(docs[0]["created_at"].replace("Z", "+00:00"))
gen_docs = []
for d in docs:
    dt = datetime.fromisoformat(d["created_at"].replace("Z", "+00:00"))
    if abs((latest_dt - dt).total_seconds()) < 10800:  # 3 hours
        gen_docs.append(d)

print(f"Latest generation: {len(gen_docs)} documents")
print(f"Output: {output_dir}")
print()

# Download each
for doc in gen_docs:
    url = doc.get("url", "")
    doc_type = doc.get("type", "unknown")
    doc_name = doc.get("name", doc_type)
    fmt = doc.get("format", "?")
    size = doc.get("size_bytes", 0)
    
    if not url:
        print(f"  SKIP {doc_name} — no URL")
        continue
    
    # Build filename from type + format
    ext = fmt if fmt else "bin"
    filename = f"{doc_type}.{ext}"
    
    print(f"  Downloading {doc_name} ({fmt}, {size:,} bytes)...")
    
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "wb") as f:
                f.write(r.content)
            print(f"    OK: {len(r.content):,} bytes → {filepath}")
        else:
            print(f"    ERROR: HTTP {r.status_code}")
    except Exception as e:
        print(f"    ERROR: {e}")

print(f"\nDone! Files saved to: {output_dir}")
print(f"To download to Mac: scp -r root@46.28.110.102:{output_dir} ~/Desktop/gen19/")
