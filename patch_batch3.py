#!/usr/bin/env python3
"""BATCH 3: Přidání 3 nových otázek dle konsenzu 10 AI.

Nové otázky:
  P5. has_ai_register        → human_oversight   (10/10 AI konsenzus)
  P6. has_ai_vendor_contracts → data_protection   (10/10 AI konsenzus)
  P7. has_ai_bias_check       → incident_management (9/10 AI konsenzus)

Plus doplnění: UNKNOWN_CHECKLISTS, _NEVIM_SEVERITY, _NO_ANSWER_RECOMMENDATIONS, _get_recommendation
"""
import unicodedata

FILE = "backend/api/questionnaire.py"

with open(FILE, encoding="utf-8") as f:
    content = f.read()

content = unicodedata.normalize("NFC", content)
original = content
changes = 0

# ═══════════════════════════════════════════════════════════════════
# PART A: VLOŽENÍ NOVÝCH OTÁZEK DO SEKCÍ
# ═══════════════════════════════════════════════════════════════════

# ─── P5: has_ai_register → end of human_oversight ─────────────────

Q_REGISTER = (
    '            {\n'
    '                "key": "has_ai_register",\n'
    '                "text": "Vedete intern\u00ed registr/seznam v\u0161ech AI syst\u00e9m\u016f, kter\u00e9 pou\u017e\u00edv\u00e1te?",\n'
    '                "type": "yes_no_unknown",\n'
    '                "help_text": "P\u0159\u00edklady:\\n'
    '1) Tabulka se seznamem AI n\u00e1stroj\u016f, jejich dodavatel\u016f a \u00fa\u010del\u016f.\\n'
    '2) Intern\u00ed datab\u00e1ze AI syst\u00e9m\u016f s kategorizac\u00ed rizik.\\n'
    '3) IT invent\u00e1\u0159, kter\u00fd zahrnuje i AI slu\u017eby.\\n\\n'
    'Registr AI syst\u00e9m\u016f je z\u00e1kladem pro compliance \u2014 bez n\u011bj nev\u00edte, jak\u00e9 povinnosti m\u00e1te.",\n'
    '                "followup": {\n'
    '                    "condition": "yes",\n'
    '                    "fields": [\n'
    '                        {"key": "register_contents", "label": "Co v\u00e1\u0161 registr obsahuje? (vyberte v\u0161e)", "type": "multi_select",\n'
    '                         "options": ["N\u00e1zev AI syst\u00e9mu", "Dodavatel / poskytovatel", "\u00da\u010del pou\u017eit\u00ed", "Kategorie rizika dle AI Act", "Odpov\u011bdn\u00e1 osoba", "Datum nasazen\u00ed", "Typ zpracov\u00e1van\u00fdch dat"]},\n'
    '                        {"key": "register_ok_info", "label": "\u2705 V\u00fdborn\u011b! Registr AI syst\u00e9m\u016f je z\u00e1klad compliance dle \u010dl. 26 AI Act. Do dokumentace zaznamen\u00e1me strukturu va\u0161eho registru a p\u0159\u00edpadn\u011b doporu\u010d\u00edme roz\u0161\u00ed\u0159en\u00ed.", "type": "info"},\n'
    '                    ]\n'
    '                },\n'
    '                "followup_no": {\n'
    '                    "fields": [\n'
    '                        {"key": "register_warning", "label": "\u26a0\ufe0f \u010cl\u00e1nek 26 AI Act vy\u017eaduje, aby zav\u00e1d\u011bj\u00edc\u00ed (deployers) m\u011bli p\u0159ehled o v\u0161ech AI syst\u00e9mech, kter\u00e9 pou\u017e\u00edvaj\u00ed. Bez registru nem\u016f\u017eete prok\u00e1zat soulad s na\u0159\u00edzen\u00edm. **V r\u00e1mci slu\u017eby AIshield v\u00e1m dod\u00e1me \u0161ablonu registru AI syst\u00e9m\u016f \u2014 jednoduchou tabulku, kterou si snadno vypln\u00edte.**", "type": "info"},\n'
    '                    ]\n'
    '                },\n'
    '                "risk_hint": "limited",\n'
    '                "ai_act_article": "\u010dl. 26 \u2014 povinnosti zav\u00e1d\u011bj\u00edc\u00edho (deployer)",\n'
    '            },'
)

anchor_pos = content.find('"logging_internal_note"')
if anchor_pos == -1:
    print("\u274c P5: Anchor 'logging_internal_note' not found")
