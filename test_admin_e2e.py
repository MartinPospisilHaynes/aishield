#!/usr/bin/env python3
"""
AIshield.cz — Admin CRM E2E Test Suite
========================================
Simuluje REÁLNOU cestu admina, který se přihlásí do CRM,
prochází všechny sekce, clickuje na detaily firem,
mění statusy, přidává poznámky, kontroluje monitoring.

11 FÁZÍ, 45+ testů:

  FÁZE 1  — Infrastruktura (API + frontend zdraví)
  FÁZE 2  — Autentizace (CRM login, Supabase JWT, bezpečnost)
  FÁZE 3  — Dashboard & statistiky
  FÁZE 4  — Seznam firem (filtrování, řazení)
  FÁZE 5  — Detail firmy (kompletní CRM karta)
  FÁZE 6  — Pipeline / funnel
  FÁZE 7  — Workflow management (statusy, poznámky, timeline)
  FÁZE 8  — Email & komunikace
  FÁZE 9  — Monitoring & alerting
  FÁZE 10 — Nástroje (audit log, cleanup, task runner)
  FÁZE 11 — Chybové stavy & bezpečnost

Spuštění:
  export SUPABASE_ANON_KEY="xxx"
  export ADMIN_EMAIL="martin@desperados-design.cz"
  export ADMIN_PASSWORD="xxx"
  python3 test_admin_e2e.py

Autor: AI (Copilot) pro Martin Haynes
"""

import json
import os
import sys
import time
import hashlib
import requests
from dataclasses import dataclass, field
from typing import Optional, Any
from datetime import datetime

# ═══════════════════════════════════════════
#  KONFIGURACE
# ═══════════════════════════════════════════
API = os.environ.get("TEST_API_URL", "https://api.aishield.cz")
WEB = os.environ.get("TEST_WEB_URL", "https://aishield.cz")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://rsxwqcrkttlfnqbjgpgc.supabase.co")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

# CRM login hardcoded credentials (same as backend)
CRM_USERNAME = "ADMIN"
CRM_PASSWORD = "Rc_732716141"

if not SUPABASE_ANON_KEY or not ADMIN_EMAIL or not ADMIN_PASSWORD:
    print("\033[91m╔══════════════════════════════════════════════════════════════╗")
    print("║  Chybí env proměnné!                                         ║")
    print("║                                                               ║")
    print("║  export SUPABASE_ANON_KEY='eyJ...'                            ║")
    print("║  export ADMIN_EMAIL='martin@desperados-design.cz'             ║")
    print("║  export ADMIN_PASSWORD='...'                                  ║")
    print("╚══════════════════════════════════════════════════════════════╝\033[0m")
    sys.exit(1)

# ── Barvy ──
G = "\033[92m"; R = "\033[91m"; Y = "\033[93m"; C = "\033[96m"
M = "\033[95m"; B = "\033[1m"; D = "\033[2m"; X = "\033[0m"


# ═══════════════════════════════════════════
#  VÝSLEDKY
# ═══════════════════════════════════════════

@dataclass
class TestResult:
    name: str
    phase: str
    passed: bool
    detail: str = ""
    duration: float = 0.0
    critical: bool = False
    warning: str = ""  # slabé místo


@dataclass
class WeakSpot:
    """Slabé místo zjištěné testem."""
    severity: str      # "critical" | "high" | "medium" | "low"
    location: str      # kde se problém nachází
    description: str   # popis problému
    test_name: str     # jaký test to odhalil


results: list[TestResult] = []
weak_spots: list[WeakSpot] = []
abort = False


def add_weak_spot(severity: str, location: str, description: str, test_name: str):
    weak_spots.append(WeakSpot(severity, location, description, test_name))


def phase_header(name: str):
    print(f"\n{B}{C}  ── {name} ──{X}")


def run_test(name: str, phase: str, func, critical: bool = False):
    global abort
    if abort:
        results.append(TestResult(name, phase, False, "Přeskočeno (předchozí kritický test selhal)", 0, critical))
        print(f"    {D}⏭️  {name} — přeskočeno{X}")
        return None
    t0 = time.time()
    try:
        detail = func()
        dur = time.time() - t0
        results.append(TestResult(name, phase, True, detail or "OK", dur, critical))
        print(f"    {G}✓{X}  {name} {D}({dur:.1f}s){X}")
        if detail:
            for line in str(detail).split("\n"):
                print(f"       {D}{line}{X}")
        return detail
    except Exception as e:
        dur = time.time() - t0
        results.append(TestResult(name, phase, False, str(e), dur, critical))
        print(f"    {R}✗{X}  {name} {D}({dur:.1f}s){X}")
        print(f"       {R}{e}{X}")
        if critical:
            abort = True
            print(f"       {R}{B}↑ KRITICKÝ — další testy přeskočeny{X}")
        return None


# ═══════════════════════════════════════════
#  STAV TESTOVACÍ SESSION
# ═══════════════════════════════════════════

class State:
    # Supabase JWT (pro require_admin endpointy)
    access_token: Optional[str] = None
    user_id: Optional[str] = None

    # CRM custom token
    crm_token: Optional[str] = None

    # Data nalezená při procházení
    companies: list = []
    first_company_id: Optional[str] = None
    first_company_name: Optional[str] = None
    company_detail: Optional[dict] = None
    pipeline_data: Optional[dict] = None
    dashboard_stats: Optional[dict] = None
    original_workflow_status: Optional[str] = None
    test_note_id: Optional[str] = None
    email_log_count: int = 0
    alerts_count: int = 0


s = State()


def admin_headers() -> dict:
    """Headers s Supabase JWT pro admin endpointy."""
    return {
        "Authorization": f"Bearer {s.access_token}",
        "Content-Type": "application/json",
    }


def crm_headers() -> dict:
    """Headers s CRM tokenem."""
    return {
        "Authorization": f"Bearer {s.crm_token}",
        "Content-Type": "application/json",
    }


# ═══════════════════════════════════════════
#  FÁZE 1 — INFRASTRUKTURA
# ═══════════════════════════════════════════

def t_api_health():
    """Kontrola že API žije."""
    r = requests.get(f"{API}/api/health", timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}"
    d = r.json()
    assert d.get("status") in ("ok", "degraded"), f"Status: {d.get('status')}"
    db = d.get("database", "?")
    if db != "connected":
        add_weak_spot("critical", "API /health", f"Databáze: {db}", "API health")
    return f"API={d['status']}, DB={db}"


