"""
AIshield.cz — Scan Engine Health Monitor
Detects scan infrastructure failures and sends immediate alert emails
to admin. Monitors: Claude API errors, Playwright crashes, rate limits,
token depletion, and general pipeline failures.

Usage:
    from backend.monitoring.engine_health import engine_monitor
    await engine_monitor.report_error("anthropic_auth", scan_id, url, error_details)
"""

import logging
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from dataclasses import dataclass, field

import httpx

from backend.config import get_settings

logger = logging.getLogger(__name__)

# ── Admin recipients ──
ADMIN_EMAILS = ["info@aishield.cz"]

# ── Cooldown: don't spam the same error type more than once per N minutes ──
COOLDOWN_MINUTES = 30

# ── Error type definitions ──
ERROR_TYPES = {
    "anthropic_auth": {
        "title": "Anthropic API — Neplatný klíč",
        "emoji": "🔑",
        "severity": "CRITICAL",
        "color": "#ef4444",
        "remediation": [
            "Ověřte ANTHROPIC_API_KEY v /opt/aishield/.env",
            "Zkontrolujte platnost klíče na console.anthropic.com",
            "Restartujte backend: systemctl restart aishield-api",
        ],
    },
    "anthropic_rate_limit": {
        "title": "Anthropic API — Rate Limit",
        "emoji": "⏱️",
        "severity": "HIGH",
        "color": "#eab308",
        "remediation": [
            "Dočasné omezení — Claude API vrací 429",
            "Klasifikátor přepnul na fallback (rule-based)",
            "Počkejte 5-10 minut, nebo zvyšte tier na console.anthropic.com",
            "Zvažte snížení frekvence skenů v rate_limit.py",
        ],
    },
    "anthropic_overloaded": {
        "title": "Anthropic API — Přetížení",
        "emoji": "🔥",
        "severity": "HIGH",
        "color": "#f97316",
        "remediation": [
            "Claude API je dočasně přetížené (529 Overloaded)",
            "Klasifikátor přepnul na fallback",
            "Zkontrolujte status.anthropic.com",
            "Obvykle se vyřeší do 15-30 minut",
        ],
    },
    "anthropic_tokens_depleted": {
        "title": "Anthropic API — Vyčerpán kredit",
        "emoji": "💸",
        "severity": "CRITICAL",
        "color": "#ef4444",
        "remediation": [
            "Účet nemá dostatečný kredit pro API volání",
            "Dobijte kredit na console.anthropic.com/settings/billing",
            "Klasifikátor mezitím běží v rule-based fallback režimu",
        ],
    },
    "playwright_crash": {
        "title": "Playwright — Selhání prohlížeče",
        "emoji": "🌐",
        "severity": "HIGH",
        "color": "#f97316",
        "remediation": [
            "Playwright browser pravděpodobně spadl",
            "Zkontrolujte: playwright install chromium",
            "Zkontrolujte RAM na serveru: free -h",
            "Restartujte: systemctl restart aishield-api",
        ],
    },
    "playwright_timeout": {
        "title": "Playwright — Timeout",
        "emoji": "⏰",
        "severity": "MEDIUM",
        "color": "#eab308",
        "remediation": [
            "Web nereagoval včas (timeout při načítání)",
            "Může být problém cílového webu, ne naší infrastruktury",
            "Pokud se opakuje u různých webů, zkontrolujte konektivitu serveru",
        ],
    },
    "database_error": {
        "title": "Supabase DB — Chyba",
        "emoji": "🗄️",
        "severity": "CRITICAL",
        "color": "#ef4444",
        "remediation": [
            "Chyba komunikace se Supabase databází",
            "Zkontrolujte SUPABASE_URL a SUPABASE_SERVICE_ROLE_KEY v .env",
            "Ověřte status Supabase projektu na app.supabase.com",
        ],
    },
    "pipeline_error": {
        "title": "Scan Pipeline — Obecná chyba",
        "emoji": "⚙️",
        "severity": "HIGH",
        "color": "#f97316",
        "remediation": [
            "Neočekávaná chyba v pipeline",
            "Zkontrolujte logy: journalctl -u aishield-api --since '30 min ago'",
            "Pokud se opakuje, restartujte: systemctl restart aishield-api",
        ],
    },
    "resend_error": {
        "title": "Resend Email — Selhání odesílání",
        "emoji": "📧",
        "severity": "HIGH",
        "color": "#f97316",
        "remediation": [
            "Chyba při odesílání emailu přes Resend API",
            "Ověřte RESEND_API_KEY v .env",
            "Zkontrolujte limity na resend.com/domains",
        ],
    },
}


