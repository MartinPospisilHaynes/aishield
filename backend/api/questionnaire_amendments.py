"""
AIshield.cz — Questionnaire Amendment API

Endpointy pro:
1. PATCH /questionnaire/answer — změna jedné odpovědi + spuštění amendment pipeline
2. GET /questionnaire/can-edit — kontrola, zda klient může editovat (plánová omezení)
3. POST /admin/amendments/{id}/approve — admin schválení dodatku
4. POST /admin/amendments/{id}/reject — admin zamítnutí dodatku
5. GET /admin/amendments/pending — seznam dodatků čekajících na schválení
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from backend.database import get_supabase
from backend.api.auth import require_admin

logger = logging.getLogger(__name__)
router = APIRouter()


# ══════════════════════════════════════════════════════════════════════
# PLÁNOVÁ OMEZENÍ — kdy může klient editovat dotazník po doručení
# ══════════════════════════════════════════════════════════════════════

# Okno pro editaci (od delivered_at)
EDIT_WINDOW = {
    "basic": timedelta(days=0),       # Basic: žádná editace po doručení
    "pro": timedelta(days=30),        # Pro: 30 dní od doručení
    "enterprise": timedelta(days=730),  # Enterprise: 2 roky
}


def _can_edit_questionnaire(plan: str, delivered_at: Optional[str]) -> dict:
    """
    Zkontroluje, zda klient může editovat dotazník.

    Returns:
        {
            can_edit: bool,
            reason: str,
            days_remaining: int | None,
        }
    """
    # Před doručením může kdokoliv editovat
    if not delivered_at:
        return {"can_edit": True, "reason": "Dokumenty zatím nebyly doručeny.", "days_remaining": None}

    window = EDIT_WINDOW.get(plan, timedelta(days=0))

    # Basic nemá editaci vůbec
    if window.total_seconds() == 0:
        return {
            "can_edit": False,
            "reason": "Plán BASIC neumožňuje úpravu dotazníku po doručení dokumentů. Upgradujte na PRO nebo ENTERPRISE.",
            "days_remaining": 0,
        }

    # Kontrola časového okna
    if isinstance(delivered_at, str):
        delivered_dt = datetime.fromisoformat(delivered_at.replace("Z", "+00:00"))
    else:
        delivered_dt = delivered_at

    now = datetime.now(timezone.utc)
    expiry = delivered_dt + window
    remaining = expiry - now

    if remaining.total_seconds() <= 0:
        return {
            "can_edit": False,
            "reason": f"Vaše okno pro úpravu dotazníku vypršelo ({window.days} dní od doručení).",
            "days_remaining": 0,
        }

    return {
        "can_edit": True,
        "reason": f"Můžete upravovat dotazník ještě {remaining.days} dní.",
        "days_remaining": remaining.days,
    }


# ══════════════════════════════════════════════════════════════════════
# PYDANTIC MODELY
# ══════════════════════════════════════════════════════════════════════

class SingleAnswerPatch(BaseModel):
    """Změna jedné odpovědi v dotazníku."""
    company_id: str
    question_key: str
    section: str
    answer: str
    details: Optional[dict] = None
    tool_name: Optional[str] = None


class ApprovalRequest(BaseModel):
    """Admin schválení/zamítnutí dodatku."""
    note: Optional[str] = None


# ══════════════════════════════════════════════════════════════════════
# ENDPOINT: GET /questionnaire/can-edit
# ══════════════════════════════════════════════════════════════════════

@router.get("/questionnaire/can-edit/{company_id}")
async def check_can_edit(company_id: str):
    """Zkontroluje, zda klient může editovat dotazník."""
    supabase = get_supabase()

    # Načíst plán a delivered_at
    client = supabase.table("clients") \
        .select("plan") \
        .eq("company_id", company_id) \
        .limit(1).execute()

    if not client.data:
        return {"can_edit": True, "reason": "Klient nenalezen — editace povolena.", "days_remaining": None}

    plan = client.data[0].get("plan", "basic")

    # Zjistit delivered_at z orders
    order = supabase.table("orders") \
        .select("delivered_at") \
        .eq("company_id", company_id) \
        .eq("status", "paid") \
        .not_.is_("delivered_at", "null") \
        .order("delivered_at", desc=True) \
        .limit(1).execute()

    delivered_at = order.data[0]["delivered_at"] if order.data else None

    result = _can_edit_questionnaire(plan, delivered_at)
    result["plan"] = plan
    return result


# ══════════════════════════════════════════════════════════════════════
# ENDPOINT: PATCH /questionnaire/answer — změna jedné odpovědi
# ══════════════════════════════════════════════════════════════════════

@router.patch("/questionnaire/answer")
async def patch_single_answer(
    patch: SingleAnswerPatch,
    background_tasks: BackgroundTasks,
):
    """
    Změní jednu odpověď v dotazníku.
    Pokud existují doručené dokumenty a plán to umožňuje,
    spustí amendment pipeline na pozadí.
    """
    supabase = get_supabase()

    # ── 1. Najít client_id ──
    client = supabase.table("clients") \
        .select("id, plan, company_id") \
        .eq("company_id", patch.company_id) \
        .limit(1).execute()

    if not client.data:
        raise HTTPException(status_code=404, detail="Klient nenalezen.")

    client_id = client.data[0]["id"]
    plan = client.data[0].get("plan", "basic")

    # ── 2. Zkontrolovat plánová omezení ──
    order = supabase.table("orders") \
        .select("delivered_at") \
        .eq("company_id", patch.company_id) \
        .eq("status", "paid") \
        .not_.is_("delivered_at", "null") \
        .order("delivered_at", desc=True) \
        .limit(1).execute()

    delivered_at = order.data[0]["delivered_at"] if order.data else None
    edit_check = _can_edit_questionnaire(plan, delivered_at)

    if not edit_check["can_edit"]:
        raise HTTPException(status_code=403, detail=edit_check["reason"])

    # ── 3. Načíst starou odpověď ──
    old_result = supabase.table("questionnaire_responses") \
        .select("answer, details") \
        .eq("client_id", client_id) \
        .eq("question_key", patch.question_key) \
        .limit(1).execute()

    old_answer = old_result.data[0]["answer"] if old_result.data else None
    old_details = old_result.data[0].get("details") if old_result.data else None

    # ── 4. UPSERT nová odpověď ──
    row = {
        "client_id": client_id,
        "section": patch.section,
        "question_key": patch.question_key,
        "answer": patch.answer,
        "details": patch.details,
        "tool_name": patch.tool_name,
    }
    supabase.table("questionnaire_responses").upsert(
        row, on_conflict="client_id,question_key"
    ).execute()

    logger.info(f"[Questionnaire PATCH] {patch.question_key}: {old_answer} → {patch.answer}")

    # ── 5. Pokud se odpověď změnila A dokumenty byly doručeny → amendment ──
    has_documents = delivered_at is not None
    answer_changed = old_answer is not None and old_answer != patch.answer

    if answer_changed and has_documents:
        changes = [{
            "key": patch.question_key,
            "old_answer": old_answer,
            "new_answer": patch.answer,
            "old_details": old_details,
            "new_details": patch.details,
        }]

        # Spustit amendment pipeline na pozadí
        background_tasks.add_task(
            _run_amendment_pipeline,
            client_id=client_id,
            company_id=patch.company_id,
            changes=changes,
        )

        return {
            "status": "saved",
            "answer_changed": True,
            "amendment_triggered": True,
            "message": "Odpověď uložena. Generuji dodatek — po kontrole administrátorem vám bude zpřístupněn na dashboardu.",
        }

    return {
        "status": "saved",
        "answer_changed": answer_changed,
        "amendment_triggered": False,
        "message": "Odpověď uložena." if answer_changed else "Odpověď uložena (beze změny).",
    }


async def _run_amendment_pipeline(client_id: str, company_id: str, changes: list[dict]):
    """Background task pro spuštění amendment pipeline."""
    try:
        from backend.documents.amendment_pipeline import process_amendment
        result = await process_amendment(client_id, company_id, changes)
        logger.info(f"[Amendment BG] Hotovo: status={result['status']}, id={result.get('amendment_id')}")
    except Exception as e:
        logger.error(f"[Amendment BG] Chyba: {e}")


# ══════════════════════════════════════════════════════════════════════
# ADMIN ENDPOINTY — schvalování dodatků
# ══════════════════════════════════════════════════════════════════════

@router.get("/admin/amendments/pending", dependencies=[Depends(require_admin)])
async def get_pending_amendments():
    """Vrátí seznam dodatků čekajících na schválení."""
    supabase = get_supabase()

    result = supabase.table("documents") \
        .select("id, company_id, name, amendment_number, change_trigger, created_at, approval_status, url") \
        .eq("approval_status", "pending_review") \
        .not_.is_("amendment_number", "null") \
        .order("created_at", desc=True) \
        .execute()

    # Doplnit jména firem
    amendments = []
    for doc in result.data or []:
        company_name = "Neznámá firma"
        try:
            comp = supabase.table("companies").select("name") \
                .eq("id", doc["company_id"]).limit(1).execute()
            if comp.data:
                company_name = comp.data[0]["name"]
        except Exception:
            pass

        amendments.append({
            **doc,
            "company_name": company_name,
        })

    return {"amendments": amendments, "count": len(amendments)}


@router.post("/admin/amendments/{amendment_id}/approve", dependencies=[Depends(require_admin)])
async def approve_amendment(amendment_id: str, body: ApprovalRequest):
    """Admin schválí dodatek — zpřístupní se klientovi na dashboardu."""
    supabase = get_supabase()

    # Ověřit, že dokument existuje a je pending
    doc = supabase.table("documents") \
        .select("id, approval_status, company_id, amendment_number") \
        .eq("id", amendment_id) \
        .limit(1).execute()

    if not doc.data:
        raise HTTPException(status_code=404, detail="Dodatek nenalezen.")

    if doc.data[0]["approval_status"] != "pending_review":
        raise HTTPException(status_code=400, detail="Tento dodatek již byl zpracován.")

    # Schválit
    supabase.table("documents").update({
        "approval_status": "approved",
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "approved_by": "admin",
        "approval_note": body.note or "Schváleno administrátorem.",
    }).eq("id", amendment_id).execute()

    logger.info(f"[Admin] Dodatek {amendment_id} schválen")

    return {
        "status": "approved",
        "amendment_id": amendment_id,
        "message": "Dodatek schválen a zpřístupněn klientovi.",
    }


@router.post("/admin/amendments/{amendment_id}/reject", dependencies=[Depends(require_admin)])
async def reject_amendment(amendment_id: str, body: ApprovalRequest):
    """Admin zamítne dodatek."""
    supabase = get_supabase()

    doc = supabase.table("documents") \
        .select("id, approval_status") \
        .eq("id", amendment_id) \
        .limit(1).execute()

    if not doc.data:
        raise HTTPException(status_code=404, detail="Dodatek nenalezen.")

    if doc.data[0]["approval_status"] != "pending_review":
        raise HTTPException(status_code=400, detail="Tento dodatek již byl zpracován.")

    supabase.table("documents").update({
        "approval_status": "rejected",
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "approved_by": "admin",
        "approval_note": body.note or "Zamítnuto administrátorem.",
    }).eq("id", amendment_id).execute()

    logger.info(f"[Admin] Dodatek {amendment_id} zamítnut")

    return {
        "status": "rejected",
        "amendment_id": amendment_id,
        "message": "Dodatek zamítnut.",
    }
