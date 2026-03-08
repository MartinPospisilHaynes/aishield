#!/usr/bin/env python3
"""
AIshield Auto-Blog Generator
=============================
Runs daily via cron. Generates a new SEO-optimized blog article about AI Act,
creates a Next.js page, generates an OG image via Gemini, updates the manifest,
rebuilds, commits and pushes to trigger Vercel deploy.

Usage:
    python3 /opt/aishield/auto_blog/auto_blog.py

Env vars (in /opt/aishield/auto_blog/.env):
    GEMINI_API_KEY=AIza...       (text generation)
    IMAGE_API_KEY=AIza...        (NanoBanana / Imagen for images)
"""

import os
import sys
import json
import re
import time
import hashlib
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from urllib.error import URLError
import base64

# ── Config ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = Path("/opt/aishield/frontend")
BLOG_DIR = FRONTEND_DIR / "src" / "app" / "blog"
PUBLIC_DIR = FRONTEND_DIR / "public" / "blog"
MANIFEST_PATH = FRONTEND_DIR / "src" / "data" / "blog-manifest.json"
TOPICS_PATH = SCRIPT_DIR / "topics.json"
USED_PATH = SCRIPT_DIR / "used_topics.json"
LOG_PATH = SCRIPT_DIR / "auto_blog.log"

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_IMAGE_MODEL = "gemini-2.5-flash"  # fallback, primary uses Imagen 4.0
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

SITE_URL = "https://aishield.cz"

# ── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("auto_blog")

# ── Load env ────────────────────────────────────────────────────────────────
def load_env():
    env_path = SCRIPT_DIR / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

load_env()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
IMAGE_API_KEY = os.environ.get("IMAGE_API_KEY", GEMINI_API_KEY)  # fallback to Gemini key
if not GEMINI_API_KEY:
    log.error("GEMINI_API_KEY not set!")
    sys.exit(1)


# ── Gemini API ──────────────────────────────────────────────────────────────
def gemini_generate(prompt: str, model: str = GEMINI_MODEL, max_tokens: int = 8192) -> str:
    """Call Gemini API and return text response."""
    url = f"{GEMINI_API_BASE}/models/{model}:generateContent?key={GEMINI_API_KEY}"
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": 0.85,
        },
    }).encode()

    req = Request(url, data=payload, headers={"Content-Type": "application/json"})

    for attempt in range(3):
        try:
            with urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return text.strip()
        except Exception as e:
            log.warning(f"Gemini attempt {attempt+1} failed: {e}")
            time.sleep(5 * (attempt + 1))

    raise RuntimeError("Gemini API failed after 3 attempts")


def gemini_generate_image(prompt: str) -> bytes | None:
    """Try to generate an image via Imagen API (NanoBanana key). Returns PNG bytes or None."""
    url = f"{GEMINI_API_BASE}/models/imagen-4.0-generate-001:predict?key={IMAGE_API_KEY}"
    payload = json.dumps({
        "instances": [{"prompt": prompt}],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "16:9",
            "safetyFilterLevel": "block_few",
        },
    }).encode()

    req = Request(url, data=payload, headers={"Content-Type": "application/json"})

    try:
        with urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        b64 = data["predictions"][0]["bytesBase64Encoded"]
        return base64.b64decode(b64)
    except Exception as e:
        log.warning(f"Image generation failed: {e}")
        return None


# ── Topic Engine ────────────────────────────────────────────────────────────
def load_topics() -> list[dict]:
    if TOPICS_PATH.exists():
        return json.loads(TOPICS_PATH.read_text(encoding="utf-8"))
    return []


def load_used() -> list[str]:
    if USED_PATH.exists():
        return json.loads(USED_PATH.read_text(encoding="utf-8"))
    return []


def save_used(used: list[str]):
    USED_PATH.write_text(json.dumps(used, ensure_ascii=False, indent=2), encoding="utf-8")


def pick_topic() -> dict:
    """Pick next unused topic. If all used, reset cycle."""
    topics = load_topics()
    used = load_used()

    available = [t for t in topics if t["slug"] not in used]
    if not available:
        log.info("All topics used, resetting cycle")
        used = []
        available = topics

    topic = available[0]
    used.append(topic["slug"])
    save_used(used)
    return topic


# ── Slug helper ─────────────────────────────────────────────────────────────
def to_slug(text: str) -> str:
    """Czech-friendly slug generator."""
    tr = str.maketrans(
        "áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ",
        "acdeeinorstuuyzACDEEINORSTUUYZ",
    )
    s = text.translate(tr).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:80]


