"""
AIshield.cz — Scan Report Email Template v2
Dark theme branded HTML email matching web design.
Includes: scan results, positive AI messaging, SEO benefit,
pricing plans, registration CTA, and contact info.
"""

from datetime import date

RISK_LABELS = {
    "high": "Vysoké riziko",
    "limited": "Omezené riziko",
    "minimal": "Minimální riziko",
}

RISK_COLORS = {
    "high": {"bg": "#3b1118", "border": "#ef4444", "text": "#fca5a5", "dot": "#ef4444"},
    "limited": {"bg": "#3b2e0a", "border": "#eab308", "text": "#fde68a", "dot": "#eab308"},
    "minimal": {"bg": "#0a3b1e", "border": "#22c55e", "text": "#86efac", "dot": "#22c55e"},
}

CATEGORY_LABELS = {
    "chatbot": "Chatbot / Konverzační AI",
    "analytics": "Analytika / Sledování",
    "recommender": "Doporučovací systém",
    "content_gen": "Generování obsahu",
    "other": "Ostatní AI systém",
}

# EU AI Act article URLs (EUR-Lex)
_AI_ACT_BASE = "https://eur-lex.europa.eu/legal-content/CS/TXT/HTML/?uri=OJ:L_202401689"
AI_ACT_LINKS = {
    "čl. 50": f"{_AI_ACT_BASE}#art_50",
    "čl. 50 odst. 1": f"{_AI_ACT_BASE}#art_50",
    "čl. 50 odst. 4": f"{_AI_ACT_BASE}#art_50",
    "čl. 4": f"{_AI_ACT_BASE}#art_4",
    "čl. 6": f"{_AI_ACT_BASE}#art_6",
    "čl. 9": f"{_AI_ACT_BASE}#art_9",
    "čl. 13": f"{_AI_ACT_BASE}#art_13",
    "čl. 14": f"{_AI_ACT_BASE}#art_14",
    "čl. 26": f"{_AI_ACT_BASE}#art_26",
    "čl. 27": f"{_AI_ACT_BASE}#art_27",
}

# Per-category short "how we fix it" text
OFFER_TEXT = {
    "chatbot": "Připravíme oznámení pro návštěvníky, nastavíme transparenční widget a zajistíme evidenci v registru AI systémů.",
    "analytics": "Vytvoříme transparenční stránku s popisem analytických AI nástrojů a aktualizujeme informační povinnost.",
    "recommender": "Popíšeme fungování doporučovacího systému, připravíme informační text pro uživatele a zajistíme soulad s čl. 50.",
    "content_gen": "Označíme AI-generovaný obsah, připravíme interní pravidla a zajistíme transparentnost pro návštěvníky.",
}
DEFAULT_OFFER = "Zajistíme kompletní soulad s AI Act — od dokumentace přes označení až po registraci systému."

# Shield logo SVG (inline, compact)
SHIELD_LOGO_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 40 40" style="vertical-align:middle;margin-right:10px;">'
    '<defs><linearGradient id="sg" x1="0%" y1="0%" x2="100%" y2="100%">'
    '<stop offset="0%" stop-color="#d946ef"/>'
    '<stop offset="100%" stop-color="#06b6d4"/>'
    '</linearGradient></defs>'
    '<path d="M20 2 L36 10 L36 22 C36 30 28 37 20 39 C12 37 4 30 4 22 L4 10 Z" '
    'fill="url(#sg)" opacity="0.9"/>'
    '<path d="M14 20 L18 24 L26 16" stroke="#fff" stroke-width="2.5" '
    'fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
    '</svg>'
)

# AI Act enforcement date
_AI_ACT_DATE = date(2026, 8, 2)


def _make_article_link(article_text: str) -> str:
    """Convert article reference like 'čl. 50 odst. 1' into a hyperlink."""
    for ref, url in AI_ACT_LINKS.items():
        if ref in article_text:
            return article_text.replace(
                ref,
                f'<a href="{url}" style="color:#a78bfa;text-decoration:underline;" target="_blank">{ref}</a>',
                1,
            )
    # Fallback: link the whole text to the base
    return f'<a href="{_AI_ACT_BASE}" style="color:#a78bfa;text-decoration:underline;" target="_blank">{article_text}</a>'


def _days_remaining() -> str:
    """Human-readable countdown to AI Act enforcement date."""
    delta = _AI_ACT_DATE - date.today()
    days = delta.days
    if days <= 0:
        return "AI Act je již v platnosti"
    months = days // 30
    remaining_days = days % 30
    if months >= 2:
        return f"{months} měsíců a {remaining_days} dní"
    elif months == 1:
        return f"1 měsíc a {remaining_days} dní"
    else:
        return f"{days} dní"


# Dark theme brand colors matching the website
D = {
    "bg_body": "#0a0a1a",
    "bg_card": "#0f172a",
    "bg_section": "#131b2e",
    "bg_elevated": "#1a2340",
    "border": "#1e293b",
    "border_light": "#334155",
    "text": "#f1f5f9",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
    "accent_fuchsia": "#d946ef",
    "accent_cyan": "#06b6d4",
    "accent_purple": "#7c3aed",
    "gradient_start": "#0f172a",
    "gradient_mid": "#1e1b4b",
    "gradient_end": "#312e81",
    "success": "#22c55e",
    "warning": "#eab308",
    "danger": "#ef4444",
}


