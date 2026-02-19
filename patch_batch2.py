#!/usr/bin/env python3
"""
BATCH 2 — Přidání chybějících followupů
========================================
P3:  Q29 followup pro "Ano" (kde přesně jsou data uložena)
P14: Q29 followup pro "Ne" (data mimo EU → GDPR varování)
P4:  Q33/Q34/Q38/Q39 followup pro "Ano" (INFO + krátký upřesnění)
"""

import re

FILE = "backend/api/questionnaire.py"

with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

original = content
changes = 0

# ──────────────────────────────────────────────
# P3 + P14: Q29 (ai_data_stored_eu) — přidat followup_yes a followup_no
# Aktuálně má jen followup pro condition="unknown"
# ──────────────────────────────────────────────

# Najít Q29 blok — hledáme konec jeho followup bloku a přidáme followup_yes/followup_no
# Aktuální struktura Q29:
#   "followup": { "condition": "unknown", "fields": [...] },
#   "risk_hint": "limited",

old_q29_risk = (
    '                "risk_hint": "limited",\n'
    '                "ai_act_article": "Na\u0159\u00edzen\u00ed GDPR \u010dl. 44+ \u2014 p\u0159enos dat do t\u0159et\u00edch zem\u00ed",\n'
    '            },\n'
    '        ],\n'
    '    },\n'
    '    # \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n'
    '    # Section 8: AI gramotnost'
)

new_q29_risk = (
    '                "followup_yes": {\n'
    '                    "fields": [\n'
    '                        {"key": "data_location_eu_detail", "label": "Kde p\u0159esn\u011b jsou data ulo\u017eena?", "type": "multi_select",\n'
    '                         "options": ["Azure EU (z\u00e1padn\u00ed Evropa)", "AWS Frankfurt / Irsko", "GCP EU", "Vlastn\u00ed server v \u010cR/EU", "Hetzner / OVH / jin\u00fd EU hosting", "Jin\u00e9"]},\n'
    '                        {"key": "data_location_eu_ok", "label": "\u2705 Ulo\u017een\u00ed dat v EU je z pohledu GDPR ide\u00e1ln\u00ed stav. Do dokumentace zaznamen\u00e1me konkr\u00e9tn\u00ed lokaci.", "type": "info"},\n'
    '                    ]\n'
    '                },\n'
    '                "followup_no": {\n'
    '                    "fields": [\n'
    '                        {"key": "data_outside_eu_warning", "label": "\u26a0\ufe0f Data va\u0161ich AI syst\u00e9m\u016f jsou ulo\u017eena mimo EU. Dle GDPR \u010dl. 44+ mus\u00edte m\u00edt pr\u00e1vn\u00ed z\u00e1klad pro p\u0159enos dat do t\u0159et\u00edch zem\u00ed \u2014 nap\u0159. standardn\u00ed smluvn\u00ed dolo\u017eky (SCC) nebo rozhodnut\u00ed o adekvaci. Ov\u011b\u0159te, zda m\u00e1te s poskytovatelem uzav\u0159enou DPA (Data Processing Agreement).", "type": "info"},\n'
    '                        {"key": "data_outside_eu_tool", "label": "Kter\u00e9 AI n\u00e1stroje ukl\u00e1daj\u00ed data mimo EU?", "type": "multi_select",\n'
    '                         "options": ["ChatGPT (OpenAI \u2014 USA)", "Google Gemini (USA)", "Claude (Anthropic \u2014 USA)", "Perplexity (USA)", "Jin\u00e9"]},\n'
    '                    ]\n'
    '                },\n'
    '                "risk_hint": "limited",\n'
    '                "ai_act_article": "Na\u0159\u00edzen\u00ed GDPR \u010dl. 44+ \u2014 p\u0159enos dat do t\u0159et\u00edch zem\u00ed",\n'
    '            },\n'
    '        ],\n'
    '    },\n'
    '    # \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n'
    '    # Section 8: AI gramotnost'
)

