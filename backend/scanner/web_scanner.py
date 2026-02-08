"""
AIshield.cz — Web Scanner (Playwright)
Hlavní modul pro skenování webových stránek.

Otevře URL v headless Chromium, načte stránku,
extrahuje HTML, skripty a metadata.
"""

import asyncio
import hashlib
import os
import base64
from dataclasses import dataclass, field
from datetime import datetime, timezone
from playwright.async_api import async_playwright, Page, Browser


@dataclass
class ScannedPage:
    """Výsledek skenování jedné stránky."""
    url: str
    final_url: str = ""                    # Po redirectech
    status_code: int = 0
    title: str = ""
    html: str = ""
    html_hash: str = ""                    # SHA256
    scripts: list[str] = field(default_factory=list)        # Src atributy <script>
    inline_scripts: list[str] = field(default_factory=list) # Obsah inline <script>
    iframes: list[str] = field(default_factory=list)        # Src atributy <iframe>
    meta_tags: dict[str, str] = field(default_factory=dict) # name -> content
    cookies: list[dict] = field(default_factory=list)
    console_messages: list[str] = field(default_factory=list)
    network_requests: list[str] = field(default_factory=list)  # URL požadavků
    screenshot_full: bytes = field(default=b"", repr=False)    # Celostránkový PNG
    screenshot_viewport: bytes = field(default=b"", repr=False) # Viewport PNG
    duration_ms: int = 0
    error: str | None = None
    scanned_at: str = ""


class WebScanner:
    """
    Playwright-based web scanner.
    Otevře stránku v headless Chromium a extrahuje vše potřebné
    pro detekci AI systémů.
    """

    def __init__(
        self,
        timeout_ms: int = 45_000,
        wait_after_load_ms: int = 5_000,
        user_agent: str | None = None,
    ):
        self.timeout_ms = timeout_ms
        self.wait_after_load_ms = wait_after_load_ms
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

    async def scan(self, url: str) -> ScannedPage:
        """
        Proskenuje URL a vrátí ScannedPage s veškerými daty.
        """
        result = ScannedPage(url=url)
        start = datetime.now(timezone.utc)
        result.scanned_at = start.isoformat()

        network_urls: list[str] = []
        console_msgs: list[str] = []

        async with async_playwright() as pw:
            browser: Browser = await pw.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ],
            )

            context = await browser.new_context(
                user_agent=self.user_agent,
                viewport={"width": 1920, "height": 1080},
                locale="cs-CZ",
                timezone_id="Europe/Prague",
                ignore_https_errors=True,
            )

            page: Page = await context.new_page()

            # Sbíráme network requesty
            page.on("request", lambda req: network_urls.append(req.url))

            # Sbíráme console messages
            page.on("console", lambda msg: console_msgs.append(
                f"[{msg.type}] {msg.text}"
            ))

            try:
                # Navigace na URL — používáme domcontentloaded + manuální čekání
                # (networkidle nefunguje na webech s WebSocket/long-polling)
                response = await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=self.timeout_ms,
                )

                if response:
                    result.status_code = response.status
                    result.final_url = page.url

                # Počkáme na networkidle manuálně (max 10s, ne-fatální)
                try:
                    await page.wait_for_load_state("networkidle", timeout=10_000)
                except Exception:
                    pass  # Nevadí, některé weby nikdy nedosáhnou networkidle

                # Počkáme na dynamický obsah (chatboty, popupy...)
                await page.wait_for_timeout(self.wait_after_load_ms)

                # ── Extrakce dat ──

                # Titulek
                result.title = await page.title()

                # Celé HTML
                result.html = await page.content()
                result.html_hash = hashlib.sha256(
                    result.html.encode("utf-8")
                ).hexdigest()

                # Externí skripty
                result.scripts = await page.eval_on_selector_all(
                    "script[src]",
                    "els => els.map(e => e.src)"
                )

                # Inline skripty
                result.inline_scripts = await page.eval_on_selector_all(
                    "script:not([src])",
                    "els => els.map(e => e.textContent || '').filter(t => t.trim().length > 0)"
                )

                # Iframes
                result.iframes = await page.eval_on_selector_all(
                    "iframe[src]",
                    "els => els.map(e => e.src)"
                )

                # Meta tagy
                result.meta_tags = await page.evaluate("""
                    () => {
                        const metas = {};
                        document.querySelectorAll('meta[name], meta[property]').forEach(m => {
                            const key = m.getAttribute('name') || m.getAttribute('property');
                            const val = m.getAttribute('content') || '';
                            if (key) metas[key] = val;
                        });
                        return metas;
                    }
                """)

                # Cookies
                cookies_raw = await context.cookies()
                result.cookies = [
                    {"name": c["name"], "domain": c["domain"], "value": c["value"][:50]}
                    for c in cookies_raw
                ]

                # ── Screenshoty ──

                # Viewport screenshot (co vidí uživatel)
                result.screenshot_viewport = await page.screenshot(
                    type="png",
                    full_page=False,
                )

                # Full-page screenshot (celá stránka)
                try:
                    result.screenshot_full = await page.screenshot(
                        type="png",
                        full_page=True,
                        timeout=10_000,
                    )
                except Exception:
                    # Některé stránky jsou příliš dlouhé
                    result.screenshot_full = result.screenshot_viewport

            except Exception as e:
                result.error = str(e)

            finally:
                result.network_requests = network_urls
                result.console_messages = console_msgs

                end = datetime.now(timezone.utc)
                result.duration_ms = int((end - start).total_seconds() * 1000)

                await browser.close()

        return result


async def scan_url(url: str) -> ScannedPage:
    """Convenience funkce — proskenuje URL a vrátí výsledek."""
    scanner = WebScanner()
    return await scanner.scan(url)
