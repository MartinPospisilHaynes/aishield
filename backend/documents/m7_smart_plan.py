"""
AIshield.cz — Modul 7: SMART AKČNÍ PLÁN (Gemini Flash)

Přepisuje hardcoded doporučení z dotazníku a skenu
do srozumitelné češtiny pomocí LLM.

Vstup:  questionnaire_findings + scan_findings + firma info
Výstup: dict[question_key → srozumitelný text akčního bodu]

Model: Gemini (přes call_gemini z llm_engine — retry + fallback)
Cache: companies.smart_plan_cache (JSON) — regeneruje se jen při změně dotazníku
"""

import hashlib
import json
import logging
from typing import Optional

from backend.documents.llm_engine import call_gemini

logger = logging.getLogger(__name__)

# Maximální stáří cache (hodiny) — po této době se vždy regeneruje
CACHE_MAX_AGE_HOURS = 168  # 7 dní

SYSTEM_PROMPT = """Jsi přátelský AI compliance poradce pro české firmy.
Tvůj úkol: přepsat suchá právnická doporučení do srozumitelných, konkrétních kroků.

PRAVIDLA:
- Piš jako bys radil kamarádovi podnikateli, který nerozumí paragrafům.
- Každý krok musí říkat CO udělat, KDO to má udělat, a JAK prakticky.
- Místo „zajistěte transparentnost dle čl. 50" napiš „přidejte k chatbotu text: Tento chat je provozován umělou inteligencí".
- Místo „proveďte conformity assessment" napiš „udělejte si kontrolní seznam, jestli váš AI systém splňuje požadavky EU".
- Žádné zkratky (DPA, DPIA, SCC) bez vysvětlení.
- Žádné právnické klišé. Přímý, jasný jazyk.
- Zachovej věcnou správnost — neodstraňuj informace, jen je přeformuluj.
- U každého kroku zachovej zmínku o relevantním článku AI Act,
  ale přirozeně v textu, ne jako suchý odkaz.
- Pokud je zmíněn konkrétní nástroj (Smartsupp, ChatGPT apod.), zakomponuj ho do rady.
- Odpovídej VÝHRADNĚ v češtině.

FORMÁT ODPOVĚDI — striktní JSON:
{
  "items": [
    {
      "key": "question_key_zde",
      "action": "Srozumitelný popis co firma má udělat — 2-4 věty."
    }
  ]
}

BEZ jakéhokoliv textu před nebo za JSON blokem. Jen čistý JSON."""


async def generate_smart_plan(
    questionnaire_findings: list[dict],
    scan_findings: list[dict],
    company_name: str = "",
    company_url: str = "",
) -> dict[str, str]:
    """
    Zavolá Gemini a vrátí dict: question_key → srozumitelný akční text.
    Pokud LLM selže, vrátí prázdný dict (= fallback na původní texty).
    """
    if not questionnaire_findings and not scan_findings:
        return {}

    # Sestavit kontext pro LLM
    firma_info = ""
    if company_name:
        firma_info += f"Firma: {company_name}\n"
    if company_url:
        firma_info += f"Web: {company_url}\n"

    items_text = ""
    for f in questionnaire_findings:
        key = f.get("question_key", "")
        original = f.get("action_required", "")
        tool = f.get("name", "")
        risk = f.get("risk_level", "")
        article = f.get("ai_act_article", "")
        items_text += (
            f"---\n"
            f"key: {key}\n"
            f"nástroj: {tool}\n"
            f"riziko: {risk}\n"
            f"článek: {article}\n"
            f"původní text: {original}\n"
        )

    for f in scan_findings:
        name = f.get("name", "")
        risk = f.get("risk_level", "")
        action = f.get("action_required", "")
        article = f.get("ai_act_article", "")
        items_text += (
            f"---\n"
            f"key: scan-{name}\n"
            f"nástroj: {name}\n"
            f"riziko: {risk}\n"
            f"článek: {article}\n"
            f"původní text: {action}\n"
        )

    prompt = f"""{firma_info}
Níže jsou doporučení z compliance analýzy. Přepiš KAŽDÉ z nich do srozumitelné češtiny.
Pro každou položku vrať přepsaný text v JSON formátu.

POLOŽKY K PŘEPSÁNÍ:
{items_text}"""

    try:
        text, meta = await call_gemini(
            system=SYSTEM_PROMPT,
            prompt=prompt,
            label="m7_smart_plan",
            temperature=0.3,
            max_tokens=4000,
        )

        logger.info(
            "[M7] Smart plan vygenerován: %d znaků, $%.4f",
            len(text), meta.get("cost_usd", 0),
        )

        # Parsovat JSON odpověď
        parsed = _parse_response(text)
        return parsed

    except Exception as e:
        logger.error("[M7] Generování smart plánu selhalo: %s", e)
        return {}


