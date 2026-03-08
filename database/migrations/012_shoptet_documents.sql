-- Shoptet Addon: tabulka shoptet_documents pro PDF dokumenty
-- + ensure scan_completed_at na shoptet_installations (pokud chybí)

CREATE TABLE IF NOT EXISTS shoptet_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    installation_id UUID NOT NULL REFERENCES shoptet_installations(id) ON DELETE CASCADE,
    doc_type TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    storage_path TEXT NOT NULL,
    file_size INTEGER DEFAULT 0,
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_shoptet_documents_installation
    ON shoptet_documents(installation_id);

-- scan_completed_at by měl existovat z migrace 011, ale pro jistotu:
ALTER TABLE shoptet_installations
    ADD COLUMN IF NOT EXISTS scan_completed_at TIMESTAMPTZ DEFAULT NULL;
