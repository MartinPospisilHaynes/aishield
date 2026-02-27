"""
AIshield.cz — Cover Page & TOC Generator

Generates:
  - Page 1: Professional cover page with AIshield branding
  - Page 2: Table of contents with document listing

Output: PDF bytes (doc #00 in the compliance kit binder)
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# AIshield logo as inline SVG (purple shield + AI text)
AISHIELD_LOGO_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 60" width="200" height="60">
  <!-- Shield -->
  <path d="M30 5 L55 15 L55 35 C55 50 30 58 30 58 C30 58 5 50 5 35 L5 15 Z"
        fill="#7c3aed" stroke="#5b21b6" stroke-width="1.5"/>
  <!-- AI text inside shield -->
  <text x="30" y="38" text-anchor="middle" font-family="Inter,Arial,sans-serif"
        font-weight="700" font-size="18" fill="white">AI</text>
  <!-- Brand name -->
  <text x="70" y="30" font-family="Inter,Arial,sans-serif" font-weight="700"
        font-size="22" fill="#0f172a">
    <tspan>AI</tspan><tspan fill="#7c3aed">shield</tspan><tspan fill="#94a3b8" font-size="14">.cz</tspan>
  </text>
  <!-- Tagline -->
  <text x="70" y="48" font-family="Inter,Arial,sans-serif" font-weight="400"
        font-size="10" fill="#64748b">AI Act Compliance Kit</text>
</svg>
"""

# Documents included in the print binder (ordered)
PRINT_DOCUMENTS = [
    ("01", "compliance_report",            "Compliance Report"),
    ("02", "action_plan",                  "Akční plán implementace"),
    ("03", "ai_register",                  "Registr AI systémů"),
    ("04", "training_outline",             "Plán školení AI Literacy"),
    ("05", "chatbot_notices",              "Texty oznámení o AI"),
    ("06", "ai_policy",                    "Interní AI politika"),
    ("07", "incident_response_plan",       "Plán řízení incidentů"),
    ("08", "dpia_template",                "Posouzení dopadů (DPIA/FRIA)"),
    ("09", "vendor_checklist",             "Dodavatelský checklist"),
    ("10", "monitoring_plan",              "Monitoring plán AI systémů"),
    ("11", "transparency_human_oversight", "Transparentnost a lidský dohled"),
]

# Non-printable documents (listed in TOC as digital-only appendices)
DIGITAL_DOCUMENTS = [
    ("A1", "transparency_page",      "Transparenční stránka (HTML)"),
    ("A2", "training_presentation",  "Školící prezentace (PPTX)"),
]