else:
    target = "            },\n        ],"
    close_pos = content.find(target, anchor_pos)
    if close_pos == -1:
        print("\u274c P5: Close pattern not found")
    else:
        insert_at = close_pos + len("            },")
        content = content[:insert_at] + "\n" + Q_REGISTER + content[insert_at:]
        changes += 1
        print("\u2705 P5: has_ai_register \u2192 human_oversight")


# ─── P6: has_ai_vendor_contracts → end of data_protection ─────────

Q_VENDOR = (
    '            {\n'
    '                "key": "has_ai_vendor_contracts",\n'
    '                "text": "M\u00e1te s dodavateli AI syst\u00e9m\u016f uzav\u0159eny smlouvy pokr\u00fdvaj\u00edc\u00ed zpracov\u00e1n\u00ed dat a odpov\u011bdnost?",\n'
    '                "type": "yes_no_unknown",\n'
    '                "help_text": "P\u0159\u00edklady ANO:\\n'
    '1) S OpenAI m\u00e1te podepsanou DPA (Data Processing Agreement).\\n'
    '2) S dodavatelem chatbotu m\u00e1te SLA s definovanou dostupnost\u00ed.\\n'
    '3) Ve smlouv\u011b je jasn\u011b uvedeno, kdo odpov\u00edd\u00e1 za chyby AI.\\n\\n'
    'P\u0159\u00edklady NE:\\n'
    '1) Pou\u017e\u00edv\u00e1te ChatGPT p\u0159es free/personal \u00fa\u010det bez firemn\u00ed smlouvy.\\n'
    '2) AI n\u00e1stroj jste si jen st\u00e1hli a nainstalovali bez jak\u00e9koliv smlouvy.\\n'
    '3) S dodavatelem AI nem\u00e1te \u0159e\u0161enou odpov\u011bdnost za \u0161kody.",\n'
    '                "followup": {\n'
    '                    "condition": "yes",\n'
    '                    "fields": [\n'
    '                        {"key": "vendor_contract_scope", "label": "Co va\u0161e smlouvy pokr\u00fdvaj\u00ed? (vyberte v\u0161e)", "type": "multi_select",\n'
    '                         "options": ["DPA (zpracov\u00e1n\u00ed osobn\u00edch \u00fadaj\u016f)", "SLA (dostupnost a kvalita slu\u017eby)", "Odpov\u011bdnost za \u0161kody zp\u016fsoben\u00e9 AI", "Pr\u00e1va k dat\u016fm a v\u00fdstup\u016fm", "Podm\u00ednky ukon\u010den\u00ed spolupr\u00e1ce", "Audit / kontrola dodavatele"]},\n'
    '                        {"key": "vendor_contract_ok_info", "label": "\u2705 V\u00fdborn\u011b! Smluvn\u00ed pokryt\u00ed s dodavateli AI je d\u016fle\u017eit\u00e9 pro GDPR i AI Act compliance. Do dokumentace zaznamen\u00e1me rozsah va\u0161ich smluv.", "type": "info"},\n'
    '                    ]\n'
    '                },\n'
    '                "followup_no": {\n'
    '                    "fields": [\n'
    '                        {"key": "vendor_contract_warning", "label": "\u26a0\ufe0f Bez smlouvy s dodavatelem AI syst\u00e9mu riskujete poru\u0161en\u00ed GDPR \u010dl. 28 (zpracovatel bez smlouvy) a nem\u00e1te pr\u00e1vn\u011b o\u0161et\u0159enou odpov\u011bdnost za chyby AI. Doporu\u010dujeme uzav\u0159\u00edt alespo\u0148 DPA s ka\u017ed\u00fdm poskytovatelem AI, kter\u00e9mu p\u0159ed\u00e1v\u00e1te firemn\u00ed nebo osobn\u00ed data. **AIshield v\u00e1m dod\u00e1 kontroln\u00ed seznam bod\u016f, kter\u00e9 by smlouva s AI dodavatelem m\u011bla obsahovat.**", "type": "info"},\n'
    '                    ]\n'
    '                },\n'
    '                "risk_hint": "limited",\n'
    '                "ai_act_article": "GDPR \u010dl. 28 \u2014 zpracovatel, AI Act \u010dl. 25-26 \u2014 povinnosti v hodnotov\u00e9m \u0159et\u011bzci",\n'
    '            },'
)

