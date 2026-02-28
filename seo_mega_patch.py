#!/usr/bin/env python3
"""
SEO/GEO mega patch for AIshield.cz
Implements: robots.txt fix, hydration fix, self-host font, schema.org JSON-LD,
meta title/desc rewrite, contrast fixes, llms.txt rewrite, FAQ page creation
"""
import os, re

BASE = "/opt/aishield/frontend"
SRC = f"{BASE}/src/app"
PUB = f"{BASE}/public"

def patch(path, old, new):
    with open(path, "r") as f:
        content = f.read()
    if old not in content:
        print(f"  SKIP {os.path.basename(path)}: pattern not found")
        return False
    content = content.replace(old, new, 1)
    with open(path, "w") as f:
        f.write(content)
    print(f"  OK   {os.path.basename(path)}")
    return True

def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    print(f"  CREATED {os.path.relpath(path, BASE)}")

# ═══════════════════════════════════════════════════════════════
# 1. FIX robots.txt — remove invalid LLMS.txt directive
# ═══════════════════════════════════════════════════════════════
print("\n1. Fixing robots.txt...")
patch(f"{PUB}/robots.txt",
    "LLMS.txt: https://aishield.cz/llms.txt",
    "# LLMs info: https://aishield.cz/llms.txt")

# ═══════════════════════════════════════════════════════════════
# 2. FIX React hydration — countdown.tsx
# ═══════════════════════════════════════════════════════════════
print("\n2. Fixing countdown hydration...")
countdown_path = f"{BASE}/src/components/countdown.tsx"
countdown_new = '''"use client";

import { useState, useEffect } from "react";

interface TimeLeft {
    months: number;
    weeks: number;
    days: number;
    hours: number;
    minutes: number;
    seconds: number;
}

const ZERO: TimeLeft = { months: 0, weeks: 0, days: 0, hours: 0, minutes: 0, seconds: 0 };

function calcTimeLeft(): TimeLeft {
    const deadline = new Date("2026-08-02T00:00:00Z").getTime();
    const now = Date.now();
    const diff = Math.max(0, deadline - now);

    const totalSeconds = Math.floor(diff / 1000);
    const totalMinutes = Math.floor(totalSeconds / 60);
    const totalHours = Math.floor(totalMinutes / 60);
    const totalDays = Math.floor(totalHours / 24);

    const months = Math.floor(totalDays / 30);
    const afterMonths = totalDays - months * 30;
    const weeks = Math.floor(afterMonths / 7);
    const days = afterMonths - weeks * 7;
    const hours = totalHours % 24;
    const minutes = totalMinutes % 60;
    const seconds = totalSeconds % 60;

    return { months, weeks, days, hours, minutes, seconds };
}

function CountdownUnit({ value, label }: { value: number; label: string }) {
    return (
        <div className="flex flex-col items-center">
            <div className="relative w-14 h-14 sm:w-20 sm:h-20 rounded-xl bg-white/[0.04] border border-white/[0.08] backdrop-blur-sm flex items-center justify-center">
                <span suppressHydrationWarning className="text-xl sm:text-3xl font-bold tabular-nums text-white">
                    {String(value).padStart(2, "0")}
                </span>
            </div>
            <span className="mt-1.5 sm:mt-2 text-[10px] sm:text-xs font-medium uppercase tracking-wider text-slate-400">
                {label}
            </span>
        </div>
    );
}

function Separator() {
    return (
        <div className="hidden sm:flex flex-col items-center justify-center pb-6">
            <span className="text-2xl font-bold text-slate-600">:</span>
        </div>
    );
}

const labels: (keyof TimeLeft)[] = ["months", "weeks", "days", "hours", "minutes", "seconds"];
const labelsCz: Record<keyof TimeLeft, string> = {
    months: "Měsíce",
    weeks: "Týdny",
    days: "Dny",
    hours: "Hodiny",
    minutes: "Minuty",
    seconds: "Sekundy",
};

function CountdownInner({ time, className }: { time: TimeLeft; className: string }) {
    return (
        <>
            <div className={`grid grid-cols-3 gap-3 sm:hidden ${className}`}>
                {labels.map((key) => (
                    <CountdownUnit key={key} value={time[key]} label={labelsCz[key]} />
                ))}
            </div>
            <div className={`hidden sm:flex items-center justify-center gap-2 ${className}`}>
                <CountdownUnit value={time.months} label="Měsíce" />
                <Separator />
                <CountdownUnit value={time.weeks} label="Týdny" />
                <Separator />
                <CountdownUnit value={time.days} label="Dny" />
                <Separator />
                <CountdownUnit value={time.hours} label="Hodiny" />
                <Separator />
                <CountdownUnit value={time.minutes} label="Minuty" />
                <Separator />
                <CountdownUnit value={time.seconds} label="Sekundy" />
            </div>
        </>
    );
}

export default function Countdown({ className = "" }: { className?: string }) {
    const [time, setTime] = useState<TimeLeft>(ZERO);

    useEffect(() => {
        setTime(calcTimeLeft());
        const id = setInterval(() => setTime(calcTimeLeft()), 1000);
        return () => clearInterval(id);
    }, []);

    return <CountdownInner time={time} className={className} />;
}
'''
with open(countdown_path, "w") as f:
    f.write(countdown_new)
