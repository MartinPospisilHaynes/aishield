"""E2E Login Test — test celého login→dashboard flow."""
import httpx
import urllib.parse

ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJzeHdxY3JrdHRsZm5xYmpncGdjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA1NzEzMTcsImV4cCI6MjA4NjE0NzMxN30.dOWAju8BwIcFTJaMe04eG5LVac4nkpiwdIz46-mQPTs"
EMAIL = "info@desperados-design.cz"
PASSWORD = "TestHeslo123!"
API = "https://api.aishield.cz"

def test():
    print("=" * 50)
    print("E2E LOGIN TEST")
    print("=" * 50)

    # 1. Login
    print("\n1. Supabase Login...")
    r = httpx.post(
        "https://rsxwqcrkttlfnqbjgpgc.supabase.co/auth/v1/token?grant_type=password",
        headers={"apikey": ANON_KEY, "Content-Type": "application/json"},
        json={"email": EMAIL, "password": PASSWORD},
        timeout=15.0
    )
    data = r.json()
    token = data.get("access_token")
    if not token:
        print(f"   FAIL: {data.get('error')} - {data.get('error_description', data.get('msg'))}")
        return False
    print(f"   OK - token: {token[:30]}...")

    # 2. Dashboard
    print("\n2. Dashboard API...")
    encoded_email = urllib.parse.quote(EMAIL, safe="")
    r2 = httpx.get(
        f"{API}/api/dashboard/{encoded_email}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=15.0
    )
    print(f"   Status: {r2.status_code}")
    if r2.status_code == 200:
        d = r2.json()
        company = d.get("company")
        print(f"   Company: {company.get('name') if company else 'None'}")
        print(f"   Scans: {len(d.get('scans', []))}")
        print(f"   Findings: {len(d.get('findings', []))}")
        print(f"   Questionnaire: {d.get('questionnaire_status')}")
    else:
        print(f"   ERROR: {r2.text[:300]}")
        return False

    # 3. Health
    print("\n3. Health check...")
    r3 = httpx.get(f"{API}/api/health", timeout=10.0)
    print(f"   Status: {r3.status_code}")
    if r3.status_code == 200:
        h = r3.json()
        print(f"   API: {h.get('status')}, DB: {h.get('database')}")
    else:
        print(f"   ERROR: {r3.text[:200]}")
        return False

    # 4. Chat
    print("\n4. Chat API...")
    r4 = httpx.post(
        f"{API}/api/chat",
        json={"session_id": "e2e-test", "messages": [{"role": "user", "content": "Ahoj"}]},
        timeout=30.0
    )
    print(f"   Status: {r4.status_code}")
    if r4.status_code == 200:
        reply = r4.json().get("reply", "")[:80]
        print(f"   Reply: {reply}...")
    else:
        print(f"   ERROR: {r4.text[:200]}")

    print("\n" + "=" * 50)
    print("ALL TESTS PASSED!")
    print("=" * 50)
    return True

if __name__ == "__main__":
    test()
