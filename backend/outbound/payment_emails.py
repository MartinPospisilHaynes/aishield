"""
AIshield.cz — Payment Email Templates
Branded HTML email templates for payment lifecycle:
1. Bank transfer invoice (order confirmation with payment details + QR code)
2. Payment received confirmation
3. Delivery notification
"""

import base64
import io
from datetime import datetime, timedelta

try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

# ── Brand constants (matching report_email.py) ──
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

PLAN_NAMES = {
    "basic": "BASIC — AI Act Compliance Kit",
    "pro": "PRO — Compliance Kit + implementace na klíč",
    "enterprise": "ENTERPRISE — Komplexní řešení + 2 roky péče",
    "coffee": "Kafé ☕",
}


def _email_wrapper(content: str) -> str:
    """Wrap content in branded email shell — dark theme matching aishield.cz."""
    return f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AIshield.cz</title>
</head>
<body style="margin:0;padding:0;background-color:#0a0a1a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#0a0a1a;">
<tr><td align="center" style="padding:32px 16px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background-color:#0f172a;border-radius:16px;border:1px solid rgba(255,255,255,0.06);overflow:hidden;">

<!-- Header -->
<tr><td style="background:linear-gradient(135deg,#1e1b4b 0%,#312e81 50%,#1e1b4b 100%);padding:32px 40px;text-align:center;">
    <div style="margin-bottom:8px;">
        {SHIELD_LOGO_SVG}
        <span style="font-size:22px;font-weight:800;color:#ffffff;letter-spacing:0.5px;vertical-align:middle;">AIshield.cz</span>
    </div>
    <div style="font-size:11px;color:rgba(255,255,255,0.5);letter-spacing:1px;text-transform:uppercase;">AI Act Compliance</div>
</td></tr>

<!-- Content -->
<tr><td style="padding:40px 40px 32px 40px;">
{content}
</td></tr>

<!-- Footer -->
<tr><td style="background:linear-gradient(135deg,#1e1b4b 0%,#312e81 100%);padding:28px 40px;text-align:center;">
    <p style="margin:0 0 8px 0;font-size:12px;color:rgba(255,255,255,0.7);">
        AIshield.cz — AI Act compliance pro české firmy
    </p>
    <p style="margin:0 0 4px 0;font-size:11px;color:rgba(255,255,255,0.4);">
        Martin Haynes | IČO: 04291247
    </p>
    <p style="margin:0;font-size:11px;color:rgba(255,255,255,0.4);">
        <a href="mailto:info@aishield.cz" style="color:#a78bfa;text-decoration:none;">info@aishield.cz</a>
        &nbsp;·&nbsp;
        <a href="https://aishield.cz" style="color:#a78bfa;text-decoration:none;">aishield.cz</a>
    </p>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""


def generate_variable_symbol(order_number: str) -> str:
    """
    Generate a numeric variable symbol from order number.
    Takes the hex part of the order number and converts to a numeric string.
    Example: AS-BASIC-A0B1C2D3 → 1680851667 (first 10 digits of hex-to-int)
    """
    # Extract the hex part (last 8 chars)
    hex_part = order_number.split("-")[-1] if "-" in order_number else order_number
    # Convert hex to int, take first 10 digits (max for VS in CZ banking)
    num = int(hex_part, 16)
    vs = str(num)[:10]
    return vs


# ── IBAN for AIshield.cz account (2610538018/3030 = Air Bank) ──
AISHIELD_IBAN = "CZ9130300000002610538018"


def generate_payment_qr_base64(amount: int, variable_symbol: str, order_number: str) -> str:
    """
    Generuje platební QR kód dle českého standardu SPAYD (Short Payment Descriptor).
    Vrací base64-encoded PNG obrázek QR kódu.

    SPAYD formát: SPD*1.0*ACC:{IBAN}*AM:{částka}*CC:CZK*X-VS:{VS}*MSG:{zpráva}
    Podporován všemi českými bankami (George, Air Bank, ČSOB, mBank, Fio, KB...).
    """
    if not HAS_QRCODE:
        return ""

    spayd = (
        f"SPD*1.0"
        f"*ACC:{AISHIELD_IBAN}"
        f"*AM:{amount:.2f}"
        f"*CC:CZK"
        f"*X-VS:{variable_symbol}"
        f"*MSG:{order_number}"
    )

    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=6, border=2)
    qr.add_data(spayd)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return base64.b64encode(buf.read()).decode("ascii")


