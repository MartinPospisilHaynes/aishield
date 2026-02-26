"""
AIshield.cz — LLM Content Generator for Documents (v4)

Generuje personalizované odborné texty pomocí 11 paralelních LLM volání —
každá sekce má vlastní specializovaný prompt pro maximální kvalitu.

Architektura:
  - 11 paralelních volání (asyncio.gather) — každá sekce fokusovaný prompt
  - Pydantic validace každého výstupu
  - Retry s error feedbackem (2 pokusy Gemini, 2 pokusy Claude fallback)
  - Graceful degradation: pokud sekce selže, ostatní pokračují
  - Průměrný cost: ~$0.20 per generace (11× Gemini 3.1 Pro)
"""

import asyncio
import json
import logging
import os
import re
from typing import Optional, Dict, List, Tuple

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ── Knowledge Base integration ──
try:
    from backend.documents.knowledge_base import (
        build_kb_context_for_llm,
        generate_vendor_assessment_kb,
        generate_chatbot_notices_kb,
        generate_monitoring_kpis_kb,
        generate_risk_analysis_kb,
        generate_transparency_oversight_kb,
        all_tools_known,
        KB_VERSION_DATE,
        get_vendor_footer,
    )
    KB_AVAILABLE = True
except ImportError:
    KB_AVAILABLE = False
    logger.warning("[LLM Content] Knowledge Base not available — pure LLM mode")


# ══════════════════════════════════════════════════════════════════════
# Per-section Pydantic modely — každá sekce má vlastní model
# ══════════════════════════════════════════════════════════════════════

class _SectionBase(BaseModel):
    myslenkovy_proces: str = ""  # Chain-of-thought (stripped from output)
    content: str = ""            # Main HTML content


class ExecutiveSummaryContent(_SectionBase): pass
class RiskAnalysisContent(_SectionBase): pass
class ComplianceRoadmapContent(_SectionBase): pass
class AIPolicyIntroContent(_SectionBase): pass
class DPIANarrativeContent(_SectionBase): pass
class IncidentGuidanceContent(_SectionBase): pass
class ChatbotNoticesContent(_SectionBase): pass
class AIRegisterIntroContent(_SectionBase): pass
class TrainingRecsContent(_SectionBase): pass
class VendorAssessmentContent(_SectionBase): pass
class MonitoringRecsContent(_SectionBase): pass
class TransparencyOversightContent(_SectionBase): pass


ALL_EXPECTED_KEYS = [
    "executive_summary", "risk_analysis", "compliance_roadmap", "ai_policy_intro",
    "dpia_narrative", "incident_guidance", "chatbot_notices_custom", "ai_register_intro",
    "training_recommendations", "vendor_assessment", "monitoring_recommendations",
]


# ══════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT — Expert AI Act Compliance Writer
# ══════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """Jsi přední český expert na EU AI Act (Nařízení (EU) 2024/1689)
a píšeš profesionální compliance dokumentaci pro české firmy.

STYL:
- Formální, autoritativní, srozumitelná čeština vhodná pro tisk a vazbu.
- Konkrétní a relevantní pro danou firmu — žádné obecné floskule.
- Cituj konkrétní články AI Act kde je to relevantní.
- Používej odbornou terminologii konzistentně.
- Vždy zmiň roli firmy: poskytovatel (provider, čl. 3(2)) nebo nasazovatel (deployer, čl. 3(4)).

KLÍČOVÉ ROZLIŠENÍ — CO DODÁVÁ AISHIELD vs. CO MUSÍ KLIENT:
Firma AIshield.cz dodává klientovi AI Act Compliance Kit — sadu dokumentů
a nástrojů pro dosažení souladu s AI Act. U každého doporučení a kroku
VŽDY jasně rozliš:
- Zajištěno v rámci Compliance Kitu — co klient UŽ DOSTAL od AIshield
  (tento dokument, registr, politiku, školení, transparenční stránku atd.)
- Vyžaduje akci klienta — co musí klient udělat interně SÁM, protože to
  závisí na jeho vnitřních procesech (např. jmenovat odpovědnou osobu,
  implementovat logging do vlastního systému, podepsat smlouvu s dodavatelem)
NIKDY nepiš klientovi vytvořte si dokument XYZ pokud tento dokument
je SOUČÁSTÍ Compliance Kitu — místo toho napiš Tento dokument je součástí
vašeho Compliance Kitu.

POVINNÉ:
- U KAŽDÉHO akčního bodu nebo doporučení VŽDY uveď KONKRÉTNÍ PŘÍKLAD v odrážkách,
  který laicky vysvětlí, co to v praxi znamená. Běžný podnikatel bez právního vzdělání
  musí z příkladu okamžitě pochopit, co konkrétně má udělat.
  Příklad špatně: „Zajistěte transparentnost dle čl. 50."
  Příklad dobře: „Zajistěte transparentnost dle čl. 50 — konkrétně:
    • Na webu přidejte viditelný text: ‚Tento chat je provozován umělou inteligencí.'
    • V patičce každé stránky s AI chatbotem umístěte odkaz na transparenční stránku.
    • Při zahájení konverzace s chatbotem zobrazte upozornění: ‚Komunikujete s AI asistentem.'"
- Kdykoli zmiňuješ dokument, který je SOUČÁSTÍ Compliance Kitu (prezentace, checklist,
  registr, plán atd.), VŽDY uveď: „tento dokument jste obdrželi jako součást Compliance Kitu
  od AIshield" — aby klient věděl, že to už MÁ a nemusí to vytvářet.

ZAKÁZÁNO:
- Klišé fráze typu V dnešní digitální době, Závěrem lze říci, je důležité si uvědomit.
- Obecné statistiky bez vztahu k firmě. Běž rovnou k věci.
- Emoji. Používej pouze text a HTML tagy.
- Konkrétní časové lhůty typu do 30 dní nebo do 2 měsíců — nedávej klientovi
  termíny pro jednotlivé kroky. Uveď pouze zákonné deadliny (2. 8. 2026 plná účinnost).
- Zmínky o testech, kvízech nebo certifikacích — AIshield je neposkytuje.

