"""Test screenshot engine na alza.cz"""
import asyncio
from backend.scanner.web_scanner import scan_url


async def test():
    print("=== Screenshot test: alza.cz ===")
    page = await scan_url("https://www.alza.cz")
    print(f"Status: {page.status_code}")
    print(f"Viewport screenshot: {len(page.screenshot_viewport)} bytes ({len(page.screenshot_viewport) / 1024:.0f} KB)")
    print(f"Full-page screenshot: {len(page.screenshot_full)} bytes ({len(page.screenshot_full) / 1024:.0f} KB)")
    print(f"Duration: {page.duration_ms}ms")

    # Uložíme pro vizuální kontrolu
    with open("/tmp/alza_viewport.png", "wb") as f:
        f.write(page.screenshot_viewport)
    with open("/tmp/alza_fullpage.png", "wb") as f:
        f.write(page.screenshot_full)

    print("Uloženo: /tmp/alza_viewport.png, /tmp/alza_fullpage.png")
    print("OK")


asyncio.run(test())
