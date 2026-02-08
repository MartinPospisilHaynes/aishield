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

logger = logging.getLogger(__name__)


async def run_scan_pipeline(scan_id: str, url: str, company_id: str) -> dict:
    """
    Kompletní pipeline skenování.
    Volá se z API endpointu po vytvoření scanu v DB.

    1. Aktualizuje status na 'running'
    2. Skenuje web Playwrightem
    3. Detekuje AI systémy
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
            _mark_error(supabase, scan_id, page.error)
            return {"status": "error", "error": page.error}

        logger.info(f"[Pipeline] Scan hotový: {len(page.html)} bytes HTML, {len(page.scripts)} skriptů")

        # 3. Detekuj AI systémy
        detector = AIDetector()
        findings: list[DetectedAI] = detector.detect(page)
        logger.info(f"[Pipeline] Nalezeno {len(findings)} AI systémů")

        # 4. Nahrát viewport screenshot do Storage
        screenshot_url = None
        if page.screenshot_viewport:
            screenshot_url = _upload_screenshot(
                supabase, scan_id, page.screenshot_viewport
            )
            logger.info(f"[Pipeline] Screenshot nahrán: {screenshot_url is not None}")

        # 5. Uložit findings do DB
        for finding in findings:
            supabase.table("findings").insert({
                "scan_id": scan_id,
                "company_id": company_id,
                "name": finding.name,
                "category": finding.category,
                "signature_matched": ", ".join(finding.matched_signatures[:5]),
                "risk_level": finding.risk_level,
                "ai_act_article": finding.ai_act_article,
                "action_required": finding.action_required,
                "ai_classification_text": finding.description_cs,
                "evidence_html": "\n".join(finding.evidence[:5]),
                "source": "scanner",
            }).execute()

        # 6. Aktualizovat scan jako done
        finished = datetime.now(timezone.utc).isoformat()
        duration = page.duration_ms // 1000

        supabase.table("scans").update({
            "status": "done",
            "finished_at": finished,
            "duration_seconds": duration,
            "total_findings": len(findings),
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
            "total_findings": len(findings),
            "duration_seconds": duration,
            "findings": [
                {
                    "name": f.name,
                    "category": f.category,
                    "risk_level": f.risk_level,
                    "ai_act_article": f.ai_act_article,
                    "action_required": f.action_required,
                    "confidence": f.confidence,
                }
                for f in findings
            ],
        }

    except Exception as e:
        logger.error(f"[Pipeline] EXCEPTION: {e}", exc_info=True)
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