def build_bank_transfer_email(
    order_number: str,
    plan: str,
    amount: int,
    email: str,
    variable_symbol: str,
    due_date: str,
) -> tuple[str, list[dict]]:
    """
    Build branded HTML email with bank transfer payment details + QR code.
    Sent when customer chooses "Bankovní převod" payment method.
    Returns (html, attachments) — attachments contain the QR code as CID inline image.
    """
    plan_name = PLAN_NAMES.get(plan, plan.upper())

    # Generuj platební QR kód (SPAYD standard)
    qr_base64 = generate_payment_qr_base64(amount, variable_symbol, order_number)
    qr_html = ""
    attachments: list[dict] = []
    if qr_base64:
        # Use CID (Content-ID) so email clients actually display the image
        # data: URIs are blocked by Gmail, Outlook, and most email clients
        attachments.append({
            "content": qr_base64,
            "filename": "qr-platba.png",
            "content_type": "image/png",
        })
        qr_html = f"""
    <!-- QR Payment Code -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:rgba(255,255,255,0.95);border-radius:12px;margin-bottom:24px;">
    <tr><td align="center" style="padding:24px;">
        <p style="margin:0 0 12px 0;font-size:13px;font-weight:700;color:#1e293b;">
            &#128241; Platební QR kód
        </p>
        <img src="data:image/png;base64,{qr_base64}" alt="Platební QR kód" width="200" height="200" style="display:block;margin:0 auto;border-radius:8px;" />
        <p style="margin:12px 0 0 0;font-size:11px;color:#64748b;line-height:1.5;">
            Naskenujte QR kód v mobilní aplikaci vaší banky.<br>
            Všechny údaje se předvyplní automaticky.
        </p>
    </td></tr>
    </table>
    """

    content = f"""
    <!-- Title -->
    <h1 style="margin:0 0 8px 0;font-size:24px;font-weight:800;color:#ffffff;">
        Potvrzení objednávky
    </h1>
    <p style="margin:0 0 24px 0;font-size:14px;color:#94a3b8;">
        Děkujeme za vaši objednávku. Níže naleznete platební údaje pro bankovní převod.
    </p>

    <!-- Order info card -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:12px;margin-bottom:24px;">
    <tr><td style="padding:20px 24px;">
        <p style="margin:0 0 4px 0;font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:1px;">Objednávka</p>
        <p style="margin:0 0 16px 0;font-size:16px;font-weight:700;color:#ffffff;font-family:monospace;">{order_number}</p>

        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr>
            <td style="padding:6px 0;font-size:13px;color:#94a3b8;width:40%;">Služba:</td>
            <td style="padding:6px 0;font-size:13px;color:#ffffff;font-weight:600;">{plan_name}</td>
        </tr>
        <tr>
            <td style="padding:6px 0;font-size:13px;color:#94a3b8;">Částka:</td>
            <td style="padding:6px 0;font-size:18px;color:#22c55e;font-weight:800;">{amount:,} Kč</td>
        </tr>
        <tr>
            <td style="padding:6px 0;font-size:13px;color:#94a3b8;">Splatnost:</td>
            <td style="padding:6px 0;font-size:13px;color:#fde68a;font-weight:600;">{due_date}</td>
        </tr>
        </table>
    </td></tr>
    </table>

    <!-- Payment details card -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:linear-gradient(135deg,rgba(6,182,212,0.08),rgba(124,58,237,0.08));border:1px solid rgba(6,182,212,0.2);border-radius:12px;margin-bottom:24px;">
    <tr><td style="padding:24px;">
        <p style="margin:0 0 16px 0;font-size:15px;font-weight:700;color:#ffffff;">
            💳 Platební údaje
        </p>

        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr>
            <td style="padding:8px 0;font-size:13px;color:#94a3b8;width:40%;vertical-align:top;">Číslo účtu:</td>
            <td style="padding:8px 0;font-size:15px;color:#22d3ee;font-weight:700;font-family:monospace;">2610538018/3030</td>
        </tr>
        <tr>
            <td style="padding:8px 0;font-size:13px;color:#94a3b8;vertical-align:top;">Variabilní symbol:</td>
            <td style="padding:8px 0;font-size:15px;color:#22d3ee;font-weight:700;font-family:monospace;">{variable_symbol}</td>
        </tr>
        <tr>
            <td style="padding:8px 0;font-size:13px;color:#94a3b8;vertical-align:top;">Částka:</td>
            <td style="padding:8px 0;font-size:15px;color:#22d3ee;font-weight:700;">{amount:,} Kč</td>
        </tr>
        </table>
    </td></tr>
    </table>

    {qr_html}

    <!-- Info -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:12px;margin-bottom:24px;">
    <tr><td style="padding:20px 24px;">
        <p style="margin:0 0 8px 0;font-size:13px;color:#94a3b8;line-height:1.6;">
            Po připsání platby na náš účet vám zašleme fakturu.
        </p>
        <p style="margin:0 0 8px 0;font-size:13px;color:#94a3b8;line-height:1.6;">
            Ihned se dáme do práce a hotové dílo odevzdáváme <strong style="color:#ffffff;">do 7 pracovních dní</strong>.
        </p>
        <p style="margin:0 0 16px 0;font-size:13px;color:#94a3b8;line-height:1.6;">
            Máte dotaz? Napište nám na <a href="mailto:info@aishield.cz" style="color:#a78bfa;text-decoration:none;">info@aishield.cz</a> nebo volejte na <a href="tel:+420732716141" style="color:#a78bfa;text-decoration:none;">732 716 141</a>
        </p>
        <p style="margin:0;font-size:13px;color:#94a3b8;line-height:1.6;">
            S pozdravem<br>
            <strong style="color:#ffffff;">Martin Haynes</strong>, CEO
        </p>
    </td></tr>
    </table>

    <!-- CTA -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:8px 0;">
        <a href="https://aishield.cz/dashboard" style="display:inline-block;padding:14px 32px;background:linear-gradient(135deg,#7c3aed,#d946ef);color:#ffffff;font-size:14px;font-weight:700;text-decoration:none;border-radius:12px;">
            Přejít na Dashboard
        </a>
    </td></tr>
    </table>
    """

    return _email_wrapper(content), attachments


