"""
AIshield.cz — Shared LLM Engine (v2)

Sdílená infrastruktura pro volání Gemini a Claude.
Retry logika, JSON parsing, cost tracking.
Používáno všemi 4 moduly pipeline.

v2: Primární Gemini přes Vertex AI (global region), fallback na AI Studio.
"""

import asyncio
import json
import logging
import os
import re
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# ── Model konfigurace ──
GEMINI_MODEL = "gemini-3.1-pro-preview"
GEMINI_FLASH_MODEL = "gemini-2.5-flash"
CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_FALLBACK_MODEL = "claude-opus-4-6"

# ── Vertex AI konfigurace ──
VERTEX_PROJECT = "gen-lang-client-0075067558"
VERTEX_LOCATION = "global"
VERTEX_SA_KEY_PATH = "/opt/aishield/vertex-sa-key.json"

GEMINI_COST_INPUT = 2.0 / 1_000_000
GEMINI_COST_OUTPUT = 12.0 / 1_000_000
GEMINI_FLASH_COST_INPUT = 0.15 / 1_000_000   # Gemini 2.5 Flash
GEMINI_FLASH_COST_OUTPUT = 0.60 / 1_000_000   # Gemini 2.5 Flash
CLAUDE_COST_INPUT = 3.0 / 1_000_000
CLAUDE_COST_OUTPUT = 15.0 / 1_000_000
CLAUDE_FALLBACK_COST_INPUT = 5.0 / 1_000_000
CLAUDE_FALLBACK_COST_OUTPUT = 25.0 / 1_000_000

# Context caching: minimum ~32K tokens (~128K chars) pro Gemini
CONTEXT_CACHE_MIN_CHARS = 100_000  # ~25K tokens, bezpečná hranice

# ── Singleton klienti ──
_gemini_client = None
_gemini_backend = None
_gemini_cache = None  # cached_content name pro context caching
_gemini_cache_key = None  # hash klíč pro invalidaci cache


def _create_gemini_client():
    """
    Vytvoří Gemini klienta (SINGLETON — vytvořen jednou, sdílen napříč voláními).
    Priorita:
    1. Vertex AI (service account) — vyšší kvóty, placené
    2. AI Studio (API key) — nižší kvóty, fallback
    """
    global _gemini_client, _gemini_backend

    if _gemini_client is not None:
        return _gemini_client, _gemini_backend

    from google import genai

    # Pokus 1: Vertex AI přes service account
    sa_key = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", VERTEX_SA_KEY_PATH)
    if os.path.exists(sa_key):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = sa_key
        try:
            client = genai.Client(
                vertexai=True,
                project=VERTEX_PROJECT,
                location=VERTEX_LOCATION,
            )
            logger.info("[LLM Engine] Gemini client: Vertex AI (%s/%s) [singleton]", VERTEX_PROJECT, VERTEX_LOCATION)
            _gemini_client = client
            _gemini_backend = "vertex"
            return client, "vertex"
        except Exception as e:
            logger.warning("[LLM Engine] Vertex AI init selhalo: %s — zkouším AI Studio", e)

    # Pokus 2: AI Studio přes API key
    from backend.config import get_settings
    settings = get_settings()
    api_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY", "")
    if api_key:
        client = genai.Client(api_key=api_key)
        logger.info("[LLM Engine] Gemini client: AI Studio (API key) [singleton]")
        _gemini_client = client
        _gemini_backend = "ai_studio"
        return client, "ai_studio"

    raise RuntimeError("Gemini: ani Vertex AI SA klíč ani GEMINI_API_KEY není dostupný")


