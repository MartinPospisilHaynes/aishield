-- ============================================================
-- 030_amendment_system.sql
-- Systém dodatků (amendments) — verzování dokumentů po změně dotazníku
-- ============================================================

-- Rozšíření tabulky documents o amendment metadata
DO $$
BEGIN
    -- Číslo dodatku (NULL = originální dokument)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'documents' AND column_name = 'amendment_number'
    ) THEN
        ALTER TABLE documents ADD COLUMN amendment_number INTEGER;
    END IF;

    -- Odkaz na původní dokument, ke kterému je dodatek
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'documents' AND column_name = 'parent_document_id'
    ) THEN
        ALTER TABLE documents ADD COLUMN parent_document_id UUID REFERENCES documents(id) ON DELETE SET NULL;
    END IF;

    -- JSON s popisem změny, která vyvolala dodatek
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'documents' AND column_name = 'change_trigger'
    ) THEN
        ALTER TABLE documents ADD COLUMN change_trigger JSONB;
    END IF;

    -- Číslo verze (1 = originál, 2+ = po regeneraci)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'documents' AND column_name = 'version'
    ) THEN
        ALTER TABLE documents ADD COLUMN version INTEGER DEFAULT 1;
    END IF;
END $$;

-- Rozšíření tabulky orders o delivered_at (kdy klient obdržel PDF)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'orders' AND column_name = 'delivered_at'
    ) THEN
        ALTER TABLE orders ADD COLUMN delivered_at TIMESTAMPTZ;
    END IF;
END $$;

-- Audit trail změn v dotazníku
CREATE TABLE IF NOT EXISTS questionnaire_change_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL,
    company_id UUID,
    question_key VARCHAR(200) NOT NULL,
    old_answer VARCHAR(50),
    new_answer VARCHAR(50),
    old_details JSONB,
    new_details JSONB,
    impact_level VARCHAR(20) CHECK (impact_level IN ('none', 'low', 'medium', 'high', 'critical')),
    risk_change VARCHAR(20) CHECK (risk_change IN ('unchanged', 'escalated', 'de-escalated')),
    affected_documents TEXT[],
    amendment_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    changed_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_change_log_client ON questionnaire_change_log(client_id);
CREATE INDEX IF NOT EXISTS idx_change_log_company ON questionnaire_change_log(company_id);
CREATE INDEX IF NOT EXISTS idx_change_log_changed ON questionnaire_change_log(changed_at DESC);

-- RLS
ALTER TABLE questionnaire_change_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_all_change_log" ON questionnaire_change_log
    FOR ALL TO service_role USING (true) WITH CHECK (true);
