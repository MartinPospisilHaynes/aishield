#!/usr/bin/env python3
"""
Patch questionnaire.py:
1) Fix ai_decision_logging — add internal note to followup_no
2) Fix monitors_ai_outputs — simplify, add scope_hint, rewrite help_text
"""
import re

FILE = "/Users/martinhaynes/Projects/aishield/backend/api/questionnaire.py"

with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

# ─── 1) ai_decision_logging: Add internal disclaimer to followup_no ───

old_logging = (
    '{"key": "logging_warning", "label": '
    '"\u26a0\ufe0f \u010cl\u00e1nek 26 odst. 1 p\u00edsm. f) AI Act vy\u017eaduje '
    'uchov\u00e1v\u00e1n\u00ed automaticky generovan\u00fdch protokol\u016f po dobu '
    'nejm\u00e9n\u011b 6 m\u011bs\u00edc\u016f. Logov\u00e1n\u00ed je kl\u00ed\u010dov\u00e9 '
    'pro audit a zp\u011btnou kontrolu.", "type": "info"},'
)

new_logging = (
    '{"key": "logging_warning", "label": '
    '"\u26a0\ufe0f \u010cl\u00e1nek 26 odst. 1 p\u00edsm. f) AI Act vy\u017eaduje '
    'uchov\u00e1v\u00e1n\u00ed automaticky generovan\u00fdch protokol\u016f po dobu '
    'nejm\u00e9n\u011b 6 m\u011bs\u00edc\u016f. Logov\u00e1n\u00ed je kl\u00ed\u010dov\u00e9 '
    'pro audit a zp\u011btnou kontrolu.", "type": "info"},\n'
    '                        {"key": "logging_internal_note", "label": '
    '"\u26a0\ufe0f D\u016fle\u017eit\u00e9: Logov\u00e1n\u00ed rozhodnut\u00ed AI '
    'je intern\u00ed z\u00e1le\u017eitost va\u0161\u00ed firmy \u2014 vy nejl\u00e9pe '
    'zn\u00e1te sv\u00e9 syst\u00e9my a procesy. AIshield v\u00e1m poskytne \u0161ablonu '
    'logovac\u00edho protokolu (co zaznamen\u00e1vat, jak dlouho uchov\u00e1vat, '
    'form\u00e1t z\u00e1znam\u016f), ale samotn\u00e9 logov\u00e1n\u00ed mus\u00edte '
    'nastavit ve sv\u00fdch intern\u00edch syst\u00e9mech.", "type": "info"},'
)

# Use regex to find the logging_warning line
pattern_logging = re.compile(
    r'\{"key": "logging_warning".*?uchovávání protokolů"\},?\s*\n',
    re.DOTALL
)

# Try direct replacement first
if old_logging in content:
    content = content.replace(old_logging, new_logging)
    print("[OK] ai_decision_logging: Added internal disclaimer via direct replace")
else:
    # Regex approach
    match = pattern_logging.search(content)
    if match:
        # Find the exact line with logging_warning
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if '"logging_warning"' in line and 'uchovávání' in line:
                # Add new line after this one
                indent = '                        '
                new_line = (
                    indent + '{"key": "logging_internal_note", "label": '
                    '"⚠️ Důležité: Logování rozhodnutí AI je interní záležitost vaší firmy — '
                    'vy nejlépe znáte své systémy a procesy. AIshield vám poskytne šablonu '
                    'logovacího protokolu (co zaznamenávat, jak dlouho uchovávat, formát '
                    'záznamů), ale samotné logování musíte nastavit ve svých interních '
                    'systémech.", "type": "info"},'
                )
                lines.insert(i + 1, new_line)
                content = '\n'.join(lines)
                print(f"[OK] ai_decision_logging: Added internal disclaimer after line {i+1}")
                break
        else:
            print("[WARN] ai_decision_logging: logging_warning not found by regex")
    else:
        print("[WARN] ai_decision_logging: Could not find logging_warning")

