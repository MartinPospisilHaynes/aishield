#!/usr/bin/env python3
"""
Comprehensive patch for questionnaire.py — fixes from user review:
1. Remove "are informed/disclosed" sub-questions (5 fields) — our documentation covers this
2. Fix typos in uses_dynamic_pricing help_text
3. Simplify uses_subliminal_manipulation — remove type sub-Q, keep only warning
4. Add 5 more AI tools to ai_data_stored_eu
5. Change has_oversight_person to always show fields (condition: "any")
6. Change warning texts — remove "Nebojte se" promises where inappropriate
7. Replace "šablonu"/"šablona" → "profesionálně zpracovanou dokumentaci" across file
"""
import re, sys

FILE = "/Users/martinhaynes/Projects/aishield/backend/api/questionnaire.py"

with open(FILE, "r", encoding="utf-8") as f:
    src = f.read()

original = src
changes = []

# ─────────────────────────────────────────────────────────
# 1. REMOVE "deepfake_disclosed" from uses_deepfake followup
# ─────────────────────────────────────────────────────────
old = '''                        {"key": "deepfake_tool_name", "label": "Kter\u00e9 n\u00e1stroje pou\u017e\u00edv\u00e1te? (vyberte v\u0161e)", "type": "multi_select",
                         "options": ["HeyGen", "Synthesia", "ElevenLabs", "D-ID", "Murf AI", "Jin\u00fd"]},
                        {"key": "deepfake_disclosed", "label": "Ozna\u010dujete tento obsah jako AI generovan\u00fd?", "type": "select",
                         "options": ["Ano", "Ne"],
                         "warning": {"Ne": "Od 2. srpna 2026 je podle \u010dl. 50 AI Act povinn\u00e9 ozna\u010dit ve\u0161ker\u00fd deep-fake obsah (syntetick\u00e1 videa, klonovan\u00fd hlas, AI avatary) jako um\u011ble vytvo\u0159en\u00fd. Nespln\u011bn\u00ed m\u016f\u017ee v\u00e9st k pokut\u011b."}},'''

new = '''                        {"key": "deepfake_tool_name", "label": "Kter\u00e9 n\u00e1stroje pou\u017e\u00edv\u00e1te? (vyberte v\u0161e)", "type": "multi_select",
                         "options": ["HeyGen", "Synthesia", "ElevenLabs", "D-ID", "Murf AI", "Jin\u00fd"]},
                        {"key": "deepfake_disclosure_info", "label": "\u2139\ufe0f Od 2. srpna 2026 je podle \u010dl. 50 AI Act povinn\u00e9 ozna\u010dit ve\u0161ker\u00fd deep-fake obsah jako um\u011ble vytvo\u0159en\u00fd. V r\u00e1mci slu\u017eby AIshield v\u00e1m dod\u00e1me profesion\u00e1ln\u011b zpracovanou dokumentaci v\u010detn\u011b pokyn\u016f pro spr\u00e1vn\u00e9 ozna\u010dov\u00e1n\u00ed AI obsahu.", "type": "info"},'''

if old in src:
    src = src.replace(old, new)
    changes.append("1. Removed deepfake_disclosed, added info about documentation")
else:
    changes.append("1. FAILED — deepfake_disclosed pattern not found")

# ─────────────────────────────────────────────────────────
# 2. REMOVE "monitoring_informed" from uses_ai_employee_monitoring
# ─────────────────────────────────────────────────────────
old = '''                        {"key": "monitoring_type", "label": "Co sledujete?", "type": "multi_select",
                         "options": ["Sledov\u00e1n\u00ed obrazovky", "M\u011b\u0159en\u00ed produktivity", "GPS sledov\u00e1n\u00ed", "Kamerov\u00fd dohled s AI", "Anal\u00fdza email\u016f", "Jin\u00e9"]},
                        {"key": "monitoring_informed", "label": "Jsou zam\u011bstnanci informov\u00e1ni?", "type": "select",
                         "options": ["Ano", "Ne"],
                         "warning": {"Ne": "Zam\u011bstnanci maj\u00ed pr\u00e1vo b\u00fdt informov\u00e1ni o sledov\u00e1n\u00ed. Neinformov\u00e1n\u00ed m\u016f\u017ee poru\u0161it GDPR i AI Act (\u010dl. 26 odst. 7)."}},'''

