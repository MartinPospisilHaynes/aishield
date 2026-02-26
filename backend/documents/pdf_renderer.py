"""
AIshield.cz — PDF Renderer (v1)

Minimální CSS wrapper pro HTML obsah generovaný LLM.
Žádný hardcoded obsah — pouze profesionální styling pro tisk.
LLM generuje kompletní HTML tělo, renderer přidá:
  - A4 page setup s hlavičkou a patičkou
  - Profesionální typografie (Inter)
  - Tabulky, seznamy, badge systém, zvýraznění
  - Podpisové bloky
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════
# UNIFIED CSS — profesionální print design
# ══════════════════════════════════════════════════════════════════════

UNIFIED_CSS = """
/* ── Fonty ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Stránka ── */
@page {
    size: A4;
    margin: 22mm 18mm 25mm 18mm;
    @top-center {
        content: "AIshield.cz | AI Act Compliance Kit";
        font-family: 'Inter', sans-serif;
        font-size: 8pt;
        color: #94a3b8;
    }
    @bottom-left {
        content: "Důvěrné — pouze pro interní potřebu";
        font-family: 'Inter', sans-serif;
        font-size: 7pt;
        color: #94a3b8;
    }
    @bottom-right {
        content: "Strana " counter(page) " / " counter(pages);
        font-family: 'Inter', sans-serif;
        font-size: 8pt;
        color: #64748b;
    }
}

/* ── Základ ── */
body {
    font-family: 'Inter', sans-serif;
    font-size: 10pt;
    line-height: 1.5;
    color: #1e293b;
    max-width: 170mm;
    margin: 0 auto;
}

/* ── Nadpisy ── */
h1 {
    font-size: 20pt;
    font-weight: 700;
    color: #0f172a;
    margin-top: 0;
    margin-bottom: 10pt;
    padding-bottom: 5pt;
    border-bottom: 3pt solid #7c3aed;
    page-break-after: avoid;
    break-after: avoid;
}
h2 {
    font-size: 13pt;
    font-weight: 600;
    color: #1e293b;
    margin-top: 16pt;
    margin-bottom: 6pt;
    padding-bottom: 3pt;
    border-bottom: 1pt solid #e2e8f0;
    page-break-after: avoid;
    break-after: avoid;
}
h3 {
    font-size: 11pt;
    font-weight: 600;
    color: #334155;
    margin-top: 12pt;
    margin-bottom: 5pt;
    page-break-after: avoid;
    break-after: avoid;
}
h4 {
    font-size: 10pt;
    font-weight: 600;
    color: #475569;
    margin-top: 10pt;
    margin-bottom: 4pt;
}

/* ── Odstavce ── */
p {
    margin-top: 3pt;
    margin-bottom: 6pt;
    text-align: justify;
    orphans: 3;
    widows: 3;
}

/* ── Seznamy ── */
ul, ol {
    margin: 4pt 0;
    padding-left: 18pt;
}
li {
    margin-bottom: 3pt;
}
ul li {
    list-style-type: none;
    position: relative;
    padding-left: 2pt;
}
ul li::before {
    content: "•";
    color: #7c3aed;
    font-weight: 700;
    position: absolute;
    left: -14pt;
}

/* ── Tabulky ── */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 8pt 0;
    font-size: 9pt;
    /* page-break-inside: auto — allow large tables to break across pages */
}
thead {
    display: table-header-group;  /* repeat header on each page */
}
tr {
    page-break-inside: avoid;  /* keep individual rows together */
}
th {
    background-color: #f1f5f9;
    font-weight: 600;
    text-align: left;
    padding: 6pt 8pt;
    border-bottom: 2pt solid #cbd5e1;
    color: #334155;
}
td {
    padding: 5pt 8pt;
    border-bottom: 1pt solid #e2e8f0;
    vertical-align: top;
}
tr:nth-child(even) td {
    background-color: #f8fafc;
}

/* ── Risk badge systém ── */
.badge {
    display: inline-block;
    padding: 1pt 8pt;
    border-radius: 3pt;
    font-size: 8.5pt;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.3pt;
}
.badge-high, .badge-vysoke {
    background-color: #fef2f2;
    color: #dc2626;
    border: 1pt solid #fecaca;
}
.badge-limited, .badge-omezene {
    background-color: #fffbeb;
    color: #d97706;
    border: 1pt solid #fde68a;
}
.badge-minimal, .badge-minimalni {
    background-color: #f0fdf4;
    color: #16a34a;
    border: 1pt solid #bbf7d0;
}

