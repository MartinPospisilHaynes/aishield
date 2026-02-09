"""
AIshield.cz — Alert System (Úkol 31)
5 typů automatických oznámení pro platící klienty.

Typy alertů:
  1. Nový AI systém detekován
  2. Transparenční prvek zmizel
  3. Změna chování AI systému
  4. Legislativní změna (manuální trigger)
  5. Měsíční compliance report

Každý alert: uloží do DB, pošle email, trackuje open/click.
"""

from dataclasses import dataclass
from datetime import datetime
from backend.database import get_supabase
from backend.outbound.email_engine import send_email
from backend.monitoring.diff_engine import ScanDiff, FindingChange


# ── Alert typy ──

ALERT_TYPES = {
    "new_ai_system": {
        "emoji": "🆕",
        "title_cs": "Nový AI systém detekován",
        "severity": "high",
    },
    "transparency_removed": {
        "emoji": "⚠️",
        "title_cs": "Transparenční prvek zmizel",
        "severity": "critical",
    },
    "ai_behavior_changed": {
        "emoji": "🔄",
        "title_cs": "Změna chování AI systému",
        "severity": "medium",
    },
    "legislative_change": {
        "emoji": "📜",
        "title_cs": "Legislativní změna",
        "severity": "high",
    },
    "monthly_report": {
        "emoji": "📊",
        "title_cs": "Měsíční compliance report",
        "severity": "info",
    },
}


@dataclass
class Alert:
    """Jeden alert pro klienta."""
    company_id: str
    company_name: str
    to_email: str
    alert_type: str
    title: str
    body_text: str
    severity: str  # critical | high | medium | info
    metadata: dict | None = None


# ── Generování alertů z diffu ──


def generate_alerts_from_diff(
    diff: ScanDiff,
    client_email: str,
) -> list[Alert]:
    """
    Analyzuje diff a vygeneruje příslušné alerty.
    Vrací seznam alertů, které je třeba odeslat.
    """
    alerts = []

    if not diff.has_changes:
        return alerts

    # 1. Nové AI systémy
    for change in diff.added:
        alerts.append(Alert(
            company_id=diff.company_id,
            company_name=diff.company_name,
            to_email=client_email,
            alert_type="new_ai_system",
            title=f"Nový AI systém na {diff.url}: {change.finding_name}",
            body_text=(
                f"Na webu {diff.url} byl detekován nový AI systém: "
                f"{change.finding_name} (kategorie: {change.category}, "
                f"riziko: {change.risk_level}). "
                f"Článek AI Act: {change.ai_act_article}."
            ),
            severity="high",
            metadata={
                "finding_name": change.finding_name,
                "category": change.category,
                "risk_level": change.risk_level,
            },
        ))

    # 2. Zmizevší AI systémy / transparenční prvky
    for change in diff.removed:
        # Pokud zmizela transparenční stránka → critical
        is_transparency = "transparen" in (change.finding_name or "").lower()
        alert_type = "transparency_removed" if is_transparency else "new_ai_system"
        severity = "critical" if is_transparency else "medium"

        alerts.append(Alert(
            company_id=diff.company_id,
            company_name=diff.company_name,
            to_email=client_email,
            alert_type=alert_type,
            title=f"{'⚠️ Transparenční prvek zmizel' if is_transparency else 'AI systém odstraněn'}: {change.finding_name}",
            body_text=(
                f"Na webu {diff.url} zmizel: {change.finding_name}. "
                f"{'Tento prvek byl součástí vaší compliance — zkontrolujte web!' if is_transparency else 'Systém byl odebrán z detekce.'}"
            ),
            severity=severity,
            metadata={"finding_name": change.finding_name, "was_present": True},
        ))

    # 3. Změněné AI systémy
    for change in diff.changed:
        alerts.append(Alert(
            company_id=diff.company_id,
            company_name=diff.company_name,
            to_email=client_email,
            alert_type="ai_behavior_changed",
            title=f"Změna AI systému na {diff.url}: {change.finding_name}",
            body_text=(
                f"AI systém {change.finding_name} změnil parametry: "
                f"{change.details}"
            ),
            severity="medium",
            metadata={"finding_name": change.finding_name, "changes": change.details},
        ))

    return alerts


# ── Email šablony pro alerty ──


