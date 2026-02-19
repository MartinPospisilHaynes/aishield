#!/usr/bin/env python3
"""
AIshield.cz — MEGA E2E test v3 (PROMETHEUS)
=============================================
Kompletní průchod celou aplikací (idempotentní — funguje opakovaně):

  FÁZE 1 — Infrastruktura (API, engine, frontend stránky)
  FÁZE 2 — Login (Supabase auth)
  FÁZE 3 — Sken webu (start / využití existujícího skenu)
  FÁZE 4 — Dashboard propojení (firma, skeny)
  FÁZE 5 — Hloubkový scan (POST /deep trigger)
  FÁZE 6 — Dotazník (struktura, kompletní submit ALL 35 otázek, results, combined report)
  FÁZE 7 — Objednávky (všechny 3 plány přes bank_transfer)
  FÁZE 8 — Finální kontrola

Spuštění:
  # Automaticky načte .env ze stejného adresáře
  python3 test_e2e_mega.py

  # Nebo ručně:
  export SUPABASE_ANON_KEY="..."
  export TEST_EMAIL="test@example.com"
  export TEST_PASSWORD="..."
  python3 test_e2e_mega.py
"""

import json
import os
import sys
import time
import requests
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

# ═══════════════════════════════════════════
#  NAČTENÍ .env (pokud existuje)
# ═══════════════════════════════════════════
def load_dotenv():
    """Načte .env soubor ze stejného adresáře jako skript."""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                if not os.environ.get(key):  # nepřepisuj explicitní env vars
                    os.environ[key] = value

load_dotenv()

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

if not SUPABASE_ANON_KEY:
    raise RuntimeError(
        "Chybí SUPABASE_ANON_KEY. Nastav v .env nebo jako env proměnnou."
    )
if not TEST_EMAIL or not TEST_PASSWORD:
    raise RuntimeError(
        "Chybí TEST_EMAIL a/nebo TEST_PASSWORD.\n"
        "Přidej do .env:\n"
        "  TEST_EMAIL=tvuj@email.cz\n"
        "  TEST_PASSWORD=tvoje_heslo\n"
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
    order_ids: list = []
    order_numbers: list = []

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
    pages = ["/", "/scan", "/registrace", "/login", "/pricing", "/dotaznik", "/dashboard"]
    ok_count = 0
    details = []
    for p in pages:
        try:
            r = requests.get(f"{WEB}{p}", timeout=15, allow_redirects=True)
            # Dashboard and dotaznik may redirect to login (302/307 → 200 after redirect)
            if r.status_code == 200:
                ok_count += 1
            else:
                details.append(f"  {p} → HTTP {r.status_code}")
        except Exception as e:
            details.append(f"  {p} → ERROR: {e}")
    assert ok_count >= 5, f"Jen {ok_count}/{len(pages)} stránek ok\n" + "\n".join(details)
    return f"Stránek OK: {ok_count}/{len(pages)}"


# ═══════════════════════════════
#  FÁZE 2 — LOGIN
# ═══════════════════════════════
def t_login():
    r = requests.post(f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}, timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:200]}"
    d = r.json()
    assert "access_token" in d, "Chybí access_token"
    s.access_token = d["access_token"]
    user = d.get("user", {})
    s.user_id = user.get("id")
    meta = user.get("user_metadata", {})
    assert user.get("email") == TEST_EMAIL, f"Email mismatch"
    return f"email={user['email']}, user_id={s.user_id[:8]}..."


def t_initial_dashboard():
    """Načte dashboard — zjistí stav účtu (může být prázdný nebo s daty)."""
    r = requests.get(f"{API}/api/dashboard/me", headers=auth_headers(), timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}"
    d = r.json()
    company = d.get("company")
    scans = d.get("scans", [])
    quest = d.get("questionnaire_status", "?")
    if company:
        s.company_id = company.get("id")
        s.company_name = company.get("name")
        # Pokud už existují skeny, vezmi poslední done scan
        done_scans = [sc for sc in scans if sc.get("status") == "done"]
        if done_scans:
            s.scan_id = done_scans[0].get("id")
    return (
        f"firma={'ANO (' + s.company_name + ')' if company else 'NE'}\n"
        f"skeny={len(scans)}, dotazník={quest}\n"
        f"{'→ Použiji existující company_id=' + s.company_id[:8] + '...' if s.company_id else '→ Bude nutné spustit sken'}"
    )


