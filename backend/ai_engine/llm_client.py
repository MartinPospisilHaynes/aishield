"""
AIshield.cz — LLM Fallback Client

Univerzální wrapper pro LLM volání s automatickým fallback:
  1. Claude (Anthropic) — primární
  2. Gemini 2.5 Flash (Google) — záloha

Funkce:
- Jednotné rozhraní pro text completion (system + user → response)
- Automatický retry s exponential backoff (tenacity)
- Fallback na Gemini pokud Claude selže (rate limit, billing, outage)
- Sledování tokenů a nákladů
- Vision podpora (Claude → Gemini fallback)

Použití:
    from backend.ai_engine.llm_client import llm_complete, llm_complete_vision

    result = await llm_complete(
        system="Jsi expert na AI Act.",
        user="Klasifikuj tento systém...",
        max_tokens=2048,
    )
    print(result.text, result.provider, result.cost_usd)
"""

import json
import logging
import os
import time
from dataclasses import dataclass, field

import httpx

from backend.config import get_settings

logger = logging.getLogger(__name__)

# ── Modely ──
CLAUDE_MODEL = "claude-sonnet-4-6"
GEMINI_MODEL = "gemini-3.1-pro-preview"
GEMINI_API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
)

# ── Cenové tarify (USD per token) ──
CLAUDE_COST_INPUT = 3.0 / 1_000_000   # $3 / 1M input  (Sonnet 4 — fallback)
CLAUDE_COST_OUTPUT = 15.0 / 1_000_000  # $15 / 1M output (Sonnet 4 — fallback)
GEMINI_COST_INPUT = 2.0 / 1_000_000   # $2 / 1M input  (Gemini 3.1 Pro)
GEMINI_COST_OUTPUT = 12.0 / 1_000_000  # $12 / 1M output (Gemini 3.1 Pro)

# ── Retry config ──
MAX_RETRIES = 3
RETRY_DELAYS = [1.0, 3.0, 9.0]


@dataclass
class LLMResult:
    """Výsledek LLM volání."""
    text: str
    provider: str  # "claude" | "gemini" | "fallback_rule"
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    fallback_used: bool = False
    fallback_reason: str = ""


# ── Globální statistiky ──
@dataclass
class _UsageStats:
    total_calls: int = 0
    claude_calls: int = 0
    gemini_calls: int = 0
    fallback_count: int = 0
    total_cost_usd: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0

_stats = _UsageStats()


async def _record_usage(provider: str, result: "LLMResult", caller: str = ""):
    """Persist usage to Supabase via tracker (fire-and-forget)."""
    try:
        from backend.monitoring.llm_usage_tracker import usage_tracker
        await usage_tracker.record(
            provider=provider,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            cost_usd=result.cost_usd,
            model=result.model,
            caller=caller,
        )
    except Exception as e:
        logger.warning(f"[LLM] Usage tracking failed: {e}")


def get_usage_stats() -> dict:
    """Vrátí globální statistiky použití LLM."""
    return {
        "total_calls": _stats.total_calls,
        "claude_calls": _stats.claude_calls,
        "gemini_calls": _stats.gemini_calls,
        "fallback_count": _stats.fallback_count,
        "total_cost_usd": round(_stats.total_cost_usd, 4),
        "total_input_tokens": _stats.total_input_tokens,
        "total_output_tokens": _stats.total_output_tokens,
    }


# ═══════════════════════════════════════════════════════════════
# CLAUDE (Anthropic) — primární
# ═══════════════════════════════════════════════════════════════

async def _call_claude(
    system: str,
    user: str,
    max_tokens: int = 2048,
    model: str | None = None,
    temperature: float = 0.0,
    prefill: str | None = None,
) -> LLMResult:
    """Zavolá Claude API (synchronně — Anthropic SDK nemá async)."""
    import anthropic

    settings = get_settings()
    api_key = settings.anthropic_api_key
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY není nastavený")

    client = anthropic.Anthropic(api_key=api_key)
    use_model = model or CLAUDE_MODEL

    messages = [{"role": "user", "content": user}]
    if prefill:
        messages.append({"role": "assistant", "content": prefill})

    response = client.messages.create(
        model=use_model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=messages,
    )

    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    cost = (input_tokens * CLAUDE_COST_INPUT) + (output_tokens * CLAUDE_COST_OUTPUT)

    # Prefill text není v odpovědi — doplníme ho
    raw_text = response.content[0].text.strip()
    if prefill:
        raw_text = prefill + raw_text

    return LLMResult(
        text=raw_text,
        provider="claude",
        model=use_model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost,
    )


async def _call_claude_vision(
    system: str,
    user_text: str,
    image_b64: str,
    media_type: str = "image/png",
    max_tokens: int = 500,
    model: str | None = None,
) -> LLMResult:
    """Zavolá Claude Vision API."""
    import anthropic

    settings = get_settings()
    api_key = settings.anthropic_api_key
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY není nastavený")

    client = anthropic.Anthropic(api_key=api_key)
    use_model = model or CLAUDE_MODEL

    response = client.messages.create(
        model=use_model,
        max_tokens=max_tokens,
        system=system,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_b64,
                    },
                },
                {"type": "text", "text": user_text},
            ],
        }],
    )

    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    cost = (input_tokens * CLAUDE_COST_INPUT) + (output_tokens * CLAUDE_COST_OUTPUT)

    return LLMResult(
        text=response.content[0].text.strip(),
        provider="claude",
        model=use_model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost,
    )


