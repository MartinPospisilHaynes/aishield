#!/usr/bin/env python3
"""
Patch questionnaire.py: Add 8 missing AI Act questions.
Run on server: python3 /opt/aishield/patch_questionnaire.py
"""

filepath = "/opt/aishield/backend/api/questionnaire.py"

with open(filepath, "r") as f:
    content = f.read()

changes_made = 0

# ═══════════════════════════════════════════════════
# 1. ADD 4 NEW PROHIBITED PRACTICE QUESTIONS
# ═══════════════════════════════════════════════════

# Marker: end of uses_realtime_biometric question (last question in prohibited_systems)
marker_prohibited = 'jinde vysoce riziková (Příloha III)",\n            },\n        ],\n    },'

if marker_prohibited in content:
    new_questions_prohibited = '''jinde vysoce riziková (Příloha III)",
            },
            {
                "key": "exploits_vulnerable_groups",
                "text": "Používáte AI k cílení na zranitelné skupiny způsobem, který by mohl poškodit jejich zájmy?",
                "type": "yes_no_unknown",
                "help_text": "Čl. 5 odst. 1 písm. b) zakazuje AI systémy, které zneužívají zranitelnosti osob kvůli věku, postižení nebo sociální/ekonomické situaci k podstatnému narušení jejich chování.\\n\\nPříklady ZAKÁZANÉHO použití:\\n1) E-shop cíleně nabízí předražené produkty seniorům, o nichž AI ví, že špatně rozumí cenám.\\n2) AI reklama cílí na zadlužené osoby s nabídkou nevýhodných půjček.\\n3) Aplikace zneužívá AI k manipulaci dětí k nákupům.\\n\\nPříklady POVOLENÉ (NENÍ porušení):\\n1) Běžná personalizace e-shopu.\\n2) Cenové akce pro seniory (zvýhodnění, ne znevýhodnění).\\n3) Standardní cílení reklamy dle zájmů.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "vulnerable_exploitation_warning", "label": "\\ud83d\\udeab ZAKÁZANÝ SYSTÉM — Zneužívání zranitelnosti skupin (věk, postižení, sociální/ekonomická situace) pomocí AI je výslovně zakázáno čl. 5 odst. 1 písm. b) AI Act. Pokuta až 35 milionů EUR nebo 7 % celosvětového obratu.", "type": "info"},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 5 odst. 1 písm. b) — zákaz zneužívání zranitelnosti",
            },
            {
                "key": "uses_criminal_risk_assessment",
                "text": "Používáte AI k predikci rizika spáchání trestného činu na základě profilování?",
                "type": "yes_no_unknown",
                "help_text": "Čl. 5 odst. 1 písm. d) zakazuje AI systémy pro posuzování rizika, že fyzická osoba spáchá trestný čin, založené výhradně na profilování nebo posuzování osobnostních rysů.\\n\\nPříklady ZAKÁZANÉHO použití:\\n1) AI vytváří ‚rizikový profil' zaměstnanců z hlediska možné krádeže.\\n2) Bezpečnostní systém predikuje ‚podezřelé chování' zákazníků na základě vzhledu.\\n3) AI hodnotí pravděpodobnost podvodu na základě osobnostního profilu (ne transakčních dat).\\n\\nPříklady POVOLENÉ (NENÍ porušení):\\n1) Detekce podvodných transakcí na základě vzorců chování.\\n2) Standardní AML/KYC kontroly.\\n3) Bezpečnostní kamery bez AI predikce.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "criminal_assessment_warning", "label": "\\ud83d\\udeab ZAKÁZANÝ SYSTÉM — Predikce kriminality na základě profilování je zakázána čl. 5 odst. 1 písm. d) AI Act. Pokuta až 35 milionů EUR.", "type": "info"},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 5 odst. 1 písm. d) — zákaz predikce kriminality z profilování",
            },
            {
                "key": "uses_untargeted_facial_scraping",
                "text": "Vytváříte nebo používáte databáze obličejů z nerozlišujícího stahování z internetu nebo kamerových záznamů?",
                "type": "yes_no_unknown",
                "help_text": "Čl. 5 odst. 1 písm. e) zakazuje vytváření nebo rozšiřování databází pro rozpoznávání obličejů prostřednictvím nerozlišujícího stahování obličejových snímků z internetu nebo kamerových záznamů.\\n\\nPříklady ZAKÁZANÉHO použití:\\n1) Stahování fotografií z sociálních sítí pro trénování rozpoznávání obličejů.\\n2) Použití služeb typu Clearview AI.\\n3) Budování databáze obličejů z CCTV záznamů bez souhlasu.\\n\\nPříklady POVOLENÉ (NENÍ porušení):\\n1) Docházkový systém na otisk prstu (se souhlasem zaměstnanců).\\n2) Kamerový systém bez AI rozpoznávání.\\n3) Fotobanka s licencovanými snímky.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "facial_scraping_warning", "label": "\\ud83d\\udeab ZAKÁZANÝ SYSTÉM — Nerozlišující stahování obličejových snímků z internetu nebo CCTV pro databáze je zakázáno čl. 5 odst. 1 písm. e) AI Act. Pokuta až 35 milionů EUR.", "type": "info"},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 5 odst. 1 písm. e) — zákaz nerozlišujícího scrapingu obličejů",
            },
            {
                "key": "uses_biometric_categorization",
                "text": "Používáte AI ke kategorizaci osob na základě biometrických údajů pro odvozování rasy, politických názorů, náboženství nebo sexuální orientace?",
                "type": "yes_no_unknown",
                "help_text": "Čl. 5 odst. 1 písm. g) zakazuje systémy biometrické kategorizace, které individuálně kategorizují fyzické osoby na základě biometrických údajů za účelem odvozování rasy, politických názorů, členství v odborech, náboženského vyznání nebo sexuální orientace.\\n\\nPříklady ZAKÁZANÉHO použití:\\n1) AI systém, který z fotografií zákazníků odvozuje etnický původ pro cílení nabídek.\\n2) Software kategorizující zaměstnance dle náboženství z biometrických dat.\\n3) AI třídění CV podle vzhledu kandidátů.\\n\\nPříklady POVOLENÉ (NENÍ porušení):\\n1) Ověření totožnosti pomocí obličeje (verifikace, ne kategorizace).\\n2) Detekce úsměvu ve fotoaparátu (technická funkce).",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "biometric_categorization_warning", "label": "\\ud83d\\udeab ZAKÁZANÝ SYSTÉM — Biometrická kategorizace pro odvozování citlivých atributů je zakázána čl. 5 odst. 1 písm. g) AI Act. Pokuta až 35 milionů EUR.", "type": "info"},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 5 odst. 1 písm. g) — zákaz biometrické kategorizace dle citlivých atributů",
            },
        ],
    },'''
    content = content.replace(marker_prohibited, new_questions_prohibited)
    changes_made += 1
    print("✅ 1/6 Added 4 prohibited practice questions")