print("  OK   countdown.tsx rewritten (hydration-safe)")

# ═══════════════════════════════════════════════════════════════
# 3. SELF-HOST Inter font + Schema.org + Meta rewrite in layout.tsx
# ═══════════════════════════════════════════════════════════════
print("\n3. Rewriting layout.tsx (font, schema, meta)...")
layout_path = f"{SRC}/layout.tsx"
with open(layout_path, "r") as f:
    layout = f.read()

# --- 3a. Replace Google Fonts link with next/font/google ---
# Add import at top
if "import { Inter }" not in layout:
    layout = layout.replace(
        'import type { Metadata } from "next";',
        'import type { Metadata } from "next";\nimport { Inter } from "next/font/google";\n\nconst inter = Inter({\n    subsets: ["latin", "latin-ext"],\n    display: "swap",\n    variable: "--font-inter",\n});'
    )

# Remove the Google Fonts <link> from <head>
layout = re.sub(
    r'\s*<link\s+href="https://fonts\.googleapis\.com/css2\?family=Inter[^"]*"\s+rel="stylesheet"\s*/?\s*>\s*',
    '\n',
    layout
)

# Add font class to <html>
layout = layout.replace(
    '<html lang="cs" className="overflow-x-hidden">',
    '<html lang="cs" className={`overflow-x-hidden ${inter.variable}`}>'
)

# Add font-family to <body>
if "font-sans" not in layout and "inter.className" not in layout:
    layout = layout.replace(
        '<body className="bg-dark-900 text-slate-100 overflow-x-hidden">',
        '<body className={`bg-dark-900 text-slate-100 overflow-x-hidden ${inter.className}`}>'
    )

# --- 3b. Update meta title + description for AEO ---
layout = layout.replace(
    'title: "AIshield.cz — Váš štít proti pokutám EU za AI Act"',
    'title: {\n        default: "AI Act compliance pro české weby — skenujte zdarma za 60 sekund | AIshield.cz",\n        template: "%s | AIshield.cz",\n    }'
)

layout = layout.replace(
    '"Automatizovaný AI Act compliance scanner pro české firmy. " +\n        "Zjistěte za 60 sekund, jestli váš web splňuje nový zákon EU o umělé inteligenci. " +\n        "Deadline: srpen 2026. Pokuta až 35 milionů EUR."',
    '"Bezplatný AI Act compliance scanner pro české firmy a e-shopy. " +\n        "Zjistěte za 60 sekund, jaké AI systémy na vašem webu běží a co musíte udělat do 2. srpna 2026. " +\n        "Pokuta až 35 mil. EUR. Jsme jediný specializovaný nástroj v ČR."'
)

