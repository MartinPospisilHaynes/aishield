#!/usr/bin/env python3
"""
BATCH 1 — Textové opravy dotazníku
===================================
P1:  Opravit datum čl. 50 (2025 → 2026) v Q12, Q13, Q14
P12: Zpřesnit Q08/Q36 nápovědy (hranice vyvíjím vs upravuji)
P13: Opravit Q38 scope_hint (misleading "občas = Ne")
"""

import re

FILE = "backend/api/questionnaire.py"

with open(FILE, "r", encoding="utf-8") as f:
    content = f.read()

original = content

# ──────────────────────────────────────────────
# P1: Opravit datum čl. 50  (2025 → 2026)
# Týká se Q12 (deepfake), Q13 (chatbot), Q14 (email)
# čl. 50 transparentnost platí od 2. srpna 2026, NE 2025
# ──────────────────────────────────────────────

# Q13 chatbot warning: "Tato povinnost platí od 2. srpna 2025."
content = content.replace(
    'Tato povinnost plat\u00ed od 2. srpna 2025.',
    'Tato povinnost plat\u00ed od 2. srpna 2026.'
)

# Q12 deepfake warning: "Od 2. srpna 2025 je podle čl. 50"
content = content.replace(
    'Od 2. srpna 2025 je podle \u010dl. 50',
    'Od 2. srpna 2026 je podle \u010dl. 50'
)

# Count replacements for P1
p1_count = original.count('2. srpna 2025') - content.count('2. srpna 2025')
print(f"P1: Opraveno {p1_count} výskytů data '2. srpna 2025' → '2. srpna 2026'")

# Verify no remaining wrong dates for čl. 50
remaining = content.count('2. srpna 2025')
print(f"    Zbývající výskyty '2. srpna 2025': {remaining} (mělo by být 0 pro čl. 50)")

# ──────────────────────────────────────────────
# P12: Zpřesnit Q08/Q36 nápovědy
# Q08 = jsme primární autor modelu
# Q36 = podstatně upravujeme existující systém
# ──────────────────────────────────────────────

# Q08 (develops_own_ai) — help_text
old_q08_help = (
    '"help_text": "P\u0159\u00edklady:\\n'
    '1) IT firma tr\u00e9nuje vlastn\u00ed ML model pro predikci popt\u00e1vky.\\n'
    '2) Startup vyv\u00edj\u00ed AI chatbota pro klienty.\\n'
    '3) E-shop integruje AI doporu\u010dovac\u00ed engine do sv\u00e9ho webu.",'
)
new_q08_help = (
    '"help_text": "Mysl\u00edme t\u00edm, \u017ee jste prim\u00e1rn\u00ed auto\u0159i AI syst\u00e9mu \u2014 navrhli jste architekturu, tr\u00e9nujete vlastn\u00ed model, nebo vyr\u00e1b\u00edte AI produkt.\\n\\n'
    'P\u0159\u00edklady ANO:\\n'
    '1) IT firma tr\u00e9nuje vlastn\u00ed ML model pro predikci popt\u00e1vky.\\n'
    '2) Startup vyv\u00edj\u00ed AI chatbota pro klienty.\\n'
    '3) E-shop vytv\u00e1\u0159\u00ed vlastn\u00ed AI doporu\u010dovac\u00ed engine.\\n\\n'
    'P\u0159\u00edklady NE (to je Q36):\\n'
    '1) Pou\u017e\u00edv\u00e1te ChatGPT API a p\u0159izp\u016fsobujete si prompty.\\n'
    '2) Fine-tunujete ciz\u00ed model na sv\u00fdch datech.\\n'
    '3) P\u0159ebudov\u00e1v\u00e1te zakoupen\u00fd n\u00e1stroj na jin\u00fd \u00fa\u010del.",'
)

if old_q08_help in content:
    content = content.replace(old_q08_help, new_q08_help, 1)
    print("P12a: Q08 help_text upraven (hranice vyvíjím vs upravuji)")
else:
    print("P12a: CHYBA — Q08 help_text nenalezen!")

