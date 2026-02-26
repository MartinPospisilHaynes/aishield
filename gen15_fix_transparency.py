"""
GEN15-FIX: Dogenerování chybějící transparency_page.
Využívá přímo pipeline funkce se správným pořadím argumentů.
"""
import asyncio
import json
import logging
import sys
import os
import time

sys.path.insert(0, "/opt/aishield")
os.chdir("/opt/aishield")

os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", "/opt/aishield/vertex-sa-key.json")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("/opt/aishield/gen15_fix_transparency.log", mode="w"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

ORDER_ID = "3054d701-df1e-476e-b179-1616ca9cbc1f"
COMPANY_ID = "62e22b1d-dbc3-486d-8aad-c495732049c8"
CLIENT_ID = "950c79fa-28a1-42d0-9e27-3c998ca9bc11"


async def main():
    logger.info("GEN15-FIX: Dogenerovani transparency_page")

    from backend.documents.pipeline_v3 import (
        _load_company_data, _load_scan_data, _load_questionnaire_data,
        build_company_context,
    )
    from backend.documents.m1_generator import generate_draft
    from backend.documents.m2_eu_critic import review_eu
    from backend.documents.m3_client_critic import review_client
    from backend.documents.m4_refiner import refine
    from backend.documents.pdf_generator import save_to_supabase_storage

    # 1. Nacti data ze DB (stejne jako pipeline)
    logger.info("Nacitam company data...")
    company_data = _load_company_data(COMPANY_ID)
    scan_data = _load_scan_data(COMPANY_ID)
    questionnaire_data = _load_questionnaire_data(CLIENT_ID)

    template_data = {}
    template_data.update(company_data)
    template_data.update(scan_data)
    template_data.update(questionnaire_data)
    if questionnaire_data.get("q_company_legal_name"):
        template_data["company_name"] = questionnaire_data["q_company_legal_name"]

    company_context = build_company_context(template_data)
    logger.info("Company context: %d znaku", len(company_context))

    doc_key = "transparency_page"
    t0 = time.time()

    # 2. M1 Generator (company_context, doc_key)
    logger.info("M1 Generator...")
    draft_html, m1_meta = await generate_draft(company_context, doc_key)
    logger.info("M1 hotov: %d znaku, $%.4f", len(draft_html), m1_meta.get("cost_usd", 0))

    if not draft_html or len(draft_html) < 100:
        logger.error("M1 vratil prazdny draft (%d znaku). Koncim.", len(draft_html or ""))
        sys.exit(2)

    # 3. M2 EU Critic (draft_html, company_context, doc_key)
    logger.info("M2 EU Critic...")
    eu_critique, m2_meta = await review_eu(draft_html, company_context, doc_key)
    eu_score = eu_critique.get("skore", "?") if isinstance(eu_critique, dict) else "?"
    logger.info("M2 hotov: EU skore=%s, $%.4f", eu_score, m2_meta.get("cost_usd", 0))

    # 4. M3 Client Critic (draft_html, company_context, doc_key)
    logger.info("M3 Client Critic...")
    client_critique, m3_meta = await review_client(draft_html, company_context, doc_key)
    client_score = client_critique.get("skore", "?") if isinstance(client_critique, dict) else "?"
    logger.info("M3 hotov: Client skore=%s, $%.4f", client_score, m3_meta.get("cost_usd", 0))

    # 5. M4 Refiner (draft_html, eu_critique, client_critique, company_context, doc_key)
    logger.info("M4 Refiner...")
    final_html, m4_meta = await refine(draft_html, eu_critique, client_critique, company_context, doc_key)
    logger.info("M4 hotov: %d znaku, $%.4f", len(final_html), m4_meta.get("cost_usd", 0))

    # 6. Uloz HTML do Supabase
    logger.info("Ukladam do Supabase Storage...")
    timestamp = "20260225_194520"
    filename = "transparencni_stranka_%s.html" % timestamp
    url = save_to_supabase_storage(
        final_html.encode("utf-8"),
        filename,
        COMPANY_ID,
        content_type="text/html",
    )
    logger.info("HTML ulozeno: %s", url)

    elapsed = time.time() - t0
    total_cost = sum(m.get("cost_usd", 0) for m in [m1_meta, m2_meta, m3_meta, m4_meta])
    logger.info("=" * 60)
    logger.info("TRANSPARENCY_PAGE HOTOV")
    logger.info("Cas: %.0fs | Cost: $%.4f | Znaku: %d", elapsed, total_cost, len(final_html))
    logger.info("EU skore: %s | Client skore: %s", eu_score, client_score)
    logger.info("URL: %s", url)
    logger.info("=" * 60)

    # Uloz HTML i lokalne
    with open("/opt/aishield/gen15_transparency_page.html", "w") as f:
        f.write(final_html)
    logger.info("Lokalni kopie: /opt/aishield/gen15_transparency_page.html")


if __name__ == "__main__":
    asyncio.run(main())