def _try_context_cache(client, system: str, context_prefix: str = "") -> Optional[str]:
    """
    Pokusí se vytvořit context cache pro system prompt + kontext.
    Vrátí cache name pokud úspěšné, None pokud obsah je příliš malý nebo cache selže.
    """
    global _gemini_cache, _gemini_cache_key
    import hashlib
    from google.genai import types

    combined = system + context_prefix
    cache_key = hashlib.md5(combined.encode()).hexdigest()

    # Pokud cache existuje pro stejný obsah, vrátit
    if _gemini_cache and _gemini_cache_key == cache_key:
        return _gemini_cache

    # Zkontrolovat minimální velikost
    if len(combined) < CONTEXT_CACHE_MIN_CHARS:
        logger.debug("[LLM Engine] Context cache: obsah příliš malý (%d znaků < %d min), přeskakuji",
                     len(combined), CONTEXT_CACHE_MIN_CHARS)
        return None

    try:
        cached = client.caches.create(
            model=model or GEMINI_MODEL,
            config=types.CreateCachedContentConfig(
                system_instruction=system,
                contents=[types.Content(
                    role="user",
                    parts=[types.Part(text=context_prefix)],
                )] if context_prefix else None,
                ttl="3600s",
                display_name="aishield-pipeline-context",
            ),
        )
        _gemini_cache = cached.name
        _gemini_cache_key = cache_key
        logger.info("[LLM Engine] Context cache vytvořen: %s (%d znaků)", cached.name, len(combined))
        return cached.name
    except Exception as e:
        logger.warning("[LLM Engine] Context cache selhalo: %s", e)
        return None


# ══════════════════════════════════════════════════════════════════════
# GEMINI CALL
# ══════════════════════════════════════════════════════════════════════

async def call_gemini(
    system: str,
    prompt: str,
    label: str = "gemini",
    temperature: float = 0.1,
    max_tokens: int = 16000,
    retries: int = 4,
    model: str = None,
    cost_input: float = None,
    cost_output: float = None,
) -> Tuple[str, dict]:
    """
    Zavolá Gemini API. Vrací (text, metadata).
    Primárně přes Vertex AI, fallback na AI Studio, pak Claude.
    Retry s exponenciálním backoff na 429/503.
    """
    from google.genai import types

    client, backend = _create_gemini_client()

    # Zkusit context caching pro system prompt
    cache_name = _try_context_cache(client, system)

    for attempt in range(retries):
        try:
            config_kwargs = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            if cache_name:
                config_kwargs["cached_content"] = cache_name
            else:
                config_kwargs["system_instruction"] = system

            response = await client.aio.models.generate_content(
                model=model or GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(**config_kwargs),
            )

            text = response.text or ""
            usage = response.usage_metadata
            in_tok = getattr(usage, "prompt_token_count", 0) or 0
            out_tok = getattr(usage, "candidates_token_count", 0) or 0
            cost = (in_tok * (cost_input or GEMINI_COST_INPUT)) + (out_tok * (cost_output or GEMINI_COST_OUTPUT))

            logger.info(
                "[LLM Engine] %s Gemini: tokens=%d+%d, cost=$%.4f, len=%d",
                label, in_tok, out_tok, cost, len(text),
            )

            meta = {
                "provider": "gemini", "model": model or GEMINI_MODEL,
                "backend": backend,
                "input_tokens": in_tok, "output_tokens": out_tok,
                "cost_usd": cost,
            }
            return text, meta

        except Exception as e:
            err = str(e)
            logger.warning("[LLM Engine] %s Gemini attempt %d: %s", label, attempt + 1, err)
            if "429" in err or "RESOURCE_EXHAUSTED" in err or "503" in err:
                delay_match = re.search(r"retryDelay.*?(\d+\.?\d*)", err)
                wait = float(delay_match.group(1)) + 1.0 if delay_match else min(5 * (2 ** attempt), 30)
                logger.info("[LLM Engine] %s: rate-limited, čekám %.0fs...", label, wait)
                await asyncio.sleep(wait)
                continue
            if attempt == retries - 1:
                raise

    # ── Fallback na Claude, pokud Gemini vyčerpala denní kvótu ──
    logger.warning(
        "[LLM Engine] %s: Gemini selhala po %d pokusech — zkouším fallback na Claude Sonnet...",
        label, retries,
    )
    try:
        text, meta = await call_claude(
            system=system,
            prompt=prompt,
            label=f"{label}_gemini_fallback",
            temperature=temperature,
            max_tokens=max_tokens,
        )
        meta["fallback_from"] = "gemini"
        meta["original_model"] = model or GEMINI_MODEL
        logger.info("[LLM Engine] %s: Gemini→Claude fallback úspěšný (%d znaků)", label, len(text))
        return text, meta
    except Exception as fallback_err:
        logger.error("[LLM Engine] %s: Gemini i Claude fallback selhaly: %s", label, fallback_err)
        raise RuntimeError(
            f"Gemini selhala po {retries} pokusech a Claude fallback také selhal pro {label}: {fallback_err}"
        )