new = '''                        {"key": "monitoring_type", "label": "Co sledujete?", "type": "multi_select",
                         "options": ["Sledov\u00e1n\u00ed obrazovky", "M\u011b\u0159en\u00ed produktivity", "GPS sledov\u00e1n\u00ed", "Kamerov\u00fd dohled s AI", "Anal\u00fdza email\u016f", "Jin\u00e9"]},
                        {"key": "monitoring_compliance_info", "label": "\u2139\ufe0f Zam\u011bstnanci mus\u00ed b\u00fdt informov\u00e1ni o sledov\u00e1n\u00ed dle GDPR i AI Act (\u010dl. 26 odst. 7). V r\u00e1mci slu\u017eby AIshield v\u00e1m dod\u00e1me profesion\u00e1ln\u011b zpracovanou prezentaci (PowerPoint), kterou zam\u011bstnanc\u016fm p\u0159edstav\u00edte, a dokumentaci informov\u00e1n\u00ed zam\u011bstnanc\u016f.", "type": "info"},'''

if old in src:
    src = src.replace(old, new)
    changes.append("2. Removed monitoring_informed, added compliance info")
else:
    changes.append("2. FAILED — monitoring_informed pattern not found")

# ─────────────────────────────────────────────────────────
# 3. REMOVE "chatbot_disclosed" from uses_ai_chatbot
# ─────────────────────────────────────────────────────────
old = '''                        {"key": "chatbot_tool_name", "label": "Kter\u00e9 n\u00e1stroje pou\u017e\u00edv\u00e1te? (vyberte v\u0161e)", "type": "multi_select",
                         "options": ["Smartsupp", "Tidio", "Intercom", "Drift", "Chatbot.cz", "Jin\u00e9"]},
                        {"key": "chatbot_disclosed", "label": "V\u00ed n\u00e1v\u0161t\u011bvn\u00edk, \u017ee komunikuje s AI?", "type": "select",
                         "options": ["Ano", "Ne"],
                         "warning": {"Ne": "Podle \u010dl. 50 AI Act mus\u00ed b\u00fdt z\u00e1kazn\u00edci informov\u00e1ni, \u017ee komunikuj\u00ed s AI syst\u00e9mem. Tato povinnost plat\u00ed od 2. srpna 2026."}},'''

new = '''                        {"key": "chatbot_tool_name", "label": "Kter\u00e9 n\u00e1stroje pou\u017e\u00edv\u00e1te? (vyberte v\u0161e)", "type": "multi_select",
                         "options": ["Smartsupp", "Tidio", "Intercom", "Drift", "Chatbot.cz", "Jin\u00e9"]},
                        {"key": "chatbot_compliance_info", "label": "\u2139\ufe0f Podle \u010dl. 50 AI Act mus\u00ed b\u00fdt z\u00e1kazn\u00edci informov\u00e1ni, \u017ee komunikuj\u00ed s AI syst\u00e9mem (od 2. srpna 2026). V r\u00e1mci slu\u017eby AIshield v\u00e1m dod\u00e1me profesion\u00e1ln\u011b zpracovanou dokumentaci v\u010detn\u011b textu ozn\u00e1men\u00ed pro chatbota.", "type": "info"},'''

if old in src:
    src = src.replace(old, new)
    changes.append("3. Removed chatbot_disclosed, added compliance info")
else:
    changes.append("3. FAILED — chatbot_disclosed pattern not found")

