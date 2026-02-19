"""
AIshield.cz — 24h Hloubkový Scan (Deep Scan)
Opakované skenování webu ze 7 zemí přes rezidenční proxy
s rotací user-agentů a zařízení po dobu 24 hodin.

Spouští se automaticky po dokončení rychlého scanu.
Po dokončení pošle výsledky emailem.
"""

import asyncio
import logging
import random
from datetime import datetime, timezone

from backend.database import get_supabase
from backend.scanner.web_scanner import WebScanner, ScannedPage
from backend.scanner.detector import AIDetector, DetectedAI
from backend.scanner.classifier import AIClassifier

logger = logging.getLogger(__name__)

# Geolokace — kopie z WebScanner pro přímý přístup
GEO_COUNTRIES = WebScanner.GEO_COUNTRIES

# ── Konfigurace ──
DEEP_SCAN_ROUNDS = 6          # Počet kol skenování
ROUND_INTERVAL_SECONDS = 5 * 60    # ⚡ TESTOVACÍ REŽIM: 5 min mezi koly (produkce: 4 * 3600)
COUNTRIES_PER_ROUND = 4       # Zemí na kolo (rotace)
DEVICE_TYPES = ["desktop", "mobile", "random"]


async def _is_cancelled(supabase, scan_id: str) -> bool:
    """Zkontroluje, zda byl deep scan zrušen (status = 'cancelled')."""
    try:
        res = supabase.table("scans").select("deep_scan_status").eq("id", scan_id).limit(1).execute()
        if res.data and res.data[0].get("deep_scan_status") == "cancelled":
            return True
    except Exception:
        pass
    return False


