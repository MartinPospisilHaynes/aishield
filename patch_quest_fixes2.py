#!/usr/bin/env python3
"""
Second pass patch — fixes remaining issues:
1. oversight_person_email: remove "(volitelné — pro eskalační plán)"
2. Add phone field after email
3. Rewrite followup_no for has_oversight_person (line-based approach)
4. Clean up ai_transparency_docs references in other maps
"""
import os

FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "api", "questionnaire.py")

with open(FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()

content = "".join(lines)
original_len = len(content)

# 1. Fix email label — replace exact line
for i, line in enumerate(lines):
    if "oversight_person_email" in line and "voliteln" in line:
        lines[i] = line.replace(
            'E-mail odpovědné osoby (volitelné — pro eskalační plán):',
            'E-mail odpovědné osoby:'
        )
        # Also try with em-dash variant
        lines[i] = lines[i].replace(
            'E-mail odpovědné osoby (volitelné \u2014 pro eskalační plán):',
            'E-mail odpovědné osoby:'
        )
        # Add phone field after this line
        indent = line[:len(line) - len(line.lstrip())]
        phone_line = indent + '{"key": "oversight_person_phone", "label": "Telefon odpovědné osoby:", "type": "text"},\n'
        lines.insert(i + 1, phone_line)
        print(f"  Fixed email label at line {i+1}, added phone at line {i+2}")
        break

# 2. Rewrite followup_no — find start and end
content = "".join(lines)
start_marker = '"followup_no": {\n                    "fields": [\n                        {"key": "oversight_warning"'
end_marker = '                    ]\n                },\n                "risk_hint": "high",\n                "ai_act_article": "čl. 14'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker, start_idx if start_idx >= 0 else 0)

if start_idx >= 0 and end_idx >= 0:
    new_followup_no = '''"followup_no": {
                    "fields": [
                        {"key": "oversight_warning", "label": "⚠️ Článek 14 AI Act vyžaduje lidský dohled nad AI systémy. Musíte určit odpovědnou osobu. Uveďte prosím její kontakt — použijeme ho v compliance dokumentaci.", "type": "info"},
                        {"key": "oversight_no_person_name", "label": "Jméno odpovědné osoby:", "type": "text"},
                        {"key": "oversight_no_person_email", "label": "E-mail odpovědné osoby:", "type": "text"},
                        {"key": "oversight_no_person_phone", "label": "Telefon odpovědné osoby:", "type": "text"},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 14'''
    content = content[:start_idx] + new_followup_no + content[end_idx + len(end_marker):]
    print("  Rewrote followup_no branch")
else:
    print(f"  FAILED: Could not find followup_no markers (start={start_idx}, end={end_idx})")
    # Debug: show nearby text
    if start_idx == -1:
        # Try to find a shorter marker
        idx = content.find('"followup_no"')
        if idx >= 0:
            print(f"  Found 'followup_no' at position {idx}")
            print(f"  Context: {repr(content[idx:idx+200])}")

# 3. Clean up ai_transparency_docs references in other maps (non-question data)
for key in ['ai_transparency_docs']:
    # Remove from any dict/list by line
    new_lines = content.split('\n')
    cleaned = []
    skip_until_brace = False
    i = 0
    while i < len(new_lines):
        line = new_lines[i]
        if f"'{key}'" in line or f'"{key}"' in line:
            # Skip this line and check if it's a multi-line block
            if '{' in line and '}' not in line:
                # Multi-line — skip until closing
                depth = line.count('{') - line.count('}')
                i += 1
                while i < len(new_lines) and depth > 0:
                    depth += new_lines[i].count('{') - new_lines[i].count('}')
                    i += 1
                continue
            elif '[' in line and ']' not in line:
                depth = line.count('[') - line.count(']')
                i += 1
                while i < len(new_lines) and depth > 0:
                    depth += new_lines[i].count('[') - new_lines[i].count(']')
                    i += 1
                continue
            else:
                # Single-line — skip
                i += 1
                continue
        cleaned.append(line)
        i += 1
    content = '\n'.join(cleaned)
    if key not in content:
        print(f"  Cleaned all '{key}' references")
    else:
        print(f"  Warning: '{key}' still found in file")

with open(FILE, "w", encoding="utf-8") as f:
    f.write(content)

print(f"\nDone. File size: {original_len} → {len(content)} bytes")
