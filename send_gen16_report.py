"""
One-shot script: Send Gen16 report email from logs + M5 audit data.
Run on VPS: cd /opt/aishield && python3 send_gen16_report.py
"""
import asyncio
import json
import re
import os
import sys

sys.path.insert(0, "/opt/aishield")

# ── Parse gen16.log + gen16b.log ──
def parse_logs():
    """Extrahuje M2/M3 data z logů."""
    docs = {}  # doc_key → {eu_score, client_score, eu_findings, client_findings, eu_hodnoceni, ...}
    
    for logfile in ["/opt/aishield/gen16.log", "/opt/aishield/gen16b.log"]:
        if not os.path.exists(logfile):
            continue
        with open(logfile, "r") as f:
            content = f.read()
        
        # Parse M2 entries: [M2 EU Critic] doc_key: skóre=X, Y nálezů, COT=Z znaků, hodnocení=W
        for m in re.finditer(
            r'\[M2 EU Critic\] (\w+): skóre=(\d+), (\d+) nálezů, COT=(\d+) znaků, hodnocení=(\S+)',
            content
        ):
            dk, score, findings, cot, hodnoceni = m.groups()
            if dk not in docs:
                docs[dk] = {}
            docs[dk]["eu_score"] = int(score)
            docs[dk]["eu_findings_count"] = int(findings)
            docs[dk]["eu_hodnoceni"] = hodnoceni
            docs[dk]["eu_cot_chars"] = int(cot)
        
        # Parse M3 entries: [M3 Client Critic] doc_key: skóre=X, Y nálezů, COT=Z znaků, hodnocení=W
        for m in re.finditer(
            r'\[M3 Client Critic\] (\w+): skóre=(\d+), (\d+) nálezů, COT=(\d+) znaků, hodnocení=(\S+)',
            content
        ):
            dk, score, findings, cot, hodnoceni = m.groups()
            if dk not in docs:
                docs[dk] = {}
            docs[dk]["client_score"] = int(score)
            docs[dk]["client_findings_count"] = int(findings)
            docs[dk]["client_hodnoceni"] = hodnoceni
            docs[dk]["client_cot_chars"] = int(cot)
        
        # Parse document completion: DOKUMENT X HOTOV: Y znaků, $Z, W tokens, Ts
        for m in re.finditer(
            r'DOKUMENT (\d+) HOTOV: (\d+) znaků, \$([0-9.]+), (\d+) tokens, (\d+)s',
            content
        ):
            idx, chars, cost, tokens, time_s = m.groups()
        
        # Parse final scores: Skóre: EU=X/10, Klient=Y/10
        for m in re.finditer(
            r'Skóre: EU=(\d+)/10, Klient=(\d+)/10',
            content
        ):
            pass  # Already captured above
    
    return docs


def load_m5_data():
    """Načte M5 audit + rules data."""
    m5_data = {}
    
    # Load latest audit
    for v in [2, 1]:
        audit_path = f"/opt/aishield/prompt_versions/v{v}_audit.json"
        if os.path.exists(audit_path):
            with open(audit_path) as f:
                m5_data["audit"] = json.load(f)
            break
    
    # Load current rules
    rules_path = "/opt/aishield/prompt_versions/m5_rules.txt"
    if os.path.exists(rules_path):
        with open(rules_path) as f:
            m5_data["rules_text"] = f.read()
    
    # Load history
    history_path = "/opt/aishield/prompt_versions/history.json"
    if os.path.exists(history_path):
        with open(history_path) as f:
            m5_data["history"] = json.load(f)
    
    return m5_data


# ── Document name mapping ──
DOC_NAMES = {
    "compliance_report": "Compliance Report",
    "action_plan": "Akční plán",
    "ai_register": "Registr AI systémů",
    "training_outline": "Plán školení",
    "transparency_human_oversight": "Transparentnost a lidský dohled",
    "transparency_page": "Transparenční stránka (HTML)",
    "training_presentation": "Školící prezentace (PPTX)",
    "chatbot_notices": "Texty oznámení",
    "ai_policy": "Interní AI politika",
    "incident_response_plan": "Plán řízení incidentů",
    "dpia_template": "DPIA/FRIA",
    "vendor_checklist": "Dodavatelský checklist",
    "monitoring_plan": "Monitoring plán",
}


