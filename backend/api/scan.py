"""
AIshield.cz — Scan API endpoint
Přijme URL, uloží do DB, vrátí scan_id.
Skutečný scanner přijde v Fázi B (úkoly 6-10).
"""

import asyncio
import logging
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

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Circuit Breaker pro scan endpoint ──

class _ScanCircuitBreaker:
    """
    Po THRESHOLD selháních za WINDOW sekund → odmítá requesty na COOLDOWN.
    """
    THRESHOLD = 3       # po kolika selháních se otevře
    WINDOW = 600        # sledovací okno (10 min)
    COOLDOWN = 120      # jak dlouho odmítá (2 min)

    def __init__(self):
        import time
        self._failures: list[float] = []
        self._opened_at: float | None = None

    def record_failure(self):
        import time
        now = time.monotonic()
        self._failures.append(now)
        self._failures = [t for t in self._failures if now - t < self.WINDOW]
        if len(self._failures) >= self.THRESHOLD:
            self._opened_at = now
            logger.warning(f"[CircuitBreaker] OTEVŘEN — {len(self._failures)} selhání")

    def record_success(self):
        self._failures.clear()
        if self._opened_at:
            logger.info("[CircuitBreaker] UZAVŘEN — scan úspěšný")
            self._opened_at = None

    def is_open(self) -> bool:
        import time
        if self._opened_at is None:
            return False
        if (time.monotonic() - self._opened_at) > self.COOLDOWN:
            self._opened_at = None
            self._failures.clear()
            logger.info("[CircuitBreaker] Auto-close po cooldown")
            return False
        return True


_circuit_breaker = _ScanCircuitBreaker()

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
    scan_warning: str | None = None
    error_message: str | None = None
    # Deep scan fields
    scan_type: str | None = None
    deep_scan_status: str | None = None
    deep_scan_started_at: str | None = None
    deep_scan_finished_at: str | None = None
    deep_scan_total_findings: int | None = None
    geo_countries_scanned: list[str] | None = None


# ── Endpointy ──


class CheckUrlRequest(BaseModel):
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