# ═══════════════════════════════════════════════════════════════
# GEMINI (Google) — fallback
# ═══════════════════════════════════════════════════════════════

async def _call_gemini(
    system: str,
    user: str,
    max_tokens: int = 2048,
    temperature: float = 0.0,
) -> LLMResult:
    """Zavolá Gemini API přes REST."""
    settings = get_settings()
    api_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY není nastavený")

    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{GEMINI_API_URL}?key={api_key}",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()

    # Parsuj odpověď
    text = ""
    candidates = data.get("candidates", [])
    if candidates:
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts).strip()

    # Token usage
    usage_meta = data.get("usageMetadata", {})
    input_tokens = usage_meta.get("promptTokenCount", 0)
    output_tokens = usage_meta.get("candidatesTokenCount", 0)
    cost = (input_tokens * GEMINI_COST_INPUT) + (output_tokens * GEMINI_COST_OUTPUT)

    return LLMResult(
        text=text,
        provider="gemini",
        model=GEMINI_MODEL,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost,
        fallback_used=False,
    )


async def _call_gemini_vision(
    system: str,
    user_text: str,
    image_b64: str,
    media_type: str = "image/png",
    max_tokens: int = 500,
) -> LLMResult:
    """Zavolá Gemini Vision API přes REST."""
    settings = get_settings()
    api_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY není nastavený")

    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{
            "role": "user",
            "parts": [
                {"inline_data": {"mime_type": media_type, "data": image_b64}},
                {"text": user_text},
            ],
        }],
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": max_tokens,
        },
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{GEMINI_API_URL}?key={api_key}",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()

    text = ""
    candidates = data.get("candidates", [])
    if candidates:
        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts).strip()

    usage_meta = data.get("usageMetadata", {})
    input_tokens = usage_meta.get("promptTokenCount", 0)
    output_tokens = usage_meta.get("candidatesTokenCount", 0)
    cost = (input_tokens * GEMINI_COST_INPUT) + (output_tokens * GEMINI_COST_OUTPUT)

    return LLMResult(
        text=text,
        provider="gemini",
        model=GEMINI_MODEL,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost,
        fallback_used=True,
    )


# ═══════════════════════════════════════════════════════════════
# VEŘEJNÉ API — s automatickým fallbackem
# ═══════════════════════════════════════════════════════════════

