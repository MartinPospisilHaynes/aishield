"""
AIshield.cz — Email Templates v2
Personalizované email šablony pro outbound kampaně.
Obsahují: screenshot webu, konkrétní nálezy, vizuální důkazy.
"""

from dataclasses import dataclass, field


@dataclass
class EmailVariant:
    """A/B testovací varianta emailu."""
    subject: str
    body_html: str
    variant_id: str


@dataclass
class FindingItem:
    """Jeden nález AI systému pro embeddování do emailu."""
    name: str
    category: str
    risk_level: str  # minimal, limited, high, prohibited
    ai_act_article: str
    action_required: str
    description: str = ""


def _risk_badge(risk_level: str) -> str:
    """Vrátí HTML badge pro úroveň rizika."""
    colors = {
        "minimal": ("#059669", "#ecfdf5", "🟢 Minimální"),
        "limited": ("#d97706", "#fffbeb", "🟡 Omezené"),
        "high": ("#dc2626", "#fef2f2", "🔴 Vysoké"),
        "prohibited": ("#7c3aed", "#f5f3ff", "⛔ Zakázané"),
    }
    fg, bg, label = colors.get(risk_level, ("#64748b", "#f8fafc", "⚪ Neznámé"))
    return (
        f'<span style="display:inline-block; background:{bg}; color:{fg}; '
        f'font-weight:600; padding:3px 10px; border-radius:6px; font-size:12px;">'
        f'{label}</span>'
    )


def _findings_table(findings: list[FindingItem]) -> str:
    """Vygeneruje HTML tabulku nálezů pro email."""
    if not findings:
        return ""

    rows = ""
    for i, f in enumerate(findings):
        bg = "#ffffff" if i % 2 == 0 else "#f8fafc"
        rows += f"""
        <tr style="background:{bg};">
            <td style="padding:12px 16px; border-bottom:1px solid #e2e8f0;">
                <strong style="color:#0f172a;">{f.name}</strong><br>
                <span style="font-size:12px; color:#64748b;">{f.description}</span>
            </td>
            <td style="padding:12px 16px; border-bottom:1px solid #e2e8f0; text-align:center;">
                {_risk_badge(f.risk_level)}
            </td>
            <td style="padding:12px 16px; border-bottom:1px solid #e2e8f0; font-size:13px; color:#475569;">
                {f.ai_act_article}<br>
                <em>{f.action_required}</em>
            </td>
        </tr>"""

    return f"""
    <table style="width:100%; border-collapse:collapse; border:1px solid #e2e8f0; border-radius:8px; overflow:hidden; margin:20px 0;">
        <thead>
            <tr style="background:linear-gradient(135deg, #0f172a, #1e1b4b);">
                <th style="padding:12px 16px; color:#e2e8f0; text-align:left; font-size:13px;">AI Systém</th>
                <th style="padding:12px 16px; color:#e2e8f0; text-align:center; font-size:13px;">Riziko</th>
                <th style="padding:12px 16px; color:#e2e8f0; text-align:left; font-size:13px;">Povinnost</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>"""