PRÁVNÍ FAKTA (použij přesně):
- AI Act vstoupil v platnost 1. 8. 2024.
- Zakázané praktiky (čl. 5) + AI literacy (čl. 4): od 2. 2. 2025.
- GPAI modely (čl. 51-56): od 2. 8. 2025.
- Plná účinnost pro většinu povinností: 2. 8. 2026.
- High-risk systémy dle Přílohy I: 2. 8. 2027.
- Pokuty: 35 mil. EUR / 7 % obratu za zakázané praktiky (čl. 99 odst. 3),
  15 mil. EUR / 3 % za ostatní porušení (čl. 99 odst. 4).
- Incidenty (čl. 73): nahlásit do 15 dnů obecně.
- Logging schopnosti: čl. 12. Uchovávání logů min. 6 měsíců: čl. 19 odst. 1.
- FRIA: čl. 27 (povinnost nasazovatelů u vybraných high-risk scénářů).
- Neposkytuj právní poradenství — jde o technickou pomůcku.

PŘÍSNÁ PRAVIDLA PRO VÝSTUP:
1. Odpověz VÝHRADNĚ platným JSON objektem.
2. Začni přímo znakem { a skonči znakem }. Žádné ```json bloky, žádný text před/za JSON.
3. Hodnoty v JSONu jsou HTML stringy: <p>, <ul><li>, <strong>.
4. Pro HTML atributy používej VÝHRADNĚ jednoduché uvozovky (např. <span class='highlight'>).
5. V textu používej české typografické uvozovky (\u201e \u201c) místo rovných.
6. Nepoužívej skutečné odřádkování uvnitř JSON hodnot — formátuj pouze HTML tagy.
"""


# ══════════════════════════════════════════════════════════════════════
# COMPANY CONTEXT BUILDER — sdílený kontext pro všechna volání
# ══════════════════════════════════════════════════════════════════════

def _build_company_context(data: dict) -> str:
    """Sestaví sdílený kontext firmy pro všechna LLM volání."""
    company = data.get("company_name", "Neznámá firma")
    industry = data.get("q_company_industry", "neznámé")
    size = data.get("q_company_size", "neznámá")
    overall_risk = data.get("overall_risk", "minimal")
    risk_breakdown = data.get("risk_breakdown", {"high": 0, "limited": 0, "minimal": 0})
    oversight = data.get("oversight_person", {})
    data_prot = data.get("data_protection", {})
    training = data.get("training", {})
    incident = data.get("incident", {})

    findings_lines = []
    for f in data.get("findings", []):
        findings_lines.append(
            f"  - {f.get('name', '?')}: kategorie={f.get('category', '?')}, "
            f"riziko={f.get('risk_level', '?')}, článek={f.get('ai_act_article', '?')}, "
            f"akce={f.get('action_required', '?')}"
        )
    findings_summary = "\n".join(findings_lines) if findings_lines else "  Žádné AI systémy nebyly detekovány na webu."

    declared_lines = []
    for d in data.get("ai_systems_declared", []):
        declared_lines.append(f"  - {d.get('tool_name', d.get('key', '?'))}")
    declared_summary = "\n".join(declared_lines) if declared_lines else "  Žádné AI systémy nebyly deklarovány v dotazníku."

    recs_lines = []
    for r in data.get("recommendations", []):
        recs_lines.append(f"  - [{r.get('risk_level','')}] {r.get('tool_name','')}: {r.get('recommendation','')}")
    recs_summary = "\n".join(recs_lines) if recs_lines else "  Žádná specifická doporučení."

    base_context = f"""KONTEXT FIRMY:
Firma: {company}
Odvětví: {industry}
Velikost: {size}
Celkové riziko: {overall_risk}
Rizikový rozpad: {risk_breakdown.get('high',0)} vysoké, {risk_breakdown.get('limited',0)} omezené, {risk_breakdown.get('minimal',0)} minimální

NALEZENÉ AI SYSTÉMY (web sken):
{findings_summary}

DEKLAROVANÉ AI SYSTÉMY (dotazník):
{declared_summary}

DOPORUČENÍ Z ANALÝZY:
{recs_summary}

ODPOVĚDNÁ OSOBA ZA AI: {oversight.get('name', 'nejmenována')} ({oversight.get('role', 'neurčena')})
ZPRACOVÁVÁ OSOBNÍ ÚDAJE PŘES AI: {'ANO' if data_prot.get('processes_personal_data') else 'NE'}
MÁ ŠKOLENÍ AI: {'ANO' if training.get('has_training') else 'NE'}
MÁ INCIDENT PLÁN: {'ANO' if incident.get('has_plan') else 'NE'}"""

    # Inject Knowledge Base facts into context (if available)
    if KB_AVAILABLE:
        try:
            kb_block = build_kb_context_for_llm(
                data.get("ai_systems_declared", []),
                data.get("findings", [])
            )
            if kb_block:
                base_context = base_context + "\n" + kb_block
                logger.info(f"[LLM Context] Injected {len(kb_block)} chars of KB facts")
        except Exception as e:
            logger.warning(f"[LLM Context] KB injection failed: {e}")

    return base_context


# ══════════════════════════════════════════════════════════════════════
# 11 SECTION-SPECIFIC PROMPT BUILDERS
# Každý prompt je specializovaný — LLM se soustředí na jedno téma
# ══════════════════════════════════════════════════════════════════════

_COT_INSTRUCTION = """Prvním klíčem je "myslenkovy_proces" — sem zapiš svůj podrobný rozbor
relevantní pro tuto konkrétní sekci. Tento text nebude v dokumentu — slouží ti k lepšímu přemýšlení.
Druhým klíčem je "content" — HTML string s textem sekce."""


def _prompt_executive_summary(ctx: str) -> str:
    return f"""{ctx}

NAPIŠ EXECUTIVE SUMMARY pro compliance report této firmy.
{_COT_INSTRUCTION}

Požadavky na "content" (400-600 slov, 3-4 odstavce <p>):
- Začni shrnutím provedené analýzy: web sken + dotazník, nalezené AI systémy, rizikový profil
- Uveď roli firmy dle AI Act: nasazovatel (deployer) dle čl. 3 odst. 4
- Jasně vysvětli CO FIRMA ZÍSKALA v rámci Compliance Kitu od AIshield:
  kompletní dokumentaci (tento report, registr AI systémů, interní AI politiku,
  akční plán, DPIA, plán řízení incidentů, dodavatelský checklist, monitoring plán,
  školící prezentaci, transparenční stránku, texty oznámení)
- Zdůrazni pozitivní kroky firmy (školení, oversight osoba atd.)
- Uveď účinnost AI Act od 2. 8. 2026 a relevantní sankce dle čl. 99
- Uzavři stručným přehledem dalších kroků, které vyžadují akci klienta (nikoliv dokumenty)
- U KAŽDÉHO doporučení uveď konkrétní příklad co to znamená v praxi
  (např. „jmenovat odpovědnou osobu za AI" → „Určete konkrétního zaměstnance,
  který bude zodpovídat za AI systémy — typicky IT manažer nebo compliance officer.")

{{{{"myslenkovy_proces": "...", "content": "<p>...</p>"}}}}"""


def _prompt_risk_analysis(ctx: str) -> str:
    return f"""{ctx}

NAPIŠ DETAILNÍ ANALÝZU RIZIK nalezených AI systémů.
{_COT_INSTRUCTION}

Požadavky na "content" (400-600 slov, 3-4 odstavce <p> + volitelně <ul><li>):
- Pro KAŽDÝ nalezený systém vysvětli PROČ má dané riziko dle AI Act
- Rozliš: vysoké riziko (čl. 6-15, Příloha III), omezené riziko (čl. 50),
  minimální riziko (dobrovolné best practices)
- Vysvětli roli nasazovatele vs. poskytovatele a co z toho plyne
- U high-risk systémů zmiň povinnosti: QMS (čl. 17), logging (čl. 12),
  FRIA (čl. 27), lidský dohled (čl. 14), transparentnost (čl. 13)
- U každé povinnosti uveď zda je ZAJIŠTĚNA Compliance Kitem nebo vyžaduje akci klienta
- Zmiň konkrétní rizika specifická pro odvětví firmy
- NEUVÁDEJ časové lhůty pro nápravná opatření
- U KAŽDÉHO rizika uveď konkrétní příklad co to znamená v praxi pro TUTO firmu
  (např. u chatbotu: „Váš chatbot na webu musí zobrazit upozornění: Komunikujete s AI.")
- U každé povinnosti firmy uveď PŘÍKLAD jak ji splnit v praxi

{{{{"myslenkovy_proces": "...", "content": "<p>...</p>"}}}}"""


def _prompt_compliance_roadmap(ctx: str) -> str:
    return f"""{ctx}

NAPIŠ PŘEHLED KROKŮ K DOSAŽENÍ SOULADU pro tuto firmu.
{_COT_INSTRUCTION}

Požadavky na "content" (400-500 slov, strukturované jako <h3> + <ul><li>):
- Rozděl kroky do dvou kategorií:
  <h3>Již zajištěno v rámci Compliance Kitu</h3> — seznam dokumentů a nástrojů
  které klient OBDRŽEL od AIshield (registr AI systémů, interní AI politika,
  DPIA posouzení, plán řízení incidentů, školící prezentace, akční plán,
  transparenční stránka, dodavatelský checklist, monitoring plán, texty oznámení)
  <h3>Kroky vyžadující akci klienta</h3> — co musí klient udělat SÁM:
  jmenovat odpovědnou osobu za AI, implementovat interní procesy,
  proškolit zaměstnance (prezentace je dodána, ale školení musí provést),
  nasadit transparenční stránku na svůj web, uzavřít DPA s dodavateli AI,
  implementovat logging a monitoring do svých systémů
- U každého kroku klienta stručně vysvětli PROČ to nemůže udělat AIshield za něj
- NEPOUŽÍVEJ konkrétní časové lhůty (žádné do 30 dní, do 2 měsíců atd.)
- Plná účinnost AI Act od 2. 8. 2026
- U KAŽDÉHO kroku vyžadujícího akci klienta uveď PRAKTICKÝ PŘÍKLAD
  co to konkrétně znamená (krok za krokem, jako návod pro laika)
- U školení ZMIň: „K provedení školení využijte PowerPointovou prezentaci,
  kterou jste obdrželi jako součást tohoto Compliance Kitu."
- U transparenční stránky ZMIň: „HTML kód transparenční stránky jste obdrželi
  v Compliance Kitu — stačí ho nasadit na váš web."

{{{{"myslenkovy_proces": "...", "content": "<h3>...</h3><ul><li>...</li></ul>"}}}}"""


def _prompt_ai_policy_intro(ctx: str) -> str:
    return f"""{ctx}

NAPIŠ ÚVOD K INTERNÍ AI POLITICE (preambuli) pro tuto firmu.
{_COT_INSTRUCTION}

Požadavky na "content" (400-600 slov, 3-4 odstavce <p>):
- Formální preambule — proč firma přijímá interní AI politiku
- Uveď že tento dokument je součástí AI Act Compliance Kitu dodaného AIshield.cz
- Odkaž na konkrétní nalezené AI systémy a rizika
- Zmiň čl. 4 AI Act (AI gramotnost — povinnost od 2. 2. 2025)
- Zmiň čl. 5 (zakázané praktiky — co firma NESMÍ dělat)
- Zahrň doporučení specifická pro odvětví firmy
- Definuj rozsah politiky: na koho se vztahuje, jaké systémy pokrývá
- Napiš jako formální dokument vhodný pro podpis vedením
- Vysvětli že tuto politiku klient převzal jako hotový dokument,
  který si může přizpůsobit interním podmínkám a podepsat
- PŘÍKLADY: uveď 2-3 konkrétní situace z praxe firmy, kde se AI politika uplatní
  (např. „Zaměstnanec chce použít ChatGPT k přepsání smlouvy — musí dodržet pravidlo XY z této politiky.")

{{{{"myslenkovy_proces": "...", "content": "<p>...</p>"}}}}"""


def _prompt_dpia_narrative(ctx: str) -> str:
    return f"""{ctx}

NAPIŠ POSOUZENÍ VLIVU NA ZÁKLADNÍ PRÁVA (FRIA/DPIA) pro tuto firmu.
{_COT_INSTRUCTION}

Požadavky na "content" (500-700 slov, 4-5 odstavců <p> + volitelně <ul><li>):
- Kombinuj AI Act čl. 27 (FRIA) s GDPR čl. 35 (DPIA)
- Identifikuj dotčené skupiny na základě odvětví firmy
- Pro každý nalezený systém zhodnoť dopad na: právo na soukromí,
  nediskriminaci, vysvětlení rozhodnutí (čl. 86 AI Act), lidský přezkum
- Navrhni konkrétní technická a organizační opatření pro zmírnění rizik
- U každého opatření rozliš:
  <strong>Dodáno v Compliance Kitu:</strong> tento DPIA dokument, monitoring plán,
  doporučení k implementaci
  <strong>Vyžaduje akci klienta:</strong> implementace technických opatření
  do vlastních systémů, nastavení přístupových práv, smluvní ošetření s dodavateli
- Zahrň sekci o zpracování osobních údajů přes AI
- U KAŽDÉHO opatření uveď PŘÍKLAD jak ho implementovat v praxi
  (např. „Nastavte v ChatGPT Enterprise vypnutí trénování na vašich datech — Settings → Data Controls → Turn off.")

{{{{"myslenkovy_proces": "...", "content": "<p>...</p>"}}}}"""


def _prompt_incident_guidance(ctx: str) -> str:
    return f"""{ctx}

NAPIŠ NÁVOD PRO ŘÍZENÍ INCIDENTŮ S AI pro tuto firmu.
{_COT_INSTRUCTION}

Požadavky na "content" (400-500 slov, 3-4 odstavce + <ul><li>):
- Čl. 73 AI Act: závažný incident nahlásit do 15 dnů dozorčímu orgánu
- Definice závažného incidentu: smrt, vážná poškození zdraví, narušení
  základních práv, škody na majetku/životním prostředí
- Uveď 3-4 konkrétní příklady incidentů relevantních PRO ODVĚTVÍ této firmy
- Navrhni eskalační scénáře: L1 (operátor), L2 (odpovědná osoba za AI), L3 (vedení)
- Zmiň povinnost dokumentace: co zaznamenat (čas, systém, dopad, opatření)
- Uchovávání důkazů a logů (čl. 12 + čl. 19 — min. 6 měsíců)
- Jasně uveď: tento plán je DODÁN v rámci Compliance Kitu, klient ho
  implementuje do svých vnitřních procesů a přizpůsobí své organizační struktuře
- U KAŽDÉHO kroku eskalačního scénáře uveď KONKRÉTNÍ PŘÍKLAD z praxe firmy
  (např. „Chatbot na webu odpověděl zákazníkovi nepravdivou informaci o ceně → L1 operátor
  okamžitě vypne chatbot, zaznamená incident, kontaktuje odpovědnou osobu za AI.")

{{{{"myslenkovy_proces": "...", "content": "<p>...</p><ul><li>...</li></ul>"}}}}"""


def _prompt_chatbot_notices(ctx: str) -> str:
    return f"""{ctx}

NAPIŠ DOPORUČENÍ K AI OZNÁMENÍM A TRANSPARENCI pro tuto firmu.
{_COT_INSTRUCTION}

Požadavky na "content" (400-500 slov, 3-4 odstavce + volitelně <ul><li>):
- Na základě KONKRÉTNÍCH nalezených systémů vysvětli:
  KTERÉ oznámení dle čl. 50 jsou POVINNÉ a které DOPORUČENÉ
- Čl. 50 odst. 1: chatboty/voiceboty — uživatel MUSÍ být informován
- Čl. 50 odst. 2: detekce emocí/biometrická kategorizace
- Čl. 50 odst. 4: AI-generovaný obsah (deep fakes, syntetický text) — označit
- Doporuč kde a jak oznámení nasadit: web banner, chatbot intro, e-mail footer
- Uveď že TEXTY těchto oznámení a transparenční stránka jsou SOUČÁSTÍ
  Compliance Kitu — klient je pouze nasadí na svůj web/systém
- Klient musí sám rozhodnout, KDE přesně oznámení umístí (závisí na jeho webu)
- Uveď KONKRÉTNÍ PŘÍKLADY textů oznámení, např.:
  • Pro chatbot: „Tento chat je provozován umělou inteligencí. Odpovědi mohou obsahovat nepřesnosti."
  • Pro web: „Na tomto webu používáme AI nástroje. Více informací na naší transparenční stránce."
  • Zmiň: „Texty oznámení i HTML kód transparenční stránky jste obdrželi v Compliance Kitu."

{{{{"myslenkovy_proces": "...", "content": "<p>...</p>"}}}}"""


def _prompt_ai_register_intro(ctx: str) -> str:
    return f"""{ctx}

NAPIŠ ÚVOD K REGISTRU AI SYSTÉMŮ pro tuto firmu.
{_COT_INSTRUCTION}

Požadavky na "content" (300-500 slov, 2-3 odstavce <p>):
- Vysvětli právní základ: čl. 49 AI Act + Příloha VIII
- Shrň co bylo nalezeno: kolik systémů web sken, kolik dotazník, rizikové úrovně
- Zdůrazni že tento registr je DODÁN v rámci Compliance Kitu jako HOTOVÝ dokument
  předvyplněný na základě skenu webu a dotazníku
- Registr je ŽIVÝ dokument — klient ho musí aktualizovat při každé změně
  (nasazení nového AI, vyřazení, změna verze, změna účelu)
- Doporuč revizi min. 1x za 6 měsíců
- Pro vysoce rizikové: registr MUSÍ obsahovat poskytovatele, účel, stav, datum
- Zmiň EU databázi (čl. 71) — povinnost registrace high-risk systémů
- Uveď PŘÍKLAD kdy klient musí registr aktualizovat:
  „Přidáte na web nový AI chatbot → do registru zapíšete: název, poskytovatele,
  účel použití, rizikovou kategorii, datum nasazení."

{{{{"myslenkovy_proces": "...", "content": "<p>...</p>"}}}}"""


def _prompt_training_recommendations(ctx: str) -> str:
    return f"""{ctx}

NAPIŠ DOPORUČENÍ PRO ŠKOLENÍ AI GRAMOTNOSTI pro tuto firmu.
{_COT_INSTRUCTION}

Požadavky na "content" (400-600 slov, 3-4 odstavce + volitelně <ul><li>):
- Čl. 4 AI Act: AI literacy povinná od 2. 2. 2025 pro VŠECHNY firmy používající AI
- Zdůrazni: školící PREZENTACE je SOUČÁSTÍ Compliance Kitu — klient ji obdržel
  jako hotový PowerPoint připravený k použití pro školení zaměstnanců
- Klient musí SÁM zajistit provedení školení (svolat zaměstnance, prezentovat)
  — AIshield nemůže školit zaměstnance klienta vzdáleně
- Zdůrazni automation bias — tendenci nekriticky přijímat výstupy AI
- Kritické myšlení a ověřování výstupů AI
- Přizpůsob odvětví firmy — jiné příklady pro různá odvětví
- Cílové skupiny: vedení, IT, běžní uživatelé — různá hloubka
- Zmíň postih za nesplnění (čl. 99 odst. 4)
- NEPIŠ o testech ani certifikacích — AIshield je neposkytuje
- VŽDY zmiň: „K provedení školení využijte PowerPointovou prezentaci
  ‚Školení AI gramotnosti', kterou jste obdrželi v Compliance Kitu.
  Prezentace je připravena k okamžitému použití — stačí ji promítnout zaměstnancům."
- Uveď KONKRÉTNÍ PŘÍKLADY automation bias z odvětví firmy
  (např. „Účetní spoléhá na AI návrh daňového přiznání bez kontroly → chyba v DPH.")

{{{{"myslenkovy_proces": "...", "content": "<p>...</p>"}}}}"""


def _prompt_vendor_assessment(ctx: str) -> str:
    return f"""{ctx}

NAPIŠ HODNOCENÍ DODAVATELŮ AI pro tuto firmu.
{_COT_INSTRUCTION}

Požadavky na "content" (400-600 slov, 3-4 odstavce + <ul><li>):
- Pro KAŽDÉHO detekovaného dodavatele/poskytovatele AI vysvětli specifické riziko
- Oblasti due diligence: transparenční dokumentace, opt-out trénování na datech,
  SLA podmínky, DPA (smlouva o zpracování dle GDPR), certifikace
- Čl. 25-26 AI Act: povinnosti nasazovatelů vůči poskytovatelům
- Dodavatelský CHECKLIST je SOUČÁSTÍ Compliance Kitu — klient ho obdržel
  jako hotový nástroj pro hodnocení dodavatelů
- Klient musí SÁM: kontaktovat dodavatele, vyjednat smlouvy, ověřit shodu —
  AIshield nemůže vstupovat do smluvních vztahů klienta s třetími stranami
- Doporuč konkrétní otázky pro due diligence: kde se data zpracovávají,
  trénuje se model na datech klienta, jaké certifikace dodavatel má
- Zmiň riziko vendor lock-in a exit strategie
- VŽDY zmiň: „K hodnocení dodavatelů využijte Dodavatelský checklist,
  který jste obdrželi v Compliance Kitu — obsahuje konkrétní otázky pro každého dodavatele."
- Uveď PŘÍKLAD dialogu s dodavatelem:
  „Napište poskytovateli chatbotu email: Prosíme o potvrzení, zda se naše konverzační data
  používají k trénování modelu. Potřebujeme to pro splnění EU AI Act."

{{{{"myslenkovy_proces": "...", "content": "<p>...</p><ul><li>...</li></ul>"}}}}"""


def _prompt_monitoring_recommendations(ctx: str) -> str:
    return f"""{ctx}

NAPIŠ DOPORUČENÍ PRO MONITORING AI SYSTÉMŮ pro tuto firmu.
{_COT_INSTRUCTION}

Požadavky na "content" (400-600 slov, 3-4 odstavce + volitelně <ul><li>):
- Čl. 12 AI Act: automatické logging schopnosti pro high-risk systémy
- Čl. 19 odst. 1: uchovávání logů min. 6 měsíců
- Monitoring PLÁN je SOUČÁSTÍ Compliance Kitu — klient ho obdržel jako hotový dokument
- Klient musí SÁM implementovat monitoring do svých systémů — AIshield nemůže
  přistupovat k interním systémům klienta
- Navrhni KPI metriky: přesnost AI výstupů, bias skóre, latence,
  počet eskalací na člověka, false positive/negative rate
- Doporuč frekvenci monitoringu podle rizikového profilu:
  high-risk = týdně, limited = měsíčně, minimal = kvartálně
- Kdo je zodpovědný za monitoring (odpovědná osoba za AI)
- Zmiň bezpečnostní audity a review výstupů AI
- VŽDY zmiň: „Monitoring plán jste obdrželi v Compliance Kitu.
  Implementujte ho do svých IT procesů — např. přidejte kontrolu AI výstupů
  do týdenního IT review meetingu."
- Uveď PŘÍKLAD KPI: „Jednou týdně zkontrolujte 10 náhodných odpovědí chatbotu —
  kolik z nich bylo fakticky správných? Pokud <80 %, eskalujte na dodavatele."

{{{{"myslenkovy_proces": "...", "content": "<p>...</p>"}}}}"""



def _prompt_transparency_oversight(ctx: str) -> str:
    return f"""{ctx}

NAPIŠ PERSONALIZOVANÉ DOPORUČENÍ PRO TRANSPARENTNOST A LIDSKÝ DOHLED pro tuto firmu.
{_COT_INSTRUCTION}

Požadavky na "content" (400-600 slov, 3-4 odstavce + <ul><li>):
- Čl. 13 AI Act: transparentnost vysoce rizikových AI systémů —
  technická dokumentace, návod k použití, srozumitelnost pro uživatele
- Čl. 14 AI Act: lidský dohled — kill switch, override, monitoring výstupů,
  kompetence dohledové osoby (AI literacy)
- Čl. 50 AI Act: POVINNOST informovat uživatele že komunikují s AI (chatbot),
  označit AI-generovaný obsah, upozornit na deep fakes
- Na základě KONKRÉTNÍCH AI systémů firmy uveď:
  KTERÉ systémy vyžadují oznámení dle čl. 50 a KTERÉ lidský dohled dle čl. 14
- Doporuč KONKRÉTNÍ opatření: kde umístit oznámení, kdo provádí dohled,
  jak často testovat kill switch, jak probíhá čtvrtletní kontrola
- Zmiň povinnost archivace záznamů o transparentnosti a dohledu
  po dobu provozu AI + 10 let (čl. 18 AI Act)
- Uveď: "Záznamový list pro čtvrtletní kontrolu transparentnosti a dohledu
  jste obdrželi v Compliance Kitu — vyplňujte ho pravidelně."
- KONKRÉTNÍ PŘÍKLADY pro firmu: "Chatbot na webu — přidejte úvodní zprávu
  'Komunikujete s AI.' Override: operátor může konverzaci převzít."

{{{{"myslenkovy_proces": "...", "content": "<p>...</p><ul><li>...</li></ul>"}}}}"""


# Registry: output_key → (PydanticModel, prompt_builder_function)
_SECTION_REGISTRY = {
    "executive_summary":         (ExecutiveSummaryContent, _prompt_executive_summary),
    "risk_analysis":             (RiskAnalysisContent,     _prompt_risk_analysis),
    "compliance_roadmap":        (ComplianceRoadmapContent, _prompt_compliance_roadmap),
    "ai_policy_intro":           (AIPolicyIntroContent,     _prompt_ai_policy_intro),
    "dpia_narrative":            (DPIANarrativeContent,     _prompt_dpia_narrative),
    "incident_guidance":         (IncidentGuidanceContent,  _prompt_incident_guidance),
    "chatbot_notices_custom":    (ChatbotNoticesContent,    _prompt_chatbot_notices),
    "ai_register_intro":         (AIRegisterIntroContent,   _prompt_ai_register_intro),
    "training_recommendations":  (TrainingRecsContent,      _prompt_training_recommendations),
    "vendor_assessment":         (VendorAssessmentContent,  _prompt_vendor_assessment),
    "monitoring_recommendations": (MonitoringRecsContent,    _prompt_monitoring_recommendations),
    "transparency_oversight":      (TransparencyOversightContent, _prompt_transparency_oversight),
}


# ══════════════════════════════════════════════════════════════════════
# ROBUST JSON PARSER (opravené backslash bugy)
# ══════════════════════════════════════════════════════════════════════


def _parse_llm_json(text: str, expected_keys: Optional[List[str]] = None) -> Optional[dict]:
    """
    Robustní parser JSON odpovědi z LLM.
    Zvládne: markdown bloky, unescaped newlines, trailing commas,
    control chars, BOM, extra text kolem JSON.
    """
    if not text:
        return None

    # Strip BOM
    text = text.lstrip("\ufeff")

    # Strip markdown code blocks
    stripped = text.strip()
    if stripped.startswith("```"):
        first_nl = stripped.find("\n")
        if first_nl > 0:
            stripped = stripped[first_nl + 1:]
        else:
            stripped = stripped[3:]
        if stripped.rstrip().endswith("```"):
            stripped = stripped.rstrip()[:-3]
        stripped = stripped.strip()
    else:
        stripped = text.strip()

    # Pokus 1: Přímý parse
    for candidate in [stripped, text]:
        try:
            result = json.loads(candidate)
            if isinstance(result, dict):
                logger.info("[LLM Content] JSON parsed (direct)")
                return result
        except (json.JSONDecodeError, ValueError):
            pass

    # Pokus 2: Extrahuj JSON objekt z textu (najdi balanced braces)
    json_str = _extract_json_object(stripped)
    if json_str:
        try:
            result = json.loads(json_str)
            if isinstance(result, dict):
                logger.info("[LLM Content] JSON parsed (extracted)")
                return result
        except (json.JSONDecodeError, ValueError):
            pass

    # Pokus 3: Oprav běžné problémy a zkus znovu
    if json_str:
        cleaned = _fix_json_string(json_str)
        try:
            result = json.loads(cleaned)
            if isinstance(result, dict):
                logger.info("[LLM Content] JSON parsed (cleaned)")
                return result
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"[LLM Content] JSON parse after cleaning failed: {e}")

    # Pokus 4: Zpracuj po klíčích pomocí regex
    keys_to_search = expected_keys or ALL_EXPECTED_KEYS
    result = _parse_json_by_keys(stripped, keys_to_search)
    if result:
        logger.info(f"[LLM Content] JSON parsed (regex, {len(result)} keys)")
        return result

    return None


