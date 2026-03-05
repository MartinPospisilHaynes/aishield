"""
AIshield.cz — LinkedIn Content Engine
AI-generování LinkedIn obsahu s anti-AI-tone systémovým promptem.

4 obsahové pilíře:
1. AI Act edukace & novinky (40%)
2. Case studies & příklady z praxe (25%)
3. Behind-the-scenes / osobní příběhy (20%)
4. Tipy pro podnikatele (15%)

Generuje: text postu, hashtags, first-comment s UTM, skóre kvality.
Dodržuje: žádný AI-slop, konverzační tón, max 1300 znaků, 3-5 hashtagů.
"""

import json
import logging
import random
from datetime import datetime, timezone
from typing import Any

from backend.ai_engine.llm_client import llm_complete
from backend.database import get_supabase

logger = logging.getLogger(__name__)

# ── Obsahové pilíře s váhami ──
CONTENT_PILLARS = [
    {"id": "ai_act", "label": "AI Act edukace & novinky", "weight": 0.40},
    {"id": "case_study", "label": "Case studies & příklady z praxe", "weight": 0.25},
    {"id": "bts", "label": "Behind-the-scenes / osobní příběhy", "weight": 0.20},
    {"id": "tips", "label": "Tipy pro podnikatele", "weight": 0.15},
]

# ── Anti AI-slop systémový prompt ──
SYSTEM_PROMPT = """Jsi zkušený LinkedIn copywriter pro českou B2B SaaS firmu AIshield.cz
(AI Act compliance platforma pro české firmy).

PRAVIDLA:
1. Piš ČESKY, přirozeně, konverzačním tónem — jako by to psal skutečný člověk.
2. ZAKÁZANÁ slova a fráze (AI-slop): "v dnešním rychle se měnícím světě", "synergický",
   "holistický", "paradigmatický", "transformativní", "revoluční", "game-changer",
   "cutting-edge", "driving innovation", "leverage", "empower", "state-of-the-art",
   "proaktivní přístup", "v dnešní době", "není žádným tajemstvím".
3. Max 1300 znaků textu postu (LinkedIn ořezává po ~210 znacích, zbytek za "...více").
4. Prvních 210 znaků MUSÍ být hook — provokativní otázka, statistika, nebo kontroverzní tvrzení.
5. Používej odřádkování pro čitelnost (prázdné řádky mezi odstavci).
6. Konči CTA (call-to-action) — otázka do komentářů, nebo výzva k akci.
7. 3-5 relevantních hashtagů (česky i anglicky mix).
8. NIKDY nepoužívej emoji na začátku řádku.
9. Odkazuj na reálné české zákony, vyhlášky, nebo EU regulace kde je to relevantní.
10. Tón: sebevědomý expert, ne prodejce. Sdílíš know-how, ne reklamu.

STRUKTURA VÝSTUPU (JSON):
{
    "post_text": "celý text postu",
    "hashtags": ["#AIAct", "#GDPR", ...],
    "first_comment": "text prvního komentáře s UTM odkazem",
    "hook_score": 8,
    "content_pillar": "ai_act",
    "reasoning": "stručné zdůvodnění proč tento obsah funguje"
}"""

# ── UTM šablona ──
UTM_TEMPLATE = (
    "https://aishield.cz/?utm_source=linkedin&utm_medium=organic"
    "&utm_campaign={campaign}&utm_content={content_id}"
)


def _pick_pillar() -> dict[str, Any]:
    """Vybere obsahový pilíř podle vah."""
    weights = [p["weight"] for p in CONTENT_PILLARS]
    return random.choices(CONTENT_PILLARS, weights=weights, k=1)[0]