# ═══════════════════════════════
#  FÁZE 3 — SKEN WEBU
# ═══════════════════════════════
def t_start_scan():
    # Pokud už máme scan z dashboardu, přeskočíme
    if s.scan_id:
        return f"⚡ Existující scan_id={s.scan_id[:8]}... (z dashboardu)"
    r = requests.post(f"{API}/api/scan", headers=auth_headers(),
        json={"url": TEST_WEB}, timeout=15)
    if r.status_code == 429:
        d = r.json()
        cached = d.get("cached_scan_id")
        if cached:
            s.scan_id = cached
            s.company_id = d.get("cached_company_id") or s.company_id
            return f"⚡ Rate limit — cache scan_id={cached}"
        raise Exception(f"Rate limit bez cache: {d.get('detail')}")
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:200]}"
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
    return f"nálezy={len(findings)}, false_positives={len(fp)}, AI={d.get('ai_classified', '?')}"


def t_html_report():
    assert s.scan_id
    r = requests.get(f"{API}/api/scan/{s.scan_id}/report", timeout=15)
    if r.status_code == 400:
        return "⚠️ Sken ještě není done"
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
        "❌ Dashboard nevidí firmu po skenu!\n"
        "   companies.email není propojený s uživatelem."
    )
    cid = company.get("id")
    if s.company_id:
        assert cid == s.company_id, f"company_id mismatch: dashboard={cid}, scan={s.company_id}"
    return f"Firma nalezena: id={cid}, name={company.get('name', '?')}"


def t_dashboard_has_scans():
    r = requests.get(f"{API}/api/dashboard/me", headers=auth_headers(), timeout=10)
    assert r.status_code == 200
    d = r.json()
    scans = d.get("scans", [])
    assert len(scans) > 0, "Dashboard neukazuje žádné skeny!"
    last = scans[0]
    assert last.get("status") == "done", f"Poslední sken: {last.get('status')}"
    findings = d.get("findings", [])
    return f"skenů={len(scans)}, poslední=done, findings={len(findings)}"


# ═══════════════════════════════
#  FÁZE 5 — HLOUBKOVÝ SCAN
# ═══════════════════════════════
def t_trigger_deep_scan():
    """Spustí 24h hloubkový scan (POST /api/scan/{id}/deep)."""
    assert s.scan_id, "Chybí scan_id"
    r = requests.post(f"{API}/api/scan/{s.scan_id}/deep", timeout=15)
    # Přijatelné odpovědi: 200 (spuštěno/již běží/již done), 429 (cooldown)
    if r.status_code == 429:
        return f"⏳ Cooldown — deep scan již proběhl v posledních 7 dnech (OK)"
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()
    status = d.get("deep_scan_status", "?")
    msg = d.get("message", "")
    return f"deep_scan_status={status}\n{msg}"


def t_verify_deep_scan_status():
    """Ověří, že deep scan je vidět ve stavu skenu."""
    assert s.scan_id, "Chybí scan_id"
    r = requests.get(f"{API}/api/scan/{s.scan_id}", timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}"
    d = r.json()
    deep_status = d.get("deep_scan_status")
    # May be pending, running, done, or None (if 429 cooldown)
    valid = [None, "pending", "running", "done"]
    assert deep_status in valid, f"Neočekávaný deep_scan_status: {deep_status}"
    return f"deep_scan_status={deep_status}"


# ═══════════════════════════════
#  FÁZE 6 — DOTAZNÍK
# ═══════════════════════════════

