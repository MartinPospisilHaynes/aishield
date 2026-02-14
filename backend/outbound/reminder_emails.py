"""
AIshield.cz — Reminder Emails
Automatické připomínkové emaily pro uživatele s neověřenými „Nevím" odpověďmi.

Odesílají se:
  - Po 14 dnech od vyplnění dotazníku
  - Po 30 dnech od vyplnění dotazníku

Email je informativní — nenutí, netiskne. Připomíná:
  - Že si uživatel provedl registraci na aishield.cz
  - Že na webu byly nalezeny AI systémy
  - Že potřebujeme zbývající údaje pro plný servis
  - Že může své odpovědi v dotazníku změnit
"""

import logging
from datetime import datetime, timezone, timedelta

from backend.database import get_supabase
from backend.outbound.email_engine import send_email

logger = logging.getLogger(__name__)


def _build_reminder_html(
    company_name: str,
    company_url: str,
    unknown_count: int,
    findings_count: int,
    dashboard_url: str,
    dotaznik_url: str,
    reminder_type: str,  # "14_days" or "30_days"
) -> str:
    """Sestaví HTML pro připomínkový email."""

    if reminder_type == "14_days":
        greeting = "Rádi bychom Vám připomněli"
        urgency = ""
    else:
        greeting = "Dovolujeme si Vám znovu připomenout"
        urgency = " Nařízení EU AI Act je již v platnosti a týká se i českých firem."

    return f"""
<!DOCTYPE html>
<html lang="cs">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:Arial,Helvetica,sans-serif;">
<div style="max-width:600px;margin:0 auto;padding:20px;">

<!-- Header -->
<div style="background:linear-gradient(135deg,#0f172a,#1e1b4b,#312e81);border-radius:12px 12px 0 0;padding:30px 24px;text-align:center;">
    <h1 style="color:white;margin:0;font-size:22px;font-weight:700;">AIshield.cz</h1>
    <p style="color:#a78bfa;margin:8px 0 0;font-size:13px;">Připomínka k Vašemu dotazníku</p>
</div>

<!-- Body -->
<div style="background:white;padding:28px 24px;border:1px solid #e2e8f0;border-top:none;">

    <p style="color:#1e293b;font-size:15px;line-height:1.6;margin:0 0 16px;">
        Dobrý den,
    </p>

    <p style="color:#1e293b;font-size:15px;line-height:1.6;margin:0 0 16px;">
        {greeting}, že jste se na <strong>aishield.cz</strong> zaregistrovali
        a nechali si zanalyzovat web <strong>{company_url}</strong>.{urgency}
    </p>

    <!-- Findings box -->
    <div style="background:#fef3c7;border:1px solid #fcd34d;border-radius:8px;padding:16px 20px;margin:20px 0;">
        <p style="color:#92400e;font-size:14px;margin:0;line-height:1.5;">
            Na Vašem webu jsme identifikovali <strong>{findings_count} oblastí souvisejících s AI</strong>,
            které se Vás přímo týkají z pohledu evropského nařízení AI Act.
        </p>
    </div>

    <p style="color:#1e293b;font-size:15px;line-height:1.6;margin:0 0 16px;">
        V dotazníku jste u <strong>{unknown_count} otázek</strong> zvolili odpověď
        &bdquo;Nevím&ldquo;. Bez těchto informací Vám bohužel nemůžeme připravit
        kompletní compliance dokumentaci.
    </p>

    <p style="color:#1e293b;font-size:15px;line-height:1.6;margin:0 0 20px;">
        Své odpovědi můžete <strong>kdykoli upravit</strong> — třeba až
        zjistíte potřebné informace od kolegů. Stačí se přihlásit a doplnit dotazník.
    </p>

    <!-- CTA buttons -->
    <div style="text-align:center;margin:24px 0;">
        <a href="{dotaznik_url}" style="display:inline-block;background:#7c3aed;color:white;text-decoration:none;padding:12px 28px;border-radius:8px;font-size:14px;font-weight:600;">
            Upravit odpovědi v dotazníku
        </a>
    </div>

    <div style="text-align:center;margin:12px 0 24px;">
        <a href="{dashboard_url}" style="color:#7c3aed;text-decoration:none;font-size:13px;">
            Přejít na dashboard →
        </a>
    </div>

    <!-- Responsibility note -->
    <div style="background:#f1f5f9;border-radius:8px;padding:14px 18px;margin:16px 0 0;">
        <p style="color:#64748b;font-size:12px;line-height:1.5;margin:0;">
            Compliance dokumentaci vyhotovujeme na základě
            Vašich odpovědí v dotazníku a výsledků analýzy webu. Za správnost
            uvedených údajů odpovídá zákazník.
        </p>
    </div>

</div>

<!-- Footer -->
<div style="background:#0f172a;border-radius:0 0 12px 12px;padding:20px 24px;text-align:center;">
    <p style="color:#94a3b8;font-size:12px;margin:0;line-height:1.5;">
        AIshield.cz — AI compliance pro české firmy<br>
        Provozovatel: Desperados Design s.r.o.
    </p>
    <p style="color:#64748b;font-size:11px;margin:8px 0 0;">
        Tento email jste obdrželi, protože jste se zaregistrovali na aishield.cz.
    </p>
</div>

</div>
</body>
</html>
"""


