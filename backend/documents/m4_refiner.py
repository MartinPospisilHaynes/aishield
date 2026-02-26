"""
AIshield.cz — Modul 4: REFINER (Claude Sonnet 4)

Přebírá draft z M1 + kritiky z M2 (EU) a M3 (klient),
produkuje FINÁLNÍ verzi HTML dokumentu.

Vstup:  draft_html + eu_critique + client_critique + company_context + doc_key
Výstup: (final_html, metadata)

Model: Claude Sonnet 4 — nejlepší pro precizní editaci a syntézu.
"""

import logging
from typing import Tuple

from backend.documents.llm_engine import call_gemini, extract_html_content

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT — Expert Editor & Refiner
# ══════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT_M4 = """Jsi expert na finální editaci profesionální compliance dokumentace.
Tvým úkolem je vzít DRAFT dokumentu a KRITIKY dvou nezávislých kritiků
a vyprodukovat FINÁLNÍ, DOKONALOU verzi dokumentu.

TVŮJ PROCES:
1. Přečti draft dokumentu
2. Přečti kritiku EU inspektora (M2) — zaměřenou na právní přesnost a úplnost
3. Přečti kritiku klienta (M3) — zaměřenou na srozumitelnost a praktičnost
4. Adresuj VŠECHNY nálezy obou kritiků:
   - Kritické a důležité nálezy MUSÍŠ opravit
   - Menší nálezy a poznámky oprav pokud to zlepší kvalitu
5. Zachovej silné stránky identifikované kritiky
6. Přidej chybějící obsah identifikovaný kritiky
7. Vyprodukuj FINÁLNÍ HTML dokument

VÝSTUPNÍ PRAVIDLA:
1. Piš přímo HTML — začni <h1> tagem.
2. NEBALÍ do ```html```, ```json```, markdown bloků.
3. NEPIŠ žádný komentář před nebo za HTML.
4. NEPIŠ poznámky typu "Zde jsem opravil..." nebo "Na základě kritiky..."
5. Výstup musí být ČISTÝ HTML dokument připravený pro PDF.
6. ZACHOVEJ všechny CSS třídy z draftu:
   .highlight, .warning, .info, .callout, .badge-high, .badge-limited,
   .badge-minimal, .metric-grid, .metric-card, .metric-value, .metric-label,
   .sig-block, .sig-field, .no-break
7. Pro HTML atributy používej jednoduché uvozovky: class='highlight'

PRIORITY PŘI KONFLIKTU KRITIKŮ:
Pokud se kritiky M2 (EU inspektor) a M3 (klient) vzájemně bijí:
1. PRÁVNÍ PŘESNOST (M2) má VŽDY přednost — právní fakt zachovej
2. SROZUMITELNOST (M3) — právní fakt přepiš srozumitelným jazykem dle M3
3. DÉLKA A OBSÁHLOST — až na posledním místě
Příklad: M2 říká "přidej citaci čl. 50", M3 říká "je to moc právnické" →
Řešení: citaci zachovej, ale vysvětli ji lidsky ("čl. 50 AI Act vyžaduje, abyste...")

KVALITATIVNÍ PRAVIDLA:
- Nesmíš VYNECHAT žádnou povinnou sekci ani tabulku z draftu
- Můžeš zkrátit redundance a vatu, pokud tím roste kvalita a čitelnost
- Přidej chybějící obsah identifikovaný kritiky
- Oprav právní nepřesnosti z EU kritiky
- Zlepši srozumitelnost na základě klientské kritiky
- Přidej konkrétní příklady tam kde chybí
- Upřesni personalizaci pro firmu
- Zachovej profesionální ton
- V textu používej české typografické uvozovky: „text“
- NEPOUŽÍVEJ emoji

