"""
AIshield.cz — Document Generation Pipeline
Úkol 19: Orchestrátor generování Compliance Kitu.

Tok: DB data → šablony → HTML → PDF → Supabase Storage → záznam v DB
"""

import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field

from backend.database import get_supabase
from backend.documents.templates import TEMPLATE_RENDERERS, TEMPLATE_NAMES
from backend.documents.pdf_generator import html_to_pdf, generate_document_pdf, save_to_supabase_storage
from backend.documents.unified_pdf import render_unified_pdf_html

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════
# DOCUMENT ELIGIBILITY — filtr dokumentů podle rizikového profilu
# ══════════════════════════════════════════════════════════════════════

def _has_chatbot(data: dict) -> bool:
    """Detekce chatbotu — ze skenu (findings) nebo dotazníku."""
    for f in data.get("findings", []):
        if f.get("category") == "chatbot":
            return True
    for sys in data.get("ai_systems_declared", []):
        if sys.get("key") in ("uses_ai_chatbot", "uses_ai_email_auto"):
            return True
    return False


def _risk_is(data: dict, *levels: str) -> bool:
    """Ověří, zda celkové riziko odpovídá některé z úrovní."""
    return data.get("overall_risk", "minimal") in levels


def _ai_system_count(data: dict) -> int:
    """Počet deklarovaných AI systémů (dotazník + sken)."""
    declared = len(data.get("ai_systems_declared", []))
    found = len(data.get("findings", []))
    return max(declared, found)


DOCUMENT_ELIGIBILITY: dict[str, dict] = {
    # ── TIER 1 — Vždy (povinné pro každého deployer AI) ──
    "compliance_report": {
        "check": lambda d: True,
        "reason": "Povinný výstup analýzy — vždy generován",
        "tier": "always",
    },
    "ai_register": {
        "check": lambda d: True,
        "reason": "Registr AI systémů — povinný dle čl. 49 AI Act",
        "tier": "always",
    },
    "training_outline": {
        "check": lambda d: True,
        "reason": "AI gramotnost — povinná dle čl. 4 AI Act pro všechny",
        "tier": "always",
    },
    "transparency_page": {
        "check": lambda d: True,
        "reason": "Transparenční stránka — povinná dle čl. 50 AI Act",
        "tier": "always",
    },
    "action_plan": {
        "check": lambda d: True,
        "reason": "Akční plán — konkrétní kroky k souladu",
        "tier": "always",
    },

    # ── TIER 2 — Podmíněné (chatbot, více AI systémů) ──
    "chatbot_notices": {
        "check": lambda d: _has_chatbot(d),
        "reason": "Texty oznámení pro chatboty — čl. 50 AI Act",
        "skip_reason": "Chatbot nebyl detekován na webu ani v dotazníku",
        "tier": "conditional",
    },
    "ai_policy": {
        "check": lambda d: (
            _risk_is(d, "limited", "high")
            or _ai_system_count(d) >= 2
            or d.get("data_protection", {}).get("processes_personal_data")
        ),
        "reason": "Interní AI politika — doporučena při 2+ AI systémech nebo zvýšeném riziku",
        "skip_reason": "Minimální riziko, max. 1 AI systém, nezpracovává osobní údaje",
        "tier": "conditional",
    },

    # ── TIER 3 — Vysoké riziko nebo specifické podmínky ──
    "incident_response_plan": {
        "check": lambda d: (
            _risk_is(d, "high")
            or d.get("data_protection", {}).get("processes_personal_data")
        ),
        "reason": "Plán řízení incidentů — požadován při vysokém riziku nebo zpracování osobních údajů",
        "skip_reason": "Minimální/limitované riziko bez zpracování osobních údajů",
        "tier": "risk-based",
    },
    "dpia_template": {
        "check": lambda d: (
            d.get("data_protection", {}).get("processes_personal_data")
            and _risk_is(d, "limited", "high")
        ),
        "reason": "DPIA šablona — vyžadována při zpracování os. údajů s AI (GDPR čl. 35 + AI Act)",
        "skip_reason": "Nezpracovává osobní údaje prostřednictvím AI nebo minimální riziko",
        "tier": "high-risk",
    },
    "vendor_checklist": {
        "check": lambda d: (
            _risk_is(d, "limited", "high")
            and _ai_system_count(d) > 0
        ),
        "reason": "Dodavatelský checklist — kontrola smluv s poskytovateli AI (čl. 25–26)",
        "skip_reason": "Minimální riziko — formální audit dodavatelských smluv není vyžadován",
        "tier": "high-risk",
    },
    "monitoring_plan": {
        "check": lambda d: (
            _risk_is(d, "high")
            or (
                d.get("data_protection", {}).get("processes_personal_data")
                and _ai_system_count(d) >= 3
            )
        ),
        "reason": "Monitoring plán — požadován při vysokém riziku nebo rozsáhlém nasazení AI",
        "skip_reason": "Méně než 3 AI systémy nebo minimální riziko bez zpracování osobních údajů",
        "tier": "high-risk",
    },
}


