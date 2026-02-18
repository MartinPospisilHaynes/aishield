"""
AIshield.cz — RAG over AI Act (Regulation EU 2024/1689)

Retrieval-Augmented Generation pro přesné citace z AI Act.
Využívá pgvector v Supabase + Gemini gemini-embedding-001.

Funkce:
- embed_ai_act_chunks() — jednorázový import AI Actu do vektorové DB
- retrieve_relevant_context() — najde relevantní články pro daný dotaz
- enrich_prompt_with_rag() — obohatí prompt o kontext z AI Actu

Tabulka v Supabase:
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE TABLE ai_act_chunks (
        id SERIAL PRIMARY KEY,
        article TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        chunk_index INT DEFAULT 0,
        embedding vector(768),
        metadata JSONB DEFAULT '{}'
    );
    CREATE INDEX ON ai_act_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 20);

Supabase RPC funkce:
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
"""

import json
import logging
import os
from typing import Optional

import httpx

from backend.database import get_supabase

logger = logging.getLogger(__name__)

# ── Gemini Embedding config ──
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 768
EMBEDDING_API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{EMBEDDING_MODEL}:embedContent"
)


# ═══════════════════════════════════════════════════════════════
# Embedding
# ═══════════════════════════════════════════════════════════════

async def _get_embedding(text: str) -> list[float]:
    """Získá embedding vektory přes Gemini gemini-embedding-001."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY není nastavený — nelze generovat embeddingy")

    payload = {
        "model": f"models/{EMBEDDING_MODEL}",
        "content": {"parts": [{"text": text}]},
        "outputDimensionality": EMBEDDING_DIM,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{EMBEDDING_API_URL}?key={api_key}",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()

    values = data.get("embedding", {}).get("values", [])
    if not values:
        raise RuntimeError(f"Gemini embedding vrátil prázdný výsledek: {data}")

    return values


async def _get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Batch embeddingy — po jednom (Gemini nemá batch endpoint pro embedContent)."""
    results = []
    for text in texts:
        emb = await _get_embedding(text)
        results.append(emb)
    return results


# ═══════════════════════════════════════════════════════════════
# Klíčové články AI Actu (český překlad)
# ═══════════════════════════════════════════════════════════════

