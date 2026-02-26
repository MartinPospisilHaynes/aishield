#!/usr/bin/env python3
"""Add /progress endpoint to questionnaire.py"""
FILE = "/opt/aishield/backend/api/questionnaire.py"

with open(FILE, "r") as f:
    content = f.read()

PROGRESS_EP = '''

@router.get("/questionnaire/{company_id}/progress")
async def get_questionnaire_progress(company_id: str):
    """Vrátí postup vyplnění dotazníku v procentech."""
    supabase = get_supabase()
    total_questions = sum(len(s["questions"]) for s in QUESTIONNAIRE_SECTIONS)

    client_id = await _get_client_id_for_company(supabase, company_id)
    if not client_id:
        return {
            "company_id": company_id,
            "total_questions": total_questions,
            "answered": 0,
            "unknown_count": 0,
            "percentage": 0,
            "status": "nezahajeno",
        }

    result = supabase.table("questionnaire_responses") \
        .select("question_key, answer") \
        .eq("client_id", client_id) \
        .execute()

    answered = len(result.data) if result.data else 0
    unknown_count = sum(1 for r in (result.data or []) if r.get("answer") == "unknown")
    pct = round((answered / total_questions) * 100) if total_questions > 0 else 0

    if pct == 0:
        status = "nezahajeno"
    elif pct < 100:
        status = "rozpracovano"
    else:
        status = "dokonceno"

    return {
        "company_id": company_id,
        "total_questions": total_questions,
        "answered": answered,
        "unknown_count": unknown_count,
        "percentage": pct,
        "status": status,
    }

'''

marker = '@router.get("/questionnaire/{company_id}/combined-report")'
if marker in content:
    content = content.replace(marker, PROGRESS_EP + marker)
    print("OK: added progress endpoint")
else:
    print("ERROR: marker not found")

with open(FILE, "w") as f:
    f.write(content)

print(f"Lines: {len(content.splitlines())}")
