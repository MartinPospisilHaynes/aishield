"""
AIshield.cz — AI Email Writer v2 (HYBRID)
Gemini 2.5 Flash píše POUZE personalizované sekce:
  1. intro — oslovení, kdo jsem, proč píšu (80-120 slov)
  2. findings_commentary — komentář k nálezům (60-100 slov)
  3. impact — dopad na klienta, co se stane (60-80 slov)

Šablona (email_templates.py) pak obalí tyto sekce krásným HTML:
  - Hlavička s logem
  - Tabulka rizik se semaforem
  - Screenshot webu
  - Deadline box, checklist, USP, CTA, footer
"""

import json
import re
import httpx
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Gemini 2.5 Flash — lepší kvalita textu
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


@dataclass
class GeneratedEmail:
    """Vygenerovaný email."""
    subject: str
    body_html: str
    variant_id: str = "hybrid_gemini25"
    model: str = GEMINI_MODEL
    tokens_used: int = 0


def _build_system_prompt() -> str:
    """Systémový prompt pro Gemini 2.5 — definuje styl a pravidla."""
    return """Jsi copywriter pro AIshield.cz. Píšeš personalizované sekce do B2B emailů,
které oslovují české firmy s upozorněním na AI Act compliance.

TVŮJ STYL:
- Čeština na úrovni rodilého mluvčího, bez chyb
- Profesionální, ale přátelský — odborník, který chce upřímně pomoct
- Piš v 1. osobě za "Bc. Martin Haynes, ředitel společnosti AIshield.cz"
- Pokud znáš jméno, oslov přímo v 5. pádu ("pane Nováku", "paní Nováková")
- Pokud neznáš, piš "Dobrý den"
- NIKDY nepiš "Vážený pane/paní" — je to zastaralé

CO NESMÍŠ:
- Žádné emoji (to řeší šablona)
- Žádné superlativy ("jediní v ČR", "revoluční")
- Žádné "Není spam" nebo disclaimer texty
- Nepoužívej slovo "spam" nikdy
- Žádné CTA tlačítka ("klikněte zde") — to řeší šablona
- Žádné ceníky ani ceny — to řeší šablona

KONTEXT:
Provedl jsi pravidelnou kontrolu AI systémů v českém online prostředí a narazil
jsi na web firmy. Detekoval jsi AI systémy, které nesplňují povinnosti dle
Nařízení Evropského parlamentu a Rady (EU) 2024/1689 ze dne 13. června 2024,
kterým se stanoví harmonizovaná pravidla pro umělou inteligenci (AI Act).

FORMÁT VÝSTUPU:
Vrať JSON objekt s těmito klíči:
{
  "subject": "předmět — formální, úřední tón, max 80 znaků, bez emoji",
  "intro": "Oslovení + představení + uklidnění + proč píšu. Viz STRUKTURA INTRA.",
  "findings_commentary": "Komentář ke konkrétním nálezům. Viz STRUKTURA.",
  "impact": "Přechod ze strašení k nabídce pomoci. Viz STRUKTURA."
}

STRUKTURA INTRO (150-200 slov):
1. Oslovení (se jménem v 5. pádu pokud ho máš)
2. "Jsem Bc. Martin Haynes, ředitel společnosti AIshield.cz."
3. Uklidnění: "Nemusíte se obávat, nic strašného se zatím neděje."
4. Proč píšu: "Při naší pravidelné kontrole AI systémů v českém online prostředí
   jsme narazili na váš web [URL]."
5. Zmínka o nařízení: Nařízení EP a Rady (EU) 2024/1689 (AI Act), které vstupuje
   v plnou účinnost 2. srpna 2026.
6. Co to znamená: všechny weby, e-shopy a aplikace musejí informovat návštěvníky
   o tom, zdali a jak využívají umělou inteligenci.
7. "Na vašich stránkách tyto informace nemáme uvedeny."
8. "V případě nesplnění povinnosti hrozí pokuty až do výše 35 milionů EUR
   nebo 7 % celosvětového ročního obratu."
9. "Na vašem webu jsme detekovali [POČET] AI systémů, což samo o sobě není
   žádný problém. Jen je potřeba mít připravenou dokumentaci podle pravidel."

STRUKTURA FINDINGS_COMMENTARY (150-250 slov):
1. Stručný komentář ke 2-3 nejdůležitějším nálezům
2. Pak POVINNĚ vypiš kompletní seznam povinností, co firma musí splnit:
   Napiš: "Dle AI Act musíte mimo jiné zajistit:"
   A pak vypiš VŠECHNY tyto body (nezkracuj, chceme, aby klient viděl rozsah):
   - Transparentní AI banner/oznámení na webu viditelné pro každého návštěvníka
   - Samostatnou stránku s informacemi o využívaných AI systémech (AI disclosure page)
   - Kompletní dokumentaci všech AI systémů včetně popisu účelu, vstupů a výstupů
   - Posouzení rizik (risk assessment) pro každý AI systém
   - Evidenci zpracování dat v souvislosti s AI systémy
   - Zavedení mechanismu lidského dohledu (human oversight)
   - Možnost eskalace komunikace s AI na lidského operátora
   - Technickou dokumentaci AI systémů dle přílohy IV AI Act
   - Záznam o školení zaměstnanců v oblasti AI gramotnosti (čl. 4 AI Act)
   - Listinnou/archivní podobu compliance dokumentace
   - Postup pro hlášení incidentů souvisejících s AI
   - Audit trail / logování rozhodnutí AI systémů
   - Aktualizaci cookie banneru a privacy policy o AI systémy
   - Registraci vysokorizikových AI systémů v EU databázi (pokud relevantní)
   Ukonči: "Vím, že to vypadá jako hodně práce — a upřímně, je."

STRUKTURA IMPACT (100-150 slov):
1. POZITIVNÍ PŘECHOD — veselý, odlehčený tón:
   "Ale od toho tu právě jsme my."
2. Zdůrazni, že se klient nemusí o nic starat.
3. Vypiš co AIshield dodá:
   - Kompletní diagnostiku webu a všech AI systémů
   - Výpis AI nástrojů s klasifikací rizik
   - Hotovou compliance dokumentaci v PDF
   - AI banner/oznámení připravené k nasazení
   - Záznam o školení (pokud má zaměstnance)
   - Průběžný monitoring nových AI systémů
4. Projev pochopení: klient se musí starat o byznys, ne o byrokracii EU.
   My rádi pomůžeme, zatímco se on může soustředit na vydělávání peněz.
5. NEPODEPISUJ SE — podpis řeší šablona.

PŘÍKLADY DOBRÝCH PŘEDMĚTŮ:
- "Oznámení o možném porušení povinností dle Nařízení EU 2024/1689 (AI Act)"
- "K AI systémům na kovacsauto.cz — povinnosti dle AI Act"
- "Upozornění: AI systémy na vašem webu a nařízení EU"

PŘÍKLADY ŠPATNÝCH PŘEDMĚTŮ:
- "⚠️ URGENTNÍ: AI systémy na vašem webu!"
- "Bezplatná AI analýza — nabídka"
- "Zaujalo nás vaše podnikání"
"""


