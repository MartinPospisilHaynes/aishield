"""
AIshield.cz — AI Email Composer v1

Personalizované cold emaily generované přes Claude (Anthropic).
Žádné šablony. Každý email je unikát, psaný na míru konkrétní firmě
na základě reálných nálezů ze skenu webu.

Používá:
  - call_claude() z backend.documents.llm_engine (retry, fallback, cost tracking)
  - _get_vocative_name_sync() z backend.outbound.email_writer (český 5. pád)
  - send_email() z backend.outbound.email_engine (Resend API)

Model: Claude Sonnet 4.6 → fallback Opus 4.6 (konfigurace v llm_engine.py)
"""

import logging
import html as html_module
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ── Parametry generování ──
EMAIL_TEMPERATURE = 0.75   # Kreativnější output, ale ne chaotický
EMAIL_MAX_TOKENS = 2000    # Email nemá být román
EMAIL_LABEL = "email_composer"

# Pevný předmět emailu
FIXED_SUBJECT = "Upozornění na riziko porušení pravidel EU na vašem webu"

# Fixní úvodní hook — šokující, stejný v každém emailu
FIXED_INTRO = "jmenuji se Martin Haynes a při návštěvě Vašeho webu jsem narazil na pár nedostatků, které budou v brzké době trestány velkými pokutami."

# Fixní podpis — vždy stejný, připojuje se kódem
FIXED_SIGNATURE = """S pozdravem
Martin Haynes
AIshield.cz
Tel: 732 716 141
www.aishield.cz"""


@dataclass
class ComposedEmail:
    """AI-generovaný email — výstup compose_email()."""
    subject: str
    body_text: str          # Čistý text od Claude
    body_html: str          # Zabalený v minimálním branded HTML
    vocative_used: str      # Jaký vokativ se použil
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


# ══════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT — srdce celého systému
# ══════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """Jsi Martin Haynes, zakladatel AIshield.cz. Píšeš POKRAČOVÁNÍ prvního kontaktního emailu.

DŮLEŽITÉ: Úvodní odstavec emailu je PŘEDEM NAPSANÝ a připojí se automaticky:
"Dobrý den [oslovení], jmenuji se Martin Haynes a při návštěvě Vašeho webu jsem narazil na pár nedostatků, které budou v brzké době trestány velkými pokutami."
Ty ho NEPÍŠEŠ. Podpis se taky připojí automaticky. Ty píšeš JEN střední část — od nálezů po CTA.

═══ AI ACT — FAKTA (znáš nazpaměť) ═══
• Nařízení EU 2024/1689 o umělé inteligenci — platí PŘÍMO, bez transpozice.
• Plná účinnost: 2. srpna 2026. Sankce: až 35 mil. EUR nebo 7 % obratu.
• Týká se ÚPLNĚ VŠECH webů a e-shopů v ČR — kdo nasazuje jakýkoli AI systém (analytika, chatboty, personalizace, trackery). NIKDO nemá výjimku.
• Je to jako GDPR — pamatujete co se dělo? Teď to samé čeká kvůli umělé inteligenci. A tentokrát to bude ještě přísnější.
• POVINNOST: transparentní stránka na webu (Article 50) — MUSÍ být na každém webu, kde běží AI systém. To je zákonná povinnost.
• Další povinnosti: dokumentace nasazení AI, informování uživatelů, označování AI obsahu.
• Dozor v ČR: Úřad pro umělou inteligenci (vzniká).
• 95 % českých firem to zatím vůbec neřeší.

═══ CO AISHIELD.CZ DODÁVÁ ═══
• Kompletní audit webu — detekce všech AI systémů
• TRANSPARENTNÍ STRÁNKU — to je klíčový produkt. Povinná na každém webu dle Article 50 AI Act. Bez ní hrozí pokuta.
• Veškerou AI Act dokumentaci
• Školení zaměstnanců
• Sloužíme VŠEM — od jednotlivců a OSVČ přes malé firmy až po velké korporáty
• Většinou hotovo za 2 týdny