# ─────────────────────────────────────────────────────────
# 4. REMOVE "email_disclosed" from uses_ai_email_auto
# ─────────────────────────────────────────────────────────
old = '''                        {"key": "email_tool", "label": "Kter\u00e9 n\u00e1stroje pou\u017e\u00edv\u00e1te? (vyberte v\u0161e)", "type": "multi_select",
                         "options": ["Freshdesk AI", "Zendesk AI", "Intercom", "Jin\u00e9"]},
                        {"key": "email_disclosed", "label": "V\u00ed z\u00e1kazn\u00edk, \u017ee odpov\u00edd\u00e1 AI?", "type": "select",
                         "options": ["Ano", "Ne"],
                         "warning": {"Ne": "Podle \u010dl. 50 AI Act mus\u00ed b\u00fdt z\u00e1kazn\u00edci informov\u00e1ni, \u017ee komunikuj\u00ed s AI syst\u00e9mem. Tato povinnost plat\u00ed od 2. srpna 2026."}},'''

new = '''                        {"key": "email_tool", "label": "Kter\u00e9 n\u00e1stroje pou\u017e\u00edv\u00e1te? (vyberte v\u0161e)", "type": "multi_select",
                         "options": ["Freshdesk AI", "Zendesk AI", "Intercom", "Jin\u00e9"]},
                        {"key": "email_compliance_info", "label": "\u2139\ufe0f Podle \u010dl. 50 AI Act mus\u00ed b\u00fdt z\u00e1kazn\u00edci informov\u00e1ni, \u017ee komunikuj\u00ed s AI syst\u00e9mem (od 2. srpna 2026). Sou\u010d\u00e1st\u00ed va\u0161\u00ed dokumentace bude text informov\u00e1n\u00ed z\u00e1kazn\u00edk\u016f.", "type": "info"},'''

if old in src:
    src = src.replace(old, new)
    changes.append("4. Removed email_disclosed, added compliance info")
else:
    changes.append("4. FAILED — email_disclosed pattern not found")

# ─────────────────────────────────────────────────────────
# 5. Change uses_ai_decision warning — remove "Nebojte se" promise
# ─────────────────────────────────────────────────────────
old = '''                        {"key": "decision_human_review", "label": "Je k dispozici lidsk\u00fd p\u0159ezkum?", "type": "select",
                         "options": ["Ano", "Ne"],
                         "warning": {"Ne": "AI rozhoduj\u00edc\u00ed o pr\u00e1vech z\u00e1kazn\u00edk\u016f bez mo\u017enosti lidsk\u00e9ho p\u0159ezkumu poru\u0161uje \u010dl. 14 AI Act (povinnost lidsk\u00e9ho dohledu). Z\u00e1kazn\u00edk m\u00e1 pr\u00e1vo po\u017eadovat, aby rozhodnut\u00ed p\u0159ezkoumal \u010dlov\u011bk."}},'''

new = '''                        {"key": "decision_human_review", "label": "Je k dispozici lidsk\u00fd p\u0159ezkum?", "type": "select",
                         "options": ["Ano", "Ne"],
                         "warning": {"Ne": "\u26a0\ufe0f AI rozhoduj\u00edc\u00ed o pr\u00e1vech z\u00e1kazn\u00edk\u016f bez mo\u017enosti lidsk\u00e9ho p\u0159ezkumu poru\u0161uje \u010dl. 14 AI Act. Z\u00e1kazn\u00edk m\u00e1 pr\u00e1vo po\u017eadovat, aby rozhodnut\u00ed p\u0159ezkoumal \u010dlov\u011bk. Mus\u00edte si nastavit intern\u00ed postupy tak, aby rozhodov\u00e1n\u00ed AI nebylo protipr\u00e1vn\u00ed \u2014 v r\u00e1mci dokumentace v\u00e1m dod\u00e1me doporu\u010den\u00ed, jak tyto procesy zavést."}},'''

if old in src:
    src = src.replace(old, new)
    changes.append("5. Changed decision_human_review warning — instructs to set up internal processes")
else:
    changes.append("5. FAILED — decision_human_review warning not found")

