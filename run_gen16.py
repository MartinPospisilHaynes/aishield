"""Gen16 — Pipeline v3 with all audit improvements."""
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
logger = logging.getLogger("gen16")

async def main():
    company_id = "3900ae47-25d5-42fb-af4d-0d06623bc8cc"

    logger.info("=" * 70)
    logger.info("GEN16 — AI Act Compliance Kit (Pipeline v3 + audit improvements)")
    logger.info(f"Company ID: {company_id}")
    logger.info("=" * 70)

    start = time.time()

    from backend.documents.pipeline_v3 import generate_compliance_kit
    result = await generate_compliance_kit(company_id)

    elapsed = time.time() - start

    logger.info("")
    logger.info("=" * 70)
    logger.info("GEN16 RESULT")
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
        "generation": 16,
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
    with open("/opt/aishield/gen16_result.json", "w") as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False, default=str)
    logger.info(f"\nResult saved to /opt/aishield/gen16_result.json")
    logger.info("=" * 70)

asyncio.run(main())
