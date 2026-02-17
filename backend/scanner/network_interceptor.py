"""
AIshield.cz — Network Interceptor v1
═══════════════════════════════════════════════════════════════
Sleduje REÁLNÉ síťové požadavky webu a detekuje volání na AI API.

Tohle je "game changer" — zatímco signaturový detektor hledá řetězce v HTML,
Network Interceptor zachytí SKUTEČNÉ requesty na api.openai.com, api.anthropic.com atd.
To je NEZPOCHYBNITELNÝ důkaz nasazení AI systému.

Integrace: Playwright page.on("request") + page.on("response")
"""

import re
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# AI API ENDPOINTS — kam weby volají AI služby
# ═══════════════════════════════════════════════════════════════

AI_API_ENDPOINTS = [
    # ── OpenAI ──
    {
        "pattern": r"api\.openai\.com",
        "name": "OpenAI API",
        "category": "Generativní AI",
        "risk_level": "limited",
        "ai_act_article": "Čl. 50 — Transparenční povinnosti",
        "description_cs": "Web komunikuje přímo s OpenAI API (ChatGPT/GPT modely). Prokázáno zachycením síťového požadavku.",
    },
    # ── Anthropic ──
    {
        "pattern": r"api\.anthropic\.com",
        "name": "Anthropic Claude API",
        "category": "Generativní AI",
        "risk_level": "limited",
        "ai_act_article": "Čl. 50 — Transparenční povinnosti",
        "description_cs": "Web komunikuje s Anthropic Claude API. Prokázáno zachycením síťového požadavku.",
    },
    # ── Google AI ──
    {
        "pattern": r"generativelanguage\.googleapis\.com",
        "name": "Google Gemini API",
        "category": "Generativní AI",
        "risk_level": "limited",
        "ai_act_article": "Čl. 50 — Transparenční povinnosti",
        "description_cs": "Web komunikuje s Google Gemini API. Prokázáno zachycením síťového požadavku.",
    },
    {
        "pattern": r"aiplatform\.googleapis\.com",
        "name": "Google Vertex AI",
        "category": "Generativní AI",
        "risk_level": "limited",
        "ai_act_article": "Čl. 50 — Transparenční povinnosti",
        "description_cs": "Web komunikuje s Google Vertex AI platformou. Prokázáno zachycením síťového požadavku.",
    },
    {
        "pattern": r"dialogflow\.googleapis\.com",
        "name": "Google Dialogflow",
        "category": "AI Chatbot",
        "risk_level": "limited",
        "ai_act_article": "Čl. 50 — Transparenční povinnosti",
        "description_cs": "Web používá Google Dialogflow chatbot engine. Prokázáno zachycením síťového požadavku.",
    },
    # ── Mistral ──
    {
        "pattern": r"api\.mistral\.ai",
        "name": "Mistral AI API",
        "category": "Generativní AI",
        "risk_level": "limited",
        "ai_act_article": "Čl. 50 — Transparenční povinnosti",
        "description_cs": "Web komunikuje s Mistral AI API. Prokázáno zachycením síťového požadavku.",
    },
    # ── Cohere ──
    {
        "pattern": r"api\.cohere\.ai|api\.cohere\.com",
        "name": "Cohere AI API",
        "category": "Generativní AI",
        "risk_level": "limited",
        "ai_act_article": "Čl. 50 — Transparenční povinnosti",
        "description_cs": "Web komunikuje s Cohere AI API. Prokázáno zachycením síťového požadavku.",
    },
    # ── Hugging Face ──
    {
        "pattern": r"api-inference\.huggingface\.co",
        "name": "Hugging Face Inference API",
        "category": "Generativní AI",
        "risk_level": "limited",
        "ai_act_article": "Čl. 50 — Transparenční povinnosti",
        "description_cs": "Web komunikuje s Hugging Face Inference API. Prokázáno zachycením síťového požadavku.",
    },
    # ── Replicate ──
    {
        "pattern": r"api\.replicate\.com",
        "name": "Replicate API",
        "category": "Generativní AI",
        "risk_level": "limited",
        "ai_act_article": "Čl. 50 — Transparenční povinnosti",
        "description_cs": "Web komunikuje s Replicate API (open-source AI modely). Prokázáno zachycením síťového požadavku.",
    },
    # ── Together AI ──
    {
        "pattern": r"api\.together\.xyz",
        "name": "Together AI API",
        "category": "Generativní AI",
        "risk_level": "limited",
        "ai_act_article": "Čl. 50 — Transparenční povinnosti",
        "description_cs": "Web komunikuje s Together AI API. Prokázáno zachycením síťového požadavku.",
    },
    # ── Perplexity ──
    {
        "pattern": r"api\.perplexity\.ai",
        "name": "Perplexity AI API",
        "category": "Generativní AI",
        "risk_level": "limited",
        "ai_act_article": "Čl. 50 — Transparenční povinnosti",
        "description_cs": "Web komunikuje s Perplexity AI API. Prokázáno zachycením síťového požadavku.",
    },
    # ── Groq ──
    {
        "pattern": r"api\.groq\.com",
        "name": "Groq API",
        "category": "Generativní AI",
        "risk_level": "limited",
        "ai_act_article": "Čl. 50 — Transparenční povinnosti",
        "description_cs": "Web komunikuje s Groq API (rychlé LLM inference). Prokázáno zachycením síťového požadavku.",
    },
    # ── DeepL ──
    {
        "pattern": r"api(?:-free)?\.deepl\.com",
        "name": "DeepL Translation API",
        "category": "AI Překlad",
        "risk_level": "minimal",
        "ai_act_article": "Čl. 50 — Transparenční povinnosti",
        "description_cs": "Web používá DeepL AI Translation API. Prokázáno zachycením síťového požadavku.",
    },
    # ── ElevenLabs ──
    {
        "pattern": r"api\.elevenlabs\.io",
        "name": "ElevenLabs Voice AI",
        "category": "AI Voice",
        "risk_level": "limited",
        "ai_act_article": "Čl. 50 — Transparenční povinnosti (syntetická řeč)",
        "description_cs": "Web používá ElevenLabs AI pro generování hlasu. Prokázáno zachycením síťového požadavku.",
    },
    # ── Stability AI ──
    {
        "pattern": r"api\.stability\.ai",
        "name": "Stability AI API",
        "category": "AI Obrázky",
        "risk_level": "limited",
        "ai_act_article": "Čl. 50 — Transparenční povinnosti (syntetický obsah)",
        "description_cs": "Web používá Stability AI pro generování obrázků. Prokázáno zachycením síťového požadavku.",
    },
    # ── Fireworks AI ──
    {
        "pattern": r"api\.fireworks\.ai",
        "name": "Fireworks AI API",
        "category": "Generativní AI",
        "risk_level": "limited",
        "ai_act_article": "Čl. 50 — Transparenční povinnosti",
        "description_cs": "Web komunikuje s Fireworks AI API. Prokázáno zachycením síťového požadavku.",
    },
    # ── Cerebras ──
    {
        "pattern": r"inference\.cerebras\.ai",
        "name": "Cerebras Inference API",
        "category": "Generativní AI",
        "risk_level": "limited",
        "ai_act_article": "Čl. 50 — Transparenční povinnosti",
        "description_cs": "Web komunikuje s Cerebras AI inference API. Prokázáno zachycením síťového požadavku.",
    },
    # ── Azure OpenAI ──
    {
        "pattern": r"\.openai\.azure\.com",
        "name": "Azure OpenAI Service",
        "category": "Generativní AI",
        "risk_level": "limited",
        "ai_act_article": "Čl. 50 — Transparenční povinnosti",
        "description_cs": "Web komunikuje s Azure OpenAI Service (enterprise GPT). Prokázáno zachycením síťového požadavku.",
    },
    # ── AWS Bedrock ──
    {
        "pattern": r"bedrock-runtime\..*\.amazonaws\.com",
        "name": "AWS Bedrock AI",
        "category": "Generativní AI",
        "risk_level": "limited",
        "ai_act_article": "Čl. 50 — Transparenční povinnosti",
        "description_cs": "Web komunikuje s AWS Bedrock AI platformou. Prokázáno zachycením síťového požadavku.",
    },
    # ── Intercom AI (Fin) ──
    {
        "pattern": r"api-iam\.intercom\.io/messenger/web/(ai|fin)",
        "name": "Intercom Fin (AI Agent)",
        "category": "AI Chatbot",
        "risk_level": "limited",
        "ai_act_article": "Čl. 50 — Transparenční povinnosti",
        "description_cs": "Web používá Intercom Fin AI agent pro komunikaci se zákazníky. Prokázáno zachycením síťového požadavku.",
    },
    # ── Drift AI ──
    {
        "pattern": r"api\.drift\.com.*/ai|chat\.drift\.com",
        "name": "Drift AI Chatbot",
        "category": "AI Chatbot",
        "risk_level": "limited",
        "ai_act_article": "Čl. 50 — Transparenční povinnosti",
        "description_cs": "Web používá Drift AI chatbot. Prokázáno zachycením síťového požadavku.",
    },
    # ── Tidio AI ──
    {
        "pattern": r"api-v2\.tidio\.co|api\.tidio\.co",
        "name": "Tidio AI Chatbot",
        "category": "AI Chatbot",
        "risk_level": "limited",
        "ai_act_article": "Čl. 50 — Transparenční povinnosti",
        "description_cs": "Web používá Tidio AI chatbot. Prokázáno zachycením síťového požadavku.",
    },
]