def get_outbound_email(
    company_name: str,
    company_url: str,
    findings_count: int,
    top_finding: str,
    variant: str = "A",
    to_email: str = "",
    screenshot_url: str = "",
    findings: list[FindingItem] | None = None,
    scan_id: str = "",
) -> EmailVariant:
    """
    Vygeneruje personalizovaný outbound email.
    Obsahuje konkrétní data z analýzy webu dané firmy.

    Args:
        company_name: Název firmy
        company_url: URL webu
        findings_count: Počet nalezených AI systémů
        top_finding: Hlavní nález (text)
        variant: A = detailní, B = krátký naléhavý
        to_email: Email příjemce (pro unsubscribe link)
        screenshot_url: URL screenshotu webu z Supabase Storage
        findings: Seznam konkrétních nálezů (pro tabulku v emailu)
        scan_id: ID skenu (pro link na report)
    """
    from urllib.parse import quote
    unsubscribe = f"https://api.aishield.cz/api/unsubscribe?email={quote(to_email)}&company={quote(company_url)}"
    scan_link = f"https://aishield.cz/scan?url={company_url}"
    if scan_id:
        report_link = f"https://aishield.cz/report/{scan_id}"
    else:
        report_link = scan_link

    # Správný tvar číslovky v češtině
    if findings_count == 1:
        pocet_text = "1 AI systém"
    elif 2 <= findings_count <= 4:
        pocet_text = f"{findings_count} AI systémy"
    else:
        pocet_text = f"{findings_count} AI systémů"

    findings_table = _findings_table(findings) if findings else ""

    # Screenshot sekce
    screenshot_section = ""
    if screenshot_url:
        screenshot_section = f"""
    <div style="margin: 24px 0;">
        <p style="font-size: 13px; color: #64748b; margin-bottom: 8px;">
            📸 <strong>Screenshot vašeho webu</strong> — vizuální důkaz nalezených AI systémů:
        </p>
        <div style="border: 2px solid #dc2626; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            <img src="{screenshot_url}" alt="Screenshot {company_url}" 
                 style="width: 100%; height: auto; display: block;">
        </div>
        <p style="font-size: 11px; color: #94a3b8; margin-top: 6px;">
            Screenshot pořízen automatickým scannerem AIshield.cz dne {_current_date_cs()}.
        </p>
    </div>"""

    if variant == "A":
        return EmailVariant(
            subject=f"AI Act: {company_name} — nalezli jsme {pocet_text} na vašem webu",
            variant_id="A",
            body_html=f"""
<!DOCTYPE html>
<html lang="cs">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 640px; margin: 0 auto; padding: 0; color: #334155; line-height: 1.7; background: #f8fafc;">

<!-- Header -->
<div style="background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%); border-radius: 0 0 16px 16px; padding: 32px 30px; text-align: center;">
    <h1 style="color: #e879f9; font-size: 28px; margin: 0 0 4px 0; letter-spacing: -0.5px;">
        AI<span style="color: white;">shield</span><span style="color: #64748b; font-size: 16px;">.cz</span>
    </h1>
    <p style="color: #94a3b8; font-size: 13px; margin: 0;">Automatická AI Act compliance kontrola</p>
</div>

<div style="padding: 30px; background: white; margin: 0;">

<p style="font-size: 15px;">Dobrý den,</p>

<p style="font-size: 15px;">provedli jsme automatickou bezpečnostní analýzu webu
<strong><a href="https://{company_url}" style="color: #6d28d9; text-decoration: none;">{company_url}</a></strong>
a nalezli jsme <strong style="color: #dc2626;">{pocet_text}</strong>,
které podléhají novému nařízení EU o umělé inteligenci
(<a href="https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689" style="color: #6d28d9;">AI Act, Nařízení EU 2024/1689</a>).</p>

<!-- Urgentní box -->
<div style="background: linear-gradient(135deg, #fef2f2, #fff1f2); border-left: 4px solid #dc2626; padding: 18px 20px; border-radius: 0 12px 12px 0; margin: 24px 0;">
    <p style="margin: 0 0 4px 0; font-size: 13px; color: #991b1b; font-weight: 600;">
        ⚠️ HLAVNÍ NÁLEZ:
    </p>
    <p style="margin: 0; font-size: 14px; color: #991b1b;">
        {top_finding}
    </p>
</div>

{screenshot_section}

<!-- Tabulka nálezů -->
{findings_table}

<!-- Deadline box -->
<div style="background: linear-gradient(135deg, #eff6ff, #eef2ff); border: 1px solid #bfdbfe; border-radius: 12px; padding: 20px; margin: 24px 0; text-align: center;">
    <p style="margin: 0 0 8px 0; font-size: 22px; font-weight: 700; color: #1e40af;">
        ⏰ Deadline: 2. srpna 2026
    </p>
    <p style="margin: 0; font-size: 14px; color: #3b82f6;">
        Firmy, které nesplní požadavky na transparenci, riskují pokutu<br>
        až <strong>35 milionů EUR</strong> nebo <strong>7 % ročního obratu</strong>.
    </p>
</div>

<h3 style="color: #0f172a; font-size: 16px; margin-top: 28px;">Co musíte udělat:</h3>
<table style="width:100%; margin: 12px 0;">
    <tr>
        <td style="padding:8px 12px; vertical-align:top;">✅</td>
        <td style="padding:8px 0; font-size:14px;">Označit AI systémy transparenčním oznámením (<strong>čl. 50 AI Act</strong>)</td>
    </tr>
    <tr>
        <td style="padding:8px 12px; vertical-align:top;">✅</td>
        <td style="padding:8px 0; font-size:14px;">Vytvořit registr všech AI systémů ve firmě</td>
    </tr>
    <tr>
        <td style="padding:8px 12px; vertical-align:top;">✅</td>
        <td style="padding:8px 0; font-size:14px;">Proškolit zaměstnance v AI gramotnosti (<strong>čl. 4</strong> — platí UŽ TEĎ)</td>
    </tr>
    <tr>
        <td style="padding:8px 12px; vertical-align:top;">✅</td>
        <td style="padding:8px 0; font-size:14px;">Vypracovat AI politiku a compliance dokumentaci</td>
    </tr>
</table>

<!-- USP box -->
<div style="background: #f0fdf4; border: 1px solid #86efac; border-radius: 12px; padding: 20px; margin: 24px 0;">
    <p style="margin: 0 0 8px 0; font-weight: 600; color: #166534; font-size: 15px;">
        🛡️ AIshield.cz — jediné automatizované řešení v ČR
    </p>
    <p style="margin: 0; font-size: 14px; color: #15803d;">
        Jsme první a <strong>jediná firma na českém trhu</strong>, která nabízí kompletní automatizovanou
        AI Act compliance. Žádné drahé konzultace za stovky tisíc — kompletní řešení od <strong>4 999 Kč</strong>.
    </p>
</div>

<!-- CTA -->
<div style="text-align: center; margin: 32px 0;">
    <a href="{report_link}"
       style="display: inline-block; background: linear-gradient(135deg, #7c3aed, #a855f7, #d946ef); color: white; font-weight: 700; padding: 16px 40px; border-radius: 12px; text-decoration: none; font-size: 16px; box-shadow: 0 4px 16px rgba(168, 85, 247, 0.4); letter-spacing: 0.3px;">
        📊 Zobrazit kompletní report ZDARMA
    </a>
</div>

<p style="font-size: 13px; color: #64748b; margin-top: 24px;">
    Máte dotazy? Odpovězte přímo na tento email nebo nás kontaktujte
    na <a href="tel:+420732716141" style="color: #6d28d9;">+420 732 716 141</a>.
</p>

<p style="font-size: 13px; color: #64748b;">
    S pozdravem,<br>
    <strong>Martin Haynes</strong><br>
    AIshield.cz — AI Act compliance pro české firmy
</p>

</div>

<!-- Footer -->
<div style="padding: 20px 30px; background: #f1f5f9; border-top: 1px solid #e2e8f0;">
    <p style="font-size: 11px; color: #94a3b8; text-align: center; margin: 0;">
        Tento email byl odeslán na základě veřejně dostupné analýzy webu {company_url}.
        Není spam — je to upozornění na reálné právní riziko dle Nařízení EU 2024/1689.<br><br>
        AIshield.cz | Martin Haynes, IČO: 17889251 | Mlýnská 53, 783 53 Velká Bystřice<br>
        <a href="{unsubscribe}" style="color: #94a3b8;">Odhlásit se z odběru</a> |
        <a href="https://aishield.cz" style="color: #94a3b8;">aishield.cz</a>
    </p>
</div>

</body>
</html>""",
        )

    else:  # Variant B — kratší, naléhavější
        return EmailVariant(
            subject=f"⚠️ {company_name}: {pocet_text} bez povinného označení — pokuta až 35 mil. EUR",
            variant_id="B",
            body_html=f"""
<!DOCTYPE html>
<html lang="cs">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 640px; margin: 0 auto; padding: 0; color: #334155; line-height: 1.7; background: #f8fafc;">

<div style="background: #0f172a; padding: 20px 30px; text-align: center;">
    <span style="color: #e879f9; font-size: 20px; font-weight: 700;">AI</span><span style="color: white; font-size: 20px; font-weight: 700;">shield</span><span style="color: #64748b; font-size: 14px;">.cz</span>
</div>

<div style="padding: 30px; background: white;">

<p>Dobrý den,</p>

<p>na webu <strong><a href="https://{company_url}" style="color: #6d28d9;">{company_url}</a></strong>
jsme identifikovali <strong style="color: #dc2626;">{pocet_text}</strong> bez povinného transparenčního
označení podle EU AI Act.</p>

{screenshot_section}

<div style="background: #fef2f2; border-radius: 12px; padding: 20px; margin: 20px 0; text-align: center;">
    <p style="margin: 0 0 4px 0; font-size: 24px; font-weight: 700; color: #dc2626;">
        35 000 000 EUR
    </p>
    <p style="margin: 0; font-size: 13px; color: #991b1b;">
        maximální pokuta za nesplnění AI Act | Deadline: <strong>2. 8. 2026</strong>
    </p>
</div>

{findings_table}

<p style="font-size: 14px;">Jsme <strong>jediná firma v ČR</strong> specializovaná na automatizovanou AI Act compliance.
Kompletní řešení od 4 999 Kč — ne stovky tisíc za právní konzultace.</p>

<div style="text-align: center; margin: 28px 0;">
    <a href="{report_link}"
       style="display: inline-block; background: #0f172a; color: #e879f9; font-weight: 700; padding: 14px 36px; border-radius: 10px; text-decoration: none; border: 2px solid #e879f9; font-size: 15px;">
        ⚡ Bezplatný compliance report za 60 sekund
    </a>
</div>

<p style="font-size: 13px; color: #64748b;">
    S pozdravem,<br>
    <strong>Martin Haynes</strong> | AIshield.cz<br>
    📞 <a href="tel:+420732716141" style="color: #6d28d9;">+420 732 716 141</a>
</p>

</div>

<div style="padding: 16px 30px; background: #f1f5f9; border-top: 1px solid #e2e8f0;">
    <p style="font-size: 11px; color: #94a3b8; text-align: center; margin: 0;">
        <a href="{unsubscribe}" style="color: #94a3b8;">Odhlásit se</a> | AIshield.cz | IČO: 17889251
    </p>
</div>

</body>
</html>""",
        )


