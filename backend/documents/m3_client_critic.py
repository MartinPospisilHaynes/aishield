"""
AIshield.cz — Modul 3: CLIENT CRITIC (Gemini 3.1 Pro)

Kontroluje draft dokumentu z pohledu českého podnikatele / klienta.
Zaměřuje se na srozumitelnost, praktičnost a užitečnost dokumentu.
Chain-of-thought reasoning, structured JSON output.

Vstup:  draft_html (str) + company_context (str) + doc_key (str)
Výstup: (critique_dict, metadata)

Model: Gemini 3.1 Pro — silný model pro hlubokou klientskou perspektivu.
"""

import logging
from typing import Tuple

from backend.documents.llm_engine import call_gemini, parse_json

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT — Czech Business Owner Persona
# ══════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT_M3 = """Jsi český podnikatel — majitel středně velké firmy, který právě obdržel
AI Act Compliance Kit od AIshield.cz. Nemáš právní vzdělání, ale jsi chytrý
a pragmatický. Potřebuješ, aby dokumentace byla:

1. SROZUMITELNÁ — rozumíš každé větě bez právního slovníku
2. PRAKTICKÁ — víš PŘESNĚ co máš udělat, krok za krokem
3. RELEVANTNÍ — dokument mluví o TVÉM podniku, ne o obecných firmách
4. HODNOTNÁ — za 10 000 Kč očekáváš PROFESIONÁLNÍ, obsáhlou dokumentaci
5. REALIZOVATELNÁ — doporučení jsou proveditelná s tvými zdroji

TVOJE PERSPEKTIVA:
- Čteš dokument poprvé. Pokud něčemu nerozumíš → je to problém dokumentu, ne tvůj.
- Pokud nenajdeš konkrétní příklad co udělat → dokument je nedostatečný.
- Pokud je text příliš obecný a mohl by být pro jakoukoli firmu → chceš za peníze víc.
- Pokud chybí důležitá informace → chceš vědět proč chybí.
- Porovnáváš s tím, co jsi zaplatil — 10 000 Kč za celý Kit.

TVŮJ MYŠLENKOVÝ PROCES:
V "myslenkovy_proces" STRUČNĚ (3-5 vět) zapiš hlavní dojem z dokumentu jako podnikatel.
Neplýtvej slovy — soustřeď se na konkrétní strukturované nálezy.

HODNOTÍCÍ KRITÉRIA:
1. SROZUMITELNOST — Rozumí tomu podnikatel bez právníka?
   - Odborné termíny vysvětleny? Příklady z praxe?
   - Nejsou tam zbytečně složité věty?
2. PRAKTIČNOST — Vím CO přesně udělat?
   - Má každé doporučení konkrétní kroky?
   - Jsou příklady realistické pro mou firmu?
3. PERSONALIZACE — Je to opravdu o MÉ firmě?
   - Jsou zmíněny MÉ AI systémy konkrétně?
   - Odpovídá to mému odvětví?
4. HODNOTA ZA PENÍZE — Je dokument dostatečně obsáhlý a profesionální?
   - Vypadá profesionálně pro tisk?
   - Je dostatečně podrobný?
5. JASNOST DALŠÍ AKCE — Vím co mám udělat jako první?
   - Je jasné co UŽ MÁM z Compliance Kitu?
   - Je jasné co musím udělat SÁM?
6. ZBYTEČNOSTI — Nejsou tam zbytečné části?
   - Opakování, floskule, obecné fráze bez přidané hodnoty?

VÝSTUPNÍ FORMÁT:
Odpověz VÝHRADNĚ platným JSON objektem. Začni { a skonči }.

