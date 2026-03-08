-- ============================================
-- AIshield.cz — Shoptet dotazník v2 migrace
-- ============================================
-- Migrace: 011_shoptet_questionnaire_v2.sql
-- Datum: 2026-03-07
-- Popis: Přidání sloupců pro 20-otázkový dotazník a scan tracking

ALTER TABLE shoptet_installations
ADD COLUMN IF NOT EXISTS questionnaire_data JSONB DEFAULT NULL;

ALTER TABLE shoptet_installations
ADD COLUMN IF NOT EXISTS scan_completed_at TIMESTAMPTZ DEFAULT NULL;

COMMENT ON COLUMN shoptet_installations.questionnaire_data IS
    'Odpovědi z dotazníku v2 (20 otázek, 7 sekcí) — uloženo jako JSON';

COMMENT ON COLUMN shoptet_installations.scan_completed_at IS
    'Kdy byl dokončen Playwright scan webu';