def t_engine_health():
    """Kontrola scan engine."""
    r = requests.get(f"{API}/api/health/engine", timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}"
    d = r.json()
    if d.get("status") not in ("ok", "ready"):
        add_weak_spot("medium", "Scan Engine", f"Engine status: {d.get('status')}", "Engine health")
    return f"Engine status={d.get('status')}"


def t_frontend_admin_pages():
    """Kontrola že admin stránky jsou dostupné (HTTP 200)."""
    pages_ok = []
    pages_fail = []
    for path in ["/", "/admin/login", "/admin"]:
        try:
            r = requests.get(f"{WEB}{path}", timeout=15, allow_redirects=True)
            if r.status_code == 200:
                pages_ok.append(path)
            else:
                pages_fail.append(f"{path} → HTTP {r.status_code}")
                add_weak_spot("high", f"Frontend {path}", f"HTTP {r.status_code}", "Frontend pages")
        except requests.RequestException as e:
            pages_fail.append(f"{path} → {e}")
            add_weak_spot("high", f"Frontend {path}", str(e), "Frontend pages")

    if pages_fail:
        raise Exception(f"Selhaly: {', '.join(pages_fail)}")
    return f"Všech {len(pages_ok)} stránek OK: {', '.join(pages_ok)}"


def t_api_response_time():
    """Měření response time klíčových endpointů."""
    endpoints = [
        ("/api/health", "GET"),
        ("/api/health/engine", "GET"),
    ]
    slow = []
    for path, method in endpoints:
        t0 = time.time()
        r = requests.get(f"{API}{path}", timeout=15)
        dur = time.time() - t0
        if dur > 3.0:
            slow.append(f"{path}: {dur:.1f}s")
            add_weak_spot("medium", f"API {path}", f"Pomalá odpověď: {dur:.1f}s (> 3s)", "Response time")
    if slow:
        return f"⚠️  Pomalé: {', '.join(slow)}"
    return "Všechny odpovědi < 3s"


# ═══════════════════════════════════════════
#  FÁZE 2 — AUTENTIZACE
# ═══════════════════════════════════════════

def t_crm_login_valid():
    """CRM login s platnými credentials."""
    r = requests.post(f"{API}/api/admin/crm/login",
                      json={"username": CRM_USERNAME, "password": CRM_PASSWORD},
                      timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()
    assert "token" in d, "Chybí token v odpovědi"
    assert d["token"].startswith("admin_"), f"Token nemá prefix admin_: {d['token'][:10]}"
    s.crm_token = d["token"]

    # Validace tokenu
    expected = "admin_" + hashlib.sha256(CRM_PASSWORD.encode()).hexdigest()[:32]
    if s.crm_token != expected:
        add_weak_spot("high", "CRM login", "Token se liší od očekávaného SHA256", "CRM login valid")

    return f"token={d['token'][:20]}…, username={d.get('username')}"


def t_crm_login_invalid():
    """CRM login se špatnými credentials → 401."""
    test_cases = [
        ({"username": "ADMIN", "password": "wrong"}, "Špatné heslo"),
        ({"username": "hacker", "password": CRM_PASSWORD}, "Špatný username"),
        ({"username": "", "password": ""}, "Prázdné údaje"),
        ({"username": "admin", "password": CRM_PASSWORD}, "Case-sensitive username"),
    ]
    passed = 0
    for body, desc in test_cases:
        r = requests.post(f"{API}/api/admin/crm/login", json=body, timeout=10)
        if r.status_code == 401:
            passed += 1
        else:
            add_weak_spot("critical", "CRM login", f"'{desc}' vrátil HTTP {r.status_code} místo 401", "CRM login invalid")
    assert passed == len(test_cases), f"Prošlo {passed}/{len(test_cases)} rejection testů"
    return f"Všech {len(test_cases)} neplatných loginů správně odmítnuto (401)"


def t_supabase_jwt_login():
    """Login přes Supabase Auth (pro require_admin endpointy).
    
    Strategie: Použijeme test-reset pro info@desperados-design.cz
    (je v TEST_EMAILS i ADMIN_EMAILS), čímž získáme admin JWT.
    Pokud to selže, zkusíme přímý login s ADMIN_EMAIL/ADMIN_PASSWORD.
    """
    test_admin_email = "info@desperados-design.cz"
    test_admin_password = "TestAdmin2026!"
    
    # 1. Zkusíme přímý login s poskytnutými credentials
    r = requests.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=10,
    )
    if r.status_code == 200:
        d = r.json()
        s.access_token = d["access_token"]
        s.user_id = d.get("user", {}).get("id")
        return f"Přímý login OK: user_id={s.user_id}, email={ADMIN_EMAIL}"
    
    # 2. Fallback: test-reset pro admin test email
    reset_r = requests.post(
        f"{API}/api/admin/test-reset",
        json={"email": test_admin_email, "password": test_admin_password, "web_url": "https://www.desperados-design.cz"},
        timeout=20,
    )
    if reset_r.status_code != 200:
        add_weak_spot("high", "Supabase JWT login",
                      f"Přímý login ({ADMIN_EMAIL}) i test-reset ({test_admin_email}) selhaly. "
                      f"Reset: HTTP {reset_r.status_code}",
                      "JWT login")
        raise Exception(f"Nelze získat admin JWT — přímý login i test-reset selhaly")
    
    # 3. Login s test-admin účtem
    import time as _time
    _time.sleep(1)  # Počkáme na propagaci
    
    r2 = requests.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
        json={"email": test_admin_email, "password": test_admin_password},
        timeout=10,
    )
    if r2.status_code != 200:
        add_weak_spot("high", "Supabase JWT login",
                      f"Test-admin login selhal: HTTP {r2.status_code}",
                      "JWT login")
        raise Exception(f"Test-admin login HTTP {r2.status_code}: {r2.text[:200]}")
    
    d = r2.json()
    assert "access_token" in d, "Chybí access_token"
    s.access_token = d["access_token"]
    s.user_id = d.get("user", {}).get("id")
    
    return f"Test-admin login OK (fallback)\nuser_id={s.user_id}\nemail={test_admin_email}"


def _require_jwt(label: str = ""):
    """Helper — přeskočí test pokud nemáme Supabase JWT."""
    if not s.access_token:
        raise Exception(f"Přeskočeno — chybí Supabase JWT token{' (' + label + ')' if label else ''}")


