"""
AIshield.cz — Modul 6: POST-M4 VERIFIKACE (Gemini Flash, INFO-ONLY)

Po M4 refinementu zkontroluje finální HTML:
- Zda M4 adresoval nálezy z M2/M3
- Dá finální skóre
- NEBLOKUJE pipeline — jen loguje
- Výsledky předá M5 pro self-improvement

Cena: ~$0.003 per dokument (~$0.03 per generaci)
Model: Gemini 2.0 Flash
"""

import logging
from typing import Tuple, Optional

from backend.documents.llm_engine import (
    call_gemini, parse_json,
    GEMINI_FLASH_MODEL, GEMINI_FLASH_COST_INPUT, GEMINI_FLASH_COST_OUTPUT,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_M6 = """Jsi kontrolor kvality dokumentu AI Act Compliance Kit.
Tvůj úkol: Zkontrolovat FINÁLNÍ verzi dokumentu (po všech úpravách) a ohodnotit ji.

Dostaneš:
1. Finální HTML dokumentu
2. Nálezy z M2 (EU inspektora) a M3 (klientského kritika) na DRAFT verzi
3. Kontext firmy

Tvůj úkol:
- Zkontroluj, zda finální verze ADRESOVALA nálezy z M2/M3
- Dej finální skóre 1-10
- Identifikuj případné PŘETRVÁVAJÍCÍ problémy

NEBUĎ přísný — hledáš jen závažné problémy, které M4 NEOPRAVIL.
Odpovídej POUZE v JSON formátu."""

PROMPT_TEMPLATE = """FINÁLNÍ HTML DOKUMENTU ({doc_name}):
{final_html_preview}

NÁLEZY M2 (EU Inspector) NA DRAFT:
{eu_findings}

NÁLEZY M3 (Client Critic) NA DRAFT:
{client_findings}

KONTEXT FIRMY (zkrácený):
{company_context_short}

Odpověz POUZE tímto JSON:
{{
  "finalni_skore": <1-10>,
  "adrresovane_nalezy": <počet nálezů z M2/M3 které M4 opravil>,
  "celkem_nalezu": <celkový počet nálezů M2+M3>,
  "pretrvavajici_problemy": [
    {{"oblast": "...", "popis": "...", "zavaznost": "kriticka|dulezita|kosmeticka"}}
  ],
  "celkove_hodnoceni": "vynikající|dobré|průměrné|nedostatečné",
  "poznamka": "1-2 věty shrnutí"
}}"""


async def post_m4_check(
    final_html: str,
    eu_critique: dict,
    client_critique: dict,
    company_context: str,
    doc_key: str,
    doc_name: str = "",
) -> Tuple[Optional[dict], dict]:
    """
    INFO-ONLY post-M4 verifikace přes Gemini Flash.
    
    Returns:
        (check_result, metadata) — check_result je dict s nálezem nebo None při chybě.
        Metadata vždy obsahuje cost_usd a tokens.
    """
    if not doc_name:
        doc_name = doc_key
    
    # Zkrátit HTML pro levný review (prvních 6000 znaků + posledních 2000)
    if len(final_html) > 10000:
        html_preview = final_html[:6000] + "\n\n[...ZKRÁCENO...]\n\n" + final_html[-2000:]
    else:
        html_preview = final_html
    
    # Formátovat nálezy M2/M3
    eu_findings_text = _format_findings(eu_critique, "M2")
    client_findings_text = _format_findings(client_critique, "M3")
    
    # Zkrátit kontext
    ctx_short = company_context[:1500] if len(company_context) > 1500 else company_context
    
    prompt = PROMPT_TEMPLATE.format(
        doc_name=doc_name,
        final_html_preview=html_preview,
        eu_findings=eu_findings_text,
        client_findings=client_findings_text,
        company_context_short=ctx_short,
    )
    
    label = f"M6_{doc_key}"
    
    try:
        text, meta = await call_gemini(
            system=SYSTEM_PROMPT_M6,
            prompt=prompt,
            label=label,
            temperature=0.1,
            max_tokens=2000,
            model=GEMINI_FLASH_MODEL,
            cost_input=GEMINI_FLASH_COST_INPUT,
            cost_output=GEMINI_FLASH_COST_OUTPUT,
        )
        
        result = parse_json(text)
        if not result:
            logger.warning(f"[M6 PostCheck] {doc_key}: JSON parsing selhal")
            result = {
                "finalni_skore": None,
                "poznamka": f"JSON parsing selhal. Raw: {text[:200]}",
            }
        
        score = result.get("finalni_skore", "?")
        hodnoceni = result.get("celkove_hodnoceni", "?")
        addressed = result.get("adrresovane_nalezy", "?")
        total = result.get("celkem_nalezu", "?")
        remaining = len(result.get("pretrvavajici_problemy", []))
        
        logger.info(f"[M6 PostCheck] {doc_name}: skóre={score}/10, "
                    f"hodnocení={hodnoceni}, "
                    f"adresováno={addressed}/{total} nálezů, "
                    f"přetrvává={remaining} problémů, "
                    f"${meta.get('cost_usd', 0):.4f}")
        
        return result, meta
        
    except Exception as e:
        logger.warning(f"[M6 PostCheck] {doc_key}: CHYBA (nekritická): {e}")
        return None, {"cost_usd": 0, "input_tokens": 0, "output_tokens": 0}


def _format_findings(critique: dict, source: str) -> str:
    """Formátuje nálezy z M2/M3 pro M6 prompt."""
    if not critique:
        return f"{source}: žádné nálezy (přeskočeno)"
    
    findings = critique.get("nalezy", [])
    if not findings:
        score = critique.get("skore", "?")
        return f"{source}: skóre {score}/10, žádné specifické nálezy"
    
    lines = [f"{source} (skóre {critique.get('skore', '?')}/10):"]
    for f in findings[:8]:  # max 8 nálezů
        sev = f.get("zavaznost", "?")
        area = f.get("oblast", "?")
        desc = f.get("popis", "?")[:150]
        lines.append(f"  [{sev}] {area}: {desc}")
    
    if len(findings) > 8:
        lines.append(f"  ... a dalších {len(findings) - 8} nálezů")
    
    return "\n".join(lines)