# ═══════════════════════════════════════════════════════════════
# AI-SPECIFIC RESPONSE HEADERS
# ═══════════════════════════════════════════════════════════════

AI_RESPONSE_HEADERS = [
    # OpenAI specific headers
    ("x-ratelimit-limit-tokens", "OpenAI API"),
    ("openai-organization", "OpenAI API"),
    ("openai-model", "OpenAI API"),
    ("openai-processing-ms", "OpenAI API"),
    # Anthropic specific headers
    ("anthropic-ratelimit-tokens-limit", "Anthropic Claude API"),
    ("x-anthropic-request-id", "Anthropic Claude API"),
    # Generic AI headers
    ("x-model-id", None),  # Generic AI model indicator
    ("x-inference-time", None),
]


@dataclass
class NetworkEvidence:
    """Jeden zachycený síťový důkaz AI systému."""
    url: str                    # Plné URL požadavku
    method: str                 # GET/POST
    resource_type: str          # xhr, fetch, websocket, script...
    matched_api: str            # Název AI API (e.g. "OpenAI API")
    category: str               # Kategorie AI systému
    risk_level: str
    ai_act_article: str
    description_cs: str
    response_status: int | None = None
    response_headers: dict = field(default_factory=dict)
    confidence: float = 0.95    # Síťový důkaz = velmi vysoká confidence


