"""
AIshield.cz — Prompt Injection Guard
═══════════════════════════════════════
Centrální obrana proti prompt injection útokům.
Zahrnuje: input sanitization, output validation, rate limiting pokusů,
logging podezřelých vstupů.
"""

import logging
import os
import re
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# 1. INPUT SANITIZATION — detekce prompt injection pokusů
# ═══════════════════════════════════════════════════════════════

# Patterny indikující prompt injection pokus (case-insensitive)
INJECTION_PATTERNS: list[tuple[str, int, str]] = [
    # (regex_pattern, severity_score, description)

    # Přímé systémové instrukce
    (r"ignore\s+(all\s+)?previous\s+instructions?", 10, "ignore_instructions"),
    (r"ignore\s+(all\s+)?above", 8, "ignore_above"),
    (r"disregard\s+(all\s+)?previous", 10, "disregard_previous"),
    (r"forget\s+(everything|all|your)\s+(instructions?|rules?|training)", 10, "forget_instructions"),

    # Přepínání rolí / osobnosti
    (r"you\s+are\s+now\s+(?!an?\s+AI)", 8, "role_switch"),
    (r"act\s+as\s+(?:a\s+)?(?:hacker|admin|root|developer|jailbreak)", 9, "act_as_malicious"),
    (r"pretend\s+(?:you\s+are|to\s+be)\s+(?!an?\s+AI)", 7, "pretend_role"),
    (r"switch\s+(?:to|into)\s+(?:dev|developer|admin|god|root)\s*mode", 9, "switch_mode"),
    (r"enter\s+(?:dev|developer|admin|god|root|sudo)\s*mode", 9, "enter_mode"),
    (r"jailbreak", 9, "jailbreak"),
    (r"DAN\s*mode", 9, "dan_mode"),

    # Pokus o extrakci systémového promptu
    (r"(?:show|reveal|print|output|display|repeat|tell\s+me)\s+(?:your\s+)?(?:system\s+)?(?:prompt|instructions?|rules?|guidelines?)", 8, "extract_prompt"),
    (r"what\s+(?:are|is)\s+your\s+(?:system\s+)?(?:prompt|instructions?|rules?|initial\s+)", 7, "query_prompt"),
    (r"(?:ukaž|zobraz|vypiš|řekni|prozraď)\s+(?:mi\s+)?(?:svůj|své|svou)?\s*(?:systémov|instrukc|pravidl|prompt|pokyn)", 8, "extract_prompt_cz"),

    # Token/delimiter injection
    (r"<\|(?:im_start|im_end|system|endoftext|user|assistant)\|>", 10, "token_injection"),
    (r"\[INST\]|\[/INST\]", 9, "inst_injection"),
    (r"###\s*(?:Instruction|System|Human|Assistant)", 9, "markdown_injection"),
    (r"<\s*system\s*>|<\s*/\s*system\s*>", 9, "xml_system_tag"),
    (r"```system", 8, "codeblock_system"),

    # Pokus o SQL/code injection přes chat
    (r"(?:DROP\s+TABLE|DELETE\s+FROM|INSERT\s+INTO|UPDATE\s+.*SET)\s", 7, "sql_injection"),
    (r"(?:import\s+os|subprocess|eval\(|exec\(|__import__)", 7, "code_injection"),

    # Manipulace s bezpečnostními pravidly
    (r"(?:safety|content)\s+(?:filter|policy|guidelines?)\s+(?:off|disabled?|bypass|override)", 9, "safety_bypass"),
    (r"(?:bypass|circumvent|override|disable)\s+(?:your\s+)?(?:safety|security|content|filter|guard)", 9, "bypass_safety"),
    (r"(?:obejdi|vypni|deaktivuj|ignoruj)\s+(?:svá|své|svou)?\s*(?:bezpečnostn|pravidl|ochr|filtr)", 8, "bypass_safety_cz"),

    # Multi-turn manipulation
    (r"(?:from\s+now\s+on|starting\s+now|henceforth)\s+(?:you\s+)?(?:will|must|should|can)", 6, "temporal_manipulation"),
    (r"(?:od\s+teď|odteď|teď\s+budeš|nyní\s+budeš)\s+", 5, "temporal_manipulation_cz"),

    # Pokus o exfiltraci dat
    (r"(?:send|post|fetch|curl|wget|http)\s+(?:to|request)", 6, "data_exfiltration"),
    (r"(?:base64|encode|encrypt|hash)\s+(?:the|your|my|this)", 5, "encoding_attempt"),
]