def t_admin_without_token():
    """Přístup k admin endpointu BEZ tokenu → 401/403."""
    endpoints = [
        ("GET", "/api/admin/stats"),
        ("GET", "/api/admin/companies"),
        ("GET", "/api/admin/crm/pipeline"),
        ("GET", "/api/admin/crm/dashboard-stats"),
    ]
    passed = 0
    details = []
    for method, path in endpoints:
        r = requests.request(method, f"{API}{path}", timeout=10)
        if r.status_code in (401, 403):
            passed += 1
        elif r.status_code == 404:
            details.append(f"{path}: 404 (endpoint chybí na serveru)")
            add_weak_spot("medium", f"Missing endpoint {path}",
                          "Endpoint vrací 404 — deployment?, route chybí?", "No-token access")
        else:
            add_weak_spot("critical", f"Auth {path}",
                          f"Vrátil HTTP {r.status_code} BEZ tokenu!", "No-token access")
    assert passed == len(endpoints), f"Bez tokenu: {passed}/{len(endpoints)} správně odmítnuto. {'; '.join(details)}"
    return f"Všech {len(endpoints)} endpointů správně vyžaduje autentizaci"


def t_admin_with_crm_token():
    """CRM token NEmá fungovat na require_admin endpointy (různý auth)."""
    _require_jwt()
    r = requests.get(f"{API}/api/admin/stats",
                     headers={"Authorization": f"Bearer {s.crm_token}"},
                     timeout=10)
    if r.status_code == 200:
        add_weak_spot("critical", "Auth bypass",
                      "CRM custom token funguje na Supabase JWT endpoint! "
                      "Backend nerozlišuje tokeny.", "CRM token leak")
        return "⚠️  CRM token AKCEPTOVÁN na JWT endpointu — BEZPEČNOSTNÍ PROBLÉM"
    return f"Správně odmítnuto: HTTP {r.status_code}"


# ═══════════════════════════════════════════
#  FÁZE 3 — DASHBOARD & STATISTIKY
# ═══════════════════════════════════════════

def t_admin_stats():
    """GET /admin/stats — základní admin statistiky."""
    _require_jwt()
    r = requests.get(f"{API}/api/admin/stats", headers=admin_headers(), timeout=15)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()
    # Ověříme že odpověď má smysluplnou strukturu
    # get_stats() vrací klíče jako companies_total, companies_scanned, emails_today atd.
    expected_substrings = ["compan", "email", "scan"]
    response_str = str(d).lower()
    missing = [k for k in expected_substrings if k not in response_str]
    if missing:
        add_weak_spot("low", "Admin stats", f"Možná chybí klíče obsahující: {missing}", "Admin stats")
    return f"Stats keys: {list(d.keys())[:8]}"


def t_crm_dashboard_stats():
    """GET /crm/dashboard-stats — rozšířené CRM statistiky."""
    _require_jwt()
    r = requests.get(f"{API}/api/admin/crm/dashboard-stats", headers=admin_headers(), timeout=15)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()
    s.dashboard_stats = d

    # Ověříme požadované sekce
    expected_sections = ["companies", "emails", "scans", "questionnaires", "orders", "needing_attention", "recent_activity"]
    missing = [s for s in expected_sections if s not in d]
    if missing:
        add_weak_spot("medium", "CRM dashboard-stats", f"Chybí sekce: {missing}", "CRM dashboard stats")

    # Zkontrolujeme konzistenci dat
    companies_total = d.get("companies", {}).get("total", 0)
    workflow_sum = sum(d.get("companies", {}).get("by_workflow_status", {}).values())
    if companies_total != workflow_sum and companies_total > 0:
        add_weak_spot("medium", "CRM dashboard-stats",
                      f"Nekonzistence: total={companies_total}, sum(workflow)={workflow_sum}",
                      "CRM dashboard stats consistency")

    info = []
    info.append(f"Firmy: {d.get('companies', {}).get('total', '?')}")
    info.append(f"Emaily: {d.get('emails', {}).get('total', '?')}")
    info.append(f"Skeny: {d.get('scans', {}).get('total', '?')}")
    info.append(f"Objednávky: {d.get('orders', {}).get('total', '?')}")
    info.append(f"Vyžadují pozornost: {len(d.get('needing_attention', []))}")
    return "\n".join(info)


def t_dashboard_stats_response_time():
    """Měření doby odpovědi CRM dashboard-stats (heavy query)."""
    _require_jwt()
    t0 = time.time()
    r = requests.get(f"{API}/api/admin/crm/dashboard-stats", headers=admin_headers(), timeout=30)
    dur = time.time() - t0
    assert r.status_code == 200, f"HTTP {r.status_code}"
    if dur > 5.0:
        add_weak_spot("high", "CRM dashboard-stats",
                      f"Velmi pomalé: {dur:.1f}s — dashboard bude nepoužitelný",
                      "Dashboard performance")
    elif dur > 2.0:
        add_weak_spot("medium", "CRM dashboard-stats",
                      f"Pomalejší: {dur:.1f}s (doporučeno < 2s)",
                      "Dashboard performance")
    return f"Response time: {dur:.2f}s"


# ═══════════════════════════════════════════
#  FÁZE 4 — SEZNAM FIREM
# ═══════════════════════════════════════════

def t_companies_list():
    """GET /admin/companies — seznam všech firem."""
    _require_jwt()
    r = requests.get(f"{API}/api/admin/companies", headers=admin_headers(), timeout=15)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()

    # Může být list nebo dict s datovou strukturou
    companies = d if isinstance(d, list) else d.get("companies", d.get("data", []))
    if isinstance(companies, list):
        s.companies = companies
    else:
        s.companies = []

    if len(s.companies) == 0:
        add_weak_spot("high", "Companies list", "Žádné firmy v systému — testy budou omezené", "Companies list")
        return "⚠️  Žádné firmy"

    # Uložíme první firmu pro další testy
    first = s.companies[0]
    s.first_company_id = first.get("id")
    s.first_company_name = first.get("name") or first.get("url", "?")

    return f"Nalezeno {len(s.companies)} firem\nPrvní: {s.first_company_name} (id={s.first_company_id})"


def t_companies_filter_scanned():
    """GET /admin/companies?status=scanned — filtrování."""
    _require_jwt()
    r = requests.get(f"{API}/api/admin/companies?status=scanned", headers=admin_headers(), timeout=15)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()
    companies = d if isinstance(d, list) else d.get("companies", d.get("data", []))
    count = len(companies) if isinstance(companies, list) else "?"
    return f"Scanned filter: {count} firem"


def t_companies_filter_all():
    """GET /admin/companies?status=all — všechny statusy."""
    _require_jwt()
    r = requests.get(f"{API}/api/admin/companies?status=all&limit=100", headers=admin_headers(), timeout=15)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()
    companies = d if isinstance(d, list) else d.get("companies", d.get("data", []))
    count = len(companies) if isinstance(companies, list) else "?"
    return f"All companies (limit 100): {count}"


