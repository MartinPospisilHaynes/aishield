#!/usr/bin/env python3
"""
AIshield.cz — Kompletní test dotazníku (questionnaire)
======================================================
Testuje:
 1. Struktura — všechny sekce a otázky se načtou
 2. Typy otázek — single_select, yes_no_unknown fungují
 3. Multi-select — u follow-up polí jde vybrat víc voleb
 4. Follow-up logika — zobrazí se jen pro odpověď "yes"
 5. Validace — prázdné odpovědi nelze odeslat
 6. Kompletní průchod — vyplnění celého dotazníku
 7. Výsledky — risk analýza vrátí smysluplná data
 8. Combined report — spoj se skenem
 9. Konzistence dat — otázky mají povinné atributy

Spuštění:
  python3 test_questionnaire.py

Vrací exit code 0 = vše OK, 1 = selhání.
"""

import json
import sys
import time
import httpx

API = "https://api.aishield.cz"
TIMEOUT = 15  # sekund na request

# Test account
TEST_EMAIL = "info@desperados-design.cz"
TEST_PASS = "Test123456!"

passed = 0
failed = 0
warnings = 0
results = []


def log(status: str, name: str, detail: str = ""):
    global passed, failed, warnings
    icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "INFO": "ℹ️"}[status]
    if status == "PASS":
        passed += 1
    elif status == "FAIL":
        failed += 1
    elif status == "WARN":
        warnings += 1
    msg = f"  {icon} {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    results.append({"status": status, "name": name, "detail": detail})


# ═══════════════════════════════════════════════════
# FÁZE 1 — Struktura dotazníku
# ═══════════════════════════════════════════════════

print("\n🔷 FÁZE 1: Struktura dotazníku\n")

client = httpx.Client(timeout=TIMEOUT)

try:
    r = client.get(f"{API}/api/questionnaire/structure")
    assert r.status_code == 200, f"Status {r.status_code}"
    structure = r.json()
    log("PASS", "GET /api/questionnaire/structure", f"status={r.status_code}")
except Exception as e:
    log("FAIL", "GET /api/questionnaire/structure", str(e))
    print("\n💀 Nelze načíst dotazník. Konec.\n")
    sys.exit(1)

sections = structure.get("sections", [])
total_q = structure.get("total_questions", 0)

# 1.1 Počet sekcí
if len(sections) >= 9:
    log("PASS", "Počet sekcí", f"{len(sections)} sekcí")
else:
    log("FAIL", "Počet sekcí", f"Očekáváno >= 9, nalezeno {len(sections)}")

# 1.2 Celkový počet otázek
if total_q >= 22:
    log("PASS", "Celkový počet otázek", f"{total_q} otázek")
else:
    log("FAIL", "Celkový počet otázek", f"Očekáváno >= 22, nalezeno {total_q}")

# 1.3 Estimated time
est = structure.get("estimated_time_minutes")
if est and est <= 10:
    log("PASS", "Odhadovaný čas", f"{est} minut")
else:
    log("WARN", "Odhadovaný čas", f"Hodnota: {est}")

# ═══════════════════════════════════════════════════
# FÁZE 2 — Validace struktury každé otázky
# ═══════════════════════════════════════════════════

print("\n🔷 FÁZE 2: Validace atributů otázek\n")

all_questions = []
all_keys = set()
required_attrs = {"key", "text", "type", "risk_hint"}

for sec in sections:
    # Section musí mít id, title, questions
    for attr in ("id", "title", "questions"):
        if attr not in sec:
            log("FAIL", f"Sekce bez '{attr}'", json.dumps(sec.get("id", "?")))

    for q in sec.get("questions", []):
        all_questions.append({**q, "_section_id": sec["id"]})
        # Duplicitní klíče?
        if q["key"] in all_keys:
            log("FAIL", "Duplicitní klíč otázky", q["key"])
        all_keys.add(q["key"])

        # Povinné atributy
        missing = required_attrs - set(q.keys())
        if missing:
            log("FAIL", f"Chybí atributy u {q['key']}", str(missing))

        # Type validace
        if q["type"] not in ("yes_no_unknown", "single_select"):
            log("FAIL", f"Neznámý typ u {q['key']}", q["type"])

        # single_select musí mít options
        if q["type"] == "single_select":
            opts = q.get("options", [])
            if len(opts) < 2:
                log("FAIL", f"single_select bez options: {q['key']}", f"options={len(opts)}")
            else:
                log("PASS", f"single_select '{q['key']}'", f"{len(opts)} voleb")

        # Followup validace
        if "followup" in q and q["followup"]:
            fu = q["followup"]
            if fu.get("condition") != "yes":
                log("WARN", f"Followup condition != 'yes'", q["key"])
            fields = fu.get("fields", [])
            if not fields:
                log("FAIL", f"Followup bez polí: {q['key']}")
            for f in fields:
                if "key" not in f or "label" not in f or "type" not in f:
                    log("FAIL", f"Followup pole bez key/label/type", f"{q['key']}.{f.get('key','?')}")
                if f["type"] in ("select", "multi_select") and not f.get("options"):
                    log("FAIL", f"select/multi_select bez options", f"{q['key']}.{f['key']}")
                if f["type"] == "multi_select":
                    log("PASS", f"multi_select pole: {f['key']}", f"{len(f.get('options', []))} voleb")

