# AIshield.cz — Copilot Agent Instructions

## Projekt
AIshield.cz je AI Act compliance scanner pro české firmy. Skenuje weby, detekuje AI systémy a generuje compliance dokumentaci podle EU AI Act (Nařízení 2024/1689).

## Architektura

### Backend (Python FastAPI) — `/backend/`
- **API:** `backend/api/` — FastAPI endpointy (questionnaire, scanner, admin CRM, auth)
- **Scanner:** `backend/scanner/` — Playwright, skenování webů
- **AI Engine:** `backend/ai_engine/` — Claude API, klasifikace nálezů
- **Documents:** `backend/documents/` — WeasyPrint, generování PDF
- **Monitoring:** `backend/monitoring/` — cron joby, diff engine
- **Prospecting:** `backend/prospecting/` — ARES, hledání firem
- **Outbound:** `backend/outbound/` — email engine (Resend)
- **Security:** `backend/security/` — rate limiting, auth middleware
- **Config:** `backend/config.py` — centrální konfigurace
- **DB:** `backend/database.py` — Supabase klient
- **Vstupní bod:** `backend/main.py` — FastAPI app

### Frontend (Next.js 14) — `/frontend/`
- Framework: Next.js 14 + Tailwind CSS + TypeScript
- App Router: `frontend/src/app/`
- Klíčové stránky:
  - `/dotaznik` — interaktivní dotazník (AI Act compliance)
  - `/admin` — CRM dashboard
  - `/dashboard` — klientský dashboard
  - `/scan` — výsledky skenování
  - `/pricing` — ceník

### Databáze (Supabase/PostgreSQL)
- Migrace: `database/` a `migrations/`
- Hlavní tabulky: `companies`, `clients`, `scans`, `scan_findings`, `questionnaire_answers`

### Widget — `/widget/`
- JavaScript widget pro weby klientů

## Hosting a deploy
- **Frontend:** Vercel (https://aishield.cz)
- **Backend API:** Hetzner VPS 46.28.110.102, cesta `/opt/aishield/`, systemd service `aishield-api`
- **DB:** Supabase (rsxwqcrkttlfnqbjgpgc.supabase.co)
- **Deploy backend:** `scp` soubory na VPS → `systemctl restart aishield-api`
- **Deploy frontend:** `cd frontend && npx vercel deploy --prod`

## Jazyk a lokalizace
- UI a texty jsou **česky** (čeština)
- Kód, komentáře a commit messages mohou být česky i anglicky
- AI Act citace odkazují na originální EU nařízení 2024/1689

## Konvence kódu

### Python (backend)
- Python 3.11+
- FastAPI s async/await
- Supabase Python klient pro DB
- Logování přes `logging` modul
- Typy: type hints všude

### TypeScript/React (frontend)
- Next.js 14 App Router
- Tailwind CSS pro styling
- "use client" direktivy kde je potřeba
- Komponenty v `frontend/src/components/`

## Testování
- E2E testy: `test_mega_e2e.py` (52 testů), `test_email_e2e.py`, `test_questionnaire_e2e.py`
- Spouštění: `python3 test_questionnaire_e2e.py --live` (proti produkci)
- CI/CD: GitHub Actions — testy musí projít před deploy

## Důležitá pravidla pro agenta
1. **Před změnou** vždy přečti existující kód a pochop strukturu
2. **Po změně backendu** — soubory se musí nahrát na VPS a restartovat service
3. **Po změně frontendu** — deploy přes Vercel
4. **Dotazník** (`backend/api/questionnaire.py`) má 9 sekcí, 27 otázek — při přidávání otázky dodržuj existující strukturu (key, label, type, help_text, risk_hint, followup atd.)
5. **Nekombinuj** backend a frontend změny do jednoho PR pokud to není nutné
6. **Piš testy** pro novou funkcionalitu
7. **Commit messages** česky, stručně, s prefixem (fix:, feat:, docs:, test:)
