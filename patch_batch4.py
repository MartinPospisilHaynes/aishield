#!/usr/bin/env python3
"""BATCH 4: Strukturální úpravy.

P2. Smazat Q35 (develops_own_ai duplikát v ai_role), přidat provider warning do Q08
P8. Přidat scope_hint do can_override_ai (vyjasnit odlišení od uses_ai_decision)
"""
import re
import unicodedata

FILE = "backend/api/questionnaire.py"

with open(FILE, encoding="utf-8") as f:
    content = f.read()

content = unicodedata.normalize("NFC", content)
original = content
changes = 0

# ═══════════════════════════════════════════════════════════════════
# P2a: Přidat ai_provider_warning do Q08 followup
# ═══════════════════════════════════════════════════════════════════

# Anchor: "Distribuujeme AI (distributor)" — unique in Q08's ai_role multi_select
anchor = '"Distribuujeme AI (distributor)"'
anchor_pos = content.find(anchor)

if anchor_pos == -1:
    print("\u274c P2a: Anchor 'Distribuujeme AI (distributor)' not found")
else:
    # Find "]},\n                    ]" — closes options + field + fields list
    close_pat = ']},\n                    ]'
    close_pos = content.find(close_pat, anchor_pos)
    if close_pos == -1:
        print("\u274c P2a: Close pattern not found after anchor")
    else:
        new_field = (
            ']},\n'
            '                        {"key": "ai_provider_warning", "label": "\u26a0\ufe0f Jako poskytovatel AI syst\u00e9mu (\u010dl. 3 bod 3) m\u00e1te rozs\u00e1hlej\u0161\u00ed povinnosti: technick\u00e1 dokumentace (p\u0159\u00edloha IV), posouzen\u00ed shody (\u010dl. 16), ozna\u010den\u00ed CE, syst\u00e9m \u0159\u00edzen\u00ed kvality. **AIshield v\u00e1m pom\u016f\u017ee s kompletn\u00ed dokumentac\u00ed.**", "type": "info"},\n'
            '                    ]'
        )
        content = content[:close_pos] + new_field + content[close_pos + len(close_pat):]
        changes += 1
        print("\u2705 P2a: ai_provider_warning p\u0159id\u00e1n do Q08 followup")


# ═══════════════════════════════════════════════════════════════════
# P2b: Smazat Q35 (develops_own_ai) z ai_role sekce
# ═══════════════════════════════════════════════════════════════════

# Find "ai_role" section, then the duplicate develops_own_ai within it
ai_role_pos = content.find('"id": "ai_role"')
if ai_role_pos == -1:
    print("\u274c P2b: Section 'ai_role' not found")
else:
    # Find the develops_own_ai key within this section
    key_pattern = '"key": "develops_own_ai"'
    dev_pos = content.find(key_pattern, ai_role_pos)
    if dev_pos == -1:
        print("\u274c P2b: develops_own_ai not found in ai_role section")
    else:
        # Find the start of Q35 block: scan backward to find "            {\n"
        before = content[:dev_pos]
        q35_start = before.rfind("            {\n")
        
        if q35_start == -1:
            print("\u274c P2b: Q35 block start not found")
        else:
            # Find Q35 block end: "            },\n            {"
            # (boundary between Q35 and modifies_ai_purpose)
            rest = content[q35_start:]
            boundary = re.search(r'            \},\n            \{', rest)
            
            if boundary is None:
                print("\u274c P2b: Q35/Q36 boundary not found")
            else:
                # Delete from q35_start to just after "            },\n"
                q35_end = q35_start + boundary.start() + len("            },\n")
                content = content[:q35_start] + content[q35_end:]
                changes += 1
                print("\u2705 P2b: Q35 (develops_own_ai duplik\u00e1t) smaz\u00e1n z ai_role")


# ═══════════════════════════════════════════════════════════════════
# P8: Přidat scope_hint do can_override_ai
# ═══════════════════════════════════════════════════════════════════

# Anchor: "can_override_ai" key + find the question block
override_pos = content.find('"key": "can_override_ai"')
if override_pos == -1:
    print("\u274c P8: can_override_ai not found")
else:
    # Find the help_text line after it
    help_pos = content.find('"help_text":', override_pos)
    if help_pos == -1:
        print("\u274c P8: help_text not found for can_override_ai")
    else:
        # Find the closing of help_text line — ends with '",\n'
        # Then insert scope_hint after it
        # We look for the next '"followup"' or '"scope_hint"' after help_text
        followup_pos = content.find('"followup":', help_pos)
        if followup_pos == -1:
            print("\u274c P8: followup not found after help_text")
        else:
            # Insert scope_hint right before "followup":
            scope_hint = (
                '                "scope_hint": "Tato ot\u00e1zka se vztahuje na V\u0160ECHNY AI syst\u00e9my ve firm\u011b \u2014 nejen z\u00e1kaznick\u00fd servis, ale i HR, finance, intern\u00ed procesy. '
                'Odpov\u011bzte ANO, pokud zam\u011bstnanci mohou v jak\u00e9mkoliv p\u0159\u00edpad\u011b rozhodnut\u00ed AI p\u0159epsat nebo zru\u0161it.",\n'
            )
            content = content[:followup_pos] + scope_hint + content[followup_pos:]
            changes += 1
            print("\u2705 P8: scope_hint p\u0159id\u00e1n do can_override_ai")


# ═══════════════════════════════════════════════════════════════════
# ZÁPIS
# ═══════════════════════════════════════════════════════════════════

if changes > 0:
    with open(FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n\u2705 BATCH 4 HOTOV \u2014 {changes}/3 zm\u011bn provedeno, soubor ulo\u017een")
else:
    print("\n\u274c \u017d\u00e1dn\u00e9 zm\u011bny nebyly provedeny!")