def generate_report_email_html(
    url: str,
    company_name: str,
    findings: list[dict],
    scan_id: str,
) -> str:
    """Generate dark-themed branded HTML email with scan results, pricing, and CTAs."""

    findings_count = len(findings)
    high_count = sum(1 for f in findings if f.get("risk_level") == "high")
    limited_count = sum(1 for f in findings if f.get("risk_level") == "limited")
    minimal_count = sum(1 for f in findings if f.get("risk_level") == "minimal")

    if findings_count == 1:
        sys_word = "AI systém"
    elif findings_count < 5:
        sys_word = "AI systémy"
    else:
        sys_word = "AI systémů"

    # ── Build findings rows ──
    findings_html = ""
    for f in findings:
        rl = f.get("risk_level", "minimal")
        colors = RISK_COLORS.get(rl, RISK_COLORS["minimal"])
        cat_label = CATEGORY_LABELS.get(f.get("category", ""), f.get("category", "Neznámá kategorie"))
        name = f.get("name", "Neznámý systém")
        ai_text = f.get("ai_classification_text", "")
        article = f.get("ai_act_article", "")
        action = f.get("action_required", "")
        risk_label = RISK_LABELS.get(rl, rl)

        extras = ""
        if ai_text:
            extras += (
                f'<div style="font-size:13px;color:{D["text_muted"]};'
                f'margin-top:8px;font-style:italic;">{ai_text}</div>'
            )
        if article:
            linked_article = _make_article_link(article)
            extras += (
                f'<div style="margin-top:6px;font-size:13px;">'
                f'<span style="color:{D["text_muted"]};">Článek:</span> '
                f'<span style="color:{D["text_secondary"]};">{linked_article}</span></div>'
            )
        if action:
            action_label = "✅ Status:" if action.startswith("✅") else "Co udělat:"
            extras += (
                f'<div style="margin-top:4px;font-size:13px;">'
                f'<span style="color:{D["text_muted"]};">{action_label}</span> '
                f'<span style="color:{D["accent_cyan"]};">{action}</span></div>'
            )

        findings_html += f"""
        <tr>
            <td style="padding:16px;border-bottom:1px solid {D["border"]};">
                <div style="font-weight:600;color:{D["text"]};font-size:15px;">{name}</div>
                <div style="font-size:12px;color:{D["text_muted"]};margin-top:2px;">{cat_label}</div>
                {extras}
            </td>
            <td style="padding:16px;border-bottom:1px solid {D["border"]};text-align:center;vertical-align:top;">
                <span style="display:inline-block;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:600;background:{colors['bg']};color:{colors['text']};border:1px solid {colors['border']};">
                    {risk_label}
                </span>
            </td>
        </tr>"""

    # ── Risk summary boxes ──
    risk_boxes = ""
    if high_count:
        risk_boxes += (
            f'<td style="text-align:center;padding:14px;background:#3b1118;'
            f'border-radius:12px;border:1px solid #ef4444;">'
            f'<div style="font-size:28px;font-weight:700;color:#ef4444;">{high_count}</div>'
            f'<div style="font-size:12px;color:#fca5a5;margin-top:2px;">Vysoké riziko</div></td>'
        )
    if limited_count:
        risk_boxes += (
            f'<td style="text-align:center;padding:14px;background:#3b2e0a;'
            f'border-radius:12px;border:1px solid #eab308;">'
            f'<div style="font-size:28px;font-weight:700;color:#eab308;">{limited_count}</div>'
            f'<div style="font-size:12px;color:#fde68a;margin-top:2px;">Omezené riziko</div></td>'
        )
    if minimal_count:
        risk_boxes += (
            f'<td style="text-align:center;padding:14px;background:#0a3b1e;'
            f'border-radius:12px;border:1px solid #22c55e;">'
            f'<div style="font-size:28px;font-weight:700;color:#22c55e;">{minimal_count}</div>'
            f'<div style="font-size:12px;color:#86efac;margin-top:2px;">Minimální riziko</div></td>'
        )

    risk_table = ""
    if risk_boxes:
        risk_table = (
            f'<div style="margin:0 24px 24px;">'
            f'<table style="width:100%;border-collapse:separate;border-spacing:8px 0;">'
            f'<tr>{risk_boxes}</tr></table></div>'
        )

    # ── Build the full HTML ──
    html = f"""<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIshield.cz — Výsledky AI Act skenu</title>
</head>
<body style="margin:0;padding:0;background:{D["bg_body"]};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
    <div style="max-width:640px;margin:0 auto;background:{D["bg_card"]};">

        <!-- HEADER -->
        <div style="background:linear-gradient(135deg, {D["gradient_start"]}, {D["gradient_mid"]}, {D["gradient_end"]});padding:36px 24px;text-align:center;border-bottom:1px solid {D["border"]};">
            <div style="font-size:28px;font-weight:800;letter-spacing:-0.5px;">
                {SHIELD_LOGO_SVG}<span style="color:#ffffff;">AI</span><span style="background:linear-gradient(135deg,{D["accent_fuchsia"]},{D["accent_cyan"]});-webkit-background-clip:text;-webkit-text-fill-color:transparent;">shield</span><span style="color:{D["text_muted"]};font-size:16px;font-weight:400;">.cz</span>
            </div>
            <div style="font-size:14px;color:{D["text_secondary"]};margin-top:6px;">Výsledky AI Act compliance skenu</div>
        </div>

        <!-- POSITIVE AI MESSAGE -->
        <div style="margin:24px;padding:20px;background:linear-gradient(135deg, #0a2a1e, #0f2b3d);border:1px solid {D["success"]};border-radius:12px;">
            <div style="font-size:16px;font-weight:700;color:{D["success"]};">
                &#10003; Skvělá zpráva — váš web využívá umělou inteligenci!
            </div>
            <p style="font-size:14px;color:{D["text_secondary"]};margin-top:10px;line-height:1.7;">
                Používáním AI technologií na svém webu máte <strong style="color:{D["text"]};">významnou konkurenční výhodu</strong>.
                Chatboty, analytika a doporučovací systémy zlepšují zákaznický zážitek a konverze.
                Teď jen potřebujete mít vše <strong style="color:{D["text"]};">legislativně v pořádku</strong>,
                aby vám tato výhoda zůstala i po začátku platnosti EU AI Act.
            </p>
        </div>

        <!-- SEO BENEFIT PANEL -->
        <div style="margin:0 24px 24px;padding:20px;background:linear-gradient(135deg, #0f1b3d, #1a1040);border:1px solid {D["accent_purple"]};border-radius:12px;">
            <div style="font-size:15px;font-weight:700;color:{D["accent_fuchsia"]};">
                &#128640; Compliance jako konkurenční výhoda v&nbsp;SEO
            </div>
            <p style="font-size:14px;color:{D["text_secondary"]};margin-top:10px;line-height:1.7;">
                Weby, které transparentně informují návštěvníky o používání AI technologií,
                získávají <strong style="color:{D["text"]};">vyšší důvěryhodnost</strong> nejen u uživatelů, ale i u vyhledávačů.
                Google i Seznam při hodnocení stránek zohledňují kvalitu zásad ochrany soukromí
                a transparentnosti — weby splňující regulatorní požadavky jsou
                <strong style="color:{D["accent_cyan"]};">lépe indexovány a zobrazovány na vyšších pozicích</strong>.
                Compliance s AI Act tak není jen povinnost, ale i investice do vaší online viditelnosti.
            </p>
        </div>

        <!-- WARNING: FINDINGS -->
        <div style="margin:0 24px 24px;padding:20px;background:#2a1015;border:2px solid {D["danger"]};border-radius:12px;">
            <div style="font-size:16px;font-weight:700;color:#fca5a5;">
                &#9888; Na vašem webu byly nalezeny AI systémy vyžadující úpravu
            </div>
            <p style="font-size:14px;color:#f8a0a0;margin-top:10px;line-height:1.7;">
                Na webu <strong style="color:#ffffff;">{url}</strong> jsme identifikovali
                <strong style="color:#ffffff;">{findings_count} {sys_word}</strong>,
                které nejsou v souladu s povinnostmi dle EU AI Act.
                Od <strong style="color:#ffffff;">2. srpna 2026</strong> musí být všechny AI systémy
                interagující s návštěvníky řádně označeny
                (<a href="{AI_ACT_LINKS['čl. 50']}" style="color:#fca5a5;text-decoration:underline;" target="_blank">čl.&nbsp;50, Nařízení&nbsp;2024/1689</a>).
                Nesplnění hrozí pokutou <strong style="color:#ffffff;">až 15&nbsp;milionů&nbsp;EUR nebo 3&nbsp;%&nbsp;obratu</strong>.
            </p>
        </div>

        <!-- SUMMARY BOX -->
        <div style="margin:0 24px 24px;padding:20px;background:{D["bg_elevated"]};border:1px solid {D["border"]};border-radius:12px;">
            <table style="width:100%;border-collapse:collapse;">
                <tr>
                    <td style="padding:8px 0;font-size:14px;color:{D["text_muted"]};">Skenovaný web</td>
                    <td style="padding:8px 0;font-size:14px;font-weight:600;color:{D["accent_cyan"]};text-align:right;">{url}</td>
                </tr>
                <tr>
                    <td style="padding:8px 0;font-size:14px;color:{D["text_muted"]};">Firma</td>
                    <td style="padding:8px 0;font-size:14px;font-weight:600;color:{D["text"]};text-align:right;">{company_name}</td>
                </tr>
                <tr>
                    <td style="padding:8px 0;font-size:14px;color:{D["text_muted"]};">Nalezené AI systémy</td>
                    <td style="padding:8px 0;font-size:26px;font-weight:700;color:{D["accent_fuchsia"]};text-align:right;">{findings_count}</td>
                </tr>
            </table>
        </div>

        <!-- RISK BOXES -->
        {risk_table}

        <!-- FINDINGS TABLE -->
        <div style="margin:0 24px 24px;">
            <div style="font-size:16px;font-weight:700;color:{D["text"]};margin-bottom:12px;">
                Nalezené AI systémy ({findings_count})
            </div>
            <table style="width:100%;border-collapse:collapse;border:1px solid {D["border"]};border-radius:12px;overflow:hidden;">
                <tr style="background:{D["bg_elevated"]};">
                    <th style="padding:12px 16px;text-align:left;font-size:13px;color:{D["text_muted"]};font-weight:600;border-bottom:1px solid {D["border"]};">Nález</th>
                    <th style="padding:12px 16px;text-align:center;font-size:13px;color:{D["text_muted"]};font-weight:600;border-bottom:1px solid {D["border"]};">Riziko</th>
                </tr>
                {findings_html}
            </table>
        </div>

        <!-- WHAT WE DELIVER -->
        <div style="margin:0 24px 24px;padding:20px;background:{D["bg_elevated"]};border:1px solid {D["border"]};border-radius:12px;">
            <div style="font-size:16px;font-weight:700;color:{D["text"]};margin-bottom:4px;text-align:center;">
                Co všechno pro vás připravíme?
            </div>
            <div style="font-size:13px;color:{D["text_muted"]};margin-bottom:16px;text-align:center;">
                Kompletní balíček dokumentace na míru pro {company_name}
            </div>
            <table style="width:100%;border-collapse:separate;border-spacing:0 8px;">
                <tr><td style="padding:12px 14px;background:{D["bg_section"]};border-radius:8px;">
                    <table cellpadding="0" cellspacing="0" style="width:100%;"><tr>
                        <td style="width:32px;vertical-align:top;padding-right:10px;">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="3" width="18" height="18" rx="3" stroke="{D['accent_fuchsia']}" stroke-width="1.5"/><path d="M8 12h8M8 8h8M8 16h5" stroke="{D['accent_fuchsia']}" stroke-width="1.5" stroke-linecap="round"/></svg>
                        </td>
                        <td>
                            <div style="font-size:14px;font-weight:600;color:{D['text']};">AI Act Compliance Report</div>
                            <div style="font-size:12px;color:{D['text_muted']};margin-top:2px;">Kompletní přehled AI systémů na vašem webu, hodnocení rizik a odkazy na konkrétní články AI Actu</div>
                        </td>
                    </tr></table>
                </td></tr>
                <tr><td style="padding:12px 14px;background:{D["bg_section"]};border-radius:8px;">
                    <table cellpadding="0" cellspacing="0" style="width:100%;"><tr>
                        <td style="width:32px;vertical-align:top;padding-right:10px;">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4 6h16M4 10h16M4 14h10M4 18h7" stroke="{D['accent_purple']}" stroke-width="1.5" stroke-linecap="round"/></svg>
                        </td>
                        <td>
                            <div style="font-size:14px;font-weight:600;color:{D['text']};">Registr AI systémů</div>
                            <div style="font-size:12px;color:{D['text_muted']};margin-top:2px;">Evidence všech AI nástrojů na vašem webu — připraveno pro případnou kontrolu úřadů</div>
                        </td>
                    </tr></table>
                </td></tr>
                <tr><td style="padding:12px 14px;background:{D["bg_section"]};border-radius:8px;">
                    <table cellpadding="0" cellspacing="0" style="width:100%;"><tr>
                        <td style="width:32px;vertical-align:top;padding-right:10px;">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="9" stroke="{D['success']}" stroke-width="1.5"/><path d="M12 3C12 3 6 8 6 12s3 6 6 6" stroke="{D['success']}" stroke-width="1.5"/><path d="M12 3c0 0 6 5 6 9s-3 6-6 6" stroke="{D['success']}" stroke-width="1.5"/><path d="M3 12h18" stroke="{D['success']}" stroke-width="1.5"/></svg>
                        </td>
                        <td>
                            <div style="font-size:14px;font-weight:600;color:{D['text']};">Transparenční stránka</div>
                            <div style="font-size:12px;color:{D['text_muted']};margin-top:2px;">Hotový HTML kód podstránky splňující <a href="{AI_ACT_LINKS['čl. 50']}" style="color:{D['accent_cyan']};text-decoration:underline;" target="_blank">čl. 50 AI Act</a> — stačí vložit na váš web</div>
                        </td>
                    </tr></table>
                </td></tr>
                <tr><td style="padding:12px 14px;background:{D["bg_section"]};border-radius:8px;">
                    <table cellpadding="0" cellspacing="0" style="width:100%;"><tr>
                        <td style="width:32px;vertical-align:top;padding-right:10px;">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z" stroke="{D['warning']}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
                        </td>
                        <td>
                            <div style="font-size:14px;font-weight:600;color:{D['text']};">Texty oznámení pro AI nástroje</div>
                            <div style="font-size:12px;color:{D['text_muted']};margin-top:2px;">Povinná oznámení pro chatboty a další AI systémy — v češtině i angličtině</div>
                        </td>
                    </tr></table>
                </td></tr>
                <tr><td style="padding:12px 14px;background:{D["bg_section"]};border-radius:8px;">
                    <table cellpadding="0" cellspacing="0" style="width:100%;"><tr>
                        <td style="width:32px;vertical-align:top;padding-right:10px;">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" stroke="{D['accent_cyan']}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
                        </td>
                        <td>
                            <div style="font-size:14px;font-weight:600;color:{D['text']};">AI politika firmy</div>
                            <div style="font-size:12px;color:{D['text_muted']};margin-top:2px;">Interní pravidla pro zaměstnance ohledně používání AI nástrojů ve vaší firmě</div>
                        </td>
                    </tr></table>
                </td></tr>
                <tr><td style="padding:12px 14px;background:linear-gradient(135deg, {D["bg_section"]}, #1a1040);border-radius:8px;border:1px solid {D['accent_fuchsia']}30;">
                    <table cellpadding="0" cellspacing="0" style="width:100%;"><tr>
                        <td style="width:32px;vertical-align:top;padding-right:10px;">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 14l9-5-9-5-9 5 9 5z" stroke="{D['accent_fuchsia']}" stroke-width="1.5" stroke-linejoin="round"/><path d="M12 14v7" stroke="{D['accent_fuchsia']}" stroke-width="1.5" stroke-linecap="round"/><path d="M21 9v5.5" stroke="{D['accent_fuchsia']}" stroke-width="1.5" stroke-linecap="round"/><path d="M6 11.5V17c0 1 2.7 3 6 3s6-2 6-3v-5.5" stroke="{D['accent_fuchsia']}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
                        </td>
                        <td>
                            <div style="font-size:14px;font-weight:600;color:{D['accent_fuchsia']};">Školení zaměstnanců v PowerPointu</div>
                            <div style="font-size:12px;color:{D['text_muted']};margin-top:2px;">Prezentace na míru přímo pro {company_name} — splnění povinnosti AI gramotnosti dle <a href="{AI_ACT_LINKS['čl. 4']}" style="color:{D['accent_cyan']};text-decoration:underline;" target="_blank">čl. 4 AI Act</a></div>
                        </td>
                    </tr></table>
                </td></tr>
                <tr><td style="padding:12px 14px;background:{D["bg_section"]};border-radius:8px;">
                    <table cellpadding="0" cellspacing="0" style="width:100%;"><tr>
                        <td style="width:32px;vertical-align:top;padding-right:10px;">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2" stroke="{D['accent_cyan']}" stroke-width="1.5" stroke-linecap="round"/><rect x="9" y="3" width="6" height="4" rx="1" stroke="{D['accent_cyan']}" stroke-width="1.5"/><path d="M9 12l2 2 4-4" stroke="{D['accent_cyan']}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
                        </td>
                        <td>
                            <div style="font-size:14px;font-weight:600;color:{D['text']};">Záznamový list o proškolení</div>
                            <div style="font-size:12px;color:{D['text_muted']};margin-top:2px;">Doklad o splnění povinnosti AI gramotnosti — připraveno k podpisu zaměstnanci</div>
                        </td>
                    </tr></table>
                </td></tr>
            </table>

            <!-- ENTERPRISE EXTRAS -->
            <div style="margin-top:16px;padding:16px;background:linear-gradient(135deg, #0f1b3d, #1a1040);border:1px solid {D['accent_purple']}40;border-radius:10px;">
                <div style="font-size:13px;font-weight:700;color:{D['accent_fuchsia']};margin-bottom:10px;text-align:center;">
                    A pro firmy, které chtějí kompletní péči:
                </div>
                <div style="font-size:13px;color:{D['text_secondary']};line-height:2;">
                    &#10003; Implementace na klíč — instalace widgetu, transparenční stránky i chatbot oznámení přímo na váš web<br>
                    &#10003; 10 hodin konzultací s compliance specialistou<br>
                    &#10003; Metodická kontrola veškeré dokumentace<br>
                    &#10003; Rozšířený audit interních AI systémů<br>
                    &#10003; 2 roky měsíčního monitoringu — automatický sken, aktualizace dokumentů<br>
                    &#10003; Dedikovaný specialista + SLA s dobou odezvy 4 hodiny
                </div>
            </div>
        </div>

        <!-- PRICING PLANS -->
        <div style="margin:0 24px 24px;">
            <div style="font-size:18px;font-weight:700;color:{D["text"]};margin-bottom:16px;text-align:center;">
                Vyberte si balíček, který vám vyhovuje
            </div>

            <!-- BASIC -->
            <div style="margin-bottom:12px;padding:20px;background:{D["bg_elevated"]};border:1px solid {D["border"]};border-radius:12px;">
                <div style="font-size:16px;font-weight:700;color:{D["text"]};">BASIC</div>
                <div style="font-size:12px;color:{D["text_muted"]};margin-top:2px;">Compliance Kit — dokumenty ke stažení</div>
                <div style="font-size:28px;font-weight:800;color:{D["text"]};margin-top:8px;">4&nbsp;999&nbsp;Kč</div>
                <div style="font-size:11px;color:{D["text_muted"]};">jednorázově</div>
                <div style="margin-top:12px;font-size:13px;color:{D["text_secondary"]};line-height:1.8;">
                    ✓ Sken webu + AI Act report &nbsp;&nbsp;
                    ✓ 7 PDF dokumentů &nbsp;&nbsp;
                    ✓ Transparenční stránka &nbsp;&nbsp;
                    ✓ Registr AI systémů &nbsp;&nbsp;
                    ✓ AI politika firmy &nbsp;&nbsp;
                    ✓ Školení v PowerPointu &nbsp;&nbsp;
                    ✓ Záznamový list o proškolení
                </div>
            </div>

            <!-- PRO (highlighted) -->
            <div style="margin-bottom:12px;padding:3px;background:linear-gradient(135deg, {D["accent_fuchsia"]}, {D["accent_cyan"]});border-radius:14px;">
                <div style="padding:20px;background:{D["bg_card"]};border-radius:12px;">
                    <div style="text-align:center;margin-bottom:8px;">
                        <span style="display:inline-block;padding:3px 14px;border-radius:20px;font-size:11px;font-weight:600;color:#ffffff;background:linear-gradient(135deg, {D["accent_fuchsia"]}, {D["accent_purple"]});">
                            &#11088; Nejoblíbenější
                        </span>
                    </div>
                    <div style="font-size:16px;font-weight:700;color:{D["text"]};">PRO</div>
                    <div style="font-size:12px;color:{D["text_muted"]};margin-top:2px;">Vše z BASIC + implementace na klíč</div>
                    <div style="font-size:28px;font-weight:800;color:{D["accent_fuchsia"]};margin-top:8px;">14&nbsp;999&nbsp;Kč</div>
                    <div style="font-size:11px;color:{D["text_muted"]};">jednorázově</div>
                    <div style="margin-top:12px;font-size:13px;color:{D["text_secondary"]};line-height:1.8;">
                        ✓ Vše z BASIC &nbsp;&nbsp;
                        ✓ Instalace widgetu na web &nbsp;&nbsp;
                        ✓ Nastavení transparenční stránky &nbsp;&nbsp;
                        ✓ Úprava chatbot oznámení &nbsp;&nbsp;
                        ✓ 30 dní podpora &nbsp;&nbsp;
                        ✓ Prioritní zpracování
                    </div>
                </div>
            </div>

            <!-- ENTERPRISE -->
            <div style="margin-bottom:12px;padding:20px;background:{D["bg_elevated"]};border:1px solid {D["border"]};border-radius:12px;">
                <div style="font-size:16px;font-weight:700;color:{D["text"]};">ENTERPRISE</div>
                <div style="font-size:12px;color:{D["text_muted"]};margin-top:2px;">Kompletní řešení + konzultace + 2 roky monitoringu</div>
                <div style="font-size:28px;font-weight:800;color:{D["text"]};margin-top:8px;">39&nbsp;999&nbsp;Kč</div>
                <div style="font-size:11px;color:{D["text_muted"]};">jednorázově</div>
                <div style="margin-top:12px;font-size:13px;color:{D["text_secondary"]};line-height:1.8;">
                    ✓ Vše z PRO &nbsp;&nbsp;
                    ✓ 10h konzultací se specialistou &nbsp;&nbsp;
                    ✓ Metodická kontrola dokumentace &nbsp;&nbsp;
                    ✓ Rozšířený audit interních AI &nbsp;&nbsp;
                    ✓ 2 roky měsíčního monitoringu &nbsp;&nbsp;
                    ✓ Dedikovaný specialista &nbsp;&nbsp;
                    ✓ SLA 4h odezva
                </div>
            </div>
        </div>

        <!-- CTA BUTTONS -->
        <div style="margin:0 24px 24px;text-align:center;">
            <a href="https://aishield.cz/pricing" style="display:inline-block;padding:14px 40px;background:linear-gradient(135deg,{D["accent_fuchsia"]},{D["accent_purple"]});color:#ffffff;font-weight:700;font-size:15px;border-radius:12px;text-decoration:none;margin-bottom:12px;">
                Zobrazit ceník a objednat
            </a>
            <br>
            <a href="https://aishield.cz/registrace" style="display:inline-block;padding:12px 32px;background:transparent;color:{D["accent_cyan"]};font-weight:600;font-size:14px;border-radius:12px;text-decoration:none;border:1px solid {D["accent_cyan"]};margin-top:8px;">
                Vytvořit účet zdarma
            </a>
        </div>

        <!-- DEADLINE COUNTDOWN -->
        <div style="margin:0 24px 24px;padding:20px;background:#2a1015;border:2px solid {D["danger"]};border-radius:12px;text-align:center;">
            <div style="font-size:13px;color:#fca5a5;text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                Do platnosti AI Act zbývá
            </div>
            <div style="font-size:32px;font-weight:800;color:{D["danger"]};margin-top:8px;">
                {_days_remaining()}
            </div>
            <p style="font-size:13px;color:#e2e8f0;margin-top:10px;line-height:1.6;">
                <a href="{AI_ACT_LINKS['čl. 50']}" style="color:#fca5a5;text-decoration:underline;font-weight:600;" target="_blank">AI Act</a>
                přichází v platnost <strong style="color:#ffffff;">2.&nbsp;srpna&nbsp;2026</strong>.
                Po tomto datu mohou úřady udělovat <strong style="color:#fca5a5;">pokuty za nesoulad</strong>.
                Doporučujeme začít s úpravami co nejdříve.
            </p>
        </div>

        <!-- CONTACT -->
        <div style="margin:0 24px 24px;padding:20px;background:{D["bg_elevated"]};border:1px solid {D["border"]};border-radius:12px;text-align:center;">
            <div style="font-size:15px;font-weight:600;color:{D["text"]};">Máte otázky? Ozvěte se nám</div>
            <div style="margin-top:12px;font-size:14px;">
                <a href="mailto:info@aishield.cz" style="color:{D["accent_cyan"]};text-decoration:none;font-weight:500;">info@aishield.cz</a>
                &nbsp;&nbsp;|&nbsp;&nbsp;
                <a href="tel:+420732716141" style="color:{D["accent_cyan"]};text-decoration:none;font-weight:500;">+420 732 716 141</a>
            </div>
            <div style="margin-top:8px;font-size:12px;color:{D["text_muted"]};">
                Odpovídáme do 24 hodin v pracovní dny.
            </div>
        </div>

        <!-- FOOTER -->
        <div style="background:linear-gradient(135deg, {D["gradient_start"]}, {D["gradient_mid"]});padding:28px 24px;text-align:center;border-top:1px solid {D["border"]};">
            <div style="font-size:14px;font-weight:600;color:{D["text_secondary"]};">
                <span style="color:#ffffff;">AI</span><span style="color:{D["accent_fuchsia"]};">shield</span><span style="color:{D["text_muted"]};">.cz</span>
                &nbsp;— AI Act compliance pro české firmy
            </div>
            <div style="font-size:11px;color:{D["text_muted"]};margin-top:10px;line-height:1.6;">
                Tento email byl vygenerován na základě automatického skenu webu {url}.<br>
                &copy; 2025 AIshield.cz | Provozovatel: Martin Haynes, IČO: 17889251
            </div>
        </div>

    </div>
</body>
</html>"""

    return html


