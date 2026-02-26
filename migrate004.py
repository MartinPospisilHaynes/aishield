#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect(
    host='aws-0-eu-central-1.pooler.supabase.com',
    port=6543,
    dbname='postgres',
    user='postgres.rsxwqcrkttlfnqbjgpgc',
    password='Rc_732716141',
    sslmode='require'
)
conn.autocommit = True
cur = conn.cursor()

stmts = [
    "ALTER TABLE email_log ADD COLUMN IF NOT EXISTS from_email VARCHAR(255) DEFAULT 'info@aishield.cz'",
    "ALTER TABLE email_events ADD COLUMN IF NOT EXISTS from_email VARCHAR(255) DEFAULT 'info@aishield.cz'",
    "CREATE INDEX IF NOT EXISTS idx_email_log_from_email ON email_log(from_email)",
    "CREATE INDEX IF NOT EXISTS idx_email_log_from_sent ON email_log(from_email, sent_at)",
    "CREATE INDEX IF NOT EXISTS idx_email_events_from ON email_events(from_email, event_type)",
    "CREATE INDEX IF NOT EXISTS idx_email_log_sent_at ON email_log(sent_at)",
    "CREATE INDEX IF NOT EXISTS idx_email_events_created ON email_events(created_at)",
]

ok = 0
for s in stmts:
    try:
        cur.execute(s)
        ok += 1
        print(f"OK: {s[:70]}")
    except Exception as e:
        print(f"SKIP: {e}")

print(f"\nMigrace 004: {ok}/{len(stmts)} done")
cur.close()
conn.close()
