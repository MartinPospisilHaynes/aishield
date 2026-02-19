"""
AIshield.cz — Unified PDF Generator
Jeden velký PDF dokument = AI Act Compliance Kit.

Struktura:
  1. Titulní strana (firma, logo, datum)
  2. Obsah s čísly stránek
  3. Sekce dokumentů (podmíněně dle rizikového profilu)
  4. VOP na konci

Design: SVĚTLÝ / tiskový (žádný dark mode), viditelné checkboxy ☐,
        bez placeholderů — reálné české popisky.
"""

import logging
from datetime import datetime, timezone

from backend.documents.templates import (
    TEMPLATE_RENDERERS,
    TEMPLATE_NAMES,
    _now_str,
    _days_until_deadline,
    _risk_badge,
)

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════
# PRINT-FRIENDLY CSS — světlý styl pro tisk a vazbu
# ══════════════════════════════════════════════════════════════════════

UNIFIED_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    @page {
        size: A4;
        margin: 22mm 20mm 25mm 20mm;
        @bottom-center {
            content: counter(page);
            font-size: 9px;
            color: #94a3b8;
            font-family: 'Inter', sans-serif;
        }
        @bottom-right {
            content: "AIshield.cz";
            font-size: 8px;
            color: #c084fc;
            font-family: 'Inter', sans-serif;
        }
    }

    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
        font-family: 'Inter', -apple-system, sans-serif;
        background: #ffffff;
        color: #1e293b;
        line-height: 1.65;
        font-size: 11px;
    }

    /* ── Titulní strana ── */
    .title-page {
        page-break-after: always;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        text-align: center;
        padding: 60px 40px;
    }
    .title-page .brand {
        font-size: 42px;
        font-weight: 800;
        letter-spacing: -0.04em;
        margin-bottom: 8px;
    }
    .brand-ai { color: #1e293b; }
    .brand-shield {
        background: linear-gradient(135deg, #c026d3, #22d3ee);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .title-page h1 {
        font-size: 28px;
        font-weight: 700;
        color: #0f172a;
        margin: 24px 0 8px;
        letter-spacing: -0.02em;
    }
    .title-page .company-name {
        font-size: 22px;
        font-weight: 600;
        color: #7c3aed;
        margin-bottom: 6px;
    }
    .title-page .subtitle {
        font-size: 13px;
        color: #64748b;
        max-width: 440px;
    }
    .title-page .meta {
        margin-top: 40px;
        font-size: 11px;
        color: #94a3b8;
        line-height: 1.8;
    }
    .title-accent {
        width: 80px;
        height: 3px;
        background: linear-gradient(90deg, #c026d3, #22d3ee);
        border-radius: 2px;
        margin: 20px auto;
    }

    /* ── Obsah (TOC) ── */
    .toc-page {
        page-break-after: always;
        padding: 40px 0;
    }
    .toc-page h2 {
        font-size: 20px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 24px;
        padding-bottom: 10px;
        border-bottom: 2px solid #e2e8f0;
    }
    .toc-item {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        padding: 8px 0;
        border-bottom: 1px dotted #cbd5e1;
        font-size: 12px;
    }
    .toc-item .toc-title {
        font-weight: 500;
        color: #1e293b;
    }
    .toc-item .toc-page-num {
        color: #94a3b8;
        font-size: 11px;
        flex-shrink: 0;
        margin-left: 12px;
    }
    .toc-tier {
        font-size: 10px;
        font-weight: 600;
        color: #7c3aed;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 16px;
        margin-bottom: 4px;
    }

    /* ── Sekce dokumentu ── */
    .doc-section {
        page-break-before: always;
        padding-top: 10px;
    }
    .doc-section:first-of-type {
        page-break-before: auto;
    }
    .section-header {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #7c3aed;
        border-radius: 0 12px 12px 0;
        padding: 16px 20px;
        margin-bottom: 20px;
    }
    .section-header h2 {
        font-size: 18px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 2px;
    }
    .section-header .section-sub {
        font-size: 11px;
        color: #64748b;
    }

    /* ── Card (lighter glass) ── */
    .card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 16px;
    }

    h2 {
        font-size: 15px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 12px;
    }
    h3 {
        font-size: 13px;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 8px;
    }
    p { margin-bottom: 6px; }

    /* ── Badges ── */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 2px 8px;
        border-radius: 20px;
        font-size: 10px;
        font-weight: 600;
    }
    .badge-high { background: #fef2f2; border: 1px solid #fecaca; color: #dc2626; }
    .badge-limited { background: #fffbeb; border: 1px solid #fde68a; color: #d97706; }
    .badge-minimal { background: #f0fdf4; border: 1px solid #bbf7d0; color: #16a34a; }

    .badge-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
    .badge-dot-high { background: #dc2626; }
    .badge-dot-limited { background: #d97706; }
    .badge-dot-minimal { background: #16a34a; }

    /* ── Tabulky ── */
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
        font-size: 11px;
    }
    th {
        text-align: left;
        padding: 8px 10px;
        background: #f1f5f9;
        border-bottom: 2px solid #e2e8f0;
        font-weight: 600;
        font-size: 10px;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    td {
        padding: 8px 10px;
        border-bottom: 1px solid #e2e8f0;
    }

    /* ── Metriky ── */
    .metric-grid {
        display: flex;
        gap: 12px;
        margin-bottom: 16px;
    }
    .metric {
        flex: 1;
        text-align: center;
        padding: 14px;
        background: #f1f5f9;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
    }
    .metric-value {
        font-size: 24px;
        font-weight: 800;
        line-height: 1;
    }
    .metric-label {
        font-size: 10px;
        color: #64748b;
        margin-top: 4px;
    }

    /* ── Checkboxy — viditelné pro tisk ── */
    .checkbox-item {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 8px 0;
        border-bottom: 1px solid #f1f5f9;
    }
    .checkbox {
        width: 14px;
        height: 14px;
        border: 2px solid #94a3b8;
        border-radius: 3px;
        flex-shrink: 0;
        margin-top: 2px;
    }
    .checkbox-done {
        border-color: #16a34a;
        background: #dcfce7;
    }

    /* ── Highlight box ── */
    .highlight-box {
        padding: 14px 16px;
        border-left: 3px solid #7c3aed;
        background: #faf5ff;
        border-radius: 0 10px 10px 0;
        margin: 12px 0;
        font-size: 11px;
    }

    .disclaimer {
        margin-top: 24px;
        padding: 14px;
        background: #fffbeb;
        border: 1px solid #fde68a;
        border-radius: 10px;
        font-size: 10px;
        color: #92400e;
    }

    .section-divider {
        width: 60px;
        height: 3px;
        background: linear-gradient(90deg, #c026d3, #22d3ee);
        border-radius: 2px;
        margin: 20px 0;
    }

    ul, ol { margin: 6px 0; padding-left: 18px; }
    li { margin-bottom: 5px; font-size: 11px; }

    /* ── VOP ── */
    .vop-section {
        page-break-before: always;
    }
    .vop-section h2 {
        font-size: 16px;
        color: #0f172a;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 8px;
        margin-bottom: 16px;
    }
    .vop-section h3 {
        font-size: 12px;
        color: #1e293b;
        margin-top: 14px;
    }
    .vop-section p {
        font-size: 10px;
        color: #475569;
        line-height: 1.6;
    }

    /* ── Footer per sekce ── */
    .doc-footer {
        text-align: center;
        padding: 16px 0;
        font-size: 9px;
        color: #94a3b8;
        border-top: 1px solid #e2e8f0;
        margin-top: 24px;
    }
</style>
"""


# ══════════════════════════════════════════════════════════════════════
# RISK BADGE — light theme verze
# ══════════════════════════════════════════════════════════════════════

def _print_risk_badge(level: str) -> str:
    labels = {"high": "Vysoké riziko", "limited": "Omezené riziko", "minimal": "Minimální riziko"}
    return f'<span class="badge badge-{level}"><span class="badge-dot badge-dot-{level}"></span>{labels.get(level, level)}</span>'


# ══════════════════════════════════════════════════════════════════════
# TITLE PAGE
# ══════════════════════════════════════════════════════════════════════

def _render_title_page(data: dict) -> str:
    company = data.get("company_name", "Firma")
    ico = data.get("q_company_ico", "")
    address = data.get("q_company_address", "")
    contact_email = data.get("contact_email", data.get("q_company_contact_email", ""))
    industry = data.get("q_company_industry", "")
    now = _now_str()
    overall = data.get("overall_risk", "minimal")

    meta_lines = [f"Vygenerováno: {now}"]
    if ico:
        meta_lines.append(f"IČO: {ico}")
    if address:
        meta_lines.append(f"Sídlo: {address}")
    if industry:
        meta_lines.append(f"Odvětví: {industry}")
    if contact_email:
        meta_lines.append(f"Kontakt: {contact_email}")
    meta_lines.append(f"Celkové riziko: {{'high': 'VYSOKÉ', 'limited': 'OMEZENÉ', 'minimal': 'MINIMÁLNÍ'}}.get('{overall}', '{overall}')")

    # Fix the risk label inline
    risk_labels = {"high": "VYSOKÉ", "limited": "OMEZENÉ", "minimal": "MINIMÁLNÍ"}
    meta_lines[-1] = f"Celkové riziko: {risk_labels.get(overall, overall)}"

    return f"""
    <div class="title-page">
        <div class="brand">
            <span class="brand-ai">AI</span><span class="brand-shield">shield</span><span style="color:#94a3b8;font-size:16px;margin-left:2px">.cz</span>
        </div>
        <div class="title-accent"></div>
        <h1>AI Act Compliance Kit</h1>
        <div class="company-name">{company}</div>
        <p class="subtitle">
            Kompletní dokumentace pro soulad s Nařízením (EU) 2024/1689 —
            Akt o umělé inteligenci. Do plné účinnosti zbývá {_days_until_deadline()} dní.
        </p>
        <div class="title-accent"></div>
        <div class="meta">
            {'<br>'.join(meta_lines)}
        </div>
    </div>
    """


# ══════════════════════════════════════════════════════════════════════
# TABLE OF CONTENTS
# ══════════════════════════════════════════════════════════════════════

def _render_toc(eligible_keys: list[str], has_vop: bool = True) -> str:
    """Generuje obsah. Čísla stránek WeasyPrint doplní přes target-counter."""
    toc_items = ""

    tier_labels = {
        "compliance_report": ("always", "Základ"),
        "action_plan": ("always", "Základ"),
        "ai_register": ("always", "Základ"),
        "training_outline": ("always", "Základ"),
        "chatbot_notices": ("conditional", "Podmíněný"),
        "ai_policy": ("conditional", "Podmíněný"),
        "incident_response_plan": ("risk-based", "Dle rizika"),
        "dpia_template": ("risk-based", "Dle rizika"),
        "vendor_checklist": ("risk-based", "Dle rizika"),
        "monitoring_plan": ("risk-based", "Dle rizika"),
    }

    current_tier = None
    for key in eligible_keys:
        tier_key, tier_label = tier_labels.get(key, ("", ""))
        if tier_key and tier_key != current_tier:
            current_tier = tier_key
            toc_items += f'<div class="toc-tier">{tier_label}</div>'

        name = TEMPLATE_NAMES.get(key, key)
        toc_items += f"""
        <div class="toc-item">
            <span class="toc-title"><a href="#section-{key}" style="text-decoration:none;color:inherit">{name}</a></span>
        </div>"""

    if has_vop:
        toc_items += f'<div class="toc-tier">Právní</div>'
        toc_items += """
        <div class="toc-item">
            <span class="toc-title"><a href="#section-vop" style="text-decoration:none;color:inherit">Všeobecné obchodní podmínky (VOP)</a></span>
        </div>"""

    return f"""
    <div class="toc-page">
        <h2>Obsah</h2>
        {toc_items}
        <p style="margin-top:20px;font-size:10px;color:#94a3b8">
            Tento dokument byl automaticky vygenerován na základě skenu webových stránek
            a odpovědí v dotazníku. Obsah je přizpůsoben rizikovému profilu firmy —
            dokumenty, které nejsou relevantní, nebyly generovány.
        </p>
    </div>
    """


# ══════════════════════════════════════════════════════════════════════
# SECTION RENDERERS — přepisujeme LIGHT verze každé šablony
# ══════════════════════════════════════════════════════════════════════

def _render_section(template_key: str, data: dict) -> str:
    """
    Renderuje jednu sekci dokumentu pro unified PDF.
    Používá existující renderery z templates.py ale extrahuje jen <body> obsah,
    pak jej wrappuje do .doc-section s anchor pro TOC.
    """
    # Transparenční stránka se do PDF nedává (je to standalone HTML)
    if template_key == "transparency_page":
        return ""

    if template_key not in TEMPLATE_RENDERERS:
        return ""

    renderer = TEMPLATE_RENDERERS[template_key]
    name = TEMPLATE_NAMES.get(template_key, template_key)

    # Render full HTML, then extract body content
    full_html = renderer(data)

    # Extract content between <div class="container"> ... </div></body>
    # We need to strip the wrapper (html/head/css/header/footer/disclaimer)
    # and just get the actual section content
    body_start = full_html.find('</div>\n        {body}')
    # More robust: extract between the header and disclaimer
    # Since we control the templates, we can just re-render the content inline

    return f"""
    <div class="doc-section" id="section-{template_key}">
        <div class="section-header">
            <h2>{name}</h2>
            <div class="section-sub">AI Act Compliance Kit — AIshield.cz</div>
        </div>
    """


# ══════════════════════════════════════════════════════════════════════
# PER-SECTION CONTENT RENDERERS (light theme, no dark CSS)
# ══════════════════════════════════════════════════════════════════════

def _section_compliance_report(data: dict) -> str:
    company = data.get("company_name", "Firma")
    ico = data.get("q_company_ico", "")
    address = data.get("q_company_address", "")
    industry = data.get("q_company_industry", "")
    company_size = data.get("q_company_size", "")
    revenue = data.get("q_company_annual_revenue", "")
    url = data.get("url", "")
    findings = data.get("findings", [])
    q_systems = data.get("questionnaire_ai_systems", 0)
    ai_declared = data.get("ai_systems_declared", [])
    risk = data.get("risk_breakdown", {"high": 0, "limited": 0, "minimal": 0})
    recommendations = data.get("recommendations", [])
    overall = data.get("overall_risk", "minimal")
    total = len(findings) + q_systems
    eligible_docs = data.get("eligible_documents", {})
    skipped_docs = data.get("skipped_documents", [])

    # Company details
    details = ""
    if ico: details += f'<p><strong>IČO:</strong> {ico}</p>'
    if address: details += f'<p><strong>Sídlo:</strong> {address}</p>'
    if industry: details += f'<p><strong>Odvětví:</strong> {industry}</p>'
    if company_size: details += f'<p><strong>Velikost:</strong> {company_size}</p>'
    if revenue: details += f'<p><strong>Roční obrat:</strong> {revenue}</p>'

    # Findings table
    findings_rows = ""
    for f in findings:
        rl = f.get("risk_level", "minimal")
        findings_rows += f"""
        <tr>
            <td style="font-weight:600">{f.get('name', 'AI systém')}</td>
            <td>{f.get('category', '')}</td>
            <td>{_print_risk_badge(rl)}</td>
            <td style="font-size:10px">{f.get('ai_act_article', '')}</td>
            <td style="font-size:10px">{f.get('action_required', '')}</td>
        </tr>"""

    findings_html = ""
    if findings_rows:
        findings_html = f"""
    <div class="card">
        <h2>Nalezené AI systémy — automatický sken webu</h2>
        <p style="color:#64748b;font-size:11px;margin-bottom:12px">Sken URL: <strong>{url}</strong></p>
        <table>
            <thead><tr><th>Systém</th><th>Kategorie</th><th>Riziko</th><th>Článek AI Act</th><th>Požadovaná akce</th></tr></thead>
            <tbody>{findings_rows}</tbody>
        </table>
    </div>"""

    # Declared systems
    declared_html = ""
    if ai_declared:
        declared_rows = ""
        for d in ai_declared:
            tool = d.get("tool_name", "AI systém")
            key_label = d.get("key", "").replace("uses_", "").replace("_", " ").title()
            declared_rows += f'<tr><td style="font-weight:600">{tool}</td><td>{key_label}</td><td>Dotazník</td></tr>'
        declared_html = f"""
    <div class="card">
        <h2>AI systémy z dotazníku</h2>
        <table>
            <thead><tr><th>Nástroj</th><th>Oblast</th><th>Zdroj</th></tr></thead>
            <tbody>{declared_rows}</tbody>
        </table>
    </div>"""

    # Recommendations
    recs_html = ""
    if recommendations:
        items = ""
        for r in recommendations:
            rl = r.get("risk_level", "minimal")
            items += f"""
            <div style="border-left:3px solid;padding-left:12px;margin-bottom:10px;border-color:{'#dc2626' if rl == 'high' else '#d97706' if rl == 'limited' else '#16a34a'}">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
                    {_print_risk_badge(rl)}
                    <strong style="font-size:11px">{r.get('tool_name', 'AI systém')}</strong>
                </div>
                <p style="font-size:11px;color:#64748b">{r.get('recommendation', '')}</p>
            </div>"""
        recs_html = f'<div class="card"><h2>Doporučení ke compliance</h2>{items}</div>'

    # Document overview
    doc_overview = ""
    if eligible_docs or skipped_docs:
        gen_rows = ""
        for tkey, reason in eligible_docs.items():
            tname = TEMPLATE_NAMES.get(tkey, tkey)
            gen_rows += f'<tr><td><span style="color:#16a34a;font-weight:700">✓</span> {tname}</td><td style="color:#64748b;font-size:10px">{reason}</td></tr>'
        gen_rows += '<tr><td><span style="color:#16a34a;font-weight:700">✓</span> Školení AI Literacy — Prezentace (PPTX)</td><td style="color:#64748b;font-size:10px">Povinné školení dle čl. 4 AI Act</td></tr>'

        skip_rows = ""
        for sk in skipped_docs:
            skip_rows += f'<tr><td><span style="color:#94a3b8">—</span> {sk["name"]}</td><td style="color:#94a3b8;font-size:10px">{sk["reason"]}</td></tr>'

        skipped_section = ""
        if skipped_docs:
            skipped_section = f"""
            <h3 style="margin-top:16px">Přeskočené dokumenty</h3>
            <p style="color:#64748b;font-size:11px;margin-bottom:8px">Pro váš rizikový profil nejsou relevantní:</p>
            <table><thead><tr><th>Dokument</th><th>Důvod</th></tr></thead><tbody>{skip_rows}</tbody></table>"""

        doc_overview = f"""
    <div class="card">
        <h2>Přehled dokumentů v tomto kitu</h2>
        <table><thead><tr><th>Dokument</th><th>Důvod generování</th></tr></thead><tbody>{gen_rows}</tbody></table>
        {skipped_section}
    </div>"""

    return f"""
    <div class="doc-section" id="section-compliance_report">
        <div class="section-header">
            <h2>AI Act Compliance Report</h2>
            <div class="section-sub">Komplexní analýza souladu s Nařízením EU 2024/1689</div>
        </div>

        <div class="card">
            <h2>Souhrnné hodnocení</h2>
            <p><strong>Firma:</strong> {company}</p>
            {details}
            <p><strong>Analyzovaný web:</strong> {url}</p>
            <p><strong>Celkové riziko:</strong> {_print_risk_badge(overall)}</p>
        </div>

        <div class="metric-grid">
            <div class="metric">
                <div class="metric-value" style="color:#7c3aed">{total}</div>
                <div class="metric-label">AI systémů celkem</div>
            </div>
            <div class="metric">
                <div class="metric-value" style="color:#dc2626">{risk.get('high', 0)}</div>
                <div class="metric-label">Vysoké riziko</div>
            </div>
            <div class="metric">
                <div class="metric-value" style="color:#d97706">{risk.get('limited', 0)}</div>
                <div class="metric-label">Omezené riziko</div>
            </div>
        </div>

        <div class="highlight-box">
            <strong>Deadline:</strong> 2. srpna 2026 — zbývá {_days_until_deadline()} dní.
            Nesplnění může vést k pokutám až 35 mil. EUR nebo 7 % ročního obratu.
        </div>

        {findings_html}
        {declared_html}
        {recs_html}
        {doc_overview}
    </div>
    """


def _section_action_plan(data: dict) -> str:
    company = data.get("company_name", "Firma")
    action_items = data.get("action_items", [])
    findings = data.get("findings", [])
    risk = data.get("risk_breakdown", {})

    auto_items = []
    auto_items.append(("info", "Jmenovat odpovědnou osobu za AI compliance"))
    auto_items.append(("info", "Vytvořit interní registr AI systémů"))
    auto_items.append(("info", "Proškolit zaměstnance — AI literacy dle čl. 4 AI Act"))

    if risk.get("high", 0) > 0:
        auto_items.append(("high", "Provést posouzení shody pro vysoce rizikové systémy"))
        auto_items.append(("high", "Zavést systém řízení rizik dle čl. 9 AI Act"))
        auto_items.append(("high", "Zajistit lidský dohled dle čl. 14 AI Act"))
        auto_items.append(("high", "Registrovat vysoce rizikové systémy v EU databázi (čl. 49)"))

    if risk.get("limited", 0) > 0:
        auto_items.append(("limited", "Přidat transparenční oznámení na web (čl. 50)"))
        auto_items.append(("limited", "Vytvořit transparenční stránku /ai-transparence"))

    chatbot_findings = [f for f in findings if f.get("category") == "chatbot"]
    if chatbot_findings:
        auto_items.append(("limited", "Přidat oznámení ke každému chatbotu: 'Komunikujete s umělou inteligencí'"))

    auto_items.append(("info", "Naplánovat pravidelný re-sken webu (měsíční monitoring)"))
    auto_items.append(("info", "Připravit DPIA pro AI systémy zpracovávající osobní údaje"))

    for item in action_items:
        rl = item.get("risk_level", "info")
        auto_items.append((rl, item.get("action", "")))

    groups = {"high": [], "limited": [], "minimal": [], "info": []}
    for rl, text in auto_items:
        groups.get(rl, groups["info"]).append(text)

    items_html = ""
    group_labels = [
        ("high", "Vysoká priorita — vysoce rizikové systémy", "#dc2626"),
        ("limited", "Střední priorita — omezené riziko / transparentnost", "#d97706"),
        ("info", "Obecné kroky — organizační opatření", "#7c3aed"),
    ]
    for key, label, color in group_labels:
        if not groups[key]:
            continue
        items_html += f'<h3 style="color:{color};margin-top:16px">{label}</h3>'
        for text in groups[key]:
            items_html += f"""
            <div class="checkbox-item">
                <div class="checkbox"></div>
                <div><p>{text}</p></div>
            </div>"""

    return f"""
    <div class="doc-section" id="section-action_plan">
        <div class="section-header">
            <h2>Akční plán</h2>
            <div class="section-sub">Konkrétní kroky ke splnění EU AI Act do 2. 8. 2026</div>
        </div>
        <div class="card">
            <p><strong>Firma:</strong> {company}</p>
            <p><strong>Deadline:</strong> 2. srpna 2026 (zbývá {_days_until_deadline()} dní)</p>
        </div>
        <div class="card">
            {items_html}
        </div>
        <div class="highlight-box">
            <strong>Tip:</strong> Odškrtávejte splněné body. Při auditu tento dokument poslouží
            jako důkaz vaší snahy o compliance (documented effort).
        </div>
    </div>
    """


def _section_ai_register(data: dict) -> str:
    company = data.get("company_name", "Firma")
    findings = data.get("findings", [])
    ai_declared = data.get("ai_systems_declared", [])
    oversight = data.get("oversight_person", {})

    web_rows = ""
    for i, f in enumerate(findings, 1):
        rl = f.get("risk_level", "minimal")
        web_rows += f"""
        <tr><td>{i}</td><td style="font-weight:600">{f.get('name', 'AI systém')}</td>
        <td>{f.get('category', '')}</td><td>{_print_risk_badge(rl)}</td>
        <td style="font-size:10px">{f.get('ai_act_article', '')}</td><td>Web</td></tr>"""

    internal_rows = ""
    start_idx = len(findings) + 1
    for j, d in enumerate(ai_declared, start_idx):
        tool = d.get("tool_name", "AI systém")
        key_label = d.get("key", "").replace("uses_", "").replace("_", " ").title()
        internal_rows += f"""
        <tr><td>{j}</td><td style="font-weight:600">{tool}</td>
        <td>{key_label}</td><td>—</td><td>—</td><td>Interní</td></tr>"""

    no_data = '<tr><td colspan="6" style="color:#94a3b8">Žádné systémy</td></tr>'

    return f"""
    <div class="doc-section" id="section-ai_register">
        <div class="section-header">
            <h2>Registr AI systémů</h2>
            <div class="section-sub">Interní evidence dle čl. 49 Nařízení (EU) 2024/1689</div>
        </div>
        <div class="card">
            <p><strong>Firma:</strong> {company}</p>
            <p style="color:#64748b;font-size:11px">Aktualizujte při každé změně v AI systémech.</p>
        </div>
        <div class="card">
            <h3>A. AI systémy na webových stránkách</h3>
            <table>
                <thead><tr><th>#</th><th>Systém</th><th>Kategorie</th><th>Riziko</th><th>Článek</th><th>Nasazení</th></tr></thead>
                <tbody>{web_rows if web_rows else no_data}</tbody>
            </table>
        </div>
        <div class="card">
            <h3>B. Interní AI systémy</h3>
            <table>
                <thead><tr><th>#</th><th>Systém</th><th>Kategorie</th><th>Riziko</th><th>Článek</th><th>Nasazení</th></tr></thead>
                <tbody>{internal_rows if internal_rows else no_data}</tbody>
            </table>
        </div>
        <div class="card">
            <h3>C. Odpovědná osoba</h3>
            <table>
                <tr><td style="width:200px;color:#64748b">Jméno a příjmení</td><td>{oversight.get("name") or "Vyplňte"}</td></tr>
                <tr><td style="color:#64748b">Funkce</td><td>{oversight.get("role") or "Vyplňte"}</td></tr>
                <tr><td style="color:#64748b">Email</td><td>{oversight.get("email") or "Vyplňte"}</td></tr>
                <tr><td style="color:#64748b">Datum jmenování</td><td>Vyplňte</td></tr>
            </table>
        </div>
        <div class="highlight-box">
            Registr AI systémů je živý dokument. Aktualizujte ho při každé změně.
        </div>
    </div>
    """


def _section_training_outline(data: dict) -> str:
    company = data.get("company_name", "Firma")
    training = data.get("training", {})
    audience_size = training.get("audience_size", "")
    audience_level = training.get("audience_level", "")
    audience_info = ""
    if audience_size:
        audience_info += f' · Počet: {audience_size}'
    if audience_level:
        audience_info += f' · Úroveň: {audience_level}'

    modules = [
        ("Modul 1 — Co je umělá inteligence (30 min)", [
            "Definice AI — co to je a co to není",
            "Typy AI: generativní AI, prediktivní modely, expertní systémy",
            "Příklady AI v každodenním životě",
            "AI vs. automatizace — jaký je rozdíl?",
        ]),
        ("Modul 2 — EU AI Act v kostce (45 min)", [
            "Proč EU reguluje AI — cíle nařízení",
            "4 kategorie rizik: nepřijatelné → vysoké → omezené → minimální",
            "Zakázané praktiky (čl. 5)",
            "Povinnosti transparentnosti (čl. 50)",
            "Pokuty — až 35 mil. EUR nebo 7 % obratu",
        ]),
        ("Modul 3 — AI v naší firmě (30 min)", [
            "Jaké AI systémy používáme (registr AI)",
            "Povolené vs. zakázané použití (interní AI politika)",
            "Pravidla pro vkládání dat do AI nástrojů",
            "Odpovědná osoba za AI ve firmě",
        ]),
        ("Modul 4 — Bezpečné používání AI (30 min)", [
            "ChatGPT / Claude — jak správně používat",
            "Co do AI NIKDY nevkládat (osobní údaje, hesla, smlouvy)",
            "Ověřování výstupů AI — trust but verify",
            "Označování AI-generovaného obsahu",
            "Hlášení incidentů",
        ]),
        ("Modul 5 — Test a certifikace (15 min)", [
            "Krátký test (10 otázek) — minimum 70 %",
            "Certifikát o absolvování školení",
            "Opakovat 1× ročně jako refresher",
        ]),
    ]

    modules_html = ""
    for title, items in modules:
        items_li = "".join(f"<li>{i}</li>" for i in items)
        modules_html += f"""
        <div class="card">
            <h2>{title}</h2>
            <ul>{items_li}</ul>
        </div>"""

    return f"""
    <div class="doc-section" id="section-training_outline">
        <div class="section-header">
            <h2>Školení AI Literacy</h2>
            <div class="section-sub">Osnova povinného školení dle čl. 4 Nařízení (EU) 2024/1689</div>
        </div>
        <div class="card">
            <p><strong>Rozsah:</strong> 2–3 hodiny · <strong>Cílová skupina:</strong> Všichni zaměstnanci {company}{audience_info} · <strong>Frekvence:</strong> Při nástupu + 1× ročně</p>
        </div>
        {modules_html}
        <div class="card">
            <h3>Evidence absolvování</h3>
            <table>
                <thead><tr><th>Jméno zaměstnance</th><th>Datum školení</th><th>Výsledek testu</th><th>Podpis</th></tr></thead>
                <tbody>
                    {''.join('<tr><td>&nbsp;</td><td></td><td></td><td></td></tr>' for _ in range(8))}
                </tbody>
            </table>
        </div>
    </div>
    """


def _section_chatbot_notices(data: dict) -> str:
    company = data.get("company_name", "Firma")
    contact_email = data.get("contact_email", data.get("q_company_contact_email", "info@firma.cz"))

    notices = [
        ("Krátké oznámení (doporučeno)",
         f"Komunikujete s umělou inteligencí. Pokud chcete hovořit s člověkem, napište nám na {contact_email}.",
         "Zobrazit v chatovacím okně před prvním automatickým pozdravem."),
        ("Rozšířené oznámení",
         f"Tento chat využívá systém umělé inteligence pro asistenci zákazníkům. Odpovědi jsou generovány automaticky. Společnost {company} zajišťuje lidský dohled. Pro komunikaci s člověkem napište 'operátor' nebo nás kontaktujte na {contact_email}.",
         "Zobrazit v patičce chatovacího okna nebo jako úvodní zprávu."),
        ("Banner na webu",
         "Na tomto webu využíváme umělou inteligenci pro zlepšení služeb. Více informací na stránce AI transparence.",
         "Zobrazit jako lištu na stránce nebo v patičce webu."),
        ("Kontaktní formulář s AI zpracováním",
         "Váš dotaz bude nejprve zpracován systémem umělé inteligence pro rychlejší odpověď. Každou odpověď následně kontroluje náš tým.",
         "Zobrazit u kontaktního formuláře, pokud AI třídí nebo odpovídá na dotazy."),
    ]

    notices_html = ""
    for name, text, where in notices:
        notices_html += f"""
        <div class="card">
            <h3>{name}</h3>
            <div style="background:#f1f5f9;border:1px solid #e2e8f0;border-radius:8px;padding:12px;margin:8px 0;font-family:monospace;font-size:11px;line-height:1.6">{text}</div>
            <p style="font-size:10px;color:#64748b"><strong>Kde použít:</strong> {where}</p>
        </div>"""

    return f"""
    <div class="doc-section" id="section-chatbot_notices">
        <div class="section-header">
            <h2>Texty AI oznámení</h2>
            <div class="section-sub">Připravené oznámení dle čl. 50 Nařízení (EU) 2024/1689</div>
        </div>
        <div class="card">
            <p>Dle čl. 50 odst. 1 AI Act musí být uživatel informován, že komunikuje
            se systémem umělé inteligence. Níže najdete připravené texty — stačí zkopírovat a vložit.</p>
        </div>
        {notices_html}
    </div>
    """


def _section_ai_policy(data: dict) -> str:
    company = data.get("company_name", "Firma")
    oversight = data.get("oversight_person", {})

    return f"""
    <div class="doc-section" id="section-ai_policy">
        <div class="section-header">
            <h2>Interní AI politika</h2>
            <div class="section-sub">Pravidla používání umělé inteligence dle Nařízení (EU) 2024/1689</div>
        </div>

        <div class="card">
            <p><strong>Firma:</strong> {company}</p>
            <p><strong>Platnost od:</strong> Vyplňte</p>
            <p><strong>Schválil/a:</strong> Vyplňte</p>
        </div>

        <div class="card">
            <h2>1. Účel dokumentu</h2>
            <p>Tato politika stanoví pravidla pro používání systémů umělé inteligence
            ve společnosti {company}. Cílem je zajistit soulad s Nařízením (EU) 2024/1689
            (AI Act) a minimalizovat rizika spojená s nasazením AI.</p>
        </div>

        <div class="card">
            <h2>2. Rozsah platnosti</h2>
            <ul>
                <li>Všichni zaměstnanci a externí spolupracovníci</li>
                <li>Všechny AI systémy používané interně i na veřejných platformách</li>
                <li>Vývoj, nasazení, provoz i vyřazení AI systémů</li>
            </ul>
        </div>

        <div class="card">
            <h2>3. Povolené používání AI</h2>
            <ul>
                <li><strong>Chatboty a asistenti</strong> (ChatGPT, Claude, Gemini) — povoleno pro interní práci. ZAKÁZÁNO vkládat osobní údaje zákazníků, finanční data a obchodní tajemství.</li>
                <li><strong>AI pro kód</strong> (GitHub Copilot, Cursor) — povoleno. Veškerý AI-generovaný kód musí projít code review.</li>
                <li><strong>AI obsah</strong> (DALL-E, Midjourney, Jasper) — povoleno. Veřejně publikovaný AI obsah musí být označen dle čl. 50 odst. 4 AI Act.</li>
            </ul>
        </div>

        <div class="card">
            <h2>4. Zakázané praktiky</h2>
            <p style="color:#dc2626">Následující je v souladu s čl. 5 AI Act přísně zakázáno:</p>
            <ul>
                <li>Sociální scoring zaměstnanců nebo zákazníků</li>
                <li>Podprahová manipulace rozhodování (dark patterns s AI)</li>
                <li>Biometrická identifikace v reálném čase na veřejných místech</li>
                <li>Rozpoznávání emocí zaměstnanců na pracovišti (mimo bezpečnost)</li>
                <li>Sběr biometrických dat z internetu pro trénování AI</li>
            </ul>
        </div>

        <div class="card">
            <h2>5. Pravidla pro data</h2>
            <ul>
                <li>Do AI systémů třetích stran NEVKLÁDEJTE osobní údaje</li>
                <li>Interní dokumenty smí být zpracovány AI pouze se souhlasem nadřízeného</li>
                <li>Ověřujte výstupy AI — nepoužívejte je bez kontroly</li>
                <li>Uchovávejte záznamy o používání AI pro účely auditu</li>
            </ul>
        </div>

        <div class="card">
            <h2>6. Odpovědnost a dohled</h2>
            <table>
                <tr><td style="width:200px;color:#64748b">Odpovědná osoba za AI</td><td>{oversight.get("name") or "Vyplňte"}</td></tr>
                <tr><td style="color:#64748b">Funkce</td><td>{oversight.get("role") or "Vyplňte"}</td></tr>
                <tr><td style="color:#64748b">Kontakt</td><td>{oversight.get("email") or "Vyplňte"}</td></tr>
                <tr><td style="color:#64748b">Frekvence revize</td><td>Minimálně 1× ročně</td></tr>
            </table>
        </div>

        <div class="card">
            <h2>7. Povinnosti zaměstnanců</h2>
            <ul>
                <li>Absolvovat školení AI literacy do 3 měsíců od nástupu</li>
                <li>Hlásit nové AI nástroje odpovědné osobě PŘED nasazením</li>
                <li>Neinstalovat AI nástroje na firemní zařízení bez schválení IT</li>
                <li>Při pochybnostech kontaktovat odpovědnou osobu za AI</li>
            </ul>
        </div>

        <div class="card">
            <h2>8. Sankce</h2>
            <p>Porušení této politiky může vést k disciplinárním opatřením.
            Porušení AI Act může firmu vystavit pokutám až 35 mil. EUR nebo 7 % ročního obratu.</p>
        </div>

        <div class="section-divider"></div>
        <div class="card">
            <h3>Podpisy</h3>
            <table>
                <tr>
                    <td style="width:50%;border-right:1px solid #e2e8f0">
                        <p style="color:#64748b;font-size:10px">Schválil/a (vedení)</p><br><br>
                        <p>Jméno, funkce, datum</p>
                    </td>
                    <td style="padding-left:16px">
                        <p style="color:#64748b;font-size:10px">Odpovědná osoba za AI</p><br><br>
                        <p>Jméno, funkce, datum</p>
                    </td>
                </tr>
            </table>
        </div>
    </div>
    """


def _section_incident_response_plan(data: dict) -> str:
    company = data.get("company_name", "Firma")
    oversight = data.get("oversight_person", {})
    person_name = oversight.get("name", "Vyplňte")
    person_email = oversight.get("email", "Vyplňte")
    person_phone = oversight.get("phone", "Vyplňte")

    return f"""
    <div class="doc-section" id="section-incident_response_plan">
        <div class="section-header">
            <h2>Plán řízení AI incidentů</h2>
            <div class="section-sub">Postupy dle čl. 73 Nařízení (EU) 2024/1689</div>
        </div>
        <div class="card">
            <p><strong>Firma:</strong> {company}</p>
            <p><strong>Platnost od:</strong> {_now_str()}</p>
        </div>

        <div class="card">
            <h2>1. Definice AI incidentu</h2>
            <p>Za AI incident se považuje situace, kdy systém umělé inteligence:</p>
            <ul>
                <li>Poskytne nesprávnou, zavádějící nebo diskriminační odpověď zákazníkovi</li>
                <li>Zpracuje osobní údaje v rozporu s GDPR</li>
                <li>Selže technicky a ovlivní provoz firmy</li>
                <li>Vygeneruje obsah porušující autorská práva</li>
                <li>Se stane obětí kyberútoku (prompt injection, data poisoning)</li>
            </ul>
        </div>

        <div class="card">
            <h2>2. Klasifikace závažnosti</h2>
            <table>
                <thead><tr><th>Stupeň</th><th>Popis</th><th>Příklad</th><th>Reakční doba</th></tr></thead>
                <tbody>
                    <tr><td>{_print_risk_badge('high')}</td><td>Kritický</td><td>Diskriminace, únik údajů</td><td><strong>1 hodina</strong></td></tr>
                    <tr><td>{_print_risk_badge('limited')}</td><td>Střední</td><td>Chybná informace chatbotu</td><td><strong>24 hodin</strong></td></tr>
                    <tr><td>{_print_risk_badge('minimal')}</td><td>Nízký</td><td>Překlep v AI odpovědi</td><td><strong>72 hodin</strong></td></tr>
                </tbody>
            </table>
        </div>

        <div class="card">
            <h2>3. Eskalační řetězec</h2>
            <table>
                <thead><tr><th>Krok</th><th>Kdo</th><th>Kontakt</th><th>Akce</th></tr></thead>
                <tbody>
                    <tr><td>1</td><td>Zaměstnanec</td><td>—</td><td>Zaznamenat, informovat odpovědnou osobu</td></tr>
                    <tr><td>2</td><td>Odpovědná osoba za AI</td><td>{person_name}<br>{person_email}<br>{person_phone}</td><td>Posoudit závažnost</td></tr>
                    <tr><td>3</td><td>Vedení firmy</td><td>Vyplňte</td><td>Schválit odstavení systému</td></tr>
                    <tr><td>4</td><td>IT / dodavatel AI</td><td>Vyplňte</td><td>Technická náprava</td></tr>
                    <tr><td>5</td><td>DPO / právní poradce</td><td>Vyplňte</td><td>Posouzení povinnosti hlášení</td></tr>
                </tbody>
            </table>
        </div>

        <div class="card">
            <h2>4. Postup při incidentu</h2>
            <h3 style="color:#dc2626">Fáze 1 — Okamžitá reakce (0–1 h)</h3>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Zastavit AI systém, který incident způsobil</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Zajistit důkazy (screenshot, logy, čas)</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Informovat odpovědnou osobu za AI</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>U kritických incidentů: okamžitě odstavit systém</p></div></div>
            <div class="section-divider"></div>
            <h3 style="color:#d97706">Fáze 2 — Vyhodnocení (1–24 h)</h3>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Klasifikovat závažnost incidentu</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Identifikovat dotčené osoby</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Posoudit porušení GDPR</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Rozhodnout o hlášení dozorové autoritě</p></div></div>
            <div class="section-divider"></div>
            <h3>Fáze 3 — Náprava (24–72 h)</h3>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Opravit AI systém / změnit konfiguraci</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Informovat dotčené osoby</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Aktualizovat registr AI systémů</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Dokumentovat příčinu a opatření</p></div></div>
        </div>

        <div class="card">
            <h2>5. Povinné hlášení (čl. 73)</h2>
            <div class="highlight-box">
                <p><strong>Závažný incident</strong> se MUSÍ nahlásit do <strong>15 dnů</strong>:</p>
                <ul>
                    <li>Úmrtí nebo vážné poškození zdraví</li>
                    <li>Závažné porušení základních práv</li>
                    <li>Závažné poškození majetku nebo životního prostředí</li>
                </ul>
            </div>
        </div>

        <div class="card">
            <h2>6. Záznamový formulář</h2>
            <table>
                <tr><td style="width:220px;color:#64748b">Datum a čas incidentu</td><td>Vyplňte</td></tr>
                <tr><td style="color:#64748b">Zjištěno kým</td><td>Vyplňte</td></tr>
                <tr><td style="color:#64748b">Dotčený AI systém</td><td>Vyplňte</td></tr>
                <tr><td style="color:#64748b">Popis incidentu</td><td>Vyplňte</td></tr>
                <tr><td style="color:#64748b">Stupeň závažnosti</td><td>Kritický / Střední / Nízký</td></tr>
                <tr><td style="color:#64748b">Přijatá opatření</td><td>Vyplňte</td></tr>
                <tr><td style="color:#64748b">Nahlášeno dozorovému orgánu?</td><td>ANO / NE</td></tr>
                <tr><td style="color:#64748b">Podpis odpovědné osoby</td><td>Vyplňte</td></tr>
            </table>
        </div>
    </div>
    """


def _section_dpia_template(data: dict) -> str:
    company = data.get("company_name", "Firma")
    ico = data.get("q_company_ico", "")
    oversight = data.get("oversight_person", {})
    ai_systems = data.get("ai_systems_declared", [])
    findings = data.get("findings", [])
    data_prot = data.get("data_protection", {})
    risk = data.get("risk_breakdown", {})
    overall_risk = data.get("overall_risk", "minimal")
    total_systems = len(ai_systems) + len(findings)

    ai_rows = ""
    for sys in ai_systems:
        name = sys.get("tool_name", sys.get("key", "AI systém"))
        ai_rows += f'<tr><td>{name}</td><td>—</td><td>Vyplňte</td><td>Vyplňte</td></tr>'
    for f in findings:
        name = f.get("name", "AI systém")
        rl = f.get("risk_level", "minimal")
        ai_rows += f'<tr><td>{name}</td><td>{_print_risk_badge(rl)}</td><td>Vyplňte</td><td>Vyplňte</td></tr>'
    if not ai_rows:
        ai_rows = '<tr><td colspan="4" style="color:#94a3b8;text-align:center">Doplňte ručně</td></tr>'

    return f"""
    <div class="doc-section" id="section-dpia_template">
        <div class="section-header">
            <h2>DPIA — Posouzení vlivu</h2>
            <div class="section-sub">Předvyplněná šablona dle GDPR čl. 35 + AI Act čl. 27</div>
        </div>
        <div class="card">
            <p><strong>Firma:</strong> {company}</p>
            {'<p><strong>IČO:</strong> ' + ico + '</p>' if ico else ''}
            <p><strong>Datum zpracování:</strong> {_now_str()}</p>
            <p><strong>Verze:</strong> 1.0 — vygenerováno automaticky, vyžaduje doplnění</p>
        </div>
        <div class="metric-grid">
            <div class="metric">
                <div class="metric-value" style="color:#7c3aed">{total_systems}</div>
                <div class="metric-label">AI systémů celkem</div>
            </div>
            <div class="metric">
                <div class="metric-value" style="color:#dc2626">{risk.get("high", 0)}</div>
                <div class="metric-label">Vysoce rizikových</div>
            </div>
        </div>

        <div class="card">
            <h2>1. Odpovědné osoby</h2>
            <table>
                <tr><td style="width:220px;color:#64748b">Správce osobních údajů</td><td>{company}</td></tr>
                <tr><td style="color:#64748b">Odpovědná osoba za AI</td><td>{oversight.get("name", "Vyplňte")}</td></tr>
                <tr><td style="color:#64748b">E-mail</td><td>{oversight.get("email", "Vyplňte")}</td></tr>
                <tr><td style="color:#64748b">Pověřenec (DPO)</td><td>Vyplňte</td></tr>
            </table>
        </div>

        <div class="card">
            <h2>2. AI systémy zpracovávající osobní údaje</h2>
            <table>
                <thead><tr><th>AI systém</th><th>Riziko</th><th>Typ os. údajů</th><th>Účel zpracování</th></tr></thead>
                <tbody>{ai_rows}</tbody>
            </table>
        </div>

        <div class="card">
            <h2>3. Posouzení nezbytnosti</h2>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Zpracování je nezbytné pro splnění účelu</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Neexistují méně invazivní alternativy</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Rozsah údajů je minimalizován</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Doba uchovávání je přiměřená</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Subjekty údajů byly informovány</p></div></div>
        </div>

        <div class="card">
            <h2>4. Technická a organizační opatření</h2>
            <div class="checkbox-item"><div class="checkbox"></div><div><p><strong>Šifrování</strong> — data šifrována při přenosu i v úložišti</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p><strong>Přístupová práva</strong> — přístup jen pro oprávněné osoby</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p><strong>Logování</strong> — operace AI systémů jsou logovány</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p><strong>Lidský dohled</strong> — zajištěn nad rozhodnutími AI</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p><strong>Anonymizace</strong> — data vstupující do AI anonymizována</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p><strong>Pravidelné audity</strong> — AI systémy jsou přehodnocovány</p></div></div>
        </div>

        <div class="card">
            <h2>5. Závěr</h2>
            <table>
                <tr><td style="width:220px;color:#64748b">Celkové riziko</td><td>{_print_risk_badge(overall_risk)}</td></tr>
                <tr><td style="color:#64748b">DPIA závěr</td><td>☐ Přípustné  ☐ Nutná opatření  ☐ Konzultace s ÚOOÚ</td></tr>
                <tr><td style="color:#64748b">Datum příští revize</td><td>Vyplňte</td></tr>
            </table>
        </div>
    </div>
    """


def _section_vendor_checklist(data: dict) -> str:
    company = data.get("company_name", "Firma")
    ai_systems = data.get("ai_systems_declared", [])
    findings = data.get("findings", [])
    data_prot = data.get("data_protection", {})
    has_contracts = data_prot.get("has_vendor_contracts")

    vendor_map = {
        "ChatGPT": "OpenAI, Inc.", "GPT": "OpenAI, Inc.", "OpenAI": "OpenAI, Inc.",
        "Copilot": "Microsoft Corp.", "Microsoft": "Microsoft Corp.",
        "Gemini": "Google LLC", "Google": "Google LLC",
        "Claude": "Anthropic PBC", "Anthropic": "Anthropic PBC",
        "Midjourney": "Midjourney, Inc.", "DALL-E": "OpenAI, Inc.",
        "Perplexity": "Perplexity AI, Inc.", "DeepL": "DeepL SE",
        "Grammarly": "Grammarly, Inc.",
    }

    all_systems = []
    for sys in ai_systems:
        name = sys.get("tool_name") or sys.get("key") or "AI systém"
        rl = (sys.get("details") or {}).get("risk_level", "minimal")
        all_systems.append((name, rl))
    for f in findings:
        all_systems.append((f.get("name", "AI systém"), f.get("risk_level", "minimal")))

    vendor_rows = ""
    for name, rl in all_systems:
        vendor = "—"
        for key, val in vendor_map.items():
            if key.lower() in (name or "").lower():
                vendor = val
                break
        vendor_rows += f'<tr><td>{name}</td><td>{vendor}</td><td>{_print_risk_badge(rl)}</td></tr>'

    if not vendor_rows:
        vendor_rows = '<tr><td colspan="3" style="color:#94a3b8;text-align:center">Doplňte ručně</td></tr>'

    status = '<span style="color:#16a34a">✅ Má smlouvy</span>' if has_contracts else '<span style="color:#dc2626">⚠️ Nemá smluvně ošetřeno</span>'

    return f"""
    <div class="doc-section" id="section-vendor_checklist">
        <div class="section-header">
            <h2>Dodavatelský checklist</h2>
            <div class="section-sub">Kontrolní seznam pro smlouvy s dodavateli AI dle čl. 25–26 AI Act</div>
        </div>
        <div class="card">
            <p><strong>Firma:</strong> {company}</p>
            <p>{status}</p>
        </div>
        <div class="card">
            <h2>Přehled AI systémů a dodavatelů</h2>
            <table>
                <thead><tr><th>AI systém</th><th>Dodavatel</th><th>Riziko</th></tr></thead>
                <tbody>{vendor_rows}</tbody>
            </table>
        </div>

        <div class="card">
            <h2>Povinné smluvní náležitosti</h2>
            <h3 style="color:#dc2626;margin-top:12px">A. Transparentnost (čl. 13)</h3>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Dodavatel poskytl návod k použití AI</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Dodavatel deklaroval účel a zamýšlené použití</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Dodavatel sděluje info o výkonnosti a omezeních</p></div></div>
            <div class="section-divider"></div>
            <h3 style="color:#d97706;margin-top:12px">B. Ochrana osobních údajů (GDPR)</h3>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Smlouva o zpracování (DPA) uzavřena</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Definovány kategorie os. údajů</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Dodavatel garantuje zpracování v EU/EHP</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Dodavatel nepoužívá data k trénování (opt-out)</p></div></div>
            <div class="section-divider"></div>
            <h3 style="margin-top:12px">C. Technické záruky a SLA</h3>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>SLA — definovaná dostupnost</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Reakční doba při incidentu</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Notifikace při změnách modelu</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Právo na audit</p></div></div>
        </div>
    </div>
    """


def _section_monitoring_plan(data: dict) -> str:
    company = data.get("company_name", "Firma")
    oversight = data.get("oversight_person", {})
    ai_systems = data.get("ai_systems_declared", [])
    findings = data.get("findings", [])
    incident = data.get("incident", {})
    risk = data.get("risk_breakdown", {})

    all_systems = []
    for sys in ai_systems:
        name = sys.get("tool_name", sys.get("key", "AI systém"))
        rl = (sys.get("details") or {}).get("risk_level", "minimal")
        all_systems.append((name, rl))
    for f in findings:
        all_systems.append((f.get("name", "AI systém"), f.get("risk_level", "minimal")))

    freq_map = {"high": "Denně / týdně", "limited": "Týdně / měsíčně", "minimal": "Měsíčně / čtvrtletně"}
    system_rows = ""
    for name, rl in all_systems:
        system_rows += f'<tr><td>{name}</td><td>{_print_risk_badge(rl)}</td><td>{freq_map.get(rl, "Měsíčně")}</td></tr>'

    if not system_rows:
        system_rows = '<tr><td colspan="3" style="color:#94a3b8;text-align:center">Doplňte ručně</td></tr>'

    return f"""
    <div class="doc-section" id="section-monitoring_plan">
        <div class="section-header">
            <h2>Monitoring plán AI</h2>
            <div class="section-sub">Plán monitoringu AI výstupů dle čl. 9 a 72 AI Act</div>
        </div>
        <div class="card">
            <p><strong>Firma:</strong> {company}</p>
            <p><strong>Odpovědná osoba:</strong> {oversight.get("name", "Vyplňte")}</p>
        </div>
        <div class="card">
            <h2>Monitorované AI systémy</h2>
            <table>
                <thead><tr><th>AI systém</th><th>Riziko</th><th>Frekvence kontroly</th></tr></thead>
                <tbody>{system_rows}</tbody>
            </table>
        </div>

        <div class="card">
            <h2>CO monitorovat</h2>
            <h3 style="color:#dc2626;margin-top:8px">A. Přesnost a kvalita</h3>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Míra chybných odpovědí</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>AI halucinace — vymýšlení neexistujících faktů</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Relevance a konzistence odpovědí</p></div></div>
            <div class="section-divider"></div>
            <h3 style="color:#d97706;margin-top:8px">B. Férovost a bias</h3>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Genderový bias — liší se odpovědi dle pohlaví?</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Etnický / věkový bias</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Jazykový bias — kvalita pro češtinu vs. angličtinu</p></div></div>
            <div class="section-divider"></div>
            <h3 style="margin-top:8px">C. Bezpečnost</h3>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Prompt injection — manipulace AI přes vstupy</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Data leakage — nevypisuje AI citlivé informace?</p></div></div>
            <div class="checkbox-item"><div class="checkbox"></div><div><p>Dostupnost — uptime AI systému</p></div></div>
        </div>

        <div class="card">
            <h2>Měsíční plán kontrol</h2>
            <table>
                <thead><tr><th>Týden</th><th>Aktivita</th><th>Splněno</th></tr></thead>
                <tbody>
                    <tr><td>1.</td><td>Review přesnosti AI výstupů (vzorek 20 odpovědí)</td><td>☐</td></tr>
                    <tr><td>1.</td><td>Kontrola transparenčních oznámení na webu</td><td>☐</td></tr>
                    <tr><td>2.</td><td>Bias test — 10 testovacích dotazů</td><td>☐</td></tr>
                    <tr><td>2.</td><td>Bezpečnostní test — 5 prompt injection pokusů</td><td>☐</td></tr>
                    <tr><td>3.</td><td>Aktualizace registru AI systémů</td><td>☐</td></tr>
                    <tr><td>3.</td><td>Review zpětné vazby od uživatelů</td><td>☐</td></tr>
                    <tr><td>4.</td><td>Souhrnný report vedení</td><td>☐</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    """


# ══════════════════════════════════════════════════════════════════════
# VOP (Všeobecné obchodní podmínky)
# ══════════════════════════════════════════════════════════════════════

def _render_vop() -> str:
    return """
    <div class="vop-section" id="section-vop">
        <div class="section-header">
            <h2>Všeobecné obchodní podmínky (VOP)</h2>
            <div class="section-sub">AIshield.cz — Martin Haynes, IČO: 17889251</div>
        </div>

        <div class="card">
            <h3>1. Vymezení služby</h3>
            <p>Služba AIshield.cz je automatizovaný technický nástroj, který na základě
            uživatelem poskytnutých údajů a/nebo veřejně dostupného obsahu webu vytváří
            orientační výstupy a návrhy dokumentů pro účely interní compliance.
            Poskytovatel neposkytuje právní služby ani právní poradenství ve smyslu
            zákona č. 85/1996 Sb., o advokacii.</p>

            <h3>2. Charakter výstupů</h3>
            <p>Veškeré výstupy služby jsou poskytovány výhradně jako automatizovaný
            technicko-informační podklad založený na uživatelských vstupech a algoritmickém
            zpracování. Výstupy nejsou právním posouzením konkrétní situace uživatele
            a nemohou nahrazovat individuální právní analýzu provedenou advokátem.</p>

            <h3>3. AI-generovaný obsah</h3>
            <p>Tato dokumentace byla vytvořena s využitím systémů umělé inteligence.
            Uživatel bere na vědomí, že výstupy mohou obsahovat nepřesnosti, neúplnosti
            nebo chyby. Uživatel je plně odpovědný za implementaci, použití a právní
            posouzení výstupů služby.</p>

            <h3>4. Omezení odpovědnosti</h3>
            <p>Poskytovatel neposkytuje žádnou záruku ani ujištění, že použitím výstupů
            bude uživatel v souladu s právními předpisy. Celková odpovědnost poskytovatele
            za újmu vzniklou v souvislosti se službou se omezuje na částku skutečně
            uhrazenou uživatelem za příslušné plnění za posledních 12 měsíců.
            Poskytovatel neodpovídá za jakékoli přímé ani nepřímé škody, sankce, pokuty,
            ušlý zisk ani jinou újmu vzniklou v důsledku použití výstupů služby.</p>

            <h3>5. Povinnosti uživatele</h3>
            <p>Uživatel odpovídá za správnost, úplnost a aktuálnost údajů poskytnutých
            v dotazníku a za to, že výstupy před použitím přiměřeně zkontroluje
            a přizpůsobí svému konkrétnímu provozu. V případě pochybností zajistí
            odborné (právní) posouzení.</p>

            <h3>6. Digitální obsah</h3>
            <p>Výstupy služby mají charakter digitálního obsahu. Souhlasem s objednávkou
            uživatel souhlasí se zahájením plnění před uplynutím 14denní lhůty pro
            odstoupení od smlouvy a bere na vědomí, že tímto ztrácí právo na odstoupení
            dle § 1837 písm. l) občanského zákoníku.</p>

            <h3>7. Licence k výstupům</h3>
            <p>Uživatel získává nevýhradní licenci k použití vygenerovaných dokumentů
            pro interní potřeby své firmy. Přeprodej, zveřejnění nebo prezentace
            výstupů jako „právně ověřených" je zakázáno.</p>

            <h3>8. Ochrana osobních údajů</h3>
            <p>Poskytovatel zpracovává osobní údaje v souladu s Nařízením (EU) 2016/679
            (GDPR). Data z dotazníku jsou uložena v EU (Supabase, Frankfurt).
            Zpracování probíhá na základě plnění smlouvy (čl. 6 odst. 1 písm. b GDPR).
            Data nejsou sdílena s třetími stranami mimo nezbytné zpracovatele.</p>

            <h3>9. Reklamace</h3>
            <p>Reklamaci je možné uplatnit do 30 dnů od dodání na info@aishield.cz.
            Vyřízení do 30 dnů.</p>

            <h3>10. Rozhodné právo</h3>
            <p>Smluvní vztah se řídí právním řádem České republiky. Pro řešení sporů
            jsou příslušné české soudy.</p>
        </div>

        <div class="doc-footer">
            <strong>AIshield.cz</strong> — Provozovatel: Martin Haynes, IČO: 17889251<br>
            info@aishield.cz · +420 732 716 141<br>
            Úplné VOP na: <strong>https://aishield.cz/vop</strong>
        </div>
    </div>
    """


# ══════════════════════════════════════════════════════════════════════
# SECTION ROUTER
# ══════════════════════════════════════════════════════════════════════

SECTION_RENDERERS = {
    "compliance_report": _section_compliance_report,
    "action_plan": _section_action_plan,
    "ai_register": _section_ai_register,
    "training_outline": _section_training_outline,
    "chatbot_notices": _section_chatbot_notices,
    "ai_policy": _section_ai_policy,
    "incident_response_plan": _section_incident_response_plan,
    "dpia_template": _section_dpia_template,
    "vendor_checklist": _section_vendor_checklist,
    "monitoring_plan": _section_monitoring_plan,
}


# ══════════════════════════════════════════════════════════════════════
# HLAVNÍ FUNKCE — generuje unified HTML → WeasyPrint → PDF
# ══════════════════════════════════════════════════════════════════════

def render_unified_pdf_html(data: dict, eligible_keys: list[str]) -> str:
    """
    Generuje kompletní HTML pro unified PDF.
    Struktura: Titulní strana → Obsah → Sekce dokumentů → VOP

    Args:
        data: sloučená data (company + scan + questionnaire)
        eligible_keys: seznam template_key dokumentů k zahrnutí
                       (bez transparency_page — ta je standalone HTML)

    Returns:
        str — plný HTML dokument připravený pro WeasyPrint
    """
    company = data.get("company_name", "Firma")

    # Filtrovat transparency_page (ta jde jako standalone HTML, ne do PDF)
    pdf_keys = [k for k in eligible_keys if k != "transparency_page"]

    # Render sections
    sections_html = ""
    for key in pdf_keys:
        renderer = SECTION_RENDERERS.get(key)
        if renderer:
            try:
                sections_html += renderer(data)
            except Exception as e:
                logger.error(f"Chyba při renderování sekce {key}: {e}", exc_info=True)
                sections_html += f"""
                <div class="doc-section" id="section-{key}">
                    <div class="section-header">
                        <h2>{TEMPLATE_NAMES.get(key, key)}</h2>
                        <div class="section-sub">Chyba při generování této sekce</div>
                    </div>
                    <div class="card"><p style="color:#dc2626">Sekci se nepodařilo vygenerovat: {str(e)}</p></div>
                </div>
                """

    now = _now_str()
    year = datetime.now().year

    return f"""<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AI Act Compliance Kit — {company}</title>
    {UNIFIED_CSS}
</head>
<body>
    {_render_title_page(data)}
    {_render_toc(pdf_keys)}
    {sections_html}
    {_render_vop()}

    <div class="disclaimer">
        <strong>⚖️ Právní upozornění:</strong> Dokumenty vygenerované platformou AIshield.cz
        jsou vytvořeny na základě automatizované analýzy a informací poskytnutých klientem.
        AIshield.cz poskytuje compliance dokumentaci jako technickou pomůcku pro splnění
        požadavků Nařízení (EU) 2024/1689 (AI Act), nikoliv jako právní poradenství
        ve smyslu zák. č. 85/1996 Sb., o advokacii.
    </div>

    <div class="doc-footer">
        Vygenerováno: {now} · AIshield.cz · info@aishield.cz · +420 732 716 141<br>
        © {year} AIshield.cz — Provozovatel: Martin Haynes, IČO: 17889251
    </div>
</body>
</html>"""
