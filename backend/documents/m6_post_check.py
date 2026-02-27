"""
AIshield.cz — Modul 6: POST-M4 VERIFIKACE (Gemini 3.1 Pro)

Po M4 refinementu zkontroluje finální HTML:
- Zda M4 adresoval nálezy z M2/M3
- Dá finální skóre
- Pokud skóre < 8, AKTIVUJE double M4 loop (M4b re-refinement)
- Výsledky předá M5 pro self-improvement

Gen22+ vylepšení:
- json_mode=True (response_mime_type=application/json)
- Retry s explicitním JSON-only promptem při parse failure
- Raw response logging při failure
- Confidence flag (high/medium/low) na základě parse metody
- Suspicious flag pokud M6 odchylka > 3 od M2+M3 průměru

Cena: ~$0.02 per dokument
Model: Gemini 3.1 Pro — přesné hodnocení pro double M4 loop
"""

import logging
import os
import re
from datetime import datetime, timezone
from typing import Tuple, Optional

from backend.documents.llm_engine import (
    call_gemini, parse_json,
)

logger = logging.getLogger(__name__)

# Složka pro raw M6 responses (debugging)
M6_RAW_DIR = "/opt/aishield/logs/m6_raw"

SYSTEM_PROMPT_M6 = """Jsi kontrolor kvality dokumentu AI Act Compliance Kit.
Tvůj úkol: Zkontrolovat FINÁLNÍ verzi dokumentu a spravedlivě ji ohodnotit.

Dostaneš:
1. Finální HTML dokumentu (po M4 refinementu)
2. Nálezy z M2 (EU inspektora) a M3 (klientského kritika) na DRAFT verzi
3. Kontext firmy

Tvůj úkol:
- Zkontroluj, zda finální verze ADRESOVALA nálezy z M2/M3
- Dej finální skóre 1-10
- Identifikuj PŘETRVÁVAJÍCÍ problémy (pouze ty, co M4 skutečně NEOPRAVIL)

KALIBRACE:
- 8-9: Dokument adresoval většinu nálezů, je kvalitní a použitelný. STANDARDNÍ SKÓRE pro dobrou práci.
- 7: Některé nálezy přetrvávají ale celek je solidní.
- 5-6: M4 neadresoval klíčové problémy.
- Pokud M4 opravil kritické a důležité nálezy, dej MINIMÁLNĚ 8 i když menší nálezy přetrvávají.

DŮLEŽITÉ: Tvé skóre rozhoduje, zda se spustí další kolo refinementu.
Skóre < 8 → dokument bude znovu opraven. Buď přesný ale SPRAVEDLIVÝ.
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

RETRY_PROMPT = """Tvá předchozí odpověď nebyla validní JSON. Odpověz ZNOVU, tentokrát POUZE validní JSON:
{{
  "finalni_skore": <1-10>,
  "adrresovane_nalezy": <počet>,
  "celkem_nalezu": <počet>,
  "pretrvavajici_problemy": [],
  "celkove_hodnoceni": "vynikající|dobré|průměrné|nedostatečné",
  "poznamka": "shrnutí"
}}

