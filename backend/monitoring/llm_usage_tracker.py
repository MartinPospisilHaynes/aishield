"""
AIshield.cz — LLM Usage Tracker

Persistent tracking of LLM API usage (tokens, cost) with:
- Per-call logging to Supabase `llm_usage_daily` table (aggregated by day + provider)
- Budget threshold alerts (80%, 95%) via email
- API key health checks (tiny test calls to verify keys work)
- Exposed via /api/admin/llm-usage endpoint

Usage:
    from backend.monitoring.llm_usage_tracker import usage_tracker
    await usage_tracker.record("claude", input_tokens=500, output_tokens=200, cost_usd=0.0045)
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# ── Budget defaults (USD per month) ──
DEFAULT_ANTHROPIC_BUDGET = 100.0
DEFAULT_GEMINI_BUDGET = 20.0

# ── Alert thresholds ──
ALERT_THRESHOLDS = [0.80, 0.95]  # 80% and 95%
ALERT_COOLDOWN_HOURS = 12  # Don't re-send same threshold alert within this window


@dataclass
class _ProviderAccum:
    """In-memory accumulator flushed to Supabase periodically."""
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    calls: int = 0


class LLMUsageTracker:
    """Singleton tracker for LLM API usage."""

    def __init__(self):
        self._accum: dict[str, _ProviderAccum] = {}  # key = "claude" | "gemini"
        self._last_flush: float = 0
        self._flush_interval = 60  # seconds — flush to DB at most once per minute
        self._last_alert: dict[str, float] = {}  # "provider:threshold" → timestamp
        self._last_health_check: float = 0
        self._health_cache: dict[str, dict] = {}

    # ── Record usage (called after every LLM call) ──

    async def record(
        self,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        model: str = "",
        caller: str = "",
    ):
        """Record a single LLM call. Accumulates in-memory, flushes periodically."""
        if provider not in self._accum:
            self._accum[provider] = _ProviderAccum()

        acc = self._accum[provider]
        acc.input_tokens += input_tokens
        acc.output_tokens += output_tokens
        acc.cost_usd += cost_usd
        acc.calls += 1

        # Flush if enough time passed
        now = time.time()
        if now - self._last_flush >= self._flush_interval:
            await self._flush()

    # ── Flush accumulated data to Supabase ──

    async def _flush(self):
        """Flush accumulated usage to `llm_usage_daily` table."""
        if not self._accum:
            return

        self._last_flush = time.time()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        try:
            from backend.database import get_supabase
            supabase = get_supabase()

            for provider, acc in self._accum.items():
                if acc.calls == 0:
                    continue

                # Upsert — increment today's row for this provider
                existing = (
                    supabase.table("llm_usage_daily")
                    .select("*")
                    .eq("date", today)
                    .eq("provider", provider)
                    .limit(1)
                    .execute()
                )

                if existing.data:
                    row = existing.data[0]
                    supabase.table("llm_usage_daily").update({
                        "input_tokens": row["input_tokens"] + acc.input_tokens,
                        "output_tokens": row["output_tokens"] + acc.output_tokens,
                        "cost_usd": round(row["cost_usd"] + acc.cost_usd, 6),
                        "calls": row["calls"] + acc.calls,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }).eq("id", row["id"]).execute()
                else:
                    supabase.table("llm_usage_daily").insert({
                        "date": today,
                        "provider": provider,
                        "input_tokens": acc.input_tokens,
                        "output_tokens": acc.output_tokens,
                        "cost_usd": round(acc.cost_usd, 6),
                        "calls": acc.calls,
                    }).execute()

                # Reset accumulator
                self._accum[provider] = _ProviderAccum()

            # Check budget after flush
            await self._check_budget_alerts()

        except Exception as e:
            logger.error(f"[LLM Usage] Flush failed: {e}")

    # ── Force flush (called on shutdown or manual trigger) ──

    async def force_flush(self):
        """Force flush accumulated data now."""
        await self._flush()

    # ── Budget alerts ──

    async def _check_budget_alerts(self):
        """Check if monthly spend crosses alert thresholds."""
        try:
            from backend.database import get_supabase
            supabase = get_supabase()

            now = datetime.now(timezone.utc)
            month_start = now.strftime("%Y-%m-01")

            result = supabase.table("llm_usage_daily").select(
                "provider, cost_usd"
            ).gte("date", month_start).execute()

            # Aggregate per provider
            monthly: dict[str, float] = {}
            for row in (result.data or []):
                p = row["provider"]
                monthly[p] = monthly.get(p, 0) + row["cost_usd"]

            budgets = {
                "claude": float(os.environ.get("LLM_BUDGET_ANTHROPIC", DEFAULT_ANTHROPIC_BUDGET)),
                "gemini": float(os.environ.get("LLM_BUDGET_GEMINI", DEFAULT_GEMINI_BUDGET)),
            }

            for provider, spent in monthly.items():
                budget = budgets.get(provider, DEFAULT_ANTHROPIC_BUDGET)
                if budget <= 0:
                    continue
                ratio = spent / budget

                for threshold in ALERT_THRESHOLDS:
                    if ratio >= threshold:
                        alert_key = f"{provider}:{threshold}"
                        last = self._last_alert.get(alert_key, 0)
                        if time.time() - last < ALERT_COOLDOWN_HOURS * 3600:
                            continue  # Already alerted recently

                        self._last_alert[alert_key] = time.time()
                        pct = int(threshold * 100)
                        await self._send_budget_alert(
                            provider, spent, budget, pct
                        )

        except Exception as e:
            logger.error(f"[LLM Usage] Budget check failed: {e}")

    async def _send_budget_alert(
        self, provider: str, spent: float, budget: float, pct: int
    ):
        """Send email alert about budget threshold crossed."""
        try:
            from backend.outbound.email_engine import send_email

            provider_name = "Anthropic (Claude)" if provider == "claude" else "Google (Gemini)"
            remaining = max(0, budget - spent)

            await send_email(
                to="info@aishield.cz",
                subject=f"🚨 LLM Budget {pct}% — {provider_name}: ${spent:.2f} / ${budget:.2f}",
                html=(
                    f"<div style='font-family:system-ui;max-width:500px'>"
                    f"<h2 style='color:#ef4444'>⚠️ LLM Budget Alert — {pct}%</h2>"
                    f"<table style='border-collapse:collapse;width:100%'>"
                    f"<tr><td style='padding:8px;border-bottom:1px solid #eee'><strong>Provider</strong></td>"
                    f"<td style='padding:8px;border-bottom:1px solid #eee'>{provider_name}</td></tr>"
                    f"<tr><td style='padding:8px;border-bottom:1px solid #eee'><strong>Tento měsíc</strong></td>"
                    f"<td style='padding:8px;border-bottom:1px solid #eee'>${spent:.2f}</td></tr>"
                    f"<tr><td style='padding:8px;border-bottom:1px solid #eee'><strong>Budget</strong></td>"
                    f"<td style='padding:8px;border-bottom:1px solid #eee'>${budget:.2f}</td></tr>"
                    f"<tr><td style='padding:8px;border-bottom:1px solid #eee'><strong>Zbývá</strong></td>"
                    f"<td style='padding:8px;border-bottom:1px solid #eee;color:#ef4444'>"
                    f"<strong>${remaining:.2f}</strong></td></tr>"
                    f"</table>"
                    f"<p style='margin-top:16px;color:#6b7280;font-size:13px'>"
                    f"Dokupte kredity na "
                    f"{'console.anthropic.com' if provider == 'claude' else 'aistudio.google.com'} "
                    f"co nejdříve.</p>"
                    f"</div>"
                ),
                from_email="info@aishield.cz",
            )
            logger.warning(
                f"[LLM Usage] Budget alert sent: {provider} at {pct}% "
                f"(${spent:.2f}/${budget:.2f})"
            )
        except Exception as e:
            logger.error(f"[LLM Usage] Alert email failed: {e}")

    # ── API Key Health Check ──

    async def check_api_keys(self) -> dict:
        """
        Test both API keys with minimal calls.
        Returns status for each provider.
        Cache for 5 minutes.
        """
        now = time.time()
        if now - self._last_health_check < 300 and self._health_cache:
            return self._health_cache

        result = {}

        # ── Anthropic ──
        try:
            from backend.config import get_settings
            import anthropic

            settings = get_settings()
            key = settings.anthropic_api_key
            if not key:
                result["claude"] = {"status": "missing", "message": "API klíč není nastaven"}
            else:
                client = anthropic.Anthropic(api_key=key)
                # Minimal API call to verify key works
                resp = client.messages.create(
                    model="claude-opus-4-6",
                    max_tokens=1,
                    messages=[{"role": "user", "content": "hi"}],
                )
                result["claude"] = {
                    "status": "ok",
                    "message": f"Klíč funguje",
                    "key_prefix": key[:12] + "...",
                }
        except anthropic.AuthenticationError:
            result["claude"] = {"status": "error", "message": "Neplatný API klíč"}
        except anthropic.PermissionDeniedError as e:
            msg = str(e).lower()
            if "credit" in msg or "billing" in msg:
                result["claude"] = {"status": "depleted", "message": "Kredity vyčerpány!"}
            else:
                result["claude"] = {"status": "error", "message": str(e)}
        except Exception as e:
            result["claude"] = {"status": "error", "message": str(e)[:200]}

        # ── Gemini ──
        try:
            import httpx

            key = os.environ.get("GEMINI_API_KEY", "")
            if not key:
                result["gemini"] = {"status": "missing", "message": "API klíč není nastaven"}
            else:
                # Use countTokens endpoint — zero cost, verifies auth
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:countTokens?key={key}"
                async with httpx.AsyncClient(timeout=10) as http:
                    resp = await http.post(url, json={
                        "contents": [{"parts": [{"text": "test"}]}]
                    })
                if resp.status_code == 200:
                    result["gemini"] = {
                        "status": "ok",
                        "message": "Klíč funguje (token count OK)",
                        "key_prefix": key[:10] + "...",
                    }
                elif resp.status_code == 403:
                    result["gemini"] = {"status": "error", "message": "API klíč nemá oprávnění"}
                elif resp.status_code == 429:
                    result["gemini"] = {"status": "rate_limited", "message": "Rate limit — ale klíč funguje"}
                else:
                    result["gemini"] = {"status": "error", "message": f"HTTP {resp.status_code}: {resp.text[:200]}"}
        except Exception as e:
            result["gemini"] = {"status": "error", "message": str(e)[:200]}

        self._health_cache = result
        self._last_health_check = now
        return result

    # ── Get usage summary for admin dashboard ──

    async def get_usage_summary(self) -> dict:
        """Return usage summary for admin dashboard."""
        # Force flush pending data first
        await self._flush()

        try:
            from backend.database import get_supabase
            from backend.ai_engine.llm_client import get_usage_stats
            supabase = get_supabase()

            now = datetime.now(timezone.utc)
            today = now.strftime("%Y-%m-%d")
            month_start = now.strftime("%Y-%m-01")

            # Get this month's data
            month_data = supabase.table("llm_usage_daily").select("*").gte(
                "date", month_start
            ).order("date", desc=True).execute()

            # Get last 30 days for trend
            from datetime import timedelta
            thirty_days_ago = (now - timedelta(days=30)).strftime("%Y-%m-%d")
            trend_data = supabase.table("llm_usage_daily").select("*").gte(
                "date", thirty_days_ago
            ).order("date").execute()

            # Aggregate monthly by provider
            monthly_by_provider: dict[str, dict] = {}
            for row in (month_data.data or []):
                p = row["provider"]
                if p not in monthly_by_provider:
                    monthly_by_provider[p] = {
                        "input_tokens": 0, "output_tokens": 0,
                        "cost_usd": 0, "calls": 0,
                    }
                monthly_by_provider[p]["input_tokens"] += row["input_tokens"]
                monthly_by_provider[p]["output_tokens"] += row["output_tokens"]
                monthly_by_provider[p]["cost_usd"] += row["cost_usd"]
                monthly_by_provider[p]["calls"] += row["calls"]

            # Today's totals
            today_by_provider: dict[str, dict] = {}
            for row in (month_data.data or []):
                if row["date"] == today:
                    today_by_provider[row["provider"]] = {
                        "input_tokens": row["input_tokens"],
                        "output_tokens": row["output_tokens"],
                        "cost_usd": row["cost_usd"],
                        "calls": row["calls"],
                    }

            # Daily trend (last 30 days)
            daily_trend = []
            for row in (trend_data.data or []):
                daily_trend.append({
                    "date": row["date"],
                    "provider": row["provider"],
                    "cost_usd": row["cost_usd"],
                    "calls": row["calls"],
                    "input_tokens": row["input_tokens"],
                    "output_tokens": row["output_tokens"],
                })

            # Budgets
            budgets = {
                "claude": float(os.environ.get("LLM_BUDGET_ANTHROPIC", DEFAULT_ANTHROPIC_BUDGET)),
                "gemini": float(os.environ.get("LLM_BUDGET_GEMINI", DEFAULT_GEMINI_BUDGET)),
            }

            # In-memory stats (since last restart)
            mem_stats = get_usage_stats()

            # API key health
            health = await self.check_api_keys()

            return {
                "monthly": monthly_by_provider,
                "today": today_by_provider,
                "daily_trend": daily_trend,
                "budgets": budgets,
                "memory_stats": mem_stats,
                "api_health": health,
                "month": now.strftime("%Y-%m"),
                "timestamp": now.isoformat(),
            }

        except Exception as e:
            logger.error(f"[LLM Usage] Summary failed: {e}")
            return {
                "error": str(e),
                "memory_stats": get_usage_stats() if 'get_usage_stats' in dir() else {},
                "api_health": await self.check_api_keys(),
            }


# ── Singleton ──
usage_tracker = LLMUsageTracker()