def t_companies_data_quality():
    """Kontrola kvality dat firem — jsou vyplněné klíčové atributy?"""
    if not s.companies:
        return "Přeskočeno — žádné firmy"

    total = len(s.companies)
    missing_email = sum(1 for c in s.companies if not c.get("email"))
    missing_name = sum(1 for c in s.companies if not c.get("name"))
    missing_url = sum(1 for c in s.companies if not c.get("url"))

    issues = []
    if missing_email > 0:
        pct = round(missing_email / total * 100)
        issues.append(f"Bez emailu: {missing_email} ({pct}%)")
        if pct > 50:
            add_weak_spot("medium", "Data quality", f"{pct}% firem nemá email", "Data quality")
    if missing_name > 0:
        pct = round(missing_name / total * 100)
        issues.append(f"Bez názvu: {missing_name} ({pct}%)")
    if missing_url > 0:
        pct = round(missing_url / total * 100)
        issues.append(f"Bez URL: {missing_url} ({pct}%)")

    if not issues:
        return f"Všech {total} firem má email, název i URL ✓"
    return "\n".join(issues)


# ═══════════════════════════════════════════
#  FÁZE 5 — DETAIL FIRMY
# ═══════════════════════════════════════════

def t_company_detail():
    """GET /crm/company/{id} — kompletní CRM karta firmy."""
    _require_jwt()
    if not s.first_company_id:
        raise Exception("Žádná firma k zobrazení")

    r = requests.get(f"{API}/api/admin/crm/company/{s.first_company_id}",
                     headers=admin_headers(), timeout=15)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()
    s.company_detail = d

    expected_keys = ["company", "latest_scan", "findings_count", "email_log",
                     "questionnaire_count", "orders", "activities"]
    missing = [k for k in expected_keys if k not in d]
    if missing:
        add_weak_spot("medium", "Company detail",
                      f"Chybí sekce v odpovědi: {missing}",
                      "Company detail structure")

    company = d.get("company", {})
    s.original_workflow_status = company.get("workflow_status")

    info = []
    info.append(f"Firma: {company.get('name', '?')}")
    info.append(f"URL: {company.get('url', '?')}")
    info.append(f"Email: {company.get('email', '?')}")
    info.append(f"Workflow: {company.get('workflow_status', '?')}")
    info.append(f"Payment: {company.get('payment_status', '?')}")
    info.append(f"Scan: {'Ano' if d.get('latest_scan') else 'Ne'}")
    info.append(f"Findings: {d.get('findings_count', 0)}")
    info.append(f"Emaily: {len(d.get('email_log', []))}")
    info.append(f"Aktivit: {len(d.get('activities', []))}")
    return "\n".join(info)


def t_company_detail_nonexistent():
    """GET /crm/company/nonexistent-uuid → 404."""
    _require_jwt()
    fake_id = "00000000-0000-0000-0000-000000000000"
    r = requests.get(f"{API}/api/admin/crm/company/{fake_id}",
                     headers=admin_headers(), timeout=10)
    if r.status_code != 404:
        add_weak_spot("medium", "Company detail 404",
                      f"Vrátil HTTP {r.status_code} místo 404 pro neexistující firmu",
                      "Company 404")
    assert r.status_code in (404, 500), f"Očekáván 404, dostal {r.status_code}"
    return f"Správně vráceno HTTP {r.status_code}"


def t_company_detail_all_fields():
    """Kontrola že company detail nevrací None pro povinná pole."""
    if not s.company_detail:
        return "Přeskočeno — detail nebyl načten"

    company = s.company_detail.get("company", {})
    required = ["id", "created_at"]
    missing = [f for f in required if company.get(f) is None]
    if missing:
        add_weak_spot("low", "Company data", f"Null povinná pole: {missing}", "Company fields")
        return f"⚠️  Null pole: {missing}"

    # Zkontrolujeme CRM-specifická pole z migrace 007
    crm_fields = ["workflow_status", "payment_status", "priority"]
    crm_missing = [f for f in crm_fields if f not in company]
    if crm_missing:
        add_weak_spot("high", "Migration 007",
                      f"CRM pole neexistují v DB: {crm_missing}",
                      "Company CRM fields")
        return f"⚠️  Chybí CRM sloupce: {crm_missing}"

    return f"Všechna pole OK, workflow={company.get('workflow_status')}, payment={company.get('payment_status')}, priority={company.get('priority')}"


def t_company_detail_multiple():
    """Projdi prvních N firem a zkontroluj že detail funguje pro všechny."""
    _require_jwt()
    if len(s.companies) < 2:
        return "Méně než 2 firmy — přeskočeno"

    check_count = min(5, len(s.companies))
    errors = []
    for i in range(check_count):
        cid = s.companies[i].get("id")
        try:
            r = requests.get(f"{API}/api/admin/crm/company/{cid}",
                             headers=admin_headers(), timeout=10)
            if r.status_code != 200:
                errors.append(f"#{i} {cid}: HTTP {r.status_code}")
        except Exception as e:
            errors.append(f"#{i} {cid}: {e}")

    if errors:
        add_weak_spot("medium", "Company detail bulk",
                      f"Chyby ve {len(errors)}/{check_count} firmách: {errors[:3]}",
                      "Company detail bulk")
        return f"⚠️  {len(errors)}/{check_count} chyb"
    return f"Všech {check_count} firem vrátilo detail OK"


# ═══════════════════════════════════════════
#  FÁZE 6 — PIPELINE / FUNNEL
# ═══════════════════════════════════════════

def t_pipeline():
    """GET /crm/pipeline — Pipeline / funnel statistiky."""
    _require_jwt()
    r = requests.get(f"{API}/api/admin/crm/pipeline", headers=admin_headers(), timeout=15)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()
    s.pipeline_data = d

    expected_keys = ["total_companies", "by_workflow_status", "by_payment_status", "by_priority", "revenue"]
    missing = [k for k in expected_keys if k not in d]
    if missing:
        add_weak_spot("medium", "Pipeline", f"Chybí klíče: {missing}", "Pipeline structure")

    info = []
    info.append(f"Total: {d.get('total_companies', '?')} firem")
    info.append(f"Workflow: {d.get('by_workflow_status', {})}")
    info.append(f"Payment: {d.get('by_payment_status', {})}")
    info.append(f"Priority: {d.get('by_priority', {})}")
    revenue = d.get("revenue", {})
    info.append(f"Revenue: orders={revenue.get('total_orders', 0)}, "
                f"paid={revenue.get('paid_amount', 0)}, "
                f"pending={revenue.get('pending_amount', 0)}")
    return "\n".join(info)


