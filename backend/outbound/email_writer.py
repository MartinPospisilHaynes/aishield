"""
AIshield.cz — AI Email Writer v3 (SIMPLIFIED)
Gemini 2.5 Flash POUZE:
  1. Skloňuje jméno kontaktní osoby do 5. pádu (vocative_name)
  2. To je vše — šablona v email_templates.py řeší zbytek.

Předmět emailu je PEVNÝ (hardcoded).
"""

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
)

# PEVNÝ předmět emailu
FIXED_SUBJECT = "Oznámení o hrozícím porušení pravidel na vašem webu dle nařízení EU"


@dataclass
class GeneratedEmail:
    """Vygenerovaný email."""
    subject: str
    body_html: str
    variant_id: str = "template_v5_gemini"
    model: str = GEMINI_MODEL
    tokens_used: int = 0


def _build_vocative_prompt(contact_person: str, legal_form: str = "") -> str:
    """Prompt pro Gemini — POUZE skloňování jména do 5. pádu."""
    return f"""Jsi expert na českou gramatiku. Tvůj JEDINÝ úkol je skloňovat jméno do 5. pádu (vokativu).

VSTUP:
Jméno: {contact_person}
Právní forma firmy: {legal_form or 'neznámá'}

PRAVIDLA:
1. Pokud je jméno prázdné nebo "neznámé", vrať prázdný string.
2. Pokud je to muž: "pane [příjmení v 5. pádu]" (např. "pane Nováku", "pane Haynesi")
3. Pokud je to žena: "paní [příjmení v 5. pádu]" (např. "paní Nováková" — ženská příjmení se v 5. pádu nemění)
4. Pokud je právní forma s.r.o. nebo a.s., oslovuj formálně.
5. Pokud si nejsi jistý pohlavím, použij neutrální tvar.

FORMÁT ODPOVĚDI — POUZE JSON:
{{"vocative_name": "pane Nováku"}}

Pokud jméno neznáš nebo je prázdné:
{{"vocative_name": ""}}
"""


def _get_vocative_name_sync(contact_person: str) -> str:
    """
    Český 5. pád (vokativ) — čistě v Pythonu, bez API.
    Spolehlivé, okamžité, bez nákladů.
    """
    if not contact_person or contact_person.lower() in ("neznámé", "neznámé jméno", ""):
        return ""

    parts = contact_person.strip().split()
    if len(parts) < 2:
        return ""

    surname = parts[-1]

    # Detekce pohlaví — ženská příjmení končí na -ová, -á, -í
    if surname.endswith("ová") or surname.endswith("á") or surname.endswith("í"):
        # Žena — 5. pád se u ženských příjmení nemění
        return f"paní {surname}"

    # Muž — pravidla pro 5. pád mužských příjmení
    # Cizí příjmení (neskloňuje se pravidelně)
    foreign_endings = ("es", "is", "us", "os", "as", "ey", "ay", "ow", "er", "on", "an",
                       "in", "en", "th", "gh", "sh", "ch")

    # Příjmení končící na souhlásku
    if surname.endswith("ek"):
        # Novák→Nováku, ale Novotný→Novotný
        vocative = surname[:-2] + "ku"
    elif surname.endswith("ec"):
        vocative = surname[:-2] + "če"
    elif surname.endswith("ík") or surname.endswith("ýk"):
        vocative = surname[:-1] + "ku"
    elif surname.endswith("ák"):
        vocative = surname[:-1] + "ku"
    elif surname.endswith("ok"):
        vocative = surname[:-1] + "ku"
    elif surname.endswith("ý"):
        vocative = surname  # Přídavná jména se nemění (Novotný)
    elif surname.endswith("ský") or surname.endswith("cký"):
        vocative = surname  # Přídavná jména
    elif surname.endswith("ič") or surname.endswith("ič"):
        vocative = surname + "i"
    elif surname.endswith("eš"):
        vocative = surname + "i"
    elif surname.endswith("č") or surname.endswith("ž") or surname.endswith("š") or surname.endswith("ř"):
        vocative = surname + "i"
    elif any(surname.lower().endswith(e) for e in foreign_endings):
        # Cizí příjmení — přidáme -i (Haynes→Haynesi, Miller→Millere)
        if surname.endswith("er"):
            vocative = surname + "e"
        elif surname.endswith("s") or surname.endswith("z"):
            vocative = surname + "i"
        else:
            vocative = surname + "e"
    elif surname.endswith("a"):
        vocative = surname[:-1] + "o"
    elif surname.endswith("k"):
        vocative = surname + "u"
    elif surname.endswith("l") or surname.endswith("r") or surname.endswith("n"):
        vocative = surname + "e"
    elif surname.endswith("d") or surname.endswith("t"):
        vocative = surname + "e"
    elif surname.endswith("b") or surname.endswith("p") or surname.endswith("v") or surname.endswith("m"):
        vocative = surname + "e"
    else:
        vocative = surname + "e"

    return f"pane {vocative}"