async def llm_complete(
    system: str,
    user: str,
    max_tokens: int = 2048,
    model: str | None = None,
    temperature: float = 0.0,
    prefer: str = "gemini",
    prefill: str | None = None,
) -> LLMResult:
    """
    Univerzální LLM completion s automatickým fallback.

    Pořadí: Gemini → Claude (fallback).
    Pokud Gemini selže, automaticky zkusí Claude.
    prefill: Volitelný text pro Claude prefill (model pokračuje za ním).

    Args:
        system: Systémový prompt
        user: Uživatelská zpráva
        max_tokens: Max output tokenů
        model: Specifický model (None = výchozí)
        temperature: Teplota generování
        prefer: "claude" nebo "gemini" — který zkusit první

    Returns:
        LLMResult s textem, providerem, tokenovou statistikou
    """
    _stats.total_calls += 1

    providers = [
        ("claude", _call_claude),
        ("gemini", _call_gemini),
    ]
    if prefer == "gemini":
        providers = list(reversed(providers))

    last_error = None

    for provider_name, call_fn in providers:
        for attempt in range(MAX_RETRIES):
            try:
                if provider_name == "claude":
                    result = await _call_claude(
                        system=system, user=user, max_tokens=max_tokens,
                        model=model, temperature=temperature,
                        prefill=prefill,
                    )
                else:
                    result = await _call_gemini(
                        system=system, user=user, max_tokens=max_tokens,
                        temperature=temperature,
                    )

                # Úspěch — zaznamenat statistiky
                if provider_name == "claude":
                    _stats.claude_calls += 1
                    if prefer != "claude":
                        # Claude was used as fallback
                        result.fallback_used = True
                        result.fallback_reason = str(last_error) if last_error else "gemini_unavailable"
                        _stats.fallback_count += 1
                else:
                    _stats.gemini_calls += 1
                    if prefer != "gemini":
                        # Gemini was used as fallback
                        result.fallback_used = True
                        result.fallback_reason = str(last_error) if last_error else "claude_unavailable"
                        _stats.fallback_count += 1

                _stats.total_cost_usd += result.cost_usd
                _stats.total_input_tokens += result.input_tokens
                _stats.total_output_tokens += result.output_tokens

                # Persist to Supabase
                await _record_usage(provider_name, result, caller="llm_complete")

                if result.fallback_used:
                    logger.warning(
                        f"[LLM] Fallback na {provider_name}: {result.fallback_reason}"
                    )
                    # Odeslat admin notifikaci emailem
                    try:
                        import asyncio
                        from backend.outbound.email_engine import send_email
                        await send_email(
                            to="info@aishield.cz",
                            subject=f"⚠️ LLM Fallback: Claude → {provider_name.capitalize()}",
                            html=(
                                f"<h3>LLM Fallback aktivován</h3>"
                                f"<p><strong>Primární provider selhal:</strong> Claude</p>"
                                f"<p><strong>Fallback provider:</strong> {provider_name.capitalize()}</p>"
                                f"<p><strong>Důvod:</strong> {result.fallback_reason}</p>"
                                f"<p><strong>Model:</strong> {result.model}</p>"
                                f"<p><strong>Tokeny:</strong> {result.input_tokens} in / {result.output_tokens} out</p>"
                                f"<p><strong>Náklad:</strong> ${result.cost_usd:.4f}</p>"
                                f"<p style='color:#6b7280;font-size:12px;'>Tato notifikace je automatická. "
                                f"Zkontrolujte stav Claude API a billing.</p>"
                            ),
                            from_email="info@aishield.cz",
                        )
                    except Exception as mail_err:
                        logger.warning(f"[LLM] Nepodařilo se odeslat fallback alert email: {mail_err}")
                else:
                    logger.info(
                        f"[LLM] {provider_name} OK — "
                        f"{result.input_tokens}+{result.output_tokens} tokens, "
                        f"${result.cost_usd:.4f}"
                    )

                return result

            except Exception as e:
                last_error = e
                is_auth_or_billing = _is_fatal_error(e)

                if is_auth_or_billing:
                    logger.error(
                        f"[LLM] {provider_name} fatální chyba (bez retry): {e}"
                    )
                    break  # Přeskoč na další provider

                delay = RETRY_DELAYS[attempt] if attempt < len(RETRY_DELAYS) else 9.0
                logger.warning(
                    f"[LLM] {provider_name} chyba (attempt {attempt+1}/{MAX_RETRIES}): {e}"
                )
                if attempt < MAX_RETRIES - 1:
                    time.sleep(delay)

        # Tento provider selhal → zkusit další
        logger.warning(f"[LLM] {provider_name} vyčerpán, zkouším další provider...")

    # Oba provideři selhali
    logger.error(f"[LLM] Všichni provideři selhali! Poslední chyba: {last_error}")
    raise RuntimeError(f"Všichni LLM provideři nedostupní: {last_error}")


async def llm_complete_vision(
    system: str,
    user_text: str,
    image_b64: str,
    media_type: str = "image/png",
    max_tokens: int = 500,
    model: str | None = None,
) -> LLMResult:
    """
    Vision LLM completion s automatickým fallback.
    Claude Vision → Gemini Vision.
    """
    _stats.total_calls += 1

    last_error = None

    # 1. Zkusit Claude Vision
    try:
        result = await _call_claude_vision(
            system=system, user_text=user_text, image_b64=image_b64,
            media_type=media_type, max_tokens=max_tokens, model=model,
        )
        _stats.claude_calls += 1
        _stats.total_cost_usd += result.cost_usd
        _stats.total_input_tokens += result.input_tokens
        _stats.total_output_tokens += result.output_tokens
        await _record_usage("claude", result, caller="llm_vision")
        logger.info(f"[LLM] Claude Vision OK — ${result.cost_usd:.4f}")
        return result
    except Exception as e:
        last_error = e
        logger.warning(f"[LLM] Claude Vision selhalo: {e}")

    # 2. Fallback na Gemini Vision
    try:
        result = await _call_gemini_vision(
            system=system, user_text=user_text, image_b64=image_b64,
            media_type=media_type, max_tokens=max_tokens,
        )
        result.fallback_used = True
        result.fallback_reason = str(last_error)
        _stats.gemini_calls += 1
        _stats.fallback_count += 1
        _stats.total_cost_usd += result.cost_usd
        _stats.total_input_tokens += result.input_tokens
        _stats.total_output_tokens += result.output_tokens
        await _record_usage("gemini", result, caller="llm_vision")
        logger.warning(f"[LLM] Gemini Vision fallback OK — ${result.cost_usd:.4f}")
        return result
    except Exception as e:
        logger.error(f"[LLM] Oba vision provideři selhali: {e}")
        raise RuntimeError(f"Všichni vision LLM provideři nedostupní: {e}")


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _is_fatal_error(e: Exception) -> bool:
    """Detekuje fatální chyby (auth, billing) — bez retry."""
    try:
        import anthropic
        if isinstance(e, anthropic.AuthenticationError):
            return True
        if isinstance(e, anthropic.APIStatusError):
            msg = str(e).lower()
            if "credit" in msg or "billing" in msg:
                return True
    except ImportError:
        pass

    error_str = str(e).lower()
    return any(kw in error_str for kw in ["authentication", "unauthorized", "403"])