def _extract_json_object(text: str) -> Optional[str]:
    """Najde první balanced {} blok v textu."""
    start = text.find("{")
    if start < 0:
        return None

    depth = 0
    in_string = False
    escape = False

    for i in range(start, len(text)):
        c = text[i]
        if escape:
            escape = False
            continue
        if c == "\\":
            if in_string:
                escape = True
            continue
        if c == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]

    # Fallback: vrátit od start do posledního }
    last_brace = text.rfind("}")
    if last_brace > start:
        return text[start:last_brace + 1]
    return None


def _fix_json_string(text: str) -> str:
    """Opraví běžné problémy v JSON stringu."""
    # Odstraň řídicí znaky (ale zachovej \n \r \t)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', ' ', text)

    # Odstraň trailing commas před } nebo ]
    text = re.sub(r',\s*([}\]])', r'\1', text)

    # Oprav unescaped newlines uvnitř JSON stringů
    result = []
    in_str = False
    esc = False
    for c in text:
        if esc:
            result.append(c)
            esc = False
            continue
        if c == '\\':
            esc = True
            result.append(c)
            continue
        if c == '"':
            in_str = not in_str
            result.append(c)
            continue
        if in_str and c == '\n':
            result.append('\\n')
            continue
        if in_str and c == '\r':
            result.append('\\r')
            continue
        if in_str and c == '\t':
            result.append('\\t')
            continue
        result.append(c)

    return ''.join(result)


