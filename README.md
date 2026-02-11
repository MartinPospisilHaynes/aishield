# 🛡️ AIshield.cz — AI Act Compliance Scanner

[![CI/CD](https://github.com/MartinPospisilHaynes/aishield/actions/workflows/ci.yml/badge.svg)](https://github.com/MartinPospisilHaynes/aishield/actions/workflows/ci.yml)
[![Monitoring](https://github.com/MartinPospisilHaynes/aishield/actions/workflows/monitoring.yml/badge.svg)](https://github.com/MartinPospisilHaynes/aishield/actions/workflows/monitoring.yml)

**Váš štít proti pokutám EU za AI Act.**

Automatizovaný nástroj pro české firmy, který skenuje weby, detekuje AI systémy a generuje compliance dokumentaci podle EU AI Act (Nařízení 2024/1689).

## 🌐 Live

| Služba | URL | Status |
|--------|-----|--------|
| Web | [aishield.cz](https://aishield.cz) | ![Web](https://img.shields.io/website?url=https%3A%2F%2Faishield.cz&label=web) |
| API | [api.aishield.cz](https://api.aishield.cz) | ![API](https://img.shields.io/website?url=https%3A%2F%2Fapi.aishield.cz%2Fapi%2Fhealth&label=api) |
| Test Report | [GitHub Pages](https://martinposisilhaynes.github.io/aishield/) | auto |

## 🏗️ Architektura

```
aishield/
├── backend/          ← Python FastAPI (scanner, AI engine, API)
│   ├── scanner/      ← Playwright — skenování webů
│   ├── ai_engine/    ← Claude API — klasifikace nálezů
│   ├── documents/    ← WeasyPrint — generování PDF
│   ├── api/          ← FastAPI endpointy
│   ├── monitoring/   ← Cron joby, diff engine, alerty
│   ├── prospecting/  ← ARES, hledání firem
│   └── outbound/     ← Robot Lovec, email engine
├── frontend/         ← Next.js 14 (landing, dashboard, dotazník)
├── widget/           ← JavaScript widget pro weby klientů
├── database/         ← SQL migrace, schémata
├── docs/             ← Dokumentace
└── scripts/          ← Utility skripty
```

## 🚀 Tech Stack

| Komponenta | Technologie | Hosting |
|---|---|---|
| Frontend | Next.js 14 + Tailwind CSS | Vercel |
| Backend API | Python FastAPI | Hetzner VPS |
| Databáze | PostgreSQL | Supabase |
| AI Engine | Claude API (Anthropic) | — |
| Scanner | Playwright (headless Chromium) | VPS |
| Platby | GoPay | — |
| Email | Resend | — |
| CI/CD | GitHub Actions | GitHub Pro |
| Monitoring | GitHub Actions (2x denně) | GitHub Pro |
| Test Reports | GitHub Pages | GitHub Pro |

## 🧪 Testování

**52 automatických testů ve 14 fázích** — spuštění: `python3 test_mega_e2e.py`

## 🔄 CI/CD Pipeline

```
Push na main
  │
  ├─ 🐍 Backend syntax check
  ├─ ⚛️ Frontend build
  │
  └─ 🧪 E2E testy (52 testů)
       │
       ├─ ✅ Pass → 🚀 Deploy backend + frontend
       │            📄 Publish report (GitHub Pages)
       │
       └─ ❌ Fail → ⛔ Deploy ZABLOKOVÁN
```

## 📋 Deadlines

- **AI Act čl. 4 + čl. 5**: platí OD 2.2.2025 ✅
- **AI Act čl. 26 + čl. 50**: platí OD 2.8.2026 ⏳

## 🔒 Security

Viz [SECURITY.md](SECURITY.md)

## 👤 Autor

Martin Haynes — [desperados-design.cz](https://www.desperados-design.cz)  
IČO: 17889251 | [info@aishield.cz](mailto:info@aishield.cz)
