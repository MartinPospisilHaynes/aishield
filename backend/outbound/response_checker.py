"""
AIshield.cz — Response Checker (LOVEC CRM)
===========================================
Monitoruje příchozí odpovědi na outbound emaily a klasifikuje je.

Dva režimy:
  1. RESEND WEBHOOK — zachytí bounced/opened/clicked eventy (automaticky)
  2. IMAP POLLING   — čte skutečné odpovědi z mailboxu (cron každých 5 min)

Po přijetí odpovědi:
  - AI klasifikuje sentiment (interested / not_interested / angry / blocked)
  - Aktualizuje outreach_status v companies tabulce
  - Zapíše response_summary (shrnutí odpovědi)
"""

import asyncio
import imaplib
import email
import logging
import os
import re
from datetime import datetime, timezone, timedelta
from email.header import decode_header

logger = logging.getLogger(__name__)

# ── Konfigurece ──

# IMAP credentials (Wedos mail)
IMAP_HOST = os.getenv("IMAP_HOST", "wes1-imap.wedos.net")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
IMAP_USER = os.getenv("IMAP_USER", "")       # info@aishield.cz
IMAP_PASS = os.getenv("IMAP_PASS", "")       # heslo k mailboxu

# Kolik dní zpátky kontrolovat
CHECK_DAYS = 7

# Výzvy pro AI klasifikaci
CLASSIFY_SYSTEM = """Jsi expert na analýzu obchodních emailů. Tvým úkolem je klasifikovat odpověď na obchodní nabídku AI Act compliance služby.

Odpověz PŘESNĚ jedním z těchto statusů:
- interested — projevuje zájem, ptá se na detaily, chce vědět víc
- meeting_scheduled — souhlasí se schůzkou/telefonátem
- not_interested — zdvořile odmítá, nemá zájem, ale není agresivní
- angry — naštvaný, vyhrožuje, je agresivní
- blocked — žádá o vyřazení z mailinglistu, odhlášení, GDPR
- autoresponse — automatická odpověď (OOO, dovolená, nedoručitelné)
- unclear — nelze jednoznačně určit

Formát odpovědi (JSON):
{"status": "interested", "summary": "Krátké shrnutí v češtině (max 100 znaků)"}
"""


async def classify_response(email_body: str, subject: str = "") -> dict:
    """
    AI klasifikace odpovědi klienta.
    Vrátí: {"status": "interested", "summary": "Projevil zájem..."}
    """
    from backend.llm_engine import call_llm

    prompt = f"""Klasifikuj tuto odpověď na obchodní email.

Předmět: {subject}
Text odpovědi:
---
{email_body[:2000]}
---

Odpověz JSON: {{"status": "...", "summary": "..."}}"""

    try:
        result = await call_llm(
            prompt=prompt,
            system=CLASSIFY_SYSTEM,
            model="gemini-2.0-flash",  # Levný a rychlý model
            temperature=0.1,
            max_tokens=200,
        )

        # Parsovat JSON z odpovědi
        import json
        text = result.get("text", "") if isinstance(result, dict) else str(result)
        # Najdi JSON v textu
        json_match = re.search(r'\{[^}]+\}', text)
        if json_match:
            parsed = json.loads(json_match.group())
            return {
                "status": parsed.get("status", "unclear"),
                "summary": parsed.get("summary", ""),
            }
        return {"status": "unclear", "summary": "AI nedokázala klasifikovat"}
    except Exception as e:
        logger.error(f"[ResponseChecker] AI klasifikace selhala: {e}")
        return {"status": "unclear", "summary": f"Chyba klasifikace: {e}"}