async def write_email(
    company_name: str,
    company_url: str,
    contact_person: str = "",
    contact_role: str = "",
    legal_form: str = "",
    findings: list[dict] | None = None,
    screenshot_url: str = "",
    scan_id: str = "",
    extra_context: str = "",
    to_email: str = "",
    api_key: str | None = None,
) -> GeneratedEmail:
    """
    Template-driven email v5.
    Gemini POUZE skloní jméno → šablona sestaví kompletní HTML.
    """
    from backend.outbound.email_templates import (
        build_hybrid_email,
        FindingRow,
    )

    key = api_key or os.environ.get("GEMINI_API_KEY", "")
    findings_dicts = findings or []

    # 1. Skloňování jména — čistě v Pythonu (spolehlivé, okamžité)
    vocative_name = _get_vocative_name_sync(contact_person)

    logger.info(
        f"Email v5: company={company_name}, url={company_url}, "
        f"contact={contact_person}, vocative={vocative_name}, "
        f"findings={len(findings_dicts)}"
    )

    # 2. Převedeme findings na FindingRow
    finding_rows = []
    for f in findings_dicts:
        finding_rows.append(FindingRow(
            name=f.get("name", "Neznámý systém"),
            category=f.get("category", "ai_tool"),
            risk_level=f.get("risk_level", "limited"),
            ai_act_article=f.get("ai_act_article", "čl. 50"),
            action_required=f.get("action_required", ""),
            description=f.get("description", ""),
        ))

    # 3. Šablona sestaví kompletní HTML
    body_html = build_hybrid_email(
        vocative_name=vocative_name,
        company_url=company_url,
        company_name=company_name,
        findings=finding_rows,
        screenshot_url=screenshot_url,
        scan_id=scan_id,
        to_email=to_email,
    )

    return GeneratedEmail(
        subject=FIXED_SUBJECT,
        body_html=body_html,
        tokens_used=0,
    )


async def generate_outbound_email(
    company_url: str,
    html: str,
    findings: list[dict],
    scan_id: str = "",
    screenshot_url: str = "",
    to_email: str = "",
    ico: str | None = None,
    api_key: str | None = None,
) -> GeneratedEmail:
    """
    End-to-end: Vytáhne info o firmě + skloní jméno + šablona sestaví email.
    Hlavní funkce volaná z pipeline.
    """
    from backend.outbound.company_info import get_company_info

    # 1. Zjistíme info o firmě
    info = await get_company_info(url=company_url, html=html, ico=ico)

    logger.info(
        f"Company info: {info.company_name}, contact={info.contact_person}, "
        f"role={info.contact_role}, form={info.legal_form}"
    )

    # 2. Gemini skloní jméno + šablona sestaví HTML
    email = await write_email(
        company_name=info.company_name,
        company_url=company_url,
        contact_person=info.contact_person,
        contact_role=info.contact_role,
        legal_form=info.legal_form,
        findings=findings,
        screenshot_url=screenshot_url,
        scan_id=scan_id,
        to_email=to_email,
        api_key=api_key,
    )

    return email
