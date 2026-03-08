"""
AIshield.cz — Admin Notifier
Odesílá emailové notifikace adminům o důležitých událostech:
  - Chyby v pipeline (fire_and_forget_notify_error)
  - Organický sken dokončen
  - Hloubkový sken spuštěn
  - Klient si zobrazil výsledky
  - Dokumenty čekají na schválení
"""

import asyncio
import logging
import threading
from datetime import datetime, timezone

from backend.outbound.email_engine import send_email

logger = logging.getLogger(__name__)

# Adminské emaily — stejné jako v pioneer.py
ADMIN_EMAILS = ["info@aishield.cz"]

ADMIN_PANEL_URL = "https://aishield.cz/admin"


def _wrap(title: str, body_html: str) -> str:
    """Obalí obsah do společné šablony."""
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; color: #1a1a2e;">
        <h2>{title}</h2>
        {body_html}
        <hr style="margin: 24px 0; border: none; border-top: 1px solid #e0e0e0;">
        <p style="font-size: 12px; color: #888;">
            Automatická notifikace z AIshield.cz — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
        </p>
    </div>"""


async def _send_to_admins(subject: str, html: str) -> None:
    """Pošle email všem adminům. Chyby loguje, ale nepropaguje."""
    for email in ADMIN_EMAILS:
        try:
            await send_email(to=email, subject=subject, html=html)
        except Exception as e:
            logger.warning(f"[AdminNotifier] Email na {email} selhal: {e}")


# ──────────────────────────────────────────────────────────────────────
#  fire_and_forget_notify_error  — synchronní wrapper pro pipeline.py
# ──────────────────────────────────────────────────────────────────────

def fire_and_forget_notify_error(
    module: str,
    error: Exception | None,
    context: dict | None = None,
) -> None:
    """
    Synchronní fire-and-forget: spustí async odeslání v novém threadu.
    Volá se z pipeline.py uvnitř try/except — nesmí nikdy crashnout.
    """
    try:
        ctx = context or {}
        subject_text = ctx.pop("subject", None)
        subject = subject_text or f"⚠️ Chyba v {module}"
        err_str = str(error) if error else "(notifikace bez chyby)"

        rows = "".join(
            f"<tr><td style='padding:6px 12px; border:1px solid #ddd; font-weight:bold;'>{k}</td>"
            f"<td style='padding:6px 12px; border:1px solid #ddd;'>{v}</td></tr>"
            for k, v in ctx.items()
        )

        html = _wrap(subject, f"""
            <p><b>Modul:</b> {module}</p>
            <p><b>Chyba:</b> <code>{err_str}</code></p>
            {"<table style='border-collapse:collapse; width:100%;'>" + rows + "</table>" if rows else ""}
            <p style="margin-top:16px;">
                <a href="{ADMIN_PANEL_URL}" style="background:#6366f1; color:white; padding:10px 20px; border-radius:8px; text-decoration:none; font-weight:bold;">
                    Otevřít admin panel
                </a>
            </p>
        """)

        def _run():
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(_send_to_admins(subject, html))
            except Exception as exc:
                logger.warning(f"[AdminNotifier] fire_and_forget selhal: {exc}")
            finally:
                loop.close()

        t = threading.Thread(target=_run, daemon=True)
        t.start()
    except Exception as e:
        logger.warning(f"[AdminNotifier] fire_and_forget_notify_error selhalo: {e}")


# ──────────────────────────────────────────────────────────────────────
#  notify_error  — async verze pro scan.py
# ──────────────────────────────────────────────────────────────────────

async def notify_error(
    module: str,
    error: Exception | None,
    context: dict | None = None,
    severity: str = "high",
) -> None:
    """Async notifikace o chybě — volá se z scan.py."""
    ctx = context or {}
    err_str = str(error) if error else "(bez detailu)"
    color = {"critical": "#dc2626", "high": "#ea580c", "medium": "#d97706"}.get(severity, "#6b7280")

    rows = "".join(
        f"<tr><td style='padding:6px 12px; border:1px solid #ddd; font-weight:bold;'>{k}</td>"
        f"<td style='padding:6px 12px; border:1px solid #ddd;'>{v}</td></tr>"
        for k, v in ctx.items()
    )

    html = _wrap(f"⚠️ Chyba v {module}", f"""
        <p><b>Modul:</b> {module}</p>
        <p><b>Závažnost:</b> <span style="color:{color}; font-weight:bold;">{severity.upper()}</span></p>
        <p><b>Chyba:</b> <code>{err_str}</code></p>
        {"<table style='border-collapse:collapse; width:100%;'>" + rows + "</table>" if rows else ""}
        <p style="margin-top:16px;">
            <a href="{ADMIN_PANEL_URL}" style="background:#6366f1; color:white; padding:10px 20px; border-radius:8px; text-decoration:none; font-weight:bold;">
                Otevřít admin panel
            </a>
        </p>
    """)
    await _send_to_admins(f"⚠️ [{severity.upper()}] Chyba v {module}", html)


# ──────────────────────────────────────────────────────────────────────
#  notify_organic_scan_completed
# ──────────────────────────────────────────────────────────────────────

async def notify_organic_scan_completed(
    scan_id: str,
    url: str,
    company_id: str,
    company_name: str,
    total_findings: int,
    high_findings: int,
    medium_findings: int,
    low_findings: int,
    scan_duration_s: float,
    triggered_by: str = "client",
    scan_status: str = "done",
) -> None:
    """Notifikace: klient si sám spustil sken a ten doběhl."""
    duration_str = f"{scan_duration_s:.1f}s" if scan_duration_s else "N/A"
    html = _wrap("🔍 Organický sken dokončen", f"""
        <p><b>Firma:</b> {company_name}</p>
        <p><b>URL:</b> {url}</p>
        <p><b>Nálezů:</b> {total_findings} (🔴 {high_findings} high, 🟠 {medium_findings} medium, 🟢 {low_findings} low)</p>
        <p><b>Doba skenu:</b> {duration_str}</p>
        <p><b>Spustil:</b> {triggered_by}</p>
        <p style="margin-top:16px;">
            <a href="{ADMIN_PANEL_URL}/company/{company_id}" style="background:#6366f1; color:white; padding:10px 20px; border-radius:8px; text-decoration:none; font-weight:bold;">
                Detail firmy v admin panelu
            </a>
        </p>
    """)
    await _send_to_admins(f"🔍 Sken dokončen — {company_name} ({high_findings} high)", html)


# ──────────────────────────────────────────────────────────────────────
#  notify_deep_scan_started
# ──────────────────────────────────────────────────────────────────────

async def notify_deep_scan_started(
    scan_id: str,
    url: str,
    company_id: str,
) -> None:
    """Notifikace: hloubkový sken zahájen."""
    html = _wrap("🕵️ Hloubkový sken spuštěn", f"""
        <p><b>Scan ID:</b> {scan_id}</p>
        <p><b>URL:</b> {url}</p>
        <p><b>Company ID:</b> {company_id}</p>
        <p style="margin-top:16px;">
            <a href="{ADMIN_PANEL_URL}" style="background:#6366f1; color:white; padding:10px 20px; border-radius:8px; text-decoration:none; font-weight:bold;">
                Sledovat v admin panelu
            </a>
        </p>
    """)
    await _send_to_admins(f"🕵️ Deep scan spuštěn — {url}", html)


# ──────────────────────────────────────────────────────────────────────
#  notify_scan_results_viewed
# ──────────────────────────────────────────────────────────────────────

async def notify_scan_results_viewed(
    scan_id: str,
    url: str,
    company_name: str,
    total_findings: int,
    high_findings: int,
    time_on_results_s: float | None = None,
    scan_duration_s: float | None = None,
    client_waited: bool | None = None,
    triggered_by: str = "client",
) -> None:
    """Notifikace: klient si prohlédl výsledky skenu."""
    time_str = f"{time_on_results_s:.0f}s" if time_on_results_s else "N/A"
    html = _wrap("👁️ Klient si prohlédl výsledky", f"""
        <p><b>Firma:</b> {company_name}</p>
        <p><b>URL:</b> {url}</p>
        <p><b>Nálezů celkem:</b> {total_findings} (🔴 {high_findings} high)</p>
        <p><b>Čas na stránce výsledků:</b> {time_str}</p>
        <p><b>Čekal na výsledky:</b> {"ano" if client_waited else "ne" if client_waited is not None else "N/A"}</p>
        <p><b>Spustil:</b> {triggered_by}</p>
        <p style="margin-top:16px;">
            <a href="{ADMIN_PANEL_URL}" style="background:#6366f1; color:white; padding:10px 20px; border-radius:8px; text-decoration:none; font-weight:bold;">
                Otevřít admin panel
            </a>
        </p>
    """)
    await _send_to_admins(f"👁️ {company_name} — prohlédl výsledky ({high_findings} high)", html)


# ──────────────────────────────────────────────────────────────────────
#  notify_documents_pending_review
# ──────────────────────────────────────────────────────────────────────

async def notify_documents_pending_review(
    company_id: str,
    company_name: str,
    doc_count: int,
    doc_names: list[str],
) -> None:
    """Notifikace: nové dokumenty vygenerované pipeline čekají na review."""
    doc_list = "".join(f"<li>{name}</li>" for name in doc_names)
    html = _wrap(f"📄 {doc_count} nových dokumentů čeká na review", f"""
        <p><b>Firma:</b> {company_name}</p>
        <p><b>Počet dokumentů:</b> {doc_count}</p>
        <ul>{doc_list}</ul>
        <p style="margin-top:16px;">
            <a href="{ADMIN_PANEL_URL}/company/{company_id}" style="background:#6366f1; color:white; padding:10px 20px; border-radius:8px; text-decoration:none; font-weight:bold;">
                Zkontrolovat dokumenty
            </a>
        </p>
    """)
    await _send_to_admins(f"📄 {company_name} — {doc_count} dokumentů ke kontrole", html)
