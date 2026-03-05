"""
AIshield.cz — LinkedIn Admin API Router
Endpointy pro správu LinkedIn obsahu z admin panelu.

Endpointy:
- GET  /api/admin/linkedin/posts       — Seznam postů (s filtrací)
- POST /api/admin/linkedin/posts       — Vytvořit post (draft)
- PUT  /api/admin/linkedin/posts/{id}  — Upravit post
- DEL  /api/admin/linkedin/posts/{id}  — Smazat post
- POST /api/admin/linkedin/posts/{id}/approve  — Schválit post
- POST /api/admin/linkedin/posts/{id}/publish  — Publikovat post
- POST /api/admin/linkedin/generate    — AI generování obsahu
- GET  /api/admin/linkedin/stats       — Souhrnné statistiky
- GET  /api/admin/linkedin/calendar    — Obsahový kalendář
- GET  /api/admin/linkedin/pillars     — Distribuce pilířů
- GET  /api/admin/linkedin/oauth/url   — OAuth URL
- GET  /api/admin/linkedin/oauth/callback — OAuth callback
- GET  /api/admin/linkedin/oauth/status — Stav OAuth připojení
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from backend.api.auth import AuthUser, require_admin
from backend.api.rate_limit import admin_limiter
from backend.database import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Rate limit ──
async def _check_admin_rate_limit(request: Request):
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    ip = ip.split(",")[0].strip()
    allowed, retry_after = admin_limiter.check(ip)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Příliš mnoho požadavků. Zkuste za {retry_after}s.",
            headers={"Retry-After": str(retry_after)},
        )


# ══════════════════════════════════════════════════════════════════════
# PYDANTIC MODELY
# ══════════════════════════════════════════════════════════════════════

class PostCreateRequest(BaseModel):
    """Vytvoření nového postu (manuální draft)."""
    content: str = Field(..., min_length=10, max_length=3000)
    hashtags: list[str] = Field(default_factory=list)
    target: str = Field(default="personal", pattern="^(personal|company)$")
    content_pillar: str = Field(default="ai_act")
    image_urls: list[str] = Field(default_factory=list)
    first_comment_text: str = Field(default="")
    scheduled_at: Optional[str] = None


class PostUpdateRequest(BaseModel):
    """Úprava existujícího postu."""
    content: Optional[str] = Field(None, min_length=10, max_length=3000)
    hashtags: Optional[list[str]] = None
    target: Optional[str] = Field(None, pattern="^(personal|company)$")
    content_pillar: Optional[str] = None
    image_urls: Optional[list[str]] = None
    first_comment_text: Optional[str] = None
    scheduled_at: Optional[str] = None


class GenerateRequest(BaseModel):
    """AI generování obsahu."""
    topic: Optional[str] = None
    pillar_id: Optional[str] = None
    context: Optional[str] = None
    target: str = Field(default="personal", pattern="^(personal|company)$")
    scheduled_at: Optional[str] = None


# ══════════════════════════════════════════════════════════════════════
# POSTY — CRUD
# ══════════════════════════════════════════════════════════════════════

@router.get("/linkedin/posts")
async def list_posts(
    status: Optional[str] = Query(None, description="Filtr: draft|approved|published|failed"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: AuthUser = Depends(require_admin),
    request: Request = None,
):
    """Seznam LinkedIn postů s filtrací."""
    await _check_admin_rate_limit(request)
    sb = get_supabase()

    query = sb.table("linkedin_posts").select("*").order("created_at", desc=True)
    if status:
        query = query.eq("status", status)
    query = query.range(offset, offset + limit - 1)

    result = query.execute()
    return {"posts": result.data or [], "count": len(result.data or [])}


@router.post("/linkedin/posts")
async def create_post(
    body: PostCreateRequest,
    user: AuthUser = Depends(require_admin),
    request: Request = None,
):
    """Vytvořit nový post (draft)."""
    await _check_admin_rate_limit(request)
    sb = get_supabase()

    row = {
        "content": body.content,
        "hashtags": body.hashtags,
        "status": "draft",
        "target": body.target,
        "content_pillar": body.content_pillar,
        "image_urls": body.image_urls,
        "first_comment_text": body.first_comment_text,
        "score": 0,
    }
    if body.scheduled_at:
        row["scheduled_at"] = body.scheduled_at

    result = sb.table("linkedin_posts").insert(row).execute()
    logger.info(f"LinkedIn post vytvořen: #{result.data[0]['id'] if result.data else '?'}")
    return {"post": result.data[0] if result.data else {}, "ok": True}


@router.put("/linkedin/posts/{post_id}")
async def update_post(
    post_id: int,
    body: PostUpdateRequest,
    user: AuthUser = Depends(require_admin),
    request: Request = None,
):
    """Upravit existující post (jen draft/approved)."""
    await _check_admin_rate_limit(request)
    sb = get_supabase()

    # Ověř že post existuje a není publikovaný
    existing = sb.table("linkedin_posts").select("status").eq("id", post_id).single().execute()
    if not existing.data:
        raise HTTPException(404, "Post nenalezen")
    if existing.data["status"] == "published":
        raise HTTPException(400, "Publikovaný post nelze editovat")

    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(400, "Žádná data k aktualizaci")

    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = sb.table("linkedin_posts").update(update_data).eq("id", post_id).execute()

    logger.info(f"LinkedIn post #{post_id} aktualizován")
    return {"post": result.data[0] if result.data else {}, "ok": True}


@router.delete("/linkedin/posts/{post_id}")
async def delete_post(
    post_id: int,
    user: AuthUser = Depends(require_admin),
    request: Request = None,
):
    """Smazat post (jen draft)."""
    await _check_admin_rate_limit(request)
    sb = get_supabase()

    existing = sb.table("linkedin_posts").select("status").eq("id", post_id).single().execute()
    if not existing.data:
        raise HTTPException(404, "Post nenalezen")
    if existing.data["status"] == "published":
        raise HTTPException(400, "Publikovaný post nelze smazat")

    sb.table("linkedin_posts").delete().eq("id", post_id).execute()
    logger.info(f"LinkedIn post #{post_id} smazán")
    return {"ok": True}


# ══════════════════════════════════════════════════════════════════════
# WORKFLOW — APPROVE & PUBLISH
# ══════════════════════════════════════════════════════════════════════

@router.post("/linkedin/posts/{post_id}/approve")
async def approve_post(
    post_id: int,
    user: AuthUser = Depends(require_admin),
    request: Request = None,
):
    """Manuální schválení postu (draft → approved). ŽÁDNÉ auto-approve!"""
    await _check_admin_rate_limit(request)
    sb = get_supabase()

    existing = sb.table("linkedin_posts").select("status").eq("id", post_id).single().execute()
    if not existing.data:
        raise HTTPException(404, "Post nenalezen")
    if existing.data["status"] != "draft":
        raise HTTPException(400, f"Post musí být ve stavu 'draft', je '{existing.data['status']}'")

    sb.table("linkedin_posts").update({
        "status": "approved",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", post_id).execute()

    logger.info(f"LinkedIn post #{post_id} schválen")
    return {"ok": True, "new_status": "approved"}


@router.post("/linkedin/posts/{post_id}/publish")
async def publish_post(
    post_id: int,
    user: AuthUser = Depends(require_admin),
    request: Request = None,
):
    """
    Publikovat schválený post na LinkedIn.
    Vyžaduje approved status a platný OAuth token.
    """
    await _check_admin_rate_limit(request)
    sb = get_supabase()

    existing = sb.table("linkedin_posts").select("*").eq("id", post_id).single().execute()
    if not existing.data:
        raise HTTPException(404, "Post nenalezen")
    if existing.data["status"] != "approved":
        raise HTTPException(400, f"Post musí být 'approved' pro publikaci, je '{existing.data['status']}'")

    post = existing.data
    target = post.get("target", "personal")

    try:
        from backend.linkedin.publisher import (
            publish_text_post,
            publish_image_post,
            post_first_comment,
        )

        # Publikace — s obrázky nebo bez
        image_urls = post.get("image_urls") or []
        if image_urls:
            result = await publish_image_post(
                content=post["content"],
                image_urls=image_urls,
                target=target,
            )
        else:
            result = await publish_text_post(
                content=post["content"],
                target=target,
            )

        post_urn = result.get("post_urn", "")

        # First-comment (pokud je definovaný)
        first_comment_urn = ""
        if post.get("first_comment_text") and post_urn:
            fc_result = await post_first_comment(
                post_urn=post_urn,
                comment_text=post["first_comment_text"],
                target=target,
            )
            first_comment_urn = fc_result.get("comment_urn", "")

        # Aktualizace DB
        sb.table("linkedin_posts").update({
            "status": "published",
            "linkedin_post_urn": post_urn,
            "first_comment_urn": first_comment_urn,
            "published_at": datetime.now(timezone.utc).isoformat(),
            "error_message": None,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", post_id).execute()

        logger.info(f"LinkedIn post #{post_id} publikován: {post_urn}")
        return {"ok": True, "post_urn": post_urn}

    except Exception as e:
        # Zaznamenat chybu
        sb.table("linkedin_posts").update({
            "status": "failed",
            "error_message": str(e)[:500],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", post_id).execute()

        logger.error(f"LinkedIn publikace selhala pro post #{post_id}: {e}")
        raise HTTPException(500, f"Publikace selhala: {str(e)[:200]}")


# ══════════════════════════════════════════════════════════════════════
# AI GENEROVÁNÍ
# ══════════════════════════════════════════════════════════════════════

@router.post("/linkedin/generate")
async def generate_content(
    body: GenerateRequest,
    user: AuthUser = Depends(require_admin),
    request: Request = None,
):
    """AI-generování LinkedIn obsahu. Uloží jako draft."""
    await _check_admin_rate_limit(request)

    from backend.linkedin.content_engine import generate_and_save

    result = await generate_and_save(
        topic=body.topic,
        pillar_id=body.pillar_id,
        context=body.context,
        target=body.target,
        scheduled_at=body.scheduled_at,
    )

    return {"post": result, "ok": True}


# ══════════════════════════════════════════════════════════════════════
# STATISTIKY & KALENDÁŘ
# ══════════════════════════════════════════════════════════════════════

@router.get("/linkedin/stats")
async def get_stats(
    user: AuthUser = Depends(require_admin),
    request: Request = None,
):
    """Souhrnné LinkedIn statistiky pro dashboard."""
    await _check_admin_rate_limit(request)
    sb = get_supabase()

    # Počty postů dle statusu
    all_posts = sb.table("linkedin_posts").select("id, status, published_at").execute()
    posts = all_posts.data or []

    status_counts = {"draft": 0, "approved": 0, "published": 0, "failed": 0}
    for p in posts:
        s = p.get("status", "draft")
        status_counts[s] = status_counts.get(s, 0) + 1

    # Poslední metriky
    latest_metrics = sb.table("linkedin_post_metrics").select(
        "impressions, likes, comments, shares, clicks, engagement_rate"
    ).order("measured_at", desc=True).limit(20).execute()

    total_impressions = sum(m.get("impressions", 0) for m in (latest_metrics.data or []))
    total_engagement = sum(
        m.get("likes", 0) + m.get("comments", 0) + m.get("shares", 0)
        for m in (latest_metrics.data or [])
    )
    avg_engagement_rate = 0.0
    rates = [m.get("engagement_rate", 0) for m in (latest_metrics.data or []) if m.get("engagement_rate")]
    if rates:
        avg_engagement_rate = round(sum(rates) / len(rates), 2)

    # UTM statistiky (posledních 30 dní)
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()[:10]
    utm = sb.table("linkedin_utm_stats").select("visits, scans_started, registrations").gte(
        "date", cutoff
    ).execute()
    total_visits = sum(u.get("visits", 0) for u in (utm.data or []))
    total_scans = sum(u.get("scans_started", 0) for u in (utm.data or []))
    total_regs = sum(u.get("registrations", 0) for u in (utm.data or []))

    return {
        "posts": status_counts,
        "total_posts": len(posts),
        "metrics": {
            "impressions": total_impressions,
            "engagement": total_engagement,
            "avg_engagement_rate": avg_engagement_rate,
        },
        "conversions": {
            "visits": total_visits,
            "scans_started": total_scans,
            "registrations": total_regs,
        },
    }


@router.get("/linkedin/calendar")
async def get_calendar(
    days: int = Query(30, ge=7, le=90),
    user: AuthUser = Depends(require_admin),
    request: Request = None,
):
    """Obsahový kalendář."""
    await _check_admin_rate_limit(request)

    from backend.linkedin.content_engine import get_content_calendar
    posts = await get_content_calendar(days)
    return {"calendar": posts, "days": days}


@router.get("/linkedin/pillars")
async def get_pillars(
    days: int = Query(90, ge=30, le=365),
    user: AuthUser = Depends(require_admin),
    request: Request = None,
):
    """Distribuce obsahových pilířů."""
    await _check_admin_rate_limit(request)

    from backend.linkedin.content_engine import get_pillar_distribution
    distribution = await get_pillar_distribution(days)
    return {"distribution": distribution, "days": days}


# ══════════════════════════════════════════════════════════════════════
# OAUTH
# ══════════════════════════════════════════════════════════════════════

@router.get("/linkedin/oauth/url")
async def get_oauth_url(
    target: str = Query("personal", pattern="^(personal|company)$"),
    user: AuthUser = Depends(require_admin),
    request: Request = None,
):
    """Vrátí OAuth authorization URL pro LinkedIn."""
    await _check_admin_rate_limit(request)

    from backend.linkedin.publisher import get_oauth_url as _get_url
    url = _get_url(target)
    return {"url": url, "target": target}


@router.get("/linkedin/oauth/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(""),
    request: Request = None,
):
    """
    OAuth callback — LinkedIn přesměruje sem po autorizaci.
    Nevyžaduje admin auth (LinkedIn posílá GET bez našich cookies).
    """
    from backend.linkedin.publisher import exchange_code_for_token, store_tokens

    # Rozpoznat target ze state
    target = "personal"
    if "company" in state:
        target = "company"

    try:
        tokens = await exchange_code_for_token(code)
        await store_tokens(
            target=target,
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token", ""),
            expires_in=tokens.get("expires_in", 5184000),
        )
        logger.info(f"LinkedIn OAuth úspěšný pro target={target}")
        # Přesměrovat zpátky do admin panelu
        return {"ok": True, "message": f"LinkedIn ({target}) úspěšně připojeno! Můžete zavřít toto okno."}
    except Exception as e:
        logger.error(f"LinkedIn OAuth chyba: {e}")
        raise HTTPException(400, f"OAuth autorizace selhala: {str(e)[:200]}")


@router.get("/linkedin/oauth/status")
async def get_oauth_status(
    user: AuthUser = Depends(require_admin),
    request: Request = None,
):
    """Zjistí stav OAuth připojení (connected/disconnected)."""
    await _check_admin_rate_limit(request)
    sb = get_supabase()

    result = sb.table("linkedin_tokens").select("target, updated_at, expires_in").execute()
    tokens = result.data or []

    status = {}
    for t in tokens:
        status[t["target"]] = {
            "connected": True,
            "updated_at": t["updated_at"],
            "expires_in": t["expires_in"],
        }

    return {
        "personal": status.get("personal", {"connected": False}),
        "company": status.get("company", {"connected": False}),
    }
