#!/usr/bin/env python3
"""
Trigger document generation (PDF + HTML + PPTX) using existing DB data.
No deep scan re-run — just generates fresh documents from current data.
"""
import asyncio
import logging
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("docgen")

async def main():
    company_id = "3900ae47-25d5-42fb-af4d-0d06623bc8cc"
    
    logger.info(f"=== DOCUMENT GENERATION START ===")
    logger.info(f"Company ID: {company_id}")
    
    start = time.time()
    
    from backend.documents.pipeline import generate_compliance_kit
    
    result = await generate_compliance_kit(company_id)
    
    elapsed = time.time() - start
    
    logger.info(f"\n{'='*60}")
    logger.info(f"=== RESULT ===")
    logger.info(f"  Company: {result.company_name}")
    logger.info(f"  Generated: {result.success_count} documents")
    logger.info(f"  Errors: {result.error_count}")
    logger.info(f"  Time: {elapsed:.1f}s")
    
    for doc in result.documents:
        logger.info(f"\n  --- {doc['template_name']} ---")
        logger.info(f"    Format: {doc['format']}")
        logger.info(f"    Size: {doc['size_bytes']:,} bytes")
        logger.info(f"    URL: {doc['download_url']}")
    
    if result.errors:
        logger.error(f"\n  === ERRORS ===")
        for e in result.errors:
            logger.error(f"    {e}")
    
    if result.skipped_documents:
        logger.info(f"\n  Skipped: {len(result.skipped_documents)} documents")
    
    logger.info(f"\n{'='*60}")
    logger.info(f"DONE in {elapsed:.1f}s")

asyncio.run(main())
