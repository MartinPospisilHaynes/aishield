# ============================================
# AIshield.cz — ENUM fix migrace
# ============================================
# Tato migrace převádí PostgreSQL ENUM typy na VARCHAR,
# protože kód posílá hodnoty mimo definici ENUM (např. "none", "pending").
# Spuštěno: 9. února 2026
# ============================================

-- findings.risk_level: ENUM → VARCHAR (kód posílá "none" pro false positives)
ALTER TABLE findings ALTER COLUMN risk_level TYPE VARCHAR(50) USING risk_level::text;
ALTER TABLE findings ALTER COLUMN risk_level SET DEFAULT 'minimal';

-- findings.confirmed_by_client: ENUM → VARCHAR
ALTER TABLE findings ALTER COLUMN confirmed_by_client TYPE VARCHAR(50) USING confirmed_by_client::text;
ALTER TABLE findings ALTER COLUMN confirmed_by_client SET DEFAULT 'unknown';

-- scans.status: ENUM → VARCHAR (kód posílá "pending", "done" apod.)
ALTER TABLE scans ALTER COLUMN status TYPE VARCHAR(50) USING status::text;
ALTER TABLE scans ALTER COLUMN status SET DEFAULT 'queued';

-- scans.triggered_by: ENUM → VARCHAR
ALTER TABLE scans ALTER COLUMN triggered_by TYPE VARCHAR(50) USING triggered_by::text;
ALTER TABLE scans ALTER COLUMN triggered_by SET DEFAULT 'manual';

-- clients.plan: ENUM → VARCHAR
ALTER TABLE clients ALTER COLUMN plan TYPE VARCHAR(50) USING plan::text;
ALTER TABLE clients ALTER COLUMN plan SET DEFAULT 'basic';
