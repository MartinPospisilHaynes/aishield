#!/usr/bin/env python3
"""
Patch script: Adds investigation checklist for "Nevím" answers,
cross-reference with scan findings, and dashboard "K prověření" data.

Run on VPS: python3 /tmp/patch_unknown.py
"""
import re

FILE = "/opt/aishield/backend/api/questionnaire.py"

with open(FILE, "r") as f:
    content = f.read()

# ═══════════════════════════════════════════
# 1. Add INVESTIGATION_STEPS dict after QUESTIONNAIRE_SECTIONS
# ═══════════════════════════════════════════

INVESTIGATION_STEPS_CODE = '''

# ── "Nevím" vyšetřovací kroky pro každou otázku ──
INVESTIGATION_STEPS: dict[str, list[str]] = {
    "uses_chatgpt": [
        "Zkontrolujte faktury za SaaS služby (hledejte OpenAI, Anthropic, Google AI)",
        "Zeptejte se zaměstnanců, zda používají ChatGPT, Claude nebo Gemini",
        "Zkontrolujte prohlížeče — má někdo záložky na chat.openai.com?",
    ],
    "uses_copilot": [
        "Zeptejte se vývojářů/IT, zda používají GitHub Copilot, Cursor nebo Codeium",
        "Zkontrolujte předplatná v GitHub/VS Code Marketplace",
    ],
    "uses_ai_content": [
        "Zkontrolujte nástroje marketingového týmu — Canva AI, Jasper, Midjourney?",
        "Zeptejte se, kdo tvoří grafiku a texty — používá AI generátory?",
    ],
    "uses_deepfake": [
        "Má firma videa s AI avatary (HeyGen, Synthesia)?",
        "Používá se klonování hlasu (ElevenLabs)?",
    ],
    "uses_ai_chatbot": [
        "Podívejte se na váš web — vidíte chatovací bublinu v rohu?",
        "Zkontrolujte nastavení webu/CMS — máte připojený Intercom, Drift, Tidio?",
        "Náš sken webu může chatbota detekovat automaticky",
    ],
    "uses_ai_email_auto": [
        "Zkontrolujte, zda e-mailový systém (Mailchimp, Ecomail) má zapnuté AI funkce",
        "Generují se automatické odpovědi na zákaznické dotazy?",
    ],
    "uses_ai_decision": [
        "Existuje systém, který automaticky schvaluje/zamítá žádosti zákazníků?",
        "Rozhoduje software o slevách, vrácení zboží nebo přístupu ke službám?",
    ],
    "uses_dynamic_pricing": [
        "Zkontrolujte ceník e-shopu — mění se ceny automaticky podle poptávky?",
        "Zapojte se do vlastního e-shopu jako nový zákazník a porovnejte ceny",
    ],
    "uses_ai_recruitment": [
        "Zeptejte se HR oddělení, zda používají AI třídění životopisů",
        "Zkontrolujte nástroje jako Teamio, LinkedIn Recruiter, Sloneek",
    ],
    "uses_ai_employee_monitoring": [
        "Používáte software sledující produktivitu (Hubstaff, Time Doctor)?",
        "Jsou v kancelářích kamery s AI analýzou?",
    ],
    "uses_emotion_recognition": [
        "Analyzuje call centrum tón hlasu zákazníků nebo zaměstnanců?",
        "Existují kamery s analýzou výrazu obličeje?",
    ],
    "uses_ai_accounting": [
        "Zkontrolujte účetní software — má AI funkce (Money, Pohoda, Fakturoid)?",
        "Generuje software automaticky účetní zápisy nebo doporučení?",
    ],
    "uses_ai_creditscoring": [
        "Hodnotíte bonitu zákazníků automaticky?",
        "Zkontrolujte, zda ERP/CRM systém přiděluje skóre zákazníkům",
    ],
    "uses_ai_insurance": [
        "Automatizuje pojišťovací systém vyhodnocování rizik?",
        "Rozhoduje AI o výši pojistného nebo likvidaci pojistných událostí?",
    ],
    "uses_social_scoring": [
        "Přidělujete zákazníkům \\u2018skóre\\u2019 ovlivňující přístup ke službám?",
        "Penalizujete zákazníky na základě chování mimo vaši službu?",
    ],
    "uses_subliminal_manipulation": [
        "Používáte dark patterns nebo skryté nudging techniky řízené AI?",
        "Personalizuje AI obsah webu způsobem, který může ovlivnit rozhodování?",
    ],
    "uses_realtime_biometric": [
        "Používáte rozpoznávání obličeje nebo otisku prstu u vstupu?",
        "Má bezpečnostní systém AI identifikaci osob v reálném čase?",
    ],
    "uses_ai_critical_infra": [
        "Řídí AI systém energetiku, vodu, dopravu nebo telekomunikace?",
        "Funguje AI jako bezpečnostní komponenta v kritické infrastruktuře?",
    ],
    "uses_ai_safety_component": [
        "Je AI součástí bezpečnostního systému (požární, auto, průmyslový)?",
        "Rozhoduje AI o bezpečnosti osob nebo majetku?",
    ],
    "ai_processes_personal_data": [
        "Zkontrolujte, zda AI nástroje zpracovávají jména, e-maily nebo osobní údaje",
        "Má firma DPIA (posouzení vlivu na ochranu údajů)?",
        "Vkládají zaměstnanci do AI nástrojů zákaznická data?",
    ],
    "ai_data_stored_eu": [
        "Zkontrolujte cloud poskytovatele — kde fyzicky běží vaše AI služby?",
        "OpenAI/Anthropic data mohou být v USA — ověřte podmínky služby",
    ],
    "ai_transparency_docs": [
        "Existuje dokument evidující všechny AI systémy ve firmě?",
        "Máte na webu transparenční stránku o použití AI?",
    ],
    "has_ai_training": [
        "Bylo provedeno školení zaměstnanců o AI (bezpečnost, pravidla, GDPR)?",
        "Existuje záznam o školení?",
    ],
    "has_ai_guidelines": [
        "Existuje firemní směrnice pro používání AI?",
        "Jsou zaměstnanci informováni o tom, co smí / nesmí do AI vkládat?",
    ],
    "develops_own_ai": [
        "Vyvíjí firma vlastní AI modely, nebo pouze používá hotové služby?",
        "Máte vývojáře, kteří trénují ML modely?",
    ],
}

# ── Mapování scan findings → dotazníkové otázky (pro cross-reference) ──
SCAN_TO_QUESTION_MAP: dict[str, str] = {
    "chatbot": "uses_ai_chatbot",
    "chat widget": "uses_ai_chatbot",
    "intercom": "uses_ai_chatbot",
    "drift": "uses_ai_chatbot",
    "tidio": "uses_ai_chatbot",
    "zendesk": "uses_ai_chatbot",
    "crisp": "uses_ai_chatbot",
    "livechat": "uses_ai_chatbot",
    "cookie": "ai_processes_personal_data",
    "tracking": "ai_processes_personal_data",
    "analytics": "ai_processes_personal_data",
    "google analytics": "ai_processes_personal_data",
    "facebook pixel": "ai_processes_personal_data",
    "hotjar": "ai_processes_personal_data",
    "personalization": "uses_ai_decision",
    "recommendation": "uses_ai_decision",
    "dynamic pricing": "uses_dynamic_pricing",
    "email automation": "uses_ai_email_auto",
    "mailchimp": "uses_ai_email_auto",
    "ecomail": "uses_ai_email_auto",
    "content generation": "uses_ai_content",
    "openai": "uses_chatgpt",
    "gpt": "uses_chatgpt",
    "anthropic": "uses_chatgpt",
    "gemini": "uses_chatgpt",
}

'''

