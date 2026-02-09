"""
AIshield.cz — Email Templates v5 (TEMPLATE-DRIVEN)
Čistě šablonový email — Gemini POUZE skloňuje jméno (5. pád).

Struktura emailu (dle zadání):
1. Header s logem
2. Úvod (ŠABLONA — ne AI) — představení, uklidnění, nařízení EU
3. Panel s pokutami (soft red)
4. Intro k nálezům + tabulka rizik
5. Compliance checklist (zelené fajfky, vyčerpávající)
6. Pozitivní pivot — "Od toho jsme tady my" + co dodáme
7. Empatie banner — "soustřeďte se na byznys"
8. Deadline box (ČERVENÝ)
9. CTA tlačítko → ceník na webu
10. Profesionální footer s Desperados Design
"""

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote


@dataclass
class EmailVariant:
    """Email varianta pro odeslání."""
    subject: str
    body_html: str
    variant_id: str = "template_v5"


@dataclass
class FindingRow:
    """Řádek tabulky rizik pro email."""
    name: str
    category: str
    risk_level: str       # minimal, limited, high, prohibited
    ai_act_article: str
    action_required: str = ""
    description: str = ""


# ── Barvy a styly ──
BRAND = {
    "gradient_start": "#0f172a",
    "gradient_mid": "#1e1b4b",
    "gradient_end": "#312e81",
    "accent": "#7c3aed",
    "accent_light": "#a78bfa",
    "text": "#1e293b",
    "text_light": "#64748b",
    "bg": "#ffffff",
    "bg_light": "#f8fafc",
    "border": "#e2e8f0",
    "success": "#22c55e",
    "warning": "#eab308",
    "danger": "#ef4444",
    "critical": "#991b1b",
}

RISK_BADGE = {
    "minimal": {
        "color": "#15803d",
        "bg": "#dcfce7",
        "label": "Minimální",
        "icon": "🟢",
    },
    "limited": {
        "color": "#a16207",
        "bg": "#fef9c3",
        "label": "Omezené",
        "icon": "🟡",
    },
    "high": {
        "color": "#dc2626",
        "bg": "#fee2e2",
        "label": "Vysoké",
        "icon": "🔴",
    },
    "prohibited": {
        "color": "#7f1d1d",
        "bg": "#fecaca",
        "label": "Zakázané",
        "icon": "⛔",
    },
}

# Mapování článků AI Act na oficiální URL (EUR-Lex)
AI_ACT_ARTICLE_URLS = {
    "čl. 4": "https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689#art_4",
    "čl. 5": "https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689#art_5",
    "čl. 6": "https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689#art_6",
    "čl. 9": "https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689#art_9",
    "čl. 10": "https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689#art_10",
    "čl. 13": "https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689#art_13",
    "čl. 14": "https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689#art_14",
    "čl. 26": "https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689#art_26",
    "čl. 27": "https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689#art_27",
    "čl. 50": "https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689#art_50",
    "čl. 52": "https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689#art_52",
    "čl. 99": "https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689#art_99",
}

# URL na celé nařízení
AI_ACT_FULL_URL = "https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689"


def _current_date_cs() -> str:
    """Aktuální datum česky."""
    months = {
        1: "ledna", 2: "února", 3: "března", 4: "dubna",
        5: "května", 6: "června", 7: "července", 8: "srpna",
        9: "září", 10: "října", 11: "listopadu", 12: "prosince",
    }
    now = datetime.utcnow()
    return f"{now.day}. {months[now.month]} {now.year}"


def _days_to_deadline() -> int:
    """Kolik dní zbývá do 2. srpna 2026."""
    deadline = datetime(2026, 8, 2)
    return (deadline - datetime.utcnow()).days


def _article_link(article: str) -> str:
    """Převede článek AI Act na klikatelný HTML odkaz."""
    # Zkusíme najít přesný match
    url = AI_ACT_ARTICLE_URLS.get(article)
    if url:
        return f'<a href="{url}" style="color: {BRAND["accent"]}; text-decoration: underline;">{article} AI Act</a>'

    # Zkusíme vytáhnout číslo článku
    import re
    m = re.search(r'(\d+)', article)
    if m:
        num = m.group(1)
        key = f"čl. {num}"
        url = AI_ACT_ARTICLE_URLS.get(key)
        if url:
            return f'<a href="{url}" style="color: {BRAND["accent"]}; text-decoration: underline;">{article}</a>'

    # Fallback — odkaz na celé nařízení
    return f'<a href="{AI_ACT_FULL_URL}" style="color: {BRAND["accent"]}; text-decoration: underline;">{article}</a>'


