"""
AIshield.cz — AI Email Writer
Gemini Flash píše personalizované emaily na míru každé firmě.

Pracuje s:
- Jméno kontaktní osoby (z ARES / z webu)
- Konkrétní nálezy AI systémů ze scanu
- URL a screenshot webu
- Kontext firmy (odvětví, velikost, právní forma)

Výstup: Čistý, osobní email v češtině — jako by ho psal člověk.
"""

import json
import httpx
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Gemini API config
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


@dataclass
class GeneratedEmail:
    """Vygenerovaný email od AI."""
    subject: str
    body_html: str
    variant_id: str = "ai_gemini"
    model: str = "gemini-2.0-flash"
    tokens_used: int = 0


def _build_system_prompt() -> str:
    """Systémový prompt pro Gemini — definuje styl a pravidla."""
    return """Jsi Martin Haynes — konzultant na AI compliance pro české firmy.
Píšeš osobní email konkrétnímu člověku. Představ si, že jsi ručně prošel jejich web,
našel na něm AI systémy a teď jim o tom píšeš.

STYL:
- Piš česky, přirozeně, jako člověk člověku
- Žádné emojis, žádné superlativy ("jediné v ČR", "revoluční")
- Žádné strašení pokutami (35M EUR odstraň úplně)
- Stručný, věcný, konkrétní — max 200 slov v těle emailu
- Tón: profesionální, ale neformální. Jako kdyby ti psal kolega z oboru.
- Piš v 1. osobě ("prošel jsem si váš web", "narazil jsem na...")
- Pokud znáš jméno, oslov přímo: "Dobrý den, pane Nováku" (5. pád!)
- Pokud neznáš, piš "Dobrý den"

STRUKTURA EMAILU:
1. Oslovení (se jménem pokud ho máš)
2. Kdo jsem + proč píšu (1-2 věty)
3. Co konkrétně jsem našel na jejich webu (konkrétní! ne obecné)
4. Co to znamená (EU AI Act, čl. 50 — povinnost transparence, deadline srpen 2026)
5. Co mají udělat (1 věta + link na report)
6. Podpis

CO NESMÍŠ:
- Psát "Není spam" nebo jakékoliv disclaimer o spamu
- Vyhrožovat pokutami nebo regulátory
- Říkat "jsme první / jediní / nejlepší"
- Psát příliš formálně nebo příliš prodejně
- Používat více než 1 call-to-action (jen link na report)
- Přehánět rizika u minimálních nálezů (Meta Pixel není katastrofa)
- NIKDY nepoužívej slovo "spam"

FORMÁT VÝSTUPU:
Vrať JSON objekt s klíči "subject" a "body".
- "subject": předmět emailu (max 60 znaků, bez emoji, konkrétní)
- "body": tělo emailu jako čistý text (HTML tagy jen pro <br>, <strong>, <a href>)

PŘÍKLADY DOBRÝCH PŘEDMĚTŮ:
- "Váš chatbot na webu kovacsauto.cz a EU AI Act"
- "AI systémy na bytoveho-detektiva.cz — krátké upozornění"
- "Pane Nováku, k vašemu webu mám poznámku"

PŘÍKLADY ŠPATNÝCH PŘEDMĚTŮ:
- "⚠️ URGENTNÍ: Nalezli jsme AI systémy!"
- "AI Act: 35M EUR pokuta hrozí vaší firmě"
- "Bezplatná AI analýza vašeho webu" """


