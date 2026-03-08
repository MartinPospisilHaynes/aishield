"""
AIshield.cz — M8 Amendment Generator

Generuje dodatek (amendment) k existující compliance dokumentaci.
Využívá M1 (draft) a M2 (EU inspector) pro dotčené sekce.

Dodatek obsahuje:
- Hlavičku s číslem, datem a názvem firmy
- Popis změny (co se změnilo v dotazníku)
- Nové rizikové hodnocení
- Aktualizované sekce dotčených dokumentů
- Instrukce pro klienta
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from backend.documents.llm_engine import call_claude
from backend.documents.m1_generator import DOCUMENT_NAMES

logger = logging.getLogger(__name__)


AMENDMENT_SYSTEM_PROMPT = """Jsi compliance expert na EU AI Act (Nařízení 2024/1689).
Generuješ DODATEK ke stávající compliance dokumentaci firmy.

PRAVIDLA:
- Piš výhradně česky, formálním právním stylem
- Odkazuj na konkrétní články AI Act
- Dodatek se VKLÁDÁ za původní dokument do pořadače
- NEGENERUJ celý dokument znovu — jen změněné/nové sekce
- Formát: čistý HTML s inline styly (pro WeasyPrint PDF)
"""


async def generate_amendment(
    company_context: str,
    impact_analysis: dict,
    affected_doc_keys: list[str],
    amendment_number: int,
    company_name: str,
) -> tuple[str, dict]:
    """
    Vygeneruje HTML dodatku.

    Args:
        company_context: aktualizovaný kontext firmy (po změně dotazníku)
        impact_analysis: výstup z M7 (impact_level, changes_detail, ...)
        affected_doc_keys: klíče dokumentů k aktualizaci
        amendment_number: pořadové číslo dodatku
        company_name: název firmy

    Returns:
        (amendment_html, metadata)
    """
    now = datetime.now(timezone.utc).strftime("%d. %m. %Y")

    # Sestavit přehled změn pro prompt
    changes_text = _format_changes_for_prompt(impact_analysis)
    affected_docs_text = "\n".join(
        f"  - {DOCUMENT_NAMES.get(k, k)}" for k in affected_doc_keys
    )

    prompt = f"""{AMENDMENT_SYSTEM_PROMPT}

═══════════════════════════════════════
ÚKOL: Vygeneruj Dodatek č. {amendment_number} ke Compliance Kitu
═══════════════════════════════════════

FIRMA: {company_name}
DATUM: {now}
ČÍSLO DODATKU: {amendment_number}

KONTEXT FIRMY (aktualizovaný):
{company_context}

ZMĚNY V DOTAZNÍKU:
{changes_text}

ÚROVEŇ DOPADU: {impact_analysis.get('impact_level', 'medium')}
ZMĚNA RIZIKA: {impact_analysis.get('risk_change', 'unchanged')}

DOTČENÉ DOKUMENTY:
{affected_docs_text}

═══════════════════════════════════════
STRUKTURA DODATKU (generuj jako HTML):
═══════════════════════════════════════

1. HLAVIČKA
   - „Dodatek č. {amendment_number} ke Compliance Kitu dle AI Act"
   - Firma, IČO, datum vydání
   - Důvod vydání (stručně)

2. PŘEHLED ZMĚN
   - Tabulka: co se změnilo, jaký dopad, nová riziková kategorie

3. AKTUALIZOVANÉ SEKCE
   Pro KAŽDÝ dotčený dokument vygeneruj sekci:
   - Název dokumentu (z DOTČENÉ DOKUMENTY)
   - Co se mění / co přibývá
   - Nový text příslušné sekce (ne celý dokument, jen změněná část)
   - Odkaz na článek AI Act

4. NOVÉ POVINNOSTI (pokud přibyly)
   - Co firma musí nově udělat
   - Termíny a doporučení

