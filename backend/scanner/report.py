"""
AIshield.cz — Report Generator
Generuje strukturovaný HTML compliance report z výsledků skenu.

Report obsahuje:
- Shrnutí (kolik AI systémů, celkové riziko)
- Detail každého nalezeného AI systému
- Doporučení dle EU AI Act
- Vizuální grafy (risk breakdown)
- Timestamp a metadata
"""

import logging
from datetime import datetime, timezone
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ReportData:
    """Data pro generování reportu."""
    scan_id: str
    url: str
    company_name: str
    started_at: str
    finished_at: str
    duration_seconds: int
    total_findings: int
    ai_classified: bool
    findings: list[dict]
    false_positives: list[dict]
    screenshot_url: str | None = None


def generate_html_report(data: ReportData) -> str:
    """Vygeneruje kompletní HTML compliance report."""

    # Spočítáme risk breakdown
    risk_counts = {"high": 0, "limited": 0, "minimal": 0}
    for f in data.findings:
        level = f.get("risk_level", "minimal")
        if level in risk_counts:
            risk_counts[level] += 1

    # Celkové hodnocení
    if risk_counts["high"] > 0:
        overall_risk = "vysoké"
        overall_color = "#dc2626"
        overall_emoji = "🔴"
        overall_message = "Váš web používá AI systémy s vysokým rizikem. Je nutné okamžitě jednat."
    elif risk_counts["limited"] > 0:
        overall_risk = "omezené"
        overall_color = "#f97316"
        overall_emoji = "🟡"
        overall_message = "Váš web používá AI systémy s omezeným rizikem. Doporučujeme provést úpravy."
    elif risk_counts["minimal"] > 0:
        overall_risk = "minimální"
        overall_color = "#22c55e"
        overall_emoji = "🟢"
        overall_message = "Váš web používá AI systémy s minimálním rizikem. Základní transparence je nutná."
    else:
        overall_risk = "žádné"
        overall_color = "#6b7280"
        overall_emoji = "✅"
        overall_message = "Na vašem webu jsme nenalezli žádné AI systémy spadající pod EU AI Act."

    # Generování HTML findings
    findings_html = ""
    for i, f in enumerate(data.findings, 1):
        risk_level = f.get("risk_level", "minimal")
        risk_badge_color = {
            "high": "#dc2626",
            "limited": "#f97316",
            "minimal": "#22c55e",
        }.get(risk_level, "#6b7280")

        risk_label = {
            "high": "Vysoké riziko",
            "limited": "Omezené riziko",
            "minimal": "Minimální riziko",
        }.get(risk_level, risk_level)

        category_icon = {
            "chatbot": "🤖",
            "analytics": "📊",
            "recommender": "🎯",
            "content_gen": "🖼️",
        }.get(f.get("category", ""), "🔍")

        category_label = {
            "chatbot": "Chatbot / Konverzační AI",
            "analytics": "Analytika / Sledování",
            "recommender": "Doporučovací systém",
            "content_gen": "Generování obsahu",
        }.get(f.get("category", ""), f.get("category", ""))

        source_badge = ""
        if f.get("source") == "ai_classified":
            source_badge = '<span style="background:#f3e8ff;color:#7e22ce;padding:2px 8px;border-radius:12px;font-size:11px;margin-left:8px;">🧠 AI verified</span>'

        findings_html += f"""
        <div style="border:1px solid #e5e7eb;border-left:4px solid {risk_badge_color};border-radius:8px;padding:16px;margin-bottom:16px;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                <div>
                    <h3 style="margin:0;font-size:16px;color:#111827;">{category_icon} {f.get('name', 'Neznámý')}{source_badge}</h3>
                    <p style="margin:4px 0 0;font-size:12px;color:#6b7280;">{category_label}</p>
                </div>
                <span style="background:{risk_badge_color}15;color:{risk_badge_color};padding:4px 12px;border-radius:12px;font-size:12px;font-weight:600;white-space:nowrap;">
                    {risk_label}
                </span>
            </div>

            {f'<p style="margin:12px 0 0;font-size:13px;color:#4b5563;font-style:italic;">{f.get("ai_classification_text", "")}</p>' if f.get("ai_classification_text") else ""}

            <table style="margin-top:12px;font-size:13px;border-collapse:collapse;width:100%;">
                {f'<tr><td style="padding:4px 8px;color:#6b7280;white-space:nowrap;vertical-align:top;">📜 Článek AI Act:</td><td style="padding:4px 8px;color:#374151;">{f.get("ai_act_article", "")}</td></tr>' if f.get("ai_act_article") else ""}
                {f'<tr><td style="padding:4px 8px;color:#6b7280;white-space:nowrap;vertical-align:top;">⚡ Požadovaná akce:</td><td style="padding:4px 8px;color:#374151;">{f.get("action_required", "")}</td></tr>' if f.get("action_required") else ""}
                {f'<tr><td style="padding:4px 8px;color:#6b7280;white-space:nowrap;vertical-align:top;">🔎 Detekováno:</td><td style="padding:4px 8px;color:#374151;font-family:monospace;font-size:11px;">{f.get("signature_matched", "")}</td></tr>' if f.get("signature_matched") else ""}
            </table>
        </div>
        """

    # False positives sekce
    fp_html = ""
    if data.false_positives:
        fp_items = ""
        for f in data.false_positives:
            fp_items += f"""
            <div style="padding:8px 12px;background:#f9fafb;border:1px solid #e5e7eb;border-radius:6px;margin-bottom:8px;opacity:0.7;">
                <span style="text-decoration:line-through;color:#6b7280;font-size:13px;">
                    {f.get('name', '')}
                </span>
                <span style="float:right;background:#e5e7eb;color:#6b7280;padding:2px 8px;border-radius:12px;font-size:11px;">false-positive</span>
                {f'<p style="margin:4px 0 0;font-size:11px;color:#9ca3af;">{f.get("action_required", "")}</p>' if f.get("action_required") else ""}
            </div>
            """
        fp_html = f"""
        <div style="margin-top:24px;">
            <h3 style="font-size:14px;color:#9ca3af;margin-bottom:12px;">
                👻 Vyřazené false-positives ({len(data.false_positives)})
            </h3>
            {fp_items}
        </div>
        """

    # Screenshot sekce
    screenshot_html = ""
    if data.screenshot_url:
        screenshot_html = f"""
        <div style="margin-top:24px;">
            <h3 style="font-size:16px;color:#111827;margin-bottom:12px;">📸 Screenshot webu</h3>
            <img src="{data.screenshot_url}" alt="Screenshot {data.url}"
                 style="max-width:100%;border:1px solid #e5e7eb;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1);" />
        </div>
        """

    # Hlavní report
    now = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")

    html = f"""<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Act Compliance Report — {data.company_name}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #111827; background: #f9fafb; }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 32px 24px; }}
        .header {{ text-align: center; padding: 40px 0 32px; }}
        .card {{ background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
        .risk-chart {{ display: flex; gap: 16px; justify-content: center; margin-top: 16px; }}
        .risk-item {{ text-align: center; padding: 12px 20px; border-radius: 8px; min-width: 100px; }}
        .footer {{ text-align: center; padding: 32px 0; color: #9ca3af; font-size: 12px; }}
        @media print {{
            body {{ background: white; }}
            .card {{ box-shadow: none; border: 1px solid #d1d5db; page-break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div style="font-size:48px;margin-bottom:16px;">🛡️</div>
            <h1 style="font-size:28px;font-weight:700;color:#111827;">AI Act Compliance Report</h1>
            <p style="font-size:16px;color:#6b7280;margin-top:8px;">{data.company_name}</p>
            <p style="font-size:13px;color:#9ca3af;margin-top:4px;">Vygenerováno: {now}</p>
        </div>

        <!-- Celkové hodnocení -->
        <div class="card" style="text-align:center;border-top:4px solid {overall_color};">
            <div style="font-size:36px;">{overall_emoji}</div>
            <h2 style="font-size:20px;margin-top:8px;color:{overall_color};">
                Celkové riziko: {overall_risk.upper()}
            </h2>
            <p style="font-size:14px;color:#4b5563;margin-top:8px;">{overall_message}</p>

            <div class="risk-chart">
                <div class="risk-item" style="background:#fef2f2;">
                    <div style="font-size:24px;font-weight:700;color:#dc2626;">{risk_counts['high']}</div>
                    <div style="font-size:11px;color:#991b1b;">Vysoké</div>
                </div>
                <div class="risk-item" style="background:#fff7ed;">
                    <div style="font-size:24px;font-weight:700;color:#f97316;">{risk_counts['limited']}</div>
                    <div style="font-size:11px;color:#9a3412;">Omezené</div>
                </div>
                <div class="risk-item" style="background:#f0fdf4;">
                    <div style="font-size:24px;font-weight:700;color:#22c55e;">{risk_counts['minimal']}</div>
                    <div style="font-size:11px;color:#166534;">Minimální</div>
                </div>
            </div>
        </div>

        <!-- Metadata skenu -->
        <div class="card">
            <h3 style="font-size:16px;color:#111827;margin-bottom:12px;">📋 Informace o skenu</h3>
            <table style="width:100%;font-size:13px;border-collapse:collapse;">
                <tr>
                    <td style="padding:6px 0;color:#6b7280;width:180px;">Skenovaná URL:</td>
                    <td style="padding:6px 0;color:#111827;font-weight:500;">{data.url}</td>
                </tr>
                <tr>
                    <td style="padding:6px 0;color:#6b7280;">Firma:</td>
                    <td style="padding:6px 0;color:#111827;">{data.company_name}</td>
                </tr>
                <tr>
                    <td style="padding:6px 0;color:#6b7280;">Scan ID:</td>
                    <td style="padding:6px 0;color:#111827;font-family:monospace;font-size:12px;">{data.scan_id}</td>
                </tr>
                <tr>
                    <td style="padding:6px 0;color:#6b7280;">Zahájeno:</td>
                    <td style="padding:6px 0;color:#111827;">{data.started_at or '—'}</td>
                </tr>
                <tr>
                    <td style="padding:6px 0;color:#6b7280;">Dokončeno:</td>
                    <td style="padding:6px 0;color:#111827;">{data.finished_at or '—'}</td>
                </tr>
                <tr>
                    <td style="padding:6px 0;color:#6b7280;">Doba skenu:</td>
                    <td style="padding:6px 0;color:#111827;">{data.duration_seconds}s</td>
                </tr>
                <tr>
                    <td style="padding:6px 0;color:#6b7280;">AI klasifikace:</td>
                    <td style="padding:6px 0;color:#111827;">{'🧠 Claude AI verified' if data.ai_classified else '⚙️ Signaturová detekce'}</td>
                </tr>
                <tr>
                    <td style="padding:6px 0;color:#6b7280;">Nalezené AI systémy:</td>
                    <td style="padding:6px 0;color:#111827;font-weight:700;font-size:16px;">{data.total_findings}</td>
                </tr>
            </table>
        </div>

        <!-- Nalezené AI systémy -->
        <div class="card">
            <h3 style="font-size:16px;color:#111827;margin-bottom:16px;">
                🤖 Nalezené AI systémy ({data.total_findings})
            </h3>
            {findings_html if data.findings else '<p style="text-align:center;color:#6b7280;padding:24px;">Žádné AI systémy nenalezeny ✅</p>'}
        </div>

        {fp_html}
        {screenshot_html}

        <!-- Doporučení -->
        <div class="card" style="border-top:4px solid #3b82f6;">
            <h3 style="font-size:16px;color:#111827;margin-bottom:12px;">💡 Obecná doporučení dle EU AI Act</h3>
            <ol style="font-size:13px;color:#374151;padding-left:20px;line-height:1.8;">
                <li><strong>Transparence (čl. 50):</strong> Informujte uživatele, že komunikují s AI systémem.</li>
                <li><strong>Cookie banner:</strong> Aktualizujte cookie banner o informace o AI zpracování.</li>
                <li><strong>Privacy policy:</strong> Doplňte do zásad ochrany osobních údajů informace o AI.</li>
                <li><strong>Lidský dohled:</strong> Zajistěte možnost přepojení na lidského operátora u chatbotů.</li>
                <li><strong>Registr AI systémů:</strong> Veďte interní evidenci všech AI systémů na webu.</li>
                <li><strong>DPIA:</strong> Pro systémy s omezeným/vysokým rizikem proveďte posouzení dopadu.</li>
            </ol>
        </div>

        <!-- Disclaimer -->
        <div class="card" style="background:#fffbeb;border-color:#fde68a;">
            <p style="font-size:12px;color:#92400e;">
                ⚠️ <strong>Upozornění:</strong> Tento report je automaticky generovaný a slouží jako orientační pomůcka.
                Nenahrazuje právní poradenství. Pro závazné posouzení souladu s EU AI Act doporučujeme konzultaci
                s právníkem specializovaným na AI regulaci. Detekce AI systémů probíhá na základě analýzy HTML,
                skriptů, cookies a síťových požadavků — některé AI systémy nemusí být detekovatelné touto metodou.
            </p>
        </div>

        <!-- Footer -->
        <div class="footer">
            <p>🛡️ AIshield.cz — AI Act Compliance pro české firmy</p>
            <p style="margin-top:4px;">info@desperados-design.cz | +420 732 716 141</p>
            <p style="margin-top:8px;">© {datetime.now().year} AIshield.cz | Všechna práva vyhrazena</p>
        </div>
    </div>
</body>
</html>"""

    logger.info(f"[Report] HTML report vygenerován: {len(html)} znaků, {data.total_findings} nálezů")
    return html
