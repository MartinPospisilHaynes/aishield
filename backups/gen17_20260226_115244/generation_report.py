"""
AIshield.cz — Generation Report Email v1
=========================================
Po každé generaci pipeline automaticky odešle přehledný report
na konfigurovaný email s výstupy z M2, M3 a M5 modulů.

Formát: čistý text, přehledný, čitelný na mobilu v posilovně.
"""

import logging
import asyncio
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ── Konfigurace ──
REPORT_EMAIL = "bc.pospa@gmail.com"
REPORT_FROM_EMAIL = "info@aishield.cz"
REPORT_FROM_NAME = "AIshield Pipeline"

# ── Mapování závažností na emoji-free značky ──
SEVERITY_MAP = {
    "kritická": "[!!!]",
    "závažná": "[!!]",
    "důležitá": "[!]",
    "doporučení": "[~]",
    "poznámka": "[.]",
}


def _format_findings(nalezy: list[dict], max_items: int = 10) -> str:
    """Naformátuje nálezy do čitelného textu."""
    if not nalezy:
        return "    (žádné nálezy)\n"

    lines = []
    for i, n in enumerate(nalezy[:max_items], 1):
        severity = n.get("zavaznost", "?")
        marker = SEVERITY_MAP.get(severity, f"[{severity}]")
        oblast = n.get("oblast", "?")
        popis = n.get("popis", n.get("popis_problemu", "?"))
        doporuceni = n.get("doporuceni", "")
        ref = n.get("reference_ai_act", "")

        lines.append(f"    {i}. {marker} {oblast}")
        lines.append(f"       {popis}")
        if doporuceni:
            lines.append(f"       -> {doporuceni}")
        if ref:
            lines.append(f"       (ref: {ref})")
        lines.append("")

    if len(nalezy) > max_items:
        lines.append(f"    ... a dalších {len(nalezy) - max_items} nálezů")
        lines.append("")

    return "\n".join(lines)


def _format_list(items: list, prefix: str = "    - ") -> str:
    """Naformátuje seznam položek."""
    if not items:
        return "    (žádné)\n"
    return "\n".join(f"{prefix}{item}" for item in items) + "\n"