# Kompilované regex patterny (lazy init)
_compiled_patterns: list[tuple[re.Pattern, int, str]] | None = None


def _get_compiled_patterns() -> list[tuple[re.Pattern, int, str]]:
    """Lazy-compile regex patterns."""
    global _compiled_patterns
    if _compiled_patterns is None:
        _compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), score, desc)
            for pattern, score, desc in INJECTION_PATTERNS
        ]
    return _compiled_patterns


# Skóre prahové hodnoty
INJECTION_WARN_THRESHOLD = 5    # Zalogovat jako podezřelé
INJECTION_BLOCK_THRESHOLD = 8   # Zablokovat zprávu


def scan_input(text: str) -> dict:
    """
    Analyzuje uživatelský vstup na prompt injection patterny.

    Returns:
        {
            "safe": bool,           # True = OK, False = zablokováno
            "score": int,           # Celkové skóre (vyšší = nebezpečnější)
            "matches": list[str],   # Názvy detekovaných patternů
            "action": str,          # "allow" | "warn" | "block"
        }
    """
    patterns = _get_compiled_patterns()
    total_score = 0
    matches = []

    for regex, score, desc in patterns:
        if regex.search(text):
            total_score += score
            matches.append(desc)

    if total_score >= INJECTION_BLOCK_THRESHOLD:
        action = "block"
        safe = False
    elif total_score >= INJECTION_WARN_THRESHOLD:
        action = "warn"
        safe = True  # Pustíme, ale zalogujeme
    else:
        action = "allow"
        safe = True

    return {
        "safe": safe,
        "score": total_score,
        "matches": matches,
        "action": action,
    }


# ═══════════════════════════════════════════════════════════════
# 2. OUTPUT VALIDATION — kontrola, že AI neodhalila systém
# ═══════════════════════════════════════════════════════════════

# Sensitive strings that should NEVER appear in public chat output
OUTPUT_BLOCKLIST_PATTERNS: list[tuple[str, str]] = [
    # API klíče a credentials
    (r"(?:api[_-]?key|secret[_-]?key|password|token)\s*[:=]\s*\S{10,}", "credential_leak"),
    (r"eyJ[A-Za-z0-9_-]{20,}", "jwt_token_leak"),
    (r"sk[-_](?:live|test)_[A-Za-z0-9]{20,}", "stripe_key_leak"),
    (r"AIza[A-Za-z0-9_-]{30,}", "google_api_key_leak"),

    # IP adresy interní infrastruktury
    (r"46\.28\.110\.102", "vps_ip_leak"),
    (r"rsxwqcrkttlfnqbjgpgc", "supabase_project_id_leak"),

    # Systémové cesty
    (r"/opt/aishield/", "server_path_leak"),
    (r"systemctl\s+(?:restart|stop|start)", "systemctl_command_leak"),

    # Hesla a tajné fráze
    (r"rododendron\d+", "dev_password_leak"),
    (r"Rc_\d{6,}", "admin_password_leak"),

    # Části systémového promptu
    (r"ZAKÁZANÁ TÉMATA", "system_prompt_leak"),
    (r"CO NESMÍŠ DĚLAT", "system_prompt_leak"),
    (r"BEZPEČNOSTNÍ PRAVIDLA PRO TEBE", "dev_prompt_leak"),
]

_compiled_output_patterns: list[tuple[re.Pattern, str]] | None = None


