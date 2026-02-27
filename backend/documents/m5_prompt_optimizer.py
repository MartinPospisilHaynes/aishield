"""
AIshield.cz — Modul 5: PROMPT OPTIMIZER (Self-Improving System)

Analyzuje agregovaná data z M2 (EU Critic) + M3 (Client Critic) po celé generaci,
identifikuje opakující se vzory a navrhuje konkrétní patche do SYSTEM_PROMPT_M1.

Architekttura:
  1. Shromáždí všechny nálezy M2+M3 z 11 dokumentů
  2. Identifikuje opakující se problémy (≥3 výskyty)
  3. Navrhne patch do SYSTEM_PROMPT_M1 (max 5 pravidel za iteraci)
  4. Uloží patch jako verzi s metadaty
  5. Automaticky se deaktivuje po dosažení konvergence

Bezpečnostní záruky:
  - Immutable core: jádro promptu (právní fakta, formát) nelze měnit
  - Max 5 pravidel za iteraci (prevence rozpliznutí)
  - Max 30 pravidel celkem / 5000 znaků — automatické prořezávání nejhorších
  - Konvergence check: vypne se při avg skóre ≥ 8.5
  - Verzování: každý patch je uložen, možnost rollbacku
  - Degradation guard: pokud skóre klesne o ≥ 0.5 vs best → automatický rollback
  - Finding rejection: M5 může explicitně odmítnout nálezy M2/M3 jako neplatné
  - No-change-is-OK: 0 nových pravidel je validní a preferovaný výstup

Model: Claude Opus 4.6 — nejsilnější model pro meta-analýzu a syntézu.
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from backend.documents.llm_engine import extract_html_content

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════
# KONFIGURACE
# ══════════════════════════════════════════════════════════════════════

# Cesta pro ukládání verzí promptů
PROMPT_VERSIONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "prompt_versions"
)

# Konvergence — M5 se automaticky vypne pokud:
CONVERGENCE_THRESHOLD = 8.5     # průměrné skóre M2+M3 >= 8.5
CONVERGENCE_GENERATIONS = 3     # po 3 generace za sebou
MAX_ITERATIONS = 20             # nebo po 20 iteracích celkem

# Bezpečnost
MAX_RULES_PER_ITERATION = 5    # max pravidel přidaných za 1 iteraci
MIN_PATTERN_OCCURRENCES = 3     # problém musí být v ≥3 dokumentech
MAX_TOTAL_RULES = 30            # absolutní limit pravidel — pak se prořezávají nejstarší
MAX_RULES_CHARS = 5000          # max velikost m5_rules.txt v znacích
DEGRADATION_THRESHOLD = 0.5     # pokud avg klesne o >= 0.5 vs best → rollback

# Model pro M5 — Opus pro maximální kvalitu meta-analýzy
M5_MODEL = "claude-opus-4-6"
M5_COST_INPUT = 5.0 / 1_000_000
M5_COST_OUTPUT = 25.0 / 1_000_000


# ══════════════════════════════════════════════════════════════════════
# IMMUTABLE CORE — tyto sekce SYSTEM_PROMPT_M1 se NESMÍ měnit
# ══════════════════════════════════════════════════════════════════════

IMMUTABLE_SECTIONS = [
    "VÝSTUPNÍ FORMÁT — HTML",       # Formátovací pravidla
    "PRÁVNÍ FAKTA — PŘESNĚ DODRŽUJ", # Zákonné údaje
    "KLÍČOVÉ ROZLIŠENÍ — AISHIELD vs. KLIENT",  # Business logika
    "DOKUMENTY V COMPLIANCE KITU",   # Seznam dokumentů
    "CHYBĚJÍCÍ DATA — FALLBACK PRAVIDLO",  # Fallback
    "DYNAMICKÉ DATUM",               # Dynamické datum
]


# ══════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT PRO M5 — Meta-Analyzer
# ══════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT_M5 = """Jsi expert na prompt engineering a meta-analýzu kvality AI výstupů.
Tvým úkolem je analyzovat zpětnou vazbu z kontrolních modulů (M2 — EU inspektor, M3 — klient)
a navrhnout KONKRÉTNÍ vylepšení generovacího promptu (SYSTEM_PROMPT_M1).

TVŮJ PROCES:
1. Analyzuj agregované nálezy z M2 (právní přesnost) a M3 (klientská spokojenost)
2. Identifikuj OPAKUJÍCÍ se vzory — problémy, které se objevují ve ≥3 dokumentech
3. Navrhni KONKRÉTNÍ nová pravidla/instrukce pro SYSTEM_PROMPT_M1
4. Každé pravidlo musí být actionable — "Při psaní X vždy Y"