def _get_eligible_documents(template_data: dict) -> tuple[dict[str, str], list[dict]]:
    """
    Vyhodnotí, které dokumenty mají být generovány na základě rizikového profilu.

    Returns:
        (eligible, skipped)
        - eligible: {template_key: reason} — dokumenty k vygenerování
        - skipped: [{key, name, reason}] — přeskočené dokumenty s vysvětlením
    """
    eligible = {}
    skipped = []

    for template_key, rule in DOCUMENT_ELIGIBILITY.items():
        if rule["check"](template_data):
            eligible[template_key] = rule["reason"]
        else:
            skipped.append({
                "key": template_key,
                "name": TEMPLATE_NAMES.get(template_key, template_key),
                "reason": rule.get("skip_reason", "Podmínky pro generování nebyly splněny"),
            })

    return eligible, skipped


@dataclass
class ComplianceKitResult:
    """Výsledek generování celého Compliance Kitu."""
    client_id: str
    company_name: str
    documents: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    skipped_documents: list[dict] = field(default_factory=list)
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
            "generated_at": self.generated_at,
            "summary": {
                "total_outputs": 3,  # 1 PDF + 1 HTML + 1 PPTX
                "generated": self.success_count,
                "skipped_sections": len(self.skipped_documents),
                "failed": self.error_count,
            },
        }


