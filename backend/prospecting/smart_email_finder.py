"""
AIshield.cz — Smart Email Finder
Pokročilý email finder využívající Playwright pro rendering
a Claude Vision pro čtení kontaktních stránek.

Strategie:
1. Rychlý regex scan (httpx) — levný, rychlý
2. Playwright render kontaktní stránky — zachytí JS-rendered emaily
3. Claude Vision fallback — přečte email ze screenshotu /kontakt stránky
   (pro případy kdy je email v obrázku / JS obfuskaci)
"""

import httpx
import asyncio
import re
import base64
from dataclasses import dataclass
from typing import Optional

from playwright.async_api import async_playwright


@dataclass
class EmailFinderResult:
    """Výsledek hledání emailu."""
    email: Optional[str] = None
    source: str = ""           # "regex", "playwright", "vision", "meta"
    confidence: float = 0.0    # 0-1
    contact_page_url: str = ""
    all_emails_found: list[str] = None

    def __post_init__(self):
        if self.all_emails_found is None:
            self.all_emails_found = []


# ── Regex a filtry ──

EMAIL_REGEX = re.compile(
    r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
    re.IGNORECASE,
)

# Freemail domény — nechceme (nejsou firemní)
FREEMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "seznam.cz", "email.cz", "post.cz", "centrum.cz",
    "volny.cz", "atlas.cz", "quick.cz", "tiscali.cz",
    "icloud.com", "me.com", "live.com", "aol.com",
    "protonmail.com", "zoho.com", "mail.com",
}

# Emaily, které nechceme (generické, nefunkční)
EMAIL_BLACKLIST_PATTERNS = {
    "woocommerce", "wordpress", "example", "test",
    "noreply", "no-reply", "mailer-daemon", "postmaster",
    "unsubscribe", "donotreply",
}

# Preferované prefixy — řazení od nejlepšího
EMAIL_PRIORITY = [
    "info@", "kontakt@", "obchod@", "office@",
    "prodej@", "eshop@", "shop@", "objednavky@",
    "podpora@", "support@", "helpdesk@",
]

# Stránky kde hledat email
CONTACT_PATHS = [
    "/kontakt",
    "/kontakty",
    "/contact",
    "/contacts",
    "/o-nas",
    "/about",
    "/about-us",
    "/impressum",
    "/podpora",
    "/napiste-nam",
]


def score_email(email: str, website_domain: str = "") -> float:
    """
    Ohodnotí kvalitu emailu 0-1.
    Firemní email na vlastní doméně > info@ > ostatní.
    """
    email_lower = email.lower()
    domain = email_lower.split("@")[1] if "@" in email_lower else ""
    prefix = email_lower.split("@")[0] if "@" in email_lower else ""

    # Blacklist
    for pattern in EMAIL_BLACKLIST_PATTERNS:
        if pattern in email_lower:
            return 0.0

    # Freemail = nízké skóre
    if domain in FREEMAIL_DOMAINS:
        return 0.2

    score = 0.5  # Základ

    # Bonus: email na doméně webu
    if website_domain and domain in website_domain.lower():
        score += 0.3

    # Bonus: preferovaný prefix
    for i, pref in enumerate(EMAIL_PRIORITY):
        if email_lower.startswith(pref):
            score += 0.2 - (i * 0.01)
            break

    # Penalizace: osobní jména (jan@, petr@)
    if re.match(r'^[a-z]{2,8}(\.[a-z]+)?@', email_lower):
        score -= 0.05

    return min(score, 1.0)


def pick_best_email(
    emails: list[str],
    website_domain: str = "",
) -> Optional[str]:
    """Vybere nejlepší email ze seznamu."""
    if not emails:
        return None

    scored = [(e, score_email(e, website_domain)) for e in emails]
    scored.sort(key=lambda x: x[1], reverse=True)

    # Vrať jen pokud skóre > 0
    if scored[0][1] > 0:
        return scored[0][0]
    return None


def extract_domain(url: str) -> str:
    """Extrahuje doménu z URL."""
    url = url.lower().rstrip("/")
    url = re.sub(r'^https?://', '', url)
    url = re.sub(r'^www\.', '', url)
    return url.split("/")[0]