PRAVIDLA PRO PATCHE:
- Navrhuješ NOVÁ pravidla, která se PŘIDAJÍ do sekce "═══ VYLEPŠENÍ Z M5 ═══" v promptu.
- NEMODIFIKUJ existující sekce promptu — pouze přidáváš nová pravidla.
- MAX 5 pravidel za iteraci — kvalita nad kvantitu.
- Každé pravidlo max 2 věty — stručné, jasné, actionable.
- Pravidla píš česky v imperativu: "Vždy uveď...", "Nikdy nepoužívej..."
- Pokud je kvalita již vysoká a nemáš co zásadního navrhnout, navrhni MÉNĚ pravidel nebo žádné.
- Pravidlo, které již v promptu existuje (byť jinak formulované), NEOPAKUJ.

BEZPEČNOSTNÍ PRVKY — NIKDY:
- Nenavrhuj změny právních faktů (data, pokuty, články zákona)
- Nenavrhuj změny formátovacích pravidel (HTML, CSS třídy)
- Nenavrhuj obecné/vágní rady ("piš lépe", "buď konkrétnější")
- Nenavrhuj pravidla, která by zkrátila nebo zjednodušila dokumenty pod profesionální úroveň

KRITICKÝ PRINCIP — NEMĚŇ TO, CO FUNGUJE:
- NE každý nález M2/M3 je oprávněný. Kritik může být přehnaně přísný nebo špatně interpretovat kontext.
- Před navržením pravidla se VŽDY zeptej: "Je tento nález legitimní, nebo si kritik vykládá požadavek špatně?"
- Pokud nález říká něco, co prompt SPRÁVNĚ dělá, ODMÍTNI ho a zdokumentuj proč.
- 0 nových pravidel je PLATNÝ a PREFEROVANÝ výstup, pokud prompt funguje dobře.
- NIKDY nepřidávej pravidlo jen proto, abys něco přidal. Každé pravidlo musí řešit PROKAZATELNÝ a OPAKOVANÝ problém.
- Více pravidel = větší šance na protichůdné instrukce a "rozmazání" promptu.

VÝSTUPNÍ FORMÁT:
Odpověz VÝHRADNĚ platným JSON objektem.

{
  "analyza": {
    "prumerny_eu_score": 7.2,
    "prumerny_client_score": 8.1,
    "celkovy_prumer": 7.65,
    "identifikovane_vzory": [
      {
        "vzor": "Popis opakujícího se problému",
        "pocet_vyskytu": 5,
        "zavaznost": "kritické|důležité|menší",
        "priklad_dokumentu": "compliance_report",
        "typicky_nalez": "Citace konkrétního nálezu z M2/M3"
      }
    ],
    "odmitnute_nalezy": [
      {
        "nalez": "Popis nálezu z M2/M3, který ODMÍTÁM jako neplatný",
        "zdroj": "M2|M3",
        "duvod_odmitnuti": "Proč je tento nález špatný — prompt dělá správně, kritik se mýlí protože...",
        "pocet_vyskytu": 3
      }
    ]
  },
  "doporuceni": {
    "stav": "beze_zmeny|drobna_uprava|zasadni_zmena",
    "nova_pravidla": [
      {
        "pravidlo": "Text nového pravidla pro SYSTEM_PROMPT_M1 (max 2 věty)",
        "duvod": "Proč toto pravidlo navrhuju — jaký vzor řeší",
        "ocekavany_efekt": "Co se zlepší"
      }
    ],
    "konvergence": false,
    "komentar": "Celkové hodnocení a další doporučení — 2-3 věty."
  }
}

Pole "stav":
- "beze_zmeny" — prompt funguje dobře, žádná pravidla nepřidávám. PREFEROVANÝ stav.
- "drobna_uprava" — 1-2 pravidla pro drobný opakující se problém.
- "zasadni_zmena" — 3-5 pravidel pro závažné systematické problémy.

Pole "odmitnute_nalezy" — POVINNĚ vyplň, pokud jsi identifikoval nálezy,
které jsou neplatné, přehnané, nebo kde kritik špatně interpretuje požadavek.
Toto pole je DŮLEŽITÉ — ukazuje, že jsi kriticky zhodnotil vstupy.