# ─────────────────────────────────────────────────────────
# 6. REMOVE "pricing_disclosed" from uses_dynamic_pricing
# ─────────────────────────────────────────────────────────
old = '''                        {"key": "pricing_disclosed", "label": "V\u00ed z\u00e1kazn\u00edk o personalizaci cen?", "type": "select",
                         "options": ["Ano", "Ne"],
                         "warning": {"Ne": "Personalizace cen bez informov\u00e1n\u00ed z\u00e1kazn\u00edka m\u016f\u017ee p\u0159edstavovat nekalou obchodn\u00ed praktiku a poru\u0161en\u00ed transparentnosti dle AI Act."}},'''

new = '''                        {"key": "pricing_compliance_info", "label": "\u26a0\ufe0f Personalizace cen bez informov\u00e1n\u00ed z\u00e1kazn\u00edka m\u016f\u017ee p\u0159edstavovat nekalou obchodn\u00ed praktiku a poru\u0161en\u00ed transparentnosti dle AI Act. Mus\u00edte si nastavit intern\u00ed postupy tak, abyste si nepo\u010d\u00ednali protipr\u00e1vn\u011b \u2014 v r\u00e1mci dokumentace v\u00e1m dod\u00e1me doporu\u010den\u00ed.", "type": "info"},'''

if old in src:
    src = src.replace(old, new)
    changes.append("6. Removed pricing_disclosed, added compliance warning + instruction")
else:
    changes.append("6. FAILED — pricing_disclosed pattern not found")

# ─────────────────────────────────────────────────────────
# 7. FIX TYPOS in uses_dynamic_pricing help_text
# ─────────────────────────────────────────────────────────
old_typo = 'Let\u011bnky zdra\u017euj\u00ed'
new_typo = 'Letenky zdra\u017euj\u00ed'
if old_typo in src:
    src = src.replace(old_typo, new_typo)
    changes.append("7a. Fixed 'Letěnky' → 'Letenky'")
else:
    changes.append("7a. FAILED — 'Letěnky' not found")

old_typo2 = 'vrac\u00edce se vs. novemu z\u00e1kazn\u00edkovi'
new_typo2 = 'vracej\u00edc\u00edmu se vs. nov\u00e9mu z\u00e1kazn\u00edkovi'
if old_typo2 in src:
    src = src.replace(old_typo2, new_typo2)
    changes.append("7b. Fixed 'vracíce se vs. novemu' → 'vracejícímu se vs. novému'")
else:
    changes.append("7b. FAILED — 'vracíce se' not found")

# ─────────────────────────────────────────────────────────
# 8. SIMPLIFY uses_subliminal_manipulation — remove type sub-Q
# ─────────────────────────────────────────────────────────
old = '''                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "manipulation_type", "label": "O jak\u00fd typ ovliv\u0148ov\u00e1n\u00ed jde? (vyberte v\u0161e)", "type": "multi_select",
                         "options": ["Dynamick\u00e9 ceny podle emoc\u00ed/chov\u00e1n\u00ed", "C\u00edlen\u00ed na zraniteln\u00e9 skupiny", "Skryt\u00e9 manipulativn\u00ed UX vzory", "Jin\u00e9"]},
                        {"key": "manipulation_warning", "label": "\ud83d\udeab ZAK\u00c1ZAN\u00dd SYST\u00c9M \u2014 Podprahov\u00e1 manipulace pomoc\u00ed AI je v\u00fdslovn\u011b zak\u00e1z\u00e1na \u010dl. 5 odst. 1 p\u00edsm. a) AI Act. Pokuta a\u017e 35 milion\u016f EUR nebo 7 % celosv\u011btov\u00e9ho obratu. Okam\u017eit\u011b ukon\u010dete provoz tohoto syst\u00e9mu a konzultujte s pr\u00e1vn\u00edkem. V tomto p\u0159\u00edpad\u011b nedok\u00e1\u017eeme pomoct ani my \u2014 jedn\u00e1 se o protipr\u00e1vn\u00ed jedn\u00e1n\u00ed.", "type": "info"},
                    ]
                },'''