else:
    print("❌ 1/6 FAILED: Could not find prohibited section marker")

# ═══════════════════════════════════════════════════
# 2. UPDATE EMOTION RECOGNITION TEXT + ADD PROHIBITION WARNING
# ═══════════════════════════════════════════════════

old_emotion_text = '"text": "Rozpoznáváte emoce zaměstnanců nebo zákazníků pomocí AI?",'
new_emotion_text = '"text": "Rozpoznáváte emoce zaměstnanců, žáků nebo zákazníků pomocí AI?",'

if old_emotion_text in content:
    content = content.replace(old_emotion_text, new_emotion_text)
    changes_made += 1
    print("✅ 2/6 Updated emotion recognition question text")
else:
    print("❌ 2/6 FAILED: Could not find emotion recognition text")

# Add prohibition warning to emotion recognition followup
old_emotion_context = '"key": "emotion_context", "label": "V jakém kontextu? (vyberte vše, co platí)", "type": "multi_select",'
new_emotion_context = '{"key": "emotion_workplace_education_warning", "label": "\\ud83d\\udeab POZOR: Čl. 5 odst. 1 písm. f) AI Act ZAKAZUJE rozpoznávání emocí na pracovišti a ve vzdělávacích institucích (s výjimkou medicínských/bezpečnostních důvodů). Pokud rozpoznáváte emoce zaměstnanců nebo žáků, jedná se o zakázanou praktiku! Pokuta až 35 milionů EUR.", "type": "info"},\n                        {"key": "emotion_context", "label": "V jakém kontextu? (vyberte vše, co platí)", "type": "multi_select",'

if old_emotion_context in content:
    content = content.replace(old_emotion_context, new_emotion_context)
    changes_made += 1
    print("✅ 3/6 Added emotion recognition prohibition warning")
else:
    print("❌ 3/6 FAILED: Could not find emotion_context marker")

# ═══════════════════════════════════════════════════
# 3. ADD EMPLOYEE NOTIFICATION QUESTION to HR section
# ═══════════════════════════════════════════════════

marker_hr_end = 'omezení rozpoznávání emocí na pracovišti",\n            },\n        ],\n    },'