anchor_pos = content.find('"data_outside_eu_tool"')
if anchor_pos == -1:
    print("\u274c P6: Anchor 'data_outside_eu_tool' not found")
else:
    target = "            },\n        ],"
    close_pos = content.find(target, anchor_pos)
    if close_pos == -1:
        print("\u274c P6: Close pattern not found")
    else:
        insert_at = close_pos + len("            },")
        content = content[:insert_at] + "\n" + Q_VENDOR + content[insert_at:]
        changes += 1
        print("\u2705 P6: has_ai_vendor_contracts \u2192 data_protection")


# ─── P7: has_ai_bias_check → end of incident_management ──────────

Q_BIAS = (
    '            {\n'
    '                "key": "has_ai_bias_check",\n'
    '                "text": "Testujete sv\u00e9 AI syst\u00e9my na diskriminaci nebo zaujatost (bias)?",\n'
    '                "type": "yes_no_unknown",\n'
    '                "help_text": "P\u0159\u00edklady ANO:\\n'
    '1) Kontrolujete, zda AI n\u00e1bor nezv\u00fdhod\u0148uje/neznev\u00fdhod\u0148uje kandid\u00e1ty podle pohlav\u00ed nebo v\u011bku.\\n'
    '2) Testujete, zda chatbot odpov\u00edd\u00e1 stejn\u011b kvalitn\u011b \u010desky i anglicky.\\n'
    '3) Analyzujete, zda AI scoring nediskriminuje ur\u010dit\u00e9 skupiny z\u00e1kazn\u00edk\u016f.\\n\\n'
    'P\u0159\u00edklady NE:\\n'
    '1) AI b\u011b\u017e\u00ed bez jak\u00e9koliv kontroly f\u00e9rovosti.\\n'
    '2) Nikdy jste netestovali, zda AI v\u00fdstupy nejsou zaujat\u00e9.\\n\\n'
    'Tato ot\u00e1zka je relevantn\u00ed zejm\u00e9na pro firmy s vysoce rizikov\u00fdmi AI syst\u00e9my (HR, finance, p\u0159\u00edstup ke slu\u017eb\u00e1m).",\n'
    '                "followup": {\n'
    '                    "condition": "yes",\n'
    '                    "fields": [\n'
    '                        {"key": "bias_check_method", "label": "Jak testujete? (vyberte v\u0161e)", "type": "multi_select",\n'
    '                         "options": ["Manu\u00e1ln\u00ed kontrola v\u00fdstup\u016f na vzorku dat", "Automatizovan\u00e9 testy f\u00e9rovosti", "Porovn\u00e1n\u00ed v\u00fdstup\u016f pro r\u016fzn\u00e9 skupiny (pohlav\u00ed, v\u011bk, etnicita)", "Zp\u011btn\u00e1 vazba od u\u017eivatel\u016f / z\u00e1kazn\u00edk\u016f", "Extern\u00ed audit"]},\n'
    '                        {"key": "bias_check_ok_info", "label": "\u2705 V\u00fdborn\u011b! Testov\u00e1n\u00ed f\u00e9rovosti AI je po\u017eadavek \u010dl. 9\u201310 AI Act. Do dokumentace zaznamen\u00e1me v\u00e1\u0161 p\u0159\u00edstup k testov\u00e1n\u00ed biasu.", "type": "info"},\n'
    '                    ]\n'
    '                },\n'
    '                "followup_no": {\n'
    '                    "fields": [\n'
    '                        {"key": "bias_check_warning", "label": "\u26a0\ufe0f \u010cl\u00e1nky 9 a 10 AI Act vy\u017eaduj\u00ed, aby vysoce rizikov\u00e9 AI syst\u00e9my byly testov\u00e1ny na bias a diskriminaci. I u syst\u00e9m\u016f s ni\u017e\u0161\u00edm rizikem je testov\u00e1n\u00ed f\u00e9rovosti dobr\u00e1 praxe. **AIshield v\u00e1m dod\u00e1 kontroln\u00ed seznam pro z\u00e1kladn\u00ed testov\u00e1n\u00ed f\u00e9rovosti AI v\u00fdstup\u016f \u2014 jednoduchou metodiku, kterou zvl\u00e1dnete i bez datov\u00e9ho analytika.**", "type": "info"},\n'
    '                    ]\n'
    '                },\n'
    '                "risk_hint": "limited",\n'
    '                "ai_act_article": "\u010dl. 9 \u2014 syst\u00e9m \u0159\u00edzen\u00ed rizik, \u010dl. 10 \u2014 spr\u00e1va dat a tr\u00e9ninkov\u00fdch dat",\n'
    '            },'
)