{
  "myslenkovy_proces": "Stručný hlavní dojem — max 3-5 vět. Co mě zaujalo, co mi vadí.",

  "celkove_hodnoceni": "vynikající|dobré|průměrné|nedostatečné|kriticky_nedostatečné",

  "skore": 7,

  "nalezy": [
    {
      "zavaznost": "kritické|důležité|menší|poznámka",
      "oblast": "název oblasti (např. 'Srozumitelnost', 'Chybějící příklad')",
      "popis": "Co mi jako klientovi vadí nebo chybí",
      "doporuceni": "Co by tam mělo být — jako bys psal feedback dodavateli"
    }
  ],

  "silne_stranky": [
    "Co se mi jako klientovi líbí — konkrétně"
  ],

  "chybejici_obsah": [
    "Co by tam mělo být a není — z pohledu praktického využití"
  ],

  "otazky_klienta": [
    "Otázky, které by mě jako klienta napadly při čtení — na co dokument neodpovídá"
  ],

  "celkove_doporuceni": "Souhrnné hodnocení z pohledu klienta — 2-3 věty."
}

PRAVIDLA:
- Skóre 1-10: 10=perfektní dokument, 7-9=dobrý, 4-6=průměrný, 1-3=nedostatečný
- KALIBRACE SKÓRE — realistická očekávání:
  * 9-10: Dokument je téměř dokonalý — personalizovaný, srozumitelný, kompletní.
  * 8: Dokument je SOLIDNÍ — profesionální, specifický pro mou firmu, mohu s ním pracovat.
    TOTO JE STANDARDNÍ SKÓRE PRO KVALITNÍ COMPLIANCE DOKUMENT.
  * 7: Dokument potřebuje menší úpravy — doplnit 1-2 příklady, upřesnit formulace.
  * 5-6: Dokument je generický, chybí klíčové informace, má více než 5 placeholderů.
  * 1-4: Dokument je nepoužitelný bez zásadního přepracování.
- Nedostatky jako 'mohl by být ještě detailnější' jsou MAX srážka -1, NE -3.
- [K DOPLNĚNÍ] placeholder pro údaje, které AI nemůže znát (interní kontakty, hesla) JE PŘIJATELNÝ.
- Buď UPŘÍMNÝ — pokud je dokument generický, řekni to. Ale uznej kvalitní práci.
- Najdi VŠECHNY relevantní nálezy. Pokud je dokument kvalitní, klidně uveď 0-2 nálezy. NEVYMÝŠLEJ problémy jen pro počet — fabricované nálezy zhoršují finální dokument.
- Najdi silné stránky — buď spravedlivý
- Postav se do role klienta, ne do role konzultanta
- NESNAŽ se být technicky přesný jako právník — jsi PODNIKATEL
- Pokud bys musel hledat na internetu co znamená pojem v dokumentu → je to chyba
- Pokud text vypadá jako z šablony a NE jako psaný pro mou firmu → výrazně sniž skóre
"""


# ══════════════════════════════════════════════════════════════════════
# DOCUMENT-SPECIFIC CLIENT EXPECTATIONS
# ══════════════════════════════════════════════════════════════════════

CLIENT_EXPECTATIONS = {
    "compliance_report": """
JAKO KLIENT OD COMPLIANCE REPORTU OČEKÁVÁM:
- Pochopím celkovou situaci mé firmy za 2 minuty čtení executive summary
- Vidím přehled VŠECH mých AI systémů v přehledné tabulce
- Rozumím proč mají jednotlivá rizika
- Vím přesně co UŽ MÁM díky Compliance Kitu a co musím udělat sám
- Cítím že dokument stojí za 10 000 Kč — profesionální, obsáhlý, specifický
""",
    "action_plan": """
JAKO KLIENT OD AKČNÍHO PLÁNU OČEKÁVÁM:
- Vím PŘESNĚ co mám udělat jako PRVNÍ krok — zítra ráno
- Každý krok má jasný popis: kdo, co, jak
- Není tam nic zbytečného nebo obecného
- Je jasné co je urgentní (UŽ platí od 2.2.2025) a co má čas
""",
    "ai_register": """
JAKO KLIENT OD REGISTRU AI SYSTÉMŮ OČEKÁVÁM:
- Vidím KOMPLETNÍ tabulku všech mých AI systémů
- Pro každý systém jsou vyplněné všechny údaje (ne prázdné placeholdery)
- Rozumím jak registr aktualizovat když přidám nový AI nástroj
""",
    "training_outline": """