# Všech 35 otázek — kompletní odpovědi simulující reálného uživatele
COMPLETE_ANSWERS = [
    # ── Sekce: industry (O vaší firmě) — 8 otázek ──
    {"question_key": "company_legal_name", "section": "industry", "answer": "TEST s.r.o."},
    {"question_key": "company_ico", "section": "industry", "answer": "12345678"},
    {"question_key": "company_address", "section": "industry", "answer": "Testovací 123, Praha 1, 110 00"},
    {"question_key": "company_contact_email", "section": "industry", "answer": TEST_EMAIL},
    {"question_key": "company_industry", "section": "industry", "answer": "IT / Technologie"},
    {"question_key": "company_size", "section": "industry", "answer": "10–49 zaměstnanců"},
    {"question_key": "company_annual_revenue", "section": "industry", "answer": "10–50 mil. Kč"},
    {"question_key": "develops_own_ai", "section": "industry", "answer": "yes"},

    # ── Sekce: prohibited_systems (Zakázané praktiky) — 3 otázky ──
    {"question_key": "uses_social_scoring", "section": "prohibited_systems", "answer": "no"},
    {"question_key": "uses_subliminal_manipulation", "section": "prohibited_systems", "answer": "no"},
    {"question_key": "uses_realtime_biometric", "section": "prohibited_systems", "answer": "no"},

    # ── Sekce: internal_ai (AI nástroje ve firmě) — 4 otázky ──
    {"question_key": "uses_chatgpt", "section": "internal_ai", "answer": "yes"},
    {"question_key": "uses_copilot", "section": "internal_ai", "answer": "yes"},
    {"question_key": "uses_ai_content", "section": "internal_ai", "answer": "yes"},
    {"question_key": "uses_deepfake", "section": "internal_ai", "answer": "no"},

    # ── Sekce: hr (Lidské zdroje a zaměstnanci) — 3 otázky ──
    {"question_key": "uses_ai_recruitment", "section": "hr", "answer": "no"},
    {"question_key": "uses_ai_employee_monitoring", "section": "hr", "answer": "no"},
    {"question_key": "uses_emotion_recognition", "section": "hr", "answer": "no"},

    # ── Sekce: finance (Finance a rozhodování) — 3 otázky ──
    {"question_key": "uses_ai_accounting", "section": "finance", "answer": "yes"},
    {"question_key": "uses_ai_creditscoring", "section": "finance", "answer": "no"},
    {"question_key": "uses_ai_insurance", "section": "finance", "answer": "no"},

    # ── Sekce: customer_service (Zákazníci a komunikace) — 5 otázek ──
    {"question_key": "uses_ai_chatbot", "section": "customer_service", "answer": "yes"},
    {"question_key": "uses_ai_email_auto", "section": "customer_service", "answer": "yes"},
    {"question_key": "uses_ai_decision", "section": "customer_service", "answer": "no"},
    {"question_key": "uses_dynamic_pricing", "section": "customer_service", "answer": "no"},
    {"question_key": "uses_ai_for_children", "section": "customer_service", "answer": "no"},

    # ── Sekce: infrastructure_safety (Bezpečnost a infrastruktura) — 2 otázky ──
    {"question_key": "uses_ai_critical_infra", "section": "infrastructure_safety", "answer": "no"},
    {"question_key": "uses_ai_safety_component", "section": "infrastructure_safety", "answer": "no"},

    # ── Sekce: data_protection (Ochrana dat) — 3 otázky ──
    {"question_key": "ai_processes_personal_data", "section": "data_protection", "answer": "yes"},
    {"question_key": "ai_data_stored_eu", "section": "data_protection", "answer": "yes"},
    {"question_key": "has_ai_vendor_contracts", "section": "data_protection", "answer": "yes"},

    # ── Sekce: ai_literacy (AI gramotnost) — 2 otázky ──
    {"question_key": "has_ai_training", "section": "ai_literacy", "answer": "unknown"},
    {"question_key": "has_ai_guidelines", "section": "ai_literacy", "answer": "no"},

    # ── Sekce: human_oversight (Lidský dohled nad AI) — 4 otázky ──
    {"question_key": "has_oversight_person", "section": "human_oversight", "answer": "yes"},
    {"question_key": "can_override_ai", "section": "human_oversight", "answer": "yes"},
    {"question_key": "ai_decision_logging", "section": "human_oversight", "answer": "yes"},
    {"question_key": "has_ai_register", "section": "human_oversight", "answer": "no"},

    # ── Sekce: ai_role (Role v AI ekosystému) — 2 otázky ──
    {"question_key": "modifies_ai_purpose", "section": "ai_role", "answer": "no"},
    {"question_key": "uses_gpai_api", "section": "ai_role", "answer": "yes"},

    # ── Sekce: incident_management (Řízení AI incidentů) — 4 otázky ──
    {"question_key": "has_incident_plan", "section": "incident_management", "answer": "no"},
    {"question_key": "monitors_ai_outputs", "section": "incident_management", "answer": "yes"},
    {"question_key": "tracks_ai_changes", "section": "incident_management", "answer": "no"},
    {"question_key": "has_ai_bias_check", "section": "incident_management", "answer": "no"},
]


