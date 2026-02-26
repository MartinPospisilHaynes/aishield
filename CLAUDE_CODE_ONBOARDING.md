# AIshield.cz — Onboarding pro Claude Code

## 1. PŘEHLED PROJEKTU

AIshield.cz = SaaS pro české firmy — automatická compliance s EU AI Act (Nařízení EU 2024/1689).
Pipeline: Klient vyplní dotazník → web scanner prověří web → pipeline vygeneruje 13 PDF dokumentů + 1 PPTX prezentaci + 1 HTML stránku = "Compliance Kit".

## 2. ARCHITEKTURA

```
/Users/martinhaynes/Projects/aishield/     ← LOKÁLNÍ KOPIE (edituj tady)
  backend/
    documents/
      pipeline.py          ← HLAVNÍ ORCHESTRÁTOR — generuje kit (944 řádků)
      unified_pdf.py       ← HTML→PDF renderer pro VŠECH 12 PDF sekcí (~2400 řádků)
      templates.py         ← HTML šablony (záhlaví, zápatí, CSS) (~600 řádků)
      pptx_generator.py    ← PowerPoint generátor (574 řádků)
      llm_content.py       ← LLM prompty pro personalizaci (~800 řádků)
      knowledge_base.py    ← Předdefinované KB texty per systém (~1200 řádků)
    api/
      questionnaire.py     ← Definice otázek + _analyze_responses() (~1650 řádků)
    scanner/
      classifier.py        ← AI klasifikátor scan findings
```

## 3. VPS PŘÍSTUPY (pro deploy — NE pro editaci)

```
VPS IP:       46.28.110.102
SSH user:     root
SSH heslo:    A7CxbS38
Projekt:      /opt/aishield/
Python venv:  /opt/aishield/venv/bin/python3
```

### Deploy postup (až po review):
```bash
# 1. Upload změněných souborů
scp backend/documents/unified_pdf.py root@46.28.110.102:/opt/aishield/backend/documents/
scp backend/documents/pptx_generator.py root@46.28.110.102:/opt/aishield/backend/documents/
scp backend/documents/pipeline.py root@46.28.110.102:/opt/aishield/backend/documents/
# (přidej další soubory dle potřeby)

# 2. Syntax check na VPS
ssh root@46.28.110.102 '/opt/aishield/venv/bin/python3 -m py_compile /opt/aishield/backend/documents/unified_pdf.py && echo OK'

# 3. Restart služeb
ssh root@46.28.110.102 'systemctl restart aishield-api && systemctl restart aishield-worker'

# 4. Ověření
ssh root@46.28.110.102 'systemctl status aishield-api --no-pager | head -5'
```

## 4. DATABÁZE (Supabase)

```
URL:              https://rsxwqcrkttlfnqbjgpgc.supabase.co
Service Role Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJzeHdxY3JrdHRsZm5xYmpncGdjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDU3MTMxNywiZXhwIjoyMDg2MTQ3MzE3fQ.dxjnj7uQ3-uRRmqFa-MXnM6t3xL-Fci8A-xTqOvy-MU
DB Password:      Rc_732716141
Project ID:       rsxwqcrkttlfnqbjgpgc
```

### Testovací záznamy (pro generování):
```
Order ID:    3054d701-df1e-476e-b179-1616ca9cbc1f
Company ID:  62e22b1d-dbc3-486d-8aad-c495732049c8
Client ID:   950c79fa-28a1-42d0-9e27-3c998ca9bc11
Firma:       Martin Haynes
IČO:         17889251
```

### Klíčové tabulky:
- `orders` — objednávky (order_id → company_id)
- `companies` — firmy
- `clients` — klienti (clients.company_id → companies.id)
- `questionnaire_responses` — 46 odpovědí (filtr: client_id)
  - Sloupce: id, client_id, section, question_key, answer, details, tool_name, submitted_at
- `findings` — scan findings (filtr: company_id)
  - Sloupce: id, scan_id, company_id, name, category, risk_level, ai_act_article, action_required, ai_classification_text, source, status, confidence
- `documents` — vygenerované dokumenty
- `document_files` — soubory v Supabase Storage

## 5. BUGY K OPRAVĚ (prioritně seřazené)

### BUG 1: Raw LLM error message viditelná zákazníkovi
**Kde:** `findings` tabulka — finding "AI API Proxy (geminiproxy)" má `ai_classification_text` obsahující raw error:
```
⚠️ AI klasifikace selhala (LLM failed: Cannot parse Claude response as JSON...)
```
**Projevuje se v:** Zpráva o souladu (str. 2), Akční plán
**Fix:** V `unified_pdf.py` — tam kde se renderuje `action_required` nebo `ai_classification_text` — přidat sanitizaci. Pokud text obsahuje "LLM failed" nebo "selhala", nahradit neutrálním textem nebo přeskočit.
**Alternativa:** Opravit v `classifier.py` — aby raw error nikdy nešel do DB.

