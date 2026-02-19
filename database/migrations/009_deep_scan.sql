-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- 009: Deep Scan (24h hloubkový scan)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- scan_type: 'quick' (výchozí rychlý scan) nebo 'deep' (24h hloubkový)
ALTER TABLE scans ADD COLUMN IF NOT EXISTS scan_type VARCHAR(20) DEFAULT 'quick';

-- parent_scan_id: odkazuje na rychlý scan, ke kterému deep scan patří
ALTER TABLE scans ADD COLUMN IF NOT EXISTS parent_scan_id UUID REFERENCES scans(id);

-- deep_scan_status: stav 24h hloubkového scanu
-- 'pending' → čeká na spuštění
-- 'running' → probíhá (24h)
-- 'done' → dokončen
-- 'error' → selhalo
ALTER TABLE scans ADD COLUMN IF NOT EXISTS deep_scan_status VARCHAR(20);

-- deep_scan_started_at / finished_at (samostatné od rychlého scanu)
ALTER TABLE scans ADD COLUMN IF NOT EXISTS deep_scan_started_at TIMESTAMPTZ;
ALTER TABLE scans ADD COLUMN IF NOT EXISTS deep_scan_finished_at TIMESTAMPTZ;

-- deep_scan_total_findings: agregovaný počet unikátních nálezů z deep scanu
ALTER TABLE scans ADD COLUMN IF NOT EXISTS deep_scan_total_findings INTEGER;

-- geo_countries_scanned: JSON pole zemí, ze kterých bylo skenováno
ALTER TABLE scans ADD COLUMN IF NOT EXISTS geo_countries_scanned JSONB;

-- Index pro vyhledávání deep scanů
CREATE INDEX IF NOT EXISTS idx_scans_deep_status ON scans(deep_scan_status) WHERE deep_scan_status IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_scans_parent ON scans(parent_scan_id) WHERE parent_scan_id IS NOT NULL;

-- Přidat source sloupec k findings (odkud nález pochází: quick_scan, deep_scan_CZ atd.)
-- Poznámka: source sloupec již existuje, využijeme ho pro deep scan provenance
-- Hodnoty: 'signature', 'ai_classified', 'ai_classified_fp', 'deep_scan_CZ', 'deep_scan_US' atd.
