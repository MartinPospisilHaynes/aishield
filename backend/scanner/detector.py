"""
AIshield.cz — AI Detector v2
Porovnává výsledky web scanneru s databází AI signatur.
Najde AI systémy na stránce.

v2: Přidána heuristická detekce — analyze neznámých AI systémů,
    JSON-LD structured data, AI transparency notices, API proxy patterns.
"""

import re
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


# ── Heuristické vzory pro detekci neznámých AI systémů ──

# API endpointy AI služeb (v network requests nebo inline skriptech)
AI_API_PATTERNS = [
    (r"generativelanguage\.googleapis\.com", "Google Gemini API"),
    (r"api\.openai\.com", "OpenAI API"),
    (r"api\.anthropic\.com", "Anthropic Claude API"),
    (r"api\.cohere\.ai", "Cohere AI API"),
    (r"api-inference\.huggingface\.co", "Hugging Face API"),
    (r"api\.replicate\.com", "Replicate API"),
    (r"api\.mistral\.ai", "Mistral AI API"),
    (r"api\.together\.xyz", "Together AI API"),
    (r"api\.perplexity\.ai", "Perplexity AI API"),
    (r"aiplatform\.googleapis\.com", "Google Vertex AI"),
    (r"dialogflow\.googleapis\.com", "Google Dialogflow"),
]

# Proxy patterns — vlastní PHP/Node proxy k AI API
AI_PROXY_PATTERNS = [
    r"gemini[_-]?proxy",
    r"openai[_-]?proxy",
    r"ai[_-]?proxy",
    r"chat[_-]?proxy",
    r"gpt[_-]?proxy",
    r"claude[_-]?proxy",
    r"llm[_-]?proxy",
    r"api[_-]?proxy.*(?:chat|ai|gpt|gemini)",
]

# Klíčová slova v HTML/skriptech indikující AI chatbot
AI_CHATBOT_KEYWORDS = [
    # JS proměnné / funkce
    r"chatbot(?:Open|Close|Init|Config|Send|Response)",
    r"aiChat(?:Widget|Bot|Config|Init)",
    r"chatSession(?:Id|Start|End)",
    r"(?:send|receive)(?:AI|Bot|Chat)(?:Message|Response)",
    r"ai[_-]?(?:response|reply|answer|message)",
    # Konfigurační klíče
    r"(?:chat|ai|bot)_?(?:api_?(?:key|url|endpoint))",
    r"(?:gemini|gpt|claude|openai|anthropic)(?:_?(?:key|token|url|endpoint|proxy))",
]

# JSON-LD structured data s AI službami
JSONLD_AI_TYPES = [
    "ai chatbot", "ai bot", "chatbot", "virtual assistant",
    "ai assistant", "artificial intelligence", "machine learning",
    "ai consultant", "ai konzultant",
]

# Transparenční oznámení o AI (český + anglický)
AI_TRANSPARENCY_PATTERNS = [
    r"(?:vytvořen[aoáé]?|generován[aoáé]?|asistován[aoáé]?).*(?:umělou? inteligenc|ai|artificial intelligence)",
    r"(?:obsah|content|text|grafik|image).*(?:ai|umělou? inteligenc|artificial intelligence).*(?:vytvořen|generován|asistován|created|generated|assisted)",
    r"(?:ai|umělá inteligence).*(?:vytváří|generuje|asistuje|creates|generates|assists).*(?:obsah|content)",
    r"powered\s+by\s+(?:ai|gpt|gemini|claude|openai|anthropic)",
    r"poháněn[oáé]?\s+(?:ai|umělou inteligencí|gemini|gpt|claude)",
    r"(?:některé|část)\s+(?:obsahu|funkcí|textů).*(?:ai|umělou inteligencí)",
]