AI_ACT_ARTICLES = [
    {
        "article": "čl. 1",
        "title": "Předmět",
        "content": (
            "Toto nařízení stanoví harmonizovaná pravidla pro uvádění na trh, "
            "uvádění do provozu a používání systémů umělé inteligence (AI systémy) v Unii. "
            "Stanoví zákazy určitých praktik v oblasti AI, specifické požadavky na vysoce "
            "rizikové systémy AI a povinnosti transparentnosti pro určité systémy AI. "
            "Stanoví rovněž pravidla pro modely AI pro obecné účely."
        ),
    },
    {
        "article": "čl. 3",
        "title": "Definice",
        "content": (
            "Systém umělé inteligence (AI systém) je strojový systém navržený tak, aby fungoval "
            "s různou úrovní autonomie, který může po zavedení vykazovat přizpůsobivost a který "
            "pro explicitní nebo implicitní cíle odvodí z přijatých vstupů způsob, jakým generovat "
            "výstupy, jako jsou predikce, obsah, doporučení nebo rozhodnutí, které mohou ovlivnit "
            "fyzické nebo virtuální prostředí. Zavádějící (deployer) je fyzická nebo právnická osoba, "
            "která používá systém AI pod svou pravomocí, s výjimkou osobního, neprofesionálního použití. "
            "Poskytovatel (provider) je osoba, která vyvíjí AI systém nebo model AI pro obecné účely "
            "a uvádí jej na trh pod svým jménem nebo ochrannou známkou."
        ),
    },
    {
        "article": "čl. 4",
        "title": "Gramotnost v oblasti AI",
        "content": (
            "Poskytovatelé a zavádějící systémů AI přijmou opatření k zajištění dostatečné úrovně "
            "gramotnosti v oblasti AI u svých zaměstnanců a dalších osob, které se zabývají provozem "
            "a používáním systémů AI jejich jménem, přičemž zohlední jejich technické znalosti, "
            "zkušenosti, vzdělání a odbornou přípravu a kontext, ve kterém se mají systémy AI používat, "
            "a osoby nebo skupiny osob, na které se mají systémy AI používat. "
            "Toto ustanovení se použije od 2. února 2025."
        ),
    },
    {
        "article": "čl. 5",
        "title": "Zakázané praktiky v oblasti AI",
        "content": (
            "Zakazují se tyto praktiky: a) uvádění na trh, uvádění do provozu nebo používání "
            "systému AI, který využívá podprahové techniky mimo vědomí osoby s cílem podstatně "
            "zkreslit chování osoby; b) systémy využívající zranitelnost osob z důvodu věku, "
            "zdravotního postižení nebo sociální situace; c) systémy pro sociální bodování osob "
            "(social scoring) ze strany veřejné moci; d) systémy pro biometrickou identifikaci "
            "v reálném čase na veřejně přístupných místech pro účely prosazování práva (s výjimkami); "
            "e) systémy, které vytvářejí databáze rozpoznávání obličejů plošným shromažďováním "
            "z internetu nebo CCTV; f) systémy pro odvozování emocí na pracovišti a ve vzdělávacích "
            "institucích (s výjimkou zdravotních/bezpečnostních důvodů). "
            "Sankce za porušení zakázaných praktik: až 35 000 000 EUR nebo 7 % celosvětového ročního obratu."
        ),
    },
    {
        "article": "čl. 6",
        "title": "Klasifikační pravidla pro vysoce rizikové systémy AI",
        "content": (
            "Systém AI je vysoce rizikový, pokud: a) je bezpečnostní komponentou produktu, "
            "na který se vztahuje harmonizační právní předpis EU uvedený v příloze I, nebo b) spadá "
            "do některé z oblastí uvedených v příloze III. Oblast přílohy III zahrnuje: biometrii, "
            "kritickou infrastrukturu, vzdělávání a odbornou přípravu, zaměstnanost a řízení "
            "pracovníků, přístup k základním službám, prosazování práva, migraci a správu hranic, "
            "výkon spravedlnosti a demokratické procesy. "
            "Vysoce rizikový systém AI podléhá povinnostem podle článků 8 až 15 před svým uvedením "
            "na trh nebo do provozu."
        ),
    },
    {
        "article": "čl. 9",
        "title": "Systém řízení rizik",
        "content": (
            "Pro vysoce rizikové systémy AI se zavede, provádí, dokumentuje a udržuje systém řízení "
            "rizik. Systém řízení rizik je chápán jako nepřetržitý iterativní proces plánovaný "
            "a prováděný po celou dobu životního cyklu vysoce rizikového systému AI. Zahrnuje: "
            "a) identifikaci a analýzu známých a rozumně předvídatelných rizik; b) odhady a hodnocení "
            "rizik; c) hodnocení dalších rizik na základě analýzy dat po uvedení na trh; "
            "d) přijetí vhodných a cílených opatření k řízení rizik."
        ),
    },
    {
        "article": "čl. 13",
        "title": "Transparentnost a poskytování informací zavádějícím",
        "content": (
            "Vysoce rizikové systémy AI jsou navrhovány a vyvíjeny tak, aby jejich fungování bylo "
            "dostatečně transparentní k tomu, aby zavádějící mohli interpretovat výstup systému "
            "a vhodně jej používat. Je zajištěn vhodný typ a stupeň transparentnosti. "
            "K vysoce rizikovým systémům AI se přiloží návod k použití ve vhodném digitálním formátu "
            "nebo jinak, který obsahuje stručné, úplné, správné a jasné informace."
        ),
    },
    {
        "article": "čl. 14",
        "title": "Lidský dohled",
        "content": (
            "Vysoce rizikové systémy AI jsou navrhovány a vyvíjeny tak, aby na ně mohly účinně "
            "dohlížet fyzické osoby. Opatření lidského dohledu umožňují osobě (osobám), jimž je "
            "svěřen lidský dohled: a) řádně porozumět příslušným schopnostem a omezením vysoce "
            "rizikového systému AI; b) řádně sledovat jeho fungování; c) být si vědomy a moci řešit "
            "nadměrnou automatizaci (automation bias); d) správně interpretovat výstup; "
            "e) rozhodnout se, že vysoce rizikový systém AI nepoužijí nebo jeho výstup jinak zruší."
        ),
    },
    {
        "article": "čl. 16",
        "title": "Povinnosti poskytovatelů vysoce rizikových systémů AI",
        "content": (
            "Poskytovatelé vysoce rizikových systémů AI: a) zajistí, aby splňovaly požadavky; "
            "b) uvedou na systému svůj název nebo ochrannou známku; c) zavedou systém řízení kvality; "
            "d) uchovávají dokumentaci; e) uchovávají automaticky generované protokoly; "
            "f) zajistí, aby systém AI prošel příslušným postupem posouzení shody; "
            "g) vypracují prohlášení o shodě EU; h) připojí označení shody CE; "
            "i) na žádost registrují systém v databázi EU."
        ),
    },
    {
        "article": "čl. 26",
        "title": "Povinnosti zavádějících vysoce rizikových systémů AI",
        "content": (
            "Zavádějící vysoce rizikových systémů AI: a) přijmou vhodná technická a organizační "
            "opatření; b) přidělí lidský dohled osobám s potřebnou způsobilostí; c) zajistí, "
            "aby vstupní data byla relevantní a dostatečně reprezentativní; d) sledují fungování "
            "systému; e) informují poskytovatele nebo distributora o závažných rizicích; "
            "f) uchovávají automaticky generované protokoly po dobu přiměřenou účelu systému, "
            "nejméně však 6 měsíců; g) před uvedením do provozu provedou posouzení dopadu na základní "
            "práva. Zavádějící, kteří jsou zaměstnavateli, informují zástupce zaměstnanců a dotčené "
            "zaměstnance o tom, že budou vystaveni vysoce rizikovému systému AI."
        ),
    },
    {
        "article": "čl. 27",
        "title": "Posouzení dopadu na základní práva",
        "content": (
            "Před uvedením vysoce rizikového systému AI do provozu zavádějící, kteří jsou subjekty "
            "veřejného práva nebo soukromými subjekty poskytujícími veřejné služby, a zavádějící "
            "vysoce rizikových systémů AI uvedených v bodě 5 písm. b) a c) přílohy III provedou "
            "posouzení dopadu na základní práva. Posouzení zahrnuje: popis procesů, dobu a četnost "
            "používání, kategorie osob a skupin, konkrétní rizika újmy, opatření lidského dohledu."
        ),
    },
    {
        "article": "čl. 50",
        "title": "Povinnosti transparentnosti pro poskytovatele a zavádějící určitých systémů AI",
        "content": (
            "Poskytovatelé systémů AI, které jsou určeny k přímé interakci s fyzickými osobami, "
            "zajistí, aby byl systém navržen a vyvinut tak, aby dotčené fyzické osoby byly informovány "
            "o tom, že komunikují se systémem AI, ledaže je to zjevné z okolností a kontextu použití. "
            "Poskytovatelé systémů AI generujících syntetický zvukový, obrazový, video obsah nebo text "
            "zajistí, aby výstupy systému AI byly označeny ve strojově čitelném formátu. "
            "Zavádějící systémů AI pro rozpoznávání emocí nebo biometrickou kategorizaci informují "
            "fyzické osoby vystavené systému o jeho provozu. "
            "Zavádějící systému AI, který generuje deep fakes, musí zveřejnit, že obsah byl uměle "
            "vytvořen nebo zmanipulován. Výjimky: umělecká, satirická nebo fiktivní díla."
        ),
    },
    {
        "article": "čl. 52",
        "title": "Registrace v databázi EU",
        "content": (
            "Před uvedením vysoce rizikového systému AI na trh nebo do provozu poskytovatel nebo "
            "případně zplnomocněný zástupce zaregistruje sebe a systém v databázi EU. "
            "Veřejné orgány a instituce EU zaregistrují systém v databázi EU a odkáží na registraci "
            "v posouzení dopadu na základní práva podle článku 27. "
            "U vysoce rizikových systémů AI uvedených v příloze III bodě 2 se registrace provádí "
            "na vnitrostátní úrovni."
        ),
    },
    {
        "article": "čl. 53-56",
        "title": "Modely AI pro obecné účely (GPAI)",
        "content": (
            "Poskytovatelé modelů AI pro obecné účely (GPAI): vypracují a aktualizují technickou "
            "dokumentaci modelu, včetně procesu tréninku a hodnocení; poskytnou informace a dokumentaci "
            "poskytovatelům následných systémů AI; zavedou pravidla dodržování autorského práva; "
            "zpracují a veřejně zpřístupní dostatečně podrobný obsah tréninkových dat. "
            "Modely GPAI se systémovým rizikem: provedou hodnocení modelu, posoudí a zmírní systémová "
            "rizika, sledují závažné incidenty a ohlásí je, zajistí odpovídající úroveň kybernetické "
            "ochrany. Modely s otevřenou licencí mají zjednodušené povinnosti."
        ),
    },
    {
        "article": "čl. 71-74",
        "title": "Správní řízení a sankce",
        "content": (
            "Členské státy stanoví pravidla pro sankce za porušení tohoto nařízení. "
            "Porušení zakázaných praktik (čl. 5): pokuta až 35 000 000 EUR nebo 7 % celkového "
            "celosvětového ročního obratu. Nesoulad s požadavky na vysoce rizikové systémy AI nebo "
            "jinými povinnostmi: pokuta až 15 000 000 EUR nebo 3 % obratu. Poskytnutí nesprávných "
            "nebo zavádějících informací: pokuta až 7 500 000 EUR nebo 1 % obratu. "
            "U malých a středních podniků a startupů se horní hranice pokuty snižuje, "
            "případně se zohledňují příjmy. Při rozhodování o pokutě se přihlíží k povaze, závažnosti "
            "a délce trvání porušení, k jakémukoliv opatření přijatému k jeho nápravě."
        ),
    },
    {
        "article": "čl. 99",
        "title": "Vstup v platnost a použitelnost",
        "content": (
            "Nařízení vstoupilo v platnost 1. srpna 2024. Použitelnost: "
            "Od 2. února 2025 — zakázané praktiky (čl. 5) a gramotnost v oblasti AI (čl. 4). "
            "Od 2. srpna 2025 — povinnosti pro modely AI pro obecné účely (kapitola V). "
            "Od 2. srpna 2026 — plná účinnost, včetně vysoce rizikových systémů AI (příloha III). "
            "Od 2. srpna 2027 — vysoce rizikové systémy AI, které jsou bezpečnostní komponentou "
            "produktů (příloha I, čl. 6 odst. 1). "
            "České firmy musí být v souladu s čl. 4 a čl. 5 již od 2. února 2025."
        ),
    },
    {
        "article": "příloha III",
        "title": "Oblasti vysoce rizikových systémů AI",
        "content": (
            "1. Biometrie: vzdálená biometrická identifikace, biometrická kategorizace, rozpoznávání emocí. "
            "2. Kritická infrastruktura: bezpečnostní komponenty řízení provozu silniční dopravy, "
            "zásobování vodou, plynem, vytápěním, elektřinou. "
            "3. Vzdělávání a odborná příprava: rozhodování o přijímání, hodnocení, sledování podvádění. "
            "4. Zaměstnanost, řízení pracovníků a přístup k samostatné výdělečné činnosti: nábor, "
            "výběr, rozhodování o povýšení nebo ukončení pracovního poměru, přidělování úkolů, "
            "sledování a hodnocení výkonu. "
            "5. Přístup k základním službám: hodnocení bonity fyzických osob, stanovení bodového "
            "hodnocení (credit scoring), posuzování žádostí o pojištění života a zdravotní pojištění, "
            "hodnocení a klasifikace tísňových volání. "
            "6. Prosazování práva: polygrafy, hodnocení spolehlivosti důkazů, profilování. "
            "7. Migrace, azyl a správa hranic: polygrafy, hodnocení rizik, rozpoznávání dokladů. "
            "8. Výkon spravedlnosti a demokratické procesy: výzkum a výklad práva a právních norem, "
            "řešení sporů, ovlivňování volebních výsledků."
        ),
    },
    {
        "article": "příloha IV",
        "title": "Technická dokumentace vysoce rizikových systémů AI",
        "content": (
            "Technická dokumentace musí obsahovat minimálně: "
            "1. Obecný popis systému AI — zamýšlený účel, vývojář, verze, interakce s hardware/software. "
            "2. Podrobný popis prvků systému AI a procesu jeho vývoje — metody a kroky výstavby, "
            "návrh systému, architektura, výpočetní zdroje, datové soubory, postupy tréninku. "
            "3. Podrobné informace o monitorování, fungování a kontrole systému AI. "
            "4. Popis vhodnosti metrik výkonnosti systému. "
            "5. Podrobný popis systému řízení rizik podle článku 9. "
            "6. Popis změn provedených během životního cyklu. "
            "7. Seznam harmonizovaných norem nebo společných specifikací. "
            "8. Kopie prohlášení o shodě EU. "
            "9. Popis systému hodnocení výkonnosti po uvedení na trh (post-market monitoring)."
        ),
    },
]