# ── Metoda 1: Rychlý regex scan (httpx) ──

async def find_email_fast(url: str) -> EmailFinderResult:
    """
    Rychlý HTTP scan — stáhne /kontakt a hledá emaily regexem.
    Nečeká na JS render. Levné a rychlé.
    """
    result = EmailFinderResult()
    domain = extract_domain(url)
    all_emails: set[str] = set()

    pages_to_check = [url.rstrip("/")] + [
        f"{url.rstrip('/')}{path}" for path in CONTACT_PATHS
    ]

    async with httpx.AsyncClient(
        timeout=8.0,
        follow_redirects=True,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; AIshield/1.0)",
            "Accept": "text/html",
        },
    ) as client:
        for page_url in pages_to_check:
            try:
                response = await client.get(page_url)
                if response.status_code != 200:
                    continue

                html = response.text

                # Hledáme mailto: linky (nejspolehlivější)
                mailto_emails = re.findall(
                    r'mailto:([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})',
                    html,
                    re.IGNORECASE,
                )
                all_emails.update(e.lower() for e in mailto_emails)

                # Regex v textu
                text_emails = EMAIL_REGEX.findall(html)
                all_emails.update(e.lower() for e in text_emails)

                # Hledáme v meta tagem
                meta_email = re.search(
                    r'<meta[^>]*name=["\']author["\'][^>]*content=["\']([^"\']*@[^"\']*)["\']',
                    html,
                    re.IGNORECASE,
                )
                if meta_email:
                    all_emails.add(meta_email.group(1).lower())

                if all_emails:
                    result.contact_page_url = page_url
                    break  # Stačí první stránka s emaily

            except Exception:
                continue

    result.all_emails_found = list(all_emails)
    best = pick_best_email(list(all_emails), domain)
    if best:
        result.email = best
        result.source = "regex"
        result.confidence = score_email(best, domain)

    return result


# ── Metoda 2: Playwright render ──

async def find_email_playwright(url: str) -> EmailFinderResult:
    """
    Playwright renderuje /kontakt stránku a hledá email v DOM.
    Zachytí JS-rendered emaily, které regex na static HTML mine.
    """
    result = EmailFinderResult()
    domain = extract_domain(url)
    all_emails: set[str] = set()

    contact_urls = [
        f"{url.rstrip('/')}{path}" for path in CONTACT_PATHS[:4]
    ]

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 720},
                locale="cs-CZ",
            )

            page = await context.new_page()

            for contact_url in contact_urls:
                try:
                    response = await page.goto(
                        contact_url,
                        wait_until="networkidle",
                        timeout=15000,
                    )
                    if not response or response.status >= 400:
                        continue

                    # Klikni na cookies souhlas
                    for selector in [
                        "text=Přijmout",
                        "text=Souhlasím",
                        "text=Accept",
                        "button:has-text('OK')",
                        "[class*='cookie'] button",
                    ]:
                        try:
                            btn = page.locator(selector).first
                            if await btn.is_visible(timeout=2000):
                                await btn.click()
                                await page.wait_for_timeout(500)
                                break
                        except Exception:
                            continue

                    # Počkej na plné načtení
                    await page.wait_for_timeout(2000)

                    # Extrahuj text celé stránky
                    body_text = await page.inner_text("body")

                    # Mailto linky z DOM
                    mailto_links = await page.eval_on_selector_all(
                        'a[href^="mailto:"]',
                        "els => els.map(e => e.href.replace('mailto:', ''))",
                    )
                    all_emails.update(e.lower() for e in mailto_links if "@" in e)

                    # Regex na rendered textu
                    text_emails = EMAIL_REGEX.findall(body_text)
                    all_emails.update(e.lower() for e in text_emails)

                    # Screenshot pro Vision fallback
                    if not all_emails:
                        screenshot = await page.screenshot(type="png")
                        result.contact_page_url = contact_url
                        # Uložíme screenshot pro případné Vision zpracování
                        result._screenshot = screenshot

                    if all_emails:
                        result.contact_page_url = contact_url
                        break

                except Exception:
                    continue

            await browser.close()

    except Exception as e:
        print(f"[EmailFinder] Playwright chyba pro {url}: {e}")

    result.all_emails_found = list(all_emails)
    best = pick_best_email(list(all_emails), domain)
    if best:
        result.email = best
        result.source = "playwright"
        result.confidence = score_email(best, domain)

    return result


