"""
AIshield.cz — Scan Pipeline
Orchestrátor celého procesu skenování:
1. Playwright skenuje web
2. Detektor najde AI systémy
3. Výsledky se uloží do Supabase (scans + findings)
"""

import json

# KLIENTI folder hooks (P5.3)
try:
    from backend.klienti.client_folder_manager import (
        ensure_client_folder, save_scan_results, save_client_profile, slugify_company_name
    )
    KLIENTI_AVAILABLE = True
except ImportError:
    KLIENTI_AVAILABLE = False
import logging
from datetime import datetime, timezone

from backend.database import get_supabase
from backend.scanner.web_scanner import WebScanner, ScannedPage
from backend.scanner.detector import AIDetector, DetectedAI
from backend.scanner.classifier import AIClassifier, ClassifiedFinding
from backend.monitoring.engine_health import engine_monitor
from arq.connections import RedisSettings

logger = logging.getLogger(__name__)


async def run_scan_pipeline(scan_id: str, url: str, company_id: str) -> dict:
    """
    Kompletní pipeline skenování.
    Volá se z API endpointu po vytvoření scanu v DB.

    1. Aktualizuje status na 'running'
    2. Skenuje web Playwrightem
    3. Detekuje AI systémy (signaturový detektor)
    3.5. Claude AI klasifikace (ověří deployed/false-positive)
    4. Ukládá findings do DB
    5. Nahrává screenshoty do Storage
    6. Aktualizuje status na 'done' nebo 'error'
    """
    supabase = get_supabase()
    now = datetime.now(timezone.utc).isoformat()

    # 1. Status → running
    supabase.table("scans").update({
        "status": "running",
        "started_at": now,
    }).eq("id", scan_id).execute()

    try:
        # 2. Skenuj web
        logger.info(f"[Pipeline] Spouštím Playwright scan: {url}")
        scanner = WebScanner()
        page: ScannedPage = await scanner.scan(url)

        if page.error:
            logger.error(f"[Pipeline] Chyba scanneru: {page.error}")
            # Classify Playwright errors
            err_lower = page.error.lower()
            if "timeout" in err_lower:
                err_type = "playwright_timeout"
            elif "browser" in err_lower or "chromium" in err_lower or "crash" in err_lower:
                err_type = "playwright_crash"
            else:
                err_type = "pipeline_error"
            await engine_monitor.report_error(err_type, scan_id, url, page.error)
            _mark_error(supabase, scan_id, page.error)
            return {"status": "error", "error": page.error}

        logger.info(f"[Pipeline] Scan hotový: {len(page.html)} bytes HTML, {len(page.scripts)} skriptů")

        # 2.5. Detekce login stránky / SPA shellu / aplikace za přihlášením
        scan_warning = _detect_login_or_app(page)
        if scan_warning:
            logger.info(f"[Pipeline] Upozornění: {scan_warning}")

        # 3. Detekuj AI systémy (signaturový detektor)
        detector = AIDetector()
        findings: list[DetectedAI] = detector.detect(page)
        logger.info(f"[Pipeline] Signaturový detektor: {len(findings)} AI systémů")

        # 3.0 Detekuj non-AI trackery (pro důvěryhodnost testu)
        trackers = detector.detect_trackers(page)
        logger.info(f"[Pipeline] Tracker detektor: {len(trackers)} non-AI sledovacích systémů")

        # 3.1 Double-scan consensus — druhý sken ověří, že findings jsou stabilní
        if findings:
            logger.info("[Pipeline] Double-scan consensus: spouštím verifikační sken")
            # Uvolníme paměť: screenshoty z prvního skenu nepotřebujeme pro verifikaci
            page.screenshot_full = b""
            # Verifikační sken s kratším čekáním
            scanner2 = WebScanner(
                timeout_ms=30_000,
                wait_after_load_ms=2_000,
            )
            page2: ScannedPage = await scanner2.scan(url)
            if not page2.error:
                findings2: list[DetectedAI] = detector.detect(page2)
                names2 = {f.name.lower() for f in findings2}
                original_count = len(findings)
                findings = [f for f in findings if f.name.lower() in names2]
                removed = original_count - len(findings)
                if removed > 0:
                    logger.info(
                        f"[Pipeline] Double-scan: odstraněno {removed} "
                        f"nestabilních findings (zůstává {len(findings)})"
                    )
                # Uvolníme paměť z druhého skenu
                del page2
            else:
                logger.warning(
                    f"[Pipeline] Double-scan selhalo: {page2.error} — "
                    "pokračuji s výsledky prvního skenu"
                )

        # 3.5. Claude AI klasifikace — ověří, co je skutečně nasazené
        classifier = AIClassifier()
        classified: list[ClassifiedFinding] = await classifier.classify(url, findings)

        # Filtrujeme: do DB jdou jen deployed=True (ale uložíme i false-positives s flageem)
        deployed = [c for c in classified if c.deployed]
        not_deployed = [c for c in classified if not c.deployed]

        # Safety net: nástroje, které NEJSOU AI systémy, vždy vyřadíme
        NON_AI_TOOLS = {"google tag manager", "google analytics 4", "seznam retargeting", "heureka", "meta pixel"}
        auto_fp = [c for c in deployed if c.name.lower() in NON_AI_TOOLS and c.risk_level == "minimal"]
        if auto_fp:
            for c in auto_fp:
                c.deployed = False
                c.reason = f"Automaticky vyřazeno: {c.name} není AI systém."
                logger.info(f"[Pipeline] Auto-FP: {c.name} vyřazen (není AI systém)")
            deployed = [c for c in deployed if c not in auto_fp]
            not_deployed.extend(auto_fp)

        logger.info(
            f"[Pipeline] Claude klasifikace: "
            f"{len(deployed)} nasazených, "
            f"{len(not_deployed)} false-positives vyřazeno"
        )
        if classifier.enabled:
            usage = classifier.usage
            logger.info(
                f"[Pipeline] Claude API: {usage['input_tokens']}+{usage['output_tokens']} tokenů, "
                f"${usage['cost_usd']:.4f}"
            )

        # 5. Uložit findings do DB
        # 5a. Nasazené AI systémy (deployed=True)
        for cf in deployed:
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
                "source": "ai_classified" if classifier.enabled else "scanner",
                "confirmed_by_client": "confirmed" if classifier.enabled else "unknown",
            }).execute()

        # 5b. False positives — uložíme pro audit, ale s flageem
        for cf in not_deployed:
            supabase.table("findings").insert({
                "scan_id": scan_id,
                "company_id": company_id,
                "name": cf.name,
                "category": cf.category,
                "signature_matched": ", ".join(cf.matched_signatures[:5]),
                "risk_level": "none",
                "ai_act_article": "",
                "action_required": cf.reason,
                "ai_classification_text": f"FALSE POSITIVE: {cf.description_cs}",
                "evidence_html": "\n".join(cf.evidence[:5]),
                "source": "ai_classified_fp",
                "confirmed_by_client": "rejected",
            }).execute()

        # 6. Aktualizovat scan jako done
        finished = datetime.now(timezone.utc).isoformat()
        duration = page.duration_ms // 1000

        update_data = {
            "status": "done",
            "finished_at": finished,
            "duration_seconds": duration,
            "total_findings": len(deployed),
            "raw_html_hash": page.html_hash,
            "scan_type": "quick",
            "trackers_json": json.dumps(trackers, ensure_ascii=False) if trackers else None,
        }
        if scan_warning:
            update_data["error_message"] = f"WARNING:{scan_warning}"
        supabase.table("scans").update(update_data).eq("id", scan_id).execute()

        # 7. Aktualizovat companies.last_scanned_at
        supabase.table("companies").update({
            "last_scanned_at": finished,
        }).eq("id", company_id).execute()

        # ── 7b. KLIENTI: uložit scan výsledky do klientské složky (P5.3) ──
        if KLIENTI_AVAILABLE:
            try:
                # Fetch company info for slug
                comp = supabase.table("companies").select("name, url, email, ico, phone").eq("id", company_id).limit(1).execute()
                company_data = comp.data[0] if comp.data else {}
                company_slug = slugify_company_name(company_data.get("url") or company_data.get("name") or company_id)
                ensure_client_folder(company_slug)

                # Save profile
                save_client_profile(company_slug, {
                    "id": company_id,
                    "name": company_data.get("name", ""),
                    "url": company_data.get("url", ""),
                    "email": company_data.get("email", ""),
                    "ico": company_data.get("ico", ""),
                    "phone": company_data.get("phone", ""),
                })

                # Save scan results
                findings_data = [
                    {
                        "name": f.name,
                        "deployed": f.deployed,
                        "category": f.category,
                        "risk_level": f.risk_level,
                        "ai_act_article": f.ai_act_article,
                        "confidence": f.confidence,
                    }
                    for f in deployed
                ]
                save_scan_results(company_slug, {"id": scan_id, "url": url}, findings_data)
                logger.info(f"[Scan] KLIENTI: scan uložen do {company_slug}/scan/")
            except Exception as e:
                logger.warning(f"[Scan] KLIENTI hook failed (non-critical): {e}")

                # Deep scan se nyní spouští manuálně přes POST /api/scan/{scan_id}/deep

        return {
            "status": "done",
            "scan_id": scan_id,
            "url": url,
            "total_findings": len(deployed),
            "false_positives": len(not_deployed),
            "duration_seconds": duration,
            "ai_classified": classifier.enabled,
            "classification_cost_usd": classifier.usage["cost_usd"] if classifier.enabled else 0,
            "findings": [
                {
                    "name": f.name,
                    "deployed": f.deployed,
                    "category": f.category,
                    "risk_level": f.risk_level,
                    "ai_act_article": f.ai_act_article,
                    "action_required": f.action_required,
                    "confidence": f.confidence,
                    "reason": f.reason,
                }
                for f in classified
            ],
            "trackers": trackers,
        }

    except Exception as e:
        logger.error(f"[Pipeline] EXCEPTION: {e}", exc_info=True)
        # Classify exception type
        err_str = str(e).lower()
        if "supabase" in err_str or "postgrest" in err_str or "database" in err_str:
            err_type = "database_error"
        elif "playwright" in err_str or "browser" in err_str:
            err_type = "playwright_crash"
        else:
            err_type = "pipeline_error"
        await engine_monitor.report_error(err_type, scan_id, url, str(e))
        _mark_error(supabase, scan_id, str(e))
        return {"status": "error", "error": str(e)}


