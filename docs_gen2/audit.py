#!/usr/bin/env python3
"""Audit all generated documents for N/A, none, doplňte and other placeholders."""
import PyPDF2
import os, re, glob

PATTERNS = [
    (r'\bN/A\b', 'N/A'),
    (r'\bnone\b', 'none (lowercase)'),
    (r'\bNone\b', 'None'),
    (r'\bNONE\b', 'NONE'),
    (r'[Dd]opln[ěi]te', 'doplňte/doplnite'),
    (r'\[.*?\]', 'placeholder [...]'),
    (r'XXX|xxx', 'XXX placeholder'),
    (r'TODO|FIXME', 'TODO/FIXME'),
    (r'Neznámá firma', 'Neznámá firma'),
    (r'neuvedeno', 'neuvedeno'),
    (r'není k dispozici', 'není k dispozici'),
    (r'nezadáno', 'nezadáno'),
    (r'nedefinováno', 'nedefinováno'),
    (r'\bchybí\b', 'chybí'),
    (r'nespecifikováno', 'nespecifikováno'),
    (r'nebylo zjištěno', 'nebylo zjištěno'),
    (r'není známo', 'není známo'),
]

os.chdir(os.path.dirname(os.path.abspath(__file__)))

for pdf_file in sorted(glob.glob("*.pdf")):
    reader = PyPDF2.PdfReader(pdf_file)
    full_text = ""
    for page in reader.pages:
        t = page.extract_text()
        if t:
            full_text += t + "\n"

    txt_file = pdf_file.replace('.pdf', '.txt')
    with open(txt_file, 'w') as f:
        f.write(full_text)

    print(f"\n{'='*70}")
    print(f"  {pdf_file} ({len(full_text)} chars, {len(reader.pages)} pages)")
    print(f"{'='*70}")

    findings = []
    lines = full_text.split('\n')
    for i, line in enumerate(lines, 1):
        for pattern, label in PATTERNS:
            matches = list(re.finditer(pattern, line))
            for m in matches:
                context = line.strip()
                if len(context) > 120:
                    start = max(0, m.start() - 40)
                    end = min(len(line), m.end() + 40)
                    context = "..." + line[start:end].strip() + "..."
                findings.append((label, i, context))

    if findings:
        for label, line_no, ctx in findings:
            print(f"  [{label}] r.{line_no}: {ctx}")
    else:
        print(f"  OK - zadne problemy")

# HTML
print(f"\n{'='*70}")
print(f"  12_transparency_page_gen2.html")
print(f"{'='*70}")
with open("12_transparency_page_gen2.html", 'r') as f:
    html_text = f.read()

html_findings = []
for pattern, label in PATTERNS:
    matches = list(re.finditer(pattern, html_text))
    for m in matches:
        start = max(0, m.start() - 40)
        end = min(len(html_text), m.end() + 40)
        ctx = html_text[start:end].replace('\n', ' ').strip()
        html_findings.append((label, ctx))

if html_findings:
    for label, ctx in html_findings:
        print(f"  [{label}] : ...{ctx}...")
else:
    print(f"  OK - zadne problemy")
