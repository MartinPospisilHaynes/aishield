"""
AIshield.cz — HTML šablony pro AI Act Compliance Kit
Úkol 17: 7 typů dokumentů generovaných z dat skenu + dotazníku.

Šablony:
1. compliance_report — Hlavní compliance report (nálezy, klasifikace, rizika)
2. transparency_page — Stránka AI transparence pro web klienta  
3. action_plan — Akční plán s checkboxy a deadliny
4. ai_register — Registr AI systémů firmy (interní dokument)
5. chatbot_notices — Texty oznámení pro chatboty (copy-paste)
6. ai_policy — Interní AI politika firmy (šablona)
7. training_outline — Osnova školení AI literacy (čl. 4)

Každá šablona: profesionální CSS, Jinja2-like placeholders, disclaimer.
"""

from datetime import datetime, timezone

# ══════════════════════════════════════════════════════════════════════
# SPOLEČNÉ STYLY
# ══════════════════════════════════════════════════════════════════════

COMMON_CSS = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --color-bg: #0f172a;
            --color-surface: #1e293b;
            --color-primary: #e879f9;
            --color-primary-dark: #c026d3;
            --color-secondary: #22d3ee;
            --color-text: #f1f5f9;
            --color-muted: #94a3b8;
            --color-border: rgba(255,255,255,0.08);
            --color-high: #ef4444;
            --color-limited: #f59e0b;
            --color-minimal: #22c55e;
        }
        
        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background: var(--color-bg);
            color: var(--color-text);
            line-height: 1.6;
            font-size: 14px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 32px;
        }
        
        /* Print styles */
        @media print {
            body { background: white; color: #1e293b; font-size: 11px; }
            .container { padding: 20px; max-width: 100%; }
            .glass-card { background: #f8fafc; border: 1px solid #e2e8f0; }
            .no-print { display: none; }
            .risk-high { color: #dc2626 !important; }
            .risk-limited { color: #d97706 !important; }
            .risk-minimal { color: #16a34a !important; }
            h1, h2, h3 { color: #0f172a; }
            .header { background: #0f172a !important; -webkit-print-color-adjust: exact; }
        }
        
        .header {
            background: linear-gradient(135deg, var(--color-bg), var(--color-surface));
            border-bottom: 1px solid var(--color-border);
            padding: 32px;
            margin: -40px -32px 32px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 24px;
            font-weight: 800;
            margin-bottom: 4px;
            letter-spacing: -0.03em;
        }
        
        .brand {
            font-weight: 800;
            letter-spacing: -0.04em;
        }
        .brand-ai { color: var(--color-text); }
        .brand-shield { 
            background: linear-gradient(135deg, var(--color-primary), var(--color-secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .subtitle {
            color: var(--color-muted);
            font-size: 13px;
        }
        
        .glass-card {
            background: rgba(30,41,59,0.7);
            backdrop-filter: blur(10px);
            border: 1px solid var(--color-border);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
        }
        
        h2 {
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 16px;
            letter-spacing: -0.02em;
        }
        
        h3 {
            font-size: 15px;
            font-weight: 600;
            margin-bottom: 12px;
        }
        
        p { margin-bottom: 8px; }
        
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
        }
        .badge-high { background: rgba(239,68,68,0.12); border: 1px solid rgba(239,68,68,0.3); color: #f87171; }
        .badge-limited { background: rgba(245,158,11,0.12); border: 1px solid rgba(245,158,11,0.3); color: #fbbf24; }
        .badge-minimal { background: rgba(34,197,94,0.12); border: 1px solid rgba(34,197,94,0.3); color: #4ade80; }
        .badge-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
        .badge-dot-high { background: #f87171; }
        .badge-dot-limited { background: #fbbf24; }
        .badge-dot-minimal { background: #4ade80; }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 12px 0;
        }
        th {
            text-align: left;
            padding: 10px 12px;
            background: rgba(15,23,42,0.5);
            border-bottom: 1px solid var(--color-border);
            font-weight: 600;
            font-size: 12px;
            color: var(--color-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        td {
            padding: 10px 12px;
            border-bottom: 1px solid var(--color-border);
            font-size: 13px;
        }
        
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }
        .metric {
            text-align: center;
            padding: 16px;
            background: rgba(15,23,42,0.5);
            border-radius: 12px;
            border: 1px solid var(--color-border);
        }
        .metric-value {
            font-size: 28px;
            font-weight: 800;
            line-height: 1;
        }
        .metric-label {
            font-size: 11px;
            color: var(--color-muted);
            margin-top: 4px;
        }
        
        .disclaimer {
            margin-top: 32px;
            padding: 16px;
            background: rgba(245,158,11,0.08);
            border: 1px solid rgba(245,158,11,0.2);
            border-radius: 12px;
            font-size: 11px;
            color: var(--color-muted);
        }
        
        .footer {
            text-align: center;
            padding: 24px 0;
            font-size: 11px;
            color: var(--color-muted);
            border-top: 1px solid var(--color-border);
            margin-top: 32px;
        }
        
        .checkbox-item {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            padding: 10px 0;
            border-bottom: 1px solid var(--color-border);
        }
        .checkbox {
            width: 18px;
            height: 18px;
            border: 2px solid var(--color-muted);
            border-radius: 4px;
            flex-shrink: 0;
            margin-top: 2px;
        }
        .checkbox-done {
            border-color: var(--color-minimal);
            background: rgba(34,197,94,0.15);
        }
        
        .section-divider {
            width: 60px;
            height: 3px;
            background: linear-gradient(90deg, var(--color-primary), var(--color-secondary));
            border-radius: 2px;
            margin: 24px 0;
        }
        
        .highlight-box {
            padding: 16px;
            border-left: 3px solid var(--color-primary);
            background: rgba(232,121,249,0.06);
            border-radius: 0 12px 12px 0;
            margin: 12px 0;
        }
        
        ul, ol { margin: 8px 0; padding-left: 20px; }
        li { margin-bottom: 6px; font-size: 13px; }
    </style>
"""

HEADER_HTML = """
    <div class="header">
        <div style="font-size:28px;margin-bottom:4px;">
            <span class="brand brand-ai">AI</span><span class="brand brand-shield">shield</span><span style="color:var(--color-muted);font-size:14px;margin-left:4px;">.cz</span>
        </div>
        <h1>{title}</h1>
        <p class="subtitle">{subtitle}</p>
    </div>
"""

DISCLAIMER_HTML = """
    <div class="disclaimer">
        <strong>⚖️ Právní upozornění:</strong> Dokumenty vygenerované platformou AIshield.cz 
        jsou vytvořeny na základě automatizované analýzy a informací poskytnutých klientem. 
        AIshield.cz poskytuje compliance dokumentaci jako technickou pomůcku pro splnění 
        požadavků Nařízení (EU) 2024/1689 (AI Act), nikoliv jako právní poradenství 
        ve smyslu zák. č. 85/1996 Sb., o advokacii. AIshield.cz nenese odpovědnost 
        za případné sankce vzniklé nesprávným nebo neúplným použitím dokumentů. 
        Klient je odpovědný za správnost poskytnutých údajů a implementaci doporučených opatření.
        Doporučujeme konzultaci s právním specialistou pro finální validaci.
    </div>
"""

FOOTER_HTML = """
    <div class="footer">
        Vygenerováno: {generated_at} &bull; AIshield.cz &bull; info@desperados-design.cz &bull; +420 732 716 141<br>
        &copy; {year} AIshield.cz — Provozovatel: Martin Haynes, IČO: 17889251
    </div>
"""


def _now_str() -> str:
    return datetime.now(timezone.utc).strftime("%d. %m. %Y, %H:%M UTC")


def _risk_badge(level: str) -> str:
    labels = {"high": "Vysoké riziko", "limited": "Omezené riziko", "minimal": "Minimální riziko"}
    return f'<span class="badge badge-{level}"><span class="badge-dot badge-dot-{level}"></span>{labels.get(level, level)}</span>'


def _wrap_page(title: str, subtitle: str, body: str) -> str:
    now = _now_str()
    year = datetime.now().year
    return f"""<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title} — AIshield.cz</title>
    {COMMON_CSS}
</head>
<body>
    <div class="container">
        {HEADER_HTML.format(title=title, subtitle=subtitle)}
        {body}
        {DISCLAIMER_HTML}
        {FOOTER_HTML.format(generated_at=now, year=year)}
    </div>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════════
# 1. COMPLIANCE REPORT — hlavní report
# ══════════════════════════════════════════════════════════════════════

def render_compliance_report(data: dict) -> str:
    """
    Hlavní AI Act compliance report.
    data: company_name, url, scan_date, findings[], questionnaire_answers[],
          risk_breakdown{}, overall_risk, recommendations[]
    """
    company = data.get("company_name", "Neznámá firma")
    url = data.get("url", "")
    findings = data.get("findings", [])
    q_systems = data.get("questionnaire_ai_systems", 0)
    risk = data.get("risk_breakdown", {"high": 0, "limited": 0, "minimal": 0})
    recommendations = data.get("recommendations", [])
    overall = data.get("overall_risk", "minimal")
    total = len(findings) + q_systems

    # Metriky
    metrics_html = f"""
    <div class="metric-grid">
        <div class="metric">
            <div class="metric-value" style="color:var(--color-primary)">{total}</div>
            <div class="metric-label">AI systémů celkem</div>
        </div>
        <div class="metric">
            <div class="metric-value" style="color:var(--color-high)">{risk.get('high', 0)}</div>
            <div class="metric-label">Vysoké riziko</div>
        </div>
        <div class="metric">
            <div class="metric-value" style="color:var(--color-limited)">{risk.get('limited', 0)}</div>
            <div class="metric-label">Omezené riziko</div>
        </div>
    </div>
    """

    # Findings tabulka
    findings_rows = ""
    for f in findings:
        rl = f.get("risk_level", "minimal")
        findings_rows += f"""
        <tr>
            <td style="font-weight:600">{f.get('name', '?')}</td>
            <td>{f.get('category', '')}</td>
            <td>{_risk_badge(rl)}</td>
            <td style="font-size:12px;color:var(--color-muted)">{f.get('ai_act_article', '')}</td>
            <td style="font-size:12px">{f.get('action_required', '')}</td>
        </tr>"""

    findings_html = ""
    if findings_rows:
        findings_html = f"""
    <div class="glass-card">
        <h2>Nalezené AI systémy — automatický sken webu</h2>
        <p style="color:var(--color-muted);font-size:13px;margin-bottom:16px">
            Sken URL: <strong>{url}</strong>
        </p>
        <table>
            <thead><tr><th>Systém</th><th>Kategorie</th><th>Riziko</th><th>Článek AI Act</th><th>Požadovaná akce</th></tr></thead>
            <tbody>{findings_rows}</tbody>
        </table>
    </div>"""

    # Dotazník systémy
    q_html = ""
    if q_systems > 0:
        q_html = f"""
    <div class="glass-card">
        <h2>Interní AI systémy — z dotazníku</h2>
        <p>Na základě vyplněného dotazníku bylo identifikováno <strong>{q_systems} interních AI systémů</strong>,
        které automatický skener webu nedetekuje.</p>
    </div>"""

    # Doporučení
    recs_html = ""
    if recommendations:
        items = ""
        for r in recommendations:
            rl = r.get("risk_level", "minimal")
            items += f"""
            <div style="border-left:3px solid var(--color-{rl});padding-left:12px;margin-bottom:12px">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
                    {_risk_badge(rl)}
                    <strong style="font-size:13px">{r.get('tool_name', 'AI systém')}</strong>
                </div>
                <p style="font-size:13px;color:var(--color-muted)">{r.get('recommendation', '')}</p>
                <p style="font-size:11px;color:var(--color-muted)">{r.get('ai_act_article', '')}</p>
            </div>"""
        recs_html = f'<div class="glass-card"><h2>Doporučení ke compliance</h2>{items}</div>'

    # Deadline
    deadline_html = """
    <div class="highlight-box">
        <strong>Deadline:</strong> 2. srpna 2026 — od tohoto data se EU AI Act plně vztahuje na všechny
        AI systémy. Nesplnění může vést k pokutám až 35 mil. EUR nebo 7 % ročního obratu.
    </div>
    """

    body = f"""
    <div class="glass-card">
        <h2>Souhrnné hodnocení</h2>
        <p><strong>Firma:</strong> {company}</p>
        <p><strong>Analyzovaný web:</strong> {url}</p>
        <p><strong>Celkové riziko:</strong> {_risk_badge(overall)}</p>
    </div>
    {metrics_html}
    {deadline_html}
    {findings_html}
    {q_html}
    {recs_html}
    """

    return _wrap_page(
        f"AI Act Compliance Report — {company}",
        f"Komplexní analýza souladu s Nařízením EU 2024/1689",
        body,
    )


# ══════════════════════════════════════════════════════════════════════
# 2. TRANSPARENCY PAGE — pro web klienta
# ══════════════════════════════════════════════════════════════════════

def render_transparency_page(data: dict) -> str:
    """
    Transparenční stránka — klient ji vloží na svůj web (/ai-transparence).
    """
    company = data.get("company_name", "Naše firma")
    findings = data.get("findings", [])
    last_updated = data.get("last_updated", _now_str())

    items_html = ""
    for f in findings:
        purpose_map = {
            "chatbot": "Komunikace se zákazníky prostřednictvím inteligentního asistenta.",
            "analytics": "Analýza návštěvnosti a chování uživatelů pro zlepšení služeb.",
            "recommender": "Personalizované doporučení produktů a obsahu.",
            "content_gen": "Asistence při tvorbě obsahu na webu.",
        }
        purpose = purpose_map.get(f.get("category", ""), "Podpora provozu webových stránek.")
        rl = f.get("risk_level", "minimal")
        items_html += f"""
        <div class="glass-card">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                <h3 style="margin:0">{f.get('name', 'AI systém')}</h3>
                {_risk_badge(rl)}
            </div>
            <p style="color:var(--color-muted);font-size:13px"><strong>Účel:</strong> {purpose}</p>
            <p style="color:var(--color-muted);font-size:13px"><strong>Riziková kategorie dle AI Act:</strong> {rl}</p>
            <p style="color:var(--color-muted);font-size:13px"><strong>Relevantní článek:</strong> {f.get('ai_act_article', 'čl. 50')}</p>
        </div>"""

    body = f"""
    <div class="glass-card">
        <h2>Informace o využití umělé inteligence</h2>
        <p>V souladu s Nařízením Evropského parlamentu a Rady (EU) 2024/1689 (AI Act)
        informujeme návštěvníky našeho webu o systémech umělé inteligence,
        které používáme.</p>
        <p style="color:var(--color-muted);font-size:12px">Poslední aktualizace: {last_updated}</p>
    </div>

    <h2>Přehled AI systémů na tomto webu</h2>
    {items_html if items_html else '<p style="color:var(--color-muted)">Na tomto webu aktuálně nevyužíváme žádné systémy umělé inteligence spadající pod regulaci AI Act.</p>'}

    <div class="glass-card">
        <h2>Vaše práva</h2>
        <ul>
            <li>Máte právo vědět, že komunikujete se systémem umělé inteligence</li>
            <li>Máte právo na lidský kontakt — napište nám na email níže</li>
            <li>Máte právo podat stížnost u příslušného dozorového orgánu</li>
        </ul>
        <p style="margin-top:12px"><strong>Kontakt:</strong> {data.get('contact_email', 'info@firma.cz')}</p>
    </div>

    <div class="glass-card">
        <h2>O AI Act</h2>
        <p style="color:var(--color-muted);font-size:13px">
            Nařízení (EU) 2024/1689 — Akt o umělé inteligenci — je první komplexní právní
            úprava AI na světě. Stanoví pravidla pro vývoj, nasazení a používání AI systémů
            v Evropské unii. Plná účinnost od 2. srpna 2026.
        </p>
    </div>
    """

    return _wrap_page(
        f"Transparence AI — {company}",
        "Informace o využití umělé inteligence dle Nařízení EU 2024/1689",
        body,
    )


# ══════════════════════════════════════════════════════════════════════
# 3. ACTION PLAN — akční plán s checkboxy
# ══════════════════════════════════════════════════════════════════════

def render_action_plan(data: dict) -> str:
    """Akční plán — konkrétní kroky ke compliance s checkboxy."""
    company = data.get("company_name", "Firma")
    action_items = data.get("action_items", [])
    findings = data.get("findings", [])
    risk = data.get("risk_breakdown", {})

    # Automatické akční body
    auto_items = []

    # Vždy
    auto_items.append(("info", "Jmenovat odpovědnou osobu za AI compliance"))
    auto_items.append(("info", "Vytvořit interní registr AI systémů (viz dokument Registr AI)"))
    auto_items.append(("info", "Proškolit zaměstnance — AI literacy dle čl. 4 AI Act"))

    if risk.get("high", 0) > 0:
        auto_items.append(("high", "Provést posouzení shody (conformity assessment) pro vysoce rizikové systémy"))
        auto_items.append(("high", "Zavést systém řízení rizik dle čl. 9 AI Act"))
        auto_items.append(("high", "Zajistit lidský dohled dle čl. 14 AI Act"))
        auto_items.append(("high", "Registrovat vysoce rizikové systémy v EU databázi (čl. 49)"))

    if risk.get("limited", 0) > 0:
        auto_items.append(("limited", "Přidat transparenční oznámení na web (čl. 50)"))
        auto_items.append(("limited", "Vytvořit transparenční stránku /ai-transparence"))
        auto_items.append(("limited", "Nainstalovat AIshield widget pro automatické oznámení"))

    # Chatbot-specific
    chatbot_findings = [f for f in findings if f.get("category") == "chatbot"]
    if chatbot_findings:
        auto_items.append(("limited", "Přidat oznámení ke každému chatbotu: 'Komunikujete s umělou inteligencí'"))

    auto_items.append(("info", "Naplánovat pravidelný re-sken webu (měsíční monitoring)"))
    auto_items.append(("info", "Připravit DPIA pro AI systémy zpracovávající osobní údaje"))

    # Custom akční body z analýzy
    for item in action_items:
        rl = item.get("risk_level", "info")
        auto_items.append((rl, item.get("action", "")))

    # Render
    groups = {"high": [], "limited": [], "minimal": [], "info": []}
    for rl, text in auto_items:
        groups.get(rl, groups["info"]).append(text)

    items_html = ""
    group_labels = [
        ("high", "Vysoká priorita — vysoce rizikové systémy", "var(--color-high)"),
        ("limited", "Střední priorita — omezené riziko / transparentnost", "var(--color-limited)"),
        ("info", "Obecné kroky — organizační opatření", "var(--color-secondary)"),
    ]
    for key, label, color in group_labels:
        if not groups[key]:
            continue
        items_html += f'<h3 style="color:{color};margin-top:20px">{label}</h3>'
        for text in groups[key]:
            items_html += f"""
            <div class="checkbox-item">
                <div class="checkbox"></div>
                <div>
                    <p style="font-size:13px">{text}</p>
                </div>
            </div>"""

    body = f"""
    <div class="glass-card">
        <h2>Akční plán — AI Act Compliance</h2>
        <p><strong>Firma:</strong> {company}</p>
        <p><strong>Deadline:</strong> 2. srpna 2026</p>
        <p style="color:var(--color-muted);font-size:13px">
            Zbývá <strong>{_days_until_deadline()}</strong> dní do plné účinnosti AI Act.
        </p>
    </div>

    <div class="glass-card">
        {items_html}
    </div>

    <div class="highlight-box">
        <strong>Tip:</strong> Vytiskněte tento akční plán a odškrtávejte splněné body.
        Při auditu poslouží jako důkaz vaší snahy o compliance (documented effort).
    </div>
    """

    return _wrap_page(
        f"Akční plán — {company}",
        "Konkrétní kroky ke splnění EU AI Act do 2. 8. 2026",
        body,
    )


def _days_until_deadline() -> int:
    deadline = datetime(2026, 8, 2, tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    delta = deadline - now
    return max(0, delta.days)


# ══════════════════════════════════════════════════════════════════════
# 4. AI REGISTER — registr AI systémů
# ══════════════════════════════════════════════════════════════════════

def render_ai_register(data: dict) -> str:
    """Interní registr AI systémů firmy — povinný dle čl. 49."""
    company = data.get("company_name", "Firma")
    findings = data.get("findings", [])
    questionnaire_recs = data.get("recommendations", [])

    # Webové systémy
    web_rows = ""
    for i, f in enumerate(findings, 1):
        rl = f.get("risk_level", "minimal")
        web_rows += f"""
        <tr>
            <td>{i}</td>
            <td style="font-weight:600">{f.get('name', '?')}</td>
            <td>{f.get('category', '')}</td>
            <td>{_risk_badge(rl)}</td>
            <td style="font-size:12px">{f.get('ai_act_article', '')}</td>
            <td>Webové stránky</td>
            <td style="font-size:12px">Automatický sken</td>
        </tr>"""

    # Interní systémy z dotazníku
    internal_rows = ""
    for j, r in enumerate(questionnaire_recs, len(findings) + 1):
        rl = r.get("risk_level", "minimal")
        internal_rows += f"""
        <tr>
            <td>{j}</td>
            <td style="font-weight:600">{r.get('tool_name', 'AI systém')}</td>
            <td>—</td>
            <td>{_risk_badge(rl)}</td>
            <td style="font-size:12px">{r.get('ai_act_article', '')}</td>
            <td>Interní</td>
            <td style="font-size:12px">Dotazník</td>
        </tr>"""

    body = f"""
    <div class="glass-card">
        <h2>Registr AI systémů firmy</h2>
        <p><strong>Firma:</strong> {company}</p>
        <p style="color:var(--color-muted);font-size:13px">
            Tento dokument slouží jako interní evidence AI systémů dle čl. 49 Nařízení (EU) 2024/1689.
            Aktualizujte ho při každé změně — nasazení nového AI systému nebo vyřazení stávajícího.
        </p>
    </div>

    <div class="glass-card">
        <h3>A. AI systémy na webových stránkách</h3>
        <table>
            <thead><tr><th>#</th><th>Systém</th><th>Kategorie</th><th>Riziko</th><th>Článek AI Act</th><th>Nasazení</th><th>Zdroj</th></tr></thead>
            <tbody>{web_rows if web_rows else '<tr><td colspan="7" style="color:var(--color-muted)">Žádné AI systémy nebyly detekovány</td></tr>'}</tbody>
        </table>
    </div>

    <div class="glass-card">
        <h3>B. Interní AI systémy</h3>
        <table>
            <thead><tr><th>#</th><th>Systém</th><th>Kategorie</th><th>Riziko</th><th>Článek AI Act</th><th>Nasazení</th><th>Zdroj</th></tr></thead>
            <tbody>{internal_rows if internal_rows else '<tr><td colspan="7" style="color:var(--color-muted)">Žádné interní AI systémy nebyly deklarovány</td></tr>'}</tbody>
        </table>
    </div>

    <div class="glass-card">
        <h3>C. Odpovědná osoba</h3>
        <table>
            <tr><td style="width:200px;color:var(--color-muted)">Jméno a příjmení</td><td>.................................................</td></tr>
            <tr><td style="color:var(--color-muted)">Funkce</td><td>.................................................</td></tr>
            <tr><td style="color:var(--color-muted)">Email</td><td>.................................................</td></tr>
            <tr><td style="color:var(--color-muted)">Datum jmenování</td><td>.................................................</td></tr>
        </table>
    </div>

    <div class="highlight-box">
        Registr AI systémů je živý dokument. Aktualizujte ho při každé změně v používaných AI systémech.
        Pro vysoce rizikové systémy je registrace v EU databázi povinná (čl. 49 AI Act).
    </div>
    """

    return _wrap_page(
        f"Registr AI systémů — {company}",
        "Interní evidence dle čl. 49 Nařízení (EU) 2024/1689",
        body,
    )


# ══════════════════════════════════════════════════════════════════════
# 5. CHATBOT NOTICES — texty oznámení pro chatboty
# ══════════════════════════════════════════════════════════════════════

def render_chatbot_notices(data: dict) -> str:
    """Texty oznámení — klient je copy-paste vloží ke svým chatbotům."""
    company = data.get("company_name", "Firma")
    chatbots = [f for f in data.get("findings", []) if f.get("category") == "chatbot"]

    notices = [
        {
            "name": "Krátké oznámení (doporučeno)",
            "text": f"Komunikujete s umělou inteligencí. Pokud chcete hovořit s člověkem, napište nám na {data.get('contact_email', 'info@firma.cz')}.",
            "where": "Zobrazit v chatovacím okně před prvním automatickým pozdravem.",
        },
        {
            "name": "Rozšířené oznámení",
            "text": f"Tento chat využívá systém umělé inteligence pro asistenci zákazníkům. Odpovědi jsou generovány automaticky. Společnost {company} zajišťuje lidský dohled nad kvalitou odpovědí. Máte-li zájem o komunikaci s člověkem, napište prosím 'operátor' nebo nás kontaktujte na {data.get('contact_email', 'info@firma.cz')}.",
            "where": "Zobrazit v patičce chatovacího okna nebo jako úvodní zprávu.",
        },
        {
            "name": "Banner na webu",
            "text": "Na tomto webu využíváme umělou inteligenci pro zlepšení služeb. Více informací naleznete na stránce AI transparence.",
            "where": "Zobrazit jako lištu na stránce (cookie-bar style) nebo v patičce webu.",
        },
        {
            "name": "Kontaktní formulář s AI zpracováním",
            "text": "Váš dotaz bude nejprve zpracován systémem umělé inteligence pro rychlejší odpověď. Každou odpověď následně kontroluje náš tým.",
            "where": "Zobrazit u kontaktního formuláře, pokud AI třídí nebo odpovídá na dotazy.",
        },
    ]

    notices_html = ""
    for n in notices:
        notices_html += f"""
    <div class="glass-card">
        <h3>{n['name']}</h3>
        <div style="background:rgba(15,23,42,0.6);border:1px solid var(--color-border);border-radius:10px;padding:16px;margin:12px 0;font-family:monospace;font-size:13px;line-height:1.6;color:var(--color-text)">
            {n['text']}
        </div>
        <p style="font-size:12px;color:var(--color-muted)"><strong>Kde použít:</strong> {n['where']}</p>
    </div>"""

    chatbot_list = ""
    if chatbots:
        items = "".join(f"<li><strong>{c.get('name', '?')}</strong> — {c.get('action_required', 'přidat oznámení')}</li>" for c in chatbots)
        chatbot_list = f"""
    <div class="glass-card">
        <h2>Detekované chatboty na vašem webu</h2>
        <ul>{items}</ul>
    </div>"""

    body = f"""
    <div class="glass-card">
        <h2>Texty oznámení o umělé inteligenci</h2>
        <p>Dle čl. 50 odst. 1 AI Act musí být uživatel informován, že komunikuje se systémem
        umělé inteligence. Níže najdete připravené texty — stačí zkopírovat a vložit.</p>
    </div>
    {chatbot_list}
    <h2>Připravené texty k použití</h2>
    {notices_html}
    <div class="highlight-box">
        <strong>Tip:</strong> Texty můžete přizpůsobit svému tone-of-voice. Důležité je zachovat
        informaci o tom, že uživatel komunikuje s AI, a nabídnout možnost kontaktu s člověkem.
    </div>
    """

    return _wrap_page(
        f"Texty AI oznámení — {company}",
        "Připravené oznámení dle čl. 50 Nařízení (EU) 2024/1689",
        body,
    )


# ══════════════════════════════════════════════════════════════════════
# 6. AI POLICY — interní AI politika
# ══════════════════════════════════════════════════════════════════════

def render_ai_policy(data: dict) -> str:
    """Interní AI politika firmy — šablona k přizpůsobení."""
    company = data.get("company_name", "Firma")

    body = f"""
    <div class="glass-card">
        <h2>Interní politika používání umělé inteligence</h2>
        <p><strong>Firma:</strong> {company}</p>
        <p><strong>Platnost od:</strong> .................................................</p>
        <p><strong>Schválil/a:</strong> .................................................</p>
    </div>

    <div class="glass-card">
        <h2>1. Účel dokumentu</h2>
        <p>Tato politika stanoví pravidla pro používání systémů umělé inteligence (AI)
        ve společnosti {company}. Cílem je zajistit soulad s Nařízením (EU) 2024/1689
        (AI Act) a minimalizovat rizika spojená s nasazením AI.</p>
    </div>

    <div class="glass-card">
        <h2>2. Rozsah platnosti</h2>
        <p>Tato politika se vztahuje na:</p>
        <ul>
            <li>Všechny zaměstnance a externí spolupracovníky</li>
            <li>Všechny AI systémy používané interně i na veřejných platformách</li>
            <li>Vývoj, nasazení, provoz i vyřazení AI systémů</li>
        </ul>
    </div>

    <div class="glass-card">
        <h2>3. Povolené používání AI</h2>
        <ul>
            <li><strong>Chatboty a asistenti</strong> (ChatGPT, Claude, Gemini) — povoleno
            pro interní práci. ZAKÁZÁNO vkládat osobní údaje zákazníků, finanční data
            a obchodní tajemství.</li>
            <li><strong>AI pro kód</strong> (GitHub Copilot, Cursor) — povoleno.
            Veškerý AI-generovaný kód musí projít code review.</li>
            <li><strong>AI obsah</strong> (DALL-E, Midjourney, Jasper) — povoleno.
            Veřejně publikovaný AI obsah musí být označen dle čl. 50 odst. 4 AI Act.</li>
        </ul>
    </div>

    <div class="glass-card">
        <h2>4. Zakázané praktiky</h2>
        <p style="color:var(--color-high)">Následující je v souladu s čl. 5 AI Act přísně zakázáno:</p>
        <ul>
            <li>Sociální scoring zaměstnanců nebo zákazníků</li>
            <li>Podprahová manipulace rozhodování (dark patterns s AI)</li>
            <li>Biometrická identifikace v reálném čase na veřejných místech</li>
            <li>Rozpoznávání emocí zaměstnanců na pracovišti (mimo bezpečnost)</li>
            <li>Sběr biometrických dat z internetu pro trénování AI</li>
        </ul>
    </div>

    <div class="glass-card">
        <h2>5. Pravidla pro data</h2>
        <ul>
            <li>Do AI systémů třetích stran NEVKLÁDEJTE osobní údaje (jména, RČ, emaily zákazníků)</li>
            <li>Interní dokumenty smí být zpracovány AI pouze se souhlasem nadřízeného</li>
            <li>Ověřujte výstupy AI — nepoužívejte je bez kontroly jako finální verzi</li>
            <li>Uchovávejte záznamy o používání AI pro účely auditu</li>
        </ul>
    </div>

    <div class="glass-card">
        <h2>6. Odpovědnost a dohled</h2>
        <table>
            <tr><td style="width:200px;color:var(--color-muted)">Odpovědná osoba za AI</td><td>.................................................</td></tr>
            <tr><td style="color:var(--color-muted)">Kontakt</td><td>.................................................</td></tr>
            <tr><td style="color:var(--color-muted)">Frekvence revize politiky</td><td>Minimálně 1× ročně</td></tr>
            <tr><td style="color:var(--color-muted)">Další revize</td><td>.................................................</td></tr>
        </table>
    </div>

    <div class="glass-card">
        <h2>7. Povinnosti zaměstnanců</h2>
        <ul>
            <li>Absolvovat školení AI literacy do 3 měsíců od nástupu (čl. 4 AI Act)</li>
            <li>Hlásit nové AI nástroje odpovědné osobě PŘED jejich nasazením</li>
            <li>Neinstalovat AI nástroje na firemní zařízení bez schválení IT</li>
            <li>Při pochybnostech kontaktovat odpovědnou osobu za AI</li>
        </ul>
    </div>

    <div class="glass-card">
        <h2>8. Sankce</h2>
        <p>Porušení této politiky může vést k disciplinárním opatřením
        včetně ukončení pracovního poměru. Porušení AI Act může firmu vystavit
        pokutám až 35 mil. EUR nebo 7 % ročního obratu.</p>
    </div>

    <div class="section-divider"></div>
    <div class="glass-card">
        <h3>Podpisy</h3>
        <table>
            <tr><td style="width:50%;border-right:1px solid var(--color-border)">
                <p style="color:var(--color-muted);font-size:12px">Schválil/a (vedení)</p>
                <br><br>
                <p>.................................................</p>
                <p style="font-size:12px;color:var(--color-muted)">Jméno, funkce, datum</p>
            </td>
            <td style="padding-left:16px">
                <p style="color:var(--color-muted);font-size:12px">Odpovědná osoba za AI</p>
                <br><br>
                <p>.................................................</p>
                <p style="font-size:12px;color:var(--color-muted)">Jméno, funkce, datum</p>
            </td></tr>
        </table>
    </div>
    """

    return _wrap_page(
        f"Interní AI politika — {company}",
        "Pravidla používání umělé inteligence dle Nařízení (EU) 2024/1689",
        body,
    )


# ══════════════════════════════════════════════════════════════════════
# 7. TRAINING OUTLINE — osnova školení AI literacy
# ══════════════════════════════════════════════════════════════════════

def render_training_outline(data: dict) -> str:
    """Osnova školení AI literacy — povinné dle čl. 4 AI Act."""
    company = data.get("company_name", "Firma")

    body = f"""
    <div class="glass-card">
        <h2>Školení AI Literacy — osnova</h2>
        <p>Povinné školení zaměstnanců dle čl. 4 Nařízení (EU) 2024/1689.</p>
        <p style="color:var(--color-muted);font-size:13px">
            <strong>Rozsah:</strong> 2–3 hodiny &bull;
            <strong>Cílová skupina:</strong> Všichni zaměstnanci společnosti {company} &bull;
            <strong>Frekvence:</strong> Při nástupu + 1× ročně refresher
        </p>
    </div>

    <div class="glass-card">
        <h2>Modul 1 — Co je umělá inteligence (30 min)</h2>
        <ul>
            <li>Definice AI — co to je a co to není</li>
            <li>Typy AI: generativní AI, prediktivní modely, expertní systémy</li>
            <li>Příklady AI v každodenním životě (navigace, doporučení, chatboty)</li>
            <li>AI vs. automatizace — jaký je rozdíl?</li>
        </ul>
    </div>

    <div class="glass-card">
        <h2>Modul 2 — EU AI Act v kostce (45 min)</h2>
        <ul>
            <li>Proč EU reguluje AI — cíle nařízení</li>
            <li>4 kategorie rizik: nepřijatelné → vysoké → omezené → minimální</li>
            <li>Zakázané praktiky (čl. 5) — co NESMÍME dělat</li>
            <li>Povinnosti transparentnosti (čl. 50) — informování uživatelů</li>
            <li>Pokuty — až 35 mil. EUR nebo 7 % obratu</li>
            <li>Deadline: 2. srpna 2026</li>
        </ul>
    </div>

    <div class="glass-card">
        <h2>Modul 3 — AI v naší firmě (30 min)</h2>
        <ul>
            <li>Jaké AI systémy používáme (prezentace registru AI)</li>
            <li>Povolené vs. zakázané použití (interní AI politika)</li>
            <li>Pravidla pro vkládání dat do AI nástrojů</li>
            <li>Kdo je odpovědná osoba za AI ve firmě</li>
        </ul>
    </div>

    <div class="glass-card">
        <h2>Modul 4 — Bezpečné používání AI v praxi (30 min)</h2>
        <ul>
            <li>ChatGPT / Claude — jak správně (a bezpečně) používat</li>
            <li>Co do AI NIKDY nevkládat (osobní údaje, hesla, smlouvy)</li>
            <li>Ověřování výstupů AI — „trust but verify"</li>
            <li>Označování AI-generovaného obsahu</li>
            <li>Hlášení incidentů — komu a jak</li>
        </ul>
    </div>

    <div class="glass-card">
        <h2>Modul 5 — Test a certifikace (15 min)</h2>
        <ul>
            <li>Krátký test (10 otázek) — ověření znalostí</li>
            <li>Minimum pro úspěšné absolvování: 70 %</li>
            <li>Certifikát o absolvování školení (evidenční účely)</li>
        </ul>
    </div>

    <div class="section-divider"></div>

    <div class="glass-card">
        <h3>Evidence absolvování</h3>
        <table>
            <thead><tr><th>Jméno zaměstnance</th><th>Datum školení</th><th>Výsledek testu</th><th>Podpis</th></tr></thead>
            <tbody>
                <tr><td>&nbsp;</td><td></td><td></td><td></td></tr>
                <tr><td>&nbsp;</td><td></td><td></td><td></td></tr>
                <tr><td>&nbsp;</td><td></td><td></td><td></td></tr>
                <tr><td>&nbsp;</td><td></td><td></td><td></td></tr>
                <tr><td>&nbsp;</td><td></td><td></td><td></td></tr>
                <tr><td>&nbsp;</td><td></td><td></td><td></td></tr>
                <tr><td>&nbsp;</td><td></td><td></td><td></td></tr>
                <tr><td>&nbsp;</td><td></td><td></td><td></td></tr>
            </tbody>
        </table>
    </div>

    <div class="highlight-box">
        <strong>Důležité:</strong> Čl. 4 AI Act vyžaduje, aby poskytovatelé i provozovatelé AI systémů
        zajistili „dostatečnou úroveň AI gramotnosti" svých zaměstnanců. Toto školení slouží jako
        důkaz splnění této povinnosti. Uchovávejte evidenci minimálně 5 let.
    </div>
    """

    return _wrap_page(
        f"Školení AI Literacy — {company}",
        "Osnova povinného školení dle čl. 4 Nařízení (EU) 2024/1689",
        body,
    )


# ══════════════════════════════════════════════════════════════════════
# EXPORT — mapa všech šablon
# ══════════════════════════════════════════════════════════════════════

TEMPLATE_RENDERERS = {
    "compliance_report": render_compliance_report,
    "transparency_page": render_transparency_page,
    "action_plan": render_action_plan,
    "ai_register": render_ai_register,
    "chatbot_notices": render_chatbot_notices,
    "ai_policy": render_ai_policy,
    "training_outline": render_training_outline,
}

TEMPLATE_NAMES = {
    "compliance_report": "AI Act Compliance Report",
    "transparency_page": "Transparenční stránka",
    "action_plan": "Akční plán",
    "ai_register": "Registr AI systémů",
    "chatbot_notices": "Texty AI oznámení",
    "ai_policy": "Interní AI politika",
    "training_outline": "Školení AI Literacy",
}
