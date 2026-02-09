-- ============================================
-- AIshield.cz — Migrace 002: Synchronizace DB se skutečným kódem
-- ============================================
-- Datum: 9. února 2026
-- Popis: Kód se vyvinul dál než původní schéma 001.
--        Tato migrace:
--        1. Přidá chybějící sloupce do companies, findings
--        2. Předělá prázdné tabulky (documents, alerts, widget_configs) na schéma, které kód skutečně používá
--        3. Vytvoří nové tabulky: email_log, email_events, email_blacklist, scan_diffs, orders, orchestrator_log, agency_batches
-- ============================================

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 1. ALTER companies — přidat ~22 chybějících sloupců
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ALTER TABLE companies ADD COLUMN IF NOT EXISTS scan_status VARCHAR(50);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS prospecting_status VARCHAR(50);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS last_scan_id UUID REFERENCES scans(id);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS scanned_at TIMESTAMPTZ;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS total_findings INTEGER DEFAULT 0;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS category VARCHAR(200);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS nace_codes JSONB;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS region VARCHAR(200);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS legal_form VARCHAR(200);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS email_valid BOOLEAN DEFAULT TRUE;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS email_source VARCHAR(100);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS email_confidence FLOAT;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS emails_sent INTEGER DEFAULT 0;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS last_email_at TIMESTAMPTZ;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS heureka_rating FLOAT;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS heureka_reviews INTEGER;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS lead_score INTEGER;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS lead_tier VARCHAR(10);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS partner VARCHAR(100);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS partner_notes TEXT;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS contact_name VARCHAR(500);

-- Nové indexy na companies
CREATE INDEX IF NOT EXISTS idx_companies_scan_status ON companies(scan_status);
CREATE INDEX IF NOT EXISTS idx_companies_prospecting_status ON companies(prospecting_status);
CREATE INDEX IF NOT EXISTS idx_companies_partner ON companies(partner);
CREATE INDEX IF NOT EXISTS idx_companies_email ON companies(email);
CREATE INDEX IF NOT EXISTS idx_companies_lead_tier ON companies(lead_tier);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 2. ALTER findings — přidat status sloupec
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ALTER TABLE findings ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'open';

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 3. DROP + RECREATE: documents (0 řádků, nekompatibilní schéma)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Kód používá company_id (ne client_id), name, url, format, size_bytes

DROP POLICY IF EXISTS "Clients can view own documents" ON documents;
DROP TABLE IF EXISTS documents CASCADE;

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    type VARCHAR(100) NOT NULL,                -- template_key (compliance_report, ai_register, ...)
    name VARCHAR(500),                         -- lidský název dokumentu
    url TEXT,                                  -- URL souboru v Storage
    format VARCHAR(20) DEFAULT 'pdf',          -- pdf / html
    size_bytes INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_documents_company ON documents(company_id);
CREATE INDEX idx_documents_type ON documents(type);

ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Clients can view own documents" ON documents
    FOR SELECT USING (
        company_id IN (
            SELECT company_id FROM clients WHERE auth_user_id = auth.uid()
        )
    );

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 4. DROP + RECREATE: alerts (0 řádků, nekompatibilní schéma)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Kód používá company_id, to_email, title, body_text, severity, metadata

DROP POLICY IF EXISTS "Clients can view own alerts" ON alerts;
DROP TABLE IF EXISTS alerts CASCADE;

CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    to_email VARCHAR(500) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,           -- new_ai_system, transparency_removed, behavior_change, law_change, monthly_report
    title VARCHAR(500),
    severity VARCHAR(20),                      -- critical, high, medium, info
    body_text TEXT,
    email_sent BOOLEAN DEFAULT FALSE,
    resend_id VARCHAR(200),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alerts_company ON alerts(company_id);