def _parse_response(text: str) -> dict[str, str]:
    """Parsuje JSON odpověď z LLM. Vrací dict key→action."""
    # Vyčistit markdown code block pokud přítomen
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Odstraň první a poslední řádek (```json a ```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Zkusit najít JSON v textu
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                data = json.loads(cleaned[start:end])
            except json.JSONDecodeError:
                logger.warning("[M7] Nepodařilo se parsovat JSON odpověď")
                return {}
        else:
            return {}

    result = {}
    items = data.get("items", [])
    for item in items:
        key = item.get("key", "")
        action = item.get("action", "")
        if key and action:
            result[key] = action
    return result


def compute_findings_hash(
    questionnaire_findings: list[dict],
    scan_findings: list[dict],
) -> str:
    """Spočítá hash z findings pro detekci změn (cache invalidace)."""
    parts = []
    for f in sorted(questionnaire_findings, key=lambda x: x.get("question_key", "")):
        parts.append(f"{f.get('question_key', '')}:{f.get('action_required', '')}")
    for f in sorted(scan_findings, key=lambda x: x.get("name", "")):
        parts.append(f"scan:{f.get('name', '')}:{f.get('action_required', '')}")
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


async def get_or_generate_smart_plan(
    supabase,
    company_id: str,
    questionnaire_findings: list[dict],
    scan_findings: list[dict],
    company_name: str = "",
    company_url: str = "",
) -> dict[str, str]:
    """
    Hlavní vstupní bod — vrátí smart plán z cache nebo nový.

    1. Spočítá hash z findings
    2. Pokud v companies.smart_plan_cache existuje a hash sedí → vrátí cache
    3. Jinak zavolá generate_smart_plan() a uloží do cache
    4. Pokud LLM selže → vrátí {} (dashboard použije původní texty)
    """
    current_hash = compute_findings_hash(questionnaire_findings, scan_findings)

    # Zkusit načíst cache
    try:
        cache_res = supabase.table("companies").select(
            "smart_plan_cache"
        ).eq("id", company_id).execute()

        if cache_res.data:
            cache_raw = cache_res.data[0].get("smart_plan_cache")
            if cache_raw:
                cache = cache_raw if isinstance(cache_raw, dict) else json.loads(cache_raw)
                if cache.get("hash") == current_hash and cache.get("items"):
                    logger.info("[M7] Cache hit pro company %s", company_id[:8])
                    return cache["items"]
    except Exception as e:
        logger.warning("[M7] Cache read failed: %s", e)

    # Generovat nový smart plán
    logger.info("[M7] Generuji smart plán pro company %s (%d q-findings, %d s-findings)",
                company_id[:8], len(questionnaire_findings), len(scan_findings))

    items = await generate_smart_plan(
        questionnaire_findings=questionnaire_findings,
        scan_findings=scan_findings,
        company_name=company_name,
        company_url=company_url,
    )

    if not items:
        logger.warning("[M7] LLM vrátil prázdný výsledek — fallback na původní texty")
        return {}

    # Uložit do cache
    cache_data = {
        "hash": current_hash,
        "items": items,
    }
    try:
        supabase.table("companies").update({
            "smart_plan_cache": json.dumps(cache_data, ensure_ascii=False),
        }).eq("id", company_id).execute()
        logger.info("[M7] Cache uložena pro company %s (%d položek)", company_id[:8], len(items))
    except Exception as e:
        logger.warning("[M7] Cache save failed: %s", e)

    return items
