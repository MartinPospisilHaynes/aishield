"""
AIshield.cz — Proaktivní sken klientů agentury (Úkol 35)
Naskenuje weby stávajících klientů Desperados Design a
připraví personalizované nabídky.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from backend.database import get_supabase
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Modely ──

class AgencyClient(BaseModel):
    """Stávající klient agentury."""
    name: str
    url: str
    email: str | None = None
    contact_name: str | None = None
    notes: str | None = None  # co jsme jim dělali


class AgencyBatchRequest(BaseModel):
    """Požadavek na hromadný sken klientů agentury."""
    clients: list[AgencyClient]


class PersonalEmailRequest(BaseModel):
    """Požadavek na personalizovaný email pro klienta agentury."""
    client_name: str
    contact_name: str
    url: str
    email: str
    findings_count: int | None = None
    scan_id: str | None = None


# ── Sken klientů agentury ──

async def scan_agency_client(client: AgencyClient) -> dict:
    """
    Naskenuje web jednoho klienta agentury.
    Uloží firmu do DB s tagem partner=desperados.
    """
    from backend.scanner.pipeline import run_scan_pipeline

    supabase = get_supabase()
    url = client.url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    # Zjistit, jestli firma už existuje
    existing = supabase.table("companies").select("id").eq("url", url).execute()

    if existing.data:
        company_id = existing.data[0]["id"]
        # Aktualizovat partner info
        supabase.table("companies").update({
            "partner": "desperados",
            "partner_notes": client.notes or "",
            "contact_name": client.contact_name or "",
        }).eq("id", company_id).execute()
    else:
        # Vytvořit novou firmu
        company = supabase.table("companies").insert({
            "name": client.name,
            "url": url,
            "email": client.email or "",
            "scan_status": "pending",
            "source": "agency_client",
            "partner": "desperados",
            "partner_notes": client.notes or "",
            "contact_name": client.contact_name or "",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        company_id = company.data[0]["id"]

    # Vytvořit sken
    scan = supabase.table("scans").insert({
        "company_id": company_id,
        "url_scanned": url,
        "status": "pending",
        "started_at": datetime.now(timezone.utc).isoformat(),
    }).execute()
    scan_id = scan.data[0]["id"]

    # Spustit scan pipeline
    try:
        result = await run_scan_pipeline(scan_id, url)

        # Počet nálezů
        findings = supabase.table("findings").select(
            "id", count="exact"
        ).eq("scan_id", scan_id).execute()
        findings_count = findings.count or 0

        return {
            "client_name": client.name,
            "url": url,
            "scan_id": scan_id,
            "company_id": company_id,
            "status": "completed",
            "findings_count": findings_count,
        }
    except Exception as e:
        logger.error(f"Chyba při skenu {url}: {e}")
        return {
            "client_name": client.name,
            "url": url,
            "scan_id": scan_id,
            "company_id": company_id,
            "status": "error",
            "error": str(e),
        }


async def run_agency_batch_scan(clients: list[AgencyClient]) -> dict:
    """
    Naskenuje všechny klienty agentury sekvenčně.
    Výsledky ukládá průběžně.
    """
    results = []
    total = len(clients)
    completed = 0
    errors = 0

    for client in clients:
        try:
            result = await scan_agency_client(client)
            results.append(result)
            if result["status"] == "completed":
                completed += 1
            else:
                errors += 1
            logger.info(
                f"Agency scan [{completed + errors}/{total}]: "
                f"{client.name} -> {result['status']} "
                f"({result.get('findings_count', 0)} nálezů)"
            )
        except Exception as e:
            errors += 1
            results.append({
                "client_name": client.name,
                "url": client.url,
                "status": "error",
                "error": str(e),
            })

    return {
        "total": total,
        "completed": completed,
        "errors": errors,
        "results": results,
    }


def generate_personal_email(
    client_name: str,
    contact_name: str,
    url: str,
    findings_count: int,
    scan_id: str | None = None,
) -> dict:
    """
    Vygeneruje personalizovaný email pro klienta agentury.
    NE automatický robot — osobní email od Martina.
    Vrací subject + body pro ruční odeslání.
    """
    first_name = contact_name.split()[0] if contact_name else "dobrý den"

    report_link = f"https://aishield.cz/scan?id={scan_id}" if scan_id else "https://aishield.cz/scan"

    subject = f"AI Act a váš web {url} — co je potřeba upravit"

    body = f"""Ahoj {first_name},