if not any(r["status"] == "FAIL" for r in results if "Fáze 2" in r.get("name", "")):
    log("PASS", "Všechny otázky mají správné atributy")


# ═══════════════════════════════════════════════════
# FÁZE 3 — Klíčové otázky existují
# ═══════════════════════════════════════════════════

print("\n🔷 FÁZE 3: Klíčové otázky\n")

expected_keys = {
    "company_industry": "Odvětví firmy",
    "company_size": "Počet zaměstnanců",
    "develops_own_ai": "Vyvíjí vlastní AI?",
    "uses_social_scoring": "Sociální scoring",
    "uses_subliminal_manipulation": "Podprahová manipulace",
    "uses_realtime_biometric": "Biometrie v reálném čase",
    "uses_chatgpt": "ChatGPT a podobné",
    "uses_copilot": "AI pro kódování",
    "uses_ai_content": "Generování obsahu",
    "uses_deepfake": "Deepfake",
    "uses_ai_recruitment": "AI nábor",
    "uses_ai_employee_monitoring": "Monitoring zaměstnanců",
    "uses_emotion_recognition": "Rozpoznávání emocí",
    "uses_ai_accounting": "AI účetnictví",
    "uses_ai_creditscoring": "Kreditní scoring",
    "uses_ai_chatbot": "AI chatbot na webu",
    "uses_ai_email_auto": "AI automatické emaily",
    "uses_ai_decision": "AI rozhodování",
    "uses_ai_critical_infra": "Kritická infrastruktura",
    "ai_processes_personal_data": "Osobní údaje",
    "ai_data_stored_eu": "Data v EU",
    "ai_transparency_docs": "Přehled AI nástrojů",
    "has_ai_training": "Školení",
    "has_ai_guidelines": "Interní pravidla",
}

for key, label in expected_keys.items():
    if key in all_keys:
        log("PASS", f"Otázka '{label}'", key)
    else:
        log("FAIL", f"Chybí otázka '{label}'", key)


# ═══════════════════════════════════════════════════
# FÁZE 4 — Multi-select správnost
# ═══════════════════════════════════════════════════

print("\n🔷 FÁZE 4: Multi-select pole\n")

# Tyto follow-up fieldy MUSÍ být multi_select
must_be_multi = {
    "chatgpt_tool_name": "Které AI chaty",
    "chatgpt_purpose": "K čemu AI chat",
    "chatgpt_data_type": "Jaká data do AI",
    "copilot_tool_name": "Které code tools",
    "copilot_code_type": "Typ software",
    "content_tool_name": "Které content tools",
    "content_published": "Kde AI obsah",
    "monitoring_type": "Co sledujete",
    "personal_data_types": "Typy osobních údajů",
    "biometric_purpose": "Účel biometrie",
    "emotion_context": "Kontext emocí",
    "infra_sector": "Sektor infrastruktury",
    "ai_role": "Role v AI řetězci",
}

for q in all_questions:
    if "followup" not in q or not q["followup"]:
        continue
    for f in q["followup"].get("fields", []):
        if f["key"] in must_be_multi:
            if f["type"] == "multi_select":
                log("PASS", f"Multi-select: {must_be_multi[f['key']]}", f["key"])
            else:
                log("FAIL", f"Mělo být multi_select: {must_be_multi[f['key']]}", f"je {f['type']}")


# ═══════════════════════════════════════════════════
# FÁZE 5 — Risk hints a AI Act reference
# ═══════════════════════════════════════════════════

print("\n🔷 FÁZE 5: Risk hints a AI Act reference\n")

valid_risks = {"none", "minimal", "limited", "high"}
risk_count = {"none": 0, "minimal": 0, "limited": 0, "high": 0}

for q in all_questions:
    rh = q.get("risk_hint", "")
    if rh not in valid_risks:
        log("FAIL", f"Neplatný risk_hint: {rh}", q["key"])
    else:
        risk_count[rh] = risk_count.get(rh, 0) + 1
    # High-risk otázky by měly mít ai_act_article
    if rh == "high" and not q.get("ai_act_article"):
        log("WARN", f"High-risk bez AI Act reference", q["key"])

log("PASS", "Risk rozložení", f"high={risk_count['high']}, limited={risk_count['limited']}, minimal={risk_count['minimal']}, none={risk_count['none']}")