if old_q29_risk in content:
    content = content.replace(old_q29_risk, new_q29_risk, 1)
    changes += 1
    print("P3+P14: Q29 followup_yes (lokace dat) + followup_no (GDPR varování) přidány")
else:
    print("P3+P14: CHYBA — Q29 kontext nenalezen!")

# ──────────────────────────────────────────────
# P4a: Q33 (can_override_ai) — přidat followup pro "Ano"
# Aktuálně má jen followup_no
# ──────────────────────────────────────────────

old_q33 = (
    '            {\n'
    '                "key": "can_override_ai",\n'
    '                "text": "Mohou va\u0161i zam\u011bstnanci p\u0159epsat nebo zru\u0161it rozhodnut\u00ed AI syst\u00e9mu?",\n'
    '                "type": "yes_no_unknown",\n'
    '                "help_text": "P\u0159\u00edklady:\\n1) HR mana\u017eer m\u016f\u017ee p\u0159epsat doporu\u010den\u00ed AI p\u0159i v\u00fdb\u011bru kandid\u00e1t\u016f.\\n2) Oper\u00e1tor m\u016f\u017ee ru\u010dn\u011b zm\u011bnit automatick\u00e9 t\u0159\u00edd\u011bn\u00ed z\u00e1kaznick\u00fdch po\u017eadavk\u016f.\\n3) Schvalovac\u00ed proces vy\u017eaduje lidsk\u00fd podpis po AI anal\u00fdze.",\n'
    '                "followup_no": {\n'
)

new_q33 = (
    '            {\n'
    '                "key": "can_override_ai",\n'
    '                "text": "Mohou va\u0161i zam\u011bstnanci p\u0159epsat nebo zru\u0161it rozhodnut\u00ed AI syst\u00e9mu?",\n'
    '                "type": "yes_no_unknown",\n'
    '                "help_text": "P\u0159\u00edklady:\\n1) HR mana\u017eer m\u016f\u017ee p\u0159epsat doporu\u010den\u00ed AI p\u0159i v\u00fdb\u011bru kandid\u00e1t\u016f.\\n2) Oper\u00e1tor m\u016f\u017ee ru\u010dn\u011b zm\u011bnit automatick\u00e9 t\u0159\u00edd\u011bn\u00ed z\u00e1kaznick\u00fdch po\u017eadavk\u016f.\\n3) Schvalovac\u00ed proces vy\u017eaduje lidsk\u00fd podpis po AI anal\u00fdze.",\n'
    '                "followup": {\n'
    '                    "condition": "yes",\n'
    '                    "fields": [\n'
    '                        {"key": "override_scope", "label": "V jak\u00fdch p\u0159\u00edpadech se override pou\u017e\u00edv\u00e1?", "type": "multi_select",\n'
    '                         "options": ["V\u017edy \u2014 AI jen doporu\u010duje, \u010dlov\u011bk rozhoduje", "P\u0159i reklamac\u00edch a st\u00ed\u017enostech", "P\u0159i HR rozhodnut\u00edch", "P\u0159i finan\u010dn\u00edch rozhodnut\u00edch", "Jen v\u00fdjime\u010dn\u011b / eskalace", "Jin\u00e9"]},\n'
    '                        {"key": "override_ok_info", "label": "\u2705 V\u00fdborn\u011b! Mo\u017enost p\u0159epsat rozhodnut\u00ed AI je kl\u00ed\u010dov\u00fd po\u017eadavek \u010dl. 14 odst. 4 p\u00edsm. d) AI Act. Do dokumentace zaznamen\u00e1me, v jak\u00fdch p\u0159\u00edpadech override pou\u017e\u00edv\u00e1te.", "type": "info"},\n'
    '                    ]\n'
    '                },\n'
    '                "followup_no": {\n'
)

if old_q33 in content:
    content = content.replace(old_q33, new_q33, 1)
    changes += 1
    print("P4a: Q33 (can_override_ai) followup pro 'Ano' přidán")
else:
    print("P4a: CHYBA — Q33 kontext nenalezen!")