CREATE INDEX idx_alerts_type ON alerts(alert_type);
CREATE INDEX idx_alerts_created ON alerts(created_at DESC);

ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Clients can view own alerts" ON alerts
    FOR SELECT USING (
        company_id IN (
            SELECT company_id FROM clients WHERE auth_user_id = auth.uid()
        )
    );

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 5. DROP + RECREATE: widget_configs (0 řádků, nekompatibilní schéma)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Kód používá company_id, custom_text, custom_banner, ai_act_deadline, show_badge

DROP POLICY IF EXISTS "Clients can view own widget config" ON widget_configs;
DROP POLICY IF EXISTS "Widget config is public readable" ON widget_configs;
DROP TRIGGER IF EXISTS trg_widget_configs_updated ON widget_configs;
DROP TABLE IF EXISTS widget_configs CASCADE;

CREATE TABLE widget_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    custom_text TEXT,
    custom_banner TEXT,
    ai_act_deadline VARCHAR(20) DEFAULT '2026-08-02',
    show_badge BOOLEAN DEFAULT TRUE,
    version INTEGER DEFAULT 1,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_widget_configs_company ON widget_configs(company_id);

ALTER TABLE widget_configs ENABLE ROW LEVEL SECURITY;

-- Widget config musí být veřejně čitelný (widget na klientově webu)
CREATE POLICY "Widget config is public readable" ON widget_configs
    FOR SELECT USING (TRUE);

CREATE TRIGGER trg_widget_configs_updated
    BEFORE UPDATE ON widget_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 6. NOVÁ TABULKA: orders (kód používá orders, ne payments)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- payments tabulka zůstane (Stripe), orders = GoPay objednávky

CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(100) NOT NULL,
    gopay_payment_id BIGINT,
    plan VARCHAR(20) NOT NULL,                 -- basic, pro
    amount INTEGER NOT NULL,                   -- CZK
    email VARCHAR(500) NOT NULL,
    user_email VARCHAR(500),                   -- alias pro dashboard lookup
    status VARCHAR(50) DEFAULT 'pending',      -- pending, CREATED, PAID, TIMEOUTED, CANCELED
    paid_at TIMESTAMPTZ,
    activated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orders_gopay ON orders(gopay_payment_id);
CREATE INDEX IF NOT EXISTS idx_orders_email ON orders(email);
CREATE INDEX IF NOT EXISTS idx_orders_user_email ON orders(user_email);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);

ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Clients can view own orders" ON orders
    FOR SELECT USING (
        email = (SELECT email FROM auth.users WHERE id = auth.uid())
        OR user_email = (SELECT email FROM auth.users WHERE id = auth.uid())
    );

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 7. NOVÁ TABULKA: email_log (outbound email tracking)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Kód používá email_log, NE outbound_emails

