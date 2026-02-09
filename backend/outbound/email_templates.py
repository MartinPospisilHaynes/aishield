"""
AIshield.cz — Email Templates v4 (HYBRID)
Krásná HTML šablona + vložitelné AI-personalizované sekce od Gemini.

Vizuální prvky (šablona):
- Hlavička s logem/brandem a gradientem
- Tabulka rizik se semaforem (🟢🟡🔴)
- Screenshot webu
- Deadline box (⏰ 2. srpna 2026)
- Checklist "Co musíte udělat"
- USP box "Proč AIshield.cz"
- CTA tlačítko
- Profesionální footer → CEO Bc. Martin Haynes

Personalizované sekce (Gemini):
- Oslovení + úvod (kdo jsem, proč píšu)
- Komentář k nálezům (co konkrétně jsem našel)
- Dopad na klienta (co se stane, když neřeší)
"""

from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import quote


@dataclass
class EmailVariant:
    """Email varianta pro odeslání."""
    subject: str
    body_html: str
    variant_id: str = "hybrid_v4"


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


def _risk_table_html(findings: list[FindingRow]) -> str:
    """Krásná tabulka rizik se semaforem."""
    if not findings:
        return ""

    rows = ""
    for f in findings:
        badge = RISK_BADGE.get(f.risk_level, RISK_BADGE["limited"])
        rows += f"""
            <tr>
                <td style="padding: 12px 16px; border-bottom: 1px solid #f1f5f9; font-size: 14px; color: {BRAND['text']};">
                    <strong>{f.name}</strong>
                    {f'<br><span style="font-size: 12px; color: {BRAND["text_light"]};">{f.description}</span>' if f.description else ''}
                </td>
                <td style="padding: 12px 8px; border-bottom: 1px solid #f1f5f9; text-align: center;">
                    <span style="display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; background: {badge['bg']}; color: {badge['color']};">
                        {badge['icon']} {badge['label']}
                    </span>
                </td>
                <td style="padding: 12px 16px; border-bottom: 1px solid #f1f5f9; font-size: 13px; color: {BRAND['text_light']};">
                    {f.ai_act_article}
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


def _deadline_box() -> str:
    """Deadline box s odpočítáváním."""
    days = _days_to_deadline()

    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="margin: 24px 0;">
        <tr>
            <td style="padding: 16px 20px; background: linear-gradient(135deg, #fefce8, #fef9c3); border: 1px solid #fde68a; border-radius: 8px; border-left: 4px solid {BRAND['warning']};">
                <table width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                        <td style="font-size: 28px; width: 40px; vertical-align: top; padding-right: 12px;">&#9200;</td>
                        <td>
                            <p style="margin: 0 0 4px 0; font-size: 15px; font-weight: 700; color: #92400e;">
                                Deadline: 2. srpna 2026
                            </p>
                            <p style="margin: 0; font-size: 13px; color: #a16207;">
                                Do plné účinnosti AI Act zbývá <strong>{days} dní</strong>.
                                Příprava compliance dokumentace zabere cca 2–4 týdny.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>"""


def _checklist_box() -> str:
    """Co musíte udělat — checklist."""
    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="margin: 20px 0;">
        <tr>
            <td style="padding: 16px 20px; background: {BRAND['bg_light']}; border: 1px solid {BRAND['border']}; border-radius: 8px;">
                <p style="margin: 0 0 12px 0; font-size: 15px; font-weight: 700; color: {BRAND['text']};">
                    Co je potřeba udělat
                </p>
                <table cellpadding="0" cellspacing="0" style="font-size: 14px; color: {BRAND['text']}; line-height: 1.8;">
                    <tr><td style="padding: 2px 8px 2px 0; color: #22c55e; font-size: 16px;">&#10003;</td><td>Označit AI systémy na webu dle čl. 50 AI Act</td></tr>
                    <tr><td style="padding: 2px 8px 2px 0; color: #22c55e; font-size: 16px;">&#10003;</td><td>Informovat uživatele, že komunikují s AI</td></tr>
                    <tr><td style="padding: 2px 8px 2px 0; color: #22c55e; font-size: 16px;">&#10003;</td><td>Dokumentovat použité AI systémy a jejich účel</td></tr>
                    <tr><td style="padding: 2px 8px 2px 0; color: #22c55e; font-size: 16px;">&#10003;</td><td>Zavést proces průběžného monitoringu</td></tr>
                </table>
            </td>
        </tr>
    </table>"""


def _usp_box() -> str:
    """USP box — proč AIshield.cz."""
    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="margin: 24px 0;">
        <tr>
            <td style="padding: 20px; background: linear-gradient(135deg, #f5f3ff, #ede9fe); border: 1px solid #c4b5fd; border-radius: 8px;">
                <p style="margin: 0 0 10px 0; font-size: 15px; font-weight: 700; color: {BRAND['accent']};">
                    &#128737; AIshield.cz — kompletní řešení AI Act compliance
                </p>
                <table cellpadding="0" cellspacing="0" style="font-size: 13px; color: {BRAND['text']}; line-height: 1.7;">
                    <tr><td style="padding: 2px 8px 2px 0;">&#8594;</td><td><strong>Automatický scan</strong> všech AI systémů na webu</td></tr>
                    <tr><td style="padding: 2px 8px 2px 0;">&#8594;</td><td><strong>Compliance report</strong> s konkrétními kroky k nápravě</td></tr>
                    <tr><td style="padding: 2px 8px 2px 0;">&#8594;</td><td><strong>Průběžný monitoring</strong> a alerting na nové AI systémy</td></tr>
                    <tr><td style="padding: 2px 8px 2px 0;">&#8594;</td><td><strong>Dokumentace a štítky</strong> připravené k nasazení</td></tr>
                </table>
                <p style="margin: 12px 0 0 0; font-size: 14px; color: {BRAND['accent']}; font-weight: 600;">
                    Jednorázově od 4 999 Kč &middot; PRO balíček 14 999 Kč
                </p>
            </td>
        </tr>
    </table>"""