# ── Laické popisy kategorií AI nálezů ──
LAYMAN_DESCRIPTIONS = {
    "chatbot": "Chatovací okénko na webu, které odpovídá návštěvníkům pomocí umělé inteligence",
    "analytics": "Nástroj pro sledování a analýzu návštěvníků webu s využitím AI predikce",
    "recommender": "Systém, který návštěvníkům doporučuje produkty nebo obsah pomocí AI",
    "content_gen": "Nástroj pro automatické generování textů nebo obrázků pomocí AI",
    "ai_tool": "AI nástroj integrovaný do webu",
    "tracking": "Sledovací skript, který sbírá data o návštěvnících",
    "tag_manager": "Správce skriptů, který může načítat AI nástroje třetích stran",
    "social": "Sociální síťový skript se strojovým učením pro cílení reklam",
    "automation": "Automatizační nástroj využívající umělou inteligenci",
    "ai_api": "Připojení k AI službě (API), které umožňuje webu používat umělou inteligenci",
    "transparency": "Oznámení o použití AI — dobrý začátek, ale vyžaduje kompletní dokumentaci",
    "marketplace": "Tržiště / e-shop platforma s integrovanými AI funkcemi",
}


def _get_layman_desc(finding: FindingRow) -> str:
    """Vrátí jednoduchý, srozumitelný popis nálezu pro laika."""
    if finding.description:
        # Pokud má vlastní popis, použijeme ho, ale zkontroluj délku
        if len(finding.description) < 120:
            return finding.description
    return LAYMAN_DESCRIPTIONS.get(finding.category, "AI systém detekovaný na vašem webu")


def _risk_table_html(findings: list[FindingRow]) -> str:
    """Tabulka rizik — jednoduchý jazyk, klikatelné články."""
    if not findings:
        return ""

    rows = ""
    for f in findings:
        badge = RISK_BADGE.get(f.risk_level, RISK_BADGE["limited"])
        desc = _get_layman_desc(f)
        article_html = _article_link(f.ai_act_article)
        rows += f"""
            <tr>
                <td style="padding: 12px 16px; border-bottom: 1px solid #f1f5f9; font-size: 14px; color: {BRAND['text']};">
                    <strong>{f.name}</strong>
                    <br><span style="font-size: 12px; color: {BRAND['text_light']};">{desc}</span>
                </td>
                <td style="padding: 12px 8px; border-bottom: 1px solid #f1f5f9; text-align: center;">
                    <span style="display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; background: {badge['bg']}; color: {badge['color']};">
                        {badge['icon']} {badge['label']}
                    </span>
                </td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #f1f5f9; font-size: 13px; color: {BRAND['text_light']};">
                    {article_html}
                </td>
            </tr>"""

    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse: collapse; margin: 20px 0; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
        <thead>
            <tr style="background: {BRAND['bg_light']};">
                <th style="padding: 10px 16px; text-align: left; font-size: 13px; font-weight: 600; color: {BRAND['text']}; border-bottom: 2px solid #e2e8f0;">AI systém</th>
                <th style="padding: 10px 8px; text-align: center; font-size: 13px; font-weight: 600; color: {BRAND['text']}; border-bottom: 2px solid #e2e8f0;">Riziko</th>
                <th style="padding: 10px 16px; text-align: left; font-size: 13px; font-weight: 600; color: {BRAND['text']}; border-bottom: 2px solid #e2e8f0;">Článek AI Act</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>"""


def _screenshot_section(screenshot_url: str, company_url: str) -> str:
    """Screenshot webu."""
    if not screenshot_url:
        return ""

    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="margin: 20px 0;">
        <tr>
            <td style="padding: 12px; background: {BRAND['bg_light']}; border: 1px solid {BRAND['border']}; border-radius: 8px; text-align: center;">
                <p style="margin: 0 0 8px 0; font-size: 12px; color: {BRAND['text_light']};">
                    Screenshot webu {company_url} — {_current_date_cs()}
                </p>
                <img src="{screenshot_url}" alt="Screenshot {company_url}"
                     style="max-width: 100%; height: auto; border: 1px solid {BRAND['border']}; border-radius: 4px;">
            </td>
        </tr>
    </table>"""


