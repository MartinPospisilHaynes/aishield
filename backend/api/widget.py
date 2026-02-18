"""
AIshield.cz — Widget Auto-Update API (Úkol 32)
Dynamické aktualizace compliance widgetu napojeného na monitoring.

Widget = JS snippet vložený na web klienta, který zobrazuje
compliance status (AI systémy, rizika, transparenční texty).

Při změně (nový sken, legislativní update) se config widgetu
automaticky aktualizuje — klient nemusí nic dělat.

Cache: max 1 hodina (widget si stahuje config přes API).
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from datetime import datetime, timezone
from backend.database import get_supabase

router = APIRouter()


# ── Widget Config Model ──


class WidgetConfigUpdate(BaseModel):
    """Manuální aktualizace widgetu (např. legislativní změna)."""
    custom_text: str | None = None
    custom_banner: str | None = None
    ai_act_deadline: str | None = None
    show_badge: bool | None = None


# ── Endpointy ──


@router.get("/widget/{company_id}/config")
async def get_widget_config(company_id: str):
    """
    Vrátí aktuální konfiguraci widgetu pro danou firmu.
    Widget si volá tento endpoint a zobrazuje compliance info.
    Cachováno na 1 hodinu (Cache-Control header).
    """
    supabase = get_supabase()

    # Načteme firmu
    company = supabase.table("companies").select(
        "id, name, url"
    ).eq("id", company_id).limit(1).execute()

    if not company.data:
        raise HTTPException(status_code=404, detail="Firma nenalezena")

    comp = company.data[0]

    # Načteme poslední sken
    last_scan = supabase.table("scans").select(
        "id, total_findings, finished_at, status"
    ).eq("company_id", company_id).eq(
        "status", "done"
    ).order("created_at", desc=True).limit(1).execute()

    # Načteme findings z posledního skenu
    findings_data = []
    total_findings = 0

    if last_scan.data:
        scan_id = last_scan.data[0]["id"]
        total_findings = last_scan.data[0].get("total_findings", 0)

        findings = supabase.table("findings").select(
            "name, category, risk_level, ai_act_article, action_required"
        ).eq("scan_id", scan_id).neq(
            "source", "ai_classified_fp"
        ).order("risk_level", desc=True).execute()

        findings_data = [
            {
                "name": f["name"],
                "category": f["category"],
                "risk_level": f["risk_level"],
                "article": f["ai_act_article"],
                "action": f["action_required"],
            }
            for f in (findings.data or [])
        ]

    # Načteme widget config (pokud existuje custom override)
    widget_cfg = supabase.table("widget_configs").select("*").eq(
        "company_id", company_id
    ).limit(1).execute()

    custom = widget_cfg.data[0] if widget_cfg.data else {}

    # Sestav config
    config = {
        "company_id": company_id,
        "company_name": comp.get("name", ""),
        "url": comp.get("url", ""),
        "version": custom.get("version", 1),
        "last_scan": last_scan.data[0].get("finished_at") if last_scan.data else None,
        "total_ai_systems": total_findings,
        "ai_systems": findings_data,
        "compliance": {
            "status": _compute_compliance_status(findings_data),
            "deadline": custom.get("ai_act_deadline", "2026-08-02"),
            "days_remaining": (datetime(2026, 8, 2) - datetime.utcnow()).days,
        },
        "display": {
            "show_badge": custom.get("show_badge", True),
            "badge_text": custom.get("custom_text") or _default_badge_text(total_findings),
            "banner": custom.get("custom_banner", ""),
            "language": "cs",
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    # Cache-Control: 1 hodina
    response = JSONResponse(content=config)
    response.headers["Cache-Control"] = "public, max-age=3600"
    response.headers["Access-Control-Allow-Origin"] = "*"  # Widget na cizí doméně
    return response


@router.put("/widget/{company_id}/config")
async def update_widget_config(company_id: str, update: WidgetConfigUpdate):
    """
    Manuální aktualizace widgetu (admin / legislativní změna).
    Upsert do widget_configs tabulky.
    """
    supabase = get_supabase()

    # Ověříme, že firma existuje
    comp = supabase.table("companies").select("id").eq(
        "id", company_id
    ).limit(1).execute()
    if not comp.data:
        raise HTTPException(status_code=404, detail="Firma nenalezena")

    # Připravíme data pro update
    update_data = {"company_id": company_id, "updated_at": datetime.utcnow().isoformat()}
    if update.custom_text is not None:
        update_data["custom_text"] = update.custom_text
    if update.custom_banner is not None:
        update_data["custom_banner"] = update.custom_banner
    if update.ai_act_deadline is not None:
        update_data["ai_act_deadline"] = update.ai_act_deadline
    if update.show_badge is not None:
        update_data["show_badge"] = update.show_badge

    # Zvýšit verzi
    existing = supabase.table("widget_configs").select("version").eq(
        "company_id", company_id
    ).limit(1).execute()
    current_version = existing.data[0]["version"] if existing.data else 0
    update_data["version"] = current_version + 1

    # Upsert
    supabase.table("widget_configs").upsert(
        update_data, on_conflict="company_id"
    ).execute()

    return {
        "company_id": company_id,
        "version": update_data["version"],
        "updated": True,
    }


@router.post("/widget/update-all")
async def update_all_widgets(request: Request):
    """
    Admin endpoint: Aktualizuje texty pro VŠECHNY klienty.
    Používá se při legislativní změně.
    """
    supabase = get_supabase()
    body = await request.json()
    custom_banner = body.get("banner", "")
    custom_text = body.get("text", "")

    # Všichni klienti s aktivním widgetem (paid orders)
    orders = supabase.table("orders").select(
        "user_email"
    ).eq("status", "paid").execute()

    unique_emails = list(set(row["user_email"] for row in (orders.data or [])))
    updated = 0

    for email in unique_emails:
        comp = supabase.table("companies").select("id").eq(
            "email", email
        ).limit(1).execute()

        if not comp.data:
            continue

        company_id = comp.data[0]["id"]

        existing = supabase.table("widget_configs").select("version").eq(
            "company_id", company_id
        ).limit(1).execute()
        version = (existing.data[0]["version"] if existing.data else 0) + 1

        supabase.table("widget_configs").upsert({
            "company_id": company_id,
            "custom_banner": custom_banner,
            "custom_text": custom_text,
            "version": version,
            "updated_at": datetime.utcnow().isoformat(),
        }, on_conflict="company_id").execute()
        updated += 1

    return {"updated_clients": updated, "message": f"Widget config aktualizován pro {updated} klientů"}


@router.get("/widget/{company_id}/embed.js")
async def get_widget_embed(company_id: str):
    """
    Vrátí JS embed kód widgetu.
    Klient vloží <script src="https://api.aishield.cz/api/widget/{id}/embed.js">
    a widget se automaticky zobrazí.
    """
    js_code = f"""