# Insert after the last section in QUESTIONNAIRE_SECTIONS (before class definitions)
# Find the line "class QuestionnaireAnswer"
insert_point = content.find("class QuestionnaireAnswer")
if insert_point == -1:
    print("ERROR: Could not find 'class QuestionnaireAnswer'")
    exit(1)

content = content[:insert_point] + INVESTIGATION_STEPS_CODE + "\n" + content[insert_point:]
print("✅ Added INVESTIGATION_STEPS and SCAN_TO_QUESTION_MAP")


# ═══════════════════════════════════════════
# 2. Update _analyze_responses to include unknown_items
# ═══════════════════════════════════════════

# Find the return statement in _analyze_responses
old_return = '''    return {
        "total_answers": len(answers),
        "ai_systems_declared": len(yes_answers),
        "unknown_count": len(unknown_answers),
        "risk_breakdown": risk_breakdown,
        "recommendations": recommendations,
    }'''

new_return = '''    # Vyšetřovací kroky pro "Nevím" odpovědi
    unknown_items = []
    for ans in unknown_answers:
        q_def = question_map.get(ans.question_key)
        if not q_def:
            continue
        steps = INVESTIGATION_STEPS.get(ans.question_key, [
            "Ověřte s odpovědnou osobou ve firmě",
            "Zkontrolujte dokumentaci a faktury za IT služby",
        ])
        unknown_items.append({
            "question_key": ans.question_key,
            "question_text": q_def.get("text", ""),
            "risk_hint": q_def.get("risk_hint", "minimal"),
            "section": q_def.get("_section_id", ""),
            "investigation_steps": steps,
        })

    # Seřadit unknown_items: high → limited → minimal
    unknown_items.sort(key=lambda x: risk_order.get(x["risk_hint"], 3))

    return {
        "total_answers": len(answers),
        "ai_systems_declared": len(yes_answers),
        "unknown_count": len(unknown_answers),
        "risk_breakdown": risk_breakdown,
        "recommendations": recommendations,
        "unknown_items": unknown_items,
    }'''