def _parse_json_by_keys(text: str, keys: Optional[List[str]] = None) -> Optional[dict]:
    """
    Pokud standardní JSON parsing selže, extrahuj hodnoty pomocí regex.
    Hledá klíče "key_name": "value..." pattern.
    """
    if keys is None:
        keys = ALL_EXPECTED_KEYS

    result = {}
    for key in keys:
        pattern = rf'"{key}"\s*:\s*"((?:[^"\\]|\\.|"")*)"'
        match = re.search(pattern, text, re.DOTALL)
        if match:
            value = match.group(1)
            value = value.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
            result[key] = value

    if len(result) >= max(1, len(keys) // 2):
        return result
    return None


# ══════════════════════════════════════════════════════════════════════
# GEMINI STRUCTURED OUTPUT — google-genai SDK
# ══════════════════════════════════════════════════════════════════════

_GEMINI_DOC_MODEL = "gemini-3.1-pro-preview"
_GEMINI_COST_INPUT = 2.0 / 1_000_000   # $2 / 1M input tokens
_GEMINI_COST_OUTPUT = 12.0 / 1_000_000  # $12 / 1M output tokens



async def _call_gemini_structured(
    chunk_name: str,
    system: str,
    user_prompt: str,
    pydantic_model: type,
    temperature: float = 0.15,
    max_tokens: int = 8000,
) -> Tuple[dict, dict]:
    """
    Volá Gemini API s nativním structured output (response_schema).
    Používá google-genai SDK přímo — nikoliv REST API.

    Returns:
        (content_dict, metadata_dict)
    Raises:
        Exception pokud Gemini selže
    """
    from google import genai
    from google.genai import types
    from backend.config import get_settings

    settings = get_settings()
    api_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY není nastavený")

    client = genai.Client(api_key=api_key)

    response = await client.aio.models.generate_content(
        model=_GEMINI_DOC_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_schema=pydantic_model,
            temperature=temperature,
            max_output_tokens=max_tokens,
        ),
    )

    # Extract text and usage
    text = response.text or ""
    usage = response.usage_metadata
    input_tokens = getattr(usage, "prompt_token_count", 0) or 0
    output_tokens = getattr(usage, "candidates_token_count", 0) or 0
    cost = (input_tokens * _GEMINI_COST_INPUT) + (output_tokens * _GEMINI_COST_OUTPUT)

    logger.info(
        f"[LLM Content] {chunk_name} Gemini structured: "
        f"tokens={input_tokens}+{output_tokens}, cost=${cost:.4f}, "
        f"raw_len={len(text)}"
    )

    # Parse JSON (structured output guarantees valid JSON)
    content = json.loads(text)

    # Validate with Pydantic
    validated = pydantic_model(**content)
    result_dict = validated.dict() if hasattr(validated, "dict") else validated.model_dump()

    # Strip reasoning field (not used in documents)
    result_dict.pop("myslenkovy_proces", None)

    # Strip empty values
    result_dict = {k: v for k, v in result_dict.items() if v}

    metadata = {
        "provider": "gemini",
        "model": _GEMINI_DOC_MODEL,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost,
    }

    return result_dict, metadata


