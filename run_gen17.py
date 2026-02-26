"""Gen17 — Pipeline v3 with preflight validation, placeholder ban, M1 two-pass."""
import asyncio
import logging
import sys
import time
import json

class FlushHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

handler = FlushHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s %(message)s"))
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger("gen17")

async def main():
    # CORRECT client_id (linked to company 62e22b1d = www.desperados-design.cz)
    client_id = "950c79fa-28a1-42d0-9e27-3c998ca9bc11"

    logger.info("=" * 70)
    logger.info("GEN17 — AI Act Compliance Kit (Pipeline v3 + Gen17 improvements)")
    logger.info(f"Client ID: {client_id}")
    logger.info("  Preflight validation: ON")
    logger.info("  Post-doc-1 validation: ON")
    logger.info("  Placeholder ban: ABSOLUTE")
    logger.info("  M1 two-pass: ON (replaces M4)")
    logger.info("  Inter-doc delay: 15s")
    logger.info("  Inspection report: v2")
    logger.info("=" * 70)

    start = time.time()

    from backend.documents.pipeline_v3 import generate_compliance_kit
    result = await generate_compliance_kit(client_id)

    elapsed = time.time() - start

    logger.info("")
    logger.info("=" * 70)
    logger.info("GEN17 RESULT")
    logger.info("=" * 70)
    logger.info(f"  Company: {result.company_name}")
    logger.info(f"  Documents: {result.success_count} OK, {result.error_count} errors")
    logger.info(f"  Total cost: ${result.total_cost_usd:.4f}")
    logger.info(f"  Total tokens: {result.total_tokens:,}")
    logger.info(f"  Time: {elapsed:.0f}s ({elapsed/60:.1f} min)")

    for doc in result.documents:
        fmt = doc['format'].upper()
        name = doc['template_name']
        size = doc['size_bytes']
        url = doc.get('download_url', '')[:80]
        logger.info(f"  [{fmt:4s}] {name:50s} {size:>8,} B  {url}")

    if result.errors:
        logger.error("\nERRORS:")
        for e in result.errors:
            logger.error(f"  {e}")

    # Save result JSON
    result_data = {
        "generation": 17,
        "company_name": result.company_name,
        "success_count": result.success_count,
        "error_count": result.error_count,
        "total_cost_usd": round(result.total_cost_usd, 4),
        "total_tokens": result.total_tokens,
        "elapsed_s": round(elapsed, 1),
        "documents": result.documents,
        "errors": result.errors,
        "pipeline_log": result.pipeline_log,
    }
    with open("/opt/aishield/gen17_result.json", "w") as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False, default=str)
    logger.info(f"\nResult saved to /opt/aishield/gen17_result.json")
    logger.info("=" * 70)

asyncio.run(main())