def _get_output_patterns() -> list[tuple[re.Pattern, str]]:
    global _compiled_output_patterns
    if _compiled_output_patterns is None:
        _compiled_output_patterns = [
            (re.compile(pattern, re.IGNORECASE), desc)
            for pattern, desc in OUTPUT_BLOCKLIST_PATTERNS
        ]
    return _compiled_output_patterns


def validate_output(text: str, is_dev_mode: bool = False) -> dict:
    """
    Zkontroluje výstup AI na únik citlivých dat.

    Returns:
        {
            "safe": bool,
            "redacted": str,        # Vyčištěný text (pokud unsafe)
            "violations": list[str],
        }
    """
    patterns = _get_output_patterns()
    violations = []

    for regex, desc in patterns:
        # V dev mode povolíme některé technické info (ale NE credentials)
        if is_dev_mode and desc in ("system_prompt_leak", "dev_prompt_leak", "server_path_leak"):
            continue
        if regex.search(text):
            violations.append(desc)

    if violations:
        # Redaktuj citlivé části
        redacted = text
        for regex, desc in patterns:
            if is_dev_mode and desc in ("system_prompt_leak", "dev_prompt_leak", "server_path_leak"):
                continue
            redacted = regex.sub("[REDACTED]", redacted)

        return {
            "safe": False,
            "redacted": redacted,
            "violations": violations,
        }

    return {"safe": True, "redacted": text, "violations": []}


# ═══════════════════════════════════════════════════════════════
# 3. BRUTE-FORCE PROTECTION — ochrana dev mode hesla
# ═══════════════════════════════════════════════════════════════

# {session_id: {"attempts": int, "locked_until": float}}
_password_attempts: dict[str, dict] = {}
MAX_PASSWORD_ATTEMPTS = 3
LOCKOUT_DURATION = 30 * 60  # 30 minut


def check_password_attempt(session_id: str) -> bool:
    """
    Zkontroluje, zda session může zkusit heslo.
    Returns True pokud může, False pokud je zamknutý.
    """
    info = _password_attempts.get(session_id)
    if not info:
        return True

    # Zkontroluj lockout
    locked_until = info.get("locked_until", 0)
    if locked_until > time.time():
        return False

    # Lockout vypršel — reset
    if locked_until > 0 and locked_until <= time.time():
        del _password_attempts[session_id]
        return True

    return info.get("attempts", 0) < MAX_PASSWORD_ATTEMPTS


def record_failed_attempt(session_id: str) -> int:
    """
    Zaznamenaj neúspěšný pokus o heslo.
    Returns počet zbývajících pokusů.
    """
    if session_id not in _password_attempts:
        _password_attempts[session_id] = {"attempts": 0, "locked_until": 0}

    _password_attempts[session_id]["attempts"] += 1
    attempts = _password_attempts[session_id]["attempts"]

    if attempts >= MAX_PASSWORD_ATTEMPTS:
        _password_attempts[session_id]["locked_until"] = time.time() + LOCKOUT_DURATION
        logger.warning(f"[PromptGuard] Session {session_id[:8]}... LOCKED OUT after {attempts} failed password attempts")
        return 0

    return MAX_PASSWORD_ATTEMPTS - attempts


def record_successful_attempt(session_id: str):
    """Reset počítadla po úspěšném přihlášení."""
    if session_id in _password_attempts:
        del _password_attempts[session_id]


# ═══════════════════════════════════════════════════════════════
# 4. LOGGING — záznam podezřelých vstupů
# ═══════════════════════════════════════════════════════════════

