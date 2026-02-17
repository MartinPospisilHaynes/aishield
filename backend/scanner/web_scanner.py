"""
AIshield.cz — Web Scanner v4 (Playwright)
Hlavní modul pro skenování webových stránek.

v4: Enriched network capture — zachytává nejen URL, ale i metodu,
    resource_type a response hlavičky pro Network Interceptor.
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
    network_requests: list[str] = field(default_factory=list)  # URL požadavků (zpětná kompatibilita)
    network_data: list[dict] = field(default_factory=list)     # v4: Enriched [{url, method, resource_type, status, headers}]
    duration_ms: int = 0
    error: str | None = None
    scanned_at: str = ""


class WebScanner:
    """
    Playwright-based web scanner v4.
    Otevře stránku v headless Chromium a extrahuje vše potřebné
    pro detekci AI systémů.

    v4: Enriched network capture pro Network Interceptor.
    """

    # AI-related domény — pro tyto zachytíme i response headers
    AI_DOMAINS = {
        "openai.com", "anthropic.com", "googleapis.com",
        "mistral.ai", "cohere.ai", "cohere.com", "huggingface.co",
        "replicate.com", "together.xyz", "perplexity.ai",
        "groq.com", "elevenlabs.io", "stability.ai",
        "fireworks.ai", "cerebras.ai", "deepl.com",
        "azure.com", "amazonaws.com", "tidio.co",
        "intercom.io", "drift.com", "x.ai", "deepseek.com",
    }

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
        network_enriched: list[dict] = []
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

            # ── v4: Enriched request capture ──
            def on_request(req):
                network_urls.append(req.url)
                network_enriched.append({
                    "url": req.url,
                    "method": req.method,
                    "resource_type": req.resource_type,
                    "status": None,
                    "headers": {},
                })

            page.on("request", on_request)

            # ── v4: Response capture — zachytíme status + AI headers ──
            def on_response(resp):
                resp_url = resp.url
                # Najdeme odpovídající request v enriched datech
                for nd in reversed(network_enriched):
                    if nd["url"] == resp_url and nd["status"] is None:
                        nd["status"] = resp.status
                        # Zachytíme hlavičky pro AI-related domény
                        try:
                            resp_url_lower = resp_url.lower()
                            is_ai_domain = any(
                                d in resp_url_lower for d in self.AI_DOMAINS
                            )
                            if is_ai_domain:
                                # Async headers — uložíme co máme sync
                                nd["headers"] = dict(resp.headers)
                        except Exception:
                            pass
                        break

            page.on("response", on_response)

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

                # ── Cookie consent auto-close ──
                try:
                    consent_selectors = [
                        'button:has-text("Přijmout vše")',
                        'button:has-text("Přijmout všechny")',
                        'button:has-text("Souhlasím")',
                        'button:has-text("Accept all")',
                        'button:has-text("Accept cookies")',
                        'button:has-text("Akceptovat")',
                        'button:has-text("Povolit vše")',
                        'a:has-text("Přijmout vše")',
                        'a:has-text("Souhlasím")',
                        'a:has-text("Accept all")',
                        'button[id*="accept"]',
                        '[id*="cookie-accept"]',
                        '[id*="consent-accept"]',
                        '[class*="cookie"] button:first-of-type',
                    ]
                    for selector in consent_selectors:
                        try:
                            btn = page.locator(selector).first
                            if await btn.is_visible(timeout=500):
                                await btn.click(timeout=2000)
                                await page.wait_for_timeout(1000)
                                break
                        except Exception:
                            continue
                except Exception:
                    pass  # Cookie consent handling is best-effort

                # ── Scroll to 50% for lazy-loaded content ──
                try:
                    total_height = await page.evaluate(
                        "document.body.scrollHeight"
                    )
                    await page.evaluate(
                        f"window.scrollTo(0, {total_height // 2})"
                    )
                    await page.wait_for_timeout(3000)
                    # Scroll back to top for screenshots
                    await page.evaluate("window.scrollTo(0, 0)")
                    await page.wait_for_timeout(1000)
                except Exception:
                    pass  # Scroll is best-effort

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

            except Exception as e:
                result.error = str(e)

            finally:
                result.network_requests = network_urls
                result.network_data = network_enriched
                result.console_messages = console_msgs

                end = datetime.now(timezone.utc)
                result.duration_ms = int((end - start).total_seconds() * 1000)

                await browser.close()

        return result


async def scan_url(url: str) -> ScannedPage:
    """Convenience funkce — proskenuje URL a vrátí výsledek."""
    scanner = WebScanner()
    return await scanner.scan(url)
