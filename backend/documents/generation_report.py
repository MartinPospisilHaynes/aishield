"""
AIshield.cz — Generation Report (v2 — Inspekční zpráva)

Odesílá po každé generaci strukturovanou inspekční zprávu emailem.
Formát: profesionální HTML report s tabulkami a detaily per dokument.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def _score_color(score) -> str:
    """Barva pro skóre."""
    try:
        s = int(score)
    except (ValueError, TypeError):
        return "#666"
    if s >= 8:
        return "#2e7d32"  # green
    if s >= 6:
        return "#f57f17"  # amber
    return "#c62828"  # red


def _severity_badge(severity: str) -> str:
    """HTML badge pro závažnost."""
    colors = {
        "kritická": ("#c62828", "#fff"),
        "důležitá": ("#e65100", "#fff"),
        "menší": ("#1565c0", "#fff"),
        "poznámka": ("#666", "#fff"),
    }
    bg, fg = colors.get(severity.lower(), ("#666", "#fff"))
    return (
        f'<span style="background:{bg};color:{fg};padding:2px 8px;'
        f'border-radius:3px;font-size:12px;font-weight:bold;">'
        f'{severity.upper()}</span>'
    )


def build_report_html(
    generation_id: str,
    all_critiques: dict,
    m5_result: Optional[dict],
    pipeline_log: list,
    total_cost: float,
    total_tokens: int,
    total_time: float,
    doc_names: dict,
) -> str:
    """Sestaví HTML inspekční zprávu."""

    now = datetime.now(timezone.utc).strftime("%d. %m. %Y %H:%M UTC")

    # Spočítej sumární statistiky
    doc_count = 0
    error_count = 0
    eu_scores = []
    client_scores = []
    for entry in pipeline_log:
        if entry.get("doc_key"):
            if entry.get("error"):
                error_count += 1
            else:
                doc_count += 1
                try:
                    eu_scores.append(int(entry.get("eu_score", 0)))
                except (ValueError, TypeError):
                    pass
                try:
                    client_scores.append(int(entry.get("client_score", 0)))
                except (ValueError, TypeError):
                    pass

    avg_eu = sum(eu_scores) / len(eu_scores) if eu_scores else 0
    avg_client = sum(client_scores) / len(client_scores) if client_scores else 0
    avg_overall = (avg_eu + avg_client) / 2 if (eu_scores and client_scores) else 0

    # Celkový verdikt
    if avg_overall >= 8:
        verdict = "VYHOVUJÍCÍ"
        verdict_color = "#2e7d32"
        verdict_icon = "&#9989;"
    elif avg_overall >= 6:
        verdict = "PODMÍNEČNĚ VYHOVUJÍCÍ"
        verdict_color = "#f57f17"
        verdict_icon = "&#9888;"
    else:
        verdict = "NEVYHOVUJÍCÍ"
        verdict_color = "#c62828"
        verdict_icon = "&#10060;"

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:Arial,Helvetica,sans-serif;max-width:800px;margin:0 auto;color:#333;line-height:1.5;">

<!-- HLAVIČKA -->
<div style="background:#1a237e;color:white;padding:24px 32px;border-radius:8px 8px 0 0;">
  <h1 style="margin:0;font-size:22px;">INSPEKČNÍ ZPRÁVA GENERACE</h1>
  <p style="margin:8px 0 0;opacity:0.8;font-size:14px;">AIshield.cz | {generation_id} | {now}</p>
</div>

<!-- VERDIKT -->
<div style="background:{verdict_color};color:white;padding:16px 32px;font-size:18px;font-weight:bold;">
  {verdict_icon} CELKOVÝ VERDIKT: {verdict}
  <span style="float:right;font-size:24px;">{avg_overall:.1f}/10</span>
</div>

<!-- SUMÁRNÍ TABULKA -->
<table style="width:100%;border-collapse:collapse;margin:0;" cellpadding="12">
  <tr style="background:#f5f5f5;">
    <td style="border:1px solid #ddd;"><strong>Dokumentů</strong><br>{doc_count} OK, {error_count} chyb</td>
    <td style="border:1px solid #ddd;"><strong>EU Inspektor</strong><br><span style="color:{_score_color(avg_eu)};font-size:20px;font-weight:bold;">{avg_eu:.1f}/10</span></td>
    <td style="border:1px solid #ddd;"><strong>Klient</strong><br><span style="color:{_score_color(avg_client)};font-size:20px;font-weight:bold;">{avg_client:.1f}/10</span></td>
    <td style="border:1px solid #ddd;"><strong>Náklady</strong><br>${total_cost:.2f} | {total_tokens:,} tok</td>
    <td style="border:1px solid #ddd;"><strong>Čas</strong><br>{total_time / 60:.0f} min</td>
  </tr>
</table>

<!-- DETAIL PER DOKUMENT -->
<h2 style="margin:24px 0 12px;color:#1a237e;border-bottom:2px solid #1a237e;padding-bottom:8px;">
  DETAIL PO DOKUMENTECH
</h2>
"""

    # Per-document detail
    for entry in pipeline_log:
        dk = entry.get("doc_key")
        if not dk:
            continue

        doc_name = doc_names.get(dk, dk)

        if entry.get("error"):
            html += f"""
<div style="background:#ffebee;border-left:4px solid #c62828;padding:12px 16px;margin:8px 0;">
  <strong style="color:#c62828;">&#10060; {doc_name}</strong> — CHYBA: {entry['error'][:200]}
</div>"""
            continue

        eu_s = entry.get("eu_score", "?")
        cl_s = entry.get("client_score", "?")
        cost = entry.get("cost_usd", 0)
        chars = entry.get("final_chars", 0)
        time_s = entry.get("time_s", 0)

        # Get critiques for this doc
        crit = all_critiques.get(dk, {})
        eu_crit = crit.get("eu", {})
        cl_crit = crit.get("client", {})

        eu_findings = eu_crit.get("nalezy", [])
        cl_findings = cl_crit.get("nalezy", [])
        eu_missing = eu_crit.get("chybejici_obsah", [])
        cl_missing = cl_crit.get("chybejici_obsah", [])
        eu_strengths = eu_crit.get("silne_stranky", [])

        html += f"""
<div style="border:1px solid #ddd;margin:12px 0;border-radius:4px;">
  <div style="background:#e8eaf6;padding:10px 16px;display:flex;justify-content:space-between;align-items:center;">
    <strong>{doc_name}</strong>
    <span>
      EU: <span style="color:{_score_color(eu_s)};font-weight:bold;">{eu_s}/10</span>
      &nbsp;|&nbsp;
      Klient: <span style="color:{_score_color(cl_s)};font-weight:bold;">{cl_s}/10</span>
      &nbsp;|&nbsp;
      ${cost:.3f} &nbsp;|&nbsp; {chars:,} zn &nbsp;|&nbsp; {time_s:.0f}s
    </span>
  </div>"""

        # EU findings
        if eu_findings:
            html += '\n  <div style="padding:8px 16px;">'
            html += '\n    <strong style="color:#1a237e;">Nálezy EU inspektora:</strong><br>'
            for n in eu_findings:
                sev = n.get("zavaznost", "?")
                html += f'\n    {_severity_badge(sev)} {n.get("oblast", "?")}: {n.get("popis", "?")}<br>'
                if n.get("doporuceni"):
                    html += f'\n    <span style="color:#555;font-size:13px;margin-left:16px;">&#8594; {n["doporuceni"]}</span><br>'
            html += '\n  </div>'

        # Client findings
        if cl_findings:
            html += '\n  <div style="padding:8px 16px;">'
            html += '\n    <strong style="color:#e65100;">Nálezy klienta:</strong><br>'
            for n in cl_findings:
                sev = n.get("zavaznost", "?")
                html += f'\n    {_severity_badge(sev)} {n.get("oblast", "?")}: {n.get("popis", "?")}<br>'
            html += '\n  </div>'

        # Missing content
        all_missing = list(set((eu_missing or []) + (cl_missing or [])))
        if all_missing:
            html += '\n  <div style="padding:8px 16px;">'
            html += '\n    <strong style="color:#c62828;">Chybějící obsah:</strong><br>'
            for m in all_missing[:8]:
                html += f'\n    &#8226; {m}<br>'
            html += '\n  </div>'

        # Strengths (condensed)
        if eu_strengths:
            html += '\n  <div style="padding:8px 16px;background:#e8f5e9;">'
            html += '\n    <strong style="color:#2e7d32;">Silné stránky:</strong> '
            html += "; ".join(str(s)[:80] for s in eu_strengths[:4])
            html += '\n  </div>'

        html += '\n</div>'

    # M5 Section
    if m5_result and m5_result.get("status") != "error":
        m5_version = m5_result.get("version", "?")
        m5_rules = m5_result.get("rules_added", 0)
        m5_avg = m5_result.get("avg_score", 0)
        m5_converged = m5_result.get("converged", False)
        m5_cost = m5_result.get("cost_usd", 0)

        html += f"""
<h2 style="margin:24px 0 12px;color:#4a148c;border-bottom:2px solid #4a148c;padding-bottom:8px;">
  SELF-IMPROVEMENT (M5)
</h2>
<table style="width:100%;border-collapse:collapse;" cellpadding="8">
  <tr style="background:#f3e5f5;">
    <td style="border:1px solid #ddd;"><strong>Verze</strong><br>v{m5_version}</td>
    <td style="border:1px solid #ddd;"><strong>Nová pravidla</strong><br>{m5_rules}</td>
    <td style="border:1px solid #ddd;"><strong>Prům. skóre</strong><br>{m5_avg:.1f}/10</td>
    <td style="border:1px solid #ddd;"><strong>Konvergence</strong><br>{"ANO" if m5_converged else "NE"}</td>
    <td style="border:1px solid #ddd;"><strong>Cost</strong><br>${m5_cost:.3f}</td>
  </tr>
</table>"""

        # M5 patterns if available
        m5_full = m5_result.get("full_response", {})
        patterns = (
            m5_full.get("analyza", {}).get("identifikovane_vzory", [])
            if isinstance(m5_full, dict) else []
        )
        if patterns:
            html += '\n<div style="padding:12px 16px;margin:8px 0;border:1px solid #ce93d8;border-radius:4px;">'
            html += '\n  <strong>Identifikované vzory:</strong><br>'
            for p in patterns:
                html += (
                    f'\n  &#8226; <strong>{p.get("vzor", "?")}</strong> '
                    f'({p.get("pocet_vyskytu", "?")}x, {p.get("zavaznost", "?")}): '
                    f'{p.get("popis_problemu", "?")[:150]}<br>'
                )
            html += '\n</div>'

    # Footer
    html += f"""
<div style="margin:32px 0 16px;padding:16px;background:#eceff1;border-radius:4px;font-size:13px;color:#666;">
  <strong>AIshield.cz</strong> | Automatická inspekční zpráva | {generation_id}<br>
  Generováno: {now} | Celkové náklady: ${total_cost:.2f} | Tokeny: {total_tokens:,} | Čas: {total_time / 60:.1f} min
</div>

</body>
</html>"""

    return html


