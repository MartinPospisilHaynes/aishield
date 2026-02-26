-- 004_multi_sender.sql
-- Přidá podporu pro multi-sender rotaci
-- from_email sloupec v email_log a email_events pro tracking per-sender

-- 1. Přidat from_email do email_log
ALTER TABLE email_log ADD COLUMN IF NOT EXISTS from_email VARCHAR(255) DEFAULT 'info@aishield.cz';

-- 2. Přidat from_email do email_events (pro bounce/complaint per sender)
ALTER TABLE email_events ADD COLUMN IF NOT EXISTS from_email VARCHAR(255) DEFAULT 'info@aishield.cz';

-- 3. Index pro rychlé dotazy per sender
CREATE INDEX IF NOT EXISTS idx_email_log_from_email ON email_log(from_email);
CREATE INDEX IF NOT EXISTS idx_email_log_from_sent ON email_log(from_email, sent_at);
CREATE INDEX IF NOT EXISTS idx_email_events_from ON email_events(from_email, event_type);

-- 4. Index pro sent_at (pro rychlé denní/týdenní dotazy)
CREATE INDEX IF NOT EXISTS idx_email_log_sent_at ON email_log(sent_at);
CREATE INDEX IF NOT EXISTS idx_email_events_created ON email_events(created_at);
