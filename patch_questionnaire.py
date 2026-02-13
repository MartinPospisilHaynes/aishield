#!/usr/bin/env python3
"""
Patch script for questionnaire.py on the VPS.
Adds:
1. INVESTIGATION_STEPS dict after QUESTIONNAIRE_SECTIONS.sort
2. SCAN_CROSS_REFERENCE dict after that
3. unknown_items in _analyze_responses() return
4. cross_references in combined-report endpoint
"""

import re
import sys

def patch(content: str) -> str:
    # ─────────────────────────────────────────────
    # 1. Insert INVESTIGATION_STEPS + SCAN_CROSS_REFERENCE
    #    after the QUESTIONNAIRE_SECTIONS.sort(...) line
    # ─────────────────────────────────────────────
    INVESTIGATION_BLOCK = '''

# ── Kroky pro prověření "Nevím" odpovědí ──

INVESTIGATION_STEPS: dict[str, list[str]] = {
    "uses_chatgpt": [
        "Zkontrolujte faktury za SaaS (hledejte OpenAI, Anthropic, Google AI)",
        "Zeptejte se zaměstnanců, zda používají ChatGPT, Claude nebo Gemini",
        "Zkontrolujte firemní prohlížeče — mají někdo záložky na chat.openai.com?",
    ],
    "uses_copilot": [
        "Zeptejte se vývojářů/IT, zda používají GitHub Copilot, Cursor nebo Codeium",
        "Zkontrolujte předplatná v GitHub/VS Code Marketplace",
    ],
    "uses_ai_content": [
        "Zkontrolujte nástroje marketingového týmu (Canva, Jasper, Midjourney?)",
        "Zeptejte se, kdo tvoří grafiku a texty — používá AI generátory?",
    ],
    "uses_deepfake": [
        "Má firma videa s AI avatary (HeyGen, Synthesia)?",
        "Používá se klonování hlasu (ElevenLabs)?",
    ],
    "uses_ai_chatbot": [
        "Podívejte se na váš web — vidíte chatovací bublinu v rohu?",
        "Zkontrolujte nastavení webu/CMS — máte připojený Intercom, Drift, Tidio?",
        "Náš sken webu může chatbota detekovat automaticky.",
    ],
    "uses_ai_email_auto": [
        "Zkontrolujte, zda e-mailový systém (Mailchimp, Ecomail) má zapnuté AI funkce",
        "Generují se automatické odpovědi na zákaznické dotazy?",
    ],
    "uses_ai_decision": [
        "Existuje nějaký systém, který automaticky schvaluje/zamítá žádosti zákazníků?",
        "Rozhoduje software o slevách, vrácení zboží nebo přístupu k službám?",
    ],
    "uses_dynamic_pricing": [
        "Zkontrolujte ceník e-shopu — mění se ceny automaticky podle poptávky?",
        "Zapojte se do vlastního e-shopu jako nový zákazník a porovnejte ceny",
    ],
    "uses_ai_recruitment": [
        "Zeptejte se HR oddělení, zda mají AI třídění životopisů",
        "Zkontrolujte nástroje jako Teamio, LinkedIn Recruiter, Sloneek",
    ],
    "uses_ai_employee_monitoring": [
        "Existuje software sledující produktivitu zaměstnanců (Hubstaff, Time Doctor)?",
        "Jsou v kancelářích kamery s AI analýzou?",
    ],
    "uses_emotion_recognition": [
        "Analyzuje call centrum tón hlasu zákazníků/zaměstnanců?",
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
        "Přidělujete zákazníkům 'skóre' ovlivňující jejich přístup ke službám?",
        "Penalizujete zákazníky na základě jejich chování mimo vaši službu?",
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
        "Je AI součástí bezpečnostního systému (požární, automobilový, průmyslový)?",
        "Rozhoduje AI o bezpečnosti osob nebo majetku?",
    ],
    "ai_processes_personal_data": [
        "Zkontrolujte, zda AI nástroje zpracovávají jména, e-maily nebo jiné osobní údaje",
        "Má firma DPIA (Data Protection Impact Assessment)?",
        "Vkládají zaměstnanci do AI zákaznická data?",
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
        "Jsou zaměstnanci informováni o tom, co smí/nesmí do AI vkládat?",
    ],
    "develops_own_ai": [
        "Vyvíjí firma vlastní AI modely nebo pouze používá hotové služby?",
        "Máte vývojáře, kteří trénují ML modely?",
    ],
}

# ── Mapování scan findings → otázky dotazníku (pro cross-reference) ──

SCAN_CROSS_REFERENCE: dict[str, str] = {
    # scan finding category or name substring → questionnaire key
    "chatbot": "uses_ai_chatbot",
    "Chatbot": "uses_ai_chatbot",
    "chat widget": "uses_ai_chatbot",
    "Intercom": "uses_ai_chatbot",
    "Drift": "uses_ai_chatbot",
    "Tidio": "uses_ai_chatbot",
    "Zendesk": "uses_ai_chatbot",
    "cookie": "ai_processes_personal_data",
    "tracking": "ai_processes_personal_data",
    "analytics": "ai_processes_personal_data",
    "Google Analytics": "ai_processes_personal_data",
    "personalization": "uses_ai_decision",
    "dynamic pricing": "uses_dynamic_pricing",
    "email automation": "uses_ai_email_auto",
    "Mailchimp": "uses_ai_email_auto",
    "content generation": "uses_ai_content",
    "OpenAI": "uses_chatgpt",
    "GPT": "uses_chatgpt",
}

'''

    anchor = 'QUESTIONNAIRE_SECTIONS.sort(key=lambda s: _SECTION_ORDER.index(s["id"]))'
    if anchor not in content:
        print("ERROR: Could not find QUESTIONNAIRE_SECTIONS.sort anchor", file=sys.stderr)
        sys.exit(1)
    content = content.replace(anchor, anchor + INVESTIGATION_BLOCK)
    print("[1/4] Inserted INVESTIGATION_STEPS and SCAN_CROSS_REFERENCE dicts")

    # ─────────────────────────────────────────────
    # 2. Update _analyze_responses return to include unknown_items
    # ─────────────────────────────────────────────

    # Find the block between "# Seřadit doporučení" and the return statement in _analyze_responses
    old_return_block = '''    # Seřadit doporučení: high → limited → minimal
    risk_order = {"high": 0, "limited": 1, "minimal": 2}
    recommendations.sort(key=lambda r: risk_order.get(r["risk_level"], 3))

    return {
        "total_answers": len(answers),
        "ai_systems_declared": len(yes_answers),
        "unknown_count": len(unknown_answers),
        "risk_breakdown": risk_breakdown,
        "recommendations": recommendations,
    }'''

    new_return_block = '''    # Seřadit doporučení: high → limited → minimal
    risk_order = {"high": 0, "limited": 1, "minimal": 2}
    recommendations.sort(key=lambda r: risk_order.get(r["risk_level"], 3))

    # Sestavit unknown_items — konkrétní kroky k prověření pro každé "Nevím"
    unknown_items = []
    for ans in unknown_answers:
        q_def = question_map.get(ans.question_key)
        if not q_def:
            continue
        steps = INVESTIGATION_STEPS.get(ans.question_key, [
            "Ověřte interně, zda se tato oblast týká vaší firmy.",
        ])
        # Hint pro cross-reference se skenem
        scan_hint = None
        for scan_keyword, q_key in SCAN_CROSS_REFERENCE.items():
            if q_key == ans.question_key:
                scan_hint = f"Sken webu může detekovat: '{scan_keyword}'"
                break

        unknown_items.append({
            "question_key": ans.question_key,
            "question_text": q_def.get("text", ""),
            "risk_hint": q_def.get("risk_hint", "minimal"),
            "investigation_steps": steps,
            "scan_hint": scan_hint,
        })

    return {
        "total_answers": len(answers),
        "ai_systems_declared": len(yes_answers),
        "unknown_count": len(unknown_answers),
        "risk_breakdown": risk_breakdown,
        "recommendations": recommendations,
        "unknown_items": unknown_items,
    }'''

    if old_return_block not in content:
        print("ERROR: Could not find _analyze_responses return block", file=sys.stderr)
        sys.exit(1)
    content = content.replace(old_return_block, new_return_block)
    print("[2/4] Updated _analyze_responses() with unknown_items")

    # ─────────────────────────────────────────────
    # 3. Update combined-report to add cross_references
    # ─────────────────────────────────────────────

    # Insert cross-reference logic before the return statement of combined-report
    # Find the return { in combined-report — it starts with "    return {"
    # after "action_items": _generate_action_items(...)

    old_combined_return = '''        "total_ai_systems": len(scan_findings) + (q_analysis["ai_systems_declared"] if q_analysis else 0),
        "action_items": _generate_action_items(scan_findings, q_analysis),
    }


# ── Pomocné funkce ──'''

    new_combined_return = '''        "total_ai_systems": len(scan_findings) + (q_analysis["ai_systems_declared"] if q_analysis else 0),
        "action_items": _generate_action_items(scan_findings, q_analysis),
        "cross_references": _build_cross_references(
            questionnaire_answers, scan_findings, q_analysis
        ),
    }


# ── Pomocné funkce ──'''

    if old_combined_return not in content:
        print("ERROR: Could not find combined-report return block", file=sys.stderr)
        sys.exit(1)
    content = content.replace(old_combined_return, new_combined_return)
    print("[3/4] Updated combined-report endpoint with cross_references")

    # ─────────────────────────────────────────────
    # 4. Add _build_cross_references function before _analyze_responses
    # ─────────────────────────────────────────────

    cross_ref_function = '''def _build_cross_references(
    questionnaire_answers: list[QuestionnaireAnswer],
    scan_findings: list[dict],
    q_analysis: dict | None,
) -> list[dict]:
    """
    Porovná 'unknown' odpovědi z dotazníku se scan findings.
    Pokud sken detekoval něco, co uživatel označil jako 'Nevím',
    navrhne odpověď a vrátí cross-reference.
    """
    if not q_analysis or not scan_findings:
        return []

    # Sestavit mapu otázek
    question_map = {}
    for section in QUESTIONNAIRE_SECTIONS:
        for q in section["questions"]:
            question_map[q["key"]] = q

    # Najít unknown odpovědi
    unknown_keys = {
        a.question_key for a in questionnaire_answers if a.answer == "unknown"
    }

    if not unknown_keys:
        return []

    cross_refs = []
    matched_keys: set[str] = set()

    for finding in scan_findings:
        finding_name = finding.get("name", "")
        finding_category = finding.get("category", "")
        search_text = f"{finding_name} {finding_category}"

        for scan_keyword, q_key in SCAN_CROSS_REFERENCE.items():
            if q_key in unknown_keys and q_key not in matched_keys:
                if scan_keyword.lower() in search_text.lower():
                    q_def = question_map.get(q_key, {})
                    cross_refs.append({
                        "question_key": q_key,
                        "question_text": q_def.get("text", ""),
                        "user_answer": "unknown",
                        "scan_detected": True,
                        "scan_finding_name": finding_name,
                        "suggested_answer": "yes",
                        "message": (
                            f"Na vašem webu jsme detekovali \\"{finding_name}\\", "
                            f"pravděpodobně tedy ANO."
                        ),
                    })
                    matched_keys.add(q_key)

    return cross_refs


'''

    anchor2 = 'def _analyze_responses(answers: list[QuestionnaireAnswer]) -> dict:'
    if anchor2 not in content:
        print("ERROR: Could not find _analyze_responses definition", file=sys.stderr)
        sys.exit(1)
    content = content.replace(anchor2, cross_ref_function + anchor2)
    print("[4/4] Added _build_cross_references() function")

    return content


if __name__ == "__main__":
    input_path = sys.argv[1]
    output_path = sys.argv[2]

    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    patched = patch(content)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(patched)

    print(f"\nPatched file written to {output_path}")