new = '''                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "manipulation_warning", "label": "\ud83d\udeab ZAK\u00c1ZAN\u00dd SYST\u00c9M \u2014 Podprahov\u00e1 manipulace pomoc\u00ed AI je v\u00fdslovn\u011b zak\u00e1z\u00e1na \u010dl. 5 odst. 1 p\u00edsm. a) AI Act. Pokuta a\u017e 35 milion\u016f EUR nebo 7 % celosv\u011btov\u00e9ho obratu. Okam\u017eit\u011b ukon\u010dete provoz tohoto syst\u00e9mu a konzultujte s pr\u00e1vn\u00edkem. V tomto p\u0159\u00edpad\u011b nedok\u00e1\u017eeme pomoct ani my \u2014 jedn\u00e1 se o protipr\u00e1vn\u00ed jedn\u00e1n\u00ed.", "type": "info"},
                    ]
                },'''

if old in src:
    src = src.replace(old, new)
    changes.append("8. Simplified uses_subliminal_manipulation — removed type sub-question")
else:
    changes.append("8. FAILED — manipulation followup pattern not found")

# ─────────────────────────────────────────────────────────
# 9. ADD 5 more AI tools to ai_data_stored_eu
# ─────────────────────────────────────────────────────────
old = '''                         "options": ["ChatGPT (OpenAI \u2014 USA)", "Google Gemini (USA/EU)", "Microsoft Copilot (EU i USA)", "Claude (Anthropic \u2014 USA)", "Vlastn\u00ed server v \u010cR/EU", "Jin\u00fd"]},'''

new = '''                         "options": ["ChatGPT (OpenAI \u2014 USA)", "Google Gemini (USA/EU)", "Microsoft Copilot (EU i USA)", "Claude (Anthropic \u2014 USA)", "Perplexity (USA)", "Midjourney (USA)", "Jasper AI (USA)", "DeepL (Německo/EU)", "Grammarly (USA)", "Notion AI (USA)", "Vlastn\u00ed server v \u010cR/EU", "Jin\u00fd"]},'''

if old in src:
    src = src.replace(old, new, 1)
    changes.append("9. Added 6 more AI tools to ai_data_stored_eu (Perplexity, Midjourney, Jasper, DeepL, Grammarly, Notion)")
else:
    changes.append("9. FAILED — ai_data_stored_eu options pattern not found")

# ─────────────────────────────────────────────────────────
# 10. Change has_oversight_person followup condition to "any"
# ─────────────────────────────────────────────────────────
# Find the oversight followup condition
old = '''"key": "has_oversight_person",
                "text": "M\u00e1te ur\u010denou osobu/t\u00fdm zodpov\u011bdn\u00fd za dohled nad AI syst\u00e9my?",
                "type": "yes_no_unknown",'''

new = '''"key": "has_oversight_person",
                "text": "M\u00e1te ur\u010denou osobu/t\u00fdm zodpov\u011bdn\u00fd za dohled nad AI syst\u00e9my?",
                "type": "yes_no_unknown",'''

# Actually just change the condition from "yes" to "any"
old_cond = '''"key": "has_oversight_person",
                "text": "M\u00e1te ur\u010denou osobu/t\u00fdm zodpov\u011bdn\u00fd za dohled nad AI syst\u00e9my?"'''
if old_cond in src:
    # Change condition in the followup
    # Find the followup block after has_oversight_person
    idx = src.index(old_cond)
    # Find "condition": "yes" after this point (within 300 chars)
    sub = src[idx:idx+600]
    old_fc = '"condition": "yes",'
    if old_fc in sub:
        pos = idx + sub.index(old_fc)
        src = src[:pos] + '"condition": "any",' + src[pos+len(old_fc):]
        changes.append("10. Changed has_oversight_person followup condition to 'any'")
    else:
        changes.append("10. FAILED — condition 'yes' not found near has_oversight_person")
else:
    changes.append("10. FAILED — has_oversight_person pattern not found")

