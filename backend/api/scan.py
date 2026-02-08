"""
AIshield.cz — Scan API endpoint
Přijme URL, uloží do DB, vrátí scan_id.
Skutečný scanner přijde v Fázi B (úkoly 6-10).
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, field_validator
from backend.database import get_supabase
from backend.scanner.pipeline import run_scan_pipeline
from backend.scanner.report import generate_html_report, ReportData
from datetime import datetime, timezone
import re

router = APIRouter()


# ── Modely ──

class ScanRequest(BaseModel):
    """Požadavek na skenování webu."""
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            v = "https://" + v
        pattern = r"^https?://[a-zA-Z0-9][-a-zA-Z0-9]*(\.[a-zA-Z0-9][-a-zA-Z0-9]*)+(/.*)?$"
        if not re.match(pattern, v):
            raise ValueError("Neplatná URL adresa")
        return v


class ScanResponse(BaseModel):
    """Odpověď po spuštění skenu."""
    scan_id: str
    company_id: str
    url: str
    status: str
    message: str


class ScanStatusResponse(BaseModel):
    """Stav existujícího skenu."""
    scan_id: str
    url: str
    status: str
    total_findings: int
    started_at: str | None
    finished_at: str | None
    company_name: str | None


# ── Endpointy ──

@router.post("/scan", response_model=ScanResponse)
async def create_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    """
    Spustí nový sken webu.
    1. Najde nebo vytvoří firmu v DB podle URL
    2. Vytvoří záznam skenu se statusem 'queued'
    3. Spustí scan pipeline na pozadí
    4. Vrátí scan_id (frontend pak polluje stav)
    """
    supabase = get_supabase()
    url = request.url

    try:
        # 1. Hledáme firmu podle URL
        existing = supabase.table("companies").select("id, name").eq("url", url).limit(1).execute()

        if existing.data:
            company_id = existing.data[0]["id"]
        else:
            # Vytvoříme novou firmu (zatím s doménou jako jménem)
            domain = re.sub(r"^https?://", "", url).split("/")[0]
            new_company = supabase.table("companies").insert({
                "name": domain,
                "url": url,
                "source": "manual",
            }).execute()
            company_id = new_company.data[0]["id"]

        # 2. Vytvoříme sken
        now = datetime.now(timezone.utc).isoformat()
        new_scan = supabase.table("scans").insert({
            "company_id": company_id,
            "url_scanned": url,
            "status": "queued",
            "triggered_by": "client",
            "started_at": now,
        }).execute()

        scan_id = new_scan.data[0]["id"]

        # 3. Aktualizujeme companies.last_scanned_at
        supabase.table("companies").update({
            "last_scanned_at": now,
        }).eq("id", company_id).execute()

        # 4. Spustíme scan pipeline na pozadí
        background_tasks.add_task(run_scan_pipeline, scan_id, url, company_id)

        return ScanResponse(
            scan_id=scan_id,
            company_id=company_id,
            url=url,
            status="queued",
            message=f"Sken webu {url} byl zařazen do fronty.",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chyba při vytváření skenu: {str(e)}",
        )


@router.get("/scan/{scan_id}", response_model=ScanStatusResponse)
async def get_scan_status(scan_id: str):
    """Vrátí aktuální stav skenu. Frontend polluje tento endpoint."""
    supabase = get_supabase()

    try:
        result = supabase.table("scans").select(
            "id, url_scanned, status, total_findings, started_at, finished_at, company_id"
        ).eq("id", scan_id).limit(1).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Sken nenalezen")

        scan = result.data[0]

        # Zjistíme jméno firmy
        company = supabase.table("companies").select("name").eq(
            "id", scan["company_id"]
        ).limit(1).execute()
        company_name = company.data[0]["name"] if company.data else None

        return ScanStatusResponse(
            scan_id=scan["id"],
            url=scan["url_scanned"],
            status=scan["status"],
            total_findings=scan["total_findings"],
            started_at=scan["started_at"],
            finished_at=scan["finished_at"],
            company_name=company_name,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chyba při čtení stavu skenu: {str(e)}",
        )


@router.get("/scans/recent")
async def get_recent_scans(limit: int = 10):
    """Vrátí posledních N skenů — pro dashboard / statistiky."""
    supabase = get_supabase()

    try:
        result = supabase.table("scans").select(
            "id, url_scanned, status, total_findings, created_at"
        ).order("created_at", desc=True).limit(limit).execute()

        return {"scans": result.data, "count": len(result.data)}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chyba při čtení skenů: {str(e)}",
        )


@router.get("/scan/{scan_id}/findings")
async def get_scan_findings(scan_id: str):
    """Vrátí všechny nálezy pro daný sken (deployed + false positives zvlášť)."""
    supabase = get_supabase()

    try:
        result = supabase.table("findings").select(
            "id, name, category, risk_level, ai_act_article, "
            "action_required, ai_classification_text, evidence_html, "
            "signature_matched, confirmed_by_client, source, created_at"
        ).eq("scan_id", scan_id).execute()

        # Rozdělíme na deployed a false-positives
        deployed = []
        false_positives = []
        for f in result.data:
            if f.get("source") == "ai_classified_fp":
                false_positives.append(f)
            else:
                deployed.append(f)

        return {
            "findings": deployed,
            "false_positives": false_positives,
            "count": len(deployed),
            "fp_count": len(false_positives),
            "ai_classified": any(
                f.get("source") in ("ai_classified", "ai_classified_fp")
                for f in result.data
            ),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chyba při čtení nálezů: {str(e)}",
        )


@router.get("/scan/{scan_id}/report", response_class=HTMLResponse)
async def get_scan_report(scan_id: str):
    """Vygeneruje HTML compliance report pro daný sken."""
    supabase = get_supabase()

    try:
        # 1. Načteme scan data
        scan_result = supabase.table("scans").select(
            "id, url_scanned, status, total_findings, started_at, finished_at, "
            "duration_seconds, company_id, screenshot_full_url"
        ).eq("id", scan_id).limit(1).execute()

        if not scan_result.data:
            raise HTTPException(status_code=404, detail="Sken nenalezen")

        scan = scan_result.data[0]

        if scan["status"] != "done":
            raise HTTPException(status_code=400, detail="Sken ještě není dokončen")

        # 2. Načteme firmu
        company = supabase.table("companies").select("name").eq(
            "id", scan["company_id"]
        ).limit(1).execute()
        company_name = company.data[0]["name"] if company.data else "Neznámá firma"

        # 3. Načteme findings
        findings_result = supabase.table("findings").select(
            "name, category, risk_level, ai_act_article, action_required, "
            "ai_classification_text, signature_matched, source, confirmed_by_client"
        ).eq("scan_id", scan_id).execute()

        deployed = []
        false_positives = []
        for f in findings_result.data:
            if f.get("source") == "ai_classified_fp":
                false_positives.append(f)
            else:
                deployed.append(f)

        ai_classified = any(
            f.get("source") in ("ai_classified", "ai_classified_fp")
            for f in findings_result.data
        )

        # 4. Generujeme report
        report_data = ReportData(
            scan_id=scan_id,
            url=scan["url_scanned"],
            company_name=company_name,
            started_at=scan.get("started_at", ""),
            finished_at=scan.get("finished_at", ""),
            duration_seconds=scan.get("duration_seconds", 0) or 0,
            total_findings=len(deployed),
            ai_classified=ai_classified,
            findings=deployed,
            false_positives=false_positives,
            screenshot_url=scan.get("screenshot_full_url"),
        )

        html = generate_html_report(report_data)
        return HTMLResponse(content=html)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chyba při generování reportu: {str(e)}",
        )