ZAKÁZÁNO:
- Mazat celé sekce nebo tabulky z draftu
- Přidávat meta-komentáře o editačním procesu
- Měnit fakticky správné informace
- Odstraňovat tabulky nebo strukturované přehledy
- Klišé: „V dnešní digitální době", „Závěrem lze říci"
- Časové lhůty pro nápravná opatření (mimo zákonné deadliny)
- Zmínky o testech, certifikacích, kvízech
"""


# ══════════════════════════════════════════════════════════════════════
# CRITIQUE FORMATTER — formátuje kritiky pro prompt
# ══════════════════════════════════════════════════════════════════════

def _format_critique(critique: dict, source: str) -> str:
    """Formátuje kritiku do čitelného textu pro Refiner prompt."""
    parts = []
    parts.append(f"══ KRITIKA: {source} ══")
    parts.append(f"Celkové hodnocení: {critique.get('celkove_hodnoceni', '?')}")
    parts.append(f"Skóre: {critique.get('skore', '?')}/10")

    # Nálezy
    nalezy = critique.get("nalezy", [])
    if nalezy:
        parts.append(f"\nNÁLEZY ({len(nalezy)}):")
        for i, n in enumerate(nalezy, 1):
            severity = n.get("zavaznost", "?").upper()
            parts.append(f"  [{severity}] {n.get('oblast', '?')}: {n.get('popis', '?')}")
            if n.get("doporuceni"):
                parts.append(f"    → Doporučení: {n['doporuceni']}")
            if n.get("reference_ai_act"):
                parts.append(f"    → Reference: {n['reference_ai_act']}")

    # Chybějící obsah
    missing = critique.get("chybejici_obsah", [])
    if missing:
        parts.append(f"\nCHYBĚJÍCÍ OBSAH:")
        for m in missing:
            parts.append(f"  • {m}")

    # Silné stránky
    strengths = critique.get("silne_stranky", [])
    if strengths:
        parts.append(f"\nSILNÉ STRÁNKY (zachovej!):")
        for s in strengths:
            parts.append(f"  ✓ {s}")

    # Otázky klienta (jen pro M3)
    questions = critique.get("otazky_klienta", [])
    if questions:
        parts.append(f"\nOTÁZKY KLIENTA (odpověz na ně v dokumentu!):")
        for q in questions:
            parts.append(f"  ? {q}")

    # Celkové doporučení
    overall = critique.get("celkove_doporuceni", "")
    if overall:
        parts.append(f"\nCELKOVÉ DOPORUČENÍ: {overall}")

    return "\n".join(parts)


# ══════════════════════════════════════════════════════════════════════
# REFINE FUNCTION — hlavní vstupní bod modulu
# ══════════════════════════════════════════════════════════════════════

async def refine(
    draft_html: str,
    eu_critique: dict,
    client_critique: dict,
    company_context: str,
    doc_key: str,
) -> Tuple[str, dict]:
    """
    Finalizuje dokument na základě draftu a obou kritik.

    Args:
        draft_html: HTML koncept z Modulu 1
        eu_critique: kritika EU inspektora z Modulu 2
        client_critique: kritika klienta z Modulu 3
        company_context: kontext firmy
        doc_key: klíč dokumentu

    Returns:
        (final_html, metadata)
    """
    doc_names = {
        "compliance_report": "Compliance Report",
        "action_plan": "Akční plán",
        "ai_register": "Registr AI systémů",
        "training_outline": "Plán školení",
        "chatbot_notices": "Texty oznámení",
        "ai_policy": "Interní AI politika",
        "incident_response_plan": "Plán řízení incidentů",
        "dpia_template": "DPIA/FRIA",
        "vendor_checklist": "Dodavatelský checklist",
        "monitoring_plan": "Monitoring plán",
        "transparency_human_oversight": "Transparentnost a lidský dohled",
        "transparency_page": "Transparenční stránka (HTML)",
        "training_presentation": "Školící prezentace (PPTX obsah)",
    }
    doc_name = doc_names.get(doc_key, doc_key)

    eu_text = _format_critique(eu_critique, "EU AI Act Inspektor")
    client_text = _format_critique(client_critique, "Klient (podnikatel)")

    eu_score = eu_critique.get("skore", 0)
    client_score = client_critique.get("skore", 0)
    eu_findings = len(eu_critique.get("nalezy", []))
    client_findings = len(client_critique.get("nalezy", []))

    prompt = f"""VYLEPŠI NÁSLEDUJÍCÍ DOKUMENT na základě DVOU NEZÁVISLÝCH KRITIK.

══ KONTEXT FIRMY ══
{company_context}

