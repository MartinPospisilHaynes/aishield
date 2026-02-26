#!/usr/bin/env python3
"""
Model swap patch:
- M1 draft+retry: claude-opus-4-6 → claude-sonnet-4-6
- M1 Pass 2 + retry: claude-opus-4-6 → claude-sonnet-4-6
- M3: call_gemini (gemini-3.1-pro) → call_gemini with model="gemini-2.0-flash" + add GEMINI_FLASH constant
- M4: call_gemini → call_claude with model="claude-opus-4-6" (import change too)
- llm_engine: add GEMINI_FLASH_MODEL + costs, add model param to call_gemini
"""
import re, sys

BASE = "/opt/aishield/backend/documents"

def patch(filepath, old, new, label=""):
    with open(filepath, 'r') as f:
        content = f.read()
    if old not in content:
        print(f"  FAIL: {label} — pattern not found in {filepath}")
        return False
    count = content.count(old)
    content = content.replace(old, new, 1) if count > 1 else content.replace(old, new)
    if count > 1:
        print(f"  WARN: {label} — found {count} occurrences, replaced first only")
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"  OK: {label}")
    return True

def patch_all(filepath, old, new, label=""):
    with open(filepath, 'r') as f:
        content = f.read()
    if old not in content:
        print(f"  FAIL: {label} — pattern not found in {filepath}")
        return False
    count = content.count(old)
    content = content.replace(old, new)
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"  OK: {label} ({count} occurrences)")
    return True

ok = 0
fail = 0

# ═══════════════════════════════════════════════
# 1. M1 GENERATOR — all 4 Opus calls → Sonnet
# ═══════════════════════════════════════════════
print("\n=== M1 GENERATOR ===")
f = f"{BASE}/m1_generator.py"
r = patch_all(f, 'model="claude-opus-4-6"', 'model="claude-sonnet-4-6"', "M1: all opus → sonnet")
ok += 1 if r else 0; fail += 0 if r else 1

# ═══════════════════════════════════════════════
# 2. LLM_ENGINE — add Flash model + cost + model param to call_gemini
# ═══════════════════════════════════════════════
print("\n=== LLM_ENGINE ===")
f = f"{BASE}/llm_engine.py"

# Add GEMINI_FLASH constants after GEMINI_MODEL line
r = patch(f, 
    'GEMINI_MODEL = "gemini-3.1-pro-preview"',
    'GEMINI_MODEL = "gemini-3.1-pro-preview"\nGEMINI_FLASH_MODEL = "gemini-2.0-flash"',
    "llm_engine: add GEMINI_FLASH_MODEL")
ok += 1 if r else 0; fail += 0 if r else 1

# Add Flash costs after Gemini Pro costs
r = patch(f,
    'GEMINI_COST_OUTPUT = 12.0 / 1_000_000',
    'GEMINI_COST_OUTPUT = 12.0 / 1_000_000\nGEMINI_FLASH_COST_INPUT = 0.075 / 1_000_000\nGEMINI_FLASH_COST_OUTPUT = 0.30 / 1_000_000',
    "llm_engine: add Flash costs")
ok += 1 if r else 0; fail += 0 if r else 1

# ═══════════════════════════════════════════════
# 3. M3 CLIENT CRITIC — use Flash model
# ═══════════════════════════════════════════════
print("\n=== M3 CLIENT CRITIC ===")
f = f"{BASE}/m3_client_critic.py"

# Update docstring
r = patch(f,
    'AIshield.cz — Modul 3: CLIENT CRITIC (Gemini 3.1 Pro)',
    'AIshield.cz — Modul 3: CLIENT CRITIC (Gemini 2.0 Flash)',
    "M3: docstring")
ok += 1 if r else 0; fail += 0 if r else 1

r = patch(f,
    'Model: Gemini 3.1 Pro — cross-model validace (jiný model než M2).',
    'Model: Gemini 2.0 Flash — cross-model validace (jiný model než M2). Levný pro soft task.',
    "M3: model docstring")