# Add more keywords
layout = layout.replace(
    '"české firmy",\n    ]',
    '"české firmy",\n        "AI Act e-shop",\n        "AI Act pokuty",\n        "AI Act článek 50",\n        "transparenční stránka",\n        "AI systémy na webu",\n        "AI Act Česko",\n        "AI Act povinnosti",\n    ]'
)

# --- 3c. Add JSON-LD Schema.org ---
# Insert schema script right after <head> opening
schema_json = '''
                {/* ── Schema.org JSON-LD ── */}
                <script
                    type="application/ld+json"
                    dangerouslySetInnerHTML={{
                        __html: JSON.stringify({
                            "@context": "https://schema.org",
                            "@graph": [
                                {
                                    "@type": "Organization",
                                    "@id": "https://aishield.cz/#organization",
                                    "name": "AIshield.cz",
                                    "url": "https://aishield.cz",
                                    "logo": "https://aishield.cz/icon.png",
                                    "description": "Automatizovaný AI Act compliance scanner pro české firmy a e-shopy. Skenování AI systémů, riziková klasifikace, generování dokumentace.",
                                    "foundingDate": "2025",
                                    "address": {
                                        "@type": "PostalAddress",
                                        "addressCountry": "CZ",
                                        "addressRegion": "Olomoucký kraj"
                                    },
                                    "contactPoint": {
                                        "@type": "ContactPoint",
                                        "telephone": "+420-732-716-141",
                                        "email": "info@aishield.cz",
                                        "contactType": "customer service",
                                        "availableLanguage": "Czech"
                                    },
                                    "sameAs": []
                                },
                                {
                                    "@type": "WebSite",
                                    "@id": "https://aishield.cz/#website",
                                    "name": "AIshield.cz",
                                    "url": "https://aishield.cz",
                                    "publisher": { "@id": "https://aishield.cz/#organization" },
                                    "inLanguage": "cs",
                                    "potentialAction": {
                                        "@type": "SearchAction",
                                        "target": "https://aishield.cz/scan?url={search_term_string}",
                                        "query-input": "required name=search_term_string"
                                    }
                                },
                                {
                                    "@type": "SoftwareApplication",
                                    "@id": "https://aishield.cz/#software",
                                    "name": "AIshield Scanner",
                                    "applicationCategory": "BusinessApplication",
                                    "operatingSystem": "Web",
                                    "offers": {
                                        "@type": "Offer",
                                        "price": "0",
                                        "priceCurrency": "CZK",
                                        "description": "Bezplatný AI Act sken webu"
                                    },
                                    "description": "Automatizovaný scanner AI systémů na webových stránkách pro splnění EU AI Act (Nařízení 2024/1689). Detekce chatbotů, analytiky, ML modelů a dalších AI nástrojů.",
                                    "creator": { "@id": "https://aishield.cz/#organization" }
                                },
                                {
                                    "@type": "FAQPage",
                                    "@id": "https://aishield.cz/#faq",
                                    "mainEntity": [
                                        {
                                            "@type": "Question",
                                            "name": "Co je AI Act a proč se mě týká?",
                                            "acceptedAnswer": {
                                                "@type": "Answer",
                                                "text": "AI Act (Nařízení EU 2024/1689) je první zákon na světě regulující umělou inteligenci. Platí pro každého, kdo v EU provozuje AI systémy — chatboty, analytiku, doporučovací systémy. Pokuta až 35 mil. EUR."
                                            }
                                        },
                                        {
                                            "@type": "Question",
                                            "name": "Jaké pokuty hrozí za porušení AI Act?",
                                            "acceptedAnswer": {
                                                "@type": "Answer",
                                                "text": "Až 35 milionů EUR nebo 7 % obratu za zakázané AI praktiky. Až 15 mil. EUR nebo 3 % za chybějící dokumentaci. Až 7,5 mil. EUR za nepravdivé informace. Pokuty se počítají za každé porušení zvlášť."
                                            }
                                        },
                                        {
                                            "@type": "Question",
                                            "name": "Týká se AI Act malých firem a e-shopů?",
                                            "acceptedAnswer": {
                                                "@type": "Answer",
                                                "text": "Ano. Pokud používáte chatbot (Smartsupp, Tidio), Google Analytics, doporučování produktů nebo reklamní pixel, zákon se vás týká. Pro malé firmy platí nižší stropy pokut, ale povinnost transparence zůstává."
                                            }
                                        },
                                        {
                                            "@type": "Question",
                                            "name": "Jaký je deadline pro splnění AI Act?",
                                            "acceptedAnswer": {
                                                "@type": "Answer",
                                                "text": "Klíčové datum je 2. srpen 2026 — plná účinnost AI Actu. Některé povinnosti (zakázané praktiky, AI gramotnost) platí od února 2025. Příprava dokumentace zabere 2–4 týdny."
                                            }
                                        },
                                        {
                                            "@type": "Question",
                                            "name": "Je skenování webu na AIshield.cz zdarma?",
                                            "acceptedAnswer": {
                                                "@type": "Answer",
                                                "text": "Ano, bezplatný sken je zcela zdarma, bez registrace a bez skrytých podmínek. Zadáte URL a za minutu dostanete přehled AI systémů na webu. Platíte pouze za compliance dokumenty."
                                            }
                                        },
                                        {
                                            "@type": "Question",
                                            "name": "Jak AIshield scanner funguje?",
                                            "acceptedAnswer": {
                                                "@type": "Answer",
                                                "text": "Scanner automaticky prochází web pomocí 24 nezávislých skenů z 8 zemí (desktop + mobil). Detekuje chatboty, analytiku, ML modely a další AI nástroje. Výsledky jsou k dispozici do 60 sekund pro základní sken, nebo do 24 hodin pro hloubkový audit."
                                            }
                                        }
                                    ]
                                },
                                {
                                    "@type": "HowTo",
                                    "@id": "https://aishield.cz/#howto",
                                    "name": "Jak splnit AI Act pro váš web",
                                    "description": "4 kroky ke kompletní AI Act compliance pro český web nebo e-shop",
                                    "step": [
                                        {
                                            "@type": "HowToStep",
                                            "position": 1,
                                            "name": "Skenujte web",
                                            "text": "Zadejte URL vašeho webu do AIshield scanneru. Za 60 sekund dostanete přehled všech AI systémů, které na webu běží."
                                        },
                                        {
                                            "@type": "HowToStep",
                                            "position": 2,
                                            "name": "Zjistěte rizika",
                                            "text": "Scanner automaticky klasifikuje nalezené AI systémy podle rizikových kategorií AI Actu a ukáže, jaké povinnosti z nich plynou."
                                        },
                                        {
                                            "@type": "HowToStep",
                                            "position": 3,
                                            "name": "Vyplňte dotazník",
                                            "text": "Krátký dotazník (5 minut) pokryje i interní AI systémy, které sken nevidí — ChatGPT, AI v účetnictví, automatizaci."
                                        },
                                        {
                                            "@type": "HowToStep",
                                            "position": 4,
                                            "name": "Obdržíte dokumenty",
                                            "text": "Do 7 dnů dostanete kompletní compliance dokumentaci: transparenční stránku, registr AI, risk assessment, interní AI politiku a školení."
                                        }
                                    ]
                                }
                            ]
                        })
                    }}
                />'''