dělal jsem vám web {url} a v rámci nové služby jsem ho proaktivně prověřil kvůli novému zákonu EU o umělé inteligenci (AI Act), který platí od srpna 2026.

Na vašem webu jsem našel {findings_count} AI systém{'ů' if findings_count != 1 else ''}, {'které potřebují' if findings_count != 1 else 'který potřebuje'} úpravu podle nových pravidel.

Připravil jsem vám detailní report: {report_link}

Co to znamená v praxi:
→ Chatbot / analytika / personalizace na webu musí splňovat nová pravidla
→ Je potřeba přidat transparenční informace pro uživatele
→ Deadline je 2. srpna 2026 — zbývá méně než 6 měsíců

Vytvořil jsem na to specializovaný nástroj (AIshield.cz), který to řeší automaticky — sken, dokumenty, monitoring. Jako můj stávající klient máte 20% slevu.

Mám vám s tím pomoci? Stačí odpovědět na tento email.

S pozdravem,
Martin Haynes
Desperados Design
+420 732 716 141
info@desperados-design.cz"""

    return {
        "to": f"{contact_name} <{url}>",
        "subject": subject,
        "body": body,
        "client_name": client_name,
    }


# ── API Endpointy ──

@router.post("/agency/scan-batch")
async def agency_batch_scan(
    request: AgencyBatchRequest,
    background_tasks: BackgroundTasks,
):
    """
    Spustí hromadný sken klientů agentury na pozadí.
    Vrátí ihned potvrzení, výsledky se ukládají do DB.
    """
    if not request.clients:
        raise HTTPException(status_code=400, detail="Seznam klientů je prázdný")

    if len(request.clients) > 50:
        raise HTTPException(status_code=400, detail="Max 50 klientů najednou")

    # Uložit batch do DB pro tracking
    supabase = get_supabase()
    batch = supabase.table("agency_batches").insert({
        "total_clients": len(request.clients),
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
    }).execute()
    batch_id = batch.data[0]["id"]

    async def _run():
        try:
            result = await run_agency_batch_scan(request.clients)
            supabase.table("agency_batches").update({
                "status": "completed",
                "completed_count": result["completed"],
                "error_count": result["errors"],
                "results": result["results"],
                "finished_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", batch_id).execute()
        except Exception as e:
            logger.error(f"Agency batch scan error: {e}")
            supabase.table("agency_batches").update({
                "status": "error",
                "error": str(e),
                "finished_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", batch_id).execute()

    background_tasks.add_task(_run)

    return {
        "batch_id": batch_id,
        "total_clients": len(request.clients),
        "status": "started",
        "message": f"Spuštěn hromadný sken {len(request.clients)} klientů agentury",
    }


@router.get("/agency/scan-batch/{batch_id}")
async def agency_batch_status(batch_id: str):
    """Vrátí stav hromadného skenu."""
    supabase = get_supabase()
    res = supabase.table("agency_batches").select("*").eq("id", batch_id).execute()

    if not res.data:
        raise HTTPException(status_code=404, detail="Batch nenalezen")

    return res.data[0]


@router.get("/agency/clients")
async def agency_clients():
    """Vrátí všechny firmy s partner=desperados."""
    supabase = get_supabase()
    res = supabase.table("companies").select(
        "*"
    ).eq("partner", "desperados").order("created_at", desc=True).execute()

    return {"clients": res.data or [], "total": len(res.data or [])}


@router.post("/agency/generate-email")
async def agency_generate_email(request: PersonalEmailRequest):
    """
    Vygeneruje personalizovaný email pro klienta agentury.
    Vrací text k ručnímu odeslání (NE automaticky).
    """
    # Pokud nemáme počet nálezů, zjistíme z DB
    findings_count = request.findings_count or 0
    if request.scan_id and not request.findings_count:
        supabase = get_supabase()
        res = supabase.table("findings").select(
            "id", count="exact"
        ).eq("scan_id", request.scan_id).execute()
        findings_count = res.count or 0

    email = generate_personal_email(
        client_name=request.client_name,
        contact_name=request.contact_name or request.client_name,
        url=request.url,
        findings_count=findings_count,
        scan_id=request.scan_id,
    )

    return email