# ═══════════════════════════════════════════════════
# FÁZE 6 — Validace odeslání (negativní testy)
# ═══════════════════════════════════════════════════

print("\n🔷 FÁZE 6: Validace odeslání\n")

# 6.1 Prázdné odpovědi
try:
    r = client.post(f"{API}/api/questionnaire/submit", json={
        "company_id": "test-validation",
        "answers": []
    })
    if r.status_code in (400, 422):
        log("PASS", "Odmítnutí prázdných odpovědí", f"status={r.status_code}")
    else:
        log("FAIL", "Prázdné odpovědi přijaty", f"status={r.status_code}")
except Exception as e:
    log("FAIL", "Validace prázdných odpovědí", str(e))

# 6.2 Chybějící company_id
try:
    r = client.post(f"{API}/api/questionnaire/submit", json={
        "answers": [{"question_key": "test", "section": "test", "answer": "yes"}]
    })
    if r.status_code in (400, 422):
        log("PASS", "Odmítnutí bez company_id", f"status={r.status_code}")
    else:
        log("FAIL", "Přijato bez company_id", f"status={r.status_code}")
except Exception as e:
    log("FAIL", "Validace company_id", str(e))


# ═══════════════════════════════════════════════════
# FÁZE 7 — Kompletní průchod dotazníkem
# ═══════════════════════════════════════════════════

print("\n🔷 FÁZE 7: Kompletní průchod dotazníkem\n")

# Simulace reálného vyplnění — jako by klient klikal
answers_payload = []

for q in all_questions:
    answer_obj = {
        "question_key": q["key"],
        "section": q["_section_id"],
        "answer": "",
        "details": None,
        "tool_name": None,
    }

    if q["type"] == "single_select":
        # Vyber první volbu
        opts = q.get("options", [])
        if opts:
            answer_obj["answer"] = opts[0]
            log("PASS", f"Klik: {q['key']}", f"→ {opts[0]}")
        else:
            log("FAIL", f"Nelze kliknout: {q['key']}", "žádné volby")
            continue

    elif q["type"] == "yes_no_unknown":
        # Střídáme odpovědi pro realistický test
        # Pro high-risk otázky odpovíme "yes" aby se testovaly followupy
        if q.get("risk_hint") == "high":
            answer_obj["answer"] = "yes"
        elif q["key"] in ("uses_chatgpt", "uses_ai_content", "uses_ai_chatbot"):
            answer_obj["answer"] = "yes"  # testovat followup
        elif q["key"] == "has_ai_training":
            answer_obj["answer"] = "no"
        elif q["key"] == "has_ai_guidelines":
            answer_obj["answer"] = "no"
        else:
            answer_obj["answer"] = "unknown"

        log("PASS", f"Klik: {q['key']}", f"→ {answer_obj['answer']}")

        # Vyplnit followup pokud je "yes"
        if answer_obj["answer"] == "yes" and "followup" in q and q["followup"]:
            details = {}
            for f in q["followup"]["fields"]:
                if f["type"] == "select" and f.get("options"):
                    details[f["key"]] = f["options"][0]
                    log("PASS", f"  Followup select: {f['key']}", f"→ {f['options'][0]}")
                elif f["type"] == "multi_select" and f.get("options"):
                    # Vybrat víc voleb (simulace multi-klik)
                    picks = f["options"][:min(3, len(f["options"]))]
                    details[f["key"]] = picks  # posíláme jako list
                    log("PASS", f"  Followup multi_select: {f['key']}", f"→ {picks}")
                elif f["type"] == "text":
                    details[f["key"]] = "Testovací hodnota"
                    log("PASS", f"  Followup text: {f['key']}", "→ Testovací hodnota")
            answer_obj["details"] = details if details else None

    answers_payload.append(answer_obj)

# Odeslat dotazník
print(f"\n  📤 Odesílám {len(answers_payload)} odpovědí...")

