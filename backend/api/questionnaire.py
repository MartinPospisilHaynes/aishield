"""
AIshield.cz — Questionnaire API
Backend pro interaktivní dotazník o interních AI systémech.

Dotazník pokrývá oblasti, které skener webu nevidí:
- HR (AI pro nábor, hodnocení zaměstnanců)
- Finance (AI účetnictví, fraud detection)
- Marketing (AI generování obsahu, personalizace)
- Interní procesy (ChatGPT, Copilot, interní chatboti)
- Zákaznický servis (AI triage, automatické odpovědi)
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.database import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Definice dotazníku ──

QUESTIONNAIRE_SECTIONS = [
    {
        "id": "prohibited_systems",
        "title": "Zakázané AI praktiky",
        "description": "Systémy, které AI Act výslovně zakazuje (čl. 5). Pokuta až 35 mil. EUR.",
        "questions": [
            {
                "key": "uses_social_scoring",
                "text": "Bodujete nebo hodnotíte zaměstnance či zákazníky na základě jejich chování, sociálních interakcí nebo osobnostních rysů?",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "scoring_tool_name", "label": "Název systému", "type": "text"},
                        {"key": "scoring_scope", "label": "Kdo je hodnocen?", "type": "select",
                         "options": ["Zaměstnanci", "Zákazníci", "Obojí"]},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 5 odst. 1 písm. c) — zákaz sociálního scoringu",
            },
            {
                "key": "uses_subliminal_manipulation",
                "text": "Používáte AI k ovlivňování rozhodnutí osob technikami, kterých si nejsou vědomy (podprahové manipulace, dark patterns)?",
                "type": "yes_no_unknown",
                "risk_hint": "high",
                "ai_act_article": "čl. 5 odst. 1 písm. a) — zákaz podprahové manipulace",
            },
            {
                "key": "uses_realtime_biometric",
                "text": "Používáte biometrickou identifikaci v reálném čase na veřejně přístupných místech (rozpoznávání obličejů zaměstnanců, zákazníků)?",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "biometric_tool_name", "label": "Název systému", "type": "text"},
                        {"key": "biometric_purpose", "label": "Účel", "type": "select",
                         "options": ["Docházka zaměstnanců", "Kontrola přístupu", "Identifikace zákazníků", "Bezpečnost"]},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 5 odst. 1 písm. h) — zákaz biometrické identifikace v reálném čase",
            },
        ],
    },
    {
        "id": "internal_ai",
        "title": "Interní AI nástroje",
        "description": "Běžné AI nástroje, které zaměstnanci používají v práci.",
        "questions": [
            {
                "key": "uses_chatgpt",
                "text": "Používají zaměstnanci ChatGPT, Claude nebo jiné AI chatboty?",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "chatgpt_tool_name", "label": "Název nástroje (např. ChatGPT, Claude, Gemini)", "type": "text"},
                        {"key": "chatgpt_purpose", "label": "K čemu ho používáte?", "type": "text"},
                        {"key": "chatgpt_data_type", "label": "Jaká data do něj vkládáte?", "type": "select",
                         "options": ["Pouze veřejná data", "Interní dokumenty", "Osobní údaje zákazníků", "Finanční data"]},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 50 odst. 1 — povinnost transparentnosti",
            },
            {
                "key": "uses_copilot",
                "text": "Používáte GitHub Copilot, Cursor nebo jiného AI asistenta pro kód?",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "copilot_tool_name", "label": "Název nástroje", "type": "text"},
                        {"key": "copilot_code_type", "label": "Typ vyvíjeného software", "type": "text"},
                    ]
                },
                "risk_hint": "minimal",
                "ai_act_article": "čl. 50 — transparentnost AI generovaného kódu",
            },
            {
                "key": "uses_ai_content",
                "text": "Generujete obsah pomocí AI (texty, obrázky, videa)?",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "content_tool_name", "label": "Nástroj (DALL-E, Midjourney, Jasper...)", "type": "text"},
                        {"key": "content_published", "label": "Publikujete AI obsah veřejně?", "type": "select",
                         "options": ["Ano, na web/sociální sítě", "Pouze interně", "Ano, bez označení"]},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 50 odst. 4 — označení AI generovaného obsahu",
            },
            {
                "key": "uses_deepfake",
                "text": "Vytváříte nebo používáte syntetický obsah (deepfake videa, klonování hlasu, AI avatary)?",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "deepfake_tool_name", "label": "Název nástroje", "type": "text"},
                        {"key": "deepfake_disclosed", "label": "Označujete tento obsah jako AI generovaný?", "type": "select",
                         "options": ["Ano, vždy", "Někdy", "Ne"]},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 50 odst. 4 — povinnost označit deepfake obsah",
            },
        ],
    },
    {
        "id": "hr",
        "title": "HR a Nábor zaměstnanců",
        "description": "AI v personalistice patří mezi vysoce rizikové systémy dle Přílohy III.",
        "questions": [
            {
                "key": "uses_ai_recruitment",
                "text": "Používáte AI pro screening CV, hodnocení kandidátů nebo automatický nábor?",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "recruitment_tool", "label": "Název nástroje", "type": "text"},
                        {"key": "recruitment_autonomous", "label": "Rozhoduje AI samostatně o kandidátech?", "type": "select",
                         "options": ["Ano, automaticky filtruje", "Ne, pouze doporučuje", "Částečně"]},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 6 + Příloha III bod 4a — nábor zaměstnanců",
            },
            {
                "key": "uses_ai_employee_monitoring",
                "text": "Monitorujete zaměstnance pomocí AI (produktivita, emoce, chování)?",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "monitoring_type", "label": "Co monitorujete?", "type": "text"},
                        {"key": "monitoring_informed", "label": "Jsou zaměstnanci informováni?", "type": "select",
                         "options": ["Ano, písemně", "Ano, ústně", "Ne"]},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 6 + Příloha III bod 4b — monitorování zaměstnanců",
            },
            {
                "key": "uses_emotion_recognition",
                "text": "Používáte AI pro rozpoznávání emocí zaměstnanců nebo zákazníků?",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "emotion_tool_name", "label": "Název systému", "type": "text"},
                        {"key": "emotion_context", "label": "V jakém kontextu?", "type": "select",
                         "options": ["Pracovní prostředí", "Zákaznický servis", "Vzdělávání", "Bezpečnost"]},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 5 odst. 1 písm. f) — omezení rozpoznávání emocí na pracovišti",
            },
        ],
    },
    {
        "id": "finance",
        "title": "Finance a rozhodování",
        "description": "AI ve financích a rozhodovacích procesech s dopadem na jednotlivce.",
        "questions": [
            {
                "key": "uses_ai_accounting",
                "text": "Používáte AI pro účetnictví, fakturaci nebo finanční analýzy?",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "accounting_tool", "label": "Název nástroje (Fakturoid AI, Money S5...)", "type": "text"},
                        {"key": "accounting_decisions", "label": "Dělá AI autonomní finanční rozhodnutí?", "type": "select",
                         "options": ["Ne, pouze asistuje", "Ano, schvaluje platby", "Ano, hodnotí kreditní riziko"]},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 50 — transparentnost",
            },
            {
                "key": "uses_ai_creditscoring",
                "text": "Používáte AI pro hodnocení kreditního rizika nebo scoring zákazníků?",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "credit_tool", "label": "Název systému", "type": "text"},
                        {"key": "credit_impact", "label": "Ovlivňuje AI rozhodnutí o úvěrech/smlouvách?", "type": "select",
                         "options": ["Ano, přímo rozhoduje", "Pouze doporučuje", "Ne"]},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 6 + Příloha III bod 5b — kreditní scoring",
            },
            {
                "key": "uses_ai_insurance",
                "text": "Používáte AI při stanovení pojistného, hodnocení pojistných událostí nebo risk managementu?",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "insurance_tool", "label": "Název systému", "type": "text"},
                        {"key": "insurance_impact", "label": "Ovlivňuje AI cenu nebo dostupnost pojištění?", "type": "select",
                         "options": ["Ano, přímo", "Pouze doporučuje", "Ne"]},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 6 + Příloha III bod 5a — pojišťovnictví",
            },
        ],
    },
    {
        "id": "customer_service",
        "title": "Zákaznický servis a komunikace",
        "description": "AI systémy v kontaktu se zákazníky vyžadují transparentnost.",
        "questions": [
            {
                "key": "uses_ai_email_auto",
                "text": "Automaticky generujete odpovědi na emaily zákazníků pomocí AI?",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "email_tool", "label": "Název nástroje", "type": "text"},
                        {"key": "email_disclosed", "label": "Ví zákazník, že odpovídá AI?", "type": "select",
                         "options": ["Ano, je to označeno", "Ne", "Někdy"]},
                    ]
                },
                "risk_hint": "limited",
                "ai_act_article": "čl. 50 odst. 1 — povinnost informovat o AI",
            },
            {
                "key": "uses_ai_decision",
                "text": "Rozhoduje AI o reklamacích, slevách nebo přístupu ke službám?",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "decision_scope", "label": "O čem AI rozhoduje?", "type": "text"},
                        {"key": "decision_human_review", "label": "Je k dispozici lidský přezkum?", "type": "select",
                         "options": ["Ano, vždy", "Na vyžádání", "Ne"]},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 14 — lidský dohled nad vysoce rizikovými systémy",
            },
        ],
    },
    {
        "id": "infrastructure_safety",
        "title": "Kritická infrastruktura a bezpečnost",
        "description": "AI v kritické infrastruktuře spadá do kategorie vysokého rizika.",
        "questions": [
            {
                "key": "uses_ai_critical_infra",
                "text": "Používáte AI pro řízení nebo monitorování kritické infrastruktury (energetika, doprava, vodohospodářství)?",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "infra_tool_name", "label": "Název systému", "type": "text"},
                        {"key": "infra_sector", "label": "Sektor", "type": "select",
                         "options": ["Energetika", "Doprava", "Vodohospodářství", "Telekomunikace", "Zdravotnictví", "Jiný"]},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 6 + Příloha III bod 2 — kritická infrastruktura",
            },
            {
                "key": "uses_ai_safety_component",
                "text": "Je AI součástí bezpečnostní komponenty produktu (např. autonomní řízení, medicínské přístroje, průmyslová automatizace)?",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "safety_product", "label": "O jaký produkt jde?", "type": "text"},
                        {"key": "safety_ce_mark", "label": "Má produkt CE označení?", "type": "select",
                         "options": ["Ano", "Ne", "V procesu"]},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 6 odst. 1 — AI jako bezpečnostní komponenta",
            },
        ],
    },
    {
        "id": "data_protection",
        "title": "Ochrana dat a GDPR",
        "description": "AI Act doplňuje GDPR — obě nařízení platí současně.",
        "questions": [
            {
                "key": "ai_processes_personal_data",
                "text": "Zpracovávají vaše AI systémy osobní údaje (jména, emaily, rodná čísla)?",
                "type": "yes_no_unknown",
                "followup": {
                    "condition": "yes",
                    "fields": [
                        {"key": "personal_data_types", "label": "Jaké osobní údaje?", "type": "text"},
                        {"key": "dpia_done", "label": "Provedli jste DPIA (posouzení vlivu na ochranu dat)?", "type": "select",
                         "options": ["Ano", "Ne", "Nevím co to je"]},
                    ]
                },
                "risk_hint": "high",
                "ai_act_article": "čl. 10 — správa dat pro vysoce rizikové AI",
            },
            {
                "key": "ai_data_stored_eu",
                "text": "Jsou data vašich AI systémů uložena v EU?",
                "type": "yes_no_unknown",
                "risk_hint": "limited",
                "ai_act_article": "Nařízení GDPR čl. 44+ — přenos dat do třetích zemí",
            },
            {
                "key": "ai_transparency_docs",
                "text": "Máte dokumentaci o tom, jaké AI systémy ve firmě používáte (registr AI)?",
                "type": "yes_no_unknown",
                "risk_hint": "limited",
                "ai_act_article": "čl. 49 — registrace vysoce rizikových AI systémů v EU databázi",
            },
        ],
    },
]


# ── Pydantic modely ──

class QuestionnaireAnswer(BaseModel):
    """Jedna odpověď z dotazníku."""
    question_key: str
    section: str
    answer: str = Field(..., pattern="^(yes|no|unknown)$")
    details: Optional[dict] = None
    tool_name: Optional[str] = None


class QuestionnaireSubmission(BaseModel):
    """Kompletní odeslání dotazníku."""
    company_id: str
    scan_id: Optional[str] = None
    answers: list[QuestionnaireAnswer]


class QuestionnaireAnalysis(BaseModel):
    """Výsledek analýzy dotazníku."""
    company_id: str
    total_answers: int
    ai_systems_declared: int
    risk_breakdown: dict
    recommendations: list[dict]


# ── Endpointy ──

@router.get("/questionnaire/structure")
async def get_questionnaire_structure():
    """Vrátí strukturu dotazníku — sekce a otázky."""
    return {
        "sections": QUESTIONNAIRE_SECTIONS,
        "total_questions": sum(len(s["questions"]) for s in QUESTIONNAIRE_SECTIONS),
        "estimated_time_minutes": 5,
    }


@router.post("/questionnaire/submit")
async def submit_questionnaire(submission: QuestionnaireSubmission):
    """
    Uloží odpovědi z dotazníku do DB.
    Vrátí analýzu rizik + doporučení.
    """
    supabase = get_supabase()

    if not submission.answers:
        raise HTTPException(status_code=400, detail="Dotazník je prázdný.")

    # Najít nebo vytvořit anonymního clienta pro tuto firmu
    client_id = await _get_or_create_client(supabase, submission.company_id)

    # Uložit každou odpověď
    saved_count = 0
    for ans in submission.answers:
        try:
            row = {
                "client_id": client_id,
                "section": ans.section,
                "question_key": ans.question_key,
                "answer": ans.answer,
                "details": ans.details,
                "tool_name": ans.tool_name,
            }
            supabase.table("questionnaire_responses").insert(row).execute()
            saved_count += 1
        except Exception as e:
            logger.error(f"[Questionnaire] Chyba při ukládání odpovědi {ans.question_key}: {e}")

    logger.info(f"[Questionnaire] Uloženo {saved_count}/{len(submission.answers)} odpovědí pro company {submission.company_id}")

    # Analyzovat odpovědi
    analysis = _analyze_responses(submission.answers)

    # Pokud máme scan_id, propojit s nálezem
    if submission.scan_id:
        analysis["scan_id"] = submission.scan_id

    return {
        "status": "saved",
        "saved_count": saved_count,
        "analysis": analysis,
    }


@router.get("/questionnaire/{company_id}/results")
async def get_questionnaire_results(company_id: str):
    """Vrátí uložené odpovědi a analýzu pro firmu."""
    supabase = get_supabase()

    client_id = await _get_client_id_for_company(supabase, company_id)
    if not client_id:
        raise HTTPException(status_code=404, detail="Dotazník nebyl vyplněn.")

    result = supabase.table("questionnaire_responses") \
        .select("*") \
        .eq("client_id", client_id) \
        .order("submitted_at", desc=True) \
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Dotazník nebyl vyplněn.")

    # Sestavit odpovědi do QuestionnaireAnswer formátu
    answers = []
    for row in result.data:
        answers.append(QuestionnaireAnswer(
            question_key=row["question_key"],
            section=row["section"],
            answer=row["answer"],
            details=row.get("details"),
            tool_name=row.get("tool_name"),
        ))

    analysis = _analyze_responses(answers)

    return {
        "company_id": company_id,
        "answers": [a.model_dump() for a in answers],
        "analysis": analysis,
        "submitted_at": result.data[0].get("submitted_at"),
    }


@router.get("/questionnaire/{company_id}/combined-report")
async def get_combined_report(company_id: str, scan_id: Optional[str] = None):
    """
    Kombinovaný report: výsledky skenu + dotazníku.
    Úkol 16: propojení dotazníku se skenem.
    """
    supabase = get_supabase()

    # 1. Načíst odpovědi z dotazníku
    client_id = await _get_client_id_for_company(supabase, company_id)

    q_result = None
    if client_id:
        q_result = supabase.table("questionnaire_responses") \
            .select("*") \
            .eq("client_id", client_id) \
            .execute()

    questionnaire_answers = []
    for row in (q_result.data or []):
        questionnaire_answers.append(QuestionnaireAnswer(
            question_key=row["question_key"],
            section=row["section"],
            answer=row["answer"],
            details=row.get("details"),
            tool_name=row.get("tool_name"),
        ))

    # 2. Načíst findings ze skenu
    scan_findings = []
    scan_info = None
    if scan_id:
        s_result = supabase.table("scans").select("*").eq("id", scan_id).single().execute()
        scan_info = s_result.data

        f_result = supabase.table("findings") \
            .select("*") \
            .eq("scan_id", scan_id) \
            .neq("source", "ai_classified_fp") \
            .execute()
        scan_findings = f_result.data or []

    # 3. Analýza dotazníku
    q_analysis = _analyze_responses(questionnaire_answers) if questionnaire_answers else None

    # 4. Celkové rizikové skóre
    all_risks = []
    for f in scan_findings:
        all_risks.append(f.get("risk_level", "minimal"))
    if q_analysis:
        for lvl, count in q_analysis["risk_breakdown"].items():
            all_risks.extend([lvl] * count)

    risk_counts = {"high": 0, "limited": 0, "minimal": 0}
    for r in all_risks:
        if r in risk_counts:
            risk_counts[r] += 1

    # Celkový risk rating
    if risk_counts["high"] > 0:
        overall_risk = "high"
        overall_emoji = "🔴"
        overall_text = "VYSOKÉ RIZIKO — Vyžaduje okamžitou akci"
    elif risk_counts["limited"] > 0:
        overall_risk = "limited"
        overall_emoji = "🟡"
        overall_text = "OMEZENÉ RIZIKO — Transparentnost nutná"
    else:
        overall_risk = "minimal"
        overall_emoji = "🟢"
        overall_text = "MINIMÁLNÍ RIZIKO — Dobrý stav"

    return {
        "company_id": company_id,
        "scan_id": scan_id,
        "overall_risk": overall_risk,
        "overall_risk_text": f"{overall_emoji} {overall_text}",
        "risk_breakdown": risk_counts,
        "scan_summary": {
            "url": scan_info.get("url") if scan_info else None,
            "status": scan_info.get("status") if scan_info else None,
            "findings_count": len(scan_findings),
            "findings": [
                {
                    "name": f["name"],
                    "category": f["category"],
                    "risk_level": f["risk_level"],
                    "ai_act_article": f.get("ai_act_article", ""),
                    "action_required": f.get("action_required", ""),
                }
                for f in scan_findings
            ],
        },
        "questionnaire_summary": {
            "completed": bool(questionnaire_answers),
            "answers_count": len(questionnaire_answers),
            "ai_systems_declared": q_analysis["ai_systems_declared"] if q_analysis else 0,
            "recommendations": q_analysis["recommendations"] if q_analysis else [],
        },
        "total_ai_systems": len(scan_findings) + (q_analysis["ai_systems_declared"] if q_analysis else 0),
        "action_items": _generate_action_items(scan_findings, q_analysis),
    }


# ── Pomocné funkce ──

def _analyze_responses(answers: list[QuestionnaireAnswer]) -> dict:
    """Analyzuje odpovědi a vrátí rizikový profil + doporučení."""

    # Najít definice otázek
    question_map = {}
    for section in QUESTIONNAIRE_SECTIONS:
        for q in section["questions"]:
            question_map[q["key"]] = q

    yes_answers = [a for a in answers if a.answer == "yes"]
    risk_breakdown = {"high": 0, "limited": 0, "minimal": 0}
    recommendations = []

    for ans in yes_answers:
        q_def = question_map.get(ans.question_key)
        if not q_def:
            continue

        risk = q_def.get("risk_hint", "minimal")
        if risk in risk_breakdown:
            risk_breakdown[risk] += 1

        # Generovat doporučení
        tool_name = ans.tool_name or "AI systém"
        recommendations.append({
            "question_key": ans.question_key,
            "tool_name": tool_name,
            "risk_level": risk,
            "ai_act_article": q_def.get("ai_act_article", ""),
            "recommendation": _get_recommendation(ans.question_key, risk, tool_name, ans.details),
            "priority": "vysoká" if risk == "high" else "střední" if risk == "limited" else "nízká",
        })

    # Seřadit doporučení: high → limited → minimal
    risk_order = {"high": 0, "limited": 1, "minimal": 2}
    recommendations.sort(key=lambda r: risk_order.get(r["risk_level"], 3))

    return {
        "total_answers": len(answers),
        "ai_systems_declared": len(yes_answers),
        "risk_breakdown": risk_breakdown,
        "recommendations": recommendations,
    }


def _get_recommendation(question_key: str, risk: str, tool_name: str, details: Optional[dict]) -> str:
    """Vrátí specifické doporučení na základě odpovědi."""
    recs = {
        # Zakázané praktiky
        "uses_social_scoring": f"ZAKÁZANÝ SYSTÉM! Sociální scoring je dle čl. 5 AI Act zakázán. Okamžitě ukončete provoz {tool_name}. Pokuta až 35 mil. EUR nebo 7 % obratu.",
        "uses_subliminal_manipulation": "ZAKÁZANÝ SYSTÉM! Podprahová manipulace je dle čl. 5 AI Act zakázána. Proveďte audit všech AI systémů ovlivňujících rozhodování uživatelů.",
        "uses_realtime_biometric": f"ZAKÁZANÝ/VYSOCE RIZIKOVÝ systém! Biometrická identifikace v reálném čase je dle čl. 5 AI Act silně omezena. Proveďte okamžitý audit {tool_name}.",
        # Interní AI
        "uses_chatgpt": f"Zavedete interní směrnici pro používání {tool_name}. Zakažte vkládání osobních údajů zákazníků. Proškolte zaměstnance o AI Act.",
        "uses_copilot": f"Zajistěte, aby AI generovaný kód prošel code review. Dokumentujte použití {tool_name} v development procesu.",
        "uses_ai_content": f"Označujte AI generovaný obsah dle čl. 50 odst. 4 AI Act. Přidejte metadata o AI původu.",
        "uses_deepfake": f"Povinnost označit syntetický obsah dle čl. 50 odst. 4. Přidejte viditelné označení ke všem AI generovaným médiím z {tool_name}.",
        # HR
        "uses_ai_recruitment": f"VYSOCE RIZIKOVÝ systém! {tool_name} spadá pod čl. 6 AI Act. Proveďte posouzení shody (conformity assessment), zajistěte lidský dohled a transparentnost vůči kandidátům.",
        "uses_ai_employee_monitoring": f"VYSOCE RIZIKOVÝ systém! Monitorování zaměstnanců AI vyžaduje souhlas, DPIA a transparentnost. Zajistěte soulad s GDPR čl. 22 a AI Act čl. 6.",
        "uses_emotion_recognition": f"ZAKÁZÁNO na pracovišti a ve vzdělávání! Rozpoznávání emocí je dle čl. 5 odst. 1 písm. f) omezeno. Proveďte audit {tool_name} a konzultujte s právníkem.",
        # Finance
        "uses_ai_accounting": f"Dokumentujte použití {tool_name} a zajistěte audit trail pro finanční rozhodnutí AI.",
        "uses_ai_creditscoring": f"VYSOCE RIZIKOVÝ systém! Kreditní scoring je regulován přílohou III AI Act. Proveďte conformity assessment a zajistěte právo na vysvětlení rozhodnutí.",
        "uses_ai_insurance": f"VYSOCE RIZIKOVÝ systém! AI v pojišťovnictví spadá pod Přílohu III bod 5a. Zajistěte posouzení shody a právo pojistníka na vysvětlení.",
        # Zákaznický servis
        "uses_ai_email_auto": f"Informujte zákazníky, že komunikují s AI (čl. 50 odst. 1). Přidejte jasné označení do automatických odpovědí.",
        "uses_ai_decision": f"AI rozhodující o právech zákazníků vyžaduje lidský dohled (čl. 14 AI Act). Zajistěte právo na přezkum člověkem.",
        # Kritická infrastruktura
        "uses_ai_critical_infra": f"VYSOCE RIZIKOVÝ systém! AI v kritické infrastruktuře spadá pod Přílohu III bod 2. Proveďte conformity assessment a zajistěte systém řízení rizik dle čl. 9.",
        "uses_ai_safety_component": f"VYSOCE RIZIKOVÝ systém! AI jako bezpečnostní komponenta spadá pod čl. 6 odst. 1. Zajistěte CE označení a conformity assessment.",
        # Ochrana dat
        "ai_processes_personal_data": f"Proveďte DPIA dle GDPR. Zajistěte právní základ pro zpracování a minimalizaci dat v AI systémech.",
        "ai_data_stored_eu": "Ověřte, kde jsou data AI systémů fyzicky uložena. Pro přenos mimo EU zajistěte adekvátní záruky (SCC, adequacy decision).",
        "ai_transparency_docs": "Vytvořte registr všech AI systémů ve firmě. Pro vysoce rizikové systémy je registrace v EU databázi povinná (čl. 49).",
    }
    return recs.get(question_key, f"Zkontrolujte soulad {tool_name} s AI Act a dokumentujte jeho použití.")


def _generate_action_items(scan_findings: list, q_analysis: Optional[dict]) -> list[dict]:
    """Generuje prioritizovaný seznam kroků ke compliance."""
    items = []

    # Z findings ze skenu
    for f in scan_findings:
        if f.get("risk_level") == "high":
            items.append({
                "priority": "🔴 VYSOKÁ",
                "action": f"Proveďte conformity assessment pro {f['name']}",
                "source": "scan",
                "risk_level": "high",
            })
        elif f.get("risk_level") == "limited":
            items.append({
                "priority": "🟡 STŘEDNÍ",
                "action": f.get("action_required", f"Zajistěte transparentnost pro {f['name']}"),
                "source": "scan",
                "risk_level": "limited",
            })

    # Z dotazníku
    if q_analysis:
        for rec in q_analysis.get("recommendations", []):
            if rec["risk_level"] == "high":
                items.append({
                    "priority": "🔴 VYSOKÁ",
                    "action": rec["recommendation"],
                    "source": "questionnaire",
                    "risk_level": "high",
                })
            elif rec["risk_level"] == "limited":
                items.append({
                    "priority": "🟡 STŘEDNÍ",
                    "action": rec["recommendation"],
                    "source": "questionnaire",
                    "risk_level": "limited",
                })

    # Obecná doporučení
    items.append({
        "priority": "📋 OBECNÉ",
        "action": "Jmenujte odpovědnou osobu za AI compliance ve firmě.",
        "source": "general",
        "risk_level": "info",
    })
    items.append({
        "priority": "📋 OBECNÉ",
        "action": "Vytvořte registr všech AI systémů používaných ve firmě.",
        "source": "general",
        "risk_level": "info",
    })

    # Seřadit: high → limited → info
    risk_order = {"high": 0, "limited": 1, "minimal": 2, "info": 3}
    items.sort(key=lambda x: risk_order.get(x["risk_level"], 4))

    return items


async def _get_or_create_client(supabase, company_id: str) -> str:
    """
    Najde nebo vytvoří anonymního clienta pro company.
    Vrátí client_id (UUID).
    Zatím nemáme auth, tak vytvoříme 'anonymous' clienta.
    """
    # Zkusit najít existujícího clienta pro tuto firmu
    result = supabase.table("clients") \
        .select("id") \
        .eq("company_id", company_id) \
        .limit(1) \
        .execute()

    if result.data:
        return result.data[0]["id"]

    # Vytvořit nového anonymního clienta
    new_client = supabase.table("clients").insert({
        "company_id": company_id,
        "contact_name": "Anonymní uživatel",
        "email": f"anonymous-{company_id[:8]}@aishield.cz",
        "contact_role": "questionnaire",
    }).execute()

    client_id = new_client.data[0]["id"]
    logger.info(f"[Questionnaire] Vytvořen anonymní client {client_id} pro company {company_id}")
    return client_id


async def _get_client_id_for_company(supabase, company_id: str) -> str | None:
    """Najde client_id pro company_id."""
    result = supabase.table("clients") \
        .select("id") \
        .eq("company_id", company_id) \
        .limit(1) \
        .execute()
    return result.data[0]["id"] if result.data else None
