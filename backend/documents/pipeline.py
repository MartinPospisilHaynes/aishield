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
from backend.documents.pdf_generator import generate_document_pdf

logger = logging.getLogger(__name__)


@dataclass
class ComplianceKitResult:
    """Výsledek generování celého Compliance Kitu."""
    client_id: str
    company_name: str
    documents: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
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
            "generated_at": self.generated_at,
            "summary": {
                "total_templates": len(TEMPLATE_RENDERERS),
                "generated": self.success_count,
                "failed": self.error_count,
            },
        }


def _load_scan_data(client_id: str) -> dict:
    """Načte data ze skenu webu pro daného klienta."""
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
            "name": f.get("tool_name", "AI systém"),
            "category": f.get("category", ""),
            "risk_level": rl,
            "ai_act_article": f.get("ai_act_article", ""),
            "action_required": f.get("action_required", ""),
            "confirmed_by_client": f.get("confirmed_by_client", "unknown"),
        })

    return {
        "findings": findings,
        "url": scan.get("url", ""),
        "scan_id": scan_id,
        "scan_date": scan.get("created_at", ""),
        "risk_breakdown": risk_breakdown,
    }


def _load_questionnaire_data(client_id: str) -> dict:
    """Načte data z dotazníku pro daného klienta."""
    supabase = get_supabase()

    responses = (
        supabase.table("questionnaire_responses")
        .select("*")
        .eq("company_id", client_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not responses.data:
        return {"questionnaire_ai_systems": 0, "recommendations": []}

    response = responses.data[0]
    answers = response.get("answers", {})
    ai_analysis = response.get("ai_analysis", {})

    # Počet interních AI systémů
    q_systems = 0
    for section_key, section_answers in answers.items():
        if isinstance(section_answers, dict):
            for key, val in section_answers.items():
                if isinstance(val, str) and val.lower() in ("ano", "yes", "true"):
                    q_systems += 1

    # Doporučení z AI analýzy
    recommendations = ai_analysis.get("recommendations", [])

    return {
        "questionnaire_ai_systems": q_systems,
        "recommendations": recommendations,
        "overall_risk": ai_analysis.get("overall_risk_level", "minimal"),
    }


def _load_company_data(client_id: str) -> dict:
    """Načte základní data o firmě."""
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
    except Exception as e:
        logger.warning(f"Nepodařilo se uložit záznam dokumentu do DB: {e}")


async def generate_compliance_kit(client_id: str) -> ComplianceKitResult:
    """
    Hlavní funkce — vygeneruje kompletní AI Act Compliance Kit.
    
    1. Načte data z DB (sken + dotazník + firma)
    2. Vygeneruje 7 dokumentů (HTML → PDF)
    3. Uloží do Supabase Storage
    4. Zapíše záznamy do DB tabulky documents
    
    Returns: ComplianceKitResult s metadaty o všech dokumentech
    """
    logger.info(f"Generování Compliance Kitu pro klienta: {client_id}")

    result = ComplianceKitResult(
        client_id=client_id,
        company_name="",
        generated_at=datetime.now(timezone.utc).isoformat(),
    )

    # 1. Načíst data
    company_data = _load_company_data(client_id)
    scan_data = _load_scan_data(client_id)
    questionnaire_data = _load_questionnaire_data(client_id)

    result.company_name = company_data.get("company_name", "Firma")

    # 2. Sloučit do jednoho data dictu
    template_data = {
        **company_data,
        **scan_data,
        **questionnaire_data,
    }

    # Automatické action_items z findings pro akční plán
    action_items = []
    for f in scan_data.get("findings", []):
        if f.get("action_required"):
            action_items.append({
                "action": f"{f.get('name', 'AI systém')}: {f['action_required']}",
                "risk_level": f.get("risk_level", "minimal"),
            })
    template_data["action_items"] = action_items

    # 3. Generovat všechny dokumenty
    for template_key in TEMPLATE_RENDERERS:
        try:
            doc_info = generate_document_pdf(
                template_key=template_key,
                data=template_data,
                client_id=client_id,
            )
            result.documents.append(doc_info)

            # 4. Záznam do DB
            _save_document_record(client_id, doc_info)

            logger.info(f"  ✓ {doc_info['template_name']} ({doc_info['format']})")

        except Exception as e:
            error_msg = f"{template_key}: {str(e)}"
            result.errors.append(error_msg)
            logger.error(f"  ✗ {error_msg}")

    logger.info(
        f"Compliance Kit hotov: {result.success_count} OK, {result.error_count} chyb"
    )

    # 5. Generovat PPTX prezentaci (školení AI Literacy)
    try:
        from backend.documents.pptx_generator import generate_training_pptx
        from backend.documents.pdf_generator import save_pdf_to_supabase

        pptx_bytes = generate_training_pptx(template_data)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        pptx_filename = f"training_presentation_{timestamp}.pptx"

        download_url = save_pdf_to_supabase(
            pptx_bytes, pptx_filename, client_id,
        )

        pptx_info = {
            "template_key": "training_presentation",
            "template_name": "Školení AI Literacy — Prezentace (PPTX)",
            "filename": pptx_filename,
            "download_url": download_url,
            "size_bytes": len(pptx_bytes),
            "format": "pptx",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        result.documents.append(pptx_info)
        _save_document_record(client_id, pptx_info)
        logger.info(f"  ✓ PPTX prezentace ({len(pptx_bytes)} bytes)")

    except Exception as e:
        error_msg = f"training_presentation: {str(e)}"
        result.errors.append(error_msg)
        logger.error(f"  ✗ PPTX: {error_msg}")

    return result


async def generate_single_document(
    client_id: str,
    template_key: str,
) -> dict:
    """Generuje jeden konkrétní dokument pro klienta."""
    company_data = _load_company_data(client_id)
    scan_data = _load_scan_data(client_id)
    questionnaire_data = _load_questionnaire_data(client_id)

    template_data = {
        **company_data,
        **scan_data,
        **questionnaire_data,
    }

    # Akční body
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
