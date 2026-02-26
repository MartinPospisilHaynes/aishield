"""
Gen18 Patch — 3 opravy:
1. PPTX: parsovani tabulek + auto-skalovani fontu
2. M1: prezencni listina v training_outline
3. LLM Engine: fix extract_html_content pro transparency_page
"""

import re

# ================================================================
# PATCH 1: PPTX GENERATOR — table parsing + font auto-scale
# ================================================================

PPTX_FILE = 'backend/documents/pptx_generator.py'

with open(PPTX_FILE, 'r') as f:
    pptx = f.read()

# 1a) Add table parsing to _SlideExtractor.__init__
old_init = '        self._in_p = False\n        self._in_speaker_notes = False'
new_init = '        self._in_p = False\n        self._in_td = False\n        self._in_th = False\n        self._in_tr = False\n        self._row_cells: list[str] = []\n        self._in_speaker_notes = False'
assert old_init in pptx, 'PPTX init patch target not found'
pptx = pptx.replace(old_init, new_init, 1)

# 1b) Add table tag handling in handle_starttag
old_starttag = '        elif tag == "li":\n            self._in_li = True\n            self._text_buf = []\n        elif tag == "p" and self._current_slide is not None:\n            self._in_p = True\n            self._text_buf = []'
new_starttag = '        elif tag == "li":\n            self._in_li = True\n            self._text_buf = []\n        elif tag == "tr":\n            self._in_tr = True\n            self._row_cells = []\n        elif tag in ("td", "th"):\n            self._in_td = True\n            self._text_buf = []\n        elif tag == "p" and self._current_slide is not None:\n            self._in_p = True\n            self._text_buf = []'
assert old_starttag in pptx, 'PPTX starttag patch target not found'
pptx = pptx.replace(old_starttag, new_starttag, 1)

# 1c) Add table tag handling in handle_endtag
old_endtag = '        elif tag == "p" and self._in_p:\n            self._in_p = False\n            text = "".join(self._text_buf).strip()\n            if text and self._current_slide:\n                self._current_slide["paragraphs"].append(text)\n        self._current_tag = ""'
new_endtag = '        elif tag in ("td", "th") and self._in_td:\n            self._in_td = False\n            cell_text = "".join(self._text_buf).strip()\n            if cell_text:\n                self._row_cells.append(cell_text)\n        elif tag == "tr" and self._in_tr:\n            self._in_tr = False\n            if self._row_cells and self._current_slide:\n                row_text = " | ".join(self._row_cells)\n                self._current_slide["bullets"].append(row_text)\n            self._row_cells = []\n        elif tag == "p" and self._in_p:\n            self._in_p = False\n            text = "".join(self._text_buf).strip()\n            if text and self._current_slide:\n                self._current_slide["paragraphs"].append(text)\n        self._current_tag = ""'
assert old_endtag in pptx, 'PPTX endtag patch target not found'
pptx = pptx.replace(old_endtag, new_endtag, 1)

# 1d) Add td/th to handle_data collection
old_data = '        elif self._in_h1 or self._in_h2 or self._in_li or self._in_p:\n            self._text_buf.append(data)'
new_data = '        elif self._in_h1 or self._in_h2 or self._in_li or self._in_p or self._in_td:\n            self._text_buf.append(data)'
assert old_data in pptx, 'PPTX handle_data patch target not found'
pptx = pptx.replace(old_data, new_data, 1)

# 1e) Auto-scale font in _create_content_slide based on content length
old_cs = '''def _create_content_slide(prs, title, bullets, client_info=None, speaker_notes=""):
    """Standardn'''
assert old_cs in pptx, 'PPTX _create_content_slide start not found'

old_bullet_call = '''    _add_bullet_list(
        slide,
        left=Inches(0.8), top=Inches(2.2),
        width=Inches(11), height=Inches(4.5),
        items=bullets,
        font_size=18,
    )
    _add_client_footer(slide, client_info)

    # Speaker notes'''