def _build_user_prompt(
    company_name: str,
    company_url: str,
    contact_person: str,
    contact_role: str,
    legal_form: str,
    findings: list[dict],
    extra_context: str = "",
) -> str:
    """Sestaví prompt s konkrétními daty pro Gemini."""

    # Formát nálezů
    findings_text = ""
    high_risk_count = 0
    categories_found = set()
    for i, f in enumerate(findings, 1):
        risk = f.get("risk_level", "limited")
        if risk in ("high", "prohibited"):
            high_risk_count += 1
        categories_found.add(f.get("category", "unknown"))
        findings_text += (
            f"  {i}. {f['name']} (kategorie: {f['category']}, riziko: {risk})\n"
            f"     AI Act: {f.get('ai_act_article', 'čl. 50')}\n"
            f"     {f.get('description', '')}\n"
        )

    has_chatbot = "chatbot" in categories_found
    has_analytics = "analytics" in categories_found
    has_recommender = "recommender" in categories_found
    has_content_gen = "content_gen" in categories_found

    # Kontext pro AI
    specialization_hint = ""
    if has_chatbot:
        specialization_hint += "Web používá AI chatbot — zmíň povinnost informovat uživatele. "
    if has_content_gen:
        specialization_hint += "Web používá AI pro generování obsahu — zmíň povinnost označit AI obsah. "
    if has_recommender:
        specialization_hint += "Web používá AI doporučovací systém — zmíň transparenci AI doporučení. "

    return f"""Napiš personalizované sekce emailu pro tuto firmu:

FIRMA: {company_name}
WEB: {company_url}
PRÁVNÍ FORMA: {legal_form or 'neznámá'}
KONTAKTNÍ OSOBA: {contact_person or 'neznámé jméno'}
POZICE: {contact_role or 'neznámá'}

POČET NÁLEZŮ: {len(findings)}
NÁLEZY:
{findings_text}

{specialization_hint}
{f'EXTRA KONTEXT: {extra_context}' if extra_context else ''}

DŮLEŽITÉ:
- V "intro" dodržuj PŘESNĚ strukturu popsanou v systémovém promptu (uklidnění,
  kdo jsem, proč píšu, zmínka o nařízení, pokuty, počet nálezů).
- V "findings_commentary" MUSÍŠ vypsat kompletní seznam povinností (viz systémový prompt).
  Nezkracuj ho! Čím více položek, tím lépe.
- V "impact" buď POZITIVNÍ a nabídni pomoc AIshield.cz.
- NEPODEPISUJ SE v žádné sekci (podpis je v šabloně).
- Piš ČESKY. Buď konkrétní — zmíň skutečná jména nálezů.

Vrať JSON: {{"subject": "...", "intro": "...", "findings_commentary": "...", "impact": "..."}}
"""


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
    to_email: str = "",
    api_key: str | None = None,
) -> GeneratedEmail:
    """
    Gemini 2.5 napíše personalizované sekce → šablona obalí HTML.

    Vrátí GeneratedEmail s kompletním HTML emailem.
    """
    from backend.outbound.email_templates import (
        build_hybrid_email,
        FindingRow,
    )

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
        extra_context=extra_context,
    )

    # Gemini 2.5 API request
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"{system_prompt}\n\n---\n\n{user_prompt}"}],
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 8000,
            "responseMimeType": "application/json",
        },
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
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
            intro = email_data.get("intro", "")
            findings_commentary = email_data.get("findings_commentary", "")
            impact = email_data.get("impact", "")

            logger.info(
                f"Gemini 2.5 email: subject='{subject[:50]}', "
                f"intro={len(intro)}ch, findings={len(findings_commentary)}ch, "
                f"impact={len(impact)}ch, tokens={tokens}"
            )

    except httpx.HTTPStatusError as e:
        logger.error(f"Gemini API error: {e.response.status_code} — {e.response.text[:500]}")
        raise
    except json.JSONDecodeError:
        logger.warning(f"Gemini response not valid JSON, trying repair: {text[:200]}")
        # Fallback 1 — zkusíme najít kompletní JSON
        json_match = re.search(r'\{.*"subject".*"intro".*\}', text, re.DOTALL)
        if json_match:
            try:
                email_data = json.loads(json_match.group())
                subject = email_data.get("subject", f"K webu {company_url}")
                intro = email_data.get("intro", "")
                findings_commentary = email_data.get("findings_commentary", "")
                impact = email_data.get("impact", "")
                tokens = 0
            except json.JSONDecodeError:
                pass
        
        # Fallback 2 — opravíme oříznutý JSON
        if not intro:
            # Zkusíme vytáhnout jednotlivé klíče regexem
            def _extract_key(key: str) -> str:
                m = re.search(rf'"{key}"\s*:\s*"((?:[^"\\]|\\.)*)', text, re.DOTALL)
                return m.group(1).replace("\\n", "\n").replace('\\"', '"') if m else ""
            
            subject = _extract_key("subject") or f"K webu {company_url}"
            intro = _extract_key("intro")
            findings_commentary = _extract_key("findings_commentary")
            impact = _extract_key("impact")
            tokens = 0
            
            if intro:
                logger.info("Gemini JSON opraven regex fallbackem")
            else:
                raise ValueError(f"Nepodařilo se parsovat Gemini odpověď: {text[:300]}")

    # ── Převedeme findings na FindingRow pro šablonu ──
    finding_rows = []
    for f in findings_dicts:
        finding_rows.append(FindingRow(
            name=f.get("name", "Neznámý systém"),
            category=f.get("category", "ai_tool"),
            risk_level=f.get("risk_level", "limited"),
            ai_act_article=f.get("ai_act_article", "čl. 50"),
            action_required=f.get("action_required", ""),
            description=f.get("description", ""),
        ))

    # ── Sestavíme hybrid email ──
    body_html = build_hybrid_email(
        gemini_intro=intro,
        gemini_findings_commentary=findings_commentary,
        gemini_impact=impact,
        company_url=company_url,
        findings=finding_rows,
        screenshot_url=screenshot_url,
        scan_id=scan_id,
        to_email=to_email,
    )

    return GeneratedEmail(
        subject=subject,
        body_html=body_html,
        tokens_used=tokens,
    )


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
    End-to-end: Vytáhne info o firmě + Gemini 2.5 napíše + šablona obalí.

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
    html_lower = html.lower() if html else ""
    if "umělou inteligencí" in html_lower or "ai generovan" in html_lower:
        extra += "Web otevřeně přiznává, že obsah je generován AI. "
    if "chatbot" in html_lower:
        chatbot_count = html_lower.count("chatbot")
        if chatbot_count > 20:
            extra += f"Web je zaměřen na chatbot služby ({chatbot_count}× zmíněno). "

    # 3. Gemini napíše personalizované sekce + šablona obalí HTML
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
        to_email=to_email,
        api_key=api_key,
    )

    return email
