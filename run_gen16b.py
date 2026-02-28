"""Gen16 Part 2 — Dogenerování 6 chybějících dokumentů (Claude limit recovery)."""
import asyncio
import logging
import sys
import time
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("gen16b")

MISSING_DOCS = [
    "chatbot_notices",
    "ai_policy",
    "incident_response_plan",
    "dpia_template",
    "vendor_checklist",
    "monitoring_plan",
]

async def main():
    company_id = "3900ae47-25d5-42fb-af4d-0d06623bc8cc"

    logger.info("=" * 70)
    logger.info("GEN16 Part 2 — Dogenerace 6 chybějících dokumentů")
    logger.info(f"Missing: {', '.join(MISSING_DOCS)}")
    logger.info("=" * 70)

    start = time.time()

    from backend.documents.pipeline_v3 import (
        _resolve_ids, _load_company_data, _load_scan_data,
        _load_questionnaire_data, build_company_context,
        DOCUMENT_NAMES, SECTION_SLUG,
    )
    from backend.documents.m1_generator import generate_draft
    from backend.documents.m2_eu_critic import review_eu
    from backend.documents.m3_client_critic import review_client
    from backend.documents.m4_refiner import refine
    from backend.documents.pdf_generator import html_to_pdf, save_to_supabase_storage
    from backend.documents.pdf_renderer import render_section_html
    from datetime import datetime, timezone

    ids = _resolve_ids(company_id)
    cid = ids["client_id"]
    comp_id = ids["company_id"]

    company_data = _load_company_data(comp_id)
    scan_data = _load_scan_data(comp_id)
    q_data = _load_questionnaire_data(cid)

    template_data = {**company_data, **scan_data, **q_data}
    if q_data.get("q_company_legal_name"):
        template_data["company_name"] = q_data["q_company_legal_name"]

    company_context = build_company_context(template_data)
    company_name = template_data.get("company_name", "Firma")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    results = []
    errors = []

    for doc_key in MISSING_DOCS:
        doc_name = DOCUMENT_NAMES.get(doc_key, doc_key)
        slug = SECTION_SLUG.get(doc_key, doc_key)
        logger.info(f"\n{'─'*60}")
        logger.info(f"GENERATING: {doc_name} ({doc_key})")
        logger.info(f"{'─'*60}")

        try:
            # M1 → M2 → M3 → M4
            draft_html, m1_meta = await generate_draft(company_context, doc_key)
            logger.info(f"  M1 OK: {len(draft_html)} znaků")

            eu_critique, m2_meta = await review_eu(draft_html, company_context, doc_key)
            eu_score = m2_meta.get("eu_score", 0)
            logger.info(f"  M2 OK: EU score={eu_score}")

            if eu_score >= 8:
                logger.info(f"  M3 SKIP (EU score >= 8)")
                client_critique = json.dumps({
                    "skóre_klient": 8,
                    "celkový_dojem": "přeskočeno — EU skóre dostatečné",
                    "nálezy": [],
                    "doporučení": []
                }, ensure_ascii=False)
            else:
                client_critique, m3_meta = await review_client(draft_html, company_context, doc_key)
                logger.info(f"  M3 OK: score={m3_meta.get('client_score', '?')}")

            final_html, m4_meta = await refine(draft_html, eu_critique, client_critique, company_context, doc_key)
            logger.info(f"  M4 OK: {len(final_html)} znaků")

            # Generate PDF
            section_html = render_section_html(doc_key, final_html, company_name)
            pdf_bytes = html_to_pdf(section_html)
            pdf_filename = f"{slug}_{timestamp}.pdf"
            pdf_url = save_to_supabase_storage(
                pdf_bytes, pdf_filename, comp_id,
                content_type="application/pdf",
            )

            doc_info = {
                "template_key": doc_key,
                "template_name": doc_name,
                "filename": pdf_filename,
                "download_url": pdf_url,
                "size_bytes": len(pdf_bytes),
                "format": "pdf",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            results.append(doc_info)
            logger.info(f"  PDF: {pdf_filename} ({len(pdf_bytes):,} B)")

        except Exception as e:
            errors.append(f"{doc_key}: {str(e)[:200]}")
            logger.error(f"  CHYBA: {e}", exc_info=True)

    elapsed = time.time() - start
    logger.info(f"\n{'='*70}")
    logger.info(f"PART 2 DONE: {len(results)} OK, {len(errors)} errors, {elapsed:.0f}s")
    for r in results:
        logger.info(f"  {r['template_name']:40s} {r['size_bytes']:>8,}B  {r['download_url'][:80]}")
    if errors:
        for e in errors:
            logger.error(f"  ERROR: {e}")

    # Save supplementary result
    with open("/opt/aishield/gen16b_result.json", "w") as f:
        json.dump({"documents": results, "errors": errors, "elapsed_s": round(elapsed, 1)}, f, indent=2, ensure_ascii=False, default=str)
    logger.info(f"\nSaved to /opt/aishield/gen16b_result.json")

asyncio.run(main())