def build_gen16_report(docs_data, m5_data):
    """Sestaví textový report pro Gen16."""
    lines = []
    lines.append("=" * 70)
    lines.append("  AISHIELD — REPORT GENERACE 16 (gen_20260226_064455)")
    lines.append("  26.02.2026")
    lines.append("=" * 70)
    lines.append("")
    
    # ── SOUHRN ──
    eu_scores = [d.get("eu_score", 0) for d in docs_data.values() if "eu_score" in d]
    client_scores = [d.get("client_score", 0) for d in docs_data.values() if "client_score" in d]
    eu_avg = sum(eu_scores) / len(eu_scores) if eu_scores else 0
    client_avg = sum(client_scores) / len(client_scores) if client_scores else 0
    
    lines.append("SOUHRN")
    lines.append("-" * 40)
    lines.append(f"  Dokumenty:        13 (8 Part1 + 6 Part2, 1 VOP statická)")
    lines.append(f"  EU skóre (avg):   {eu_avg:.1f}/10")
    lines.append(f"  Klient skóre:     {client_avg:.1f}/10")
    lines.append(f"  Celkový průměr:   {(eu_avg + client_avg)/2:.1f}/10")
    lines.append(f"  Celkové náklady:  ~$3.64 (Part1: $2.14 + Part2: ~$1.50)")
    lines.append(f"  Celkový čas:      ~80 min (Part1: 46.6 + Part2: 33.4)")
    lines.append("")
    lines.append("  Part 1 (8 docs): CLAUDE API LIMIT hit na doc 5-10,")
    lines.append("    docs 11-13 prošly po obnovení limitu.")
    lines.append("  Part 2 (6 docs): Dogenerace chybějících — 6/6 OK.")
    lines.append("")
    
    # ── SKÓRE PO DOKUMENTECH ──
    lines.append("SKÓRE PO DOKUMENTECH")
    lines.append("-" * 70)
    lines.append(f"  {'Dokument':<42s} {'EU':>4s}  {'Klient':>6s}  {'EU nálezy':>10s}  {'Kl. nálezy':>10s}")
    lines.append(f"  {'─'*42}  {'──':>4s}  {'──────':>6s}  {'──────────':>10s}  {'──────────':>10s}")
    
    for dk in ["compliance_report", "action_plan", "ai_register", "training_outline",
               "transparency_human_oversight", "transparency_page", "training_presentation",
               "chatbot_notices", "ai_policy", "incident_response_plan", 
               "dpia_template", "vendor_checklist", "monitoring_plan"]:
        dn = DOC_NAMES.get(dk, dk)
        d = docs_data.get(dk, {})
        eu = d.get("eu_score", "-")
        cl = d.get("client_score", "-")
        eu_f = d.get("eu_findings_count", "-")
        cl_f = d.get("client_findings_count", "-")
        lines.append(f"  {dn:<42s} {str(eu):>4s}  {str(cl):>6s}  {str(eu_f):>10s}  {str(cl_f):>10s}")
    lines.append("")
    
    # ══════════════════════════════════════════════════════════
    # M2 — EU INSPEKTOR
    # ══════════════════════════════════════════════════════════
    lines.append("")
    lines.append("=" * 70)
    lines.append("  M2 — EU INSPEKTOR (Claude Sonnet 4): PŘEHLED VÝTEK")
    lines.append("=" * 70)
    lines.append("")
    lines.append("  POZN.: Detailní text nálezů nebyl v Gen16 ukládán do")
    lines.append("  logu (pouze skóre + počet). Od Gen17 bude automaticky")
    lines.append("  zachycen a odeslán emailem s plným textem nálezů.")
    lines.append("")
    
    for dk in sorted(docs_data.keys()):
        d = docs_data.get(dk, {})
        if "eu_score" not in d:
            continue
        dn = DOC_NAMES.get(dk, dk)
        eu = d["eu_score"]
        hodnoceni = d.get("eu_hodnoceni", "?")
        eu_f = d.get("eu_findings_count", 0)
        
        marker = "[!!!]" if eu <= 4 else "[!!]" if eu <= 5 else "[!]" if eu <= 6 else "[OK]"
        lines.append(f"  {marker} [{eu}/10] {dn}")
        lines.append(f"         Hodnocení: {hodnoceni}, {eu_f} nálezů")
        lines.append("")
    
    # Závěr z M5 analýzy (ta analyzovala M2 výstupy)
    audit = m5_data.get("audit", {})
    m5_resp = audit.get("m5_full_response", {})
    analyza = m5_resp.get("analyza", {})
    vzory = analyza.get("identifikovane_vzory", [])
    
    if vzory:
        lines.append("  VZORY IDENTIFIKOVANÉ M5 Z EU INSPEKCÍ:")
        lines.append("  " + "-" * 50)
        for i, vzor in enumerate(vzory, 1):
            pattern = vzor.get("vzor", "?")
            pocet = vzor.get("pocet_vyskytu", "?")
            priklady = vzor.get("priklady_dokumentu", [])
            lines.append(f"  {i}. {pattern}")
            lines.append(f"     Výskyt: {pocet}x | Dokumenty: {', '.join(priklady[:3])}")
            lines.append("")
    
    # ══════════════════════════════════════════════════════════
    # M3 — ZÁKAZNÍK
    # ══════════════════════════════════════════════════════════
    lines.append("")
    lines.append("=" * 70)
    lines.append("  M3 — ZÁKAZNÍK (Gemini): PŘEHLED VÝTEK")
    lines.append("=" * 70)
    lines.append("")
    
    for dk in sorted(docs_data.keys()):
        d = docs_data.get(dk, {})
        if "client_score" not in d:
            continue
        dn = DOC_NAMES.get(dk, dk)
        cl = d["client_score"]
        hodnoceni = d.get("client_hodnoceni", "?")
        cl_f = d.get("client_findings_count", 0)
        
        marker = "[!!!]" if cl <= 4 else "[!!]" if cl <= 5 else "[!]" if cl <= 6 else "[OK]"
        lines.append(f"  {marker} [{cl}/10] {dn}")
        lines.append(f"         Hodnocení: {hodnoceni}, {cl_f} nálezů")
        lines.append("")
    
    # Nejhůř hodnocené
    worst_client = sorted(
        [(dk, d.get("client_score", 10)) for dk, d in docs_data.items() if "client_score" in d],
        key=lambda x: x[1]
    )[:3]
    if worst_client:
        lines.append("  NEJHŮŘE HODNOCENÉ ZÁKAZNÍKEM:")
        for dk, score in worst_client:
            lines.append(f"    - {DOC_NAMES.get(dk, dk)}: {score}/10")
        lines.append("")
    
    # ══════════════════════════════════════════════════════════
    # M5 — SELF-IMPROVEMENT
    # ══════════════════════════════════════════════════════════
    lines.append("")
    lines.append("=" * 70)
    lines.append("  M5 — SELF-IMPROVEMENT: CO SE NAUČIL A ZAPSAL DO M1")
    lines.append("=" * 70)
    lines.append("")
    
    history = m5_data.get("history", [])
    if history:
        latest = history[-1]
        lines.append(f"  Verze pravidel: v{latest.get('version', '?')}")
        lines.append(f"  Generace:       {latest.get('generation_id', '?')}")
        lines.append(f"  Nových pravidel: {latest.get('rules_added', '?')}")
        lines.append(f"  EU průměr:      {latest.get('eu_avg', '?')}")
        lines.append(f"  Klient průměr:  {latest.get('client_avg', '?')}")
        lines.append(f"  Konvergováno:   {'ANO' if latest.get('converged') else 'NE'}")
        lines.append(f"  Náklady M5:     ${latest.get('cost_usd', 0)}")
        lines.append("")
        
        rules = latest.get("rules", [])
        reasons = latest.get("reasons", [])
        if rules:
            lines.append("  NOVÁ PRAVIDLA ZAPSANÁ ZPĚT DO M1:")
            lines.append("  " + "=" * 50)
            for i, rule in enumerate(rules):
                lines.append("")
                lines.append(f"  PRAVIDLO #{i+1}:")
                # Wrap long text
                words = rule.split()
                line = "    "
                for w in words:
                    if len(line) + len(w) + 1 > 68:
                        lines.append(line)
                        line = "    " + w
                    else:
                        line += (" " if len(line) > 4 else "") + w
                if line.strip():
                    lines.append(line)
                
                if i < len(reasons) and reasons[i]:
                    lines.append("")
                    lines.append(f"  DŮVOD:")
                    words = reasons[i].split()
                    line = "    "
                    for w in words:
                        if len(line) + len(w) + 1 > 68:
                            lines.append(line)
                            line = "    " + w
                        else:
                            line += (" " if len(line) > 4 else "") + w
                    if line.strip():
                        lines.append(line)
                lines.append("")
    
    # M5 komentář
    doporuceni = m5_resp.get("doporuceni", {})
    komentar = doporuceni.get("komentar", "")
    if komentar:
        lines.append("")
        lines.append("  KOMENTÁŘ M5 (Claude Opus 4.6):")
        lines.append("  " + "-" * 50)
        # Word wrap
        words = komentar.split()
        line = "  "
        for w in words:
            if len(line) + len(w) + 1 > 68:
                lines.append(line)
                line = "  " + w
            else:
                line += (" " if len(line) > 2 else "") + w
        if line.strip():
            lines.append(line)
        lines.append("")
    
    # ── Current M5 rules file ──
    rules_text = m5_data.get("rules_text", "")
    if rules_text:
        lines.append("")
        lines.append("  AKTUÁLNÍ M5_RULES.TXT (kompletní soubor):")
        lines.append("  " + "-" * 50)
        for rl in rules_text.split("\n"):
            lines.append(f"  {rl}")
        lines.append("")
    
    # ── CO SE ZMĚNÍ V DALŠÍ GENERACI ──
    lines.append("")
    lines.append("=" * 70)
    lines.append("  CO SE ZMĚNÍ V GEN17")
    lines.append("=" * 70)
    lines.append("")
    lines.append("  1. M5 pravidla v2 budou automaticky vložena do M1 promptu")
    lines.append("  2. Nový auto-report modul bude odesílat plné M2/M3 nálezy")
    lines.append("  3. M5 pravidla zdvojnásobila objem (2077 -> 4158 znaků)")
    lines.append("     Part2 už běžela s novými pravidly — efekt viditelný")
    lines.append("")
    
    # ── Patička ──
    lines.append("-" * 70)
    lines.append("  Automaticky generováno | AIshield Pipeline v3")
    lines.append("  Od Gen17 budou v reportu plné texty M2/M3 nálezů.")
    lines.append("-" * 70)
    
    return "\n".join(lines)


