"""
AIshield.cz — Hlavní FastAPI aplikace
Vstupní bod backendu. Všechny routery se registrují zde.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Načíst .env soubor (relativně k hlavnímu adresáři projektu)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from backend.api.health import router as health_router
from backend.api.scan import router as scan_router
from backend.api.questionnaire import router as questionnaire_router
from backend.api.documents import router as documents_router
from backend.api.payments import router as payments_router
from backend.api.dashboard import router as dashboard_router
from backend.api.admin import router as admin_router
from backend.api.admin_crm import router as admin_crm_router
from backend.api.unsubscribe import router as unsubscribe_router
from backend.api.widget import router as widget_router
from backend.api.agency import router as agency_router
from backend.api.enterprise import router as enterprise_router
from backend.api.send_report import router as send_report_router
from backend.api.ares_lookup import router as ares_lookup_router
from backend.security.export import router as export_router

# ── Vytvoření aplikace ──
from backend.config import get_settings as _get_settings
_cfg = _get_settings()

app = FastAPI(
    title="AIshield.cz API",
    description="🛡️ AI Act Compliance Scanner — API pro skenování webů, "
                "klasifikaci AI systémů a generování compliance dokumentů.",
    version="0.1.0",
    docs_url="/docs" if _cfg.debug else None,
    redoc_url="/redoc" if _cfg.debug else None,
    openapi_url="/openapi.json" if _cfg.debug else None,
)

# ── CORS — povolení volání z frontendu ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",        # Next.js dev server
        "https://aishield.cz",          # Produkce
        "https://www.aishield.cz",      # Produkce s www
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)

# ── Registrace routerů ──
app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(scan_router, prefix="/api", tags=["Scanner"])
app.include_router(questionnaire_router, prefix="/api", tags=["Questionnaire"])
app.include_router(documents_router, prefix="/api", tags=["Documents"])
app.include_router(payments_router, prefix="/api/payments", tags=["Payments"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
app.include_router(admin_crm_router, prefix="/api/admin", tags=["Admin CRM"])
app.include_router(unsubscribe_router, prefix="/api", tags=["Unsubscribe"])
app.include_router(widget_router, prefix="/api", tags=["Widget"])
app.include_router(agency_router, prefix="/api/admin", tags=["Agency"])
app.include_router(enterprise_router, prefix="/api", tags=["Enterprise"])
app.include_router(send_report_router, prefix="/api", tags=["SendReport"])
app.include_router(ares_lookup_router, prefix="/api", tags=["ARES"])
app.include_router(export_router, prefix="/api/admin", tags=["Export"])


@app.get("/")
async def root():
    """Kořenový endpoint — info o API."""
    return {
        "name": "🛡️ AIshield.cz API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
        "message": "Váš štít proti pokutám EU za AI Act.",
    }
