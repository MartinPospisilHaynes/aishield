#!/usr/bin/env python3
"""BATCH 5: Volitelné změny.

P9.  uses_ai_for_children  → customer_service (8/10 konsenzus)
P11. uses_gpai_api          → ai_role          (7/10 konsenzus)

Plus doplnění: UNKNOWN_CHECKLISTS, _NEVIM_SEVERITY, _get_recommendation
"""
import unicodedata

FILE = "backend/api/questionnaire.py"

with open(FILE, encoding="utf-8") as f:
    content = f.read()

content = unicodedata.normalize("NFC", content)
original = content
changes = 0

# ═══════════════════════════════════════════════════════════════════
# P9: uses_ai_for_children → end of customer_service
# ═══════════════════════════════════════════════════════════════════

Q_CHILDREN = (
    '            {\n'
    '                "key": "uses_ai_for_children",\n'
    '                "text": "Pou\u017e\u00edv\u00e1te AI syst\u00e9my, kter\u00e9 p\u0159\u00edmo interaguj\u00ed s d\u011btmi nebo nezletil\u00fdmi?",\n'
    '                "type": "yes_no_unknown",\n'
    '                "help_text": "P\u0159\u00edklady ANO:\\n'
    '1) AI chatbot/tutor pro \u017e\u00e1ky z\u00e1kladn\u00edch \u0161kol.\\n'
    '2) AI doporu\u010dovac\u00ed syst\u00e9m v d\u011btsk\u00e9 mobiln\u00ed aplikaci.\\n'
    '3) AI hra nebo eduka\u010dn\u00ed platforma pro d\u011bti.\\n'
    '4) AI filtrov\u00e1n\u00ed obsahu pro nezletil\u00e9.\\n\\n'
    'P\u0159\u00edklady NE:\\n'
    '1) AI n\u00e1stroje pou\u017e\u00edvaj\u00ed pouze dosp\u011bl\u00ed zam\u011bstnanci.\\n'
    '2) E-shop c\u00edl\u00ed na dosp\u011bl\u00e9 z\u00e1kazn\u00edky.\\n'
    '3) B2B produkt bez interakce s d\u011btmi.\\n\\n'
    'Tato ot\u00e1zka je relevantn\u00ed pro vzd\u011bl\u00e1v\u00e1n\u00ed, hry, d\u011btsk\u00e9 aplikace a slu\u017eby c\u00edlen\u00e9 na nezletil\u00e9.",\n'
    '                "followup": {\n'
    '                    "condition": "yes",\n'
    '                    "fields": [\n'
    '                        {"key": "children_ai_context", "label": "V jak\u00e9m kontextu AI s d\u011btmi interaguje?", "type": "multi_select",\n'
    '                         "options": ["Vzd\u011bl\u00e1v\u00e1n\u00ed / e-learning", "Mobiln\u00ed aplikace / hry", "Doporu\u010dov\u00e1n\u00ed obsahu", "Chatbot / virtu\u00e1ln\u00ed asistent", "Filtrov\u00e1n\u00ed / moderov\u00e1n\u00ed obsahu", "Jin\u00e9"]},\n'
    '                        {"key": "children_ai_warning", "label": "\u26a0\ufe0f AI syst\u00e9my interaguj\u00edc\u00ed s d\u011btmi jsou dle P\u0159\u00edlohy III AI Act pova\u017eov\u00e1ny za vysoce rizikov\u00e9. Mus\u00edte zajistit posouzen\u00ed shody, technickou dokumentaci a zv\u00fd\u0161enou ochranu. \u010cl. 5 zakazuje AI manipulaci zraniteln\u00fdch skupin, kam d\u011bti pat\u0159\u00ed. **AIshield v\u00e1m pom\u016f\u017ee s compliance dokumentac\u00ed pro AI c\u00edlen\u00e9 na d\u011bti.**", "type": "info"},\n'
    '                    ]\n'
    '                },\n'
    '                "risk_hint": "high",\n'
    '                "ai_act_article": "P\u0159\u00edloha III bod 3 \u2014 vzd\u011bl\u00e1v\u00e1n\u00ed + \u010dl. 5 odst. 1 p\u00edsm. a,b) \u2014 ochrana zraniteln\u00fdch skupin",\n'
    '            },'
)

# Anchor: "pricing_disclosed" is unique to uses_dynamic_pricing (last question in customer_service)
anchor_pos = content.find('"pricing_disclosed"')
if anchor_pos == -1:
    print("\u274c P9: Anchor 'pricing_disclosed' not found")
else:
    target = "            },\n        ],"
    close_pos = content.find(target, anchor_pos)
    if close_pos == -1:
        print("\u274c P9: Close pattern not found")
    else:
        insert_at = close_pos + len("            },")
        content = content[:insert_at] + "\n" + Q_CHILDREN + content[insert_at:]
        changes += 1
        print("\u2705 P9: uses_ai_for_children \u2192 customer_service")


# ═══════════════════════════════════════════════════════════════════
# P11: uses_gpai_api → end of ai_role
# ═══════════════════════════════════════════════════════════════════

