"""
AIshield.cz — Scan Report Email Template
Branded HTML email with scan results, pricing info, and contact CTA.
"""

from backend.outbound.email_templates import BRAND

RISK_LABELS = {
    "high": "Vysoké riziko",
    "limited": "Omezené riziko",
    "minimal": "Minimální riziko",
}

RISK_COLORS = {
    "high": {"bg": "#fef2f2", "border": "#fca5a5", "text": "#991b1b", "dot": "#ef4444"},
    "limited": {"bg": "#fefce8", "border": "#fde047", "text": "#854d0e", "dot": "#eab308"},
    "minimal": {"bg": "#f0fdf4", "border": "#86efac", "text": "#166534", "dot": "#22c55e"},
}

CATEGORY_LABELS = {
    "chatbot": "Chatbot / Konverzační AI",
    "analytics": "Analytika / Sledování",
    "recommender": "Doporučovací systém",
    "content_gen": "Generování obsahu",
}


def generate_report_email_html(
    url: str,
    company_name: str,
    findings: list[dict],
    scan_id: str,
) -> str:
    """Generate branded HTML email with scan results."""

    findings_count = len(findings)
    high_count = sum(1 for f in findings if f.get("risk_level") == "high")
    limited_count = sum(1 for f in findings if f.get("risk_level") == "limited")
    minimal_count = sum(1 for f in findings if f.get("risk_level") == "minimal")

    # Plural helper
    if findings_count == 1:
        sys_word = "systém"
    elif findings_count < 5:
        sys_word = "systémy"
    else:
        sys_word = "systémů"

    # Build findings rows
    findings_html = ""
    for f in findings:
        rl = f.get("risk_level", "minimal")
        colors = RISK_COLORS.get(rl, RISK_COLORS["minimal"])
        cat_label = CATEGORY_LABELS.get(f.get("category", ""), f.get("category", ""))
        name = f.get("name", "")
        ai_text = f.get("ai_classification_text", "")
        article = f.get("ai_act_article", "")
        action = f.get("action_required", "")

        ai_text_html = ""
        if ai_text:
            ai_text_html = (
                f'<div style="font-size:13px;color:{BRAND["text_light"]};'
                f'margin-top:8px;font-style:italic;">{ai_text}</div>'
            )

        article_html = ""
        if article:
            article_html = (
                f'<div style="margin-top:8px;font-size:13px;">'
                f'<span style="color:{BRAND["text_light"]};">Článek:</span> '
                f'<span style="color:{BRAND["text"]};">{article}</span></div>'
            )

        action_html = ""
        if action:
            action_html = (
                f'<div style="margin-top:4px;font-size:13px;">'
                f'<span style="color:{BRAND["text_light"]};">Co udělat:</span> '
                f'<span style="color:{BRAND["text"]};">{action}</span></div>'
            )

        risk_label = RISK_LABELS.get(rl, rl)

        findings_html += f"""
        <tr>
            <td style="padding:16px;border-bottom:1px solid {BRAND["border"]};">
                <div style="font-weight:600;color:{BRAND["text"]};font-size:15px;">{name}</div>
                <div style="font-size:12px;color:{BRAND["text_light"]};margin-top:2px;">{cat_label}</div>
                {ai_text_html}
                {article_html}
                {action_html}
            </td>
            <td style="padding:16px;border-bottom:1px solid {BRAND["border"]};text-align:center;vertical-align:top;">
                <span style="display:inline-block;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;background:{colors['bg']};color:{colors['text']};border:1px solid {colors['border']};">
                    {risk_label}
                </span>
            </td>
        </tr>"""

    # Risk overview boxes
    risk_boxes = ""
    if high_count:
        risk_boxes += (
            '<td style="text-align:center;padding:12px;background:#fef2f2;'
            'border-radius:12px;border:1px solid #fca5a5;">'
            f'<div style="font-size:28px;font-weight:700;color:#ef4444;">{high_count}</div>'
            '<div style="font-size:12px;color:#991b1b;">Vysoké riziko</div></td>'
        )
    if limited_count:
        risk_boxes += (
            '<td style="text-align:center;padding:12px;background:#fefce8;'
            'border-radius:12px;border:1px solid #fde047;">'
            f'<div style="font-size:28px;font-weight:700;color:#eab308;">{limited_count}</div>'
            '<div style="font-size:12px;color:#854d0e;">Omezené riziko</div></td>'
        )
    if minimal_count:
        risk_boxes += (
            '<td style="text-align:center;padding:12px;background:#f0fdf4;'
            'border-radius:12px;border:1px solid #86efac;">'
            f'<div style="font-size:28px;font-weight:700;color:#22c55e;">{minimal_count}</div>'
            '<div style="font-size:12px;color:#166534;">Minimální riziko</div></td>'
        )

    risk_table = ""
    if risk_boxes:
        risk_table = (
            '<div style="margin:0 24px 24px;">'
            '<table style="width:100%;border-collapse:separate;border-spacing:8px 0;">'
            f'<tr>{risk_boxes}</tr></table></div>'
        )

    html = f"""<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIshield.cz — Výsledky skenu</title>
</head>
<body style="margin:0;padding:0;background:{BRAND["bg_light"]};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
    <div style="max-width:640px;margin:0 auto;background:{BRAND["bg"]};">

        <!-- HEADER -->
        <div style="background:linear-gradient(135deg,{BRAND["gradient_start"]},{BRAND["gradient_mid"]},{BRAND["gradient_end"]});padding:32px 24px;text-align:center;">
            <div style="font-size:24px;font-weight:700;color:#ffffff;letter-spacing:-0.5px;">AIshield.cz</div>
            <div style="font-size:14px;color:{BRAND["accent_light"]};margin-top:4px;">Výsledky AI Act compliance skenu</div>
        </div>

        <!-- RED WARNING -->
        <div style="margin:24px;padding:20px;background:#fef2f2;border:2px solid #fca5a5;border-radius:12px;">
            <div style="font-size:16px;font-weight:700;color:#991b1b;">Na vašem webu byly nalezeny AI systémy bez povinného označení</div>
            <p style="font-size:14px;color:#7f1d1d;margin-top:8px;line-height:1.6;">
                Na webu <strong>{url}</strong> jsme nalezli <strong>{findings_count} AI {sys_word}</strong>,
                které nejsou označeny pro návštěvníky.
                Od <strong>2. srpna 2026</strong> je toto porušením EU AI Act (Nařízení 2024/1689, čl. 50)
                a hrozí pokuta <strong>až 15 milionů EUR nebo 3 % obratu</strong>.
            </p>
        </div>

        <!-- SUMMARY -->
        <div style="margin:0 24px 24px;padding:20px;background:{BRAND["bg_light"]};border:1px solid {BRAND["border"]};border-radius:12px;">
            <table style="width:100%;border-collapse:collapse;">
                <tr>
                    <td style="padding:6px 0;font-size:14px;color:{BRAND["text_light"]};">Skenovaný web</td>
                    <td style="padding:6px 0;font-size:14px;font-weight:600;color:{BRAND["text"]};text-align:right;">{url}</td>
                </tr>
                <tr>
                    <td style="padding:6px 0;font-size:14px;color:{BRAND["text_light"]};">Firma</td>
                    <td style="padding:6px 0;font-size:14px;font-weight:600;color:{BRAND["text"]};text-align:right;">{company_name}</td>
                </tr>
                <tr>
                    <td style="padding:6px 0;font-size:14px;color:{BRAND["text_light"]};">Nalezené AI systémy</td>
                    <td style="padding:6px 0;font-size:22px;font-weight:700;color:{BRAND["text"]};text-align:right;">{findings_count}</td>
                </tr>
            </table>
        </div>

        <!-- RISK BOXES -->
        {risk_table}

        <!-- WHAT IT MEANS -->
        <div style="margin:0 24px 24px;padding:16px;background:#fffbeb;border:1px solid #fde68a;border-radius:12px;">
            <p style="font-size:14px;color:#92400e;margin:0;line-height:1.6;">
                <strong style="color:{BRAND["text"]};">Váš web musí být upraven.</strong>
                Nalezené AI systémy vyžadují buď označení pro návštěvníky, interní evidenci, nebo obojí.
                Bez úprav riskujete pokutu dle EU AI Act.
            </p>
        </div>

        <!-- FINDINGS TABLE -->
        <div style="margin:0 24px 24px;">
            <div style="font-size:16px;font-weight:700;color:{BRAND["text"]};margin-bottom:12px;">
                Nalezené AI systémy ({findings_count})
            </div>
            <table style="width:100%;border-collapse:collapse;border:1px solid {BRAND["border"]};border-radius:12px;overflow:hidden;">
                <tr style="background:{BRAND["bg_light"]};">
                    <th style="padding:12px 16px;text-align:left;font-size:13px;color:{BRAND["text_light"]};font-weight:600;border-bottom:1px solid {BRAND["border"]};">Nález</th>
                    <th style="padding:12px 16px;text-align:center;font-size:13px;color:{BRAND["text_light"]};font-weight:600;border-bottom:1px solid {BRAND["border"]};">Riziko</th>
                </tr>
                {findings_html}
            </table>
        </div>

        <!-- BOTTOM WARNING -->
        <div style="margin:0 24px 24px;padding:16px;background:#fef2f2;border:2px solid #fca5a5;border-radius:12px;">
            <div style="font-size:14px;font-weight:700;color:#991b1b;">Důležité: Toto musíte řešit</div>
            <p style="font-size:13px;color:#7f1d1d;margin-top:6px;line-height:1.5;">
                Výše uvedené AI systémy na vašem webu nemají povinné oznámení pro návštěvníky.
                Dle EU AI Act (čl. 50) musí být návštěvníkům jasně sděleno, že komunikují s AI.
                Povinnost platí od 2. srpna 2026.
            </p>
        </div>

        <!-- PRICING CTA -->
        <div style="margin:0 24px 24px;padding:24px;background:linear-gradient(135deg,{BRAND["gradient_start"]},{BRAND["gradient_mid"]});border-radius:12px;text-align:center;">
            <div style="font-size:18px;font-weight:700;color:#ffffff;">Chcete to vyřešit za vás?</div>
            <p style="font-size:14px;color:{BRAND["accent_light"]};margin-top:8px;line-height:1.5;">
                Připravíme kompletní dokumentaci, transparenční stránku a vše potřebné pro soulad s AI Act.
            </p>
            <div style="margin-top:16px;">
                <a href="https://aishield.cz/pricing" style="display:inline-block;padding:12px 32px;background:{BRAND["accent"]};color:#ffffff;font-weight:600;font-size:14px;border-radius:8px;text-decoration:none;">
                    Zobrazit ceník služeb
                </a>
            </div>
        </div>

        <!-- CONTACT -->
        <div style="margin:0 24px 24px;padding:20px;background:{BRAND["bg_light"]};border:1px solid {BRAND["border"]};border-radius:12px;text-align:center;">
            <div style="font-size:15px;font-weight:600;color:{BRAND["text"]};">Máte otázky? Ozvěte se nám</div>
            <div style="margin-top:10px;font-size:14px;color:{BRAND["text_light"]};">
                <a href="mailto:info@aishield.cz" style="color:{BRAND["accent"]};text-decoration:none;">info@aishield.cz</a>
                &nbsp;&nbsp;|&nbsp;&nbsp;
                <a href="tel:+420773216877" style="color:{BRAND["accent"]};text-decoration:none;">+420 773 216 877</a>
            </div>
        </div>

        <!-- FOOTER -->
        <div style="background:linear-gradient(135deg,{BRAND["gradient_start"]},{BRAND["gradient_mid"]});padding:24px;text-align:center;">
            <div style="font-size:13px;color:{BRAND["accent_light"]};">AIshield.cz — AI Act compliance pro české firmy</div>
            <div style="font-size:11px;color:#94a3b8;margin-top:8px;">
                Tento email byl vygenerován na základě automatického skenu webu {url}.
                <br>2025 AIshield.cz | Desperados-design.cz
            </div>
        </div>

    </div>
</body>
</html>"""

    return html