def _detect_login_or_app(page) -> str | None:
    """
    Detekuje, zda naskenovaná stránka je:
    - Login formulář / OAuth redirect
    - Prázdný SPA shell (React/Vue/Angular app loader)
    - Aplikace za přihlášením
    Vrátí upozornění (str) nebo None.
    """
    import re

    html_lower = page.html.lower() if page.html else ""
    url_lower = (page.final_url or page.url or "").lower()
    text_len = len(re.sub(r'<[^>]+>', '', page.html or '').strip())

    # 1. URL redirect na login/auth stránku
    login_url_patterns = [
        r'/login', r'/signin', r'/sign-in', r'/auth', r'/authenticate',
        r'/prihlaseni', r'/prihlasit', r'/oauth', r'/sso',
        r'/accounts/login', r'/user/login', r'/admin/login',
    ]
    for pat in login_url_patterns:
        if re.search(pat, url_lower):
            return (
                "LOGIN_WALL|Tato stránka přesměrovala na přihlašovací formulář. "
                "Scanner může analyzovat pouze veřejně přístupné webové stránky, "
                "ne aplikace za přihlášením."
            )

    # 2. Login formulář v HTML (password input + form)
    has_password_input = bool(re.search(r'<input[^>]*type=["\']password["\']', html_lower))
    has_login_form = bool(re.search(
        r'(?:přihlásit|přihlášení|login|sign\s*in|log\s*in|heslo|password|uživatel|username|e-mail.*heslo)',
        html_lower
    ))
    if has_password_input and has_login_form:
        return (
            "LOGIN_WALL|Stránka obsahuje přihlašovací formulář. "
            "Pravděpodobně se jedná o aplikaci za přihlášením — "
            "scanner nemůže analyzovat obsah za login stránkou."
        )

    # 3. Prázdný SPA shell (velmi málo textu, typické React/Vue/Angular loading)
    spa_indicators = [
        r'<div\s+id=["\'](?:root|app|__next|__nuxt)["\'\s][^>]*>\s*</div>',
        r'<div\s+id=["\'](?:root|app|__next|__nuxt)["\'\s][^>]*>\s*<noscript>',
        r'loading\.\.\.', r'načítání', r'please wait', r'moment please',
    ]
    html_text_ratio = text_len / max(len(page.html or ''), 1)
    is_spa_shell = (
        html_text_ratio < 0.02  # Méně než 2% textu vs HTML
        and len(page.html or '') > 500  # Ale HTML existuje (ne prázdná stránka)
        and any(re.search(p, html_lower) for p in spa_indicators)
    )
    if is_spa_shell:
        return (
            "SPA_APP|Stránka vypadá jako webová aplikace (SPA), která se načítá dynamicky. "
            "Scanner zachytil pouze prázdný shell bez obsahu. "
            "AI systémy uvnitř aplikace není možné detekovat bez přihlášení."
        )

    # 4. OAuth/SSO redirect (meta refresh, JS redirect na auth provider)
    oauth_patterns = [
        r'accounts\.google\.com/o/oauth',
        r'login\.microsoftonline\.com',
        r'github\.com/login/oauth',
        r'auth0\.com',
        r'cognito.*amazonaws\.com',
        r'okta\.com',
    ]
    for pat in oauth_patterns:
        if re.search(pat, html_lower) or re.search(pat, url_lower):
            return (
                "OAUTH_REDIRECT|Stránka přesměrovává na externího poskytovatele přihlášení (OAuth/SSO). "
                "Scanner může analyzovat pouze veřejně přístupné stránky."
            )

    return None


def _mark_error(supabase, scan_id: str, error_message: str):
    """Označí scan jako chybný."""
    supabase.table("scans").update({
        "status": "error",
        "error_message": error_message[:2000],
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", scan_id).execute()