def _render_alert_email(alert: Alert, dashboard_url: str) -> tuple[str, str]:
    """
    Vrátí (subject, html) pro alert email.
    """
    type_info = ALERT_TYPES.get(alert.alert_type, ALERT_TYPES["new_ai_system"])
    emoji = type_info["emoji"]

    severity_colors = {
        "critical": "#ef4444",  # red
        "high": "#f97316",      # orange
        "medium": "#eab308",    # yellow
        "info": "#22d3ee",      # cyan
    }
    color = severity_colors.get(alert.severity, "#94a3b8")

    subject = f"{emoji} AIshield: {alert.title}"

    html = f"""
<!DOCTYPE html>
<html lang="cs">
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #334155; line-height: 1.6;">

<div style="background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); border-radius: 12px; padding: 24px; margin-bottom: 24px;">
    <table cellpadding="0" cellspacing="0" width="100%"><tr>
        <td><h1 style="color: #e879f9; font-size: 18px; margin: 0;">AI<span style="color: white;">shield</span><span style="color: #64748b; font-size: 12px;">.cz</span></h1></td>
        <td style="text-align: right;"><span style="background: {color}22; color: {color}; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; border: 1px solid {color}44;">{type_info['title_cs']}</span></td>
    </tr></table>
</div>

<div style="background: {color}08; border-left: 4px solid {color}; padding: 16px 20px; border-radius: 0 8px 8px 0; margin-bottom: 20px;">
    <p style="margin: 0; font-weight: 600; color: #0f172a;">{emoji} {alert.title}</p>
</div>

<p>Dobrý den,</p>

<p>{alert.body_text}</p>

<div style="text-align: center; margin: 28px 0;">
    <a href="{dashboard_url}"
       style="display: inline-block; background: linear-gradient(135deg, #d946ef, #a855f7); color: white; font-weight: 600; padding: 14px 32px; border-radius: 10px; text-decoration: none; font-size: 15px;">
        Otevřít dashboard →
    </a>
</div>

<p style="font-size: 13px; color: #64748b;">
    Tento alert vám byl odeslán automaticky systémem AIshield.cz
    na základě monitoringu vašeho webu. Monitoring běží denně a sleduje
    změny AI systémů a compliance status.
</p>

<hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;">
<p style="font-size: 11px; color: #94a3b8; text-align: center;">
    AIshield.cz — Automatický AI Act compliance monitoring<br>
    <a href="https://aishield.cz/api/unsubscribe?email={alert.to_email}" style="color: #94a3b8;">Odhlásit se z alertů</a>
</p>

</body>
</html>"""

    return subject, html


def _render_monthly_report_email(
    company_name: str,
    url: str,
    to_email: str,
    total_findings: int,
    compliance_score: int,
    changes_this_month: int,
    dashboard_url: str,
) -> tuple[str, str]:
    """Měsíční reportovací email."""
    month_name = datetime.utcnow().strftime("%B %Y")

    score_color = (
        "#22c55e" if compliance_score >= 80 else
        "#eab308" if compliance_score >= 50 else
        "#ef4444"
    )

    subject = f"📊 AIshield: Měsíční report — {company_name} ({month_name})"

    html = f"""
<!DOCTYPE html>
<html lang="cs">
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #334155; line-height: 1.6;">

<div style="background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); border-radius: 12px; padding: 24px; margin-bottom: 24px;">
    <h1 style="color: #e879f9; font-size: 18px; margin: 0 0 8px 0;">AI<span style="color: white;">shield</span><span style="color: #64748b; font-size: 12px;">.cz</span></h1>
    <p style="color: #94a3b8; font-size: 14px; margin: 0;">Měsíční compliance report — {month_name}</p>
</div>

<p>Dobrý den,</p>

<p>Přehled compliance stavu webu <strong>{url}</strong> za uplynulý měsíc:</p>

<table cellpadding="0" cellspacing="0" width="100%" style="margin: 20px 0;">
    <tr>
        <td style="padding: 12px; background: #f8fafc; border-radius: 8px 0 0 8px; text-align: center; width: 33%;">
            <div style="font-size: 28px; font-weight: 700; color: {score_color};">{compliance_score}%</div>
            <div style="font-size: 12px; color: #64748b;">Compliance skóre</div>
        </td>
        <td style="padding: 12px; background: #f8fafc; text-align: center; width: 33%;">
            <div style="font-size: 28px; font-weight: 700; color: #0f172a;">{total_findings}</div>
            <div style="font-size: 12px; color: #64748b;">AI systémů</div>
        </td>
        <td style="padding: 12px; background: #f8fafc; border-radius: 0 8px 8px 0; text-align: center; width: 33%;">
            <div style="font-size: 28px; font-weight: 700; color: {'#ef4444' if changes_this_month > 0 else '#22c55e'};">{changes_this_month}</div>
            <div style="font-size: 12px; color: #64748b;">Změn tento měsíc</div>
        </td>
    </tr>
</table>

{"<p style='color: #22c55e; font-weight: 600;'>✅ Žádné změny — váš web je stabilní.</p>" if changes_this_month == 0 else f"<p style='color: #f97316; font-weight: 600;'>⚠️ {changes_this_month} změn detekováno — zkontrolujte dashboard.</p>"}

<p>AI Act vstupuje plně v platnost <strong>2. srpna 2026</strong>.
Zbývá <strong>{(datetime(2026, 8, 2) - datetime.utcnow()).days} dní</strong>.</p>

<div style="text-align: center; margin: 28px 0;">
    <a href="{dashboard_url}"
       style="display: inline-block; background: linear-gradient(135deg, #d946ef, #a855f7); color: white; font-weight: 600; padding: 14px 32px; border-radius: 10px; text-decoration: none; font-size: 15px;">
        Zobrazit detail v dashboardu →
    </a>
</div>

<hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;">
<p style="font-size: 11px; color: #94a3b8; text-align: center;">
    AIshield.cz — Automatický AI Act compliance monitoring<br>
    <a href="https://aishield.cz/api/unsubscribe?email={to_email}" style="color: #94a3b8;">Odhlásit se z reportů</a>
</p>

</body>
</html>"""

    return subject, html