# ── Metoda 3: Claude Vision ──

async def find_email_vision(screenshot: bytes, url: str) -> EmailFinderResult:
    """
    Pošle screenshot kontaktní stránky do LLM Vision (Claude → Gemini fallback).
    Přečte email i když je v obrázku nebo JS obfuskaci.
    """
    result = EmailFinderResult()
    domain = extract_domain(url)

    try:
        from backend.ai_engine.llm_client import llm_complete_vision

        b64_image = base64.b64encode(screenshot).decode("utf-8")

        llm_result = await llm_complete_vision(
            system="Jsi expert na extrakci kontaktních údajů z webových stránek.",
            user_text=(
                "Na tomto screenshotu je kontaktní stránka české firmy. "
                "Najdi všechny emailové adresy viditelné na stránce. "
                "Odpověz POUZE emailovými adresami, každou na novém řádku. "
                "Pokud žádný email nenajdeš, odpověz: NONE"
            ),
            image_b64=b64_image,
            media_type="image/png",
            max_tokens=200,
        )

        text = llm_result.text
        if text != "NONE":
            emails = EMAIL_REGEX.findall(text)
            result.all_emails_found = [e.lower() for e in emails]
            best = pick_best_email(result.all_emails_found, domain)
            if best:
                result.email = best
                result.source = f"vision/{llm_result.provider}"
                result.confidence = score_email(best, domain) * 0.9  # Mírná penalizace

    except Exception as e:
        print(f"[EmailFinder] Vision chyba pro {url}: {e}")

    return result


# ── Hlavní orchestrace ──

async def find_email_smart(
    url: str,
    use_playwright: bool = True,
    use_vision: bool = True,
) -> EmailFinderResult:
    """
    Kaskádové hledání emailu:
    1. Rychlý regex (httpx) — levný
    2. Playwright render — dražší, ale vídí JS
    3. Claude Vision — nejdražší, ale čte i obrázky

    Přestane hledat jakmile najde email s confidence >= 0.6
    """
    # Fáze 1: Rychlý scan
    result = await find_email_fast(url)
    if result.email and result.confidence >= 0.6:
        return result

    # Fáze 2: Playwright
    if use_playwright:
        pw_result = await find_email_playwright(url)
        if pw_result.email and pw_result.confidence > (result.confidence or 0):
            result = pw_result
        if result.email and result.confidence >= 0.6:
            return result

        # Fáze 3: Vision (pouze pokud Playwright udělal screenshot)
        if use_vision and hasattr(pw_result, "_screenshot") and pw_result._screenshot:
            vision_result = await find_email_vision(pw_result._screenshot, url)
            if vision_result.email and vision_result.confidence > (result.confidence or 0):
                result = vision_result

    return result


async def batch_find_emails(
    companies: list[dict],
    use_playwright: bool = True,
    use_vision: bool = False,  # Vision jen na vyžádání (náklady)
    concurrency: int = 3,
) -> dict[str, EmailFinderResult]:
    """
    Najde emaily pro batch firem.
    companies: [{"url": "...", "ico": "..."}]
    Vrací: {url: EmailFinderResult}
    """
    semaphore = asyncio.Semaphore(concurrency)
    results: dict[str, EmailFinderResult] = {}

    async def process(company: dict):
        url = company.get("url", "")
        if not url:
            return
        async with semaphore:
            result = await find_email_smart(
                url,
                use_playwright=use_playwright,
                use_vision=use_vision,
            )
            results[url] = result
            if result.email:
                print(f"  ✅ {url} → {result.email} ({result.source}, {result.confidence:.0%})")
            else:
                print(f"  ❌ {url} → email nenalezen")
            await asyncio.sleep(0.5)

    await asyncio.gather(*[process(c) for c in companies])

    found = sum(1 for r in results.values() if r.email)
    print(f"[EmailFinder] {found}/{len(companies)} firem s nalezeným emailem")
    return results