async def send_reminder_emails(reminder_type: str = "14_days") -> dict:
    """
    Najde uživatele, kteří mají neověřené „Nevím" odpovědi a poslední
    dotazník vyplnili před 14 / 30 dny. Pošle jim připomínkový email.

    Volá se z cron jobu nebo admin endpointu.

    Args:
        reminder_type: "14_days" nebo "30_days"

    Returns:
        dict s počtem odeslaných emailů
    """
    supabase = get_supabase()

    if reminder_type == "14_days":
        days_ago = 14
        subject = "Připomínka: V dotazníku nám chybí některé Vaše odpovědi"
    else:
        days_ago = 30
        subject = "Připomínáme se - chybí nám od Vás důležité údaje"

    # Časové okno: hledáme odpovědi staré days_ago ± 1 den
    target_date = datetime.now(timezone.utc) - timedelta(days=days_ago)
    window_start = target_date - timedelta(hours=12)
    window_end = target_date + timedelta(hours=12)

    sent_count = 0
    skipped_count = 0
    errors = []

    try:
        # Najdi klienty s dotazníkovými odpověďmi ve správném časovém okně
        # a s alespoň jednou "unknown" odpovědí
        clients_res = supabase.table("questionnaire_responses") \
            .select("client_id, submitted_at") \
            .eq("answer", "unknown") \
            .gte("submitted_at", window_start.isoformat()) \
            .lte("submitted_at", window_end.isoformat()) \
            .execute()

        if not clients_res.data:
            logger.info(f"[Reminder] Žádní kandidáti pro {reminder_type} reminder")
            return {"sent": 0, "skipped": 0, "errors": []}

        # Unikátní client_ids
        client_ids = list(set(row["client_id"] for row in clients_res.data))
        logger.info(f"[Reminder] Nalezeno {len(client_ids)} klientů pro {reminder_type} reminder")

        for client_id in client_ids:
            try:
                # Najdi klienta a jeho firmu
                client_res = supabase.table("clients") \
                    .select("id, company_id, email") \
                    .eq("id", client_id) \
                    .single() \
                    .execute()

                if not client_res.data:
                    continue

                client = client_res.data
                company_id = client["company_id"]

                # Najdi firmu
                company_res = supabase.table("companies") \
                    .select("id, name, url, email") \
                    .eq("id", company_id) \
                    .single() \
                    .execute()

                if not company_res.data:
                    continue

                company = company_res.data
                email = company.get("email") or client.get("email", "")

                # Přeskoč anonymní / neplatné emaily
                if not email or "anonymous" in email or "@aishield.cz" in email:
                    skipped_count += 1
                    continue

                # Zkontroluj, zda jsme tento reminder už neposlali
                # (pomocí tagu v logs — jednoduchá ochrana proti duplicitám)
                reminder_tag = f"reminder_{reminder_type}_{company_id}"
                existing = supabase.table("email_logs") \
                    .select("id") \
                    .eq("tag", reminder_tag) \
                    .limit(1) \
                    .execute()

                if existing.data:
                    skipped_count += 1
                    continue

                # Spočítej unknown odpovědi a findings
                unknown_res = supabase.table("questionnaire_responses") \
                    .select("id") \
                    .eq("client_id", client_id) \
                    .eq("answer", "unknown") \
                    .execute()
                unknown_count = len(unknown_res.data) if unknown_res.data else 0

                # Findings ze skenu
                scans_res = supabase.table("scans") \
                    .select("id") \
                    .eq("company_id", company_id) \
                    .order("created_at", desc=True) \
                    .limit(1) \
                    .execute()

                findings_count = 0
                if scans_res.data:
                    findings_res = supabase.table("findings") \
                        .select("id") \
                        .eq("scan_id", scans_res.data[0]["id"]) \
                        .neq("source", "ai_classified_fp") \
                        .execute()
                    findings_count = len(findings_res.data) if findings_res.data else 0

                if unknown_count == 0:
                    skipped_count += 1
                    continue

                # Sestav URL
                company_url = company.get("url", company.get("name", "váš web"))
                dashboard_url = f"https://aishield.cz/dashboard"
                dotaznik_url = f"https://aishield.cz/dotaznik?company_id={company_id}&edit=true"

                # Sestav a odešli email
                html = _build_reminder_html(
                    company_name=company.get("name", ""),
                    company_url=company_url,
                    unknown_count=unknown_count,
                    findings_count=findings_count,
                    dashboard_url=dashboard_url,
                    dotaznik_url=dotaznik_url,
                    reminder_type=reminder_type,
                )

                result = await send_email(
                    to=email,
                    subject=subject,
                    html=html,
                )

                # Zaloguj odeslání (ochrana proti duplicitám)
                try:
                    supabase.table("email_logs").insert({
                        "company_id": company_id,
                        "email": email,
                        "subject": subject,
                        "tag": reminder_tag,
                        "resend_id": result.get("id", ""),
                        "status": "sent",
                    }).execute()
                except Exception:
                    pass  # Tabulka nemusí existovat — to nás nezastaví

                sent_count += 1
                logger.info(f"[Reminder] Odeslán {reminder_type} reminder na {email} (company {company_id})")

            except Exception as e:
                errors.append(f"Client {client_id}: {str(e)}")
                logger.error(f"[Reminder] Chyba u klienta {client_id}: {e}")

    except Exception as e:
        errors.append(f"Hlavní chyba: {str(e)}")
        logger.error(f"[Reminder] Hlavní chyba: {e}")

    result = {"sent": sent_count, "skipped": skipped_count, "errors": errors}
    logger.info(f"[Reminder] {reminder_type} hotovo: {result}")
    return result