async def main():
    print("Parsování logů...")
    docs_data = parse_logs()
    print(f"  Nalezeno {len(docs_data)} dokumentů s M2/M3 daty")
    
    print("Načítání M5 dat...")
    m5_data = load_m5_data()
    print(f"  Audit: {'OK' if 'audit' in m5_data else 'MISSING'}")
    print(f"  Rules: {len(m5_data.get('rules_text', ''))} znaků")
    
    print("Sestavování reportu...")
    report_text = build_gen16_report(docs_data, m5_data)
    
    # Save to file
    with open("/opt/aishield/gen16_report.txt", "w") as f:
        f.write(report_text)
    print(f"  Report uložen: /opt/aishield/gen16_report.txt ({len(report_text)} znaků)")
    
    # Build HTML
    import html as html_mod
    escaped = html_mod.escape(report_text)
    html_report = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: 'Courier New', monospace; font-size: 13px; line-height: 1.5; background: #f5f5f5; padding: 20px;">
<pre style="white-space: pre-wrap; word-wrap: break-word; background: #fff; padding: 20px; border-radius: 8px; border: 1px solid #ddd; max-width: 800px; margin: 0 auto;">
{escaped}
</pre>
</body>
</html>"""
    
    # Send via Resend
    print("Odesílání emailu...")
    from backend.outbound.email_engine import send_email
    result = await send_email(
        to="bc.pospa@gmail.com",
        subject="[AIshield] Report Generace 16 — M2/M3/M5 výstupy",
        html=html_report,
        from_email="info@aishield.cz",
        from_name="AIshield Pipeline",
    )
    
    resend_id = result.get("id", "?")
    status = result.get("status", "?")
    print(f"  Email odeslán! Resend ID: {resend_id}, Status: {status}")
    print(f"\nHotovo!")


if __name__ == "__main__":
    asyncio.run(main())
