# 🛡️ AIshield.cz — AI Act Compliance Scanner

**Váš štít proti pokutám EU za AI Act.**

Automatizovaný nástroj pro české firmy, který skenuje weby, detekuje AI systémy a generuje compliance dokumentaci podle EU AI Act (Nařízení 2024/1689).

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
| Frontend | Next.js 14 + Tailwind + shadcn/ui | Vercel (zdarma) |
| Backend API | Python FastAPI | Railway ($5/měsíc) |
| Databáze | PostgreSQL | Supabase (zdarma) |
| AI Engine | Claude API (Anthropic) | — |
| Scanner | Playwright (headless Chromium) | Wedos VPS |
| PDF | WeasyPrint | — |
| Platby | Stripe | — |
| Email | Resend | — |
| Doména | aishield.cz | Wedos |

## 📋 Deadlines

- **AI Act čl. 4 + čl. 5**: platí OD 2.2.2025
- **AI Act čl. 26 + čl. 50**: platí OD 2.8.2026 (za 6 měsíců)

## 👤 Autor

Martin Haynes — [desperados-design.cz](https://www.desperados-design.cz)  
IČO: 17889251
