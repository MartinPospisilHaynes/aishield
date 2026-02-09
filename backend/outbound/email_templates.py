"""
AIshield.cz — Email Templates v3
Čistý, lidský styl. Žádný spam, žádné emojis, žádné gradienty.
Člověk píše člověku — odborník, který chce upřímně pomoct.
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


def _findings_list_plain(findings: list[FindingItem]) -> str:
    """Vygeneruje čistý textový seznam nálezů (minimální HTML)."""
    if not findings:
        return ""

    items = ""
    for f in findings:
        risk_cs = {
            "minimal": "minimální",
            "limited": "omezené",
            "high": "vysoké",
            "prohibited": "zakázané",
        }.get(f.risk_level, f.risk_level)

        items += f"""
        <tr>
            <td style="padding: 8px 0; border-bottom: 1px solid #eee; vertical-align: top;">
                <strong>{f.name}</strong>
                {f' — <em>{f.description}</em>' if f.description else ''}
            </td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #eee; text-align: center; white-space: nowrap;">
                riziko: {risk_cs}
            </td>
            <td style="padding: 8px 0; border-bottom: 1px solid #eee; font-size: 13px; color: #555;">
                {f.ai_act_article}
            </td>
        </tr>"""

    return f"""
    <table style="width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 14px;">
        <thead>
            <tr style="border-bottom: 2px solid #333;">
                <th style="padding: 6px 0; text-align: left;">AI systém</th>
                <th style="padding: 6px 12px; text-align: center;">Riziko</th>
                <th style="padding: 6px 0; text-align: left;">AI Act</th>
            </tr>
        </thead>
        <tbody>{items}</tbody>
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
    Vygeneruje personalizovaný outbound email v3.
    Čistý styl, žádný spam, žádné emojis.
    """
    from urllib.parse import quote
    unsubscribe = f"https://api.aishield.cz/api/unsubscribe?email={quote(to_email)}&company={quote(company_url)}"
    report_link = f"https://aishield.cz/report/{scan_id}" if scan_id else f"https://aishield.cz/scan?url={company_url}"

    # Správný tvar číslovky
    if findings_count == 1:
        pocet_text = "1 AI systém"
    elif 2 <= findings_count <= 4:
        pocet_text = f"{findings_count} AI systémy"
    else:
        pocet_text = f"{findings_count} AI systémů"

    findings_table = _findings_list_plain(findings) if findings else ""

    # Screenshot — jednoduchý, bez červeného rámečku
    screenshot_section = ""
    if screenshot_url:
        screenshot_section = f"""
    <p style="margin-top: 16px; font-size: 13px; color: #666;">
        (Screenshot vašeho webu z {_current_date_cs()}:)
    </p>
    <img src="{screenshot_url}" alt="Screenshot {company_url}"
         style="max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 16px;">"""

    # ── Varianta A — Profesionální konzultant ──
    if variant == "A":
        return EmailVariant(
            subject=f"AI Act a web {company_url} — krátké upozornění",
            variant_id="A",
            body_html=_wrap_plain_email(f"""
<p>Dobrý den,</p>

<p>jmenuji se Martin Haynes a zabývám se compliance s EU AI Act
(Nařízení 2024/1689) pro české firmy.</p>

<p>Prošel jsem si web <strong>{company_url}</strong> a narazil jsem
na {pocet_text}, které spadají pod novou regulaci:</p>

{findings_table}

<p>Hlavní zjištění: <strong>{top_finding}</strong></p>

{screenshot_section}

<p>Co to znamená v praxi?<br>
Od 2. srpna 2026 musí být každý AI systém na webu transparentně
označen — uživatel musí vědět, že komunikuje s AI, ne s člověkem.
Za nedodržení hrozí sankce ze strany dozorového úřadu.</p>

<p>Neříkám to, abych strašil. Jde o konkrétní povinnost, kterou
většina českých firem zatím neřeší, protože o ní neví.</p>

<p>Připravil jsem pro vás krátký report s konkrétními kroky,
co je potřeba udělat:</p>

<p><a href="{report_link}" style="color: #1a56db;">Zobrazit compliance report</a></p>

<p>Pokud máte dotazy, klidně odpovězte na tento email nebo
zavolejte na +420 732 716 141.</p>

<p>S pozdravem,<br>
Martin Haynes<br>
<span style="color: #666;">AIshield.cz — AI Act compliance</span></p>
""", company_url, unsubscribe),
        )

    # ── Varianta B — Stručné upozornění ──
    else:
        return EmailVariant(
            subject=f"Upozornění k webu {company_url} — AI Act",
            variant_id="B",
            body_html=_wrap_plain_email(f"""
<p>Dobrý den,</p>

<p>na webu <strong>{company_url}</strong> jsem identifikoval
{pocet_text} bez povinného označení dle EU AI Act.</p>

{findings_table}

{screenshot_section}

<p>Stručně: od srpna 2026 musí být AI systémy na webech
transparentně označeny. Připravil jsem konkrétní report,
co u vás opravit:</p>

<p><a href="{report_link}" style="color: #1a56db;">Zobrazit report</a></p>

<p>Martin Haynes<br>
<span style="color: #666;">+420 732 716 141 | AIshield.cz</span></p>
""", company_url, unsubscribe),
        )


def _wrap_plain_email(content: str, company_url: str, unsubscribe: str) -> str:
    """Obalí obsah do minimálního HTML — čistý, Plain-textový vzhled."""
    return f"""<!DOCTYPE html>
<html lang="cs">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #222; line-height: 1.6; font-size: 15px; background: #fff;">

{content}

<hr style="border: none; border-top: 1px solid #ddd; margin: 32px 0 16px 0;">
<p style="font-size: 11px; color: #999; line-height: 1.4;">
    Tento email je jednorázové upozornění založené na veřejně dostupné
    analýze webu {company_url}. Nebudeme vás zahlcovat dalšími emaily.<br>
    AIshield.cz | Martin Haynes, IČO: 17889251 | Mlýnská 53, 783 53 Velká Bystřice<br>
    <a href="{unsubscribe}" style="color: #999;">Nechci dostávat další upozornění</a>
</p>

</body>
</html>"""


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
    """Follow-up email pro firmy, které nereagovaly. Taky čistý styl."""
    from urllib.parse import quote
    report_link = f"https://aishield.cz/report/{scan_id}" if scan_id else f"https://aishield.cz/scan?url={company_url}"
    unsubscribe = f"https://api.aishield.cz/api/unsubscribe?email={quote(to_email)}&company={quote(company_url)}"

    from datetime import datetime
    deadline = datetime(2026, 8, 2)
    remaining_days = (deadline - datetime.utcnow()).days

    return EmailVariant(
        subject=f"Doplnění k AI Act analýze webu {company_url}",
        variant_id="followup",
        body_html=_wrap_plain_email(f"""
<p>Dobrý den,</p>

<p>před {days_since} dny jsem vám poslal upozornění k AI systémům
na webu {company_url}.</p>

<p>Chápu, že to nemusí být priorita — jen pro kontext:
do plné účinnosti AI Act zbývá {remaining_days} dní a příprava
compliance dokumentace nějaký čas zabere.</p>

<p>Váš report je stále k dispozici:
<a href="{report_link}" style="color: #1a56db;">zobrazit report</a></p>

<p>Pokud to řešíte s někým jiným nebo to nepotřebujete, klidně
mě ignorujte — nebudu dál obtěžovat.</p>

<p>Martin Haynes<br>
<span style="color: #666;">+420 732 716 141 | AIshield.cz</span></p>
""", company_url, unsubscribe),
    )