═══ TVŮJ STYL ═══
1. Piš jako ČLOVĚK. Žádné firemní klišé. Žádné „V dnešní dynamické době…".
2. Vykej (Vy, Vám, Váš — VŽDY s velkým V).
3. Krátké věty. Max 1-2 souvětí, pak tečka.
4. Občas hovorový obrat — „ruku na srdce", „jednoduše řečeno", „no a to je problém".
5. VŽDY jmenuj KONKRÉTNÍ systémy z dodaných nálezů. Nic si nevymýšlej.
6. Tvůj text (bez úvodu a podpisu): 120–200 slov.
7. Buď informativní a PŘÍMÝ — problém je reálný, ale bez doomsday marketingu.
8. Neprezentuj se jako AI — jsi Martin, živý člověk.
9. NIKDY neříkej „jmenuji se…" ani „provozuji…" — to už je v úvodu.
10. NEZAČÍNEJ představováním firmy AIshield — rovnou piš o nálezech.

═══ STRUKTURA (jen to co píšeš TY — bez úvodu, bez podpisu) ═══

1. NÁLEZY (2-4 věty)
   Co KONKRÉTNĚ jsi na webu našel. Jmenuj systémy jménem. Popiš web jménem.
   U každého stručně: CO dělá a PROČ spadá pod AI Act.

2. KONTEXT + GDPR ANALOGIE (2-3 věty)
   Zmiň deadline 2. srpna 2026.
   Přirovnej ke GDPR: „Vzpomeňte na GDPR — teď to samé čeká kvůli AI."
   Zdůrazni: týká se to ABSOLUTNĚ VŠECH webů a e-shopů v Česku, bohužel nikdo nemá výjimku.

3. ŘEŠENÍ — TRANSPARENTNÍ STRÁNKA (2-3 věty)
   Hlavní povinnost: transparentní stránka na webu (Article 50) — MUSÍ být na každém webu s AI.
   Zmiň kompletní dokumentaci + školení.
   „Pomáháme od jednotlivců a OSVČ až po velké korporáty."
   „Většinou je to otázka 2 týdnů."

4. CTA (1 věta)
   Neformální. „Stačí odpovědět." nebo „Zavolejte mi." Žádný tlak.