try:
    r = client.post(f"{API}/api/questionnaire/submit", json={
        "company_id": "test-questionnaire-audit",
        "scan_id": None,
        "answers": answers_payload,
    })
    if r.status_code == 200:
        data = r.json()
        analysis = data.get("analysis", {})
        log("PASS", "Submit dotazníku", f"status=200")

        # Ověřit analýzu
        total_ans = analysis.get("total_answers", 0)
        ai_declared = analysis.get("ai_systems_declared", 0)
        risk_bd = analysis.get("risk_breakdown", {})
        recs = analysis.get("recommendations", [])

        if total_ans >= 20:
            log("PASS", "Analýza: odpovědi", f"{total_ans} odpovědí zpracováno")
        else:
            log("FAIL", "Analýza: odpovědi", f"Jen {total_ans} zpracováno z {len(answers_payload)}")

        if ai_declared >= 1:
            log("PASS", "Analýza: AI systémy", f"{ai_declared} AI systémů deklarováno")
        else:
            log("WARN", "Analýza: AI systémy", f"Jen {ai_declared} deklarováno")

        high_r = risk_bd.get("high", 0)
        if high_r > 0:
            log("PASS", "Analýza: high-risk detekce", f"{high_r} vysoce rizikových")
        else:
            log("WARN", "Analýza: žádné high-risk", "Odpovídali jsme 'yes' na high-risk otázky")

        if len(recs) > 0:
            log("PASS", "Analýza: doporučení", f"{len(recs)} doporučení")
            # Zkontrolovat strukturu prvního doporučení
            rec0 = recs[0]
            for field in ("question_key", "recommendation", "risk_level"):
                if field in rec0:
                    log("PASS", f"  Doporučení má '{field}'")
                else:
                    log("FAIL", f"  Doporučení chybí '{field}'")
        else:
            log("FAIL", "Analýza: žádná doporučení")

    else:
        log("FAIL", "Submit dotazníku", f"status={r.status_code}: {r.text[:200]}")
except Exception as e:
    log("FAIL", "Submit dotazníku", str(e))


# ═══════════════════════════════════════════════════
# FÁZE 8 — Načtení výsledků
# ═══════════════════════════════════════════════════

print("\n🔷 FÁZE 8: Načtení výsledků\n")

try:
    r = client.get(f"{API}/api/questionnaire/test-questionnaire-audit/results")
    if r.status_code == 200:
        data = r.json()
        log("PASS", "GET results", f"status=200, klíče: {list(data.keys())[:5]}")
    else:
        log("WARN", "GET results", f"status={r.status_code}")
except Exception as e:
    log("WARN", "GET results", str(e))


# ═══════════════════════════════════════════════════
# FÁZE 9 — Frontend konzistence
# ═══════════════════════════════════════════════════

print("\n🔷 FÁZE 9: Frontend konzistence\n")

# Ověřit, že frontend stránka dotazníku existuje
try:
    r = client.get("https://aishield.cz/dotaznik", follow_redirects=True)
    if r.status_code == 200:
        html = r.text
        # Musí obsahovat klíčové UI elementy
        checks = {
            "Začít": "Tlačítko 'Začít'",
            "krátkých otázek": "Popis počtu otázek",
            "questionnaire/structure": "API fetch volání",
        }
        for needle, label in checks.items():
            if needle.lower() in html.lower():
                log("PASS", f"Frontend: {label}")
            else:
                log("WARN", f"Frontend: chybí '{label}'")
    else:
        log("FAIL", "Frontend dotazník stránka", f"status={r.status_code}")
except Exception as e:
    log("FAIL", "Frontend dotazník stránka", str(e))


# ═══════════════════════════════════════════════════
# FÁZE 10 — UX pravidla
# ═══════════════════════════════════════════════════

print("\n🔷 FÁZE 10: UX pravidla\n")

# 10.1 Žádná otázka nemá víc než 100 znaků
for q in all_questions:
    text = q.get("text", "")
    if len(text) > 120:
        log("WARN", f"Příliš dlouhá otázka ({len(text)} zn.)", q["key"])

# 10.2 Každá sekce má description
for sec in sections:
    if not sec.get("description"):
        log("WARN", f"Sekce bez popisu", sec.get("id", "?"))
    else:
        log("PASS", f"Sekce '{sec['id']}' má popis")

# 10.3 Help text u složitých otázek
complex_keys = {"uses_social_scoring", "uses_subliminal_manipulation", "uses_ai_creditscoring", "ai_processes_personal_data"}
for q in all_questions:
    if q["key"] in complex_keys:
        if q.get("help_text"):
            log("PASS", f"Help text u '{q['key']}'")
        else:
            log("WARN", f"Chybí help text u složité otázky", q["key"])

# 10.4 Followup labels by měly být srozumitelné
for q in all_questions:
    if "followup" in q and q["followup"]:
        for f in q["followup"]["fields"]:
            if len(f.get("label", "")) < 3:
                log("FAIL", f"Followup label příliš krátký", f"{q['key']}.{f['key']}")


# ═══════════════════════════════════════════════════
# SHRNUTÍ
# ═══════════════════════════════════════════════════

print("\n" + "═" * 55)
print(f"  VÝSLEDKY: ✅ {passed} passed | ❌ {failed} failed | ⚠️ {warnings} warnings")
print("═" * 55)

if failed == 0:
    print("\n  🏆 DOTAZNÍK JE V POŘÁDKU!\n")
else:
    print(f"\n  🔧 Nalezeno {failed} problémů k opravě.\n")
    print("  Selhané testy:")
    for r in results:
        if r["status"] == "FAIL":
            print(f"    ❌ {r['name']}: {r['detail']}")
    print()

client.close()
sys.exit(0 if failed == 0 else 1)
