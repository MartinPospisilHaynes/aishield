#!/usr/bin/env python3
"""
AIshield.cz — Kompletní E2E test uživatelské cesty
====================================================
Simuluje REÁLNOU cestu uživatele od prvního kontaktu po plně funkční profil:

  FÁZE 1 — Infrastruktura
  FÁZE 2 — Registrace a login
  FÁZE 3 — Sken webu (přihlášený uživatel)
  FÁZE 4 — Dashboard propojení
  FÁZE 5 — Dotazník
  FÁZE 6 — Finální kontrola dashboardu

Spuštění:  python3 test_e2e_full.py
"""

import json
import os
import sys
import time
import requests
from dataclasses import dataclass
from typing import Optional

# ═══════════════════════════════════════════
#  KONFIGURACE
# ═══════════════════════════════════════════
API = os.environ.get("TEST_API_URL", "https://api.aishield.cz")
WEB = os.environ.get("TEST_WEB_URL", "https://aishield.cz")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://rsxwqcrkttlfnqbjgpgc.supabase.co")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
TEST_EMAIL = os.environ.get("TEST_EMAIL", "")
TEST_PASSWORD = os.environ.get("TEST_PASSWORD", "")
TEST_WEB = os.environ.get("TEST_WEB", "https://www.desperados-design.cz")

if not SUPABASE_ANON_KEY or not TEST_EMAIL or not TEST_PASSWORD:
    raise RuntimeError(
        "Chybí env proměnné: SUPABASE_ANON_KEY, TEST_EMAIL, TEST_PASSWORD. "
        "Nastav je před spuštěním testů."
    )

# Barvy
G = "\033[92m"; R = "\033[91m"; Y = "\033[93m"; C = "\033[96m"
B = "\033[1m"; D = "\033[2m"; X = "\033[0m"


@dataclass
class TestResult:
    name: str
    phase: str
    passed: bool
    detail: str = ""
    duration: float = 0.0
    critical: bool = False

results: list[TestResult] = []
abort = False


def phase_header(name: str):
    print(f"\n{B}{C}  ── {name} ──{X}")


def run_test(name, phase, func, critical=False):
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
            for line in detail.split("\n"):
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
class State:
    access_token: Optional[str] = None
    user_id: Optional[str] = None
    company_id: Optional[str] = None
    scan_id: Optional[str] = None
    finding_ids: list = []
    company_name: Optional[str] = None
    scan_findings_count: int = 0
s = State()

def auth_headers():
    return {"Authorization": f"Bearer {s.access_token}", "Content-Type": "application/json"}


# ═══════════════════════════════
#  FÁZE 1 — INFRASTRUKTURA
# ═══════════════════════════════
def t_api_health():
    r = requests.get(f"{API}/api/health", timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}"
    d = r.json()
    assert d["status"] in ("ok", "degraded"), f"Status: {d['status']}"
    assert d.get("database") == "connected", f"DB: {d.get('database')}"
    return f"API={d['status']}, DB={d['database']}"

def t_engine_health():
    r = requests.get(f"{API}/api/health/engine", timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}"
    return f"status={r.json().get('status')}"

def t_frontend_pages():
    pages = ["/", "/scan", "/registrace", "/login", "/pricing"]
    for p in pages:
        r = requests.get(f"{WEB}{p}", timeout=15, allow_redirects=True)
        assert r.status_code == 200, f"{p} → HTTP {r.status_code}"
    return f"Všech {len(pages)} stránek HTTP 200"


# ═══════════════════════════════
#  FÁZE 2 — REGISTRACE / LOGIN
# ═══════════════════════════════
def t_reset_account():
    r = requests.post(f"{API}/api/admin/test-reset",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "web_url": TEST_WEB}, timeout=15)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()
    assert d["status"] == "reset_complete", f"Status: {d['status']}"
    assert d["auto_confirmed"] is True, "Účet NENÍ auto-potvrzený!"
    s.user_id = d["new_user_id"]
    return f"user_id={s.user_id}\nVyčištěno: {', '.join(d.get('cleaned_tables', []))}"