# ─── 2) monitors_ai_outputs: Simplify the question ───
# The question already has a scope_hint and two warnings in followup_no.
# Let's improve the help_text to be clearer and add a followup for "yes" too.

# Find and update the help_text for monitors_ai_outputs
old_monitors_help = (
    '"help_text": "P\u0159\u00edklady:\\n1) T\u00fddenn\u00ed audit vzorku '
    'chatbotov\u00fdch odpov\u011bd\u00ed.\\n2) M\u011bs\u00ed\u010dn\u00ed '
    'kontrola p\u0159esnosti AI doporu\u010den\u00ed.\\n3) Automatick\u00fd '
    'monitoring bias a drift v ML modelech.",'
)

new_monitors_help = (
    '"help_text": "T\u00e1\u017ee se, jestli n\u011bkdo ve va\u0161\u00ed firm\u011b '
    'pravideln\u011b kontroluje, \u017ee AI d\u011bl\u00e1 to, co m\u00e1.\\n\\n'
    'P\u0159\u00edklady ANO:\\n'
    '1) Vedouc\u00ed \u010dte n\u00e1hodn\u00e9 odpov\u011bdi chatbota a ov\u011b\u0159uje '
    'spr\u00e1vnost.\\n'
    '2) T\u00fdm jednou m\u011bs\u00ed\u010dn\u011b kontroluje AI doporu\u010den\u00ed.\\n'
    '3) V\u00fdvoj\u00e1\u0159 monitoruje p\u0159esnost ML modelu.\\n\\n'
    'P\u0159\u00edklady NE:\\n'
    '1) AI chatbot b\u011b\u017e\u00ed a nikdo jeho odpov\u011bdi nekontroluje.\\n'
    '2) AI generuje reporty, kter\u00e9 se pos\u00edlaj\u00ed p\u0159\u00edmo '
    'z\u00e1kazn\u00edk\u016fm.\\n\\n'
    'Pokud AI pou\u017e\u00edv\u00e1te jen ob\u010das pro sebe (nap\u0159. ChatGPT), '
    'odpov\u011bzte Ne.",'
)

# Try direct replace
if old_monitors_help in content:
    content = content.replace(old_monitors_help, new_monitors_help)
    print("[OK] monitors_ai_outputs: Updated help_text via direct replace")
else:
    # Regex approach - find the line
    lines = content.split('\n')
    found = False
    for i, line in enumerate(lines):
        if 'monitors_ai_outputs' in line:
            # Found the question key, now find help_text nearby
            for j in range(i, min(i+10, len(lines))):
                if '"help_text"' in lines[j] and 'audit vzorku' in lines[j]:
                    lines[j] = (
                        '                "help_text": "Táže se, jestli někdo ve vaší firmě '
                        'pravidelně kontroluje, že AI dělá to, co má.\\n\\n'
                        'Příklady ANO:\\n'
                        '1) Vedoucí čte náhodné odpovědi chatbota a ověřuje správnost.\\n'
                        '2) Tým jednou měsíčně kontroluje AI doporučení.\\n'
                        '3) Vývojář monitoruje přesnost ML modelu.\\n\\n'
                        'Příklady NE:\\n'
                        '1) AI chatbot běží a nikdo jeho odpovědi nekontroluje.\\n'
                        '2) AI generuje reporty, které se posílají přímo zákazníkům.\\n\\n'
                        'Pokud AI používáte jen občas pro sebe (např. ChatGPT), odpovězte Ne.",'
                    )
                    found = True
                    print(f"[OK] monitors_ai_outputs: Updated help_text at line {j+1}")
                    break
            break
    if not found:
        print("[WARN] monitors_ai_outputs: Could not find help_text to replace")
    content = '\n'.join(lines)

# Write back
with open(FILE, "w", encoding="utf-8") as f:
    f.write(content)

print("\n[DONE] Patch applied. Verify with: python3 -c \"import ast; ast.parse(open('{}').read()); print('Syntax OK')\"".format(FILE))