# ── Article Generator ───────────────────────────────────────────────────────
def generate_article(topic: dict) -> dict:
    """Generate a full blog article using Gemini."""
    today = datetime.now()
    date_str = today.strftime("%-d. %B %Y").replace(
        "January", "ledna"
    ).replace("February", "února").replace("March", "března").replace(
        "April", "dubna"
    ).replace("May", "května").replace("June", "června").replace(
        "July", "července"
    ).replace("August", "srpna").replace("September", "září").replace(
        "October", "října"
    ).replace("November", "listopadu").replace("December", "prosince")

    prompt = f"""Jsi odborný copywriter specializovaný na EU AI Act (Nařízení EU 2024/1689).
    
Napiš blog článek pro web AIshield.cz na téma: "{topic['title']}"

Kontext: {topic.get('context', '')}

POŽADAVKY:
- Jazyk: čeština, profesionální ale srozumitelný tón
- Délka: 800-1200 slov (ne méně!)
- Struktura: 4-6 sekcí s H2 nadpisy
- Každá sekce: min 2-3 odstavce
- SEO: přirozeně zakomponuj klíčová slova: {topic.get('keywords', 'AI Act, compliance, české firmy')}
- Na konci: CTA odkazující na sken webu (aishield.cz/scan)
- Uveď konkrétní články AI Actu kde je to relevantní (čl. 4, čl. 5, čl. 50 atd.)
- Piš jako expert, ale pro čtenáře který AI Act nezná
- NEPOUŽÍVEJ Unicode escape sekvence — piš přímo česky s diakritikou
- Nepoužívej markdown formátování jako # nebo ** — výstup je čistý text

Odpověz PŘESNĚ v tomto JSON formátu (a nic jiného!):
{{
    "meta_title": "SEO titulek stránky (max 60 znaků) | AIshield.cz",
    "meta_description": "Meta description (max 155 znaků) — lákavý, s klíčovými slovy",
    "h1_title": "Hlavní nadpis článku (část 1 — neutrální)",
    "h1_accent": "Hlavní nadpis článku (část 2 — zvýrazněná)",
    "subtitle": "{date_str} • X min čtení",
    "tag": "jedno slovo kategorie (Průvodce/Návod/Analýza/Novinka/Checklist/Přehled)",
    "excerpt": "Krátký popis pro náhled (1-2 věty, max 120 znaků)",
    "sections": [
        {{
            "heading": "H2 nadpis sekce",
            "paragraphs": ["odstavec 1", "odstavec 2", "odstavec 3"]
        }}
    ],
    "internal_links": [
        {{"text": "text odkazu", "href": "/ai-act/pokuty"}}
    ]
}}

Interní odkazy vyber z těchto existujících stránek:
/ai-act, /ai-act/co-je-ai-act, /ai-act/rizikove-kategorie, /ai-act/clanek-50, 
/ai-act/pokuty, /ai-act/e-shopy, /ai-act/checklist, /integrace, /integrace/smartsupp, 
/integrace/google-analytics, /integrace/shoptet, /integrace/openai-chatgpt, 
/integrace/meta-pixel, /srovnani, /metodika, /report, /faq, /scan, /pricing
"""

    raw = gemini_generate(prompt, max_tokens=8192)

    # Extract JSON from response (handle ```json ... ``` wrapper)
    json_match = re.search(r"\{[\s\S]*\}", raw)
    if not json_match:
        raise ValueError(f"No JSON found in Gemini response:\n{raw[:500]}")

    json_str = json_match.group()
    # Fix common Gemini JSON issues
    json_str = re.sub(r",\s*}", "}", json_str)  # trailing commas before }
    json_str = re.sub(r",\s*]", "]", json_str)  # trailing commas before ]
    json_str = json_str.replace("\n", " ")  # literal newlines in strings

    try:
        article = json.loads(json_str)
    except json.JSONDecodeError as e:
        log.warning(f"JSON parse error: {e}, attempting repair...")
        # Try to fix unescaped quotes inside strings
        # First, try strict=False
        try:
            article = json.loads(json_str, strict=False)
        except json.JSONDecodeError:
            # Last resort: ask Gemini to fix its own JSON
            repair_prompt = f"Fix this broken JSON. Return ONLY valid JSON, nothing else:\n{json_str[:4000]}"
            repaired = gemini_generate(repair_prompt, max_tokens=8192)
            repair_match = re.search(r"\{[\s\S]*\}", repaired)
            if repair_match:
                repaired_str = repair_match.group()
                repaired_str = re.sub(r",\s*}", "}", repaired_str)
                repaired_str = re.sub(r",\s*]", "]", repaired_str)
                article = json.loads(repaired_str, strict=False)
            else:
                raise
    article["slug"] = topic["slug"]
    article["date"] = today.strftime("%Y-%m-%d")
    article["date_human"] = date_str
    article["topic_title"] = topic["title"]

    log.info(f"Generated article: {article['meta_title']}")
    return article


