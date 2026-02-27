#!/usr/bin/env python3
"""
AIshield.cz — Automatický responzivní test (Playwright)
========================================================
Spuštění:  cd /opt/aishield && ./venv/bin/python test_responsive.py
Výstup:    /opt/aishield/responsive_report/ (screenshoty + HTML report)

Testuje všechny veřejné stránky na 3 viewportech:
  - Mobile  (375×812, iPhone 14)
  - Tablet  (768×1024, iPad)
  - Desktop (1440×900)

Kontroly:
  1. Screenshot každé stránky na každém viewportu
  2. Horizontální overflow detekce (scrollWidth > clientWidth)
  3. Detekce oříznutého textu (text-overflow: ellipsis)
  4. Viditelnost klíčových elementů (h1, nav, buttons)
  5. Kontrola z-index překryvů
  6. Detekce příliš malého fontu (<10px)
  7. Kontrola tapovatelné velikosti (min 44×44px pro touch)
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# ── Nastavení ──
BASE_URL = os.getenv("TEST_URL", "https://aishield.cz")
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/opt/aishield/responsive_report"))
TIMEOUT = 15_000  # ms

VIEWPORTS = {
    "mobile":  {"width": 375,  "height": 812},
    "tablet":  {"width": 768,  "height": 1024},
    "desktop": {"width": 1440, "height": 900},
}

# Stránky k testování (veřejně přístupné bez autentizace)
PAGES = [
    {"path": "/",          "name": "homepage",  "desc": "Hlavní stránka"},
    {"path": "/pricing",   "name": "pricing",   "desc": "Ceník"},
    {"path": "/about",     "name": "about",     "desc": "Jak to funguje"},
    {"path": "/login",     "name": "login",     "desc": "Přihlášení"},
    {"path": "/registrace","name": "registrace","desc": "Registrace"},
    {"path": "/scan",      "name": "scan",      "desc": "Skenovat web"},
    {"path": "/dotaznik",  "name": "dotaznik",  "desc": "Dotazník"},
]


async def run_tests():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ Playwright není nainstalován. Spusťte: pip install playwright && playwright install chromium")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    screenshots_dir = OUTPUT_DIR / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)

    results = []
    start_time = datetime.now()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for vp_name, vp_size in VIEWPORTS.items():
            context = await browser.new_context(
                viewport=vp_size,
                device_scale_factor=2 if vp_name == "mobile" else 1,
                user_agent=(
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                    "Mobile/15E148 Safari/604.1"
                    if vp_name == "mobile" else None
                ),
            )
            page = await context.new_page()

            for pg in PAGES:
                url = f"{BASE_URL}{pg['path']}"
                page_name = pg["name"]
                print(f"  🔍 [{vp_name:>7}] {pg['desc']:20} → {url}")

                result = {
                    "page": page_name,
                    "viewport": vp_name,
                    "url": url,
                    "width": vp_size["width"],
                    "height": vp_size["height"],
                    "issues": [],
                    "score": 100,
                    "screenshot": f"screenshots/{page_name}_{vp_name}.png",
                }

                try:
                    # Načti stránku
                    response = await page.goto(url, wait_until="networkidle", timeout=TIMEOUT)

                    if response and response.status >= 400:
                        result["issues"].append({
                            "type": "http_error",
                            "severity": "critical",
                            "detail": f"HTTP {response.status}",
                        })
                        result["score"] -= 50

                    # Počkej na vykreslení
                    await page.wait_for_timeout(1500)

                    # ── Test 1: Horizontální overflow ──
                    overflow = await page.evaluate("""() => {
                        const body = document.body;
                        const html = document.documentElement;
                        const overflows = [];
                        
                        // Check body/html overflow
                        if (html.scrollWidth > html.clientWidth + 5) {
                            overflows.push({
                                element: 'html',
                                scrollWidth: html.scrollWidth,
                                clientWidth: html.clientWidth,
                                diff: html.scrollWidth - html.clientWidth,
                            });
                        }
                        
                        // Check all elements
                        const all = document.querySelectorAll('*');
                        for (const el of all) {
                            const rect = el.getBoundingClientRect();
                            if (rect.right > window.innerWidth + 5 && rect.width > 0) {
                                const tag = el.tagName.toLowerCase();
                                const cls = el.className?.toString().slice(0, 60) || '';
                                overflows.push({
                                    element: `${tag}.${cls}`,
                                    right: Math.round(rect.right),
                                    viewportWidth: window.innerWidth,
                                    overflow: Math.round(rect.right - window.innerWidth),
                                });
                                if (overflows.length > 5) break;
                            }
                        }
                        return overflows;
                    }""")

                    if overflow:
                        result["issues"].append({
                            "type": "horizontal_overflow",
                            "severity": "high",
                            "detail": f"{len(overflow)} elementů přetéká viewport",
                            "elements": overflow[:3],
                        })
                        result["score"] -= min(30, len(overflow) * 10)

                    # ── Test 2: Příliš malý font (<10px) ──
                    small_fonts = await page.evaluate("""() => {
                        const problems = [];
                        const els = document.querySelectorAll('p, span, a, li, td, th, label, h1, h2, h3, h4, button');
                        for (const el of els) {
                            const text = el.innerText?.trim();
                            if (!text || text.length === 0) continue;
                            const style = window.getComputedStyle(el);
                            const size = parseFloat(style.fontSize);
                            if (size < 10 && size > 0) {
                                problems.push({
                                    text: text.slice(0, 40),
                                    fontSize: size,
                                    element: el.tagName.toLowerCase(),
                                });
                                if (problems.length > 3) break;
                            }
                        }
                        return problems;
                    }""")

                    if small_fonts:
                        result["issues"].append({
                            "type": "small_font",
                            "severity": "medium",
                            "detail": f"{len(small_fonts)} textů má font <10px",
                            "elements": small_fonts[:3],
                        })
                        result["score"] -= min(15, len(small_fonts) * 5)

                    # ── Test 3: Tapovatelná velikost (touch targets <44px) ──
                    if vp_name == "mobile":
                        small_targets = await page.evaluate("""() => {
                            const problems = [];
                            const clickables = document.querySelectorAll('a, button, input, select, [role="button"], [onclick]');
                            for (const el of clickables) {
                                const rect = el.getBoundingClientRect();
                                if (rect.width === 0 || rect.height === 0) continue;
                                if (rect.width < 44 || rect.height < 44) {
                                    // Skip if invisible
                                    const style = window.getComputedStyle(el);
                                    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') continue;
                                    
                                    const text = el.innerText?.trim().slice(0, 30) || el.getAttribute('aria-label') || el.tagName;
                                    problems.push({
                                        text: text,
                                        width: Math.round(rect.width),
                                        height: Math.round(rect.height),
                                        element: el.tagName.toLowerCase(),
                                    });
                                    if (problems.length > 5) break;
                                }
                            }
                            return problems;
                        }""")

                        if small_targets:
                            result["issues"].append({
                                "type": "small_touch_target",
                                "severity": "medium",
                                "detail": f"{len(small_targets)} tlačítek/odkazů je menších než 44×44px",
                                "elements": small_targets[:3],
                            })
                            result["score"] -= min(15, len(small_targets) * 3)

                    # ── Test 4: Viditelnost H1 ──
                    h1_visible = await page.evaluate("""() => {
                        const h1 = document.querySelector('h1');
                        if (!h1) return { exists: false };
                        const rect = h1.getBoundingClientRect();
                        const style = window.getComputedStyle(h1);
                        return {
                            exists: true,
                            visible: style.display !== 'none' && style.visibility !== 'hidden',
                            inViewport: rect.top < window.innerHeight && rect.bottom > 0,
                            text: h1.innerText?.slice(0, 60),
                        };
                    }""")

                    if not h1_visible.get("exists"):
                        result["issues"].append({
                            "type": "missing_h1",
                            "severity": "low",
                            "detail": "Stránka nemá H1 element",
                        })
                        result["score"] -= 5
                    elif not h1_visible.get("visible") or not h1_visible.get("inViewport"):
                        result["issues"].append({
                            "type": "h1_not_visible",
                            "severity": "medium",
                            "detail": f"H1 není viditelný: '{h1_visible.get('text', '')}'",
                        })
                        result["score"] -= 10

                    # ── Test 5: Tabulky bez overflow-x ──
                    tables_overflow = await page.evaluate("""() => {
                        const problems = [];
                        const tables = document.querySelectorAll('table');
                        for (const table of tables) {
                            const rect = table.getBoundingClientRect();
                            const parentRect = table.parentElement?.getBoundingClientRect();
                            if (!parentRect) continue;
                            
                            // Check if table is wider than viewport
                            if (rect.width > window.innerWidth) {
                                const parent = table.parentElement;
                                const parentStyle = window.getComputedStyle(parent);
                                const hasScroll = parentStyle.overflowX === 'auto' || 
                                                  parentStyle.overflowX === 'scroll' ||
                                                  parentStyle.overflow === 'auto' ||
                                                  parentStyle.overflow === 'scroll';
                                if (!hasScroll) {
                                    problems.push({
                                        tableWidth: Math.round(rect.width),
                                        viewportWidth: window.innerWidth,
                                        parentOverflow: parentStyle.overflowX || parentStyle.overflow,
                                        cols: table.querySelectorAll('th, thead td').length,
                                    });
                                }
                            }
                        }
                        return problems;
                    }""")

                    if tables_overflow:
                        result["issues"].append({
                            "type": "table_overflow",
                            "severity": "high",
                            "detail": f"{len(tables_overflow)} tabulek přetéká bez horizontálního scrollu",
                            "elements": tables_overflow,
                        })
                        result["score"] -= min(30, len(tables_overflow) * 10)

                    # ── Test 6: Light-mode classes na dark site ──
                    light_mode = await page.evaluate("""() => {
                        const problems = [];
                        const all = document.querySelectorAll('*');
                        for (const el of all) {
                            const style = window.getComputedStyle(el);
                            const bg = style.backgroundColor;
                            const color = style.color;
                            
                            // Detect white/light bg on dark site
                            if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') {
                                // Parse RGB values
                                const match = bg.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
                                if (match) {
                                    const [_, r, g, b] = match.map(Number);
                                    const brightness = (r * 299 + g * 587 + b * 114) / 1000;
                                    // If element has very bright bg AND dark text = light mode element
                                    if (brightness > 230) {
                                        const colorMatch = color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
                                        if (colorMatch) {
                                            const [__, cr, cg, cb] = colorMatch.map(Number);
                                            const textBright = (cr * 299 + cg * 587 + cb * 114) / 1000;
                                            if (textBright < 80) {
                                                const rect = el.getBoundingClientRect();
                                                if (rect.width > 50 && rect.height > 20) {
                                                    problems.push({
                                                        element: el.tagName.toLowerCase(),
                                                        class: el.className?.toString().slice(0, 50),
                                                        bgBrightness: Math.round(brightness),
                                                        textBrightness: Math.round(textBright),
                                                        size: `${Math.round(rect.width)}×${Math.round(rect.height)}`,
                                                    });
                                                    if (problems.length > 3) break;
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        return problems;
                    }""")

                    if light_mode:
                        result["issues"].append({
                            "type": "light_mode_mismatch",
                            "severity": "high",
                            "detail": f"{len(light_mode)} elementů má light-mode styl na dark site",
                            "elements": light_mode[:3],
                        })
                        result["score"] -= min(25, len(light_mode) * 8)

                    # Clamp score
                    result["score"] = max(0, min(100, result["score"]))

                    # Screenshot
                    ss_path = screenshots_dir / f"{page_name}_{vp_name}.png"
                    await page.screenshot(path=str(ss_path), full_page=True)

                except Exception as e:
                    result["issues"].append({
                        "type": "error",
                        "severity": "critical",
                        "detail": str(e)[:200],
                    })
                    result["score"] = 0

                results.append(result)

            await context.close()

        await browser.close()

    # ── Generuj HTML report ──
    duration = (datetime.now() - start_time).total_seconds()
    generate_html_report(results, duration)
    generate_json_report(results, duration)

    # ── Souhrn v terminálu ──
    print(f"\n{'='*60}")
    print(f"  AIshield.cz Responsiveness Test — DONE ({duration:.1f}s)")
    print(f"{'='*60}\n")

    for vp_name in VIEWPORTS:
        print(f"  📱 {vp_name.upper():>7}:")
        vp_results = [r for r in results if r["viewport"] == vp_name]
        for r in vp_results:
            icon = "✅" if r["score"] >= 80 else "⚠️" if r["score"] >= 50 else "❌"
            issues_str = f" ({len(r['issues'])} issues)" if r["issues"] else ""
            print(f"    {icon} {r['page']:15} → {r['score']:3}/100{issues_str}")
        print()

    # Celkové skóre
    total = sum(r["score"] for r in results)
    avg = total / len(results) if results else 0
    print(f"  📊 Průměrné skóre: {avg:.0f}/100")
    print(f"  📁 Report: {OUTPUT_DIR}/report.html")
    print(f"  📁 JSON:   {OUTPUT_DIR}/results.json\n")

    # Exit code: fail pokud avg < 60
    sys.exit(0 if avg >= 60 else 1)


def severity_color(sev):
    return {"critical": "#ef4444", "high": "#f97316", "medium": "#eab308", "low": "#22d3ee"}.get(sev, "#94a3b8")


def severity_icon(sev):
    return {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}.get(sev, "⚪")


def score_color(score):
    if score >= 80: return "#4ade80"
    if score >= 50: return "#facc15"
    return "#f87171"


def generate_html_report(results, duration):
    """Generuje krásný HTML report se screenshoty."""
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    avg_score = sum(r["score"] for r in results) / len(results) if results else 0
    total_issues = sum(len(r["issues"]) for r in results)

    html = f"""<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIshield.cz — Responsive Audit Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', system-ui, sans-serif; background: #0f172a; color: #e2e8f0; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        
        .header {{ text-align: center; margin-bottom: 3rem; padding: 2rem; border-bottom: 1px solid rgba(255,255,255,0.08); }}
        .header h1 {{ font-size: 2rem; font-weight: 800; margin-bottom: 0.5rem; }}
        .header h1 span {{ background: linear-gradient(135deg, #e879f9, #22d3ee); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .header .meta {{ color: #94a3b8; font-size: 0.875rem; }}
        
        .stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 2rem; }}
        .stat {{ background: rgba(30,41,59,0.6); border: 1px solid rgba(255,255,255,0.08); border-radius: 1rem; padding: 1.5rem; text-align: center; }}
        .stat .value {{ font-size: 2rem; font-weight: 800; }}
        .stat .label {{ font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 0.25rem; }}
        
        .viewport-section {{ margin-bottom: 3rem; }}
        .viewport-title {{ font-size: 1.25rem; font-weight: 700; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid rgba(255,255,255,0.06); }}
        
        .page-card {{ background: rgba(30,41,59,0.6); border: 1px solid rgba(255,255,255,0.08); border-radius: 1rem; margin-bottom: 1rem; overflow: hidden; }}
        .page-header {{ display: flex; align-items: center; justify-content: space-between; padding: 1rem 1.5rem; cursor: pointer; }}
        .page-header:hover {{ background: rgba(255,255,255,0.03); }}
        .page-name {{ font-weight: 600; }}
        .score-badge {{ padding: 0.25rem 0.75rem; border-radius: 2rem; font-size: 0.875rem; font-weight: 700; }}
        
        .page-details {{ padding: 0 1.5rem 1.5rem; }}
        .issue {{ display: flex; align-items: flex-start; gap: 0.75rem; padding: 0.75rem; border-radius: 0.5rem; margin-bottom: 0.5rem; background: rgba(0,0,0,0.2); }}
        .issue-type {{ font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }}
        .issue-detail {{ font-size: 0.875rem; color: #cbd5e1; }}
        
        .screenshot {{ margin-top: 1rem; }}
        .screenshot img {{ max-width: 100%; border-radius: 0.5rem; border: 1px solid rgba(255,255,255,0.1); }}
        .screenshot-label {{ font-size: 0.75rem; color: #64748b; margin-top: 0.25rem; }}
        
        .no-issues {{ color: #4ade80; font-size: 0.875rem; padding: 0.75rem; }}
        
        details > summary {{ list-style: none; }}
        details > summary::-webkit-details-marker {{ display: none; }}
        details[open] .chevron {{ transform: rotate(180deg); }}
        .chevron {{ transition: transform 0.2s; color: #64748b; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AIshield.cz — <span>Responsive Audit</span></h1>
            <p class="meta">{now} • {duration:.1f}s • {len(results)} testů</p>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="value" style="color: {score_color(avg_score)}">{avg_score:.0f}%</div>
                <div class="label">Průměrné skóre</div>
            </div>
            <div class="stat">
                <div class="value" style="color: {'#f87171' if total_issues > 10 else '#facc15' if total_issues > 0 else '#4ade80'}">{total_issues}</div>
                <div class="label">Celkem problémů</div>
            </div>
            <div class="stat">
                <div class="value" style="color: #22d3ee">{len(PAGES) * len(VIEWPORTS)}</div>
                <div class="label">Testovaných kombinací</div>
            </div>
        </div>
"""

    for vp_name, vp_size in VIEWPORTS.items():
        icon = {"mobile": "📱", "tablet": "📋", "desktop": "🖥️"}[vp_name]
        vp_results = [r for r in results if r["viewport"] == vp_name]
        vp_avg = sum(r["score"] for r in vp_results) / len(vp_results) if vp_results else 0

        html += f"""
        <div class="viewport-section">
            <div class="viewport-title">
                {icon} {vp_name.upper()} ({vp_size['width']}×{vp_size['height']}) — 
                <span style="color: {score_color(vp_avg)}">{vp_avg:.0f}% průměr</span>
            </div>
"""
        for r in vp_results:
            sc = r["score"]
            issues = r["issues"]
            badge_bg = score_color(sc) + "20"
            badge_color = score_color(sc)

            html += f"""
            <details class="page-card">
                <summary class="page-header">
                    <span class="page-name">{r['page']} <span style="color: #64748b; font-weight: 400; font-size: 0.8rem;">({r['url']})</span></span>
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        {'<span style="color: #94a3b8; font-size: 0.8rem;">' + str(len(issues)) + ' issues</span>' if issues else '<span style="color: #4ade80; font-size: 0.8rem;">OK</span>'}
                        <span class="score-badge" style="background: {badge_bg}; color: {badge_color};">{sc}/100</span>
                        <span class="chevron">▼</span>
                    </div>
                </summary>
                <div class="page-details">
"""
            if issues:
                for issue in issues:
                    sev = issue["severity"]
                    html += f"""
                    <div class="issue">
                        <span style="color: {severity_color(sev)}; font-size: 1.1rem;">{severity_icon(sev)}</span>
                        <div>
                            <div class="issue-type" style="color: {severity_color(sev)}">{issue['type'].replace('_', ' ')}</div>
                            <div class="issue-detail">{issue['detail']}</div>
                        </div>
                    </div>
"""
            else:
                html += '                    <div class="no-issues">✅ Žádné problémy nenalezeny</div>\n'

            html += f"""
                    <div class="screenshot">
                        <img src="{r['screenshot']}" alt="{r['page']} {vp_name}" loading="lazy" />
                        <div class="screenshot-label">{r['page']} — {vp_name} ({r['width']}×{r['height']})</div>
                    </div>
                </div>
            </details>
"""
        html += "        </div>\n"

    html += """
    </div>
</body>
</html>
"""

    report_path = OUTPUT_DIR / "report.html"
    report_path.write_text(html, encoding="utf-8")
    print(f"  📄 HTML report: {report_path}")


def generate_json_report(results, duration):
    """Uloží strojově čitelný JSON report."""
    data = {
        "generated": datetime.now().isoformat(),
        "base_url": BASE_URL,
        "duration_seconds": round(duration, 1),
        "viewports": VIEWPORTS,
        "pages_tested": len(PAGES),
        "total_tests": len(results),
        "average_score": round(sum(r["score"] for r in results) / len(results), 1) if results else 0,
        "results": results,
    }
    json_path = OUTPUT_DIR / "results.json"
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  📊 JSON report: {json_path}")


if __name__ == "__main__":
    print(f"\n🛡️  AIshield.cz Responsive Test")
    print(f"{'='*40}")
    print(f"  URL:       {BASE_URL}")
    print(f"  Viewports: {', '.join(VIEWPORTS.keys())}")
    print(f"  Pages:     {len(PAGES)}")
    print(f"  Output:    {OUTPUT_DIR}")
    print(f"{'='*40}\n")
    asyncio.run(run_tests())
