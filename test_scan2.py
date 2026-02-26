import asyncio
import logging

logging.basicConfig(level=logging.INFO)

from backend.scanner.web_scanner import WebScanner
from backend.scanner.detector import AIDetector

async def test():
    # Test web s Tidio chatbotem
    url = "https://www.smartsupp.com"
    print(f"\n=== SCANNING {url} ===")
    
    scanner = WebScanner(timeout_ms=30000, wait_after_load_ms=5000)
    page = await scanner.scan(url)
    
    if page.error:
        print(f"ERROR: {page.error}")
        return
    
    print(f"Status: {page.status_code}")
    print(f"Network requests: {len(page.network_requests)}")
    print(f"Network data (enriched): {len(page.network_data)}")
    
    # Show AI-related network requests
    ai_keywords = ["openai", "anthropic", "gemini", "tidio", "intercom", "drift", 
                    "smartsupp", "dialogflow", "mistral", "cohere", "groq"]
    for nd in page.network_data:
        url_lower = nd["url"].lower()
        if any(k in url_lower for k in ai_keywords):
            m = nd["method"]
            u = nd["url"][:120]
            s = nd["status"]
            rt = nd["resource_type"]
            print(f"  AI-RELATED: {m} [{rt}] {u}  status={s}")
    
    # Run detector
    detector = AIDetector()
    findings = detector.detect(page)
    
    print(f"\n=== FINDINGS: {len(findings)} ===")
    for f in findings:
        sigs = str(f.matched_signatures)
        if "network_intercept" in sigs:
            source = ">>> NETWORK <<<"
        elif "network_heuristic" in sigs:
            source = "NETWORK-HEURISTIC"
        else:
            source = "SIGNATURE/HEURISTIC"
        print(f"  [{source}] {f.name} | conf={f.confidence} | risk={f.risk_level}")
        for e in f.evidence[:2]:
            print(f"    Evidence: {e[:120]}")

asyncio.run(test())
