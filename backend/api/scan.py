"""
AIshield.cz — Scan API endpoint
Přijme URL, uloží do DB, vrátí scan_id.
Skutečný scanner přijde v Fázi B (úkoly 6-10).
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, field_validator
from backend.database import get_supabase
from backend.scanner.pipeline import run_scan_pipeline
from backend.scanner.report import generate_html_report, ReportData
from backend.api.auth import get_optional_user, AuthUser, ADMIN_EMAILS
from backend.api.rate_limit import scan_limiter
from datetime import datetime, timezone
import ipaddress
import re
import socket
from urllib.parse import urlparse

router = APIRouter()

# ── SSRF ochrana ──

_BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

_BLOCKED_HOSTNAMES = {"localhost", "localhost.localdomain", "metadata.google.internal"}


def _is_url_safe(url: str) -> bool:
    """Kontrola, že URL nesměřuje na interní/privátní IP (SSRF ochrana)."""
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        return False
    if hostname.lower() in _BLOCKED_HOSTNAMES:
        return False
    try:
        # Resolve DNS a ověř všechny výsledné IP adresy
        for info in socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM):
            addr = info[4][0]
            ip = ipaddress.ip_address(addr)
            for net in _BLOCKED_NETWORKS:
                if ip in net:
                    return False
    except (socket.gaierror, ValueError):
        return False
    return True


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
        # SSRF ochrana — blokovat interní/privátní adresy
        if not _is_url_safe(v):
            raise ValueError("Zadaná URL směřuje na interní adresu a nemůže být skenována")
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
async def create_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks,
    http_request: Request = None,
    user: AuthUser | None = Depends(get_optional_user),
):
    """
    Spustí nový sken webu.
    1. Rate limit kontrola (URL cache, IP limit, globální limit)
    2. Najde nebo vytvoří firmu v DB podle URL
    3. Vytvoří záznam skenu se statusem 'queued'
    4. Spustí scan pipeline na pozadí
    5. Vrátí scan_id (frontend pak polluje stav)
    """
    supabase = get_supabase()
    url = request.url

    # ── Rate limiting ──
    client_ip = "unknown"
    if http_request:
        client_ip = (
            http_request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or http_request.headers.get("x-real-ip", "")
            or http_request.client.host if http_request.client else "unknown"
        )

    is_authenticated = user is not None
    is_admin = user is not None and user.email in ADMIN_EMAILS

    limit_result = scan_limiter.check(
        url=url,
        client_ip=client_ip,
        is_authenticated=is_authenticated,
        is_admin=is_admin,
    )

    if not limit_result.allowed:
        # Pokud máme cached výsledky, vrátíme scan_id pro přesměrování
        if limit_result.cached_scan_id:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": limit_result.reason,
                    "cached_scan_id": limit_result.cached_scan_id,
                    "cached_company_id": limit_result.cached_company_id,
                    "retry_after": limit_result.retry_after,
                },
                headers={"Retry-After": str(limit_result.retry_after)},
            )
        return JSONResponse(
            status_code=429,
            content={
                "detail": limit_result.reason,
                "retry_after": limit_result.retry_after,
            },
            headers={"Retry-After": str(limit_result.retry_after)},
        )

    try:
        # 1. Hledáme firmu podle URL
        existing = supabase.table("companies").select("id, name, email").eq("url", url).limit(1).execute()

        user_email = user.email if user else None
        user_meta = user.metadata if user else {}
        company_name_from_meta = user_meta.get("company_name", "")

        if existing.data:
            company_id = existing.data[0]["id"]
            # Pokud je uživatel přihlášený a firma nemá email → propojíme
            if user_email and not existing.data[0].get("email"):
                update_data = {"email": user_email}
                if company_name_from_meta:
                    update_data["name"] = company_name_from_meta
                supabase.table("companies").update(update_data).eq("id", company_id).execute()
        else:
            # Vytvoříme novou firmu — s emailem pokud je uživatel přihlášený
            domain = re.sub(r"^https?://", "", url).split("/")[0]
            insert_data = {
                "name": company_name_from_meta or domain,
                "url": url,
                "source": "manual",
            }
            if user_email:
                insert_data["email"] = user_email
            new_company = supabase.table("companies").insert(insert_data).execute()
            company_id = new_company.data[0]["id"]

        # 2. Vytvoříme sken
        now = datetime.now(timezone.utc).isoformat()
        new_scan = supabase.table("scans").insert({
            "company_id": company_id,
            "url_scanned": url,
            "status": "queued",
            "triggered_by": "client" if not user else "authenticated",
            "started_at": now,
        }).execute()

        scan_id = new_scan.data[0]["id"]

        # 3. Aktualizujeme companies.last_scanned_at
        supabase.table("companies").update({
            "last_scanned_at": now,
        }).eq("id", company_id).execute()

        # 4. Spustíme scan pipeline na pozadí
        background_tasks.add_task(run_scan_pipeline, scan_id, url, company_id)

        # 5. Zaregistrujeme sken do rate limiter cache
        scan_limiter.register_scan(url, scan_id, company_id)

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

        # Detekce zaseknutého skenu — pokud běží >5 minut, worker zřejmě spadl
        STALE_SCAN_TIMEOUT_SECONDS = 300  # 5 minut
        if scan["status"] in ("running", "queued") and scan.get("started_at"):
            try:
                started = datetime.fromisoformat(scan["started_at"].replace("Z", "+00:00"))
                elapsed = (datetime.now(timezone.utc) - started).total_seconds()
                if elapsed > STALE_SCAN_TIMEOUT_SECONDS:
                    import logging
                    logging.getLogger(__name__).warning(
                        f"[StaleScan] Scan {scan_id} běží {elapsed:.0f}s — označuji jako error"
                    )
                    now_iso = datetime.now(timezone.utc).isoformat()
                    supabase.table("scans").update({
                        "status": "error",
                        "error_message": f"Sken vypršel po {int(elapsed)}s — worker proces zřejmě spadl. Zkuste to prosím znovu.",
                        "finished_at": now_iso,
                    }).eq("id", scan_id).execute()
                    scan["status"] = "error"
                    scan["finished_at"] = now_iso
            except Exception:
                pass  # Nepodstatné — neblokujeme odpověď

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


# ── Potvrzení nálezů ──

class ConfirmFindingRequest(BaseModel):
    """Požadavek na potvrzení/zamítnutí nálezu."""
    confirmed: bool  # True = potvrzeno klientem, False = zamítnuto
    note: str = ""   # Volitelná poznámka


@router.patch("/finding/{finding_id}/confirm")
async def confirm_finding(finding_id: str, request: ConfirmFindingRequest):
    """
    Klient potvrdí nebo zamítne nález.
    - confirmed=true → 'confirmed'
    - confirmed=false → 'rejected'
    """
    supabase = get_supabase()

    try:
        # Ověříme, že finding existuje
        existing = supabase.table("findings").select("id, name").eq(
            "id", finding_id
        ).limit(1).execute()

        if not existing.data:
            raise HTTPException(status_code=404, detail="Nález nenalezen")

        status = "confirmed" if request.confirmed else "rejected"

        supabase.table("findings").update({
            "confirmed_by_client": status,
        }).eq("id", finding_id).execute()

        return {
            "finding_id": finding_id,
            "name": existing.data[0]["name"],
            "confirmed_by_client": status,
            "message": f"Nález {'potvrzen' if request.confirmed else 'zamítnut'} klientem.",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chyba při potvrzování nálezu: {str(e)}",
        )


@router.patch("/scan/{scan_id}/confirm-all")
async def confirm_all_findings(scan_id: str, request: ConfirmFindingRequest):
    """Hromadně potvrdí/zamítne všechny nálezy pro daný sken."""
    supabase = get_supabase()

    try:
        status = "confirmed" if request.confirmed else "rejected"

        result = supabase.table("findings").update({
            "confirmed_by_client": status,
        }).eq("scan_id", scan_id).neq(
            "source", "ai_classified_fp"  # Nechceme měnit false-positives
        ).execute()

        count = len(result.data) if result.data else 0

        return {
            "scan_id": scan_id,
            "confirmed_by_client": status,
            "updated_count": count,
            "message": f"{count} nálezů {'potvrzeno' if request.confirmed else 'zamítnuto'}.",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chyba při hromadném potvrzování: {str(e)}",
        )