CREATE TABLE IF NOT EXISTS email_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_ico VARCHAR(10),
    to_email VARCHAR(500) NOT NULL,
    subject VARCHAR(500),
    variant VARCHAR(20),                       -- A/B test variant
    resend_id VARCHAR(200),
    status VARCHAR(50) DEFAULT 'sent',         -- sent, delivered, opened, clicked, dry_run
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_log_sent_at ON email_log(sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_email_log_status ON email_log(status);
CREATE INDEX IF NOT EXISTS idx_email_log_to_email ON email_log(to_email);
CREATE INDEX IF NOT EXISTS idx_email_log_resend_id ON email_log(resend_id);

-- Pouze admin přístup (backend používá service_role)
ALTER TABLE email_log ENABLE ROW LEVEL SECURITY;

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 8. NOVÁ TABULKA: email_events (webhook event tracking)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CREATE TABLE IF NOT EXISTS email_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resend_id VARCHAR(200),
    to_email VARCHAR(500) NOT NULL,
    event_type VARCHAR(50) NOT NULL,           -- bounce, complaint, unsubscribe
    bounce_type VARCHAR(20),                   -- hard, soft
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_email_events_type ON email_events(event_type);
CREATE INDEX IF NOT EXISTS idx_email_events_created ON email_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_email_events_to_email ON email_events(to_email);

ALTER TABLE email_events ENABLE ROW LEVEL SECURITY;

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 9. NOVÁ TABULKA: email_blacklist
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CREATE TABLE IF NOT EXISTS email_blacklist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(500) NOT NULL,
    reason VARCHAR(100),                       -- spam_complaint, user_unsubscribed, hard_bounce
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_email_blacklist_email ON email_blacklist(email);

ALTER TABLE email_blacklist ENABLE ROW LEVEL SECURITY;

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 10. NOVÁ TABULKA: scan_diffs (porovnání skenů)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CREATE TABLE IF NOT EXISTS scan_diffs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    previous_scan_id UUID NOT NULL REFERENCES scans(id),
    current_scan_id UUID NOT NULL REFERENCES scans(id),
    has_changes BOOLEAN DEFAULT FALSE,
    added_count INTEGER DEFAULT 0,
    removed_count INTEGER DEFAULT 0,
    changed_count INTEGER DEFAULT 0,
    unchanged_count INTEGER DEFAULT 0,
    summary TEXT,
    details JSONB,                             -- {added: [...], removed: [...], changed: [...]}
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scan_diffs_company ON scan_diffs(company_id);
CREATE INDEX IF NOT EXISTS idx_scan_diffs_created ON scan_diffs(created_at DESC);

ALTER TABLE scan_diffs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Clients can view own scan diffs" ON scan_diffs
    FOR SELECT USING (
        company_id IN (
            SELECT company_id FROM clients WHERE auth_user_id = auth.uid()
        )
    );

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 11. NOVÁ TABULKA: orchestrator_log (logy automatizace)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CREATE TABLE IF NOT EXISTS orchestrator_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_name VARCHAR(100) NOT NULL,
    status VARCHAR(50),                        -- running, completed, failed
    result JSONB,
    error TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orchestrator_log_started ON orchestrator_log(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_orchestrator_log_task ON orchestrator_log(task_name);

ALTER TABLE orchestrator_log ENABLE ROW LEVEL SECURITY;

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 12. NOVÁ TABULKA: agency_batches (hromadné skeny agentury)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CREATE TABLE IF NOT EXISTS agency_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    total_clients INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'running',      -- running, completed, error
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    completed_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    results JSONB,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agency_batches_status ON agency_batches(status);
CREATE INDEX IF NOT EXISTS idx_agency_batches_created ON agency_batches(created_at DESC);

ALTER TABLE agency_batches ENABLE ROW LEVEL SECURITY;

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 13. Upravit source ENUM — přidat 'agency_client'
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Kód insertuje source='agency_client' ale ENUM to nemá.
-- Řešení: DROP NOT NULL constraint na source (kód používá VARCHAR hodnoty přímo)
-- a změnit sloupec na VARCHAR

ALTER TABLE companies ALTER COLUMN source DROP DEFAULT;
ALTER TABLE companies ALTER COLUMN source TYPE VARCHAR(50) USING source::text;
ALTER TABLE companies ALTER COLUMN source SET DEFAULT 'manual';

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 14. Přidat url_scanned alias — scans tabulka
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Kód agency.py insertuje "url" ale schéma má "url_scanned"
-- Přidáme generated column jako alias (nebo ALTER TABLE)

-- Pokud kód insertuje "url", přidáme sloupec url jako nullable
ALTER TABLE scans ADD COLUMN IF NOT EXISTS url VARCHAR(2000);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- HOTOVO
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Nové tabulky: email_log, email_events, email_blacklist, 
--               scan_diffs, orders, orchestrator_log, agency_batches
-- Předělané: documents, alerts, widget_configs
-- Rozšířené: companies (+22 sloupců), findings (+status), scans (+url)
-- Celkem: 17 tabulek (10 existujících + 7 nových)
-- ============================================