# ─────────────────────────────────────────────────────────
# 11. Change credit_impact warning — no "Nebojte se" promise
# ─────────────────────────────────────────────────────────
old = '''"warning": {"Ano, p\u0159\u00edmo rozhoduje": "Automatick\u00e9 rozhodov\u00e1n\u00ed o \u00fav\u011brech bez lidsk\u00e9ho dohledu spad\u00e1 do kategorie vysoce rizikov\u00fdch AI syst\u00e9m\u016f (P\u0159\u00edloha III, bod 5b). Vy\u017eaduje registraci v EU datab\u00e1zi a pr\u016fb\u011b\u017en\u00e9 monitorov\u00e1n\u00ed."}'''

new = '''"warning": {"Ano, p\u0159\u00edmo rozhoduje": "\u26a0\ufe0f Automatick\u00e9 rozhodov\u00e1n\u00ed o \u00fav\u011brech bez lidsk\u00e9ho dohledu spad\u00e1 do kategorie vysoce rizikov\u00fdch AI syst\u00e9m\u016f (P\u0159\u00edloha III, bod 5b). Va\u0161e firma mus\u00ed prov\u00e9st registraci v EU datab\u00e1zi a zajistit pr\u016fb\u011b\u017en\u00e9 monitorov\u00e1n\u00ed \u2014 toto je z\u00e1konn\u00e1 povinnost, kterou mus\u00edte splnit intern\u011b. V r\u00e1mci dokumentace v\u00e1m poskytneme pot\u0159ebn\u00e9 podklady a doporu\u010den\u00ed."}'''

if old in src:
    src = src.replace(old, new)
    changes.append("11. Changed credit_impact warning — must register with authorities")
else:
    changes.append("11. FAILED — credit_impact warning not found")

# ─────────────────────────────────────────────────────────
# 12. Change insurance_impact warning — no blanket promise
# ─────────────────────────────────────────────────────────
old = '''"warning": {"Ano": "AI syst\u00e9m, kter\u00fd ovliv\u0148uje cenu nebo dostupnost poji\u0161t\u011bn\u00ed, je vysoce rizikov\u00fd dle P\u0159\u00edlohy III, bod 5a. Mus\u00edte zajistit posouzen\u00ed shody, registraci v EU datab\u00e1zi, pr\u016fb\u011b\u017en\u00e9 monitorov\u00e1n\u00ed a pr\u00e1vo pojistn\u00edka na vysv\u011btlen\u00ed rozhodnut\u00ed."}'''

new = '''"warning": {"Ano": "\u26a0\ufe0f AI syst\u00e9m ovliv\u0148uj\u00edc\u00ed cenu nebo dostupnost poji\u0161t\u011bn\u00ed je vysoce rizikov\u00fd dle P\u0159\u00edlohy III, bod 5a. Va\u0161e firma mus\u00ed zajistit posouzen\u00ed shody, registraci v EU datab\u00e1zi, pr\u016fb\u011b\u017en\u00e9 monitorov\u00e1n\u00ed a pr\u00e1vo pojistn\u00edka na vysv\u011btlen\u00ed rozhodnut\u00ed \u2014 toto jsou z\u00e1konn\u00e9 povinnosti, kter\u00e9 mus\u00edte splnit intern\u011b. V r\u00e1mci dokumentace v\u00e1m poskytneme podklady a doporu\u010den\u00ed."}'''

if old in src:
    src = src.replace(old, new)
    changes.append("12. Changed insurance_impact warning — must handle internally")
else:
    changes.append("12. FAILED — insurance_impact warning not found")

# ─────────────────────────────────────────────────────────
# 13. Replace "šablonu" / "šablona" → "profesionálně zpracovanou dokumentaci"
# ─────────────────────────────────────────────────────────

# 13a. has_ai_training → training_attendance warning
old = 'AIshield.cz v\u00e1m v r\u00e1mci slu\u017eeb dod\u00e1 kompletn\u00ed \u0161kolic\u00ed prezentaci + \u0161ablonu prezen\u010dn\u00ed listiny.'
new = 'AIshield.cz v\u00e1m v r\u00e1mci slu\u017eeb dod\u00e1 kompletn\u00ed \u0161kolic\u00ed prezentaci + profesion\u00e1ln\u011b zpracovanou prezen\u010dn\u00ed listinu.'
if old in src:
    src = src.replace(old, new)
    changes.append("13a. Fixed training_attendance: šablonu → profesionálně zpracovanou")
