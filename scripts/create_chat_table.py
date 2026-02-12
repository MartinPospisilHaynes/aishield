"""Create chat_messages table in Supabase via direct Postgres connection."""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

ref = os.environ["SUPABASE_URL"].replace("https://", "").split(".")[0]
password = os.environ.get("SUPABASE_DB_PASSWORD", "")

conn_str = f"postgresql://postgres:{password}@db.{ref}.supabase.co:5432/postgres"

sql = """
CREATE TABLE IF NOT EXISTS chat_messages (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id text NOT NULL,
    role text NOT NULL CHECK (role IN ('user', 'assistant')),
    content text NOT NULL,
    page_url text,
    created_at timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created ON chat_messages(created_at DESC);
"""

try:
    conn = psycopg2.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(sql)
    print("Table chat_messages created successfully!")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