def _intro_section(
    vocative_name: str,
    company_url: str,
    company_name: str,
    findings_count: int,
) -> str:
    """
    Úvodní sekce emailu — ŠABLONA, ne AI.
    Gemini pouze dodá vocative_name (skloněné jméno v 5. pádu).
    """
    # Oslovení
    if vocative_name:
        greeting = f"Dobrý den {vocative_name},"
    else:
        greeting = "Dobrý den,"

    # Počet nálezů
    if findings_count == 1:
        pocet = "1 AI systém"
    elif 2 <= findings_count <= 4:
        pocet = f"{findings_count} AI systémy"
    else:
        pocet = f"{findings_count} AI systémů"

    # Pro "zaujal mě Váš web" použij URL,
    # pro ostatní účely company_name
    display_url = company_url.replace("https://www.", "").replace("http://www.", "").replace("https://", "").replace("http://", "").rstrip("/")

    return f"""
    <div style="font-size: 15px; line-height: 1.7; color: {BRAND['text']};">
        <p style="margin: 0 0 14px 0;">
            {greeting}
        </p>
        <p style="margin: 0 0 14px 0;">
            jsem Martin Haynes, zakladatel
            <a href="https://aishield.cz" style="color: {BRAND['accent']}; text-decoration: underline; font-weight: 600;">AIshield.cz</a>,
            a&nbsp;zaujal mě Váš web <strong>{display_url}</strong>.
        </p>
        <p style="margin: 0 0 14px 0;">
            <strong>Nemusíte se obávat, nic strašného se zatím neděje.</strong>
            Jen jsme Vás chtěli upozornit, že při naší pravidelné kontrole
            webů a&nbsp;e-shopů v&nbsp;českém online prostředí jsme narazili
            na váš web <strong>{company_url}</strong>.
        </p>
        <p style="margin: 0 0 14px 0;">
            Jistě je Vám dobře známo, že k&nbsp;<strong>2.&nbsp;srpnu 2026</strong>
            vstupuje v&nbsp;plnou účinnost nové
            <a href="{AI_ACT_FULL_URL}" style="color: {BRAND['accent']}; text-decoration: underline;">nařízení Evropské unie (AI Act)</a>,
            dle kterého musejí <strong>všechny webové stránky, e-shopy
            a&nbsp;aplikace</strong> informovat své uživatele o&nbsp;tom,
            zda&#8209;li a&nbsp;jak využívají na svých stránkách umělou inteligenci.
        </p>
        <p style="margin: 0 0 14px 0;">
            Bohužel&nbsp;— na vašem webu <strong>tyto informace zatím uvedeny nemáte</strong>.
        </p>
    </div>"""