═══ ZAKÁZÁNO ═══
✗ Úvod „jmenuji se…", „provozuji…", „představuji se…" — JE PŘEDEM NAPSANÝ
✗ Úvodní představení firmy AIshield.cz — rovnou k nálezům
✗ Podpis — připojí se automaticky
✗ „Dobrý den" — je v úvodu
✗ CAPS LOCK (kromě „AI Act" a „AI")
✗ Vykřičníky za sebou (!!!)
✗ „ZDARMA", „AKCE", „SLEVA"
✗ Smyšlené nálezy, které nejsou v dodaných datech
✗ Generické fráze („digitální transformace", „moderní svět", „dynamická doba")
✗ Emoji, HTML tagy
✗ Více než 1 CTA

═══ PŘÍKLAD pokračování (pro inspiraci, NE pro kopírování!) ═══
(Poznámka: toto je JEN střední část. Úvod a podpis se připojí automaticky.)

Prošel jsem Váš web nova-restaurace.cz a náš skener na něm detekoval tři systémy, které spadají pod AI Act: Google Analytics 4 — zpracovává chování návštěvníků pomocí strojového učení, Meta Pixel — sledovací AI od Facebooku pro cílení reklam, a Google Tag Manager, který celé nasazení koordinuje.

Vzpomeňte na GDPR — kolik bylo zmatku, pokut a stresu. Teď přichází to samé kvůli umělé inteligenci. Nařízení AI Act se týká úplně všech webů a e-shopů v Česku. Od 2. srpna 2026 platí plné sankce a bohužel nikdo nemá výjimku.

Klíčová povinnost je takzvaná transparentní stránka — ta musí být na každém webu, kde běží jakýkoli AI systém. V AIshield.cz Vám ji připravíme spolu s kompletní dokumentací a školením. Pomáháme od jednotlivců a OSVČ až po velké firmy — většinou je to otázka dvou týdnů.

Pokud Vás to zajímá, stačí odpovědět na tento email.

═══ FORMÁT ODPOVĚDI ═══
Odpověz POUZE středním textem emailu (od nálezů po CTA). Čistý text.
Žádný úvod, žádný podpis, žádný předmět, žádné SUBJECT:, žádné oddělovače.
Začni rovnou první větou o nálezech na webu."""


# ══════════════════════════════════════════════════════════════════════
# POMOCNÉ FUNKCE
# ══════════════════════════════════════════════════════════════════════

# Mapování kategorií findings na lidský český popis
CATEGORY_LABELS = {
    "tracking": "sledovací systém",
    "analytics": "analytický AI systém",
    "advertising": "reklamní AI systém",
    "personalization": "personalizační AI",
    "chatbot": "AI chatbot",
    "ai_tool": "AI nástroj",
    "automation": "automatizační AI systém",
    "recommendation": "doporučovací AI systém",
    "content_generation": "systém pro generování obsahu pomocí AI",
}


def _build_findings_text(findings: list[dict]) -> str:
    """Převede findings na čitelný text pro Claude."""
    if not findings:
        return "Na webu nebyly detekovány konkrétní AI systémy, ale web vykazuje znaky použití AI technologií."

    lines = []
    for i, f in enumerate(findings, 1):
        name = f.get("name", "Neznámý systém")
        category = f.get("category", "ai_tool")
        desc = f.get("description_cs", "") or f.get("description", "")
        label = CATEGORY_LABELS.get(category, "AI systém")

        line = f"  {i}. {name} ({label})"
        if desc:
            line += f" — {desc}"
        lines.append(line)

    return "\n".join(lines)


def _build_user_prompt(
    company_name: str,
    company_url: str,
    vocative_name: str,
    contact_person: str,
    legal_form: str,
    industry: str,
    findings: list[dict],
) -> str:
    """Sestaví uživatelský prompt se všemi daty o firmě."""
    findings_text = _build_findings_text(findings)
    findings_count = len(findings) if findings else 0

    return f"""Napiš POKRAČOVÁNÍ emailu (střední část — od nálezů po CTA).
Úvod a podpis se připojí automaticky — ty je NEPÍŠEŠ.

═══ DATA O FIRMĚ ═══
Název firmy: {company_name or "neznámý"}
Web: {company_url}
Kontaktní osoba: {contact_person or "neznámá"}
Právní forma: {legal_form or "neznámá"}
Obor: {industry or "neznámý"}

═══ NALEZENÉ AI SYSTÉMY ({findings_count}) ═══
{findings_text}

═══ POKYNY ═══
- MUSÍŠ jmenovat přesně tyto nalezené systémy — nesmíš si vymyslet jiné.
- Pokud je systémů hodně (4+), vyber 2-3 nejdůležitější a ostatní shrň ("a další").
- Přizpůsob tón právní formě: OSVČ = osobnější, s.r.o./a.s. = formálnější.
- Pokud znáš obor firmy, zakomponuj ho přirozeně.
- NEZAPOMEŇ zmínit GDPR analogii — že se to týká VŠECH webů a e-shopů.
- NEZAPOMEŇ zmínit transparentní stránku jako zákonnou povinnost.
- NEZAPOMEŇ zmínit že pomáháme od OSVČ po velké korporáty.
- Odpověz POUZE středním textem — žádný úvod, žádný podpis, žádný předmět."""


def _parse_email_output(text: str) -> str:
    """Parsuje výstup Claude — vrací čistý střední text (bez úvodu a podpisu)."""
    text = text.strip()

    # Pokud Claude přesto vrátil SUBJECT: ... --- ..., odstraníme to
    match = re.match(
        r'^SUBJECT:\s*.+?\s*\n---\s*\n(.+)',
        text,
        re.DOTALL,
    )
    if match:
        text = match.group(1).strip()

    # Pokud začíná SUBJECT: bez ---, odebereme první řádek
    if text.upper().startswith("SUBJECT"):
        lines = text.split("\n", 1)
        if len(lines) == 2:
            text = lines[1].strip().lstrip("-").strip()

    # Odstraníme podpis, pokud ho Claude přidal
    sig_match = re.search(r'\n\s*S pozdravem\s*\n', text, re.IGNORECASE)
    if sig_match:
        text = text[:sig_match.start()].strip()

    # Odstraníme úvod "Dobrý den" / "jmenuji se", pokud ho Claude přidal
    intro_match = re.match(
        r'^(?:Dobrý den[^,]*,?\s*\n+)?(?:jmenuji se[^\n]*\n+)?',
        text,
        re.IGNORECASE,
    )
    if intro_match and intro_match.end() > 0:
        candidate = text[intro_match.end():].strip()
        if candidate:  # Jen pokud po ořezu něco zbyde
            text = candidate

    return text


def _wrap_in_html(body_text: str, company_url: str = "") -> str:
    """
    Zabalí čistý text do minimálního branded HTML.
    Čistý, profesionální, žádný marketing template.
    Maximální doručitelnost.
    """
    # Escapujeme HTML entity v textu
    escaped = html_module.escape(body_text)

    # Převedeme řádky na <br> a prázdné řádky na mezery mezi odstavci
    paragraphs = escaped.split("\n\n")
    html_parts = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        # Uvnitř odstavce: \n → <br>
        p = p.replace("\n", "<br>")
        html_parts.append(f'<p style="margin:0 0 16px 0;line-height:1.6;">{p}</p>')

    body_html = "\n".join(html_parts)

    return f"""<!DOCTYPE html>
<html lang="cs">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#ffffff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#ffffff;">
<tr><td style="padding:24px;color:#000000;font-size:15px;line-height:1.6;">
{body_html}
</td></tr>
</table>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════════
# HLAVNÍ FUNKCE
# ══════════════════════════════════════════════════════════════════════

async def compose_email(
    company_name: str,
    company_url: str,
    contact_person: str = "",
    legal_form: str = "",
    industry: str = "",
    findings: list[dict] | None = None,
    scan_id: str = "",
) -> ComposedEmail:
    """
    Vygeneruje personalizovaný email přes Claude.

    Args:
        company_name: Název firmy (např. "Restaurace Mlýn s.r.o.")
        company_url: URL webu firmy
        contact_person: Jméno kontaktu (bude sklonováno do vokativu)
        legal_form: Právní forma (OSVČ, s.r.o., a.s., ...)
        industry: Obor firmy
        findings: Seznam nálezů ze skenu [{name, category, description_cs}, ...]
        scan_id: ID skenu pro logging

    Returns:
        ComposedEmail s vygenerovaným textem a HTML
    """
    from backend.outbound.email_writer import _get_vocative_name_sync
    from backend.documents.llm_engine import call_claude

    findings = findings or []

    # 1. Český vokativ — čistě Python, bez API
    vocative_name = _get_vocative_name_sync(contact_person)

    logger.info(
        "[Email Composer] Generuji email: company=%s, url=%s, contact=%s, "
        "vocative=%s, findings=%d, scan=%s",
        company_name, company_url, contact_person,
        vocative_name, len(findings), scan_id,
    )

    # 2. Sestavíme prompt
    user_prompt = _build_user_prompt(
        company_name=company_name,
        company_url=company_url,
        vocative_name=vocative_name,
        contact_person=contact_person,
        legal_form=legal_form,
        industry=industry,
        findings=findings,
    )

    # 3. Zavoláme Claude (retry + fallback + cost tracking v llm_engine)
    text, meta = await call_claude(
        system=SYSTEM_PROMPT,
        prompt=user_prompt,
        label=EMAIL_LABEL,
        temperature=EMAIL_TEMPERATURE,
        max_tokens=EMAIL_MAX_TOKENS,
    )

    # 4. Parsujeme výstup (Claude píše jen střed — bez úvodu a podpisu)
    ai_body = _parse_email_output(text)
    subject = FIXED_SUBJECT

    # 5. Sestavíme plný email: fixní úvod + AI tělo + fixní podpis
    if vocative_name:
        greeting = f"Dobrý den {vocative_name},"
    else:
        greeting = "Dobrý den,"
    body_text = f"{greeting}\n\n{FIXED_INTRO}\n\n{ai_body}\n\n{FIXED_SIGNATURE}"

    # 6. Zabalíme do HTML
    body_html = _wrap_in_html(body_text, company_url)

    logger.info(
        "[Email Composer] Hotovo: subject='%s', body_len=%d, model=%s, cost=$%.4f",
        subject[:60], len(body_text),
        meta.get("model", "?"), meta.get("cost_usd", 0),
    )

    return ComposedEmail(
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        vocative_used=vocative_name,
        model=meta.get("model", ""),
        input_tokens=meta.get("input_tokens", 0),
        output_tokens=meta.get("output_tokens", 0),
        cost_usd=meta.get("cost_usd", 0),
    )


async def compose_and_send(
    to_email: str,
    company_name: str,
    company_url: str,
    contact_person: str = "",
    legal_form: str = "",
    industry: str = "",
    findings: list[dict] | None = None,
    scan_id: str = "",
    from_email: str | None = None,
    from_name: str = "Martin Haynes | AIshield.cz",
    dry_run: bool = False,
) -> dict:
    """
    Vygeneruje personalizovaný email a odešle ho přes Resend.

    Args:
        to_email: Cílová emailová adresa
        dry_run: Pokud True, email se nevyšle, jen se vrátí

    Returns:
        dict s klíči: email (ComposedEmail), send_result (Resend response), sent (bool)
    """
    from backend.outbound.email_engine import send_email

    # 1. Generujeme email
    email = await compose_email(
        company_name=company_name,
        company_url=company_url,
        contact_person=contact_person,
        legal_form=legal_form,
        industry=industry,
        findings=findings,
        scan_id=scan_id,
    )

    result = {
        "email": email,
        "subject": email.subject,
        "body_text": email.body_text,
        "body_html": email.body_html,
        "vocative": email.vocative_used,
        "model": email.model,
        "cost_usd": email.cost_usd,
        "tokens": email.input_tokens + email.output_tokens,
        "sent": False,
        "send_result": None,
    }

    if dry_run:
        logger.info("[Email Composer] DRY RUN — email nevyslán: to=%s", to_email)
        return result

    # 2. Odešleme
    try:
        send_result = await send_email(
            to=to_email,
            subject=email.subject,
            html=email.body_html,
            from_email=from_email,
            from_name=from_name,
        )
        result["send_result"] = send_result
        result["sent"] = True
        logger.info(
            "[Email Composer] Email odeslán: to=%s, resend_id=%s",
            to_email, send_result.get("id", "?"),
        )
    except Exception as e:
        logger.error("[Email Composer] Chyba při odesílání: %s", e)
        result["send_error"] = str(e)

    return result


# ══════════════════════════════════════════════════════════════════════
# HELPER: Rychlý test z příkazové řádky
# ══════════════════════════════════════════════════════════════════════

async def _demo():
    """Demo test — vygeneruje email pro fiktivní firmu a vypíše ho."""
    email = await compose_email(
        company_name="Restaurace Mlýn s.r.o.",
        company_url="www.restaurace-mlyn.cz",
        contact_person="Jan Novotný",
        legal_form="s.r.o.",
        industry="pohostinství",
        findings=[
            {
                "name": "Google Analytics 4",
                "category": "analytics",
                "description_cs": "Webová analytika od Google využívající strojové učení pro analýzu chování návštěvníků",
            },
            {
                "name": "Meta Pixel (Facebook)",
                "category": "advertising",
                "description_cs": "Sledovací pixel Facebooku pro cílení reklam pomocí AI",
            },
            {
                "name": "Google Tag Manager",
                "category": "tracking",
                "description_cs": "Správce tagů pro koordinaci marketingových a analytických nástrojů",
            },
        ],
    )
    print("=" * 60)
    print(f"SUBJECT: {email.subject}")
    print(f"MODEL: {email.model}")
    print(f"TOKENS: {email.input_tokens} + {email.output_tokens}")
    print(f"COST: ${email.cost_usd:.4f}")
    print(f"VOCATIVE: {email.vocative_used}")
    print("=" * 60)
    print(email.body_text)
    print("=" * 60)


if __name__ == "__main__":
    import asyncio
    import sys
    sys.path.insert(0, "/opt/aishield")
    from dotenv import load_dotenv
    load_dotenv("/opt/aishield/.env")
    asyncio.run(_demo())
