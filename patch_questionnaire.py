#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive patch for questionnaire.py
Re-applies all session changes:
1. Company profile fields (legal name, ICO, address, email, revenue)
2. has_oversight_person enhancement (role, name, email, scope follow-ups)
3. has_incident_plan YES follow-up (escalation chain, communication)
4. ai_transparency_docs follow-ups
5. has_ai_training audience fields
6. has_ai_guidelines YES follow-up
"""

filepath = '/Users/martinhaynes/Projects/aishield/backend/api/questionnaire.py'

with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

content = ''.join(lines)
original_len = len(content)

# ============================================================
# PATCH 1: Add company profile fields to "industry" section
# ============================================================
# Insert before company_industry: legal_name, ico, address, contact_email, annual_revenue

COMPANY_FIELDS = '''            {
                "key": "company_legal_name",
                "text": "Obchodn\u00ed firma (n\u00e1zev spole\u010dnosti nebo jm\u00e9no OSV\u010c):",
                "type": "text",
                "help_text": "P\u0159esn\u00fd n\u00e1zev tak, jak je zaps\u00e1n v obchodn\u00edm rejst\u0159\u00edku nebo \u017eivnostensk\u00e9m rejst\u0159\u00edku.\\nP\u0159\u00edklady:\\n1) ACME Solutions s.r.o.\\n2) Jan Nov\u00e1k \u2014 grafick\u00fd design\\n3) TechStart a.s.",
                "risk_hint": "none",
                "ai_act_article": None,
            },
            {
                "key": "company_ico",
                "text": "I\u010cO (identifika\u010dn\u00ed \u010d\u00edslo osoby):",
                "type": "text",
                "help_text": "8m\u00edstn\u00e9 \u010d\u00edslo z obchodn\u00edho nebo \u017eivnostensk\u00e9ho rejst\u0159\u00edku. Slou\u017e\u00ed k identifikaci va\u0161\u00ed firmy v ofici\u00e1ln\u00ed dokumentaci.\\nP\u0159\u00edklady: 12345678, 05123456.",
                "risk_hint": "none",
                "ai_act_article": None,
            },
            {
                "key": "company_address",
                "text": "S\u00eddlo firmy (adresa):",
                "type": "text",
                "help_text": "Adresa s\u00eddla dle rejst\u0159\u00edku \u2014 pou\u017eijeme ji v Compliance Reportu, na transpar\u011bn\u010dn\u00ed str\u00e1nce a v ofici\u00e1ln\u00ed dokumentaci.\\nP\u0159\u00edklad: V\u00e1clavsk\u00e9 n\u00e1m\u011bst\u00ed 1, 110 00 Praha 1",
                "risk_hint": "none",
                "ai_act_article": None,
            },
            {
                "key": "company_contact_email",
                "text": "Kontaktn\u00ed e-mail pro AI z\u00e1le\u017eitosti:",
                "type": "text",
                "help_text": "E-mail, na kter\u00fd se mohou obracet z\u00e1kazn\u00edci, zam\u011bstnanci nebo dozorov\u00e9 org\u00e1ny ohledn\u011b va\u0161eho pou\u017e\u00edv\u00e1n\u00ed AI. Zobraz\u00ed se na transpar\u011bn\u010dn\u00ed str\u00e1nce.\\nP\u0159\u00edklad: ai@vase-firma.cz nebo info@vase-firma.cz",
                "risk_hint": "none",
                "ai_act_article": "\u010dl. 50 \u2014 transparentnost a informov\u00e1n\u00ed",
            },
'''

marker1 = '"key": "company_industry"'
idx1 = content.find(marker1)
if idx1 > 0:
    # Find the { that starts the company_industry dict
    brace = content.rfind('{', 0, idx1)
    # Insert company fields before it
    content = content[:brace] + COMPANY_FIELDS + content[brace:]
    print("PATCH 1: Company profile fields added")
else:
    print("PATCH 1 SKIP: company_industry not found")

# Also add company_annual_revenue after company_size
REVENUE_FIELD = '''            {
                "key": "company_annual_revenue",
                "text": "Jak\u00fd je p\u0159ibli\u017en\u00fd ro\u010dn\u00ed obrat va\u0161\u00ed firmy?",
                "type": "single_select",
                "options": [
                    "Do 2 mil. K\u010d",
                    "2\u201310 mil. K\u010d",
                    "10\u201350 mil. K\u010d",
                    "50\u2013250 mil. K\u010d",
                    "250 mil. \u2013 1 mld. K\u010d",
                    "Nad 1 mld. K\u010d",
                    "Nechci uv\u00e1d\u011bt",
                ],
                "help_text": "Pot\u0159ebujeme pro v\u00fdpo\u010det maxim\u00e1ln\u00ed v\u00fd\u0161e pokut dle AI Act (pokuty se po\u010d\u00edtaj\u00ed jako % z celosv\u011btov\u00e9ho obratu). \u00dadaj je d\u016fv\u011brn\u00fd a slou\u017e\u00ed pouze pro va\u0161i compliance dokumentaci.\\n\\n\U0001f4a1 Nemus\u00edte odpov\u00eddat p\u0159esn\u011b \u2014 sta\u010d\u00ed p\u0159ibli\u017en\u00fd rozsah.",
                "risk_hint": "none",
                "ai_act_article": "\u010dl. 99 \u2014 spr\u00e1vn\u00ed pokuty (% z obratu)",
            },
'''

marker_size = '"key": "develops_own_ai"'
idx_size = content.find(marker_size)
if idx_size > 0:
    brace_size = content.rfind('{', 0, idx_size)
    content = content[:brace_size] + REVENUE_FIELD + content[brace_size:]
    print("PATCH 1b: Annual revenue field added")

# ============================================================
# PATCH 2: Enhance has_oversight_person with role follow-ups
# ============================================================

marker2 = '"key": "has_oversight_person"'
idx2 = content.find(marker2)
if idx2 > 0:
    # Find the followup section for "yes"
    followup_idx = content.find('"followup":', idx2)
    # Check if it already has oversight_role (our enhancement)
    next_q = content.find('"key": "can_override_ai"', idx2)
    block2 = content[idx2:next_q] if next_q > 0 else ''
    
    if '"oversight_role"' not in block2 and followup_idx > 0 and followup_idx < next_q:
        # Find the "fields": [ after followup
        fields_start = content.find('"fields": [', followup_idx)
        if fields_start > 0 and fields_start < next_q:
            # Find the ] that closes the fields array
            # Count brackets
            bracket_count = 0
            pos = fields_start + len('"fields": [')
            while pos < len(content):
                if content[pos] == '[':
                    bracket_count += 1
                elif content[pos] == ']':
                    if bracket_count == 0:
                        break
                    bracket_count -= 1
                pos += 1
            
            # Replace the entire fields array content
            old_fields_end = pos  # position of closing ]
            new_yes_fields = """
                        {"key": "oversight_role", "label": "Jakou roli m\u00e1 osoba, kter\u00e1 na AI dohl\u00ed\u017e\u00ed?", "type": "select",
                         "options": [
                             "Jednatel / majitel (dohl\u00ed\u017e\u00edm osobn\u011b)",
                             "IT mana\u017eer / vedouc\u00ed IT",
                             "Compliance officer",
                             "DPO (pov\u011b\u0159enec pro ochranu osobn\u00edch \u00fadaj\u016f)",
                             "T\u00fdm / komise AI governance",
                             "Jin\u00e1 role"
                         ]},
                        {"key": "oversight_person_name", "label": "Jm\u00e9no odpov\u011bdn\u00e9 osoby (voliteln\u00e9 \u2014 pou\u017eijeme v dokumentaci):", "type": "text"},
                        {"key": "oversight_person_email", "label": "E-mail odpov\u011bdn\u00e9 osoby (voliteln\u00e9 \u2014 pro eskalac\u030cn\u00ed pl\u00e1n):", "type": "text"},
                        {"key": "oversight_scope", "label": "Na co konkr\u00e9tn\u011b dohl\u00ed\u017e\u00ed?", "type": "multi_select",
                         "options": [
                             "Chatbot na webu",
                             "Intern\u00ed AI n\u00e1stroje (ChatGPT, Copilot apod.)",
                             "AI analytiku a doporu\u010dovac\u00ed syst\u00e9my",
                             "AI v z\u00e1kaznick\u00e9m servisu",
                             "AI v HR / n\u00e1boru",
                             "AI v \u00fa\u010detnictv\u00ed / financ\u00edch",
                             "V\u0161e \u2014 zast\u0159e\u0161uje kompletn\u00ed AI governance"
                         ]},
                        {"key": "oversight_ok_info", "label": "\u2705 V\u00fdborn\u011b! Tyto \u00fadaje pou\u017eijeme pro AI governance dokumentaci \u2014 jasn\u011b v n\u00ed definujeme role, odpov\u011bdnosti a eskalac\u030cn\u00ed postupy p\u0159\u00edmo na m\u00edru va\u0161\u00ed firm\u011b.", "type": "info"},
                    """
            content = content[:fields_start + len('"fields": [')] + new_yes_fields + content[old_fields_end:]
            print("PATCH 2a: has_oversight_person YES follow-up enhanced")
    
    # Now enhance the followup_no
    followup_no_idx = content.find('"followup_no":', idx2)
    next_q2 = content.find('"key": "can_override_ai"', idx2)
    block2b = content[followup_no_idx:next_q2] if followup_no_idx > 0 and next_q2 > 0 else ''
    
    if '"oversight_suggested_role"' not in block2b and followup_no_idx > 0:
        fields_no_start = content.find('"fields": [', followup_no_idx)
        if fields_no_start > 0 and fields_no_start < next_q2:
            bracket_count = 0
            pos = fields_no_start + len('"fields": [')
            while pos < len(content):
                if content[pos] == '[':
                    bracket_count += 1
                elif content[pos] == ']':
                    if bracket_count == 0:
                        break
                    bracket_count -= 1
                pos += 1
            
            new_no_fields = """
                        {"key": "oversight_warning", "label": "\u26a0\ufe0f \u010cl\u00e1nek 14 AI Act vy\u017eaduje lidsk\u00fd dohled nad vysoce rizikov\u00fdmi AI syst\u00e9my. I u syst\u00e9m\u016f s omezen\u00fdm rizikem (chatboty) je vhodn\u00e9 m\u00edt odpov\u011bdnou osobu.", "type": "info"},
                        {"key": "oversight_suggested_role", "label": "Kdo by ve va\u0161\u00ed firm\u011b mohl na AI dohl\u00ed\u017eet?", "type": "select",
                         "options": [
                             "J\u00e1 osobn\u011b (jednatel / majitel)",
                             "N\u011bkdo z IT odd\u011blen\u00ed",
                             "N\u011bkdo z veden\u00ed / managementu",
                             "Nem\u00e1me vhodnou osobu \u2014 pot\u0159ebujeme poradit"
                         ],
                         "warning": {"Nem\u00e1me vhodnou osobu \u2014 pot\u0159ebujeme poradit": "\U0001f4a1 V r\u00e1mci AI governance dokumentace v\u00e1m navrhneme, jakou roli vytvo\u0159it a co by m\u011bla zahrnovat. Pro men\u0161\u00ed firmy sta\u010d\u00ed pov\u011b\u0159it jednu existuj\u00edc\u00ed osobu \u2014 nemus\u00edte vytv\u00e1\u0159et novou pozici."}},
                        {"key": "oversight_help_info", "label": "\u2705 Nevad\u00ed \u2014 **AIshield v\u00e1m v r\u00e1mci Compliance Kitu pom\u016f\u017ee definovat role a odpov\u011bdnosti v AI governance dokumentaci.** Navrhneme konkr\u00e9tn\u00ed osobu, jej\u00ed kompetence a eskalac\u030cn\u00ed postup na m\u00edru va\u0161\u00ed firm\u011b.", "type": "info"},
                    """
            content = content[:fields_no_start + len('"fields": [')] + new_no_fields + content[pos:]
            print("PATCH 2b: has_oversight_person NO follow-up enhanced")

# ============================================================
# PATCH 3: Enhance has_incident_plan with YES follow-up
# ============================================================

marker3 = '"key": "has_incident_plan"'
idx3 = content.find(marker3)
if idx3 > 0:
    next_q3 = content.find('"key": "monitors_ai_outputs"', idx3)
    block3 = content[idx3:next_q3] if next_q3 > 0 else ''
    
    if '"followup":' not in block3:
        followup_no3 = content.find('"followup_no":', idx3)
        if followup_no3 > 0 and followup_no3 < next_q3:
            yes_followup3 = '''"followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "incident_plan_scope", "label": "Co v\u00e1\u0161 pl\u00e1n pokr\u00fdv\u00e1? (vyberte v\u0161e)", "type": "multi_select",
                         "options": [
                             "Postup p\u0159i chybn\u00e9 AI odpov\u011bdi z\u00e1kazn\u00edkovi",
                             "Eskalac\u030cn\u00ed proces (kdo rozhoduje o dal\u0161\u00edch kroc\u00edch)",
                             "Okam\u017eit\u00e9 odstaven\u00ed AI syst\u00e9mu",
                             "Hl\u00e1\u0161en\u00ed incidentu dozorov\u00e9 autorit\u011b",
                             "Informov\u00e1n\u00ed dot\u010den\u00fdch osob",
                             "Z\u00e1znamy a dokumentace incidentu",
                         ]},
                        {"key": "incident_escalation_chain", "label": "Kdo je v eskalac\u030cn\u00edm \u0159et\u011bzci? (vyberte v\u0161e, co plat\u00ed)", "type": "multi_select",
                         "options": [
                             "Oper\u00e1tor / zam\u011bstnanec, kter\u00fd incident zjist\u00ed",
                             "Vedouc\u00ed odd\u011blen\u00ed / mana\u017eer",
                             "IT odd\u011blen\u00ed / spr\u00e1vce syst\u00e9mu",
                             "Jednatel / veden\u00ed firmy",
                             "DPO / Compliance officer",
                             "Extern\u00ed pr\u00e1vn\u00ed poradce",
                         ]},
                        {"key": "incident_communication", "label": "Jak komunikujete incidenty intern\u011b?", "type": "multi_select",
                         "options": [
                             "E-mail",
                             "Telefon / krizov\u00e1 linka",
                             "Intern\u00ed chat (Teams, Slack apod.)",
                             "Ticketovac\u00ed syst\u00e9m (Jira, Freshdesk apod.)",
                             "Nem\u00e1me definovan\u00fd kan\u00e1l",
                         ]},
                        {"key": "incident_existing_ok", "label": "\u2705 V\u00fdborn\u011b! Na z\u00e1klad\u011b t\u011bchto informac\u00ed dopln\u00edme v\u00e1\u0161 st\u00e1vaj\u00edc\u00ed pl\u00e1n o po\u017eadavky AI Act \u2014 zejm\u00e9na povinn\u00e9 hl\u00e1\u0161en\u00ed z\u00e1va\u017en\u00fdch incident\u016f dle \u010dl. 73 a komunikaci s dozorovou autoritou.", "type": "info"},
                    ]
                },
                '''
            content = content[:followup_no3] + yes_followup3 + content[followup_no3:]
            print("PATCH 3: has_incident_plan YES follow-up added")

# ============================================================
# PATCH 4: Enhance ai_transparency_docs with follow-ups
# ============================================================

marker4 = '"key": "ai_transparency_docs"'
idx4 = content.find(marker4)
if idx4 > 0:
    next_q4_search = content.find('"id": "ai_literacy"', idx4)
    block4 = content[idx4:next_q4_search] if next_q4_search > 0 else ''
    
    if '"followup":' not in block4:
        # Find the risk_hint line
        risk_idx = content.find('"risk_hint": "limited"', idx4)
        if risk_idx > 0 and risk_idx < next_q4_search:
            # Insert followup and followup_unknown before risk_hint
            # First, find the start of the risk_hint line (go back to whitespace start)
            line_start = content.rfind('\n', 0, risk_idx) + 1
            
            followup4 = '''                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "transparency_format", "label": "V jak\u00e9m form\u00e1tu p\u0159ehled vedete?", "type": "select",
                         "options": [
                             "Excel / Google Sheets tabulka",
                             "Intern\u00ed wiki / Confluence / Notion",
                             "Word / PDF dokument",
                             "Jen neform\u00e1ln\u00ed pov\u011bdom\u00ed (nic p\u00edsemn\u00e9ho)",
                         ]},
                        {"key": "transparency_ok_info", "label": "\u2705 V\u00fdborn\u011b! Na z\u00e1klad\u011b v\u00fdsledk\u016f dotazn\u00edku a skenu v\u00e1m vytvo\u0159\u00edme kompletn\u00ed Registr AI syst\u00e9m\u016f \u2014 form\u00e1ln\u00ed dokument spl\u0148uj\u00edc\u00ed po\u017eadavky \u010dl. 49 AI Act, kter\u00fd m\u016f\u017eete p\u0159edlo\u017eit p\u0159i auditu.", "type": "info"},
                    ]
                },
                "followup_unknown": {
                    "fields": [
                        {"key": "transparency_unknown_info", "label": "\U0001f4a1 Nevad\u00ed \u2014 na z\u00e1klad\u011b v\u00fdsledk\u016f dotazn\u00edku a skenu va\u0161eho webu v\u00e1m automaticky vytvo\u0159\u00edme kompletn\u00ed Registr AI syst\u00e9m\u016f. Nemus\u00edte nic dohled\u00e1vat, pokryje v\u0161e, co jsme spole\u010dn\u011b identifikovali.", "type": "info"},
                    ]
                },
'''
            content = content[:line_start] + followup4 + content[line_start:]
            print("PATCH 4: ai_transparency_docs follow-ups added")

# ============================================================
# PATCH 5: Add training audience fields to has_ai_training
# ============================================================

marker5 = '"key": "training_attendance"'
idx5 = content.find(marker5)
if idx5 > 0:
    marker5_info = '"key": "training_info"'
    idx5_info = content.find(marker5_info, idx5)
    if idx5_info > 0:
        # Insert before training_info field
        field_start5 = content.rfind('{', 0, idx5_info)
        new_fields5 = '{"key": "training_audience_size", "label": "Kolik lid\u00ed pot\u0159ebuje pro\u0161kolit?", "type": "select",\n                         "options": ["1\u20135 osob", "6\u201320 osob", "21\u201350 osob", "51\u2013100 osob", "100+ osob"]},\n                        {"key": "training_audience_level", "label": "Jak\u00e1 je technick\u00e1 \u00farove\u0148 \u0161kolen\u00fdch osob?", "type": "select",\n                         "options": [\n                             "Netechni\u010dt\u00ed (administrativa, obchod, marketing)",\n                             "St\u0159edn\u011b technicky zdatn\u00ed (mana\u017ee\u0159i, analytici)",\n                             "Techni\u010dt\u00ed (IT, v\u00fdvoj\u00e1\u0159i, data analytici)",\n                             "Mix \u2014 r\u016fzn\u00e9 \u00farovn\u011b",\n                         ]},\n                        '
        content = content[:field_start5] + new_fields5 + content[field_start5:]
        print("PATCH 5: has_ai_training audience fields added")

# ============================================================
# PATCH 6: Add YES follow-up to has_ai_guidelines
# ============================================================

marker6 = '"key": "has_ai_guidelines"'
idx6 = content.find(marker6)
if idx6 > 0:
    next_q6 = content.find('"key":', idx6 + len(marker6))
    block6 = content[idx6:next_q6] if next_q6 > 0 else content[idx6:idx6+2000]
    
    if '"followup":' not in block6 and '"followup_no":' in block6:
        followup_no6 = content.find('"followup_no":', idx6)
        if followup_no6 > 0:
            yes_followup6 = '''"followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "guidelines_scope", "label": "Co va\u0161e pravidla pokr\u00fdvaj\u00ed? (vyberte v\u0161e)", "type": "multi_select",
                         "options": [
                             "Kter\u00e9 AI n\u00e1stroje sm\u00ed zam\u011bstnanci pou\u017e\u00edvat",
                             "Jak\u00e1 data se sm\u00ed do AI vkl\u00e1dat",
                             "Kdo schvaluje nov\u00e9 AI n\u00e1stroje",
                             "Pravidla pro AI generovan\u00fd obsah",
                             "Ochrana osobn\u00edch \u00fadaj\u016f p\u0159i pr\u00e1ci s AI",
                             "Postup p\u0159i AI incidentu",
                         ]},
                        {"key": "guidelines_format", "label": "V jak\u00e9m form\u00e1tu pravidla m\u00e1te?", "type": "select",
                         "options": [
                             "P\u00edsemn\u00e1 sm\u011brnice / intern\u00ed p\u0159edpis",
                             "Sou\u010d\u00e1st jin\u00e9ho dokumentu (IT politika, GDPR apod.)",
                             "\u00dastn\u00ed pravidla / nepsan\u00e1 dohoda",
                         ]},
                        {"key": "guidelines_ok_info", "label": "\u2705 V\u00fdborn\u011b! Va\u0161i st\u00e1vaj\u00edc\u00ed sm\u011brnici roz\u0161\u00ed\u0159\u00edme o po\u017eadavky AI Act a dod\u00e1me kompletn\u00ed AI politiku firmy na m\u00edru.", "type": "info"},
                    ]
                },
                '''
            content = content[:followup_no6] + yes_followup6 + content[followup_no6:]
            print("PATCH 6: has_ai_guidelines YES follow-up added")

# ============================================================
# Update the section description
# ============================================================
old_desc = '"description": "Řeknete nám, čím se zabýváte, a my přizpůsobíme otázky."'
new_desc = '"description": "Řeknete nám, čím se zabýváte, a my přizpůsobíme otázky a dokumentaci přímo na míru."'
if old_desc in content:
    content = content.replace(old_desc, new_desc)
    print("PATCH 7: Section description updated")

# ============================================================
# WRITE
# ============================================================

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

new_len = len(content)
print(f"\nDone! File grew from {original_len} to {new_len} chars (+{new_len - original_len})")