══ DRAFT DOKUMENTU: {doc_name} ══
(EU skóre: {eu_score}/10, {eu_findings} nálezů | Klient skóre: {client_score}/10, {client_findings} nálezů)

{draft_html}

══ KRITIKA #1: EU AI ACT INSPEKTOR ══
(Zaměření: právní přesnost, úplnost, správné citace)

{eu_text}

══ KRITIKA #2: KLIENT / PODNIKATEL ══
(Zaměření: srozumitelnost, praktičnost, personalizace, hodnota)

{client_text}

══ TVŮJ ÚKOL ══
1. Adresuj VŠECHNY kritické a důležité nálezy OBOU kritiků.
2. Zachovej identifikované silné stránky.
3. Přidej chybějící obsah.
4. Odpověz na otázky klienta přímo v textu dokumentu.
5. Nemaž celé sekce — můžeš zkrátit redundance, ale zachovej všechny povinné bloky.
6. Piš přímo HTML — začni <h1>. Žádné komentáře, žádný wrapper.
"""

    # Special output instructions for non-standard document formats
    if doc_key == "transparency_page":
        prompt += """

⚠️ SPECIÁLNÍ INSTRUKCE PRO TRANSPARENČNÍ STRÁNKU:
Tento dokument je STANDALONE HTML stránka (NE PDF obsah).
Zachovej CELOU strukturu: <!-- komentáře -->, <meta> tagy, JSON-LD, CSS, <html>...<\/html>.
NEZAČÍNEJ <h1> — zachovej kompletní HTML od prvního <!-- komentáře --> po poslední </html> tag.
Nemaž meta tagy, JSON-LD data, Dublin Core, Open Graph ani CSS styly.
"""
    elif doc_key == "training_presentation":
        prompt += """

⚠️ SPECIÁLNÍ INSTRUKCE PRO ŠKOLÍCÍ PREZENTACI:
Tento dokument bude automaticky převeden do PowerPoint (PPTX).
Zachovej strukturu: <h1> pro název, <h2> pro každý slide, <ul><li> pro odrážky.
NEMĚŇ formát — pouze vylepši OBSAH slidů.
"""

    label = f"M4_{doc_key}"
    logger.info(f"[M4 Refiner] Finalizuji: {doc_name} "
                f"(draft: {len(draft_html)} znaků, EU: {eu_score}/10, Klient: {client_score}/10)")

    text, meta = await call_gemini(
        system=SYSTEM_PROMPT_M4,
        prompt=prompt,
        label=label,
        temperature=0.15,   # very focused, minimal creativity
        max_tokens=16000,   # must be >= M1 output
    )

    html = extract_html_content(text)

    # Kontrola kvality — finální HTML by měl být >= 50% délky draftu (ochrana proti degradaci)
    if html and len(html) < len(draft_html) * 0.5:
        logger.warning(f"[M4 Refiner] {doc_key}: finální HTML je výrazně kratší než draft "
                      f"({len(html)} vs {len(draft_html)}), zkouším znovu")
        text2, meta2 = await call_gemini(
            system=SYSTEM_PROMPT_M4,
            prompt=prompt + f"""

DŮLEŽITÉ: Tvá předchozí odpověď měla pouze {len(html)} znaků, zatímco draft má {len(draft_html)} znaků.
To je příliš málo — pravděpodobně jsi vynechal celé sekce. Zachovej VŠECHNY povinné sekce a tabulky.
Můžeš zkrátit redundance, ale nemaž celé bloky.
""",
            label=f"{label}_retry",
            temperature=0.2,
            max_tokens=16000,
        )
        html2 = extract_html_content(text2)
        if html2 and len(html2) > len(html):
            html = html2
            meta = meta2

    # Fallback: pokud refine kompletně selže, vrátit draft
    if not html or len(html) < 200:
        logger.error(f"[M4 Refiner] {doc_key}: refine selhal, vracím original draft")
        html = draft_html
        meta["fallback"] = True

    logger.info(f"[M4 Refiner] {doc_key}: finální verze ({len(html)} znaků, "
                f"draft byl {len(draft_html)} znaků, "
                f"{'delší ✓' if len(html) >= len(draft_html) else 'KRATŠÍ ⚠'})")

    return html, meta
