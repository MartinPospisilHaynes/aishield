"""
AIshield.cz — AI Detector v3
Porovnává výsledky web scanneru s databází AI signatur.
Najde AI systémy na stránce.

v3: Network Interceptor integration — zachytává REÁLNÉ network requesty
    na AI API (api.openai.com, api.anthropic.com...) s confidence 0.95.
    Plus heuristická detekce z v2.
"""

import re
from dataclasses import dataclass
from backend.scanner.web_scanner import ScannedPage
from backend.scanner.signatures import AISignature, get_all_signatures
from backend.scanner.network_interceptor import NetworkInterceptor, NetworkAnalysisResult
import logging

logger = logging.getLogger(__name__)


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
    (r"api\.groq\.com", "Groq API"),
    (r"api\.fireworks\.ai", "Fireworks AI API"),
    (r"api\.deepinfra\.com", "DeepInfra API"),
    (r"api\.anyscale\.com", "Anyscale API"),
    (r"inference\.cerebras\.ai", "Cerebras API"),
    (r"api\.sambanova\.ai", "SambaNova API"),
    (r"api-free\.deepl\.com|api\.deepl\.com", "DeepL Translation API"),
    (r"api\.stability\.ai", "Stability AI API"),
    (r"api\.runwayml\.com", "Runway ML API"),
    (r"api\.elevenlabs\.io", "ElevenLabs Voice AI"),
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
    r"/api/(?:chat|ai|completion|generate|stream)",
    r"/v1/(?:chat|completions|embeddings|images)",
    r"(?:chat|ai|bot)(?:api|endpoint|backend|service)",
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

        # ── 2. Network Interceptor — zachytí REÁLNÉ API volání ──
        interceptor = NetworkInterceptor()
        net_result: NetworkAnalysisResult = interceptor.analyze(
            network_requests=page.network_requests,
            response_data=getattr(page, "network_data", None),
        )

        if net_result.ai_requests:
            logger.info(
                f"[Detector] NetworkInterceptor: {len(net_result.ai_requests)} "
                f"přímých AI API volání zachyceno!"
            )
            for evidence in net_result.ai_requests:
                if evidence.matched_api.lower() not in " ".join(found_names):
                    results.append(DetectedAI(
                        name=evidence.matched_api,
                        category=evidence.category,
                        risk_level=evidence.risk_level,
                        ai_act_article=evidence.ai_act_article,
                        action_required=f"SÍŤOVÝ DŮKAZ: {evidence.description_cs} "
                                       "AI systém musí být transparentně označen dle AI Act.",
                        description_cs=evidence.description_cs,
                        matched_signatures=[f"network_intercept:{evidence.url[:150]}"],
                        evidence=[
                            f"Network: {evidence.method} {evidence.url[:200]}",
                            f"Status: {evidence.response_status}",
                            f"Resource: {evidence.resource_type}",
                        ],
                        confidence=evidence.confidence,
                    ))
                    found_names.add(evidence.matched_api.lower())

        if net_result.proxy_suspects:
            logger.info(
                f"[Detector] NetworkInterceptor: {len(net_result.proxy_suspects)} "
                f"podezřelých proxy endpointů"
            )

        # ── 3. Heuristic detection ──
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

        # 1. Hledáme v HTML (word boundary + skip comments)
        for pattern in sig.signatures:
            pat_lower = pattern.lower()
            match = self._word_boundary_search(pat_lower, html_lower)
            if match:
                idx = match.start()
                # Skip matches inside HTML comments
                if self._is_in_html_comment(html_lower, idx):
                    continue
                matched.append(f"html:{pattern}")
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

        # 3. Hledáme v inline skriptech (word boundary)
        for inline in page.inline_scripts:
            inline_lower = inline.lower()
            for pattern in sig.signatures:
                match = self._word_boundary_search(pattern.lower(), inline_lower)
                if match:
                    matched.append(f"inline:{pattern}")
                    idx = match.start()
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
    # HELPER METHODS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @staticmethod
    def _word_boundary_search(pattern: str, text: str) -> re.Match | None:
        """Search for pattern with smart word boundaries to avoid partial matches.
        E.g. 'frase' won't match 'paraphrase', 'drift' won't match 'adrift'."""
        if not pattern:
            return None
        escaped = re.escape(pattern)
        prefix = r'\b' if pattern[0].isalnum() or pattern[0] == '_' else ''
        suffix = r'\b' if pattern[-1].isalnum() or pattern[-1] == '_' else ''
        return re.search(prefix + escaped + suffix, text)

    @staticmethod
    def _is_in_html_comment(html: str, idx: int) -> bool:
        """Check if position idx is inside an HTML comment <!-- ... -->."""
        comment_start = html.rfind('<!--', 0, idx)
        if comment_start == -1:
            return False
        comment_end = html.find('-->', comment_start)
        return comment_end == -1 or comment_end > idx

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # HEURISTICKÁ DETEKCE (v2, doplňuje Network Interceptor)
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
                        confidence=0.50,
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
                        ai_act_article="čl. 50 odst. 2 — transparenční povinnost (SPLNĚNA)",
                        action_required="✅ Váš web již splňuje čl. 50 AI Act — transparenční "
                                       "oznámení o používání AI je aktivně nasazeno a informuje "
                                       "návštěvníky. Žádná další akce není potřeba.",
                        description_cs="Na webu nalezeno aktivní transparenční oznámení o používání AI. "
                                      "Web informuje návštěvníky, že využívá umělou inteligenci — "
                                      "tím splňuje transparenční povinnost dle čl. 50 AI Act.",
                        matched_signatures=[f"transparency:{pattern}"],
                        evidence=[f"Text: ...{snippet}..."],
                        confidence=0.90,
                    ))
                    already_found.add(notice_name.lower())
                break  # Stačí jeden transparency match

        # ── 2f. Chatbot keyword frequency ──
        chatbot_freq = html_lower.count("chatbot") + all_inline.count("chatbot")
        # Slovo "chatbot" 25+ krát na stránce = silný indikátor
        if chatbot_freq >= 25:
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

        # ── 2g. CSP Header Analysis ──
        # Hledáme Content-Security-Policy v meta tagu nebo inline HTML
        csp_match = re.search(
            r'<meta\s+http-equiv=["\']content-security-policy["\']\s+content=["\']([^"\']+)',
            html_lower, re.IGNORECASE,
        )
        if csp_match:
            csp_value = csp_match.group(1)
            csp_ai_domains = [
                ("openai.com", "OpenAI"),
                ("anthropic.com", "Anthropic"),
                ("googleapis.com/ai", "Google AI"),
                ("generativelanguage.googleapis.com", "Google Gemini"),
                ("huggingface.co", "Hugging Face"),
                ("replicate.com", "Replicate"),
                ("cohere.ai", "Cohere"),
                ("mistral.ai", "Mistral"),
                ("stability.ai", "Stability AI"),
                ("deepl.com", "DeepL"),
            ]
            for domain, name in csp_ai_domains:
                if domain in csp_value:
                    csp_name = f"CSP povolení: {name}"
                    if csp_name.lower() not in " ".join(already_found):
                        results.append(DetectedAI(
                            name=csp_name,
                            category="chatbot",
                            risk_level="limited",
                            ai_act_article="čl. 50 odst. 1",
                            action_required=f"V CSP hlavičce webu je povolena doména {domain}, "
                                           "což indikuje komunikaci s AI službou.",
                            description_cs=f"V Content-Security-Policy je povolena AI doména "
                                          f"{domain} ({name}). Web komunikuje s AI službou.",
                            matched_signatures=[f"csp:{domain}"],
                            evidence=[f"CSP: {csp_value[:200]}"],
                            confidence=0.90,
                        ))
                        already_found.add(csp_name.lower())

        # ── 2h. WebSocket / SSE detekce AI streamingu ──
        ws_ai_patterns = [
            (r"wss?://[^\"'\s]*(?:chat|ai|bot|gpt|gemini|claude|openai)", "WebSocket AI"),
            (r"text/event-stream", "SSE AI Streaming"),
            (r"EventSource\s*\(\s*[\"'][^\"']*(?:chat|ai|completion|stream)", "SSE AI Endpoint"),
        ]
        for pattern, ws_name in ws_ai_patterns:
            ws_match = re.search(pattern, all_text, re.IGNORECASE)
            if ws_match and ws_name.lower() not in " ".join(already_found):
                snippet = all_text[max(0, ws_match.start()-30):ws_match.end()+60].replace("\n", " ").strip()
                results.append(DetectedAI(
                    name=ws_name,
                    category="chatbot",
                    risk_level="limited",
                    ai_act_article="čl. 50 odst. 1",
                    action_required="Detekováno real-time AI streaming spojení. "
                                   "AI systém musí být transparentně označen.",
                    description_cs=f"Detekován {ws_name} — web používá real-time "
                                  "streamování odpovědí z AI modelu.",
                    matched_signatures=[f"streaming:{pattern}"],
                    evidence=[f"Kód: ...{snippet}..."],
                    confidence=0.80,
                ))
                already_found.add(ws_name.lower())

        # ── 2i. localStorage/sessionStorage AI klíče ──
        storage_ai_patterns = [
            r"(?:local|session)Storage\.(?:set|get)Item\s*\(\s*[\"'](?:[^\"']*(?:ai[_-]|chatbot|chat[_-]session|gpt|gemini|claude|bot[_-]config|assistant))[^\"']*[\"']",
        ]
        for pattern in storage_ai_patterns:
            st_match = re.search(pattern, all_inline, re.IGNORECASE)
            if st_match:
                snippet = all_inline[max(0, st_match.start()-20):st_match.end()+40].replace("\n", " ").strip()
                storage_name = "AI Session Storage"
                if storage_name.lower() not in " ".join(already_found):
                    results.append(DetectedAI(
                        name=storage_name,
                        category="chatbot",
                        risk_level="limited",
                        ai_act_article="čl. 50 odst. 1",
                        action_required="Web ukládá AI session data do prohlížeče. "
                                       "AI systém musí být transparentně označen.",
                        description_cs="V kódu webu detekováno ukládání AI session dat "
                                      "do localStorage/sessionStorage prohlížeče.",
                        matched_signatures=[f"storage:{pattern}"],
                        evidence=[f"Kód: ...{snippet}..."],
                        confidence=0.70,
                    ))
                    already_found.add(storage_name.lower())

        # ── 2j. Meta tag AI indikátory ──
        ai_meta_patterns = [
            (r'<meta\s+name=["\']generator["\']\s+content=["\'][^"\']*(?:ai|gpt|gemini|openai|anthropic|chatgpt)[^"\']*["\']', "AI Generator Meta"),
            (r'data-ai-(?:model|provider|version|type)\s*=\s*["\']', "AI Data Attribute"),
            (r'<meta\s+name=["\']ai[_-]?(?:disclosure|policy|system|provider)["\']', "AI Meta Disclosure"),
        ]
        for pattern, meta_name in ai_meta_patterns:
            meta_match = re.search(pattern, html_lower, re.IGNORECASE)
            if meta_match and meta_name.lower() not in " ".join(already_found):
                snippet = page.html[max(0, meta_match.start()-10):meta_match.end()+60].replace("\n", " ").strip()
                results.append(DetectedAI(
                    name=meta_name,
                    category="content_gen",
                    risk_level="limited",
                    ai_act_article="čl. 50 odst. 2",
                    action_required="Web v meta datech deklaruje využití AI. "
                                   "AI systém musí být kompletně dokumentován.",
                    description_cs=f"V HTML meta datech nalezen indikátor AI systému.",
                    matched_signatures=[f"meta:{pattern}"],
                    evidence=[f"HTML: ...{snippet}..."],
                    confidence=0.85,
                ))
                already_found.add(meta_name.lower())

        # ── 2k. AI disclosure page links ──
        disclosure_patterns = [
            r'href=["\'][^"\']*(?:/ai[_-]?disclosure|/ai[_-]?policy|/artificial[_-]?intelligence|/ai[_-]?transparency|/ai[_-]?ethics|/pouziti[_-]?ai|/ai[_-]?informace)',
        ]
        for pattern in disclosure_patterns:
            disc_match = re.search(pattern, html_lower, re.IGNORECASE)
            if disc_match:
                snippet = page.html[max(0, disc_match.start()):disc_match.end()+50].replace("\n", " ").strip()
                disc_name = "AI Disclosure Page"
                if disc_name.lower() not in " ".join(already_found):
                    results.append(DetectedAI(
                        name=disc_name,
                        category="content_gen",
                        risk_level="limited",
                        ai_act_article="čl. 50",
                        action_required="Web má stránku o AI disclosure — ověřte, "
                                       "že splňuje požadavky čl. 50 AI Act.",
                        description_cs="Na webu nalezen odkaz na stránku o transparenci AI. "
                                      "Web pravděpodobně používá AI systémy a částečně "
                                      "plní transparenční povinnosti.",
                        matched_signatures=[f"disclosure:{pattern}"],
                        evidence=[f"HTML: ...{snippet}..."],
                        confidence=0.90,
                    ))
                    already_found.add(disc_name.lower())

        # ── 2l. Global AI variable fingerprinting ──
        global_var_patterns = [
            (r"window\.VF_", "Voiceflow"),
            (r"window\.__twk", "Tawk.to"),
            (r"window\.Intercom\b", "Intercom"),
            (r"window\.drift\b", "Drift"),
            (r"window\.HubSpotConversations", "HubSpot Chat"),
            (r"window\.fcWidget", "Freshchat"),
            (r"window\.Beacon\b", "Help Scout"),
            (r"window\.zE\b", "Zendesk"),
            (r"window\.LiveChatWidget", "LiveChat"),
            (r"window\.$crisp", "Crisp"),
            (r"window\.chatwootSettings", "Chatwoot"),
            (r"window\.kommunicate", "Kommunicate"),
            (r"window\.adaSettings", "Ada"),
            (r"window\.botpressWebChat", "Botpress"),
        ]
        for pattern, var_name in global_var_patterns:
            if re.search(pattern, all_inline):
                # Jen přidáme extra evidenci pokud chatbot ještě nebyl nalezen
                found_key = var_name.lower()
                if found_key not in " ".join(already_found):
                    results.append(DetectedAI(
                        name=var_name,
                        category="chatbot",
                        risk_level="limited",
                        ai_act_article="čl. 50 odst. 1",
                        action_required=f"{var_name} AI chatbot musí být transparentně označen.",
                        description_cs=f"Detekována globální JS proměnná {var_name}.",
                        matched_signatures=[f"global_var:{pattern}"],
                        evidence=[f"Global variable: {pattern}"],
                        confidence=0.85,
                    ))
                    already_found.add(found_key)

        # ── 2m. Service Worker / Web Worker AI detekce ──
        sw_patterns = [
            r"navigator\.serviceWorker\.register\s*\(\s*[\"'][^\"']*(?:chat|ai|bot|assistant)[^\"']*[\"']",
            r"new\s+Worker\s*\(\s*[\"'][^\"']*(?:ai|ml|inference|model|wasm|onnx|tf)[^\"']*[\"']",
        ]
        for pattern in sw_patterns:
            sw_match = re.search(pattern, all_inline, re.IGNORECASE)
            if sw_match:
                snippet = all_inline[max(0, sw_match.start()-20):sw_match.end()+40].replace("\n", " ").strip()
                sw_name = "AI Web Worker"
                if sw_name.lower() not in " ".join(already_found):
                    results.append(DetectedAI(
                        name=sw_name,
                        category="chatbot",
                        risk_level="limited",
                        ai_act_article="čl. 50 odst. 1",
                        action_required="Detekován AI Web Worker — web pravděpodobně "
                                       "spouští AI inference přímo v prohlížeči.",
                        description_cs="Detekován Service Worker nebo Web Worker s AI funkcemi. "
                                      "Web může spouštět AI model přímo v prohlížeči klienta.",
                        matched_signatures=[f"worker:{pattern}"],
                        evidence=[f"Kód: ...{snippet}..."],
                        confidence=0.75,
                    ))
                    already_found.add(sw_name.lower())

        # ── 2n. WASM / WebGPU AI inference ──
        wasm_patterns = [
            r"WebAssembly\.instantiate",
            r"\.wasm\b",
            r"onnxruntime",
            r"tensorflow.*wasm",
            r"@xenova/transformers",
            r"navigator\.gpu\b",
            r"webnn\b",
            r"ml5\.js",
        ]
        wasm_evidence = []
        for pattern in wasm_patterns:
            wasm_match = re.search(pattern, all_inline, re.IGNORECASE)
            if wasm_match:
                snippet = all_inline[max(0, wasm_match.start()-20):wasm_match.end()+30].replace("\n", " ").strip()
                wasm_evidence.append(f"Kód: ...{snippet}...")
        if len(wasm_evidence) >= 2:
            wasm_name = "Client-side AI Inference"
            if wasm_name.lower() not in " ".join(already_found):
                results.append(DetectedAI(
                    name=wasm_name,
                    category="chatbot",
                    risk_level="limited",
                    ai_act_article="čl. 50 odst. 1",
                    action_required="Detekována AI inference v prohlížeči (WASM/WebGPU). "
                                   "I lokálně spouštěné AI modely musí být transparentně označeny.",
                    description_cs="Na webu detekováno spouštění AI modelu přímo v prohlížeči "
                                  "pomocí WebAssembly, ONNX Runtime nebo WebGPU.",
                    matched_signatures=["wasm_ai_inference"],
                    evidence=wasm_evidence[:5],
                    confidence=0.80,
                ))
                already_found.add(wasm_name.lower())

        # ── 2o. AI cookie patterns (generické) ──
        ai_cookie_keywords = ["_ai_", "_chatbot", "_bot_id", "_assistant", "gpt_session",
                              "_ml_", "ai_consent", "chatgpt", "gemini_"]
        for cookie in page.cookies:
            cname = cookie["name"].lower()
            for kw in ai_cookie_keywords:
                if kw in cname:
                    cookie_name = f"AI Cookie ({cookie['name']})"
                    if cookie_name.lower() not in " ".join(already_found):
                        results.append(DetectedAI(
                            name="AI Session Cookie",
                            category="chatbot",
                            risk_level="limited",
                            ai_act_article="čl. 50 odst. 1",
                            action_required="Detekován AI-related cookie. "
                                           "AI systém musí být uveden v cookie banneru.",
                            description_cs=f"Cookie '{cookie['name']}' naznačuje přítomnost "
                                          "AI systému na webu.",
                            matched_signatures=[f"cookie_heuristic:{kw}"],
                            evidence=[f"Cookie: {cookie['name']} (domain: {cookie['domain']})"],
                            confidence=0.65,
                        ))
                        already_found.add(cookie_name.lower())
                    break

        # ── 2p. Schema.org AI markup ──
        schema_ai_patterns = [
            r'"@type"\s*:\s*"(?:AIApplication|SoftwareApplication)"[^}]*"(?:name|applicationCategory)"\s*:\s*"[^"]*(?:ai|chatbot|assistant|machine learning)',
            r'"@type"\s*:\s*"WebSite"[^}]*"potentialAction"[^}]*"(?:ai|chatbot|search)"',
            r'"usesAI"\s*:\s*(?:true|"true")',
            r'"ai(?:System|Provider|Model)"\s*:',
        ]
        for pattern in schema_ai_patterns:
            schema_match = re.search(pattern, html_lower, re.IGNORECASE)
            if schema_match:
                snippet = page.html[max(0, schema_match.start()-20):schema_match.end()+60].replace("\n", " ").strip()
                schema_name = "Schema.org AI Markup"
                if schema_name.lower() not in " ".join(already_found):
                    results.append(DetectedAI(
                        name=schema_name,
                        category="content_gen",
                        risk_level="limited",
                        ai_act_article="čl. 50",
                        action_required="Web ve structured data deklaruje AI funkce. "
                                       "Ověřte kompletnost AI Act compliance.",
                        description_cs="V Schema.org structured data nalezeny indikátory "
                                      "AI systému na webu.",
                        matched_signatures=[f"schema:{pattern}"],
                        evidence=[f"Structured data: ...{snippet}..."],
                        confidence=0.85,
                    ))
                    already_found.add(schema_name.lower())
                break

        return results

    def detect_trackers(self, page: ScannedPage) -> list[dict]:
        """
        Detekuje non-AI sledovací systémy na stránce.
        Vrací seznam {name, category, description_cs, icon, evidence}.
        Tyto systémy NESPADAJÍ pod AI Act — zobrazujeme je pro důvěryhodnost.
        """
        from backend.scanner.signatures import get_all_trackers
        trackers = get_all_trackers()
        results: list[dict] = []
        found_names: set[str] = set()

        html_lower = page.html.lower()
        script_urls = [s.lower() for s in page.scripts]
        cookies = page.cookies

        for tracker in trackers:
            matched: list[str] = []
            evidence: list[str] = []

            # HTML signature matching
            for sig in tracker.signatures:
                if sig.lower() in html_lower:
                    matched.append(f"html:{sig}")
                    idx = html_lower.find(sig.lower())
                    snippet = page.html[max(0, idx-20):idx+len(sig)+30].strip()
                    if snippet:
                        evidence.append(f"HTML: ...{snippet[:80]}...")

            # Script URL matching
            for sp in tracker.script_patterns:
                for su in script_urls:
                    if sp.lower() in su:
                        matched.append(f"script:{sp}")
                        evidence.append(f"Script: {su[:120]}")

            # Cookie matching
            for cp in tracker.cookie_patterns:
                for cookie in cookies:
                    if cp.lower() in cookie["name"].lower():
                        matched.append(f"cookie:{cp}")
                        evidence.append(f"Cookie: {cookie['name']}")

            if matched:
                name = tracker.name
                if name.lower() not in found_names:
                    found_names.add(name.lower())
                    results.append({
                        "name": name,
                        "category": tracker.category,
                        "description_cs": tracker.description_cs,
                        "icon": tracker.icon,
                        "evidence": evidence[:3],
                        "matched_count": len(matched),
                    })

        return results


def detect_page(page) -> list:
    """Convenience funkce — detekuje AI systémy na stránce."""
    detector = AIDetector()
    return detector.detect(page)
