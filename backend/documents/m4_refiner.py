"""
AIshield.cz — Modul 4: REFINER (Claude Opus 4.6)

Přebírá draft z M1 + kritiky z M2 (EU) a M3 (klient),
produkuje FINÁLNÍ verzi HTML dokumentu.

Vstup:  draft_html + eu_critique + client_critique + company_context + doc_key
Výstup: (final_html, metadata)

Model: Claude Opus 4.6 — nejlepší pro koherentní finální dokument (cross-chunk drift prevention).
"""

import logging
import re
from typing import Tuple

from backend.documents.llm_engine import call_claude, extract_html_content

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

PRIORITY PŘI KONFLIKTU KRITIKŮ (ZÁVAZNÉ POŘADÍ):
Pokud se kritiky M2 (EU inspektor) a M3 (klient) vzájemně bijí:
1. PRÁVNÍ PŘESNOST (M2) má ABSOLUTNÍ přednost — právní fakt VŽDY zachovej
2. SROZUMITELNOST (M3) — právní fakt přepiš srozumitelným jazykem dle M3
3. STRUČNOST — preferuj kratší, hustší text. Škrtej redundance a vatu.
4. DÉLKA A OBSÁHLOST — až na posledním místě
Pokud M2 říká „přidej detail" a M3 říká „zkrať" → zachovej právní detail, ale piš stručněji.
Příklad: M2 říká "přidej citaci čl. 50", M3 říká "je to moc právnické" →
Řešení: citaci zachovej, ale vysvětli ji lidsky ("čl. 50 AI Act vyžaduje, abyste...")

KVALITATIVNÍ PRAVIDLA:
- Nesmíš VYNECHAT žádnou povinnou sekci ani tabulku z draftu
- AKTIVNĚ zkracuj redundance, vatu a opakující se formulace
- Preferuj tabulky a seznamy před souvislým textem
- Výsledek SMÍŠ zkrátit oproti draftu, pokud zachováš všechny povinné sekce
- Přidej chybějící obsah identifikovaný kritiky
- Oprav právní nepřesnosti z EU kritiky
- Zlepši srozumitelnost na základě klientské kritiky
- Přidej konkrétní příklady tam kde chybí
- Upřesni personalizaci pro firmu
- Zachovej profesionální ton
- V textu používej české typografické uvozovky: „text“
- NEPOUŽÍVEJ emoji
- AKTIVNĚ zkracuj dokument — cíl je STRUČNOST. Raději 5 silných vět než 20 slabých.
- NIKDY nepřidávej časové termíny nebo ultimáta pro klienta

ZAKÁZÁNO:
- Mazat celé sekce nebo tabulky z draftu
- Přidávat meta-komentáře o editačním procesu
- Měnit fakticky správné informace
- Odstraňovat tabulky nebo strukturované přehledy
- Klišé: „V dnešní digitální době", „Závěrem lze říci"
- Jakékoli časové termíny, ultimáta nebo tlak na klienta („do 30 dní“,
  „do 2 měsíců“, „urgentní“, „zbývá X měsíců“, „firma je v prodlení“).
  Zákonné milníky AI Act uváděj POUZE jako informativní fakta — NIKDY jako tlak
- Zmínky o testech, certifikacích, kvízech
- Anglické nadpisy
- Na transparenční stránce NIKDY nezmiňuj čl. 5 (zakázané praktiky), interní audit, FRIA/DPIA detaily
- Na transparenční stránce NIKDY neuváděj nerealistické počty systémů ani systémy, které nejsou v kontextu
- Transparenční stránka má být pozitivní, vstřícná, srozumitelná běžnému člověku: Executive Summary → Shrnutí, Reporting → Výkaznictví,
  Review → Revize, Checklist → Kontrolní seznam, Scope → Rozsah atd.
  VŠECHNY nadpisy MUSEJÍ být česky. Pokud najdeš anglický nadpis v draftu, přelož ho.
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

    text, meta = await call_claude(
        system=SYSTEM_PROMPT_M4,
        prompt=prompt,
        label=label,
        temperature=0.15,   # very focused, minimal creativity
        max_tokens=10000,   # must be >= M1 output
        model="claude-opus-4-6",
    )

    html = extract_html_content(text)

    # G: Kontrola kvality — délka + sekce (smart retry)
    h2_draft = len(re.findall(r'<h2[^>]*>', draft_html))
    h2_final = len(re.findall(r'<h2[^>]*>', html)) if html else 0
    length_ratio = len(html) / len(draft_html) if html and len(draft_html) > 0 else 0
    section_ratio = h2_final / h2_draft if h2_draft > 0 else 1.0

    # Log quality metrics always
    logger.info(f"[M4 Refiner] {doc_key}: kvalita — "
                f"délka {len(html)}/{len(draft_html)} ({length_ratio:.0%}), "
                f"sekce {h2_final}/{h2_draft} ({section_ratio:.0%})")

    # Smart retry: only if CATASTROPHIC degradation (both dimensions bad)
    # - Length under 60% AND sections under 50% = something went very wrong
    # - Small trims (>80% length) are NEVER retried — Opus may have improved
    catastrophic_length = length_ratio < 0.6
    catastrophic_sections = section_ratio < 0.5
    needs_retry = html and catastrophic_length and catastrophic_sections

    if needs_retry:
        logger.warning(f"[M4 Refiner] {doc_key}: KATASTROFÁLNÍ ztráta obsahu "
                       f"(délka {length_ratio:.0%}, sekce {section_ratio:.0%}) → retry")
        text2, meta2 = await call_claude(
            system=SYSTEM_PROMPT_M4,
            prompt=prompt + f"""

DŮLEŽITÉ: Tvá předchozí odpověď měla pouze {len(html)} znaků a {h2_final} sekcí,
zatímco draft má {len(draft_html)} znaků a {h2_draft} sekcí.
Ztratil jsi příliš mnoho obsahu. Zachovej VŠECHNY povinné sekce a tabulky.
Můžeš zkrátit redundance, ale nemaž celé bloky.
""",
            label=f"{label}_retry",
            temperature=0.2,
            max_tokens=10000,
            model="claude-opus-4-6",
        )
        html2 = extract_html_content(text2)
        if html2 and len(html2) > len(html):
            html = html2
            meta = meta2
            meta["retry_used"] = True
    elif html and (length_ratio < 0.8 or section_ratio < 0.7):
        # Mild degradation — log warning but DON'T retry (Opus decision respected)
        logger.info(f"[M4 Refiner] {doc_key}: mírné zkrácení ({length_ratio:.0%} délka, "
                    f"{section_ratio:.0%} sekce) — Opus rozhodnutí respektováno, BEZ retry")

    # Fallback: pokud refine kompletně selže, vrátit draft
    if not html or len(html) < 200:
        logger.error(f"[M4 Refiner] {doc_key}: refine selhal, vracím original draft")
        html = draft_html
        meta["fallback"] = True
        meta["fallback_reason"] = "M4 output empty or < 200 chars"

    logger.info(f"[M4 Refiner] {doc_key}: finální verze ({len(html)} znaků, "
                f"draft byl {len(draft_html)} znaků, "
                f"{'delší ✓' if len(html) >= len(draft_html) else 'KRATŠÍ ⚠'})")

    return html, meta
