import os, re, sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Check HTML for "none riziko"
html_files = [f for f in os.listdir('.') if f.endswith('.html')]
for html_file in html_files:
    with open(html_file, 'r') as f:
        html = f.read()
    none_matches = [(i+1, line.strip()[:100]) for i, line in enumerate(html.split('\n')) if 'none' in line.lower() and 'riziko' in line.lower()]
    print(f"=== {html_file} ===")
    print(f"  'none riziko' matches: {len(none_matches)}")
    for ln, txt in none_matches[:5]:
        print(f"    L{ln}: {txt}")

# Check PDFs for None/N/A/doplňte
try:
    from PyPDF2 import PdfReader
except ImportError:
    os.system('pip3 install PyPDF2 -q')
    from PyPDF2 import PdfReader

patterns = [
    (r'\bNone\b', 'None'),
    (r'\bN/A\b', 'N/A'),
    (r'(?i)doplňte|vyplňte', 'Doplňte/Vyplňte'),
    (r'none riziko', 'none riziko'),
]

pdf_files = sorted([f for f in os.listdir('.') if f.endswith('.pdf')])
for pf in pdf_files:
    reader = PdfReader(pf)
    text = '\n'.join(page.extract_text() or '' for page in reader.pages)
    issues = []
    for pat, label in patterns:
        matches = re.findall(pat, text)
        if matches:
            issues.append(f"{len(matches)}x {label}")
    short = pf.replace('_20260224_210627', '')
    if issues:
        print(f"\n=== {short} === ISSUES: {', '.join(issues)}")
        for pat, label in patterns:
            for m in re.finditer(pat, text):
                start = max(0, m.start()-40)
                end = min(len(text), m.end()+40)
                ctx = text[start:end].replace('\n', ' ')
                print(f"  [{label}] ...{ctx}...")
    else:
        print(f"  {short}: CLEAN")