def _load_scan_data(client_id: str) -> dict:
    """Načte data ze skenu webu pro daného klienta."""
    logger.info(f"[Pipeline] Načítám scan data pro klienta {client_id}")
    supabase = get_supabase()

    # Najít poslední sken klienta
    scans = (
        supabase.table("scans")
        .select("*")
        .eq("company_id", client_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not scans.data:
        logger.warning(f"[Pipeline] Žádný sken nalezen pro klienta {client_id}")
        return {"findings": [], "url": "", "scan_id": None}

    scan = scans.data[0]
    scan_id = scan["id"]

    # Načíst nálezy (findings) pro tento sken
    findings_res = (
        supabase.table("findings")
        .select("*")
        .eq("scan_id", scan_id)
        .execute()
    )

    findings = []
    risk_breakdown = {"high": 0, "limited": 0, "minimal": 0}
    for f in findings_res.data or []:
        rl = f.get("risk_level", "minimal")
        risk_breakdown[rl] = risk_breakdown.get(rl, 0) + 1
        findings.append({
            "name": f.get("name", "AI systém"),
            "category": f.get("category", ""),
            "risk_level": rl,
            "ai_act_article": f.get("ai_act_article", ""),
            "action_required": f.get("action_required", ""),
            "ai_classification_text": f.get("ai_classification_text", ""),
            "confirmed_by_client": f.get("confirmed_by_client", "unknown"),
            "source": f.get("source", ""),
        })

    logger.info(
        f"[Pipeline] Scan data načtena: {len(findings)} findings, "
        f"risk_breakdown={risk_breakdown}, deep_scan={scan.get('deep_scan_status', 'N/A')}"
    )

    return {
        "findings": findings,
        "url": scan.get("url", ""),
        "scan_id": scan_id,
        "scan_date": scan.get("created_at", ""),
        "risk_breakdown": risk_breakdown,
        # Deep scan metadata — pro dokumenty
        "deep_scan_status": scan.get("deep_scan_status"),
        "deep_scan_started_at": scan.get("deep_scan_started_at"),
        "deep_scan_finished_at": scan.get("deep_scan_finished_at"),
        "deep_scan_total_findings": scan.get("deep_scan_total_findings"),
        "geo_countries_scanned": scan.get("geo_countries_scanned", []),
        "total_findings": scan.get("total_findings", len(findings)),
    }


def _load_questionnaire_data(client_id: str) -> dict:
    """
    Načte data z dotazníku pro daného klienta.
    Nový formát: questionnaire_responses tabulka — jeden řádek per odpověď
    (client_id, section, question_key, answer, details, tool_name).
    """
    logger.info(f"[Pipeline] Načítám dotazník pro klienta {client_id}")
    supabase = get_supabase()
    responses = None

    # Pokus 1: Přímé vyhledání dle client_id
    try:
        res = (
            supabase.table("questionnaire_responses")
            .select("question_key, section, answer, details, tool_name")
            .eq("client_id", client_id)
            .execute()
        )
        if res.data:
            responses = res.data
    except Exception:
        pass

    # Pokus 2: Mapování přes clients tabulku (company_id → client_id)
    if not responses:
        try:
            mapping = (
                supabase.table("clients")
                .select("id")
                .eq("company_id", client_id)
                .limit(1)
                .execute()
            )
            if mapping.data:
                mapped_id = mapping.data[0]["id"]
                res = (
                    supabase.table("questionnaire_responses")
                    .select("question_key, section, answer, details, tool_name")
                    .eq("client_id", mapped_id)
                    .execute()
                )
                if res.data:
                    responses = res.data
        except Exception:
            pass

    if not responses:
        logger.warning(f"[Pipeline] Žádné odpovědi z dotazníku pro klienta {client_id}")
        return {
            "questionnaire_completed": False,
            "questionnaire_ai_systems": 0,
            "recommendations": [],
            "risk_breakdown": {"high": 0, "limited": 0, "minimal": 0},
        }

    logger.info(f"[Pipeline] Dotazník: {len(responses)} odpovědí nalezeno")

    # ── Parsovat odpovědi do {question_key → data} ──
    answers_by_key: dict[str, dict] = {}
    for row in responses:
        key = row.get("question_key", "")
        if not key:
            continue
        answers_by_key[key] = {
            "answer": row.get("answer", ""),
            "details": row.get("details") or {},
            "tool_name": row.get("tool_name", ""),
            "section": row.get("section", ""),
        }

    def _get(qkey: str, default: str = "") -> str:
        return answers_by_key.get(qkey, {}).get("answer", default)

    def _get_detail(qkey: str, detail_key: str, default=""):
        return (answers_by_key.get(qkey, {}).get("details") or {}).get(detail_key, default)

    # ── Firemní údaje z dotazníku ──
    company_legal_name = _get("company_legal_name")
    company_ico = _get("company_ico")
    company_address = _get("company_address")
    company_contact_email = _get("company_contact_email")
    company_industry = _get("company_industry")
    company_size = _get("company_size")
    company_annual_revenue = _get("company_annual_revenue")

    # ── Odpovědná osoba za AI (čl. 14) ──
    oversight_raw = answers_by_key.get("has_oversight_person", {})
    oversight_details = oversight_raw.get("details") or {}
    oversight_person = {
        "has_person": oversight_raw.get("answer") == "yes",
        "name": oversight_details.get("oversight_person_name", ""),
        "email": oversight_details.get("oversight_person_email", ""),
        "phone": oversight_details.get("oversight_person_phone", ""),
        "role": oversight_details.get("oversight_role", ""),
        "scope": oversight_details.get("oversight_scope", []),
    }

    # ── AI systémy ve firmě (yes odpovědi) ──
    ai_system_keys = [
        "uses_chatgpt", "uses_copilot", "uses_ai_content", "uses_deepfake",
        "uses_ai_recruitment", "uses_ai_employee_monitoring", "uses_emotion_recognition",
        "uses_ai_accounting", "uses_ai_creditscoring", "uses_ai_insurance",
        "uses_ai_chatbot", "uses_ai_email_auto", "uses_ai_decision",
        "uses_dynamic_pricing", "uses_ai_for_children", "uses_ai_critical_infra",
        "uses_ai_safety_component", "develops_own_ai", "modifies_ai_purpose",
        "uses_gpai_api",
    ]
    ai_systems_declared = []
    for syskey in ai_system_keys:
        sdata = answers_by_key.get(syskey, {})
        if sdata.get("answer") == "yes":
            ai_systems_declared.append({
                "key": syskey,
                "tool_name": sdata.get("tool_name", "AI systém"),
                "details": sdata.get("details", {}),
                "section": sdata.get("section", ""),
            })

    # ── Zakázané praktiky ──
    prohibited = {
        "social_scoring": _get("uses_social_scoring") == "yes",
        "subliminal_manipulation": _get("uses_subliminal_manipulation") == "yes",
        "realtime_biometric": _get("uses_realtime_biometric") == "yes",
    }

    # ── Školení / AI gramotnost ──
    training = {
        "has_training": _get("has_ai_training") == "yes",
        "has_guidelines": _get("has_ai_guidelines") == "yes",
        "attendance": _get_detail("has_ai_training", "training_attendance", ""),
        "audience_size": _get_detail("has_ai_training", "training_audience_size", ""),
        "audience_level": _get_detail("has_ai_training", "training_audience_level", ""),
    }

    # ── Incident management ──
    incident = {
        "has_plan": _get("has_incident_plan") == "yes",
        "plan_scope": _get_detail("has_incident_plan", "incident_plan_scope", []),
        "monitors_outputs": _get("monitors_ai_outputs") == "yes",
        "tracks_changes": _get("tracks_ai_changes") == "yes",
        "has_bias_check": _get("has_ai_bias_check") == "yes",
    }

    # ── Ochrana dat ──
    data_protection = {
        "processes_personal_data": _get("ai_processes_personal_data") == "yes",
        "data_in_eu": _get("ai_data_stored_eu") == "yes",
        "has_vendor_contracts": _get("has_ai_vendor_contracts") == "yes",
    }

    # ── Lidský dohled ──
    human_oversight = {
        "can_override": _get("can_override_ai") == "yes",
        "has_logging": _get("ai_decision_logging") == "yes",
        "has_register": _get("has_ai_register") == "yes",
    }

    # ── Analýza rizik (přes existující funkci z questionnaire.py) ──
    try:
        from backend.api.questionnaire import QuestionnaireAnswer, _analyze_responses
        qa_list = [
            QuestionnaireAnswer(
                question_key=row["question_key"],
                section=row["section"],
                answer=row["answer"],
                details=row.get("details"),
                tool_name=row.get("tool_name"),
            )
            for row in responses
        ]
        analysis = _analyze_responses(qa_list)
    except Exception as e:
        logger.warning(f"Analýza dotazníku selhala (fallback): {e}")
        analysis = {
            "risk_breakdown": {"high": 0, "limited": 0, "minimal": 0},
            "recommendations": [],
            "ai_systems_declared": len(ai_systems_declared),
        }

    # Celkové riziko
    rb = analysis.get("risk_breakdown", {})
    if rb.get("high", 0) > 0:
        overall_risk = "high"
    elif rb.get("limited", 0) > 0:
        overall_risk = "limited"
    else:
        overall_risk = "minimal"

    return {
        "questionnaire_completed": True,
        "questionnaire_answers": answers_by_key,
        "questionnaire_ai_systems": len(ai_systems_declared),
        "ai_systems_declared": ai_systems_declared,
        "recommendations": analysis.get("recommendations", []),
        "risk_breakdown": analysis.get("risk_breakdown", {}),
        "overall_risk": overall_risk,
        # Firemní údaje z dotazníku
        "q_company_legal_name": company_legal_name,
        "q_company_ico": company_ico,
        "q_company_address": company_address,
        "q_company_contact_email": company_contact_email,
        "q_company_industry": company_industry,
        "q_company_size": company_size,
        "q_company_annual_revenue": company_annual_revenue,
        # Odpovědná osoba
        "oversight_person": oversight_person,
        # Zakázané praktiky
        "prohibited_systems": prohibited,
        # Školení
        "training": training,
        # Incident management
        "incident": incident,
        # Ochrana dat
        "data_protection": data_protection,
        # Lidský dohled
        "human_oversight": human_oversight,
    }


def _load_company_data(client_id: str) -> dict:
    """Načte základní data o firmě."""
    logger.info(f"[Pipeline] Načítám data firmy pro klienta {client_id}")
    supabase = get_supabase()

    company = (
        supabase.table("companies")
        .select("*")
        .eq("id", client_id)
        .limit(1)
        .execute()
    )

    if not company.data:
        # Zkusit clients tabulku
        client = (
            supabase.table("clients")
            .select("*")
            .eq("id", client_id)
            .limit(1)
            .execute()
        )
        if client.data:
            c = client.data[0]
            return {
                "company_name": c.get("company_name", c.get("name", "Neznámá firma")),
                "contact_email": c.get("email", ""),
            }
        return {"company_name": "Neznámá firma", "contact_email": ""}

    c = company.data[0]
    return {
        "company_name": c.get("name", "Neznámá firma"),
        "contact_email": c.get("email", ""),
    }


def _save_document_record(client_id: str, doc_info: dict) -> None:
    """Uloží záznam o generovaném dokumentu do DB tabulky 'documents'."""
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
        logger.info(f"[Pipeline] DB záznam uložen: {doc_info['template_key']} ({doc_info.get('format', 'pdf')})")
    except Exception as e:
        logger.error(f"[Pipeline] Nepodařilo se uložit záznam dokumentu do DB: {e}", exc_info=True)


async def generate_compliance_kit(client_id: str) -> ComplianceKitResult:
    """
    Hlavní funkce — vygeneruje kompletní AI Act Compliance Kit.

    Výstup: přesně 3 soubory:
      - 1 × PDF  — Unified PDF (titulní strana, obsah, všechny sekce, VOP)
      - 1 × HTML — transparenční stránka (adaptive — klient si ji vloží na web)
      - 1 × PPTX — školící prezentace AI Literacy

    Returns: ComplianceKitResult s metadaty o všech dokumentech
    """
    logger.info(f"Generování Compliance Kitu pro klienta: {client_id}")

    result = ComplianceKitResult(
        client_id=client_id,
        company_name="",
        generated_at=datetime.now(timezone.utc).isoformat(),
    )

    # ── 1. Načíst data ──
    logger.info(f"[Pipeline] ═══ KROK 1: Načítání dat z DB ═══")
    company_data = _load_company_data(client_id)
    scan_data = _load_scan_data(client_id)
    questionnaire_data = _load_questionnaire_data(client_id)

    # Sloučit do jednoho data dictu
    template_data = {
        **company_data,
        **scan_data,
        **questionnaire_data,
    }

    # Upřednostnit název firmy z dotazníku (přesný právní název)
    if questionnaire_data.get("q_company_legal_name"):
        template_data["company_name"] = questionnaire_data["q_company_legal_name"]
    if questionnaire_data.get("q_company_contact_email"):
        template_data["contact_email"] = questionnaire_data["q_company_contact_email"]

    result.company_name = template_data.get("company_name", "Firma")

    # Akční body z findings pro akční plán
    action_items = []
    for f in scan_data.get("findings", []):
        if f.get("action_required"):
            action_items.append({
                "action": f"{f.get('name', 'AI systém')}: {f['action_required']}",
                "risk_level": f.get("risk_level", "minimal"),
            })
    template_data["action_items"] = action_items

    # ── 2. Vyhodnotit eligibilitu dokumentů dle rizikového profilu ──
    logger.info(f"[Pipeline] ═══ KROK 2: Vyhodnocení eligibility dokumentů ═══")
    eligible, skipped = _get_eligible_documents(template_data)
    result.skipped_documents = skipped

    # Předat do šablon — compliance report vypíše přehled
    template_data["eligible_documents"] = eligible
    template_data["skipped_documents"] = skipped

    logger.info(
        f"  Rizikový profil: {template_data.get('overall_risk', '?')} | "
        f"Eligible: {len(eligible)} šablon | Skipped: {len(skipped)}"
    )
    for sk in skipped:
        logger.info(f"  ⊘ {sk['name']}: {sk['reason']}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    eligible_keys = list(eligible.keys())

    # ── 3. UNIFIED PDF — jeden velký PDF se vším ──
    logger.info(f"[Pipeline] ═══ KROK 3: Generování Unified PDF ({len(eligible_keys)} sekcí) ═══")
    try:
        unified_html = render_unified_pdf_html(template_data, eligible_keys)
        pdf_bytes = html_to_pdf(unified_html)

        pdf_filename = f"ai_act_compliance_kit_{timestamp}.pdf"
        pdf_url = save_to_supabase_storage(
            pdf_bytes, pdf_filename, client_id,
            content_type="application/pdf",
        )

        pdf_info = {
            "template_key": "compliance_kit_unified",
            "template_name": "AI Act Compliance Kit (PDF)",
            "filename": pdf_filename,
            "download_url": pdf_url,
            "size_bytes": len(pdf_bytes),
            "format": "pdf",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        result.documents.append(pdf_info)
        _save_document_record(client_id, pdf_info)
        logger.info(f"  ✓ Unified PDF ({len(pdf_bytes):,} bytes, {len(eligible_keys)} sekcí)")

    except Exception as e:
        error_msg = f"unified_pdf: {str(e)}"
        result.errors.append(error_msg)
        logger.error(f"  ✗ Unified PDF: {error_msg}", exc_info=True)

    # ── 4. HTML — transparenční stránka (standalone, adaptive CSS) ──
    logger.info(f"[Pipeline] === KROK 4: Transparencni stranka HTML ===")
    if "transparency_page" in eligible:
        try:
            renderer = TEMPLATE_RENDERERS["transparency_page"]
            html_content = renderer(template_data)
            html_bytes = html_content.encode("utf-8")

            html_filename = f"transparencni_stranka_{timestamp}.html"
            html_url = save_to_supabase_storage(
                html_bytes, html_filename, client_id,
                content_type="text/html",
            )

            html_info = {
                "template_key": "transparency_page",
                "template_name": TEMPLATE_NAMES["transparency_page"],
                "filename": html_filename,
                "download_url": html_url,
                "size_bytes": len(html_bytes),
                "format": "html",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            result.documents.append(html_info)
            _save_document_record(client_id, html_info)
            logger.info(f"  ✓ Transparenční stránka HTML ({len(html_bytes):,} bytes)")

        except Exception as e:
            error_msg = f"transparency_page: {str(e)}"
            result.errors.append(error_msg)
            logger.error(f"  ✗ HTML: {error_msg}", exc_info=True)

    # ── 5. PPTX — školící prezentace (vždy — čl. 4 AI Act) ──
    logger.info("[Pipeline] === KROK 5: PPTX prezentace ===")
    try:
        from backend.documents.pptx_generator import generate_training_pptx
        pptx_bytes = generate_training_pptx(template_data)

        pptx_filename = f"skoleni_ai_literacy_{timestamp}.pptx"
        pptx_url = save_to_supabase_storage(
            pptx_bytes, pptx_filename, client_id,
            content_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )

        pptx_info = {
            "template_key": "training_presentation",
            "template_name": "Školení AI Literacy — Prezentace (PPTX)",
            "filename": pptx_filename,
            "download_url": pptx_url,
            "size_bytes": len(pptx_bytes),
            "format": "pptx",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        result.documents.append(pptx_info)
        _save_document_record(client_id, pptx_info)
        logger.info(f"  ✓ PPTX prezentace ({len(pptx_bytes):,} bytes)")

    except Exception as e:
        error_msg = f"training_presentation: {str(e)}"
        result.errors.append(error_msg)
        logger.error(f"  ✗ PPTX: {error_msg}", exc_info=True)

    logger.info(
        f"Compliance Kit hotov: {result.success_count} OK, {result.error_count} chyb"
    )
    return result


async def generate_single_document(
    client_id: str,
    template_key: str,
) -> dict:
    """Generuje jeden konkrétní dokument pro klienta (standalone HTML → PDF)."""
    company_data = _load_company_data(client_id)
    scan_data = _load_scan_data(client_id)
    questionnaire_data = _load_questionnaire_data(client_id)

    template_data = {
        **company_data,
        **scan_data,
        **questionnaire_data,
    }

    if questionnaire_data.get("q_company_legal_name"):
        template_data["company_name"] = questionnaire_data["q_company_legal_name"]
    if questionnaire_data.get("q_company_contact_email"):
        template_data["contact_email"] = questionnaire_data["q_company_contact_email"]

    action_items = []
    for f in scan_data.get("findings", []):
        if f.get("action_required"):
            action_items.append({
                "action": f"{f.get('name', 'AI systém')}: {f['action_required']}",
                "risk_level": f.get("risk_level", "minimal"),
            })
    template_data["action_items"] = action_items

    doc_info = generate_document_pdf(
        template_key=template_key,
        data=template_data,
        client_id=client_id,
    )

    _save_document_record(client_id, doc_info)
    return doc_info
