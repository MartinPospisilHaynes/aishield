"""
AIshield.cz — Scan Pipeline
Orchestrátor celého procesu skenování:
1. Playwright skenuje web
2. Detektor najde AI systémy
3. Výsledky se uloží do Supabase (scans + findings)
4. Screenshoty se uloží do Supabase Storage
"""

import base64
import logging
from datetime import datetime, timezone

from backend.database import get_supabase
from backend.scanner.web_scanner import WebScanner, ScannedPage
from backend.scanner.detector import AIDetector, DetectedAI
from backend.scanner.classifier import AIClassifier, ClassifiedFinding
from backend.monitoring.engine_health import engine_monitor

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

        # 3. Detekuj AI systémy (signaturový detektor)
        detector = AIDetector()
        findings: list[DetectedAI] = detector.detect(page)
        logger.info(f"[Pipeline] Signaturový detektor: {len(findings)} AI systémů")

        # 3.5. Claude AI klasifikace — ověří, co je skutečně nasazené
        classifier = AIClassifier()
        classified: list[ClassifiedFinding] = await classifier.classify(url, findings)

        # Filtrujeme: do DB jdou jen deployed=True (ale uložíme i false-positives s flageem)
        deployed = [c for c in classified if c.deployed]
        not_deployed = [c for c in classified if not c.deployed]

        # Safety net: nástroje, které NEJSOU AI systémy, vždy vyřadíme
        NON_AI_TOOLS = {"google tag manager", "google analytics 4", "seznam retargeting", "heureka"}
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

        # 4. Nahrát viewport screenshot do Storage
        screenshot_url = None
        if page.screenshot_viewport:
            screenshot_url = _upload_screenshot(
                supabase, scan_id, page.screenshot_viewport
            )
            logger.info(f"[Pipeline] Screenshot nahrán: {screenshot_url is not None}")

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

        supabase.table("scans").update({
            "status": "done",
            "finished_at": finished,
            "duration_seconds": duration,
            "total_findings": len(deployed),
            "raw_html_hash": page.html_hash,
            "screenshot_full_url": screenshot_url,
        }).eq("id", scan_id).execute()

        # 7. Aktualizovat companies.last_scanned_at
        supabase.table("companies").update({
            "last_scanned_at": finished,
        }).eq("id", company_id).execute()

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


def _mark_error(supabase, scan_id: str, error_message: str):
    """Označí scan jako chybný."""
    supabase.table("scans").update({
        "status": "error",
        "error_message": error_message[:2000],
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", scan_id).execute()


def _upload_screenshot(supabase, scan_id: str, screenshot_bytes: bytes) -> str | None:
    """Nahraje screenshot do Supabase Storage."""
    try:
        path = f"scans/{scan_id}/viewport.png"
        supabase.storage.from_("screenshots").upload(
            path=path,
            file=screenshot_bytes,
            file_options={"content-type": "image/png"},
        )
        # Vrátíme public URL
        url = supabase.storage.from_("screenshots").get_public_url(path)
        return url
    except Exception:
        return None