if marker_hr_end in content:
    new_hr = '''omezení rozpoznávání emocí na pracovišti",
            },
            {
                "key": "informs_employees_about_ai",
                "text": "Informujete zaměstnance předem o tom, že budou vystaveni AI systémům na pracovišti?",
                "type": "yes_no_unknown",
                "help_text": "Článek 26 odst. 7 AI Act vyžaduje, aby zaměstnavatelé před nasazením AI na pracovišti informovali zástupce zaměstnanců a dotčené pracovníky.\\n\\nPříklady ANO:\\n1) Zaslali jste zaměstnancům oznámení o nasazení AI chatbota.\\n2) Na poradě jste představili nový AI nástroj pro hodnocení výkonu.\\n3) Interní e-mail o tom, že firma začíná používat AI monitoring.\\n\\nPříklady NE:\\n1) AI nástroje jste nasadili bez jakéhokoliv informování zaměstnanců.\\n2) Zaměstnanci nevědí, že jsou monitorováni AI.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "employee_notification_method", "label": "Jak zaměstnance informujete? (vyberte vše)", "type": "multi_select",
                         "options": ["E-mail / interní sdělení", "Porada / prezentace", "Interní směrnice / dokument", "Podpis souhlasu / potvrzení", "Oznámení na intranetu", "Jiné"]},
                        {"key": "employee_notification_ok", "label": "✅ Výborně! Informování zaměstnanců je požadavek čl. 26 odst. 7 AI Act. V rámci služby AIshield vám dodáme profesionálně zpracovanou prezentaci a vzorové oznámení.", "type": "info"},
                    ]
                },
                "followup_no": {
                    "fields": [
                        {"key": "employee_notification_warning", "label": "⚠️ Článek 26 odst. 7 AI Act vyžaduje, abyste zaměstnance informovali PŘEDEM o tom, že budou vystaveni AI systémům na pracovišti. **V rámci služby AIshield vám dodáme profesionálně zpracované oznámení pro zaměstnance a prezentaci k představení AI systémů na pracovišti.**", "type": "info"},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 26 odst. 7 — informování zaměstnanců o AI na pracovišti",
            },
        ],
    },'''
    content = content.replace(marker_hr_end, new_hr)
    changes_made += 1
    print("✅ 4/6 Added employee notification question to HR section")
else:
    print("❌ 4/6 FAILED: Could not find HR section end marker")

# ═══════════════════════════════════════════════════
# 4. ADD EDUCATION SECTION (new section between finance and customer_service)
# ═══════════════════════════════════════════════════

marker_customer = '    # ──────────────────────────────────────────────\n    # Section 5: Zákazníci a komunikace\n    # ──────────────────────────────────────────────'

if marker_customer in content:
    education_section = '''    # ──────────────────────────────────────────────
    # Section: AI ve vzdělávání (Příloha III bod 3)
    # ──────────────────────────────────────────────
    {
        "id": "education",
        "title": "AI ve vzdělávání",
        "description": "AI Act klasifikuje AI ve vzdělávání jako vysoce rizikový systém (Příloha III bod 3).",
        "questions": [
            {
                "key": "uses_ai_education",
                "text": "Používáte AI ve vzdělávání nebo hodnocení žáků/studentů?",
                "type": "yes_no_unknown",
                "help_text": "Příloha III bod 3 AI Act klasifikuje jako vysoce rizikové AI systémy určené k použití ve vzdělávání.\\n\\nPříklady ANO:\\n1) AI systém pro přijímací řízení (rozhoduje o přijetí studentů).\\n2) AI hodnotí eseje, testy nebo zkoušky studentů.\\n3) AI monitoruje studenty při online zkouškách (proctoring).\\n4) E-learning platforma s AI, která rozhoduje o úrovni obtížnosti studia.\\n5) AI doporučuje kariérní poradenství ve škole.\\n\\nPříklady NE (NENÍ porušení):\\n1) Učitel občas použije ChatGPT na přípravu výuky.\\n2) Studenti používají AI překladač.\\n3) Školní web s AI chatbotem pro obecné dotazy.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "education_ai_scope", "label": "V čem AI ve vzdělávání používáte? (vyberte vše)", "type": "multi_select",
                         "options": ["Přijímací řízení / výběr studentů", "Hodnocení testů / esejí / zkoušek", "Monitoring při zkouškách (proctoring)", "Přizpůsobení úrovně studia (adaptivní learning)", "Kariérní poradenství", "Detekce podvádění / opisování", "Jiné"]},
                        {"key": "education_ai_warning", "label": "⚠️ VYSOCE RIZIKOVÝ SYSTÉM — AI ve vzdělávání spadá pod Přílohu III bod 3 AI Act. Povinnosti: systém řízení rizik (čl. 9), technická dokumentace (Příloha IV), lidský dohled (čl. 14), transparentnost (čl. 13), monitoring (čl. 72). **AIshield vám pomůže s kompletní compliance dokumentací.**", "type": "info"},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "Příloha III bod 3 — AI ve vzdělávání a odborné přípravě",
            },
        ],
    },
    # ──────────────────────────────────────────────
    # Section 5: Zákazníci a komunikace
    # ──────────────────────────────────────────────'''
    content = content.replace(marker_customer, education_section)
    changes_made += 1
    print("✅ 5/6 Added education section")