Pokud jsou dokumenty již kvalitní (průměr ≥ 8.5), nastav "konvergence": true
a "nova_pravidla" nechej prázdné.
"""


# ══════════════════════════════════════════════════════════════════════
# PROMPT VERSION MANAGER
# ══════════════════════════════════════════════════════════════════════

class PromptVersionManager:
    """Spravuje verze SYSTEM_PROMPT_M1 s kompletní historií."""

    def __init__(self, versions_dir: str = PROMPT_VERSIONS_DIR):
        self.versions_dir = versions_dir
        os.makedirs(versions_dir, exist_ok=True)
        self.history_file = os.path.join(versions_dir, "history.json")
        self.m5_rules_file = os.path.join(versions_dir, "m5_rules.txt")
        self._history = self._load_history()

    def _load_history(self) -> List[dict]:
        """Načte historii verzí."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_history(self):
        """Uloží historii."""
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(self._history, f, ensure_ascii=False, indent=2, default=str)

    def get_current_version(self) -> int:
        """Vrátí číslo aktuální verze."""
        return len(self._history)

    def get_current_m5_rules(self) -> str:
        """Vrátí aktuální M5 pravidla jako text pro vložení do promptu."""
        if os.path.exists(self.m5_rules_file):
            with open(self.m5_rules_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        return ""

    def get_convergence_status(self) -> dict:
        """Zkontroluje, zda bylo dosaženo konvergence."""
        version = self.get_current_version()

        if version >= MAX_ITERATIONS:
            return {
                "converged": True,
                "reason": f"Dosažen maximální počet iterací ({MAX_ITERATIONS})",
                "version": version,
            }

        # Kontrola posledních N generací
        if len(self._history) >= CONVERGENCE_GENERATIONS:
            recent = self._history[-CONVERGENCE_GENERATIONS:]
            avg_scores = [h.get("avg_score", 0) for h in recent]
            if all(s >= CONVERGENCE_THRESHOLD for s in avg_scores):
                return {
                    "converged": True,
                    "reason": f"Průměrné skóre ≥ {CONVERGENCE_THRESHOLD} po {CONVERGENCE_GENERATIONS} generace",
                    "scores": avg_scores,
                    "version": version,
                }

        return {
            "converged": False,
            "version": version,
            "iterations_remaining": MAX_ITERATIONS - version,
        }

    def check_degradation(self) -> dict:
        """
        Degradation guard — detekuje, zda M5 pravidla ZHORŠUJÍ kvalitu.

        Logika:
        - Najde nejlepší historické avg_score
        - Porovná s posledním avg_score
        - Pokud pokles >= DEGRADATION_THRESHOLD → doporučí rollback
        - Pokud 2 po sobě jdoucí poklesy → rollback na best verzi
        """
        if len(self._history) < 2:
            return {"should_rollback": False, "reason": "Nedostatek dat"}

        scores = [(h["version"], h["avg_score"]) for h in self._history]
        best_version, best_score = max(scores, key=lambda x: x[1])
        current_version, current_score = scores[-1]

        drop = best_score - current_score

        # Podmínka 1: Velký propad oproti nejlepšímu skóre
        if drop >= DEGRADATION_THRESHOLD:
            return {
                "should_rollback": True,
                "reason": f"Propad {drop:.2f} >= {DEGRADATION_THRESHOLD} vs best v{best_version}",
                "best_score": best_score,
                "best_version": best_version,
                "current_score": current_score,
                "drop": drop,
                "rollback_to_version": best_version,
            }

        # Podmínka 2: Dva po sobě jdoucí poklesy
        if len(scores) >= 3:
            s1, s2, s3 = scores[-3][1], scores[-2][1], scores[-1][1]
            if s3 < s2 < s1:
                return {
                    "should_rollback": True,
                    "reason": f"Dva po sobě jdoucí poklesy: {s1:.2f} → {s2:.2f} → {s3:.2f}",
                    "best_score": best_score,
                    "best_version": best_version,
                    "current_score": current_score,
                    "drop": drop,
                    "rollback_to_version": best_version,
                }

        return {
            "should_rollback": False,
            "best_score": best_score,
            "current_score": current_score,
            "drop": drop,
        }

    def prune_if_needed(self) -> int:
        """
        Prořezává pravidla pokud překročí MAX_TOTAL_RULES nebo MAX_RULES_CHARS.

        Strategie: odstraní pravidla Z VERZÍ s nejhorším skóre (ty nepomáhaly).
        Vrací počet odstraněných pravidel.
        """
        current_rules = self.get_current_m5_rules()
        if not current_rules:
            return 0

        # Spočítej pravidla
        rule_lines = [l for l in current_rules.split("\n") if l.strip().startswith("- ")]
        total_rules = len(rule_lines)
        total_chars = len(current_rules)

        if total_rules <= MAX_TOTAL_RULES and total_chars <= MAX_RULES_CHARS:
            return 0  # V limitu

        logger.warning(f"[M5 PromptOptimizer] PRUNE: {total_rules} pravidel ({total_chars} znaků) "
                      f"překračuje limit ({MAX_TOTAL_RULES} pravidel / {MAX_RULES_CHARS} znaků)")

        # Najdi verze seřazené od nejhoršího skóre
        if not self._history:
            return 0

        sorted_versions = sorted(self._history, key=lambda h: h["avg_score"])

        pruned = 0
        for worst_entry in sorted_versions:
            if total_rules <= MAX_TOTAL_RULES and total_chars <= MAX_RULES_CHARS:
                break

            v = worst_entry["version"]
            rules_in_version = worst_entry.get("rules_added", 0)
            if rules_in_version == 0:
                continue

            # Odstraň sekci této verze z rules souboru
            section_marker = f"# --- M5 v{v} ("
            if section_marker in current_rules:
                # Najdi začátek a konec sekce
                start = current_rules.index(section_marker)
                next_section = current_rules.find("# --- M5 v", start + 1)
                if next_section == -1:
                    section_text = current_rules[start:]
                else:
                    section_text = current_rules[start:next_section]

                current_rules = current_rules.replace(section_text, "")
                total_rules -= rules_in_version
                total_chars = len(current_rules)
                pruned += rules_in_version

                logger.warning(f"[M5 PromptOptimizer] PRUNED v{v} ({rules_in_version} pravidel, "
                              f"avg_score={worst_entry['avg_score']:.2f} — nejhorší)")

        if pruned > 0:
            # Ulož prořezaný soubor
            with open(self.m5_rules_file, "w", encoding="utf-8") as f:
                f.write(current_rules.strip() + "\n")
            logger.info(f"[M5 PromptOptimizer] Prořezáno {pruned} pravidel. "
                       f"Zbývá {total_rules} pravidel, {total_chars} znaků.")

        return pruned

    def add_version(
        self,
        generation_id: str,
        new_rules: List[dict],
        analysis: dict,
        avg_score: float,
        cost_usd: float,
        m5_response: dict,
    ) -> dict:
        """Přidá novou verzi pravidel."""
        version = self.get_current_version() + 1
        timestamp = datetime.now(timezone.utc).isoformat()

        # Uložit verzi do historie
        version_entry = {
            "version": version,
            "generation_id": generation_id,
            "timestamp": timestamp,
            "avg_score": round(avg_score, 2),
            "eu_avg": round(analysis.get("prumerny_eu_score", 0), 2),
            "client_avg": round(analysis.get("prumerny_client_score", 0), 2),
            "rules_added": len(new_rules),
            "rules": [r.get("pravidlo", "") for r in new_rules],
            "reasons": [r.get("duvod", "") for r in new_rules],
            "cost_usd": round(cost_usd, 4),
            "converged": m5_response.get("doporuceni", {}).get("konvergence", False),
        }
        self._history.append(version_entry)
        self._save_history()

        # Aktualizovat soubor s pravidly
        self._update_rules_file(new_rules)

        # Uložit kompletní M5 response pro audit
        audit_file = os.path.join(self.versions_dir, f"v{version}_audit.json")
        with open(audit_file, "w", encoding="utf-8") as f:
            json.dump({
                "version": version,
                "generation_id": generation_id,
                "timestamp": timestamp,
                "m5_full_response": m5_response,
                "analysis_input": analysis,
            }, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"[M5 PromptOptimizer] Verze v{version} uložena: "
                    f"{len(new_rules)} nových pravidel, avg={avg_score:.2f}")

        return version_entry

    def _update_rules_file(self, new_rules: List[dict]):
        """Přidá nová pravidla do souboru m5_rules.txt."""
        existing = self.get_current_m5_rules()
        version = self.get_current_version()

        new_section = f"\n# --- M5 v{version} ({datetime.now().strftime('%Y-%m-%d')}) ---\n"
        for rule in new_rules:
            text = rule.get("pravidlo", "").strip()
            if text:
                new_section += f"- {text}\n"

        updated = existing + new_section
        with open(self.m5_rules_file, "w", encoding="utf-8") as f:
            f.write(updated)

    def rollback(self, to_version: int) -> bool:
        """Vrátí pravidla na starší verzi."""
        if to_version < 0 or to_version > len(self._history):
            return False

        # Přebudovat rules soubor ze starších verzí
        rules_text = ""
        for entry in self._history[:to_version]:
            v = entry["version"]
            ts = entry["timestamp"][:10]
            rules_text += f"\n# --- M5 v{v} ({ts}) ---\n"
            for rule in entry.get("rules", []):
                rules_text += f"- {rule}\n"

        with open(self.m5_rules_file, "w", encoding="utf-8") as f:
            f.write(rules_text)

        # Zalogovat rollback
        logger.warning(f"[M5 PromptOptimizer] ROLLBACK na verzi v{to_version}")
        return True

    def get_summary(self) -> str:
        """Vrátí čitelný přehled historie."""
        if not self._history:
            return "Žádné verze — M5 ještě neběžel."

        lines = [f"M5 Prompt Optimizer — {len(self._history)} verzí\n"]
        for entry in self._history:
            v = entry["version"]
            score = entry["avg_score"]
            rules = entry["rules_added"]
            conv = " [KONVERGENCE]" if entry.get("converged") else ""
            lines.append(f"  v{v}: avg={score:.1f}, +{rules} pravidel, ${entry['cost_usd']:.4f}{conv}")

        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════
# HLAVNÍ FUNKCE — analyze_and_optimize
# ══════════════════════════════════════════════════════════════════════

async def analyze_and_optimize(
    pipeline_log: List[dict],
    all_critiques: Dict[str, dict],
    generation_id: str = "unknown",
    post_m4_checks: Dict[str, dict] = None,
) -> dict:
    """
    Hlavní vstupní bod M5 — analyzuje generaci a navrhne vylepšení promptu.

    Args:
        pipeline_log: pipeline_log z ComplianceKitResult — seznam dict per doc
        all_critiques: dict {doc_key: {"eu": eu_critique, "client": client_critique}}
        generation_id: identifikátor generace (gen12, gen13, ...)
        post_m4_checks: dict {doc_key: M6 post-check result} — INFO-ONLY finální skóre

    Returns:
        dict s výsledky M5 analýzy
    """
    m5_start = time.time()
    logger.info(f"")
    logger.info(f"[M5 PromptOptimizer] {'═'*55}")
    logger.info(f"[M5 PromptOptimizer] MODUL 5: Prompt Self-Optimization")
    logger.info(f"[M5 PromptOptimizer] Generace: {generation_id}")
    logger.info(f"[M5 PromptOptimizer] {'═'*55}")

    manager = PromptVersionManager()

    # ── 1. Konvergence check ──
    conv_status = manager.get_convergence_status()
    if conv_status["converged"]:
        logger.info(f"[M5 PromptOptimizer] KONVERGENCE DOSAŽENA: {conv_status['reason']}")
        logger.info(f"[M5 PromptOptimizer] M5 je deaktivován — žádné další změny.")
        return {
            "status": "converged",
            "reason": conv_status["reason"],
            "version": conv_status["version"],
            "cost_usd": 0,
        }

    logger.info(f"[M5 PromptOptimizer] Aktuální verze: v{conv_status['version']}")
    logger.info(f"[M5 PromptOptimizer] Zbývá iterací: {conv_status['iterations_remaining']}")

    # ── 1b. Degradation guard — rollback pokud pravidla zhoršují skóre ──
    degradation = manager.check_degradation()
    if degradation["should_rollback"]:
        rollback_to = degradation["rollback_to_version"]
        logger.warning(f"[M5 PromptOptimizer] DEGRADATION GUARD: "
                      f"skóre kleslo z {degradation['best_score']:.2f} na {degradation['current_score']:.2f} "
                      f"(pokles {degradation['drop']:.2f} >= {DEGRADATION_THRESHOLD})")
        logger.warning(f"[M5 PromptOptimizer] AUTO-ROLLBACK na v{rollback_to} (nejlepší historické skóre)")
        manager.rollback(rollback_to)
        # Pokračuj s analýzou, ale s varováním
        logger.info(f"[M5 PromptOptimizer] Rollback proveden. Pokračuji s analýzou na nové baseline.")

    # ── 2. Agregace dat z M2+M3 ──
    aggregated = _aggregate_critiques(pipeline_log, all_critiques, post_m4_checks or {})
    logger.info(f"[M5 PromptOptimizer] Agregace: {aggregated['doc_count']} dokumentů, "
                f"EU avg={aggregated['eu_avg']:.1f}, Client avg={aggregated['client_avg']:.1f}")

    # ── 3. Přečíst aktuální M5 pravidla ──
    current_rules = manager.get_current_m5_rules()
    if current_rules:
        logger.info(f"[M5 PromptOptimizer] Existující M5 pravidla: {len(current_rules)} znaků")
    else:
        logger.info(f"[M5 PromptOptimizer] Žádná existující M5 pravidla (první iterace)")

    # ── 4. Zavolat Claude Opus pro analýzu ──
    prompt = _build_m5_prompt(aggregated, current_rules, conv_status["version"])

    logger.info(f"[M5 PromptOptimizer] Volám Claude Opus 4.6 pro meta-analýzu...")
    m5_response, meta = await _call_m5(prompt)

    cost = meta.get("cost_usd", 0)
    logger.info(f"[M5 PromptOptimizer] Odpověď: ${cost:.4f}, "
                f"{meta.get('input_tokens', 0)}+{meta.get('output_tokens', 0)} tokens")

    # ── 5. Zpracovat odpověď ──
    if not m5_response:
        logger.error(f"[M5 PromptOptimizer] M5 nevrátil platnou odpověď!")
        return {"status": "error", "error": "Invalid M5 response", "cost_usd": cost}

    analysis = m5_response.get("analyza", {})
    recommendations = m5_response.get("doporuceni", {})
    new_rules = recommendations.get("nova_pravidla", [])
    is_converged = recommendations.get("konvergence", False)

    # ── 6. Bezpečnostní kontroly ──
    new_rules = _safety_check_rules(new_rules)

    if len(new_rules) > MAX_RULES_PER_ITERATION:
        logger.warning(f"[M5 PromptOptimizer] Příliš mnoho pravidel ({len(new_rules)}), "
                      f"ořezávám na {MAX_RULES_PER_ITERATION}")
        new_rules = new_rules[:MAX_RULES_PER_ITERATION]

    # ── 7. Uložit verzi ──
    avg_score = (aggregated["eu_avg"] + aggregated["client_avg"]) / 2

    if new_rules:
        version_entry = manager.add_version(
            generation_id=generation_id,
            new_rules=new_rules,
            analysis=analysis,
            avg_score=avg_score,
            cost_usd=cost,
            m5_response=m5_response,
        )
        logger.info(f"[M5 PromptOptimizer] Uloženo: v{version_entry['version']}")

        # ── Prořezávání — kontrola velikosti pravidel ──
        pruned = manager.prune_if_needed()
        if pruned:
            logger.info(f"[M5 PromptOptimizer] Prořezáno {pruned} starých pravidel (anti-bloat)")
    else:
        logger.info(f"[M5 PromptOptimizer] Žádná nová pravidla — M5 zhodnotil prompt jako dostatečný.")
        version_entry = {"version": conv_status["version"], "rules_added": 0}

    # ── 8. Logování výsledků ──
    m5_time = time.time() - m5_start

    # Logovat odmítnuté nálezy (M5 říká "kritik se mýlí")
    rejected = analysis.get("odmitnute_nalezy", [])
    if rejected:
        logger.info(f"[M5 PromptOptimizer] ODMÍTNUTO {len(rejected)} nálezů jako neplatné:")
        for rej in rejected:
            logger.info(f"[M5 PromptOptimizer]   REJECTED [{rej.get('zdroj', '?')}]: "
                       f"{rej.get('nalez', '?')}")
            logger.info(f"[M5 PromptOptimizer]     Důvod odmítnutí: {rej.get('duvod_odmitnuti', '?')}")

    stav = recommendations.get("stav", "neznámý")
    logger.info(f"[M5 PromptOptimizer] Stav: {stav}")

    for i, rule in enumerate(new_rules, 1):
        logger.info(f"[M5 PromptOptimizer]   Pravidlo #{i}: {rule.get('pravidlo', '?')}")
        logger.info(f"[M5 PromptOptimizer]     Důvod: {rule.get('duvod', '?')}")

    if is_converged:
        logger.info(f"[M5 PromptOptimizer] M5 navrhuje KONVERGENCI — příští generace bez M5.")

    logger.info(f"[M5 PromptOptimizer] Komentář: {recommendations.get('komentar', 'N/A')}")
    logger.info(f"[M5 PromptOptimizer] Čas: {m5_time:.1f}s, Cost: ${cost:.4f}")
    logger.info(f"[M5 PromptOptimizer] {'═'*55}")

    return {
        "status": "optimized" if new_rules else "no_change",
        "stav": recommendations.get("stav", "beze_zmeny" if not new_rules else "drobna_uprava"),
        "version": version_entry.get("version", conv_status["version"]),
        "rules_added": len(new_rules),
        "rules": [r.get("pravidlo", "") for r in new_rules],
        "rejected_findings": len(rejected),
        "rejected_details": [{"nalez": r.get("nalez", ""), "duvod": r.get("duvod_odmitnuti", "")} for r in rejected],
        "avg_score": round(avg_score, 2),
        "eu_avg": round(aggregated["eu_avg"], 2),
        "client_avg": round(aggregated["client_avg"], 2),
        "converged": is_converged,
        "degradation_check": degradation if 'degradation' in dir() else None,
        "cost_usd": round(cost, 4),
        "time_s": round(m5_time, 1),
        "comment": recommendations.get("komentar", ""),
    }


# ══════════════════════════════════════════════════════════════════════
# HELPER FUNKCE
# ══════════════════════════════════════════════════════════════════════

def _aggregate_critiques(
    pipeline_log: List[dict],
    all_critiques: Dict[str, dict],
    post_m4_checks: Dict[str, dict] = None,
) -> dict:
    """Agreguje nálezy M2+M3+M6 přes všechny dokumenty."""
    eu_scores = []
    client_scores = []
    m6_scores = []
    all_eu_findings = []
    all_client_findings = []
    all_m6_findings = []
    doc_count = 0
    post_m4_checks = post_m4_checks or {}

    for entry in pipeline_log:
        doc_key = entry.get("doc_key")
        if not doc_key or entry.get("error"):
            continue

        doc_count += 1
        eu_score = entry.get("eu_score", 0)
        client_score = entry.get("client_score", 0)

        if isinstance(eu_score, (int, float)):
            eu_scores.append(eu_score)
        if isinstance(client_score, (int, float)):
            client_scores.append(client_score)

        # Detailní nálezy
        critiques = all_critiques.get(doc_key, {})
        eu_data = critiques.get("eu", {})
        client_data = critiques.get("client", {})

        for finding in eu_data.get("nalezy", []):
            all_eu_findings.append({
                "doc_key": doc_key,
                "doc_name": entry.get("doc_name", doc_key),
                **finding,
            })

        for finding in client_data.get("nalezy", []):
            all_client_findings.append({
                "doc_key": doc_key,
                "doc_name": entry.get("doc_name", doc_key),
                **finding,
            })

        # M6 post-M4 check findings
        m6_data = post_m4_checks.get(doc_key, {})
        m6_score = m6_data.get("finalni_skore")
        if isinstance(m6_score, (int, float)):
            m6_scores.append(m6_score)
        for finding in m6_data.get("pretrvavajici_problemy", []):
            all_m6_findings.append({
                "doc_key": doc_key,
                "doc_name": entry.get("doc_name", doc_key),
                **finding,
            })

    return {
        "doc_count": doc_count,
        "eu_avg": sum(eu_scores) / len(eu_scores) if eu_scores else 0,
        "m6_avg": sum(m6_scores) / len(m6_scores) if m6_scores else 0,
        "m6_scores": m6_scores,
        "m6_findings": all_m6_findings,
        "m6_findings_count": len(all_m6_findings),
        "client_avg": sum(client_scores) / len(client_scores) if client_scores else 0,
        "eu_scores": eu_scores,
        "client_scores": client_scores,
        "eu_findings": all_eu_findings,
        "client_findings": all_client_findings,
        "eu_findings_count": len(all_eu_findings),
        "client_findings_count": len(all_client_findings),
    }


def _build_m5_prompt(aggregated: dict, current_rules: str, version: int) -> str:
    """Sestaví prompt pro M5."""

    # Formátování nálezů
    eu_text = _format_findings(aggregated["eu_findings"], "EU Inspector (M2)")
    client_text = _format_findings(aggregated["client_findings"], "Client (M3)")
    m6_text = _format_findings(aggregated.get("m6_findings", []), "Post-M4 Verifikace (M6)")

    # Skóre přehled
    scores_text = "SKÓRE PO DOKUMENTECH:\n"
    m6_scores_list = aggregated.get("m6_scores", [])
    for i, (eu, cl) in enumerate(zip(aggregated["eu_scores"], aggregated["client_scores"]), 1):
        m6_s = m6_scores_list[i-1] if i-1 < len(m6_scores_list) else "?"
        scores_text += f"  Doc {i}: EU(draft)={eu}/10, Client(draft)={cl}/10, M6(final)={m6_s}/10\n"

    rules_section = ""
    if current_rules:
        rules_section = f"""
═══ AKTUÁLNÍ M5 PRAVIDLA (verze v{version}) ═══
{current_rules}

UPOZORNĚNÍ: Nenavrhuj pravidla, která již existují (byť jinak formulovaná).
"""

    return f"""ANALYZUJ výsledky generace compliance dokumentů a navrhni vylepšení promptu.

═══ PŘEHLED GENERACE ═══
Dokumentů: {aggregated['doc_count']}
Průměrné skóre EU (M2, draft): {aggregated['eu_avg']:.1f}/10
Průměrné skóre Client (M3, draft): {aggregated['client_avg']:.1f}/10
Průměrné skóre M6 (finál po M4): {aggregated.get('m6_avg', 0):.1f}/10
Celkový průměr draft: {(aggregated['eu_avg'] + aggregated['client_avg']) / 2:.1f}/10
Počet EU nálezů (draft): {aggregated['eu_findings_count']}
Počet Client nálezů (draft): {aggregated['client_findings_count']}
Počet přetrvávajících nálezů po M4: {aggregated.get('m6_findings_count', 0)}

DŮLEŽITÉ: M6 skóre hodnotí FINÁLNÍ verzi po M4 úpravách.
Pokud M6 skóre >> M2/M3 skóre → M4 refiner funguje dobře.
Pokud M6 stále nachází problémy → prompt M1 potřebuje úpravu.

{scores_text}

═══ NÁLEZY EU INSPEKTORA (M2) — {aggregated['eu_findings_count']} celkem ═══
{eu_text}

═══ NÁLEZY KLIENTA (M3) — {aggregated['client_findings_count']} celkem ═══
{client_text}

{m6_text}
{rules_section}
═══ TVŮJ ÚKOL ═══
1. Identifikuj opakující se VZORY — problémy, které se objevují ve ≥{MIN_PATTERN_OCCURRENCES} dokumentech.
2. Navrhni max {MAX_RULES_PER_ITERATION} KONKRÉTNÍCH pravidel pro zlepšení generovacího promptu.
3. Pokud je průměrné skóre ≥ {CONVERGENCE_THRESHOLD}, nastav konvergence=true.
4. Odpověz JSON dle specifikace.
"""


def _format_findings(findings: list, source: str) -> str:
    """Formátuje nálezy pro M5 prompt."""
    if not findings:
        return f"Žádné nálezy z {source}."

    lines = []
    for f in findings:
        severity = f.get("zavaznost", "?")
        area = f.get("oblast", "?")
        desc = f.get("popis", "?")
        doc = f.get("doc_name", f.get("doc_key", "?"))
        lines.append(f"  [{severity}] {doc} — {area}: {desc}")

    return "\n".join(lines)


def _safety_check_rules(rules: List[dict]) -> List[dict]:
    """Bezpečnostní kontrola — odfiltruje nebezpečná pravidla."""
    safe_rules = []
    blocked_keywords = [
        "datum", "platnost", "pokut", "článek", "článk", "čl.",   # právní fakta
        "html", "css", "class=", "<h1>", "<div>",                  # formátovací
        "emoji",                                                    # již existuje
    ]

    for rule in rules:
        text = rule.get("pravidlo", "").lower()

        # Kontrola na immutable obsah
        is_blocked = False
        for keyword in blocked_keywords:
            if keyword in text and any(
                s.lower() in text for s in ["změň", "uprav", "smaž", "odstraň", "přepiš"]
            ):
                logger.warning(f"[M5 Safety] BLOKOVÁNO pravidlo (immutable): {rule.get('pravidlo', '')}")
                is_blocked = True
                break

        if not is_blocked and text.strip():
            safe_rules.append(rule)

    return safe_rules


async def _call_m5(prompt: str) -> Tuple[Optional[dict], dict]:
    """Zavolá Claude Opus 4.6 pro M5 analýzu."""
    import anthropic
    import os
    from backend.config import get_settings

    settings = get_settings()
    api_key = settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY není nastavený")

    client = anthropic.AsyncAnthropic(api_key=api_key)

    try:
        response = await client.messages.create(
            model=M5_MODEL,
            max_tokens=4000,    # M5 nepotřebuje dlouhý output
            temperature=0.2,    # lehce kreativní pro meta-analýzu
            system=SYSTEM_PROMPT_M5,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text if response.content else ""
        in_tok = response.usage.input_tokens if response.usage else 0
        out_tok = response.usage.output_tokens if response.usage else 0
        cost = (in_tok * M5_COST_INPUT) + (out_tok * M5_COST_OUTPUT)

        logger.info(f"[M5 PromptOptimizer] Claude Opus 4.6: "
                    f"tokens={in_tok}+{out_tok}, cost=${cost:.4f}")

        meta = {
            "provider": "claude",
            "model": M5_MODEL,
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "cost_usd": cost,
        }

        # Parse JSON
        from backend.documents.llm_engine import parse_json
        parsed = parse_json(text)
        return parsed, meta

    except Exception as e:
        logger.error(f"[M5 PromptOptimizer] Chyba volání: {e}", exc_info=True)
        return None, {"cost_usd": 0, "error": str(e)}


# ══════════════════════════════════════════════════════════════════════
# INTEGRACE S M1 — inject pravidla do SYSTEM_PROMPT_M1
# ══════════════════════════════════════════════════════════════════════

def get_enhanced_system_prompt_m1(base_prompt: str) -> str:
    """
    Vrátí SYSTEM_PROMPT_M1 obohacený o M5 pravidla.
    Volá se z M1 generátoru na začátku každé generace.

    Args:
        base_prompt: původní SYSTEM_PROMPT_M1

    Returns:
        Prompt doplněný o M5 pravidla (nebo nezměněný, pokud žádná nejsou)
    """
    manager = PromptVersionManager()
    rules = manager.get_current_m5_rules()

    if not rules:
        return base_prompt

    # Přidej M5 sekci před koncovou část promptu
    m5_section = f"""

═══ VYLEPŠENÍ Z M5 — AUTOMATICKÁ OPTIMALIZACE (v{manager.get_current_version()}) ═══

Následující pravidla byla automaticky identifikována analýzou zpětné vazby
z předchozích generací. DODRŽUJ je stejně přísně jako ostatní pravidla.

{rules}
"""

    # Vložit před poslední sekci (PRÁVNÍ FAKTA)
    marker = "═══ PRÁVNÍ FAKTA"
    if marker in base_prompt:
        idx = base_prompt.index(marker)
        return base_prompt[:idx] + m5_section + "\n" + base_prompt[idx:]
    else:
        return base_prompt + m5_section