# ── Odesílání alertů ──


async def send_alert(alert: Alert) -> dict:
    """Odešle alert emailem a uloží do DB."""
    supabase = get_supabase()
    dashboard_url = f"https://aishield.cz/dashboard"

    subject, html = _render_alert_email(alert, dashboard_url)

    # Odeslat email
    result = await send_email(
        to=alert.to_email,
        subject=subject,
        html=html,
    )

    # Uložit alert do DB
    supabase.table("alerts").insert({
        "company_id": alert.company_id,
        "to_email": alert.to_email,
        "alert_type": alert.alert_type,
        "title": alert.title,
        "severity": alert.severity,
        "body_text": alert.body_text,
        "email_sent": result.get("id") != "dry_run",
        "resend_id": result.get("id", ""),
        "metadata": alert.metadata,
        "created_at": datetime.utcnow().isoformat(),
    }).execute()

    return {
        "alert_type": alert.alert_type,
        "to": alert.to_email,
        "sent": result.get("id") != "dry_run",
        "resend_id": result.get("id", ""),
    }


async def send_alerts_from_diff(
    diff: ScanDiff,
    client_email: str,
) -> list[dict]:
    """Generuje a odesílá všechny alerty z diffu."""
    alerts = generate_alerts_from_diff(diff, client_email)
    results = []

    for alert in alerts:
        result = await send_alert(alert)
        results.append(result)

    return results


async def send_monthly_report(
    company_id: str,
    to_email: str,
) -> dict:
    """Vygeneruje a odešle měsíční compliance report."""
    supabase = get_supabase()

    # Načteme firmu
    company = supabase.table("companies").select(
        "name, url"
    ).eq("id", company_id).limit(1).execute()

    if not company.data:
        return {"error": "Firma nenalezena"}

    name = company.data[0]["name"]
    url = company.data[0]["url"]

    # Poslední sken
    last_scan = supabase.table("scans").select(
        "id, total_findings"
    ).eq("company_id", company_id).eq(
        "status", "done"
    ).order("created_at", desc=True).limit(1).execute()

    total_findings = last_scan.data[0]["total_findings"] if last_scan.data else 0

    # Compliance skóre
    if last_scan.data:
        findings = supabase.table("findings").select(
            "confirmed_by_client, status"
        ).eq("scan_id", last_scan.data[0]["id"]).neq(
            "source", "ai_classified_fp"
        ).execute()

        total = len(findings.data or [])
        resolved = sum(
            1 for f in (findings.data or [])
            if f.get("confirmed_by_client") == "false_positive"
            or f.get("status") == "resolved"
        )
        compliance_score = round((resolved / total) * 100) if total > 0 else 0
    else:
        compliance_score = 0

    # Změny tento měsíc (z scan_diffs)
    from datetime import timedelta
    month_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
    diffs = supabase.table("scan_diffs").select(
        "has_changes, added_count, removed_count, changed_count"
    ).eq("company_id", company_id).gte(
        "created_at", month_ago
    ).execute()

    changes_this_month = sum(
        (d.get("added_count", 0) + d.get("removed_count", 0) + d.get("changed_count", 0))
        for d in (diffs.data or [])
    )

    dashboard_url = "https://aishield.cz/dashboard"

    subject, html = _render_monthly_report_email(
        company_name=name,
        url=url,
        to_email=to_email,
        total_findings=total_findings,
        compliance_score=compliance_score,
        changes_this_month=changes_this_month,
        dashboard_url=dashboard_url,
    )

    result = await send_email(to=to_email, subject=subject, html=html)

    # Uložit alert
    supabase.table("alerts").insert({
        "company_id": company_id,
        "to_email": to_email,
        "alert_type": "monthly_report",
        "title": f"Měsíční report — {name}",
        "severity": "info",
        "body_text": f"Compliance: {compliance_score}%, Findings: {total_findings}, Změny: {changes_this_month}",
        "email_sent": result.get("id") != "dry_run",
        "resend_id": result.get("id", ""),
        "created_at": datetime.utcnow().isoformat(),
    }).execute()

    return {
        "alert_type": "monthly_report",
        "to": to_email,
        "compliance_score": compliance_score,
        "changes_this_month": changes_this_month,
        "sent": result.get("id") != "dry_run",
    }