Q_GPAI = (
    '            {\n'
    '                "key": "uses_gpai_api",\n'
    '                "text": "Integrujete API velk\u00fdch jazykov\u00fdch model\u016f (LLM) do vlastn\u00edch produkt\u016f nebo slu\u017eeb?",\n'
    '                "type": "yes_no_unknown",\n'
    '                "help_text": "P\u0159\u00edklady ANO:\\n'
    '1) Vol\u00e1te ChatGPT/Claude/Gemini API z va\u0161\u00ed aplikace pro z\u00e1kazn\u00edky.\\n'
    '2) Chatbot na va\u0161em webu je poh\u00e1n\u011bn LLM p\u0159es API.\\n'
    '3) V\u00e1\u0161 SaaS produkt generuje texty/anal\u00fdzy pomoc\u00ed LLM.\\n\\n'
    'P\u0159\u00edklady NE:\\n'
    '1) Zam\u011bstnanci ru\u010dn\u011b pou\u017e\u00edvaj\u00ed ChatGPT (to pat\u0159\u00ed do sekce intern\u00ed AI).\\n'
    '2) Pouze testujete API intern\u011b.\\n'
    '3) Nepou\u017e\u00edv\u00e1te \u017e\u00e1dn\u00e9 LLM API.",\n'
    '                "followup": {\n'
    '                    "condition": "yes",\n'
    '                    "fields": [\n'
    '                        {"key": "gpai_provider", "label": "Kter\u00e9 API pou\u017e\u00edv\u00e1te?", "type": "multi_select",\n'
    '                         "options": ["OpenAI (GPT-4/4o)", "Anthropic (Claude)", "Google (Gemini)", "Meta (Llama)", "Mistral", "Vlastn\u00ed model", "Jin\u00e9"]},\n'
    '                        {"key": "gpai_customer_facing", "label": "Jsou v\u00fdstupy LLM viditeln\u00e9 p\u0159\u00edmo z\u00e1kazn\u00edk\u016fm?", "type": "select",\n'
    '                         "options": ["Ano, z\u00e1kazn\u00edci vid\u00ed AI v\u00fdstupy p\u0159\u00edmo", "\u010c\u00e1ste\u010dn\u011b \u2014 AI navrhuje, \u010dlov\u011bk kontroluje", "Ne \u2014 pouze intern\u00ed pou\u017eit\u00ed"],\n'
    '                         "warning": {"Ano, z\u00e1kazn\u00edci vid\u00ed AI v\u00fdstupy p\u0159\u00edmo": "\u26a0\ufe0f Od 2. srpna 2025 plat\u00ed pravidla pro GPAI (\u010dl. 51-54 AI Act). Jako deployer integruj\u00edc\u00ed LLM do z\u00e1kaznick\u00e9ho produktu m\u00e1te povinnost transparentnosti \u2014 z\u00e1kazn\u00edci mus\u00ed v\u011bd\u011bt, \u017ee interaguj\u00ed s AI (\u010dl. 50). **AIshield v\u00e1m pom\u016f\u017ee s GPAI compliance.**"}},\n'
    '                    ]\n'
    '                },\n'
    '                "risk_hint": "limited",\n'
    '                "ai_act_article": "\u010dl. 51-54 \u2014 GPAI povinnosti, \u010dl. 50 \u2014 transparentnost",\n'
    '            },'
)

# Anchor: "modified_ai_warning" is unique to modifies_ai_purpose (only question in ai_role now)
anchor_pos = content.find('"modified_ai_warning"')
if anchor_pos == -1:
    print("\u274c P11: Anchor 'modified_ai_warning' not found")
else:
    target = "            },\n        ],"
    close_pos = content.find(target, anchor_pos)
    if close_pos == -1:
        print("\u274c P11: Close pattern not found")
    else:
        insert_at = close_pos + len("            },")
        content = content[:insert_at] + "\n" + Q_GPAI + content[insert_at:]
        changes += 1
        print("\u2705 P11: uses_gpai_api \u2192 ai_role")


# ═══════════════════════════════════════════════════════════════════
# PART B: UNKNOWN_CHECKLISTS
# ═══════════════════════════════════════════════════════════════════