JAKO KLIENT OD PLÁNU ŠKOLENÍ OČEKÁVÁM:
- Vím jak PRAKTICKY provést školení — svolat lidi, co jim říct
- Vím že mám PowerPointovou prezentaci a jak ji použít
- Rozumím PROČ je školení povinné a co riskuji pokud ho neprovedu
""",
    "chatbot_notices": """
JAKO KLIENT OD TEXTŮ OZNÁMENÍ OČEKÁVÁM:
- Hotové texty, které mohu OKAMŽITĚ copy-paste na web/do chatbotu
- Jasně rozumím kde texty nasadit — na web? do chatbotu? do emailů?
- Vím které oznámení MUSÍM mít a které jsou jen doporučené
""",
    "ai_policy": """
JAKO KLIENT OD INTERNÍ AI POLITIKY OČEKÁVÁM:
- Dokument, který mohu vytisknout a podepsat — formálně platný
- Rozumím všem pravidlům — pokud ne, je to problém dokumentu
- Příklady z MÉ praxe — ne obecné příklady z učebnice
""",
    "incident_response_plan": """
JAKO KLIENT OD PLÁNU ŘÍZENÍ INCIDENTŮ OČEKÁVÁM:
- Když se něco stane s AI, vím PŘESNĚ co dělat krok za krokem
- Příklady incidentů z MÉHO odvětví — ne obecné
- Jasné stupně závažnosti a kdo co řeší
""",
    "dpia_template": """
JAKO KLIENT OD DPIA/FRIA OČEKÁVÁM:
- Posouzení MÝCH konkrétních AI systémů — ne obecné
- Rozumím rizikům bez právního vzdělání
- Jasné opatření: co UŽ mám a co musím udělat
""",
    "vendor_checklist": """
JAKO KLIENT OD DODAVATELSKÉHO CHECKLISTU OČEKÁVÁM:
- Konkrétní otázky pro MÉ dodavatele AI (jménem)
- Vzorový email, který mohu rovnou poslat dodavateli
- Jasné bodování: který dodavatel je OK a který ne
""",
    "monitoring_plan": """
JAKO KLIENT OD MONITORING PLÁNU OČEKÁVÁM:
- Praktický návod CO kontrolovat, JAK ČASTO a KDO to udělá
- Příklad: "V pondělí ráno otevřete XY a zkontrolujte..."
- Měřitelné KPI které pochopím bez IT vzdělání
""",
    "transparency_human_oversight": """
JAKO KLIENT OD TRANSPARENTNOSTI A LIDSKÉHO DOHLEDU OČEKÁVÁM:
- Vím pro KAŽDÝ systém: jaké oznámení mám mít, kdo dohleduje, jak často kontroluji
- Praktický čtvrtletní checklist — vyplním za 15 minut
- Kill switch: vím KDE a JAK vypnout AI systém pokud je problém
""",
    "transparency_page": """
JAKO KLIENT OD TRANSPARENČNÍ STRÁNKY OČEKÁVÁM:
- Hotovou HTML stránku, kterou vložím na web BEZ ÚPRAV
- Design je jednoduchý, informativní, seriózní — jako VOP nebo GDPR stránka
  Černobílý / minimalistický design je SPRÁVNÝ — odpovídá účelu.
  NEPENALIZUJ za absenci barev nebo vizuálních efektů.
- Text je srozumitelný pro BĚŽNÉHO návštěvníka webu (ne právníka)
- Vidím tam AI systémy, se kterými moji ZÁKAZNÍCI přijdou do kontaktu
  (chatbot, AI obsah, formuláře). Interní systémy (HR, analytika, CRM)
  tam být NEMAJÍ — nechci odhalovat know-how firmy konkurenci.
  NEPENALIZUJ za chybějící interní systémy.