5. INSTRUKCE PRO KLIENTA
   - „Tento dodatek vložte do pořadače za dokument [XY]"
   - „Dodatek platí od [datum] a nahrazuje příslušné sekce v původních dokumentech"

DŮLEŽITÉ:
- Generuj POUZE ZMĚNĚNÉ sekce, ne celé dokumenty
- Vždy uveď číslo článku AI Act
- HTML s inline CSS pro WeasyPrint rendering
- Použij profesionální design — tmavá hlavička, přehledné tabulky
"""

    html, meta = await call_claude(
        system=AMENDMENT_SYSTEM_PROMPT,
        prompt=prompt,
        label="M8_amendment",
        temperature=0.3,
        max_tokens=8000,
    )

    # Validace výstupu
    if not html or len(html) < 200:
        logger.error("[M8] Amendment příliš krátký nebo prázdný")
        html = _generate_fallback_amendment(
            amendment_number, company_name, now, impact_analysis, affected_doc_keys
        )

    logger.info(
        f"[M8] Amendment č.{amendment_number} vygenerován: "
        f"{len(html)} chars, {len(affected_doc_keys)} dokumentů"
    )

    return html, meta


def _format_changes_for_prompt(impact_analysis: dict) -> str:
    """Formátuje změny do čitelného textu pro LLM prompt."""
    lines = []
    for detail in impact_analysis.get("changes_detail", []):
        if detail.get("impact") == "none":
            continue
        lines.append(
            f"- {detail['description']} "
            f"[dopad: {detail['impact']}, riziko: {detail.get('risk_hint', '?')}]"
        )
    return "\n".join(lines) if lines else "Žádné podstatné změny."


def _generate_fallback_amendment(
    amendment_number: int,
    company_name: str,
    date_str: str,
    impact_analysis: dict,
    affected_doc_keys: list[str],
) -> str:
    """Fallback HTML pokud LLM selže."""
    changes_rows = ""
    for detail in impact_analysis.get("changes_detail", []):
        if detail.get("impact") == "none":
            continue
        changes_rows += f"""
        <tr>
            <td style="padding:8px; border:1px solid #ddd;">{detail['key']}</td>
            <td style="padding:8px; border:1px solid #ddd;">{detail['description']}</td>
            <td style="padding:8px; border:1px solid #ddd;">{detail.get('impact', '?')}</td>
        </tr>"""

    docs_list = "".join(
        f"<li>{DOCUMENT_NAMES.get(k, k)}</li>" for k in affected_doc_keys
    )

    return f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 800px; margin: 0 auto;">
        <div style="background: #1a1a2e; color: white; padding: 30px; border-radius: 12px 12px 0 0;">
            <h1 style="margin: 0; font-size: 24px;">Dodatek č. {amendment_number}</h1>
            <p style="margin: 8px 0 0; opacity: 0.8;">ke Compliance Kitu dle AI Act (Nařízení EU 2024/1689)</p>
            <p style="margin: 8px 0 0; opacity: 0.7;">{company_name} — {date_str}</p>
        </div>
        <div style="padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 12px 12px;">
            <h2>Přehled změn</h2>
            <table style="width:100%; border-collapse:collapse; margin: 16px 0;">
                <tr style="background:#f0f0f0;">
                    <th style="padding:8px; text-align:left; border:1px solid #ddd;">Otázka</th>
                    <th style="padding:8px; text-align:left; border:1px solid #ddd;">Popis změny</th>
                    <th style="padding:8px; text-align:left; border:1px solid #ddd;">Dopad</th>
                </tr>
                {changes_rows}
            </table>
            <h2>Dotčené dokumenty</h2>
            <p>Následující dokumenty vyžadují aktualizaci:</p>
            <ul>{docs_list}</ul>
            <h2>Instrukce</h2>
            <p>Tento dodatek vložte do pořadače za příslušné dokumenty.
            Dodatek platí od {date_str} a doplňuje příslušné sekce v původních dokumentech.</p>
        </div>
    </div>
    """