else:
    changes.append("13a. FAILED — training_attendance šablonu not found")

# 13b. training_info
old = '\u0161ablony prezen\u010dn\u00ed listiny'
new = 'prezen\u010dn\u00ed listiny'
if old in src:
    src = src.replace(old, new)
    changes.append("13b. Fixed training_info: šablony → removed")
else:
    changes.append("13b. FAILED — training_info šablony not found")

# 13c. training_no_warning
old = 'kompletn\u00ed \u0161kolic\u00ed prezentaci (PowerPoint) + \u0161ablona prezen\u010dn\u00ed listiny, kterou zam\u011bstnanci podep\u00ed\u0161ou. V\u0161e za\u0159\u00edd\u00edme za v\u00e1s.'
new = 'kompletn\u00ed \u0161kolic\u00ed prezentaci (PowerPoint) + profesion\u00e1ln\u011b zpracovanou prezen\u010dn\u00ed listinu, kterou zam\u011bstnanci podep\u00ed\u0161ou.'
if old in src:
    src = src.replace(old, new)
    changes.append("13c. Fixed training_no_warning: šablona + 'Vše zařídíme' removed")
else:
    changes.append("13c. FAILED — training_no_warning pattern not found")

# 13d. guidelines_no_warning
old = 'v\u00e1m dod\u00e1me kompletn\u00ed \u0161ablonu sm\u011brnice \u201ePravidla pro pou\u017e\u00edv\u00e1n\u00ed AI ve firm\u011b\u201c, kterou si snadno p\u0159izp\u016fsob\u00edte.'
new = 'v\u00e1m dod\u00e1me profesion\u00e1ln\u011b zpracovanou sm\u011brnici \u201ePravidla pro pou\u017e\u00edv\u00e1n\u00ed AI ve firm\u011b\u201c, kterou si snadno p\u0159izp\u016fsob\u00edte.'
if old in src:
    src = src.replace(old, new)
    changes.append("13d. Fixed guidelines_no_warning: šablonu → profesionálně zpracovanou")
else:
    changes.append("13d. FAILED — guidelines_no_warning šablonu not found")

# 13e. logging_internal_note
old = 'AIshield v\u00e1m poskytne \u0161ablonu logovac\u00edho protokolu'
new = 'AIshield v\u00e1m poskytne profesion\u00e1ln\u011b zpracovan\u00fd logovac\u00ed protokol'
if old in src:
    src = src.replace(old, new)
    changes.append("13e. Fixed logging_internal_note: šablonu → profesionálně zpracovaný")
else:
    changes.append("13e. FAILED — logging_internal_note šablonu not found")

# 13f. register_warning
old = 'v\u00e1m dod\u00e1me \u0161ablonu registru AI syst\u00e9m\u016f \u2014 jednoduchou tabulku, kterou si snadno vypln\u00edte.'
new = 'v\u00e1m dod\u00e1me profesion\u00e1ln\u011b zpracovan\u00fd registr AI syst\u00e9m\u016f \u2014 jednoduchou tabulku, kterou si snadno vypln\u00edte.'
if old in src:
    src = src.replace(old, new)
    changes.append("13f. Fixed register_warning: šablonu → profesionálně zpracovaný")
else:
    changes.append("13f. FAILED — register_warning šablonu not found")

# 13g. incident_warning
old = 'v\u00e1m dod\u00e1me \u0161ablonu pl\u00e1nu \u0159\u00edzen\u00ed AI incident\u016f.'
new = 'v\u00e1m dod\u00e1me profesion\u00e1ln\u011b zpracovan\u00fd pl\u00e1n \u0159\u00edzen\u00ed AI incident\u016f.'
if old in src:
    src = src.replace(old, new)
    changes.append("13g. Fixed incident_warning: šablonu → profesionálně zpracovaný")
else:
    changes.append("13g. FAILED — incident_warning šablonu not found")