else:
    print("❌ 5/6 FAILED: Could not find customer service section marker")

# ═══════════════════════════════════════════════════
# 5. ADD CYBERSECURITY QUESTION to incident_management
# ═══════════════════════════════════════════════════

marker_incident_end = 'správa dat a tréninkových dat",\n            },\n        ],\n    },\n    # ═══'

if marker_incident_end in content:
    new_incident = '''správa dat a tréninkových dat",
            },
            {
                "key": "has_cybersecurity_measures",
                "text": "Máte opatření kybernetické bezpečnosti pro vaše AI systémy?",
                "type": "yes_no_unknown",
                "help_text": "Článek 15 AI Act vyžaduje, aby vysoce rizikové AI systémy dosahovaly náležité úrovně kybernetické bezpečnosti.\\n\\nPříklady ANO:\\n1) AI systém má ošetřený vstup proti injection útokům (prompt injection).\\n2) Přístupy k AI nástrojům jsou chráněny MFA.\\n3) Data pro AI jsou šifrována a přístup je logován.\\n4) Máte zálohy dat AI systémů.\\n\\nPříklady NE:\\n1) AI chatbot nemá žádné zabezpečení proti zneužití.\\n2) Zaměstnanci mají neomezený přístup k AI bez hesla.\\n3) Nikdy jste netestovali bezpečnost AI.",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "cybersecurity_scope", "label": "Jaká opatření máte? (vyberte vše)", "type": "multi_select",
                         "options": ["Ochrana proti prompt injection", "MFA / řízení přístupů", "Šifrování dat", "Pravidelné bezpečnostní testy", "Zálohy dat AI systémů", "Monitoring bezpečnostních incidentů", "Firewall / WAF", "Jiné"]},
                        {"key": "cybersecurity_ok", "label": "✅ Výborně! Kybernetická bezpečnost AI je požadavek čl. 15 AI Act. Do compliance dokumentace zaznamenáme vaše bezpečnostní opatření.", "type": "info"},
                    ]
                },
                "followup_no": {
                    "fields": [
                        {"key": "cybersecurity_warning", "label": "⚠️ Článek 15 AI Act vyžaduje, aby AI systémy dosahovaly náležité úrovně kybernetické bezpečnosti — ochrana proti manipulaci s daty (data poisoning), manipulaci se vstupy (prompt injection) a pokusům o neoprávněný přístup. **V rámci Compliance Kitu vám vygenerujeme bezpečnostní checklist pro vaše AI systémy.**", "type": "info"},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 15 — přesnost, spolehlivost a kybernetická bezpečnost",
            },
        ],
    },
    # ═══'''
    content = content.replace(marker_incident_end, new_incident)
    changes_made += 1
    print("✅ 6/6 Added cybersecurity question")
else:
    print("❌ 6/6 FAILED: Could not find incident management end marker")

# ═══════════════════════════════════════════════════
# 6. UPDATE _SECTION_ORDER to include 'education'
# ═══════════════════════════════════════════════════

old_order = '"industry", "internal_ai", "customer_service", "hr", "finance",'
new_order = '"industry", "internal_ai", "customer_service", "hr", "finance", "education",'

if old_order in content:
    content = content.replace(old_order, new_order)
    print("✅ Updated _SECTION_ORDER with 'education'")
else:
    print("⚠️ Could not find _SECTION_ORDER — may need manual update")

# Write result
with open(filepath, "w") as f:
    f.write(content)

print(f"\n{'='*50}")
print(f"Changes made: {changes_made}/6")
print(f"File size: {len(content)} chars")

# Count main questions
lines = content.split('\n')
main_keys = [l for l in lines if '"key":' in l and '"label":' not in l]
print(f"Main question keys found: {len(main_keys)}")
print("Expected: 55 (47 original + 4 prohibited + 1 education + 1 employee + 1 cybersecurity + 1 emotion unchanged = 55)")