def _penalty_panel() -> str:
    """Panel s pokutami — soft red."""
    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="margin: 20px 0;">
        <tr>
            <td style="padding: 18px 22px; background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; border-left: 4px solid {BRAND['danger']};">
                <p style="margin: 0 0 6px 0; font-size: 15px; font-weight: 700; color: #991b1b;">
                    &#9888;&#65039; Hrozící sankce za nesoulad s AI Act
                </p>
                <p style="margin: 0; font-size: 14px; line-height: 1.6; color: #7f1d1d;">
                    V&nbsp;případě nesplnění povinností hrozí pokuty až do výše
                    <strong>35&nbsp;milionů&nbsp;EUR</strong> nebo
                    <strong>7&nbsp;% celosvětového ročního obratu</strong> společnosti
                    (podle toho, která částka je vyšší).
                    Dozorový úřad může zahájit kontrolu kdykoliv po 2.&nbsp;srpnu 2026.
                </p>
            </td>
        </tr>
    </table>"""


def _findings_intro(findings_count: int) -> str:
    """Úvod k tabulce nálezů."""
    if findings_count == 1:
        pocet = "1 AI systém"
    elif 2 <= findings_count <= 4:
        pocet = f"{findings_count} AI systémy"
    else:
        pocet = f"{findings_count} AI systémů"

    return f"""
    <div style="font-size: 15px; line-height: 1.7; color: {BRAND['text']}; margin: 20px 0 8px 0;">
        <p style="margin: 0 0 14px 0;">
            Na Vašich stránkách jsme detekovali <strong>{pocet}</strong>,
            což samo o&nbsp;sobě <strong>není žádný problém</strong>&nbsp;—
            ba naopak, využívání AI je dnes konkurenční výhoda.
        </p>
        <p style="margin: 0;">
            Jen je potřeba mít připravenou <strong>kompletní dokumentaci</strong>
            podle pravidel EU a&nbsp;informovat návštěvníky vašeho webu:
        </p>
    </div>"""


def _compliance_checklist() -> str:
    """Vyčerpávající seznam compliance povinností — zelené fajfky."""
    items = [
        "Transparentní <strong>AI banner / oznámení</strong> na webu viditelné pro každého návštěvníka",
        "Samostatnou <strong>stránku s&nbsp;informacemi</strong> o&nbsp;všech využívaných AI systémech (AI disclosure page)",
        "Kompletní <strong>dokumentaci všech AI systémů</strong> včetně popisu účelu, vstupních a&nbsp;výstupních dat",
        "<strong>Posouzení rizik</strong> (risk assessment) pro každý jednotlivý AI systém",
        "Evidenci <strong>zpracování dat</strong> v&nbsp;souvislosti s&nbsp;AI systémy",
        "Zavedení mechanismu <strong>lidského dohledu</strong> (human oversight) nad AI systémy",
        "Možnost <strong>eskalace komunikace</strong> s&nbsp;AI na lidského operátora",
        "<strong>Technickou dokumentaci</strong> AI systémů dle přílohy&nbsp;IV AI Act",
        "Záznam o&nbsp;<strong>školení zaměstnanců</strong> v&nbsp;oblasti AI gramotnosti (<a href='https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689#art_4' style='color: {BRAND['accent']}; text-decoration: underline;'>čl.&nbsp;4 AI Act</a>)",
        "Listinnou / archivní podobu <strong>compliance dokumentace</strong>",
        "Postup pro <strong>hlášení incidentů</strong> souvisejících s&nbsp;AI",
        "<strong>Audit trail</strong> / logování rozhodnutí AI systémů",
        "Aktualizaci <strong>cookie banneru a&nbsp;privacy policy</strong> o&nbsp;AI systémy",
        "Registraci <strong>vysokorizikových AI systémů</strong> v&nbsp;EU databázi (pokud je to relevantní)",
        "<strong>Akční plán</strong> s&nbsp;konkrétními kroky a&nbsp;termíny pro dosažení souladu",
        "Průběžný <strong>monitoring a&nbsp;evidenci</strong> nově přidaných AI nástrojů",
    ]

    rows = ""
    for item in items:
        rows += f"""
                    <tr>
                        <td style="padding: 4px 10px 4px 0; vertical-align: top; width: 28px;">
                            <span style="display: inline-block; width: 22px; height: 22px; border-radius: 50%; background: #dcfce7; text-align: center; line-height: 22px; font-size: 13px; color: #15803d; font-weight: 700;">&#10003;</span>
                        </td>
                        <td style="padding: 4px 0; font-size: 14px; line-height: 1.5; color: {BRAND['text']};">
                            {item}
                        </td>
                    </tr>"""

    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="margin: 20px 0;">
        <tr>
            <td style="padding: 20px 22px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; border-left: 4px solid {BRAND['success']};">
                <p style="margin: 0 0 14px 0; font-size: 15px; font-weight: 700; color: #166534;">
                    &#9989; Co vše musíte dle AI Act zajistit
                </p>
                <p style="margin: 0 0 12px 0; font-size: 14px; color: {BRAND['text']};">
                    Dle <a href="{AI_ACT_FULL_URL}" style="color: {BRAND['accent']}; text-decoration: underline;">Nařízení (EU) 2024/1689</a> musíte mimo jiné zajistit:
                </p>
                <table cellpadding="0" cellspacing="0" width="100%">
                    {rows}
                </table>
                <p style="margin: 14px 0 0 0; font-size: 14px; color: {BRAND['text']}; font-style: italic;">
                    Vím, že to vypadá jako hodně práce&nbsp;— a&nbsp;upřímně, <strong>je</strong>.
                </p>
            </td>
        </tr>
    </table>"""