# 13h. changes_internal_note
old = 'AIshield v\u00e1m dod\u00e1 \u0161ablonu pro tuto evidenci.'
new = 'AIshield v\u00e1m dod\u00e1 profesion\u00e1ln\u011b zpracovanou dokumentaci pro tuto evidenci.'
if old in src:
    src = src.replace(old, new)
    changes.append("13h. Fixed changes_internal_note: šablonu → profesionálně zpracovanou dokumentaci")
else:
    changes.append("13h. FAILED — changes_internal_note šablonu not found")

# 13i. _NO_ANSWER_RECOMMENDATIONS has_ai_training
old = '\u0161kolic\u00ed prezentaci (PowerPoint) a \u0161ablonu prezen\u010dn\u00ed listiny.'
new = '\u0161kolic\u00ed prezentaci (PowerPoint) a profesion\u00e1ln\u011b zpracovanou prezen\u010dn\u00ed listinu.'
if old in src:
    src = src.replace(old, new)
    changes.append("13i. Fixed _NO_ANSWER_RECOMMENDATIONS training: šablonu → dokumentaci")
else:
    changes.append("13i. FAILED — _NO_ANSWER_RECOMMENDATIONS training not found")

# 13j. _NO_ANSWER_RECOMMENDATIONS has_ai_guidelines (šablonu směrnice)
old = 'univerz\u00e1ln\u00ed \u0161ablonu sm\u011brnice'
new = 'profesion\u00e1ln\u011b zpracovanou sm\u011brnici'
if old in src:
    src = src.replace(old, new)
    changes.append("13j. Fixed _NO_ANSWER_RECOMMENDATIONS guidelines: šablonu → profesionálně")
else:
    changes.append("13j. FAILED — _NO_ANSWER_RECOMMENDATIONS guidelines not found")

# 13k. _NO_ANSWER_RECOMMENDATIONS has_ai_guidelines (šablona vám k tomu poslouží)
old = '\u0161ablona v\u00e1m k tomu poslou\u017e\u00ed jako z\u00e1klad'
new = 'dokumentace v\u00e1m k tomu poslou\u017e\u00ed jako z\u00e1klad'
if old in src:
    src = src.replace(old, new)
    changes.append("13k. Fixed _NO_ANSWER_RECOMMENDATIONS guidelines: šablona → dokumentace")
else:
    changes.append("13k. FAILED — šablona vám not found")

# 13l. _NO_ANSWER_RECOMMENDATIONS has_ai_register
old = '\u0161ablonu registru AI syst\u00e9m\u016f \u2014\n'
new = 'profesion\u00e1ln\u011b zpracovan\u00fd registr AI syst\u00e9m\u016f \u2014\n'
if old in src:
    src = src.replace(old, new)
    changes.append("13l. Fixed _NO_ANSWER_RECOMMENDATIONS register: šablonu → profesionálně")
else:
    # Try without newline
    old2 = '\u0161ablonu registru AI syst\u00e9m\u016f \u2014'
    new2 = 'profesion\u00e1ln\u011b zpracovan\u00fd registr AI syst\u00e9m\u016f \u2014'
    if old2 in src:
        src = src.replace(old2, new2, 1)  # Only replace 1 (the _NO_ANSWER one, the other was already changed)
        changes.append("13l. Fixed _NO_ANSWER_RECOMMENDATIONS register (alt): šablonu → profesionálně")
    else:
        changes.append("13l. FAILED — _NO_ANSWER_RECOMMENDATIONS register not found")

# ─────────────────────────────────────────────────────────
# WRITE OUTPUT
# ─────────────────────────────────────────────────────────
with open(FILE, "w", encoding="utf-8") as f:
    f.write(src)

print(f"\n{'='*60}")
print(f"PATCH RESULTS ({len(changes)} operations)")
print(f"{'='*60}")
for c in changes:
    status = "✅" if "FAILED" not in c else "❌"
    print(f"  {status} {c}")

ok = sum(1 for c in changes if "FAILED" not in c)
fail = sum(1 for c in changes if "FAILED" in c)
print(f"\n  Summary: {ok} succeeded, {fail} failed")