def build_report_text(
    generation_id: str,
    all_critiques: dict[str, dict],
    m5_result: dict | None,
    pipeline_log: list[dict],
    total_cost: float,
    total_tokens: int,
    total_time: float,
    doc_names: dict[str, str] | None = None,
) -> str:
    """
    Sestaví kompletní textový report z jedné generace.
    
    Args:
        generation_id: ID generace (např. "gen_20260226_064455")
        all_critiques: dict doc_key -> {"eu": {...}, "client": {...}}
        m5_result: výstup z M5 (nebo None pokud neběžel)
        pipeline_log: seznam logových záznamů z pipeline
        total_cost: celkové náklady v USD
        total_tokens: celkový počet tokenů
        total_time: celkový čas v sekundách
        doc_names: mapování doc_key -> český název (volitelné)
    """
    now = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")
    doc_names = doc_names or {}

    lines = []
    lines.append("=" * 70)
    lines.append(f"  AISHIELD — REPORT GENERACE {generation_id}")
    lines.append(f"  {now}")
    lines.append("=" * 70)
    lines.append("")

    # ── Souhrnná tabulka ──
    lines.append("SOUHRN")
    lines.append("-" * 40)

    # Spočítáme průměry
    eu_scores = []
    client_scores = []
    for entry in pipeline_log:
        if "eu_score" in entry:
            try:
                eu_scores.append(int(entry["eu_score"]))
            except (ValueError, TypeError):
                pass
        if "client_score" in entry:
            try:
                client_scores.append(int(entry["client_score"]))
            except (ValueError, TypeError):
                pass

    eu_avg = sum(eu_scores) / len(eu_scores) if eu_scores else 0
    client_avg = sum(client_scores) / len(client_scores) if client_scores else 0

    doc_count = sum(1 for e in pipeline_log if "doc_key" in e and "error" not in e)
    err_count = sum(1 for e in pipeline_log if "error" in e and "doc_key" in e)

    lines.append(f"  Dokumenty:        {doc_count} hotových, {err_count} chyb")
    lines.append(f"  EU skóre (avg):   {eu_avg:.1f}/10")
    lines.append(f"  Klient skóre:     {client_avg:.1f}/10")
    lines.append(f"  Celkové náklady:  ${total_cost:.2f}")
    lines.append(f"  Celkové tokeny:   {total_tokens:,}")
    lines.append(f"  Celkový čas:      {total_time:.0f}s ({total_time/60:.1f} min)")
    lines.append("")

    # ── Skóre po dokumentech ──
    lines.append("SKÓRE PO DOKUMENTECH")
    lines.append("-" * 40)
    for entry in pipeline_log:
        if "doc_key" not in entry:
            continue
        dk = entry["doc_key"]
        dn = entry.get("doc_name", doc_names.get(dk, dk))
        eu = entry.get("eu_score", "?")
        cl = entry.get("client_score", "?")
        err = entry.get("error", "")
        if err:
            lines.append(f"  {dn:.<40s} CHYBA: {err[:60]}")
        else:
            lines.append(f"  {dn:.<40s} EU={eu}/10  Klient={cl}/10")
    lines.append("")

    # ══════════════════════════════════════════════════════════
    # M2 — EU INSPEKTOR: Detailní výtky
    # ══════════════════════════════════════════════════════════
    lines.append("")
    lines.append("=" * 70)
    lines.append("  M2 — EU INSPEKTOR (Claude): CO VYTÝKÁ")
    lines.append("=" * 70)
    lines.append("")

    for doc_key, critiques in all_critiques.items():
        eu = critiques.get("eu", {})
        dn = doc_names.get(doc_key, doc_key)
        score = eu.get("skore", "?")
        hodnoceni = eu.get("celkove_hodnoceni", "?")

        lines.append(f"  [{score}/10] {dn} ({hodnoceni})")
        lines.append(f"  {'~' * 50}")

        # Myšlenkový proces
        cot = eu.get("myslenkovy_proces", "")
        if cot:
            lines.append(f"  Závěr inspektora: {cot}")
            lines.append("")

        # Nálezy
        nalezy = eu.get("nalezy", [])
        if nalezy:
            lines.append("  Nálezy:")
            lines.append(_format_findings(nalezy))

        # Silné stránky
        silne = eu.get("silne_stranky", [])
        if silne:
            lines.append("  Silné stránky:")
            lines.append(_format_list(silne))

        # Chybějící obsah
        chybejici = eu.get("chybejici_obsah", [])
        if chybejici:
            lines.append("  Chybějící obsah:")
            lines.append(_format_list(chybejici))

        # Celkové doporučení
        doporuc = eu.get("celkove_doporuceni", "")
        if doporuc:
            lines.append(f"  Doporučení: {doporuc}")

        lines.append("")
        lines.append("")

    # ══════════════════════════════════════════════════════════
    # M3 — ZÁKAZNÍK: Detailní výtky
    # ══════════════════════════════════════════════════════════
    lines.append("=" * 70)
    lines.append("  M3 — ZÁKAZNÍK (Gemini): CO MU VADÍ")
    lines.append("=" * 70)
    lines.append("")

    for doc_key, critiques in all_critiques.items():
        client = critiques.get("client", {})
        dn = doc_names.get(doc_key, doc_key)
        score = client.get("skore", "?")
        hodnoceni = client.get("celkove_hodnoceni", "?")

        lines.append(f"  [{score}/10] {dn} ({hodnoceni})")
        lines.append(f"  {'~' * 50}")

        # Myšlenkový proces
        cot = client.get("myslenkovy_proces", "")
        if cot:
            lines.append(f"  Dojem klienta: {cot}")
            lines.append("")

        # Nálezy
        nalezy = client.get("nalezy", [])
        if nalezy:
            lines.append("  Nálezy:")
            lines.append(_format_findings(nalezy))

        # Silné stránky
        silne = client.get("silne_stranky", [])
        if silne:
            lines.append("  Silné stránky:")
            lines.append(_format_list(silne))

        # Otázky klienta
        otazky = client.get("otazky_klienta", [])
        if otazky:
            lines.append("  Otázky klienta:")
            lines.append(_format_list(otazky))

        # Celkové doporučení
        doporuc = client.get("celkove_doporuceni", "")
        if doporuc:
            lines.append(f"  Doporučení: {doporuc}")

        lines.append("")
        lines.append("")

    # ══════════════════════════════════════════════════════════
    # M5 — SELF-IMPROVEMENT: Co se naučil a co zapsal do M1
    # ══════════════════════════════════════════════════════════
    lines.append("=" * 70)
    lines.append("  M5 — SELF-IMPROVEMENT: CO SE NAUČIL")
    lines.append("=" * 70)
    lines.append("")

    if m5_result and m5_result.get("status") == "optimized":
        lines.append(f"  Verze pravidel:   v{m5_result.get('version', '?')}")
        lines.append(f"  Nových pravidel:  {m5_result.get('rules_added', '?')}")
        lines.append(f"  Průměrné skóre:   {m5_result.get('avg_score', '?')}")
        lines.append(f"  Konvergováno:     {'ANO' if m5_result.get('converged') else 'NE'}")
        lines.append(f"  Náklady M5:       ${m5_result.get('cost_usd', 0):.4f}")
        lines.append(f"  Čas M5:           {m5_result.get('time_s', 0):.1f}s")
        lines.append("")

        # Pravidla
        rules = m5_result.get("rules", [])
        if rules:
            lines.append("  NOVÁ PRAVIDLA ZAPSANÁ DO M1:")
            lines.append("  " + "-" * 40)
            for i, rule in enumerate(rules, 1):
                text = rule if isinstance(rule, str) else rule.get("text", rule.get("pravidlo", str(rule)))
                reason = rule.get("duvod", "") if isinstance(rule, dict) else ""
                lines.append(f"")
                lines.append(f"  Pravidlo #{i}:")
                lines.append(f"    {text}")
                if reason:
                    lines.append(f"    Důvod: {reason}")
            lines.append("")

        # Komentář
        comment = m5_result.get("comment", "")
        if comment:
            lines.append(f"  KOMENTÁŘ M5:")
            lines.append(f"  {comment}")
            lines.append("")

    elif m5_result and m5_result.get("status") == "converged":
        lines.append("  M5 konvergoval — pravidla jsou stabilní, žádné nové úpravy.")
        lines.append("")
    elif m5_result and m5_result.get("error"):
        lines.append(f"  M5 CHYBA: {m5_result.get('error')}")
        lines.append("")
    else:
        lines.append("  M5 neběžel nebo neprodukoval výstup.")
        lines.append("")

    # ── Chyby pipeline ──
    errors_in_log = [e for e in pipeline_log if "error" in e and "doc_key" in e]
    if errors_in_log:
        lines.append("")
        lines.append("=" * 70)
        lines.append("  CHYBY PIPELINE")
        lines.append("=" * 70)
        for e in errors_in_log:
            lines.append(f"  {e.get('doc_name', e.get('doc_key', '?'))}: {e['error'][:200]}")
        lines.append("")

    # ── Patička ──
    lines.append("")
    lines.append("-" * 70)
    lines.append("  Automaticky generováno pipeline v3 | AIshield.cz")
    lines.append("-" * 70)

    return "\n".join(lines)


