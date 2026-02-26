-- ============================================
-- AIshield.cz — Databázové schéma v1.0
-- ============================================
-- Migrace: 001_initial_schema.sql
-- Datum: 8. února 2026
-- Databáze: Supabase PostgreSQL
-- ============================================

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- ENUM TYPY
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CREATE TYPE company_source AS ENUM ('ares', 'manual', 'shoptet', 'firmy_cz', 'agency');
CREATE TYPE scan_status AS ENUM ('queued', 'running', 'done', 'error');
CREATE TYPE scan_trigger AS ENUM ('robot', 'client', 'manual', 'monitoring');
CREATE TYPE risk_level AS ENUM ('minimal', 'limited', 'high', 'unacceptable');
CREATE TYPE finding_confirmation AS ENUM ('confirmed', 'rejected', 'unknown');
CREATE TYPE client_plan AS ENUM ('basic', 'pro', 'enterprise');
CREATE TYPE payment_status AS ENUM ('pending', 'paid', 'failed', 'refunded');
CREATE TYPE alert_type AS ENUM ('new_ai_system', 'transparency_missing', 'behavior_change', 'law_change', 'monthly_report');
CREATE TYPE document_type AS ENUM ('compliance_report', 'transparency_page', 'action_plan', 'ai_register', 'chatbot_notices', 'ai_policy', 'training_outline');

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- TABULKA: companies (firmy z ARES, Shoptet, ručně)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Každá firma, kterou jsme kdy skenovali nebo o ní víme.
-- Může jít o prospect (ještě neklient) i o platícího klienta.

CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ico VARCHAR(10),                          -- IČO z ARES
    name VARCHAR(500) NOT NULL,               -- Název firmy
    url VARCHAR(2000),                        -- URL webu
    email VARCHAR(500),                       -- Kontaktní email
    phone VARCHAR(50),                        -- Telefon
    nace_code VARCHAR(10),                    -- NACE kód odvětví
    address TEXT,                             -- Adresa sídla
    employee_count INTEGER,                   -- Počet zaměstnanců
    source company_source DEFAULT 'manual',   -- Odkud firmu známe
    last_scanned_at TIMESTAMPTZ,              -- Kdy naposledy skenována
    outbound_email_sent_at TIMESTAMPTZ,       -- Kdy poslán outbound email
    outbound_email_count INTEGER DEFAULT 0,   -- Kolik emailů posláno
    notes TEXT,                               -- Interní poznámky
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_companies_ico ON companies(ico) WHERE ico IS NOT NULL;
CREATE INDEX idx_companies_url ON companies(url);
CREATE INDEX idx_companies_source ON companies(source);
CREATE INDEX idx_companies_last_scanned ON companies(last_scanned_at);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- TABULKA: clients (nasmlouvaní platící klienti)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Podmnožina companies — ti, co zaplatili a mají účet.
-- Propojeno s Supabase Auth přes auth_user_id.

CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_user_id UUID REFERENCES auth.users(id),    -- Supabase Auth
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    plan client_plan NOT NULL DEFAULT 'basic',
    email VARCHAR(500) NOT NULL,
    contact_name VARCHAR(500),                -- Jméno kontaktní osoby
    contact_role VARCHAR(200),                -- Funkce (jednatel, IT...)
    scan_frequency INTEGER DEFAULT 30,        -- Dní mezi skeny (monitoring)
    widget_installed BOOLEAN DEFAULT FALSE,
    widget_version VARCHAR(20),
    partner_ref VARCHAR(100),                 -- Odkud přišel (desperados, utm...)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_clients_auth_user ON clients(auth_user_id);
CREATE INDEX idx_clients_company ON clients(company_id);
CREATE INDEX idx_clients_plan ON clients(plan);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- TABULKA: scans (výsledky skenování)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Každý sken webu = jeden řádek. Firma může mít desítky skenů
-- (první sken + měsíční monitoring).

CREATE TABLE scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    triggered_by scan_trigger DEFAULT 'manual',
    url_scanned VARCHAR(2000) NOT NULL,       -- Konkrétní URL co jsme skenovali
    status scan_status DEFAULT 'queued',
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    duration_seconds INTEGER,                 -- Jak dlouho sken trval
    total_findings INTEGER DEFAULT 0,         -- Počet nálezů
    raw_html_hash VARCHAR(64),                -- SHA256 hash HTML (pro porovnání)
    screenshot_full_url TEXT,                 -- Celostránkový screenshot
    error_message TEXT,                       -- Pokud sken selhal
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scans_company ON scans(company_id);
CREATE INDEX idx_scans_status ON scans(status);
CREATE INDEX idx_scans_created ON scans(created_at DESC);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- TABULKA: findings (jednotlivé nálezy ze skenu)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Každý nalezený AI systém na webu = jeden finding.
-- Sken může mít 0-20 findings.