# ══════════════════════════════════════════════════════════════════════
# CLAUDE CALL
# ══════════════════════════════════════════════════════════════════════

async def call_claude(
    system: str,
    prompt: str,
    label: str = "claude",
    temperature: float = 0.1,
    max_tokens: int = 16000,
    retries: int = 6,
    model: str = None,
) -> Tuple[str, dict]:
    """
    Zavolá Claude (Anthropic) API. Vrací (text, metadata).
    Fallback: Sonnet 4.6 → Opus 4.6 při přetížení (529/503).
    """
    import anthropic
    from backend.config import get_settings

    settings = get_settings()
    api_key = settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY není nastavený")

    client = anthropic.AsyncAnthropic(api_key=api_key)

    # If explicit model requested, use only that; otherwise Sonnet -> Opus fallback
    if model == "claude-opus-4-6":
        models_to_try = [
            (CLAUDE_FALLBACK_MODEL, CLAUDE_FALLBACK_COST_INPUT, CLAUDE_FALLBACK_COST_OUTPUT, retries),
        ]
    elif model:
        models_to_try = [
            (model, CLAUDE_COST_INPUT, CLAUDE_COST_OUTPUT, retries),
        ]
    else:
        models_to_try = [
            (CLAUDE_MODEL, CLAUDE_COST_INPUT, CLAUDE_COST_OUTPUT, 3),
            (CLAUDE_FALLBACK_MODEL, CLAUDE_FALLBACK_COST_INPUT, CLAUDE_FALLBACK_COST_OUTPUT, 3),
        ]

    last_error = None
    for model, cost_in, cost_out, model_retries in models_to_try:
        for attempt in range(model_retries):
            try:
                response = await client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system,
                    messages=[{"role": "user", "content": prompt}],
                )

                text = response.content[0].text if response.content else ""
                in_tok = response.usage.input_tokens if response.usage else 0
                out_tok = response.usage.output_tokens if response.usage else 0
                cost = (in_tok * cost_in) + (out_tok * cost_out)

                logger.info(
                    "[LLM Engine] %s %s: tokens=%d+%d, cost=$%.4f, len=%d",
                    label, model, in_tok, out_tok, cost, len(text),
                )

                meta = {
                    "provider": "claude", "model": model,
                    "input_tokens": in_tok, "output_tokens": out_tok,
                    "cost_usd": cost,
                }
                return text, meta

            except Exception as e:
                err = str(e)
                status_code = getattr(e, "status_code", 0) or 0
                logger.warning("[LLM Engine] %s %s attempt %d (status=%s): %s",
                               label, model, attempt + 1, status_code, err)
                last_error = e

                is_overloaded = (
                    "overloaded" in err.lower()
                    or "529" in err
                    or status_code == 529
                )
                is_retryable = (
                    is_overloaded
                    or "rate" in err.lower()
                    or "503" in err
                    or "500" in err
                    or status_code in (429, 500, 503)
                )

                if is_retryable:
                    if is_overloaded and attempt >= 1:
                        # After 2 overloaded attempts, skip to fallback model
                        logger.info("[LLM Engine] %s: %s overloaded %d×, přepínám na fallback...",
                                    label, model, attempt + 1)
                        break
                    wait = min(10 * (2 ** attempt), 60)
                    logger.info("[LLM Engine] %s: retryable error, čekám %.0fs...", label, wait)
                    await asyncio.sleep(wait)
                    continue
                # Non-retryable error — try fallback model
                if status_code == 404:
                    logger.warning("[LLM Engine] %s: %s vrátil 404, zkouším fallback...", label, model)
                    break
                if attempt == model_retries - 1:
                    raise

        # If we broke out of retry loop (overloaded/404), continue to next model
        logger.info("[LLM Engine] %s: přepínám z %s na další model...", label, model)

    raise RuntimeError(f"Claude selhala na všech modelech ({CLAUDE_MODEL}, {CLAUDE_FALLBACK_MODEL}) pro {label}: {last_error}")


# ══════════════════════════════════════════════════════════════════════
# JSON PARSER — robustní extrakce JSON z LLM výstupu
# ══════════════════════════════════════════════════════════════════════