async def trigger_legislative_alert(
    title: str,
    body_text: str,
) -> dict:
    """
    Manuální trigger: legislativní změna → pošli alert VŠEM platícím klientům.
    Volá se z admin dashboardu.
    """
    supabase = get_supabase()

    # Všichni platící klienti
    orders = supabase.table("orders").select(
        "user_email"
    ).eq("status", "paid").execute()

    unique_emails = list(set(row["user_email"] for row in (orders.data or [])))
    results = []

    for email in unique_emails:
        # Najdi firmu
        comp = supabase.table("companies").select("id, name").eq(
            "email", email
        ).limit(1).execute()

        company_id = comp.data[0]["id"] if comp.data else ""
        company_name = comp.data[0]["name"] if comp.data else "Váš web"

        alert = Alert(
            company_id=company_id,
            company_name=company_name,
            to_email=email,
            alert_type="legislative_change",
            title=title,
            body_text=body_text,
            severity="high",
            metadata={"manual_trigger": True},
        )

        result = await send_alert(alert)
        results.append(result)

    return {
        "alert_type": "legislative_change",
        "recipients": len(unique_emails),
        "results": results,
    }


# ── Hlavní monitoring pipeline ──


async def run_monitoring_with_alerts() -> dict:
    """
    Kompletní monitoring pipeline:
    1. Reskenuj všechny platící klienty
    2. Pro každého udělej diff s předchozím skenem
    3. Pokud se něco změnilo → pošli alert
    4. Uloží diff do DB

    Volá se z orchestrátoru (03:00 monitoring task).
    """
    from backend.monitoring.diff_engine import run_diff_for_company, save_diff_to_db
    from backend.scanner.pipeline import run_scan_pipeline

    supabase = get_supabase()

    # Všichni platící klienti
    orders = supabase.table("orders").select(
        "user_email"
    ).eq("status", "paid").execute()

    unique_emails = list(set(row["user_email"] for row in (orders.data or [])))
    stats = {
        "clients_scanned": 0,
        "diffs_found": 0,
        "alerts_sent": 0,
        "errors": 0,
    }

    for email in unique_emails:
        comp = supabase.table("companies").select("id, url").eq(
            "email", email
        ).limit(1).execute()

        if not comp.data or not comp.data[0].get("url"):
            continue

        company_id = comp.data[0]["id"]
        url = comp.data[0]["url"]

        try:
            # 1. Resken
            # Vytvoří nový sken
            from datetime import timezone
            now = datetime.now(timezone.utc).isoformat()
            scan_res = supabase.table("scans").insert({
                "company_id": company_id,
                "url_scanned": url,
                "status": "queued",
                "triggered_by": "monitoring",
                "started_at": now,
            }).execute()

            scan_id = scan_res.data[0]["id"]
            await run_scan_pipeline(scan_id, url, company_id)
            stats["clients_scanned"] += 1

            # 2. Diff
            diff = await run_diff_for_company(company_id)
            if diff and diff.has_changes:
                # Uložit diff
                await save_diff_to_db(diff)
                stats["diffs_found"] += 1

                # 3. Alerty
                alert_results = await send_alerts_from_diff(diff, email)
                stats["alerts_sent"] += len(alert_results)

        except Exception as e:
            print(f"[Monitoring] Chyba pro {email}: {e}")
            stats["errors"] += 1

    return stats
