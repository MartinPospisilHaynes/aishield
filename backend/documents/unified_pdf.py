"""
AIshield.cz — Unified PDF Generator (v3 — Jinja2 rewrite)
Čistý, profesionální PDF pro tisk a vazbu.

Architektura:
  - Jinja2 šablony (inline) pro čistý HTML
  - Oddělení: CSS | data preprocessor | sekce šablony
  - Žádné "Vyplňte", žádné "None", žádné checkboxy
  - LLM obsah se vkládá do větších slotů
  - Bullet points (•) místo checkboxů (☐)
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from jinja2 import Environment, BaseLoader, select_autoescape

from backend.documents.templates import (
    TEMPLATE_RENDERERS,
    TEMPLATE_NAMES,
    _now_str,
    _days_until_deadline,
    _risk_badge,
)

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════
# RISK MAP — klasifikace AI systémů dle AI Act Annex III
# ══════════════════════════════════════════════════════════════════════

QUESTIONNAIRE_RISK_MAP = {
    "uses_ai_employee_monitoring": "high",
    "uses_ai_recruitment": "high",
    "uses_ai_creditscoring": "high",
    "uses_emotion_recognition": "high",
    "uses_biometric_categorization": "high",
    "uses_ai_insurance": "high",
    "uses_ai_for_children": "high",
    "uses_ai_critical_infra": "high",
    "uses_ai_safety_component": "high",
    "uses_ai_decision": "high",
    "develops_own_ai": "high",
    "modifies_ai_purpose": "high",
    "uses_social_scoring": "high",
    "uses_subliminal_manipulation": "high",
    "uses_realtime_biometric": "high",
    "uses_ai_chatbot": "limited",
    "uses_ai_email_auto": "limited",
    "uses_chatgpt": "limited",
    "uses_copilot": "limited",
    "uses_ai_content": "limited",
    "uses_deepfake": "limited",
    "uses_dynamic_pricing": "limited",
    "uses_ai_accounting": "limited",
    "uses_gpai_api": "limited",
    "uses_ai_translation": "minimal",
    "uses_ai_analytics": "minimal",
    "uses_ai_data_processing": "minimal",
}

# Mapa dodavatelů AI
VENDOR_MAP = {
    "chatgpt": ("OpenAI, Inc.", "USA"),
    "gpt": ("OpenAI, Inc.", "USA"),
    "openai": ("OpenAI, Inc.", "USA"),
    "copilot": ("Microsoft Corp.", "USA"),
    "microsoft": ("Microsoft Corp.", "USA"),
    "gemini": ("Google LLC", "USA"),
    "google": ("Google LLC", "USA"),
    "claude": ("Anthropic PBC", "USA"),
    "anthropic": ("Anthropic PBC", "USA"),
    "midjourney": ("Midjourney, Inc.", "USA"),
    "dall-e": ("OpenAI, Inc.", "USA"),
    "perplexity": ("Perplexity AI, Inc.", "USA"),
    "deepl": ("DeepL SE", "Německo (EU)"),
    "grammarly": ("Grammarly, Inc.", "USA"),
    "jasper": ("Jasper AI, Inc.", "USA"),
    "cursor": ("Anysphere, Inc.", "USA"),
    "github": ("Microsoft Corp.", "USA"),
    "suno": ("Suno, Inc.", "USA"),
    "stable diffusion": ("Stability AI, Ltd.", "UK"),
    "whisper": ("OpenAI, Inc.", "USA"),
}


# ══════════════════════════════════════════════════════════════════════
# DATA PREPROCESSOR — sanitizace dat před renderováním
# ══════════════════════════════════════════════════════════════════════

def _safe(val, fallback="—"):
    """Vrátí hodnotu nebo fallback. Nikdy None/prázdný string."""
    if val is None:
        return fallback
    s = str(val).strip()
    if not s or s.lower() in ("none", "null", "n/a", "undefined"):
        return fallback
    return s


def _resolve_vendor(tool_name: str) -> tuple:
    """Najde dodavatele a zemi pro AI systém."""
    lower = (tool_name or "").lower()
    for key, (vendor, country) in VENDOR_MAP.items():
        if key in lower:
            return vendor, country
    return "—", "—"


def _risk_label(level: str) -> str:
    """Čitelný český label pro úroveň rizika."""
    return {
        "high": "VYSOKÉ RIZIKO",
        "limited": "Omezené riziko",
        "minimal": "Minimální riziko",
    }.get(level, level)


def _risk_level_for_system(sys_dict: dict) -> str:
    """Určí rizikovou úroveň pro AI systém z dotazníku."""
    return QUESTIONNAIRE_RISK_MAP.get(sys_dict.get("key", ""), "minimal")


def _preprocess_data(data: dict) -> dict:
    """
    Připraví data pro šablony. Sanitizuje, doplní fallbacky,
    vyřeší dodavatele, sloučí web + dotazník systémy.
    """
    d = dict(data)  # shallow copy

    # Základní firemní údaje
    d["company"] = _safe(d.get("company_name"), "Firma")
    d["ico"] = _safe(d.get("q_company_ico"))
    d["address"] = _safe(d.get("q_company_address"))
    d["industry"] = _safe(d.get("q_company_industry"))
    d["company_size"] = _safe(d.get("q_company_size"))
    d["revenue"] = _safe(d.get("q_company_annual_revenue"))
    d["contact_email"] = _safe(d.get("contact_email", d.get("q_company_contact_email")))
    d["phone"] = _safe(d.get("q_company_phone", d.get("phone", "")))
    d["website"] = _safe(d.get("q_company_website", d.get("website", d.get("url", ""))))

    # Rizikový profil
    d["overall_risk"] = d.get("overall_risk", "minimal")
    d["risk"] = d.get("risk_breakdown", {"high": 0, "limited": 0, "minimal": 0})
    d["overall_risk_label"] = _risk_label(d["overall_risk"])

    # Datum
    d["now"] = _now_str()
    d["days_left"] = _days_until_deadline()
    d["year"] = datetime.now().year

    # Odpovědná osoba
    ov = d.get("oversight_person", {})
    if not isinstance(ov, dict):
        ov = {}
    d["oversight"] = {
        "name": _safe(ov.get("name")),
        "role": _safe(ov.get("role")),
        "email": _safe(ov.get("email")),
        "phone": _safe(ov.get("phone")),
        "has_person": ov.get("has_person", False),
    }

    # ── Sloučený seznam AI systémů (web + dotazník) ──
    all_systems = []

    # Web scan findings
    for f in d.get("findings", []):
        name = _safe(f.get("name"), "AI systém")
        rl = f.get("risk_level", "minimal")
        vendor, country = _resolve_vendor(name)
        all_systems.append({
            "name": name,
            "category": _safe(f.get("category")),
            "risk_level": rl,
            "risk_label": _risk_label(rl),
            "article": _safe(f.get("ai_act_article")),
            "action": _safe(f.get("action_required")),
            "source": "Web sken",
            "vendor": vendor,
            "country": country,
        })

    # Dotazník systémy
    for s in d.get("ai_systems_declared", []):
        name = _safe(s.get("tool_name"), "AI systém")
        rl = _risk_level_for_system(s)
        vendor, country = _resolve_vendor(name)
        key_label = s.get("key", "").replace("uses_", "").replace("_", " ").title()
        all_systems.append({
            "name": name,
            "category": key_label,
            "risk_level": rl,
            "risk_label": _risk_label(rl),
            "article": "—",
            "action": "—",
            "source": "Dotazník",
            "vendor": vendor,
            "country": country,
        })

    d["all_systems"] = all_systems
    d["total_systems"] = len(all_systems)
    d["system_names"] = [s["name"] for s in all_systems if s["name"] != "—"]

    # Skupiny systémů podle rizika
    d["high_systems"] = [s for s in all_systems if s["risk_level"] == "high"]
    d["limited_systems"] = [s for s in all_systems if s["risk_level"] == "limited"]
    d["minimal_systems"] = [s for s in all_systems if s["risk_level"] == "minimal"]

    # Dodavatelé (deduplikovaní)
    vendors_seen = set()
    d["vendors"] = []
    for s in all_systems:
        v = s["vendor"]
        if v != "—" and v not in vendors_seen:
            vendors_seen.add(v)
            d["vendors"].append({"name": v, "country": s["country"], "systems": []})
    # Přiřadit systémy k dodavatelům
    for v in d["vendors"]:
        v["systems"] = [s["name"] for s in all_systems if s["vendor"] == v["name"]]

    # LLM content
    d["llm"] = d.get("llm_content", {})

    # Recommendations
    recs = []
    for r in d.get("recommendations", []):
        recs.append({
            "tool_name": _safe(r.get("tool_name"), "AI systém"),
            "risk_level": r.get("risk_level", "minimal"),
            "recommendation": _safe(r.get("recommendation")),
        })
    d["recs"] = recs

    # Eligible / skipped docs
    d["eligible_docs"] = d.get("eligible_documents", {})
    d["skipped_docs"] = d.get("skipped_documents", [])

    # Training
    d["training"] = d.get("training", {})

    # Data protection
    d["data_prot"] = d.get("data_protection", {})

    # Incident
    d["incident"] = d.get("incident", {})

    # Human oversight
    d["human_oversight"] = d.get("human_oversight", {})

    # Prohibited
    d["prohibited"] = d.get("prohibited_systems", {})

    return d


# ══════════════════════════════════════════════════════════════════════
# CSS — čistý, profesionální, tiskový design
# ══════════════════════════════════════════════════════════════════════

UNIFIED_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    @page {
        size: A4;
        margin: 18mm 18mm 20mm 18mm;

        @top-left {
            content: "AIshield.cz";
            font-size: 8px; font-weight: 700; color: #333;
            font-family: 'Inter', sans-serif;
            letter-spacing: 0.05em;
            border-bottom: 0.5pt solid #ccc;
            padding-bottom: 4mm;
        }
        @top-right {
            content: "AI Act Compliance Kit";
            font-size: 8px; color: #888;
            font-family: 'Inter', sans-serif;
            border-bottom: 0.5pt solid #ccc;
            padding-bottom: 4mm;
        }
        @bottom-left {
            content: "Vypracováno odborným týmem s využitím AI nástrojů | aishield.cz";
            font-size: 7px; color: #aaa;
            font-family: 'Inter', sans-serif;
            border-top: 0.5pt solid #ccc;
            padding-top: 3mm;
        }
        @bottom-center {
            content: "Strana " counter(page) " z " counter(pages);
            font-size: 8px; color: #666;
            font-family: 'Inter', sans-serif;
            border-top: 0.5pt solid #ccc;
            padding-top: 3mm;
        }
        @bottom-right {
            content: "© AIshield.cz";
            font-size: 7px; color: #aaa;
            font-family: 'Inter', sans-serif;
            border-top: 0.5pt solid #ccc;
            padding-top: 3mm;
        }
    }

    @page :first {
        @top-left { content: none; }
        @top-right { content: none; }
        @bottom-left { content: none; }
        @bottom-center { content: none; }
        @bottom-right { content: none; }
    }

    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
        font-family: 'Inter', -apple-system, sans-serif;
        background: #fff;
        color: #111;
        line-height: 1.45;
        font-size: 10.5px;
    }

    /* ── Titulní strana ── */
    .title-page {
        page-break-after: always;
        display: flex; flex-direction: column;
        justify-content: center; align-items: center;
        min-height: 100vh; text-align: center;
        padding: 60px 40px;
    }
    .title-page .brand { font-size: 36px; font-weight: 800; letter-spacing: -0.04em; margin-bottom: 8px; color: #111; }
    .title-page h1 { font-size: 26px; font-weight: 700; color: #111; margin: 24px 0 8px; }
    .title-page .company-name { font-size: 22px; font-weight: 600; color: #111; margin-bottom: 6px; }
    .title-page .subtitle { font-size: 13px; color: #444; max-width: 440px; }
    .title-page .meta { margin-top: 40px; font-size: 11px; color: #666; line-height: 1.8; }
    .title-accent { width: 80px; height: 2px; background: #111; margin: 20px auto; }

    /* ── Obsah (TOC) ── */
    .toc-page { page-break-after: always; padding: 40px 0; }
    .toc-page h2 { font-size: 20px; font-weight: 700; color: #111; margin-bottom: 24px; padding-bottom: 10px; border-bottom: 2px solid #111; }
    .toc-item { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px dotted #ccc; font-size: 12px; }
    .toc-number { font-weight: 600; color: #111; min-width: 30px; }
    .toc-title { font-weight: 500; color: #111; flex: 1; }
    .toc-tier { font-size: 10px; font-weight: 700; color: #333; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 18px; margin-bottom: 4px; border-bottom: 1px solid #eee; padding-bottom: 4px; }

    /* ── Sekce dokumentu ── */
    .doc-section { page-break-before: always; padding-top: 8px; }
    .section-header { border-bottom: 2px solid #111; padding: 0 0 6px; margin-bottom: 14px; }
    .section-header h2 { font-size: 16px; font-weight: 700; color: #111; margin-bottom: 2px; }
    .section-header .section-number { font-size: 11px; font-weight: 700; color: #555; text-transform: uppercase; letter-spacing: 0.05em; }
    .section-header .section-sub { font-size: 11px; color: #666; }

    /* ── Nadpisy uvnitř sekcí ── */
    h2 { font-size: 13px; font-weight: 700; color: #111; margin: 16px 0 6px; }
    h3 { font-size: 11.5px; font-weight: 600; color: #222; margin: 12px 0 4px; }
    p { margin-bottom: 5px; color: #111; font-size: 10.5px; }

    /* ── Tabulky — čisté, bez těžkých rámečků ── */
    table { width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 10.5px; }
    th { text-align: left; padding: 5px 8px; background: #f5f5f5; border-bottom: 2px solid #ccc; font-weight: 600; font-size: 9.5px; color: #333; text-transform: uppercase; letter-spacing: 0.04em; }
    td { padding: 5px 8px; border-bottom: 1px solid #eee; color: #111; }
    tr:last-child td { border-bottom: none; }

    /* ── Badges — konzervativní ── */
    .badge { display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 3px; font-size: 10px; font-weight: 600; border: 1px solid #ccc; background: #fff; color: #111; }
    .badge-high { border-color: #111; font-weight: 800; }
    .badge-limited { border-color: #888; }
    .badge-minimal { border-color: #ccc; }
    .badge-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
    .badge-dot-high { background: #111; }
    .badge-dot-limited { background: #888; }
    .badge-dot-minimal { background: #ccc; }

    /* ── Metriky ── */
    .metric-grid { display: flex; gap: 12px; margin: 12px 0; }
    .metric { flex: 1; text-align: center; padding: 10px; border-bottom: 2px solid #111; }
    .metric-value { font-size: 26px; font-weight: 800; line-height: 1; color: #111; }
    .metric-label { font-size: 10px; color: #666; margin-top: 4px; }

    /* ── Highlight box ── */
    .highlight { padding: 10px 14px; border-left: 3px solid #111; background: #f9f9f9; margin: 10px 0; font-size: 10.5px; color: #111; }

    /* ── Bullet point list (nahrazuje checkboxy) ── */
    .bp-list { margin: 6px 0; padding: 0; list-style: none; }
    .bp-list li { padding: 4px 0 4px 18px; position: relative; font-size: 10.5px; color: #111; border-bottom: 1px solid #f5f5f5; }
    .bp-list li:last-child { border-bottom: none; }
    .bp-list li::before { content: "•"; position: absolute; left: 4px; font-weight: 800; color: #111; }

    /* ── Subsection spacing ── */
    .subsection { margin: 14px 0; }
    .subsection h3 { margin-bottom: 6px; }

    ul, ol { margin: 4px 0; padding-left: 18px; }
    li { margin-bottom: 3px; font-size: 10.5px; color: #111; }

    /* ── VOP ── */
    .vop-section { page-break-before: always; }
    .vop-section h2 { font-size: 16px; color: #111; border-bottom: 2px solid #111; padding-bottom: 8px; margin-bottom: 16px; }
    .vop-section h3 { font-size: 12px; color: #222; margin-top: 14px; }
    .vop-section p { font-size: 10px; color: #333; line-height: 1.6; }

    /* ── Doc footer ── */
    .doc-footer { text-align: center; padding: 16px 0; font-size: 9px; color: #888; border-top: 1px solid #eee; margin-top: 24px; }

    /* ── Semafor ── */
    .semaphore { display: flex; align-items: center; gap: 14px; padding: 14px; border: 2px solid #111; margin: 12px 0; }
    .semaphore-icon { font-size: 36px; line-height: 1; }
    .semaphore-text p { margin-bottom: 2px; }

    /* ── Signature block ── */
    .sig-block { display: flex; gap: 20px; margin-top: 16px; }
    .sig-cell { flex: 1; border-top: 1px solid #ccc; padding-top: 8px; }
    .sig-cell .label { font-size: 9px; color: #888; margin-bottom: 24px; }
    .sig-cell .line { font-size: 10px; color: #111; }
</style>
"""


