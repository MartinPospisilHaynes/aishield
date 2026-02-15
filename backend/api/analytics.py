"""
AIshield.cz — Analytics API
Sběr behaviorálních eventů z frontendu.
Endpoint přijímá batch eventů, obohacuje o device/browser info a ukládá do Supabase.
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

from backend.database import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Modely ──

class AnalyticsEvent(BaseModel):
    """Jeden event z frontendu."""
    session_id: str
    event_name: str
    properties: dict = {}
    page_url: Optional[str] = None
    referrer: Optional[str] = None
    user_email: Optional[str] = None
    duration_ms: Optional[int] = None
    timestamp: Optional[str] = None  # ISO string from frontend


class AnalyticsBatch(BaseModel):
    """Batch eventů — frontend posílá po dávkách."""
    events: list[AnalyticsEvent]


# ── Helpers ──

def _parse_user_agent(ua: str) -> dict:
    """Jednoduchý parser user-agenta — bez externích závislostí."""
    result = {"device": "desktop", "browser": "unknown", "os": "unknown"}

    ua_lower = ua.lower()

    # Device
    if "mobile" in ua_lower or "android" in ua_lower:
        result["device"] = "mobile"
    elif "tablet" in ua_lower or "ipad" in ua_lower:
        result["device"] = "tablet"

    # Browser
    if "edg/" in ua_lower or "edge/" in ua_lower:
        result["browser"] = "Edge"
    elif "opr/" in ua_lower or "opera" in ua_lower:
        result["browser"] = "Opera"
    elif "chrome" in ua_lower and "chromium" not in ua_lower:
        result["browser"] = "Chrome"
    elif "firefox" in ua_lower:
        result["browser"] = "Firefox"
    elif "safari" in ua_lower:
        result["browser"] = "Safari"

    # OS
    if "windows" in ua_lower:
        result["os"] = "Windows"
    elif "mac os" in ua_lower or "macintosh" in ua_lower:
        result["os"] = "macOS"
    elif "linux" in ua_lower:
        result["os"] = "Linux"
    elif "android" in ua_lower:
        result["os"] = "Android"
    elif "iphone" in ua_lower or "ipad" in ua_lower:
        result["os"] = "iOS"

    return result


def _hash_ip(ip: str) -> str:
    """Hash IP adresy — GDPR friendly, nelze zpětně deanonymizovat."""
    return hashlib.sha256(f"aishield_salt_{ip}".encode()).hexdigest()[:16]


# ── Endpoints ──

@router.post("/event", status_code=202)
async def track_event(body: AnalyticsBatch, request: Request):
    """
    Přijme batch analytických eventů z frontendu a uloží je do Supabase.
    Vrací 202 Accepted — fire-and-forget, frontend nečeká na odpověď.
    """
    if not body.events:
        return {"status": "ok", "saved": 0}

    # Limit na 50 eventů v jednom batchi (ochrana proti zneužití)
    events = body.events[:50]

    # User-Agent parsing
    ua_string = request.headers.get("user-agent", "")
    ua_info = _parse_user_agent(ua_string)

    # IP hash
    forwarded = request.headers.get("x-forwarded-for", "")
    client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
    ip_hash = _hash_ip(client_ip)

    # Prepare rows for batch insert
    rows = []
    for ev in events:
        rows.append({
            "session_id": ev.session_id,
            "event_name": ev.event_name,
            "properties": ev.properties,
            "page_url": ev.page_url,
            "referrer": ev.referrer,
            "user_email": ev.user_email,
            "device": ua_info["device"],
            "browser": ua_info["browser"],
            "os": ua_info["os"],
            "ip_hash": ip_hash,
            "duration_ms": ev.duration_ms,
            "created_at": ev.timestamp or datetime.now(timezone.utc).isoformat(),
        })

    try:
        sb = get_supabase()
        sb.table("analytics_events").insert(rows).execute()
        logger.info(f"Analytics: saved {len(rows)} events (session={events[0].session_id[:8]}...)")
    except Exception as e:
        logger.error(f"Analytics insert failed: {e}")
        # Don't fail the request — analytics should never break the app
        return {"status": "partial", "error": str(e), "saved": 0}

    return {"status": "ok", "saved": len(rows)}


@router.get("/events")
async def get_events(
    limit: int = 100,
    event_name: Optional[str] = None,
    session_id: Optional[str] = None,
    since: Optional[str] = None,
):
    """
    Admin endpoint — vrací posledních N eventů.
    Filtrovat lze podle event_name, session_id, since (ISO date).
    """
    try:
        sb = get_supabase()
        q = sb.table("analytics_events").select("*").order("created_at", desc=True).limit(limit)

        if event_name:
            q = q.eq("event_name", event_name)
        if session_id:
            q = q.eq("session_id", session_id)
        if since:
            q = q.gte("created_at", since)

        result = q.execute()
        return {"events": result.data, "count": len(result.data)}
    except Exception as e:
        logger.error(f"Analytics fetch failed: {e}")
        return {"events": [], "count": 0, "error": str(e)}


@router.get("/stats")
async def get_analytics_stats(days: int = 30):
    """
    Agregované statistiky pro admin panel — funnely, top stránky, denní počty.
    """
    try:
        sb = get_supabase()
        from datetime import timedelta
        since_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        # All events in the period
        result = sb.table("analytics_events") \
            .select("event_name, page_url, session_id, created_at, properties, duration_ms") \
            .gte("created_at", since_date) \
            .order("created_at", desc=True) \
            .limit(10000) \
            .execute()

        events = result.data

        # ── Funnel ──
        unique_sessions = set()
        funnel = {
            "page_view": set(),
            "scan_url_entered": set(),
            "scan_started": set(),
            "scan_completed": set(),
            "email_entered": set(),
            "email_verified": set(),
            "registration_completed": set(),
            "questionnaire_started": set(),
            "questionnaire_completed": set(),
            "pricing_page_viewed": set(),
            "checkout_started": set(),
            "payment_completed": set(),
        }

        # ── Top pages ──
        page_counts: dict[str, int] = {}

        # ── Daily counts ──
        daily_counts: dict[str, int] = {}

        # ── Event type counts ──
        event_type_counts: dict[str, int] = {}

        # ── Questionnaire analytics ──
        question_times: dict[str, list[int]] = {}  # question_id -> [time_ms, ...]
        question_changes: dict[str, int] = {}       # question_id -> change_count
        nevim_count = 0

        for ev in events:
            sid = ev.get("session_id", "")
            name = ev.get("event_name", "")
            unique_sessions.add(sid)

            # Funnel
            if name in funnel:
                funnel[name].add(sid)

            # Top pages
            page = ev.get("page_url", "")
            if page and name == "page_view":
                page_counts[page] = page_counts.get(page, 0) + 1

            # Daily
            day = ev.get("created_at", "")[:10]
            if day:
                daily_counts[day] = daily_counts.get(day, 0) + 1

            # Event type
            event_type_counts[name] = event_type_counts.get(name, 0) + 1

            # Questionnaire
            props = ev.get("properties") or {}
            if name == "question_answered":
                qid = str(props.get("question_id", ""))
                time_ms = ev.get("duration_ms") or props.get("time_spent_ms", 0)
                if qid and time_ms:
                    question_times.setdefault(qid, []).append(time_ms)
                if props.get("answer_type") == "nevim":
                    nevim_count += 1

            if name == "question_changed":
                qid = str(props.get("question_id", ""))
                question_changes[qid] = question_changes.get(qid, 0) + 1

        # Compute averages for questions
        question_avg_times = {
            qid: round(sum(times) / len(times))
            for qid, times in question_times.items()
            if times
        }

        # Sort top pages
        top_pages = sorted(page_counts.items(), key=lambda x: x[1], reverse=True)[:20]

        # Sort daily
        daily_sorted = sorted(daily_counts.items())

        return {
            "total_events": len(events),
            "unique_sessions": len(unique_sessions),
            "funnel": {k: len(v) for k, v in funnel.items()},
            "top_pages": [{"page": p, "views": c} for p, c in top_pages],
            "daily": [{"date": d, "count": c} for d, c in daily_sorted],
            "event_types": dict(sorted(event_type_counts.items(), key=lambda x: x[1], reverse=True)),
            "questionnaire": {
                "avg_time_per_question": question_avg_times,
                "changes_per_question": question_changes,
                "total_nevim_answers": nevim_count,
            },
        }
    except Exception as e:
        logger.error(f"Analytics stats failed: {e}")
        return {"error": str(e)}


@router.get("/sessions")
async def get_sessions(limit: int = 50):
    """Vrací seznam unikátních sessions s metadaty."""
    try:
        sb = get_supabase()
        result = sb.table("analytics_events") \
            .select("session_id, device, browser, os, ip_hash, created_at, page_url, user_email") \
            .order("created_at", desc=True) \
            .limit(5000) \
            .execute()

        sessions: dict[str, dict] = {}
        for ev in result.data:
            sid = ev["session_id"]
            if sid not in sessions:
                sessions[sid] = {
                    "session_id": sid,
                    "device": ev.get("device"),
                    "browser": ev.get("browser"),
                    "os": ev.get("os"),
                    "first_seen": ev.get("created_at"),
                    "last_seen": ev.get("created_at"),
                    "user_email": ev.get("user_email"),
                    "pages": set(),
                    "event_count": 0,
                }
            s = sessions[sid]
            s["event_count"] += 1
            s["last_seen"] = ev.get("created_at")  # since ordered DESC, first is latest
            if ev.get("page_url"):
                s["pages"].add(ev["page_url"])
            if ev.get("user_email") and not s["user_email"]:
                s["user_email"] = ev["user_email"]

        # Convert sets to lists and sort by last_seen
        session_list = []
        for s in sessions.values():
            s["pages"] = list(s["pages"])
            s["page_count"] = len(s["pages"])
            session_list.append(s)

        session_list.sort(key=lambda x: x.get("last_seen", ""), reverse=True)

        return {"sessions": session_list[:limit], "total": len(session_list)}
    except Exception as e:
        logger.error(f"Analytics sessions failed: {e}")
        return {"sessions": [], "total": 0, "error": str(e)}