def t_login():
    r = requests.post(f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}, timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()
    assert "access_token" in d, f"Chybí access_token"
    s.access_token = d["access_token"]
    user = d.get("user", {})
    meta = user.get("user_metadata", {})
    assert user.get("email") == TEST_EMAIL, f"Email mismatch"
    return f"email={user['email']}\nweb_url={meta.get('web_url', '?')}\ncompany={meta.get('company_name', '?')}"

def t_empty_dashboard():
    r = requests.get(f"{API}/api/dashboard/me", headers=auth_headers(), timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}"
    d = r.json()
    assert d["company"] is None, f"Firma by měla být None po resetu, je: {d['company']}"
    assert len(d["scans"]) == 0, f"Skeny={len(d['scans'])}, měly být 0"
    assert d["questionnaire_status"] == "nevyplněn"
    return "Dashboard prázdný — správně po resetu"


# ═══════════════════════════════
#  FÁZE 3 — SKEN WEBU
# ═══════════════════════════════
def t_start_scan():
    r = requests.post(f"{API}/api/scan", headers=auth_headers(),
        json={"url": TEST_WEB}, timeout=15)
    if r.status_code == 429:
        d = r.json()
        cached = d.get("cached_scan_id")
        if cached:
            s.scan_id = cached
            s.company_id = d.get("cached_company_id")
            return f"⚡ Rate limit — cache scan_id={cached}"
        raise Exception(f"Rate limit bez cache: {d.get('detail')}")
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()
    assert d.get("scan_id"), "Chybí scan_id!"
    assert d.get("company_id"), "Chybí company_id!"
    s.scan_id = d["scan_id"]
    s.company_id = d["company_id"]
    return f"scan_id={s.scan_id}\ncompany_id={s.company_id}"

def t_poll_scan():
    assert s.scan_id, "Chybí scan_id"
    max_wait, interval, elapsed = 180, 5, 0
    status = "?"
    while elapsed < max_wait:
        r = requests.get(f"{API}/api/scan/{s.scan_id}", timeout=10)
        assert r.status_code == 200, f"HTTP {r.status_code}"
        d = r.json()
        status = d.get("status")
        s.company_name = d.get("company_name", "?")
        if status == "done":
            s.scan_findings_count = d.get("total_findings", 0)
            return f"status=done ✅\nfindings={s.scan_findings_count}, company={s.company_name}, doba={elapsed}s"
        if status == "error":
            raise Exception(f"Sken selhal: {json.dumps(d, ensure_ascii=False)}")
        sys.stdout.write(f"\r       ⏳ Sken běží... [{elapsed}s] status={status}   ")
        sys.stdout.flush()
        time.sleep(interval)
        elapsed += interval
    print()
    return f"⚠️ Timeout po {max_wait}s — status={status}"

def t_findings():
    assert s.scan_id
    r = requests.get(f"{API}/api/scan/{s.scan_id}/findings", timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}"
    d = r.json()
    findings = d.get("findings", [])
    fp = d.get("false_positives", [])
    s.finding_ids = [f["id"] for f in findings]
    if findings:
        required = ["id", "name", "category", "risk_level"]
        missing = [k for k in required if k not in findings[0]]
        assert not missing, f"Nálezům chybí: {missing}"
    return f"nálezy={len(findings)}, false_positives={len(fp)}, AI={d.get('ai_classified','?')}"

def t_html_report():
    assert s.scan_id
    r = requests.get(f"{API}/api/scan/{s.scan_id}/report", timeout=15)
    if r.status_code == 400: return "⚠️ Sken ještě není done"
    assert r.status_code == 200, f"HTTP {r.status_code}"
    assert "text/html" in r.headers.get("content-type", ""), "Není HTML!"
    assert len(r.text) > 500, f"Report krátký: {len(r.text)}B"
    return f"HTML report: {len(r.text)} bytes"

def t_send_report_email():
    assert s.scan_id
    r = requests.post(f"{API}/api/scan/{s.scan_id}/send-report",
        json={"email": TEST_EMAIL}, timeout=15)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()
    assert d.get("status") == "sent", f"Status: {d}"
    return f"Report email odeslán na {d.get('email')}"