def build_payment_received_email(
    order_number: str,
    plan: str,
    amount: int,
) -> str:
    """
    Build branded HTML email confirming payment was received.
    Sent when admin confirms bank transfer arrived.
    """
    plan_name = PLAN_NAMES.get(plan, plan.upper())

    content = f"""
    <!-- Title -->
    <h1 style="margin:0 0 8px 0;font-size:24px;font-weight:800;color:#ffffff;">
        Platba přijata ✅
    </h1>
    <p style="margin:0 0 24px 0;font-size:14px;color:#94a3b8;">
        Vaše platba za objednávku <strong style="color:#ffffff;">{order_number}</strong> dorazila na náš účet.
    </p>

    <!-- Order summary -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:rgba(34,197,94,0.06);border:1px solid rgba(34,197,94,0.2);border-radius:12px;margin-bottom:24px;">
    <tr><td style="padding:20px 24px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr>
            <td style="padding:6px 0;font-size:13px;color:#94a3b8;width:40%;">Služba:</td>
            <td style="padding:6px 0;font-size:13px;color:#ffffff;font-weight:600;">{plan_name}</td>
        </tr>
        <tr>
            <td style="padding:6px 0;font-size:13px;color:#94a3b8;">Uhrazeno:</td>
            <td style="padding:6px 0;font-size:16px;color:#22c55e;font-weight:800;">{amount:,} Kč</td>
        </tr>
        </table>
    </td></tr>
    </table>

    <!-- What happens next -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:12px;margin-bottom:24px;">
    <tr><td style="padding:24px;">
        <p style="margin:0 0 16px 0;font-size:15px;font-weight:700;color:#ffffff;">
            Co bude následovat?
        </p>
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr>
            <td style="padding:8px 0;font-size:13px;color:#94a3b8;line-height:1.6;">
                <span style="color:#d946ef;font-weight:700;">1.</span>
                Dáváme se ihned do práce na vaší dokumentaci.
            </td>
        </tr>
        <tr>
            <td style="padding:8px 0;font-size:13px;color:#94a3b8;line-height:1.6;">
                <span style="color:#d946ef;font-weight:700;">2.</span>
                Vyplňte prosím <a href="https://aishield.cz/dotaznik" style="color:#a78bfa;text-decoration:none;font-weight:600;">dotazník</a> — abychom vám připravili dokumenty na míru.
            </td>
        </tr>
        <tr>
            <td style="padding:8px 0;font-size:13px;color:#94a3b8;line-height:1.6;">
                <span style="color:#d946ef;font-weight:700;">3.</span>
                Hotové dílo odevzdáváme <strong style="color:#ffffff;">do 7 pracovních dní</strong>.
            </td>
        </tr>
        </table>
    </td></tr>
    </table>

    <!-- CTA -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:8px 0 0 0;">
        <a href="https://aishield.cz/dotaznik" style="display:inline-block;padding:14px 32px;background:linear-gradient(135deg,#7c3aed,#d946ef);color:#ffffff;font-size:14px;font-weight:700;text-decoration:none;border-radius:12px;margin-right:8px;">
            Vyplnit dotazník
        </a>
    </td></tr>
    <tr><td align="center" style="padding:12px 0 0 0;">
        <a href="https://aishield.cz/dashboard" style="display:inline-block;padding:12px 28px;border:1px solid rgba(255,255,255,0.15);color:#ffffff;font-size:13px;font-weight:600;text-decoration:none;border-radius:12px;">
            Přejít na Dashboard
        </a>
    </td></tr>
    </table>
    """

    return _email_wrapper(content)