anchor_pos = content.find('"changes_internal_note"')
if anchor_pos == -1:
    print("\u274c P7: Anchor 'changes_internal_note' not found")
else:
    target = "            },\n        ],"
    close_pos = content.find(target, anchor_pos)
    if close_pos == -1:
        print("\u274c P7: Close pattern not found")
    else:
        insert_at = close_pos + len("            },")
        content = content[:insert_at] + "\n" + Q_BIAS + content[insert_at:]
        changes += 1
        print("\u2705 P7: has_ai_bias_check \u2192 incident_management")


# ═══════════════════════════════════════════════════════════════════
# PART B: UNKNOWN_CHECKLISTS — přidání 3 nových klíčů
# ═══════════════════════════════════════════════════════════════════

NEW_CHECKLISTS = (
    "\n    # Governance\n"
    "    'has_ai_register': [\n"
    "        'Koho se zeptat: IT odd\u011blen\u00ed, compliance officer, veden\u00ed firmy.',\n"
    "        'P\u0159\u00edklad: Firma pou\u017e\u00edv\u00e1 ChatGPT, Copilot a AI chatbot na webu, ale nikde nem\u00e1 centr\u00e1ln\u00ed seznam t\u011bchto n\u00e1stroj\u016f.',\n"
    "        'Zjist\u011bte, zda existuje jak\u00fdkoliv p\u0159ehled AI n\u00e1stroj\u016f \u2014 i neform\u00e1ln\u00ed seznam v Excelu se po\u010d\u00edt\u00e1.',\n"
    "        'Zkontrolujte IT invent\u00e1\u0159 \u2014 zahrnuje i cloudov\u00e9 AI slu\u017eby?',\n"
    "    ],\n"
    "    'has_ai_vendor_contracts': [\n"
    "        'Koho se zeptat: pr\u00e1vn\u00ed odd\u011blen\u00ed, IT odd\u011blen\u00ed, n\u00e1kup.',\n"
    "        'P\u0159\u00edklad: Firma plat\u00ed za ChatGPT Plus, ale nem\u00e1 s OpenAI \u017e\u00e1dnou firemn\u00ed smlouvu ani DPA.',\n"
    "        'Zkontrolujte faktury za AI slu\u017eby \u2014 m\u00e1te k nim odpov\u00eddaj\u00edc\u00ed smlouvy?',\n"
    "        'Ov\u011b\u0159te, zda smlouvy pokr\u00fdvaj\u00ed zpracov\u00e1n\u00ed dat, odpov\u011bdnost za chyby AI a podm\u00ednky ukon\u010den\u00ed.',\n"
    "    ],\n"
    "    'has_ai_bias_check': [\n"
    "        'Koho se zeptat: CTO, v\u00fdvoj\u00e1\u0159i, HR odd\u011blen\u00ed (pro AI v n\u00e1boru), compliance officer.',\n"
    "        'P\u0159\u00edklad: AI n\u00e1stroj pro n\u00e1bor automaticky vy\u0159azuje kandid\u00e1ty, ale nikdo netestoval, zda nediskriminuje podle pohlav\u00ed nebo v\u011bku.',\n"
    "        'Zkontrolujte, zda AI rozhodnut\u00ed nezv\u00fdhod\u0148uj\u00ed/neznev\u00fdhod\u0148uj\u00ed ur\u010dit\u00e9 skupiny z\u00e1kazn\u00edk\u016f nebo zam\u011bstnanc\u016f.',\n"
    "        'Ov\u011b\u0159te, zda m\u00e1te zp\u011btnou vazbu od u\u017eivatel\u016f AI syst\u00e9m\u016f.',\n"
    "    ],"
)

# Find UNKNOWN_CHECKLISTS dict, then 'develops_own_ai' (last existing key), then close
uc_start = content.find("UNKNOWN_CHECKLISTS")
if uc_start == -1:
    print("\u274c UNKNOWN_CHECKLISTS not found")