def parse_json(text: str) -> Optional[dict]:
    """Robustně extrahuje JSON objekt z LLM výstupu."""
    if not text:
        return None

    stripped = text.strip()
    # Odstraň markdown bloky
    stripped = re.sub(r"^```(?:json)?\s*\n?", "", stripped)
    stripped = re.sub(r"\n?```\s*$", "", stripped)
    stripped = stripped.strip()
    # Odstraň BOM
    if stripped.startswith("\ufeff"):
        stripped = stripped[1:]

    # Pokus 1: přímé parsování
    try:
        result = json.loads(stripped)
        if isinstance(result, dict):
            return result
    except (json.JSONDecodeError, ValueError):
        pass

    # Pokus 2: extrahuj balanced {}
    json_str = _extract_json_object(stripped)
    if json_str:
        try:
            result = json.loads(json_str)
            if isinstance(result, dict):
                return result
        except (json.JSONDecodeError, ValueError):
            pass

    # Pokus 3: oprav běžné problémy
    if json_str:
        cleaned = _fix_json_string(json_str)
        try:
            result = json.loads(cleaned)
            if isinstance(result, dict):
                return result
        except (json.JSONDecodeError, ValueError):
            pass

    return None


def extract_html_content(text: str) -> str:
    """
    Extrahuje HTML obsah z LLM odpovědi.
    Pokud je v JSON, vytáhne 'content' klíč.
    Pokud je surový HTML, vrátí přímo.
    """
    if not text:
        return ""

    # Detekce kompletni HTML stranky — bypass JSON parsovani
    # (Transparency page obsahuje JSON-LD <script> bloky, ktere
    #  parse_json() mylne interpretuje jako JSON odpoved LLM)
    _stripped = text.strip()
    _stripped = re.sub(r"^```(?:html)?\s*\n?", "", _stripped)
    if (_stripped.startswith("<!--") or
        _stripped.lower().startswith("<!doctype") or
        _stripped.lower().startswith("<html")):
        logger.info("[extract_html] Detekovana kompletni HTML stranka — bypass JSON parsing")
        _stripped = re.sub(r"\n?```\s*$", "", _stripped)
        return _stripped.strip()

    # Zkus JSON
    parsed = parse_json(text)
    if parsed:
        # Vrať 'content' klíč pokud existuje
        if "content" in parsed:
            return parsed["content"]
        # Hledej HTML v jakémkoliv klíči (html, page, body, output...)
        for k in ("html", "page", "body", "output", "result", "html_content"):
            if k in parsed and isinstance(parsed[k], str) and len(parsed[k]) > 50:
                return parsed[k]
        # Jinak spoj všechny HTML hodnoty
        parts = []
        for k, v in parsed.items():
            if k == "myslenkovy_proces":
                continue
            if isinstance(v, str) and len(v) > 20:
                parts.append(v)
        if parts:
            return "\n".join(parts)
        # JSON parsování vrátilo prázdno — padni na raw text extrakci
        logger.warning("[extract_html] JSON parsován ale žádný HTML obsah nenalezen, zkouším raw text")

    # Surový HTML
    stripped = text.strip()
    stripped = re.sub(r"^```(?:html)?\s*\n?", "", stripped)
    stripped = re.sub(r"\n?```\s*$", "", stripped)
    return stripped.strip()


def _extract_json_object(text: str) -> Optional[str]:
    """Najde první balanced {} blok."""
    start = text.find("{")
    if start < 0:
        return None

    depth = 0
    in_string = False
    escape = False

    for i in range(start, len(text)):
        c = text[i]
        if escape:
            escape = False
            continue
        if c == "\\":
            if in_string:
                escape = True
            continue
        if c == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]

    last_brace = text.rfind("}")
    if last_brace > start:
        return text[start : last_brace + 1]
    return None


def _fix_json_string(text: str) -> str:
    """Opraví běžné JSON problémy."""
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    text = re.sub(r",\s*([}\]])", r"\1", text)

    result = []
    in_str = False
    esc = False
    for c in text:
        if esc:
            result.append(c)
            esc = False
            continue
        if c == "\\":
            esc = True
            result.append(c)
            continue
        if c == '"':
            in_str = not in_str
            result.append(c)
            continue
        if in_str and c == "\n":
            result.append("\\n")
            continue
        if in_str and c == "\r":
            result.append("\\r")
            continue
        result.append(c)

    return "".join(result)