# ══════════════════════════════════════════════════════════════════════
# JINJA2 ENVIRONMENT
# ══════════════════════════════════════════════════════════════════════

_jinja_env = Environment(
    loader=BaseLoader(),
    autoescape=select_autoescape([]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def _badge_html(level: str) -> str:
    css = level if level in ("high", "limited", "minimal") else "minimal"
    labels = {"high": "VYSOKÉ RIZIKO", "limited": "Omezené riziko", "minimal": "Minimální riziko"}
    return (f'<span class="badge badge-{css}">'
            f'<span class="badge-dot badge-dot-{css}"></span>'
            f'{labels.get(level, level)}</span>')

_jinja_env.globals["badge"] = _badge_html
_jinja_env.globals["safe"] = _safe


# ══════════════════════════════════════════════════════════════════════
# JINJA2 ŠABLONY — inline definované pro jednoduchost
# ══════════════════════════════════════════════════════════════════════

# ── TITULNÍ STRANA ──
TPL_TITLE = _jinja_env.from_string("""
<div class="title-page">
    <div class="brand">
        <span style="color:#111">AI</span><span style="color:#333">shield</span><span style="color:#888;font-size:16px">.cz</span>
    </div>
    <div class="title-accent"></div>
    <h1>AI Act Compliance Kit</h1>
    <div class="company-name">{{ company }}</div>
    <p class="subtitle">
        Kompletní dokumentace pro soulad s Nařízením (EU) 2024/1689 —
        Akt o umělé inteligenci. Do plné účinnosti zbývá {{ days_left }} dní.
    </p>
    <div class="title-accent"></div>
    <div class="meta">
        Vygenerováno: {{ now }}<br>
        {% if ico != "—" %}IČO: {{ ico }}<br>{% endif %}
        {% if address != "—" %}Sídlo: {{ address }}<br>{% endif %}
        {% if industry != "—" %}Odvětví: {{ industry }}<br>{% endif %}
        {% if contact_email != "—" %}Kontakt: {{ contact_email }}<br>{% endif %}
        Celkové riziko: {{ overall_risk_label }}
        {% if phone != "—" %}<br>Telefon: {{ phone }}{% endif %}
        {% if website != "—" %}<br>Web: {{ website }}{% endif %}
    </div>
    <div style="margin-top:50px; padding-top:20px; border-top:1px solid #ddd; font-size:9px; color:#888; line-height:1.8;">
        <strong style="color:#333">Vypracoval:</strong> AIshield.cz — AI Act compliance pro české firmy<br>
        Bc. Martin Haynes | IČO: 17889251<br>
        info@aishield.cz | +420 732 716 141 | aishield.cz<br>
        {% if oversight.has_person and oversight.name != "—" %}
        Zodpovědná osoba klienta: {{ oversight.name }}{% if oversight.role != "—" %} ({{ oversight.role }}){% endif %}
        {% endif %}
    </div>
</div>
""")

# ── OBSAH ──
TPL_TOC = _jinja_env.from_string("""
<div class="toc-page">
    <h2>Obsah</h2>
    {% set ns = namespace(chapter=0, current_tier="") %}
    {% set tier_map = {
        "compliance_report": "Základní dokumenty",
        "action_plan": "Základní dokumenty",
        "ai_register": "Základní dokumenty",
        "training_outline": "Základní dokumenty",
        "chatbot_notices": "Podmíněné dokumenty",
        "ai_policy": "Podmíněné dokumenty",
        "incident_response_plan": "Dokumenty dle rizikového profilu",
        "dpia_template": "Dokumenty dle rizikového profilu",
        "vendor_checklist": "Dokumenty dle rizikového profilu",
        "monitoring_plan": "Dokumenty dle rizikového profilu",
        "transparency_human_oversight": "Dokumenty dle rizikového profilu",
    } %}
    {% for key in pdf_keys %}
        {% set tier = tier_map.get(key, "") %}
        {% if tier and tier != ns.current_tier %}
            {% set ns.current_tier = tier %}
            <div class="toc-tier">{{ tier }}</div>
        {% endif %}
        {% set ns.chapter = ns.chapter + 1 %}
        <div class="toc-item">
            <span class="toc-number">{{ ns.chapter }}.</span>
            <span class="toc-title">{{ section_names.get(key, key) }}</span>
        </div>
    {% endfor %}
    <div class="toc-tier">Právní ustanovení</div>
    {% set ns.chapter = ns.chapter + 1 %}
    <div class="toc-item">
        <span class="toc-number">{{ ns.chapter }}.</span>
        <span class="toc-title">Všeobecné obchodní podmínky (VOP)</span>
    </div>
    <p style="margin-top:20px;font-size:10px;color:#666">
        Tento dokument byl vygenerován odborným týmem AIshield.cz s využitím pokročilých AI nástrojů
        na základě automatického skenu webu, hloubkové analýzy a odpovědí v dotazníku.
        Obsah je přizpůsoben rizikovému profilu vaší firmy.
    </p>
</div>
""")

# ── COMPLIANCE REPORT ──
TPL_COMPLIANCE_REPORT = _jinja_env.from_string("""
<div class="doc-section" id="section-compliance_report">
    <div class="section-header">
        <div class="section-number">Kapitola {{ chapter }}</div>
        <h2>AI Act Compliance Report</h2>
        <div class="section-sub">Komplexní analýza souladu s Nařízením EU 2024/1689</div>
    </div>

    <table>
        <tr><td style="width:160px;color:#555"><strong>Firma</strong></td><td><strong>{{ company }}</strong></td></tr>
        {% if ico != "—" %}<tr><td style="color:#555">IČO</td><td>{{ ico }}</td></tr>{% endif %}
        {% if address != "—" %}<tr><td style="color:#555">Sídlo</td><td>{{ address }}</td></tr>{% endif %}
        {% if industry != "—" %}<tr><td style="color:#555">Odvětví</td><td>{{ industry }}</td></tr>{% endif %}
        {% if company_size != "—" %}<tr><td style="color:#555">Velikost</td><td>{{ company_size }}</td></tr>{% endif %}
        {% if website != "—" %}<tr><td style="color:#555">Web</td><td>{{ website }}</td></tr>{% endif %}
        <tr><td style="color:#555">Celkové riziko</td><td>{{ badge(overall_risk) }}</td></tr>
    </table>

    {% set sem = {"high": ("🔴", "Vysoké riziko — vyžadována okamžitá akce"),
                  "limited": ("🟡", "Omezené riziko — splnit transparenční povinnosti"),
                  "minimal": ("🟢", "Minimální riziko — dobrovolné best practices")} %}
    {% set icon, text = sem.get(overall_risk, sem["minimal"]) %}
    <div class="semaphore">
        <div class="semaphore-icon">{{ icon }}</div>
        <div class="semaphore-text">
            <p style="font-weight:700;font-size:14px">{{ text }}</p>
            <p style="font-size:11px;color:#555">
                Společnost {{ company }} vystupuje v roli <strong>nasazovatele (deployer)</strong>
                AI systémů dle čl. 3 odst. 4 Nařízení (EU) 2024/1689.
            </p>
        </div>
    </div>

    <div class="metric-grid">
        <div class="metric"><div class="metric-value">{{ total_systems }}</div><div class="metric-label">AI systémů celkem</div></div>
        <div class="metric"><div class="metric-value">{{ risk.get("high", 0) }}</div><div class="metric-label">Vysoké riziko</div></div>
        <div class="metric"><div class="metric-value">{{ risk.get("limited", 0) }}</div><div class="metric-label">Omezené riziko</div></div>
        <div class="metric"><div class="metric-value">{{ risk.get("minimal", 0) }}</div><div class="metric-label">Minimální riziko</div></div>
    </div>

    <div class="highlight">
        <strong>AI Act — plná účinnost:</strong> 2. srpna 2026 — zbývá {{ days_left }} dní.<br>
        Nesplnění: až <strong>35 mil. EUR</strong> / <strong>7 % obratu</strong> (zakázané praktiky, čl. 99).
        Vysoké riziko: až 15 mil. EUR / 3 %. Transparentnost: až 7,5 mil. EUR / 1,5 %.
    </div>

    {% if llm.get("executive_summary") %}
    <h2>Manažerské shrnutí</h2>
    {{ llm["executive_summary"] }}
    {% endif %}

    {% if all_systems %}
    <h2>Nalezené AI systémy</h2>
    <table>
        <thead><tr><th>Systém</th><th>Kategorie</th><th>Riziko</th><th>Zdroj</th><th>Požadovaná akce</th></tr></thead>
        <tbody>
        {% for s in all_systems %}
            <tr>
                <td style="font-weight:600">{{ s.name }}</td>
                <td>{{ s.category }}</td>
                <td>{{ badge(s.risk_level) }}</td>
                <td>{{ s.source }}</td>
                <td style="font-size:10px">{{ s.action }}</td>
            </tr>
        {% endfor %}
        </tbody>
    </table>
    {% endif %}

    {% if llm.get("risk_analysis") %}
    <h2>Detailní analýza rizik</h2>
    {{ llm["risk_analysis"] }}
    {% endif %}

    {% if recs %}
    <h2>Doporučení ke compliance</h2>
    {% for r in recs %}
    <div style="border-left:2px solid #111;padding-left:12px;margin-bottom:10px">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
            {{ badge(r.risk_level) }}
            <strong style="font-size:11px">{{ r.tool_name }}</strong>
        </div>
        <p style="font-size:11px;color:#444">{{ r.recommendation }}</p>
    </div>
    {% endfor %}
    {% endif %}

    <h2>Právní rámec — klíčové články AI Act</h2>
    <table>
        <thead><tr><th>Článek</th><th>Povinnost</th><th>Relevance pro {{ company }}</th></tr></thead>
        <tbody>
            <tr><td><strong>čl. 4</strong></td><td>AI gramotnost — povinné školení</td><td>{{ "✓ Školení probíhá" if training.get("has_training") else "⚠ Nutno zajistit" }}</td></tr>
            <tr><td><strong>čl. 5</strong></td><td>Zakázané praktiky</td><td>{{ "⚠ Deklarováno rizikové užití" if prohibited.get("social_scoring") or prohibited.get("subliminal_manipulation") else "✓ Žádná zakázaná praktika" }}</td></tr>
            <tr><td><strong>čl. 6–7</strong></td><td>Klasifikace vysokého rizika</td><td>{{ "⚠ " ~ high_systems|length ~ " vysoce rizikových" if high_systems else "✓ Žádný vysoce rizikový systém" }}</td></tr>
            <tr><td><strong>čl. 50</strong></td><td>Transparenční povinnosti</td><td>{{ "⚠ Nutné — AI detekován" if limited_systems else "✓ Splnit preventivně" }}</td></tr>
            <tr><td><strong>čl. 73</strong></td><td>Hlášení závažných incidentů</td><td>{{ "⚠ Nutný incident plán" if high_systems or data_prot.get("processes_personal_data") else "Doporučeno" }}</td></tr>
        </tbody>
    </table>

    {% if eligible_docs or skipped_docs %}
    <h2>Dokumenty v tomto Compliance Kitu</h2>
    <table>
        <thead><tr><th>Dokument</th><th>Důvod</th></tr></thead>
        <tbody>
        {% for tkey, reason in eligible_docs.items() %}
            <tr><td><strong>✓</strong> {{ section_names.get(tkey, tkey) }}</td><td style="font-size:10px">{{ reason }}</td></tr>
        {% endfor %}
            <tr><td><strong>✓</strong> Školení AI Literacy — Prezentace (PPTX)</td><td style="font-size:10px">Povinné školení dle čl. 4 AI Act</td></tr>
        {% if skipped_docs %}
        </tbody>
    </table>
    <h3>Přeskočené dokumenty</h3>
    <p style="color:#555;font-size:11px">Pro váš rizikový profil nejsou relevantní:</p>
    <table>
        <thead><tr><th>Dokument</th><th>Důvod</th></tr></thead>
        <tbody>
        {% for sk in skipped_docs %}
            <tr><td style="color:#888">— {{ sk.name }}</td><td style="color:#888;font-size:10px">{{ sk.reason }}</td></tr>
        {% endfor %}
        {% endif %}
        </tbody>
    </table>
    {% endif %}
</div>
""")

# ── AKČNÍ PLÁN ──
TPL_ACTION_PLAN = _jinja_env.from_string("""
<div class="doc-section" id="section-action_plan">
    <div class="section-header">
        <div class="section-number">Kapitola {{ chapter }}</div>
        <h2>Akční plán</h2>
        <div class="section-sub">Konkrétní kroky ke splnění EU AI Act — plná účinnost 2. 8. 2026</div>
    </div>

    <table>
        <tr><td style="width:180px;color:#555"><strong>Firma</strong></td><td>{{ company }}</td></tr>
        <tr><td style="color:#555">Plná účinnost AI Act</td><td><strong>2. srpna 2026</strong> (zbývá {{ days_left }} dní)</td></tr>
    </table>

    {% if llm.get("compliance_roadmap") %}
    <h2>Harmonogram implementace</h2>
    {{ llm["compliance_roadmap"] }}
    {% endif %}

    <h2>Kroky ke compliance</h2>

    <div class="subsection">
    <h3>🔴 Vysoká priorita — vysoce rizikové systémy</h3>
    {% if high_systems %}
    <ul class="bp-list">
        <li>Provést posouzení shody pro vysoce rizikové systémy (čl. 43)</li>
        <li>Zavést systém řízení rizik dle čl. 9 AI Act</li>
        <li>Zajistit lidský dohled dle čl. 14 AI Act</li>
        <li>Registrovat vysoce rizikové systémy v EU databázi (čl. 49)</li>
        <li>Dokumentovat kvalitu dat dle čl. 10 — data governance</li>
        <li>Zajistit technickou dokumentaci dle přílohy IV</li>
    </ul>
    {% else %}
    <p style="color:#888">Žádné vysoce rizikové systémy nebyly identifikovány.</p>
    {% endif %}
    </div>

    <div class="subsection">
    <h3>🟡 Střední priorita — transparenční povinnosti</h3>
    {% if limited_systems %}
    <ul class="bp-list">
        <li>Nasadit transparenční oznámení na web (čl. 50) — texty jsou součástí tohoto Compliance Kitu</li>
        <li>Nasadit transparenční stránku /ai-transparence — HTML kód je součástí Compliance Kitu</li>
        <li>Označit AI-generovaný obsah dle čl. 50 odst. 4</li>
        {% for s in limited_systems %}
        <li>{{ s.name }}: zajistit informování uživatelů o interakci s AI</li>
        {% endfor %}
    </ul>
    {% else %}
    <p style="color:#888">Žádné systémy s omezeným rizikem nebyly identifikovány.</p>
    {% endif %}
    </div>

    <div class="subsection">
    <h3>🟢 Obecné kroky — organizační opatření</h3>
    <ul class="bp-list">
        <li>Jmenovat odpovědnou osobu za AI compliance (čl. 14 — lidský dohled)</li>
        <li>Proškolit zaměstnance — využijte školící prezentaci z Compliance Kitu (čl. 4 AI Act)</li>
        <li>Zavést proces pro zavedení nového AI nástroje (schvalovací workflow)</li>
        <li>Naplánovat pravidelný re-sken webu (měsíční monitoring)</li>
        <li>Zkontrolovat smlouvy s dodavateli AI — využijte dodavatelský checklist z Compliance Kitu</li>
        <li>Nastavit logování AI výstupů s retencí min. 6 měsíců (čl. 12)</li>
    </ul>
    </div>

    <div class="highlight">
        <strong>Tip:</strong> Při auditu tento dokument poslouží jako důkaz vaší snahy
        o compliance (<em>documented effort</em>). Uchovávejte minimálně 5 let.
    </div>
</div>
""")

# ── REGISTR AI SYSTÉMŮ ──
TPL_AI_REGISTER = _jinja_env.from_string("""
<div class="doc-section" id="section-ai_register">
    <div class="section-header">
        <div class="section-number">Kapitola {{ chapter }}</div>
        <h2>Registr AI systémů</h2>
        <div class="section-sub">Interní evidence dle čl. 49 a přílohy VIII Nařízení (EU) 2024/1689</div>
    </div>

    <table>
        <tr><td style="width:180px;color:#555"><strong>Firma</strong></td><td>{{ company }}</td></tr>
        {% if ico != "—" %}<tr><td style="color:#555">IČO</td><td>{{ ico }}</td></tr>{% endif %}
        <tr><td style="color:#555">Poslední aktualizace</td><td>{{ now }}</td></tr>
    </table>

    <div class="highlight">
        <strong>Příloha VIII AI Act</strong> — Pro vysoce rizikové systémy musí registr obsahovat:
        jméno poskytovatele, popis zamýšleného účelu, stav systému, datum a důvod stažení,
        členské státy použití a dotčené osoby.
    </div>

    {% if llm.get("ai_register_intro") %}
    <h2>Přehled AI krajiny firmy</h2>
    {{ llm["ai_register_intro"] }}
    {% endif %}

    {% if all_systems %}
    <h2>Souhrnný přehled AI systémů</h2>
    <table>
        <thead><tr><th>#</th><th>Systém</th><th>Kategorie</th><th>Riziko</th><th>Dodavatel</th><th>Zdroj</th></tr></thead>
        <tbody>
        {% for s in all_systems %}
            <tr>
                <td>{{ loop.index }}</td>
                <td style="font-weight:600">{{ s.name }}</td>
                <td>{{ s.category }}</td>
                <td>{{ badge(s.risk_level) }}</td>
                <td>{{ s.vendor }}</td>
                <td>{{ s.source }}</td>
            </tr>
        {% endfor %}
        </tbody>
    </table>

    <h2>Detailní karty AI systémů</h2>
    {% for s in all_systems %}
    <div class="subsection">
        <h3>Systém č. {{ loop.index }}: {{ s.name }}</h3>
        <table>
            <tr><td style="width:200px;color:#555">Název systému</td><td><strong>{{ s.name }}</strong></td></tr>
            <tr><td style="color:#555">Kategorie</td><td>{{ s.category }}</td></tr>
            <tr><td style="color:#555">Riziková kategorie</td><td>{{ badge(s.risk_level) }}</td></tr>
            {% if s.article != "—" %}<tr><td style="color:#555">Článek AI Act</td><td>{{ s.article }}</td></tr>{% endif %}
            <tr><td style="color:#555">Zdroj detekce</td><td>{{ s.source }}</td></tr>
            <tr><td style="color:#555">Dodavatel</td><td>{{ s.vendor }}</td></tr>
            <tr><td style="color:#555">Země dodavatele</td><td>{{ s.country }}</td></tr>
        </table>
    </div>
    {% endfor %}
    {% else %}
    <p style="color:#888">Žádné AI systémy nebyly identifikovány. Registr bude aktualizován při zavedení AI.</p>
    {% endif %}

    {% if oversight.has_person %}
    <h2>Odpovědná osoba za registr</h2>
    <table>
        <tr><td style="width:200px;color:#555">Jméno</td><td>{{ oversight.name }}</td></tr>
        {% if oversight.role != "—" %}<tr><td style="color:#555">Funkce</td><td>{{ oversight.role }}</td></tr>{% endif %}
        {% if oversight.email != "—" %}<tr><td style="color:#555">Email</td><td>{{ oversight.email }}</td></tr>{% endif %}
        {% if oversight.phone != "—" %}<tr><td style="color:#555">Telefon</td><td>{{ oversight.phone }}</td></tr>{% endif %}
    </table>
    {% endif %}

    <h2>Historie změn registru</h2>
    <table>
        <thead><tr><th>Datum</th><th>Změna</th><th>Provedl</th></tr></thead>
        <tbody>
            <tr><td>{{ now }}</td><td>Vytvoření registru</td><td>AIshield.cz</td></tr>
        </tbody>
    </table>
</div>
""")

# ── ŠKOLENÍ ──
TPL_TRAINING = _jinja_env.from_string("""
<div class="doc-section" id="section-training_outline">
    <div class="section-header">
        <div class="section-number">Kapitola {{ chapter }}</div>
        <h2>Školení AI Literacy</h2>
        <div class="section-sub">Osnova povinného školení dle čl. 4 Nařízení (EU) 2024/1689</div>
    </div>

    <table>
        <tr><td style="width:160px;color:#555">Rozsah</td><td>3–4 hodiny</td></tr>
        <tr><td style="color:#555">Cílová skupina</td><td>Všichni zaměstnanci {{ company }}</td></tr>
        <tr><td style="color:#555">Frekvence</td><td>Při nástupu + 1× ročně</td></tr>
        <tr><td style="color:#555">Materiály</td><td><strong>PowerPointová prezentace je součástí Compliance Kitu</strong></td></tr>
    </table>

    <div class="highlight">
        <strong>čl. 4 AI Act:</strong> „Poskytovatelé a nasazovatelé přijímají opatření k zajištění
        dostatečné úrovně AI gramotnosti svého personálu…" — povinné od 2. 2. 2025.
    </div>

    {% set modules = [
        ("Modul 1 — Co je umělá inteligence (30 min)", [
            "Definice AI dle čl. 3 odst. 1 AI Act",
            "Typy AI: generativní AI (LLM), prediktivní modely, expertní systémy",
            "GPAI — modely obecného určení (čl. 51–56)",
            "AI vs. automatizace — ne každá automatizace je AI"
        ]),
        ("Modul 2 — EU AI Act v kostce (45 min)", [
            "4 kategorie rizik: nepřijatelné → vysoké → omezené → minimální",
            "Zakázané praktiky (čl. 5): sociální scoring, podprahová manipulace",
            "Povinnosti pro nasazovatele (čl. 26) — většina českých firem",
            "Pokuty — až 35 mil. EUR / 7 % obratu (čl. 99)"
        ]),
        ("Modul 3 — AI v naší firmě (30 min)", [
            "Přehled AI systémů firmy " ~ company ~ " z registru",
            "Povolené vs. zakázané použití (interní AI politika)",
            "Pravidla pro vkládání dat do AI — co ANO, co NIKDY",
            "Proces zavedení nového AI nástroje"
        ]),
        ("Modul 4 — Bezpečné používání AI (30 min)", [
            "Správné formulování promptů pro ChatGPT / Claude / Gemini",
            "Co do AI NIKDY nevkládat: osobní údaje, hesla, smlouvy",
            "Ověřování výstupů — halucinace, neaktuální informace",
            "Hlášení incidentů — postup a kontakty"
        ]),
        ("Modul 5 — Automation bias a kritické myšlení (30 min)", [
            "Automation bias — tendence nekriticky přijímat výstupy AI",
            "Techniky kritického myšlení: vždy ověřit klíčová fakta",
            "Nikdy nepoužívat AI výstup jako jediný zdroj pro důležitá rozhodnutí",
            "Odpovědnost: za rozhodnutí odpovídá ČLOVĚK, ne AI (čl. 14)"
        ]),
        ("Modul 6 — Evidence a prezenční listina (15 min)", [
            "Prezenční listina podepsaná účastníky",
            "Opakovat 1× ročně + při zavedení nového AI systému",
            "Uchovávat evidenci min. 5 let pro účely auditu"
        ])
    ] %}

    {% for title, items in modules %}
    <div class="subsection">
        <h3>{{ title }}</h3>
        <ul class="bp-list">
        {% for item in items %}
            <li>{{ item }}</li>
        {% endfor %}
        </ul>
    </div>
    {% endfor %}

    {% if llm.get("training_recommendations") %}
    <h2>Specifická doporučení pro školení</h2>
    {{ llm["training_recommendations"] }}
    {% endif %}

    <h2>Prezenční listina</h2>
    <p style="font-size:10px;color:#555">Uchovávejte podepsanou prezenční listinu min. 5 let pro účely auditu.</p>
    <table>
        <thead><tr><th>Č.</th><th>Jméno</th><th>Pozice</th><th>Datum</th><th>Podpis</th></tr></thead>
        <tbody>
        {% for i in range(1, 8) %}
            <tr><td>{{ i }}</td><td>&nbsp;</td><td></td><td></td><td></td></tr>
        {% endfor %}
        </tbody>
    </table>
</div>
""")

# ── AI OZNÁMENÍ ──
TPL_CHATBOT_NOTICES = _jinja_env.from_string("""
<div class="doc-section" id="section-chatbot_notices">
    <div class="section-header">
        <div class="section-number">Kapitola {{ chapter }}</div>
        <h2>Texty AI oznámení</h2>
        <div class="section-sub">Připravené oznámení dle čl. 50 Nařízení (EU) 2024/1689</div>
    </div>

    <div class="highlight">
        <strong>čl. 50 AI Act — Povinnost informovat:</strong>
        Provozovatelé AI systémů musí zajistit, aby osoby <strong>byly informovány,
        že komunikují se systémem AI</strong>, a to jasným a srozumitelným způsobem.
    </div>

    {% if llm.get("chatbot_notices_custom") %}
    <h2>Doporučení pro vaši firmu</h2>
    {{ llm["chatbot_notices_custom"] }}
    {% endif %}

    {% set email = contact_email if contact_email != "—" else "info@firma.cz" %}

    <h2>Připravené texty k nasazení</h2>

    <div class="subsection">
        <h3>1. Krátké oznámení — chatbot</h3>
        <div style="background:#f5f5f5;padding:12px;margin:6px 0;font-family:monospace;font-size:11px;line-height:1.6">&#x1F916; Komunikujete s umělou inteligencí. Pokud chcete hovořit s člověkem, napište nám na {{ email }}.</div>
        <p style="font-size:10px;color:#555"><strong>Kde použít:</strong> Zobrazit v chatovacím okně před prvním automatickým pozdravem.</p>
        <p style="font-size:10px;color:#333"><strong>Právní základ:</strong> Povinné dle čl. 50 odst. 1</p>
    </div>

    <div class="subsection">
        <h3>2. Rozšířené oznámení — chatbot</h3>
        <div style="background:#f5f5f5;padding:12px;margin:6px 0;font-family:monospace;font-size:11px;line-height:1.6">Tento chat využívá systém umělé inteligence. Odpovědi jsou generovány automaticky a mohou obsahovat nepřesnosti. Společnost {{ company }} zajišťuje lidský dohled. Pro komunikaci s člověkem napište &bdquo;operátor&ldquo; nebo nás kontaktujte na {{ email }}.</div>
        <p style="font-size:10px;color:#555"><strong>Kde použít:</strong> Zobrazit v patičce chatovacího okna nebo jako úvodní zprávu.</p>
        <p style="font-size:10px;color:#333"><strong>Právní základ:</strong> Povinné dle čl. 50 odst. 1</p>
    </div>

    <div class="subsection">
        <h3>3. Banner na webu</h3>
        <div style="background:#f5f5f5;padding:12px;margin:6px 0;font-family:monospace;font-size:11px;line-height:1.6">Na tomto webu využíváme systémy umělé inteligence. Podrobnosti najdete na naší stránce AI transparence.</div>
        <p style="font-size:10px;color:#555"><strong>Kde použít:</strong> Zobrazit jako lištu na stránce nebo v patičce webu.</p>
        <p style="font-size:10px;color:#333"><strong>Právní základ:</strong> Doporučeno dle čl. 50</p>
    </div>

    <div class="subsection">
        <h3>4. E-mailová automatická odpověď</h3>
        <div style="background:#f5f5f5;padding:12px;margin:6px 0;font-family:monospace;font-size:11px;line-height:1.6">Děkujeme za Váš e-mail. Pro rychlejší vyřízení byl Váš dotaz předběžně zpracován systémem AI. Výslednou odpověď kontroluje člen týmu {{ company }}.</div>
        <p style="font-size:10px;color:#555"><strong>Kde použít:</strong> Vložit do automatické odpovědi e-mailového systému.</p>
        <p style="font-size:10px;color:#333"><strong>Právní základ:</strong> Doporučeno dle čl. 50</p>
    </div>

    <div class="subsection">
        <h3>5. AI-generovaný obsah</h3>
        <div style="background:#f5f5f5;padding:12px;margin:6px 0;font-family:monospace;font-size:11px;line-height:1.6">Tento obsah byl vytvořen nebo upraven pomocí umělé inteligence. &copy; {{ company }}</div>
        <p style="font-size:10px;color:#555"><strong>Kde použít:</strong> Označit AI-generovaný marketingový obsah, obrázky, texty, videa.</p>
        <p style="font-size:10px;color:#333"><strong>Právní základ:</strong> Povinné dle čl. 50 odst. 4</p>
    </div>

    <div class="subsection">
        <h3>6. Interní nástroje</h3>
        <div style="background:#f5f5f5;padding:12px;margin:6px 0;font-family:monospace;font-size:11px;line-height:1.6">Tento nástroj využívá umělou inteligenci. Výstupy nelze považovat za konečné — vždy ověřte správnost. Nevkládejte osobní údaje zákazníků.</div>
        <p style="font-size:10px;color:#555"><strong>Kde použít:</strong> Zobrazit při spuštění interního AI nástroje.</p>
        <p style="font-size:10px;color:#333"><strong>Právní základ:</strong> Doporučeno dle čl. 4 (AI literacy)</p>
    </div>

    <h2>Požadavky na přístupnost</h2>
    <ul class="bp-list">
        <li>Textové oznámení čitelné pro screen reader (alt text, ARIA labels)</li>
        <li>Dostatečný kontrast textu (min. 4.5:1 dle WCAG 2.1 AA)</li>
        <li>Velikost písma min. 14px, možnost zvětšení</li>
        <li>Možnost odmítnutí AI a přepnutí na lidského operátora</li>
    </ul>
</div>
""")

# ── AI POLITIKA ──
TPL_AI_POLICY = _jinja_env.from_string("""
<div class="doc-section" id="section-ai_policy">
    <div class="section-header">
        <div class="section-number">Kapitola {{ chapter }}</div>
        <h2>Interní AI politika</h2>
        <div class="section-sub">Pravidla používání umělé inteligence dle Nařízení (EU) 2024/1689</div>
    </div>

    <table>
        <tr><td style="width:200px;color:#555">Firma</td><td><strong>{{ company }}</strong></td></tr>
        <tr><td style="color:#555">Verze</td><td>1.0</td></tr>
        <tr><td style="color:#555">Platnost od</td><td>{{ now }}</td></tr>
        <tr><td style="color:#555">Příští revize</td><td>Nejpozději za 12 měsíců</td></tr>
        {% if oversight.name != "—" %}<tr><td style="color:#555">Odpovědná osoba za AI</td><td>{{ oversight.name }}</td></tr>{% endif %}
    </table>

    {% if llm.get("ai_policy_intro") %}
    {{ llm["ai_policy_intro"] }}
    {% endif %}

    <h2>1. Účel a cíle politiky</h2>
    <p>Tato politika stanoví pravidla pro používání, nasazování a správu systémů umělé inteligence
    ve společnosti {{ company }}.</p>
    <ul class="bp-list">
        <li>Zajistit soulad s Nařízením (EU) 2024/1689 (AI Act)</li>
        <li>Minimalizovat právní, reputační a provozní rizika</li>
        <li>Stanovit jasné odpovědnosti a pravidla</li>
        <li>Chránit práva zákazníků, zaměstnanců a dalších osob</li>
    </ul>

    <h2>2. Rozsah platnosti</h2>
    <p>Tato politika se vztahuje na všechny zaměstnance, spolupracovníky a dodavatele společnosti {{ company }}.</p>
    {% if system_names %}
    <p><strong>Aktuálně používané AI systémy:</strong> {{ system_names|join(", ") }}</p>
    {% endif %}

    <h2>3. Klasifikace AI systémů dle AI Act</h2>
    <table>
        <thead><tr><th>Kategorie</th><th>Příklad</th><th>Povinnosti</th></tr></thead>
        <tbody>
            <tr><td>{{ badge("high") }}</td><td>HR rozhodování, credit scoring</td><td>DPIA, registrace, monitoring</td></tr>
            <tr><td>{{ badge("limited") }}</td><td>Chatboty, doporučovací systémy</td><td>Transparenční oznámení (čl. 50)</td></tr>
            <tr><td>{{ badge("minimal") }}</td><td>Spam filtry, AI překlady</td><td>AI literacy (čl. 4)</td></tr>
        </tbody>
    </table>

    <h2>4. Povolené používání AI</h2>
    <h3>4.1 Obecné AI nástroje (ChatGPT, Claude, Gemini)</h3>
    <ul class="bp-list">
        <li>Povoleno pro interní práci: výzkum, analýza, brainstorming, překlady</li>
        <li><strong>ZAKÁZÁNO</strong> vkládat: osobní údaje zákazníků, finanční data, obchodní tajemství</li>
        <li>Výstupy VŽDY ověřit před použitím (AI halucinace, faktuální chyby)</li>
    </ul>
    <h3>4.2 AI pro kód (GitHub Copilot, Cursor)</h3>
    <ul class="bp-list">
        <li>Povoleno — AI-generovaný kód musí projít code review</li>
        <li>Nepoužívat pro bezpečnostně kritický kód bez manuální kontroly</li>
    </ul>
    <h3>4.3 AI pro zákaznický servis</h3>
    <ul class="bp-list">
        <li>Zákazník MUSÍ být informován, že komunikuje s AI (čl. 50)</li>
        <li>Zajistit možnost přepnutí na lidského operátora</li>
        <li>Lidský dohled nad AI odpověďmi — review vzorku min. 1× týdně</li>
    </ul>

    <h2>5. Zakázané praktiky (čl. 5 AI Act)</h2>
    <table>
        <thead><tr><th>Praktika</th><th>Článek</th><th>Sankce</th></tr></thead>
        <tbody>
            <tr><td>Sociální scoring</td><td>čl. 5(1)(c)</td><td rowspan="3">35 mil. EUR / 7 % obratu</td></tr>
            <tr><td>Podprahová manipulace</td><td>čl. 5(1)(a)</td></tr>
            <tr><td>Real-time biometrie na veřejnosti</td><td>čl. 5(1)(h)</td></tr>
        </tbody>
    </table>

    <h2>6. Pravidla pro data a soukromí</h2>
    <ul class="bp-list">
        <li>Do AI třetích stran NEVKLÁDEJTE osobní údaje (GDPR čl. 5, 6)</li>
        <li>Ověřujte opt-out trénování modelů na vašich datech</li>
        <li>Uchovávejte záznamy o používání AI — min. 6 měsíců (čl. 12)</li>
        <li>Před nasazením nového AI proveďte DPIA (GDPR čl. 35)</li>
    </ul>

    <h2>7. Povinnosti zaměstnanců</h2>
    <ul class="bp-list">
        <li>Absolvovat školení AI literacy (čl. 4) — prezentace v Compliance Kitu</li>
        <li>Hlásit nové AI nástroje odpovědné osobě PŘED nasazením</li>
        <li>Hlásit AI incidenty ihned odpovědné osobě</li>
        <li>Nespoléhat se slepě na AI výstupy — uplatnit kritické myšlení</li>
    </ul>

    <h2>8. Compliance kalendář</h2>
    <table>
        <thead><tr><th>Datum</th><th>Povinnost</th></tr></thead>
        <tbody>
            <tr><td><strong>2. 2. 2025</strong></td><td>Zákaz zakázaných praktik (čl. 5) + AI literacy (čl. 4) — již platí</td></tr>
            <tr><td><strong>2. 8. 2025</strong></td><td>Pravidla pro GPAI modely (čl. 51–56)</td></tr>
            <tr><td><strong>2. 8. 2026</strong></td><td>Plná compliance pro vysoce rizikové AI systémy</td></tr>
        </tbody>
    </table>

    <div class="sig-block">
        <div class="sig-cell"><div class="label">Schválil/a (vedení)</div><div class="line">Jméno, funkce, datum, podpis</div></div>
        <div class="sig-cell"><div class="label">Odpovědná osoba za AI</div><div class="line">Jméno, funkce, datum, podpis</div></div>
    </div>
</div>
""")

# ── INCIDENT RESPONSE PLAN ──
TPL_INCIDENT = _jinja_env.from_string("""
<div class="doc-section" id="section-incident_response_plan">
    <div class="section-header">
        <div class="section-number">Kapitola {{ chapter }}</div>
        <h2>Plán řízení AI incidentů</h2>
        <div class="section-sub">Postupy dle čl. 73 Nařízení (EU) 2024/1689</div>
    </div>

    <table>
        <tr><td style="width:180px;color:#555">Firma</td><td>{{ company }}</td></tr>
        <tr><td style="color:#555">Platnost od</td><td>{{ now }}</td></tr>
        {% if oversight.name != "—" %}<tr><td style="color:#555">Odpovědná osoba</td><td>{{ oversight.name }}{% if oversight.email != "—" %} ({{ oversight.email }}){% endif %}</td></tr>{% endif %}
    </table>

    <h2>1. Definice AI incidentu</h2>
    <p>Za AI incident se považuje situace, kdy systém AI:</p>
    <ul class="bp-list">
        <li>Poskytne nesprávnou, zavádějící nebo diskriminační odpověď</li>
        <li>Zpracuje osobní údaje v rozporu s GDPR</li>
        <li>Vygeneruje obsah porušující autorská práva</li>
        <li>Se stane obětí kyberútoku (prompt injection, data poisoning)</li>
        <li>Způsobí fyzickou nebo psychickou újmu osobám</li>
    </ul>

    <h2>2. Klasifikace závažnosti</h2>
    <table>
        <thead><tr><th>Stupeň</th><th>Příklad</th><th>Reakce</th></tr></thead>
        <tbody>
            <tr><td>{{ badge("high") }} <strong>Kritický</strong></td><td>Diskriminace, únik osobních údajů</td><td><strong>1 hodina</strong></td></tr>
            <tr><td>{{ badge("limited") }} <strong>Střední</strong></td><td>Chybná informace chatbotu</td><td><strong>24 hodin</strong></td></tr>
            <tr><td>{{ badge("minimal") }} <strong>Nízký</strong></td><td>Překlep v AI odpovědi</td><td><strong>72 hodin</strong></td></tr>
        </tbody>
    </table>

    <div class="highlight">
        <strong>Zákonné lhůty hlášení (čl. 73 AI Act):</strong><br>
        Závažný incident → 15 dnů dozorové autoritě<br>
        Poškození zdraví → 10 dnů<br>
        Masivní porušení práv → 2 dny<br>
        GDPR data breach → 72 hodin ÚOOÚ (čl. 33 GDPR)
    </div>

    {% if llm.get("incident_guidance") %}
    <h2>Specifické pokyny pro {{ company }}</h2>
    {{ llm["incident_guidance"] }}
    {% endif %}

    <h2>3. Postup při incidentu</h2>
    <h3>Fáze 1 — Okamžitá reakce</h3>
    <ul class="bp-list">
        <li>Zastavit AI systém, který incident způsobil</li>
        <li>Zajistit důkazy — screenshot, logy, čas, dotčení uživatelé</li>
        <li>Informovat odpovědnou osobu za AI</li>
        <li>U kritických incidentů: okamžitě odstavit systém</li>
    </ul>
    <h3>Fáze 2 — Vyhodnocení</h3>
    <ul class="bp-list">
        <li>Klasifikovat závažnost (kritický / střední / nízký)</li>
        <li>Posoudit povinnost hlášení dle čl. 73 AI Act</li>
        <li>Analyzovat root cause</li>
    </ul>
    <h3>Fáze 3 — Náprava</h3>
    <ul class="bp-list">
        <li>Opravit AI systém / změnit konfiguraci</li>
        <li>Informovat dotčené osoby</li>
        <li>Aktualizovat registr AI systémů</li>
        <li>Dokumentovat příčinu a přijatá opatření</li>
    </ul>

    <h2>4. Záznamový formulář incidentu</h2>
    <table>
        <tr><td style="width:220px;color:#555">Číslo incidentu</td><td>AI-INC-______</td></tr>
        <tr><td style="color:#555">Datum a čas</td><td></td></tr>
        <tr><td style="color:#555">Dotčený AI systém</td><td></td></tr>
        <tr><td style="color:#555">Závažnost</td><td>Kritický / Střední / Nízký</td></tr>
        <tr><td style="color:#555">Popis incidentu</td><td></td></tr>
        <tr><td style="color:#555">Root cause</td><td></td></tr>
        <tr><td style="color:#555">Přijatá opatření</td><td></td></tr>
        <tr><td style="color:#555">Podpis</td><td></td></tr>
    </table>
</div>
""")

# ── DPIA ──
TPL_DPIA = _jinja_env.from_string("""
<div class="doc-section" id="section-dpia_template">
    <div class="section-header">
        <div class="section-number">Kapitola {{ chapter }}</div>
        <h2>DPIA — Posouzení vlivu na ochranu údajů a základní práva</h2>
        <div class="section-sub">Šablona dle GDPR čl. 35 + AI Act čl. 27 (FRIA)</div>
    </div>

    <table>
        <tr><td style="width:180px;color:#555">Firma</td><td>{{ company }}</td></tr>
        <tr><td style="color:#555">Datum zpracování</td><td>{{ now }}</td></tr>
        <tr><td style="color:#555">Celkové riziko</td><td>{{ badge(overall_risk) }}</td></tr>
    </table>

    <div class="metric-grid">
        <div class="metric"><div class="metric-value">{{ total_systems }}</div><div class="metric-label">AI systémů</div></div>
        <div class="metric"><div class="metric-value">{{ high_systems|length }}</div><div class="metric-label">Vysoce rizikových</div></div>
    </div>

    <div class="highlight">
        <strong>Čl. 27 AI Act — FRIA:</strong> Nasazovatelé vysoce rizikových AI systémů musí
        před nasazením provést posouzení dopadu na základní práva. Doplňuje DPIA dle GDPR čl. 35.
    </div>

    {% if llm.get("dpia_narrative") %}
    <h2>Odborné posouzení</h2>
    {{ llm["dpia_narrative"] }}
    {% endif %}

    <h2>1. Odpovědné osoby</h2>
    <table>
        <tr><td style="width:220px;color:#555">Správce osobních údajů</td><td>{{ company }}</td></tr>
        {% if oversight.name != "—" %}<tr><td style="color:#555">Odpovědná osoba za AI</td><td>{{ oversight.name }}</td></tr>{% endif %}
        {% if oversight.email != "—" %}<tr><td style="color:#555">E-mail</td><td>{{ oversight.email }}</td></tr>{% endif %}
    </table>

    {% if all_systems %}
    <h2>2. AI systémy zpracovávající osobní údaje</h2>
    <table>
        <thead><tr><th>AI systém</th><th>Riziko</th><th>Dodavatel</th></tr></thead>
        <tbody>
        {% for s in all_systems %}
            <tr><td>{{ s.name }}</td><td>{{ badge(s.risk_level) }}</td><td>{{ s.vendor }}</td></tr>
        {% endfor %}
        </tbody>
    </table>
    {% endif %}

    <h2>3. Posouzení nezbytnosti (GDPR čl. 35)</h2>
    <ul class="bp-list">
        <li>Zpracování je nezbytné pro splnění legitimního účelu</li>
        <li>Rozsah údajů je minimalizován (data minimization)</li>
        <li>Doba uchovávání je definovaná</li>
        <li>Subjekty údajů byly informovány (transparence)</li>
        <li>Právní základ zpracování identifikován (čl. 6 GDPR)</li>
    </ul>

    <h2>4. Technická a organizační opatření</h2>
    <ul class="bp-list">
        <li><strong>Šifrování</strong> — data šifrována při přenosu (TLS) i v úložišti</li>
        <li><strong>Přístupová práva</strong> — RBAC, přístup jen pro oprávněné</li>
        <li><strong>Logování</strong> — min. 6 měsíců (čl. 12)</li>
        <li><strong>Lidský dohled</strong> — AI rozhodnutí přezkoumatelná člověkem (čl. 14)</li>
        <li><strong>Anonymizace</strong> — data vstupující do AI anonymizována</li>
        <li><strong>Pravidelné audity</strong> — min. 1× ročně</li>
    </ul>

    <h2>5. Závěr posouzení</h2>
    <table>
        <tr><td style="width:220px;color:#555">Celkové riziko</td><td>{{ badge(overall_risk) }}</td></tr>
    </table>

    <div class="sig-block">
        <div class="sig-cell"><div class="label">Odpovědná osoba za AI</div><div class="line">Jméno, datum, podpis</div></div>
        <div class="sig-cell"><div class="label">DPO / pověřenec</div><div class="line">Jméno, datum, podpis</div></div>
        <div class="sig-cell"><div class="label">Vedení firmy</div><div class="line">Jméno, datum, podpis</div></div>
    </div>
</div>
""")

# ── VENDOR CHECKLIST ──
TPL_VENDOR = _jinja_env.from_string("""
<div class="doc-section" id="section-vendor_checklist">
    <div class="section-header">
        <div class="section-number">Kapitola {{ chapter }}</div>
        <h2>Dodavatelský checklist</h2>
        <div class="section-sub">Kontrolní seznam smluv s dodavateli AI dle čl. 25–26 AI Act</div>
    </div>

    <table>
        <tr><td style="width:200px;color:#555">Firma</td><td>{{ company }}</td></tr>
        <tr><td style="color:#555">Smluvní pokrytí</td><td>{{ "✓ Má smlouvy s dodavateli AI" if data_prot.get("has_vendor_contracts") else "⚠ Nemá smluvně ošetřeno" }}</td></tr>
    </table>

    {% if vendors %}
    <h2>Přehled dodavatelů AI</h2>
    <table>
        <thead><tr><th>Dodavatel</th><th>Sídlo</th><th>AI systémy</th></tr></thead>
        <tbody>
        {% for v in vendors %}
            <tr><td><strong>{{ v.name }}</strong></td><td>{{ v.country }}</td><td>{{ v.systems|join(", ") }}</td></tr>
        {% endfor %}
        </tbody>
    </table>
    {% endif %}

    {% if all_systems %}
    <h2>AI systémy a dodavatelé</h2>
    <table>
        <thead><tr><th>AI systém</th><th>Dodavatel</th><th>Země</th><th>Riziko</th></tr></thead>
        <tbody>
        {% for s in all_systems %}
            <tr><td>{{ s.name }}</td><td>{{ s.vendor }}</td><td>{{ s.country }}</td><td>{{ badge(s.risk_level) }}</td></tr>
        {% endfor %}
        </tbody>
    </table>
    {% endif %}

    <div class="highlight">
        <strong>Pozor — mimo-EU dodavatelé:</strong> Pro předávání osobních údajů do USA
        je nutný SCC nebo certifikace dle EU-US Data Privacy Framework.
    </div>

    {% if llm.get("vendor_assessment") %}
    <h2>Hodnocení dodavatelů</h2>
    {{ llm["vendor_assessment"] }}
    {% endif %}

    <h2>Povinné smluvní náležitosti</h2>
    <h3>A. Transparentnost a dokumentace (čl. 13)</h3>
    <ul class="bp-list">
        <li>Dodavatel poskytl návod k použití AI systému</li>
        <li>Dodavatel deklaroval zamýšlený účel použití</li>
        <li>Dodavatel informuje o změnách modelu / API</li>
    </ul>
    <h3>B. Ochrana osobních údajů (GDPR)</h3>
    <ul class="bp-list">
        <li>DPA / zpracovatelská smlouva uzavřena</li>
        <li>Dodavatel garantuje zpracování v EU/EHP (nebo má SCC)</li>
        <li><strong>Dodavatel NEPOUŽÍVÁ data klienta k trénování modelu (opt-out)</strong></li>
        <li>Definováno nakládání s daty po ukončení smlouvy</li>
    </ul>
    <h3>C. Technické záruky</h3>
    <ul class="bp-list">
        <li>SLA — dostupnost a výkonnost</li>
        <li>Právo na audit a kontrolu dodavatele</li>
        <li>Bezpečnostní certifikace (SOC 2, ISO 27001)</li>
    </ul>

    {% if vendors %}
    <h2>Per-dodavatel checklist</h2>
    <table>
        <thead>
            <tr><th>Kritérium</th>{% for v in vendors[:4] %}<th>{{ v.name[:20] }}</th>{% endfor %}</tr>
        </thead>
        <tbody>
            {% for crit in ["DPA uzavřena", "Data v EU", "Opt-out trénování", "SLA definováno", "Právo na audit", "Certifikace"] %}
            <tr><td>{{ crit }}</td>{% for v in vendors[:4] %}<td></td>{% endfor %}</tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}
</div>
""")

# ── MONITORING PLAN ──
TPL_MONITORING = _jinja_env.from_string("""
<div class="doc-section" id="section-monitoring_plan">
    <div class="section-header">
        <div class="section-number">Kapitola {{ chapter }}</div>
        <h2>Monitoring plán AI</h2>
        <div class="section-sub">Plán monitoringu AI výstupů dle čl. 9, 12 a 72 AI Act</div>
    </div>

    <table>
        <tr><td style="width:180px;color:#555">Firma</td><td>{{ company }}</td></tr>
        {% if oversight.name != "—" %}<tr><td style="color:#555">Odpovědná osoba</td><td>{{ oversight.name }}</td></tr>{% endif %}
        <tr><td style="color:#555">Platnost od</td><td>{{ now }}</td></tr>
    </table>

    <div class="highlight">
        <strong>čl. 12 AI Act:</strong> Logy z provozu AI systémů musí být uchovávány
        <strong>minimálně 6 měsíců</strong>.
    </div>

    {% if all_systems %}
    <h2>Monitorované AI systémy</h2>
    {% set freq_map = {"high": "Denně / týdně", "limited": "Týdně / měsíčně", "minimal": "Měsíčně / čtvrtletně"} %}
    <table>
        <thead><tr><th>AI systém</th><th>Riziko</th><th>Frekvence kontroly</th></tr></thead>
        <tbody>
        {% for s in all_systems %}
            <tr><td>{{ s.name }}</td><td>{{ badge(s.risk_level) }}</td><td>{{ freq_map.get(s.risk_level, "Měsíčně") }}</td></tr>
        {% endfor %}
        </tbody>
    </table>
    {% endif %}

    {% if llm.get("monitoring_recommendations") %}
    <h2>Specifická doporučení</h2>
    {{ llm["monitoring_recommendations"] }}
    {% endif %}

    <h2>KPI metriky</h2>
    <h3>A. Přesnost a kvalita</h3>
    <ul class="bp-list">
        <li>Míra chybných odpovědí (error rate)</li>
        <li>AI halucinace (hallucination rate)</li>
        <li>Spokojenost uživatelů (feedback score)</li>
    </ul>
    <h3>B. Férovost a bias</h3>
    <ul class="bp-list">
        <li>Genderový a etnický bias</li>
        <li>Jazykový bias — kvalita pro češtinu vs. angličtinu</li>
    </ul>
    <h3>C. Bezpečnost</h3>
    <ul class="bp-list">
        <li>Prompt injection pokusy (red teaming)</li>
        <li>Data leakage — citlivé informace ve výstupech</li>
        <li>Uptime a dostupnost (SLA monitoring)</li>
    </ul>

    <h2>Měsíční plán kontrol</h2>
    <table>
        <thead><tr><th>Týden</th><th>Aktivita</th><th>Odpovědnost</th></tr></thead>
        <tbody>
            <tr><td>1.</td><td>Review přesnosti AI výstupů (vzorek 20 odpovědí)</td><td>Odpovědná osoba</td></tr>
            <tr><td>2.</td><td>Bias test — 10 testovacích dotazů z různých skupin</td><td>Odpovědná osoba</td></tr>
            <tr><td>3.</td><td>Aktualizace registru AI systémů</td><td>Odpovědná osoba</td></tr>
            <tr><td>4.</td><td>Souhrnný report vedení</td><td>Odpovědná osoba</td></tr>
        </tbody>
    </table>
</div>
""")

# ── TRANSPARENTNOST A LIDSKÝ DOHLED ──
TPL_TRANSPARENCY = _jinja_env.from_string("""
<div class="doc-section" id="section-transparency_human_oversight">
    <div class="section-header">
        <div class="section-number">Kapitola {{ chapter }}</div>
        <h2>Záznamy o transparentnosti a lidském dohledu</h2>
        <div class="section-sub">Povinnosti dle čl. 13, 14 a 50 AI Act</div>
    </div>

    <table>
        <tr><td style="width:200px;color:#555">Firma</td><td>{{ company }}</td></tr>
        {% if oversight.name != "—" %}<tr><td style="color:#555">Odpovědná osoba</td><td>{{ oversight.name }}</td></tr>{% endif %}
        <tr><td style="color:#555">Celkové riziko</td><td>{{ badge(overall_risk) }}</td></tr>
    </table>

    <div class="highlight">
        <strong>Čl. 13</strong> — Transparentnost vysoce rizikových AI<br>
        <strong>Čl. 14</strong> — Lidský dohled nad vysoce rizikovými AI<br>
        <strong>Čl. 50</strong> — Transparenční povinnosti pro všechny AI
    </div>

    {% if llm.get("transparency_oversight") %}
    <h2>Personalizovaná doporučení</h2>
    {{ llm["transparency_oversight"] }}
    {% endif %}

    <h2>1. Aktuální stav opatření</h2>
    <table>
        <tr><td style="width:280px">Možnost přerušení / přepsání AI</td><td>{{ "✅ Zavedeno" if human_oversight.get("can_override") else "⚠️ Nezavedeno" }}</td></tr>
        <tr><td>Logování AI rozhodnutí</td><td>{{ "✅ Zavedeno" if human_oversight.get("has_logging") else "⚠️ Nezavedeno" }}</td></tr>
        <tr><td>Monitoring výstupů AI</td><td>{{ "✅ Zavedeno" if incident.get("monitors_outputs") else "⚠️ Nezavedeno" }}</td></tr>
    </table>

    {% if all_systems %}
    <h2>2. AI systémy — transparentnost a dohled</h2>
    <table>
        <thead><tr><th>#</th><th>AI systém</th><th>Riziko</th><th>Zdroj</th></tr></thead>
        <tbody>
        {% for s in all_systems %}
            <tr><td>{{ loop.index }}</td><td>{{ s.name }}</td><td>{{ badge(s.risk_level) }}</td><td>{{ s.source }}</td></tr>
        {% endfor %}
        </tbody>
    </table>
    {% endif %}

    <h2>3. Povinnosti transparentnosti (čl. 50)</h2>
    <ul class="bp-list">
        <li>Uživatel informován, že komunikuje s AI</li>
        <li>AI-generovaný obsah označen</li>
        <li>Dotčené osoby mohou požádat o lidský přezkum</li>
    </ul>

    <h2>4. Opatření lidského dohledu (čl. 14)</h2>
    <ul class="bp-list">
        <li>Kill switch — AI lze kdykoli zastavit</li>
        <li>Override — člověk může přepsat AI rozhodnutí</li>
        <li>Monitoring — výstupy AI kontrolovány člověkem</li>
        <li>Kompetence — dohledová osoba proškolena</li>
    </ul>

    <h2>5. Záznamový list — čtvrtletní kontrola</h2>
    <table>
        <tr><td style="width:260px;color:#888">Období</td><td></td></tr>
        <tr><td style="color:#888">Datum kontroly</td><td></td></tr>
        <tr><td style="color:#888">Kontroloval/a</td><td></td></tr>
        <tr><td style="color:#888">Oznámení na webu</td><td>OK / Chybí</td></tr>
        <tr><td style="color:#888">Logování aktivní</td><td>OK / Nefunkční</td></tr>
        <tr><td style="color:#888">Kill switch testován</td><td>Ano / Ne</td></tr>
        <tr><td style="color:#888">Nalezené problémy</td><td></td></tr>
        <tr><td style="color:#888">Podpis</td><td></td></tr>
    </table>

    <div class="highlight">
        Archivujte záznamy po dobu provozu AI + 10 let (čl. 18 AI Act).
    </div>
</div>
""")

# ── VOP ──
TPL_VOP = _jinja_env.from_string("""
<div class="vop-section" id="section-vop">
    <div class="section-header">
        <h2>Všeobecné obchodní podmínky (VOP)</h2>
        <div class="section-sub">AIshield.cz — Martin Haynes, IČO: 17889251</div>
    </div>

    <h3>1. Vymezení služby</h3>
    <p>Služba AIshield.cz je automatizovaný technický nástroj, který na základě
    uživatelem poskytnutých údajů a veřejně dostupného obsahu webu vytváří
    orientační výstupy a návrhy dokumentů pro účely interní compliance.
    Poskytovatel neposkytuje právní služby ve smyslu zákona č. 85/1996 Sb.</p>

    <h3>2. Charakter výstupů</h3>
    <p>Výstupy jsou technicko-informační podklad založený na uživatelských vstupech
    a algoritmickém zpracování. Nejsou právním posouzením a nemohou nahrazovat
    individuální právní analýzu provedenou advokátem.</p>

    <h3>3. AI-generovaný obsah</h3>
    <p>Dokumentace byla vytvořena s využitím systémů umělé inteligence a odborného
    dohledu týmu AIshield.cz. Uživatel je odpovědný za implementaci a právní
    posouzení výstupů.</p>

    <h3>4. Omezení odpovědnosti</h3>
    <p>Celková odpovědnost poskytovatele se omezuje na částku uhrazenou za službu
    za posledních 12 měsíců. Poskytovatel neodpovídá za přímé ani nepřímé škody
    vzniklé použitím výstupů.</p>

    <h3>5. Povinnosti uživatele</h3>
    <p>Uživatel odpovídá za správnost údajů v dotazníku a za to, že výstupy
    přiměřeně zkontroluje a přizpůsobí svému provozu.</p>

    <h3>6. Licence k výstupům</h3>
    <p>Uživatel získává nevýhradní licenci pro interní potřeby své firmy.
    Přeprodej nebo prezentace výstupů jako „právně ověřených" je zakázáno.</p>

    <h3>7. Ochrana osobních údajů</h3>
    <p>Zpracování probíhá v souladu s GDPR. Data uložena v EU (Frankfurt).
    Zpracování na základě čl. 6 odst. 1 písm. b GDPR.</p>

    <h3>8. Reklamace</h3>
    <p>Do 30 dnů od dodání na info@aishield.cz. Vyřízení do 30 dnů.</p>

    <h3>9. Rozhodné právo</h3>
    <p>České právo, příslušné české soudy.</p>

    <div class="doc-footer">
        <strong>AIshield.cz</strong> — Provozovatel: Martin Haynes, IČO: 17889251<br>
        info@aishield.cz · +420 732 716 141 · aishield.cz
    </div>
</div>
""")


# ══════════════════════════════════════════════════════════════════════
# SECTION ROUTER
# ══════════════════════════════════════════════════════════════════════

_SECTION_TEMPLATES = {
    "compliance_report": TPL_COMPLIANCE_REPORT,
    "action_plan": TPL_ACTION_PLAN,
    "ai_register": TPL_AI_REGISTER,
    "training_outline": TPL_TRAINING,
    "chatbot_notices": TPL_CHATBOT_NOTICES,
    "ai_policy": TPL_AI_POLICY,
    "incident_response_plan": TPL_INCIDENT,
    "dpia_template": TPL_DPIA,
    "vendor_checklist": TPL_VENDOR,
    "monitoring_plan": TPL_MONITORING,
    "transparency_human_oversight": TPL_TRANSPARENCY,
}

# Backward compatibility — pipeline.py imports SECTION_RENDERERS
def _make_renderer(tpl):
    """Vytvoří renderer funkci pro šablonu."""
    def renderer(data):
        ctx = _preprocess_data(data)
        ctx["chapter"] = ctx.get("_chapter", "")
        ctx["section_names"] = TEMPLATE_NAMES
        return tpl.render(**ctx)
    return renderer

SECTION_RENDERERS = {key: _make_renderer(tpl) for key, tpl in _SECTION_TEMPLATES.items()}


# ══════════════════════════════════════════════════════════════════════
# HLAVNÍ FUNKCE — generování HTML pro PDF
# ══════════════════════════════════════════════════════════════════════

def render_unified_pdf_html(data: dict, eligible_keys: list) -> str:
    """
    Generuje kompletní HTML pro unified PDF.
    Titulní strana → Obsah → Sekce → VOP
    """
    ctx = _preprocess_data(data)
    ctx["section_names"] = TEMPLATE_NAMES
    company = ctx["company"]

    pdf_keys = [k for k in eligible_keys if k != "transparency_page"]
    ctx["pdf_keys"] = pdf_keys

    # Render title + TOC
    title_html = TPL_TITLE.render(**ctx)
    toc_html = TPL_TOC.render(**ctx)

    # Render sections
    sections_html = ""
    for chapter_num, key in enumerate(pdf_keys, 1):
        tpl = _SECTION_TEMPLATES.get(key)
        if tpl:
            try:
                ctx["chapter"] = chapter_num
                ctx["_chapter"] = chapter_num
                section_html = tpl.render(**ctx)
                sections_html += section_html
            except Exception as e:
                logger.error(f"Chyba při renderování {key}: {e}", exc_info=True)
                sections_html += f"""
                <div class="doc-section" id="section-{key}">
                    <div class="section-header">
                        <div class="section-number">Kapitola {chapter_num}</div>
                        <h2>{TEMPLATE_NAMES.get(key, key)}</h2>
                        <div class="section-sub">Chyba při generování sekce</div>
                    </div>
                    <p>Sekci se nepodařilo vygenerovat: {str(e)}</p>
                </div>"""

    vop_html = TPL_VOP.render(**ctx)

    now = ctx["now"]
    year = ctx["year"]

    return f"""<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="utf-8">
    <title>AI Act Compliance Kit — {company}</title>
    {UNIFIED_CSS}
</head>
<body>
    {title_html}
    {toc_html}
    {sections_html}
    {vop_html}

    <div class="doc-footer">
        Vygenerováno: {now} · AIshield.cz · info@aishield.cz · +420 732 716 141<br>
        © {year} AIshield.cz — Vypracováno odborným týmem s využitím pokročilých AI nástrojů
    </div>
</body>
</html>"""


def render_section_pdf_html(section_key: str, data: dict) -> str:
    """
    Generuje standalone HTML pro jednu sekci → WeasyPrint → PDF.
    """
    tpl = _SECTION_TEMPLATES.get(section_key)
    if not tpl:
        raise ValueError(f"Neznámá sekce: {section_key}")

    ctx = _preprocess_data(data)
    ctx["chapter"] = ""
    ctx["section_names"] = TEMPLATE_NAMES
    company = ctx["company"]
    section_name = TEMPLATE_NAMES.get(section_key, section_key)
    now = ctx["now"]
    year = ctx["year"]
    overall = ctx["overall_risk"]
    risk_labels = {"high": "VYSOKÉ", "limited": "OMEZENÉ", "minimal": "MINIMÁLNÍ"}

    try:
        section_html = tpl.render(**ctx)
    except Exception as e:
        logger.error(f"Chyba při renderování sekce {section_key}: {e}", exc_info=True)
        section_html = f'<div class="doc-section"><p>Sekci se nepodařilo vygenerovat: {e}</p></div>'

    mini_title = f"""
    <div style="text-align:center; padding:40px 20px 30px; border-bottom:2px solid #111; margin-bottom:20px;">
        <div style="font-size:14px; font-weight:800; color:#111;">
            <span>AI</span><span style="color:#333">shield</span><span style="color:#888;font-size:8px">.cz</span>
        </div>
        <div style="width:40px; height:1px; background:#111; margin:8px auto;"></div>
        <h1 style="font-size:20px; font-weight:700; color:#111; margin:12px 0 4px;">{section_name}</h1>
        <div style="font-size:14px; font-weight:600; color:#111;">{company}</div>
        <div style="font-size:10px; color:#666; margin-top:8px;">
            AI Act Compliance Kit · Celkové riziko: {risk_labels.get(overall, overall)} · {now}
        </div>
    </div>
    """

    return f"""<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="utf-8">
    <title>{section_name} — {company}</title>
    {UNIFIED_CSS}
</head>
<body>
    {mini_title}
    {section_html}

    <div class="doc-footer">
        {section_name} · {company} · Vygenerováno: {now}<br>
        AIshield.cz · Vypracováno odborným týmem s využitím pokročilých AI nástrojů<br>
        © {year} AIshield.cz · info@aishield.cz · +420 732 716 141
    </div>
</body>
</html>"""