def _build_user_prompt(
    company_name: str,
    company_url: str,
    contact_person: str,
    contact_role: str,
    legal_form: str,
    findings: list[dict],
    screenshot_url: str = "",
    scan_id: str = "",
    extra_context: str = "",
) -> str:
    """Sestaví prompt s konkrétními daty pro Gemini."""

    # Formát nálezů
    findings_text = ""
    for i, f in enumerate(findings, 1):
        findings_text += (
            f"{i}. {f['name']} ({f['category']}) — riziko: {f['risk_level']}\n"
            f"   AI Act: {f.get('ai_act_article', 'čl. 50')}\n"
            f"   Popis: {f.get('description', '')}\n"
            f"   Co udělat: {f.get('action_required', '')}\n\n"
        )

    report_link = f"https://aishield.cz/report/{scan_id}" if scan_id else f"https://aishield.cz/scan?url={company_url}"

    prompt = f"""Napiš personalizovaný email pro tuto firmu:

FIRMA:
- Název: {company_name}
- Web: {company_url}
- Právní forma: {legal_form or 'neznámá'}
- Kontaktní osoba: {contact_person or 'neznámé jméno'}
- Pozice: {contact_role or 'neznámá'}

NÁLEZY NA WEBU (co jsme detekovali):
{findings_text}

LINK NA REPORT: {report_link}

{f'EXTRA KONTEXT: {extra_context}' if extra_context else ''}

PODPIS:
Martin Haynes
+420 732 716 141 | AIshield.cz

Vrať JSON: {{"subject": "...", "body": "..."}}
Tělo emailu je plain text s minimálním HTML (<br>, <strong>, <a>).
Pamatuj — piš jako člověk, který si opravdu sedl a projel ten web."""

    return prompt


async def write_email(
    company_name: str,
    company_url: str,
    contact_person: str = "",
    contact_role: str = "",
    legal_form: str = "",
    findings: list[dict] | None = None,
    screenshot_url: str = "",
    scan_id: str = "",
    extra_context: str = "",
    api_key: str | None = None,
) -> GeneratedEmail:
    """
    Nechá Gemini Flash napsat personalizovaný email.

    Args:
        company_name: Název firmy
        company_url: URL webu
        contact_person: Jméno kontaktní osoby (z ARES/webu)
        contact_role: Pozice (jednatel, majitel, CEO...)
        legal_form: Právní forma (OSVČ, s.r.o., ...)
        findings: Seznam nálezů z detektoru
        screenshot_url: URL screenshotu
        scan_id: ID skenu
        extra_context: Další kontext (např. "web je celý AI-generovaný")
        api_key: Gemini API key (nebo z env GEMINI_API_KEY)
    """
    key = api_key or os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise ValueError("GEMINI_API_KEY není nastaven")

    findings_dicts = findings or []

    system_prompt = _build_system_prompt()
    user_prompt = _build_user_prompt(
        company_name=company_name,
        company_url=company_url,
        contact_person=contact_person,
        contact_role=contact_role,
        legal_form=legal_form,
        findings=findings_dicts,
        screenshot_url=screenshot_url,
        scan_id=scan_id,
        extra_context=extra_context,
    )

    # Gemini API request
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"{system_prompt}\n\n---\n\n{user_prompt}"}],
            }
        ],
        "generationConfig": {
            "temperature": 0.75,
            "maxOutputTokens": 2000,
            "responseMimeType": "application/json",
        },
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{GEMINI_API_URL}?key={key}",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()

            # Parsování odpovědi
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError(f"Gemini vrátil prázdnou odpověď: {data}")

            text = candidates[0]["content"]["parts"][0]["text"]

            # Token usage
            usage = data.get("usageMetadata", {})
            tokens = usage.get("totalTokenCount", 0)

            # Parsování JSON z odpovědi
            email_data = json.loads(text)

            subject = email_data.get("subject", f"K webu {company_url}")
            body = email_data.get("body", "")

            logger.info(
                f"Gemini email written: subject='{subject[:50]}', "
                f"body_len={len(body)}, tokens={tokens}"
            )

            # Wrap do minimálního HTML
            body_html = _wrap_email_html(body, company_url, scan_id)

            return GeneratedEmail(
                subject=subject,
                body_html=body_html,
                tokens_used=tokens,
            )

    except httpx.HTTPStatusError as e:
        logger.error(f"Gemini API error: {e.response.status_code} — {e.response.text[:300]}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Gemini response not valid JSON: {text[:300]}")
        # Fallback — zkusíme vytáhnout JSON z textu
        json_match = __import__("re").search(r'\{[^{}]*"subject"[^{}]*"body"[^{}]*\}', text, __import__("re").DOTALL)
        if json_match:
            email_data = json.loads(json_match.group())
            body_html = _wrap_email_html(email_data["body"], company_url, scan_id)
            return GeneratedEmail(
                subject=email_data["subject"],
                body_html=body_html,
                tokens_used=0,
            )
        raise ValueError(f"Nepodařilo se parsovat Gemini odpověď: {text[:200]}") from e