if "application/ld+json" not in layout:
    layout = layout.replace(
        '<meta name="theme-color" content="#7c3aed" />',
        '<meta name="theme-color" content="#7c3aed" />' + schema_json
    )

with open(layout_path, "w") as f:
    f.write(layout)
print("  OK   layout.tsx rewritten (font + schema + meta)")

# ═══════════════════════════════════════════════════════════════
# 4. FIX contrast — footer text from slate-500 to slate-400
# ═══════════════════════════════════════════════════════════════
print("\n4. Fixing contrast in layout footer...")
with open(layout_path, "r") as f:
    layout = f.read()

# Fix countdown label contrast (already done in countdown.tsx)
# Fix footer text contrast
footer_fixes = [
    ('text-slate-500 leading-relaxed', 'text-slate-400 leading-relaxed'),
    ('text-slate-500 mt-1 flex-shrink-0', 'text-slate-400 mt-1 flex-shrink-0'),
]
for old, new in footer_fixes:
    if old in layout:
        layout = layout.replace(old, new)
        print(f"  OK   footer contrast: {old[:30]}...")

with open(layout_path, "w") as f:
    f.write(layout)

# ═══════════════════════════════════════════════════════════════
# 5. Fix neonPulse animation — use transform only (no box-shadow)
# ═══════════════════════════════════════════════════════════════
print("\n5. Fixing neonPulse animation (composited)...")
css_path = f"{SRC}/globals.css"
with open(css_path, "r") as f:
    css = f.read()