new_bullet_call = '''    # Auto-scale font based on content volume
    total_chars = sum(len(b) for b in bullets)
    num_bullets = len(bullets)
    if total_chars > 1500 or num_bullets > 10:
        font_size = 12
    elif total_chars > 1000 or num_bullets > 7:
        font_size = 14
    elif total_chars > 600 or num_bullets > 5:
        font_size = 16
    else:
        font_size = 18

    _add_bullet_list(
        slide,
        left=Inches(0.8), top=Inches(2.2),
        width=Inches(11), height=Inches(4.5),
        items=bullets,
        font_size=font_size,
    )
    _add_client_footer(slide, client_info)

    # Speaker notes'''
assert old_bullet_call in pptx, 'PPTX bullet_call patch target not found'
pptx = pptx.replace(old_bullet_call, new_bullet_call, 1)

with open(PPTX_FILE, 'w') as f:
    f.write(pptx)
print('[OK] PPTX generator patched: table parsing + font auto-scale')


# ================================================================
# PATCH 2: M1 GENERATOR — prezencni listina v training_outline
# ================================================================

M1_FILE = 'backend/documents/m1_generator.py'

with open(M1_FILE, 'r') as f:
    m1 = f.read()

old_training = '''<h2>9. Kontroln'''
assert old_training in m1, 'M1 training section 9 not found'

old_end = '''DULEZITE:
- NEPIS o testech'''
# Try the actual text with diacritics
old_end2 = """- Odvětvově specifické příklady automation bias
\"\"\""""

assert old_end2 in m1, 'M1 training end marker not found'

new_end2 = """- Odvětvově specifické příklady automation bias

<h2>10. Prezenční listina školení</h2>
- Na konci dokumentu POVINNĚ přidej prezenční listinu pro evidenci účasti.
- Zjisti počet zaměstnanců z kontextu firmy (hledej velikost firmy / company size).
- Vytvoř HTML <table> s PŘESNĚ tolika řádky, kolik má firma zaměstnanců.
  Pokud je uvedeno „250+" nebo rozsah, použij horní hranici (např. 250 pro „250+", 100 pro „51-100").
  Pokud počet zaměstnanců nelze zjistit, vytvoř 30 řádků.
- Sloupce tabulky:
  | č. | Jméno | Příjmení | Podpis |
- Každý řádek očísluj (1, 2, 3, ...).
- Sloupce Jméno, Příjmení a Podpis nech PRÁZDNÉ (klient si je vyplní ručně).
- Buňky pro podpis udělej široké (min 150px) — lidé tam budou podepisovat.
- Nad tabulku přidej hlavičku:
  Název školení: Školení AI gramotnosti dle čl. 4 AI Act
  Datum konání: _______________
  Školitel: _______________
  Místo konání: _______________
- Pod tabulku přidej řádek pro podpis školitele:
  Podpis školitele: _______________  Datum: _______________
\"\"\""""

m1 = m1.replace(old_end2, new_end2, 1)

with open(M1_FILE, 'w') as f:
    f.write(m1)
print('[OK] M1 generator patched: prezencni listina added to training_outline')


# ================================================================
# PATCH 3: LLM ENGINE — fix extract_html_content for full HTML
# ================================================================

LLM_FILE = 'backend/documents/llm_engine.py'

with open(LLM_FILE, 'r') as f:
    llm = f.read()

old_extract = '''    if not text:
        return ""

    # Zkus JSON'''
new_extract = '''    if not text:
        return ""

    # Detekce kompletni HTML stranky — bypass JSON parsovani
    # (Transparency page obsahuje JSON-LD <script> bloky, ktere
    #  parse_json() mylne interpretuje jako JSON odpoved LLM)
    _stripped = text.strip()
    _stripped = re.sub(r"^```(?:html)?\\s*\\n?", "", _stripped)
    if (_stripped.startswith("<!--") or
        _stripped.lower().startswith("<!doctype") or
        _stripped.lower().startswith("<html")):
        logger.info("[extract_html] Detekovana kompletni HTML stranka — bypass JSON parsing")
        _stripped = re.sub(r"\\n?```\\s*$", "", _stripped)
        return _stripped.strip()

    # Zkus JSON'''
assert old_extract in llm, 'LLM extract_html_content patch target not found'
llm = llm.replace(old_extract, new_extract, 1)

with open(LLM_FILE, 'w') as f:
    f.write(llm)
print('[OK] LLM engine patched: extract_html_content bypass for full HTML pages')

print()
print('========================================')
print('VSECHNY 3 PATCHE USPESNE APLIKOVANY')
print('========================================')
