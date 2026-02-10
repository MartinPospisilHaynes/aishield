"""
AIshield.cz — Supabase Auth Configuration Updater
Updates Site URL, redirect URLs, and email templates via Supabase Management API.

Usage:
    1. Go to https://supabase.com/dashboard/account/tokens
    2. Generate a new access token
    3. Run:  SUPABASE_ACCESS_TOKEN=sbp_xxx python3 scripts/update_supabase_auth.py
"""

import os
import sys
import json
import urllib.request
import urllib.error

PROJECT_REF = "rsxwqcrkttlfnqbjgpgc"
MANAGEMENT_API = f"https://api.supabase.com/v1/projects/{PROJECT_REF}/config/auth"
SITE_URL = "https://aishield.cz"

# ── Branded email templates ──

# Dark theme colors (must match the rest of the brand)
BG_BODY = "#0a0a1a"
BG_CARD = "#0f172a"
BG_SECTION = "#131b2e"
BG_ELEVATED = "#1a2340"
BORDER = "#1e293b"
TEXT = "#f1f5f9"
TEXT_SECONDARY = "#94a3b8"
TEXT_MUTED = "#64748b"
ACCENT_FUCHSIA = "#d946ef"
ACCENT_CYAN = "#06b6d4"
GRADIENT_START = "#0f172a"
GRADIENT_MID = "#1e1b4b"
GRADIENT_END = "#312e81"

SHIELD_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 40 40" '
    'style="vertical-align:middle;margin-right:10px;">'
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


def _email_wrapper(title: str, body_content: str) -> str:
    """Wrap body content in a branded dark-theme HTML email layout."""
    return f"""<!DOCTYPE html>
<html lang="cs">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title></head>
<body style="margin:0;padding:0;background:{BG_BODY};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:{BG_BODY};padding:24px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:{BG_CARD};border-radius:16px;overflow:hidden;border:1px solid {BORDER};">

<!-- HEADER -->
<tr><td style="background:linear-gradient(135deg,{GRADIENT_START},{GRADIENT_MID},{GRADIENT_END});padding:28px 24px;text-align:center;border-bottom:1px solid {BORDER};">
    <div style="font-size:26px;font-weight:800;letter-spacing:-0.5px;">
        {SHIELD_SVG}<span style="color:#ffffff;">AI</span><span style="background:linear-gradient(135deg,{ACCENT_FUCHSIA},{ACCENT_CYAN});-webkit-background-clip:text;-webkit-text-fill-color:transparent;">shield</span><span style="color:{TEXT_MUTED};font-size:15px;font-weight:400;">.cz</span>
    </div>
</td></tr>

<!-- BODY -->
<tr><td style="padding:32px 28px;">
{body_content}
</td></tr>

<!-- FOOTER -->
<tr><td style="background:{BG_SECTION};padding:20px 24px;text-align:center;border-top:1px solid {BORDER};">
    <p style="margin:0;font-size:12px;color:{TEXT_MUTED};line-height:1.5;">
        &copy; 2025 AIshield.cz &mdash; Compliance software pro AI Act<br>
        <a href="https://aishield.cz" style="color:{ACCENT_CYAN};text-decoration:none;">aishield.cz</a>
    </p>
</td></tr>

</table>
</td></tr>
</table>
</body></html>"""


# ── Confirmation email (verify signup) ──
CONFIRM_EMAIL_SUBJECT = "Potvrďte svůj email — AIshield.cz"
CONFIRM_EMAIL_TEMPLATE = _email_wrapper("Potvrďte email", f"""
    <div style="text-align:center;">
        <div style="margin:0 auto 20px;width:56px;height:56px;border-radius:14px;background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.2);display:flex;align-items:center;justify-content:center;">
            <svg width="28" height="28" fill="none" stroke="#22c55e" viewBox="0 0 24 24" style="display:block;margin:auto;padding-top:14px;">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
            </svg>
        </div>
        <h1 style="font-size:22px;font-weight:700;color:{TEXT};margin:0 0 10px;">Potvrďte svůj email</h1>
        <p style="font-size:14px;color:{TEXT_SECONDARY};line-height:1.6;margin:0 0 24px;">
            Děkujeme za registraci na AIshield.cz!<br>
            Klikněte na tlačítko níže pro potvrzení vaší e-mailové adresy<br>
            a aktivaci vašeho účtu.
        </p>
        <a href="{{{{ .ConfirmationURL }}}}"
           style="display:inline-block;padding:14px 40px;background:linear-gradient(135deg,{ACCENT_FUCHSIA},{ACCENT_CYAN});
                  color:#ffffff;font-size:15px;font-weight:700;text-decoration:none;border-radius:12px;
                  letter-spacing:0.3px;">
            Potvrdit email
        </a>
        <p style="font-size:12px;color:{TEXT_MUTED};margin:20px 0 0;line-height:1.5;">
            Pokud jste se na AIshield.cz neregistrovali, tento email můžete ignorovat.
        </p>
    </div>
""")


