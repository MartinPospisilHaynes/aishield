#!/usr/bin/env python3
"""
Patch: Přidá M7 Smart Plan do dashboard.py

Injektuje volání M7 modulu po sestavení questionnaire_findings.
M7 přepíše hardcoded action_required texty do srozumitelné češtiny pomocí Gemini.
"""
import sys

DASHBOARD_PATH = "/opt/aishield/backend/api/dashboard.py"

# Přečíst soubor
with open(DASHBOARD_PATH) as f:
    content = f.read()

# ═══ PATCH 1: Přidat M7 volání po questionnaire analýze ═══

OLD_BLOCK = """    except Exception:
        pass  # Tabulka nemusí existovat

    # 7. Compliance skóre"""

NEW_BLOCK = """    except Exception:
        pass  # Tabulka nemusí existovat

    # 6b. M7 Smart Akční Plán — přepíše hardcoded texty pomocí LLM
    if questionnaire_findings or findings:
        try:
            from backend.documents.m7_smart_plan import get_or_generate_smart_plan
            smart_items = await get_or_generate_smart_plan(
                supabase=supabase,
                company_id=company_id,
                questionnaire_findings=questionnaire_findings,
                scan_findings=findings,
                company_name=company.get("name", "") if company else "",
                company_url=company.get("url", "") if company else "",
            )
            if smart_items:
                # Přepsat action_required v questionnaire_findings
                for qf in questionnaire_findings:
                    key = qf.get("question_key", "")
                    if key in smart_items:
                        qf["action_required"] = smart_items[key]
                # Přepsat action_required v scan findings
                for sf in findings:
                    scan_key = f"scan-{sf.get('name', '')}"
                    if scan_key in smart_items:
                        sf["action_required"] = smart_items[scan_key]
                logger.info(
                    f"[Dashboard] M7 smart plan aplikován: "
                    f"{len(smart_items)} položek přepsáno pro {company_id[:8]}"
                )
        except Exception as e:
            logger.warning(f"[Dashboard] M7 smart plan selhal (fallback na původní texty): {e}")

    # 7. Compliance skóre"""

assert OLD_BLOCK in content, "Guard failed — OLD_BLOCK pro M7 injekci nenalezen v dashboard.py!"
content = content.replace(OLD_BLOCK, NEW_BLOCK)

# Uložit
with open(DASHBOARD_PATH, "w") as f:
    f.write(content)

print(f"PATCH OK — M7 Smart Plan injektován do {DASHBOARD_PATH}")
print(f"  Velikost: {len(content)} bytů")