def _cta_button(report_link: str) -> str:
    """CTA tlačítko — zobrazit report."""
    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="margin: 24px 0;">
        <tr>
            <td align="center">
                <!--[if mso]>
                <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml"
                    href="{report_link}" style="height:48px;v-text-anchor:middle;width:280px;"
                    arcsize="17%" fillcolor="{BRAND['accent']}">
                <center style="color:#ffffff;font-family:Arial;font-size:15px;font-weight:bold;">
                    Zobrazit compliance report &rarr;
                </center>
                </v:roundrect>
                <![endif]-->
                <!--[if !mso]><!-->
                <a href="{report_link}"
                   style="display: inline-block; padding: 14px 32px; background: {BRAND['accent']};
                          color: #ffffff; font-size: 15px; font-weight: 600; text-decoration: none;
                          border-radius: 8px; letter-spacing: 0.3px;">
                    Zobrazit compliance report &#8594;
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
                            <span style="font-size: 22px; font-weight: 700; color: #ffffff; letter-spacing: -0.5px;">
                                &#128737; AIshield.cz
                            </span>
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
    """Profesionální footer."""
    unsubscribe = ""
    if to_email:
        unsubscribe = f'https://api.aishield.cz/api/unsubscribe?email={quote(to_email)}&company={quote(company_url)}'

    unsub_link = ""
    if unsubscribe:
        unsub_link = f' &middot; <a href="{unsubscribe}" style="color: #94a3b8; text-decoration: underline;">Odhlásit se</a>'

    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" style="margin-top: 32px; border-top: 1px solid {BRAND['border']};">
        <tr>
            <td style="padding: 20px 0 0 0;">
                <p style="margin: 0 0 4px 0; font-size: 13px; color: {BRAND['text']};">
                    <strong>Bc. Martin Haynes</strong> — CEO, AIshield.cz
                </p>
                <p style="margin: 0 0 12px 0; font-size: 13px; color: {BRAND['text_light']};">
                    &#128222; +420 732 716 141 &middot; &#9993; info@aishield.cz &middot; &#127760; aishield.cz
                </p>
                <p style="margin: 0; font-size: 11px; color: #94a3b8; line-height: 1.5;">
                    Jednorázové upozornění na základě veřejně dostupné analýzy webu {company_url}.<br>
                    AIshield.cz &middot; IČO: 17889251 &middot; Mlýnská 53, 783 53 Velká Bystřice{unsub_link}
                </p>
            </td>
        </tr>
    </table>"""


def build_hybrid_email(
    gemini_intro: str,
    gemini_findings_commentary: str,
    gemini_impact: str,
    company_url: str,
    findings: list[FindingRow],
    screenshot_url: str = "",
    scan_id: str = "",
    to_email: str = "",
) -> str:
    """
    Sestaví krásný HYBRID email:
    - Header, tabulka, deadline, CTA = šablona
    - Intro, komentář k nálezům, dopad = Gemini
    """
    report_link = (
        f"https://aishield.cz/report/{scan_id}"
        if scan_id
        else f"https://aishield.cz/scan?url={company_url}"
    )

    # Gemini text → HTML (newlines → <br>)
    def to_html(text: str) -> str:
        if not text:
            return ""
        # Pokud Gemini vrátil HTML tagy, necháme je
        if "<p>" in text or "<br" in text:
            return text
        return text.replace("\n\n", "</p><p>").replace("\n", "<br>")

    intro_html = to_html(gemini_intro)
    findings_html = to_html(gemini_findings_commentary)
    impact_html = to_html(gemini_impact)

    risk_table = _risk_table_html(findings)
    screenshot = _screenshot_section(screenshot_url, company_url)
    deadline = _deadline_box()
    checklist = _checklist_box()
    usp = _usp_box()
    cta = _cta_button(report_link)
    header = _header_html(company_url)
    footer = _footer_html(company_url, to_email)

    return f"""<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIshield.cz — AI Act compliance report</title>
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

                        <!-- Personalizovaný úvod (Gemini) -->
                        <div style="font-size: 15px; line-height: 1.65; color: {BRAND['text']};">
                            <p style="margin: 0 0 16px 0;">{intro_html}</p>
                        </div>

                        <!-- Screenshot -->
                        {screenshot}

                        <!-- Tabulka rizik (šablona) -->
                        {risk_table}

                        <!-- Komentář k nálezům (Gemini) -->
                        <div style="font-size: 14px; line-height: 1.65; color: {BRAND['text']}; margin: 16px 0;">
                            <p style="margin: 0;">{findings_html}</p>
                        </div>

                        <!-- Deadline box (šablona) -->
                        {deadline}

                        <!-- Dopad na klienta (Gemini) -->
                        <div style="font-size: 14px; line-height: 1.65; color: {BRAND['text']}; margin: 16px 0;">
                            <p style="margin: 0;">{impact_html}</p>
                        </div>

                        <!-- Checklist (šablona) -->
                        {checklist}

                        <!-- USP box (šablona) -->
                        {usp}

                        <!-- CTA tlačítko (šablona) -->
                        {cta}

                        <!-- Footer -->
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
    """Follow-up email — čistý styl s vizuálním designem."""
    report_link = (
        f"https://aishield.cz/report/{scan_id}"
        if scan_id
        else f"https://aishield.cz/scan?url={company_url}"
    )
    days = _days_to_deadline()

    header = _header_html(company_url)
    cta = _cta_button(report_link)
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
                            <p>před {days_since} dny jsem vám poslal upozornění k AI systémům
                            na webu <strong>{company_url}</strong>.</p>
                            <p>Chápu, že to nemusí být priorita — jen pro kontext:
                            do plné účinnosti AI Act zbývá <strong>{days} dní</strong>
                            a příprava compliance dokumentace nějaký čas zabere.</p>
                            <p>Váš report je stále k dispozici:</p>
                        </div>
                        {cta}
                        <div style="font-size: 14px; line-height: 1.65; color: {BRAND['text']};">
                            <p>Pokud to řešíte s někým jiným nebo to nepotřebujete,
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


