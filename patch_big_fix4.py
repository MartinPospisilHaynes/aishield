#!/usr/bin/env python3
"""Fix remaining šablonu/Nebojte issues using byte-level replacement."""
import unicodedata

FILE = "/Users/martinhaynes/Projects/aishield/backend/api/questionnaire.py"

with open(FILE, "r", encoding="utf-8") as f:
    src = f.read()

# Normalize to NFC (composed form)
src = unicodedata.normalize("NFC", src)
changes = []

# Helper: normalize both search and replace strings
def nfc(s):
    return unicodedata.normalize("NFC", s)

# 13a: Fix training_attendance warning - šablonu prezenční listiny
old = nfc("školící prezentaci + šablonu prezenční listiny.**")
new = nfc("školící prezentaci + profesionálně zpracovanou prezenční listinu.**")
if old in src:
    src = src.replace(old, new)
    changes.append("13a OK: training_attendance fixed")
else:
    changes.append(f"13a FAIL: '{old[:30]}...' not found")

# 13c: Fix training_no_warning - remove Nebojte se + fix šablona
old_c = nfc("**Nebojte se — součástí všech AIshield balíčků je kompletní školící prezentace (PowerPoint) + šablona prezenční listiny, kterou zaměstnanci podepíšou. Vše zařídíme za vás.**")
new_c = nfc("**Součástí všech AIshield balíčků je kompletní školící prezentace (PowerPoint) + profesionálně zpracovaná prezenční listina, kterou zaměstnanci podepíšou.**")
if old_c in src:
    src = src.replace(old_c, new_c)
    changes.append("13c OK: training_no_warning Nebojte removed + šablona fixed")
else:
    # Try to find Nebojte se and show context
    idx = src.find(nfc("Nebojte se"))
    if idx >= 0:
        # Extract from ** to **
        block_start = src.rfind("**", max(0, idx-100), idx)
        block_end = src.find("**", idx)
        if block_end >= 0:
            block_end += 2
        actual = src[block_start:block_end]
        changes.append(f"13c FAIL: Nebojte found but exact pattern differs")
        changes.append(f"  ACTUAL: {repr(actual[:200])}")
        changes.append(f"  EXPECTED: {repr(old_c[:200])}")
        # Try direct replacement anyway
        if actual and block_start >= 0:
            src = src[:block_start] + new_c + src[block_end:]
            changes.append(f"13c FIXED via position-based replacement")
    else:
        changes.append("13c FAIL: Nebojte not found at all")

# 13i: Fix _NO_ANSWER_RECOMMENDATIONS training
old_i = nfc("školící prezentaci (PowerPoint) a šablonu prezenční listiny.")
new_i = nfc("školící prezentaci (PowerPoint) a profesionálně zpracovanou prezenční listinu.")
if old_i in src:
    src = src.replace(old_i, new_i)
    changes.append("13i OK: _NO_ANSWER recs training fixed")
else:
    changes.append(f"13i FAIL: recs pattern not found")

# Verify no more šablonu/šablona remains
for word in ["šablonu", "šablona"]:
    nword = nfc(word)
    count = src.count(nword)
    if count > 0:
        changes.append(f"WARNING: '{word}' still appears {count} time(s)")
        start = 0
        while True:
            pos = src.find(nword, start)
            if pos == -1:
                break
            changes.append(f"  at pos {pos}: ...{src[max(0,pos-30):pos+50]}...")
            start = pos + 1

with open(FILE, "w", encoding="utf-8") as f:
    f.write(src)

print("\nResults:")
for c in changes:
    print(f"  {c}")