@dataclass
class NetworkAnalysisResult:
    """Výsledek síťové analýzy jedné stránky."""
    total_requests: int = 0
    ai_requests: list[NetworkEvidence] = field(default_factory=list)
    proxy_suspects: list[dict] = field(default_factory=list)
    summary: str = ""


class NetworkInterceptor:
    """
    Analyzuje zachycené síťové požadavky z Playwright a hledá
    volání na AI API endpointy.
    
    Tři úrovně detekce:
    1. PŘÍMÉ API VOLÁNÍ: Web volá api.openai.com → nezpochybnitelný důkaz
    2. RESPONSE HEADERS: Server vrací AI-specific hlavičky (x-ratelimit-limit-tokens)  
    3. PROXY DETEKCE: Web volá vlastní /api/chat, /api/ai → podezření na proxy
    """

    # Proxy patterns — vlastní backend proxy k AI API
    PROXY_PATTERNS = [
        r"/api/(?:chat|ai|completion|generate|stream|ask|query|bot)",
        r"/v1/(?:chat|completions|embeddings|images|audio)",
        r"/(?:chat|ai|bot)/(?:send|message|query|response|stream)",
        r"/api/v\d+/(?:chat|ai|message|conversation)",
        r"/webhook/(?:ai|chatbot|bot)",
    ]

    def analyze(
        self,
        network_requests: list[str],
        response_data: list[dict] | None = None,
    ) -> NetworkAnalysisResult:
        """
        Analyzuje seznam zachycených network requestů.
        
        Args:
            network_requests: Seznam URL z page.on("request")
            response_data: Volitelně i response info [{url, status, headers}]
        
        Returns:
            NetworkAnalysisResult s nalezenými AI API voláními
        """
        result = NetworkAnalysisResult(total_requests=len(network_requests))
        seen_apis: set[str] = set()  # Deduplikace

        # ── 1. Přímá API volání ──
        for req_url in network_requests:
            url_lower = req_url.lower()
            for endpoint in AI_API_ENDPOINTS:
                if re.search(endpoint["pattern"], url_lower):
                    api_name = endpoint["name"]
                    if api_name not in seen_apis:
                        seen_apis.add(api_name)
                        evidence = NetworkEvidence(
                            url=req_url[:500],  # Ořízni dlouhé URL
                            method="UNKNOWN",  # Zjistíme z enriched dat
                            resource_type="xhr/fetch",
                            matched_api=api_name,
                            category=endpoint["category"],
                            risk_level=endpoint["risk_level"],
                            ai_act_article=endpoint["ai_act_article"],
                            description_cs=endpoint["description_cs"],
                            confidence=0.95,  # Přímý API call = vysoká jistota
                        )
                        result.ai_requests.append(evidence)
                        logger.info(
                            f"[NetworkInterceptor] 🎯 PŘÍMÝ AI API CALL: "
                            f"{api_name} → {req_url[:100]}"
                        )

        # ── 2. Response headers analýza ──
        if response_data:
            for resp in response_data:
                resp_headers = resp.get("headers", {})
                resp_url = resp.get("url", "")
                for header_name, expected_api in AI_RESPONSE_HEADERS:
                    if header_name.lower() in {
                        k.lower(): v for k, v in resp_headers.items()
                    }:
                        api_name = expected_api or f"AI service (header: {header_name})"
                        if api_name not in seen_apis:
                            seen_apis.add(api_name)
                            evidence = NetworkEvidence(
                                url=resp_url[:500],
                                method="RESPONSE",
                                resource_type="response_header",
                                matched_api=api_name,
                                category="Generativní AI",
                                risk_level="limited",
                                ai_act_article="Čl. 50 — Transparenční povinnosti",
                                description_cs=f"Server vrací AI-specific hlavičku '{header_name}'. Indikátor AI systému.",
                                response_status=resp.get("status"),
                                response_headers={header_name: resp_headers.get(header_name, "")},
                                confidence=0.85,
                            )
                            result.ai_requests.append(evidence)
                            logger.info(
                                f"[NetworkInterceptor] 🔍 AI HEADER: "
                                f"{header_name} v odpovědi z {resp_url[:80]}"
                            )

        # ── 3. Proxy detekce (nižší confidence — potřebuje verifikaci) ──
        base_url = self._extract_base_url(network_requests)
        for req_url in network_requests:
            # Hledáme jen requesty na STEJNOU doménu (vlastní proxy)
            if base_url and base_url in req_url.lower():
                for proxy_pattern in self.PROXY_PATTERNS:
                    if re.search(proxy_pattern, req_url, re.IGNORECASE):
                        result.proxy_suspects.append({
                            "url": req_url[:500],
                            "pattern": proxy_pattern,
                            "note": "Podezření na AI proxy endpoint — web pravděpodobně proxy-uje requesty na AI API přes vlastní backend.",
                        })
                        logger.info(
                            f"[NetworkInterceptor] ⚠️ PROXY SUSPECT: "
                            f"{req_url[:100]} (pattern: {proxy_pattern})"
                        )
                        break  # Jeden URL matchne jen jednou

        # ── Shrnutí ──
        if result.ai_requests:
            apis = ", ".join(sorted(seen_apis))
            result.summary = (
                f"Zachyceno {len(result.ai_requests)} přímých AI API volání: {apis}. "
                f"Celkem {result.total_requests} síťových požadavků analyzováno."
            )
        elif result.proxy_suspects:
            result.summary = (
                f"Žádné přímé AI API volání, ale {len(result.proxy_suspects)} "
                f"podezřelých proxy endpointů detekováno."
            )
        else:
            result.summary = (
                f"Analyzováno {result.total_requests} síťových požadavků — "
                f"žádné AI API volání detekováno."
            )

        logger.info(f"[NetworkInterceptor] {result.summary}")
        return result

    @staticmethod
    def _extract_base_url(urls: list[str]) -> str:
        """Extrahuje base doménu z prvního URL."""
        if not urls:
            return ""
        from urllib.parse import urlparse
        try:
            parsed = urlparse(urls[0])
            return parsed.netloc.lower()
        except Exception:
            return ""
