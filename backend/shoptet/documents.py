"""
AIshield.cz — Shoptet Addon: Document Generator
Generuje PDF dokumenty pro e-shopy (Free i Standard plán).

Free plán:
  - AI Registr (seznam AI systémů, klasifikace, riziko)
  - Compliance Checklist (akční plán před deadline)

Dokumenty se generují po vyplnění dotazníku.
PDF přes WeasyPrint (HTML → PDF).
Uloží se do Supabase Storage + metadata do shoptet_documents.
"""

import io
import logging
from datetime import datetime, timezone

from backend.database import get_supabase

logger = logging.getLogger("shoptet.documents")


def _generate_register_html(eshop_name: str, ai_systems: list[dict], score: int, breakdown: dict) -> str:
    """Generuje HTML pro AI Registr (seznam AI systémů)."""
    now = datetime.now(timezone.utc).strftime("%d.%m.%Y")

    art50 = [s for s in ai_systems if s.get("ai_act_article") == "art50"]
    art4 = [s for s in ai_systems if s.get("ai_act_article") == "art4"]
    annex3 = [s for s in ai_systems if s.get("ai_act_article") == "annex3"]

    def rows(systems: list[dict]) -> str:
        html = ""
        for s in systems:
            details = s.get("details", {})
            source_label = {"questionnaire": "Dotazník", "scanner": "Automatický scan", "wizard": "Wizard", "manual": "Manuální"}.get(s.get("source", ""), s.get("source", ""))
            risk_label = {"minimal": "Minimální", "limited": "Omezené", "high": "Vysoké"}.get(s.get("risk_level", ""), s.get("risk_level", ""))
            risk_color = {"minimal": "#22c55e", "limited": "#eab308", "high": "#ef4444"}.get(s.get("risk_level", ""), "#888")
            html += f"""<tr>
                <td style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb;">{_esc(s.get("provider", "N/A"))}</td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb;">{_esc(details.get("description_cs", s.get("ai_type", "")))}</td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb;"><span style="color: {risk_color}; font-weight: 600;">{risk_label}</span></td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #e5e7eb;">{source_label}</td>
            </tr>"""
        return html

    # Score breakdown
    scan_val = breakdown.get("scan", 0)
    det_val = breakdown.get("detection", 0)
    gov_val = breakdown.get("governance", 0)
    trans_val = breakdown.get("transparency", 0)

    return f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="utf-8">
