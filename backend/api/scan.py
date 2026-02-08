"""
AIshield.cz — Scan API endpoint
Přijme URL, uloží do DB, vrátí scan_id.
Skutečný scanner přijde v Fázi B (úkoly 6-10).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from backend.database import get_supabase
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
async def create_scan(request: ScanRequest):
    """
    Spustí nový sken webu.
    1. Najde nebo vytvoří firmu v DB podle URL
    2. Vytvoří záznam skenu se statusem 'queued'
    3. Vrátí scan_id (frontend pak polluje stav)
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