/* ── Zvýrazněný box ── */
.highlight, .callout {
    background-color: #f5f3ff;
    border-left: 4pt solid #7c3aed;
    padding: 10pt 14pt;
    margin: 12pt 0;
    border-radius: 0 4pt 4pt 0;
}
.warning {
    background-color: #fffbeb;
    border-left: 4pt solid #f59e0b;
    padding: 10pt 14pt;
    margin: 12pt 0;
    border-radius: 0 4pt 4pt 0;
}
.info {
    background-color: #eff6ff;
    border-left: 4pt solid #3b82f6;
    padding: 10pt 14pt;
    margin: 12pt 0;
    border-radius: 0 4pt 4pt 0;
}

/* ── Podpisový blok ── */
.sig-block {
    margin-top: 30pt;
    display: flex;
    gap: 40pt;
    page-break-inside: avoid;
}
.sig-field {
    flex: 1;
    border-top: 1pt solid #94a3b8;
    padding-top: 6pt;
    font-size: 9pt;
    color: #64748b;
    text-align: center;
}

/* ── Semaphore ── */
.semaphore {
    display: inline-block;
    width: 14pt;
    height: 14pt;
    border-radius: 50%;
    vertical-align: middle;
    margin-right: 6pt;
}
.semaphore-red { background-color: #dc2626; }
.semaphore-orange { background-color: #f59e0b; }
.semaphore-green { background-color: #16a34a; }

/* ── Metric grid ── */
.metric-grid {
    display: flex;
    gap: 12pt;
    margin: 12pt 0;
}
.metric-card {
    flex: 1;
    text-align: center;
    padding: 10pt;
    background: #f8fafc;
    border-radius: 4pt;
    border: 1pt solid #e2e8f0;
}
.metric-value {
    font-size: 24pt;
    font-weight: 700;
    color: #7c3aed;
}
.metric-label {
    font-size: 8pt;
    color: #64748b;
    text-transform: uppercase;
}

/* ── Stránkování ── */
.page-break { page-break-before: always; }
.no-break { page-break-inside: avoid; }

/* ── Ochrana proti osiřelým nadpisům ── */
h1 + table, h1 + p, h1 + ul, h1 + ol, h1 + div, h1 + dl,
h2 + table, h2 + p, h2 + ul, h2 + ol, h2 + div, h2 + dl,
h3 + table, h3 + p, h3 + ul, h3 + ol, h3 + div, h3 + dl {
    page-break-before: avoid;
    break-before: avoid;
}

/* ── Sekce ── */
.section {
    page-break-before: always;
    padding-top: 10pt;
}
.section:first-child {
    page-break-before: avoid;
}

/* ── Footer poznámka ── */
.doc-footer {
    margin-top: 30pt;
    padding-top: 10pt;
    border-top: 1pt solid #e2e8f0;
    font-size: 8pt;
    color: #94a3b8;
    text-align: center;
}
"""


# ══════════════════════════════════════════════════════════════════════
# VOP — Všeobecné obchodní podmínky (business terms)
# ══════════════════════════════════════════════════════════════════════

VOP_HTML = """
<div class="section">
<h1>Všeobecné obchodní podmínky</h1>

<h2>1. Poskytovatel</h2>
<p>AIshield.cz je služba provozovaná za účelem poskytování AI Act compliance
dokumentace a souvisejících nástrojů pro české podnikatele a firmy.</p>

<h2>2. Předmět služby</h2>
<p>Předmětem služby je vypracování sady dokumentů (AI Act Compliance Kit)
na základě analýzy AI systémů používaných klientem. Dokumentace slouží jako
technická pomůcka a podpůrný materiál pro dosažení souladu s Nařízením (EU) 2024/1689
o umělé inteligenci (AI Act).</p>

<h2>3. Povaha dokumentace</h2>
<p>Dodaná dokumentace <strong>nepředstavuje právní poradenství</strong> ve smyslu
zákona č. 85/1996 Sb., o advokacii. Jedná se o technickou analýzu a návrh podkladů,
které by měl klient konzultovat s kvalifikovaným právním poradcem. AIshield.cz
nenese odpovědnost za právní rozhodnutí učiněná na základě těchto dokumentů.</p>

<h2>4. Metodologie</h2>
<p>Analýza je provedena kombinací automatizovaného webového skenu, dotazníkového šetření
a zpracování výsledků s využitím nástrojů umělé inteligence. Generované texty jsou
zpracovány odborným týmem s využitím AI nástrojů a ověřeny proti aktuálnímu znění
AI Act a souvisejících předpisů.</p>

<h2>5. Platnost a aktualizace</h2>
<p>Dokumentace odráží stav k datu vyhotovení. EU AI Act i výkladová praxe se průběžně
vyvíjí. Doporučujeme provést aktualizaci vždy, když dojde k podstatné změně
používaných AI systémů, organizační struktury nebo právního rámce.</p>

<h2>6. Důvěrnost</h2>
<p>Veškeré informace poskytnuté klientem jsou považovány za důvěrné a jsou zpracovávány
v souladu s GDPR. Data jsou uložena na zabezpečených serverech s šifrováním a nejsou
sdílena s třetími stranami bez souhlasu klienta.</p>

<h2>7. Odpovědnost</h2>
<p>AIshield.cz vynakládá maximální úsilí na přesnost a aktuálnost poskytovaných informací.
Odpovědnost za škody vzniklé v důsledku použití dokumentace je omezena na výši uhrazené
ceny služby. AIshield.cz neodpovídá za škody vzniklé v důsledku nesprávné implementace
doporučení klientem nebo za rozhodnutí regulatorních orgánů.</p>

<h2>8. Reklamace</h2>
<p>Případné reklamace je možné uplatnit do 14 dnů od dodání dokumentace na adrese
info@aishield.cz. Reklamace bude posouzena a vyřízena do 30 dnů.</p>

<h2>9. Kontakt</h2>
<p>AIshield.cz<br>
E-mail: info@aishield.cz<br>
Web: https://aishield.cz</p>
</div>
"""


# ══════════════════════════════════════════════════════════════════════
# RENDERING FUNCTIONS
# ══════════════════════════════════════════════════════════════════════

def render_full_document(
    sections_html: dict,
    company_name: str,
    ico: str = "",
    overall_risk: str = "minimal",
    generated_date: str = "",
) -> str:
    """
    Sestaví kompletní HTML dokument ze sekcí generovaných LLM.

    Args:
        sections_html: dict {section_key: html_content} — finální HTML z Modulu 4
        company_name: název firmy
        ico: IČO firmy
        overall_risk: celkové riziko (high/limited/minimal)
        generated_date: datum generování

    Returns:
        Kompletní HTML dokument připravený pro WeasyPrint
    """
    if not generated_date:
        generated_date = datetime.now().strftime("%d. %m. %Y")

    risk_labels = {"high": "Vysoké", "limited": "Omezené", "minimal": "Minimální"}
    risk_label = risk_labels.get(overall_risk, "Minimální")
    risk_color = {"high": "red", "limited": "orange", "minimal": "green"}.get(overall_risk, "green")

    # Titulní strana
    title_html = f"""
    <div style="text-align:center; padding-top:120pt;">
        <p style="font-size:11pt; color:#7c3aed; text-transform:uppercase; letter-spacing:2pt; font-weight:600;">
            AIshield.cz
        </p>
        <h1 style="font-size:28pt; border:none; margin-top:20pt; padding-bottom:0;">
            AI Act Compliance Kit
        </h1>
        <p style="font-size:14pt; color:#475569; margin-top:10pt;">
            Kompletní dokumentace pro soulad s Nařízením (EU) 2024/1689
        </p>
        <div style="margin-top:40pt; padding:16pt; background:#f8fafc; border-radius:6pt; display:inline-block; text-align:left;">
            <table style="border:none; font-size:11pt;">
                <tr><td style="border:none; color:#64748b; padding:3pt 12pt 3pt 0;">Firma:</td>
                    <td style="border:none; font-weight:600; padding:3pt 0;">{company_name}</td></tr>
                <tr><td style="border:none; color:#64748b; padding:3pt 12pt 3pt 0;">IČO:</td>
                    <td style="border:none; padding:3pt 0;">{ico or '—'}</td></tr>
                <tr><td style="border:none; color:#64748b; padding:3pt 12pt 3pt 0;">Riziko:</td>
                    <td style="border:none; padding:3pt 0;">
                        <span class="semaphore semaphore-{risk_color}"></span> {risk_label}
                    </td></tr>
                <tr><td style="border:none; color:#64748b; padding:3pt 12pt 3pt 0;">Datum:</td>
                    <td style="border:none; padding:3pt 0;">{generated_date}</td></tr>
            </table>
        </div>
    </div>
    """

    # Obsah (TOC)
    section_names = {
        "compliance_report": "Compliance Report",
        "action_plan": "Akční plán",
        "ai_register": "Registr AI systémů",
        "training_outline": "Plán školení",
        "chatbot_notices": "Texty oznámení",
        "ai_policy": "Interní AI politika",
        "incident_response_plan": "Plán řízení incidentů",
        "dpia_template": "Posouzení dopadů (DPIA/FRIA)",
        "vendor_checklist": "Dodavatelský checklist",
        "monitoring_plan": "Monitoring plán",
        "transparency_human_oversight": "Transparentnost a lidský dohled",
    }

    toc_items = []
    for i, (key, name) in enumerate(section_names.items(), 1):
        if key in sections_html:
            toc_items.append(f"<li>{i}. {name}</li>")

    toc_html = f"""
    <div class="page-break"></div>
    <h1>Obsah</h1>
    <ol style="font-size:11pt; line-height:2.2;">
        {''.join(toc_items)}
        <li>{len(toc_items) + 1}. Všeobecné obchodní podmínky</li>
    </ol>
    """

    # Sekce
    body_parts = [title_html, toc_html]

    for key in section_names:
        if key in sections_html:
            html = sections_html[key]
            body_parts.append(f'<div class="section">{html}</div>')

    # VOP
    body_parts.append(VOP_HTML)

    # Footer
    body_parts.append(f"""
    <div class="doc-footer">
        Dokument vypracován odborným týmem AIshield.cz s využitím AI nástrojů |
        Datum: {generated_date} | {company_name}
    </div>
    """)

    body = "\n".join(body_parts)

    return f"""<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="utf-8">
    <title>AI Act Compliance Kit — {company_name}</title>
    <style>{UNIFIED_CSS}</style>
</head>
<body>
{body}
</body>
</html>"""


def render_section_html(section_key: str, section_html: str, company_name: str) -> str:
    """
    Renderuje jednu sekci jako standalone PDF.
    Používá se pro per-section PDF generování.
    """
    section_names = {
        "compliance_report": "Compliance Report",
        "action_plan": "Akční plán",
        "ai_register": "Registr AI systémů",
        "training_outline": "Plán školení",
        "chatbot_notices": "Texty oznámení",
        "ai_policy": "Interní AI politika",
        "incident_response_plan": "Plán řízení incidentů",
        "dpia_template": "Posouzení dopadů (DPIA/FRIA)",
        "vendor_checklist": "Dodavatelský checklist",
        "monitoring_plan": "Monitoring plán",
        "transparency_human_oversight": "Transparentnost a lidský dohled",
    }

    name = section_names.get(section_key, section_key)
    date = datetime.now().strftime("%d. %m. %Y")

    return f"""<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="utf-8">
    <title>{name} — {company_name}</title>
    <style>{UNIFIED_CSS}</style>
</head>
<body>
    <div style="margin-bottom:16pt; padding-bottom:8pt; border-bottom:2pt solid #7c3aed;">
        <span style="font-size:8pt; color:#7c3aed; text-transform:uppercase; letter-spacing:1pt;">
            AIshield.cz | AI Act Compliance Kit
        </span>
        <span style="float:right; font-size:8pt; color:#94a3b8;">{date}</span>
        <br>
        <span style="font-size:9pt; color:#64748b;">{company_name}</span>
    </div>
    {section_html}
    <div class="doc-footer">
        Dokument vypracován odborným týmem AIshield.cz s využitím AI nástrojů | {date}
    </div>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════════
# BACKWARD COMPATIBILITY — SECTION_RENDERERS dict
# ══════════════════════════════════════════════════════════════════════

# Minimální kompatibilita s pipeline.py, která volá SECTION_RENDERERS[key](data)
# V novém systému se tohle nepoužívá — pipeline volá render_section_html přímo

SECTION_KEYS = [
    "compliance_report", "action_plan", "ai_register", "training_outline",
    "chatbot_notices", "ai_policy", "incident_response_plan", "dpia_template",
    "vendor_checklist", "monitoring_plan", "transparency_human_oversight",
]

QUESTIONNAIRE_RISK_MAP = {
    "uses_ai_recruitment": "high",
    "uses_ai_credit_scoring": "high",
    "uses_ai_insurance": "high",
    "uses_ai_law_enforcement": "high",
    "uses_ai_border_control": "high",
    "uses_ai_justice": "high",
    "uses_ai_biometric_id": "high",
    "uses_ai_critical_infra": "high",
    "uses_ai_education": "high",
    "uses_ai_employment": "high",
    "uses_ai_public_services": "high",
    "uses_ai_medical_devices": "high",
    "uses_ai_vehicle_safety": "high",
    "uses_ai_chatbot": "limited",
    "uses_ai_emotion_recognition": "limited",
    "uses_ai_biometric_categorization": "limited",
    "uses_ai_content_generation": "limited",
    "uses_ai_image_manipulation": "limited",
    "uses_ai_translation": "minimal",
    "uses_ai_spam_filter": "minimal",
    "uses_ai_search_optimization": "minimal",
    "uses_ai_grammar_check": "minimal",
    "uses_ai_data_analytics": "minimal",
    "uses_ai_inventory": "minimal",
    "uses_ai_scheduling": "minimal",
    "uses_ai_code_assistant": "minimal",
    "uses_ai_document_processing": "minimal",
    "uses_ai_internal_chatbot": "minimal",
}