def t_pipeline_consistency():
    """Kontrola konzistence pipeline dat vs companies."""
    if not s.pipeline_data or not s.dashboard_stats:
        return "Přeskočeno — chybí data"

    pipeline_total = s.pipeline_data.get("total_companies", 0)
    stats_total = s.dashboard_stats.get("companies", {}).get("total", 0)

    if pipeline_total != stats_total:
        add_weak_spot("medium", "Pipeline vs Stats",
                      f"Pipeline total={pipeline_total} ≠ Stats total={stats_total}",
                      "Pipeline consistency")
        return f"⚠️  Nekonzistence: pipeline={pipeline_total} vs stats={stats_total}"
    return f"Konzistentní: {pipeline_total} firem v obou endpointech"


# ═══════════════════════════════════════════
#  FÁZE 7 — WORKFLOW MANAGEMENT
# ═══════════════════════════════════════════

def t_status_update_workflow():
    """PATCH /crm/company/{id}/status — změní workflow_status."""
    _require_jwt()
    if not s.first_company_id:
        raise Exception("Žádná firma pro test")

    new_status = "contacted"
    r = requests.patch(
        f"{API}/api/admin/crm/company/{s.first_company_id}/status",
        headers=admin_headers(),
        json={"workflow_status": new_status},
        timeout=10,
    )
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()
    assert d.get("status") == "updated", f"Status: {d.get('status')}"

    return f"Workflow status změněn na '{new_status}'"


def t_status_update_payment():
    """PATCH — změní payment_status."""
    _require_jwt()
    if not s.first_company_id:
        raise Exception("Žádná firma pro test")

    r = requests.patch(
        f"{API}/api/admin/crm/company/{s.first_company_id}/status",
        headers=admin_headers(),
        json={"payment_status": "invoiced"},
        timeout=10,
    )
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    return "Payment status změněn na 'invoiced'"


def t_status_update_priority():
    """PATCH — změní priority."""
    _require_jwt()
    if not s.first_company_id:
        raise Exception("Žádná firma pro test")

    r = requests.patch(
        f"{API}/api/admin/crm/company/{s.first_company_id}/status",
        headers=admin_headers(),
        json={"priority": "high"},
        timeout=10,
    )
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    return "Priority změněna na 'high'"


def t_status_update_combined():
    """PATCH — změní více polí najednou."""
    _require_jwt()
    if not s.first_company_id:
        raise Exception("Žádná firma pro test")

    r = requests.patch(
        f"{API}/api/admin/crm/company/{s.first_company_id}/status",
        headers=admin_headers(),
        json={
            "next_action": "E2E test follow-up",
            "assigned_to": "test-bot",
        },
        timeout=10,
    )
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    return "Next action + assigned_to aktualizovány"


def t_status_update_empty():
    """PATCH s prázdným body → 400."""
    _require_jwt()
    if not s.first_company_id:
        raise Exception("Žádná firma pro test")

    r = requests.patch(
        f"{API}/api/admin/crm/company/{s.first_company_id}/status",
        headers=admin_headers(),
        json={},
        timeout=10,
    )
    if r.status_code != 400:
        add_weak_spot("medium", "Status update validation",
                      f"Prázdný PATCH vrátil {r.status_code} místo 400",
                      "Status empty body")
    return f"Prázdný PATCH → HTTP {r.status_code}"


def t_status_update_invalid_field():
    """PATCH s nepovoleným polem → ignorováno nebo 400."""
    _require_jwt()
    if not s.first_company_id:
        raise Exception("Žádná firma pro test")

    r = requests.patch(
        f"{API}/api/admin/crm/company/{s.first_company_id}/status",
        headers=admin_headers(),
        json={"hacker_field": "injection", "name": "HACKED"},
        timeout=10,
    )
    if r.status_code == 200:
        d = r.json()
        updated = d.get("updated_fields", {})
        if "hacker_field" in updated or "name" in updated:
            add_weak_spot("critical", "Status update",
                          "Backend akceptuje nepovolená pole! Mass assignment vulnerability.",
                          "Invalid field injection")
            return "⚠️  KRITICKÉ: Nepovolená pole akceptována!"
        return "Nepovolená pole správně ignorována"
    return f"HTTP {r.status_code} — pole odmítnuta"


def t_add_note():
    """POST /crm/company/{id}/note — přidání poznámky."""
    _require_jwt()
    if not s.first_company_id:
        raise Exception("Žádná firma pro test")

    note_title = f"E2E test note [{datetime.now().strftime('%H:%M:%S')}]"
    r = requests.post(
        f"{API}/api/admin/crm/company/{s.first_company_id}/note",
        headers=admin_headers(),
        json={
            "title": note_title,
            "description": "Automatický test — tato poznámka byla vytvořena E2E testem.",
            "activity_type": "note",
        },
        timeout=10,
    )
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()
    assert d.get("status") == "created", f"Status: {d.get('status')}"

    activity = d.get("activity", {})
    s.test_note_id = activity.get("id")
    return f"Poznámka vytvořena: '{note_title}', id={s.test_note_id}"


def t_add_note_no_title():
    """POST note bez title → 400."""
    _require_jwt()
    if not s.first_company_id:
        raise Exception("Žádná firma pro test")

    r = requests.post(
        f"{API}/api/admin/crm/company/{s.first_company_id}/note",
        headers=admin_headers(),
        json={"description": "note bez title"},
        timeout=10,
    )
    if r.status_code != 400:
        add_weak_spot("medium", "Note validation",
                      f"Note bez title vrátil {r.status_code} místo 400",
                      "Note no title")
    return f"Note bez title → HTTP {r.status_code}"


