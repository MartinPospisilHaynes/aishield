"""
AIshield.cz — AI Classifier (Claude API)

Ověřuje nálezy z detektoru pomocí Claude AI:
1. Potvrdí/vyvrátí, zda je AI systém skutečně NASAZENÝ na webu
2. Zpřesní klasifikaci rizika podle AI Act
3. Vygeneruje doporučení v češtině

Fallback v2: pokud API selže → inteligentní degradace (jen high-confidence findings),
nikdy „vše deployed=true".
"""

import json
import logging
import re
import time
from dataclasses import dataclass, asdict

import anthropic

from backend.config import get_settings
from backend.scanner.detector import DetectedAI
from backend.monitoring.engine_health import engine_monitor
from backend.ai_engine.llm_client import llm_complete
from backend.ai_engine.rag import enrich_prompt_with_rag

logger = logging.getLogger(__name__)

# ── Retry konfigurace ──
MAX_RETRIES = 3
RETRY_DELAYS = [1.0, 3.0, 9.0]  # Exponential backoff

# ── Confidence threshold pro inteligentní fallback ──
FALLBACK_CONFIDENCE_THRESHOLD = 0.80

# ── Cena za token (Claude 3.5 Haiku, USD) ──
COST_PER_INPUT_TOKEN = 0.80 / 1_000_000   # $0.80 / 1M
COST_PER_OUTPUT_TOKEN = 4.00 / 1_000_000   # $4.00 / 1M

SYSTEM_PROMPT = """Jsi expert na EU AI Act (Nařízení EU 2024/1689) a webovou analytiku.

Dostaneš seznam AI systémů, které automatický skener detekoval na webové stránce.
Skener hledá signatury (textové vzory) v HTML, skriptech, cookies a síťových požadavcích.

Tvůj úkol:
1. Pro KAŽDÝ nález rozhodni, zda je AI systém skutečně NASAZENÝ na webu (deployed=true),
   nebo je to jen ZMÍNKA v textu (deployed=false). Například e-shop může mít v patičce
   odkaz "porovnání chatbotů" — to neznamená, že chatbot používá.

   DŮLEŽITÉ PRO DEPLOYED=FALSE:
   - Pokud je nález jen textová zmínka názvu produktu/platformy BEZ aktivního nasazení → deployed=false
   - Pokud je nález jen v obsahu blogu, popisu, článku, patičce, nebo seznamu partnerů → deployed=false
   - Pokud není jasný důkaz o aktivním skriptu, API volání nebo běžícím widgetu → deployed=false
   - Raději označ jako deployed=false než jako deployed=true s "Nízké riziko / Pouze zmínka"
   - NIKDY neoznačuj jako deployed=true s popisem typu "pouze zmínka" nebo "ne nasazený" — to je logický rozpor

   NÁSTROJE, KTERÉ NEJSOU AI SYSTÉMY — VŽDY deployed=false:
   - Google Tag Manager (GTM) — je to jen kontejner na tagy, sám o sobě NENÍ AI systém
   - Google Analytics 4 (GA4) — standardní webová analytika, NENÍ AI systém (pokud nemá aktivní Predictive Audiences)
   - Seznam Retargeting, Sklik — běžný retargeting, NENÍ AI systém
   - Heureka — e-commerce tracking, NENÍ AI systém
   - Základní tracking pixely (bez AI funkcí) — NEJSOU AI systémy
   Tyto nástroje NIKDY neoznačuj jako deployed=true, protože by to vytvořilo falešně pozitivní nález.

2. Pro nasazené systémy upřesni:
   - risk_level: "minimal", "limited", "high" nebo "unacceptable" podle AI Act
   - ai_act_article: konkrétní článek/odstavec AI Act
   - action_required: stručné doporučení česky (1-2 věty)
   - description_cs: popis systému a jeho AI funkcí česky (1-2 věty)
   - confidence: 0.0 - 1.0 (jak jsi si jistý)

3. Pokud najdeš AI systém, který skener neodhalil, přidej ho s deployed=true.

DŮLEŽITÉ:
- Piš ČESKY (doporučení, popisy)
- Buď stručný a přesný
- U chatbotů: čl. 50 odst. 1 AI Act (povinnost informovat, že uživatel komunikuje s AI)
- U generátorů obsahu: čl. 50 odst. 2 (povinnost označit syntetický obsah)
- U doporučovacích systémů: čl. 50 odst. 1 pokud personalizované
- Analytické nástroje (GA4, GTM, pixely) NEJSOU AI systémy dle AI Act — označ jako deployed=false
- Vrať POUZE validní JSON pole

SPECIÁLNÍ PŘÍPAD — AI TRANSPARENCY NOTICE:
Pokud skener nalezl "AI Transparency Notice" (transparenční oznámení o AI), znamená to, že web
UŽ AKTIVNĚ INFORMUJE návštěvníky o používání AI. Toto je POZITIVNÍ zjištění — web JIŽ SPLŇUJE
transparenční povinnost dle čl. 50 AI Act.
- deployed=true (oznámení je skutečně nasazené na webu)
- risk_level="limited" (transparenční povinnost = omezené riziko, ale JE SPLNĚNA)
- action_required: Napiš že web UŽ SPLŇUJE tuto povinnost. NIKDY nepíš "informujte návštěvníky"
  nebo "stačí informovat" — protože detekované oznámení JE ta informace pro návštěvníky!
  Příklad: "✅ Váš web již splňuje čl. 50 AI Act — transparenční oznámení o AI je na místě."
- description_cs: Popiš co oznámení dělá (informuje návštěvníky o použití AI na webu)
- confidence: 0.90"""

