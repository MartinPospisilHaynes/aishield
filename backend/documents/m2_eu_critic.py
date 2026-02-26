"""
AIshield.cz — Modul 2: EU INSPECTOR CRITIC (Claude Sonnet 4)

Kontroluje draft dokumentu z pohledu EU inspektora AI Act.
Chain-of-thought reasoning, citace konkrétních článků, structured JSON output.

Vstup:  draft_html (str) + company_context (str) + doc_key (str)
Výstup: (critique_dict, metadata)

Model: Claude Sonnet 4 — nejlepší pro analytické, kritické myšlení.
"""

import json
import logging
from typing import Tuple

from backend.documents.llm_engine import call_claude, parse_json

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT — EU AI Act Inspector Persona
# ══════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT_M2 = """Jsi přísný inspektor EU AI Act — pracuješ pro evropský dozorový úřad
pro umělou inteligenci. Tvým úkolem je KRITICKY přezkoumat compliance dokumentaci
českých firem a identifikovat VŠECHNY nedostatky, chyby a mezery.

TVOJE ROLE:
- Jsi expert na Nařízení (EU) 2024/1689 (AI Act) a znáš KAŽDÝ článek zpaměti.
- Kontroluješ dokumentaci jako bys prováděl regulatorní audit.
- Jsi PŘÍSNÝ ale SPRAVEDLIVÝ — uznáváš kvalitní práci, ale nenecháš projít nic nesprávného.
- Myslíš jako právník — KAŽDÝ tvůj nález musí být podložen konkrétním článkem AI Act.

TVŮJ MYŠLENKOVÝ PROCES:
V klíči "myslenkovy_proces" STRUČNĚ (3-5 vět) zapiš hlavní závěr analýzy.
Neplýtvej slovy — soustřeď se na konkrétní strukturované nálezy.

KRITÉRIA HODNOCENÍ:
1. PRÁVNÍ PŘESNOST — jsou citace AI Act správné? Správné čísla článků, odstavců?
2. ÚPLNOST — pokrývá dokument VŠECHNY relevantní povinnosti?
3. PERSONALIZACE — je dokument skutečně specifický pro firmu, nebo je generický?
4. PRAKTIČNOST — jsou doporučení realizovatelná?
5. ROZLIŠENÍ ROLÍ — správně rozlišuje poskytovatele vs. nasazovatele?
6. AISHIELD vs. KLIENT — správně rozlišuje co je dodáno v Kitu vs. co musí klient?
7. ČASOVÉ LHŮTY — neuvádí neoprávněné lhůty? Zákonné deadliny správně?
8. ZAKÁZANÉ FRÁZE — neobsahuje klišé, obecné fráze, emoji?
9. PŘÍKLADY — má KAŽDÉ doporučení konkrétní příklad z praxe?
10. TABULKY A STRUKTURA — je dokument dobře strukturovaný pro tisk?

PRÁVNÍ FAKTA — KONTROLUJ PŘESNĚ:
- AI Act platnost: 1. 8. 2024
- Zakázané praktiky + AI literacy: od 2. 2. 2025
- GPAI: od 2. 8. 2025
- Plná účinnost: 2. 8. 2026
- High-risk Příloha I: 2. 8. 2027
- Pokuty: 35M/7% (čl. 99/3), 15M/3% (čl. 99/4)
- Incidenty: 15 dní (čl. 73)
- Logy: 6 měsíců (čl. 19/1)
- FRIA: čl. 27
- AI gramotnost: čl. 4

VÝSTUPNÍ FORMÁT:
Odpověz VÝHRADNĚ platným JSON objektem. Začni { a skonči }.
Žádný markdown, žádný text před/za JSON.

