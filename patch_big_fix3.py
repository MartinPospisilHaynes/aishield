#!/usr/bin/env python3
"""Fix remaining 3 patches: 13a, 13c, 13i."""
FILE = "/Users/martinhaynes/Projects/aishield/backend/api/questionnaire.py"

with open(FILE, "r", encoding="utf-8") as f:
    src = f.read()

changes = []

# 13a: training_attendance warning — exact string from file
old = '\u0161kolic\u00ed prezentaci + \u0161ablonu prezen\u010dn\u00ed listiny.**'
new = '\u0161kolic\u00ed prezentaci + profesion\u00e1ln\u011b zpracovanou prezen\u010dn\u00ed listinu.**'
if old in src:
    src = src.replace(old, new)
    changes.append("13a OK")
else:
    changes.append("13a FAIL")

# 13c: training_no_warning — Nebojte se... search
# First find "Nebojte se" occurrence
idx = src.find("Nebojte se")
if idx >= 0:
    print(f"Found 'Nebojte se' at position {idx}")
    context = repr(src[max(0,idx-20):idx+250])
    print(f"Context: {context}")
    
    # Replace the entire Nebojte se block
    old_nb = '**Nebojte se \u2014 sou\u010d\u00e1st\u00ed v\u0161ech AIshield bal\u00ed\u010dk\u016f je kompletn\u00ed \u0161kolic\u00ed prezentace (PowerPoint) + \u0161ablona prezen\u010dn\u00ed listiny, kterou zam\u011bstnanci podep\u00ed\u0161ou. V\u0161e za\u0159\u00edd\u00edme za v\u00e1s.**'
    if old_nb in src:
        new_nb = '**Sou\u010d\u00e1st\u00ed v\u0161ech AIshield bal\u00ed\u010dk\u016f je kompletn\u00ed \u0161kolic\u00ed prezentace (PowerPoint) + profesion\u00e1ln\u011b zpracovan\u00e1 prezen\u010dn\u00ed listina, kterou zam\u011bstnanci podep\u00ed\u0161ou.**'
        src = src.replace(old_nb, new_nb)
        changes.append("13c OK - exact match")
    else:
        # Try character by character
        # Look for pattern near the found index
        snippet = src[idx:idx+300]
        print(f"Nearby: {repr(snippet)}")
        changes.append("13c FAIL - Nebojte found but block pattern mismatch")
else:
    changes.append("13c FAIL - Nebojte not found at all")

# Check for remaining šablonu/šablona
for word in ['\u0161ablonu', '\u0161ablona']:
    positions = []
    start = 0
    while True:
        pos = src.find(word, start)
        if pos == -1:
            break
        positions.append(pos)
        start = pos + 1
    if positions:
        print(f"\nRemaining '{word}' at {len(positions)} position(s):")
        for p in positions:
            print(f"  pos {p}: ...{src[max(0,p-20):p+60]}...")

# 13i: _NO_ANSWER recs training
old_recs = '\u0161kolic\u00ed prezentaci (PowerPoint) a \u0161ablonu prezen\u010dn\u00ed listiny.'
new_recs = '\u0161kolic\u00ed prezentaci (PowerPoint) a profesion\u00e1ln\u011b zpracovanou prezen\u010dn\u00ed listinu.'
if old_recs in src:
    src = src.replace(old_recs, new_recs)
    changes.append("13i OK")
else:
    changes.append("13i FAIL")

with open(FILE, "w", encoding="utf-8") as f:
    f.write(src)

print("\nResults:")
for c in changes:
    print(f"  {c}")