# Replace neonPulse to use only transform + opacity (GPU composited)
old_neon = """@keyframes neonPulse {

    0%,
    100% {
        transform: scale(1);
        box-shadow: 0 0 20px rgba(232, 121, 249, 0.3), 0 0 40px rgba(232, 121, 249, 0.1);
    }

    50% {
        transform: scale(1.06);
        box-shadow: 0 0 35px rgba(232, 121, 249, 0.6), 0 0 70px rgba(232, 121, 249, 0.25), 0 0 100px rgba(192, 38, 211, 0.15);
    }
}"""

new_neon = """@keyframes neonPulse {

    0%,
    100% {
        transform: scale(1);
        opacity: 1;
    }

    50% {
        transform: scale(1.04);
        opacity: 0.92;
    }
}"""

if old_neon in css:
    css = css.replace(old_neon, new_neon)
    print("  OK   neonPulse → composited (transform+opacity only)")
else:
    print("  SKIP neonPulse pattern not found exactly")

# Replace glowShimmer to use only opacity
old_glow = """@keyframes glowShimmer {

    0%,
    100% {
        border-color: rgba(232, 121, 249, 0.2);
        box-shadow: 0 0 15px rgba(232, 121, 249, 0.05);
    }

    50% {
        border-color: rgba(34, 211, 238, 0.25);
        box-shadow: 0 0 25px rgba(34, 211, 238, 0.08);
    }
}"""

new_glow = """@keyframes glowShimmer {

    0%,
    100% {
        opacity: 1;
    }

    50% {
        opacity: 0.85;
    }
}"""

if old_glow in css:
    css = css.replace(old_glow, new_glow)
    print("  OK   glowShimmer → composited (opacity only)")
else:
    print("  SKIP glowShimmer pattern not found exactly")

# Add will-change to cta-pulse
css = css.replace(
    ".cta-pulse {\n    animation: neonPulse 2s ease-in-out infinite;\n}",
    ".cta-pulse {\n    animation: neonPulse 2s ease-in-out infinite;\n    will-change: transform, opacity;\n}"
)

with open(css_path, "w") as f:
    f.write(css)