# ── Magic link / OTP email ──
MAGIC_LINK_SUBJECT = "Váš přihlašovací odkaz — AIshield.cz"
MAGIC_LINK_TEMPLATE = _email_wrapper("Přihlášení", f"""
    <div style="text-align:center;">
        <h1 style="font-size:22px;font-weight:700;color:{TEXT};margin:0 0 10px;">Přihlášení do AIshield.cz</h1>
        <p style="font-size:14px;color:{TEXT_SECONDARY};line-height:1.6;margin:0 0 24px;">
            Klikněte na tlačítko níže pro přihlášení do vašeho účtu.
        </p>
        <a href="{{{{ .ConfirmationURL }}}}"
           style="display:inline-block;padding:14px 40px;background:linear-gradient(135deg,{ACCENT_FUCHSIA},{ACCENT_CYAN});
                  color:#ffffff;font-size:15px;font-weight:700;text-decoration:none;border-radius:12px;">
            Přihlásit se
        </a>
        <p style="font-size:12px;color:{TEXT_MUTED};margin:20px 0 0;">
            Pokud jste o přihlášení nežádali, tento email můžete ignorovat.
        </p>
    </div>
""")


# ── Password recovery email ──
RECOVERY_SUBJECT = "Obnovení hesla — AIshield.cz"
RECOVERY_TEMPLATE = _email_wrapper("Obnovení hesla", f"""
    <div style="text-align:center;">
        <div style="margin:0 auto 20px;width:56px;height:56px;border-radius:14px;background:rgba(234,179,8,0.1);border:1px solid rgba(234,179,8,0.2);display:flex;align-items:center;justify-content:center;">
            <svg width="28" height="28" fill="none" stroke="#eab308" viewBox="0 0 24 24" style="display:block;margin:auto;padding-top:14px;">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke-width="2"/>
                <path stroke-width="2" d="M7 11V7a5 5 0 0110 0v4"/>
            </svg>
        </div>
        <h1 style="font-size:22px;font-weight:700;color:{TEXT};margin:0 0 10px;">Obnovení hesla</h1>
        <p style="font-size:14px;color:{TEXT_SECONDARY};line-height:1.6;margin:0 0 24px;">
            Obdrželi jsme žádost o změnu hesla k vašemu účtu.<br>
            Klikněte na tlačítko níže pro nastavení nového hesla.
        </p>
        <a href="{{{{ .ConfirmationURL }}}}"
           style="display:inline-block;padding:14px 40px;background:linear-gradient(135deg,{ACCENT_FUCHSIA},{ACCENT_CYAN});
                  color:#ffffff;font-size:15px;font-weight:700;text-decoration:none;border-radius:12px;">
            Nastavit nové heslo
        </a>
        <p style="font-size:12px;color:{TEXT_MUTED};margin:20px 0 0;">
            Pokud jste o změnu hesla nežádali, tento email můžete ignorovat.
        </p>
    </div>
""")


# ── Email change confirmation ──
EMAIL_CHANGE_SUBJECT = "Potvrzení změny emailu — AIshield.cz"
EMAIL_CHANGE_TEMPLATE = _email_wrapper("Změna emailu", f"""
    <div style="text-align:center;">
        <h1 style="font-size:22px;font-weight:700;color:{TEXT};margin:0 0 10px;">Potvrzení nového emailu</h1>
        <p style="font-size:14px;color:{TEXT_SECONDARY};line-height:1.6;margin:0 0 24px;">
            Klikněte na tlačítko níže pro potvrzení změny e-mailové adresy.
        </p>
        <a href="{{{{ .ConfirmationURL }}}}"
           style="display:inline-block;padding:14px 40px;background:linear-gradient(135deg,{ACCENT_FUCHSIA},{ACCENT_CYAN});
                  color:#ffffff;font-size:15px;font-weight:700;text-decoration:none;border-radius:12px;">
            Potvrdit nový email
        </a>
    </div>
""")


def update_supabase_auth():
    """Update Supabase auth config via Management API."""
    token = os.environ.get("SUPABASE_ACCESS_TOKEN")
    if not token:
        print("❌ Chybí SUPABASE_ACCESS_TOKEN!")
        print("   1. Jděte na https://supabase.com/dashboard/account/tokens")
        print("   2. Vytvořte nový access token")
        print("   3. Spusťte: SUPABASE_ACCESS_TOKEN=sbp_xxx python3 scripts/update_supabase_auth.py")
        sys.exit(1)

    payload = {
        "SITE_URL": SITE_URL,
        "URI_ALLOW_LIST": "https://aishield.cz/**,https://www.aishield.cz/**,http://localhost:3000/**",
        "MAILER_SUBJECTS_CONFIRMATION": CONFIRM_EMAIL_SUBJECT,
        "MAILER_TEMPLATES_CONFIRMATION_CONTENT": CONFIRM_EMAIL_TEMPLATE,
        "MAILER_SUBJECTS_RECOVERY": RECOVERY_SUBJECT,
        "MAILER_TEMPLATES_RECOVERY_CONTENT": RECOVERY_TEMPLATE,
        "MAILER_SUBJECTS_MAGIC_LINK": MAGIC_LINK_SUBJECT,
        "MAILER_TEMPLATES_MAGIC_LINK_CONTENT": MAGIC_LINK_TEMPLATE,
        "MAILER_SUBJECTS_EMAIL_CHANGE": EMAIL_CHANGE_SUBJECT,
        "MAILER_TEMPLATES_EMAIL_CHANGE_CONTENT": EMAIL_CHANGE_TEMPLATE,
    }

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        MANAGEMENT_API,
        data=data,
        method="PATCH",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            print("✅ Supabase auth config updated successfully!")
            print(f"   Site URL: {SITE_URL}")
            print(f"   Redirect URLs: https://aishield.cz/**, http://localhost:3000/**")
            print(f"   Email templates: Confirmation, Recovery, Magic Link, Email Change")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"❌ API error {e.code}: {body}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    update_supabase_auth()