if old_return in content:
    content = content.replace(old_return, new_return)
    print("✅ Updated _analyze_responses return with unknown_items")
else:
    print("⚠️  Could not find exact return block in _analyze_responses, trying flexible match...")
    # Try a more flexible approach
    pattern = r'(    return \{\s*\n\s*"total_answers".*?"recommendations": recommendations,\s*\n\s*\})'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        content = content.replace(match.group(0), new_return)
        print("✅ Updated _analyze_responses return with unknown_items (flexible match)")
    else:
        print("ERROR: Could not patch _analyze_responses return")


# ═══════════════════════════════════════════
# 3. Update combined-report to include cross_references
# ═══════════════════════════════════════════

# Find the return block of get_combined_report and add cross_references
old_combined_return = '''        "action_items": _generate_action_items(scan_findings, q_analysis),
    }'''

new_combined_return = '''        "action_items": _generate_action_items(scan_findings, q_analysis),
        "unknown_items": q_analysis.get("unknown_items", []) if q_analysis else [],
        "cross_references": _cross_reference_scan_vs_unknown(scan_findings, questionnaire_answers),
    }'''

if old_combined_return in content:
    content = content.replace(old_combined_return, new_combined_return)
    print("✅ Updated combined-report return with cross_references")
else:
    print("ERROR: Could not patch combined-report return")


# ═══════════════════════════════════════════
# 4. Add _cross_reference_scan_vs_unknown function
# ═══════════════════════════════════════════

CROSS_REF_FUNCTION = '''

def _cross_reference_scan_vs_unknown(scan_findings: list, answers: list) -> list[dict]:
    """
    Porovná scan findings s 'unknown' odpověďmi z dotazníku.
    Pokud scan našel něco, co uživatel označil jako 'nevím', navrhne odpověď.
    """
    unknown_keys = {a.question_key for a in answers if a.answer == "unknown"}
    if not unknown_keys or not scan_findings:
        return []

    # Build question text map
    question_map = {}
    for section in QUESTIONNAIRE_SECTIONS:
        for q in section["questions"]:
            question_map[q["key"]] = q

    cross_refs = []
    matched_keys = set()

    for finding in scan_findings:
        fname = (finding.get("name", "") or "").lower()
        fcat = (finding.get("category", "") or "").lower()
        combined = fname + " " + fcat

        for scan_keyword, q_key in SCAN_TO_QUESTION_MAP.items():
            if scan_keyword.lower() in combined and q_key in unknown_keys and q_key not in matched_keys:
                q_def = question_map.get(q_key, {})
                cross_refs.append({
                    "question_key": q_key,
                    "question_text": q_def.get("text", ""),
                    "user_answer": "unknown",
                    "scan_detected": True,
                    "scan_finding_name": finding.get("name", ""),
                    "scan_finding_risk": finding.get("risk_level", "minimal"),
                    "suggested_answer": "yes",
                    "message": f'Na vašem webu jsme detekovali „{finding.get("name", "AI systém")}" — pravděpodobně odpověď na tuto otázku je ANO.',
                })
                matched_keys.add(q_key)

    return cross_refs

'''

# Insert before the last function or at the end
# Find _get_or_create_client and insert before it
insert_point2 = content.find("async def _get_or_create_client")
if insert_point2 == -1:
    # Fallback: append at end
    content += CROSS_REF_FUNCTION
    print("✅ Added _cross_reference_scan_vs_unknown (at end)")
else:
    content = content[:insert_point2] + CROSS_REF_FUNCTION + "\n" + content[insert_point2:]
    print("✅ Added _cross_reference_scan_vs_unknown (before _get_or_create_client)")


# ═══════════════════════════════════════════
# 5. Add section_id to question_map in _analyze_responses
# ═══════════════════════════════════════════

old_qmap = '''    question_map = {}
    for section in QUESTIONNAIRE_SECTIONS:
        for q in section["questions"]:
            question_map[q["key"]] = q'''

new_qmap = '''    question_map = {}
    for section in QUESTIONNAIRE_SECTIONS:
        for q in section["questions"]:
            q_copy = dict(q)
            q_copy["_section_id"] = section["id"]
            question_map[q["key"]] = q_copy'''

if old_qmap in content:
    content = content.replace(old_qmap, new_qmap, 1)
    print("✅ Added _section_id to question_map")
else:
    print("⚠️  Could not patch question_map (may already have it)")


# ═══════════════════════════════════════════
# Write the patched file
# ═══════════════════════════════════════════

with open(FILE, "w") as f:
    f.write(content)

print(f"\n✅ File written: {FILE}")
print(f"   Lines: {len(content.splitlines())}")
