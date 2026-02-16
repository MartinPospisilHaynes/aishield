"""
AIshield.cz — Dashboard API
Endpointy pro zákaznický portál — přehled compliance stavu,
dokumenty, skeny, akční plán.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from backend.database import get_supabase
from backend.api.auth import AuthUser, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/me")
async def get_my_dashboard(user: AuthUser = Depends(get_current_user)):
    """
    Vrátí kompletní data pro dashboard přihlášeného uživatele.
    Najde firmu podle emailu z JWT tokenu.
    """
    web_url = user.metadata.get("web_url", "") if user.metadata else ""
    return await _load_dashboard(user.email, web_url=web_url)


@router.get("/{user_email}")
async def get_dashboard_data(user_email: str, user: AuthUser = Depends(get_current_user)):
    """
    Vrátí dashboard data pro konkrétní email.
    Uživatel může přistoupit pouze ke svým datům (nebo admin k jakýmkoliv).
    """
    from backend.api.auth import ADMIN_EMAILS

    # Uživatel může vidět jen svá data, admin může vidět všechna
    if user.email != user_email and user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Přístup odepřen")

    web_url = user.metadata.get("web_url", "") if user.metadata else ""
    return await _load_dashboard(user_email, web_url=web_url)


async def _load_dashboard(user_email: str, web_url: str = ""):
    """Interní funkce — načte dashboard data pro daný email."""
    supabase = get_supabase()

    # 1. Najít firmu podle emailu
    company_res = supabase.table("companies").select("*").eq(
        "email", user_email
    ).execute()

    company = company_res.data[0] if company_res.data else None

    # 1b. Fallback: zkusit najít podle web_url z user_metadata
    #     (pro případ, že sken proběhl dříve než se propojil email)
    if not company and web_url:
        url_variants = [web_url]
        # Zkusit i varianty s/bez www
        if "://www." in web_url:
            url_variants.append(web_url.replace("://www.", "://"))
        else:
            url_variants.append(web_url.replace("://", "://www."))
        for url_v in url_variants:
            company_res2 = supabase.table("companies").select("*").eq(
                "url", url_v
            ).limit(1).execute()
            if company_res2.data:
                company = company_res2.data[0]
                # Propojíme — nastavíme email na company, aby příště fungovalo rovnou
                try:
                    supabase.table("companies").update(
                        {"email": user_email}
                    ).eq("id", company["id"]).execute()
                except Exception:
                    pass
                break

    if not company:
        # Zkusit najít podle objednávky
        order_res = supabase.table("orders").select("*").eq(
            "email", user_email
        ).order("created_at", desc=True).execute()

        return {
            "company": None,
            "scans": [],
            "findings": [],
            "documents": [],
            "orders": order_res.data or [],
            "questionnaire_status": "nevyplněn",
            "compliance_score": None,
        }

    company_id = company["id"]

    # 2. Skeny
    scans_res = supabase.table("scans").select("*").eq(
        "company_id", company_id
    ).order("created_at", desc=True).limit(10).execute()

    # 3. Nálezy (z posledního skenu) — filtrujeme false positives
    findings = []
    # Nástroje, které NEJSOU AI systémy (pro zpětnou kompatibilitu se starými skeny)
    NON_AI_TOOLS = {"google tag manager", "google analytics 4", "seznam retargeting", "heureka"}
    if scans_res.data:
        latest_scan_id = scans_res.data[0]["id"]
        findings_res = supabase.table("findings").select("*").eq(
            "scan_id", latest_scan_id
        ).neq("source", "ai_classified_fp").neq(
            "risk_level", "none"
        ).order("risk_level", desc=True).execute()
        # Bezpečnostní filtr: vyřadíme i staré záznamy non-AI nástrojů
        findings = [
            f for f in (findings_res.data or [])
            if f.get("name", "").lower() not in NON_AI_TOOLS
        ]

    # 4. Dokumenty
    docs_res = supabase.table("documents").select("*").eq(
        "company_id", company_id
    ).order("created_at", desc=True).execute()

    # 5. Objednávky
    orders_res = supabase.table("orders").select("*").eq(
        "email", user_email
    ).order("created_at", desc=True).execute()

    # 6. Dotazník — přes tabulku clients (client.company_id → questionnaire_responses.client_id)
    # Lidsky čitelné popisy pro dashboard (laik musí pochopit, o co jde)
    _HUMAN_SUMMARIES = {
        "develops_own_ai": "Vyvíjíte vlastní AI → musíte dokumentovat svou roli a povinnosti",
        "uses_social_scoring": "Hodnocení lidí skórem chování → může být zakázaná praktika",
        "uses_subliminal_manipulation": "AI ovlivňuje lidi bez jejich vědomí → zakázaná praktika",
        "uses_realtime_biometric": "Rozpoznávání obličeje / otisku prstu → silně regulováno",
        "uses_chatgpt": "Zaměstnanci používají AI chaty → musíte nastavit pravidla",
        "uses_copilot": "AI píše kód → zajistěte kontrolu a dokumentaci",
        "uses_ai_content": "AI generuje texty nebo obrázky → musíte je označit",
        "uses_deepfake": "Syntetická videa nebo klonování hlasu → povinné označení",
        "uses_ai_recruitment": "AI třídí životopisy / kandidáty → vysoce rizikový systém",
        "uses_ai_employee_monitoring": "AI sleduje zaměstnance → vysoce rizikový systém",
        "uses_emotion_recognition": "AI rozpoznává emoce → na pracovišti zakázáno",
        "uses_ai_accounting": "AI v účetnictví → dokumentujte a zajistěte transparentnost",
        "uses_ai_creditscoring": "AI hodnotí bonitu zákazníků → vysoce rizikový systém",
        "uses_ai_insurance": "AI v pojišťovnictví → vysoce rizikový systém",
        "uses_ai_chatbot": "Chatbot na webu → zákazník musí vědět, že mluví s AI",
        "uses_ai_email_auto": "AI odpovídá na emaily → zákazník musí být informován",
        "uses_ai_decision": "AI rozhoduje o reklamacích / slevách → vyžaduje lidský dohled",
        "uses_dynamic_pricing": "AI mění ceny podle zákazníka → může být manipulativní",
        "uses_ai_critical_infra": "AI řídí kritickou infrastrukturu → vysoce rizikový systém",
        "uses_ai_safety_component": "AI v bezpečnostní komponentě → vyžaduje CE a registraci",
        "ai_processes_personal_data": "AI zpracovává osobní údaje → nutné posouzení dopadu (DPIA)",
        "ai_data_stored_eu": "Data AI systémů mimo EU → riziko porušení GDPR",
        "ai_transparency_docs": "Chybí přehled AI ve firmě → musíte vést interní evidenci",
        "has_ai_training": "Zaměstnanci neproškoleni v AI → povinnost od února 2025",
        "has_ai_guidelines": "Chybí firemní pravidla pro AI → doporučeno pro soulad",
    }

    questionnaire_status = "nevyplněn"
    questionnaire_findings = []
    questionnaire_unknowns = []
    questionnaire_summary = {}
    try:
        # Najdi klienta pro tuto firmu
        client_res = supabase.table("clients").select("id").eq(
            "company_id", company_id
        ).limit(1).execute()
        if client_res.data:
            client_id = client_res.data[0]["id"]
            quest_res = supabase.table("questionnaire_responses").select("*").eq(
                "client_id", client_id
            ).execute()
            if quest_res.data:
                # Count total required questions dynamically
                from backend.api.questionnaire import QUESTIONNAIRE_SECTIONS
                all_question_keys = {q["key"] for s in QUESTIONNAIRE_SECTIONS for q in s["questions"]}
                required_count = len(all_question_keys)
                answered_count = len(quest_res.data)
                if answered_count >= required_count:
                    questionnaire_status = "dokončen"
                else:
                    questionnaire_status = f"rozpracován ({answered_count}/{required_count})"
                # Analyzovat odpovědi a vygenerovat findings
                try:
                    from backend.api.questionnaire import (
                        QuestionnaireAnswer,
                        _analyze_responses,
                        QUESTIONNAIRE_SECTIONS,
                    )
                    # Sestavit QuestionnaireAnswer objekty
                    q_answers = []
                    for row in quest_res.data:
                        q_answers.append(QuestionnaireAnswer(
                            question_key=row["question_key"],
                            section=row["section"],
                            answer=row["answer"],
                            details=row.get("details"),
                            tool_name=row.get("tool_name"),
                        ))

                    analysis = _analyze_responses(q_answers)

                    # Vytvořit question_map pro texty otázek
                    question_map = {}
                    for section in QUESTIONNAIRE_SECTIONS:
                        for q in section["questions"]:
                            question_map[q["key"]] = q

                    # Recommendations → questionnaire_findings (pro dashboard)
                    for rec in analysis.get("recommendations", []):
                        q_def = question_map.get(rec["question_key"], {})
                        q_text = q_def.get("text", rec["question_key"])

                        # "nevím" odpovědi jdou do seznamu unknowns
                        is_unknown = any(
                            a.answer == "unknown" and a.question_key == rec["question_key"]
                            for a in q_answers
                        )
                        if is_unknown:
                            questionnaire_unknowns.append({
                                "question_key": rec["question_key"],
                                "question_text": q_text,
                                "risk_level": rec["risk_level"],
                                "ai_act_article": rec.get("ai_act_article", ""),
                                "recommendation": rec["recommendation"],
                                "priority": rec["priority"],
                                "severity": rec.get("severity", "limited"),
                                "severity_color": rec.get("severity_color", "yellow"),
                                "severity_label": rec.get("severity_label", "Omezené riziko"),
                                "checklist": rec.get("checklist", []),
                            })
                        else:
                            # Najít odpovídající odpověď pro tool_name / details
                            matching_answer = next(
                                (a for a in q_answers if a.question_key == rec["question_key"]),
                                None,
                            )
                            tool_name = rec.get("tool_name", "")
                            if matching_answer and matching_answer.details:
                                # Pokusit se zjistit název nástrojů z details
                                tool_names_list = []
                                other_texts = []
                                for dk, dv in matching_answer.details.items():
                                    # Sbírat _other pole (uživatelem zadaný vlastní název)
                                    if dk.endswith("_other") and isinstance(dv, str) and dv.strip():
                                        other_texts.append(dv.strip())
                                    # Sbírat tool/nástroj pole
                                    elif ("tool" in dk or dk.endswith("_tool")) and dv and not dk.endswith("_other"):
                                        if isinstance(dv, list):
                                            # Filtrovat "Jiný"/"Jiné" z výběru
                                            filtered = [v for v in dv if v not in ("Jiný", "Jiné")]
                                            tool_names_list.extend(filtered)
                                        elif isinstance(dv, str) and dv not in ("Jiný", "Jiné"):
                                            tool_names_list.append(dv)
                                # Přidat vlastní názvy z _other polí
                                tool_names_list.extend(other_texts)
                                if tool_names_list:
                                    tool_name = ", ".join(tool_names_list)

                            questionnaire_findings.append({
                                "question_key": rec["question_key"],
                                "name": tool_name or q_text,
                                "category": q_def.get("ai_act_article", ""),
                                "human_summary": _HUMAN_SUMMARIES.get(rec["question_key"], q_text),
                                "risk_level": rec["risk_level"],
                                "ai_act_article": rec.get("ai_act_article", ""),
                                "action_required": rec["recommendation"],
                                "priority": rec["priority"],
                                "source": "questionnaire",
                            })

                    questionnaire_summary = {
                        "total_answers": analysis.get("total_answers", 0),
                        "ai_systems_declared": analysis.get("ai_systems_declared", 0),
                        "unknown_count": analysis.get("unknown_count", 0),
                        "risk_breakdown": analysis.get("risk_breakdown", {}),
                    }
                    logger.info(
                        f"[Dashboard] Questionnaire analysis: "
                        f"{len(questionnaire_findings)} findings, "
                        f"{len(questionnaire_unknowns)} unknowns "
                        f"for company {company_id}"
                    )
                except Exception as e:
                    logger.error(f"[Dashboard] Chyba při analýze dotazníku: {e}")
    except Exception:
        pass  # Tabulka nemusí existovat

    # 7. Compliance skóre
    total_findings = len(findings)
    resolved = sum(
        1 for f in findings
        if f.get("confirmed_by_client") == "false_positive"
        or f.get("status") == "resolved"
    )
    compliance_score = (
        round((resolved / total_findings) * 100) if total_findings > 0 else None
    )

    return {
        "company": {
            "id": company_id,
            "name": company.get("name", ""),
            "url": company.get("url", ""),
            "created_at": company.get("created_at", ""),
            "workflow_status": company.get("workflow_status", "new"),
        },
        "scans": [
            {
                "id": s["id"],
                "url": s.get("url", ""),
                "status": s.get("status", ""),
                "total_findings": s.get("total_findings", 0),
                "created_at": s.get("created_at", ""),
                "finished_at": s.get("finished_at"),
            }
            for s in (scans_res.data or [])
        ],
        "findings": [
            {
                "id": f["id"],
                "name": f.get("name", ""),
                "category": f.get("category", ""),
                "risk_level": f.get("risk_level", ""),
                "ai_act_article": f.get("ai_act_article", ""),
                "action_required": f.get("action_required", ""),
                "confirmed_by_client": f.get("confirmed_by_client"),
                "status": f.get("status", "open"),
            }
            for f in findings
        ],
        "documents": [
            {
                "id": d["id"],
                "template_key": d.get("template_key", ""),
                "name": d.get("name", ""),
                "file_url": d.get("file_url", ""),
                "created_at": d.get("created_at", ""),
            }
            for d in (docs_res.data or [])
        ],
        "orders": [
            {
                "order_number": o.get("order_number", ""),
                "plan": o.get("plan", ""),
                "amount": o.get("amount", 0),
                "status": o.get("status", ""),
                "created_at": o.get("created_at", ""),
                "paid_at": o.get("paid_at"),
            }
            for o in (orders_res.data or [])
        ],
        "questionnaire_status": questionnaire_status,
        "questionnaire_findings": questionnaire_findings,
        "questionnaire_unknowns": questionnaire_unknowns,
        "questionnaire_summary": questionnaire_summary,
        "compliance_score": compliance_score,
    }
