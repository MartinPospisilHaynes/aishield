#!/usr/bin/env python3
"""
Patch questionnaire.py:
1. Remove "Nechci uvádět" from revenue question options
2. Delete ai_transparency_docs question entirely
3. Fix has_oversight_person: remove "volitelné", add phone, remove "Výborně!", rewrite followup_no
"""

import re

import os
FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "api", "questionnaire.py")

with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

original = content

# ─── 1. Remove "Nechci uvádět" from revenue options ───
# Find the line with "Nechci uvádět" inside company_annual_revenue options and remove it
content = re.sub(
    r'\s*"Nechci uv\u00e1d\u011bt",\n',
    '\n',
    content
)

# ─── 2. Delete ai_transparency_docs question ───
# This is a full question dict starting with {"key": "ai_transparency_docs" and ending before the next question
# It's bounded by the closing }], of the previous question and the start of section 8
content = re.sub(
    r'\s*\{\s*"key":\s*"ai_transparency_docs".*?\},\n',
    '\n',
    content,
    flags=re.DOTALL
)

# ─── 3. Fix has_oversight_person "Ano" branch ───
# 3a. Remove "(volitelné — použijeme v dokumentaci)" from oversight_person_name
content = content.replace(
    'Jm\u00e9no odpov\u011bdn\u00e9 osoby (voliteln\u00e9 \u2014 pou\u017eijeme v dokumentaci):',
    'Jm\u00e9no odpov\u011bdn\u00e9 osoby:'
)

# 3b. Remove "(volitelné — pro eskalační plán)" from oversight_person_email
content = content.replace(
    'E-mail odpov\u011bdn\u00e9 osoby (voliteln\u00e9 \u2014 pro eskala\u010dn\u00ed pl\u00e1n):',
    'E-mail odpov\u011bdn\u00e9 osoby:'
)

# 3c. Add phone field after oversight_person_email in "Ano" followup
# Find the oversight_person_email line and add phone after it
content = content.replace(
    '{"key": "oversight_person_email", "label": "E-mail odpov\u011bdn\u00e9 osoby:", "type": "text"},',
    '{"key": "oversight_person_email", "label": "E-mail odpov\u011bdn\u00e9 osoby:", "type": "text"},\n                        {"key": "oversight_person_phone", "label": "Telefon odpov\u011bdn\u00e9 osoby:", "type": "text"},'
)

# 3d. Remove "Výborně!" info from "Ano" followup
content = re.sub(
    r'\s*\{"key":\s*"oversight_ok_info".*?\},\n',
    '\n',
    content,
    flags=re.DOTALL
)

# ─── 4. Rewrite has_oversight_person "Ne" branch ───
# Replace the entire followup_no block for has_oversight_person
old_followup_no = '''"followup_no": {
                    "fields": [
                        {"key": "oversight_warning", "label": "\u26a0\ufe0f \u010cl\u00e1nek 14 AI Act vy\u017eaduje lidsk\u00fd dohled nad vysoce rizikov\u00fdmi AI syst\u00e9my. I u syst\u00e9m\u016f s omezen\u00fdm rizikem (chatboty) je vhodn\u00e9 m\u00edt odpov\u011bdnou osobu.", "type": "info"},
                        {"key": "oversight_suggested_role", "label": "Kdo by ve va\u0161\u00ed firm\u011b mohl na AI dohl\u00ed\u017eet?", "type": "select",
                         "options": [
                             "J\u00e1 osobn\u011b (jednatel / majitel)",
                             "N\u011bkdo z IT odd\u011blen\u00ed",
                             "N\u011bkdo z veden\u00ed / managementu",
                             "Nem\u00e1me vhodnou osobu \u2014 pot\u0159ebujeme poradit"
                         ],
                         "warning": {"Nem\u00e1me vhodnou osobu \u2014 pot\u0159ebujeme poradit": "\ud83d\udca1 V r\u00e1mci AI governance dokumentace v\u00e1m navrhneme, jakou roli vytvo\u0159it a co by m\u011bla zahrnovat. Pro men\u0161\u00ed firmy sta\u010d\u00ed pov\u011b\u0159it jednu existuj\u00edc\u00ed osobu \u2014 nemus\u00edte vytv\u00e1\u0159et novou pozici."}},
                        {"key": "oversight_help_info", "label": "\u2705 Nevad\u00ed \u2014 **AIshield v\u00e1m v r\u00e1mci Compliance Kitu pom\u016f\u017ee definovat role a odpov\u011bdnosti v AI governance dokumentaci.** Navrhneme konkr\u00e9tn\u00ed osobu, jej\u00ed kompetence a eskala\u010dn\u00ed postup na m\u00edru va\u0161\u00ed firm\u011b.", "type": "info"},
                    ]
                },'''

new_followup_no = '''"followup_no": {
                    "fields": [
                        {"key": "oversight_warning", "label": "\u26a0\ufe0f \u010cl\u00e1nek 14 AI Act vy\u017eaduje lidsk\u00fd dohled nad vysoce rizikov\u00fdmi AI syst\u00e9my. I u syst\u00e9m\u016f s omezen\u00fdm rizikem (chatboty) je nutn\u00e9 m\u00edt odpov\u011bdnou osobu. Uve\u010fte pros\u00edm kontakt \u2014 pou\u017eijeme ho v compliance dokumentaci.", "type": "info"},
                        {"key": "oversight_no_person_name", "label": "Jm\u00e9no odpov\u011bdn\u00e9 osoby:", "type": "text"},
                        {"key": "oversight_no_person_email", "label": "E-mail odpov\u011bdn\u00e9 osoby:", "type": "text"},
                        {"key": "oversight_no_person_phone", "label": "Telefon odpov\u011bdn\u00e9 osoby:", "type": "text"},
                    ]
                },'''

content = content.replace(old_followup_no, new_followup_no)

# ─── Verify changes ───
changes = []
if "Nechci uv\u00e1d\u011bt" not in content:
    changes.append("1. Removed 'Nechci uvádět' from revenue")
else:
    changes.append("1. FAILED: 'Nechci uvádět' still present")

if "ai_transparency_docs" not in content:
    changes.append("2. Deleted ai_transparency_docs question")
else:
    changes.append("2. FAILED: ai_transparency_docs still present")

if "voliteln\u00e9" not in content:
    changes.append("3a. Removed 'volitelné' from field labels")
else:
    changes.append("3a. FAILED: 'volitelné' still present")

if "oversight_person_phone" in content:
    changes.append("3b. Added phone field to 'Ano' branch")
else:
    changes.append("3b. FAILED: phone field not added")

if "oversight_ok_info" not in content:
    changes.append("3c. Removed 'Výborně!' info")
else:
    changes.append("3c. FAILED: 'Výborně!' still present")

if "oversight_no_person_name" in content:
    changes.append("4. Rewrote 'Ne' branch with name/email/phone fields")
else:
    changes.append("4. FAILED: 'Ne' branch not rewritten")

with open(FILE, "w", encoding="utf-8") as f:
    f.write(content)

for c in changes:
    print(c)

print(f"\nDone. File size: {len(original)} → {len(content)} bytes")
