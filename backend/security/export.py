"""
AIshield.cz — Šifrovaný export zákaznických dat
Admin endpoint pro stažení kompletních dat firmy jako šifrovaný JSON.
Používá Fernet (AES-128-CBC) symetrické šifrování.
"""

import io
import json
import logging
import zipfile
from datetime import datetime, timezone

from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response

from backend.api.auth import AuthUser, require_admin
from backend.config import get_settings
from backend.database import get_supabase
from backend.security import log_access

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_fernet() -> Fernet:
    """Vrátí Fernet cipher s klíčem z env."""
    settings = get_settings()
    key = getattr(settings, "data_export_key", "")
    if not key:
        raise HTTPException(
            status_code=500,
            detail="DATA_EXPORT_KEY není nastaven v .env — "
                   "vygeneruj klíč: python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'",
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def _collect_company_data(company_id: str) -> dict:
    """Shromáždí VŠECHNA data firmy z DB."""
    supabase = get_supabase()

    # 1. Firma
    company = supabase.table("companies").select("*").eq("id", company_id).execute()
    if not company.data:
        raise HTTPException(status_code=404, detail="Firma nenalezena")

    company_info = company.data[0]
    company_name = company_info.get("name", "?")

    # 2. Klienti
    clients = supabase.table("clients").select("*").eq("company_id", company_id).execute()
    client_ids = [c["id"] for c in (clients.data or [])]

    # 3. Dotazník
    questionnaire = []
    for cid in client_ids:
        q = supabase.table("questionnaire_responses").select("*").eq("client_id", cid).execute()
        questionnaire.extend(q.data or [])

    # 4. Skeny
    scans = supabase.table("scans").select("*").eq("company_id", company_id).execute()
    scan_ids = [s["id"] for s in (scans.data or [])]

    # 5. Findings
    findings = []
    for sid in scan_ids:
        f = supabase.table("findings").select("*").eq("scan_id", sid).execute()
        findings.extend(f.data or [])

    # 6. Dokumenty
    documents = []
    for cid in client_ids:
        d = supabase.table("documents").select("*").eq("client_id", cid).execute()
        documents.extend(d.data or [])

    # 7. Alerty
    alerts = []
    for cid in client_ids:
        a = supabase.table("alerts").select("*").eq("client_id", cid).execute()
        alerts.extend(a.data or [])

    # 8. Objednávky (podle emailu firmy)
    orders = []
    email = company_info.get("email")
    if email:
        o = supabase.table("orders").select("*").eq("email", email).execute()
        orders = o.data or []

    # 9. Scan diffs
    diffs = supabase.table("scan_diffs").select("*").eq("company_id", company_id).execute()

    return {
        "export_info": {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "company_id": company_id,
            "company_name": company_name,
            "format_version": "1.0",
        },
        "company": company_info,
        "clients": clients.data or [],
        "questionnaire_responses": questionnaire,
        "scans": scans.data or [],
        "findings": findings,
        "documents": documents,
        "alerts": alerts,
        "orders": orders,
        "scan_diffs": diffs.data or [],
    }


@router.get("/export/{company_id}")
async def admin_export_company(
    company_id: str,
    request: Request,
    user: AuthUser = Depends(require_admin),
    encrypted: bool = True,
):
    """
    Exportuje kompletní data firmy jako šifrovaný nebo nešifrovaný ZIP.

    - encrypted=true (default): ZIP obsahuje `data.enc` (Fernet šifrovaný JSON)
    - encrypted=false: ZIP obsahuje `data.json` (plaintext, jen pro debug)

    Dešifrování:
      from cryptography.fernet import Fernet
      f = Fernet(b"<DATA_EXPORT_KEY>")
      data = json.loads(f.decrypt(open("data.enc","rb").read()))
    """
    # Shromáždíme data
    data = _collect_company_data(company_id)
    company_name = data["export_info"]["company_name"]

    # Audit log
    await log_access(
        actor_email=user.email,
        action="export",
        resource_type="company",
        resource_id=company_id,
        resource_detail=f"Export: {company_name}",
        request=request,
        metadata={
            "encrypted": encrypted,
            "records": {
                "questionnaire": len(data["questionnaire_responses"]),
                "scans": len(data["scans"]),
                "findings": len(data["findings"]),
            },
        },
    )

    # JSON serialize
    json_bytes = json.dumps(data, ensure_ascii=False, indent=2, default=str).encode("utf-8")

    # Vytvořit ZIP
    buf = io.BytesIO()
    safe_name = (
        company_name.lower()
        .replace(" ", "_")
        .replace(".", "_")
        .replace("/", "_")
    )[:50]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    zip_filename = f"aishield_export_{safe_name}_{timestamp}"

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        if encrypted:
            fernet = _get_fernet()
            encrypted_data = fernet.encrypt(json_bytes)
            zf.writestr("data.enc", encrypted_data)
            zf.writestr("README.txt",
                "AIshield.cz — Šifrovaný export dat\n"
                "====================================\n\n"
                "Soubor data.enc je šifrovaný pomocí Fernet (AES-128-CBC).\n\n"
                "Dešifrování v Pythonu:\n"
                "  from cryptography.fernet import Fernet\n"
                "  import json\n"
                "  f = Fernet(b'<VÁŠ_DATA_EXPORT_KEY>')\n"
                "  data = json.loads(f.decrypt(open('data.enc','rb').read()))\n"
                "  print(json.dumps(data, indent=2, ensure_ascii=False))\n\n"
                f"Exportováno: {data['export_info']['exported_at']}\n"
                f"Firma: {company_name}\n"
            )
        else:
            zf.writestr("data.json", json_bytes)

    buf.seek(0)

    logger.info(
        f"[Export] Admin {user.email} exportoval data firmy {company_name} "
        f"({company_id}), encrypted={encrypted}, size={buf.getbuffer().nbytes}B"
    )

    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{zip_filename}.zip"',
            "X-Export-Encrypted": str(encrypted).lower(),
        },
    )


@router.get("/export/{company_id}/preview")
async def admin_export_preview(
    company_id: str,
    request: Request,
    user: AuthUser = Depends(require_admin),
):
    """
    Vrátí přehled dat firmy BEZ samotných dat — jen počty záznamů.
    Užitečné pro kontrolu před exportem.
    """
    supabase = get_supabase()

    company = supabase.table("companies").select("id, name, url, email").eq("id", company_id).execute()
    if not company.data:
        raise HTTPException(status_code=404, detail="Firma nenalezena")

    company_info = company.data[0]

    clients = supabase.table("clients").select("id").eq("company_id", company_id).execute()
    client_ids = [c["id"] for c in (clients.data or [])]

    q_count = 0
    for cid in client_ids:
        q = supabase.table("questionnaire_responses").select("id", count="exact").eq("client_id", cid).execute()
        q_count += q.count or len(q.data or [])

    scans = supabase.table("scans").select("id", count="exact").eq("company_id", company_id).execute()
    scan_count = scans.count or len(scans.data or [])

    scan_ids = [s["id"] for s in (scans.data or [])]
    f_count = 0
    for sid in scan_ids:
        f = supabase.table("findings").select("id", count="exact").eq("scan_id", sid).execute()
        f_count += f.count or len(f.data or [])

    await log_access(
        actor_email=user.email,
        action="view",
        resource_type="company",
        resource_id=company_id,
        resource_detail=f"Preview: {company_info.get('name', '?')}",
        request=request,
    )

    return {
        "company": company_info,
        "record_counts": {
            "clients": len(client_ids),
            "questionnaire_responses": q_count,
            "scans": scan_count,
            "findings": f_count,
        },
    }
