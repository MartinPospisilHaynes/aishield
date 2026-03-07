-- ============================================
-- AIshield.cz — Shoptet Addon schéma
-- ============================================
-- Migrace: 010_shoptet_addon.sql
-- Datum: 2026-03-06

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- TABULKA: shoptet_installations
-- Instalace addonu na Shoptet eshopech
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CREATE TABLE shoptet_installations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    eshop_id INTEGER NOT NULL,
    eshop_url VARCHAR(2000),
    eshop_name VARCHAR(500),
    oauth_access_token TEXT,          -- ENCRYPTED (Fernet AES-128)
    contact_email TEXT,               -- ENCRYPTED
    template_name VARCHAR(100),
    language VARCHAR(10) DEFAULT 'cs',
    plan VARCHAR(20) DEFAULT 'basic',
    status VARCHAR(20) DEFAULT 'active',
    wizard_completed_at TIMESTAMPTZ,
    last_scan_at TIMESTAMPTZ,
    compliance_page_slug VARCHAR(200) DEFAULT 'ai-compliance',
    compliance_page_shoptet_id INTEGER,
    installed_at TIMESTAMPTZ DEFAULT NOW(),
    uninstalled_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_shoptet_inst_eshop ON shoptet_installations(eshop_id)
    WHERE status != 'uninstalled';
CREATE INDEX idx_shoptet_inst_status ON shoptet_installations(status);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- TABULKA: shoptet_ai_systems
-- AI systémy identifikované wizardem nebo scannerem
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CREATE TABLE shoptet_ai_systems (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    installation_id UUID NOT NULL REFERENCES shoptet_installations(id) ON DELETE CASCADE,
    source VARCHAR(20) NOT NULL DEFAULT 'wizard',
    provider VARCHAR(200) NOT NULL,
    ai_type VARCHAR(50) NOT NULL,
    ai_act_article VARCHAR(20) DEFAULT 'none',
    risk_level VARCHAR(20) DEFAULT 'minimal',
    confidence VARCHAR(20) DEFAULT 'probable',
    is_active BOOLEAN DEFAULT TRUE,
    details JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_shoptet_ai_installation ON shoptet_ai_systems(installation_id);
CREATE INDEX idx_shoptet_ai_active ON shoptet_ai_systems(installation_id, is_active);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- TABULKA: shoptet_compliance_pages
-- Vygenerované compliance stránky na eshopech
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CREATE TABLE shoptet_compliance_pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    installation_id UUID NOT NULL REFERENCES shoptet_installations(id) ON DELETE CASCADE,
    page_shoptet_id INTEGER,
    html_content TEXT,
    language VARCHAR(10) DEFAULT 'cs',
    is_published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_shoptet_page_inst ON shoptet_compliance_pages(installation_id);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- TABULKA: shoptet_documents
-- Vygenerované PDF dokumenty
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CREATE TABLE shoptet_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    installation_id UUID NOT NULL REFERENCES shoptet_installations(id) ON DELETE CASCADE,
    doc_type VARCHAR(50) NOT NULL,
    storage_path TEXT,
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    version INTEGER DEFAULT 1
);

CREATE INDEX idx_shoptet_docs_inst ON shoptet_documents(installation_id);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- RLS POLITIKY
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ALTER TABLE shoptet_installations ENABLE ROW LEVEL SECURITY;
ALTER TABLE shoptet_ai_systems ENABLE ROW LEVEL SECURITY;
ALTER TABLE shoptet_compliance_pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE shoptet_documents ENABLE ROW LEVEL SECURITY;

-- Service role má plný přístup
CREATE POLICY "service_full_access" ON shoptet_installations
    FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_full_access" ON shoptet_ai_systems
    FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_full_access" ON shoptet_compliance_pages
    FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_full_access" ON shoptet_documents
    FOR ALL USING (true) WITH CHECK (true);