def render_cover_page_html(
    company_name: str,
    project_title: str = "AI Act Compliance Kit",
    generation_date: str = None,
    generation_id: str = None,
) -> str:
    """
    Generates cover page HTML with AIshield branding + TOC on page 2.
    Returns standalone HTML ready for WeasyPrint PDF conversion.
    """
    if not generation_date:
        generation_date = datetime.now().strftime("%d. %m. %Y")

    # Build TOC items
    toc_items = []
    for num, key, name in PRINT_DOCUMENTS:
        toc_items.append(
            f'<tr><td style="font-weight:600;color:#7c3aed;width:40px;">{num}</td>'
            f'<td>{name}</td></tr>'
        )

    # Digital appendices
    digital_items = []
    for num, key, name in DIGITAL_DOCUMENTS:
        digital_items.append(
            f'<tr><td style="font-weight:600;color:#94a3b8;width:40px;">{num}</td>'
            f'<td style="color:#64748b;">{name} <em>(pouze digitální)</em></td></tr>'
        )

    toc_html = "\n".join(toc_items)
    digital_html = "\n".join(digital_items)

    gen_id_line = ""
    if generation_id:
        gen_id_line = f'<div style="font-size:8pt;color:#94a3b8;margin-top:4pt;">ID: {generation_id}</div>'

    return f"""<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="utf-8">
    <title>AI Act Compliance Kit — {company_name}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        @page {{
            size: A4;
            margin: 0;
        }}

        @page content {{
            margin: 22mm 18mm 25mm 18mm;
        }}

        body {{
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 0;
            color: #1e293b;
        }}

        /* ── COVER PAGE ── */
        .cover {{
            width: 210mm;
            height: 297mm;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            position: relative;
            page: auto;
        }}

        .cover-top-bar {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 8mm;
            background: linear-gradient(135deg, #7c3aed, #5b21b6);
        }}

        .cover-bottom-bar {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 3mm;
            background: linear-gradient(135deg, #7c3aed, #5b21b6);
        }}

        .cover-logo {{
            margin-bottom: 30mm;
        }}

        .cover-title {{
            font-size: 28pt;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 8pt;
            letter-spacing: -0.5pt;
        }}

        .cover-subtitle {{
            font-size: 14pt;
            font-weight: 400;
            color: #7c3aed;
            margin-bottom: 25mm;
        }}

        .cover-company {{
            font-size: 18pt;
            font-weight: 600;
            color: #334155;
            padding: 10pt 30pt;
            border: 2pt solid #e2e8f0;
            border-radius: 4pt;
            margin-bottom: 10mm;
        }}

        .cover-date {{
            font-size: 11pt;
            color: #64748b;
        }}

        .cover-footer {{
            position: absolute;
            bottom: 15mm;
            font-size: 8pt;
            color: #94a3b8;
        }}

        /* ── TOC PAGE ── */
        .toc {{
            page: content;
            page-break-before: always;
            padding: 0 18mm;
        }}

        .toc h1 {{
            font-size: 18pt;
            font-weight: 700;
            color: #0f172a;
            margin-top: 5mm;
            margin-bottom: 8mm;
            padding-bottom: 4pt;
            border-bottom: 3pt solid #7c3aed;
        }}

        .toc h2 {{
            font-size: 11pt;
            font-weight: 600;
            color: #334155;
            margin-top: 10mm;
            margin-bottom: 4mm;
        }}

        .toc table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 10pt;
        }}

        .toc td {{
            padding: 5pt 8pt;
            border-bottom: 1pt solid #e2e8f0;
        }}

        .toc tr:hover td {{
            background: #f8fafc;
        }}

        .toc-note {{
            margin-top: 10mm;
            font-size: 8pt;
            color: #94a3b8;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <!-- PAGE 1: COVER -->
    <div class="cover">
        <div class="cover-top-bar"></div>
        <div class="cover-logo">
            {AISHIELD_LOGO_SVG}
        </div>
        <div class="cover-title">AI Act Compliance Kit</div>
        <div class="cover-subtitle">Dokumentace souladu s nařízením EU o umělé inteligenci</div>
        <div class="cover-company">{company_name}</div>
        <div class="cover-date">
            Vypracováno: {generation_date}
            {gen_id_line}
        </div>
        <div class="cover-bottom-bar"></div>
        <div class="cover-footer">
            AIshield.cz | Důvěrné — pouze pro interní potřebu objednatele
        </div>
    </div>

    <!-- PAGE 2: TABLE OF CONTENTS -->
    <div class="toc">
        <h1>Obsah dokumentace</h1>

        <h2>Tištěné dokumenty (sešit)</h2>
        <table>
            <thead>
                <tr>
                    <th style="width:40px;text-align:left;font-size:9pt;color:#94a3b8;">Č.</th>
                    <th style="text-align:left;font-size:9pt;color:#94a3b8;">Název dokumentu</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="font-weight:600;color:#7c3aed;">00</td>
                    <td>Titulní strana a obsah <em>(tento dokument)</em></td>
                </tr>
                {toc_html}
            </tbody>
        </table>

        <h2>Digitální přílohy</h2>
        <table>
            <tbody>
                {digital_html}
            </tbody>
        </table>

        <div class="toc-note">
            Všechny dokumenty tvoří celek AI Act Compliance Kit
            a jsou platné k datu {generation_date}.<br>
            Dokumenty 01–11 jsou určeny pro tisk. Přílohy A1–A2 jsou dodávány výhradně v digitální podobě.
        </div>
    </div>
</body>
</html>"""