def _deliverables_panel() -> str:
    """Pozitivní pivot — co vše AIshield dodá."""
    items = [
        ("<strong>Kompletní diagnostiku</strong> webu", "Automatický sken všech AI systémů na vašich stránkách"),
        ("<strong>Inventář AI nástrojů</strong>", "Přehledný výpis s&nbsp;klasifikací rizik dle AI Act"),
        ("<strong>Hotovou compliance dokumentaci</strong> v&nbsp;PDF", "AI Policy, Transparency Notices, AI Registr"),
        ("<strong>AI banner / oznámení</strong>", "Připravené k&nbsp;okamžitému nasazení na váš web"),
        ("<strong>Samostatnou transparenční stránku</strong>", "HTML stránka s&nbsp;informacemi o&nbsp;AI pro vaše návštěvníky"),
        ("<strong>Záznamy o&nbsp;školení</strong>", "Dokumentace AI gramotnosti pro zaměstnance (čl.&nbsp;4)"),
        ("<strong>Kompletní akční plán</strong>", "Konkrétní kroky s&nbsp;termíny — přesně co, kdy a&nbsp;jak"),
        ("<strong>Dotazník interních AI systémů</strong>", "Pomůžeme zmapovat i&nbsp;AI, které scanner nevidí (HR, ERP…)"),
        ("<strong>Průběžný monitoring</strong> a&nbsp;alerting", "Automatické sledování nových AI nástrojů na webu"),
        ("<strong>Widget pro váš web</strong>", "Vizuální prvek informující návštěvníky o&nbsp;AI compliance"),
    ]

    rows = ""
    for title, desc in items:
        rows += f"""
                    <tr>
                        <td style="padding: 5px 10px 5px 0; vertical-align: top; width: 24px;">
                            <span style="font-size: 16px;">&#10132;</span>
                        </td>
                        <td style="padding: 5px 0; font-size: 14px; line-height: 1.5; color: {BRAND['text']};">
                            {title}<br>
                            <span style="font-size: 12px; color: {BRAND['text_light']};">{desc}</span>
                        </td>
                    </tr>"""

    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="margin: 24px 0;">
        <tr>
            <td style="padding: 22px; background: linear-gradient(135deg, #f0f9ff, #e0f2fe); border: 1px solid #7dd3fc; border-radius: 8px; border-left: 4px solid #0284c7;">
                <p style="margin: 0 0 6px 0; font-size: 18px; font-weight: 700; color: #0c4a6e;">
                    &#127881; Od toho jsme tady ale teď my!
                </p>
                <p style="margin: 0 0 16px 0; font-size: 15px; color: {BRAND['text']};">
                    <strong>Nemusíte se o&nbsp;nic starat.</strong>
                    Vše vyřešíme za Vás — kompletně, na klíč:
                </p>
                <table cellpadding="0" cellspacing="0" width="100%">
                    {rows}
                </table>
            </td>
        </tr>
    </table>"""


def _empathy_banner() -> str:
    """Empatie banner — soustřeďte se na byznys."""
    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="margin: 20px 0;">
        <tr>
            <td style="padding: 18px 22px; background: linear-gradient(135deg, #f5f3ff, #ede9fe); border: 1px solid #c4b5fd; border-radius: 8px; text-align: center;">
                <p style="margin: 0 0 6px 0; font-size: 24px;">&#128170;</p>
                <p style="margin: 0 0 6px 0; font-size: 16px; font-weight: 700; color: {BRAND['accent']};">
                    Chápeme, že se potřebujete soustředit na svůj byznys, ne na byrokracii EU.
                </p>
                <p style="margin: 0; font-size: 14px; color: {BRAND['text_light']};">
                    My rádi pomůžeme — zatímco se Vy budete věnovat tomu, co umíte nejlépe.
                </p>
            </td>
        </tr>
    </table>"""