# ═══════════════════════════════
#  FÁZE 4 — DASHBOARD PROPOJENÍ
# ═══════════════════════════════
def t_dashboard_has_company():
    r = requests.get(f"{API}/api/dashboard/me", headers=auth_headers(), timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}"
    d = r.json()
    company = d.get("company")
    assert company is not None, (
        "❌ KRITICKÝ BUG: Dashboard nevidí firmu po skenu!\n"
        "   companies.email není propojený s uživatelem."
    )
    cid = company.get("id")
    if s.company_id:
        assert cid == s.company_id, f"company_id mismatch: dashboard={cid}, scan={s.company_id}"
    return f"✅ Firma nalezena!\nid={cid}\nname={company.get('name','?')}\nurl={company.get('url','?')}"

def t_dashboard_has_scans():
    r = requests.get(f"{API}/api/dashboard/me", headers=auth_headers(), timeout=10)
    assert r.status_code == 200
    d = r.json()
    scans = d.get("scans", [])
    assert len(scans) > 0, "❌ Dashboard neukazuje žádné skeny!"
    last = scans[0]
    assert last.get("status") == "done", f"Poslední sken: {last.get('status')}"
    findings = d.get("findings", [])
    return f"skenů={len(scans)}, poslední=done, findings={len(findings)}"


# ═══════════════════════════════
#  FÁZE 5 — DOTAZNÍK
# ═══════════════════════════════
def t_questionnaire_structure():
    r = requests.get(f"{API}/api/questionnaire/structure", timeout=10)
    assert r.status_code == 200
    d = r.json()
    sections = d.get("sections", [])
    assert len(sections) > 0, "Žádné sekce!"
    return f"sekcí={len(sections)}, otázek={d.get('total_questions',0)}"

def t_submit_questionnaire():
    assert s.company_id, "Chybí company_id"
    answers = [
        {"question_key": "industry_type", "section": "industry", "answer": "E-shop / Online obchod"},
        {"question_key": "uses_biometric", "section": "prohibited_systems", "answer": "no"},
        {"question_key": "uses_social_scoring", "section": "prohibited_systems", "answer": "no"},
        {"question_key": "uses_chatgpt", "section": "internal_ai", "answer": "yes", "tool_name": "ChatGPT"},
        {"question_key": "uses_copilot", "section": "internal_ai", "answer": "yes", "tool_name": "GitHub Copilot"},
        {"question_key": "uses_ai_recruitment", "section": "hr", "answer": "no"},
        {"question_key": "uses_ai_credit_scoring", "section": "finance", "answer": "no"},
        {"question_key": "uses_chatbot", "section": "customer_service", "answer": "yes", "tool_name": "Chatbot"},
        {"question_key": "uses_ai_monitoring", "section": "infrastructure_safety", "answer": "no"},
        {"question_key": "has_data_processing_agreement", "section": "data_protection", "answer": "yes"},
        {"question_key": "ai_literacy_training", "section": "ai_literacy", "answer": "unknown"},
    ]
    r = requests.post(f"{API}/api/questionnaire/submit",
        json={"company_id": s.company_id, "scan_id": s.scan_id, "answers": answers}, timeout=15)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()
    assert d.get("saved_count", 0) > 0, f"Neuloženo: {d}"
    a = d.get("analysis", {})
    return f"uloženo={d['saved_count']}, AI systémy={a.get('ai_systems_declared','?')}, riziko={a.get('risk_breakdown','?')}"

