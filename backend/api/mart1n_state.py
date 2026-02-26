"""
AIshield.cz — MART1N State Machine
Deterministic question flow controller for the Uršula chatbot.

The state machine decides WHICH question to ask next based on answered keys.
The LLM only FORMULATES the question naturally and EXTRACTS answers.
This reduces prompt size from ~15K tokens to ~1.2K tokens per request.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from backend.api.questionnaire import QUESTIONNAIRE_SECTIONS

logger = logging.getLogger(__name__)

# ── Pre-compute ordered question list with branching ──

@dataclass
class QuestionNode:
    """A single question or followup field in the questionnaire."""
    key: str
    text: str
    qtype: str  # text, yes_no_unknown, single_select, multi_select, select, conditional_fields
    options: list[str] = field(default_factory=list)
    help_text: str = ""
    risk_hint: str = ""
    ai_act_article: str = ""
    section_id: str = ""
    section_title: str = ""
    # Branching
    is_followup: bool = False
    parent_key: str = ""           # key of the parent question
    trigger_condition: str = ""     # "yes", "no", "unknown", specific option text, "any", ""
    is_info: bool = False           # display-only (no answer needed)


def _build_question_graph() -> list[QuestionNode]:
    """
    Build a flat ordered list of all questions including followups.
    Followups are placed right after their parent question.
    """
    nodes: list[QuestionNode] = []

    for section in QUESTIONNAIRE_SECTIONS:
        sid = section["id"]
        stitle = section["title"]

        for q in section["questions"]:
            # Main question
            main_node = QuestionNode(
                key=q["key"],
                text=q["text"],
                qtype=q["type"],
                options=q.get("options", []),
                help_text=q.get("help_text", ""),
                risk_hint=q.get("risk_hint", ""),
                ai_act_article=q.get("ai_act_article") or "",
                section_id=sid,
                section_title=stitle,
            )
            nodes.append(main_node)

            # Followup fields (triggered on yes / specific answer)
            if q.get("followup"):
                fu = q["followup"]
                condition = fu.get("condition", "yes")
                for f_field in fu.get("fields", []):
                    is_info = f_field.get("type") == "info"
                    fu_node = QuestionNode(
                        key=f_field.get("key", ""),
                        text=f_field.get("text", "") or f_field.get("label", ""),
                        qtype=f_field.get("type", "text"),
                        options=f_field.get("options", []),
                        help_text=f_field.get("help_text", ""),
                        section_id=sid,
                        section_title=stitle,
                        is_followup=True,
                        parent_key=q["key"],
                        trigger_condition=condition,
                        is_info=is_info,
                    )
                    nodes.append(fu_node)

            # Followup_no fields (triggered on "no")
            if q.get("followup_no"):
                fu_no = q["followup_no"]
                for f_field in fu_no.get("fields", []):
                    is_info = f_field.get("type") == "info"
                    fu_node = QuestionNode(
                        key=f_field.get("key", ""),
                        text=f_field.get("text", "") or f_field.get("label", ""),
                        qtype=f_field.get("type", "text"),
                        options=f_field.get("options", []),
                        help_text=f_field.get("help_text", ""),
                        section_id=sid,
                        section_title=stitle,
                        is_followup=True,
                        parent_key=q["key"],
                        trigger_condition="no",
                        is_info=is_info,
                    )
                    nodes.append(fu_node)

    return nodes


# Module-level graph — built once at import
_QUESTION_GRAPH: list[QuestionNode] = _build_question_graph()

# All answerable keys (excluding info nodes)
ALL_ANSWERABLE_KEYS: set[str] = {
    n.key for n in _QUESTION_GRAPH if n.key and not n.is_info
}

# Total main questions (for progress calculation denominator)
_MAIN_QUESTION_COUNT = sum(1 for n in _QUESTION_GRAPH if not n.is_followup)
_TOTAL_ANSWERABLE = len(ALL_ANSWERABLE_KEYS)


@dataclass
class NextAction:
    """What the chatbot should do next."""
    action: str  # "ask_question" | "show_info" | "complete"
    node: QuestionNode | None = None
    section_id: str = ""
    section_title: str = ""
    progress: int = 0
    # For "ask_question": what Claude should formulate
    question_text: str = ""
    question_type: str = ""
    question_options: list[str] = field(default_factory=list)
    question_key: str = ""
    help_text: str = ""
    risk_hint: str = ""
    ai_act_article: str = ""
    is_followup: bool = False
    parent_key: str = ""


def _should_trigger_followup(node: QuestionNode, answered: dict[str, str]) -> bool:
    """
    Check if a followup node should be triggered based on the parent's answer.
    
    Args:
        node: The followup QuestionNode
        answered: Dict of question_key → answer value
    
    Returns:
        True if this followup should be asked/shown.
    """
    parent_answer = answered.get(node.parent_key, "").lower().strip()
    
    if not parent_answer:
        return False  # Parent not answered yet — skip followup
    
    condition = node.trigger_condition.lower().strip()
    
    # "any" means always show if parent was answered at all
    if condition == "any":
        return True
    
    # "yes" / "no" / "unknown" — direct match
    if condition in ("yes", "no", "unknown"):
        return parent_answer == condition
    
    # Specific option text (e.g. "Jiné", "Implementujeme sami...")
    # Check if the parent's answer contains the condition text
    if condition in parent_answer.lower():
        return True
    
    # For multi_select answers stored as comma-separated or list-like
    if condition and condition in parent_answer:
        return True
    
    return False


def get_next_action(answered: dict[str, str]) -> NextAction:
    """
    Determine the next action based on currently answered questions.
    
    Args:
        answered: Dict of question_key → answer value (non-"unknown" answers)
    
    Returns:
        NextAction describing what to do next.
    """
    answered_keys = set(answered.keys())
    answered_count = len(answered_keys & ALL_ANSWERABLE_KEYS)
    
    # Calculate progress: based on main questions + active followups
    # Simple: answered / total_answerable, capped at 95 (closing gets 100)
    progress = min(95, round((answered_count / max(1, _TOTAL_ANSWERABLE)) * 100))
    
    for node in _QUESTION_GRAPH:
        # Skip info-only nodes (will be handled as part of ask_question context)
        if node.is_info:
            continue
        
        # Skip already answered
        if node.key in answered_keys:
            continue
        
        # For followups: check if they should trigger
        if node.is_followup:
            if not _should_trigger_followup(node, answered):
                continue  # Skip — condition not met
        
        # For main questions: no additional check needed
        # This is the next unanswered question!
        
        # Collect any info nodes that come right after this question
        # (they're display-only context the LLM should show)
        
        return NextAction(
            action="ask_question",
            node=node,
            section_id=node.section_id,
            section_title=node.section_title,
            progress=progress,
            question_text=node.text,
            question_type=node.qtype,
            question_options=node.options,
            question_key=node.key,
            help_text=node.help_text,
            risk_hint=node.risk_hint,
            ai_act_article=node.ai_act_article,
            is_followup=node.is_followup,
            parent_key=node.parent_key,
        )
    
    # All questions answered (or skipped) → complete
    return NextAction(
        action="complete",
        progress=100,
    )


def get_info_for_answer(question_key: str, answer: str) -> list[QuestionNode]:
    """
    After a question is answered, return any info nodes that should be
    displayed to the user (warnings, confirmations, etc.).
    
    These are followup nodes with type="info" that are triggered by the answer.
    """
    info_nodes: list[QuestionNode] = []
    answered_mock = {question_key: answer}
    
    for node in _QUESTION_GRAPH:
        if not node.is_info:
            continue
        if node.parent_key != question_key:
            continue
        if _should_trigger_followup(node, answered_mock):
            info_nodes.append(node)
    
    return info_nodes


def get_section_progress(answered_keys: set[str]) -> list[dict]:
    """
    Get per-section progress for display.
    Returns list of {id, title, answered, total, complete}.
    """
    sections = []
    for section in QUESTIONNAIRE_SECTIONS:
        section_keys = {q["key"] for q in section["questions"]}
        answered = len(section_keys & answered_keys)
        total = len(section_keys)
        sections.append({
            "id": section["id"],
            "title": section["title"],
            "answered": answered,
            "total": total,
            "complete": answered >= total,
        })
    return sections


def get_question_context_for_prompt(next_action: NextAction) -> str:
    """
    Build a minimal question context block for the LLM prompt.
    ~200 tokens max.
    """
    if next_action.action != "ask_question":
        return ""
    
    lines = [
        "<current_question>",
        f"section: {next_action.section_title}",
        f"key: {next_action.question_key}",
        f"text: {next_action.question_text}",
        f"type: {next_action.question_type}",
    ]
    
    if next_action.question_options:
        lines.append(f"options: {', '.join(next_action.question_options)}")
    
    if next_action.help_text:
        # Truncate to save tokens
        lines.append(f"help: {next_action.help_text[:200]}")
    
    if next_action.risk_hint and next_action.risk_hint != "none":
        lines.append(f"risk: {next_action.risk_hint}")
    
    if next_action.ai_act_article:
        lines.append(f"ai_act: {next_action.ai_act_article}")
    
    if next_action.is_followup:
        lines.append(f"followup_of: {next_action.parent_key}")
    
    lines.append("</current_question>")
    return "\n".join(lines)