<style>
    @page {{ size: A4; margin: 2cm; }}
    body {{ font-family: 'Segoe UI', Tahoma, Arial, sans-serif; color: #1e293b; line-height: 1.6; font-size: 11pt; }}
    h1 {{ color: #0f172a; font-size: 22pt; border-bottom: 3px solid #7c3aed; padding-bottom: 8px; }}
    h2 {{ color: #334155; font-size: 14pt; margin-top: 24px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
    thead th {{ background: #f1f5f9; padding: 10px 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #cbd5e1; font-size: 10pt; }}
    .meta {{ color: #64748b; font-size: 9pt; }}
    .score-box {{ display: inline-block; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 20px; margin: 4px 8px 4px 0; text-align: center; }}
    .score-box .val {{ font-size: 20pt; font-weight: 700; }}
    .score-box .label {{ font-size: 8pt; color: #64748b; }}
    .footer {{ margin-top: 40px; padding-top: 16px; border-top: 1px solid #e2e8f0; font-size: 8pt; color: #94a3b8; }}
</style>
</head>
<body>

<h1>Registr AI systémů</h1>
<p class="meta">{_esc(eshop_name)} &bull; Vygenerováno: {now} &bull; AIshield.cz</p>

<h2>Compliance skóre</h2>
<div>
    <div class="score-box"><div class="val" style="color: {"#22c55e" if score >= 80 else "#eab308" if score >= 50 else "#ef4444"}">{score}%</div><div class="label">Celkové skóre</div></div>
    <div class="score-box"><div class="val">{scan_val}/15</div><div class="label">Sken webu</div></div>
    <div class="score-box"><div class="val">{det_val}/25</div><div class="label">Detekce AI</div></div>
    <div class="score-box"><div class="val">{gov_val}/30</div><div class="label">Governance</div></div>
    <div class="score-box"><div class="val">{trans_val}/30</div><div class="label">Transparentnost</div></div>
</div>

<h2>Celkový počet AI systémů: {len(ai_systems)}</h2>
"""  + (f"""
<h2>Article 50 — Povinná transparence ({len(art50)} systémů)</h2>
<p>Tyto AI systémy komunikují přímo se zákazníky. Dle EU AI Act (Nařízení 2024/1689) musíte zákazníky informovat o jejich použití. <strong>Deadline: 2. srpna 2026.</strong></p>
<table>
<thead><tr><th>Poskytovatel</th><th>Účel</th><th>Riziko</th><th>Zdroj</th></tr></thead>
<tbody>{rows(art50)}</tbody>
</table>
""" if art50 else "") + (f"""
<h2>Article 4 — Evidenční povinnost ({len(art4)} systémů)</h2>
<p>Tyto AI systémy podléhají požadavku na AI gramotnost (Article 4). <strong>Platí od 2. února 2025.</strong></p>
<table>
<thead><tr><th>Poskytovatel</th><th>Účel</th><th>Riziko</th><th>Zdroj</th></tr></thead>
<tbody>{rows(art4)}</tbody>
</table>
""" if art4 else "") + (f"""
<h2>Příloha III — Vysoce rizikové AI ({len(annex3)} systémů)</h2>
<p style="color: #ef4444; font-weight: 600;">Vysoce rizikové AI systémy vyžadují rozšířenou dokumentaci a posouzení shody.</p>
<table>
<thead><tr><th>Poskytovatel</th><th>Účel</th><th>Riziko</th><th>Zdroj</th></tr></thead>
<tbody>{rows(annex3)}</tbody>
</table>
""" if annex3 else "") + ("""
<p><em>Nebyly identifikovány žádné AI systémy.</em></p>
""" if not ai_systems else "") + f"""
<div class="footer">
    <p>Tento dokument byl vygenerován automaticky systémem AIshield.cz na základě sebehodnocení provozovatele e-shopu
    a automatického skenu webu. Nepředstavuje právní poradenství.</p>
    <p>Nařízení EU 2024/1689 (AI Act) — Article 4 (AI gramotnost, od 2.2.2025), Article 50 (transparence, od 2.8.2026)</p>
</div>

</body>
</html>"""


def _generate_checklist_html(eshop_name: str, ai_systems: list[dict], questionnaire_data: dict | None) -> str:
    """Generuje HTML pro Compliance Checklist (co udělat před deadline)."""
    now = datetime.now(timezone.utc).strftime("%d.%m.%Y")

    art50 = [s for s in ai_systems if s.get("ai_act_article") == "art50"]
    has_high_risk = any(s.get("risk_level") == "high" for s in ai_systems)

    # Data z dotazníku
    q = questionnaire_data or {}
    has_training = q.get("has_ai_training", "ne") != "ne"
    has_guidelines = q.get("has_ai_guidelines", "ne") != "ne"
    has_register = q.get("has_ai_register", "ne") != "ne"
    has_oversight = q.get("has_oversight_person", "ne") != "ne"
    has_transparency = q.get("has_transparency_page", "ne") != "ne"
    can_override = q.get("can_override_ai", "ne") not in ("ne", "nevim")

    def item(done: bool, text: str, deadline: str = "", priority: str = "medium") -> str:
        icon = "&#10003;" if done else "&#9744;"
        color = "#22c55e" if done else "#ef4444" if priority == "high" else "#eab308"
        dl = f' <span style="color: #94a3b8; font-size: 9pt;">({deadline})</span>' if deadline else ""
        return f'<tr><td style="padding: 6px 10px; border-bottom: 1px solid #f1f5f9; color: {color}; font-size: 14pt; width: 30px; text-align: center;">{icon}</td><td style="padding: 6px 10px; border-bottom: 1px solid #f1f5f9;{"text-decoration: line-through; color: #94a3b8;" if done else ""}">{text}{dl}</td></tr>'

    items = []
    # Article 4 (platí od 2.2.2025)
    items.append(item(has_training, "Proškolit zaměstnance o AI gramotnosti (Article 4)", "Platí od 2.2.2025", "high"))
    items.append(item(has_register, "Vytvořit registr AI systémů používaných ve firmě", "Doporučeno ihned"))
    items.append(item(has_guidelines, "Sepsat interní pravidla pro používání AI", "Doporučeno ihned"))
    items.append(item(has_oversight, "Určit odpovědnou osobu za AI compliance", "Doporučeno ihned"))

    # Article 50 (deadline 2.8.2026)
    if art50:
        items.append(item(has_transparency, f"Informovat zákazníky o {len(art50)} AI systémech na webu (Article 50)", "Deadline: 2.8.2026", "high"))
        items.append(item(False, "Publikovat transparenční stránku /ai-compliance na e-shopu", "Deadline: 2.8.2026", "high"))

    items.append(item(can_override, "Zajistit možnost lidského přepsání AI rozhodnutí", "Doporučeno"))

    if has_high_risk:
        items.append(item(False, "Konzultovat vysoce rizikové AI systémy s právníkem", "Před 2.8.2026", "high"))
        items.append(item(False, "Připravit rozšířenou dokumentaci pro vysoce rizikové AI", "Před 2.8.2026", "high"))

    items_html = "\n".join(items)

    return f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="utf-8">
<style>
    @page {{ size: A4; margin: 2cm; }}
    body {{ font-family: 'Segoe UI', Tahoma, Arial, sans-serif; color: #1e293b; line-height: 1.6; font-size: 11pt; }}
    h1 {{ color: #0f172a; font-size: 22pt; border-bottom: 3px solid #06b6d4; padding-bottom: 8px; }}
    h2 {{ color: #334155; font-size: 14pt; margin-top: 24px; }}
    .meta {{ color: #64748b; font-size: 9pt; }}
    .deadline-box {{ background: #fef2f2; border: 2px solid #fca5a5; border-radius: 8px; padding: 16px; margin: 16px 0; }}
    .deadline-box h3 {{ color: #dc2626; margin: 0 0 4px 0; font-size: 13pt; }}
    .deadline-box p {{ margin: 0; color: #7f1d1d; }}
    .info-box {{ background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 16px; margin: 16px 0; }}
    .footer {{ margin-top: 40px; padding-top: 16px; border-top: 1px solid #e2e8f0; font-size: 8pt; color: #94a3b8; }}
</style>
</head>
<body>

<h1>AI Act Compliance Checklist</h1>
<p class="meta">{_esc(eshop_name)} &bull; Vygenerováno: {now} &bull; AIshield.cz</p>

<div class="deadline-box">
    <h3>Klíčové termíny</h3>
    <p><strong>2. února 2025</strong> — Article 4: Povinnost AI gramotnosti personálu (již platí!)</p>
    <p><strong>2. srpna 2026</strong> — Article 50: Povinnost transparence vůči zákazníkům</p>
</div>

<div class="info-box">
    <p><strong>Identifikováno {len(ai_systems)} AI systémů</strong> na vašem e-shopu
    ({len(art50)} vyžaduje informování zákazníků).</p>
</div>

<h2>Akční plán</h2>
<table style="width: 100%; border-collapse: collapse;">
{items_html}
</table>

<h2>Další doporučené kroky</h2>
<ol>
    <li>Pravidelně (čtvrtletně) aktualizujte registr AI systémů</li>
    <li>Sledujte prováděcí předpisy k AI Act, které upřesní povinnosti</li>
    <li>Zapojte AI compliance do onboarding procesu nových zaměstnanců</li>
    <li>Dokumentujte všechna rozhodnutí o nasazení nových AI nástrojů</li>
</ol>

<div class="footer">
    <p>Tento dokument byl vygenerován automaticky systémem AIshield.cz na základě sebehodnocení provozovatele e-shopu.
    Nepředstavuje právní poradenství. Pro závazné posouzení kontaktujte odborníka na AI regulaci.</p>
    <p>Nařízení EU 2024/1689 (AI Act) — plný text: <em>eur-lex.europa.eu</em></p>
</div>

</body>
</html>"""


def _esc(text: str) -> str:
    """Escapuje HTML speciální znaky."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


async def generate_shoptet_documents(installation_id: str) -> dict:
    """
    Generuje PDF dokumenty pro Shoptet instalaci.
    Vrací {"generated": [...], "error": None}
    """
    sb = get_supabase()
    result = {"generated": [], "error": None}

    try:
        # Načíst instalaci s daty
        inst = sb.table("shoptet_installations").select("*").eq(
            "id", installation_id,
        ).execute()

        if not inst.data:
            result["error"] = "Instalace nenalezena"
            return result

        installation = inst.data[0]
        eshop_name = installation.get("eshop_name") or installation.get("eshop_url") or "E-shop"
        questionnaire_data = installation.get("questionnaire_data")

        # Načíst AI systémy
        systems = sb.table("shoptet_ai_systems").select("*").eq(
            "installation_id", installation_id,
        ).eq("is_active", True).execute()
        ai_systems = systems.data or []

        # Compliance skóre
        score = 0
        breakdown = {}
        if questionnaire_data:
            from backend.shoptet.models import QuestionnaireRequest as QR
            q_data = QR(**questionnaire_data)

            page = sb.table("shoptet_compliance_pages").select("is_published").eq(
                "installation_id", installation_id,
            ).execute()
            page_published = bool(page.data and page.data[0].get("is_published"))

            from backend.shoptet.wizard import calculate_compliance_score
            scan_completed = bool(installation.get("scan_completed_at"))
            score, breakdown = calculate_compliance_score(
                q_data, ai_systems,
                scan_completed=scan_completed,
                compliance_page_published=page_published,
            )

        # Smazat staré dokumenty (idempotence)
        sb.table("shoptet_documents").delete().eq(
            "installation_id", installation_id,
        ).execute()

        # 1. AI Registr PDF
        register_html = _generate_register_html(eshop_name, ai_systems, score, breakdown)
        register_pdf = await _html_to_pdf(register_html)
        if register_pdf:
            path = f"shoptet/{installation_id}/ai_registr.pdf"
            _upload_to_storage(sb, path, register_pdf)
            sb.table("shoptet_documents").insert({
                "installation_id": installation_id,
                "doc_type": "ai_registr",
                "title": "Registr AI systémů",
                "storage_path": path,
                "file_size": len(register_pdf),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
            result["generated"].append("ai_registr")
            logger.info(f"AI Registr vygenerován: {path} ({len(register_pdf)} bytes)")

        # 2. Compliance Checklist PDF
        checklist_html = _generate_checklist_html(eshop_name, ai_systems, questionnaire_data)
        checklist_pdf = await _html_to_pdf(checklist_html)
        if checklist_pdf:
            path = f"shoptet/{installation_id}/compliance_checklist.pdf"
            _upload_to_storage(sb, path, checklist_pdf)
            sb.table("shoptet_documents").insert({
                "installation_id": installation_id,
                "doc_type": "compliance_checklist",
                "title": "AI Act Compliance Checklist",
                "storage_path": path,
                "file_size": len(checklist_pdf),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
            result["generated"].append("compliance_checklist")
            logger.info(f"Checklist vygenerován: {path} ({len(checklist_pdf)} bytes)")

        logger.info(
            f"Dokumenty hotovy: installation={installation_id}, "
            f"count={len(result['generated'])}"
        )

    except Exception as e:
        logger.error(f"Generování dokumentů selhalo: {e}")
        result["error"] = str(e)

    return result


async def _html_to_pdf(html: str) -> bytes | None:
    """Konvertuje HTML na PDF přes WeasyPrint."""
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html).write_pdf()
        return pdf_bytes
    except ImportError:
        logger.error("WeasyPrint není nainstalován")
        return None
    except Exception as e:
        logger.error(f"PDF generování selhalo: {e}")
        return None


def _upload_to_storage(sb, path: str, data: bytes) -> None:
    """Nahraje soubor do Supabase Storage."""
    try:
        # Smazat starý soubor pokud existuje
        try:
            sb.storage.from_("documents").remove([path])
        except Exception:
            pass
        sb.storage.from_("documents").upload(
            path,
            data,
            file_options={"content-type": "application/pdf", "upsert": "true"},
        )
    except Exception as e:
        logger.error(f"Upload do storage selhal: {path}: {e}")
        raise
