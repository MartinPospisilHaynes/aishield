"""
AIshield.cz — Document Generation Pipeline v3

4-modulová architektura: M1 Generator → M2 EU Critic → M3 Client Critic → M4 Refiner
Sekvenční zpracování: každý dokument projde celým pipeline před dalším.

Model přiřazení:
  M1: Gemini 3.1 Pro (generátor)
  M2: Claude Sonnet 4 (EU inspektor)
  M3: Gemini 3.1 Pro (klientský kritik)
  M4: Claude Sonnet 4 (refiner)
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from backend.database import get_supabase
from backend.documents.pdf_generator import html_to_pdf, save_to_supabase_storage
from backend.documents.pdf_renderer import render_section_html
from backend.documents.m1_generator import generate_draft, DOCUMENT_NAMES, PROMPT_BUILDERS
from backend.documents.m2_eu_critic import review_eu
from backend.documents.m3_client_critic import review_client
from backend.documents.m4_refiner import refine
from backend.documents.m5_prompt_optimizer import analyze_and_optimize
from backend.documents.generation_report import send_generation_report

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════
# DOCUMENT KEYS — 11 dokumentů zpracovávaných pipeline
# ══════════════════════════════════════════════════════════════════════

DOCUMENT_KEYS = [
    "compliance_report",
    "action_plan",
    "ai_register",
    "training_outline",
    "chatbot_notices",
    "ai_policy",
    "incident_response_plan",
    "dpia_template",
    "vendor_checklist",
    "monitoring_plan",
    "transparency_human_oversight",
    "transparency_page",
    "training_presentation",
]

SECTION_SLUG = {
    "compliance_report": "compliance_report",
    "action_plan": "akcni_plan",
    "ai_register": "registr_ai_systemu",
    "training_outline": "skoleni_ai_literacy",
    "chatbot_notices": "oznameni_ai",
    "ai_policy": "interni_ai_politika",
    "incident_response_plan": "plan_rizeni_incidentu",
    "dpia_template": "dpia_posouzeni_vlivu",
    "vendor_checklist": "dodavatelsky_checklist",
    "monitoring_plan": "monitoring_plan_ai",
    "transparency_human_oversight": "transparentnost_lidsky_dohled",
    "transparency_page": "transparencni_stranka",
    "training_presentation": "skolici_prezentace",
}


# ══════════════════════════════════════════════════════════════════════
# RESULT DATACLASS
# ══════════════════════════════════════════════════════════════════════

@dataclass
class ComplianceKitResult:
    """Výsledek generování celého Compliance Kitu."""
    client_id: str
    company_name: str
    documents: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    skipped_documents: list = field(default_factory=list)
    pipeline_log: list = field(default_factory=list)
    total_cost_usd: float = 0.0
    total_tokens: int = 0
    generated_at: str = ""

    @property
    def success_count(self) -> int:
        return len(self.documents)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    def to_dict(self) -> dict:
        return {
            "client_id": self.client_id,
            "company_name": self.company_name,
            "documents": self.documents,
            "errors": self.errors,
            "skipped_documents": self.skipped_documents,
            "pipeline_log": self.pipeline_log,
            "total_cost_usd": self.total_cost_usd,
            "total_tokens": self.total_tokens,
            "generated_at": self.generated_at,
            "summary": {
                "total_documents": self.success_count,
                "failed": self.error_count,
                "cost_usd": f"${self.total_cost_usd:.4f}",
                "total_tokens": self.total_tokens,
            },
        }


# ══════════════════════════════════════════════════════════════════════
# DATA LOADING — z Supabase DB
# ══════════════════════════════════════════════════════════════════════

def _resolve_ids(input_id: str) -> dict:
    """Rozřeší vstupní ID na client_id + company_id."""
    supabase = get_supabase()

    # 1. Zkusit jako order_id
    order = supabase.table("orders").select("*").eq("id", input_id).limit(1).execute()
    if order.data:
        o = order.data[0]
        company_id = o.get("company_id", "")
        client = supabase.table("clients").select("id").eq("company_id", company_id).limit(1).execute()
        client_id = client.data[0]["id"] if client.data else company_id
        logger.info(f"[Pipeline] Resolved order_id → company={company_id}, client={client_id}")
        return {
            "client_id": client_id, "company_id": company_id,
            "billing_data": {
                "billing_name": o.get("billing_name", ""),
                "billing_ico": o.get("billing_ico", ""),
                "billing_email": o.get("billing_email", ""),
            },
        }

    # 2. Zkusit jako client_id
    client = supabase.table("clients").select("id, company_id").eq("id", input_id).limit(1).execute()
    if client.data:
        company_id = client.data[0].get("company_id", input_id)
        return {"client_id": input_id, "company_id": company_id, "billing_data": {}}

    # 3. Zkusit jako company_id
    company = supabase.table("companies").select("id").eq("id", input_id).limit(1).execute()
    if company.data:
        client = supabase.table("clients").select("id").eq("company_id", input_id).limit(1).execute()
        client_id = client.data[0]["id"] if client.data else input_id
        return {"client_id": client_id, "company_id": input_id, "billing_data": {}}

    # 4. Fallback
    logger.warning(f"[Pipeline] ID {input_id} nerozřešeno — fallback")
    return {"client_id": input_id, "company_id": input_id, "billing_data": {}}


def _load_scan_data(client_id: str) -> dict:
    """Načte data ze skenu webu."""
    logger.info(f"[Pipeline] Načítám scan data pro {client_id}")
    supabase = get_supabase()

    scans = (
        supabase.table("scans").select("*")
        .eq("company_id", client_id)
        .order("created_at", desc=True).limit(1).execute()
    )
    if not scans.data:
        return {"findings": [], "url": "", "scan_id": None, "risk_breakdown": {"high": 0, "limited": 0, "minimal": 0}}

    scan = scans.data[0]
    scan_id = scan["id"]
    findings_res = supabase.table("findings").select("*").eq("scan_id", scan_id).execute()

    findings = []
    seen_names: set = set()
    risk_breakdown = {"high": 0, "limited": 0, "minimal": 0}

    for f in findings_res.data or []:
        name = f.get("name", "AI systém")
        name_lower = name.strip().lower()
        if name_lower in seen_names:
            continue
        seen_names.add(name_lower)
        rl = f.get("risk_level", "minimal")
        risk_breakdown[rl] = risk_breakdown.get(rl, 0) + 1

        # Sanitize error markers
        classification_text = f.get("ai_classification_text", "")
        action_req = f.get("action_required", "")
        for marker in ("LLM failed", "Cannot parse", "Raw text:", "JSONDecodeError", "klasifikace selhala"):
            if marker in classification_text:
                classification_text = "Klasifikace provedena na základě signatur a heuristické analýzy."
                break
            if marker in action_req:
                action_req = "Doporučujeme ověřit klasifikaci tohoto systému."
                break

        findings.append({
            "name": name, "category": f.get("category", ""),
            "risk_level": rl, "ai_act_article": f.get("ai_act_article", ""),
            "action_required": action_req,
            "ai_classification_text": classification_text,
            "confirmed_by_client": f.get("confirmed_by_client", "unknown"),
            "source": f.get("source", ""),
        })

    logger.info(f"[Pipeline] Scan: {len(findings)} findings, risk={risk_breakdown}")
    return {
        "findings": findings, "url": scan.get("url", ""), "scan_id": scan_id,
        "scan_date": scan.get("created_at", ""), "risk_breakdown": risk_breakdown,
    }


def _load_questionnaire_data(client_id: str) -> dict:
    """Načte dotazníková data."""
    logger.info(f"[Pipeline] Načítám dotazník pro {client_id}")
    supabase = get_supabase()
    responses = None

    try:
        res = (supabase.table("questionnaire_responses")
               .select("question_key, section, answer, details, tool_name")
               .eq("client_id", client_id).execute())
        if res.data:
            responses = res.data
    except Exception:
        pass

    if not responses:
        try:
            mapping = supabase.table("clients").select("id").eq("company_id", client_id).limit(1).execute()
            if mapping.data:
                res = (supabase.table("questionnaire_responses")
                       .select("question_key, section, answer, details, tool_name")
                       .eq("client_id", mapping.data[0]["id"]).execute())
                if res.data:
                    responses = res.data
        except Exception:
            pass

    if not responses:
        return {
            "questionnaire_completed": False, "questionnaire_ai_systems": 0,
            "recommendations": [], "risk_breakdown": {"high": 0, "limited": 0, "minimal": 0},
        }

    logger.info(f"[Pipeline] Dotazník: {len(responses)} odpovědí")
    answers_by_key = {}
    for row in responses:
        key = row.get("question_key", "")
        if key:
            answers_by_key[key] = {
                "answer": row.get("answer", ""),
                "details": row.get("details") or {},
                "tool_name": row.get("tool_name", ""),
                "section": row.get("section", ""),
            }

    def _get(qkey, default=""):
        return answers_by_key.get(qkey, {}).get("answer", default)

    def _get_detail(qkey, detail_key, default=""):
        return (answers_by_key.get(qkey, {}).get("details") or {}).get(detail_key, default)

    # Company details
    company_legal_name = _get("company_legal_name")
    company_ico = _get("company_ico")
    raw_address = _get("company_address")
    if " || " in raw_address:
        parts = [p.strip() for p in raw_address.split(" || ")]
        street, house, city, zipcode = (parts + ["","","",""])[:4]
        addr_parts = []
        if street and house:
            addr_parts.append(f"{street} {house}")
        elif street:
            addr_parts.append(street)
        if city:
            addr_parts.append(city)
        if zipcode:
            addr_parts.append(zipcode)
        company_address = ", ".join(addr_parts)
    else:
        company_address = raw_address

    company_contact_email = _get("company_contact_email")
    company_industry = _get("company_industry")
    company_size = _get("company_size")

    # Oversight person
    oversight_raw = answers_by_key.get("has_oversight_person", {})
    oversight_details = oversight_raw.get("details") or {}
    oversight_person = {
        "has_person": oversight_raw.get("answer") == "yes",
        "name": oversight_details.get("oversight_person_name", ""),
        "email": oversight_details.get("oversight_person_email", ""),
        "role": oversight_details.get("oversight_role", ""),
    }

    # AI systems
    TOOL_NAME_MAP = {
        "uses_chatgpt": ("chatgpt_tool_name", "ChatGPT"),
        "uses_copilot": ("copilot_tool_name", "GitHub Copilot"),
        "uses_ai_content": ("content_tool_name", "AI generátor obsahu"),
        "uses_deepfake": ("deepfake_tool_name", "AI video/syntetický obsah"),
        "uses_ai_chatbot": ("chatbot_tool_name", "AI chatbot"),
        "uses_ai_email_auto": ("email_tool", "AI e-mailový asistent"),
        "uses_ai_recruitment": ("recruitment_tool", "AI náborový systém"),
        "uses_ai_employee_monitoring": ("monitoring_type", "AI monitoring zaměstnanců"),
        "uses_emotion_recognition": ("emotion_tool_name", "Rozpoznávání emocí"),
        "uses_ai_creditscoring": ("credit_tool", "AI credit scoring"),
        "uses_ai_accounting": ("accounting_tool", "AI účetní systém"),
        "uses_ai_insurance": ("insurance_tool", "AI pojišťovací systém"),
        "uses_ai_decision": ("decision_scope", "AI automatizované rozhodování"),
        "uses_dynamic_pricing": ("pricing_tool", "Dynamická cenotvorba"),
        "uses_ai_for_children": ("children_ai_context", "AI pro děti"),
        "uses_ai_critical_infra": ("infra_tool_name", "AI kritická infrastruktura"),
        "uses_ai_safety_component": ("safety_product", "AI bezpečnostní komponenta"),
        "develops_own_ai": (None, "Vlastní vývoj AI"),
        "modifies_ai_purpose": (None, "Změna účelu AI systému"),
        "uses_gpai_api": ("gpai_provider", "GPAI API"),
    }

    ai_systems_declared = []
    for syskey, (detail_key, fallback) in TOOL_NAME_MAP.items():
        sdata = answers_by_key.get(syskey, {})
        if sdata.get("answer") == "yes":
            details = sdata.get("details") or {}
            raw_tool = sdata.get("tool_name") or ""
            if raw_tool and raw_tool.lower() not in ("none", "null", ""):
                name = raw_tool
            elif detail_key and details.get(detail_key):
                val = details[detail_key]
                name = ", ".join(str(v) for v in val[:5]) if isinstance(val, list) else str(val)
            else:
                name = fallback
            ai_systems_declared.append({"key": syskey, "tool_name": name, "details": details})

    # Prohibited
    prohibited = {
        "social_scoring": _get("uses_social_scoring") == "yes",
        "subliminal_manipulation": _get("uses_subliminal_manipulation") == "yes",
        "realtime_biometric": _get("uses_realtime_biometric") == "yes",
    }

    # Training, Incident, Data protection, Human oversight
    training = {"has_training": _get("has_ai_training") == "yes", "has_guidelines": _get("has_ai_guidelines") == "yes"}
    incident = {"has_plan": _get("has_incident_plan") == "yes", "monitors_outputs": _get("monitors_ai_outputs") == "yes"}
    data_protection = {"processes_personal_data": _get("ai_processes_personal_data") == "yes",
                       "data_in_eu": _get("ai_data_stored_eu") == "yes",
                       "has_vendor_contracts": _get("has_ai_vendor_contracts") == "yes"}
    human_oversight = {"can_override": _get("can_override_ai") == "yes",
                       "has_logging": _get("ai_decision_logging") == "yes"}

    # Risk analysis
    try:
        from backend.api.questionnaire import QuestionnaireAnswer, _analyze_responses
        qa_list = [QuestionnaireAnswer(
            question_key=r["question_key"], section=r["section"],
            answer=r["answer"], details=r.get("details"), tool_name=r.get("tool_name"),
        ) for r in responses]
        analysis = _analyze_responses(qa_list)
    except Exception as e:
        logger.warning(f"Analýza dotazníku selhala: {e}")
        analysis = {"risk_breakdown": {"high": 0, "limited": 0, "minimal": 0}, "recommendations": []}

    rb = analysis.get("risk_breakdown", {})
    overall_risk = "high" if rb.get("high", 0) > 0 else ("limited" if rb.get("limited", 0) > 0 else "minimal")

    return {
        "questionnaire_completed": True, "questionnaire_answers": answers_by_key,
        "ai_systems_declared": ai_systems_declared,
        "recommendations": analysis.get("recommendations", []),
        "risk_breakdown": analysis.get("risk_breakdown", {}),
        "overall_risk": overall_risk,
        "q_company_legal_name": company_legal_name, "q_company_ico": company_ico,
        "q_company_address": company_address,
        "q_company_contact_email": company_contact_email,
        "q_company_industry": company_industry, "q_company_size": company_size,
        "oversight_person": oversight_person, "prohibited_systems": prohibited,
        "training": training, "incident": incident,
        "data_protection": data_protection, "human_oversight": human_oversight,
    }


def _load_company_data(company_id: str) -> dict:
    """Načte data firmy."""
    supabase = get_supabase()
    company = supabase.table("companies").select("*").eq("id", company_id).limit(1).execute()
    if not company.data:
        client = supabase.table("clients").select("*").eq("id", company_id).limit(1).execute()
        if client.data:
            c = client.data[0]
            return {"company_name": c.get("company_name", c.get("name", "Neznámá firma")),
                    "contact_email": c.get("email", "")}
        return {"company_name": "Neznámá firma", "contact_email": ""}
    c = company.data[0]
    return {"company_name": c.get("name", "Neznámá firma"), "contact_email": c.get("email", "")}


def _save_document_record(client_id: str, doc_info: dict) -> None:
    """Uloží záznam dokumentu do DB."""
    supabase = get_supabase()
    try:
        supabase.table("documents").insert({
            "company_id": client_id,
            "type": doc_info["template_key"],
            "name": doc_info["template_name"],
            "url": doc_info.get("download_url", ""),
            "format": doc_info.get("format", "pdf"),
            "size_bytes": doc_info.get("size_bytes", 0),
        }).execute()
    except Exception as e:
        logger.error(f"[Pipeline] DB save failed: {e}")


# ══════════════════════════════════════════════════════════════════════
# COMPANY CONTEXT BUILDER — sdílený kontext pro všechny moduly
# ══════════════════════════════════════════════════════════════════════

def build_company_context(data: dict) -> str:
    """Sestaví sdílený textový kontext firmy pro LLM moduly."""
    company = data.get("company_name", "Neznámá firma")
    industry = data.get("q_company_industry", "neznámé")
    size = data.get("q_company_size", "neznámá")
    overall_risk = data.get("overall_risk", "minimal")
    risk_breakdown = data.get("risk_breakdown", {"high": 0, "limited": 0, "minimal": 0})
    oversight = data.get("oversight_person", {})
    data_prot = data.get("data_protection", {})
    training = data.get("training", {})
    incident = data.get("incident", {})

    findings_lines = []
    for f in data.get("findings", []):
        findings_lines.append(
            f"  - {f.get('name', '?')}: kategorie={f.get('category', '?')}, "
            f"riziko={f.get('risk_level', '?')}, článek={f.get('ai_act_article', '?')}, "
            f"akce={f.get('action_required', '?')}"
        )
    findings_summary = "\n".join(findings_lines) if findings_lines else "  Žádné AI systémy nebyly detekovány na webu."

    declared_lines = []
    for d in data.get("ai_systems_declared", []):
        declared_lines.append(f"  - {d.get('tool_name', d.get('key', '?'))}")
    declared_summary = "\n".join(declared_lines) if declared_lines else "  Žádné AI systémy nebyly deklarovány."

    recs_lines = []
    for r in data.get("recommendations", []):
        recs_lines.append(f"  - [{r.get('risk_level','')}] {r.get('tool_name','')}: {r.get('recommendation','')}")
    recs_summary = "\n".join(recs_lines) if recs_lines else "  Žádná specifická doporučení."

    from datetime import date
    today = date.today().strftime("%d. %m. %Y")

    return f"""KONTEXT FIRMY:
Dnešní datum: {today}
Firma: {company}
IČO: {data.get('q_company_ico', 'neuvedeno')}
Odvětví: {industry}
Velikost: {size}
Celkové riziko: {overall_risk}
Rizikový rozpad: {risk_breakdown.get('high',0)} vysoké, {risk_breakdown.get('limited',0)} omezené, {risk_breakdown.get('minimal',0)} minimální

NALEZENÉ AI SYSTÉMY (web sken):
{findings_summary}

DEKLAROVANÉ AI SYSTÉMY (dotazník):
{declared_summary}

DOPORUČENÍ Z ANALÝZY:
{recs_summary}

ODPOVĚDNÁ OSOBA ZA AI: {oversight.get('name', 'nejmenována')} ({oversight.get('role', 'neurčena')})
ZPRACOVÁVÁ OSOBNÍ ÚDAJE PŘES AI: {'ANO' if data_prot.get('processes_personal_data') else 'NE'}
MÁ ŠKOLENÍ AI: {'ANO' if training.get('has_training') else 'NE'}
MÁ INCIDENT PLÁN: {'ANO' if incident.get('has_plan') else 'NE'}
MÁ SMLOUVY S DODAVATELI AI: {'ANO' if data_prot.get('has_vendor_contracts') else 'NE'}
MŮŽE OVERRIDOVAT AI: {'ANO' if data.get('human_oversight', {}).get('can_override') else 'NE'}
MÁ AI LOGGING: {'ANO' if data.get('human_oversight', {}).get('has_logging') else 'NE'}"""


# ══════════════════════════════════════════════════════════════════════
# HLAVNÍ PIPELINE — M1 → M2 → M3 → M4 (sekvenčně per dokument)
# ══════════════════════════════════════════════════════════════════════

async def generate_compliance_kit(input_id: str) -> ComplianceKitResult:
    """
    Vygeneruje kompletní AI Act Compliance Kit.

    Architektura v3: pro každý z 11 dokumentů:
      M1 (Gemini) → M2 (Claude) → M3 (Gemini) → M4 (Claude) → PDF

    Výstup: 11 × PDF + 1 × HTML (transparenční stránka) + 1 × PPTX (prezentace)
    """
    pipeline_start = time.time()

    # ── 0. Resolve IDs ──
    ids = _resolve_ids(input_id)
    client_id = ids["client_id"]
    company_id = ids["company_id"]

    logger.info(f"{'='*70}")
    logger.info(f"[Pipeline v3] START generování Compliance Kitu")
    logger.info(f"[Pipeline v3] Order: {input_id}, Client: {client_id}, Company: {company_id}")
    logger.info(f"{'='*70}")

    result = ComplianceKitResult(
        client_id=client_id,
        company_name="",
        generated_at=datetime.now(timezone.utc).isoformat(),
    )

    # ── 1. Načíst data z DB ──
    logger.info(f"[Pipeline v3] ═══ KROK 1: Načítání dat z DB ═══")
    step_start = time.time()

    company_data = _load_company_data(company_id)
    scan_data = _load_scan_data(company_id)
    questionnaire_data = _load_questionnaire_data(client_id)

    template_data = {**company_data, **scan_data, **questionnaire_data}
    if questionnaire_data.get("q_company_legal_name"):
        template_data["company_name"] = questionnaire_data["q_company_legal_name"]
    if questionnaire_data.get("q_company_contact_email"):
        template_data["contact_email"] = questionnaire_data["q_company_contact_email"]

    result.company_name = template_data.get("company_name", "Firma")
    company_name = result.company_name
    ico = questionnaire_data.get("q_company_ico", "")
    overall_risk = template_data.get("overall_risk", "minimal")

    logger.info(f"[Pipeline v3] Firma: {company_name}, Riziko: {overall_risk}")
    logger.info(f"[Pipeline v3] Findings: {len(scan_data.get('findings', []))}, "
                f"Declared: {len(questionnaire_data.get('ai_systems_declared', []))}")
    logger.info(f"[Pipeline v3] DB load: {time.time()-step_start:.1f}s")

    # ── 2. Build company context ──
    company_context = build_company_context(template_data)
    logger.info(f"[Pipeline v3] Company context: {len(company_context)} znaků")
    result.pipeline_log.append({
        "step": "data_loaded",
        "company": company_name,
        "findings": len(scan_data.get("findings", [])),
        "declared_systems": len(questionnaire_data.get("ai_systems_declared", [])),
        "overall_risk": overall_risk,
        "context_chars": len(company_context),
    })

    # ── 3. Per-document M1→M2→M3→M4 pipeline ──
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    all_final_html = {}   # doc_key → final HTML
    all_critiques = {}    # doc_key → {"eu": eu_critique, "client": client_critique} pro M5

    logger.info(f"[Pipeline v3] ═══ KROK 2: Generování {len(DOCUMENT_KEYS)} dokumentů (M1→M2→M3→M4) ═══")

    for doc_idx, doc_key in enumerate(DOCUMENT_KEYS, 1):
        doc_name = DOCUMENT_NAMES.get(doc_key, doc_key)
        doc_start = time.time()
        doc_cost = 0.0
        doc_tokens = 0

        logger.info(f"")
        logger.info(f"[Pipeline v3] {'─'*60}")
        logger.info(f"[Pipeline v3] DOKUMENT {doc_idx}/{len(DOCUMENT_KEYS)}: {doc_name}")
        logger.info(f"[Pipeline v3] {'─'*60}")

        try:
            # ── M1: Generator (Gemini 3.1 Pro) ──
            m1_start = time.time()
            logger.info(f"[Pipeline v3]   M1 Generator (Gemini) → {doc_name}...")
            draft_html, m1_meta = await generate_draft(company_context, doc_key)
            m1_time = time.time() - m1_start
            m1_cost = m1_meta.get("cost_usd", 0)
            m1_tokens = m1_meta.get("input_tokens", 0) + m1_meta.get("output_tokens", 0)
            logger.info(f"[Pipeline v3]   M1 hotov: {len(draft_html)} znaků, "
                       f"${m1_cost:.4f}, {m1_tokens} tokens, {m1_time:.1f}s")

            if not draft_html or len(draft_html) < 200:
                raise ValueError(f"M1 vrátil prázdný/krátký draft ({len(draft_html)} znaků)")

            # ── M2: EU Inspector (Claude Sonnet 4) ──
            m2_start = time.time()
            logger.info(f"[Pipeline v3]   M2 EU Critic (Claude) → {doc_name}...")
            eu_critique, m2_meta = await review_eu(draft_html, company_context, doc_key)
            m2_time = time.time() - m2_start
            m2_cost = m2_meta.get("cost_usd", 0)
            m2_tokens = m2_meta.get("input_tokens", 0) + m2_meta.get("output_tokens", 0)
            eu_score = eu_critique.get("skore", "?")
            logger.info(f"[Pipeline v3]   M2 hotov: skóre={eu_score}/10, "
                       f"${m2_cost:.4f}, {m2_tokens} tokens, {m2_time:.1f}s")

            # ── M3: Client Critic — SKIP if EU skóre >= 8 (cost optimization) ──
            eu_score_num = 0
            try:
                eu_score_num = int(eu_score)
            except (ValueError, TypeError):
                eu_score_num = 0

            if eu_score_num >= 8:
                logger.info(f"[Pipeline v3]   M3 SKIP: EU skóre {eu_score_num} >= 8, klient review přeskočen (úspora tokenů)")
                client_critique = {
                    "myslenkovy_proces": f"Přeskočeno — EU skóre {eu_score_num}/10 je dostatečné.",
                    "celkove_hodnoceni": "dobré",
                    "skore": eu_score_num,
                    "nalezy": [],
                    "silne_stranky": ["EU inspektor dal vysoké skóre — dokument splňuje standardy."],
                    "chybejici_obsah": [],
                    "otazky_klienta": [],
                    "celkove_doporuceni": "Dokument splňuje kvalitativní standardy.",
                }
                m3_meta = {"cost_usd": 0, "input_tokens": 0, "output_tokens": 0}
                m3_cost = 0
                m3_tokens = 0
                m3_time = 0.0
                client_score = eu_score_num
            else:
                # ── M3: Client Critic (Gemini 3.1 Pro) ──
                m3_start = time.time()
                logger.info(f"[Pipeline v3]   M3 Client Critic (Gemini) → {doc_name}...")
                client_critique, m3_meta = await review_client(draft_html, company_context, doc_key)
                m3_time = time.time() - m3_start
                m3_cost = m3_meta.get("cost_usd", 0)
                m3_tokens = m3_meta.get("input_tokens", 0) + m3_meta.get("output_tokens", 0)
                client_score = client_critique.get("skore", "?")
                logger.info(f"[Pipeline v3]   M3 hotov: skóre={client_score}/10, "
                           f"${m3_cost:.4f}, {m3_tokens} tokens, {m3_time:.1f}s")

            # Uložit kritiky pro M5 analýzu
            all_critiques[doc_key] = {
                "eu": eu_critique,
                "client": client_critique,
            }

            # ── M4: Refiner (Gemini) ──
            m4_start = time.time()
            logger.info(f"[Pipeline v3]   M4 Refiner (Claude) → {doc_name}...")
            final_html, m4_meta = await refine(
                draft_html, eu_critique, client_critique, company_context, doc_key
            )
            m4_time = time.time() - m4_start
            m4_cost = m4_meta.get("cost_usd", 0)
            m4_tokens = m4_meta.get("input_tokens", 0) + m4_meta.get("output_tokens", 0)
            logger.info(f"[Pipeline v3]   M4 hotov: {len(final_html)} znaků, "
                       f"${m4_cost:.4f}, {m4_tokens} tokens, {m4_time:.1f}s")

            # Celkové metriky dokumentu
            doc_cost = m1_cost + m2_cost + m3_cost + m4_cost
            doc_tokens = m1_tokens + m2_tokens + m3_tokens + m4_tokens
            doc_time = time.time() - doc_start

            logger.info(f"[Pipeline v3]   DOKUMENT {doc_idx} HOTOV: "
                       f"{len(final_html)} znaků, ${doc_cost:.4f}, "
                       f"{doc_tokens} tokens, {doc_time:.0f}s")
            logger.info(f"[Pipeline v3]   Skóre: EU={eu_score}/10, Klient={client_score}/10")

            all_final_html[doc_key] = final_html
            result.total_cost_usd += doc_cost
            result.total_tokens += doc_tokens

            # Save intermediate HTML to disk for per-doc monitoring
            try:
                html_out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "gen_html")
                os.makedirs(html_out_dir, exist_ok=True)
                html_path = os.path.join(html_out_dir, f"{doc_key}.html")
                with open(html_path, "w", encoding="utf-8") as hf:
                    hf.write(final_html)
                logger.info(f"[Pipeline v3]   HTML uložen: {html_path}")
            except Exception as html_err:
                logger.warning(f"[Pipeline v3]   HTML save failed: {html_err}")

            result.pipeline_log.append({
                "doc_key": doc_key,
                "doc_name": doc_name,
                "doc_index": f"{doc_idx}/{len(DOCUMENT_KEYS)}",
                "draft_chars": len(draft_html),
                "final_chars": len(final_html),
                "eu_score": eu_score,
                "client_score": client_score,
                "cost_usd": round(doc_cost, 4),
                "tokens": doc_tokens,
                "time_s": round(doc_time, 1),
                "m1_time": round(m1_time, 1),
                "m2_time": round(m2_time, 1),
                "m3_time": round(m3_time, 1),
                "m4_time": round(m4_time, 1),
            })

        except Exception as e:
            doc_time = time.time() - doc_start
            error_msg = f"{doc_key}: {str(e)}"
            result.errors.append(error_msg)
            logger.error(f"[Pipeline v3]   CHYBA v {doc_name}: {e}", exc_info=True)
            result.pipeline_log.append({
                "doc_key": doc_key, "doc_name": doc_name,
                "error": str(e), "time_s": round(doc_time, 1),
            })

    # ── 3b. M5: Prompt Self-Optimization (Claude Opus 4.6) ──
    generation_id = f"gen_{timestamp}"
    m5_result = None
    try:
        logger.info(f"")
        logger.info(f"[Pipeline v3] ═══ M5: Prompt Self-Optimization ═══")

        m5_result = await analyze_and_optimize(
            pipeline_log=result.pipeline_log,
            all_critiques=all_critiques,
            generation_id=generation_id,
        )

        result.total_cost_usd += m5_result.get("cost_usd", 0)
        result.pipeline_log.append({
            "step": "m5_optimization",
            "status": m5_result.get("status", "unknown"),
            "version": m5_result.get("version", 0),
            "rules_added": m5_result.get("rules_added", 0),
            "avg_score": m5_result.get("avg_score", 0),
            "converged": m5_result.get("converged", False),
            "cost_usd": m5_result.get("cost_usd", 0),
            "time_s": m5_result.get("time_s", 0),
        })

    except Exception as e:
        logger.error(f"[Pipeline v3] M5 CHYBA (nekritická): {e}", exc_info=True)
        m5_result = {"status": "error", "error": str(e)}
        result.pipeline_log.append({
            "step": "m5_optimization",
            "error": str(e),
        })

    # ── 3c. Email report M2/M3/M5 ──
    try:
        total_time = time.time() - pipeline_start
        logger.info(f"[Pipeline v3] ═══ Odesílám report generace emailem ═══")
        report_result = await send_generation_report(
            generation_id=generation_id,
            all_critiques=all_critiques,
            m5_result=m5_result,
            pipeline_log=result.pipeline_log,
            total_cost=result.total_cost_usd,
            total_tokens=result.total_tokens,
            total_time=total_time,
            doc_names=DOCUMENT_NAMES,
        )
        if report_result.get("sent"):
            logger.info(f"[Pipeline v3] Report odeslán (resend_id={report_result.get('resend_id')})")
        else:
            logger.warning(f"[Pipeline v3] Report se nepodařilo odeslat: {report_result.get('error', '?')}")
    except Exception as e:
        logger.error(f"[Pipeline v3] Report email CHYBA (nekritická): {e}", exc_info=True)

    # ── 4. Generate PDFs ──
    logger.info(f"")
    logger.info(f"[Pipeline v3] ═══ KROK 3: Generování PDF souborů ═══")

    for doc_key, final_html in all_final_html.items():
        # Skip docs with special output format (not PDF)
        if doc_key in ("transparency_page", "training_presentation"):
            continue
        doc_name = DOCUMENT_NAMES.get(doc_key, doc_key)
        slug = SECTION_SLUG.get(doc_key, doc_key)

        try:
            section_html = render_section_html(doc_key, final_html, company_name)
            pdf_bytes = html_to_pdf(section_html)
            pdf_filename = f"{slug}_{timestamp}.pdf"
            pdf_url = save_to_supabase_storage(
                pdf_bytes, pdf_filename, company_id,
                content_type="application/pdf",
            )

            pdf_info = {
                "template_key": doc_key, "template_name": doc_name,
                "filename": pdf_filename, "download_url": pdf_url,
                "size_bytes": len(pdf_bytes), "format": "pdf",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            result.documents.append(pdf_info)
            _save_document_record(company_id, pdf_info)
            logger.info(f"[Pipeline v3]   PDF: {doc_name} ({len(pdf_bytes):,} bytes)")

        except Exception as e:
            result.errors.append(f"PDF {doc_key}: {str(e)}")
            logger.error(f"[Pipeline v3]   PDF CHYBA {doc_name}: {e}", exc_info=True)

    # ── 5. Transparenční stránka (HTML) — LLM-generated via M1→M4 ──
    logger.info(f"[Pipeline v3] ═══ KROK 4: Transparenční stránka HTML ═══")
    try:
        tp_html = all_final_html.get("transparency_page")
        if tp_html:
            # LLM generates complete standalone HTML — save as-is
            html_bytes = tp_html.encode("utf-8")
            html_filename = f"transparencni_stranka_{timestamp}.html"
            html_url = save_to_supabase_storage(
                html_bytes, html_filename, company_id,
                content_type="text/html",
            )
            html_info = {
                "template_key": "transparency_page",
                "template_name": "Transparenční stránka (HTML)",
                "filename": html_filename, "download_url": html_url,
                "size_bytes": len(html_bytes), "format": "html",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            result.documents.append(html_info)
            _save_document_record(company_id, html_info)
            logger.info(f"[Pipeline v3]   HTML: {len(html_bytes):,} bytes")
        else:
            logger.warning("[Pipeline v3]   transparency_page not in all_final_html — skipping")
    except Exception as e:
        result.errors.append(f"transparency_page: {str(e)}")
        logger.error(f"[Pipeline v3]   HTML CHYBA: {e}", exc_info=True)

    # ── 6. PPTX prezentace — LLM-generated via M1→M4, then converted ──
    logger.info(f"[Pipeline v3] ═══ KROK 5: PPTX prezentace ═══")
    try:
        pres_html = all_final_html.get("training_presentation")
        if pres_html:
            from backend.documents.pptx_generator import html_slides_to_pptx
            pptx_bytes = html_slides_to_pptx(pres_html, template_data)
            pptx_filename = f"skoleni_ai_literacy_{timestamp}.pptx"
            pptx_url = save_to_supabase_storage(
                pptx_bytes, pptx_filename, company_id,
                content_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            )
            pptx_info = {
                "template_key": "training_presentation",
                "template_name": "Školení AI Literacy — Prezentace (PPTX)",
                "filename": pptx_filename, "download_url": pptx_url,
                "size_bytes": len(pptx_bytes), "format": "pptx",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            result.documents.append(pptx_info)
            _save_document_record(company_id, pptx_info)
            logger.info(f"[Pipeline v3]   PPTX: {len(pptx_bytes):,} bytes")
        else:
            logger.warning("[Pipeline v3]   training_presentation not in all_final_html — skipping")
    except Exception as e:
        result.errors.append(f"pptx: {str(e)}")
        logger.error(f"[Pipeline v3]   PPTX CHYBA: {e}", exc_info=True)

    # ── 7. Statické VOP (PDF) — přesná kopie z webu, bez LLM ──
    logger.info(f"[Pipeline v3] ═══ KROK 6: Statické VOP (PDF) ═══")
    try:
        vop_html_path = os.path.join(os.path.dirname(__file__), "vop_template.html")
        if os.path.exists(vop_html_path):
            with open(vop_html_path, "r", encoding="utf-8") as f:
                vop_html = f.read()
            vop_pdf_bytes = html_to_pdf(vop_html)
            vop_filename = f"vop_aishield_{timestamp}.pdf"
            vop_url = save_to_supabase_storage(
                vop_pdf_bytes, vop_filename, company_id,
                content_type="application/pdf",
            )
            vop_info = {
                "template_key": "vop",
                "template_name": "Všeobecné obchodní podmínky (VOP)",
                "filename": vop_filename, "download_url": vop_url,
                "size_bytes": len(vop_pdf_bytes), "format": "pdf",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "static": True,
            }
            result.documents.append(vop_info)
            _save_document_record(company_id, vop_info)
            logger.info(f"[Pipeline v3]   VOP PDF: {len(vop_pdf_bytes):,} bytes (statický dokument)")
        else:
            logger.warning(f"[Pipeline v3]   VOP šablona nenalezena: {vop_html_path}")
    except Exception as e:
        result.errors.append(f"vop: {str(e)}")
        logger.error(f"[Pipeline v3]   VOP CHYBA: {e}", exc_info=True)

    # ── HOTOVO ──
    total_time = time.time() - pipeline_start
    logger.info(f"")
    logger.info(f"{'='*70}")
    logger.info(f"[Pipeline v3] COMPLIANCE KIT HOTOV!")
    logger.info(f"[Pipeline v3] Firma: {company_name}")
    logger.info(f"[Pipeline v3] Dokumenty: {result.success_count} OK, {result.error_count} chyb")
    logger.info(f"[Pipeline v3] Celkový cost: ${result.total_cost_usd:.4f}")
    logger.info(f"[Pipeline v3] Celkové tokeny: {result.total_tokens:,}")
    logger.info(f"[Pipeline v3] Celkový čas: {total_time:.0f}s ({total_time/60:.1f} min)")
    logger.info(f"{'='*70}")

    result.pipeline_log.append({
        "step": "completed",
        "total_documents": result.success_count,
        "total_errors": result.error_count,
        "total_cost_usd": round(result.total_cost_usd, 4),
        "total_tokens": result.total_tokens,
        "total_time_s": round(total_time, 1),
    })

    return result


async def generate_single_document(input_id: str, template_key: str) -> dict:
    """Generuje jeden dokument (M1→M2→M3→M4 → PDF)."""
    ids = _resolve_ids(input_id)
    client_id = ids["client_id"]
    company_id = ids["company_id"]

    company_data = _load_company_data(company_id)
    scan_data = _load_scan_data(company_id)
    questionnaire_data = _load_questionnaire_data(client_id)

    template_data = {**company_data, **scan_data, **questionnaire_data}
    if questionnaire_data.get("q_company_legal_name"):
        template_data["company_name"] = questionnaire_data["q_company_legal_name"]

    company_context = build_company_context(template_data)
    company_name = template_data.get("company_name", "Firma")

    draft_html, _ = await generate_draft(company_context, template_key)
    eu_critique, _ = await review_eu(draft_html, company_context, template_key)
    client_critique, _ = await review_client(draft_html, company_context, template_key)
    final_html, _ = await refine(draft_html, eu_critique, client_critique, company_context, template_key)

    section_html = render_section_html(template_key, final_html, company_name)
    pdf_bytes = html_to_pdf(section_html)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    slug = SECTION_SLUG.get(template_key, template_key)
    pdf_filename = f"{slug}_{timestamp}.pdf"
    pdf_url = save_to_supabase_storage(pdf_bytes, pdf_filename, company_id, content_type="application/pdf")

    doc_info = {
        "template_key": template_key,
        "template_name": DOCUMENT_NAMES.get(template_key, template_key),
        "filename": pdf_filename, "download_url": pdf_url,
        "size_bytes": len(pdf_bytes), "format": "pdf",
    }
    _save_document_record(company_id, doc_info)
    return doc_info
