-- ============================================
-- AIshield.cz — Migration 006: Security Hardening
-- ============================================
-- 1. Audit log tabulka pro sledování přístupu k datům
-- 2. RLS na companies tabulce (chyběla!)
-- 3. RLS na outbound_emails tabulce (chyběla!)
-- 4. Data retention metadata (created_at indexy)
-- ============================================

-- ═══════════════════════════════════════════
-- 1. AUDIT LOG — kdo, kdy, co přistoupil
-- ═══════════════════════════════════════════

CREATE TABLE IF NOT EXISTS data_access_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_email TEXT NOT NULL,               -- kdo přistoupil (admin email)
    actor_role TEXT DEFAULT 'admin',          -- 'admin' | 'system' | 'user'
    action TEXT NOT NULL,                     -- 'view' | 'export' | 'delete' | 'edit'
    resource_type TEXT NOT NULL,              -- 'company' | 'questionnaire' | 'scan' | 'finding'
    resource_id TEXT,                         -- UUID entity
    resource_detail TEXT,                     -- lidsky čitelný popis (název firmy, URL...)
    ip_address TEXT,
    user_agent TEXT,
    metadata JSONB DEFAULT '{}',             -- extra kontext
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index pro rychlé dotazy
CREATE INDEX IF NOT EXISTS idx_data_access_log_created ON data_access_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_data_access_log_actor ON data_access_log(actor_email);
CREATE INDEX IF NOT EXISTS idx_data_access_log_resource ON data_access_log(resource_type, resource_id);

-- RLS: jen service_role (backend) smí zapisovat a číst audit log
ALTER TABLE data_access_log ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS service_role_all_audit_log ON data_access_log;
CREATE POLICY service_role_all_audit_log ON data_access_log
    FOR ALL
    USING (auth.role() = 'service_role');


-- ═══════════════════════════════════════════
-- 2. RLS NA COMPANIES (chyběla!)
-- ═══════════════════════════════════════════

ALTER TABLE companies ENABLE ROW LEVEL SECURITY;

-- Uživatelé vidí jenom svoji firmu (propojeno přes email)
DROP POLICY IF EXISTS client_select_own_company ON companies;
CREATE POLICY client_select_own_company ON companies
    FOR SELECT
    USING (
        email = (SELECT email FROM auth.users WHERE id = auth.uid())
        OR url IN (
            SELECT (raw_user_meta_data->>'web_url')::text
            FROM auth.users
            WHERE id = auth.uid()
        )
    );

-- Service role (backend) má plný přístup
DROP POLICY IF EXISTS service_role_all_companies ON companies;
CREATE POLICY service_role_all_companies ON companies
    FOR ALL
    USING (auth.role() = 'service_role');


-- ═══════════════════════════════════════════
-- 3. RLS NA OUTBOUND_EMAILS (chyběla!)
-- ═══════════════════════════════════════════

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'outbound_emails') THEN
        ALTER TABLE outbound_emails ENABLE ROW LEVEL SECURITY;
        
        -- Jen service_role — outbound emaily jsou interní systémová data
        EXECUTE 'DROP POLICY IF EXISTS service_role_all_outbound_emails ON outbound_emails';
        EXECUTE 'CREATE POLICY service_role_all_outbound_emails ON outbound_emails
            FOR ALL
            USING (auth.role() = ''service_role'')';
    END IF;
END $$;


-- ═══════════════════════════════════════════
-- 4. INDEX PRO DATA RETENTION (cleanup podle stáří)
-- ═══════════════════════════════════════════

-- Questionnaire responses — budeme mazat starší záznamy
CREATE INDEX IF NOT EXISTS idx_questionnaire_responses_submitted
    ON questionnaire_responses(submitted_at);

-- Companies — pro identifikaci neaktivních
CREATE INDEX IF NOT EXISTS idx_companies_last_scanned
    ON companies(last_scanned_at);

-- Scans — pro identifikaci starých skenů
CREATE INDEX IF NOT EXISTS idx_scans_finished
    ON scans(finished_at);


-- ═══════════════════════════════════════════
-- HOTOVO
-- ═══════════════════════════════════════════