# Q36 (modifies_ai_purpose) — help_text
old_q36_help = (
    '"help_text": "P\u0159\u00edklady:\\n'
    '1) P\u0159etr\u00e9nov\u00e1n\u00ed ChatGPT API na vlastn\u00edch datech pro specifick\u00fd \u00fa\u010del.\\n'
    '2) Vlastn\u00ed fine-tuning jazykov\u00e9ho modelu.\\n'
    '3) Zm\u011bna \u00fa\u010delu AI n\u00e1stroje (nap\u0159. z marketingu na HR screening).",'
)
new_q36_help = (
    '"help_text": "Sem pat\u0159\u00ed p\u0159\u00edpady, kdy podstatn\u011b m\u011bn\u00edte existuj\u00edc\u00ed AI syst\u00e9m t\u0159et\u00ed strany \u2014 fine-tuning, zm\u011bna \u00fa\u010delu, p\u0159etr\u00e9nov\u00e1n\u00ed. Dle \u010dl. 25 AI Act se t\u00edm m\u016f\u017eete st\u00e1t poskytovatelem.\\n\\n'
    'P\u0159\u00edklady ANO:\\n'
    '1) Fine-tunujete GPT/Claude na vlastn\u00edch datech pro specifick\u00fd \u00fa\u010del.\\n'
    '2) P\u0159etr\u00e9nov\u00e1v\u00e1te jazykov\u00fd model pro \u00fapln\u011b jin\u00e9 pou\u017eit\u00ed.\\n'
    '3) M\u011bn\u00edte \u00fa\u010del AI n\u00e1stroje (nap\u0159. z marketingu na HR screening).\\n\\n'
    'P\u0159\u00edklady NE:\\n'
    '1) Pou\u017e\u00edv\u00e1te ChatGPT/Claude tak, jak je, bez \u00faprav.\\n'
    '2) Jen p\u00ed\u0161ete vlastn\u00ed prompty (to nen\u00ed \u00faprava syst\u00e9mu).\\n'
    '3) Pou\u017e\u00edv\u00e1te RAG bez zm\u011bny z\u00e1kladn\u00edho modelu.",'
)

if old_q36_help in content:
    content = content.replace(old_q36_help, new_q36_help, 1)
    print("P12b: Q36 help_text upraven (fine-tuning vs běžné použití)")
else:
    print("P12b: CHYBA — Q36 help_text nenalezen!")

# ──────────────────────────────────────────────
# P13: Opravit Q38 (monitors_ai_outputs) scope_hint
# Aktuální: "Pokud AI nástroje pouze občas používáte ... odpovězte Ne"
# Problém: falešný dojem, že občasné použití = žádná povinnost
# ──────────────────────────────────────────────

old_q38_scope = (
    '"scope_hint": "Tato ot\u00e1zka se t\u00fdk\u00e1 firem, kter\u00e9 aktivn\u011b provozuj\u00ed AI syst\u00e9my '
    'v kontaktu s klienty nebo pro intern\u00ed rozhodov\u00e1n\u00ed (chatbot, AI doporu\u010den\u00ed, automatizace). '
    'Pokud AI n\u00e1stroje pouze ob\u010das pou\u017e\u00edv\u00e1te (nap\u0159. ChatGPT pro osobn\u00ed pot\u0159ebu), '
    'odpov\u011bzte \\"Ne\\".",'
)
new_q38_scope = (
    '"scope_hint": "Tato ot\u00e1zka se t\u00fdk\u00e1 v\u0161ech AI syst\u00e9m\u016f, kter\u00e9 ve firm\u011b pou\u017e\u00edv\u00e1te. '
    'Odpov\u011bzte ANO, pokud n\u011bkdo pravideln\u011b kontroluje spr\u00e1vnost v\u00fdstup\u016f AI '
    '(nap\u0159. \u010dte odpov\u011bdi chatbota, ov\u011b\u0159uje AI doporu\u010den\u00ed). '
    'Odpov\u011bzte NE, pokud AI b\u011b\u017e\u00ed bez jak\u00e9koliv kontroly kvality v\u00fdstup\u016f.",'
)

if old_q38_scope in content:
    content = content.replace(old_q38_scope, new_q38_scope, 1)
    print("P13: Q38 scope_hint opraven (odstraněno misleading 'občas = Ne')")
else:
    print("P13: CHYBA — Q38 scope_hint nenalezen!")

# ──────────────────────────────────────────────
# Uložit a potvrdit
# ──────────────────────────────────────────────

if content != original:
    with open(FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n✅ BATCH 1 HOTOV — soubor uložen ({FILE})")
else:
    print("\n❌ Žádné změny neprovedeny!")