CREATE TABLE findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Co jsme našli
    name VARCHAR(200) NOT NULL,               -- Smartsupp, GA4, Tidio...
    category VARCHAR(100) NOT NULL,           -- chatbot, analytics, recommender...
    signature_matched VARCHAR(200),           -- Jaká signatura to chytla
    
    -- AI Act klasifikace
    risk_level risk_level DEFAULT 'minimal',
    ai_act_article VARCHAR(100),              -- čl. 50, čl. 26, čl. 5...
    action_required TEXT,                     -- Co musí firma udělat
    ai_classification_text TEXT,              -- Celý text klasifikace z Claude
    
    -- Důkazy
    screenshot_url TEXT,                      -- Screenshot nálezu
    evidence_html TEXT,                       -- HTML snippet kde jsme to našli
    position_on_page VARCHAR(200),            -- Kde na stránce (header, footer, popup...)
    
    -- Potvrzení klientem
    confirmed_by_client finding_confirmation DEFAULT 'unknown',
    confirmed_at TIMESTAMPTZ,
    
    -- Zdroj
    source VARCHAR(50) DEFAULT 'scanner',     -- scanner / questionnaire
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_findings_scan ON findings(scan_id);
CREATE INDEX idx_findings_company ON findings(company_id);
CREATE INDEX idx_findings_risk ON findings(risk_level);
CREATE INDEX idx_findings_name ON findings(name);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- TABULKA: questionnaire_responses (odpovědi z dotazníku)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Klient vyplní dotazník o interních AI systémech.
-- Každá odpověď = jeden řádek.

CREATE TABLE questionnaire_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    section VARCHAR(100) NOT NULL,            -- hr, finance, marketing, internal...
    question_key VARCHAR(200) NOT NULL,       -- uses_ai_in_hr, chatgpt_internal...
    answer VARCHAR(50) NOT NULL,              -- yes / no / unknown
    details JSONB,                            -- Follow-up odpovědi (JSON)
    tool_name VARCHAR(200),                   -- Název nástroje (ChatGPT, Copilot...)
    submitted_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_questionnaire_client ON questionnaire_responses(client_id);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- TABULKA: documents (vygenerované dokumenty)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Každý vygenerovaný PDF/HTML dokument pro klienta.

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    type document_type NOT NULL,
    version INTEGER DEFAULT 1,                -- Verze dokumentu (resken = nová verze)
    pdf_url TEXT,                             -- URL v Supabase Storage
    html_content TEXT,                        -- HTML obsah (pro transparency page)
    metadata JSONB,                           -- Doplňkové info (počet stran, etc.)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_documents_client ON documents(client_id);
CREATE INDEX idx_documents_type ON documents(type);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- TABULKA: alerts (odeslané alerty klientům)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 5 typů alertů z monitoringu (viz technická dokumentace 17.11)

CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    scan_id UUID REFERENCES scans(id),        -- Který sken vyvolal alert
    alert_type alert_type NOT NULL,
    subject VARCHAR(500),                     -- Předmět emailu
    message TEXT NOT NULL,                    -- Obsah alertu
    sent_at TIMESTAMPTZ,                      -- Kdy odeslán
    opened_at TIMESTAMPTZ,                    -- Kdy otevřen (tracking pixel)
    clicked_at TIMESTAMPTZ,                   -- Kdy kliknuto na CTA
    action_taken BOOLEAN DEFAULT FALSE,       -- Zákazník provedl akci?
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alerts_client ON alerts(client_id);
CREATE INDEX idx_alerts_type ON alerts(alert_type);
CREATE INDEX idx_alerts_sent ON alerts(sent_at DESC);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- TABULKA: payments (platby přes Stripe)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    stripe_session_id VARCHAR(500),
    stripe_payment_intent VARCHAR(500),
    amount INTEGER NOT NULL,                  -- Částka v CZK (halíře)
    currency VARCHAR(3) DEFAULT 'CZK',
    plan client_plan NOT NULL,
    status payment_status DEFAULT 'pending',
    paid_at TIMESTAMPTZ,
    invoice_url TEXT,                          -- URL na Stripe fakturu
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_payments_client ON payments(client_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_stripe ON payments(stripe_session_id);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- TABULKA: widget_configs (konfigurace widgetu pro každého klienta)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Widget na webu klienta volá API a dostane tuto konfiguraci.
-- Dynamicky aktualizovatelné (změní se zákon → změníme texty).

CREATE TABLE widget_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Texty widgetu
    bar_text VARCHAR(500) DEFAULT '🤖 Tento web využívá umělou inteligenci.',
    bar_link_text VARCHAR(200) DEFAULT 'Více informací',
    bar_link_url TEXT,                        -- URL na transparenční stránku
    
    -- Vzhled
    position VARCHAR(20) DEFAULT 'bottom',    -- bottom / top
    bg_color VARCHAR(7) DEFAULT '#1a1a2e',
    text_color VARCHAR(7) DEFAULT '#ffffff',
    accent_color VARCHAR(7) DEFAULT '#e94560',
    
    -- AI systémy k zobrazení
    ai_systems JSONB DEFAULT '[]'::jsonb,     -- Seznam AI systémů pro widget
    
    -- Verze (pro cache busting)
    version INTEGER DEFAULT 1,
    
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_widget_configs_client ON widget_configs(client_id);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- TABULKA: outbound_emails (log odeslaných outbound emailů)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CREATE TABLE outbound_emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    scan_id UUID REFERENCES scans(id),
    email_to VARCHAR(500) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    template VARCHAR(100) DEFAULT 'default',  -- Šablona emailu (A/B test)
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    opened_at TIMESTAMPTZ,                    -- Tracking pixel
    clicked_at TIMESTAMPTZ,                   -- Klik na CTA
    unsubscribed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_outbound_company ON outbound_emails(company_id);
CREATE INDEX idx_outbound_sent ON outbound_emails(sent_at DESC);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- AUTO-UPDATE TRIGGER (updated_at)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_companies_updated
    BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_clients_updated
    BEFORE UPDATE ON clients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_widget_configs_updated
    BEFORE UPDATE ON widget_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- ROW LEVEL SECURITY (RLS)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Klient vidí POUZE SVÁ data. Admin vidí vše.

ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE scans ENABLE ROW LEVEL SECURITY;
ALTER TABLE findings ENABLE ROW LEVEL SECURITY;
ALTER TABLE questionnaire_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE widget_configs ENABLE ROW LEVEL SECURITY;

-- Klient vidí jen svá data
CREATE POLICY "Clients can view own data" ON clients
    FOR SELECT USING (auth.uid() = auth_user_id);

CREATE POLICY "Clients can view own scans" ON scans
    FOR SELECT USING (
        company_id IN (
            SELECT company_id FROM clients WHERE auth_user_id = auth.uid()
        )
    );

CREATE POLICY "Clients can view own findings" ON findings
    FOR SELECT USING (
        company_id IN (
            SELECT company_id FROM clients WHERE auth_user_id = auth.uid()
        )
    );

CREATE POLICY "Clients can manage own questionnaire" ON questionnaire_responses
    FOR ALL USING (
        client_id IN (
            SELECT id FROM clients WHERE auth_user_id = auth.uid()
        )
    );

CREATE POLICY "Clients can view own documents" ON documents
    FOR SELECT USING (
        client_id IN (
            SELECT id FROM clients WHERE auth_user_id = auth.uid()
        )
    );

CREATE POLICY "Clients can view own alerts" ON alerts
    FOR SELECT USING (
        client_id IN (
            SELECT id FROM clients WHERE auth_user_id = auth.uid()
        )
    );

CREATE POLICY "Clients can view own payments" ON payments
    FOR SELECT USING (
        client_id IN (
            SELECT id FROM clients WHERE auth_user_id = auth.uid()
        )
    );

CREATE POLICY "Clients can view own widget config" ON widget_configs
    FOR SELECT USING (
        client_id IN (
            SELECT id FROM clients WHERE auth_user_id = auth.uid()
        )
    );

-- Widget config je PUBLIC READ (widget na webu klienta musí číst bez autentizace)
CREATE POLICY "Widget config is public readable" ON widget_configs
    FOR SELECT USING (is_active = TRUE);

-- Service role (backend) má přístup ke všemu přes service_key
-- (Supabase service_role automaticky obchází RLS)

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- STORAGE BUCKET pro screenshoty a PDF
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INSERT INTO storage.buckets (id, name, public)
VALUES ('screenshots', 'screenshots', TRUE);

INSERT INTO storage.buckets (id, name, public)
VALUES ('documents', 'documents', FALSE);

-- Screenshots jsou veřejné (pro outbound emaily a widget)
CREATE POLICY "Screenshots are public" ON storage.objects
    FOR SELECT USING (bucket_id = 'screenshots');

-- Dokumenty jsou jen pro autentizované klienty
CREATE POLICY "Documents are private" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'documents'
        AND auth.role() = 'authenticated'
    );

-- ============================================
-- KONEC MIGRACE 001
-- ============================================
-- Tabulky: companies, clients, scans, findings,
--          questionnaire_responses, documents, alerts,
--          payments, widget_configs, outbound_emails
-- Celkem: 10 tabulek + 2 storage buckets
-- ============================================