NEW_CHECKLISTS = (
    "\n    # D\u011bti / GPAI\n"
    "    'uses_ai_for_children': [\n"
    "        'Koho se zeptat: produktov\u00fd mana\u017eer, v\u00fdvoj\u00e1\u0159i, marketing.',\n"
    "        'P\u0159\u00edklad: Mobiln\u00ed aplikace s AI chatbotem, kterou pou\u017e\u00edvaj\u00ed d\u011bti \u2014 nap\u0159. eduka\u010dn\u00ed hra nebo online v\u00fdukov\u00e1 platforma.',\n"
    "        'Zkontrolujte, zda va\u0161e AI produkty/slu\u017eby c\u00edl\u00ed na osoby mlad\u0161\u00ed 18 let.',\n"
    "        'Ov\u011b\u0159te, zda sbir\u00e1te data d\u011bt\u00ed nebo AI interaguje s d\u011btmi p\u0159\u00edmo.',\n"
    "    ],\n"
    "    'uses_gpai_api': [\n"
    "        'Koho se zeptat: CTO, v\u00fdvoj\u00e1\u0159i, produktov\u00fd t\u00fdm.',\n"
    "        'P\u0159\u00edklad: Firma vol\u00e1 OpenAI API ze sv\u00e9 aplikace a v\u00fdstupy zobrazuje z\u00e1kazn\u00edk\u016fm.',\n"
    "        'Zkontrolujte zdrojov\u00fd k\u00f3d a faktury \u2014 platite za API kl\u00ed\u010de k LLM slu\u017eb\u00e1m?',\n"
    "        'Ov\u011b\u0159te, zda v\u00fdstupy LLM vid\u00ed kone\u010dn\u00ed u\u017eivatel\u00e9 va\u0161eho produktu.',\n"
    "    ],"
)

# Insert after has_ai_bias_check (last key we added in BATCH 3)
uc_start = content.find("UNKNOWN_CHECKLISTS")
if uc_start == -1:
    print("\u274c UNKNOWN_CHECKLISTS not found")
else:
    bias_key = content.find("'has_ai_bias_check'", uc_start)
    if bias_key == -1:
        print("\u274c 'has_ai_bias_check' not found in UNKNOWN_CHECKLISTS")
    else:
        close_pat = "    ],\n}"
        close_pos = content.find(close_pat, bias_key)
        if close_pos == -1:
            print("\u274c UNKNOWN_CHECKLISTS close not found")
        else:
            insert_at = close_pos + len("    ],")
            content = content[:insert_at] + NEW_CHECKLISTS + content[insert_at:]
            changes += 1
            print("\u2705 UNKNOWN_CHECKLISTS: 2 nov\u00e9 kl\u00ed\u010de")


# ═══════════════════════════════════════════════════════════════════
# PART C: _NEVIM_SEVERITY
# ═══════════════════════════════════════════════════════════════════

NEW_SEVERITY = (
    "\n    # D\u011bti / GPAI\n"
    "    'uses_ai_for_children':         {'severity': 'high',     'color': 'orange', 'label': 'Vysok\u00e9 riziko'},\n"
    "    'uses_gpai_api':                {'severity': 'limited',  'color': 'yellow', 'label': 'Omezen\u00e9 riziko'},"
)

ns_start = content.find("_NEVIM_SEVERITY")
if ns_start == -1:
    print("\u274c _NEVIM_SEVERITY not found")
else:
    bias_sev = content.find("'has_ai_bias_check'", ns_start)
    if bias_sev == -1:
        print("\u274c 'has_ai_bias_check' not found in _NEVIM_SEVERITY")
    else:
        close_pos = content.find("\n}", bias_sev)
        if close_pos == -1:
            print("\u274c _NEVIM_SEVERITY close not found")
        else:
            content = content[:close_pos] + NEW_SEVERITY + content[close_pos:]
            changes += 1
            print("\u2705 _NEVIM_SEVERITY: 2 nov\u00e9 kl\u00ed\u010de")


# ═══════════════════════════════════════════════════════════════════
# PART D: _get_recommendation
# ═══════════════════════════════════════════════════════════════════

NEW_RECS = (
    '\n        # D\u011bti / GPAI\n'
    '        "uses_ai_for_children": "AI interaguj\u00edc\u00ed s d\u011btmi je vysoce rizikov\u00e9 dle P\u0159\u00edlohy III AI Act. Prove\u010fte posouzen\u00ed shody a zajist\u011bte zv\u00fd\u0161enou ochranu nezletil\u00fdch.",\n'
    '        "uses_gpai_api": "Integrujete LLM API do z\u00e1kaznick\u00fdch produkt\u016f \u2014 od srpna 2025 plat\u00ed GPAI pravidla (\u010dl. 51-54). Zajist\u011bte transparentnost a dokumentaci.",'
)

rec_start = content.find("_get_recommendation")
if rec_start == -1:
    print("\u274c _get_recommendation not found")
else:
    bias_rec = content.find('"has_ai_bias_check"', rec_start)
    if bias_rec == -1:
        print("\u274c 'has_ai_bias_check' not found in _get_recommendation")
    else:
        close_pos = content.find("\n    }", bias_rec)
        if close_pos == -1:
            print("\u274c _get_recommendation close not found")
        else:
            content = content[:close_pos] + NEW_RECS + content[close_pos:]
            changes += 1
            print("\u2705 _get_recommendation: 2 nov\u00e9 kl\u00ed\u010de")


# ═══════════════════════════════════════════════════════════════════
# ZÁPIS
# ═══════════════════════════════════════════════════════════════════

if changes > 0:
    with open(FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n\u2705 BATCH 5 HOTOV \u2014 {changes}/6 zm\u011bn provedeno, soubor ulo\u017een")
else:
    print("\n\u274c \u017d\u00e1dn\u00e9 zm\u011bny nebyly provedeny!")
