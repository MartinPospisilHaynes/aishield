-- AIshield.cz — RAG: pgvector setup pro AI Act
-- Spustit v Supabase SQL Editor (https://supabase.com/dashboard → SQL Editor)
-- Jednorázová migrace — bezpečné spustit opakovaně díky IF NOT EXISTS

-- 1. Aktivace pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Tabulka pro chunky AI Actu
CREATE TABLE IF NOT EXISTS ai_act_chunks (
    id SERIAL PRIMARY KEY,
    article TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    chunk_index INT DEFAULT 0,
    embedding vector(768),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Index pro rychlé vyhledávání (cosine similarity)
CREATE INDEX IF NOT EXISTS idx_ai_act_chunks_embedding
    ON ai_act_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 20);

-- 4. Unikátní index na článek (prevence duplicit)
CREATE UNIQUE INDEX IF NOT EXISTS idx_ai_act_chunks_article
    ON ai_act_chunks (article, chunk_index);

-- 5. RPC funkce pro similarity search
CREATE OR REPLACE FUNCTION match_ai_act_chunks(
    query_embedding vector(768),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 5
) RETURNS TABLE (
    id int,
    article text,
    title text,
    content text,
    similarity float
) LANGUAGE sql STABLE AS $$
    SELECT
        id,
        article,
        title,
        content,
        1 - (embedding <=> query_embedding) AS similarity
    FROM ai_act_chunks
    WHERE 1 - (embedding <=> query_embedding) > match_threshold
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;

-- HOTOVO! Po spuštění tohoto SQL zavolejte z Pythonu:
--   from backend.ai_engine.rag import embed_ai_act_chunks
--   import asyncio
--   asyncio.run(embed_ai_act_chunks())
