#!/usr/bin/env python3
"""
AIshield.cz — Generování #12
Pipeline v3: M1 (Gemini) → M2 (Claude Sonnet) → M3 (Gemini) → M4 (Gemini)
COST-OPTIMIZED: Claude only for M2 EU legal review.

Spuštění:
    cd /opt/aishield
    /opt/aishield/venv/bin/python3 gen12.py

Monitoring:
    tail -f /opt/aishield/gen12.log
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime, timezone

# ── Logging setup ──────────────────────────────────────────────────
LOG_FILE = "/opt/aishield/gen12.log"
LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
root_logger.addHandler(console_handler)

# File handler
file_handler = logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8")
file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
root_logger.addHandler(file_handler)

logger = logging.getLogger("gen12")


# ── Configuration ──────────────────────────────────────────────────
ORDER_ID = "3054d701-df1e-476e-b179-1616ca9cbc1f"


async def main():
    """Hlavní funkce — spouští Pipeline v3."""

    logger.info("=" * 70)
    logger.info("AISHIELD.CZ — GENEROVÁNÍ #12 (COST-OPTIMIZED)")
    logger.info("Pipeline v3: M1(Gemini) → M2(Sonnet 4.6) → M3(Gemini) → M4(Gemini)")
    logger.info(f"Order ID: {ORDER_ID}")
    logger.info(f"Start: {datetime.now(timezone.utc).isoformat()}")
    logger.info(f"Log: {LOG_FILE}")
    logger.info("=" * 70)
    logger.info("")

    start_time = time.time()

    try:
        from backend.documents.pipeline_v3 import generate_compliance_kit

        result = await generate_compliance_kit(ORDER_ID)

        elapsed = time.time() - start_time

        logger.info("")
        logger.info("=" * 70)
        logger.info("VÝSLEDEK GENEROVÁNÍ #12")
        logger.info("=" * 70)
        logger.info(f"Firma: {result.company_name}")
        logger.info(f"Dokumenty OK: {result.success_count}")
        logger.info(f"Chyby: {result.error_count}")
        logger.info(f"Celkový cost: ${result.total_cost_usd:.4f}")
        logger.info(f"Celkové tokeny: {result.total_tokens:,}")
        logger.info(f"Celkový čas: {elapsed:.0f}s ({elapsed/60:.1f} min)")
        logger.info("")

        if result.documents:
            logger.info("VYGENEROVANÉ DOKUMENTY:")
            for i, doc in enumerate(result.documents, 1):
                logger.info(f"  {i}. {doc['template_name']}")
                logger.info(f"     Soubor: {doc['filename']}")
                logger.info(f"     Velikost: {doc.get('size_bytes', 0):,} bytes")
                logger.info(f"     URL: {doc.get('download_url', 'N/A')}")
                logger.info("")

        if result.errors:
            logger.warning("CHYBY:")
            for err in result.errors:
                logger.warning(f"  ⚠ {err}")
            logger.info("")

        # Pipeline log detail
        logger.info("PIPELINE LOG:")
        for entry in result.pipeline_log:
            if entry.get("step") == "data_loaded":
                logger.info(f"  Data: {entry.get('company','?')}, "
                          f"findings={entry.get('findings',0)}, "
                          f"declared={entry.get('declared_systems',0)}, "
                          f"risk={entry.get('overall_risk','?')}")
            elif entry.get("step") == "completed":
                logger.info(f"  Hotovo: {entry.get('total_documents',0)} docs, "
                          f"${entry.get('total_cost_usd',0):.4f}, "
                          f"{entry.get('total_time_s',0):.0f}s")
            elif entry.get("doc_key"):
                doc = entry
                logger.info(
                    f"  {doc.get('doc_index','?')} {doc.get('doc_name','?')}: "
                    f"EU={doc.get('eu_score','?')}/10, "
                    f"Client={doc.get('client_score','?')}/10, "
                    f"draft={doc.get('draft_chars',0)} → final={doc.get('final_chars',0)} znaků, "
                    f"${doc.get('cost_usd',0):.4f}, {doc.get('time_s',0):.0f}s"
                )
            elif entry.get("error"):
                logger.warning(f"  CHYBA {entry.get('doc_key','?')}: {entry.get('error','?')}")

        # Save result JSON
        result_json = json.dumps(result.to_dict(), ensure_ascii=False, indent=2, default=str)
        result_path = "/opt/aishield/gen12_result.json"
        with open(result_path, "w", encoding="utf-8") as f:
            f.write(result_json)
        logger.info(f"\nVýsledek uložen: {result_path}")

        logger.info("")
        logger.info("=" * 70)

        if result.error_count == 0:
            logger.info("GENEROVÁNÍ #12 ÚSPĚŠNĚ DOKONČENO!")
        else:
            logger.warning(f"GENEROVÁNÍ #12 DOKONČENO S {result.error_count} CHYBAMI")

        logger.info("=" * 70)

        return result

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"FATÁLNÍ CHYBA po {elapsed:.0f}s: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