Struktura:
{
  "myslenkovy_proces": "Stručný závěr analýzy — max 3-5 vět. Co je hlavní problém, co je OK.",

  "celkove_hodnoceni": "vynikající|dobré|průměrné|nedostatečné|kriticky_nedostatečné",

  "skore": 7,

  "nalezy": [
    {
      "zavaznost": "kritické|důležité|menší|poznámka",
      "oblast": "název oblasti (např. 'Právní přesnost', 'Chybějící obsah')",
      "popis": "Přesný popis problému",
      "doporuceni": "Konkrétní doporučení jak opravit",
      "reference_ai_act": "čl. XX odst. Y AI Act (pokud relevantní)"
    }
  ],

  "silne_stranky": [
    "Konkrétní silná stránka dokumentu #1",
    "Konkrétní silná stránka dokumentu #2"
  ],

  "chybejici_obsah": [
    "Konkrétní obsah, který v dokumentu CHYBÍ a MĚLO by tam být"
  ],

  "celkove_doporuceni": "Souhrnné doporučení pro zlepšení dokumentu — 2-3 věty."
}

PRAVIDLA:
- Skóre 1-10: 10=perfektní, 7-9=dobré, 4-6=průměrné, 1-3=nedostatečné
- KAŽDÝ nález MUSÍ mít referenci na AI Act pokud existuje
- Najdi VŠECHNY relevantní nálezy. Pokud je dokument kvalitní, klidně uveď 0-2 nálezy. NEVYMÝŠLEJ problémy jen pro počet — fabricované nálezy zhoršují finální dokument.
- Najdi silné stránky — buď spravedlivý
- Používej jednoduché uvozovky pro HTML atributy v JSON stringách
"""


# ══════════════════════════════════════════════════════════════════════
# DOCUMENT-SPECIFIC FOCUS AREAS
# ══════════════════════════════════════════════════════════════════════

DOCUMENT_FOCUS = {
    "compliance_report": """
SPECIFICKÉ KONTROLY PRO COMPLIANCE REPORT:
- Obsahuje executive summary s přehledem všech dokumentů v Kitu?
- Je riziková analýza detailní pro KAŽDÝ systém, nebo generická?
- Jsou citovány správné články pro správné systémy?
- Je roadmap rozdělen na "Zajištěno Kitem" vs. "Akce klienta"?
- Obsahuje tabulku nalezených systémů s kompletními daty?
- Má metodologii analýzy (web sken + dotazník)?
""",
    "action_plan": """
SPECIFICKÉ KONTROLY PRO AKČNÍ PLÁN:
- Jsou kroky logicky seřazeny (urgentní první)?
- Je AI gramotnost zmíněna jako urgentní (od 2.2.2025 UŽ PLATÍ)?
- Nejsou uvedeny neoprávněné časové lhůty (žádné "do 30 dní")?
- Má checklistovou tabulku na konci?
- Rozlišuje "dodáno v Kitu" vs. "akce klienta" u každého kroku?
""",
    "ai_register": """
SPECIFICKÉ KONTROLY PRO REGISTR AI:
- Čl. 49 + Příloha VIII správně citovány?
- Jsou VŠECHNY systémy z kontextu zahrnuty (sken + dotazník)?
- Má detailní karty pro KAŽDÝ systém?
- Obsahuje pokyny pro údržbu (živý dokument)?
- Zmiňuje EU databázi high-risk systémů (čl. 71)?
""",
    "training_outline": """
SPECIFICKÉ KONTROLY PRO PLÁN ŠKOLENÍ:
- Čl. 4 AI Act: AI gramotnost od 2.2.2025 správně?
- Zmiňuje PowerPointovou prezentaci z Compliance Kitu?
- Rozlišuje cílové skupiny (vedení, IT, běžní uživatelé)?
- Má příklady automation bias pro odvětví firmy?
- NEOBSAHUJE zmínky o testech/certifikacích/kvízech?
""",
    "chatbot_notices": """
SPECIFICKÉ KONTROLY PRO TEXTY OZNÁMENÍ:
- Čl. 50 správně aplikován na konkrétní systémy?
- Jsou texty oznámení KONKRÉTNÍ (ne generické)?
- Rozlišuje povinná vs. doporučená oznámení?
- Zmiňuje transparenční stránku z Compliance Kitu?
- Jsou příklady nasazení (web, chatbot, email)?
""",
    "ai_policy": """
