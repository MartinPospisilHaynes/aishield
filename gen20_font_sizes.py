#!/usr/bin/env python3
"""
Gen20 patch: Reduce all font sizes by ~1pt proportionally in pdf_renderer.py
"""

FILE = "/opt/aishield/backend/documents/pdf_renderer.py"

with open(FILE, "r") as f:
    code = f.read()

# Ordered replacements (most specific first to avoid double-replacing)
# Format: (old, new, description)
replacements = [
    # Title page inline styles (most specific - include context)
    ('font-size:28pt; border:none;', 'font-size:26pt; border:none;', 'title h1 28→26'),
    ('font-size:14pt; color:#475569;', 'font-size:13pt; color:#475569;', 'title subtitle 14→13'),
    ('border:none; font-size:11pt;', 'border:none; font-size:10pt;', 'title table 11→10'),
    ('font-size:11pt; line-height:2.2;', 'font-size:10pt; line-height:2.2;', 'TOC 11→10'),
    ('font-size:11pt; color:#7c3aed;', 'font-size:10pt; color:#7c3aed;', 'title brand 11→10'),
    
    # CSS class definitions (body and headings)
    # body font-size
    ('    font-size: 10pt;\n    line-height: 1.5;\n    color: #1e293b;',
     '    font-size: 9pt;\n    line-height: 1.5;\n    color: #1e293b;',
     'body 10→9'),
    
    # h1 font-size
    ('    font-size: 20pt;\n    font-weight: 700;\n    color: #0f172a;',
     '    font-size: 18pt;\n    font-weight: 700;\n    color: #0f172a;',
     'h1 20→18'),
    
    # h2 font-size
    ('    font-size: 13pt;\n    font-weight: 600;\n    color: #1e293b;',
     '    font-size: 12pt;\n    font-weight: 600;\n    color: #1e293b;',
     'h2 13→12'),
    
    # h3 font-size
    ('    font-size: 11pt;\n    font-weight: 600;\n    color: #334155;',
     '    font-size: 10pt;\n    font-weight: 600;\n    color: #334155;',
     'h3 11→10'),
    
    # h4 font-size
    ('    font-size: 10pt;\n    font-weight: 600;\n    color: #475569;',
     '    font-size: 9pt;\n    font-weight: 600;\n    color: #475569;',
     'h4 10→9'),
    
    # table font-size
    ('    margin: 8pt 0;\n    font-size: 9pt;',
     '    margin: 8pt 0;\n    font-size: 8pt;',
     'table 9→8'),
    
    # badge font-size
    ('    font-size: 8.5pt;\n    font-weight: 600;',
     '    font-size: 7.5pt;\n    font-weight: 600;',
     'badge 8.5→7.5'),
    
    # sig-field font-size
    ('    font-size: 9pt;\n    color: #64748b;\n    text-align: center;',
     '    font-size: 8pt;\n    color: #64748b;\n    text-align: center;',
     'sig-field 9→8'),
    
    # metric-value
    ('    font-size: 24pt;\n    font-weight: 700;\n    color: #7c3aed;',
     '    font-size: 22pt;\n    font-weight: 700;\n    color: #7c3aed;',
     'metric-value 24→22'),
    
    # metric-label
    ('    font-size: 8pt;\n    color: #64748b;\n    text-transform: uppercase;',
     '    font-size: 7pt;\n    color: #64748b;\n    text-transform: uppercase;',
     'metric-label 8→7'),
    
    # doc-footer
    ('    font-size: 8pt;\n    color: #94a3b8;\n    text-align: center;',
     '    font-size: 7pt;\n    color: #94a3b8;\n    text-align: center;',
     'doc-footer 8→7'),
]

changes = 0
for old, new, desc in replacements:
    if old in code:
        code = code.replace(old, new, 1)
        changes += 1
        print(f"  OK: {desc}")
    else:
        print(f"  SKIP: {desc} (not found)")

# Also reduce line-height slightly for tighter layout
old_lh = '    line-height: 1.5;\n    color: #1e293b;'
new_lh = '    line-height: 1.45;\n    color: #1e293b;'
if old_lh in code:
    code = code.replace(old_lh, new_lh, 1)
    changes += 1
    print("  OK: line-height 1.5→1.45")

with open(FILE, "w") as f:
    f.write(code)

print(f"\nTotal: {changes} changes in pdf_renderer.py")
