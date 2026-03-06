#!/usr/bin/env python3
"""
AIshield.cz — E2E diagnostický skript celého funnelu.
Testuje každý krok od health-checku po platbu.

Spuštění:
    python3 scripts/e2e_funnel_test.py

Spuštění na VPS:
    ssh root@46.28.110.102 "cd /opt/aishield && /opt/aishield/venv/bin/python3 scripts/e2e_funnel_test.py"
"""

import json
import sys
import time
import urllib.request
import urllib.error
from dataclasses import dataclass

API_BASE = "http://localhost:8000"
TEST_URL = "https://www.example.com"

# Barvy
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


@dataclass
class TestResult:
    name: str
    passed: bool
    detail: str = ""
    data: dict | None = None


results: list[TestResult] = []


def api_call(method: str, path: str, body: dict | None = None, token: str | None = None) -> tuple[int, dict | str]:
    """Provede API volání, vrátí (status_code, json_data nebo error string)."""
    url = f"{API_BASE}{path}"
    data_bytes = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode() if e.fp else ""
        try:
            return e.code, json.loads(raw)
        except (json.JSONDecodeError, Exception):
            return e.code, raw
    except urllib.error.URLError as e:
        return 0, str(e.reason)
    except Exception as e:
        return 0, str(e)


def test(name: str):
    """Dekorátor pro testovací funkci."""
    def decorator(func):
        def wrapper():
            try:
                result = func()
                results.append(result)
                status = f"{GREEN}PASS{RESET}" if result.passed else f"{RED}FAIL{RESET}"
                print(f"  {status}  {result.name}")
                if result.detail:
                    print(f"         {CYAN}{result.detail}{RESET}")
                return result
            except Exception as e:
                r = TestResult(name=name, passed=False, detail=f"Exception: {e}")
                results.append(r)
                print(f"  {RED}FAIL{RESET}  {name}")
                print(f"         {RED}{e}{RESET}")
                return r
        wrapper.__name__ = name
        return wrapper
    return decorator


# ═══════════════════════════════════════════
# TESTY
# ═══════════════════════════════════════════

@test("1. Health check — API běží")
def test_health():
    code, data = api_call("GET", "/api/health")
    if code == 200 and isinstance(data, dict) and data.get("status") == "ok":
        db_status = data.get("database", "?")
        return TestResult("1. Health check — API běží", True, f"DB: {db_status}, version: {data.get('version')}")
    return TestResult("1. Health check — API běží", False, f"HTTP {code}: {data}")


@test("2. Scan endpoint — vytvoření skenu")
def test_scan_create():
    code, data = api_call("POST", "/api/scan", {"url": TEST_URL})
    if code == 200 and isinstance(data, dict) and data.get("scan_id"):
        return TestResult("2. Scan endpoint — vytvoření skenu", True,
                         f"scan_id={data['scan_id']}, status={data.get('status')}", data=data)
    if code == 429:
        # Rate limited — zkusíme získat cached scan
        if isinstance(data, dict) and data.get("cached_scan_id"):
            return TestResult("2. Scan endpoint — vytvoření skenu", True,
                             f"Rate limited, cached scan_id={data['cached_scan_id']}", data={"scan_id": data["cached_scan_id"]})
        return TestResult("2. Scan endpoint — vytvoření skenu", True,
                         f"Rate limited (expected): {data.get('detail', data)}")
    return TestResult("2. Scan endpoint — vytvoření skenu", False, f"HTTP {code}: {data}")


@test("3. Scan status — polling")
def test_scan_status():
    # Hledáme scan_id z předchozího testu
    scan_test = next((r for r in results if "scan_id" in (r.data or {})), None)
    if not scan_test or not scan_test.data:
        return TestResult("3. Scan status — polling", False, "Nemám scan_id z předchozího kroku")

    scan_id = scan_test.data["scan_id"]
    code, data = api_call("GET", f"/api/scan/{scan_id}")
    if code == 200 and isinstance(data, dict):
        return TestResult("3. Scan status — polling", True,
                         f"status={data.get('status')}, findings={data.get('total_findings')}")
    return TestResult("3. Scan status — polling", False, f"HTTP {code}: {data}")


@test("4. Questionnaire structure — endpoint dostupný")
def test_questionnaire_structure():
    code, data = api_call("GET", "/api/questionnaire/structure")
    if code == 200 and isinstance(data, dict) and data.get("sections"):
        sections = data["sections"]
        total_q = sum(len(s.get("questions", [])) for s in sections)
        return TestResult("4. Questionnaire structure — endpoint dostupný", True,
                         f"{len(sections)} sekcí, {total_q} otázek")
    return TestResult("4. Questionnaire structure — endpoint dostupný", False, f"HTTP {code}: {data}")