# ── TSX Page Builder ────────────────────────────────────────────────────────
def build_page_tsx(article: dict, has_image: bool = False) -> str:
    """Build a Next.js page.tsx file from article data."""
    slug = article["slug"]
    sections_jsx = []

    for sec in article["sections"]:
        paras = []
        for p in sec["paragraphs"]:
            # Escape JSX special chars
            p_escaped = p.replace("{", "&#123;").replace("}", "&#125;")
            paras.append(f'                <p>{p_escaped}</p>')

        section_block = f"""            <section>
                <h2 className="text-xl font-semibold text-white mb-3">{sec["heading"]}</h2>
{chr(10).join(paras)}
            </section>"""
        sections_jsx.append(section_block)

    # Internal links
    links_jsx = ""
    if article.get("internal_links"):
        link_items = []
        for lnk in article["internal_links"]:
            link_items.append(
                f'                    <li><Link href="{lnk["href"]}" '
                f'className="text-fuchsia-400 hover:text-fuchsia-300 transition-colors">'
                f'{lnk["text"]}</Link></li>'
            )
        links_jsx = f"""
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Související články</h2>
                <ul className="list-disc pl-6 space-y-2 text-slate-400">
{chr(10).join(link_items)}
                </ul>
            </section>"""

    # OG image import
    image_import = ""
    image_meta = ""
    if has_image:
        image_import = f'\nimport ogImage from "@/../../public/blog/{slug}.png";'
        image_meta = f"""
    openGraph: {{
        images: [{{ url: "/blog/{slug}.png", width: 1200, height: 630 }}],
    }},"""

    # BlogPosting JSON-LD schema
    blog_schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": f"{article['h1_title']} {article['h1_accent']}",
        "description": article["meta_description"],
        "datePublished": article["date"],
        "dateModified": article["date"],
        "author": {"@type": "Organization", "name": "AIshield.cz", "url": "https://aishield.cz"},
        "publisher": {"@type": "Organization", "name": "AIshield.cz", "logo": {"@type": "ImageObject", "url": "https://aishield.cz/icon.png"}},
        "mainEntityOfPage": {"@type": "WebPage", "@id": f"{SITE_URL}/blog/{slug}"},
        "inLanguage": "cs",
        "keywords": article.get("topic_title", "AI Act, compliance"),
        "image": f"{SITE_URL}/blog/{slug}.png" if has_image else f"{SITE_URL}/icon.png",
    }, ensure_ascii=False)

    tsx = f'''import type {{ Metadata }} from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {{
    title: "{article["meta_title"]}",
    description: "{article["meta_description"]}",
    alternates: {{ canonical: "{SITE_URL}/blog/{slug}" }},{image_meta}
}};

export default function Page() {{
    return (
        <>
        <script type="application/ld+json" dangerouslySetInnerHTML={{{{ __html: `{blog_schema}` }}}} />
        <ContentPage
            heroImage="/blog/{slug}.png"
            breadcrumbs={{[
                {{ label: "Domů", href: "/" }},
                {{ label: "Blog", href: "/blog" }},
                {{ label: "{article["h1_title"]}" }},
            ]}}
            title="{article["h1_title"]}"
            titleAccent="{article["h1_accent"]}"
            subtitle="{article["subtitle"]}"
        >
{chr(10).join(sections_jsx)}
{links_jsx}
        </ContentPage>
        </>
    );
}}
'''
    return tsx


# ── Manifest Manager ───────────────────────────────────────────────────────
def load_manifest() -> list[dict]:
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return []


def save_manifest(manifest: list[dict]):
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def add_to_manifest(article: dict, has_image: bool = False):
    manifest = load_manifest()

    # Don't add duplicate
    if any(a["slug"] == article["slug"] for a in manifest):
        log.warning(f"Article {article['slug']} already in manifest, skipping")
        return

    entry = {
        "slug": article["slug"],
        "href": f"/blog/{article['slug']}",
        "title": f"{article['h1_title']} {article['h1_accent']}",
        "desc": article["excerpt"],
        "date": article["date"],
        "date_human": article["date_human"],
        "tag": article["tag"],
    }
    if has_image:
        entry["image"] = f"/blog/{article['slug']}.png"

    # Insert at beginning (newest first)
    manifest.insert(0, entry)
    save_manifest(manifest)
    log.info(f"Added to manifest: {article['slug']} (total: {len(manifest)})")