SPECIFICKÉ KONTROLY PRO INTERNÍ AI POLITIKU:
- Formální formát interní směrnice?
- Pokrývá zakázané praktiky (čl. 5)?
- Definuje schvalovací proces pro nové AI systémy?
- Má sekci o odpovědnostech?
- Má sankce za porušení?
- Podpisový blok na konci?
""",
    "incident_response_plan": """
SPECIFICKÉ KONTROLY PRO PLÁN ŘÍZENÍ INCIDENTŮ:
- Čl. 73: 15denní lhůta správně uvedena?
- Definice závažného incidentu přesná?
- 3-stupňová eskalace (L1/L2/L3)?
- Příklady incidentů SPECIFICKÉ pro odvětví firmy?
- Šablona dokumentace incidentu?
- Uchovávání důkazů (6 měsíců, čl. 19)?
""",
    "dpia_template": """
SPECIFICKÉ KONTROLY PRO DPIA/FRIA:
- Kombinuje AI Act čl. 27 (FRIA) s GDPR čl. 35 (DPIA)?
- Posouzení pro KAŽDÝ systém firmy?
- Identifikuje dotčené skupiny osob?
- Má tabulku rizik s pravděpodobností/závažností?
- Navrhuje konkrétní mitigační opatření?
""",
    "vendor_checklist": """
SPECIFICKÉ KONTROLY PRO DODAVATELSKÝ CHECKLIST:
- Čl. 25-26 AI Act správně?
- Hodnotí KAŽDÉHO detekovaného dodavatele?
- Obsahuje due diligence otázky?
- Vzorový email dodavateli?
- Smluvní požadavky (DPA, SLA)?
""",
    "monitoring_plan": """
SPECIFICKÉ KONTROLY PRO MONITORING PLÁN:
- Čl. 12 + čl. 19 správně?
- KPI metriky MĚŘITELNÉ a KONKRÉTNÍ?
- Frekvence dle rizikového profilu?
- Praktický příklad monitoring aktivity?
- Reporting šablona?
""",
    "transparency_human_oversight": """
SPECIFICKÉ KONTROLY PRO TRANSPARENTNOST A LIDSKÝ DOHLED:
- Čl. 13, 14, 50 správně aplikovány?
- Kill switch popsán pro každý systém?
- Human override procedury?
- Čtvrtletní kontrolní formulář?
- Archivační povinnosti (čl. 18: provoz + 10 let)?
""",
    "transparency_page": """
SPECIFICKÉ KONTROLY PRO TRANSPARENČNÍ STRÁNKU (HTML):
- Čl. 50 správně aplikován na VŠECHNY AI systémy firmy?
- Obsahuje JSON-LD strukturovaná data (WebPage, FAQPage, Organization)?
- E-E-A-T signály přítomny (autor, kvalifikace, zdroje)?
- Open Graph a Twitter Card meta tagy?
- Přístupnost: WCAG kompatibilní, sémantické HTML5?
- Je text srozumitelný pro laika (zákazník/návštěvník webu)?
- Obsahuje FAQ sekci s reálnými otázkami?
- Kontaktní údaje pro dotazy k AI?
- Odkaz na AI Act (Nařízení EU 2024/1689)?
- Je HTML standalone — klient ho může vložit na web bez úprav?
""",
    "training_presentation": """