# ── Zpětná kompatibilita s email_engine.py ──
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
    """Fallback pro email_engine.py — pokud se volá bez Gemini."""
    report_link = (
        f"https://aishield.cz/report/{scan_id}"
        if scan_id
        else f"https://aishield.cz/scan?url={company_url}"
    )

    if findings_count == 1:
        pocet = "1 AI systém"
    elif 2 <= findings_count <= 4:
        pocet = f"{findings_count} AI systémy"
    else:
        pocet = f"{findings_count} AI systémů"

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
        gemini_intro=f"Dobrý den,<br><br>jmenuji se Martin Haynes a zabývám se compliance s EU AI Act pro české firmy. "
                     f"Na webu <strong>{company_url}</strong> jsem identifikoval <strong>{pocet}</strong>, "
                     f"které spadají pod novou regulaci.",
        gemini_findings_commentary=f"Hlavní nález: <strong>{top_finding}</strong>. "
                                    f"Každý AI systém na webu musí být dle AI Act transparentně označen.",
        gemini_impact="Nedodržení povinností AI Act může vést k sankcím ze strany dozorového úřadu. "
                      "Ale hlavně — vaši zákazníci mají právo vědět, že komunikují s AI.",
        company_url=company_url,
        findings=finding_rows,
        screenshot_url=screenshot_url,
        scan_id=scan_id,
        to_email=to_email,
    )

    return EmailVariant(
        subject=f"AI Act a web {company_url} — krátké upozornění",
        body_html=html,
        variant_id=variant,
    )