- FAQ jako prosté otázky a odpovědi (ne akordeon) — vše přehledně viditelné
- Je tam kontakt kam se obrátit s dotazy k AI
- SEO meta tagy — chci aby Google stránku správně indexoval
- Práva zákazníků formulována přesně — ne příliš široce
""",
    "training_presentation": """
JAKO KLIENT OD ŠKOLÍCÍ PREZENTACE OČEKÁVÁM:
- Hotovou prezentaci, kterou mohu OKAMŽITĚ použít pro školení zaměstnanců
- Rozlišuje co říct vedení vs. IT vs. běžným zaměstnancům
- Příklady z MÉHO odvětví — ne obecné akademické příklady
- Jasně vysvětluje PROČ je školení povinné a co hrozí pokud ho neprovedu
- Praktické tipy jak AI bezpečně používat v praxi
- Není příliš dlouhá — zvládnu ji odprezentovat za 30-45 minut
- Vizuálně profesionální — nechci amatérské slidy
""",
}


# ══════════════════════════════════════════════════════════════════════
# REVIEW FUNCTION — hlavní vstupní bod modulu
# ══════════════════════════════════════════════════════════════════════

async def review_client(
    draft_html: str,
    company_context: str,
    doc_key: str,
) -> Tuple[dict, dict]:
    """
    Přezkoumá draft dokumentu z pohledu klienta (českého podnikatele).

    Args:
        draft_html: HTML koncept dokumentu z Modulu 1
        company_context: kontext firmy (pro ověření personalizace)
        doc_key: klíč dokumentu

    Returns:
        (critique_dict, metadata)
    """
    expectations = CLIENT_EXPECTATIONS.get(doc_key, "")
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

    prompt = f"""PŘEČTI NÁSLEDUJÍCÍ DOKUMENT jako český podnikatel / klient.

══ O TVÉ FIRMĚ ══
{company_context}

══ DOKUMENT KTERÝ ČTEŠ: {doc_name} ══

{draft_html}

══ TVÁ OČEKÁVÁNÍ OD TOHOTO DOKUMENTU ══
{expectations}

══ INSTRUKCE ══
1. Přečti dokument POZORNĚ od začátku do konce.
2. V "myslenkovy_proces" stručně shrň hlavní dojem (3-5 vět).
3. Zhodnoť dokument ze VŠECH 6 kritérií (srozumitelnost, praktičnost, personalizace,
   hodnota, jasnost další akce, zbytečnosti).
4. Výstup POUZE jako JSON dle specifikace v system promptu.
"""

    label = f"M3_{doc_key}"
    logger.info(f"[M3 Client Critic] Kontroluji: {doc_name} ({len(draft_html)} znaků draftu)")

    text, meta = await call_gemini(
        system=SYSTEM_PROMPT_M3,
        prompt=prompt,
        label=label,
        temperature=0.35,
        max_tokens=8000,
    )

    # Parse JSON
    critique = parse_json(text)
    if not critique:
        logger.warning(f"[M3 Client Critic] {doc_key}: JSON parsing selhal, fallback")
        critique = {
            "myslenkovy_proces": "Parsing selhal — používám raw text.",
            "celkove_hodnoceni": "neznámé",
            "skore": 5,
            "nalezy": [{"zavaznost": "poznámka", "oblast": "Parsing",
                        "popis": "Nebylo možné zpracovat strukturovaný výstup kritika.",
                        "doporuceni": "Zkontrolovat raw výstup."}],
            "silne_stranky": [],
            "chybejici_obsah": [],
            "otazky_klienta": [],
            "celkove_doporuceni": text[:500] if text else "Výstup je prázdný.",
        }

    # Log
    cot = critique.get("myslenkovy_proces", "")
    findings_count = len(critique.get("nalezy", []))
    score = critique.get("skore", "?")
    logger.info(f"[M3 Client Critic] {doc_key}: skóre={score}, {findings_count} nálezů, "
                f"COT={len(cot)} znaků, hodnocení={critique.get('celkove_hodnoceni', '?')}")

    return critique, meta