class AIDetector:
    """
    Detekuje AI systémy na základě výsledků skenování.
    
    v2: Dvoustupňová detekce:
    1. Signature matching — porovnání s known signatures
    2. Heuristic detection — analýza neznámých AI systémů
    """

    def __init__(self, signatures: list[AISignature] | None = None):
        self.signatures = signatures or get_all_signatures()

    def detect(self, page: ScannedPage) -> list[DetectedAI]:
        """Detekuje AI systémy na proskenované stránce."""
        results: list[DetectedAI] = []
        found_names: set[str] = set()

        # ── 1. Signature-based detection ──
        for sig in self.signatures:
            matched, evidence = self._check_signature(sig, page)
            if matched:
                confidence = min(1.0, len(matched) * 0.3 + len(evidence) * 0.1)
                results.append(DetectedAI(
                    name=sig.name,
                    category=sig.category,
                    risk_level=sig.risk_level,
                    ai_act_article=sig.ai_act_article,
                    action_required=sig.action_required,
                    description_cs=sig.description_cs,
                    matched_signatures=matched,
                    evidence=evidence[:10],
                    confidence=round(confidence, 2),
                ))
                found_names.add(sig.name.lower())

        # ── 2. Heuristic detection ──
        heuristic_results = self._heuristic_detect(page, found_names)
        results.extend(heuristic_results)

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
                    idx = inline_lower.find(pattern.lower())
                    start = max(0, idx - 30)
                    end = min(len(inline), idx + len(pattern) + 30)
                    snippet = inline[start:end].replace("\n", " ").strip()
                    evidence.append(f"Inline JS: ...{snippet}...")
                    break

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
                    break

        matched = list(dict.fromkeys(matched))
        evidence = list(dict.fromkeys(evidence))
        return matched, evidence

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # HEURISTICKÁ DETEKCE
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def _heuristic_detect(
        self, page: ScannedPage, already_found: set[str]
    ) -> list[DetectedAI]:
        """
        Heuristická detekce AI systémů, které nemají explicitní signaturu.
        Hledá: API volání, proxy patterny, JSON-LD, transparenční oznámení,
        keyword frequency.
        """
        results: list[DetectedAI] = []
        html_lower = page.html.lower()
        all_inline = "\n".join(page.inline_scripts).lower()
        all_text = html_lower + "\n" + all_inline

        # ── 2a. AI API endpointy v network requests ──
        for req_url in page.network_requests:
            for pattern, name in AI_API_PATTERNS:
                if re.search(pattern, req_url, re.IGNORECASE):
                    if name.lower() not in " ".join(already_found):
                        results.append(DetectedAI(
                            name=name,
                            category="chatbot",
                            risk_level="limited",
                            ai_act_article="čl. 50 odst. 1",
                            action_required=f"Detekována komunikace s {name}. "
                                           "AI systém musí být transparentně označen.",
                            description_cs=f"Heuristicky detekováno volání na {name}.",
                            matched_signatures=[f"network_heuristic:{pattern}"],
                            evidence=[f"Network request: {req_url[:200]}"],
                            confidence=0.85,
                        ))
                        already_found.add(name.lower())

        # ── 2b. AI API endpointy v inline skriptech ──
        for pattern, name in AI_API_PATTERNS:
            if re.search(pattern, all_inline, re.IGNORECASE):
                if name.lower() not in " ".join(already_found):
                    match = re.search(pattern, all_inline, re.IGNORECASE)
                    start = max(0, match.start() - 40)
                    end = min(len(all_inline), match.end() + 60)
                    snippet = all_inline[start:end].replace("\n", " ").strip()
                    results.append(DetectedAI(
                        name=name,
                        category="chatbot",
                        risk_level="limited",
                        ai_act_article="čl. 50 odst. 1",
                        action_required=f"V kódu webu nalezena reference na {name}. "
                                       "AI systém musí být transparentně označen.",
                        description_cs=f"V JavaScriptu detekována reference na {name}.",
                        matched_signatures=[f"inline_heuristic:{pattern}"],
                        evidence=[f"Inline JS: ...{snippet}..."],
                        confidence=0.75,
                    ))
                    already_found.add(name.lower())

        # ── 2c. AI proxy patterny ──
        for pattern in AI_PROXY_PATTERNS:
            if re.search(pattern, all_text, re.IGNORECASE):
                match = re.search(pattern, all_text, re.IGNORECASE)
                matched_text = match.group()
                proxy_name = f"AI API Proxy ({matched_text})"
                if proxy_name.lower() not in " ".join(already_found):
                    start = max(0, match.start() - 40)
                    end = min(len(all_text), match.end() + 60)
                    snippet = all_text[start:end].replace("\n", " ").strip()
                    results.append(DetectedAI(
                        name=proxy_name,
                        category="chatbot",
                        risk_level="limited",
                        ai_act_article="čl. 50 odst. 1",
                        action_required="Detekován AI proxy endpoint — web pravděpodobně "
                                       "používá AI chatbot přes vlastní backend. "
                                       "AI systém musí být transparentně označen uživatelům.",
                        description_cs=f"Na webu detekován AI proxy endpoint '{matched_text}'. "
                                      "Typicky slouží jako prostředník mezi frontendem a AI API "
                                      "(GPT, Gemini, Claude). Chatbot musí být označen dle čl. 50.",
                        matched_signatures=[f"proxy_heuristic:{pattern}"],
                        evidence=[f"Kód: ...{snippet}..."],
                        confidence=0.80,
                    ))
                    already_found.add(proxy_name.lower())
                    break  # Jedna proxy detekce stačí

        # ── 2d. JSON-LD structured data s AI službami ──
        jsonld_matches = re.finditer(
            r'"@type"\s*:\s*"Service"[^}]*?"name"\s*:\s*"([^"]+)"',
            page.html, re.IGNORECASE | re.DOTALL,
        )
        for m in jsonld_matches:
            service_name = m.group(1).lower()
            for ai_type in JSONLD_AI_TYPES:
                if ai_type in service_name:
                    display_name = m.group(1)
                    if display_name.lower() not in " ".join(already_found):
                        results.append(DetectedAI(
                            name=f"AI služba: {display_name}",
                            category="chatbot",
                            risk_level="limited",
                            ai_act_article="čl. 50 odst. 1",
                            action_required="Web v structured data deklaruje AI službu. "
                                           "Dle čl. 50 AI Act musí být AI systém "
                                           "transparentně oznámen uživatelům.",
                            description_cs=f"V JSON-LD structured data nalezena AI služba "
                                          f"'{display_name}'. Web provozuje AI systém, "
                                          "který musí být označen.",
                            matched_signatures=[f"jsonld:{ai_type}"],
                            evidence=[f"JSON-LD Service: {page.html[m.start():m.end()][:200]}"],
                            confidence=0.85,
                        ))
                        already_found.add(display_name.lower())
                    break

        # ── 2e. AI Transparency notice ──
        for pattern in AI_TRANSPARENCY_PATTERNS:
            match = re.search(pattern, html_lower, re.IGNORECASE)
            if match:
                start = max(0, match.start() - 30)
                end = min(len(page.html), match.end() + 80)
                snippet = page.html[start:end].replace("\n", " ").strip()
                notice_name = "AI Transparency Notice"
                if notice_name.lower() not in " ".join(already_found):
                    results.append(DetectedAI(
                        name=notice_name,
                        category="content_gen",
                        risk_level="limited",
                        ai_act_article="čl. 50 odst. 2",
                        action_required="Web otevřeně deklaruje použití AI pro tvorbu obsahu. "
                                       "Dle čl. 50 odst. 2 AI Act musí být AI generovaný "
                                       "obsah (text, grafika, audio, video) označen.",
                        description_cs="Na webu nalezeno transparenční oznámení o používání AI. "
                                      "Web přiznává, že část obsahu je vytvořena nebo "
                                      "asistována umělou inteligencí.",
                        matched_signatures=[f"transparency:{pattern}"],
                        evidence=[f"Text: ...{snippet}..."],
                        confidence=0.90,
                    ))
                    already_found.add(notice_name.lower())
                break  # Stačí jeden transparency match

        # ── 2f. Chatbot keyword frequency ──
        chatbot_freq = html_lower.count("chatbot") + all_inline.count("chatbot")
        # Slovo "chatbot" 10+ krát na stránce = silný indikátor
        if chatbot_freq >= 10:
            generic_name = "Custom AI Chatbot"
            # Ale jen pokud jsme ještě žádný chatbot nenašli
            chatbot_already = any(
                "chatbot" in n for n in already_found
            )
            if not chatbot_already and generic_name.lower() not in " ".join(already_found):
                # Zjistíme, jaký model se používá (pokud lze)
                model_hint = ""
                for kw, model in [
                    ("gemini", "Google Gemini"),
                    ("gpt", "OpenAI GPT"),
                    ("claude", "Anthropic Claude"),
                    ("openai", "OpenAI"),
                    ("anthropic", "Anthropic"),
                ]:
                    if all_inline.count(kw) >= 3:
                        model_hint = model
                        break

                if model_hint:
                    generic_name = f"Custom AI Chatbot ({model_hint})"

                results.append(DetectedAI(
                    name=generic_name,
                    category="chatbot",
                    risk_level="limited",
                    ai_act_article="čl. 50 odst. 1",
                    action_required="Na webu detekován vlastní AI chatbot. "
                                   "Každý AI chatbot musí být transparentně označen "
                                   "dle čl. 50 AI Act — uživatel musí vědět, "
                                   "že komunikuje s AI, ne s člověkem.",
                    description_cs=f"Heuristicky detekován AI chatbot na webu "
                                  f"(slovo 'chatbot' nalezeno {chatbot_freq}× v kódu"
                                  f"{f', model: {model_hint}' if model_hint else ''}).",
                    matched_signatures=[f"keyword_freq:chatbot={chatbot_freq}"],
                    evidence=[f"Keyword frequency: 'chatbot' = {chatbot_freq}×"],
                    confidence=min(0.90, 0.5 + chatbot_freq * 0.02),
                ))

        return results


def detect_ai_systems(page: ScannedPage) -> list[DetectedAI]:
    """Convenience funkce — detekuje AI systémy na stránce."""
    detector = AIDetector()
    return detector.detect(page)