def _current_date_cs() -> str:
    """Vrátí aktuální datum v českém formátu."""
    from datetime import datetime
    months = {
        1: "ledna", 2: "února", 3: "března", 4: "dubna", 5: "května", 6: "června",
        7: "července", 8: "srpna", 9: "září", 10: "října", 11: "listopadu", 12: "prosince",
    }
    now = datetime.utcnow()
    return f"{now.day}. {months[now.month]} {now.year}"


def get_followup_email(
    company_name: str,
    company_url: str,
    days_since: int,
    to_email: str = "",
    scan_id: str = "",
) -> EmailVariant:
    """Follow-up email pro firmy, které nereagovaly."""
    from urllib.parse import quote
    report_link = f"https://aishield.cz/report/{scan_id}" if scan_id else f"https://aishield.cz/scan?url={company_url}"
    unsubscribe = f"https://api.aishield.cz/api/unsubscribe?email={quote(to_email)}&company={quote(company_url)}"

    # Spočítat zbývající dny do deadlinu (2. srpna 2026)
    from datetime import datetime
    deadline = datetime(2026, 8, 2)
    remaining_days = (deadline - datetime.utcnow()).days

    return EmailVariant(
        subject=f"Připomínka: {company_name} — {remaining_days} dní do AI Act deadlinu",
        variant_id="followup",
        body_html=f"""
<!DOCTYPE html>
<html lang="cs">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="font-family: -apple-system, BlinkMp, 'Segoe UI', Roboto, sans-serif; max-width: 640px; margin: 0 auto; padding: 0; color: #334155; line-height: 1.7; background: #f8fafc;">

<div style="background: linear-gradient(135deg, #0f172a, #1e1b4b); padding: 24px 30px; text-align: center;">
    <span style="color: #e879f9; font-size: 22px; font-weight: 700;">AI</span><span style="color: white; font-size: 22px; font-weight: 700;">shield</span><span style="color: #64748b; font-size: 14px;">.cz</span>
</div>

<div style="padding: 30px; background: white;">

<p>Dobrý den,</p>

<p>před {days_since} dny jsme vám poslali upozornění na AI systémy
nalezené na webu <strong>{company_url}</strong>.</p>

<div style="background: #fef2f2; border-radius: 12px; padding: 20px; margin: 20px 0; text-align: center;">
    <p style="margin: 0 0 4px 0; font-size: 36px; font-weight: 700; color: #dc2626;">
        {remaining_days}
    </p>
    <p style="margin: 0; font-size: 14px; color: #991b1b;">
        dní zbývá do plné účinnosti AI Act (2. srpna 2026)
    </p>
</div>

<p>Příprava compliance dokumentace zabere čas. Pokud začnete teď, stihnete
vše včas a vyhnete se pokutám.</p>

<p>Váš bezplatný compliance report je stále k dispozici:</p>

<div style="text-align: center; margin: 28px 0;">
    <a href="{report_link}"
       style="display: inline-block; background: linear-gradient(135deg, #7c3aed, #a855f7); color: white; font-weight: 700; padding: 14px 36px; border-radius: 10px; text-decoration: none; font-size: 15px;">
        Zobrazit report
    </a>
</div>

<p style="font-size: 13px; color: #64748b;">
    S pozdravem,<br>
    <strong>Martin Haynes</strong> | AIshield.cz<br>
    📞 +420 732 716 141
</p>

</div>

<div style="padding: 16px 30px; background: #f1f5f9;">
    <p style="font-size: 11px; color: #94a3b8; text-align: center; margin: 0;">
        <a href="{unsubscribe}" style="color: #94a3b8;">Odhlásit se</a> | AIshield.cz | IČO: 17889251
    </p>
</div>

</body>
</html>""",
    )
