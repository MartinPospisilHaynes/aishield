"""
AIshield.cz — Web Scanner v5 (Playwright)
Hlavní modul pro skenování webových stránek.

v5: Enhanced interactions (full scroll, hover, subpage nav),
    user-agent rotation, Bright Data proxy support.
v4: Enriched network capture — zachytává nejen URL, ale i metodu,
    resource_type a response hlavičky pro Network Interceptor.
"""

import asyncio
import hashlib
import logging
import os
import random
import base64
from dataclasses import dataclass, field
from datetime import datetime, timezone
from playwright.async_api import async_playwright, Page, Browser

logger = logging.getLogger(__name__)


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
    Playwright-based web scanner v5.
    Otevře stránku v headless Chromium a extrahuje vše potřebné
    pro detekci AI systémů.

    v5: Full scroll, hover, subpage nav, UA rotation, Bright Data proxy.
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

    # User-agent pool — rotace desktop + mobile
    UA_DESKTOP = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    ]
    UA_MOBILE = [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    ]

    # Geolokace — 7 zemí, 1 na každý kontinent
    GEO_COUNTRIES = ["cz", "gb", "us", "br", "jp", "za", "au"]

    def __init__(
        self,
        timeout_ms: int = 45_000,
        wait_after_load_ms: int = 5_000,
        user_agent: str | None = None,
        device_type: str = "desktop",  # "desktop" | "mobile" | "random"
        proxy_country: str | None = None,  # ISO country code ("us", "de", ...) or None for random
        use_proxy: bool = False,  # True = use Bright Data proxy
    ):
        self.timeout_ms = timeout_ms
        self.wait_after_load_ms = wait_after_load_ms
        self.device_type = device_type
        self.use_proxy = use_proxy
        self.proxy_country = proxy_country

        # Bright Data proxy credentials z env
        self._proxy_host = os.environ.get("BRIGHT_DATA_HOST", "brd.superproxy.io")
        self._proxy_port = os.environ.get("BRIGHT_DATA_PORT", "33335")
        self._proxy_user = os.environ.get("BRIGHT_DATA_USER", "")
        self._proxy_pass = os.environ.get("BRIGHT_DATA_PASS", "")

        # Auto-enable proxy pokud jsou credentials v env
        if self._proxy_user and self._proxy_pass and not self.use_proxy:
            # Jen logujeme, neaktivujeme automaticky — musí se zapnout explicitně
            pass

        # User-agent
        if user_agent:
            self.user_agent = user_agent
        elif device_type == "mobile":
            self.user_agent = random.choice(self.UA_MOBILE)
        elif device_type == "random":
            pool = self.UA_DESKTOP + self.UA_MOBILE
            self.user_agent = random.choice(pool)
            self.device_type = "mobile" if self.user_agent in self.UA_MOBILE else "desktop"
        else:
            self.user_agent = random.choice(self.UA_DESKTOP)

        # Viewport dle device type
        if self.device_type == "mobile":
            self.viewport = {"width": 390, "height": 844}
        else:
            self.viewport = {"width": 1920, "height": 1080}

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
            # ── v5: Bright Data residential proxy OR local only ──
            launch_args = {
                "headless": True,
                "args": [
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ],
            }

            if self.use_proxy and self._proxy_user and self._proxy_pass:
                # Postavíme username s country targetingem
                proxy_username = self._proxy_user
                country = self.proxy_country or random.choice(self.GEO_COUNTRIES)
                proxy_username += f"-country-{country}"
                # Každý scan = nová IP (random session)
                session_id = hashlib.md5(f"{url}{datetime.now().isoformat()}".encode()).hexdigest()[:8]
                proxy_username += f"-session-{session_id}"

                proxy_server = f"http://{self._proxy_host}:{self._proxy_port}"
                launch_args["proxy"] = {
                    "server": proxy_server,
                    "username": proxy_username,
                    "password": self._proxy_pass,
                }
                logger.info(f"[Scanner] Using Bright Data proxy: country={country}, session={session_id}")
            else:
                if self.use_proxy:
                    logger.warning("[Scanner] Proxy requested but BRIGHT_DATA credentials not set — running without proxy")

            browser: Browser = await pw.chromium.launch(**launch_args)

            context = await browser.new_context(
                user_agent=self.user_agent,
                viewport=self.viewport,
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

                # ── v5: Full scroll — postupný scroll dolů po viewport krocích ──
                try:
                    total_height = await page.evaluate("document.body.scrollHeight")
                    viewport_h = self.viewport["height"]
                    position = 0
                    while position < total_height:
                        position += viewport_h
                        await page.evaluate(f"window.scrollTo(0, {position})")
                        await page.wait_for_timeout(400)
                        # Stránka může dorůst (lazy loading)
                        total_height = await page.evaluate("document.body.scrollHeight")
                        # Bezpečnostní limit — max 20 scrollů
                        if position > viewport_h * 20:
                            break
                    # Počkáme na dynamický obsah spuštěný scrollem
                    await page.wait_for_timeout(2000)
                except Exception:
                    pass  # Scroll is best-effort

                # ── v5: Hover nad typickými chatbot triggery ──
                try:
                    hover_selectors = [
                        '[class*="chat"]', '[class*="Chat"]',
                        '[id*="chat"]', '[id*="Chat"]',
                        '[class*="widget"]', '[class*="Widget"]',
                        '[class*="support"]', '[class*="help"]',
                        '[class*="messenger"]', '[class*="intercom"]',
                        '[class*="tidio"]', '[class*="drift"]',
                        '[class*="crisp"]', '[class*="smartsupp"]',
                        'button[aria-label*="chat" i]',
                        'button[aria-label*="help" i]',
                        'button[aria-label*="support" i]',
                        'div[class*="fab"]',  # floating action button
                        'iframe[src*="chat"]',
                    ]
                    hovered = 0
                    for sel in hover_selectors:
                        try:
                            loc = page.locator(sel).first
                            if await loc.is_visible(timeout=300):
                                await loc.hover(timeout=1000)
                                hovered += 1
                                await page.wait_for_timeout(500)
                                if hovered >= 3:
                                    break
                        except Exception:
                            continue
                    if hovered > 0:
                        await page.wait_for_timeout(2000)
                except Exception:
                    pass  # Hover is best-effort

                # ── v5: Klik na kontaktní/support stránky (objeví chatboty) ──
                try:
                    contact_selectors = [
                        'a:has-text("Kontakt")',
                        'a:has-text("kontakt")',
                        'a:has-text("Contact")',
                        'a:has-text("Podpora")',
                        'a:has-text("Support")',
                        'a:has-text("Napište nám")',
                        'a:has-text("Pomoc")',
                        'a:has-text("Help")',
                    ]
                    for sel in contact_selectors:
                        try:
                            link = page.locator(sel).first
                            if await link.is_visible(timeout=300):
                                href = await link.get_attribute("href")
                                # Jen interní linky (ne mailto:, tel:, external)
                                if href and not href.startswith(("mailto:", "tel:", "http://", "https://")):
                                    await link.click(timeout=3000)
                                    await page.wait_for_timeout(3000)
                                    break
                                elif href and href.startswith(("http://", "https://")) and (page.url.split("/")[2] in href):
                                    await link.click(timeout=3000)
                                    await page.wait_for_timeout(3000)
                                    break
                        except Exception:
                            continue
                except Exception:
                    pass  # Contact navigation is best-effort

                # Scroll zpátky na top pro extrakci
                try:
                    await page.evaluate("window.scrollTo(0, 0)")
                    await page.wait_for_timeout(500)
                except Exception:
                    pass

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


async def scan_url(
    url: str,
    device_type: str = "desktop",
    use_proxy: bool = False,
    proxy_country: str | None = None,
) -> ScannedPage:
    """Convenience funkce — proskenuje URL a vrátí výsledek."""
    scanner = WebScanner(
        device_type=device_type,
        use_proxy=use_proxy,
        proxy_country=proxy_country,
    )
    return await scanner.scan(url)
