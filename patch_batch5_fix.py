#!/usr/bin/env python3
"""BATCH 5 FIX: Oprava UNKNOWN_CHECKLISTS a _NEVIM_SEVERITY.

1. Odstranit severity dict záznamy omylem vložené do UNKNOWN_CHECKLISTS
2. Přidat checklist záznamy pro uses_ai_for_children a uses_gpai_api
3. Přidat severity záznamy do _NEVIM_SEVERITY pro všech 5 nových klíčů
"""
import unicodedata

FILE = "backend/api/questionnaire.py"

with open(FILE, encoding="utf-8") as f:
    content = f.read()

content = unicodedata.normalize("NFC", content)
changes = 0

# ═══════════════════════════════════════════════════════════════════
# FIX 1: Odstranit severity záznamy z UNKNOWN_CHECKLISTS
# ═══════════════════════════════════════════════════════════════════

# These 7 lines don't belong in UNKNOWN_CHECKLISTS
bad_block = (
    "    # Governance\n"
    "    'has_ai_register':              {'severity': 'limited',  'color': 'yellow', 'label': 'Omezen\u00e9 riziko'},\n"
    "    'has_ai_vendor_contracts':      {'severity': 'limited',  'color': 'yellow', 'label': 'Omezen\u00e9 riziko'},\n"
    "    'has_ai_bias_check':            {'severity': 'limited',  'color': 'yellow', 'label': 'Omezen\u00e9 riziko'},\n"
    "    # D\u011bti / GPAI\n"
    "    'uses_ai_for_children':         {'severity': 'high',     'color': 'orange', 'label': 'Vysok\u00e9 riziko'},\n"
    "    'uses_gpai_api':                {'severity': 'limited',  'color': 'yellow', 'label': 'Omezen\u00e9 riziko'},\n"
)

bad_block_norm = unicodedata.normalize("NFC", bad_block)

if bad_block_norm in content:
    content = content.replace(bad_block_norm, "", 1)
    changes += 1
    print("\u2705 FIX 1: Severity z\u00e1znamy odstran\u011bny z UNKNOWN_CHECKLISTS")
else:
    print("\u274c FIX 1: Bad block not found in UNKNOWN_CHECKLISTS")


# ═══════════════════════════════════════════════════════════════════
# FIX 2: Přidat checklist záznamy pro uses_ai_for_children a uses_gpai_api
# ═══════════════════════════════════════════════════════════════════

NEW_CHECKLISTS = (
    "    # D\u011bti / GPAI\n"
    "    'uses_ai_for_children': [\n"
    "        'Koho se zeptat: produktov\u00fd mana\u017eer, v\u00fdvoj\u00e1\u0159i, marketing.',\n"
    "        'P\u0159\u00edklad: Mobiln\u00ed aplikace s AI chatbotem, kterou pou\u017e\u00edvaj\u00ed d\u011bti \u2014 nap\u0159. eduka\u010dn\u00ed hra nebo online v\u00fdukov\u00e1 platforma.',\n"
    "        'Zkontrolujte, zda va\u0161e AI produkty/slu\u017eby c\u00edl\u00ed na osoby mlad\u0161\u00ed 18 let.',\n"
    "        'Ov\u011b\u0159te, zda sb\u00edr\u00e1te data d\u011bt\u00ed nebo AI interaguje s d\u011btmi p\u0159\u00edmo.',\n"
    "    ],\n"
    "    'uses_gpai_api': [\n"
    "        'Koho se zeptat: CTO, v\u00fdvoj\u00e1\u0159i, produktov\u00fd t\u00fdm.',\n"
    "        'P\u0159\u00edklad: Firma vol\u00e1 OpenAI API ze sv\u00e9 aplikace a v\u00fdstupy zobrazuje z\u00e1kazn\u00edk\u016fm.',\n"
    "        'Zkontrolujte zdrojov\u00fd k\u00f3d a faktury \u2014 plat\u00edte za API kl\u00ed\u010de k LLM slu\u017eb\u00e1m?',\n"
    "        'Ov\u011b\u0159te, zda v\u00fdstupy LLM vid\u00ed kone\u010dn\u00ed u\u017eivatel\u00e9 va\u0161eho produktu.',\n"
    "    ],\n"
)

# Insert before closing "}" of UNKNOWN_CHECKLISTS
# Find has_ai_bias_check checklist (last entry now), then "],\n}"
uc_start = content.find("UNKNOWN_CHECKLISTS")
if uc_start == -1:
    print("\u274c FIX 2: UNKNOWN_CHECKLISTS not found")
else:
    # Find the last checklist list — has_ai_bias_check
    bias_checklist = content.find("'has_ai_bias_check': [", uc_start)
    if bias_checklist == -1:
        print("\u274c FIX 2: has_ai_bias_check not found in UNKNOWN_CHECKLISTS")
    else:
        close_pat = "    ],\n}"
        close_pos = content.find(close_pat, bias_checklist)
        if close_pos == -1:
            print("\u274c FIX 2: Close pattern not found")
        else:
            insert_at = close_pos + len("    ],\n")
            content = content[:insert_at] + NEW_CHECKLISTS + content[insert_at:]
            changes += 1
            print("\u2705 FIX 2: Checklist z\u00e1znamy p\u0159id\u00e1ny pro children + GPAI")


# ═══════════════════════════════════════════════════════════════════
# FIX 3: Přidat severity záznamy do _NEVIM_SEVERITY
# ═══════════════════════════════════════════════════════════════════

NEW_SEVERITY = (
    "\n    # Governance\n"
    "    'has_ai_register':              {'severity': 'limited',  'color': 'yellow', 'label': 'Omezen\u00e9 riziko'},\n"
    "    'has_ai_vendor_contracts':      {'severity': 'limited',  'color': 'yellow', 'label': 'Omezen\u00e9 riziko'},\n"
    "    'has_ai_bias_check':            {'severity': 'limited',  'color': 'yellow', 'label': 'Omezen\u00e9 riziko'},\n"
    "    # D\u011bti / GPAI\n"
    "    'uses_ai_for_children':         {'severity': 'high',     'color': 'orange', 'label': 'Vysok\u00e9 riziko'},\n"
    "    'uses_gpai_api':                {'severity': 'limited',  'color': 'yellow', 'label': 'Omezen\u00e9 riziko'},"
)

# Find _NEVIM_SEVERITY, then 'uses_copilot' (last existing key), then "\n}"
ns_start = content.find("_NEVIM_SEVERITY")
if ns_start == -1:
    print("\u274c FIX 3: _NEVIM_SEVERITY not found")
else:
    copilot = content.find("'uses_copilot'", ns_start)
    if copilot == -1:
        print("\u274c FIX 3: 'uses_copilot' not found in _NEVIM_SEVERITY")
    else:
        close_pos = content.find("\n}", copilot)
        if close_pos == -1:
            print("\u274c FIX 3: _NEVIM_SEVERITY close not found")
        else:
            content = content[:close_pos] + NEW_SEVERITY + content[close_pos:]
            changes += 1
            print("\u2705 FIX 3: Severity z\u00e1znamy p\u0159id\u00e1ny do _NEVIM_SEVERITY")


# ═══════════════════════════════════════════════════════════════════
# ZÁPIS
# ═══════════════════════════════════════════════════════════════════

if changes > 0:
    with open(FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n\u2705 BATCH 5 FIX HOTOV \u2014 {changes}/3 oprav provedeno, soubor ulo\u017een")
else:
    print("\n\u274c \u017d\u00e1dn\u00e9 opravy nebyly provedeny!")