# ── Sitemap Updater ─────────────────────────────────────────────────────────
def update_sitemap(slug: str):
    sitemap_path = FRONTEND_DIR / "public" / "sitemap.xml"
    if not sitemap_path.exists():
        log.warning("sitemap.xml not found")
        return

    content = sitemap_path.read_text(encoding="utf-8")
    new_entry = f"""  <url>
    <loc>{SITE_URL}/blog/{slug}</loc>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>"""

    if f"/blog/{slug}" in content:
        log.info(f"Sitemap already contains /blog/{slug}")
        return

    # Insert before </urlset>
    content = content.replace("</urlset>", f"{new_entry}\n</urlset>")
    sitemap_path.write_text(content, encoding="utf-8")
    log.info(f"Added /blog/{slug} to sitemap")




# ── IndexNow API ────────────────────────────────────────────────────────────
INDEXNOW_KEY = "aishield2026czaiact"

def submit_indexnow(url: str):
    """Submit URL to IndexNow (Bing, Yandex, Seznam, Naver instantly)."""
    # Create key file if not exists
    key_file = FRONTEND_DIR / "public" / f"{INDEXNOW_KEY}.txt"
    if not key_file.exists():
        key_file.write_text(INDEXNOW_KEY)
        log.info(f"Created IndexNow key file: {key_file}")

    payload = json.dumps({
        "host": "aishield.cz",
        "key": INDEXNOW_KEY,
        "keyLocation": f"https://aishield.cz/{INDEXNOW_KEY}.txt",
        "urlList": [url]
    }).encode()

    for endpoint in [
        "https://api.indexnow.org/indexnow",
        "https://www.bing.com/indexnow",
        "https://yandex.com/indexnow",
    ]:
        req = Request(endpoint, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urlopen(req, timeout=15) as resp:
                log.info(f"IndexNow {endpoint}: {resp.status}")
        except Exception as e:
            log.warning(f"IndexNow {endpoint} failed: {e}")


def ping_sitemaps():
    """Ping Google and Bing about sitemap update."""
    sitemap_url = f"{SITE_URL}/sitemap.xml"
    urls = [
        f"https://www.google.com/ping?sitemap={sitemap_url}",
        f"https://www.bing.com/ping?sitemap={sitemap_url}",
    ]
    for url in urls:
        req = Request(url)
        try:
            with urlopen(req, timeout=15) as resp:
                log.info(f"Sitemap ping {url}: {resp.status}")
        except Exception as e:
            log.warning(f"Sitemap ping failed: {e}")


def regenerate_rss():
    """Regenerate RSS feed from manifest."""
    manifest = load_manifest()
    items = ""
    for a in manifest:
        items += f"""    <item>
      <title>{a['title']}</title>
      <link>{SITE_URL}{a['href']}</link>
      <guid isPermaLink="true">{SITE_URL}{a['href']}</guid>
      <description>{a['desc']}</description>
      <pubDate>{a['date']}</pubDate>
      <category>{a.get('tag', 'AI Act')}</category>
    </item>
"""
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel>
    <title>AIshield.cz Blog — AI Act novinky pro české firmy</title>
    <link>{SITE_URL}/blog</link>
    <description>Praktické návody, analýzy a novinky o EU AI Act pro české firmy a e-shopy. Deadline: srpen 2026.</description>
    <language>cs</language>
    <lastBuildDate>{manifest[0]['date'] if manifest else ''}</lastBuildDate>
    <atom:link href="{SITE_URL}/blog/feed.xml" rel="self" type="application/rss+xml"/>
    <image>
      <url>{SITE_URL}/icon.png</url>
      <title>AIshield.cz</title>
      <link>{SITE_URL}</link>
    </image>
    <managingEditor>info@aishield.cz (AIshield.cz)</managingEditor>
    <copyright>© 2025-2026 AIshield.cz</copyright>
    <ttl>1440</ttl>
{items}  </channel>
</rss>
"""
    feed_dir = FRONTEND_DIR / "public" / "blog"
    feed_dir.mkdir(parents=True, exist_ok=True)
    (feed_dir / "feed.xml").write_text(rss, encoding="utf-8")
    log.info("RSS feed regenerated")


def update_llms_full(article: dict):
    """Append new article to llms-full.txt."""
    llms_path = FRONTEND_DIR / "public" / "llms-full.txt"
    if llms_path.exists():
        content = llms_path.read_text(encoding="utf-8")
        new_line = f"- [{article['h1_title']} {article['h1_accent']}]({SITE_URL}/blog/{article['slug']}) — {article['excerpt']} ({article['date_human']})\n"
        # Insert after "## Blog Articles" section
        if "## Blog Articles" in content:
            # Find end of blog section and insert
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("## Blog Articles"):
                    # Find next empty line or section after articles
                    j = i + 1
                    while j < len(lines) and (lines[j].startswith("- [") or lines[j].strip() == ""):
                        j += 1
                    lines.insert(j - 1, new_line.rstrip("\n"))
                    break
            llms_path.write_text("\n".join(lines), encoding="utf-8")
            log.info("Updated llms-full.txt with new article")


# ── Git Deploy ──────────────────────────────────────────────────────────────
def git_deploy(slug: str):
    """Commit and push to trigger Vercel deploy."""
    cmds = [
        ["git", "add", "-A"],
        ["git", "commit", "-m", f"blog: auto-publish {slug}"],
        ["git", "push", "origin", "main-deploy:main", "--force"],
    ]
    for cmd in cmds:
        log.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, cwd=str(FRONTEND_DIR), capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0 and "nothing to commit" not in result.stderr:
            log.warning(f"Command output: {result.stdout}\n{result.stderr}")


# ── Build Check ─────────────────────────────────────────────────────────────
def npm_build() -> bool:
    """Run npm build and return success status."""
    log.info("Running npm build...")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=str(FRONTEND_DIR),
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode == 0:
        log.info("Build succeeded")
        return True
    else:
        log.error(f"Build failed:\n{result.stdout[-2000:]}\n{result.stderr[-2000:]}")
        return False


# ── Main Pipeline ───────────────────────────────────────────────────────────
def main():
    log.info("=" * 60)
    log.info("AIshield Auto-Blog Generator starting")
    log.info("=" * 60)

    # 1. Pick topic
    topic = pick_topic()
    log.info(f"Topic: {topic['title']} (slug: {topic['slug']})")

    # 2. Generate article
    article = generate_article(topic)

    # 3. Generate OG image
    has_image = False
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    image_prompt = (
        f"Professional minimalist blog header image for article about: {topic['title']}. "
        f"Dark background (#0a0a0f), neon fuchsia (#d946ef) and cyan (#06b6d4) accent colors. "
        f"Abstract tech/AI theme, clean modern design. No text. 16:9 aspect ratio."
    )
    image_data = gemini_generate_image(image_prompt)
    if image_data:
        img_path = PUBLIC_DIR / f"{article['slug']}.png"
        img_path.write_bytes(image_data)
        has_image = True
        log.info(f"Image saved: {img_path}")
    else:
        log.info("No image generated, continuing without")

    # 4. Create page directory + TSX
    page_dir = BLOG_DIR / article["slug"]
    page_dir.mkdir(parents=True, exist_ok=True)
    tsx_content = build_page_tsx(article, has_image=has_image)
    (page_dir / "page.tsx").write_text(tsx_content, encoding="utf-8")
    log.info(f"Page created: {page_dir / 'page.tsx'}")

    # 5. Update manifest
    add_to_manifest(article, has_image=has_image)

    # 6. Update sitemap
    update_sitemap(article["slug"])

    # 7. Build
    if not npm_build():
        # If build fails, remove the page and revert
        log.error("Build failed! Removing article and reverting...")
        import shutil
        shutil.rmtree(page_dir, ignore_errors=True)
        # Remove from manifest
        manifest = load_manifest()
        manifest = [m for m in manifest if m["slug"] != article["slug"]]
        save_manifest(manifest)
        sys.exit(1)

    # 8. Regenerate RSS feed
    regenerate_rss()

    # 9. Update llms-full.txt
    update_llms_full(article)

    # 10. Deploy
    git_deploy(article["slug"])

    # 11. IndexNow — instant indexing by Bing, Yandex, Seznam
    article_url = f"{SITE_URL}/blog/{article['slug']}"
    submit_indexnow(article_url)
    submit_indexnow(f"{SITE_URL}/blog")  # also re-index blog hub

    # 12. Ping sitemaps to Google and Bing
    ping_sitemaps()

    log.info(f"✅ Article published: {article_url}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
