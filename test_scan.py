import asyncio
import logging
import json

logging.basicConfig(level=logging.INFO)

from backend.scanner.web_scanner import WebScanner
from backend.scanner.detector import AIDetector
from backend.scanner.network_interceptor import NetworkInterceptor

async def test():
    url = "https://www.alza.cz"
    print(f"\n=== SCANNING {url} ===")
    
    scanner = WebScanner(timeout_ms=30000, wait_after_load_ms=3000)
    page = await scanner.scan(url)
    
    if page.error:
        print(f"ERROR: {page.error}")
        return
    
    print(f"Status: {page.status_code}")
    print(f"Title: {page.title}")
    print(f"HTML: {len(page.html)} bytes")
    print(f"Network requests: {len(page.network_requests)}")
    print(f"Network data (enriched): {len(page.network_data)}")
    
    # Enriched data sample
    print(f"\n--- ENRICHED NETWORK DATA (sample) ---")
    for nd in page.network_data[:5]:
        m = nd["method"]
        rt = nd["resource_type"]
        u = nd["url"][:80]
        s = nd["status"]
        print(f"  {m} {rt} {u}  status={s}")
    
    # AI-related requests
    ai_domains = ["openai", "anthropic", "googleapis.com/ai", "gemini", "tidio", "intercom", "drift"]
    ai_related = [nd for nd in page.network_data if any(d in nd["url"].lower() for d in ai_domains)]
    if ai_related:
        print(f"\n--- AI-RELATED NETWORK REQUESTS ---")
        for nd in ai_related:
            m = nd["method"]
            u = nd["url"][:120]
            s = nd["status"]
            print(f"  {m} {u}  status={s}")
            hdrs = nd["headers"]
            if hdrs:
                print(f"    Headers: {json.dumps(hdrs)[:200]}")
    
    # Run detector
    detector = AIDetector()
    findings = detector.detect(page)
    
    print(f"\n=== FINDINGS: {len(findings)} ===")
    for f in findings:
        sigs = str(f.matched_signatures)
        source = "NETWORK" if "network_intercept" in sigs else "SIGNATURE/HEURISTIC"
        print(f"  [{source}] {f.name} | {f.category} | conf={f.confidence} | risk={f.risk_level}")
        for e in f.evidence[:2]:
            print(f"    Evidence: {e[:120]}")

asyncio.run(test())
