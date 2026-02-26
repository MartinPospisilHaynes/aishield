"""GEN14 — Compliance Kit se 13 dokumenty + Gemini→Claude fallback."""
import asyncio, json, logging, sys, os, time

sys.path.insert(0, "/opt/aishield")
os.chdir("/opt/aishield")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("/opt/aishield/gen14.log", mode="w"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

ORDER_ID = "3054d701-df1e-476e-b179-1616ca9cbc1f"

async def main():
    logger.info("GEN14 START — 13 dokumentů s Gemini→Claude fallback")
    logger.info("Order ID: %s", ORDER_ID)

    from backend.documents.pipeline_v3 import generate_compliance_kit

    t0 = time.time()
    result = await generate_compliance_kit(input_id=ORDER_ID)

    elapsed = time.time() - t0
    logger.info("GEN14 HOTOVO za %.0f sekund (%.1f min)", elapsed, elapsed/60)
    logger.info("Dokumentů: %d", len(result.documents))
    total_cost = sum(d.get("cost_usd", 0) for d in (result.pipeline_log or []) if isinstance(d, dict))
    logger.info("Celkové náklady: \$%.4f", total_cost)

    out_path = "/opt/aishield/gen14_result.json"
    with open(out_path, "w") as f:
        json.dump(result.model_dump(), f, indent=2, ensure_ascii=False, default=str)
    logger.info("Výsledek uložen: %s", out_path)

if __name__ == "__main__":
    asyncio.run(main())
