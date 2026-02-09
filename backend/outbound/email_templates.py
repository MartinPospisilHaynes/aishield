"""
AIshield.cz — Email Templates v6 (TEMPLATE-DRIVEN)
Čistě šablonový email — bez AI generování textu.

Změny oproti v5:
- Nový předmět a popis v headeru
- Přepracovaný úvod ("já jsem", končí "pochybení:")
- Bez tučného písma (<strong>) — vypadalo AI-generovaně
- Odkazy ve firemní barvě bez podtržení
- Přeuspořádané sekce: nálezy hned po úvodu, pak pokuty
- Bez levých barevných linek u panelů
- Nový nadpis deliverables, odstraněn Widget
- SVG ikona místo emoji v empathy banneru
- Tmavě modrý footer (jako header), centrovaný, bílé písmo
- Disclaimer o spamu vrácen, adresa odstraněna
"""

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote


@dataclass
class EmailVariant:
    """Email varianta pro odeslání."""
    subject: str
    body_html: str
    variant_id: str = "template_v6"


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

# Stav = buď je to neoznačeno (porušení), nebo zakázáno (vážné porušení)
STATUS_BADGE = {
    "default": {
        "color": "#92400e",
        "bg": "#fef3c7",
        "label": "Neoznačeno",
        "icon": "⚠️",
    },
    "prohibited": {
        "color": "#7f1d1d",
        "bg": "#fecaca",
        "label": "Zakázaný systém",
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
    url = AI_ACT_ARTICLE_URLS.get(article)
    if url:
        return f'<a href="{url}" style="color: {BRAND["accent"]}; text-decoration: none;">{article} AI Act</a>'

    import re
    m = re.search(r'(\d+)', article)
    if m:
        num = m.group(1)
        key = f"čl. {num}"
        url = AI_ACT_ARTICLE_URLS.get(key)
        if url:
            return f'<a href="{url}" style="color: {BRAND["accent"]}; text-decoration: none;">{article}</a>'

    return f'<a href="{AI_ACT_FULL_URL}" style="color: {BRAND["accent"]}; text-decoration: none;">{article}</a>'


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
        if len(finding.description) < 120:
            return finding.description
    return LAYMAN_DESCRIPTIONS.get(finding.category, "AI systém detekovaný na vašem webu")


def _risk_table_html(findings: list[FindingRow]) -> str:
    """Tabulka rizik — jednoduchý jazyk, klikatelné články."""
    if not findings:
        return ""

    rows = ""
    for f in findings:
        badge = STATUS_BADGE["prohibited"] if f.risk_level == "prohibited" else STATUS_BADGE["default"]
        desc = _get_layman_desc(f)
        article_html = _article_link(f.ai_act_article)
        rows += f"""
            <tr>
                <td style="padding: 12px 16px; border-bottom: 1px solid #f1f5f9; font-size: 14px; color: {BRAND['text']};">
                    {f.name}
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
                <th style="padding: 10px 8px; text-align: center; font-size: 13px; font-weight: 600; color: {BRAND['text']}; border-bottom: 2px solid #e2e8f0;">Stav</th>
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
    Úvodní sekce emailu — ŠABLONA.
    Končí textem "pochybení:" — tabulka nálezů následuje hned za ní.
    """
    # Oslovení
    if vocative_name:
        greeting = f"Dobrý den {vocative_name},"
    else:
        greeting = "Dobrý den,"

    display_url = company_url.replace("https://www.", "").replace("http://www.", "").replace("https://", "").replace("http://", "").rstrip("/")

    return f"""
    <div style="font-size: 15px; line-height: 1.7; color: {BRAND['text']};">
        <p style="margin: 0 0 14px 0;">
            {greeting}
        </p>
        <p style="margin: 0 0 14px 0;">
            já jsem Martin Haynes, zakladatel
            <a href="https://aishield.cz" style="color: {BRAND['accent']}; text-decoration: none;">AIshield.cz</a>,
            a&nbsp;zaujal mě Váš web {display_url}.
        </p>
        <p style="margin: 0 0 14px 0;">
            Nemusíte se obávat, nic hrozného se zatím neděje.
            Jen jsme Vás chtěli upozornit, že při naší pravidelné kontrole
            webů a&nbsp;e-shopů jsme narazili na Váš web, který bude
            od 2.&nbsp;srpna 2026 nevyhovující po stránce legislativní
            kvůli zákonu Evropské unie a&nbsp;blížícímu se
            <a href="{AI_ACT_FULL_URL}" style="color: {BRAND['accent']}; text-decoration: none;">AI&nbsp;Act</a>.
            (Tak jak se před pár lety muselo rychle implementovat GDPR,
            dnes jsme v&nbsp;podobné situaci, jen kvůli umělé inteligenci.)
        </p>
        <p style="margin: 0 0 14px 0;">
            Jistě je Vám dobře známo, že k&nbsp;2.&nbsp;srpnu 2026
            vstupuje v&nbsp;plnou účinnost nové
            <a href="{AI_ACT_FULL_URL}" style="color: {BRAND['accent']}; text-decoration: none;">nařízení Evropské unie (AI Act)</a>,
            dle kterého musejí všechny webové stránky, e-shopy
            a&nbsp;aplikace informovat své uživatele o&nbsp;tom,
            zda&#8209;li a&nbsp;jak využívají umělou inteligenci na svých stránkách.
        </p>
        <p style="margin: 0 0 4px 0;">
            Bohužel&nbsp;— na vašem webu tyto informace zatím uvedeny nejsou.
            Byť náš software, podobný tomu, kterému budou webové stránky
            podrobovat i&nbsp;kontrolní úřady od 2.&nbsp;srpna 2026,
            zjistil tato pochybení:
        </p>
    </div>"""


def _penalty_panel() -> str:
    """Panel s pokutami — červený obdélník, BEZ levé linky."""
    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="margin: 20px 0;">
        <tr>
            <td style="padding: 18px 22px; background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px;">
                <p style="margin: 0 0 6px 0; font-size: 15px; font-weight: 700; color: #991b1b;">
                    &#9888;&#65039; Hrozící sankce za nesoulad s AI Act
                </p>
                <p style="margin: 0; font-size: 14px; line-height: 1.6; color: #7f1d1d;">
                    V&nbsp;případě nesplnění povinností hrozí pokuty až do výše
                    35&nbsp;milionů&nbsp;EUR nebo
                    7&nbsp;% celosvětového ročního obratu společnosti
                    (podle toho, která částka je vyšší).
                    Dozorový úřad může zahájit kontrolu kdykoliv po 2.&nbsp;srpnu 2026.
                </p>
            </td>
        </tr>
    </table>"""


def _compliance_checklist() -> str:
    """Vyčerpávající seznam compliance povinností — zelené fajfky, BEZ tučného písma, BEZ levé linky."""
    items = [
        "Transparentní AI banner / oznámení na webu viditelné pro každého návštěvníka",
        "Samostatnou stránku s&nbsp;informacemi o&nbsp;všech využívaných AI systémech (AI disclosure page)",
        "Kompletní dokumentaci všech AI systémů včetně popisu účelu, vstupních a&nbsp;výstupních dat",
        "Posouzení rizik (risk assessment) pro každý jednotlivý AI systém",
        "Evidenci zpracování dat v&nbsp;souvislosti s&nbsp;AI systémy",
        "Zavedení mechanismu lidského dohledu (human oversight) nad AI systémy",
        "Možnost eskalace komunikace s&nbsp;AI na lidského operátora",
        "Technickou dokumentaci AI systémů dle přílohy&nbsp;IV AI Act",
        f"Záznam o&nbsp;školení zaměstnanců v&nbsp;oblasti AI gramotnosti (<a href='https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689#art_4' style='color: {BRAND['accent']}; text-decoration: none;'>čl.&nbsp;4 AI Act</a>)",
        "Listinnou / archivní podobu compliance dokumentace",
        "Postup pro hlášení incidentů souvisejících s&nbsp;AI",
        "Audit trail / logování rozhodnutí AI systémů",
        "Aktualizaci cookie banneru a&nbsp;privacy policy o&nbsp;AI systémy",
        "Registraci vysokorizikových AI systémů v&nbsp;EU databázi (pokud je to relevantní)",
        "Akční plán s&nbsp;konkrétními kroky a&nbsp;termíny pro dosažení souladu",
        "Průběžný monitoring a&nbsp;evidenci nově přidaných AI nástrojů",
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
            <td style="padding: 20px 22px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px;">
                <p style="margin: 0 0 14px 0; font-size: 15px; font-weight: 700; color: #166534;">
                    &#9989; Co vše musíte dle AI Act zajistit
                </p>
                <p style="margin: 0 0 12px 0; font-size: 14px; color: {BRAND['text']};">
                    Dle <a href="{AI_ACT_FULL_URL}" style="color: {BRAND['accent']}; text-decoration: none;">Nařízení (EU) 2024/1689</a> musíte mimo jiné zajistit:
                </p>
                <table cellpadding="0" cellspacing="0" width="100%">
                    {rows}
                </table>
                <p style="margin: 14px 0 0 0; font-size: 14px; color: {BRAND['text']}; font-style: italic;">
                    Vím, že to vypadá jako hodně práce&nbsp;— a&nbsp;upřímně, je.
                </p>
            </td>
        </tr>
    </table>"""


def _deliverables_panel() -> str:
    """Pozitivní pivot — co vše AIshield dodá. BEZ levé linky, BEZ tučného písma."""
    items = [
        ("Kompletní diagnostiku webu", "Automatický sken všech AI systémů na vašich stránkách"),
        ("Inventář AI nástrojů", "Přehledný výpis s&nbsp;klasifikací rizik dle AI Act"),
        ("Hotovou compliance dokumentaci v&nbsp;PDF", "AI Policy, Transparency Notices, AI Registr"),
        ("AI banner / oznámení", "Připravené k&nbsp;okamžitému nasazení na váš web"),
        ("Samostatnou transparenční stránku", "HTML stránka s&nbsp;informacemi o&nbsp;AI pro vaše návštěvníky"),
        ("Záznamy o&nbsp;školení", "Dokumentace AI gramotnosti pro zaměstnance (čl.&nbsp;4)"),
        ("Kompletní akční plán", "Konkrétní kroky s&nbsp;termíny — přesně co, kdy a&nbsp;jak"),
        ("Dotazník interních AI systémů", "Pomůžeme zmapovat i&nbsp;AI, které scanner nevidí (HR, ERP…)"),
        ("Průběžný monitoring a&nbsp;alerting", "Automatické sledování nových AI nástrojů na webu"),
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
            <td style="padding: 22px; background: linear-gradient(135deg, #f0f9ff, #e0f2fe); border: 1px solid #7dd3fc; border-radius: 8px;">
                <p style="margin: 0 0 6px 0; font-size: 18px; font-weight: 700; color: #0c4a6e;">
                    &#127881; Od toho jsme tady teď kdo? Od toho jsme tady teď my.
                </p>
                <p style="margin: 0 0 16px 0; font-size: 15px; color: {BRAND['text']};">
                    Nemusíte se o&nbsp;nic starat.
                    Vše vyřešíme za Vás — kompletně, na klíč:
                </p>
                <table cellpadding="0" cellspacing="0" width="100%">
                    {rows}
                </table>
            </td>
        </tr>
    </table>"""


# SVG ikona štítu — data URI pro kompatibilitu s emailovými klienty
_SHIELD_SVG = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='36' height='36' "
    "viewBox='0 0 24 24'%3E%3Cpath d='M12 2L3 7v5c0 5.55 3.84 10.74 9 12 5.16-1.26 "
    "9-6.45 9-12V7l-9-5z' fill='%237c3aed'/%3E%3Cpath d='M10 15.5l-3.5-3.5 1.41-1.41L10 "
    "12.67l5.59-5.59L17 8.5l-7 7z' fill='%23ffffff'/%3E%3C/svg%3E"
)


def _empathy_banner() -> str:
    """Empatie banner — soustřeďte se na byznys. SVG ikona místo emoji."""
    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="margin: 20px 0;">
        <tr>
            <td style="padding: 18px 22px; background: linear-gradient(135deg, #f5f3ff, #ede9fe); border: 1px solid #c4b5fd; border-radius: 8px; text-align: center;">
                <p style="margin: 0 0 8px 0;">
                    <img src="{_SHIELD_SVG}" width="36" height="36" alt="&#128737;"
                         style="display: inline-block; vertical-align: middle;">
                </p>
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
    """Deadline box s odpočítáváním — ČERVENÝ, BEZ levé linky."""
    days = _days_to_deadline()

    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="margin: 24px 0;">
        <tr>
            <td style="padding: 16px 20px; background: linear-gradient(135deg, #fef2f2, #fee2e2); border: 1px solid #fca5a5; border-radius: 8px;">
                <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                        <td style="font-size: 28px; width: 40px; vertical-align: top; padding-right: 12px;">&#9200;</td>
                        <td>
                            <p style="margin: 0 0 4px 0; font-size: 15px; font-weight: 700; color: #991b1b;">
                                Deadline: 2. srpna 2026
                            </p>
                            <p style="margin: 0; font-size: 13px; color: #b91c1c;">
                                Do plné účinnosti AI Act zbývá
                                <span style="font-size: 15px; color: #991b1b; font-weight: 600;">{days} dní</span>.
                                Příprava compliance dokumentace zabere cca 2–4 týdny.
                                Nenechávejte to na poslední chvíli.
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
    """Hlavička s logem a novým popisem služby."""
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
                            <span style="font-size: 12px; color: #a5b4fc; letter-spacing: 0.3px; line-height: 1.5;">
                                Zajistíme, aby váš web splňoval blížící se normu evropské unie AI&nbsp;ACT,
                                která přichází v&nbsp;platnost 2.&nbsp;srpna 2026
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
    """Profesionální footer — tmavě modrý (jako header), centrovaný, bílé písmo."""
    unsubscribe = ""
    if to_email:
        unsubscribe = f'https://api.aishield.cz/api/unsubscribe?email={quote(to_email)}&company={quote(company_url)}'

    unsub_link = ""
    if unsubscribe:
        unsub_link = f"""
                <p style="margin: 10px 0 0 0; font-size: 11px;">
                    <a href="{unsubscribe}" style="color: #c7d2fe; text-decoration: none;">Odhlásit se z upozornění</a>
                </p>"""

    return f"""
    <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
            <td style="padding: 28px 24px; text-align: center;
                        background: linear-gradient(135deg, {BRAND['gradient_start']}, {BRAND['gradient_mid']}, {BRAND['gradient_end']});">

                <p style="margin: 0 0 6px 0; font-size: 14px; font-weight: 700; color: #ffffff;">
                    Bc. Martin Haynes
                </p>
                <p style="margin: 0 0 10px 0; font-size: 13px; color: #e0e7ff;">
                    Zakladatel &amp; CEO,
                    <a href="https://aishield.cz" style="color: #c7d2fe; text-decoration: none;">AIshield.cz</a>
                </p>

                <p style="margin: 0 0 4px 0; font-size: 13px; color: #e0e7ff;">
                    &#128222;
                    <a href="tel:+420732716141" style="color: #e0e7ff; text-decoration: none;">+420 732 716 141</a>
                </p>
                <p style="margin: 0 0 4px 0; font-size: 13px; color: #e0e7ff;">
                    &#9993;
                    <a href="mailto:info@aishield.cz" style="color: #c7d2fe; text-decoration: none;">info@aishield.cz</a>
                </p>
                <p style="margin: 0 0 12px 0; font-size: 13px; color: #e0e7ff;">
                    &#127760;
                    <a href="https://aishield.cz" style="color: #c7d2fe; text-decoration: none;">aishield.cz</a>
                </p>

                <p style="margin: 0 0 6px 0; font-size: 11px; color: #a5b4fc;">
                    <a href="https://aishield.cz" style="color: #a5b4fc; text-decoration: none;">AIshield.cz</a>
                    je projekt společnosti
                    <a href="https://www.desperados-design.cz" style="color: #a5b4fc; text-decoration: none;">Desperados Design</a>
                    &middot; IČO: 17889251
                </p>

                <p style="margin: 8px 0 0 0; font-size: 11px; color: #a5b4fc; line-height: 1.5;">
                    Tato zpráva není nevyžádaným obchodním sdělením (spam),
                    ale informativním upozorněním na základě automatické analýzy
                    veřejně přístupného obsahu vašeho webu v&nbsp;rámci veřejného zájmu
                    na dodržování evropské legislativy.
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
    Sestaví TEMPLATE-DRIVEN email v6.
    Pořadí: úvod → nálezy → screenshot → pokuty → checklist →
            deliverables → empatie → deadline → CTA → footer.
    """
    header = _header_html(company_url)
    intro = _intro_section(vocative_name, company_url, company_name, len(findings))
    risk_table = _risk_table_html(findings)
    screenshot = _screenshot_section(screenshot_url, company_url)
    penalty = _penalty_panel()
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
                    <td style="padding: 28px;">

                        <!-- 1. Úvod (končí "pochybení:") -->
                        {intro}

                        <!-- 2. Tabulka rizik (hned po úvodu) -->
                        {risk_table}

                        <!-- 3. Screenshot (volitelný) -->
                        {screenshot}

                        <!-- 4. Panel s pokutami -->
                        {penalty}

                        <!-- 5. Compliance checklist -->
                        {checklist}

                        <!-- 6. Co dodáme — pozitivní pivot -->
                        {deliverables}

                        <!-- 7. Empatie banner -->
                        {empathy}

                        <!-- 8. Deadline (ČERVENÝ) -->
                        {deadline}

                        <!-- 9. CTA → ceník -->
                        {cta}

                    </td>
                </tr>

                <!-- FOOTER (tmavě modrý, full-width) -->
                <tr>
                    <td>{footer}</td>
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
                                na webu {company_url}.</p>
                            <p>Chápu, že to nemusí být priorita — jen pro kontext:
                                do plné účinnosti AI Act zbývá {days} dní
                                a&nbsp;příprava compliance dokumentace nějaký čas zabere.</p>
                            <p>Nabídka řešení je stále k&nbsp;dispozici:</p>
                        </div>
                        {cta}
                        <div style="font-size: 14px; line-height: 1.65; color: {BRAND['text']};">
                            <p>Pokud to řešíte s&nbsp;někým jiným nebo to nepotřebujete,
                                klidně mě ignorujte — nebudu dál obtěžovat.</p>
                        </div>
                    </td>
                </tr>
                <tr><td>{footer}</td></tr>
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
    """Fallback bez vocative — používá šablonový úvod."""
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
        subject="Upozornění na riziko porušení pravidel evropské legislativy na vašem webu",
        body_html=html,
        variant_id=variant,
    )