# ═══════════════════════════════════════════════════════════════
# 6. Rewrite llms.txt (richer, Czech-focused)
# ═══════════════════════════════════════════════════════════════
print("\n6. Rewriting llms.txt...")
llms_txt = """# AIshield.cz — AI Act compliance scanner pro české firmy

> Jediný specializovaný nástroj v České republice pro automatickou kontrolu souladu webů a e-shopů s EU AI Act (Nařízení 2024/1689). Bezplatné skenování, riziková klasifikace, generování dokumentace. Deadline: 2. srpen 2026.

## O AIshield.cz

AIshield.cz je česká SaaS platforma, která firmám pomáhá splnit požadavky EU AI Act. Nabízí automatizované skenování webů za účelem detekce AI systémů (chatboty, analytika, ML modely, doporučovací systémy), rizikovou klasifikaci dle článku 6, generování povinné dokumentace (transparenční stránky, technická dokumentace, riziková posouzení) a dashboard pro průběžný monitoring compliance.

## Klíčové stránky

- [Hlavní stránka](https://aishield.cz/) — hodnota služby, countdown do deadline, sociální důkazy
- [Bezplatný AI sken](https://aishield.cz/scan) — zadejte URL a za 60 sekund zjistěte, jaké AI systémy na webu běží
- [Ceník](https://aishield.cz/pricing) — balíčky BASIC, PRO, ENTERPRISE
- [Jak to funguje](https://aishield.cz/about) — 4-krokový proces od skenu po dokumenty
- [AI Act dotazník](https://aishield.cz/dotaznik) — interní AI governance assessment
- [Enterprise řešení](https://aishield.cz/enterprise) — zakázkové compliance projekty
- [FAQ](https://aishield.cz/faq) — časté otázky o AI Actu a naší službě
- [Ochrana soukromí](https://aishield.cz/privacy) — GDPR informace
- [Obchodní podmínky](https://aishield.cz/terms) — VOP

## Služby

1. **Detekce AI systémů** — 24 nezávislých skenů z 8 zemí, desktop + mobil, headless browser analýza
2. **Riziková klasifikace** — automatické zařazení do kategorií: Nepřijatelné, Vysoké, Omezené, Minimální riziko
3. **Transparenční stránka** — HTML stránka pro splnění čl. 50 AI Actu
4. **Compliance dokumentace** — technická dokumentace, riziková posouzení, registr AI systémů, interní AI politika
5. **Compliance dashboard** — sledování stavu, správa dokumentů, alerty na změny
6. **AI Act knowledge base** — 59 specializovaných compliance nástrojů

## Cílová skupina

České firmy všech velikostí, které používají AI systémy a potřebují splnit EU AI Act. Zejména: e-shopy (Shoptet, WooCommerce, Shopify), webové agentury, advokátní kanceláře, účetní firmy, obce, školy, výrobní podniky.

## Časté dotazy

### Co je AI Act?
EU AI Act (Nařízení 2024/1689) je první komplexní právní rámec pro umělou inteligenci. Stanoví pravidla pro poskytovatele a nasazovatele AI systémů na základě rizikových úrovní. Porušení: pokuta až 35 mil. EUR nebo 7 % obratu.

### Koho se AI Act týká?
Každého, kdo v EU provozuje nebo nasazuje AI systémy. E-shopy s chatbotem, weby s Google Analytics, firmy používající AI pro HR, marketing nebo zákaznický servis.

### Jaký je deadline?
2. srpen 2026 — plná účinnost AI Actu. Některé povinnosti (zakázané praktiky, AI gramotnost) platí od února 2025.

### Je sken zdarma?
Ano, bezplatný sken není nijak omezen. Žádná registrace, žádné platební údaje. Platíte pouze za compliance dokumenty.

### Jak sken funguje?
Robot automaticky prochází web pomocí 24 nezávislých skenů z 8 zemí (desktop + mobil). Detekuje chatboty, analytiku, ML modely, cookies, JavaScriptové knihovny. Výsledky do 60 sekund (základní sken) nebo 24 hodin (hloubkový audit).

## Technologie

- Frontend: Next.js (React), TypeScript, Tailwind CSS — Vercel
- Backend: Python (FastAPI) — dedikovaný VPS
- Databáze: Supabase (PostgreSQL)
- AI: OpenAI GPT-4o pro generování dokumentů
- Skenování: Playwright headless browser

## Legislativa

- EU AI Act: Nařízení (EU) 2024/1689 — https://eur-lex.europa.eu/eli/reg/2024/1689/oj
- Účinnost: 1. srpna 2024
- Plná účinnost: 2. srpna 2026
- High-risk povinnosti: 2. srpna 2027

## Kontakt

- Web: https://www.aishield.cz
- Email: info@aishield.cz
- Telefon: +420 732 716 141
- IČO: 17889251
- Provozovatel: Martin Haynes
"""
write(f"{PUB}/llms.txt", llms_txt)