(function() {{
    var API = "https://api.aishield.cz/api/widget/{company_id}/config";
    var container = document.createElement("div");
    container.id = "aishield-widget";
    container.style.cssText = "position:fixed;bottom:20px;right:20px;z-index:9999;font-family:-apple-system,sans-serif;";

    fetch(API)
        .then(function(r) {{ return r.json(); }})
        .then(function(cfg) {{
            if (!cfg.display.show_badge) return;

            var count = cfg.total_ai_systems;
            var status = cfg.compliance.status;
            var days = cfg.compliance.days_remaining;
            var color = status === "compliant" ? "#22c55e" : status === "at_risk" ? "#f97316" : "#ef4444";

            container.innerHTML = '<div style="background:#0f172a;border:1px solid ' + color + '44;border-radius:12px;padding:12px 16px;color:white;font-size:13px;box-shadow:0 4px 20px rgba(0,0,0,0.3);cursor:pointer;min-width:200px;">'
                + '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">'
                + '<span style="width:8px;height:8px;border-radius:50%;background:' + color + ';"></span>'
                + '<strong style="color:#e879f9;">AI</strong><strong>shield</strong>'
                + '</div>'
                + '<div style="color:#94a3b8;font-size:11px;">' + cfg.display.badge_text + '</div>'
                + (cfg.display.banner ? '<div style="margin-top:6px;padding:6px 8px;background:' + color + '22;border-radius:6px;font-size:11px;color:' + color + ';">' + cfg.display.banner + '</div>' : '')
                + '</div>';

            document.body.appendChild(container);
        }})
        .catch(function(e) {{ console.log("AIshield widget error:", e); }});
}})();
"""
    return Response(
        content=js_code,
        media_type="application/javascript",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/widget/{company_id}/bundle.js")
async def get_widget_bundle(company_id: str):
    """
    Vrátí Web Component widget bundle (<3 KB gzipped).
    Shadow DOM, zero dependencies, chatbot detection.

    Klient vloží:
      <script src="https://api.aishield.cz/api/widget/{id}/bundle.js" defer></script>
    
    Widget se automaticky vytvoří a zobrazí.
    GDPR: Nepotřebuje cookie souhlas (pouze informační).
    """
    import os
    widget_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "widget", "aishield-widget.js"
    )

    try:
        with open(widget_path, "r", encoding="utf-8") as f:
            js_code = f.read()
    except FileNotFoundError:
        # Fallback: jednoduchý inline widget
        js_code = f"""
(function(){{
    var el=document.createElement('div');
    el.style.cssText='position:fixed;bottom:20px;right:20px;z-index:9999;background:#0f172a;border:1px solid rgba(232,121,249,0.3);border-radius:12px;padding:10px 14px;color:#f1f5f9;font-family:-apple-system,sans-serif;font-size:13px;box-shadow:0 4px 24px rgba(0,0,0,0.4);';
    el.innerHTML='<strong style="color:#e879f9">AI</strong><strong>shield</strong>';
    document.body.appendChild(el);
}})();
"""

    return Response(
        content=js_code,
        media_type="application/javascript",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*",
        },
    )


# ── Auto-update po novém skenu ──


async def auto_update_widget_after_scan(company_id: str, scan_id: str):
    """
    Voláno po dokončení monitoring skenu.
    Automaticky aktualizuje widget config s novými findings.
    """
    supabase = get_supabase()

    existing = supabase.table("widget_configs").select("version").eq(
        "company_id", company_id
    ).limit(1).execute()

    if not existing.data:
        return  # Widget neexistuje → nic neděláme

    version = existing.data[0]["version"] + 1

    supabase.table("widget_configs").update({
        "version": version,
        "updated_at": datetime.utcnow().isoformat(),
    }).eq("company_id", company_id).execute()

    return {"company_id": company_id, "version": version}


# ── Helpery ──


def _compute_compliance_status(findings: list[dict]) -> str:
    """Compliance status dle findings."""
    if not findings:
        return "no_data"

    high_risk = sum(1 for f in findings if f.get("risk_level") in ("high", "critical"))

    if high_risk == 0:
        return "compliant"
    elif high_risk <= 2:
        return "at_risk"
    else:
        return "non_compliant"


def _default_badge_text(total_findings: int) -> str:
    """Výchozí text badge."""
    if total_findings == 0:
        return "Žádné AI systémy detekovány"
    elif total_findings == 1:
        return "1 AI systém detekován — AI Act compliance"
    else:
        return f"{total_findings} AI systémů — AI Act compliance"