async def deep_scan_job(ctx: dict, scan_id: str, url: str, company_id: str):
    """
    24h hloubkový scan — ARQ job.
    Spouští se po quick scanu. Provádí 6 kol po 4 hodinách,
    každé kolo skenuje ze 4 zemí (desktop + mobile).
    Po dokončení agreguje výsledky a pošle email.
    """
    supabase = get_supabase()
    now = datetime.now(timezone.utc).isoformat()

    logger.info(f"[DeepScan] START: scan={scan_id}, url={url}")

    # Označit deep scan jako running
    supabase.table("scans").update({
        "deep_scan_status": "running",
        "deep_scan_started_at": now,
    }).eq("id", scan_id).execute()

    all_findings: dict[str, dict] = {}  # name -> finding info (deduplikace)
    all_trackers: dict[str, dict] = {}  # tracker name -> tracker info (deduplikace)
    countries_scanned: list[str] = []
    rounds_completed = 0
    total_scans_done = 0
    errors: list[str] = []

    try:
        # Zamíchat země pro rovnoměrné pokrytí
        shuffled_countries = list(GEO_COUNTRIES)
        random.shuffle(shuffled_countries)

        for round_num in range(DEEP_SCAN_ROUNDS):
            # ── Kontrola zrušení před každým kolem ──
            if await _is_cancelled(supabase, scan_id):
                logger.info(f"[DeepScan] ZRUŠENO adminem před kolem {round_num + 1}")
                finished = datetime.now(timezone.utc).isoformat()
                supabase.table("scans").update({
                    "deep_scan_finished_at": finished,
                    "deep_scan_total_findings": len(all_findings),
                    "geo_countries_scanned": countries_scanned,
                }).eq("id", scan_id).execute()
                return {
                    "status": "cancelled",
                    "rounds_completed": rounds_completed,
                    "scans": total_scans_done,
                    "countries": countries_scanned,
                }

            logger.info(f"[DeepScan] Kolo {round_num + 1}/{DEEP_SCAN_ROUNDS}")

            # Vybrat země pro toto kolo (rotující)
            start_idx = (round_num * COUNTRIES_PER_ROUND) % len(shuffled_countries)
            round_countries = []
            for i in range(COUNTRIES_PER_ROUND):
                idx = (start_idx + i) % len(shuffled_countries)
                round_countries.append(shuffled_countries[idx])

            # Skenovat z každé země (střídáme desktop/mobile)
            for i, country in enumerate(round_countries):
                # ── Kontrola zrušení před každým skenem ──
                if await _is_cancelled(supabase, scan_id):
                    logger.info(f"[DeepScan] ZRUŠENO adminem v kole {round_num + 1}, scan {i + 1}")
                    finished = datetime.now(timezone.utc).isoformat()
                    supabase.table("scans").update({
                        "deep_scan_finished_at": finished,
                        "deep_scan_total_findings": len(all_findings),
                        "geo_countries_scanned": countries_scanned,
                    }).eq("id", scan_id).execute()
                    return {
                        "status": "cancelled",
                        "rounds_completed": rounds_completed,
                        "scans": total_scans_done,
                        "countries": countries_scanned,
                    }

                device = DEVICE_TYPES[i % len(DEVICE_TYPES)]
                try:
                    logger.info(
                        f"[DeepScan] Scan {total_scans_done + 1}: "
                        f"country={country}, device={device}"
                    )

                    scanner = WebScanner(
                        use_proxy=True,
                        proxy_country=country,
                        device_type=device,
                        timeout_ms=45_000,
                        wait_after_load_ms=5_000,
                    )
                    page: ScannedPage = await scanner.scan(url)

                    if page.error:
                        logger.warning(
                            f"[DeepScan] Scan error ({country}/{device}): {page.error}"
                        )
                        errors.append(f"{country}/{device}: {page.error}")
                        continue

                    # Detekce AI systémů
                    detector = AIDetector()
                    findings: list[DetectedAI] = detector.detect(page)

                    # Detekce non-AI trackerů
                    round_trackers = detector.detect_trackers(page)
                    for t in round_trackers:
                        tkey = t["name"].lower().strip()
                        if tkey not in all_trackers:
                            all_trackers[tkey] = t

                    for f in findings:
                        key = f.name.lower().strip()
                        if key not in all_findings:
                            all_findings[key] = {
                                "name": f.name,
                                "category": f.category,
                                "matched_signatures": list(f.matched_signatures[:5]),
                                "evidence": list(f.evidence[:3]),
                                "found_in_countries": [country],
                                "found_on_devices": [device],
                                "first_seen_round": round_num + 1,
                            }
                        else:
                            existing = all_findings[key]
                            if country not in existing["found_in_countries"]:
                                existing["found_in_countries"].append(country)
                            if device not in existing["found_on_devices"]:
                                existing["found_on_devices"].append(device)

                    if country not in countries_scanned:
                        countries_scanned.append(country)
                    total_scans_done += 1

                    logger.info(
                        f"[DeepScan] {country}/{device}: "
                        f"{len(findings)} findings (celkem unikátních: {len(all_findings)})"
                    )

                except Exception as scan_err:
                    logger.error(f"[DeepScan] Exception ({country}/{device}): {scan_err}")
                    errors.append(f"{country}/{device}: {str(scan_err)[:100]}")

                # Pauza mezi scany (30-90s) — šetrnější k proxy
                if total_scans_done < DEEP_SCAN_ROUNDS * COUNTRIES_PER_ROUND:
                    delay = random.randint(30, 90)
                    await asyncio.sleep(delay)

            rounds_completed += 1

            # Průběžná aktualizace v DB
            supabase.table("scans").update({
                "deep_scan_total_findings": len(all_findings),
                "geo_countries_scanned": countries_scanned,
            }).eq("id", scan_id).execute()

            # Pauza mezi koly (4 hodiny, nebo kratší pro poslední kolo)
            if round_num < DEEP_SCAN_ROUNDS - 1:
                jitter = random.randint(-300, 300)  # ±5min jitter
                wait = ROUND_INTERVAL_SECONDS + jitter
                logger.info(f"[DeepScan] Čekám {wait // 3600}h {(wait % 3600) // 60}min do dalšího kola")
                # Spát po 60s kvůli možnosti zrušení
                slept = 0
                while slept < wait:
                    chunk = min(60, wait - slept)
                    await asyncio.sleep(chunk)
                    slept += chunk
                    # Kontrola zrušení každých 60s během čekání
                    if slept % 300 < 61 and await _is_cancelled(supabase, scan_id):
                        logger.info(f"[DeepScan] ZRUŠENO adminem během čekání po kole {round_num + 1}")
                        finished = datetime.now(timezone.utc).isoformat()
                        supabase.table("scans").update({
                            "deep_scan_finished_at": finished,
                            "deep_scan_total_findings": len(all_findings),
                            "geo_countries_scanned": countries_scanned,
                        }).eq("id", scan_id).execute()
                        return {
                            "status": "cancelled",
                            "rounds_completed": rounds_completed,
                            "scans": total_scans_done,
                            "countries": countries_scanned,
                        }

        # ── Klasifikace všech nálezů přes Claude ──
        logger.info(f"[DeepScan] Klasifikuji {len(all_findings)} nálezů přes Claude")

        # Převést na DetectedAI objekty pro classifier
        detected_list: list[DetectedAI] = []
        for key, info in all_findings.items():
            detected_list.append(DetectedAI(
                name=info["name"],
                category=info["category"],
                matched_signatures=info["matched_signatures"],
                evidence=info["evidence"],
                confidence=0.8,
            ))

        classifier = AIClassifier()
        classified = await classifier.classify(url, detected_list)

        deployed = [c for c in classified if c.deployed]
        not_deployed = [c for c in classified if not c.deployed]

        # Safety net
        NON_AI_TOOLS = {"google tag manager", "google analytics 4", "seznam retargeting", "heureka"}
        auto_fp = [c for c in deployed if c.name.lower() in NON_AI_TOOLS and c.risk_level == "minimal"]
        for c in auto_fp:
            c.deployed = False
        deployed = [c for c in deployed if c not in auto_fp]
        not_deployed.extend(auto_fp)

        # ── Uložit deep scan findings (jako child scany) ──
        for cf in deployed:
            finding_info = all_findings.get(cf.name.lower().strip(), {})
            source_label = f"deep_scan_{'_'.join(finding_info.get('found_in_countries', ['unknown']))}"

            supabase.table("findings").insert({
                "scan_id": scan_id,
                "company_id": company_id,
                "name": cf.name,
                "category": cf.category,
                "signature_matched": ", ".join(cf.matched_signatures[:5]),
                "risk_level": cf.risk_level,
                "ai_act_article": cf.ai_act_article,
                "action_required": cf.action_required,
                "ai_classification_text": cf.description_cs,
                "evidence_html": "\n".join(cf.evidence[:5]),
                "source": source_label[:50],
                "confirmed_by_client": "confirmed" if classifier.enabled else "unknown",
            }).execute()

        # ── Aktualizovat scan ──
        finished = datetime.now(timezone.utc).isoformat()

        # Celkový počet unikátních findings (quick + deep dohromady)
        all_findings_res = supabase.table("findings").select("name").eq(
            "scan_id", scan_id
        ).neq("source", "ai_classified_fp").neq("risk_level", "none").execute()

        unique_names = set()
        for f in (all_findings_res.data or []):
            unique_names.add(f["name"].lower().strip())
        total_unique = len(unique_names)

        # Uložit trackery jako JSON
        import json as _json
        trackers_list = list(all_trackers.values())

        supabase.table("scans").update({
            "deep_scan_status": "done",
            "deep_scan_finished_at": finished,
            "deep_scan_total_findings": total_unique,
            "total_findings": total_unique,  # aktualizovat i celkový počet
            "geo_countries_scanned": countries_scanned,
            "trackers_json": _json.dumps(trackers_list, ensure_ascii=False) if trackers_list else None,
        }).eq("id", scan_id).execute()

        logger.info(
            f"[DeepScan] HOTOVO: {total_unique} unikátních systémů, "
            f"{rounds_completed} kol, {total_scans_done} scanů, "
            f"{len(countries_scanned)} zemí"
        )

        # ── Odeslat email s výsledky ──
        try:
            company = supabase.table("companies").select("name, email").eq(
                "id", company_id
            ).limit(1).execute()

            if company.data and company.data[0].get("email"):
                email_to = company.data[0]["email"]
                company_name = company.data[0].get("name", url)

                from backend.outbound.email_engine import send_email
                html = _build_deep_scan_email(
                    company_name=company_name,
                    url=url,
                    total_findings=total_unique,
                    findings=deployed,
                    countries_scanned=countries_scanned,
                    total_scans=total_scans_done,
                    scan_id=scan_id,
                    trackers=list(all_trackers.values()),
                )
                await send_email(
                    to=email_to,
                    subject=f"✅ 24h hloubkový scan dokončen — {total_unique} AI systémů nalezeno",
                    html=html,
                    from_email="info@aishield.cz",
                    from_name="AIshield.cz",
                )
                logger.info(f"[DeepScan] Email odeslán na {email_to}")
            else:
                logger.warning(f"[DeepScan] Žádný email pro company {company_id}")
        except Exception as email_err:
            logger.error(f"[DeepScan] Chyba odesílání emailu: {email_err}")

        return {
            "status": "done",
            "total_unique_findings": total_unique,
            "deployed": len(deployed),
            "false_positives": len(not_deployed),
            "rounds": rounds_completed,
            "scans": total_scans_done,
            "countries": countries_scanned,
        }

    except Exception as e:
        logger.error(f"[DeepScan] FATÁLNÍ CHYBA: {e}", exc_info=True)
        finished = datetime.now(timezone.utc).isoformat()
        supabase.table("scans").update({
            "deep_scan_status": "error",
            "deep_scan_finished_at": finished,
        }).eq("id", scan_id).execute()
        raise