# ══════════════════════════════════════════════════════════════════════
# LLM CALL — Gemini structured output → Claude fallback
# ══════════════════════════════════════════════════════════════════════

async def _call_llm_chunk(
    chunk_name: str,
    user_prompt: str,
    expected_keys: List[str],
    pydantic_model: type,
) -> dict:
    """
    Zavolá LLM pro jeden chunk.
    Strategie: Gemini structured output (2 pokusy) → Claude fallback (2 pokusy).
    """
    # ── Pokus 1: Gemini s nativním structured output ──
    gemini_available = True
    try:
        from google import genai  # noqa: F401
    except ImportError:
        gemini_available = False
        logger.warning("[LLM Content] google-genai SDK není k dispozici, přeskakuji Gemini")

    if gemini_available:
        for attempt in range(4):
            try:
                content, meta = await _call_gemini_structured(
                    chunk_name=chunk_name,
                    system=SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    pydantic_model=pydantic_model,
                    temperature=0.15 if attempt == 0 else 0.1,
                    max_tokens=16000,
                )

                if content:
                    total_chars = sum(len(v) for v in content.values() if isinstance(v, str))
                    logger.info(
                        f"[LLM Content] {chunk_name}: {len(content)} sekcí, "
                        f"{total_chars} znaků (Gemini structured output)"
                    )

                    # Track usage in Supabase
                    try:
                        from backend.ai_engine.llm_client import _record_usage, LLMResult
                        await _record_usage("gemini", LLMResult(
                            text="", provider="gemini", model=meta["model"],
                            input_tokens=meta["input_tokens"],
                            output_tokens=meta["output_tokens"],
                            cost_usd=meta["cost_usd"],
                        ), caller="llm_content_structured")
                    except Exception:
                        pass

                    return content
                else:
                    logger.warning(
                        f"[LLM Content] {chunk_name} Gemini attempt {attempt+1}: "
                        f"prázdný výstup po validaci"
                    )
            except Exception as e:
                err_str = str(e)
                logger.warning(
                    f"[LLM Content] {chunk_name} Gemini attempt {attempt+1} error: {e}"
                )
                # Na 429 rate-limit počkáme podle retryDelay nebo exponential backoff
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    # Pokus extrahovat retryDelay z chybové zprávy
                    delay_match = re.search(r"retryDelay.*?(\d+\.?\d*)", err_str)
                    if delay_match:
                        wait = float(delay_match.group(1)) + 1.0
                    else:
                        wait = min(5 * (2 ** attempt), 30)  # 5, 10, 20, 30s
                    logger.info(f"[LLM Content] {chunk_name}: rate-limited, čekám {wait:.0f}s...")
                    await asyncio.sleep(wait)
                    continue  # Zkusit znovu

    # ── Pokus 2: Claude fallback přes llm_complete() ──
    logger.warning(f"[LLM Content] {chunk_name}: Gemini selhalo → Claude fallback")
    from backend.ai_engine.llm_client import llm_complete

    last_text = ""
    last_error = ""

    for attempt in range(2):
        try:
            if attempt == 0:
                prompt = user_prompt
            else:
                # Retry: pošli error feedback
                prompt = (
                    f"Tvá předchozí odpověď nebyla platný JSON. Vrať POUZE čistý JSON objekt "
                    f"s přesně těmito klíči: {', '.join(expected_keys)}.\n\n"
                    f"Chyba: {last_error}\n"
                    f"Začátek tvé předchozí odpovědi: {repr(last_text[:300])}\n\n"
                    f"Oprav a vrať platný JSON. Začni přímo znakem {{."
                )

            result = await llm_complete(
                system=SYSTEM_PROMPT,
                user=prompt,
                max_tokens=16000,
                temperature=0.15 if attempt == 0 else 0.1,
                prefer="claude",
                prefill="{",
            )

            logger.info(
                f"[LLM Content] {chunk_name} Claude attempt {attempt+1}: "
                f"provider={result.provider}, "
                f"tokens={result.input_tokens}+{result.output_tokens}, "
                f"cost=${result.cost_usd:.4f}"
            )

            text = result.text.strip()
            last_text = text

            logger.info(f"[LLM Content] {chunk_name} raw length: {len(text)} chars")

            content = _parse_llm_json(text, expected_keys)

            if content is None:
                last_error = "JSON parsing zcela selhal"
                logger.warning(f"[LLM Content] {chunk_name} Claude attempt {attempt+1}: parse failed")
                continue

            # Pydantic validace
            try:
                validated = pydantic_model(**content)
                validated_dict = validated.dict() if hasattr(validated, "dict") else validated.model_dump()
                validated_dict.pop("myslenkovy_proces", None)
                validated_dict = {k: v for k, v in validated_dict.items() if v}
                if validated_dict:
                    logger.info(
                        f"[LLM Content] {chunk_name}: {len(validated_dict)} sekcí, "
                        f"{sum(len(v) for v in validated_dict.values())} znaků (Claude fallback)"
                    )
                    return validated_dict
                else:
                    last_error = "Všechny klíče jsou prázdné"
            except Exception as ve:
                last_error = f"Pydantic validace: {ve}"
                logger.warning(f"[LLM Content] {chunk_name} validation failed: {ve}")
                non_empty = {k: v for k, v in content.items() if v and k in expected_keys}
                if non_empty:
                    return non_empty

        except Exception as e:
            last_error = str(e)
            logger.error(f"[LLM Content] {chunk_name} Claude attempt {attempt+1} error: {e}")

    logger.error(f"[LLM Content] {chunk_name}: Gemini i Claude selhaly")
    return {}