def _decode_email_body(msg) -> str:
    """Extrahuje textový obsah z email message."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    try:
                        body = payload.decode(charset, errors="replace")
                    except Exception:
                        body = payload.decode("utf-8", errors="replace")
                    break
            elif content_type == "text/html" and not body:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    try:
                        body = payload.decode(charset, errors="replace")
                    except Exception:
                        body = payload.decode("utf-8", errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            try:
                body = payload.decode(charset, errors="replace")
            except Exception:
                body = payload.decode("utf-8", errors="replace")

    # Odstraň HTML tagy (jednoduchý strip)
    body = re.sub(r'<[^>]+>', ' ', body)
    body = re.sub(r'\s+', ' ', body).strip()
    return body[:3000]  # Max 3000 znaků


def _decode_header_value(value: str) -> str:
    """Dekóduje email header (UTF-8, base64, atd.)."""
    if not value:
        return ""
    decoded_parts = decode_header(value)
    result = ""
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result += part.decode(charset or "utf-8", errors="replace")
        else:
            result += part
    return result


async def check_imap_responses() -> dict:
    """
    Zkontroluje příchozí emaily přes IMAP a klasifikuje odpovědi.

    Pro každý email:
    1. Zjistí od koho přišel (from_email)
    2. Najde odpovídající firmu v DB (companies.email = from_email)
    3. AI klasifikuje odpověď
    4. Aktualizuje outreach_status + response_summary v DB

    Vrátí: {"checked": 15, "classified": 3, "details": [...]}
    """
    if not IMAP_USER or not IMAP_PASS:
        return {
            "status": "skipped",
            "reason": "IMAP credentials nejsou nastavené (IMAP_USER, IMAP_PASS v .env)",
        }

    from backend.database import get_supabase

    stats = {"checked": 0, "classified": 0, "errors": 0, "details": []}

    try:
        # Připojení k IMAP
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(IMAP_USER, IMAP_PASS)
        mail.select("INBOX")

        # Hledej emaily z posledních X dní
        since_date = (datetime.now() - timedelta(days=CHECK_DAYS)).strftime("%d-%b-%Y")
        _, msg_ids = mail.search(None, f'(SINCE "{since_date}")')

        if not msg_ids[0]:
            mail.logout()
            return {"checked": 0, "classified": 0, "details": []}

        supabase = get_supabase()
        ids = msg_ids[0].split()
        stats["checked"] = len(ids)

        logger.info(f"[ResponseChecker] Nalezeno {len(ids)} emailů za posledních {CHECK_DAYS} dní")

        for msg_id in ids:
            try:
                _, data = mail.fetch(msg_id, "(RFC822)")
                raw_email = data[0][1]
                msg = email.message_from_bytes(raw_email)

                from_raw = msg.get("From", "")
                from_decoded = _decode_header_value(from_raw)
                # Extrahuj email adresu
                from_match = re.search(r'[\w.+-]+@[\w.-]+\.\w+', from_decoded)
                if not from_match:
                    continue
                from_email = from_match.group().lower()

                # Přeskoč naše vlastní emaily
                if "aishield.cz" in from_email:
                    continue

                subject = _decode_header_value(msg.get("Subject", ""))
                body = _decode_email_body(msg)

                if not body or len(body) < 5:
                    continue

                # Hledej firmu v DB podle emailu odesílatele
                company_res = supabase.table("companies").select(
                    "id, name, email, outreach_status, outbound_email_count"
                ).eq("email", from_email).limit(1).execute()

                if not company_res.data:
                    # Zkusíme hledat podle domény
                    domain = from_email.split("@")[1]
                    company_res = supabase.table("companies").select(
                        "id, name, email, outreach_status, outbound_email_count"
                    ).ilike("email", f"%@{domain}").limit(1).execute()

                if not company_res.data:
                    continue  # Neznámý odesílatel

                company = company_res.data[0]

                # Přeskoč firmy, kterým jsme ještě neposlali email
                if company.get("outbound_email_count", 0) == 0 and company.get("outreach_status") == "not_contacted":
                    continue

                # AI klasifikace
                classification = await classify_response(body, subject)
                new_status = classification["status"]
                summary = classification["summary"]

                # Mapování AI výstupu na outreach_status
                status_map = {
                    "interested": "interested",
                    "meeting_scheduled": "meeting_scheduled",
                    "not_interested": "not_interested",
                    "angry": "angry",
                    "blocked": "blocked",
                    "autoresponse": None,  # Nechej stávající status
                    "unclear": "responded",
                }
                db_status = status_map.get(new_status)

                if db_status:
                    update_data = {
                        "outreach_status": db_status,
                        "response_summary": summary,
                        "last_response_at": datetime.now(timezone.utc).isoformat(),
                        "response_count": company.get("response_count", 0) + 1,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }

                    # Pokud negativní → uložit důvod
                    if db_status in ("angry", "blocked", "not_interested"):
                        update_data["rejection_reason"] = summary

                    supabase.table("companies").update(update_data).eq(
                        "id", company["id"]
                    ).execute()

                    stats["classified"] += 1
                    stats["details"].append({
                        "company": company.get("name", "?"),
                        "from": from_email,
                        "status": db_status,
                        "summary": summary,
                    })

                    logger.info(
                        f"[ResponseChecker] {company.get('name')}: "
                        f"{from_email} → {db_status} ({summary})"
                    )

            except Exception as e:
                logger.error(f"[ResponseChecker] Chyba při zpracování emailu: {e}")
                stats["errors"] += 1

        mail.logout()

    except imaplib.IMAP4.error as e:
        logger.error(f"[ResponseChecker] IMAP chyba: {e}")
        return {"status": "error", "reason": f"IMAP: {e}"}
    except Exception as e:
        logger.error(f"[ResponseChecker] Neočekávaná chyba: {e}")
        return {"status": "error", "reason": str(e)}

    logger.info(
        f"[ResponseChecker] Hotovo: {stats['checked']} zkontrolováno, "
        f"{stats['classified']} klasifikováno, {stats['errors']} chyb"
    )
    return stats


async def update_outreach_from_resend_events():
    """
    Aktualizuje outreach_status na základě Resend webhookových eventů.
    Volané jako cron job — zpracuje nenavázané eventy z email_events tabulky.

    Logika:
    - email.bounced    → outreach_status = 'bounced'
    - email.delivered  → outreach_status zůstane 'email_sent' (jen potvrzení)
    - email.opened     → outreach_status zůstane (info v email_log.opened_at)
    - email.clicked    → outreach_status zůstane (info v email_log.clicked_at)
    - email.complained → outreach_status = 'blocked' (spam report)
    """
    from backend.database import get_supabase

    supabase = get_supabase()
    stats = {"processed": 0, "bounced": 0, "blocked": 0}

    try:
        # Nenavázané bounce eventy z posledního dne
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        events = supabase.table("email_events").select(
            "id, to_email, event_type, bounce_type, created_at"
        ).gte("created_at", yesterday).execute()

        for event in (events.data or []):
            to_email = event.get("to_email", "").lower()
            event_type = event.get("event_type", "")

            if not to_email:
                continue

            # Najdi firmu
            company_res = supabase.table("companies").select(
                "id, outreach_status"
            ).eq("email", to_email).limit(1).execute()

            if not company_res.data:
                continue

            company = company_res.data[0]
            current_status = company.get("outreach_status", "not_contacted")

            new_status = None
            if event_type == "email.bounced":
                new_status = "bounced"
                stats["bounced"] += 1
            elif event_type == "email.complained":
                new_status = "blocked"
                stats["blocked"] += 1

            if new_status and current_status != new_status:
                supabase.table("companies").update({
                    "outreach_status": new_status,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }).eq("id", company["id"]).execute()

            stats["processed"] += 1

    except Exception as e:
        logger.error(f"[ResponseChecker] Resend events chyba: {e}")

    return stats


async def run_response_check():
    """
    Kompletní response check cyklus:
    1. Zpracuj Resend webhook eventy (bounced → outreach_status)
    2. Zkontroluj IMAP inbox (odpovědi → AI klasifikace)
    """
    logger.info("[ResponseChecker] Spouštím kontrolu odpovědí...")

    results = {}

    # Krok 1: Resend eventy
    results["resend_events"] = await update_outreach_from_resend_events()

    # Krok 2: IMAP (pokud jsou credentials)
    results["imap"] = await check_imap_responses()

    logger.info(f"[ResponseChecker] Hotovo: {results}")
    return results


# ── CLI ──

if __name__ == "__main__":
    asyncio.run(run_response_check())