# ──────────────────────────────────────────────
# P4b: Q34 (ai_decision_logging) — přidat followup pro "Ano"
# Aktuálně má jen followup_no
# ──────────────────────────────────────────────

old_q34 = (
    '            {\n'
    '                "key": "ai_decision_logging",\n'
    '                "text": "Zaznamen\u00e1v\u00e1te rozhodnut\u00ed, kter\u00e1 AI syst\u00e9my d\u011blaj\u00ed nebo doporu\u010duj\u00ed?",\n'
    '                "type": "yes_no_unknown",\n'
    '                "help_text": "P\u0159\u00edklady:\\n1) Log chatbotov\u00fdch odpov\u011bd\u00ed pro zp\u011btnou kontrolu.\\n2) Archivace AI doporu\u010den\u00ed v CRM.\\n3) Z\u00e1znam automatizovan\u00fdch rozhodnut\u00ed v intern\u00edm syst\u00e9mu.",\n'
    '                "followup_no": {\n'
)

new_q34 = (
    '            {\n'
    '                "key": "ai_decision_logging",\n'
    '                "text": "Zaznamen\u00e1v\u00e1te rozhodnut\u00ed, kter\u00e1 AI syst\u00e9my d\u011blaj\u00ed nebo doporu\u010duj\u00ed?",\n'
    '                "type": "yes_no_unknown",\n'
    '                "help_text": "P\u0159\u00edklady:\\n1) Log chatbotov\u00fdch odpov\u011bd\u00ed pro zp\u011btnou kontrolu.\\n2) Archivace AI doporu\u010den\u00ed v CRM.\\n3) Z\u00e1znam automatizovan\u00fdch rozhodnut\u00ed v intern\u00edm syst\u00e9mu.",\n'
    '                "followup": {\n'
    '                    "condition": "yes",\n'
    '                    "fields": [\n'
    '                        {"key": "logging_method", "label": "Jak\u00fdm zp\u016fsobem logujete?", "type": "multi_select",\n'
    '                         "options": ["Logy v aplikaci (automatick\u00e9)", "Export do SIEM / centr\u00e1ln\u00edho logu", "Excel / tabulka", "Ticketovac\u00ed syst\u00e9m (Jira, Freshdesk)", "Jin\u00fd syst\u00e9m"]},\n'
    '                        {"key": "logging_retention", "label": "Jak dlouho logy uchov\u00e1v\u00e1te?", "type": "single_select",\n'
    '                         "options": ["M\u00e9n\u011b ne\u017e 6 m\u011bs\u00edc\u016f", "6\u201312 m\u011bs\u00edc\u016f", "1\u20133 roky", "D\u00e9le ne\u017e 3 roky", "Nev\u00edm"]},\n'
    '                        {"key": "logging_ok_info", "label": "\u2705 V\u00fdborn\u011b! \u010cl. 26 odst. 1 p\u00edsm. f) AI Act vy\u017eaduje uchov\u00e1v\u00e1n\u00ed log\u016f minim\u00e1ln\u011b 6 m\u011bs\u00edc\u016f. Do dokumentace zaznamen\u00e1me v\u00e1\u0161 syst\u00e9m logov\u00e1n\u00ed.", "type": "info"},\n'
    '                    ]\n'
    '                },\n'
    '                "followup_no": {\n'
)

if old_q34 in content:
    content = content.replace(old_q34, new_q34, 1)
    changes += 1
    print("P4b: Q34 (ai_decision_logging) followup pro 'Ano' přidán")
else:
    print("P4b: CHYBA — Q34 kontext nenalezen!")

# ──────────────────────────────────────────────
# P4c: Q38 (monitors_ai_outputs) — přidat followup pro "Ano"
# Aktuálně má jen followup_no
# ──────────────────────────────────────────────

# Q38 má scope_hint (upraven v BATCH 1), pak followup_no
# Potřebujeme přidat followup (condition=yes) před followup_no

old_q38_start = (
    '                "key": "monitors_ai_outputs",\n'
    '                "text": "Pravideln\u011b kontrolujete kvalitu a spr\u00e1vnost v\u00fdstup\u016f va\u0161ich AI syst\u00e9m\u016f?",'
)