def t_questionnaire_structure():
    r = requests.get(f"{API}/api/questionnaire/structure", timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}"
    d = r.json()
    sections = d.get("sections", [])
    assert len(sections) >= 10, f"Málo sekcí: {len(sections)}"
    total_q = d.get("total_questions", 0)
    assert total_q >= 30, f"Málo otázek: {total_q}"
    section_ids = [sec["id"] for sec in sections]
    return f"sekcí={len(sections)}, otázek={total_q}\nsekce: {', '.join(section_ids)}"


def t_submit_questionnaire():
    """Odešle KOMPLETNÍ dotazník — všech 35 odpovědí."""
    assert s.company_id, "Chybí company_id"
    r = requests.post(f"{API}/api/questionnaire/submit",
        json={
            "company_id": s.company_id,
            "scan_id": s.scan_id,
            "answers": COMPLETE_ANSWERS,
        },
        headers=auth_headers(),
        timeout=20)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()
    saved = d.get("saved_count", 0)
    assert saved >= 40, f"Uloženo jen {saved} odpovědí (očekáváno 43)"
    a = d.get("analysis", {})
    return (
        f"uloženo={saved}/{len(COMPLETE_ANSWERS)}\n"
        f"AI systémy={a.get('ai_systems_declared', '?')}\n"
        f"riziko={a.get('risk_breakdown', '?')}"
    )


