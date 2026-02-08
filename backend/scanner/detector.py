"""
AIshield.cz — AI Detector
Porovnává výsledky web scanneru s databází AI signatur.
Najde AI systémy na stránce.
"""

from dataclasses import dataclass
from backend.scanner.web_scanner import ScannedPage
from backend.scanner.signatures import AISignature, get_all_signatures


@dataclass
class DetectedAI:
    """Jeden nalezený AI systém na webu."""
    name: str
    category: str
    risk_level: str
    ai_act_article: str
    action_required: str
    description_cs: str
    matched_signatures: list[str]   # Které signatury matchly
    evidence: list[str]             # Konkrétní důkazy (URL, snippet...)
    confidence: float               # 0.0 - 1.0


class AIDetector:
    """
    Detekuje AI systémy na základě výsledků skenování.
    Prohledává HTML, skripty, iframe, cookies a network requesty.
    """

    def __init__(self, signatures: list[AISignature] | None = None):
        self.signatures = signatures or get_all_signatures()

    def detect(self, page: ScannedPage) -> list[DetectedAI]:
        """Detekuje AI systémy na proskenované stránce."""
        results: list[DetectedAI] = []

        for sig in self.signatures:
            matched, evidence = self._check_signature(sig, page)

            if matched:
                # Confidence podle počtu matchů
                confidence = min(1.0, len(matched) * 0.3 + len(evidence) * 0.1)

                results.append(DetectedAI(
                    name=sig.name,
                    category=sig.category,
                    risk_level=sig.risk_level,
                    ai_act_article=sig.ai_act_article,
                    action_required=sig.action_required,
                    description_cs=sig.description_cs,
                    matched_signatures=matched,
                    evidence=evidence[:10],  # Max 10 důkazů
                    confidence=round(confidence, 2),
                ))

        # Seřadíme podle rizika (high > limited > minimal)
        risk_order = {"unacceptable": 4, "high": 3, "limited": 2, "minimal": 1}
        results.sort(key=lambda r: risk_order.get(r.risk_level, 0), reverse=True)

        return results

    def _check_signature(
        self, sig: AISignature, page: ScannedPage
    ) -> tuple[list[str], list[str]]:
        """
        Zkontroluje jednu signaturu proti výsledkům skenování.
        Vrátí (matched_signatures, evidence).
        """
        matched: list[str] = []
        evidence: list[str] = []
        html_lower = page.html.lower()

        # 1. Hledáme v HTML
        for pattern in sig.signatures:
            pat_lower = pattern.lower()
            if pat_lower in html_lower:
                matched.append(f"html:{pattern}")
                # Najdeme kontext (50 znaků kolem)
                idx = html_lower.find(pat_lower)
                start = max(0, idx - 30)
                end = min(len(page.html), idx + len(pattern) + 30)
                snippet = page.html[start:end].replace("\n", " ").strip()
                evidence.append(f"HTML: ...{snippet}...")

        # 2. Hledáme v URL externích skriptů
        for script_url in page.scripts:
            script_lower = script_url.lower()
            for pattern in sig.script_patterns:
                if pattern.lower() in script_lower:
                    matched.append(f"script:{pattern}")
                    evidence.append(f"Script: {script_url[:150]}")

        # 3. Hledáme v inline skriptech
        for inline in page.inline_scripts:
            inline_lower = inline.lower()
            for pattern in sig.signatures:
                if pattern.lower() in inline_lower:
                    matched.append(f"inline:{pattern}")
                    # Krátký snippet
                    idx = inline_lower.find(pattern.lower())
                    start = max(0, idx - 30)
                    end = min(len(inline), idx + len(pattern) + 30)
                    snippet = inline[start:end].replace("\n", " ").strip()
                    evidence.append(f"Inline JS: ...{snippet}...")
                    break  # Jeden match za inline stačí

        # 4. Hledáme v iframe
        for iframe_url in page.iframes:
            iframe_lower = iframe_url.lower()
            for pattern in sig.iframe_patterns:
                if pattern.lower() in iframe_lower:
                    matched.append(f"iframe:{pattern}")
                    evidence.append(f"Iframe: {iframe_url[:150]}")

        # 5. Hledáme v cookies
        for cookie in page.cookies:
            cookie_name_lower = cookie["name"].lower()
            for pattern in sig.cookie_patterns:
                if pattern.lower() in cookie_name_lower:
                    matched.append(f"cookie:{pattern}")
                    evidence.append(f"Cookie: {cookie['name']} (domain: {cookie['domain']})")

        # 6. Hledáme v network requestech
        for req_url in page.network_requests:
            req_lower = req_url.lower()
            for pattern in sig.network_patterns:
                if pattern.lower() in req_lower:
                    matched.append(f"network:{pattern}")
                    evidence.append(f"Network: {req_url[:150]}")
                    break  # Jeden match za URL stačí

        # Deduplikace
        matched = list(dict.fromkeys(matched))
        evidence = list(dict.fromkeys(evidence))

        return matched, evidence


def detect_ai_systems(page: ScannedPage) -> list[DetectedAI]:
    """Convenience funkce — detekuje AI systémy na stránce."""
    detector = AIDetector()
    return detector.detect(page)