# Find Q38 and add followup before followup_no
# The structure after BATCH 1 scope_hint change:
# "scope_hint": "...",
# "followup_no": {

old_q38_followup_no = (
    '                "followup_no": {\n'
    '                    "fields": [\n'
    '                        {"key": "monitoring_warning"'
)

# We need to find this specific followup_no that belongs to monitors_ai_outputs
# Let's use a broader context to be precise
old_q38_block = (
    '"scope_hint": "Tato ot\u00e1zka se t\u00fdk\u00e1 v\u0161ech AI syst\u00e9m\u016f, kter\u00e9 ve firm\u011b pou\u017e\u00edv\u00e1te. '
    'Odpov\u011bzte ANO, pokud n\u011bkdo pravideln\u011b kontroluje spr\u00e1vnost v\u00fdstup\u016f AI '
    '(nap\u0159. \u010dte odpov\u011bdi chatbota, ov\u011b\u0159uje AI doporu\u010den\u00ed). '
    'Odpov\u011bzte NE, pokud AI b\u011b\u017e\u00ed bez jak\u00e9koliv kontroly kvality v\u00fdstup\u016f.",\n'
    '                "followup_no": {'
)

new_q38_block = (
    '"scope_hint": "Tato ot\u00e1zka se t\u00fdk\u00e1 v\u0161ech AI syst\u00e9m\u016f, kter\u00e9 ve firm\u011b pou\u017e\u00edv\u00e1te. '
    'Odpov\u011bzte ANO, pokud n\u011bkdo pravideln\u011b kontroluje spr\u00e1vnost v\u00fdstup\u016f AI '
    '(nap\u0159. \u010dte odpov\u011bdi chatbota, ov\u011b\u0159uje AI doporu\u010den\u00ed). '
    'Odpov\u011bzte NE, pokud AI b\u011b\u017e\u00ed bez jak\u00e9koliv kontroly kvality v\u00fdstup\u016f.",\n'
    '                "followup": {\n'
    '                    "condition": "yes",\n'
    '                    "fields": [\n'
    '                        {"key": "monitoring_frequency", "label": "Jak \u010dasto kontrolujete v\u00fdstupy AI?", "type": "single_select",\n'
    '                         "options": ["Denn\u011b", "T\u00fddn\u011b", "M\u011bs\u00ed\u010dn\u011b", "Nep\u0159\u00edpravid\u011bln\u011b / ad hoc"]},\n'
    '                        {"key": "monitoring_ok_info", "label": "\u2705 V\u00fdborn\u011b! Pravideln\u00fd monitoring v\u00fdstup\u016f AI je z\u00e1kladem \u010dl. 9 AI Act (syst\u00e9m \u0159\u00edzen\u00ed rizik). Do dokumentace zaznamen\u00e1me v\u00e1\u0161 monitoring proces.", "type": "info"},\n'
    '                    ]\n'
    '                },\n'
    '                "followup_no": {'
)

if old_q38_block in content:
    content = content.replace(old_q38_block, new_q38_block, 1)
    changes += 1
    print("P4c: Q38 (monitors_ai_outputs) followup pro 'Ano' přidán")
else:
    print("P4c: CHYBA — Q38 kontext nenalezen!")

# ──────────────────────────────────────────────
# P4d: Q39 (tracks_ai_changes) — přidat followup pro "Ano"
# Aktuálně má jen followup_no
# ──────────────────────────────────────────────

old_q39 = (
    '            {\n'
    '                "key": "tracks_ai_changes",\n'
    '                "text": "Dokumentujete zm\u011bny ve vlastn\u00edch AI syst\u00e9mech, kter\u00e9 provozujete nebo vyv\u00edj\u00edte?",\n'
    '                "type": "yes_no_unknown",\n'
)