# ═══════════════════════════════════════════════════════════════
# Email šablona — 24h scan dokončen
# ═══════════════════════════════════════════════════════════════

_COUNTRY_FLAGS = {
    "cz": "🇨🇿", "gb": "🇬🇧", "us": "🇺🇸", "br": "🇧🇷",
    "jp": "🇯🇵", "za": "🇿🇦", "au": "🇦🇺",
}

_COUNTRY_CITIES = {
    "cz": "Praha", "gb": "Londýn", "us": "New York", "br": "São Paulo",
    "jp": "Tokio", "za": "Johannesburg", "au": "Sydney",
}

_COUNTRY_NAMES = {
    "cz": "Česko", "gb": "Velká Británie", "us": "USA", "br": "Brazílie",
    "jp": "Japonsko", "za": "Jihoafrická republika", "au": "Austrálie",
}


def _build_deep_scan_email(
    company_name: str,
    url: str,
    total_findings: int,
    findings: list,
    countries_scanned: list[str],
    total_scans: int,
    scan_id: str,
    trackers: list[dict] | None = None,
) -> str:
    """Vytvoří HTML email s výsledky 24h hloubkového scanu."""

    # Vlajky skenovaných zemí s městy
    flags_html = ""
    for c in countries_scanned:
        cl = c.lower()
        flag = _COUNTRY_FLAGS.get(cl, '🌐')
        city = _COUNTRY_CITIES.get(cl, '')
        country_name = _COUNTRY_NAMES.get(cl, c.upper())
        flags_html += (
            f"<div style='display:inline-block;text-align:center;margin:4px 8px;'>"
            f"<span style='font-size:24px;'>{flag}</span><br>"
            f"<span style='font-size:11px;color:#e2e8f0;font-weight:600;'>{city}</span><br>"
            f"<span style='font-size:10px;color:#64748b;'>{country_name}</span>"
            f"</div>"
        )

    # Tabulka nalezených systémů
    findings_rows = ""
    risk_colors = {
        "high": "#ef4444",
        "limited": "#f59e0b",
        "minimal": "#22c55e",
    }
    for f in findings:
        risk = getattr(f, "risk_level", "limited")
        color = risk_colors.get(risk, "#f59e0b")
        risk_label = {"high": "Vysoké", "limited": "Omezené", "minimal": "Minimální"}.get(risk, risk)
        name = getattr(f, "name", "N/A")
        category = getattr(f, "category", "")
        desc = getattr(f, "description_cs", "")[:120]

        findings_rows += f"""
        <tr>
            <td style="padding:12px 16px;border-bottom:1px solid #1e293b;color:#f1f5f9;font-weight:600;">{name}</td>
            <td style="padding:12px 16px;border-bottom:1px solid #1e293b;color:#94a3b8;font-size:13px;">{category}</td>
            <td style="padding:12px 16px;border-bottom:1px solid #1e293b;">
                <span style="display:inline-block;padding:2px 10px;border-radius:12px;font-size:12px;font-weight:600;
                    background:{color}22;color:{color};border:1px solid {color}44;">{risk_label}</span>
            </td>
        </tr>"""

    # Číslo: "byl nalezen 1 AI systém" / "byly nalezeny 2-4 AI systémy" / "bylo nalezeno 5+ AI systémů"
    if total_findings == 1:
        count_text = "byl nalezen <strong>1 AI systém</strong>"
    elif 2 <= total_findings <= 4:
        count_text = f"byly nalezeny <strong>{total_findings} AI systémy</strong>"
    else:
        count_text = f"bylo nalezeno <strong>{total_findings} AI systémů</strong>"

    dashboard_url = f"https://aishield.cz/dashboard"
    dotaznik_url = f"https://aishield.cz/dotaznik"
    pricing_url = f"https://aishield.cz/pricing"

    # Sekce non-AI trackerů
    trackers_html = ""
    if trackers:
        tracker_items = ""
        for t in trackers:
            icon = t.get("icon", "📊")
            name = t.get("name", "?")
            desc = t.get("description_cs", "")[:80]
            cat = t.get("category", "")
            tracker_items += (
                f"<tr>"
                f"<td style='padding:8px 16px;border-bottom:1px solid #1e293b;color:#f1f5f9;font-size:14px;'>"
                f"<span style='font-size:16px;margin-right:6px;'>{icon}</span> {name}</td>"
                f"<td style='padding:8px 16px;border-bottom:1px solid #1e293b;color:#94a3b8;font-size:12px;'>{cat}</td>"
                f"<td style='padding:8px 16px;border-bottom:1px solid #1e293b;color:#64748b;font-size:12px;'>{desc}</td>"
                f"</tr>"
            )
        trackers_html = f"""
    <tr>
        <td style="padding:0 40px 24px;">
            <div style="background:#14532d11;border:1px solid #22c55e33;border-radius:12px;padding:16px 20px 8px;">
                <p style="color:#86efac;font-size:14px;margin:0 0 4px;font-weight:600;">
                    📊 Dalších {len(trackers)} sledovacích systémů (non-AI)
                </p>
                <p style="color:#64748b;font-size:12px;margin:0 0 12px;">
                    Tyto technologie nejsou umělou inteligencí a nespadají pod AI Act.
                    Zobrazujeme je pro úplnost — aby náš scan pokryl vše.
                </p>
                <table width="100%" cellpadding="0" cellspacing="0" style="background:#0f172a;border-radius:8px;overflow:hidden;">
                    <tr style="background:#1e293b;">
                        <th style="padding:8px 16px;text-align:left;color:#94a3b8;font-size:11px;font-weight:600;text-transform:uppercase;">Systém</th>
                        <th style="padding:8px 16px;text-align:left;color:#94a3b8;font-size:11px;font-weight:600;text-transform:uppercase;">Typ</th>
                        <th style="padding:8px 16px;text-align:left;color:#94a3b8;font-size:11px;font-weight:600;text-transform:uppercase;">Popis</th>
                    </tr>
                    {tracker_items}
                </table>
            </div>
        </td>
    </tr>
    """

    return f"""<!DOCTYPE html>
<html lang="cs">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0f172a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">

<!-- Wrapper -->
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0f172a;">
<tr><td align="center" style="padding:32px 16px;">

<!-- Card -->
<table width="600" cellpadding="0" cellspacing="0" style="background:#1e293b;border-radius:16px;overflow:hidden;border:1px solid #334155;">

    <!-- Header gradient -->
    <tr>
        <td style="background:linear-gradient(135deg,#7c3aed 0%,#06b6d4 100%);padding:32px 40px;text-align:center;">
            <img src="https://aishield.cz/logo-white.png" alt="AIshield" width="140" style="display:block;margin:0 auto 12px;">
            <h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:700;letter-spacing:-0.3px;">
                ✅ 24h hloubkový scan dokončen
            </h1>
        </td>
    </tr>

    <!-- Big number -->
    <tr>
        <td style="padding:32px 40px 16px;text-align:center;">
            <div style="font-size:56px;font-weight:800;color:#fbbf24;line-height:1;">{total_findings}</div>
            <p style="margin:8px 0 0;color:#94a3b8;font-size:15px;">
                AI {f"systém nalezen" if total_findings == 1 else f"systémů nalezeno"} na vašem webu
            </p>
        </td>
    </tr>

    <!-- Scan stats -->
    <tr>
        <td style="padding:0 40px 24px;">
            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="padding:12px;text-align:center;background:#0f172a;border-radius:12px 0 0 12px;">
                        <div style="font-size:20px;font-weight:700;color:#7c3aed;">{total_scans}</div>
                        <div style="font-size:11px;color:#64748b;margin-top:2px;">skenů provedeno</div>
                    </td>
                    <td style="padding:12px;text-align:center;background:#0f172a;">
                        <div style="font-size:20px;font-weight:700;color:#06b6d4;">{len(countries_scanned)}</div>
                        <div style="font-size:11px;color:#64748b;margin-top:2px;">zemí pokryto</div>
                    </td>
                    <td style="padding:12px;text-align:center;background:#0f172a;border-radius:0 12px 12px 0;">
                        <div style="font-size:20px;font-weight:700;color:#22c55e;">24h</div>
                        <div style="font-size:11px;color:#64748b;margin-top:2px;">doba skenování</div>
                    </td>
                </tr>
            </table>
        </td>
    </tr>

    <!-- Countries with cities -->
    <tr>
        <td style="padding:0 40px 24px;text-align:center;">
            <p style="color:#64748b;font-size:12px;margin:0 0 12px;">Skenováno z 6 kontinentů:</p>
            <div style="background:#0f172a;border-radius:12px;padding:16px;border:1px solid #334155;">
                {flags_html}
            </div>
        </td>
    </tr>

    <!-- Main message -->
    <tr>
        <td style="padding:0 40px 24px;">
            <div style="background:#0f172a;border-radius:12px;padding:20px 24px;border:1px solid #334155;">
                <p style="color:#e2e8f0;font-size:15px;line-height:1.6;margin:0;">
                    Dobrý den,<br><br>
                    váš <strong style="color:#7c3aed;">24hodinový hloubkový scan</strong> webu
                    <strong style="color:#06b6d4;">{url}</strong> byl úspěšně dokončen.
                    Celkem {count_text}, které spadají pod
                    <strong style="color:#fbbf24;">zákon EU o umělé inteligenci (AI Act)</strong>
                    a bohužel nemají na vašem webu patřičné označení.
                </p>
            </div>
        </td>
    </tr>

    <!-- Findings table -->
    {"" if not findings else f'''
    <tr>
        <td style="padding:0 40px 24px;">
            <h3 style="color:#f1f5f9;font-size:16px;margin:0 0 12px;">Nalezené AI systémy:</h3>
            <table width="100%" cellpadding="0" cellspacing="0" style="background:#0f172a;border-radius:12px;overflow:hidden;border:1px solid #334155;">
                <tr style="background:#1e293b;">
                    <th style="padding:10px 16px;text-align:left;color:#94a3b8;font-size:12px;font-weight:600;text-transform:uppercase;">Systém</th>
                    <th style="padding:10px 16px;text-align:left;color:#94a3b8;font-size:12px;font-weight:600;text-transform:uppercase;">Kategorie</th>
                    <th style="padding:10px 16px;text-align:left;color:#94a3b8;font-size:12px;font-weight:600;text-transform:uppercase;">Riziko</th>
                </tr>
                {findings_rows}
            </table>
        </td>
    </tr>
    '''}

    <!-- Non-AI trackery -->
    {trackers_html}

    <!-- Warning box -->
    <tr>
        <td style="padding:0 40px 24px;">
            <div style="background:#7f1d1d22;border:1px solid #ef444444;border-radius:12px;padding:16px 20px;">
                <p style="color:#fca5a5;font-size:14px;margin:0;line-height:1.5;">
                    ⚠️ <strong>Důležité:</strong> Podle AI Act (čl. 50) musí být návštěvníkům jasně sděleno,
                    že komunikují s AI. Povinnost platí od <strong>2. srpna 2026</strong>.
                    Za nesplnění hrozí pokuta až <strong>15 mil. € / 3 % obratu</strong>.
                </p>
            </div>
        </td>
    </tr>

    <!-- Reassurance -->
    <tr>
        <td style="padding:0 40px 24px;">
            <div style="background:#14532d22;border:1px solid #22c55e44;border-radius:12px;padding:16px 20px;">
                <p style="color:#86efac;font-size:14px;margin:0;line-height:1.5;">
                    🛡️ <strong>Nemusíte se obávat — vše vyřešíme za vás.</strong><br>
                    Stačí vyplnit krátký dotazník, vybrat balíček, a do 7 dnů vám dodáme kompletní dokumentaci
                    pro soulad s AI Act. Žádná byrokracie, žádné starosti.
                </p>
            </div>
        </td>
    </tr>

    <!-- CTA buttons -->
    <tr>
        <td style="padding:0 40px 32px;text-align:center;">
            <a href="{dotaznik_url}" style="display:inline-block;background:linear-gradient(135deg,#7c3aed,#a855f7);color:#fff;
                padding:14px 32px;border-radius:12px;text-decoration:none;font-weight:700;font-size:15px;
                margin:0 8px 8px 0;">
                Vyplnit dotazník →
            </a>
            <a href="{pricing_url}" style="display:inline-block;background:#334155;color:#e2e8f0;
                padding:14px 32px;border-radius:12px;text-decoration:none;font-weight:600;font-size:15px;
                border:1px solid #475569;margin:0 0 8px 0;">
                Zobrazit ceník
            </a>
        </td>
    </tr>

    <!-- Dashboard link -->
    <tr>
        <td style="padding:0 40px 32px;text-align:center;">
            <p style="color:#64748b;font-size:13px;margin:0;">
                Kompletní výsledky najdete ve vašem
                <a href="{dashboard_url}" style="color:#06b6d4;text-decoration:underline;">dashboardu</a>.
            </p>
        </td>
    </tr>

    <!-- Footer -->
    <tr>
        <td style="background:#0f172a;padding:20px 40px;text-align:center;border-top:1px solid #1e293b;">
            <p style="color:#475569;font-size:12px;margin:0;line-height:1.5;">
                AIshield.cz · Ochrana firem před pokutami z AI Act<br>
                <a href="tel:+420732716141" style="color:#475569;text-decoration:none;">+420 732 716 141</a>
                ·
                <a href="mailto:info@aishield.cz" style="color:#475569;text-decoration:none;">info@aishield.cz</a>
            </p>
        </td>
    </tr>

</table>
<!-- /Card -->

</td></tr>
</table>
<!-- /Wrapper -->

</body>
</html>"""