ok += 1 if r else 0; fail += 0 if r else 1

# Update import to get Flash model constant
r = patch(f,
    'from backend.documents.llm_engine import call_gemini, parse_json',
    'from backend.documents.llm_engine import call_gemini, parse_json, GEMINI_FLASH_MODEL, GEMINI_FLASH_COST_INPUT, GEMINI_FLASH_COST_OUTPUT',
    "M3: import Flash constants")
ok += 1 if r else 0; fail += 0 if r else 1

# Update call_gemini to pass Flash model
r = patch(f,
    """    text, meta = await call_gemini(
        system=SYSTEM_PROMPT_M3,
        prompt=prompt,
        label=label,
        temperature=0.35,   # more diverse client perspectives
        max_tokens=8000,
    )""",
    """    text, meta = await call_gemini(
        system=SYSTEM_PROMPT_M3,
        prompt=prompt,
        label=label,
        temperature=0.35,   # more diverse client perspectives
        max_tokens=8000,
        model=GEMINI_FLASH_MODEL,
        cost_input=GEMINI_FLASH_COST_INPUT,
        cost_output=GEMINI_FLASH_COST_OUTPUT,
    )""",
    "M3: call_gemini with Flash model")
ok += 1 if r else 0; fail += 0 if r else 1

# ═══════════════════════════════════════════════
# 4. M4 REFINER — Gemini Pro → Claude Opus
# ═══════════════════════════════════════════════
print("\n=== M4 REFINER ===")
f = f"{BASE}/m4_refiner.py"

# Update docstring
r = patch(f,
    'AIshield.cz — Modul 4: REFINER (Claude Sonnet 4)',
    'AIshield.cz — Modul 4: REFINER (Claude Opus 4.6)',
    "M4: docstring title")
ok += 1 if r else 0; fail += 0 if r else 1

r = patch(f,
    'Model: Claude Sonnet 4 — nejlepší pro precizní editaci a syntézu.',
    'Model: Claude Opus 4.6 — nejlepší pro koherentní finální dokument (cross-chunk drift prevention).',
    "M4: model docstring")
ok += 1 if r else 0; fail += 0 if r else 1

# Change import from call_gemini to call_claude
r = patch(f,
    'from backend.documents.llm_engine import call_gemini, extract_html_content',
    'from backend.documents.llm_engine import call_claude, extract_html_content',
    "M4: import call_claude")
ok += 1 if r else 0; fail += 0 if r else 1

# First call_gemini → call_claude
r = patch(f,
    """    text, meta = await call_gemini(
        system=SYSTEM_PROMPT_M4,
        prompt=prompt,
        label=label,
        temperature=0.15,   # very focused, minimal creativity
        max_tokens=16000,   # must be >= M1 output
    )""",
    """    text, meta = await call_claude(
        system=SYSTEM_PROMPT_M4,
        prompt=prompt,
        label=label,
        temperature=0.15,   # very focused, minimal creativity
        max_tokens=16000,   # must be >= M1 output
        model="claude-opus-4-6",
    )""",
    "M4: main call → call_claude opus")
ok += 1 if r else 0; fail += 0 if r else 1

# Retry call_gemini → call_claude
r = patch(f,
    """        text2, meta2 = await call_gemini(
            system=SYSTEM_PROMPT_M4,
            prompt=prompt + f\"\"\"\n\nDŮLEŽITÉ: Tvá předchozí odpověď měla pouze {len(html)} znaků, zatímco draft má {len(draft_html)} znaků.\nTo je příliš málo — pravděpodobně jsi vynechal celé sekce. Zachovej VŠECHNY povinné sekce a tabulky.\nMůžeš zkrátit redundance, ale nemaž celé bloky.\n\"\"\",
            label=f\"{label}_retry\",
            temperature=0.2,
            max_tokens=16000,
        )""",
    """        text2, meta2 = await call_claude(
            system=SYSTEM_PROMPT_M4,
            prompt=prompt + f\"\"\"\n\nDŮLEŽITÉ: Tvá předchozí odpověď měla pouze {len(html)} znaků, zatímco draft má {len(draft_html)} znaků.\nTo je příliš málo — pravděpodobně jsi vynechal celé sekce. Zachovej VŠECHNY povinné sekce a tabulky.\nMůžeš zkrátit redundance, ale nemaž celé bloky.\n\"\"\",
            label=f\"{label}_retry\",
            temperature=0.2,
            max_tokens=16000,
            model="claude-opus-4-6",
        )""",
    "M4: retry call → call_claude opus")
