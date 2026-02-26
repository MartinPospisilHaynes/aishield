#!/usr/bin/env python3
"""
Patch 2: Add severity, recommendations, and _get_recommendation entries
for the 7 new question keys.
"""

filepath = "/opt/aishield/backend/api/questionnaire.py"

with open(filepath, "r") as f:
    content = f.read()

changes = 0

# ════════════════════════════════════════════
# 1. _NEVIM_SEVERITY — add new prohibited + education + cybersecurity + employee
# ════════════════════════════════════════════

marker_sev = "'uses_emotion_recognition':     {'severity': 'critical', 'color': 'red',    'label': 'Kritické'},"

if marker_sev in content:
    new_sev = """'uses_emotion_recognition':     {'severity': 'critical', 'color': 'red',    'label': 'Kritické'},
    'exploits_vulnerable_groups':   {'severity': 'critical', 'color': 'red',    'label': 'Kritické'},
    'uses_criminal_risk_assessment':{'severity': 'critical', 'color': 'red',    'label': 'Kritické'},
    'uses_untargeted_facial_scraping':{'severity': 'critical','color': 'red',   'label': 'Kritické'},
    'uses_biometric_categorization':{'severity': 'critical', 'color': 'red',    'label': 'Kritické'},"""
    content = content.replace(marker_sev, new_sev)
    changes += 1
    print("✅ 1/4 Added prohibited severity entries")
else:
    print("❌ 1/4 FAILED: _NEVIM_SEVERITY prohibited marker not found")

# Add education + employee + cybersecurity severity after uses_ai_insurance
marker_sev2 = "'uses_ai_insurance':            {'severity': 'high',     'color': 'orange', 'label': 'Vysoké riziko'},"

if marker_sev2 in content:
    new_sev2 = """'uses_ai_insurance':            {'severity': 'high',     'color': 'orange', 'label': 'Vysoké riziko'},
    'uses_ai_education':            {'severity': 'high',     'color': 'orange', 'label': 'Vysoké riziko'},
    'informs_employees_about_ai':   {'severity': 'limited',  'color': 'yellow', 'label': 'Omezené riziko'},
    'has_cybersecurity_measures':   {'severity': 'limited',  'color': 'yellow', 'label': 'Omezené riziko'},"""
    content = content.replace(marker_sev2, new_sev2)
    changes += 1
    print("✅ 2/4 Added education/employee/cyber severity entries")
else:
    print("❌ 2/4 FAILED: _NEVIM_SEVERITY education marker not found")

# ════════════════════════════════════════════
# 2. _NO_ANSWER_RECOMMENDATIONS — add entries for new compliance-relevant questions
# ════════════════════════════════════════════

marker_no = "    'has_ai_bias_check': {\n        'risk_level': 'limited',"

if marker_no in content:
    new_no = """    'informs_employees_about_ai': {
        'risk_level': 'limited',
        'priority': 'vysoká',
        'recommendation': (
            'Neinformujete zaměstnance o AI systémech na pracovišti. '
            'Článek 26 odst. 7 AI Act vyžaduje, abyste zaměstnance předem '
            'informovali o tom, že budou vystaveni AI systémům. '
            'AIshield vám dodá profesionálně zpracované oznámení pro zaměstnance '
            'a prezentaci k představení AI systémů na pracovišti.'
        ),
    },
    'has_cybersecurity_measures': {
        'risk_level': 'limited',
        'priority': 'střední',
        'recommendation': (
            'Nemáte opatření kybernetické bezpečnosti pro AI systémy. '
            'Článek 15 AI Act vyžaduje ochranu proti manipulaci s daty '
            '(data poisoning), manipulaci se vstupy (prompt injection) '
            'a neoprávněnému přístupu. '
            'V rámci Compliance Kitu vám vygenerujeme bezpečnostní checklist.'
        ),
    },
    'has_ai_bias_check': {
        'risk_level': 'limited',"""
    content = content.replace(marker_no, new_no)
    changes += 1
    print("✅ 3/4 Added _NO_ANSWER_RECOMMENDATIONS entries")
else:
    print("❌ 3/4 FAILED: _NO_ANSWER_RECOMMENDATIONS marker not found")

# ════════════════════════════════════════════
# 3. _get_recommendation — add new keys
# ════════════════════════════════════════════

marker_rec = '        "uses_gpai_api": "Integrujete LLM API'

if marker_rec in content:
    new_rec = '''        # Nové zakázané praktiky
        "exploits_vulnerable_groups": "ZAKÁZANÝ SYSTÉM! Zneužívání zranitelnosti skupin (věk, postižení, sociální/ekonomická situace) je dle čl. 5 odst. 1 písm. b) AI Act zakázáno. Pokuta až 35 mil. EUR.",
        "uses_criminal_risk_assessment": "ZAKÁZANÝ SYSTÉM! Predikce kriminality na základě profilování je dle čl. 5 odst. 1 písm. d) AI Act zakázána. Ukončete provoz okamžitě.",
        "uses_untargeted_facial_scraping": "ZAKÁZANÝ SYSTÉM! Nerozlišující stahování obličejů z internetu/CCTV pro databáze je dle čl. 5 odst. 1 písm. e) AI Act zakázáno. Pokuta až 35 mil. EUR.",
        "uses_biometric_categorization": "ZAKÁZANÝ SYSTÉM! Biometrická kategorizace pro odvozování rasy, náboženství nebo sexuální orientace je dle čl. 5 odst. 1 písm. g) AI Act zakázána.",
        # Vzdělávání
        "uses_ai_education": f"VYSOCE RIZIKOVÝ systém! AI ve vzdělávání je regulováno Přílohou III bod 3 AI Act. Proveďte posouzení shody, zajistěte lidský dohled a transparentnost vůči studentům.",
        # Zaměstnanci
        "informs_employees_about_ai": "Informujte zaměstnance předem o nasazení AI na pracovišti — čl. 26 odst. 7 AI Act. AIshield dodá vzorové oznámení.",
        # Kybernetická bezpečnost
        "has_cybersecurity_measures": "Zajistěte kybernetickou bezpečnost AI systémů — čl. 15 AI Act vyžaduje ochranu proti data poisoning, prompt injection a neoprávněnému přístupu.",
        "uses_gpai_api": "Integrujete LLM API'''
    content = content.replace(marker_rec, new_rec)
    changes += 1
    print("✅ 4/4 Added _get_recommendation entries")
else:
    print("❌ 4/4 FAILED: _get_recommendation marker not found")

# ════════════════════════════════════════════
# Write result
# ════════════════════════════════════════════

with open(filepath, "w") as f:
    f.write(content)

print(f"\nChanges: {changes}/4")
print(f"File size: {len(content)} chars")