### BUG 2: Neúplná QUESTIONNAIRE_RISK_MAP
**Kde:** `unified_pdf.py` řádek ~415
**Problém:** Mapa mapuje question_key → risk_level, ale chybí 9+ klíčů. Fallback je "minimal".
**Doplnit:**
```python
QUESTIONNAIRE_RISK_MAP = {
    # Existující:
    "uses_ai_employee_monitoring": "high",
    "uses_ai_recruitment": "high",
    "uses_ai_creditscoring": "high",
    "uses_emotion_recognition": "high",
    "uses_biometric_categorization": "high",
    "uses_ai_chatbot": "limited",
    "uses_ai_email_auto": "limited",
    "uses_chatgpt": "limited",
    "uses_copilot": "limited",
    "uses_ai_content": "limited",
    "uses_deepfake": "limited",
    "uses_ai_translation": "minimal",
    "uses_ai_analytics": "minimal",
    "uses_ai_data_processing": "minimal",
    # CHYBĚJÍCÍ — DOPLNIT:
    "uses_ai_insurance": "high",           # Příloha III bod 5a
    "uses_ai_for_children": "high",        # Příloha III bod 3
    "uses_ai_critical_infra": "high",      # Příloha III bod 2
    "uses_ai_safety_component": "high",    # čl. 6 odst. 1
    "develops_own_ai": "high",             # čl. 16 — provider povinnosti
    "modifies_ai_purpose": "high",         # čl. 25 — nový provider
    "uses_gpai_api": "limited",            # čl. 51-54 GPAI
    "uses_ai_decision": "high",            # čl. 14 — automatizované rozhodování
    "uses_dynamic_pricing": "limited",     # čl. 5 potenciálně manipulativní
    "uses_ai_accounting": "limited",       # finance — omezené
    "uses_social_scoring": "high",         # čl. 5 — ZAKÁZÁNO
    "uses_subliminal_manipulation": "high", # čl. 5 — ZAKÁZÁNO
    "uses_realtime_biometric": "high",     # čl. 5 — ZAKÁZÁNO
}
```

### BUG 3: Monitoring plan + Vendor checklist ignorují QUESTIONNAIRE_RISK_MAP
**Kde:** `unified_pdf.py` — funkce `_section_monitoring_plan()` (řádek ~2006) a `_section_vendor_checklist()` (řádek ~1895)
**Problém:** Obě dělají:
```python
rl = (sys.get("details") or {}).get("risk_level") or "minimal"
```
`details` NIKDY neobsahuje `risk_level` — jsou to detaily odpovědi (nástroje, metody atd.)
**Fix:** Nahradit za:
```python
rl = QUESTIONNAIRE_RISK_MAP.get(sys.get("key", ""), "minimal")
```

### BUG 4: Duplicitní scan findings
**Kde:** `pipeline.py` — funkce `_load_company_data()` (~řádek 240)
**Problém:** DB obsahuje 13 findings, ale jen 8 unikátních systémů. Duplikáty vznikly z různých scan sources (ai_classified + deep_scan).
**Fix:** Po načtení findings přidat deduplikaci:
```python
seen = set()
unique_findings = []
for f in findings:
    key = f.get("name", "")
    if key and key not in seen:
        seen.add(key)
        unique_findings.append(f)
    elif not key:
        unique_findings.append(f)
findings = unique_findings
```
**Pozor:** Při duplikátech preferovat ten s vyšším risk_level nebo s lepším source.

### BUG 5: Duplicitní LLM text v Transparentnost dokumentu
**Kde:** `unified_pdf.py` — sekce `_section_transparency_oversight()` (~řádek 2200+)
**Problém:** LLM personalizovaný text se vloží 2×. Pravděpodobně se volá `_get_llm_content()` dvakrát, nebo je template zdvojený.
**Fix:** Zkontroluj, zda se `llm_recommendation` nevkládá na dvou místech v HTML šabloně.