Předchozí raw výstup (pro kontext):
{raw_text_preview}"""


def _save_raw_response(doc_key: str, text: str, attempt: int = 1):
    """Uloží raw Gemini response do souboru pro post-mortem analýzu."""
    try:
        os.makedirs(M6_RAW_DIR, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        fpath = os.path.join(M6_RAW_DIR, f"{doc_key}_{ts}_attempt{attempt}.txt")
        with open(fpath, "w") as f:
            f.write(f"doc_key: {doc_key}\nattempt: {attempt}\nlen: {len(text)}\n\n{text}")
        logger.info(f"[M6 PostCheck] Raw response saved: {fpath} ({len(text)} chars)")
    except Exception as e:
        logger.warning(f"[M6 PostCheck] Cannot save raw response: {e}")


async def post_m4_check(
    final_html: str,
    eu_critique: dict,
    client_critique: dict,
    company_context: str,
    doc_key: str,
    doc_name: str = "",
) -> Tuple[Optional[dict], dict]:
    """
    Post-M4 verifikace přes Gemini.
    
    Vylepšení Gen22+:
    - json_mode=True (response_mime_type=application/json)
    - Retry s explicitním JSON-only promptem při parse failure
    - Raw response logging při failure
    - Confidence flag (high/medium/low) na základě parse metody
    - Suspicious flag pokud M6 odchylka > 3 od M2+M3 průměru
    
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
    total_cost = 0
    total_in_tok = 0
    total_out_tok = 0
    
    try:
        # ── Pokus 1: Standardní volání s json_mode ──
        text, meta = await call_gemini(
            system=SYSTEM_PROMPT_M6,
            prompt=prompt,
            label=label,
            temperature=0.1,
            max_tokens=2000,
            json_mode=True,
        )
        total_cost += meta.get("cost_usd", 0)
        total_in_tok += meta.get("input_tokens", 0)
        total_out_tok += meta.get("output_tokens", 0)
        
        result = parse_json(text)
        
        # ── Pokus 2: Retry s explicitním JSON promptem ──
        if not result:
            logger.warning(
                f"[M6 PostCheck] {doc_key}: JSON parse failure (attempt 1, {len(text)} chars). Retrying..."
            )
            _save_raw_response(doc_key, text, attempt=1)
            
            retry_prompt = RETRY_PROMPT.format(raw_text_preview=text[:500])
            text2, meta2 = await call_gemini(
                system=SYSTEM_PROMPT_M6,
                prompt=retry_prompt,
                label=f"{label}_retry",
                temperature=0.0,
                max_tokens=1000,
                json_mode=True,
            )
            total_cost += meta2.get("cost_usd", 0)
            total_in_tok += meta2.get("input_tokens", 0)
            total_out_tok += meta2.get("output_tokens", 0)
            
            result = parse_json(text2)
            if result:
                logger.info(f"[M6 PostCheck] {doc_key}: JSON retry SUCCESSFUL")
                result["m6_confidence"] = "medium"
                result["m6_parse_method"] = "json_retry"
            else:
                _save_raw_response(doc_key, text2, attempt=2)
        else:
            result["m6_confidence"] = "high"
            result["m6_parse_method"] = "json_direct"
        
        # ── Pokus 3: Regex fallback (confidence=low) ──
        if not result:
            score_match = re.search(r'"finalni_skore"\s*:\s*(\d+)', text)
            if not score_match:
                # Zkusit i ve druhém pokusu
                score_match = re.search(r'"finalni_skore"\s*:\s*(\d+)', text2)
            
            if score_match:
                extracted_score = int(score_match.group(1))
                logger.warning(
                    f"[M6 PostCheck] {doc_key}: JSON parse failed 2x, "
                    f"regex extracted score={extracted_score} (CONFIDENCE=LOW)"
                )
                result = {
                    "finalni_skore": extracted_score,
                    "m6_confidence": "low",
                    "m6_parse_method": "regex_fallback",
                    "poznamka": f"Score extrahován regex fallbackem po 2 pokusech. "
                                f"Raw len={len(text)}+{len(text2)}",
                }
            else:
                logger.warning(f"[M6 PostCheck] {doc_key}: JSON + regex failed → score=None")
                result = {
                    "finalni_skore": None,
                    "m6_confidence": "none",
                    "m6_parse_method": "failed",
                    "poznamka": f"Všechny pokusy selhaly. Raw len={len(text)}",
                }
        
        # ── Dual-score validace: porovnej M6 vs M2+M3 průměr ──
        m6_score = result.get("finalni_skore")
        eu_score = eu_critique.get("skore") if isinstance(eu_critique, dict) else None
        client_score = client_critique.get("skore") if isinstance(client_critique, dict) else None
        
        if m6_score is not None and eu_score is not None and client_score is not None:
            try:
                m2m3_avg = (float(eu_score) + float(client_score)) / 2
                deviation = abs(float(m6_score) - m2m3_avg)
                if deviation > 3:
                    result["m6_suspicious"] = True
                    result["m6_deviation"] = round(deviation, 1)
                    logger.warning(
                        f"[M6 PostCheck] {doc_key}: SUSPICIOUS — M6={m6_score} vs "
                        f"M2+M3 avg={m2m3_avg:.1f} (odchylka {deviation:.1f} > 3)"
                    )
            except (ValueError, TypeError):
                pass
        
        # ── Logování výsledku ──
        score = result.get("finalni_skore", "?")
        hodnoceni = result.get("celkove_hodnoceni", "?")
        addressed = result.get("adrresovane_nalezy", "?")
        total_findings = result.get("celkem_nalezu", "?")
        remaining = len(result.get("pretrvavajici_problemy", []))
        confidence = result.get("m6_confidence", "?")
        
        logger.info(f"[M6 PostCheck] {doc_name}: skóre={score}/10, "
                    f"hodnocení={hodnoceni}, "
                    f"adresováno={addressed}/{total_findings} nálezů, "
                    f"přetrvává={remaining} problémů, "
                    f"confidence={confidence}, "
                    f"${total_cost:.4f}")
        
        final_meta = {
            "provider": "gemini",
            "cost_usd": total_cost,
            "input_tokens": total_in_tok,
            "output_tokens": total_out_tok,
        }
        return result, final_meta
        
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