def log_injection_attempt(
    session_id: str,
    user_input: str,
    scan_result: dict,
    page_url: str | None = None,
):
    """Zaloguje podezřelý vstup do Supabase tabulky a logu."""
    logger.warning(
        f"[PromptGuard] Injection detected: session={session_id[:8]}... "
        f"score={scan_result['score']} matches={scan_result['matches']} "
        f"action={scan_result['action']}"
    )

    # Zalogovat do Supabase (best-effort)
    try:
        from supabase import create_client
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if url and key:
            sb = create_client(url, key)
            sb.table("analytics_events").insert({
                "event_type": "prompt_injection_attempt",
                "page_url": page_url or "/chat",
                "metadata": {
                    "session_id": session_id[:8] + "...",
                    "score": scan_result["score"],
                    "matches": scan_result["matches"],
                    "action": scan_result["action"],
                    "input_preview": user_input[:100] + ("..." if len(user_input) > 100 else ""),
                },
                "created_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
    except Exception as e:
        logger.error(f"[PromptGuard] Log to DB failed: {e}")


# ═══════════════════════════════════════════════════════════════
# 5. INDIRECT INJECTION DEFENSE — pro scanner pipeline
# ═══════════════════════════════════════════════════════════════

def sanitize_scanned_content(html_content: str, max_length: int = 50000) -> str:
    """
    Vyčistí obsah stažený ze skenované stránky před předáním AI modelu.
    Odstraní potenciální prompt injection skrytý v HTML.
    """
    # Ořízni na max délku
    sanitized = html_content[:max_length]

    # Odstraň HTML komentáře (mohou obsahovat skryté instrukce)
    sanitized = re.sub(r"<!--[\s\S]*?-->", "", sanitized)

    # Odstraň hidden elementy s potenciálními instrukcemi
    sanitized = re.sub(
        r'<[^>]+(?:style\s*=\s*["\'][^"\']*(?:display\s*:\s*none|visibility\s*:\s*hidden|opacity\s*:\s*0|font-size\s*:\s*0)[^"\']*["\'])[^>]*>[\s\S]*?</[^>]+>',
        "",
        sanitized,
        flags=re.IGNORECASE,
    )

    # Odstraň data-* atributy s podezřele dlouhým obsahem (> 200 znaků)
    sanitized = re.sub(r'data-[a-z-]+="[^"]{200,}"', '', sanitized)

    # Odstraň base64 bloky (mohou skrývat instrukce)
    sanitized = re.sub(r'(?:data:[^;]+;base64,)[A-Za-z0-9+/=]{500,}', '[BASE64_REMOVED]', sanitized)

    # Odstraň noscript prank injections
    sanitized = re.sub(r'<noscript>[\s\S]*?</noscript>', '', sanitized, flags=re.IGNORECASE)

    return sanitized


# ═══════════════════════════════════════════════════════════════
# 6. CONVERSATION LIMITS
# ═══════════════════════════════════════════════════════════════

MAX_CONVERSATION_LENGTH = 30  # Max zpráv v konverzaci
MAX_REPEATED_SIMILAR = 3     # Max opakování podobného dotazu


def check_conversation_limits(messages: list) -> dict:
    """
    Zkontroluje limity konverzace.

    Returns:
        {
            "ok": bool,
            "reason": str | None,
        }
    """
    if len(messages) > MAX_CONVERSATION_LENGTH:
        return {
            "ok": False,
            "reason": "Konverzace je příliš dlouhá. Začněte prosím nový chat obnovením stránky.",
        }

    # Detekce opakovaných podobných zpráv (brute-force prompt injection)
    if len(messages) >= MAX_REPEATED_SIMILAR * 2:
        user_msgs = [m.content if hasattr(m, 'content') else m.get('content', '')
                     for m in messages if (m.role if hasattr(m, 'role') else m.get('role', '')) == 'user']
        if len(user_msgs) >= MAX_REPEATED_SIMILAR:
            last_msgs = user_msgs[-MAX_REPEATED_SIMILAR:]
            # Kontrola, zda jsou poslední zprávy podobné (>80% shoda)
            if len(set(last_msgs)) == 1:
                return {
                    "ok": False,
                    "reason": "Opakujete stejnou zprávu. Zkuste prosím jiný dotaz.",
                }

    return {"ok": True, "reason": None}