else:
    dev_ai = content.find("'develops_own_ai'", uc_start)
    if dev_ai == -1:
        print("\u274c 'develops_own_ai' not found in UNKNOWN_CHECKLISTS")
    else:
        # Find "    ],\n}" — closing develops_own_ai list + dict
        close_pat = "    ],\n}"
        close_pos = content.find(close_pat, dev_ai)
        if close_pos == -1:
            print("\u274c UNKNOWN_CHECKLISTS close not found")
        else:
            insert_at = close_pos + len("    ],")
            content = content[:insert_at] + NEW_CHECKLISTS + content[insert_at:]
            changes += 1
            print("\u2705 UNKNOWN_CHECKLISTS: 3 nov\u00e9 kl\u00ed\u010de p\u0159id\u00e1ny")


# ═══════════════════════════════════════════════════════════════════
# PART C: _NEVIM_SEVERITY — přidání 3 nových klíčů
# ═══════════════════════════════════════════════════════════════════

NEW_SEVERITY = (
    "\n    # Governance\n"
    "    'has_ai_register':              {'severity': 'limited',  'color': 'yellow', 'label': 'Omezen\u00e9 riziko'},\n"
    "    'has_ai_vendor_contracts':      {'severity': 'limited',  'color': 'yellow', 'label': 'Omezen\u00e9 riziko'},\n"
    "    'has_ai_bias_check':            {'severity': 'limited',  'color': 'yellow', 'label': 'Omezen\u00e9 riziko'},"
)

# Find _NEVIM_SEVERITY, then 'uses_copilot' (last existing key), then closing }
ns_start = content.find("_NEVIM_SEVERITY")
if ns_start == -1:
    print("\u274c _NEVIM_SEVERITY not found")
else:
    copilot = content.find("'uses_copilot'", ns_start)
    if copilot == -1:
        print("\u274c 'uses_copilot' not found in _NEVIM_SEVERITY")
    else:
        # Find "\n}" after uses_copilot line — closing the dict
        close_pos = content.find("\n}", copilot)
        if close_pos == -1:
            print("\u274c _NEVIM_SEVERITY close not found")
        else:
            # Insert before "\n}"
            content = content[:close_pos] + NEW_SEVERITY + content[close_pos:]
            changes += 1
            print("\u2705 _NEVIM_SEVERITY: 3 nov\u00e9 kl\u00ed\u010de p\u0159id\u00e1ny")


# ═══════════════════════════════════════════════════════════════════
# PART D: _NO_ANSWER_RECOMMENDATIONS — přidání 3 nových klíčů
# ═══════════════════════════════════════════════════════════════════

NEW_NO_ANSWER = (
    "\n    'has_ai_register': {\n"
    "        'risk_level': 'limited',\n"
    "        'priority': 'vysok\u00e1',\n"
    "        'recommendation': (\n"
    "            'Nem\u00e1te intern\u00ed registr AI syst\u00e9m\u016f. '\n"
    "            '\u010cl\u00e1nek 26 AI Act vy\u017eaduje, aby zav\u00e1d\u011bj\u00edc\u00ed m\u011bli p\u0159ehled '\n"
    "            'o v\u0161ech AI syst\u00e9mech, kter\u00e9 pou\u017e\u00edvaj\u00ed. '\n"
    "            'Bez registru nem\u016f\u017eete prok\u00e1zat soulad s na\u0159\u00edzen\u00edm. '\n"
    "            'AIshield v\u00e1m dod\u00e1 \u0161ablonu registru AI syst\u00e9m\u016f \u2014 '\n"
    "            'jednoduchou tabulku, kterou si snadno vypln\u00edte.'\n"
    "        ),\n"
    "    },\n"
    "    'has_ai_vendor_contracts': {\n"
    "        'risk_level': 'limited',\n"
    "        'priority': 'st\u0159edn\u00ed',\n"
    "        'recommendation': (\n"
    "            'Nem\u00e1te smlouvy s dodavateli AI syst\u00e9m\u016f. '\n"
    "            'GDPR \u010dl. 28 vy\u017eaduje smlouvu se zpracovatelem osobn\u00edch \u00fadaj\u016f '\n"
    "            'a AI Act \u010dl. 25-26 definuje povinnosti v hodnotov\u00e9m \u0159et\u011bzci. '\n"
    "            'Bez DPA riskujete pokutu za poru\u0161en\u00ed GDPR. '\n"
    "            'AIshield v\u00e1m dod\u00e1 kontroln\u00ed seznam bod\u016f, '\n"
    "            'kter\u00e9 by smlouva s AI dodavatelem m\u011bla obsahovat.'\n"
    "        ),\n"
    "    },\n"
    "    'has_ai_bias_check': {\n"
    "        'risk_level': 'limited',\n"
    "        'priority': 'st\u0159edn\u00ed',\n"
    "        'recommendation': (\n"
    "            'Netestujete AI syst\u00e9my na diskriminaci nebo bias. '\n"
    "            '\u010cl\u00e1nky 9 a 10 AI Act vy\u017eaduj\u00ed testov\u00e1n\u00ed f\u00e9rovosti '\n"
    "            'zejm\u00e9na u vysoce rizikov\u00fdch AI syst\u00e9m\u016f (HR, finance, p\u0159\u00edstup ke slu\u017eb\u00e1m). '\n"
    "            'I u syst\u00e9m\u016f s ni\u017e\u0161\u00edm rizikem je testov\u00e1n\u00ed f\u00e9rovosti dobr\u00e1 praxe. '\n"
    "            'AIshield v\u00e1m dod\u00e1 jednoduchou metodiku pro z\u00e1kladn\u00ed testov\u00e1n\u00ed biasu.'\n"
    "        ),\n"
    "    },"
)

