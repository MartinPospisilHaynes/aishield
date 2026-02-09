"""
AIshield.cz — Email Templates
Personalizované email šablony pro outbound kampaně.
"""

from dataclasses import dataclass


@dataclass
class EmailVariant:
    """A/B testovací varianta emailu."""
    subject: str
    body_html: str
    variant_id: str


def get_outbound_email(
    company_name: str,
    company_url: str,
    findings_count: int,
    top_finding: str,
    variant: str = "A",
    to_email: str = "",
) -> EmailVariant:
    """
    Vygeneruje personalizovaný outbound email.
    Obsahuje konkrétní data z analýzy webu dané firmy.
    """
    from urllib.parse import quote
    unsubscribe = f"https://aishield.cz/api/unsubscribe?email={quote(to_email)}&company={quote(company_url)}"
    scan_link = f"https://aishield.cz/scan?url={company_url}"

    if variant == "A":
        return EmailVariant(
            subject=f"AI Act: {company_name} — nalezli jsme {findings_count} AI systémů na vašem webu",
            variant_id="A",
            body_html=f"""
<!DOCTYPE html>
<html lang="cs">
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #334155; line-height: 1.6;">

<div style="background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); border-radius: 12px; padding: 30px; margin-bottom: 24px;">
    <h1 style="color: #e879f9; font-size: 20px; margin: 0 0 8px 0;">
        AI<span style="color: white;">shield</span><span style="color: #64748b; font-size: 14px;">.cz</span>
    </h1>
    <p style="color: #94a3b8; font-size: 14px; margin: 0;">Automatická AI Act compliance kontrola</p>
</div>

<p>Dobrý den,</p>

<p>na webu <strong>{company_url}</strong> jsme automaticky detekovali
<strong style="color: #dc2626;">{findings_count} AI systémů</strong>,
které podléhají novému nařízení EU o umělé inteligenci (AI Act).</p>

<div style="background: #fef2f2; border-left: 4px solid #dc2626; padding: 16px; border-radius: 0 8px 8px 0; margin: 20px 0;">
    <p style="margin: 0; font-size: 14px; color: #991b1b;">
        <strong>Hlavní nález:</strong> {top_finding}
    </p>
</div>

<p>AI Act vstupuje v platnost <strong>2. srpna 2026</strong>.
Firmy, které nesplní požadavky na transparenci, riskují pokutu
až <strong>35 milionů EUR</strong> nebo 7 % ročního obratu.</p>

<h3 style="color: #0f172a; font-size: 16px;">Co musíte udělat:</h3>
<ul style="padding-left: 20px;">
    <li>Označit AI systémy transparenčním oznámením (čl. 50)</li>
    <li>Vytvořit registr AI systémů</li>
    <li>Proškolit zaměstnance v AI gramotnosti (čl. 4)</li>
</ul>

<div style="text-align: center; margin: 30px 0;">
    <a href="{scan_link}"
       style="display: inline-block; background: linear-gradient(135deg, #d946ef, #a855f7); color: white; font-weight: 600; padding: 14px 32px; border-radius: 10px; text-decoration: none; font-size: 15px;">
        Zobrazit kompletní report ZDARMA
    </a>
</div>

<p style="font-size: 13px; color: #64748b;">
    Tento email byl odeslán na základě veřejně dostupné analýzy webu {company_url}.
    Není spam — je to upozornění na reálné právní riziko.
</p>

<hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;">

<p style="font-size: 11px; color: #94a3b8; text-align: center;">
    AIshield.cz | Martin Haynes, IČO: 17889251 | Mlýnská 53, 783 53 Velká Bystřice<br>
    <a href="{unsubscribe}" style="color: #94a3b8;">Odhlásit se z odběru</a>
</p>

</body>
</html>""",
        )

    else:  # Variant B — kratší, naléhavější
        return EmailVariant(
            subject=f"Porušuje {company_name} EU zákon o AI? Zjistěte ZDARMA",
            variant_id="B",
            body_html=f"""
<!DOCTYPE html>
<html lang="cs">
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #334155; line-height: 1.6;">

<p>Dobrý den,</p>

<p>rychlá informace: na webu <strong>{company_url}</strong> jsme našli
<strong>{findings_count} AI systémů</strong> bez povinného označení podle EU AI Act.</p>

<p>Deadline: <strong>2. 8. 2026</strong>. Pokuta: až <strong>35 mil. EUR</strong>.</p>

<p>Připravili jsme vám bezplatný report — trvá 60 sekund:</p>

<div style="text-align: center; margin: 24px 0;">
    <a href="{scan_link}"
       style="display: inline-block; background: #0f172a; color: #e879f9; font-weight: 600; padding: 12px 28px; border-radius: 10px; text-decoration: none; border: 1px solid #e879f9;">
        Zkontrolovat {company_url}
    </a>
</div>

<p style="font-size: 13px; color: #64748b;">S pozdravem,<br>Martin Haynes | AIshield.cz</p>

<hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;">
<p style="font-size: 11px; color: #94a3b8; text-align: center;">
    <a href="{unsubscribe}" style="color: #94a3b8;">Odhlásit se</a>
</p>

</body>
</html>""",
        )


def get_followup_email(
    company_name: str,
    company_url: str,
    days_since: int,
    to_email: str = "",
) -> EmailVariant:
    """Follow-up email pro firmy, které nereagovaly."""
    from urllib.parse import quote
    scan_link = f"https://aishield.cz/scan?url={company_url}"
    unsubscribe = f"https://aishield.cz/api/unsubscribe?email={quote(to_email)}&company={quote(company_url)}"

    return EmailVariant(
        subject=f"Připomínka: AI Act compliance pro {company_name}",
        variant_id="followup",
        body_html=f"""
<!DOCTYPE html>
<html lang="cs">
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #334155; line-height: 1.6;">

<p>Dobrý den,</p>

<p>před {days_since} dny jsme vám poslali upozornění na AI systémy
nalezené na webu {company_url}.</p>

<p>Chceme se jen ujistit, že jste informaci obdrželi.
EU AI Act vstupuje v platnost za <strong>méně než 6 měsíců</strong>
a příprava zabere čas.</p>

<p>Váš bezplatný compliance report je stále k dispozici:</p>

<div style="text-align: center; margin: 24px 0;">
    <a href="{scan_link}"
       style="display: inline-block; background: linear-gradient(135deg, #d946ef, #a855f7); color: white; font-weight: 600; padding: 12px 28px; border-radius: 10px; text-decoration: none;">
        Zobrazit report
    </a>
</div>

<p style="font-size: 13px; color: #64748b;">S pozdravem,<br>tým AIshield.cz</p>

<hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;">
<p style="font-size: 11px; color: #94a3b8; text-align: center;">
    <a href="{unsubscribe}" style="color: #94a3b8;">Odhlásit se</a>
</p>

</body>
</html>""",
    )