@dataclass
class ErrorEvent:
    """Single recorded error event."""
    error_type: str
    scan_id: str | None
    url: str | None
    details: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EngineHealthMonitor:
    """
    Singleton monitor that tracks scan engine errors and sends
    immediate admin alerts with cooldown to prevent spam.
    """

    def __init__(self):
        # Track last alert time per error type (cooldown)
        self._last_alert: dict[str, datetime] = {}
        # Rolling error counter per type (last hour)
        self._error_counts: dict[str, list[datetime]] = defaultdict(list)
        # Total lifetime counters
        self._lifetime_counts: dict[str, int] = defaultdict(int)

    def _is_on_cooldown(self, error_type: str) -> bool:
        """Check if this error type was alerted recently."""
        last = self._last_alert.get(error_type)
        if not last:
            return False
        return (datetime.now(timezone.utc) - last) < timedelta(minutes=COOLDOWN_MINUTES)

    def _prune_old_events(self, error_type: str):
        """Remove events older than 1 hour from rolling counter."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        self._error_counts[error_type] = [
            ts for ts in self._error_counts[error_type] if ts > cutoff
        ]

    def get_health_status(self) -> dict:
        """Return current health metrics (for admin API endpoint)."""
        now = datetime.now(timezone.utc)
        status = {}
        for err_type in ERROR_TYPES:
            self._prune_old_events(err_type)
            count_1h = len(self._error_counts.get(err_type, []))
            lifetime = self._lifetime_counts.get(err_type, 0)
            last = self._last_alert.get(err_type)
            status[err_type] = {
                "last_1h": count_1h,
                "lifetime": lifetime,
                "last_alert": last.isoformat() if last else None,
                "on_cooldown": self._is_on_cooldown(err_type),
            }
        return status

    async def report_error(
        self,
        error_type: str,
        scan_id: str | None = None,
        url: str | None = None,
        details: str = "",
    ):
        """
        Report a scan engine error. Sends alert email if not on cooldown.

        Args:
            error_type: Key from ERROR_TYPES
            scan_id: Optional scan UUID
            url: Optional scanned URL
            details: Error message / traceback excerpt
        """
        now = datetime.now(timezone.utc)

        # Track event
        self._error_counts[error_type].append(now)
        self._lifetime_counts[error_type] += 1
        self._prune_old_events(error_type)

        error_info = ERROR_TYPES.get(error_type, ERROR_TYPES["pipeline_error"])
        count_1h = len(self._error_counts[error_type])

        logger.warning(
            f"[EngineHealth] {error_info['emoji']} {error_info['title']} "
            f"(scan={scan_id}, url={url}, count_1h={count_1h})"
        )

        # Skip alert if on cooldown
        if self._is_on_cooldown(error_type):
            logger.info(
                f"[EngineHealth] Alert pro '{error_type}' je na cooldownu — "
                f"email nebude odeslán"
            )
            return

        # Send alert
        self._last_alert[error_type] = now

        try:
            html = self._build_alert_email(error_type, error_info, scan_id, url, details, count_1h)
            subject = f"[AIshield {error_info['severity']}] {error_info['emoji']} {error_info['title']}"

            settings = get_settings()
            if not settings.resend_api_key:
                logger.error("[EngineHealth] RESEND_API_KEY chybí — alert email neodesílán")
                return

            for admin_email in ADMIN_EMAILS:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        "https://api.resend.com/emails",
                        headers={
                            "Authorization": f"Bearer {settings.resend_api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "from": "AIshield Monitor <info@aishield.cz>",
                            "to": [admin_email],
                            "subject": subject,
                            "html": html,
                        },
                    )
                    if resp.status_code in (200, 201):
                        logger.info(f"[EngineHealth] Alert email odeslán na {admin_email}")
                    else:
                        logger.error(
                            f"[EngineHealth] Chyba odesílání alertu: "
                            f"{resp.status_code} {resp.text}"
                        )

        except Exception as e:
            logger.error(f"[EngineHealth] Nelze odeslat alert email: {e}", exc_info=True)

    def _build_alert_email(
        self,
        error_type: str,
        error_info: dict,
        scan_id: str | None,
        url: str | None,
        details: str,
        count_1h: int,
    ) -> str:
        """Build dark-themed alert email HTML."""
        severity = error_info["severity"]
        color = error_info["color"]
        title = error_info["title"]
        emoji = error_info["emoji"]
        remediation = error_info.get("remediation", [])

        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        # Severity colors
        sev_colors = {
            "CRITICAL": {"bg": "#3b1118", "text": "#fca5a5", "border": "#ef4444"},
            "HIGH": {"bg": "#3b2e0a", "text": "#fde68a", "border": "#eab308"},
            "MEDIUM": {"bg": "#1a2340", "text": "#94a3b8", "border": "#334155"},
        }
        sc = sev_colors.get(severity, sev_colors["MEDIUM"])

        # Build remediation list
        rem_html = ""
        for i, step in enumerate(remediation, 1):
            rem_html += (
                f'<tr><td style="padding:8px 12px;font-size:13px;color:#94a3b8;'
                f'border-bottom:1px solid #1e293b;">'
                f'<span style="color:#06b6d4;font-weight:600;">{i}.</span> {step}'
                f'</td></tr>'
            )

        # Details section
        details_html = ""
        if details:
            # Truncate very long tracebacks
            truncated = details[:1500]
            if len(details) > 1500:
                truncated += "\n... (zkráceno)"
            details_html = f"""
            <div style="margin:0 24px 20px;">
                <div style="font-size:13px;font-weight:600;color:#64748b;margin-bottom:8px;">DETAIL CHYBY</div>
                <div style="background:#0a0a1a;border:1px solid #1e293b;border-radius:8px;padding:14px;
                            font-family:'SF Mono',Menlo,monospace;font-size:12px;color:#94a3b8;
                            white-space:pre-wrap;word-break:break-all;line-height:1.5;">
{truncated}
                </div>
            </div>"""

        # Scan info
        scan_html = ""
        if scan_id or url:
            rows = ""
            if url:
                rows += (
                    f'<tr><td style="padding:6px 0;color:#64748b;font-size:13px;">URL</td>'
                    f'<td style="padding:6px 0;color:#06b6d4;font-size:13px;text-align:right;">{url}</td></tr>'
                )
            if scan_id:
                rows += (
                    f'<tr><td style="padding:6px 0;color:#64748b;font-size:13px;">Scan ID</td>'
                    f'<td style="padding:6px 0;color:#f1f5f9;font-size:13px;text-align:right;'
                    f'font-family:monospace;">{scan_id[:8]}...</td></tr>'
                )
            scan_html = f"""
            <div style="margin:0 24px 20px;padding:14px;background:#1a2340;border:1px solid #1e293b;border-radius:10px;">
                <table style="width:100%;border-collapse:collapse;">{rows}</table>
            </div>"""

        html = f"""<!DOCTYPE html>
