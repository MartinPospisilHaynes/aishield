-- Engine Health Counters — persistent storage for lifetime error counts
-- and last alert timestamps. Used by EngineHealthMonitor to survive restarts.
--
-- Run once in Supabase SQL editor or via psql.

CREATE TABLE IF NOT EXISTS engine_health_counters (
    error_type   TEXT PRIMARY KEY,
    lifetime_count BIGINT NOT NULL DEFAULT 0,
    last_alert_at  TIMESTAMPTZ,
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Auto-update updated_at on upsert
CREATE OR REPLACE FUNCTION update_engine_health_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_engine_health_updated_at ON engine_health_counters;

CREATE TRIGGER trg_engine_health_updated_at
    BEFORE UPDATE ON engine_health_counters
    FOR EACH ROW
    EXECUTE FUNCTION update_engine_health_updated_at();

-- RLS: only service_role can access (backend uses service_role key)
ALTER TABLE engine_health_counters ENABLE ROW LEVEL SECURITY;

-- Allow service_role full access
CREATE POLICY "service_role_full_access" ON engine_health_counters
    FOR ALL
    USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');
