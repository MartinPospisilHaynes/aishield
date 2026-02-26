"""
GEN15 — Compliance Kit: 13 dokumentů přes Vertex AI (gemini-3.1-pro-preview)
PID lock ochrana proti duplicitnímu spuštění.
"""
import asyncio
import json
import logging
import sys
import os
import time
import fcntl

sys.path.insert(0, "/opt/aishield")
os.chdir("/opt/aishield")

# ── PID lock — zamezí duplicitnímu spuštění ──
LOCK_FILE = "/tmp/gen15.lock"

def acquire_lock():
    """Získá exclusive lock. Pokud běží jiný gen15, okamžitě skončí."""
    lock_fd = open(LOCK_FILE, "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_fd.write(str(os.getpid()))
        lock_fd.flush()
        return lock_fd
    except BlockingIOError:
        print("CHYBA: gen15 už běží (PID lock). Ukončuji.")
        sys.exit(1)

lock_fd = acquire_lock()

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("/opt/aishield/gen15.log", mode="w"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ── Zajisti GOOGLE_APPLICATION_CREDENTIALS ──
os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", "/opt/aishield/vertex-sa-key.json")

ORDER_ID = "3054d701-df1e-476e-b179-1616ca9cbc1f"


async def main():
    logger.info("=" * 70)
    logger.info("GEN15 START — 13 dokumentu pres Vertex AI (gemini-3.1-pro-preview)")
    logger.info("=" * 70)
    logger.info("Order ID: %s", ORDER_ID)
    logger.info("PID: %d", os.getpid())
    logger.info("GOOGLE_APPLICATION_CREDENTIALS: %s", os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "NOT SET"))

    from backend.documents.pipeline_v3 import generate_compliance_kit

    t0 = time.time()

    try:
        result = await generate_compliance_kit(input_id=ORDER_ID)
    except Exception as e:
        elapsed = time.time() - t0
        logger.error("GEN15 SELHAL po %.0f sekundach: %s", elapsed, e, exc_info=True)
        sys.exit(2)

    elapsed = time.time() - t0
    logger.info("=" * 70)
    logger.info("GEN15 HOTOVO za %.0f sekund (%.1f min)", elapsed, elapsed / 60)
    logger.info("=" * 70)
    logger.info("Dokumentu: %d", len(result.documents))

    # Spocitej celkove naklady
    total_cost = 0.0
    vertex_calls = 0
    claude_calls = 0
    for entry in (result.pipeline_log or []):
        if isinstance(entry, dict):
            total_cost += entry.get("cost_usd", 0)
            if entry.get("backend") == "vertex":
                vertex_calls += 1
            if entry.get("provider") == "claude":
                claude_calls += 1
    logger.info("Celkove naklady: $%.4f", total_cost)
    logger.info("Vertex AI volani: %d | Claude volani: %d", vertex_calls, claude_calls)

    # Uloz vysledek
    out_path = "/opt/aishield/gen15_result.json"
    with open(out_path, "w") as f:
        json.dump(result.model_dump(), f, indent=2, ensure_ascii=False, default=str)
    logger.info("Vysledek ulozen: %s", out_path)

    # Vypis info o kazdem dokumentu
    for doc_key, doc_info in result.documents.items():
        status = "OK" if doc_info.get("download_url") else "CHYBI PDF"
        logger.info("  [%s] %s — %s", status, doc_key, doc_info.get("filename", "???"))


if __name__ == "__main__":
    asyncio.run(main())