# ═══════════════════════════════════════════════════════════════
# Ingest — jednorázový import AI Actu do Supabase
# ═══════════════════════════════════════════════════════════════

async def embed_ai_act_chunks() -> dict:
    """
    Nahraje všechny klíčové články AI Act do Supabase s embeddingy.
    Bezpečné pro opakované spuštění — existující záznamy přeskočí.

    Returns:
        {"inserted": 15, "skipped": 3, "errors": 0}
    """
    sb = get_supabase()
    stats = {"inserted": 0, "skipped": 0, "errors": 0}

    for chunk in AI_ACT_ARTICLES:
        # Zkontroluj, zda článek už existuje
        existing = (
            sb.table("ai_act_chunks")
            .select("id")
            .eq("article", chunk["article"])
            .execute()
        )

        if existing.data:
            stats["skipped"] += 1
            logger.debug(f"[RAG] Přeskakuju {chunk['article']} — už existuje")
            continue

        try:
            # Vygeneruj embedding
            full_text = f"{chunk['article']} — {chunk['title']}\n\n{chunk['content']}"
            embedding = await _get_embedding(full_text)

            # Ulož do Supabase
            sb.table("ai_act_chunks").insert({
                "article": chunk["article"],
                "title": chunk["title"],
                "content": chunk["content"],
                "chunk_index": 0,
                "embedding": embedding,
                "metadata": {"source": "EU_2024_1689", "language": "cs"},
            }).execute()

            stats["inserted"] += 1
            logger.info(f"[RAG] Vložen {chunk['article']}: {chunk['title']}")

        except Exception as e:
            stats["errors"] += 1
            logger.error(f"[RAG] Chyba při vkládání {chunk['article']}: {e}")

    logger.info(f"[RAG] Import hotov: {stats}")
    return stats