# ══════════════════════════════════════════════════════════════════════
# MAIN GENERATOR — 11 paralelních volání (asyncio.gather)
# ══════════════════════════════════════════════════════════════════════

async def _generate_one_section(
    key: str,
    pydantic_model: type,
    prompt_builder,
    company_context: str,
) -> Tuple[str, str]:
    """
    Generuje jednu sekci — vrací (key, "html content") nebo (key, "").
    """
    try:
        prompt = prompt_builder(company_context)
        result = await _call_llm_chunk(
            chunk_name=key,
            user_prompt=prompt,
            expected_keys=["content"],
            pydantic_model=pydantic_model,
        )
        content_text = result.get("content", "")
        if content_text:
            chars = len(content_text)
            logger.info(f"[LLM Content] {key}: {chars} znaků OK")
            return key, content_text
        else:
            logger.warning(f"[LLM Content] {key}: prázdný výstup")
            return key, ""
    except Exception as e:
        logger.error(f"[LLM Content] {key} selhalo: {e}")
        return key, ""


async def generate_document_content(data: dict) -> dict:
    """
    Generuje personalizovaný obsah pro 11 sekcí — každá má vlastní prompt.
    Sekce se generují SEKVENČNĚ (jedna po druhé) — spolehlivé, žádné rate limity.

    Returns:
        dict s 11 klíči (nebo méně při graceful degradation).
    """
    logger.info(f"[LLM Content] Generuji obsah — {len(_SECTION_REGISTRY)} sekcí (sekvenčně)")

    company_context = _build_company_context(data)

    # ── KB pre-generation: skip LLM for sections fully covered by Knowledge Base ──
    kb_generated: Dict[str, str] = {}
    if KB_AVAILABLE:
        try:
            ai_systems = data.get("ai_systems_declared", [])
            findings = data.get("findings", [])
            _kb_all_known = all_tools_known(ai_systems)
            logger.info(f"[LLM Content] KB: all_tools_known={_kb_all_known}")

            if _kb_all_known:
                # Try KB generators for sections that can be fully pre-written
                _kb_generators = {
                    "vendor_assessment": lambda: generate_vendor_assessment_kb(ai_systems, findings),
                    "chatbot_notices_custom": lambda: generate_chatbot_notices_kb(ai_systems, findings),
                    "monitoring_recommendations": lambda: generate_monitoring_kpis_kb(ai_systems),
                    "transparency_oversight": lambda: generate_transparency_oversight_kb(
                        ai_systems, findings,
                        human_oversight=data.get("human_oversight", {}),
                        incident=data.get("incident", {}),
                    ),
                }
                for sec_key, gen_fn in _kb_generators.items():
                    try:
                        result = gen_fn()
                        if result:
                            kb_generated[sec_key] = result
                            logger.info(f"[LLM Content] KB pre-generated: {sec_key} ({len(result)} chars) — skipping LLM")
                    except Exception as e:
                        logger.warning(f"[LLM Content] KB generator {sec_key} failed: {e} — will use LLM")
        except Exception as e:
            logger.warning(f"[LLM Content] KB pre-generation failed: {e}")

    # Sekvenční generování — jedna sekce po druhé, žádný rate-limit problém
    final_content: Dict[str, str] = {}
    for i, (key, (model, builder)) in enumerate(_SECTION_REGISTRY.items(), 1):
        # Skip if already generated by KB
        if key in kb_generated:
            final_content[key] = kb_generated[key]
            logger.info(f"[LLM Content] [{i}/{len(_SECTION_REGISTRY)}] {key}: ✓ KB (skipping LLM)")
            continue

        logger.info(f"[LLM Content] [{i}/{len(_SECTION_REGISTRY)}] Generuji: {key}")
        try:
            result_key, content = await _generate_one_section(key, model, builder, company_context)
            if content:
                final_content[result_key] = content
        except Exception as e:
            logger.error(f"[LLM Content] {key} selhalo: {e}")

    # ── Shrnutí ──
    missing = [k for k in ALL_EXPECTED_KEYS if k not in final_content]
    if missing:
        logger.warning(f"[LLM Content] Chybějící klíče ({len(missing)}): {missing}")

    total_chars = sum(len(v) for v in final_content.values())
    kb_count = len(kb_generated) if KB_AVAILABLE else 0
    llm_count = len(final_content) - kb_count
    logger.info(
        f"[LLM Content] Hotovo: {len(final_content)}/{len(_SECTION_REGISTRY)} sekcí, "
        f"{total_chars} znaků celkem "
        f"(KB: {kb_count} sekcí, LLM: {llm_count} sekcí)"
    )

    return final_content