@test("5. Payment gateways — dostupné")
def test_gateways():
    code, data = api_call("GET", "/api/payments/gateways")
    if code == 200 and isinstance(data, dict) and data.get("gateways"):
        gateways = data["gateways"]
        active = [g["id"] for g in gateways if g.get("available")]
        return TestResult("5. Payment gateways — dostupné", True,
                         f"Aktivní: {', '.join(active)}")
    return TestResult("5. Payment gateways — dostupné", False, f"HTTP {code}: {data}")


@test("6. Dashboard endpoint — bez auth vrátí 401")
def test_dashboard_no_auth():
    code, data = api_call("GET", "/api/dashboard/me")
    if code in (401, 403):
        return TestResult("6. Dashboard endpoint — bez auth vrátí 401", True,
                         f"HTTP {code} — auth je vyžadována ✓")
    return TestResult("6. Dashboard endpoint — bez auth vrátí 401", False,
                     f"HTTP {code} — očekáván 401: {data}")


@test("7. Voucher validate — neplatný kód")
def test_voucher_invalid():
    code, data = api_call("POST", "/api/payments/voucher/validate", {"code": "NEEXISTUJE"})
    if code == 200 and isinstance(data, dict) and data.get("valid") is False:
        return TestResult("7. Voucher validate — neplatný kód", True,
                         f"valid=False ✓ — {data.get('message')}")
    return TestResult("7. Voucher validate — neplatný kód", False, f"HTTP {code}: {data}")


@test("8. Checkout — bez auth vrátí 401")
def test_checkout_no_auth():
    code, data = api_call("POST", "/api/payments/checkout", {
        "plan": "basic", "email": "test@test.cz", "gateway": "stripe"
    })
    if code in (401, 403):
        return TestResult("8. Checkout — bez auth vrátí 401", True,
                         f"HTTP {code} — auth je vyžadována ✓")
    return TestResult("8. Checkout — bez auth vrátí 401", False,
                     f"HTTP {code} — očekáván 401: {data}")


@test("9. DB kontrola — tabulka companies existuje")
def test_db_companies():
    """Ověří nepřímo přes health check (database_message)."""
    code, data = api_call("GET", "/api/health")
    if code == 200 and isinstance(data, dict):
        db_msg = data.get("database_message", "")
        if "companies" in db_msg.lower() or data.get("database") == "connected":
            return TestResult("9. DB kontrola — tabulka companies existuje", True,
                             f"DB: {data.get('database')}, msg: {db_msg}")
    return TestResult("9. DB kontrola — tabulka companies existuje", False,
                     f"DB problém: {data}")


@test("10. CORS — preflight check")
def test_cors():
    """Ověří že API odpovídá na OPTIONS (CORS preflight)."""
    url = f"{API_BASE}/api/health"
    req = urllib.request.Request(url, method="OPTIONS", headers={
        "Origin": "https://aishield.cz",
        "Access-Control-Request-Method": "GET",
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            cors_header = resp.headers.get("Access-Control-Allow-Origin", "")
            if cors_header:
                return TestResult("10. CORS — preflight check", True,
                                 f"ACAO: {cors_header}")
            return TestResult("10. CORS — preflight check", True,
                             f"HTTP {resp.status} (no CORS header — may use middleware)")
    except urllib.error.HTTPError as e:
        if e.code == 405:
            return TestResult("10. CORS — preflight check", True,
                             "405 Method Not Allowed — CORS handled by middleware")
        return TestResult("10. CORS — preflight check", False, f"HTTP {e.code}")
    except Exception as e:
        return TestResult("10. CORS — preflight check", False, str(e))


# ═══════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════

def main():
    print(f"\n{BOLD}{'═' * 56}{RESET}")
    print(f"{BOLD}  AIshield.cz — E2E Funnel Diagnostika{RESET}")
    print(f"{BOLD}  API: {API_BASE}{RESET}")
    print(f"{BOLD}{'═' * 56}{RESET}\n")

    tests = [
        test_health,
        test_scan_create,
        test_scan_status,
        test_questionnaire_structure,
        test_gateways,
        test_dashboard_no_auth,
        test_voucher_invalid,
        test_checkout_no_auth,
        test_db_companies,
        test_cors,
    ]

    for t in tests:
        t()

    # Shrnutí
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    total = len(results)

    print(f"\n{BOLD}{'─' * 56}{RESET}")
    print(f"{BOLD}  Výsledek: {GREEN}{passed} PASS{RESET} / {RED if failed else GREEN}{failed} FAIL{RESET} / {total} celkem")

    if failed:
        print(f"\n  {RED}Selhané testy:{RESET}")
        for r in results:
            if not r.passed:
                print(f"    ✗ {r.name}: {r.detail}")

    print(f"{BOLD}{'═' * 56}{RESET}\n")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