SPECIFICKÉ KONTROLY PRO ŠKOLÍCÍ PREZENTACI:
- Čl. 4 AI Act (AI gramotnost) správně vysvětlen?
- Pokrývá VŠECHNY cílové skupiny (vedení, IT, běžní uživatelé)?
- Obsahuje konkrétní příklady z odvětví firmy?
- Automation bias a rizika AI — reálné příklady?
- Zakázané praktiky (čl. 5) srozumitelně vysvětleny?
- GDPR vs AI Act rozlišení?
- Praktické guidelines pro bezpečné používání AI?
- NEOBSAHUJE testy, kvízy ani certifikace?
- Má agenda/osnovu prezentace?
- Je rozsah adekvátní (cca 13-15 slidů)?
""",
}


# ══════════════════════════════════════════════════════════════════════
# REVIEW FUNCTION — hlavní vstupní bod modulu
# ══════════════════════════════════════════════════════════════════════

async def review_eu(
    draft_html: str,
    company_context: str,
    doc_key: str,
) -> Tuple[dict, dict]:
    """
    Přezkoumá draft dokumentu z pohledu EU inspektora.

    Args:
        draft_html: HTML koncept dokumentu z Modulu 1
        company_context: kontext firmy (pro ověření personalizace)
        doc_key: klíč dokumentu

    Returns:
        (critique_dict, metadata)
    """
    doc_focus = DOCUMENT_FOCUS.get(doc_key, "")
    doc_names = {
        "compliance_report": "Compliance Report",
        "action_plan": "Akční plán",
        "ai_register": "Registr AI systémů",
        "training_outline": "Plán školení",
        "chatbot_notices": "Texty oznámení",
        "ai_policy": "Interní AI politika",
        "incident_response_plan": "Plán řízení incidentů",
        "dpia_template": "DPIA/FRIA",
        "vendor_checklist": "Dodavatelský checklist",
        "monitoring_plan": "Monitoring plán",
        "transparency_human_oversight": "Transparentnost a lidský dohled",
        "transparency_page": "Transparenční stránka (HTML)",
        "training_presentation": "Školící prezentace (PPTX obsah)",
    }
    doc_name = doc_names.get(doc_key, doc_key)

    prompt = f"""PŘEZKOUMEJ NÁSLEDUJÍCÍ DOKUMENT jako EU AI Act inspektor.

══ KONTEXT FIRMY ══
{company_context}

══ KONTROLOVANÝ DOKUMENT: {doc_name} ══

{draft_html}

══ SPECIFICKÉ KONTROLNÍ BODY PRO TENTO TYP DOKUMENTU ══
{doc_focus}

══ INSTRUKCE ══
1. Stručně shrň hlavní závěr v "myslenkovy_proces" (3-5 vět).
2. Identifikuj VŠECHNY nedostatky — právní chyby, chybějící obsah, generický text.
3. Oceň silné stránky — buď spravedlivý.
4. Výstup POUZE jako JSON dle specifikace v system promptu.
"""

    label = f"M2_{doc_key}"
    logger.info(f"[M2 EU Critic] Kontroluji: {doc_name} ({len(draft_html)} znaků draftu)")

    text, meta = await call_claude(
        system=SYSTEM_PROMPT_M2,
        prompt=prompt,
        label=label,
        temperature=0.3,    # balanced: diverse findings + precision
        max_tokens=8000,
    )

    # Parse JSON
    critique = parse_json(text)
    if not critique:
        logger.warning(f"[M2 EU Critic] {doc_key}: JSON parsing selhal, fallback")
        critique = {
            "myslenkovy_proces": "Parsing selhal — používám raw text.",
            "celkove_hodnoceni": "neznámé",
            "skore": 5,
            "nalezy": [{"zavaznost": "poznámka", "oblast": "Parsing",
                        "popis": "Nebylo možné zpracovat strukturovaný výstup kritika.",
                        "doporuceni": "Zkontrolovat raw výstup.", "reference_ai_act": ""}],
            "silne_stranky": [],
            "chybejici_obsah": [],
            "celkove_doporuceni": text[:500] if text else "Výstup je prázdný.",
        }

    # Log chain-of-thought length
    cot = critique.get("myslenkovy_proces", "")
    findings_count = len(critique.get("nalezy", []))
    score = critique.get("skore", "?")
    logger.info(f"[M2 EU Critic] {doc_key}: skóre={score}, {findings_count} nálezů, "
                f"COT={len(cot)} znaků, hodnocení={critique.get('celkove_hodnoceni', '?')}")

    return critique, meta
