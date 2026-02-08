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

# ── Vytvoření aplikace ──
app = FastAPI(
    title="AIshield.cz API",
    description="🛡️ AI Act Compliance Scanner — API pro skenování webů, "
                "klasifikaci AI systémů a generování compliance dokumentů.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
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
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Registrace routerů ──
app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(scan_router, prefix="/api", tags=["Scanner"])
app.include_router(questionnaire_router, prefix="/api", tags=["Questionnaire"])
app.include_router(documents_router, prefix="/api", tags=["Documents"])
app.include_router(payments_router, prefix="/api/payments", tags=["Payments"])


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