def build_report_text(
    generation_id: str,
    all_critiques: dict,
    m5_result: Optional[dict],
    pipeline_log: list,
    total_cost: float,
    total_tokens: int,
    total_time: float,
    doc_names: dict,
) -> str:
    """Sestaví plain-text verzi inspekční zprávy (fallback)."""
    lines = []
    lines.append("=" * 60)
    lines.append("INSPEKČNÍ ZPRÁVA GENERACE")
    lines.append(f"ID: {generation_id}")
    lines.append(f"Datum: {datetime.now(timezone.utc).strftime('%d. %m. %Y %H:%M UTC')}")
    lines.append("=" * 60)
    lines.append("")

    for entry in pipeline_log:
        dk = entry.get("doc_key")
        if not dk:
            continue
        doc_name = doc_names.get(dk, dk)
        if entry.get("error"):
            lines.append(f"[CHYBA] {doc_name}: {entry['error'][:150]}")
            continue
        eu_s = entry.get("eu_score", "?")
        cl_s = entry.get("client_score", "?")
        lines.append(
            f"{doc_name}: EU={eu_s}/10, Klient={cl_s}/10, "
            f"${entry.get('cost_usd', 0):.3f}"
        )

        crit = all_critiques.get(dk, {})
        for n in crit.get("eu", {}).get("nalezy", []):
            lines.append(
                f"  [{n.get('zavaznost', '?').upper()}] "
                f"{n.get('oblast', '?')}: {n.get('popis', '?')[:100]}"
            )

    lines.append("")
    lines.append(
        f"Celkem: ${total_cost:.2f} | {total_tokens:,} tokenů | "
        f"{total_time / 60:.1f} min"
    )
    return "\n".join(lines)


