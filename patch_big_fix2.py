#!/usr/bin/env python3
"""Fix the 4 remaining failed patches."""
FILE = "/Users/martinhaynes/Projects/aishield/backend/api/questionnaire.py"

with open(FILE, "r", encoding="utf-8") as f:
    src = f.read()

changes = []

# 8. Remove manipulation_type from uses_subliminal_manipulation
# The issue was the 🚫 emoji encoding — use actual content from file
old_block = '                        {"key": "manipulation_type"'
idx = src.find(old_block)
if idx >= 0:
    # Find the end of manipulation_type line (ends with "]},") and start of manipulation_warning
    end_of_type = src.find('\n', idx)
    # Find next line (options line)
    next_line_start = end_of_type + 1
    next_line_end = src.find('\n', next_line_start)
    # Remove both lines (manipulation_type key + options line)
    src = src[:idx] + src[next_line_end+1:]
    changes.append("8. Removed manipulation_type sub-question")
else:
    changes.append("8. FAILED — manipulation_type not found")

# 13a. training_attendance warning — has ** markers
old = '**AIshield.cz v\u00e1m v r\u00e1mci slu\u017eeb dod\u00e1 kompletn\u00ed \u0161kolic\u00ed prezentaci + \u0161ablonu prezen\u010dn\u00ed listiny.**'
new = '**AIshield.cz v\u00e1m v r\u00e1mci slu\u017eeb dod\u00e1 kompletn\u00ed \u0161kolic\u00ed prezentaci + profesion\u00e1ln\u011b zpracovanou prezen\u010dn\u00ed listinu.**'
if old in src:
    src = src.replace(old, new)
    changes.append("13a. Fixed training_attendance: šablonu → profesionálně zpracovanou")
else:
    changes.append("13a. FAILED — training_attendance ** pattern not found")

# 13c. training_no_warning — has ** and "Nebojte se"
old = '**Nebojte se \u2014 sou\u010d\u00e1st\u00ed v\u0161ech AIshield bal\u00ed\u010dk\u016f je kompletn\u00ed \u0161kolic\u00ed prezentace (PowerPoint) + \u0161ablona prezen\u010dn\u00ed listiny, kterou zam\u011bstnanci podep\u00ed\u0161ou. V\u0161e za\u0159\u00edd\u00edme za v\u00e1s.**'
new = '**Sou\u010d\u00e1st\u00ed v\u0161ech AIshield bal\u00ed\u010dk\u016f je kompletn\u00ed \u0161kolic\u00ed prezentace (PowerPoint) + profesion\u00e1ln\u011b zpracovan\u00e1 prezen\u010dn\u00ed listina, kterou zam\u011bstnanci podep\u00ed\u0161ou.**'
if old in src:
    src = src.replace(old, new)
    changes.append("13c. Fixed training_no_warning: removed Nebojte se + šablona → profesionální")
else:
    changes.append("13c. FAILED — training_no_warning Nebojte pattern not found")

# 13i. _NO_ANSWER_RECOMMENDATIONS has_ai_training
old = '\u0161kolic\u00ed prezentaci (PowerPoint) a \u0161ablonu prezen\u010dn\u00ed listiny.'
new = '\u0161kolic\u00ed prezentaci (PowerPoint) a profesion\u00e1ln\u011b zpracovanou prezen\u010dn\u00ed listinu.'
if old in src:
    src = src.replace(old, new)
    changes.append("13i. Fixed _NO_ANSWER recs training šablonu")
else:
    changes.append("13i. FAILED — recs training not found")

with open(FILE, "w", encoding="utf-8") as f:
    f.write(src)

for c in changes:
    status = "✅" if "FAILED" not in c else "❌"
    print(f"  {status} {c}")

ok = sum(1 for c in changes if "FAILED" not in c)
fail = sum(1 for c in changes if "FAILED" in c)
print(f"\n  Summary: {ok} succeeded, {fail} failed")
