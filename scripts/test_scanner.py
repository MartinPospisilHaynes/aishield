"""Test scanner + detektor na alza.cz"""
import asyncio
from backend.scanner.web_scanner import scan_url
from backend.scanner.detector import detect_ai_systems


async def test():
    print("=== Skenuji alza.cz ===")
    page = await scan_url("https://www.alza.cz")
    print(f"Stranka: {page.title}")
    print(f"Scripts: {len(page.scripts)}, Network: {len(page.network_requests)}")
    print()

    findings = detect_ai_systems(page)
    print(f"=== NALEZENO {len(findings)} AI SYSTEMU ===")
    print()

    for i, f in enumerate(findings, 1):
        print(f"{i}. {f.name} [{f.category}]")
        print(f"   Riziko: {f.risk_level} | AI Act: {f.ai_act_article}")
        print(f"   Confidence: {f.confidence}")
        print(f"   Matched: {len(f.matched_signatures)} signatur")
        for m in f.matched_signatures[:5]:
            print(f"     - {m}")
        print(f"   Evidence ({len(f.evidence)}):")
        for e in f.evidence[:3]:
            print(f"     > {e[:120]}")
        print(f"   Akce: {f.action_required[:100]}")
        print()


asyncio.run(test())