# ═══════════════════════════════════════════════════════════════
# Retrieve — vyhledávání relevantních článků
# ═══════════════════════════════════════════════════════════════

async def retrieve_relevant_context(
    query: str,
    top_k: int = 5,
    threshold: float = 0.45,
) -> list[dict]:
    """
    Najde nejrelevantnější články AI Act pro daný dotaz.

    Args:
        query: Dotaz (např. "chatbot na webu" nebo "HR recruitment AI")
        top_k: Počet výsledků
        threshold: Minimální cosine similarity

    Returns:
        [{"article": "čl. 50", "title": "...", "content": "...", "similarity": 0.82}, ...]
    """
    sb = get_supabase()

    # Embedding dotazu
    query_embedding = await _get_embedding(query)

    # Cosine similarity search přes Supabase RPC
    result = sb.rpc("match_ai_act_chunks", {
        "query_embedding": query_embedding,
        "match_threshold": threshold,
        "match_count": top_k,
    }).execute()

    if not result.data:
        logger.debug(f"[RAG] Žádný relevantní kontext pro: {query[:80]}...")
        return []

    logger.info(
        f"[RAG] Nalezeno {len(result.data)} relevantních článků "
        f"(top similarity: {result.data[0].get('similarity', 0):.3f})"
    )

    return result.data