def build_report_html(text_report: str) -> str:
    """Zabalí textový report do minimálního HTML pro email."""
    # Escapujeme HTML znaky
    import html as html_mod
    escaped = html_mod.escape(text_report)

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: 'Courier New', monospace; font-size: 13px; line-height: 1.5; background: #f5f5f5; padding: 20px;">
<pre style="white-space: pre-wrap; word-wrap: break-word; background: #fff; padding: 20px; border-radius: 8px; border: 1px solid #ddd; max-width: 800px; margin: 0 auto;">
{escaped}
</pre>
</body>
</html>"""


async def send_generation_report(
    generation_id: str,
    all_critiques: dict[str, dict],
    m5_result: dict | None,
    pipeline_log: list[dict],
    total_cost: float,
    total_tokens: int,
    total_time: float,
    doc_names: dict[str, str] | None = None,
    recipient: str = REPORT_EMAIL,
) -> dict:
    """
    Sestaví a odešle report generace emailem.
    
    Returns:
        dict s klíči: {"sent": bool, "resend_id": str, "error": str}
    """
    try:
        # 1. Sestav textový report
        text_report = build_report_text(
            generation_id=generation_id,
            all_critiques=all_critiques,
            m5_result=m5_result,
            pipeline_log=pipeline_log,
            total_cost=total_cost,
            total_tokens=total_tokens,
            total_time=total_time,
            doc_names=doc_names,
        )

        # 2. Zabal do HTML
        html_report = build_report_html(text_report)

        # 3. Odešli
        subject = f"[AIshield] Report generace {generation_id}"

        from backend.outbound.email_engine import send_email
        result = await send_email(
            to=recipient,
            subject=subject,
            html=html_report,
            from_email=REPORT_FROM_EMAIL,
            from_name=REPORT_FROM_NAME,
        )

        resend_id = result.get("id", "?")
        logger.info(f"[GenReport] Report odeslán na {recipient} (resend_id={resend_id})")

        return {"sent": True, "resend_id": resend_id, "text_report": text_report}

    except Exception as e:
        logger.error(f"[GenReport] Chyba při odesílání reportu: {e}", exc_info=True)
        return {"sent": False, "error": str(e), "text_report": text_report if 'text_report' in dir() else ""}
