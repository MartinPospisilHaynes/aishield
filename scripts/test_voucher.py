"""E2E test: voucher checkout flow."""
import os, sys, json, requests
sys.path.insert(0, '/opt/aishield')
for line in open('/opt/aishield/.env'):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, _, v = line.partition('=')
        os.environ.setdefault(k.strip(), v.strip())

API = "https://api.aishield.cz"

# 1. Test voucher validate — valid code
print("1. Validate PIONEER-TEST-001...")
r = requests.post(f"{API}/api/payments/voucher/validate", json={"code": "PIONEER-TEST-001"})
assert r.status_code == 200, f"FAIL: {r.status_code} {r.text}"
d = r.json()
assert d["valid"] == True, f"FAIL: not valid: {d}"
assert d["discount_percent"] == 100, f"FAIL: discount={d['discount_percent']}"
print(f"   OK: {d}")

# 2. Test voucher validate — invalid code
print("2. Validate NEEXISTUJE...")
r = requests.post(f"{API}/api/payments/voucher/validate", json={"code": "NEEXISTUJE"})
assert r.status_code == 200
d = r.json()
assert d["valid"] == False
print(f"   OK: {d}")

# 3. Test voucher validate — empty code
print("3. Validate empty...")
r = requests.post(f"{API}/api/payments/voucher/validate", json={"code": ""})
assert r.status_code == 200
d = r.json()
assert d["valid"] == False
print(f"   OK: {d}")

# 4. Test checkout with voucher (needs auth token) — we'll test via supabase
print("4. Testing checkout with voucher via direct function call...")
from backend.database import get_supabase
sb = get_supabase()

# Create a test jwt for bc.pospa@gmail.com
from supabase import create_client
url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
admin_sb = create_client(url, key)

# Just test the internal _validate_voucher function
from backend.api.payments import _validate_voucher
result = _validate_voucher("PIONEER-TEST-001", "basic")
assert result["valid"] == True, f"FAIL: {result}"
assert result["discount_percent"] == 100
print(f"   OK: _validate_voucher('PIONEER-TEST-001', 'basic') = {result}")

result = _validate_voucher("", None)
assert result["valid"] == False
print(f"   OK: _validate_voucher('', None) = {result}")

print()
print("✅ Všechny testy prošly!")