def _deadline_box() -> str:
    """Deadline box s odpočítáváním — ČERVENÝ."""
    days = _days_to_deadline()

    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="margin: 24px 0;">
        <tr>
            <td style="padding: 16px 20px; background: linear-gradient(135deg, #fef2f2, #fee2e2); border: 1px solid #fca5a5; border-radius: 8px; border-left: 4px solid {BRAND['danger']};">
                <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                        <td style="font-size: 28px; width: 40px; vertical-align: top; padding-right: 12px;">&#9200;</td>
                        <td>
                            <p style="margin: 0 0 4px 0; font-size: 15px; font-weight: 700; color: #991b1b;">
                                Deadline: 2. srpna 2026
                            </p>
                            <p style="margin: 0; font-size: 13px; color: #b91c1c;">
                                Do plné účinnosti AI Act zbývá <strong style="font-size: 15px; color: #991b1b;">{days} dní</strong>.
                                Příprava compliance dokumentace zabere cca 2–4 týdny.
                                <strong>Nenechávejte to na poslední chvíli.</strong>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>"""


def _cta_button() -> str:
    """CTA tlačítko → ceník/nabídka na webu."""
    cta_link = "https://aishield.cz/#pricing"

    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="margin: 24px 0;">
        <tr>
            <td align="center">
                <!--[if mso]>
                <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml"
                    href="{cta_link}" style="height:48px;v-text-anchor:middle;width:300px;"
                    arcsize="17%" fillcolor="{BRAND['accent']}">
                <center style="color:#ffffff;font-family:Arial;font-size:15px;font-weight:bold;">
                    Zobrazit nabídku řešení &rarr;
                </center>
                </v:roundrect>
                <![endif]-->
                <!--[if !mso]><!-->
                <a href="{cta_link}"
                   style="display: inline-block; padding: 14px 36px; background: {BRAND['accent']};
                          color: #ffffff; font-size: 15px; font-weight: 600; text-decoration: none;
                          border-radius: 8px; letter-spacing: 0.3px;">
                    Zobrazit nabídku řešení &#8594;
                </a>
                <!--<![endif]-->
            </td>
        </tr>
    </table>"""


def _header_html(company_url: str) -> str:
    """Hlavička s logem a brand barvami."""
    return f"""
    <table width="100%" cellpadding="0" cellspacing="0"
           style="background: linear-gradient(135deg, {BRAND['gradient_start']}, {BRAND['gradient_mid']}, {BRAND['gradient_end']});
                  border-radius: 8px 8px 0 0; margin-bottom: 0;">
        <tr>
            <td style="padding: 24px 28px;">
                <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                        <td>
                            <a href="https://aishield.cz" style="text-decoration: none;">
                                <span style="font-size: 22px; font-weight: 700; color: #ffffff; letter-spacing: -0.5px;">
                                    &#128737; AIshield.cz
                                </span>
                            </a>
                            <br>
                            <span style="font-size: 12px; color: #a5b4fc; letter-spacing: 0.5px;">
                                AI Act compliance pro české firmy
                            </span>
                        </td>
                        <td style="text-align: right; vertical-align: middle;">
                            <span style="font-size: 12px; color: #a5b4fc;">
                                {_current_date_cs()}
                            </span>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>"""