ok += 1 if r else 0; fail += 0 if r else 1

# ═══════════════════════════════════════════════
# 5. LLM_ENGINE — add model + cost params to call_gemini
# ═══════════════════════════════════════════════
print("\n=== LLM_ENGINE call_gemini model param ===")
f = f"{BASE}/llm_engine.py"

# Read the file to find call_gemini signature
with open(f, 'r') as fh:
    content = fh.read()

# Find and update call_gemini function signature
# The function needs model=, cost_input=, cost_output= parameters
old_sig = """async def call_gemini(
    system: str,
    prompt: str,
    label: str = "gemini",
    temperature: float = 0.1,
    max_tokens: int = 8192,
    retries: int = 4,"""

if old_sig in content:
    new_sig = """async def call_gemini(
    system: str,
    prompt: str,
    label: str = "gemini",
    temperature: float = 0.1,
    max_tokens: int = 8192,
    retries: int = 4,
    model: str = None,
    cost_input: float = None,
    cost_output: float = None,"""
    content = content.replace(old_sig, new_sig)
    
    # Now update inside the function to use the model param
    # Find where GEMINI_MODEL is used in generate_content
    content = content.replace(
        '            model=GEMINI_MODEL,\n',
        '            model=model or GEMINI_MODEL,\n',
        1  # first occurrence only (in generate_content call)
    )
    
    # Update cost calculation to use passed costs or defaults
    content = content.replace(
        '            cost = (in_tok * GEMINI_COST_INPUT) + (out_tok * GEMINI_COST_OUTPUT)',
        '            cost = (in_tok * (cost_input or GEMINI_COST_INPUT)) + (out_tok * (cost_output or GEMINI_COST_OUTPUT))'
    )
    
    # Update model in meta dict
    content = content.replace(
        '                "provider": "gemini", "model": GEMINI_MODEL,',
        '                "provider": "gemini", "model": model or GEMINI_MODEL,'
    )
    
    # Update fallback meta
    content = content.replace(
        '        meta["original_model"] = GEMINI_MODEL',
        '        meta["original_model"] = model or GEMINI_MODEL'
    )
    
    with open(f, 'w') as fh:
        fh.write(content)
    print(f"  OK: llm_engine: call_gemini model/cost params added")
    ok += 1
else:
    print(f"  FAIL: llm_engine: call_gemini signature not found")
    fail += 1

# Also need to update the second model= in the retry call within call_gemini
with open(f, 'r') as fh:
    content = fh.read()

# The second model=GEMINI_MODEL is in the retry generate_content call
count = content.count('model=model or GEMINI_MODEL,')
if count < 2:
    # Find the retry body with GEMINI_MODEL
    old_retry = '                model=GEMINI_MODEL,'
    if old_retry in content:
        content = content.replace(old_retry, '                model=model or GEMINI_MODEL,')
        with open(f, 'w') as fh:
            fh.write(content)
        print(f"  OK: llm_engine: retry call model param updated")
        ok += 1
    else:
        print(f"  SKIP: llm_engine: retry model already updated or not found")
else:
    print(f"  SKIP: llm_engine: retry model already updated ({count} occurrences)")

print(f"\n{'='*50}")
print(f"DONE: {ok} OK, {fail} FAIL")