### BUG 6: PPTX prezentace — nedostatečná (HLAVNÍ ÚKOL)
**Kde:** `pptx_generator.py` (574 řádků)
**Problém:** 12 generických slidů, žádná per-systém personalizace, LLM se nezapojuje.
**Co chybí:**
- Slidy popisující KAŽDÝ AI systém firmy (název, co to dělá, riziko, příklad, povinnosti zaměstnanců)
- Specifické zakázané praktiky firmy (ne generický výčet)
- Postup při incidentu (eskalační řetězec)
- Kdo je odpovědná osoba a co přesně dělá
- Konkrétní příklady z oboru firmy
- Slide o důsledcích (pokuty, odpovědnost)
**Sub-bugy v PPTX:**
- `risk_level: "limited"` je hardcoded pro declared systems (řádek ~460) — mělo by být z QUESTIONNAIRE_RISK_MAP
- "none riziko" se zobrazuje raw — mělo by být "Mimo klasifikaci"
- Footer "Martin Haynes • Martin Haynes" — company_name = person_name → duplicitní
- Titulka ukazuje 14 odvětví v jednom řádku — potřeba zkrátit/oříznout

## 6. FLOW DAT (jak pipeline funguje)

```
generate_compliance_kit(order_id)
  └→ _resolve_ids(order_id) → company_id, client_id, billing_data
  └→ _load_company_data(company_id, billing_data)
       └→ findings z tabulky "findings" (WHERE company_id=...)
       └→ company z tabulky "companies" (WHERE id=company_id)
  └→ _load_questionnaire(client_id)
       └→ responses z tabulky "questionnaire_responses" (WHERE client_id=...)
       └→ → ai_systems_declared[], risk_breakdown, recommendations[]
  └→ pro každou sekci (12 PDF + PPTX + HTML):
       └→ unified_pdf._render_section(key, merged_data)
            └→ llm_content.get_llm_recommendation(key, data) → Gemini API call
            └→ Predefined KB text z knowledge_base.py
            └→ HTML template z unified_pdf.py
            └→ weasyprint → PDF bytes
       └→ pptx_generator.generate_training_pptx(data) → PPTX bytes
  └→ upload do Supabase Storage
```

## 7. QUESTIONNAIRE → DOKUMENT MAPOVÁNÍ

46 odpovědí v dotazníku. Klíčové:
- `uses_*` otázky (yes/no) → `ai_systems_declared[]` → zobrazeny ve VŠECH dokumentech
- Každá `uses_*` otázka má `risk_hint` v definici (questionnaire.py) — "high"/"limited"/"minimal"
- `QUESTIONNAIRE_RISK_MAP` v unified_pdf.py musí ODPOVÍDAT `risk_hint` z questionnaire.py
- Klient odpověděl YES na: social_scoring, subliminal_manipulation, realtime_biometric → zakázané praktiky (čl. 5)

## 8. GENEROVÁNÍ NOVÉ VERZE (po opravách)

**Toto NEDĚLEJ TY. Deploy a generování provede jiný agent (GitHub Copilot) po review tvých změn.**

Pro kontext — takto to funguje na produkci:
```
# Na VPS se spustí:
/opt/aishield/venv/bin/python3 -c "
from backend.documents.pipeline import generate_compliance_kit
result = generate_compliance_kit('3054d701-df1e-476e-b179-1616ca9cbc1f')
"
# Výstup: 13 PDF + 1 PPTX + 1 HTML → upload do Supabase Storage
```

## 9. ⚠️ KRITICKÉ PRAVIDLO — DEPLOY DĚLÁŠ TY NE!

**NEPŘIPOJUJ SE NA VPS. NEDEPLOYUJ. NESPOUŠTĚJ SSH PŘÍKAZY.**

Tvůj úkol je POUZE editovat soubory LOKÁLNĚ v ~/Projects/aishield/. 
Hesla a přístupy k VPS a Supabase jsou zde uvedeny pouze jako KONTEXT, abys rozuměl architektuře a datovému toku. 

**Deploy na VPS, restart služeb a generování nové verze provede JINÝ AGENT (GitHub Copilot)**, který má na starost produkční prostředí. On zkontroluje tvé lokální změny a teprve po review je nahraje na server.

### Tvůj workflow:
1. ✅ Edituj soubory lokálně (~/Projects/aishield/backend/...)
2. ✅ Spusť `python3 -m py_compile soubor.py` pro syntax check
3. ✅ Popiš co jsi změnil a proč
4. ❌ NEPŘIPOJUJ SE na 46.28.110.102
5. ❌ NESPOUŠTĚJ scp, ssh, rsync na VPS
6. ❌ NEVOLEJ Supabase API (ani pro čtení)
7. ❌ NERESTARTUJ služby
8. ❌ NEGENERUJ dokumenty

## 10. DALŠÍ POZNÁMKY

- **LLM API klíče** jsou v `/opt/aishield/.env` na VPS (Gemini, Claude, OpenAI)
- **weasyprint** je nainstalován ve venv na VPS — PDF rendering funguje jen tam
- **python-pptx** je nainstalován ve venv na VPS i lokálně
- Soubory v Supabase Storage jsou pod cestou: `documents/{company_id}/...`