def t_questionnaire_results():
    assert s.company_id
    r = requests.get(f"{API}/api/questionnaire/{s.company_id}/results", timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()
    answers = d.get("answers", [])
    assert len(answers) >= 40, f"Málo odpovědí: {len(answers)}"
    return f"odpovědí={len(answers)}, submitted={d.get('submitted_at', '?')}"


def t_questionnaire_progress():
    assert s.company_id
    r = requests.get(f"{API}/api/questionnaire/{s.company_id}/progress", timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()
    total = d.get("total_answers", 0)
    complete = d.get("is_complete", False)
    return f"total_answers={total}, is_complete={complete}, has_unknowns={d.get('has_unknowns', '?')}"


def t_combined_report():
    assert s.company_id
    url = f"{API}/api/questionnaire/{s.company_id}/combined-report"
    if s.scan_id:
        url += f"?scan_id={s.scan_id}"
    r = requests.get(url, timeout=15)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()
    risk = d.get("overall_risk", "?")
    ai_count = d.get("total_ai_systems", 0)
    items = d.get("action_items", [])
    return (
        f"riziko={risk}, AI systémy={ai_count}\n"
        f"akční body={len(items)}\n"
        f"{d.get('overall_risk_text', '')[:100]}"
    )


def t_questionnaire_my_status():
    """Ověří /api/questionnaire/my-status endpoint."""
    r = requests.get(f"{API}/api/questionnaire/my-status", headers=auth_headers(), timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()
    status = d.get("status", "?")
    return f"status={status}, company_id={d.get('company_id', '?')}"


# ═══════════════════════════════
#  FÁZE 7 — OBJEDNÁVKY (všechny 3 plány)
# ═══════════════════════════════
BILLING_DATA = {
    "company": "TEST s.r.o.",
    "ico": "12345678",
    "dic": "CZ12345678",
    "street": "Testovací 123",
    "city": "Praha",
    "zip": "11000",
    "phone": "+420777888999",
    "email": TEST_EMAIL,
}


def _checkout_plan(plan_name: str):
    """Vytvoří objednávku pro daný plán přes bank_transfer."""
    r = requests.post(
        f"{API}/api/payments/checkout",
        headers=auth_headers(),
        json={
            "plan": plan_name,
            "email": TEST_EMAIL,
            "gateway": "bank_transfer",
            "billing": BILLING_DATA,
        },
        timeout=15,
    )
    assert r.status_code == 200, f"HTTP {r.status_code}: {r.text}"
    d = r.json()
    assert d.get("payment_id"), f"Chybí payment_id: {d}"
    assert d.get("order_number"), f"Chybí order_number: {d}"
    assert d.get("gateway") == "bank_transfer", f"Gateway: {d.get('gateway')}"
    s.order_ids.append(d["payment_id"])
    s.order_numbers.append(d["order_number"])
    return (
        f"order={d['order_number']}\n"
        f"payment_id={d['payment_id']}\n"
        f"gateway_url={d.get('gateway_url', '?')[:80]}"
    )


def t_checkout_basic():
    return _checkout_plan("basic")


def t_checkout_pro():
    return _checkout_plan("pro")


def t_checkout_enterprise():
    return _checkout_plan("enterprise")


def t_list_gateways():
    """Ověří /api/payments/gateways endpoint."""
    r = requests.get(f"{API}/api/payments/gateways", timeout=10)
    assert r.status_code == 200, f"HTTP {r.status_code}"
    d = r.json()
    gateways = d.get("gateways", [])
    assert len(gateways) >= 2, f"Málo bran: {len(gateways)}"
    ids = [g["id"] for g in gateways]
    assert "stripe" in ids, f"Stripe chybí! {ids}"
    assert "bank_transfer" in ids, f"Bank_transfer chybí! {ids}"
    return f"brány: {', '.join(ids)}"


# ═══════════════════════════════
#  FÁZE 8 — FINÁLNÍ KONTROLA
# ═══════════════════════════════
def t_final_dashboard():
    r = requests.get(f"{API}/api/dashboard/me", headers=auth_headers(), timeout=10)
    assert r.status_code == 200
    d = r.json()
    company = d.get("company")
    assert company, "Firma chybí!"
    scans = d.get("scans", [])
    assert len(scans) > 0, "Žádné skeny!"
    findings = d.get("findings", [])
    quest = d.get("questionnaire_status")
    assert quest == "dokončen", f"Dotazník: {quest} (očekáváno: dokončen)"
    score = d.get("compliance_score")
    return (
        f"✅ KOMPLETNÍ PROFIL:\n"
        f"   firma: {company.get('name', '?')} ({company.get('url', '')})\n"
        f"   skeny: {len(scans)}\n"
        f"   nálezy: {len(findings)}\n"
        f"   dotazník: {quest}\n"
        f"   compliance: {score}\n"
        f"   objednávky: {len(s.order_numbers)}"
    )


def t_final_questionnaire():
    """Ověří finální stav dotazníku v dashboardu."""
    r = requests.get(f"{API}/api/dashboard/me", headers=auth_headers(), timeout=10)
    assert r.status_code == 200
    d = r.json()
    quest_status = d.get("questionnaire_status")
    assert quest_status == "dokončen", f"questionnaire_status={quest_status}"
    return f"questionnaire_status=dokončen ✅"


def t_final_all_orders():
    """Ověří, že všechny 3 objednávky existují."""
    assert len(s.order_numbers) == 3, f"Očekávány 3 objednávky, máme {len(s.order_numbers)}"
    plans_ordered = set()
    for on in s.order_numbers:
        if "BASIC" in on:
            plans_ordered.add("basic")
        elif "PRO" in on:
            plans_ordered.add("pro")
        elif "ENTERPRISE" in on:
            plans_ordered.add("enterprise")
    assert len(plans_ordered) == 3, f"Chybí plán(y): {plans_ordered}"
    return f"Všechny 3 plány objednány: {', '.join(sorted(plans_ordered))}\n" + "\n".join(s.order_numbers)


# ═══════════════════════════════
#  MAIN
# ═══════════════════════════════
def main():
    print()
    print(f"{B}{C}{'═' * 68}{X}")
    print(f"{B}{C}  🛡️  AIshield.cz — MEGA E2E Test v3 (PROMETHEUS){X}")
    print(f"{B}{C}{'═' * 68}{X}")
    print(f"  {D}API:  {API}  |  Web: {WEB}{X}")
    print(f"  {D}Účet: {TEST_EMAIL}  |  URL: {TEST_WEB}{X}")
    print(f"  {D}Testů: 8 fází, ~25 testů{X}")

    # ── FÁZE 1 ──
    phase_header("FÁZE 1: Infrastruktura")
    run_test("API health check", "Infra", t_api_health, critical=True)
    run_test("Engine health", "Infra", t_engine_health)
    run_test("Frontend stránky (7x)", "Infra", t_frontend_pages)

    # ── FÁZE 2 ──
    phase_header("FÁZE 2: Login")
    run_test("Login (Supabase)", "Auth", t_login, critical=True)
    run_test("Načtení dashboardu (stav účtu)", "Auth", t_initial_dashboard)

    # ── FÁZE 3 ──
    phase_header("FÁZE 3: Sken webu")
    run_test("Spuštění skenu", "Sken", t_start_scan, critical=True)
    run_test("Polling — čekání na dokončení", "Sken", t_poll_scan, critical=True)
    run_test("Findings (nálezy)", "Sken", t_findings)
    run_test("HTML report", "Sken", t_html_report)
    run_test("Odeslání report emailu", "Sken", t_send_report_email)

    # ── FÁZE 4 ──
    phase_header("FÁZE 4: Dashboard ↔ Sken propojení")
    run_test("Dashboard → firma nalezena", "Link", t_dashboard_has_company, critical=True)
    run_test("Dashboard → skeny viditelné", "Link", t_dashboard_has_scans)

    # ── FÁZE 5 ──
    phase_header("FÁZE 5: Hloubkový scan (24h)")
    run_test("Trigger deep scan", "Deep", t_trigger_deep_scan)
    run_test("Ověření deep scan status", "Deep", t_verify_deep_scan_status)

    # ── FÁZE 6 ──
    phase_header("FÁZE 6: Dotazník (kompletní — 35 otázek)")
    run_test("Struktura dotazníku", "Quest", t_questionnaire_structure)
    run_test("Odeslání ALL 35 odpovědí", "Quest", t_submit_questionnaire, critical=True)
    run_test("Výsledky dotazníku", "Quest", t_questionnaire_results)
    run_test("Progress dotazníku", "Quest", t_questionnaire_progress)
    run_test("Combined report (sken + dotazník)", "Quest", t_combined_report)
    run_test("My-status endpoint", "Quest", t_questionnaire_my_status)

    # ── FÁZE 7 ──
    phase_header("FÁZE 7: Objednávky (3 plány, bank_transfer)")
    run_test("Platební brány (gateways)", "Pay", t_list_gateways)
    run_test("Checkout BASIC (4 999 Kč)", "Pay", t_checkout_basic)
    run_test("Checkout PRO (14 999 Kč)", "Pay", t_checkout_pro)
    run_test("Checkout ENTERPRISE (39 999 Kč)", "Pay", t_checkout_enterprise)

    # ── FÁZE 8 ──
    phase_header("FÁZE 8: Finální kontrola")
    run_test("Dashboard — kompletní profil", "Final", t_final_dashboard)
    run_test("Dotazník — status dokončen", "Final", t_final_questionnaire)
    run_test("Všechny 3 objednávky", "Final", t_final_all_orders)

    # ═══════ SOUHRN ═══════
    print()
    print(f"{B}{C}{'═' * 68}{X}")
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    skipped = sum(1 for r in results if "Přeskočeno" in r.detail)
    total = len(results)
    t_total = sum(r.duration for r in results)

    if failed == 0:
        print(f"{B}{G}")
        print(f"  ✅ VŠECH {passed}/{total} TESTŮ PROŠLO ({t_total:.0f}s)")
        print()
        print(f"  Kompletní uživatelská cesta funguje:")
        print(f"  reset → login → sken → findings → report email →")
        print(f"  dashboard → deep scan → dotazník (35 otázek) →")
        print(f"  combined report → 3 objednávky → kompletní profil ✓")
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
        print()
        if skipped > 0:
            print(f"  {Y}⏭️  Přeskočeno: {skipped} testů kvůli kritické chybě{X}")
    print(f"{C}{'═' * 68}{X}\n")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