USER_PROMPT_TEMPLATE = """Analyzovaný web: {url}

Automatický skener nalezl tyto AI systémy:

{findings_json}

Vrať JSON pole objektů s touto strukturou:
[
  {{
    "name": "název systému",
    "deployed": true/false,
    "category": "chatbot|analytics|recommender|content_gen|other",
    "risk_level": "minimal|limited|high|unacceptable",
    "ai_act_article": "čl. XX odst. Y",
    "action_required": "doporučení česky",
    "description_cs": "popis česky",
    "confidence": 0.85,
    "reason": "proč deployed/ne-deployed (česky, 1 věta)"
  }}
]

Vrať POUZE JSON pole, žádný další text."""


@dataclass
class ClassifiedFinding:
    """Výsledek AI klasifikace jednoho nálezu."""
    name: str
    deployed: bool
    category: str
    risk_level: str
    ai_act_article: str
    action_required: str
    description_cs: str
    confidence: float
    reason: str
    # Zachováme originální data z detektoru
    matched_signatures: list[str]
    evidence: list[str]


class AIClassifier:
    """
    Klasifikátor nálezů pomocí Claude API.
    Ověřuje, zda jsou nalezené AI systémy skutečně nasazené.
    """

    def __init__(self, api_key: str | None = None, model: str = "claude-opus-4-6"):
        settings = get_settings()
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model
        self.enabled = bool(self.api_key)
        self._usage = {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}

        if self.enabled:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            logger.info(f"[Classifier] Claude API aktivní (model: {self.model})")
        else:
            self.client = None
            logger.warning("[Classifier] ANTHROPIC_API_KEY není nastaven — fallback na rule-based")

    @property
    def usage(self) -> dict:
        """Vrátí statistiky použití API."""
        return self._usage.copy()

    async def classify(
        self, url: str, findings: list[DetectedAI]
    ) -> list[ClassifiedFinding]:
        """
        Klasifikuje nálezy pomocí LLM (Claude → Gemini fallback).
        Pokud oba provideři selžou, vrátí INTELIGENTNÍ fallback
        (jen high-confidence findings, nikdy „vše deployed=true").
        """
        if not self.enabled or not findings:
            return self._intelligent_fallback(findings, reason="API key not configured")

        try:
            return await self._claude_classify(url, findings)
        except Exception as e:
            logger.error(f"[Classifier] LLM klasifikace selhala (oba provideři): {e}")
            await engine_monitor.report_error(
                "llm_classification_failed", scan_id=None, url=url,
                details=str(e)[:500],
            )
            return self._intelligent_fallback(findings, reason=f"LLM failed: {e}")

    async def _claude_classify(
        self, url: str, findings: list[DetectedAI]
    ) -> list[ClassifiedFinding]:
        """Zavolá LLM API pro klasifikaci (Claude → Gemini fallback)."""

        # Připravíme zjednodušený JSON pro Claude
        findings_for_claude = []
        for f in findings:
            # Sanitize evidence — ochrana proti indirect prompt injection
            from backend.security.prompt_guard import sanitize_scanned_content
            sanitized_evidence = [
                sanitize_scanned_content(e, max_length=500) for e in f.evidence[:5]
            ]
            findings_for_claude.append({
                "name": f.name,
                "category": f.category,
                "risk_level": f.risk_level,
                "matched_signatures": f.matched_signatures[:5],
                "evidence": sanitized_evidence,
                "confidence": f.confidence,
            })

        user_message = USER_PROMPT_TEMPLATE.format(
            url=url,
            findings_json=json.dumps(findings_for_claude, ensure_ascii=False, indent=2),
        )

        logger.info(f"[Classifier] Posílám {len(findings)} nálezů do LLM (Claude → Gemini fallback)")

        # Obohatíme systémový prompt o relevantní články AI Act (RAG)
        rag_query = f"AI systémy na webu {url}: " + ", ".join(
            f.name for f in findings[:10]
        )
        enriched_system_prompt = await enrich_prompt_with_rag(
            SYSTEM_PROMPT, rag_query, top_k=5, threshold=0.40,
        )

        # Volání přes LLM wrapper s automatickým fallback
        result = await llm_complete(
            system=enriched_system_prompt,
            user=user_message,
            max_tokens=2048,
            model=self.model,
        )

        # Statistiky
        self._usage["input_tokens"] += result.input_tokens
        self._usage["output_tokens"] += result.output_tokens
        self._usage["cost_usd"] += result.cost_usd

        provider_info = f"{result.provider}/{result.model}"
        if result.fallback_used:
            provider_info += f" (fallback: {result.fallback_reason[:80]})"

        logger.info(
            f"[Classifier] {provider_info} odpověděl: "
            f"{result.input_tokens} input + {result.output_tokens} output tokens, "
            f"cena: ${result.cost_usd:.4f}"
        )

        # Parsování odpovědi — ROBUSTNÍ (řeší code fences, text kolem JSON, atd.)
        raw_text = result.text
        classified_data = self._robust_json_parse(raw_text)

        # Namapujeme zpět na ClassifiedFinding
        # Potřebujeme zachovat original evidence/signatures
        findings_by_name = {f.name.lower(): f for f in findings}

        results: list[ClassifiedFinding] = []
        for item in classified_data:
            name_lower = item["name"].lower()
            original = findings_by_name.get(name_lower)

            results.append(ClassifiedFinding(
                name=item["name"],
                deployed=item.get("deployed", True),
                category=item.get("category", "other"),
                risk_level=item.get("risk_level", "minimal"),
                ai_act_article=item.get("ai_act_article", ""),
                action_required=item.get("action_required", ""),
                description_cs=item.get("description_cs", ""),
                confidence=item.get("confidence", 0.5),
                reason=item.get("reason", ""),
                matched_signatures=original.matched_signatures if original else [],
                evidence=original.evidence if original else [],
            ))

        deployed_count = sum(1 for r in results if r.deployed)
        logger.info(
            f"[Classifier] Výsledek: {deployed_count}/{len(results)} skutečně nasazených"
        )

        return results

    def _robust_json_parse(self, raw_text: str) -> list[dict]:
        """
        Robustní JSON parsing — zvládne:
        1. Čistý JSON
        2. JSON v markdown code fences (```json ... ```)
        3. JSON array schovaný v konverzačním textu
        4. Neplatné JSON → exception (chytá se výše)
        """
        text = raw_text.strip()

        # 1. Odstraň markdown code fences
        if "```" in text:
            # Najdi obsah mezi prvním ``` a posledním ```
            fence_pattern = r'```(?:json)?\s*\n?(.*?)```'
            fence_match = re.search(fence_pattern, text, re.DOTALL)
            if fence_match:
                text = fence_match.group(1).strip()

        # 2. Zkus přímo parsovat
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return data
            # Pokud Claude vrátil dict místo array
            if isinstance(data, dict):
                return [data]
        except json.JSONDecodeError:
            pass

        # 3. Regex extraction — najdi JSON array v textu
        array_match = re.search(r'\[[\s\S]*\]', text)
        if array_match:
            try:
                data = json.loads(array_match.group())
                if isinstance(data, list):
                    logger.info("[Classifier] JSON extracted via regex from text")
                    return data
            except json.JSONDecodeError:
                pass

        # 4. Nic nefungovalo → raise
        raise json.JSONDecodeError(
            f"Cannot parse Claude response as JSON. Raw text: {raw_text[:200]}...",
            raw_text, 0
        )

    def _intelligent_fallback(
        self, findings: list[DetectedAI], reason: str = ""
    ) -> list[ClassifiedFinding]:
        """
        INTELIGENTNÍ fallback — NIKDY neoznačí „vše deployed=true".
        
        Logika:
        - High-confidence findings (≥0.80) → deployed=true (pravděpodobně reálné)
        - Low-confidence findings (<0.80) → deployed=false (pravděpodobně false-positives)
        - Vše se označí jako „⚠️ neověřeno AI klasifikátorem"
        """
        logger.warning(
            f"[Classifier] INTELIGENTNÍ FALLBACK: {len(findings)} findings, "
            f"threshold={FALLBACK_CONFIDENCE_THRESHOLD}, reason={reason}"
        )

        results = []
        deployed_count = 0
        fp_count = 0

        for f in findings:
            is_deployed = f.confidence >= FALLBACK_CONFIDENCE_THRESHOLD
            if is_deployed:
                deployed_count += 1
            else:
                fp_count += 1

            results.append(ClassifiedFinding(
                name=f.name,
                deployed=is_deployed,
                category=f.category,
                risk_level=f.risk_level if is_deployed else "none",
                ai_act_article=f.ai_act_article if is_deployed else "",
                action_required=f.action_required if is_deployed else
                    f"Nízká confidence ({f.confidence:.0%}) — pravděpodobně false positive.",
                description_cs=f.description_cs,
                confidence=f.confidence,
                reason=f"⚠️ AI klasifikace selhala ({reason}). "
                       f"{'Ponecháno' if is_deployed else 'Vyřazeno'} "
                       f"na základě confidence={f.confidence:.2f} "
                       f"(threshold={FALLBACK_CONFIDENCE_THRESHOLD}).",
                matched_signatures=f.matched_signatures,
                evidence=f.evidence,
            ))

        logger.warning(
            f"[Classifier] Fallback result: {deployed_count} deployed, {fp_count} false-positives"
        )
        return results