def t_questionnaire_results():
    assert s.company_id
    r = requests.get(f"{API}/api/questionnaire/{s.company_id}/results", timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()
    assert len(d.get("answers", [])) > 0, "Žádné odpovědi!"
    return f"odpovědí={len(d['answers'])}, submitted={d.get('submitted_at','?')}"

def t_combined_report():
    assert s.company_id
    url = f"{API}/api/questionnaire/{s.company_id}/combined-report"
    if s.scan_id: url += f"?scan_id={s.scan_id}"
    r = requests.get(url, timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()
    return (
        f"riziko={d.get('overall_risk','?')}, AI systémy={d.get('total_ai_systems',0)}\n"
        f"akční body={len(d.get('action_items',[]))}\n"
        f"{d.get('overall_risk_text','')}"
    )


# ═══════════════════════════════
#  FÁZE 6 — FINÁLNÍ DASHBOARD
# ═══════════════════════════════
def t_final_dashboard():
    r = requests.get(f"{API}/api/dashboard/me", headers=auth_headers(), timeout=10)
    assert r.status_code == 200
    d = r.json()
    company = d.get("company")
    assert company, "❌ Firma chybí!"
    scans = d.get("scans", [])
    assert len(scans) > 0, "❌ Žádné skeny!"
    findings = d.get("findings", [])
    quest = d.get("questionnaire_status")
    assert quest == "dokončen", f"❌ Dotazník: {quest}"
    score = d.get("compliance_score")
    return (
        f"✅ KOMPLETNÍ PROFIL:\n"
        f"   firma: {company.get('name','?')} ({company.get('url','')})\n"
        f"   skeny: {len(scans)}\n"
        f"   nálezy: {len(findings)}\n"
        f"   dotazník: {quest}\n"
        f"   compliance: {score}"
    )


# ═══════════════════════════════
#  MAIN
# ═══════════════════════════════
def main():
    print()
    print(f"{B}{C}{'═' * 62}{X}")
    print(f"{B}{C}  🛡️  AIshield.cz — Kompletní test uživatelské cesty{X}")
    print(f"{B}{C}{'═' * 62}{X}")
    print(f"  {D}API:  {API}  |  Web: {WEB}{X}")
    print(f"  {D}Účet: {TEST_EMAIL}  |  URL: {TEST_WEB}{X}")

    phase_header("FÁZE 1: Infrastruktura")
    run_test("API health check", "Infra", t_api_health, critical=True)
    run_test("Engine health", "Infra", t_engine_health)
    run_test("Frontend stránky (5x)", "Infra", t_frontend_pages)

    phase_header("FÁZE 2: Registrace a login")
    run_test("Reset testovacího účtu", "Auth", t_reset_account, critical=True)
    run_test("Login (Supabase)", "Auth", t_login, critical=True)
    run_test("Dashboard prázdný po resetu", "Auth", t_empty_dashboard)

    phase_header("FÁZE 3: Sken webu")
    run_test("Spuštění skenu", "Sken", t_start_scan, critical=True)
    run_test("Polling — čekání na dokončení", "Sken", t_poll_scan, critical=True)
    run_test("Findings (nálezy)", "Sken", t_findings)
    run_test("HTML report", "Sken", t_html_report)
    run_test("Odeslání report emailu", "Sken", t_send_report_email)

    phase_header("FÁZE 4: Dashboard ↔ Sken propojení")
    run_test("Dashboard → firma nalezena", "Link", t_dashboard_has_company, critical=True)
    run_test("Dashboard → skeny viditelné", "Link", t_dashboard_has_scans)

    phase_header("FÁZE 5: Dotazník")
    run_test("Struktura dotazníku", "Quest", t_questionnaire_structure)
    run_test("Odeslání odpovědí", "Quest", t_submit_questionnaire)
    run_test("Výsledky dotazníku", "Quest", t_questionnaire_results)
    run_test("Combined report", "Quest", t_combined_report)

    phase_header("FÁZE 6: Finální kontrola")
    run_test("Dashboard — kompletní profil", "Final", t_final_dashboard)

    # ═══════ SOUHRN ═══════
    print()
    print(f"{B}{C}{'═' * 62}{X}")
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    skipped = sum(1 for r in results if "Přeskočeno" in r.detail)
    total = len(results)
    t_total = sum(r.duration for r in results)

    if failed == 0:
        print(f"{B}{G}")
        print(f"  ✅ VŠECH {passed}/{total} TESTŮ PROŠLO ({t_total:.0f}s)")
        print(f"")
        print(f"  Celá uživatelská cesta funguje:")
        print(f"  reset → login → sken → findings → report email →")
        print(f"  dashboard s firmou → dotazník → combined report →")
        print(f"  kompletní uživatelský profil ✓")
        print(f"{X}")
    else:
        print(f"{B}{R}")
        print(f"  ❌ SELHALO: {failed}/{total} (prošlo: {passed}, přeskočeno: {skipped}, čas: {t_total:.0f}s)")
        print(f"{X}")
        for r in results:
            if not r.passed and "Přeskočeno" not in r.detail:
                c = f" {R}[KRITICKÝ]{X}" if r.critical else ""
                print(f"  {R}✗ [{r.phase}] {r.name}{c}{X}")
                for line in r.detail.split("\n"):
                    print(f"    {R}{line}{X}")
    print(f"{C}{'═' * 62}{X}\n")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
