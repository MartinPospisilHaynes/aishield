"""
AIshield.cz — Amendment Pipeline

Orchestruje generování dodatků po změně dotazníku:
1. Přijme změny z PATCH /questionnaire/answer
2. M7: Analyzuje dopad změn
3. M8: Vygeneruje HTML dodatku
4. M2: EU Inspector zkontroluje dodatek
5. Uloží do DB se statusem pending_review (čeká na admin schválení)
6. Pošle admin notifikaci
"""

import logging
from datetime import datetime, timezone

from backend.database import get_supabase
from backend.documents.m7_change_impact import analyze_change_impact
from backend.documents.m8_amendment import generate_amendment
from backend.documents.m2_eu_critic import review_eu
from backend.documents.pdf_generator import html_to_pdf, save_to_supabase_storage
from backend.documents.pipeline import _load_questionnaire_data, _load_scan_data, build_company_context

logger = logging.getLogger(__name__)


async def process_amendment(
    client_id: str,
    company_id: str,
    changes: list[dict],
) -> dict:
    """
    Celý amendment pipeline:
    changes = [{key, old_answer, new_answer, old_details, new_details}, ...]

    Vrací:
        {
            status: "generated" | "no_changes" | "error",
            amendment_id: UUID | None,
            impact: {...},
        }
    """
    supabase = get_supabase()

    # ── Krok 1: M7 — analýza dopadu ──
    logger.info(f"[Amendment] Spouštím M7 pro {len(changes)} změn, client={client_id}")

    # Načti aktuální risk breakdown
    old_risk = None
    try:
        from backend.api.questionnaire import _analyze_responses, QuestionnaireAnswer
        old_resp = supabase.table("questionnaire_responses") \
            .select("question_key, section, answer, details, tool_name") \
            .eq("client_id", client_id) \
            .neq("question_key", "__position__") \
            .execute()
        if old_resp.data:
            qa_list = [QuestionnaireAnswer(
                question_key=r["question_key"], section=r["section"],
                answer=r["answer"], details=r.get("details"), tool_name=r.get("tool_name"),
            ) for r in old_resp.data]
            analysis = _analyze_responses(qa_list)
            old_risk = analysis.get("risk_breakdown")
    except Exception as e:
        logger.warning(f"[Amendment] Nepodařilo se načíst risk breakdown: {e}")

    impact = analyze_change_impact(changes, old_risk)

    if not impact["needs_amendment"]:
        logger.info("[Amendment] Žádný amendment není třeba (jen kontaktní údaje)")
        return {
            "status": "no_changes",
            "amendment_id": None,
            "impact": impact,
        }

    # ── Krok 2: Načíst kontext firmy ──
    try:
        scan_data = _load_scan_data(company_id)
        quest_data = _load_questionnaire_data(client_id)

        # Načíst company info
        comp = supabase.table("companies").select("name, ico, url, email") \
            .eq("id", company_id).limit(1).execute()
        company_name = comp.data[0].get("name", "Neznámá firma") if comp.data else "Neznámá firma"

        company_context = build_company_context({
            **scan_data, **quest_data,
            "company_name": company_name,
        })
    except Exception as e:
        logger.error(f"[Amendment] Chyba při načítání kontextu: {e}")
        return {"status": "error", "amendment_id": None, "impact": impact}

    # ── Krok 3: Zjistit číslo dodatku ──
    try:
        existing = supabase.table("documents") \
            .select("amendment_number") \
            .eq("company_id", company_id) \
            .not_.is_("amendment_number", "null") \
            .order("amendment_number", desc=True) \
            .limit(1).execute()
        last_num = existing.data[0]["amendment_number"] if existing.data else 0
        amendment_number = last_num + 1
    except Exception:
        amendment_number = 1

    # ── Krok 4: M8 — vygenerovat dodatek ──
    affected_docs = impact["affected_documents"]
    logger.info(f"[Amendment] M8: Generuji dodatek č.{amendment_number} pro {company_name}")

    try:
        amendment_html, m8_meta = await generate_amendment(
            company_context=company_context,
            impact_analysis=impact,
            affected_doc_keys=affected_docs,
            amendment_number=amendment_number,
            company_name=company_name,
        )
    except Exception as e:
        logger.error(f"[Amendment] M8 selhal: {e}")
        return {"status": "error", "amendment_id": None, "impact": impact}

    # ── Krok 5: M2 — EU Inspector kontrola dodatku ──
    m2_score = 0
    try:
        eu_critique, m2_meta = await review_eu(amendment_html, company_context, "amendment")
        m2_score = eu_critique.get("skore", 0) if isinstance(eu_critique, dict) else 0
        logger.info(f"[Amendment] M2 skóre: {m2_score}/10")
    except Exception as e:
        logger.warning(f"[Amendment] M2 kontrola selhala (pokračuji): {e}")

    # ── Krok 6: PDF + uložení ──
    try:
        pdf_bytes = html_to_pdf(amendment_html)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"dodatek_{amendment_number}_{timestamp}.pdf"
        pdf_url = save_to_supabase_storage(pdf_bytes, filename, company_id)
    except Exception as e:
        logger.error(f"[Amendment] PDF generování selhalo: {e}")
        pdf_url = ""

    # ── Krok 7: Uložit do DB jako pending_review ──
    amendment_id = None
    try:
        doc_row = {
            "company_id": company_id,
            "type": "amendment",
            "name": f"Dodatek č. {amendment_number}",
            "url": pdf_url,
            "format": "pdf",
            "amendment_number": amendment_number,
            "change_trigger": {
                "changes": changes,
                "impact": impact,
                "m2_score": m2_score,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
            "approval_status": "pending_review",  # Čeká na admin schválení
        }
        result = supabase.table("documents").insert(doc_row).execute()
        if result.data:
            amendment_id = result.data[0]["id"]
            logger.info(f"[Amendment] Uložen: id={amendment_id}, status=pending_review")
    except Exception as e:
        logger.error(f"[Amendment] DB uložení selhalo: {e}")

    # ── Krok 8: Zapsat do change_log ──
    try:
        for change in changes:
            supabase.table("questionnaire_change_log").insert({
                "client_id": client_id,
                "company_id": company_id,
                "question_key": change["key"],
                "old_answer": change.get("old_answer"),
                "new_answer": change.get("new_answer"),
                "old_details": change.get("old_details"),
                "new_details": change.get("new_details"),
                "impact_level": next(
                    (d["impact"] for d in impact["changes_detail"] if d["key"] == change["key"]),
                    "medium"
                ),
                "risk_change": impact["risk_change"],
                "affected_documents": affected_docs,
                "amendment_id": amendment_id,
            }).execute()
    except Exception as e:
        logger.warning(f"[Amendment] Change log zápis selhal: {e}")

    # ── Krok 9: Admin notifikace ──
    try:
        await _send_amendment_notification(
            company_name=company_name,
            company_id=company_id,
            amendment_number=amendment_number,
            impact=impact,
            m2_score=m2_score,
            amendment_id=amendment_id,
        )
    except Exception as e:
        logger.warning(f"[Amendment] Email notifikace selhala: {e}")

    return {
        "status": "generated",
        "amendment_id": amendment_id,
        "impact": impact,
        "amendment_number": amendment_number,
        "m2_score": m2_score,
        "pdf_url": pdf_url,
    }


async def _send_amendment_notification(
    company_name: str,
    company_id: str,
    amendment_number: int,
    impact: dict,
    m2_score: int,
    amendment_id: str | None,
) -> None:
    """Pošle admin emailem info o novém dodatku ke schválení."""
    changes_rows = ""
    for detail in impact.get("changes_detail", []):
        if detail.get("impact") == "none":
            continue
        color = {
            "critical": "#dc2626", "high": "#ea580c",
            "medium": "#d97706", "low": "#65a30d",
        }.get(detail["impact"], "#6b7280")
        changes_rows += f"""
        <tr>
            <td style="padding:8px; border:1px solid #ddd;">{detail['key']}</td>
            <td style="padding:8px; border:1px solid #ddd;">{detail['description']}</td>
            <td style="padding:8px; border:1px solid #ddd; color:{color}; font-weight:bold;">{detail['impact'].upper()}</td>
        </tr>"""

    impact_color = {
        "critical": "#dc2626", "high": "#ea580c",
        "medium": "#d97706", "low": "#65a30d", "none": "#6b7280",
    }.get(impact["impact_level"], "#6b7280")

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto;">
        <h2 style="color:#1a1a2e;">📋 Dodatek č. {amendment_number} čeká na schválení</h2>
        <p><b>Firma:</b> {company_name}</p>
        <p><b>Dopad změny:</b> <span style="color:{impact_color}; font-weight:bold;">{impact['impact_level'].upper()}</span></p>
        <p><b>Změna rizika:</b> {impact['risk_change']}</p>
        <p><b>M2 EU Inspector skóre:</b> {m2_score}/10</p>
        <p><b>Dotčeno dokumentů:</b> {len(impact['affected_documents'])}</p>

        <h3>Změny:</h3>
        <table style="width:100%; border-collapse:collapse;">
            <tr style="background:#f0f0f0;">
                <th style="padding:8px; text-align:left; border:1px solid #ddd;">Otázka</th>
                <th style="padding:8px; text-align:left; border:1px solid #ddd;">Popis</th>
                <th style="padding:8px; text-align:left; border:1px solid #ddd;">Dopad</th>
            </tr>
            {changes_rows}
        </table>

        <div style="margin:20px 0; padding:16px; background:#fff3cd; border:1px solid #ffc107; border-radius:8px;">
            <b>⚠️ Tento dodatek čeká na tvé schválení.</b><br>
            Po schválení se zpřístupní klientovi na dashboardu ke stažení.
        </div>

        <p>
            <a href="https://aishield.cz/admin" style="display:inline-block; background:#6366f1; color:white; padding:12px 24px; border-radius:8px; text-decoration:none; font-weight:bold;">
                📋 Schválit v admin panelu
            </a>
        </p>
    </div>
    """

    from backend.outbound.email_engine import send_email
    await send_email(
        to="info@desperados-design.cz",
        subject=f"📋 Dodatek č. {amendment_number} — {company_name} — ke schválení",
        html=html,
    )
    logger.info(f"[Amendment] Admin notifikace odeslána pro {company_name}")
