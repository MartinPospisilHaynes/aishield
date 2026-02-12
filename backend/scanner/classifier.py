"""
AIshield.cz — AI Classifier (Claude API)

Ověřuje nálezy z detektoru pomocí Claude AI:
1. Potvrdí/vyvrátí, zda je AI systém skutečně NASAZENÝ na webu
2. Zpřesní klasifikaci rizika podle AI Act
3. Vygeneruje doporučení v češtině

Fallback: pokud API klíč není nastaven, vrátí původní nálezy beze změn.
"""

import json
import logging
from dataclasses import dataclass, asdict

import anthropic

from backend.config import get_settings
from backend.scanner.detector import DetectedAI
from backend.monitoring.engine_health import engine_monitor

logger = logging.getLogger(__name__)

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
- U analytiky s AI predikcemi: čl. 50 odst. 4
- U doporučovacích systémů: čl. 50 odst. 1 pokud personalizované
- Vrať POUZE validní JSON pole"""

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

    def __init__(self, api_key: str | None = None, model: str = "claude-sonnet-4-20250514"):
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
        Klasifikuje nálezy pomocí Claude API.
        Pokud API není dostupné, vrátí fallback klasifikaci.
        """
        if not self.enabled or not findings:
            return self._fallback_classify(findings)

        try:
            return await self._claude_classify(url, findings)
        except anthropic.AuthenticationError as e:
            logger.error("[Classifier] Neplatný API klíč!")
            await engine_monitor.report_error(
                "anthropic_auth", scan_id=None, url=url,
                details=str(e),
            )
            return self._fallback_classify(findings)
        except anthropic.RateLimitError as e:
            logger.warning("[Classifier] Rate limit — fallback")
            await engine_monitor.report_error(
                "anthropic_rate_limit", scan_id=None, url=url,
                details=str(e),
            )
            return self._fallback_classify(findings)
        except anthropic.APIStatusError as e:
            # Catches 529 Overloaded, billing errors, etc.
            error_type = "anthropic_overloaded" if e.status_code == 529 else "pipeline_error"
            if "credit" in str(e).lower() or "billing" in str(e).lower():
                error_type = "anthropic_tokens_depleted"
            logger.error(f"[Classifier] API status error {e.status_code}: {e}")
            await engine_monitor.report_error(
                error_type, scan_id=None, url=url,
                details=f"Status {e.status_code}: {e}",
            )
            return self._fallback_classify(findings)
        except Exception as e:
            logger.error(f"[Classifier] Chyba: {e}", exc_info=True)
            await engine_monitor.report_error(
                "pipeline_error", scan_id=None, url=url,
                details=f"Classifier exception: {e}",
            )
            return self._fallback_classify(findings)

    async def _claude_classify(
        self, url: str, findings: list[DetectedAI]
    ) -> list[ClassifiedFinding]:
        """Zavolá Claude API pro klasifikaci."""

        # Připravíme zjednodušený JSON pro Claude
        findings_for_claude = []
        for f in findings:
            findings_for_claude.append({
                "name": f.name,
                "category": f.category,
                "risk_level": f.risk_level,
                "matched_signatures": f.matched_signatures[:5],
                "evidence": f.evidence[:5],
                "confidence": f.confidence,
            })

        user_message = USER_PROMPT_TEMPLATE.format(
            url=url,
            findings_json=json.dumps(findings_for_claude, ensure_ascii=False, indent=2),
        )

        logger.info(f"[Classifier] Posílám {len(findings)} nálezů do Claude ({self.model})")

        # Volání Claude API (synchronní — v async kontextu to běží v threadpoolu)
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_message},
            ],
        )

        # Statistiky
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = (input_tokens * COST_PER_INPUT_TOKEN) + (output_tokens * COST_PER_OUTPUT_TOKEN)

        self._usage["input_tokens"] += input_tokens
        self._usage["output_tokens"] += output_tokens
        self._usage["cost_usd"] += cost

        logger.info(
            f"[Classifier] Claude odpověděl: "
            f"{input_tokens} input + {output_tokens} output tokens, "
            f"cena: ${cost:.4f}"
        )

        # Parsování odpovědi
        raw_text = response.content[0].text.strip()

        # Odstranění markdown code fences pokud jsou
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            raw_text = "\n".join(lines[1:])  # Odstraníme první řádek (```json)
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

        classified_data = json.loads(raw_text)

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

    def _fallback_classify(self, findings: list[DetectedAI]) -> list[ClassifiedFinding]:
        """
        Fallback klasifikace bez Claude API.
        Všechny nálezy označí jako deployed (konzervativní přístup).
        """
        logger.info(f"[Classifier] Fallback klasifikace pro {len(findings)} nálezů")

        return [
            ClassifiedFinding(
                name=f.name,
                deployed=True,  # Konzervativně: vše je nasazené
                category=f.category,
                risk_level=f.risk_level,
                ai_act_article=f.ai_act_article,
                action_required=f.action_required,
                description_cs=f.description_cs,
                confidence=f.confidence,
                reason="Automatická detekce (bez AI ověření)",
                matched_signatures=f.matched_signatures,
                evidence=f.evidence,
            )
            for f in findings
        ]