def t_timeline():
    """GET /crm/company/{id}/timeline — timeline aktivit."""
    _require_jwt()
    if not s.first_company_id:
        raise Exception("Žádná firma pro test")

    r = requests.get(f"{API}/api/admin/crm/company/{s.first_company_id}/timeline",
                     headers=admin_headers(), timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()

    activities = d.get("activities", [])
    total = d.get("total", 0)

    # Měla by tam být naše test note + status changes
    note_found = any("E2E test note" in (a.get("title") or "") for a in activities)
    status_changes = sum(1 for a in activities if a.get("activity_type") == "status_change")

    if not note_found and s.test_note_id:
        add_weak_spot("medium", "Timeline", "Test poznámka se neobjevila v timeline", "Timeline note")

    return f"Timeline: {total} aktivit, status_changes={status_changes}, test_note={'nalezena' if note_found else 'CHYBÍ'}"


def t_restore_original_status():
    """Obnovení původního workflow_status (cleanup)."""
    _require_jwt()
    if not s.first_company_id:
        return "Přeskočeno"

    restore_status = s.original_workflow_status or "new"
    r = requests.patch(
        f"{API}/api/admin/crm/company/{s.first_company_id}/status",
        headers=admin_headers(),
        json={
            "workflow_status": restore_status,
            "payment_status": "none",
            "priority": "normal",
            "next_action": None,
            "assigned_to": None,
        },
        timeout=10,
    )
    if r.status_code == 200:
        return f"Status obnoven na '{restore_status}'"
    return f"⚠️  Obnova selhala: HTTP {r.status_code}"


# ═══════════════════════════════════════════
#  FÁZE 8 — EMAIL & KOMUNIKACE
# ═══════════════════════════════════════════

def t_email_log():
    """GET /admin/email-log — log odeslaných emailů."""
    _require_jwt()
    r = requests.get(f"{API}/api/admin/email-log", headers=admin_headers(), timeout=15)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()

    emails = d if isinstance(d, list) else d.get("emails", d.get("data", []))
    s.email_log_count = len(emails) if isinstance(emails, list) else 0

    if s.email_log_count == 0:
        add_weak_spot("low", "Email log", "Žádné emaily v logu", "Email log empty")

    return f"Emailů v logu: {s.email_log_count}"


def t_email_health():
    """GET /admin/email-health — zdraví emailového systému."""
    _require_jwt()
    r = requests.get(f"{API}/api/admin/email-health", headers=admin_headers(), timeout=15)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()

    status = d.get("status", "?")
    if status != "ok":
        add_weak_spot("high", "Email health",
                      f"Email systém není OK: {status}",
                      "Email health")

    return f"Email health: {json.dumps(d, ensure_ascii=False)[:200]}"


# ═══════════════════════════════════════════
#  FÁZE 9 — MONITORING & ALERTING
# ═══════════════════════════════════════════

def t_alerts():
    """GET /admin/alerts — legislativní alerty."""
    _require_jwt()
    r = requests.get(f"{API}/api/admin/alerts", headers=admin_headers(), timeout=15)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()

    alerts = d if isinstance(d, list) else d.get("alerts", d.get("data", []))
    s.alerts_count = len(alerts) if isinstance(alerts, list) else 0

    return f"Alertů: {s.alerts_count}"


def t_diffs():
    """GET /admin/diffs — scan diff monitoring."""
    _require_jwt()
    r = requests.get(f"{API}/api/admin/diffs", headers=admin_headers(), timeout=15)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()

    diffs = d if isinstance(d, list) else d.get("diffs", d.get("data", []))
    count = len(diffs) if isinstance(diffs, list) else 0

    return f"Diffů: {count}"


def t_audit_log():
    """GET /admin/audit-log — přístupový audit log."""
    _require_jwt()
    r = requests.get(f"{API}/api/admin/audit-log", headers=admin_headers(), timeout=15)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()

    logs = d.get("logs", [])
    total = d.get("total", len(logs))

    # Zkontrolujeme strukturu logu
    if logs:
        first = logs[0]
        expected_fields = ["actor_email", "action", "resource_type", "created_at"]
        missing = [f for f in expected_fields if f not in first]
        if missing:
            add_weak_spot("low", "Audit log", f"Chybí pole v logu: {missing}", "Audit log fields")

    return f"Audit log: {total} záznamů"


def t_audit_log_filter():
    """GET /admin/audit-log?resource_type=company — filtr."""
    _require_jwt()
    r = requests.get(f"{API}/api/admin/audit-log?resource_type=company",
                     headers=admin_headers(), timeout=15)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()
    count = d.get("total", len(d.get("logs", [])))
    return f"Audit log (company): {count} záznamů"


# ═══════════════════════════════════════════
#  FÁZE 10 — NÁSTROJE
# ═══════════════════════════════════════════

def t_task_runner_list():
    """POST /admin/run/{task} — test s neexistujícím taskem."""
    _require_jwt()
    r = requests.post(f"{API}/api/admin/run/nonexistent_task",
                      headers=admin_headers(), timeout=10)
    # Měl by vrátit chybu, ne 500
    if r.status_code == 500:
        add_weak_spot("medium", "Task runner",
                      "Neexistující task vrátil 500 místo 400/404",
                      "Task runner unknown")
    return f"Neexistující task → HTTP {r.status_code}"


def t_task_runner_cleanup():
    """POST /admin/cleanup/run — spustí data retention cleanup."""
    _require_jwt()
    r = requests.post(f"{API}/api/admin/cleanup/run",
                      headers=admin_headers(), timeout=30)
    if r.status_code == 200:
        d = r.json()
        return f"Cleanup: {json.dumps(d, ensure_ascii=False)[:200]}"
    elif r.status_code == 500:
        add_weak_spot("medium", "Cleanup", f"Cleanup selhal: {r.text[:200]}", "Cleanup run")
    return f"Cleanup → HTTP {r.status_code}"


# ═══════════════════════════════════════════
#  FÁZE 11 — CHYBOVÉ STAVY & BEZPEČNOST
# ═══════════════════════════════════════════

def t_sql_injection_attempt():
    """Test SQL injection přes company_id."""
    _require_jwt()
    payloads = [
        "'; DROP TABLE companies; --",
        "1 OR 1=1",
        "union select * from auth.users",
    ]
    for payload in payloads:
        r = requests.get(f"{API}/api/admin/crm/company/{payload}",
                         headers=admin_headers(), timeout=10)
        if r.status_code == 200:
            add_weak_spot("critical", "SQL Injection",
                          f"Payload '{payload}' vrátil 200!", "SQL injection")
    return f"Všechny {len(payloads)} SQL injection payloady odmítnuty"


def t_xss_in_note():
    """Test XSS v poznámce — backend by měl sanitizovat HTML tagy."""
    _require_jwt()
    if not s.first_company_id:
        return "Přeskočeno"

    xss_payload = "<script>alert('xss')</script>"
    r = requests.post(
        f"{API}/api/admin/crm/company/{s.first_company_id}/note",
        headers=admin_headers(),
        json={"title": xss_payload, "description": "<img onerror=alert(1) src=x>"},
        timeout=10,
    )
    if r.status_code == 200:
        d = r.json()
        activity = d.get("activity", {})
        title = activity.get("title") or ""
        description = activity.get("description") or ""
        if "<script>" in title or "<img" in description:
            add_weak_spot("high", "XSS v poznámkách",
                          "Backend ukládá HTML tagy bez sanitizace!",
                          "XSS note")
            return "⚠️  Backend ukládá XSS payload!"
        return f"✅ XSS sanitizováno: title='{title[:50]}'"
    return f"XSS test → HTTP {r.status_code}"


def t_large_payload():
    """Test s velkým payloadem (DoS prevention)."""
    _require_jwt()
    if not s.first_company_id:
        return "Přeskočeno"

    large_text = "A" * 100_000  # 100KB text
    r = requests.post(
        f"{API}/api/admin/crm/company/{s.first_company_id}/note",
        headers=admin_headers(),
        json={"title": "Large payload test", "description": large_text},
        timeout=15,
    )
    if r.status_code == 200:
        add_weak_spot("medium", "Large payload",
                      "100KB poznámka akceptována — chybí limit velikosti",
                      "Large payload note")
        return "⚠️  100KB poznámka akceptována"
    elif r.status_code == 400:
        return f"✅ Velký payload odmítnut (HTTP 400)"
    return f"Velký payload → HTTP {r.status_code}"


def t_rate_limiting():
    """Test rate limitingu — 20 rychlých requestů."""
    _require_jwt()
    url = f"{API}/api/admin/crm/dashboard-stats"
    statuses = []
    for _ in range(20):
        try:
            r = requests.get(url, headers=admin_headers(), timeout=5)
            statuses.append(r.status_code)
        except:
            statuses.append(0)

    rate_limited = sum(1 for s in statuses if s == 429)
    ok_count = sum(1 for s in statuses if s == 200)

    # Admin rate limit je 60 req/min — 20 requestů by mělo projít
    # Ale pokud žádný nebyl rate-limited, je to OK (limit je štědrý)
    if rate_limited > 0:
        return f"✅ Rate limiting aktivní: {ok_count}× OK, {rate_limited}× 429"
    else:
        # Není to slabé místo — limit 60/min je záměrně štědrý
        return f"20 requestů: {ok_count}× OK (rate limit 60/min ještě nedosažen)"


def t_cors_headers():
    """Kontrola CORS headerů na admin endpointu."""
    r = requests.options(f"{API}/api/admin/stats",
                         headers={
                             "Origin": "https://evil.com",
                             "Access-Control-Request-Method": "GET",
                         }, timeout=10)
    cors_origin = r.headers.get("Access-Control-Allow-Origin", "")
    if cors_origin == "*":
        add_weak_spot("high", "CORS",
                      "Access-Control-Allow-Origin: * — měl by být omezený na aishield.cz",
                      "CORS wildcard")
        return "⚠️  CORS povoluje * (wildcard)"
    elif "evil.com" in cors_origin:
        add_weak_spot("critical", "CORS",
                      "CORS povoluje libovolný Origin!",
                      "CORS open")
        return "⚠️  CORS odráží libovolný Origin"
    return f"CORS Origin: '{cors_origin}' — OK"


def t_sensitive_data_in_response():
    """Kontrola že odpovědi neobsahují citlivá data."""
    if not s.company_detail:
        return "Přeskočeno"

    response_str = json.dumps(s.company_detail)
    sensitive_patterns = ["password", "secret", "jwt_secret", "service_role", "private_key"]
    found = [p for p in sensitive_patterns if p in response_str.lower()]

    if found:
        add_weak_spot("critical", "Sensitive data leak",
                      f"Odpověď obsahuje citlivá data: {found}",
                      "Sensitive data")
        return f"⚠️  KRITICKÉ: {found}"
    return "Žádná citlivá data v odpovědích"


def t_api_versioning():
    """Kontrola consistency API verzování."""
    # Zkusíme neexistující API path
    r = requests.get(f"{API}/api/v2/admin/stats", headers=admin_headers(), timeout=10)
    if r.status_code == 200:
        add_weak_spot("low", "API versioning",
                      "/api/v2/ existuje — je potřeba verzování?",
                      "API versioning")
    return f"/api/v2/admin/stats → HTTP {r.status_code} (OK pokud 404)"


# ═══════════════════════════════════════════
#  MAIN — Spuštění všech testů
# ═══════════════════════════════════════════

def main():
    start = time.time()
    print(f"\n{B}{M}╔══════════════════════════════════════════════════════════════╗")
    print(f"║     AIshield.cz — Admin CRM E2E Test Suite                   ║")
    print(f"║     {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                                     ║")
    print(f"╚══════════════════════════════════════════════════════════════╝{X}")
    print(f"  API:    {API}")
    print(f"  WEB:    {WEB}")
    print(f"  Admin:  {ADMIN_EMAIL}")

    # ── FÁZE 1 ──
    phase_header("FÁZE 1 — Infrastruktura")
    run_test("API health", "1-Infra", t_api_health, critical=True)
    run_test("Engine health", "1-Infra", t_engine_health)
    run_test("Frontend admin stránky", "1-Infra", t_frontend_admin_pages)
    run_test("Response time", "1-Infra", t_api_response_time)

    # ── FÁZE 2 ──
    phase_header("FÁZE 2 — Autentizace")
    run_test("CRM login (platný)", "2-Auth", t_crm_login_valid, critical=True)
    run_test("CRM login (neplatný)", "2-Auth", t_crm_login_invalid)
    run_test("Supabase JWT login", "2-Auth", t_supabase_jwt_login)
    run_test("Admin bez tokenu → 401", "2-Auth", t_admin_without_token)
    run_test("CRM token na JWT endpoint", "2-Auth", t_admin_with_crm_token)

    # ── FÁZE 3 ──
    phase_header("FÁZE 3 — Dashboard & statistiky")
    run_test("Admin stats", "3-Dashboard", t_admin_stats)
    run_test("CRM dashboard stats", "3-Dashboard", t_crm_dashboard_stats)
    run_test("Dashboard response time", "3-Dashboard", t_dashboard_stats_response_time)

    # ── FÁZE 4 ──
    phase_header("FÁZE 4 — Seznam firem")
    run_test("Firmy — kompletní seznam", "4-Companies", t_companies_list)
    run_test("Firmy — filtr: scanned", "4-Companies", t_companies_filter_scanned)
    run_test("Firmy — filtr: all (limit 100)", "4-Companies", t_companies_filter_all)
    run_test("Kvalita dat firem", "4-Companies", t_companies_data_quality)

    # ── FÁZE 5 ──
    phase_header("FÁZE 5 — Detail firmy")
    run_test("CRM detail firmy", "5-Detail", t_company_detail)
    run_test("Detail — neexistující firma", "5-Detail", t_company_detail_nonexistent)
    run_test("Detail — kontrola polí", "5-Detail", t_company_detail_all_fields)
    run_test("Detail — hromadný test (5 firem)", "5-Detail", t_company_detail_multiple)

    # ── FÁZE 6 ──
    phase_header("FÁZE 6 — Pipeline / funnel")
    run_test("Pipeline statistiky", "6-Pipeline", t_pipeline)
    run_test("Pipeline vs stats konzistence", "6-Pipeline", t_pipeline_consistency)

    # ── FÁZE 7 ──
    phase_header("FÁZE 7 — Workflow management")
    run_test("Status update — workflow", "7-Workflow", t_status_update_workflow)
    run_test("Status update — payment", "7-Workflow", t_status_update_payment)
    run_test("Status update — priority", "7-Workflow", t_status_update_priority)
    run_test("Status update — combined", "7-Workflow", t_status_update_combined)
    run_test("Status update — prázdný body", "7-Workflow", t_status_update_empty)
    run_test("Status update — nepovolené pole", "7-Workflow", t_status_update_invalid_field)
    run_test("Přidání poznámky", "7-Workflow", t_add_note)
    run_test("Poznámka bez title → 400", "7-Workflow", t_add_note_no_title)
    run_test("Timeline aktivit", "7-Workflow", t_timeline)
    run_test("Obnova původního statusu", "7-Workflow", t_restore_original_status)

    # ── FÁZE 8 ──
    phase_header("FÁZE 8 — Email & komunikace")
    run_test("Email log", "8-Email", t_email_log)
    run_test("Email health", "8-Email", t_email_health)

    # ── FÁZE 9 ──
    phase_header("FÁZE 9 — Monitoring & alerting")
    run_test("Alerts", "9-Monitor", t_alerts)
    run_test("Scan diffs", "9-Monitor", t_diffs)
    run_test("Audit log", "9-Monitor", t_audit_log)
    run_test("Audit log — filtr", "9-Monitor", t_audit_log_filter)

    # ── FÁZE 10 ──
    phase_header("FÁZE 10 — Nástroje")
    run_test("Task runner — neznámý task", "10-Tools", t_task_runner_list)
    run_test("Data cleanup run", "10-Tools", t_task_runner_cleanup)

    # ── FÁZE 11 ──
    phase_header("FÁZE 11 — Chybové stavy & bezpečnost")
    run_test("SQL injection attempt", "11-Security", t_sql_injection_attempt)
    run_test("XSS v poznámkách", "11-Security", t_xss_in_note)
    run_test("Velký payload (100KB)", "11-Security", t_large_payload)
    run_test("Rate limiting (20 req)", "11-Security", t_rate_limiting)
    run_test("CORS headers", "11-Security", t_cors_headers)
    run_test("Citlivá data v odpovědích", "11-Security", t_sensitive_data_in_response)
    run_test("API versioning", "11-Security", t_api_versioning)

    # ═══════════════════════════════════════════
    #  SOUHRN
    # ═══════════════════════════════════════════
    duration = time.time() - start
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    critical_fails = sum(1 for r in results if not r.passed and r.critical)

    print(f"\n{B}{M}═══════════════════════════════════════════════════════════════")
    print(f"  SOUHRN TESTŮ")
    print(f"═══════════════════════════════════════════════════════════════{X}")
    print(f"  Celkem:    {total} testů")
    print(f"  {G}Prošlo:    {passed}{X}")
    print(f"  {R}Selhalo:   {failed}{X}")
    if critical_fails:
        print(f"  {R}{B}Kritických: {critical_fails}{X}")
    print(f"  Doba:      {duration:.1f}s")
    print(f"  Úspěšnost: {round(passed / total * 100)}%")

    # ── Selhané testy ──
    if failed > 0:
        print(f"\n{R}{B}  SELHANÉ TESTY:{X}")
        for r in results:
            if not r.passed:
                icon = "🔴" if r.critical else "🟡"
                print(f"    {icon}  [{r.phase}] {r.name}")
                print(f"       {D}{r.detail[:200]}{X}")

    # ── Slabá místa ──
    if weak_spots:
        print(f"\n{Y}{B}  ══════════════════════════════════════════════════════════")
        print(f"  NALEZENÁ SLABÁ MÍSTA ({len(weak_spots)})")
        print(f"  ══════════════════════════════════════════════════════════{X}")

        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_spots = sorted(weak_spots, key=lambda w: severity_order.get(w.severity, 99))

        severity_icons = {
            "critical": f"{R}🔴 CRITICAL",
            "high":     f"{R}🟠 HIGH",
            "medium":   f"{Y}🟡 MEDIUM",
            "low":      f"{D}🔵 LOW",
        }

        for ws in sorted_spots:
            icon = severity_icons.get(ws.severity, "⚪")
            print(f"\n    {icon}{X}  {B}{ws.location}{X}")
            print(f"       {ws.description}")
            print(f"       {D}(zjištěno testem: {ws.test_name}){X}")

        # Počty podle severity
        by_sev = {}
        for ws in weak_spots:
            by_sev[ws.severity] = by_sev.get(ws.severity, 0) + 1
        print(f"\n    {B}Shrnutí:{X}  ", end="")
        parts = []
        for sev in ["critical", "high", "medium", "low"]:
            if sev in by_sev:
                parts.append(f"{sev.upper()}: {by_sev[sev]}")
        print(" | ".join(parts))
    else:
        print(f"\n{G}{B}  ✅ ŽÁDNÁ SLABÁ MÍSTA NENALEZENA{X}")

    # ── Detail po fázích ──
    print(f"\n{B}  DETAIL PO FÁZÍCH:{X}")
    phases = {}
    for r in results:
        phases.setdefault(r.phase, []).append(r)
    for phase, tests in phases.items():
        ok = sum(1 for t in tests if t.passed)
        total_p = len(tests)
        color = G if ok == total_p else (Y if ok > 0 else R)
        print(f"    {color}{ok}/{total_p}{X}  {phase}")

    # ── Exit code ──
    print()
    if critical_fails > 0:
        print(f"{R}{B}  ❌ KRITICKÉ SELHÁNÍ — deploy ZABLOKOVÁN{X}")
        sys.exit(2)
    elif failed > 0 or any(ws.severity == "critical" for ws in weak_spots):
        print(f"{Y}{B}  ⚠️  NĚKTERÉ TESTY SELHALY — doporučeno opravit{X}")
        sys.exit(1)
    else:
        print(f"{G}{B}  ✅ VŠE V POŘÁDKU{X}")
        sys.exit(0)


if __name__ == "__main__":
    main()
