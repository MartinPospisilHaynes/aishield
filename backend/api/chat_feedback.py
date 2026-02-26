"""
AIshield.cz — Chat Feedback API
═══════════════════════════════════════════════════════════════
Admin endpoints for viewing Uršula chat feedback & sentiment stats.
"""

import logging
from fastapi import APIRouter, Depends, Query
from backend.api.auth import AuthUser, require_admin
from backend.database import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/chat-feedback",
    dependencies=[Depends(require_admin)],
)
async def get_chat_feedback(
    limit: int = Query(50, ge=1, le=200),
    sentiment: str = Query(None, description="Filter: positive|negative|neutral|mixed"),
):
    """Get chat feedback entries for admin panel."""
    try:
        sb = get_supabase()
        q = sb.table("chat_feedback") \
            .select("*") \
            .order("created_at", desc=True)

        if sentiment:
            q = q.eq("ai_sentiment", sentiment)

        result = q.limit(limit).execute()
        return {"feedback": result.data or [], "total": len(result.data or [])}
    except Exception as e:
        logger.error(f"[FEEDBACK API] Error: {e}")
        return {"feedback": [], "total": 0, "error": str(e)}


@router.get(
    "/chat-feedback/stats",
    dependencies=[Depends(require_admin)],
)
async def get_chat_feedback_stats():
    """Get aggregated chat feedback statistics."""
    try:
        sb = get_supabase()
        result = sb.table("chat_feedback") \
            .select("ai_sentiment, ai_humor_reception, feedback_sentiment, completion_status, questions_answered") \
            .execute()

        data = result.data or []
        total = len(data)
        if total == 0:
            return {
                "total": 0,
                "sentiment": {},
                "humor": {},
                "completion": {},
                "avg_questions": 0,
            }

        # Sentiment distribution
        sentiment_counts = {}
        for row in data:
            s = row.get("ai_sentiment") or "unknown"
            sentiment_counts[s] = sentiment_counts.get(s, 0) + 1

        # Humor reception distribution
        humor_counts = {}
        for row in data:
            h = row.get("ai_humor_reception") or "unknown"
            humor_counts[h] = humor_counts.get(h, 0) + 1

        # Completion distribution
        completion_counts = {}
        for row in data:
            c = row.get("completion_status") or "unknown"
            completion_counts[c] = completion_counts.get(c, 0) + 1

        # Average questions answered
        q_counts = [row.get("questions_answered") or 0 for row in data]
        avg_questions = round(sum(q_counts) / len(q_counts), 1) if q_counts else 0

        return {
            "total": total,
            "sentiment": sentiment_counts,
            "humor": humor_counts,
            "completion": completion_counts,
            "avg_questions": avg_questions,
        }
    except Exception as e:
        logger.error(f"[FEEDBACK STATS] Error: {e}")
        return {"total": 0, "sentiment": {}, "humor": {}, "completion": {}, "avg_questions": 0, "error": str(e)}