def _wrap_email_html(
    body_text: str,
    company_url: str,
    scan_id: str = "",
    to_email: str = "",
) -> str:
    """Obalí tělo emailu do minimálního HTML — čistý, profesionální."""
    from urllib.parse import quote

    unsubscribe = ""
    if to_email:
        unsubscribe = f'https://api.aishield.cz/api/unsubscribe?email={quote(to_email)}&company={quote(company_url)}'

    # Převedeme plain text na HTML (zachováme <br>, <strong>, <a>)
    # Ale newlines musíme nahradit za <br>
    if "<br" not in body_text and "<p>" not in body_text:
        body_text = body_text.replace("\n\n", "</p><p>").replace("\n", "<br>")
        body_text = f"<p>{body_text}</p>"

    unsubscribe_line = ""
    if unsubscribe:
        unsubscribe_line = f'<a href="{unsubscribe}" style="color: #999;">Nechci dostávat další upozornění</a>'

    return f"""<!DOCTYPE html>
<html lang="cs">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #222; line-height: 1.6; font-size: 15px; background: #fff;">

{body_text}

<hr style="border: none; border-top: 1px solid #ddd; margin: 32px 0 16px 0;">
<p style="font-size: 11px; color: #999; line-height: 1.4;">
    Jednorázové upozornění na základě veřejně dostupné analýzy webu {company_url}.<br>
    AIshield.cz | Martin Haynes, IČO: 17889251 | Mlýnská 53, 783 53 Velká Bystřice<br>
    {unsubscribe_line}
</p>

</body>
</html>"""


async def generate_outbound_email(
    company_url: str,
    html: str,
    findings: list[dict],
    scan_id: str = "",
    screenshot_url: str = "",
    to_email: str = "",
    ico: str | None = None,
    api_key: str | None = None,
) -> GeneratedEmail:
    """
    End-to-end: Vytáhne info o firmě + nechá Gemini napsat email.

    Tohle je hlavní funkce, kterou volá pipeline.
    """
    from backend.outbound.company_info import get_company_info

    # 1. Zjistíme info o firmě
    info = await get_company_info(url=company_url, html=html, ico=ico)

    logger.info(
        f"Company info: {info.company_name}, contact={info.contact_person}, "
        f"role={info.contact_role}, form={info.legal_form}"
    )

    # 2. Extra kontext z webu
    extra = ""
    # Detekce AI-generovaného obsahu
    html_lower = html.lower()
    if "umělou inteligencí" in html_lower or "ai generovan" in html_lower:
        extra += "Web otevřeně přiznává, že obsah je generován AI. "
    if "chatbot" in html_lower:
        chatbot_count = html_lower.count("chatbot")
        if chatbot_count > 20:
            extra += f"Web nabízí chatbot služby (slovo 'chatbot' se vyskytuje {chatbot_count}× na stránce). "

    # 3. Gemini napíše email
    email = await write_email(
        company_name=info.company_name,
        company_url=company_url,
        contact_person=info.contact_person,
        contact_role=info.contact_role,
        legal_form=info.legal_form,
        findings=findings,
        screenshot_url=screenshot_url,
        scan_id=scan_id,
        extra_context=extra,
        api_key=api_key,
    )

    # 4. Re-wrap s to_email pro unsubscribe
    if to_email:
        email.body_html = _wrap_email_html(
            # Extrahujeme body zpět (odstraníme wrapper)
            email.body_html.split('<body')[1].split('>',1)[1].rsplit('<hr',1)[0],
            company_url,
            scan_id,
            to_email,
        )

    return email
