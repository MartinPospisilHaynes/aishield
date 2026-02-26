#!/usr/bin/env python3
"""
Gen20 patch: Ban English headings across all prompts.
1. Add system-level rule: ALL headings must be in Czech
2. Replace specific English headings found in prompts
3. Add rule to M4 refiner too
"""

# ===== M1 GENERATOR =====
FILE_M1 = "/opt/aishield/backend/documents/m1_generator.py"

with open(FILE_M1, "r") as f:
    code = f.read()

changes = 0

# 1. Replace specific English headings → Czech
replacements = [
    ("<h2>1. Executive Summary</h2>", "<h2>1. Shrnut\u00ed pro veden\u00ed</h2>"),
    ("<h1>Compliance Report \u2014 Souhrnn\u00e1 zpr\u00e1va o souladu s AI Act</h1>",
     "<h1>Zpr\u00e1va o souladu s AI Act</h1>"),
    ("<h2>8. Kontroln\u00ed tabulka (checklist)</h2>",
     "<h2>8. Kontroln\u00ed tabulka</h2>"),
    ("<h1>Dodavatelsk\u00fd checklist \u2014 hodnocen\u00ed poskytovatel\u016f AI</h1>",
     "<h1>Dodavatelsk\u00fd kontroln\u00ed list \u2014 hodnocen\u00ed poskytovatel\u016f AI</h1>"),
    ("<h2>7. Reporting</h2>", "<h2>7. V\u00fdkaznictv\u00ed a hl\u00e1\u0161en\u00ed</h2>"),
    ("<h2>8. Review a aktualizace</h2>", "<h2>8. Revize a aktualizace</h2>"),
]

for old, new in replacements:
    if old in code:
        code = code.replace(old, new, 1)
        changes += 1
        print(f"  OK heading: {old[:50]}... -> {new[:50]}...")

# 2. Also fix inline English terms in headings context
inline_fixes = [
    ("Risk assessment p\u0159ed nasazen\u00edm", "Posouzen\u00ed rizik p\u0159ed nasazen\u00edm"),
]
for old, new in inline_fixes:
    if old in code:
        code = code.replace(old, new)
        changes += 1
        print(f"  OK inline: {old}")

# 3. Add system rule: NO ENGLISH HEADINGS
# Find the section about HTML formatting rules (line ~40-50)
old_rule = "1. Pi\u0161 p\u0159\u00edmo HTML obsah \u2014 za\u010dni <h1> tagem s n\u00e1zvem dokumentu."
new_rule = """1. Pi\u0161 p\u0159\u00edmo HTML obsah \u2014 za\u010dni <h1> tagem s n\u00e1zvem dokumentu.
   V\u0160ECHNY nadpisy (<h1>, <h2>, <h3>) MUSEJ\u00cd b\u00fdt v \u010ce\u0161tin\u011b.
   ZAK\u00c1Z\u00c1NO: anglick\u00e9 nadpisy (Executive Summary, Risk Assessment, Key Findings,
   Next Steps, Action Items, Reporting, Review, Scope, Appendix, Checklist, Compliance Report).
   Pou\u017e\u00edvej \u010desk\u00e9 ekvivalenty: Shrnut\u00ed, Posouzen\u00ed rizik, Kl\u00ed\u010dov\u00e1 zji\u0161t\u011bn\u00ed,
   Dal\u0161\u00ed kroky, Ak\u010dn\u00ed body, V\u00fdkaznictv\u00ed, Revize, Rozsah, P\u0159\u00edloha, Kontroln\u00ed seznam."""

if old_rule in code:
    code = code.replace(old_rule, new_rule, 1)
    changes += 1
    print("  OK: System rule added — no English headings")

# 4. Add to NIKDY/ZAKÁZÁNO section
old_nikdy = "- Kli\u0161\u00e9: \u201eV dne\u0161n\u00ed digit\u00e1ln\u00ed dob\u011b\u201c, \u201eZ\u00e1v\u011brem lze \u0159\u00edci\u201c"
new_nikdy = """- Kli\u0161\u00e9: \u201eV dne\u0161n\u00ed digit\u00e1ln\u00ed dob\u011b\u201c, \u201eZ\u00e1v\u011brem lze \u0159\u00edci\u201c
- Anglick\u00e9 nadpisy a n\u00e1zvy kapitol (Executive Summary, Risk Assessment, Checklist,
  Reporting, Review, Scope, Appendix, Compliance Report \u2014 v\u017edy \u010cesky!)"""

if old_nikdy in code:
    code = code.replace(old_nikdy, new_nikdy, 1)
    changes += 1
    print("  OK: NIKDY section extended — no English headings")

with open(FILE_M1, "w") as f:
    f.write(code)

print(f"\nm1_generator.py: {changes} changes")

# ===== M4 REFINER =====
FILE_M4 = "/opt/aishield/backend/documents/m4_refiner.py"

with open(FILE_M4, "r") as f:
    code4 = f.read()

m4_changes = 0

# Add no-English-headings rule to M4 ZAK\u00c1Z\u00c1NO section
old_klise = "- Kli\u0161\u00e9: \u201eV dne\u0161n\u00ed digit\u00e1ln\u00ed dob\u011b\u201c, \u201eZ\u00e1v\u011brem lze \u0159\u00edci\u201c"
new_klise = """- Kli\u0161\u00e9: \u201eV dne\u0161n\u00ed digit\u00e1ln\u00ed dob\u011b\u201c, \u201eZ\u00e1v\u011brem lze \u0159\u00edci\u201c
- Anglick\u00e9 nadpisy: Executive Summary \u2192 Shrnut\u00ed, Reporting \u2192 V\u00fdkaznictv\u00ed,
  Review \u2192 Revize, Checklist \u2192 Kontroln\u00ed seznam, Scope \u2192 Rozsah atd.
  V\u0160ECHNY nadpisy MUSEJ\u00cd b\u00fdt \u010desky. Pokud najde\u0161 anglick\u00fd nadpis v draftu, p\u0159elo\u017e ho."""

if old_klise in code4:
    code4 = code4.replace(old_klise, new_klise, 1)
    m4_changes += 1
    print("  OK M4: ZAKÁZÁNO section — no English headings")

with open(FILE_M4, "w") as f:
    f.write(code4)

print(f"m4_refiner.py: {m4_changes} changes")
print("\nDone!")