async def enrich_prompt_with_rag(
    base_prompt: str,
    query: str,
    top_k: int = 5,
    threshold: float = 0.45,
) -> str:
    """
    Obohatí prompt o relevantní kontext z AI Act.
    Přidá citace jako kontext před hlavní instrukci.

    Args:
        base_prompt: Původní systémový prompt
        query: Kontext pro vyhledávání (typicky user message nebo popis AI systému)
        top_k: Max počet článků
        threshold: Min similarity

    Returns:
        Obohacený prompt s citacemi z AI Act
    """
    try:
        chunks = await retrieve_relevant_context(query, top_k=top_k, threshold=threshold)
    except Exception as e:
        logger.warning(f"[RAG] Nelze získat kontext — pokračuji bez RAG: {e}")
        return base_prompt

    if not chunks:
        return base_prompt

    # Sestav kontext z nalezených článků
    rag_context = "RELEVANTNÍ USTANOVENÍ AI ACT (Nařízení EU 2024/1689):\n\n"
    for chunk in chunks:
        article = chunk.get("article", "?")
        title = chunk.get("title", "")
        content = chunk.get("content", "")
        sim = chunk.get("similarity", 0)
        rag_context += f"── {article}: {title} (relevance: {sim:.2f}) ──\n{content}\n\n"

    rag_context += (
        "INSTRUKCE: Při odpovídání cituj konkrétní články AI Act z výše uvedeného kontextu. "
        "Nepoužívej informace o AI Act, které nejsou v kontextu — pokud si nejsi jistý, řekni to.\n\n"
    )

    enriched = rag_context + base_prompt
    logger.info(f"[RAG] Prompt obohacen o {len(chunks)} článků ({len(rag_context)} znaků)")

    return enriched


# ═══════════════════════════════════════════════════════════════
# Setup — SQL migrace (spustit jednou ručně v Supabase SQL Editor)
# ═══════════════════════════════════════════════════════════════

MIGRATION_SQL = """
-- Aktivace pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabulka pro chunky AI Actu
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

-- Index pro rychlé vyhledávání
CREATE INDEX IF NOT EXISTS idx_ai_act_chunks_embedding
    ON ai_act_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 20);

-- Unikátní index na článek (prevence duplicit)
CREATE UNIQUE INDEX IF NOT EXISTS idx_ai_act_chunks_article
    ON ai_act_chunks (article, chunk_index);

-- RPC funkce pro similarity search
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
"""


def print_migration_sql():
    """Vypíše SQL migraci pro Supabase SQL Editor."""
    print("=" * 60)
    print("SPUSŤTE NÁSLEDUJÍCÍ SQL V SUPABASE SQL EDITOR:")
    print("=" * 60)
    print(MIGRATION_SQL)
    print("=" * 60)
    print("Po spuštění SQL zavolejte: await embed_ai_act_chunks()")
    print("=" * 60)