<html lang="cs">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#0a0a1a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<div style="max-width:600px;margin:0 auto;background:#0f172a;">

    <!-- HEADER -->
    <div style="background:linear-gradient(135deg,#0f172a,#1e1b4b,#312e81);padding:28px 24px;text-align:center;border-bottom:1px solid #1e293b;">
        <div style="font-size:22px;font-weight:800;">
            <span style="color:#ffffff;">AI</span><span style="color:#d946ef;">shield</span><span style="color:#64748b;font-size:14px;">.cz</span>
            <span style="color:#64748b;font-size:14px;font-weight:400;margin-left:8px;">ENGINE MONITOR</span>
        </div>
    </div>

    <!-- SEVERITY BADGE -->
    <div style="margin:24px;padding:18px;background:{sc['bg']};border:2px solid {sc['border']};border-radius:12px;">
        <div style="font-size:11px;font-weight:600;color:{sc['text']};text-transform:uppercase;letter-spacing:1.5px;">
            {severity}
        </div>
        <div style="font-size:18px;font-weight:700;color:#f1f5f9;margin-top:6px;">
            {emoji} {title}
        </div>
        <div style="font-size:12px;color:#64748b;margin-top:8px;">{now_str}</div>
    </div>

    <!-- ERROR STATS -->
    <div style="margin:0 24px 20px;">
        <table style="width:100%;border-collapse:separate;border-spacing:8px 0;">
            <tr>
                <td style="text-align:center;padding:14px;background:#1a2340;border-radius:10px;border:1px solid #1e293b;">
                    <div style="font-size:24px;font-weight:700;color:{color};">{count_1h}</div>
                    <div style="font-size:11px;color:#64748b;margin-top:2px;">Za poslední hodinu</div>
                </td>
                <td style="text-align:center;padding:14px;background:#1a2340;border-radius:10px;border:1px solid #1e293b;">
                    <div style="font-size:24px;font-weight:700;color:#f1f5f9;">{self._lifetime_counts.get(error_type, 0)}</div>
                    <div style="font-size:11px;color:#64748b;margin-top:2px;">Celkem (od restartu)</div>
                </td>
            </tr>
        </table>
    </div>

    <!-- SCAN INFO -->
    {scan_html}

    <!-- ERROR DETAILS -->
    {details_html}

    <!-- REMEDIATION -->
    <div style="margin:0 24px 20px;">
        <div style="font-size:13px;font-weight:600;color:#64748b;margin-bottom:8px;">DOPORUČENÝ POSTUP</div>
        <table style="width:100%;border-collapse:collapse;background:#131b2e;border:1px solid #1e293b;border-radius:10px;overflow:hidden;">
            {rem_html}
        </table>
    </div>

    <!-- QUICK LINKS -->
    <div style="margin:0 24px 20px;text-align:center;">
        <a href="https://api.aishield.cz/health" style="display:inline-block;padding:10px 24px;background:#7c3aed;color:#ffffff;font-weight:600;font-size:13px;border-radius:8px;text-decoration:none;margin:0 4px;">
            Health Check
        </a>
        <a href="https://app.supabase.com" style="display:inline-block;padding:10px 24px;background:transparent;color:#06b6d4;font-weight:600;font-size:13px;border-radius:8px;text-decoration:none;border:1px solid #06b6d4;margin:0 4px;">
            Supabase
        </a>
    </div>

    <!-- FOOTER -->
    <div style="background:#0a0a1a;padding:20px 24px;text-align:center;border-top:1px solid #1e293b;">
        <div style="font-size:11px;color:#475569;">
            Tento alert byl automaticky vygenerován AIshield Engine Monitorem.<br>
            Cooldown: {COOLDOWN_MINUTES} min — další alert stejného typu bude odeslán nejdříve {COOLDOWN_MINUTES} min po tomto.
        </div>
    </div>

</div>
</body>
</html>"""
        return html


# ── Singleton instance ──
engine_monitor = EngineHealthMonitor()