# ═══════════════════════════════════════════════════════════════
# 7. Create /faq page
# ═══════════════════════════════════════════════════════════════
print("\n7. Creating /faq page...")
faq_page = '''import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Časté otázky o AI Act compliance",
    description:
        "Odpovědi na nejčastější otázky o EU AI Act, povinnostech pro české firmy, " +
        "pokutách, deadlinu 2. srpna 2026 a službách AIshield.cz.",
    alternates: { canonical: "https://aishield.cz/faq" },
};

const FAQ_ITEMS = [
    {
        q: "Co je AI Act a proč se mě týká?",
        a: "AI Act (Nařízení EU 2024/1689) je první zákon na světě, který komplexně reguluje umělou inteligenci. Platí pro každého, kdo v EU provozuje nebo nasazuje AI systémy — bez ohledu na velikost firmy. Chatbot, Google Analytics, doporučovací systém produktů, reklamní pixel — to vše jsou AI systémy ve smyslu zákona.",
    },
    {
        q: "Jaké pokuty hrozí za porušení AI Act?",
        a: "Až 35 milionů EUR nebo 7 % obratu za zakázané AI praktiky. Až 15 mil. EUR nebo 3 % za chybějící dokumentaci a neoznačený chatbot. Až 7,5 mil. EUR za nepravdivé informace. Pokuty se počítají za každé porušení zvlášť — 3 neoznačené AI systémy = 3 sankce.",
    },
    {
        q: "Týká se AI Act malých firem a e-shopů?",
        a: "Ano. Zákon platí pro všechny, kdo v EU provozují AI systémy. Používáte Smartsupp chatbot? Google Analytics? Doporučování produktů na Shoptetu? To vše jsou AI systémy. Pro malé firmy platí nižší stropy pokut, ale povinnost transparence (čl. 50) zůstává.",
    },
    {
        q: "Co když nevím, jestli mám AI na webu?",
        a: "To je naprosto normální — většina firem netuší, jaké AI nástroje na jejich webu běží. Právě proto nabízíme bezplatný sken. Zadáte URL a za minutu dostanete kompletní přehled. Žádná registrace, žádné platební údaje.",
    },
    {
        q: "Jak AIshield scanner funguje?",
        a: "Scanner automaticky prochází web pomocí 24 nezávislých skenů z 8 zemí (desktop + mobil). Detekuje chatboty, analytiku, ML modely, cookies a JavaScriptové knihovny. Základní sken trvá 60 sekund. Hloubkový audit (24h) opakuje sken v různých denních dobách pro zachycení dynamicky načítaných nástrojů.",
    },
    {
        q: "Jaký je deadline pro splnění AI Act?",
        a: "Klíčové datum je 2. srpen 2026 — plná účinnost AI Actu. Ale pozor: zákaz nepřijatelných AI praktik (čl. 5) platí od února 2025. Povinnost AI gramotnosti zaměstnanců (čl. 4) platí rovněž od února 2025. Příprava dokumentace zabere 2–4 týdny.",
    },
    {
        q: "Co je transparenční stránka?",
        a: "Transparenční stránka je HTML dokument, který musíte umístit na web, abyste informovali uživatele o používání AI systémů. Vyžaduje ji článek 50 AI Actu. AIshield ji generuje automaticky se všemi požadovanými informacemi — stačí ji vložit do patičky webu.",
    },
    {
        q: "Nahradíte advokáta?",
        a: "Ne — jsme technický nástroj, ne právní poradna. Automaticky identifikujeme AI systémy, připravíme dokumentaci, vygenerujeme transparenční stránku a interní AI politiku. Pro většinu malých firem to stačí. Pokud máte high-risk AI nebo specifickou situaci, doporučujeme dokumenty konzultovat s právníkem.",
    },
    {
        q: "Je skenování webu opravdu zdarma?",
        a: "Ano, zcela zdarma, nezávazné a bez skrytých podmínek. Nemusíte se registrovat ani zadávat platební údaje. Sken si můžete spustit opakovaně. Platíte pouze za compliance dokumenty, pokud se rozhodnete je objednat.",
    },
    {
        q: "Jak se liší BASIC, PRO a ENTERPRISE balíček?",
        a: "BASIC pokrývá základní povinnosti (transparenční stránka, registr AI). PRO přidává kompletní dokumentaci včetně risk assessmentu a interní AI politiky. ENTERPRISE zahrnuje konzultaci, právní revizi a white-label řešení pro agentury. Podrobnosti na stránce Ceník.",
    },
];

export default function FAQPage() {
    return (
        <section className="py-20 sm:py-28">
            <div className="mx-auto max-w-3xl px-4 sm:px-6">
                {/* Headline */}
                <div className="text-center mb-16">
                    <h1 className="text-4xl font-extrabold sm:text-5xl mb-4">
                        Časté <span className="neon-text">otázky</span>
                    </h1>
                    <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                        Odpovědi na nejčastější dotazy o EU AI Act, povinnostech pro české firmy
                        a službách AIshield.cz.
                    </p>
                </div>

                {/* FAQ Items */}
                <div className="space-y-6">
                    {FAQ_ITEMS.map((item, i) => (
                        <details
                            key={i}
                            className="group rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden"
                        >
                            <summary className="flex cursor-pointer items-center justify-between px-6 py-5 text-left font-semibold text-slate-100 hover:bg-white/[0.03] transition-colors">
                                <span className="pr-4">{item.q}</span>
                                <svg
                                    className="w-5 h-5 flex-shrink-0 text-fuchsia-400 transition-transform group-open:rotate-45"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                    strokeWidth={2}
                                >
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                                </svg>
                            </summary>
                            <div className="px-6 pb-5 text-slate-400 leading-relaxed">
                                {item.a}
                            </div>
                        </details>
                    ))}
                </div>

                {/* CTA */}
                <div className="mt-16 text-center">
                    <p className="text-slate-400 mb-6">Nenašli jste odpověď?</p>
                    <div className="flex flex-col sm:flex-row gap-4 justify-center">
                        <a
                            href="/scan"
                            className="btn-primary cta-pulse text-base px-8 py-3.5 inline-flex items-center justify-center gap-2"
                        >
                            Skenovat web ZDARMA
                        </a>
                        <a
                            href="mailto:info@aishield.cz"
                            className="rounded-xl border border-white/[0.1] bg-white/[0.03] px-8 py-3.5 text-base font-medium text-slate-200 hover:bg-white/[0.06] transition-colors inline-flex items-center justify-center gap-2"
                        >
                            Napsat nám
                        </a>
                    </div>
                </div>
            </div>
        </section>
    );
}
'''
write(f"{SRC}/faq/page.tsx", faq_page)