def _footer_html(company_url: str, to_email: str = "") -> str:
    """Profesionální footer s Desperados Design."""
    unsubscribe = ""
    if to_email:
        unsubscribe = f'https://api.aishield.cz/api/unsubscribe?email={quote(to_email)}&company={quote(company_url)}'

    unsub_link = ""
    if unsubscribe:
        unsub_link = f"""
            <p style="margin: 10px 0 0 0; font-size: 11px;">
                <a href="{unsubscribe}" style="color: #94a3b8; text-decoration: underline;">Odhlásit se z upozornění</a>
            </p>"""

    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="margin-top: 32px; border-top: 2px solid {BRAND['border']};">
        <tr>
            <td style="padding: 24px 0 0 0;">
                <!-- Kontakt -->
                <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 16px;">
                    <tr>
                        <td>
                            <p style="margin: 0 0 6px 0; font-size: 14px; font-weight: 700; color: {BRAND['text']};">
                                Bc. Martin Haynes
                            </p>
                            <p style="margin: 0 0 4px 0; font-size: 13px; color: {BRAND['text_light']};">
                                Zakladatel &amp; CEO,
                                <a href="https://aishield.cz" style="color: {BRAND['accent']}; text-decoration: underline;">AIshield.cz</a>
                            </p>
                        </td>
                    </tr>
                </table>

                <!-- Kontaktní údaje -->
                <table cellpadding="0" cellspacing="0" style="font-size: 13px; color: {BRAND['text_light']}; line-height: 1.8;">
                    <tr>
                        <td style="padding-right: 6px;">&#128222;</td>
                        <td><a href="tel:+420732716141" style="color: {BRAND['text_light']}; text-decoration: none;">+420 732 716 141</a></td>
                    </tr>
                    <tr>
                        <td style="padding-right: 6px;">&#9993;</td>
                        <td><a href="mailto:info@aishield.cz" style="color: {BRAND['accent']}; text-decoration: underline;">info@aishield.cz</a></td>
                    </tr>
                    <tr>
                        <td style="padding-right: 6px;">&#127760;</td>
                        <td><a href="https://aishield.cz" style="color: {BRAND['accent']}; text-decoration: underline;">aishield.cz</a></td>
                    </tr>
                </table>

                <!-- Desperados Design -->
                <p style="margin: 16px 0 0 0; font-size: 11px; color: #94a3b8; line-height: 1.5; border-top: 1px solid {BRAND['border']}; padding-top: 12px;">
                    <a href="https://aishield.cz" style="color: #94a3b8; text-decoration: underline;">AIshield.cz</a>
                    je projekt společnosti
                    <a href="https://www.desperados-design.cz" style="color: #94a3b8; text-decoration: underline;">Desperados Design</a>
                    &middot; IČO: 17889251 &middot; Mlýnská 53, 783 53 Velká Bystřice
                </p>
                <p style="margin: 6px 0 0 0; font-size: 11px; color: #94a3b8;">
                    Jednorázové upozornění na základě veřejně dostupné analýzy webu {company_url}.
                </p>
                {unsub_link}
            </td>
        </tr>
    </table>"""


def build_hybrid_email(
    vocative_name: str,
    company_url: str,
    company_name: str,
    findings: list[FindingRow],
    screenshot_url: str = "",
    scan_id: str = "",
    to_email: str = "",
) -> str:
    """
    Sestaví TEMPLATE-DRIVEN email v5.
    Gemini dodává POUZE vocative_name (skloněné jméno).
    Vše ostatní je šablona.
    """
    header = _header_html(company_url)
    intro = _intro_section(vocative_name, company_url, company_name, len(findings))
    penalty = _penalty_panel()
    findings_intro = _findings_intro(len(findings))
    risk_table = _risk_table_html(findings)
    screenshot = _screenshot_section(screenshot_url, company_url)
    checklist = _compliance_checklist()
    deliverables = _deliverables_panel()
    empathy = _empathy_banner()
    deadline = _deadline_box()
    cta = _cta_button()
    footer = _footer_html(company_url, to_email)

    return f"""<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIshield.cz — upozornění na AI Act</title>
    <!--[if mso]>
    <style>
        table {{ border-collapse: collapse; }}
        td {{ font-family: Arial, sans-serif; }}
    </style>
    <![endif]-->
</head>
<body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">