def generate_zero_findings_email_html(
    url: str,
    company_name: str,
    scan_id: str,
) -> str:
    """
    Generate branded HTML email for scans that found ZERO AI systems.
    Warns the user that quick scan ≠ safety, explains where AI can hide,
    and emphasizes the still-present compliance risk.
    """

    html = f"""<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIshield.cz — Výsledky AI Act skenu</title>
</head>
<body style="margin:0;padding:0;background:{D["bg_body"]};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
    <div style="max-width:640px;margin:0 auto;background:{D["bg_card"]};">

        <!-- HEADER -->
        <div style="background:linear-gradient(135deg, {D["gradient_start"]}, {D["gradient_mid"]}, {D["gradient_end"]});padding:36px 24px;text-align:center;border-bottom:1px solid {D["border"]};">
            <div style="font-size:28px;font-weight:800;letter-spacing:-0.5px;">
                {SHIELD_LOGO_SVG}<span style="color:#ffffff;">AI</span><span style="background:linear-gradient(135deg,{D["accent_fuchsia"]},{D["accent_cyan"]});-webkit-background-clip:text;-webkit-text-fill-color:transparent;">shield</span><span style="color:{D["text_muted"]};font-size:16px;font-weight:400;">.cz</span>
            </div>
            <div style="font-size:14px;color:{D["text_secondary"]};margin-top:6px;">Výsledky AI Act compliance skenu</div>
        </div>

        <!-- SCAN RESULT: NO AI DETECTED -->
        <div style="margin:24px;padding:20px;background:linear-gradient(135deg, #1a2a15, #1a2b1a);border:1px solid {D["warning"]};border-radius:12px;">
            <div style="font-size:16px;font-weight:700;color:{D["warning"]};">
                &#128269; Rychlý sken neodhalil žádné AI systémy na vašem webu
            </div>
            <p style="font-size:14px;color:{D["text_secondary"]};margin-top:10px;line-height:1.7;">
                Na webu <strong style="color:{D["text"]};">{url}</strong> jsme provedli automatický
                sken a <strong style="color:{D["text"]};">nenašli žádné viditelné AI systémy</strong>.
                To je dobrý začátek, ale <strong style="color:{D["warning"]};">rozhodně to neznamená,
                že jste mimo dosah AI Act</strong>.
            </p>
        </div>

        <!-- WARNING: FALSE SENSE OF SECURITY -->
        <div style="margin:0 24px 24px;padding:20px;background:#2a1015;border:2px solid {D["danger"]};border-radius:12px;">
            <div style="font-size:16px;font-weight:700;color:#fca5a5;">
                &#9888; Pozor — nenechte se ukolébat falešným pocitem bezpečí
            </div>
            <p style="font-size:14px;color:#f8a0a0;margin-top:10px;line-height:1.7;">
                Rychlý sken analyzuje pouze <strong style="color:#ffffff;">veřejně viditelný kód vašeho webu</strong>.
                Existuje celá řada AI systémů, které tento sken <strong style="color:#ffffff;">nemůže odhalit</strong>,
                protože pracují na pozadí, v&nbsp;interních systémech nebo přes API.
                <strong style="color:{D["warning"]};">EU AI Act se vztahuje na VŠECHNY AI systémy</strong>,
                které vaše firma používá — nejen na ty viditelné na webu.
            </p>
        </div>

        <!-- WHERE AI CAN HIDE -->
        <div style="margin:0 24px 24px;padding:20px;background:{D["bg_elevated"]};border:1px solid {D["border"]};border-radius:12px;">
            <div style="font-size:16px;font-weight:700;color:{D["text"]};margin-bottom:14px;text-align:center;">
                &#129520; Kde všude se může AI schovávat?
            </div>
            <table style="width:100%;border-collapse:separate;border-spacing:0 6px;">
                <tr><td style="padding:10px 14px;background:{D["bg_section"]};border-radius:8px;">
                    <div style="font-size:14px;font-weight:600;color:{D["accent_fuchsia"]};">&#128187; CRM a obchodní nástroje</div>
                    <div style="font-size:12px;color:{D["text_muted"]};margin-top:3px;">Salesforce Einstein, HubSpot AI, Pipedrive AI — automatické skórování leadů, predikce prodejů, AI doporučení.</div>
                </td></tr>
                <tr><td style="padding:10px 14px;background:{D["bg_section"]};border-radius:8px;">
                    <div style="font-size:14px;font-weight:600;color:{D["accent_cyan"]};">&#128231; E-mailový marketing</div>
                    <div style="font-size:12px;color:{D["text_muted"]};margin-top:3px;">Mailchimp, Ecomail, SmartEmailing — AI optimalizace předmětů, segmentace, prediktivní analýza odesílání.</div>
                </td></tr>
                <tr><td style="padding:10px 14px;background:{D["bg_section"]};border-radius:8px;">
                    <div style="font-size:14px;font-weight:600;color:{D["accent_purple"]};">&#129302; Chatboti a zákaznická podpora</div>
                    <div style="font-size:12px;color:{D["text_muted"]};margin-top:3px;">Intercom, Zendesk AI, Tidio — chatboti mohou běžet přes iframe nebo JavaScript z externích domén, které rychlý sken nevidí.</div>
                </td></tr>
                <tr><td style="padding:10px 14px;background:{D["bg_section"]};border-radius:8px;">
                    <div style="font-size:14px;font-weight:600;color:{D["success"]};">&#128202; HR a nábor</div>
                    <div style="font-size:12px;color:{D["text_muted"]};margin-top:3px;">LinkedIn Recruiter AI, Teamio, hledací algoritmy — automatické třídění životopisů a hodnocení kandidátů spadá pod vysoké riziko.</div>
                </td></tr>
                <tr><td style="padding:10px 14px;background:{D["bg_section"]};border-radius:8px;">
                    <div style="font-size:14px;font-weight:600;color:{D["warning"]};">&#128200; Účetnictví a finance</div>
                    <div style="font-size:12px;color:{D["text_muted"]};margin-top:3px;">ABRA AI, Money S5, Fakturoid — automatická kategorizace faktur, predikce cash flow, AI párování plateb.</div>
                </td></tr>
                <tr><td style="padding:10px 14px;background:{D["bg_section"]};border-radius:8px;">
                    <div style="font-size:14px;font-weight:600;color:{D["danger"]};">&#128274; Bezpečnostní systémy</div>
                    <div style="font-size:12px;color:{D["text_muted"]};margin-top:3px;">Kamerové systémy s rozpoznáváním obličejů, přístupové systémy, biometrické čtečky — spadají pod zakázané nebo vysokorizikové AI.</div>
                </td></tr>
                <tr><td style="padding:10px 14px;background:{D["bg_section"]};border-radius:8px;">
                    <div style="font-size:14px;font-weight:600;color:{D["accent_fuchsia"]};">&#9999;&#65039; Generování obsahu</div>
                    <div style="font-size:12px;color:{D["text_muted"]};margin-top:3px;">ChatGPT, Claude, Gemini, Copilot — pokud zaměstnanci používají AI k tvorbě textů, obrázků nebo kódu, i to podléhá regulaci.</div>
                </td></tr>
                <tr><td style="padding:10px 14px;background:{D["bg_section"]};border-radius:8px;">
                    <div style="font-size:14px;font-weight:600;color:{D["accent_cyan"]};">&#128722; E-shop a doporučování</div>
                    <div style="font-size:12px;color:{D["text_muted"]};margin-top:3px;">Doporučovací algoritmy produktů, personalizované nabídky, dynamické ceny — běží na backendu a nejsou viditelné v&nbsp;HTML kódu.</div>
                </td></tr>
            </table>
        </div>

        <!-- AI ACT OBLIGATIONS STILL APPLY -->
        <div style="margin:0 24px 24px;padding:20px;background:linear-gradient(135deg, #0f1b3d, #1a1040);border:1px solid {D["accent_purple"]};border-radius:12px;">
            <div style="font-size:15px;font-weight:700;color:{D["accent_fuchsia"]};">
                &#9878;&#65039; Povinnosti dle AI Act platí pro KAŽDOU firmu
            </div>
            <p style="font-size:14px;color:{D["text_secondary"]};margin-top:10px;line-height:1.7;">
                <a href="{AI_ACT_LINKS['čl. 4']}" style="color:{D['accent_cyan']};text-decoration:underline;" target="_blank">Článek 4 AI Act</a>
                ukládá <strong style="color:{D["text"]};">povinnost AI gramotnosti</strong> — každá firma musí zajistit,
                aby její zaměstnanci rozuměli AI systémům, se kterými pracují. Tato povinnost platí
                <strong style="color:{D["warning"]};">bez ohledu na to, zda máte AI na webu</strong>.
            </p>
            <p style="font-size:14px;color:{D["text_secondary"]};margin-top:8px;line-height:1.7;">
                Navíc <a href="{AI_ACT_LINKS['čl. 50']}" style="color:{D['accent_cyan']};text-decoration:underline;" target="_blank">čl.&nbsp;50</a>
                vyžaduje <strong style="color:{D["text"]};">transparenční povinnosti</strong> pro všechny AI systémy
                interagující s osobami. Nesplnění hrozí pokutou
                <strong style="color:{D["danger"]};">až 15&nbsp;milionů&nbsp;EUR nebo 3&nbsp;%&nbsp;obratu</strong>.
            </p>
        </div>

        <!-- RECOMMENDATION: DEEP SCAN + QUESTIONNAIRE -->
        <div style="margin:0 24px 24px;padding:20px;background:{D["bg_elevated"]};border:2px solid {D["accent_cyan"]};border-radius:12px;">
            <div style="font-size:16px;font-weight:700;color:{D["accent_cyan"]};margin-bottom:10px;">
                &#128161; Co doporučujeme udělat
            </div>
            <div style="font-size:14px;color:{D["text_secondary"]};line-height:2;">
                <strong style="color:{D["text"]};">1.</strong> Spusťte <strong style="color:{D["text"]};">hloubkový 24h scan</strong> — skenuje web ze 7 zemí, z různých zařízení, odhalí i dočasně skryté AI systémy<br>
                <strong style="color:{D["text"]};">2.</strong> Vyplňte <strong style="color:{D["text"]};">compliance dotazník</strong> — odhalí AI systémy ve vašich interních procesech, které žádný sken webu nemůže najít<br>
                <strong style="color:{D["text"]};">3.</strong> Zajistěte <strong style="color:{D["text"]};">školení zaměstnanců</strong> — povinnost AI gramotnosti dle čl. 4 platí od 2.&nbsp;února&nbsp;2025
            </div>
        </div>

        <!-- SUMMARY BOX -->
        <div style="margin:0 24px 24px;padding:20px;background:{D["bg_elevated"]};border:1px solid {D["border"]};border-radius:12px;">
            <table style="width:100%;border-collapse:collapse;">
                <tr>
                    <td style="padding:8px 0;font-size:14px;color:{D["text_muted"]};">Skenovaný web</td>
                    <td style="padding:8px 0;font-size:14px;font-weight:600;color:{D["accent_cyan"]};text-align:right;">{url}</td>
                </tr>
                <tr>
                    <td style="padding:8px 0;font-size:14px;color:{D["text_muted"]};">Firma</td>
                    <td style="padding:8px 0;font-size:14px;font-weight:600;color:{D["text"]};text-align:right;">{company_name}</td>
                </tr>
                <tr>
                    <td style="padding:8px 0;font-size:14px;color:{D["text_muted"]};">Typ skenu</td>
                    <td style="padding:8px 0;font-size:14px;font-weight:600;color:{D["warning"]};text-align:right;">Rychlý sken (pouze veřejný kód webu)</td>
                </tr>
                <tr>
                    <td style="padding:8px 0;font-size:14px;color:{D["text_muted"]};">Nalezené AI systémy na webu</td>
                    <td style="padding:8px 0;font-size:26px;font-weight:700;color:{D["success"]};text-align:right;">0</td>
                </tr>
                <tr>
                    <td style="padding:8px 0;font-size:14px;color:{D["text_muted"]};">Interní AI systémy</td>
                    <td style="padding:8px 0;font-size:14px;font-weight:600;color:{D["warning"]};text-align:right;">&#10067; Nezjištěno — vyplňte dotazník</td>
                </tr>
            </table>
        </div>

        <!-- WHAT WE DELIVER -->
        <div style="margin:0 24px 24px;padding:20px;background:{D["bg_elevated"]};border:1px solid {D["border"]};border-radius:12px;">
            <div style="font-size:16px;font-weight:700;color:{D["text"]};margin-bottom:4px;text-align:center;">
                I bez nálezů na webu pro vás připravíme
            </div>
            <div style="font-size:13px;color:{D["text_muted"]};margin-bottom:16px;text-align:center;">
                Povinná dokumentace dle AI Act — bez ohledu na výsledek skenu webu
            </div>
            <table style="width:100%;border-collapse:separate;border-spacing:0 8px;">
                <tr><td style="padding:12px 14px;background:{D["bg_section"]};border-radius:8px;">
                    <div style="font-size:14px;font-weight:600;color:{D['text']};">&#128203; AI politika firmy</div>
                    <div style="font-size:12px;color:{D['text_muted']};margin-top:2px;">Interní pravidla pro zaměstnance — povinné pro každou firmu využívající jakékoliv AI nástroje</div>
                </td></tr>
                <tr><td style="padding:12px 14px;background:linear-gradient(135deg, {D["bg_section"]}, #1a1040);border-radius:8px;border:1px solid {D['accent_fuchsia']}30;">
                    <div style="font-size:14px;font-weight:600;color:{D['accent_fuchsia']};">&#127891; Školení zaměstnanců v PowerPointu</div>
                    <div style="font-size:12px;color:{D['text_muted']};margin-top:2px;">Povinnost AI gramotnosti dle <a href="{AI_ACT_LINKS['čl. 4']}" style="color:{D['accent_cyan']};text-decoration:underline;" target="_blank">čl. 4 AI Act</a> — platí od 2. února 2025!</div>
                </td></tr>
                <tr><td style="padding:12px 14px;background:{D["bg_section"]};border-radius:8px;">
                    <div style="font-size:14px;font-weight:600;color:{D['text']};">&#128203; Záznamový list o proškolení</div>
                    <div style="font-size:12px;color:{D['text_muted']};margin-top:2px;">Doklad prokazující splnění povinnosti — připraveno k podpisu zaměstnanci</div>
                </td></tr>
                <tr><td style="padding:12px 14px;background:{D["bg_section"]};border-radius:8px;">
                    <div style="font-size:14px;font-weight:600;color:{D['text']};">&#128209; Registr AI systémů</div>
                    <div style="font-size:12px;color:{D['text_muted']};margin-top:2px;">Evidence AI nástrojů ve firmě — po vyplnění dotazníku na míru pro {company_name}</div>
                </td></tr>
                <tr><td style="padding:12px 14px;background:{D["bg_section"]};border-radius:8px;">
                    <div style="font-size:14px;font-weight:600;color:{D['text']};">&#128196; AI Act Compliance Report</div>
                    <div style="font-size:12px;color:{D['text_muted']};margin-top:2px;">Kompletní přehled včetně interních systémů odhalených dotazníkem</div>
                </td></tr>
            </table>
        </div>

        <!-- PRICING PLANS -->
        <div style="margin:0 24px 24px;">
            <div style="font-size:18px;font-weight:700;color:{D["text"]};margin-bottom:16px;text-align:center;">
                Vyberte si balíček, který vám vyhovuje
            </div>

            <!-- BASIC -->
            <div style="margin-bottom:12px;padding:20px;background:{D["bg_elevated"]};border:1px solid {D["border"]};border-radius:12px;">
                <div style="font-size:16px;font-weight:700;color:{D["text"]};">BASIC</div>
                <div style="font-size:12px;color:{D["text_muted"]};margin-top:2px;">Compliance Kit — dokumenty ke stažení</div>
                <div style="font-size:28px;font-weight:800;color:{D["text"]};margin-top:8px;">4&nbsp;999&nbsp;Kč</div>
                <div style="font-size:11px;color:{D["text_muted"]};">jednorázově</div>
                <div style="margin-top:12px;font-size:13px;color:{D["text_secondary"]};line-height:1.8;">
                    ✓ Sken webu + AI Act report &nbsp;&nbsp;
                    ✓ 7 PDF dokumentů &nbsp;&nbsp;
                    ✓ Transparenční stránka &nbsp;&nbsp;
                    ✓ Registr AI systémů &nbsp;&nbsp;
                    ✓ AI politika firmy &nbsp;&nbsp;
                    ✓ Školení v PowerPointu &nbsp;&nbsp;
                    ✓ Záznamový list o proškolení
                </div>
            </div>

            <!-- PRO (highlighted) -->
            <div style="margin-bottom:12px;padding:3px;background:linear-gradient(135deg, {D["accent_fuchsia"]}, {D["accent_cyan"]});border-radius:14px;">
                <div style="padding:20px;background:{D["bg_card"]};border-radius:12px;">
                    <div style="text-align:center;margin-bottom:8px;">
                        <span style="display:inline-block;padding:3px 14px;border-radius:20px;font-size:11px;font-weight:600;color:#ffffff;background:linear-gradient(135deg, {D["accent_fuchsia"]}, {D["accent_purple"]});">
                            &#11088; Nejoblíbenější
                        </span>
                    </div>
                    <div style="font-size:16px;font-weight:700;color:{D["text"]};">PRO</div>
                    <div style="font-size:12px;color:{D["text_muted"]};margin-top:2px;">Vše z BASIC + implementace na klíč</div>
                    <div style="font-size:28px;font-weight:800;color:{D["accent_fuchsia"]};margin-top:8px;">14&nbsp;999&nbsp;Kč</div>
                    <div style="font-size:11px;color:{D["text_muted"]};">jednorázově</div>
                    <div style="margin-top:12px;font-size:13px;color:{D["text_secondary"]};line-height:1.8;">
                        ✓ Vše z BASIC &nbsp;&nbsp;
                        ✓ Instalace widgetu na web &nbsp;&nbsp;
                        ✓ Nastavení transparenční stránky &nbsp;&nbsp;
                        ✓ Úprava chatbot oznámení &nbsp;&nbsp;
                        ✓ 30 dní podpora &nbsp;&nbsp;
                        ✓ Prioritní zpracování
                    </div>
                </div>
            </div>

            <!-- ENTERPRISE -->
            <div style="margin-bottom:12px;padding:20px;background:{D["bg_elevated"]};border:1px solid {D["border"]};border-radius:12px;">
                <div style="font-size:16px;font-weight:700;color:{D["text"]};">ENTERPRISE</div>
                <div style="font-size:12px;color:{D["text_muted"]};margin-top:2px;">Kompletní řešení + konzultace + 2 roky monitoringu</div>
                <div style="font-size:28px;font-weight:800;color:{D["text"]};margin-top:8px;">39&nbsp;999&nbsp;Kč</div>
                <div style="font-size:11px;color:{D["text_muted"]};">jednorázově</div>
                <div style="margin-top:12px;font-size:13px;color:{D["text_secondary"]};line-height:1.8;">
                    ✓ Vše z PRO &nbsp;&nbsp;
                    ✓ 10h konzultací se specialistou &nbsp;&nbsp;
                    ✓ Metodická kontrola dokumentace &nbsp;&nbsp;
                    ✓ Rozšířený audit interních AI &nbsp;&nbsp;
                    ✓ 2 roky měsíčního monitoringu &nbsp;&nbsp;
                    ✓ Dedikovaný specialista &nbsp;&nbsp;
                    ✓ SLA 4h odezva
                </div>
            </div>
        </div>

        <!-- CTA BUTTONS -->
        <div style="margin:0 24px 24px;text-align:center;">
            <a href="https://aishield.cz/pricing" style="display:inline-block;padding:14px 40px;background:linear-gradient(135deg,{D["accent_fuchsia"]},{D["accent_purple"]});color:#ffffff;font-weight:700;font-size:15px;border-radius:12px;text-decoration:none;margin-bottom:12px;">
                Zobrazit ceník a objednat
            </a>
            <br>
            <a href="https://aishield.cz/registrace" style="display:inline-block;padding:12px 32px;background:transparent;color:{D["accent_cyan"]};font-weight:600;font-size:14px;border-radius:12px;text-decoration:none;border:1px solid {D["accent_cyan"]};margin-top:8px;">
                Vytvořit účet zdarma
            </a>
        </div>

        <!-- DEADLINE COUNTDOWN -->
        <div style="margin:0 24px 24px;padding:20px;background:#2a1015;border:2px solid {D["danger"]};border-radius:12px;text-align:center;">
            <div style="font-size:13px;color:#fca5a5;text-transform:uppercase;letter-spacing:1px;font-weight:600;">
                Do platnosti AI Act zbývá
            </div>
            <div style="font-size:32px;font-weight:800;color:{D["danger"]};margin-top:8px;">
                {_days_remaining()}
            </div>
            <p style="font-size:13px;color:#e2e8f0;margin-top:10px;line-height:1.6;">
                <a href="{AI_ACT_LINKS['čl. 50']}" style="color:#fca5a5;text-decoration:underline;font-weight:600;" target="_blank">AI Act</a>
                přichází v platnost <strong style="color:#ffffff;">2.&nbsp;srpna&nbsp;2026</strong>.
                Po tomto datu mohou úřady udělovat <strong style="color:#fca5a5;">pokuty za nesoulad</strong>.
                Doporučujeme provést interní audit co nejdříve.
            </p>
        </div>

        <!-- CONTACT -->
        <div style="margin:0 24px 24px;padding:20px;background:{D["bg_elevated"]};border:1px solid {D["border"]};border-radius:12px;text-align:center;">
            <div style="font-size:15px;font-weight:600;color:{D["text"]};">Máte otázky? Ozvěte se nám</div>
            <div style="margin-top:12px;font-size:14px;">
                <a href="mailto:info@aishield.cz" style="color:{D["accent_cyan"]};text-decoration:none;font-weight:500;">info@aishield.cz</a>
                &nbsp;&nbsp;|&nbsp;&nbsp;
                <a href="tel:+420732716141" style="color:{D["accent_cyan"]};text-decoration:none;font-weight:500;">+420 732 716 141</a>
            </div>
            <div style="margin-top:8px;font-size:12px;color:{D["text_muted"]};">
                Odpovídáme do 24 hodin v pracovní dny.
            </div>
        </div>

        <!-- FOOTER -->
        <div style="background:linear-gradient(135deg, {D["gradient_start"]}, {D["gradient_mid"]});padding:28px 24px;text-align:center;border-top:1px solid {D["border"]};">
            <div style="font-size:14px;font-weight:600;color:{D["text_secondary"]};">
                <span style="color:#ffffff;">AI</span><span style="color:{D["accent_fuchsia"]};">shield</span><span style="color:{D["text_muted"]};">.cz</span>
                &nbsp;— AI Act compliance pro české firmy
            </div>
            <div style="font-size:11px;color:{D["text_muted"]};margin-top:10px;line-height:1.6;">
                Tento email byl vygenerován na základě automatického skenu webu {url}.<br>
                &copy; 2025 AIshield.cz | Provozovatel: Martin Haynes, IČO: 17889251
            </div>
        </div>

    </div>
</body>
</html>"""

    return html