# ═══════════════════════════════════════════════════════════════
# 8. Update sitemap — add /faq
# ═══════════════════════════════════════════════════════════════
print("\n8. Updating sitemap...")
sitemap_path = f"{BASE}/public/sitemap.xml"
if os.path.exists(sitemap_path):
    with open(sitemap_path, "r") as f:
        sitemap = f.read()
    if "/faq" not in sitemap:
        sitemap = sitemap.replace(
            "</urlset>",
            """    <url>
        <loc>https://aishield.cz/faq</loc>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>
</urlset>"""
        )
        with open(sitemap_path, "w") as f:
            f.write(sitemap)
        print("  OK   Added /faq to sitemap.xml")
else:
    print("  SKIP sitemap.xml not found (Next.js may generate it)")

# ═══════════════════════════════════════════════════════════════
# 9. Add heading hierarchy fix (H3 before H2 issue from PageSpeed)
# PageSpeed flagged: <h3> "CO ZÁKON VYŽADUJE" appearing before any H2
# ═══════════════════════════════════════════════════════════════
print("\n9. Checking heading hierarchy...")
page_path = f"{SRC}/page.tsx"
with open(page_path, "r") as f:
    page = f.read()

# Fix the H3 that appears before H2
if 'h3 className="text-sm font-semibold uppercase tracking-wider text-fuchsia-400 mb-4 text-' in page:
    page = page.replace(
        'h3 className="text-sm font-semibold uppercase tracking-wider text-fuchsia-400 mb-4 text-',
        'p className="text-sm font-semibold uppercase tracking-wider text-fuchsia-400 mb-4 text-'
    )
    with open(page_path, "w") as f:
        f.write(page)
    print("  OK   Fixed h3→p for pre-H2 label")
else:
    print("  SKIP h3 pattern not found")

print("\n" + "=" * 60)
print("ALL PATCHES APPLIED")
print("=" * 60)