<!-- Outer wrapper -->
<table width="100%" cellpadding="0" cellspacing="0" style="background: #f1f5f9; padding: 20px 0;">
    <tr>
        <td align="center">
            <!-- Email container -->
            <table width="600" cellpadding="0" cellspacing="0"
                   style="max-width: 600px; width: 100%; background: {BRAND['bg']};
                          border-radius: 8px; overflow: hidden;
                          box-shadow: 0 1px 3px rgba(0,0,0,0.1);">

                <!-- HEADER -->
                <tr>
                    <td>{header}</td>
                </tr>

                <!-- BODY -->
                <tr>
                    <td style="padding: 28px 28px 0 28px;">

                        <!-- 1. Úvod (ŠABLONA) -->
                        {intro}

                        <!-- 2. Panel s pokutami -->
                        {penalty}

                        <!-- 3. Intro k nálezům -->
                        {findings_intro}

                        <!-- 4. Screenshot -->
                        {screenshot}

                        <!-- 5. Tabulka rizik -->
                        {risk_table}

                        <!-- 6. Compliance checklist -->
                        {checklist}

                        <!-- 7. Co dodáme — pozitivní pivot -->
                        {deliverables}

                        <!-- 8. Empatie banner -->
                        {empathy}

                        <!-- 9. Deadline (ČERVENÝ) -->
                        {deadline}

                        <!-- 10. CTA → ceník -->
                        {cta}

                        <!-- 11. Footer -->
                        {footer}

                    </td>
                </tr>

            </table>
            <!-- /Email container -->
        </td>
    </tr>
</table>
<!-- /Outer wrapper -->

</body>
</html>"""


def get_followup_email(
    company_name: str,
    company_url: str,
    days_since: int,
    to_email: str = "",
    scan_id: str = "",
) -> EmailVariant:
    """Follow-up email."""
    days = _days_to_deadline()
    header = _header_html(company_url)
    cta = _cta_button()
    footer = _footer_html(company_url, to_email)

    body_html = f"""<!DOCTYPE html>
<html lang="cs">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background: #f1f5f9; padding: 20px 0;">
    <tr>
        <td align="center">
            <table width="600" cellpadding="0" cellspacing="0"
                   style="max-width: 600px; width: 100%; background: #fff;
                          border-radius: 8px; overflow: hidden;
                          box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <tr><td>{header}</td></tr>
                <tr>
                    <td style="padding: 28px;">
                        <div style="font-size: 15px; line-height: 1.65; color: {BRAND['text']};">
                            <p>Dobrý den,</p>
                            <p>před {days_since} dny jsem vám poslal upozornění k&nbsp;AI systémům
                                na webu <strong>{company_url}</strong>.</p>
                            <p>Chápu, že to nemusí být priorita — jen pro kontext:
                                do plné účinnosti AI Act zbývá <strong>{days} dní</strong>
                                a&nbsp;příprava compliance dokumentace nějaký čas zabere.</p>
                            <p>Nabídka řešení je stále k&nbsp;dispozici:</p>
                        </div>
                        {cta}
                        <div style="font-size: 14px; line-height: 1.65; color: {BRAND['text']};">
                            <p>Pokud to řešíte s&nbsp;někým jiným nebo to nepotřebujete,
                                klidně mě ignorujte — nebudu dál obtěžovat.</p>
                        </div>
                        {footer}
                    </td>
                </tr>
            </table>
        </td>
    </tr>
</table>
</body>
</html>"""

    return EmailVariant(
        subject=f"Doplnění k AI Act analýze webu {company_url}",
        body_html=body_html,
    )


# ── Zpětná kompatibilita ──
def get_outbound_email(
    company_name: str,
    company_url: str,
    findings_count: int,
    top_finding: str,
    variant: str = "A",
    to_email: str = "",
    screenshot_url: str = "",
    findings: list | None = None,
    scan_id: str = "",
) -> EmailVariant:
    """Fallback bez Gemini — používá šablonový úvod."""
    finding_rows = []
    if findings:
        for f in findings:
            if isinstance(f, dict):
                finding_rows.append(FindingRow(
                    name=f.get("name", ""),
                    category=f.get("category", ""),
                    risk_level=f.get("risk_level", "limited"),
                    ai_act_article=f.get("ai_act_article", "čl. 50"),
                    description=f.get("description", ""),
                ))

    html = build_hybrid_email(
        vocative_name="",
        company_url=company_url,
        company_name=company_name,
        findings=finding_rows,
        screenshot_url=screenshot_url,
        scan_id=scan_id,
        to_email=to_email,
    )

    return EmailVariant(
        subject="Oznámení o hrozícím porušení pravidel na vašem webu dle nařízení EU",
        body_html=html,
        variant_id=variant,
    )