# Find _NO_ANSWER_RECOMMENDATIONS, then 'ai_data_stored_eu' (last key), then closing }
na_start = content.find("_NO_ANSWER_RECOMMENDATIONS")
if na_start == -1:
    print("\u274c _NO_ANSWER_RECOMMENDATIONS not found")
else:
    data_eu = content.find("'ai_data_stored_eu'", na_start)
    if data_eu == -1:
        print("\u274c 'ai_data_stored_eu' not found in _NO_ANSWER_RECOMMENDATIONS")
    else:
        # Find "    },\n}" — closing ai_data_stored_eu entry + dict
        close_pat = "    },\n}"
        close_pos = content.find(close_pat, data_eu)
        if close_pos == -1:
            print("\u274c _NO_ANSWER_RECOMMENDATIONS close not found")
        else:
            insert_at = close_pos + len("    },")
            content = content[:insert_at] + NEW_NO_ANSWER + content[insert_at:]
            changes += 1
            print("\u2705 _NO_ANSWER_RECOMMENDATIONS: 3 nov\u00e9 kl\u00ed\u010de p\u0159id\u00e1ny")


# ═══════════════════════════════════════════════════════════════════
# PART E: _get_recommendation — přidání 3 nových klíčů do recs dict
# ═══════════════════════════════════════════════════════════════════

NEW_RECS = (
    '\n        # Governance\n'
    '        "has_ai_register": "Vytvo\u0159te intern\u00ed registr v\u0161ech AI syst\u00e9m\u016f \u2014 \u010dl. 26 AI Act vy\u017eaduje p\u0159ehled o nasazen\u00fdch AI syst\u00e9mech.",\n'
    '        "has_ai_vendor_contracts": "Uzav\u0159ete smlouvy (DPA, SLA) s dodavateli AI syst\u00e9m\u016f \u2014 GDPR \u010dl. 28 vy\u017eaduje smlouvu se zpracovatelem dat.",\n'
    '        "has_ai_bias_check": "Testujte AI syst\u00e9my na f\u00e9rovost a diskriminaci \u2014 \u010dl. 9-10 AI Act vy\u017eaduj\u00ed \u0159\u00edzen\u00ed rizik v\u010detn\u011b biasu.",'
)

# Find _get_recommendation function, then "has_ai_guidelines" (last key in recs), then closing }
rec_start = content.find("_get_recommendation")
if rec_start == -1:
    print("\u274c _get_recommendation not found")
else:
    guidelines = content.find('"has_ai_guidelines"', rec_start)
    if guidelines == -1:
        print("\u274c 'has_ai_guidelines' not found in _get_recommendation")
    else:
        # Find "\n    }" after has_ai_guidelines — closing the recs dict
        close_pos = content.find("\n    }", guidelines)
        if close_pos == -1:
            print("\u274c _get_recommendation recs close not found")
        else:
            content = content[:close_pos] + NEW_RECS + content[close_pos:]
            changes += 1
            print("\u2705 _get_recommendation: 3 nov\u00e9 kl\u00ed\u010de p\u0159id\u00e1ny")


# ═══════════════════════════════════════════════════════════════════
# ZÁPIS
# ═══════════════════════════════════════════════════════════════════

if changes > 0:
    with open(FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n\u2705 BATCH 3 HOTOV \u2014 {changes}/7 zm\u011bn provedeno, soubor ulo\u017een")
else:
    print("\n\u274c \u017d\u00e1dn\u00e9 zm\u011bny nebyly provedeny!")
