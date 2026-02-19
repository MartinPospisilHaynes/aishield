#!/usr/bin/env python3
"""Confirm the e2e-test user's email via Supabase admin API."""
import os
import sys
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

url = os.environ["SUPABASE_URL"]
service_key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
anon_key = os.environ["SUPABASE_ANON_KEY"]

print(f"Supabase: {url}")

# 1) List users
r = requests.get(
    f"{url}/auth/v1/admin/users",
    headers={"apikey": service_key, "Authorization": f"Bearer {service_key}"},
    timeout=10,
)
assert r.status_code == 200, f"List users failed: {r.status_code} {r.text[:200]}"
users = r.json().get("users", [])
print(f"Found {len(users)} users")

target = None
for u in users:
    if u.get("email") == "e2e-test@aishield.cz":
        target = u
        break

if not target:
    print("User e2e-test@aishield.cz not found!")
    sys.exit(1)

uid = target["id"]
confirmed = target.get("email_confirmed_at")
print(f"User ID: {uid}, email confirmed: {confirmed}")

# 2) Confirm email
r2 = requests.put(
    f"{url}/auth/v1/admin/users/{uid}",
    json={"email_confirm": True},
    headers={
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
    },
    timeout=10,
)
print(f"Confirm result: {r2.status_code}")
if r2.status_code != 200:
    print(r2.text[:300])
    sys.exit(1)

# 3) Verify login
r3 = requests.post(
    f"{url}/auth/v1/token?grant_type=password",
    json={"email": "e2e-test@aishield.cz", "password": "E2eTest2026!"},
    headers={"apikey": anon_key, "Content-Type": "application/json"},
    timeout=10,
)
print(f"Login: {r3.status_code}")
if r3.status_code == 200:
    print("LOGIN OK!")
else:
    print(r3.text[:200])
    sys.exit(1)