# Find the scope_hint + followup_no boundary for Q39
old_q39_boundary = (
    '"scope_hint": "Tato ot\u00e1zka se t\u00fdk\u00e1 firem, kter\u00e9 PROVOZUJ\u00cd nebo VYVI\u0301J\u0306EJ\u00cd vlastn\u00ed AI \u0159e\u0161en\u00ed'
)

# Hmm, the text uses composed unicode characters. Let me try a different approach.
# Let me search for the normalized form

# Actually, let me look for the followup_no of tracks_ai_changes by its unique key
old_q39_fn = (
    '                        {"key": "changes_warning"'
)

# Better approach: find the exact text around Q39's followup_no using unique markers
# The scope_hint text is unique to Q39
q39_scope_marker = 'PROVOZUJ'

# Let me try finding the scope_hint line for Q39 and inserting followup before followup_no
# Using regex for more flexibility

q39_pattern = (
    r'("scope_hint": "Tato ot[^"]*PROVOZUJ[^"]*",\n)'
    r'(\s+"followup_no": \{)'
)

q39_replacement = (
    r'\g<1>'
    '                "followup": {\n'
    '                    "condition": "yes",\n'
    '                    "fields": [\n'
    '                        {"key": "changes_tracking_method", "label": "Jak zm\u011bny dokumentujete?", "type": "multi_select",\n'
    '                         "options": ["Verze v Git / repozit\u00e1\u0159i", "Intern\u00ed tabulka / evidence", "Ticketovac\u00ed syst\u00e9m (Jira)", "Changelog v dokumentaci", "Jin\u00fd zp\u016fsob"]},\n'
    '                        {"key": "changes_ok_info", "label": "\u2705 V\u00fdborn\u011b! Dokumentace zm\u011bn je po\u017eadavek P\u0159\u00edlohy IV bod 6 AI Act. Do compliance dokumentace zaznamen\u00e1me v\u00e1\u0161 syst\u00e9m evidence zm\u011bn.", "type": "info"},\n'
    '                    ]\n'
    '                },\n'
    r'\g<2>'
)

new_content, count = re.subn(q39_pattern, q39_replacement, content, count=1)
if count > 0:
    content = new_content
    changes += 1
    print("P4d: Q39 (tracks_ai_changes) followup pro 'Ano' přidán")
else:
    print("P4d: CHYBA — Q39 regex pattern nenalezen! Zkouším alternativu...")
    # Alternative: try simpler finding
    # Find "changes_warning" and insert before the followup_no that contains it
    alt_marker = '"followup_no": {\n                    "fields": [\n                        {"key": "changes_warning"'
    if alt_marker in content:
        insert_text = (
            '"followup": {\n'
            '                    "condition": "yes",\n'
            '                    "fields": [\n'
            '                        {"key": "changes_tracking_method", "label": "Jak zm\u011bny dokumentujete?", "type": "multi_select",\n'
            '                         "options": ["Verze v Git / repozit\u00e1\u0159i", "Intern\u00ed tabulka / evidence", "Ticketovac\u00ed syst\u00e9m (Jira)", "Changelog v dokumentaci", "Jin\u00fd zp\u016fsob"]},\n'
            '                        {"key": "changes_ok_info", "label": "\u2705 V\u00fdborn\u011b! Dokumentace zm\u011bn je po\u017eadavek P\u0159\u00edlohy IV bod 6 AI Act. Do compliance dokumentace zaznamen\u00e1me v\u00e1\u0161 syst\u00e9m evidence zm\u011bn.", "type": "info"},\n'
            '                    ]\n'
            '                },\n'
            '                '
        )
        content = content.replace(alt_marker, insert_text + alt_marker, 1)
        changes += 1
        print("P4d: Q39 (tracks_ai_changes) followup pro 'Ano' přidán (alternativní metoda)")
    else:
        print("P4d: CHYBA — ani alternativa nenalezena!")

# ──────────────────────────────────────────────
# Uložit a potvrdit
# ──────────────────────────────────────────────

if content != original:
    with open(FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n✅ BATCH 2 HOTOV — {changes} změn provedeno, soubor uložen ({FILE})")
else:
    print("\n❌ Žádné změny neprovedeny!")