def build_payment_confirmation_email(
    order_number: str,
    plan: str,
    amount: int,
    gateway: str,
) -> str:
    """
    Build branded HTML email confirming online payment (Stripe/GoPay/Comgate).
    Sent automatically after successful online payment.
    """
    plan_name = PLAN_NAMES.get(plan, plan.upper())
    gateway_name = {"stripe": "Stripe", "gopay": "GoPay", "comgate": "Comgate"}.get(gateway, gateway)

    content = f"""
    <!-- Title -->
    <h1 style="margin:0 0 8px 0;font-size:24px;font-weight:800;color:#ffffff;">
        Platba úspěšná ✅
    </h1>
    <p style="margin:0 0 24px 0;font-size:14px;color:#94a3b8;">
        Děkujeme! Vaše platba přes {gateway_name} proběhla úspěšně.
    </p>

    <!-- Order summary -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:rgba(34,197,94,0.06);border:1px solid rgba(34,197,94,0.2);border-radius:12px;margin-bottom:24px;">
    <tr><td style="padding:20px 24px;">
        <p style="margin:0 0 4px 0;font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:1px;">Objednávka</p>
        <p style="margin:0 0 16px 0;font-size:16px;font-weight:700;color:#ffffff;font-family:monospace;">{order_number}</p>
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr>
            <td style="padding:6px 0;font-size:13px;color:#94a3b8;width:40%;">Služba:</td>
            <td style="padding:6px 0;font-size:13px;color:#ffffff;font-weight:600;">{plan_name}</td>
        </tr>
        <tr>
            <td style="padding:6px 0;font-size:13px;color:#94a3b8;">Uhrazeno:</td>
            <td style="padding:6px 0;font-size:16px;color:#22c55e;font-weight:800;">{amount:,} Kč</td>
        </tr>
        <tr>
            <td style="padding:6px 0;font-size:13px;color:#94a3b8;">Brána:</td>
            <td style="padding:6px 0;font-size:13px;color:#ffffff;">{gateway_name}</td>
        </tr>
        </table>
    </td></tr>
    </table>

    <!-- Next steps -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:12px;margin-bottom:24px;">
    <tr><td style="padding:24px;">
        <p style="margin:0 0 12px 0;font-size:13px;color:#94a3b8;line-height:1.6;">
            Faktura vám přijde na email. Nyní prosím vyplňte dotazník, abychom vám připravili dokumenty přesně na míru.
        </p>
        <p style="margin:0;font-size:13px;color:#94a3b8;line-height:1.6;">
            Hotové dílo odevzdáváme <strong style="color:#ffffff;">do 7 pracovních dní</strong>.
        </p>
    </td></tr>
    </table>

    <!-- CTA -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center" style="padding:8px 0 0 0;">
        <a href="https://aishield.cz/dotaznik" style="display:inline-block;padding:14px 32px;background:linear-gradient(135deg,#7c3aed,#d946ef);color:#ffffff;font-size:14px;font-weight:700;text-decoration:none;border-radius:12px;">
            Vyplnit dotazník
        </a>
    </td></tr>
    <tr><td align="center" style="padding:12px 0 0 0;">
        <a href="https://aishield.cz/dashboard" style="display:inline-block;padding:12px 28px;border:1px solid rgba(255,255,255,0.15);color:#ffffff;font-size:13px;font-weight:600;text-decoration:none;border-radius:12px;">
            Přejít na Dashboard
        </a>
    </td></tr>
    </table>
    """

    return _email_wrapper(content)