async def send_generation_report(
    generation_id: str,
    all_critiques: dict,
    m5_result: Optional[dict],
    pipeline_log: list,
    total_cost: float,
    total_tokens: int,
    total_time: float,
    doc_names: dict,
) -> dict:
    """Odešle inspekční zprávu emailem přes Resend."""
    try:
        from backend.outbound.email_engine import send_email

        html = build_report_html(
            generation_id, all_critiques, m5_result,
            pipeline_log, total_cost, total_tokens, total_time, doc_names,
        )
        text = build_report_text(
            generation_id, all_critiques, m5_result,
            pipeline_log, total_cost, total_tokens, total_time, doc_names,
        )

        # Spočítej průměrné skóre pro subject
        eu_scores = []
        cl_scores = []
        for entry in pipeline_log:
            if entry.get("doc_key") and not entry.get("error"):
                try:
                    eu_scores.append(int(entry.get("eu_score", 0)))
                except (ValueError, TypeError):
                    pass
                try:
                    cl_scores.append(int(entry.get("client_score", 0)))
                except (ValueError, TypeError):
                    pass
        avg_eu = sum(eu_scores) / len(eu_scores) if eu_scores else 0
        avg_cl = sum(cl_scores) / len(cl_scores) if cl_scores else 0
        avg = (avg_eu + avg_cl) / 2

        # Verdikt pro subject
        if avg >= 8:
            verdict = "PASS"
        elif avg >= 6:
            verdict = "WARN"
        else:
            verdict = "FAIL"

        doc_ok = sum(1 for e in pipeline_log if e.get("doc_key") and not e.get("error"))
        doc_err = sum(1 for e in pipeline_log if e.get("doc_key") and e.get("error"))

        subject = (
            f"[{verdict}] {generation_id} | {avg:.1f}/10 | "
            f"{doc_ok} OK, {doc_err} err | ${total_cost:.2f}"
        )

        result = await send_email(
            to="bc.pospa@gmail.com",
            subject=subject,
            html=html,
            text=text,
            sender_name="AIshield Inspector",
        )

        logger.info(f"[Report] Inspekční zpráva odeslána: {result.get('resend_id', '?')}")
        return {"sent": True, "resend_id": result.get("resend_id", "")}

    except Exception as e:
        logger.error(f"[Report] Odeslání selhalo: {e}", exc_info=True)
        return {"sent": False, "error": str(e)}
