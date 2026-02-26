"""
Gen13 — 13 dokumentů včetně LLM-generované transparency page a PPTX
"""
import sys
sys.path.insert(0, "/opt/aishield")

import asyncio
import json
import logging
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("/opt/aishield/gen13.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

ORDER_ID = "3054d701-df1e-476e-b179-1616ca9cbc1f"

async def main():
    from backend.documents.pipeline_v3 import generate_compliance_kit, DOCUMENT_KEYS
    logging.info(f"GEN13 START — {len(DOCUMENT_KEYS)} dokumentů: {DOCUMENT_KEYS}")
    logging.info(f"Order ID: {ORDER_ID}")

    result = await generate_compliance_kit(ORDER_ID)

    out = {
        "generation": "gen13",
        "order_id": ORDER_ID,
        "company_name": result.company_name,
        "success_count": result.success_count,
        "error_count": result.error_count,
        "total_cost_usd": result.total_cost_usd,
        "total_tokens": result.total_tokens,
        "documents": result.documents,
        "errors": result.errors,
        "pipeline_log": result.pipeline_log,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    with open("/opt/aishield/gen13_result.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)

    logging.info(f"GEN13 HOTOVO — {result.success_count} OK, {result.error_count} chyb, ${result.total_cost_usd:.4f}")

if __name__ == "__main__":
    asyncio.run(main())
