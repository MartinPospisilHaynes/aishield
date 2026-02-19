#!/usr/bin/env python3
"""Test document generation pipeline end-to-end."""
import os
import sys
import json
from pathlib import Path

# Load .env
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

import requests

API = os.environ.get("TEST_API_URL", "https://api.aishield.cz")
SUPABASE_URL = os.environ["SUPABASE_URL"]
ANON_KEY = os.environ["SUPABASE_ANON_KEY"]

# Login
r = requests.post(
    f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
    json={"email": "e2e-test@aishield.cz", "password": "E2eTest2026!"},
    headers={"apikey": ANON_KEY, "Content-Type": "application/json"},
    timeout=10,
)
assert r.status_code == 200, f"Login failed: {r.status_code}"
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✓ Login OK")

# Get company_id from dashboard
r2 = requests.get(f"{API}/api/dashboard/me", headers=headers, timeout=10)
assert r2.status_code == 200, f"Dashboard: {r2.status_code} {r2.text[:200]}"
company = r2.json().get("company", {})
company_id = company.get("id", "")
print(f"✓ Company: {company.get('name', '?')} (id={company_id})")

# List available templates
r3 = requests.get(f"{API}/api/documents/templates", headers=headers, timeout=10)
print(f"✓ Templates endpoint: {r3.status_code}")
if r3.status_code == 200:
    templates = r3.json()
    print(f"  Templates: {json.dumps(templates, indent=2, ensure_ascii=False)[:500]}")

# Generate FULL compliance kit
print(f"\n--- Generating compliance kit for {company_id} ---")
r4 = requests.post(
    f"{API}/api/documents/generate/{company_id}",
    headers=headers,
    timeout=120,
)
print(f"Generate result: {r4.status_code}")
if r4.status_code == 200:
    result = r4.json()
    print(f"✅ SUCCESS!")
    print(f"  Company: {result.get('company_name', '?')}")
    print(f"  Generated: {result.get('summary', {}).get('generated', '?')}")
    print(f"  Failed: {result.get('summary', {}).get('failed', '?')}")
    print(f"\n  Documents:")
    for doc in result.get("documents", []):
        print(f"    - {doc.get('template_key', '?')}: {doc.get('filename', '?')} ({doc.get('size_bytes', 0)} bytes)")
    if result.get("errors"):
        print(f"\n  Errors:")
        for err in result["errors"]:
            print(f"    ⚠ {err}")
else:
    print(f"❌ FAILED: {r4.text[:500]}")

# Test single document generation
print(f"\n--- Generating single document (compliance_report) ---")
r5 = requests.post(
    f"{API}/api/documents/generate/{company_id}/compliance_report",
    headers=headers,
    timeout=60,
)
print(f"Single doc result: {r5.status_code}")
if r5.status_code == 200:
    result = r5.json()
    print(f"✅ {result.get('filename', '?')} ({result.get('size_bytes', 0)} bytes)")
else:
    print(f"❌ {r5.text[:500]}")