async def generate_post(
    topic: str | None = None,
    pillar_id: str | None = None,
    context: str | None = None,
) -> dict[str, Any]:
    """
    Vygeneruje LinkedIn post pomocí LLM.

    Args:
        topic: Volitelné téma (pokud None, AI vybere samo)
        pillar_id: Volitelný ID pilíře (pokud None, vybere se podle vah)
        context: Volitelný kontext (článek, novinka, data)

    Returns:
        {
            "post_text": str,
            "hashtags": list[str],
            "first_comment": str,
            "hook_score": int,
            "content_pillar": str,
            "reasoning": str,
        }
    """
    pillar = next(
        (p for p in CONTENT_PILLARS if p["id"] == pillar_id),
        _pick_pillar()
    ) if pillar_id else _pick_pillar()

    user_prompt = f"""Vygeneruj LinkedIn post pro AIshield.cz.

OBSAHOVÝ PILÍŘ: {pillar["label"]} ({pillar["id"]})
"""
    if topic:
        user_prompt += f"\nTÉMA: {topic}\n"
    if context:
        user_prompt += f"\nKONTEXT/PODKLAD:\n{context[:2000]}\n"

    user_prompt += f"""
FIRST-COMMENT UTM odkaz: Použij tento formát:
{UTM_TEMPLATE.format(campaign=pillar["id"], content_id="{{post_id}}")}
({{post_id}} nahraď krátkým ID jako "aiact-feb25" nebo podobně)

Vrať POUZE validní JSON dle specifikace v system promptu."""

    result = await llm_complete(
        system=SYSTEM_PROMPT,
        user=user_prompt,
        max_tokens=1500,
        temperature=0.7,
        prefer="claude",
    )

    # Parse JSON z odpovědi
    try:
        # Vyčistit markdown code block pokud je tam
        text = result.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]
        parsed = json.loads(text)
    except json.JSONDecodeError:
        logger.error(f"LLM vrátil nevalidní JSON: {result.text[:200]}")
        parsed = {
            "post_text": result.text,
            "hashtags": [],
            "first_comment": "",
            "hook_score": 0,
            "content_pillar": pillar["id"],
            "reasoning": "Chyba parsování — manuální korekce nutná",
        }

    # Zajistit všechny klíče
    parsed.setdefault("content_pillar", pillar["id"])
    parsed.setdefault("hook_score", 0)
    parsed.setdefault("hashtags", [])
    parsed.setdefault("first_comment", "")
    parsed.setdefault("reasoning", "")

    return parsed


async def generate_and_save(
    topic: str | None = None,
    pillar_id: str | None = None,
    context: str | None = None,
    target: str = "personal",
    scheduled_at: str | None = None,
) -> dict[str, Any]:
    """
    Vygeneruje post a uloží ho jako draft do DB.
    """
    generated = await generate_post(topic, pillar_id, context)

    sb = get_supabase()
    row = {
        "content": generated["post_text"],
        "hashtags": generated.get("hashtags", []),
        "status": "draft",
        "target": target,
        "content_pillar": generated.get("content_pillar", ""),
        "score": generated.get("hook_score", 0),
        "first_comment_text": generated.get("first_comment", ""),
        "image_urls": [],
    }
    if scheduled_at:
        row["scheduled_at"] = scheduled_at

    result = sb.table("linkedin_posts").insert(row).execute()
    post_data = result.data[0] if result.data else {}

    logger.info(f"LinkedIn draft uložen: #{post_data.get('id')} pillar={generated.get('content_pillar')}")

    return {
        **post_data,
        "reasoning": generated.get("reasoning", ""),
        "hook_score": generated.get("hook_score", 0),
    }


async def get_content_calendar(days: int = 30) -> list[dict[str, Any]]:
    """
    Vrátí obsahový kalendář na X dní dopředu.
    Zahrnuje plánované posty + doporučení pro prázdné sloty.
    """
    sb = get_supabase()
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days)

    posts = sb.table("linkedin_posts").select("*").gte(
        "scheduled_at", now.isoformat()
    ).lte(
        "scheduled_at", end.isoformat()
    ).order("scheduled_at").execute()

    return posts.data or []


async def get_pillar_distribution(days: int = 90) -> dict[str, Any]:
    """
    Spočítá distribuci obsahových pilířů za posledních X dní.
    Pro ověření, že dodržujeme 40/25/20/15 mix.
    """
    sb = get_supabase()
    from datetime import timedelta

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    posts = sb.table("linkedin_posts").select("content_pillar").in_(
        "status", ["published", "approved"]
    ).gte("created_at", cutoff).execute()

    counts: dict[str, int] = {}
    for post in posts.data or []:
        p = post.get("content_pillar", "unknown")
        counts[p] = counts.get(p, 0) + 1

    total = sum(counts.values()) or 1
    distribution = {
        pid: {
            "count": counts.get(pid, 0),
            "actual_pct": round(counts.get(pid, 0) / total * 100, 1),
            "target_pct": next((p["weight"] * 100 for p in CONTENT_PILLARS if p["id"] == pid), 0),
        }
        for pid in [p["id"] for p in CONTENT_PILLARS]
    }

    return distribution