@router.post("/scan/check-url")
async def check_url(req: CheckUrlRequest):
    """Ověří, že URL je validní a web odpovídá (HEAD request)."""
    import httpx

    # Ověř DNS zvlášť – lepší chybová hláška
    parsed = urlparse(req.url)
    hostname = parsed.hostname
    try:
        socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror:
        raise HTTPException(
            status_code=422,
            detail=f"Doména {hostname} neexistuje nebo není dostupná"
        )

    if not _is_url_safe(req.url):
        raise HTTPException(
            status_code=422,
            detail="Zadaná URL směřuje na interní adresu"
        )

    try:
        async with httpx.AsyncClient(timeout=8, follow_redirects=True, verify=False) as client:
            r = await client.head(req.url)
            if r.status_code < 500:
                return {"ok": True, "status_code": r.status_code, "url": str(r.url)}
            raise HTTPException(status_code=422, detail=f"Web vrátil chybu {r.status_code}")
    except httpx.ConnectError:
        raise HTTPException(status_code=422, detail="Web není dostupný — zkontrolujte adresu")
    except httpx.TimeoutException:
        raise HTTPException(status_code=422, detail="Web neodpovídá (timeout) — zkontrolujte adresu")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=422, detail="Nepodařilo se ověřit web — zkontrolujte adresu")


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
    # ── Circuit breaker ──
    if _circuit_breaker.is_open():
        return JSONResponse(
            status_code=503,
            content={"detail": "Skenovací služba je dočasně přetížena. Zkuste to za 2 minuty.", "retry_after": 120},
            headers={"Retry-After": "120"},
        )

    supabase = get_supabase()
    url = request.url
    logger.info(f"[Scan] create_scan: url={url}, user={user.email if user else 'anonymous'}")

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

    # ── DB-backed domain cooldown (survives restarts) ──
    if not is_admin:
        try:
            from backend.api.rate_limit import URL_COOLDOWN_SECONDS
            from datetime import timedelta
            from dateutil.parser import parse as dt_parse
            domain_norm = scan_limiter.normalize_url(url).split("/")[0]
            one_hour_ago = (datetime.now(timezone.utc) - timedelta(seconds=URL_COOLDOWN_SECONDS)).isoformat()
            recent = supabase.table("scans").select(
                "id, company_id, url_scanned, finished_at, created_at, status"
            ).gte(
                "created_at", one_hour_ago
            ).in_(
                "status", ["done", "running", "queued"]
            ).limit(50).execute()

            for row in (recent.data or []):
                row_domain = scan_limiter.normalize_url(row["url_scanned"]).split("/")[0]
                if row_domain == domain_norm:
                    # Found a recent scan on this domain — block
                    from dateutil.parser import parse as dt_parse
                    scan_time = dt_parse(row["finished_at"] or row.get("created_at", "") or "")
                    age_s = (datetime.now(timezone.utc) - scan_time).total_seconds()
                    remaining = max(1, int(URL_COOLDOWN_SECONDS - age_s))
                    mins_ago = max(1, int(age_s // 60))
                    mins_left = remaining // 60
                    # Register in memory cache too
                    scan_limiter.register_scan(url, row["id"], row["company_id"])
                    logger.info(f"[Scan] DB cooldown hit: {domain_norm} scanned {mins_ago}m ago")
                    return JSONResponse(
                        status_code=429,
                        content={
                            "detail": f"Tento web byl skenován před {mins_ago} minutami. "
                                      f"Další sken bude možný za {mins_left} min.",
                            "cached_scan_id": row["id"],
                            "cached_company_id": row["company_id"],
                            "retry_after": remaining,
                        },
                        headers={"Retry-After": str(remaining)},
                    )
        except Exception as e:
            logger.warning(f"[Scan] DB cooldown check failed (allowing scan): {e}")

    try:
        # 1. Hledáme firmu podle URL (přesný match + doménový fallback)
        existing = supabase.table("companies").select("id, name, email").eq("url", url).limit(1).execute()

        # Fallback: hledej podle domény (bez http(s)://, www.)
        if not existing.data:
            _domain_clean = re.sub(r"^https?://(www\.)?", "", url).split("/")[0].lower().strip(".")
            if _domain_clean:
                # Hledáme firmu kde url OBSAHUJE doménu
                _fb = supabase.table("companies").select("id, name, email").ilike("url", f"%{_domain_clean}%").limit(1).execute()
                if _fb.data:
                    existing = _fb
                    logger.info(f"[Scan] Domain fallback matched: {_domain_clean} → company {_fb.data[0]['id']}")

        user_email = user.email if user else None
        user_meta = user.metadata if user else {}
        company_name_from_meta = user_meta.get("company_name", "")
        ico_from_meta = user_meta.get("ico", "")

        if existing.data:
            company_id = existing.data[0]["id"]
            existing_company = existing.data[0]
            # Doplníme chybějící údaje z user_metadata (email, IČO, název)
            update_data = {}
            if user_email and not existing_company.get("email"):
                update_data["email"] = user_email
            if company_name_from_meta and (not existing_company.get("name") or existing_company["name"] == re.sub(r"^https?://", "", url).split("/")[0]):
                update_data["name"] = company_name_from_meta
            if ico_from_meta and not existing_company.get("ico"):
                update_data["ico"] = ico_from_meta
            if update_data:
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
            if ico_from_meta:
                insert_data["ico"] = ico_from_meta
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

        # 4. Spustíme scan pipeline na pozadí S TIMEOUT OCHRANOU
        async def _guarded_scan(sid: str, u: str, cid: str):
            """Wrapper: hard timeout 180s + error handling."""
            try:
                _result = await asyncio.wait_for(
                    run_scan_pipeline(sid, u, cid),
                    timeout=180.0,
                )
                if isinstance(_result, dict) and _result.get("status") == "done":
                    _circuit_breaker.record_success()
                    # ── Okamžitá notifikace o organickém skenu ──
                    try:
                        from backend.monitoring.admin_notifier import notify_organic_scan_completed
                        sb_notif = get_supabase()
                        scan_row = sb_notif.table("scans").select("*").eq("id", sid).single().execute()
                        comp_row = sb_notif.table("companies").select("name").eq("id", cid).single().execute()
                        findings_data = sb_notif.table("findings").select("risk_level").eq("scan_id", sid).execute()
                        
                        high_f = sum(1 for f in findings_data.data if f.get("risk_level") == "high")
                        med_f = sum(1 for f in findings_data.data if f.get("risk_level") == "medium")
                        low_f = sum(1 for f in findings_data.data if f.get("risk_level") == "low")
                        
                        started = scan_row.data.get("started_at", "")
                        finished = scan_row.data.get("finished_at", "")
                        duration = 0.0
                        if started and finished:
                            from datetime import datetime as _dt
                            try:
                                t0 = _dt.fromisoformat(started.replace("Z", "+00:00"))
                                t1 = _dt.fromisoformat(finished.replace("Z", "+00:00"))
                                duration = (t1 - t0).total_seconds()
                            except Exception:
                                pass
                        
                        await notify_organic_scan_completed(
                            scan_id=sid,
                            url=u,
                            company_id=cid,
                            company_name=comp_row.data.get("name", ""),
                            total_findings=len(findings_data.data),
                            high_findings=high_f,
                            medium_findings=med_f,
                            low_findings=low_f,
                            scan_duration_s=duration,
                            triggered_by=scan_row.data.get("triggered_by", "client"),
                            scan_status="done",
                        )
                    except Exception as notif_err:
                        logger.warning(f"[Scan] Organic scan notif selhala (non-fatal): {notif_err}")
                elif isinstance(_result, dict) and _result.get("status") == "error":
                    _circuit_breaker.record_failure()
            except asyncio.TimeoutError:
                _circuit_breaker.record_failure()
                logger.error(f"[Scan] HARD TIMEOUT 180s pro scan {sid} ({u})")
                try:
                    sb = get_supabase()
                    sb.table("scans").update({
                        "status": "error",
                        "error_message": "Sken vypršel po 180s — web je příliš pomalý nebo nereaguje.",
                        "finished_at": datetime.now(timezone.utc).isoformat(),
                    }).eq("id", sid).execute()
                except Exception as db_err:
                    logger.error(f"[Scan] DB update po timeout selhalo: {db_err}")
            except Exception as exc:
                _circuit_breaker.record_failure()
                logger.error(f"[Scan] Neočekávaná chyba v pipeline: {exc}", exc_info=True)
                try:
                    sb = get_supabase()
                    sb.table("scans").update({
                        "status": "error",
                        "error_message": f"Pipeline error: {str(exc)[:500]}",
                        "finished_at": datetime.now(timezone.utc).isoformat(),
                    }).eq("id", sid).execute()
                except Exception:
                    pass
                # ── Error logging → admin email ──
                try:
                    from backend.monitoring.admin_notifier import notify_error
                    await notify_error(
                        module="scan_pipeline",
                        error=exc,
                        context={"scan_id": sid, "url": u, "company_id": company_id},
                    )
                except Exception:
                    pass

        background_tasks.add_task(_guarded_scan, scan_id, url, company_id)

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
            "id, url_scanned, status, total_findings, started_at, finished_at, company_id, error_message, "
            "scan_type, deep_scan_status, deep_scan_started_at, deep_scan_finished_at, deep_scan_total_findings, geo_countries_scanned"
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
                    logger.warning(
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
            except Exception as e:
                logger.warning(f"[Scan] Non-critical status check failed: {e}")  # Nepodstatné — neblokujeme odpověď

        # Zjistíme jméno firmy
        company = supabase.table("companies").select("name").eq(
            "id", scan["company_id"]
        ).limit(1).execute()
        company_name = company.data[0]["name"] if company.data else None

        # Parsuj scan_warning z error_message (formát "WARNING:TYPE|text")
        scan_warning = None
        error_message = scan.get("error_message")
        if error_message and error_message.startswith("WARNING:"):
            scan_warning = error_message[8:]  # Odstraň "WARNING:" prefix
            error_message = None  # Není to chyba, jen varovat

        return ScanStatusResponse(
            scan_id=scan["id"],
            url=scan["url_scanned"],
            status=scan["status"],
            total_findings=scan["total_findings"],
            started_at=scan["started_at"],
            finished_at=scan["finished_at"],
            company_name=company_name,
            scan_warning=scan_warning,
            error_message=error_message,
            scan_type=scan.get("scan_type"),
            deep_scan_status=scan.get("deep_scan_status"),
            deep_scan_started_at=scan.get("deep_scan_started_at"),
            deep_scan_finished_at=scan.get("deep_scan_finished_at"),
            deep_scan_total_findings=scan.get("deep_scan_total_findings"),
            geo_countries_scanned=scan.get("geo_countries_scanned"),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chyba při čtení stavu skenu: {str(e)}",
        )


@router.get("/scans/recent")
async def get_recent_scans(
    limit: int = 10,
    user: AuthUser | None = Depends(get_optional_user),
):
    """Vrátí posledních N skenů — vyžaduje admin přístup."""
    # Zabezpečení: pouze admin může vidět všechny skeny
    if not user or user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Přístup odepřen — vyžaduje admin oprávnění")

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
    """Vrátí všechny nálezy pro daný sken (deployed + false positives + trackery zvlášť)."""
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

        # Načteme trackery z scans tabulky
        trackers = []
        try:
            scan_row = supabase.table("scans").select("trackers_json").eq("id", scan_id).single().execute()
            if scan_row.data and scan_row.data.get("trackers_json"):
                import json
                trackers = json.loads(scan_row.data["trackers_json"])
        except Exception as e:
            logger.debug(f"[Scan] trackers_json not available for scan {scan_id}: {e}")

        return {
            "findings": deployed,
            "false_positives": false_positives,
            "trackers": trackers,
            "count": len(deployed),
            "fp_count": len(false_positives),
            "tracker_count": len(trackers),
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


@router.post("/scan/{scan_id}/deep")
async def trigger_deep_scan(scan_id: str):
    """
    Ručně spustí 24h hloubkový scan pro daný sken.
    Kontroluje cooldown (max 1× za 7 dní na doménu).
    """
    from datetime import timedelta
    from arq.connections import ArqRedis, create_pool
    from arq.connections import RedisSettings

    logger.info(f"[DeepTrigger] Požadavek na spuštění deep scanu: scan_id={scan_id}")

    supabase = get_supabase()

    # 1. Najít scan
    scan_res = supabase.table("scans").select(
        "id, url_scanned, company_id, status, deep_scan_status, deep_scan_started_at"
    ).eq("id", scan_id).limit(1).execute()

    if not scan_res.data:
        logger.warning(f"[DeepTrigger] Scan nenalezen: scan_id={scan_id}")
        raise HTTPException(status_code=404, detail="Scan nenalezen.")

    scan = scan_res.data[0]
    company_id = scan["company_id"]
    url = scan["url_scanned"]
    current_deep_status = scan["deep_scan_status"]

    logger.info(
        f"[DeepTrigger] Stav scanu: scan_id={scan_id}, url={url}, "
        f"status={scan['status']}, deep_scan_status={current_deep_status}, "
        f"company_id={company_id}"
    )

    if not url:
        logger.error(f"[DeepTrigger] Scan nemá URL! scan_id={scan_id}")
        raise HTTPException(status_code=400, detail="Scan nemá URL. Kontaktujte podporu.")

    if scan["status"] != "done":
        logger.warning(f"[DeepTrigger] Rychlý scan nedokončen: scan_id={scan_id}, status={scan['status']}")
        raise HTTPException(status_code=400, detail="Rychlý scan ještě nebyl dokončen.")

    if current_deep_status in ("running", "pending"):
        # Check if stuck — auto-reset
        from datetime import datetime, timezone, timedelta
        import os
        _stuck_hours = 1 if os.getenv("DEEP_SCAN_MODE", "production").lower() == "testing" else 26
        started = scan.get("deep_scan_started_at")
        if started:
            started_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
            elapsed_h = (datetime.now(timezone.utc) - started_dt).total_seconds() / 3600
            if elapsed_h > _stuck_hours:
                logger.warning(
                    f"[DeepTrigger] Zaseknutý deep scan detekován ({elapsed_h:.1f}h), resetuji: scan_id={scan_id}"
                )
                supabase.table("scans").update({
                    "deep_scan_status": None,
                    "deep_scan_started_at": None,
                }).eq("id", scan_id).execute()
                # Fall through — allow re-trigger
            else:
                logger.info(
                    f"[DeepTrigger] Deep scan již běží ({elapsed_h:.1f}h): scan_id={scan_id}"
                )
                return {
                    "scan_id": scan_id,
                    "deep_scan_status": current_deep_status,
                    "message": "Hloubkový scan již běží. Výsledky obdržíte e-mailem do 24 hodin.",
                }
        else:
            logger.info(
                f"[DeepTrigger] Deep scan status={current_deep_status} ale chybí started_at: scan_id={scan_id}"
            )
            return {
                "scan_id": scan_id,
                "deep_scan_status": current_deep_status,
                "message": "Hloubkový scan již běží. Výsledky obdržíte e-mailem do 24 hodin.",
            }

    if current_deep_status == "done":
        logger.info(f"[DeepTrigger] Deep scan již dokončen: scan_id={scan_id}")
        return {
            "scan_id": scan_id,
            "deep_scan_status": "done",
            "message": "Hloubkový scan již byl dokončen. Výsledky najdete v dashboardu.",
        }

    # 2. Cooldown: max 1× za 7 dní pro danou doménu
    from datetime import datetime, timezone
    cooldown_since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    recent_deep = supabase.table("scans").select("id").eq(
        "company_id", company_id
    ).eq(
        "deep_scan_status", "done"
    ).gte(
        "deep_scan_finished_at", cooldown_since
    ).limit(1).execute()

    if recent_deep.data:
        logger.warning(
            f"[DeepTrigger] Cooldown aktivní: company_id={company_id}, "
            f"poslední deep scan={recent_deep.data[0]['id']}"
        )
        raise HTTPException(
            status_code=429,
            detail="Hloubkový scan byl proveden v posledních 7 dnech. Zkuste to později.",
        )

    # 3. Stagger: rozložit starty deep scanů v čase
    #    Kolo = 3 země × ~3 min = ~8 min. Interval = 3h = 180 min.
    #    Stagger 6 min → 30 zákazníků se vejde do jednoho intervalu.
    #    Max 2 Playwright instance naráz (8 min kolo / 6 min stagger).
    STAGGER_MINUTES = 6
    active_deep = supabase.table("scans").select("id").in_(
        "deep_scan_status", ["pending", "running"]
    ).execute()
    active_count = len(active_deep.data) if active_deep.data else 0
    defer_minutes = active_count * STAGGER_MINUTES

    logger.info(
        f"[DeepTrigger] Plánuji deep scan: scan_id={scan_id}, url={url}, "
        f"active_deep={active_count}, defer={defer_minutes}min"
    )
    supabase.table("scans").update({
        "deep_scan_status": "pending",
    }).eq("id", scan_id).execute()

    try:
        pool = await create_pool(RedisSettings(host="localhost", port=6379))
        await pool.enqueue_job(
            "deep_scan_job",
            scan_id,
            url,
            company_id,
            _job_id=f"deep-{scan_id}",
            _defer_by=timedelta(minutes=defer_minutes),
        )
        await pool.close()
        logger.info(
            f"[DeepTrigger] ✅ Deep scan naplánován: scan_id={scan_id}, "
            f"url={url}, start za {defer_minutes} min"
        )

        # ── Admin notifikace: deep scan spuštěn ──
        try:
            from backend.monitoring.admin_notifier import notify_deep_scan_started
            await notify_deep_scan_started(scan_id, url, company_id)
        except Exception as notif_err:
            logger.error(f"[DeepTrigger] Admin notif selhala: {notif_err}")

    except Exception as enqueue_err:
        logger.error(
            f"[DeepTrigger] ❌ Chyba při enqueue: scan_id={scan_id}, error={enqueue_err}",
            exc_info=True,
        )
        # Rollback status
        supabase.table("scans").update({
            "deep_scan_status": None,
        }).eq("id", scan_id).execute()
        # ── Error logging → admin email ──
        try:
            from backend.monitoring.admin_notifier import notify_error
            await notify_error(
                module="deep_scan_trigger",
                error=enqueue_err,
                context={"scan_id": scan_id, "url": url},
                severity="critical",
            )
        except Exception:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"Nepodařilo se naplánovat hloubkový scan: {str(enqueue_err)}",
        )

    return {
        "scan_id": scan_id,
        "deep_scan_status": "pending",
        "message": "Hloubkový 24h scan byl úspěšně spuštěn. Výsledky obdržíte e-mailem.",
    }

# ══════════════════════════════════════════════════════════════
# RESULTS-VIEWED — Frontend zavolá když klient vidí výsledky
# ══════════════════════════════════════════════════════════════

class ResultsViewedRequest(BaseModel):
    """Data z frontendu o zobrazení výsledků."""
    time_on_results_s: float = 0.0
    client_waited: bool = True
    scan_duration_s: float = 0.0


@router.post("/scan/{scan_id}/results-viewed")
async def scan_results_viewed(scan_id: str, body: ResultsViewedRequest):
    """
    Frontend zavolá tento endpoint když klient uvidí výsledky skenu.
    Odešle okamžitou notifikaci adminovi s analýzou chování klienta.
    """
    supabase = get_supabase()

    try:
        # Načteme data o skenu
        scan_row = supabase.table("scans").select(
            "id, url_scanned, company_id, status, total_findings, triggered_by, started_at, finished_at"
        ).eq("id", scan_id).single().execute()

        if not scan_row.data:
            raise HTTPException(status_code=404, detail="Scan nenalezen")

        scan = scan_row.data

        # Jen organic skeny (ne admin)
        triggered_by = scan.get("triggered_by", "client")

        # Načteme firmu
        comp = supabase.table("companies").select("name").eq("id", scan["company_id"]).single().execute()
        company_name = comp.data.get("name", "") if comp.data else ""

        # Načteme findings pro risk breakdown
        findings = supabase.table("findings").select("risk_level").eq("scan_id", scan_id).execute()
        high_f = sum(1 for f in findings.data if f.get("risk_level") == "high")

        # Skutečná délka skenu z DB
        scan_duration = body.scan_duration_s
        if scan.get("started_at") and scan.get("finished_at"):
            try:
                t0 = datetime.fromisoformat(scan["started_at"].replace("Z", "+00:00"))
                t1 = datetime.fromisoformat(scan["finished_at"].replace("Z", "+00:00"))
                scan_duration = (t1 - t0).total_seconds()
            except Exception:
                pass

        # Zalogujeme do analytics tabulky
        from backend.api.analytics import track_server_event
        track_server_event(
            event_name="scan_results_viewed",
            properties={
                "scan_id": scan_id,
                "url": scan.get("url_scanned"),
                "time_on_results_s": body.time_on_results_s,
                "client_waited": body.client_waited,
                "total_findings": scan.get("total_findings", 0),
                "high_findings": high_f,
            },
        )

        # Odešleme email notifikaci
        from backend.monitoring.admin_notifier import notify_scan_results_viewed
        await notify_scan_results_viewed(
            scan_id=scan_id,
            url=scan.get("url_scanned", ""),
            company_name=company_name,
            total_findings=scan.get("total_findings", 0) or len(findings.data),
            high_findings=high_f,
            time_on_results_s=body.time_on_results_s,
            scan_duration_s=scan_duration,
            client_waited=body.client_waited,
            triggered_by=triggered_by,
        )

        # Uložíme info o zhlédnutí do scans tabulky
        supabase.table("scans").update({
            "results_viewed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", scan_id).execute()

        return {"status": "ok", "message": "Notifikace odeslána"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Scan] results-viewed selhalo: {e}")
        return {"status": "error", "message": str(e)}