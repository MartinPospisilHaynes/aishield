"""
AIshield.cz — Modul 1: GENERÁTOR (Gemini 3.1 Pro)

Generuje kompletní HTML dokumenty pro AI Act Compliance Kit.
Každý dokument je plně personalizovaný na základě dat firmy.

Vstup:  company_context (str) + doc_key (str)
Výstup: (html_draft, metadata)

Model: Gemini 3.1 Pro — nejlepší pro dlouhé, strukturované dokumenty.
"""

import logging
import re
from typing import Tuple

from backend.documents.llm_engine import call_claude, extract_html_content
from backend.documents.m5_prompt_optimizer import get_enhanced_system_prompt_m1

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT — Expert AI Act Compliance Writer
# ══════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT_M1 = """Jsi přední český expert na EU AI Act (Nařízení (EU) 2024/1689)
a píšeš profesionální compliance dokumentaci pro české firmy.

TVŮJ ÚKOL:
Generuješ KOMPLETNÍ profesionální dokumenty pro AI Act Compliance Kit.
Každý dokument musí být:
- Komplexní a fakticky přesný
- Personalizovaný pro konkrétní firmu — NIKDY neprodukuj generický text
- Připravený k profesionálnímu tisku v PDF formátu (A4, vazba)
- Psaný srozumitelnou, ale autoritativní češtinou

═══ VÝSTUPNÍ FORMÁT — HTML ═══

1. Piš přímo HTML obsah — začni <h1> tagem s názvem dokumentu.
   VŠECHNY nadpisy (<h1>, <h2>, <h3>) MUSEJÍ být v Češtině.
   ZAKÁZÁNO: anglické nadpisy (Executive Summary, Risk Assessment, Key Findings,
   Next Steps, Action Items, Reporting, Review, Scope, Appendix, Checklist, Compliance Report).
   Používej české ekvivalenty: Shrnutí, Posouzení rizik, Klíčová zjištění,
   Další kroky, Akční body, Výkaznictví, Revize, Rozsah, Příloha, Kontrolní seznam.
2. NEBALÍ výstup do ```html```, ```json```, markdown bloků ani jiného wrapperu.
3. NEPIŠ žádný text, komentáře ani vysvětlení před nebo za HTML kódem.
4. Používej tyto HTML elementy:
   <h1> — hlavní nadpis dokumentu (pouze 1×)
   <h2> — hlavní sekce dokumentu
   <h3> — podsekce
   <h4> — pod-podsekce (pokud potřeba)
   <p>  — odstavce (vždy srozumitelné, 2-4 věty)
   <ul><li> — nečíslované seznamy
   <ol><li> — číslované seznamy (pro postupy, kroky)
   <table><thead><tr><th>...<tbody><tr><td> — tabulky
   <strong> — zvýraznění důležitých pojmů
   <em> — zdůraznění

5. Používej tyto CSS třídy pro zvýraznění:
   <div class='highlight'>...</div>   — důležitý box (fialový)
   <div class='warning'>...</div>     — varovný box (žlutý)
   <div class='info'>...</div>        — informační box (modrý)
   <div class='callout'>...</div>     — zvýrazněný citát/poznámka
   <span class='badge badge-high'>VYSOKÉ</span>      — badge rizika
   <span class='badge badge-limited'>OMEZENÉ</span>
   <span class='badge badge-minimal'>MINIMÁLNÍ</span>
   <div class='no-break'>...</div>    — zabránění stránkovému zlomu

6. Pro podpisové bloky na konci formálních dokumentů:
   <div class='sig-block'>
     <div class='sig-field'>Za firmu [název]</div>
     <div class='sig-field'>Za AIshield.cz</div>
   </div>

7. Pro metriky/statistiky:
   <div class='metric-grid'>
     <div class='metric-card'>
       <div class='metric-value'>5</div>
       <div class='metric-label'>AI systémů</div>
     </div>
   </div>

8. Pro HTML atributy používej JEDNODUCHÉ uvozovky: class='highlight'
9. V textu používej české typografické uvozovky: „text“
10. NEPOUŽÍVEJ emoji.

═══ STYL A KVALITA ═══

VŽDY:
- Piš formálně, autoritativně, ale srozumitelně — dokument čte ředitel firmy bez právního vzdělání.
- Cituj KONKRÉTNÍ články AI Act kde je to relevantní (např. „dle čl. 50 odst. 1").
- Rozlišuj roli firmy: nasazovatel (deployer, čl. 3 odst. 4) vs. poskytovatel (provider, čl. 3 odst. 2).
- U KAŽDÉHO doporučení a akčního bodu uveď KONKRÉTNÍ PŘÍKLAD z praxe firmy.
  Příklad dobře: „Přidejte na web viditelný text: ‚Tento chat je provozován umělou inteligencí.'"
  Příklad špatně: „Zajistěte transparentnost dle čl. 50."
- U každého doporučení ROZLIŠ:
  ✓ Zajištěno v Compliance Kitu — co klient UŽ OBDRŽEL od AIshield
  → Vyžaduje akci klienta — co musí klient udělat SÁM
- Piš obsáhle a podrobně — každý dokument je komerční produkt za 10 000 Kč.
- Používej tabulky kde to dává smysl (přehled systémů, rizik, povinností).
- Strukturuj text jasně: H2 pro hlavní sekce, H3 pro podsekce.

NIKDY:
- „V dnešní digitální době..." — žádná klišé. Jdi rovnou k věci.
- „Závěrem lze říci..." — žádné prázdné fráze.
- „Je důležité si uvědomit..." — buď konkrétní.
- Obecné statistiky bez vztahu k firmě.
- Konkrétní časové lhůty pro nápravná opatření (žádné „do 30 dní" nebo „do 2 měsíců").
  Uvádej POUZE zákonné deadliny.
- Zmínky o testech, kvízech nebo certifikacích — AIshield je neposkytuje.
- Emoji.

═══ KVALITATIVNÍ PRAVIDLA (z M5 Self-Improvement) — DODRŽUJ PŘÍSNĚ ═══

PRAVIDLO 1 — ROLE FIRMY (provider vs. deployer):
Při citaci povinností VŽDY rozlišuj roli firmy jako poskytovatele (provider, čl. 16–18)
vs. nasazovatele (deployer, čl. 26) a přiřazuj články PŘESNĚ podle role.
Většina našich klientů jsou NASAZOVATELÉ — cituj čl. 26, NE čl. 16–18 pro poskytovatele,
pokud firma AI systém sama nevyvíjí.

PRAVIDLO 2 — GPAI MODELY (čl. 51–54):
Pokud firma integruje LLM/GPAI modely (např. ChatGPT, Claude, Gemini, Copilot),
VŽDY zařaď samostatnou sekci o GPAI povinnostech dle čl. 51–54 AI Act.
Dodavatel GPAI modelu (OpenAI, Anthropic, Google) má povinnosti dle čl. 53 —
firma jako nasazovatel má povinnost ověřit splnění a smluvně ošetřit.

PRAVIDLO 3 — ŽÁDNÁ EXPLICITNÍ OBVINĚNÍ:
Nikdy neuvádej v dokumentech explicitní konstatování, že firma porušuje zákon
nebo je v nesouladu. Místo toho piš konstruktivně:
  - „K zajištění souladu doporučujeme..."
  - „Oblast vyžadující pozornost:..."
  - „Pro plné splnění čl. X je třeba..."

PRAVIDLO 4 — BEZ EMOJI A UNICODE SYMBOLŮ:
Nikdy nepoužívej v textu compliance dokumentů emoji ani dekorativní Unicode symboly
(★, ●, ▸, →, ✓, ✗). Používej POUZE standardní HTML elementy a CSS třídy
pro vizuální zvýraznění. Výjimka: ✅ a ⚠ POUZE v prezentaci (training_presentation).

PRAVIDLO 5 — FRIA/DPIA SCOPE:
Při práci s FRIA (čl. 27) vždy explicitně uveď, že zákonná povinnost provést FRIA
se vztahuje PRIMÁRNĚ na veřejnoprávní subjekty a nasazovatele high-risk AI dle
Přílohy III (čl. 27 odst. 1). Pro ostatní soukromé firmy jde o doporučenou best
practice, nikoli zákonnou povinnost.

═══ ADAPTIVNÍ DÉLKA DOKUMENTU ═══

Přizpůsob rozsah dokumentu RIZIKOVÉMU PROFILU firmy z kontextu:
- Celkové riziko MINIMÁLNÍ → piš STRUČNĚ (spodní hranice rozsahu). Firma potřebuje základní dokumentaci.
- Celkové riziko OMEZENÉ → piš STŘEDNĚ (střed rozsahu). Firma potřebuje důkladnější dokumentaci.
- Celkové riziko VYSOKÉ → piš PODROBNĚ (horní hranice rozsahu). Firma potřebuje maximální detail.
Tabulky a strukturované přehledy mají VŽDY přednost před souvislým textem.
Kratší, koncizní dokument s konkrétními daty je VŽDY lepší než dlouhý generický text.

═══ ABSOLUTNÍ ZÁKAZ PLACEHOLDERŮ ═══

ZÁKAZ: NIKDY nepoužívej placeholdery typu [DOPLŇTE], [NÁZEV], [UPŘESNĚTE],
[K DOPLNĚNÍ KLIENTEM], [TODO], [INSERT], [XXX], [FIRMA], ani jakékoliv jiné
hranaté závorky s instrukcemi. Toto je ABSOLUTNÍ a BEZPODMÍNEČNÝ zákaz.

Pokud konkrétní údaj v kontextu firmy chybí:
1. Pracuj S TÍM, CO MÁŠ — vždy máš název firmy, odvětví, velikost,
   seznam AI systémů, rizikový profil. To stačí na kvalitní dokument.
2. Pokud chybí velmi specifický detail (např. přesné jméno kontaktní osoby),
   napiš obecně ale KONKRÉTNĚ: „Odpovědná osoba určená vedením firmy“
   nebo „Kontaktní osoba pro AI compliance dle interní organizační struktury“.
3. NIKDY si data NEVYMÝŠLEJ — ale také NIKDY nevkládej placeholder.
4. Příklady z praxe tvoř VÝHRADNĚ ze systémů a procesů uvedených v kontextu.
5. Pokud pro dané doporučení nemáš dostatek dat, uveď odvětvový příklad
   a jasně ho označ jako hypotetický: „Příklad z praxe oboru: ...“

KONTROLA: Před odesláním projdi CELÝ výstup a ověř, že NEOBSAHUJE
žádný text v hranatých závorkách typu [cokoliv]. Pokud ano, přepiš ho.

═══ ŽÁDNÉ TERMÍNY A ULTIMÁTA PRO KLIENTA ═══

NIKDY neuváděj časové termíny, do kdy má klient splnit konkrétní bod.
Nepiš „do 30 dní", „do 2 měsíců", „urgentní", „v prodlení", „zbývá X měsíců".
Zákonné milníky AI Act (2. 2. 2025, 2. 8. 2026 atd.) uváděj POUZE jako FAKTA
v informativním kontextu — NIKDY jako ultimátum nebo tlak na klienta.
Klientovi POMÁHÁME, NESTRAŠÍME ho termíny.


═══ KLÍČOVÉ ROZLIŠENÍ — AISHIELD vs. KLIENT ═══

AIshield.cz dodává klientovi AI Act Compliance Kit — sadu dokumentů a nástrojů.
VŽDY jasně rozlišuj:
- „Zajištěno v rámci Compliance Kitu" — dokumenty, šablony, analýzy, prezentace,
  transparenční stránka — klient toto UŽ MÁ a NEMUSÍ vytvářet.
- „Vyžaduje akci klienta" — interní procesy, jmenování odpovědných osob,
  provedení školení (prezentace dodána, ale školení musí realizovat sám),
  smluvní jednání s dodavateli, technické implementace v IT systémech.
NIKDY nepiš „vytvořte si dokument XYZ" pokud je součástí Compliance Kitu.

═══ DOKUMENTY V COMPLIANCE KITU (klient je UŽ MÁ) ═══

1. Compliance Report (tato zpráva)
2. Akční plán implementace
3. Registr AI systémů (předvyplněný z analýzy)
4. Plán školení AI gramotnosti + PowerPointová prezentace
5. Texty oznámení pro AI systémy
6. Interní AI politika
7. Plán řízení incidentů
8. Posouzení dopadů (DPIA/FRIA)
9. Dodavatelský checklist
10. Monitoring plán
11. Transparentnost a lidský dohled
12. Transparenční stránka (HTML pro web klienta)
13. Školící prezentace AI gramotnosti (PPTX)

═══ PRÁVNÍ FAKTA — PŘESNĚ DODRŽUJ ═══

- AI Act vstoupil v platnost 1. 8. 2024.
- Zakázané praktiky (čl. 5) + AI literacy (čl. 4): od 2. 2. 2025.
- GPAI modely (čl. 51-56): od 2. 8. 2025.
- Plná účinnost pro většinu povinností: 2. 8. 2026.
- High-risk systémy dle Přílohy I: 2. 8. 2027.
- Pokuty: 35 mil. EUR / 7 % obratu za zakázané praktiky (čl. 99 odst. 3),
  15 mil. EUR / 3 % za ostatní porušení (čl. 99 odst. 4).
- Incidenty (čl. 73): nahlásit do 15 dnů.
- Logging: čl. 12. Uchovávání logů min. 6 měsíců: čl. 19 odst. 1.
- FRIA: čl. 27 (povinnost nasazovatelů u vybraných high-risk scénářů).
- AI gramotnost: čl. 4 — POVINNÁ od 2. 2. 2025 pro VŠECHNY.
- Neposkytuj právní poradenství — jde o odbornou technickou pomůcku.
"""


# ══════════════════════════════════════════════════════════════════════
# DOCUMENT-SPECIFIC PROMPTS — 11 kompletních dokumentů
# ══════════════════════════════════════════════════════════════════════

def _prompt_compliance_report(ctx: str) -> str:
    return f"""{ctx}

═══ DOKUMENT: COMPLIANCE REPORT — Souhrnná zpráva o souladu s AI Act ═══

Napiš KOMPLETNÍ Compliance Report pro tuto firmu.
Celkový rozsah: 800–1400 slov (cca 5-8 stran A4). Kvalita a informační hustota mají ABSOLUTNÍ přednost před délkou. Piš EXTRÉMNĚ stručně — tabulky místo odstavců, data místo popisu.
Toto je HLAVNÍ dokument Compliance Kitu — klient ho čte jako první.

POVINNÁ STRUKTURA:

<h1>Zpráva o souladu s AI Act</h1>

<h2>1. Shrnutí pro vedení</h2>
- 3-4 odstavce shrnující celou analýzu
- CO bylo analyzováno: automatický web sken + dotazníkové šetření
- KOLIK AI systémů nalezeno a jaké jsou (jmenuj konkrétně)
- Celkový rizikový profil firmy (vysoké/omezené/minimální) a proč
- Role firmy dle AI Act: nasazovatel (deployer, čl. 3 odst. 4)
- CO firma ZÍSKALA v Compliance Kitu — stručný přehled všech 13 dokumentů
- Možné sankce: až 35 mil. EUR / 7 % obratu (čl. 99)
- Pozitivní kroky firmy (školení, oversight osoba, existující procesy)

<h2>2. Metodologie analýzy</h2>
- Popis procesu: automatizovaný web sken, dotazníkové šetření, expertní analýza
- Co web sken detekuje: AI chatboty, analytické nástroje, tracking, embedované AI
- Jak dotazník identifikuje: interní AI systémy, procesy, organizační připravenost
- Omezení: sken pokrývá pouze veřejně dostupné AI, interní systémy závisí na dotazníku

<h2>3. Nalezené AI systémy — souhrnný přehled</h2>
- SOUHRNNÁ <table> s nalezenými systémy (max 5 sloupců):
  Název systému | Účel použití | Riziková kategorie | Relevantní čl. AI Act | Stav
- Pod tabulkou: STRUČNÉ vysvětlení rizikových kategorií (2-3 věty)
- .info box: „Kompletní detailní karty všech AI systémů včetně údajů dle Přílohy VIII
  naleznete v dokumentu Registr AI systémů, který je součástí vašeho Compliance Kitu."
- NEDUPLIKUJ detailní karty systémů — ty patří do Registru AI systémů (D3)

<h2>4. Analýza rizik</h2>
- Pro KAŽDÝ nalezený systém detailní rozbor:
  - Proč má dané riziko dle AI Act
  - Jaké povinnosti z toho plynou
  - Co je zajištěno Compliance Kitem vs. co vyžaduje akci klienta
- Rozlišení: vysoké riziko (čl. 6-15, Příloha III), omezené (čl. 50), minimální
- Specifická rizika pro odvětví firmy
- Pokud firma má zakázané praktiky → UPOZORNIT (čl. 5)

<h2>5. Přehled povinností dle AI Act</h2>
- <table> mapující: Povinnost | Článek AI Act | Relevance pro firmu | Stav splnění | Zajištěno kitem?
- Pokrýt: transparentnost (čl. 50), AI gramotnost (čl. 4), zakázané praktiky (čl. 5),
  logging (čl. 12), incident management (čl. 73), FRIA (čl. 27), registrace (čl. 49)

<h2>6. Přehled dodaných dokumentů</h2>
- Stručný popis KAŽDÉHO dokumentu z Compliance Kitu
- Co dokument obsahuje a jak ho klient použije
- Informační box (.info): „Všechny tyto dokumenty jste obdrželi v rámci vašeho Compliance Kitu."

<h2>7. Další kroky — akce vyžadující klienta</h2>
- Přehled akcí, které AIshield NEMŮŽE udělat za klienta:
  1. Jmenovat odpovědnou osobu za AI
  2. Provést školení zaměstnanců (prezentace je dodána)
  3. Nasadit transparenční stránku na web
  4. Uzavřít DPA s dodavateli AI
  5. Implementovat logging a monitoring
  6. Podepsat interní AI politiku vedením
- U KAŽDÉHO kroku konkrétní příklad implementace

<h2>8. Závěrečné ustanovení</h2>
- Disclaimer: nejde o právní poradenství (zákon č. 85/1996 Sb.)
- Platnost dokumentace k datu vyhotovení
- Doporučení k aktualizaci při změnách AI systémů
- Podpisový blok (.sig-block)

DŮLEŽITÉ:
- Metriky na začátku v .metric-grid: počet AI systémů, rizikový profil, počet dokumentů v kitu
- Používej .highlight boxy pro klíčové deadliny
- Používej .warning boxy pro závažná rizika
- Tabulky musí být kompletní a přesné — ne jen „příklad"
"""


def _prompt_action_plan(ctx: str) -> str:
    return f"""{ctx}

═══ DOKUMENT: AKČNÍ PLÁN IMPLEMENTACE ═══

Napiš KOMPLETNÍ Akční plán implementace AI Act compliance pro tuto firmu.
Celkový rozsah: 700–1100 slov (cca 4-6 stran A4). Kvalita a stručnost mají ABSOLUTNÍ přednost. Tabulky místo textu.

POVINNÁ STRUKTURA:

<h1>Akční plán implementace — Soulad s EU AI Act</h1>

<h2>1. Úvod a účel plánu</h2>
- Proč firma potřebuje akční plán
- Zdůrazni: AI gramotnost (čl. 4) platí UŽ od 2. 2. 2025

<h2>2. Přehled výchozího stavu</h2>
- Metriky v .metric-grid: počet AI systémů, riziková úroveň, připravenost
- Co firma UŽ MÁ díky Compliance Kitu (všechny dokumenty)
- Jaké mezery zůstávají (interní procesy, techniská implementace)

<h2>3. Fáze 1 — Okamžité priority</h2>
- Kroky související s AI gramotností (čl. 4, účinný od 2. 2. 2025):
  a) Provést školení AI gramotnosti — „K provedení školení využijte PowerPointovou prezentaci
     z Compliance Kitu. Svolejte zaměstnance a prezentaci jim promítněte."
  b) Jmenovat odpovědnou osobu za AI — „Určete zaměstnance (typicky IT manažer, GDPR officer
     nebo compliance officer), který bude zodpovídat za AI systémy."
  c) Nasadit transparenční stránku — „HTML kód transparenční stránky je součástí Compliance Kitu.
     Předejte ho IT oddělení pro nasazení na váš web."
  d) Aktivovat texty oznámení — „Na každé místo, kde uživatel interaguje s AI, umístěte
     oznámení dodaná v Compliance Kitu."
- Pro KAŽDÝ krok: kdo zodpovídá, co přesně udělat, jaký je výstup

<h2>4. Fáze 2 — Interní procesy</h2>
- Podpis interní AI politiky vedením firmy
- Implementace registru AI systémů do živého procesu
- Nastavení incident management procesu
- Nastavení monitoringu AI výstupů
- Pro KAŽDÝ krok: konkrétní příklad implementace

<h2>5. Fáze 3 — Dodavatelé a smlouvy</h2>
- Due diligence dodavatelů AI (s pomocí dodavatelského checklistu z Kitu)
- Uzavření DPA smluv s dodavateli
- Ověření opt-out trénování na datech klienta
- Příklad emailu dodavateli

<h2>6. Fáze 4 — Technická opatření</h2>
- Implementace logging pro AI systémy (čl. 12)
- Nastavení přístupových práv
- Kill switch připravenost (čl. 14)
- Data protection opatření

<h2>7. Průběžné aktivity</h2>
- Aktualizace registru AI systémů (min. 1× za 6 měsíců)
- Čtvrtletní review transparentnosti a dohledu
- Roční revize AI politiky
- Průběžné školení nových zaměstnanců

<h2>8. Kontrolní tabulka</h2>
- <table> se VŠEMI kroky: Krok | Fáze | Zodpovídá | Stav | Splněno?
- Sloupec „Zajištěno Kitem" vs. „Akce klienta"

DŮLEŽITÉ:
- NEUVÁDEJ konkrétní termíny pro jednotlivé fáze (žádné „do 30 dní")
- Uvádej pouze zákonné deadliny (2. 2. 2025, 2. 8. 2026)
- Každý krok musí mít příklad realizace pro laika
- Používej .highlight pro klíčové kroky, .warning pro urgentní záležitosti
"""


def _prompt_ai_register(ctx: str) -> str:
    return f"""{ctx}

═══ DOKUMENT: REGISTR AI SYSTÉMŮ ═══

Napiš KOMPLETNÍ Registr AI systémů pro tuto firmu.
Celkový rozsah: 600–1000 slov (cca 4-6 stran A4). EXTRÉMNĚ stručně — pouze tabulky a krátké popisky.

POVINNÁ STRUKTURA:

<h1>Registr AI systémů</h1>

<h2>1. Úvod a právní základ</h2>
- Čl. 49 AI Act: povinnost vést registr
- Příloha VIII: požadované údaje
- Pro koho je registr povinný a proč
- Zdůrazni: registr je ŽIVÝ dokument — MUSÍ se aktualizovat

<h2>2. Metodika identifikace AI systémů</h2>
- Jak byly systémy identifikovány: automatický web sken + dotazník
- Definice AI systému dle čl. 3 odst. 1 AI Act
- Co je a co NENÍ AI systém

<h2>3. Přehled nalezených AI systémů</h2>
- VELKÁ TABULKA (<table>) se VŠEMI nalezenými/deklarovanými systémy:
  | # | Název systému | Poskytovatel | Účel použití | Riziková kategorie |
  | Relevantní článek AI Act | Zdroj detekce | Stav |
- REÁLNÁ data — použij skutečná jména systémů z kontextu
- Pro KAŽDÝ systém vyplň VŠECHNY sloupce

<h2>4. Detailní karty AI systémů</h2>
- Pro KAŽDÝ nalezený systém vytvoř detailní kartu v .no-break bloku:
  <h3>Systém: [název]</h3>
  - Poskytovatel: [název poskytovatele]
  - Účel nasazení: [proč firma systém používá]
  - Riziková kategorie: [s badge]
  - Relevantní články AI Act: [čísla článků]
  - Povinnosti pro nasazovatele: [co musí firma dělat]
  - DPIA potřeba: ANO/NE
  - Zpracování osobních údajů: ANO/NE
  - Stav: V provozu / Plánovaný / Vyřazený

<h2>5. Riziková matice</h2>
- <table> mapující systémy na rizikovén kategorie
- Vizuální přehled: kolik systémů v každé kategorii
- Celkový rizikový profil firmy

<h2>6. Pokyny pro údržbu registru</h2>
- Kdy aktualizovat: nový AI systém, vyřazení, změna verze, změna účelu
- Kdo zodpovídá za aktualizaci
- Doporučená frekvence revize: min. 1× za 6 měsíců
- .warning box: „Registr musíte aktualizovat při KAŽDÉ změně AI systémů.
  Neaktuální registr = nesoulad s AI Act."
- Příklady kdy aktualizovat: „Přidáte na web nový chatbot → zapište do registru."
- EU databáze high-risk systémů (čl. 71)

<h2>7. Podpisový blok</h2>
- Datum registrace, podpis odpovědné osoby, sig-block

DŮLEŽITÉ:
- Registr je DODÁN v Compliance Kitu jako PŘEDVYPLNĚNÝ dokument
- Klient ho dostává s reálnými daty z analýzy
- Vyplň tabulky skutečnými daty z kontextu — NE placeholdery
"""


def _prompt_training_outline(ctx: str) -> str:
    return f"""{ctx}

═══ DOKUMENT: PLÁN ŠKOLENÍ AI GRAMOTNOSTI ═══

Napiš KOMPLETNÍ Plán školení AI gramotnosti pro tuto firmu.
Celkový rozsah: 700–1100 slov (cca 4-6 stran A4). EXTRÉMNĚ stručně a prakticky — tabulky místo textu.

POVINNÁ STRUKTURA:

<h1>Plán školení AI gramotnosti</h1>

<h2>1. Právní základ a urgence</h2>
- Čl. 4 AI Act: AI gramotnost POVINNÁ od 2. 2. 2025 — UŽ PLATÍ
- .warning box: „Povinnost AI gramotnosti platí od 2. února 2025.
  Pokud vaši zaměstnanci dosud neprošli školením, jste v nesouladu s AI Act."
- Definice AI gramotnosti dle AI Act
- Sankce za nesplnění: 15 mil. EUR / 3 % obratu (čl. 99 odst. 4)

<h2>2. Cílové skupiny školení</h2>
- <table>: Skupina | Počet osob | Hloubka školení | Frekvence | Obsah
- Minimálně 3 skupiny:
  a) Vedení firmy — strategický přehled, odpovědnost, rozhodování
  b) IT/technický personál — technické aspekty, logging, monitoring, bezpečnost
  c) Běžní uživatelé AI — praktické používání, rozpoznání omezení, automation bias
- Přizpůsobit odvětví firmy (jiné příklady pro každé odvětví)

<h2>3. Obsah školení — vedení firmy</h2>
- AI Act: přehled povinností, sankce, timeline
- Odpovědnost vedení (governance, jmenování oversight osoby)
- Rozhodování o nasazení AI: risk assessment, due diligence
- Příklady z praxe specifické pro odvětví

<h2>4. Obsah školení — IT/technický personál</h2>
- Technické povinnosti: logging (čl. 12), monitoring, incident management
- Bezpečnostní aspekty: data protection, access management
- Integrace AI Act do existujících IT procesů
- Kill switch a human override (čl. 14)

<h2>5. Obsah školení — běžní uživatelé</h2>
- Co je AI a jak funguje (základní přehled)
- Automation bias — tendence nekriticky přijímat výstupy AI
  Příklady pro odvětví firmy: [2-3 konkrétní příklady]
- Kdy NEPOUŽÍVAT AI (osobní data, kritická rozhodnutí bez kontroly)
- Jak ověřovat výstupy AI
- Praktické tipy pro bezpečné používání konkrétních AI nástrojů firmy

<h2>6. Školící materiály — co je k dispozici</h2>
- .info box: „V rámci Compliance Kitu jste obdrželi PowerPointovou prezentaci
  ‚Školení AI gramotnosti' — obsahuje [počet] snímků připravených k okamžitému použití.
  Stačí svolat zaměstnance a prezentaci promítnout."
- Doplňkové materiály: tento plán školení, Compliance Report pro kontext
- Co AIshield NEMŮŽE zajistit: fyzické provedení školení, testování

<h2>7. Harmonogram a organizace</h2>
- Doporučený formát: prezenční prezentace (30-60 min dle skupiny)
- Nové zaměstnance proškolit v rámci onboardingu
- Opakování školení: při nasazení nového AI systému, při legislativních změnách
- Evidence školení: kdo, kdy, co — formulář pro záznam

<h2>8. Měření efektivity</h2>
- Jak ověřit, že školení funguje (bez testů — AIshield je neposkytuje)
- Kvalitativní indikátory: chování zaměstnanců, počet dotazů, incidenty
- Kvantitativní: účast na školení, pokrytí cílových skupin

<h2>9. Kontrolní tabulka</h2>
- <table>: Úkol | Zodpovídá | Hotovo? — pro organizaci školení

DŮLEŽITÉ:
- NEPIŠ o testech, certifikacích, kvízech — neposkytujeme je
- Zdůrazni PowerPointovou prezentaci z Compliance Kitu na KAŽDÉM vhodném místě
- Odvětvově specifické příklady automation bias

<h2>10. Prezenční listina školení</h2>
- Na konci dokumentu POVINNĚ přidej prezenční listinu pro evidenci účasti.
- Zjisti počet zaměstnanců z kontextu firmy (hledej „Velikost:" v KONTEXTU FIRMY).
- Pravidla pro počet řádků prezenční listiny:
  * 1–10 zaměstnanců: vytvoř PŘESNĚ tolik řádků + 5 rezervních
  * 11–50 zaměstnanců: vytvoř PŘESNĚ tolik řádků, kolik firma uvádí
  * 51–250 zaměstnanců: vytvoř PŘESNĚ tolik řádků (např. 100 pro „51–100", 250 pro „101–250")
  * 250+ zaměstnanců: vytvoř PŘESNĚ 250 řádků. NE 50, NE 100 — PŘESNĚ 250.
  * Nelze zjistit: vytvoř 30 řádků
- KRITICKÉ: Pokud firma má 250+ zaměstnanců, MUSÍ být 250 řádků.
  Tabulka bude dlouhá — to je SPRÁVNĚ. Po vytištění ji zaměstnanci vyplní.
  NIKDY nezkracuj tabulku. 250 řádků = 250 řádků.
- Sloupce tabulky:
  | č. | Jméno | Příjmení | Podpis |
- Každý řádek očísluj (1, 2, 3, ...).
- Sloupce Jméno, Příjmení a Podpis nech PRÁZDNÉ (klient si je vyplní ručně).
- Buňky pro podpis udělej široké (min 150px) — lidé tam budou podepisovat.
- Nad tabulku přidej hlavičku:
  Název školení: Školení AI gramotnosti dle čl. 4 AI Act
  Datum konání: _______________
  Školitel: _______________
  Místo konání: _______________
- Pod tabulku přidej řádek pro podpis školitele:
  Podpis školitele: _______________  Datum: _______________
"""


def _prompt_chatbot_notices(ctx: str) -> str:
    return f"""{ctx}

═══ DOKUMENT: TEXTY OZNÁMENÍ PRO AI SYSTÉMY ═══

Napiš KOMPLETNÍ dokument s texty oznámení pro AI systémy této firmy.
Celkový rozsah: 500–800 slov. Toto je KRATŠÍ dokument — texty oznámení mají být stručné, jasné a copy-paste ready. Kvalita a přímá použitelnost mají ABSOLUTNÍ přednost.

POVINNÁ STRUKTURA:

<h1>Texty oznámení pro AI systémy</h1>

<h2>1. Právní základ — povinnost transparentnosti</h2>
- Čl. 50 AI Act: povinnost informovat uživatele o interakci s AI
- Čl. 50 odst. 1: systémy určené k přímé interakci s osobami (chatboty, voiceboty)
- Čl. 50 odst. 2: systémy detekující emoce nebo biometrické kategorizace
- Čl. 50 odst. 4: AI-generovaný obsah (deep fakes, syntetický text/obraz/audio)
- .warning box pokud firma má chatbot: „Váš AI chatbot MUSÍ informovat uživatele,
  že komunikují s umělou inteligencí. Toto je ZÁKONNÁ POVINNOST od 2. 8. 2026."

<h2>2. Přehled AI systémů vyžadujících oznámení</h2>
- <table>: AI systém | Typ oznámení | Povinné/Doporučené | Článek AI Act | Kde umístit
- Pro KAŽDÝ nalezený systém firmy rozhodnout jaké oznámení potřebuje
- Rozlišit POVINNÁ (dle AI Act) vs. DOPORUČENÁ (best practice)

<h2>3. Hotové texty oznámení</h2>
Pro KAŽDÝ AI systém firmy vytvořit KONKRÉTNÍ texty:

<h3>3.1 Oznámení pro [konkrétní systém]</h3>
- TEXT pro web banner: přesné znění oznámení
- TEXT pro úvodní zprávu chatbotu (pokud relevantní)
- TEXT pro email footer (pokud relevantní)
- TEXT pro interní upozornění (pokud relevantní)
- Každý text v .callout boxu — připravený ke kopírování

<h3>3.2 Oznámení pro [další systém]</h3>
(opakovat pro každý nalezený systém)

<h2>4. Transparenční stránka — odkaz</h2>
- .info box: „Kompletní HTML transparenční stránka pro váš web je dodána jako
  samostatný dokument v Compliance Kitu (Transparenční stránka). Stránku stačí
  nasadit na URL /ai-transparence na vašem webu."
- Stručně: jak propojit oznámení s transparenční stránkou (odkaz v textu oznámení)
- NEREPLIKUJ obsah transparenční stránky — ten je v samostatném dokumentu

<h2>5. Implementační průvodce</h2>
- KDE přesně oznámení umístit — pro každý typ:
  Web: header/footer/banner/popup
  Chatbot: první zpráva konverzace
  Email: podpis/patička
  Aplikace: splash screen/about page
- KDY zobrazovat: při první interakci vs. trvale
- Technické požadavky: viditelnost, jazyk, přístupnost

<h2>6. Příklady nesprávného a správného oznámení</h2>
- <table> s příklady: ŠPATNĚ vs. SPRÁVNĚ
- Časté chyby: příliš malý text, schovaný v podmínkách, bez odkazu na transparenční stránku

DŮLEŽITÉ:
- Texty oznámení jsou DODÁNY v Compliance Kitu — klient je pouze nasadí
- Každý text musí být KONKRÉTNÍ pro systémy firmy (ne generický)
- Texty musí být v češtině, srozumitelné pro běžného uživatele
"""


def _prompt_ai_policy(ctx: str) -> str:
    return f"""{ctx}

═══ DOKUMENT: INTERNÍ AI POLITIKA ═══

Napiš KOMPLETNÍ Interní AI politiku pro tuto firmu.
Celkový rozsah: 800–1400 slov (cca 4-6 stran A4). Piš jako interní směrnici — EXTRÉMNĚ stručně. Bullet pointy a tabulky místo odstavců.
Toto je formální interní dokument — formát jako vnitřní směrnice firmy.

POVINNÁ STRUKTURA:

<h1>Interní AI politika</h1>
<p><em>Vnitřní směrnice č. [X]/2026</em></p>

<h2>Preambule</h2>
- Proč firma přijímá tuto politiku
- Reference na AI Act (Nařízení (EU) 2024/1689)
- Čl. 4 — AI gramotnost, čl. 5 — zakázané praktiky
- Odkaz na konkrétní AI systémy firmy
- .info box: „Tento dokument je součástí AI Act Compliance Kitu dodaného AIshield.cz.
  Klient jej přebírá jako hotovou šablonu, kterou přizpůsobí interním podmínkám a podepíše."

<h2>1. Účel a rozsah</h2>
- Na koho se vztahuje: všichni zaměstnanci, dodavatelé, subdodavatelé
- Jaké systémy pokrývá: všechny AI systémy dle definice čl. 3 AI Act
- Účinnost od: datum podpisu vedením

<h2>2. Definice</h2>
- AI systém (čl. 3 odst. 1)
- Poskytovatel (čl. 3 odst. 2) vs. Nasazovatel (čl. 3 odst. 4)
- Vysoké riziko, Omezené riziko, Minimální riziko
- Provozovatel, Uživatel, Dotčená osoba

<h2>3. Základní principy</h2>
- Transparentnost — informovat o používání AI
- Odpovědnost — vždy identifikovatelná odpovědná osoba
- Lidský dohled — AI nedělá nevratná rozhodnutí bez kontroly člověka
- Ochrana dat — GDPR compliance při práci s AI
- Nediskriminace — monitorovat bias ve výstupech AI
- Bezpečnost — ochrana dat a systémů

<h2>4. Pravidla pro používání AI</h2>
<h3>4.1 Povolené použití</h3>
- Konkrétní příklady z odvětví firmy
<h3>4.2 Podmíněně povolené použití</h3>
- Vyžaduje schválení nadřízeného/odpovědné osoby
<h3>4.3 Zakázané použití</h3>
- Čl. 5 AI Act: social scoring, subliminal manipulation, real-time biometrics
- Specifická omezení pro firmu: osobní data klientů, právně závazná rozhodnutí bez kontroly
- 2-3 PŘÍKLADY z praxe firmy: „Zaměstnanec NESMÍ..."

<h2>5. Zavedení nového AI systému</h2>
- Schvalovací proces: kdo rozhoduje, jaké podmínky
- Posouzení rizik před nasazením
- Aktualizace registru AI systémů
- DPA/smluvní ošetření s dodavatelem
- Diagram procesu ve formě číslovaného seznamu

<h2>6. Odpovědnosti</h2>
- Vedení firmy: strategie, zdroje, podpis politiky
- Odpovědná osoba za AI: dohled, monitoring, reporting
- Vedoucí oddělení: školení svých lidí, dodržování pravidel
- Každý zaměstnanec: řádné používání AI, hlášení incidentů

<h2>7. Školení a vzdělávání</h2>
- Reference na Plán školení z Compliance Kitu
- „K provedení školení využijte PowerPointovou prezentaci z Compliance Kitu."
- Povinnost proškolení: nástup, změna systémů, roční obnova

<h2>8. Řízení incidentů</h2>
- Postup při incidentu — reference na Plán řízení incidentů z Kitu
- Komu hlásit, jak dokumentovat, čl. 73

<h2>9. Monitoring a audit</h2>
- Reference na Monitoring plán z Compliance Kitu
- Čtvrtletní review, roční audit
- KPI sledování

<h2>10. Sankce za porušení</h2>
- Interní sankce: napomenutí, vytýkací dopis, ukončení pracovního poměru
- Regulatorní: pokuty dle AI Act (čl. 99)

<h2>11. Závěrečná ustanovení</h2>
- Účinnost, revize, odpovědnost za aktualizaci
- Sig-block (.sig-block) pro vedení firmy

DŮLEŽITÉ:
- Formální jazyk vhodný pro interní směrnici (česká administrativa)
- Klient tento dokument PŘEBÍRÁ jako hotový a PODEPÍŠE
- Musí být personalizovaný pro firmu — ne generická šablona
"""


def _prompt_incident_response_plan(ctx: str) -> str:
    return f"""{ctx}

═══ DOKUMENT: PLÁN ŘÍZENÍ INCIDENTŮ S AI ═══

Napiš KOMPLETNÍ Plán řízení incidentů pro tuto firmu.
Celkový rozsah: 700–1100 slov (cca 4-6 stran A4). EXTRÉMNĚ stručně — kroky a tabulky místo odstavců.

POVINNÁ STRUKTURA:

<h1>Plán řízení incidentů s AI systémy</h1>

<h2>1. Účel a rozsah</h2>
- Proč je plán potřeba: čl. 73 AI Act — povinnost hlásit závažné incidenty
- Na co se plán vztahuje: všechny AI systémy provozované firmou
- Tento plán je SOUČÁSTÍ Compliance Kitu — klient ho implementuje do svých procesů

<h2>2. Definice závažného incidentu</h2>
- Dle AI Act čl. 73: smrt nebo vážné poškození zdraví, narušení základních práv,
  významné škody na majetku/životním prostředí
- .callout box: přesná citace definice z AI Act
- 4-5 KONKRÉTNÍCH příkladů incidentů RELEVANTNÍCH PRO ODVĚTVÍ firmy
  (např. pro e-commerce: „Chatbot informuje zákazníka o neexistující akci za 1 Kč")

<h2>3. Klasifikace incidentů</h2>
- <table> s úrovněmi:
  | Úroveň | Závažnost | Příklad | Reakční doba | Eskalace |
  | L1 — Nízká | Operativní chyba | Chatbot odpovídá nepřesně | Do 24h | Operátor |
  | L2 — Střední | Opakované chyby/stížnosti | Bias ve výstupech, data leak | Do 4h | Odpovědná osoba |
  | L3 — Vysoká | Závažný incident dle čl. 73 | Škoda na zdraví/právech | Ihned | Vedení + regulátor |

<h2>4. Reakční postupy</h2>
<h3>4.1 L1 — Operativní incident</h3>
- Krok za krokem: detekce → izolace → oprava → dokumentace
- Kdo zodpovídá, co přesně udělat
- Příklad scénáře pro firmu

<h3>4.2 L2 — Střední incident</h3>
- Krok za krokem: detekce → eskalace → analýza → náprava → follow-up
- Odpovědná osoba za AI přebírá řízení
- Kill switch rozhodnutí: kdy AI systém vypnout

<h3>4.3 L3 — Závažný incident</h3>
- Krok za krokem: okamžité opatření → izolace → nahlášení (15 dní!) → vyšetřování → náprava
- Nahlášení dozorčímu orgánu (čl. 73) do 15 dnů
- Komunikační plán: interní, externí, média
- Uchování důkazů a logů (čl. 12 + čl. 19 — min. 6 měsíců)

<h2>5. Eskalační matice</h2>
- <table>: Typ incidentu | L1 kontakt | L2 kontakt | L3 kontakt | Externí kontakt
- Telefonní/emailové kontakty (placeholder pro vyplnění klientem)
- .warning box: „NAHLÁŠENÍ ZÁVAŽNÉHO INCIDENTU DOZORČÍMU ORGÁNU DO 15 DNÍ (čl. 73 AI Act)"

<h2>6. Dokumentace incidentů</h2>
- Co zaznamenat: datum, čas, systém, popis, dopad, opatření, follow-up
- Šablona záznamu (formulář v tabulce)
- Kde uchovávat záznamy
- Doba uchovávání: min. 6 měsíců (čl. 19)

<h2>7. Prevence a poučení</h2>
- After-action review po každém incidentu
- Aktualizace postupů na základě zkušeností
- Sdílení poznatků v rámci firmy

<h2>8. Kontaktní seznam</h2>
- Tabulka pro vyplnění klientem: Role | Jméno | Telefon | Email
- .info box: „Vyplňte kontaktní údaje odpovědných osob ve vaší firmě."

DŮLEŽITÉ:
- Plán je DODÁN v Compliance Kitu — klient ho přizpůsobí své organizaci
- Příklady incidentů musí být SPECIFICKÉ pro odvětví firmy
- Zmínit zákonnou lhůtu 15 dní pro nahlášení (čl. 73) — informativně, bez tlaku
"""


def _prompt_dpia_template(ctx: str) -> str:
    return f"""{ctx}

═══ DOKUMENT: POSOUZENÍ DOPADŮ (DPIA/FRIA) ═══

Napiš KOMPLETNÍ Posouzení dopadů na základní práva pro tuto firmu.
Celkový rozsah: 700–1100 slov (cca 4-6 stran A4). EXTRÉMNĚ stručně — tabulky a hodnocení místo odstavců.

POVINNÁ STRUKTURA:

<h1>Posouzení dopadů na základní práva — DPIA/FRIA</h1>

<h2>1. Úvod a právní základ</h2>
- Kombinace AI Act čl. 27 (FRIA) s GDPR čl. 35 (DPIA)
- Kdy je FRIA povinné: čl. 27 — nasazovatelé vybraných high-risk systémů
- Kdy je DPIA povinné: zpracování osobních údajů přes AI
- .info box: „Tento dokument kombinuje posouzení dle AI Act (FRIA) s posouzením dle GDPR (DPIA)
  a je dodán jako součást Compliance Kitu."

<h2>2. Popis AI systémů firmy</h2>
- Pro KAŽDÝ nalezený systém:
  - Účel zpracování / nasazení
  - Jaká data systém zpracovává
  - Skupiny dotčených osob: zákazníci, zaměstnanci, veřejnost
  - Rozsah zpracování: počet dotčených osob, frekvence, zeměpisný rozsah

<h2>3. Posouzení nutnosti a přiměřenosti</h2>
- Je AI systém nezbytný pro daný účel?
- Existují méně invazivní alternativy?
- Je rozsah zpracování přiměřený účelu?
- Pro KAŽDÝ systém firmy odpovědět na tyto otázky

<h2>4. Identifikace rizik pro základní práva</h2>
Pro KAŽDÝ systém posoudit dopad na:
- Právo na soukromí a ochranu osobních údajů (GDPR + čl. 8 LZPS)
- Právo na nediskriminaci (bias ve výstupech AI)
- Právo na vysvětlení rozhodnutí (čl. 86 AI Act)
- Právo na lidský přezkum (čl. 14 AI Act)
- Právo na efektivní opravné prostředky
- <table>: Riziko | Pravděpodobnost | Závažnost | Celkové skóre
  Hodnotit: Nízká/Střední/Vysoká pro každé

<h2>5. Opatření ke zmírnění rizik</h2>
- Pro KAŽDÉ identifikované riziko navrhnout opatření
- Rozlišit:
  <strong>Zajištěno Compliance Kitem:</strong> dokumentace, šablony, doporučení
  <strong>Vyžaduje akci klienta:</strong> technická implementace, smluvní opatření, organizační změny
- <table>: Riziko | Opatření | Zodpovědnost | Stav | Zbytková rizikovost

<h2>6. Zpracování osobních údajů přes AI</h2>
- Na základě dat z dotazníku: zpracovává firma osobní údaje přes AI?
- Pokud ANO: GDPR compliance opatření, DPA s dodavateli, informační povinnost
- Specifické požadavky pro odvětví firmy

<h2>7. Konzultace s dotčenými subjekty</h2>
- Doporučení: zapojit zaměstnance, zákazníky, odbory (pokud relevantní)
- Postup konzultace

<h2>8. Závěr a doporučení</h2>
- Celkové hodnocení: jsou rizika přijatelná po implementaci opatření?
- Zbytková rizika
- Podmínky pro pokračování v provozu AI systémů
- Datum příštího přezkumu
- Sig-block

DŮLEŽITÉ:
- Posouzení musí být SPECIFICKÉ pro systémy firmy — ne obecné
- Rizika hodnotit realisticky — ne vše je vysoké riziko
- U každého opatření uvést kdo zodpovídá a konkrétní příklad implementace
"""


def _prompt_vendor_checklist(ctx: str) -> str:
    return f"""{ctx}

═══ DOKUMENT: DODAVATELSKÝ CHECKLIST ═══

Napiš KOMPLETNÍ Dodavatelský checklist pro tuto firmu.
Celkový rozsah: 500–800 slov. EXTRÉMNĚ stručně — tabulkové checklisty, žádné odstavce.

POVINNÁ STRUKTURA:

<h1>Dodavatelský kontrolní list — hodnocení poskytovatelů AI</h1>

<h2>1. Úvod</h2>
- Čl. 25-26 AI Act: povinnosti nasazovatelů vůči poskytovatelům
- Due diligence jako zákonná povinnost
- .info box: „Tento checklist je součástí Compliance Kitu. Použijte ho pro
  systematické hodnocení KAŽDÉHO dodavatele AI systémů ve vaší firmě."

<h2>2. Přehled dodavatelů AI</h2>
- <table>: Dodavatel/Systém | Kategorie | Riziko | Smluvní vztah | DPA podepsáno?
- REÁLNÍ dodavatelé z kontextu firmy

<h2>3. Hodnocení jednotlivých dodavatelů</h2>
Pro KAŽDÝ detekovaný AI systém / dodavatele:
<h3>3.X Hodnocení: [Název systému/dodavatele]</h3>

<table> s hodnotícími kritérii:
| Kritérium | Otázka | Odpověď | Riziko |
| Transparentnost | Poskytuje dodavatel technickou dokumentaci dle AI Act? | | |
| Data | Kde se data zpracovávají (EU/mimo EU)? | | |
| Trénování | Trénuje se model na datech klienta? Existuje opt-out? | | |
| DPA | Je podepsána smlouva o zpracování osobních údajů (GDPR)? | | |
| SLA | Jaké jsou garance dostupnosti a výkonu? | | |
| Certifikace | Má dodavatel ISO 27001, SOC 2, nebo jiné certifikace? | | |
| EU AI Act compliance | Deklaruje dodavatel soulad s AI Act? | | |
| Exit strategie | Je možné data exportovat a systém nahradit? | | |

<h2>4. Vzorové dotazy pro dodavatele</h2>
- 10-15 KONKRÉTNÍCH otázek pro email/schůzku s dodavatelem
- Pro KAŽDOU otázku vysvětlit PROČ je důležitá
- .callout box: Vzorový email dodavateli:
  „Vážený poskytovateli, v rámci plnění EU AI Act (Nařízení 2024/1689)
  potřebujeme ověřit následující informace o vašem AI systému [název]:
  1. Kde jsou data zpracovávána? 2. Trénuje se model na našich datech?..." atd.

<h2>5. Smluvní požadavky</h2>
- Co musí obsahovat smlouva s AI dodavatelem:
  - DPA (GDPR Article 28)
  - Transparenční povinnosti dodavatele
  - SLA a dostupnost
  - Odpovědnost za chyby AI
  - Exit strategie a portabilita dat
  - Compliance s AI Act
- Reference: čl. 25-26 AI Act povinnosti v dodavatelském řetězci

<h2>6. Akční doporučení</h2>
- Pro KAŽDÉHO dodavatele konkrétní doporučení: co udělat, priorita, urgence
- .warning pro dodavatele bez DPA

<h2>7. Kontrolní tabulka</h2>
- Souhrnná tabulka: Dodavatel | Všechna kritéria splněna? | Akce potřeba? | Deadline

DŮLEŽITÉ:
- Checklist je DODÁN jako hotový nástroj v Compliance Kitu
- Klient ho musí SÁM vyplnit a kontaktovat dodavatele
- AIshield nemůže vstupovat do smluvních vztahů klienta
- Vyplň co je známo z analýzy, zbytek nechej k doplnění klientem
"""


def _prompt_monitoring_plan(ctx: str) -> str:
    return f"""{ctx}

═══ DOKUMENT: MONITORING PLÁN AI SYSTÉMŮ ═══

Napiš KOMPLETNÍ Monitoring plán pro tuto firmu.
Celkový rozsah: 600–1000 slov (cca 4-6 stran A4). EXTRÉMNĚ stručně — metriky a tabulky místo textu.

POVINNÁ STRUKTURA:

<h1>Monitoring plán AI systémů</h1>

<h2>1. Účel a právní základ</h2>
- Čl. 12 AI Act: automatické logging schopnosti
- Čl. 19 odst. 1: uchovávání logů min. 6 měsíců
- Čl. 9: risk management systém pro high-risk AI
- .info box: „Tento monitoring plán je součástí Compliance Kitu. Implementujte ho
  do svých IT procesů — AIshield nemůže přistupovat k vašim interním systémům."

<h2>2. Přehled monitorovaných AI systémů</h2>
- <table>: AI systém | Kategorie rizika | Frekvence monitoringu | Zodpovědná osoba
- Doporučená frekvence dle rizika:
  High-risk: týdně | Limited: měsíčně | Minimal: kvartálně

<h2>3. KPI metriky pro monitoring</h2>
- Pro KAŽDÝ AI systém definovat měřitelné metriky:
<h3>3.X Metriky: [Název systému]</h3>
<table>:
| KPI | Popis | Cílová hodnota | Jak měřit | Frekvence |
| Přesnost výstupů | % správných odpovědí/výstupů | >90% | Namátková kontrola | Týdně |
| False positive rate | % falešně pozitivních | <5% | Logging analýza | Měsíčně |
| Eskalace na člověka | Počet eskalací | Trend klesající | Ticket systém | Týdně |
| Doba odpovědi | Latence AI systému | <2s | Monitoring nástroj | Průběžně |
| Stížnosti uživatelů | Počet stížností na AI | Trend klesající | Support systém | Měsíčně |
| Bias skóre | Rovnoměrnost výstupů napříč skupinami | Variace <10% | Auditní kontrola | Kvartálně |

<h2>4. Praktický monitoring — jak na to</h2>
- .callout box s KONKRÉTNÍM příkladem:
  „Jednou týdně zkontrolujte 10 náhodných odpovědí chatbotu:
  1. Otevřete historii konverzací
  2. Vyberte náhodně 10 konverzací z uplynulého týdne
  3. Zkontrolujte: Byla odpověď správná? Relevantní? Bez diskriminace?
  4. Zaznamenejte výsledek: X z 10 správných
  5. Pokud <8 z 10 → eskalujte na odpovědnou osobu"
- Podobný příklad pro KAŽDÝ systém firmy

<h2>5. Logging a evidence</h2>
- Co logovat: vstup, výstup, čas, uživatel, verze modelu
- Kde ukládat logy: doporučení (ne u dodavatele, vlastní storage pokud možno)
- Jak dlouho: min. 6 měsíců (čl. 19)
- Přístupová práva k logům

<h2>6. Eskalační pravidla</h2>
- Kdy eskalovat: KPI mimo cílovou hodnotu, opakované chyby, stížnosti
- Kam: odpovědná osoba za AI, vedení
- Reference na Plán řízení incidentů z Compliance Kitu

<h2>7. Výkaznictví a hlášení</h2>
- Měsíční report: kdo připravuje, co obsahuje, komu se předkládá
- Šablona reportu (tabulka)
- Roční souhrnný report pro vedení

<h2>8. Revize a aktualizace</h2>
- Čtvrtletní review monitorovacích metrik
- Roční aktualizace plánu
- Podmínky mimořádné revize: nový systém, incident, legislativní změna

DŮLEŽITÉ:
- Plán je DODÁN v Compliance Kitu — klient implementuje do svých procesů
- KPI musí být MĚŘITELNÉ a KONKRÉTNÍ pro systémy firmy
- Příklady monitoring aktivit musí být srozumitelné pro laika
"""


def _prompt_transparency_human_oversight(ctx: str) -> str:
    return f"""{ctx}

═══ DOKUMENT: TRANSPARENTNOST A LIDSKÝ DOHLED ═══

Napiš KOMPLETNÍ dokument o transparentnosti a lidském dohledu pro tuto firmu.
Celkový rozsah: 700–1100 slov (cca 4-6 stran A4). EXTRÉMNĚ stručně a prakticky — tabulky místo textu.

POVINNÁ STRUKTURA:

<h1>Transparentnost a lidský dohled nad AI systémy</h1>

<h2>1. Právní rámec</h2>
- Čl. 13 AI Act: transparentnost pro high-risk AI — technická dokumentace, návod k použití
- Čl. 14 AI Act: lidský dohled — kill switch, override, monitoring
- Čl. 50 AI Act: informování uživatelů o interakci s AI
- Čl. 18 AI Act: archivace dokumentace — po dobu provozu + 10 let
- Jak se tyto články vztahují NA KONKRÉTNÍ systémy firmy

<h2>2. Přehled požadavků na transparentnost</h2>
- <table>: AI systém | Čl. 50 povinné? | Čl. 13 povinné? | Čl. 14 povinné? | Opatření
- Pro KAŽDÝ systém firmy vyhodnotit které články se aplikují

<h2>3. Transparenční opatření — per systém</h2>
Pro KAŽDÝ AI systém firmy:
<h3>3.X Transparentnost: [Název systému]</h3>
- Jaká oznámení jsou potřeba (reference na dokument Texty oznámení z Kitu)
- Kde a jak oznámení implementovat
- Technická dokumentace: co musí být k dispozici
- Srozumitelnost pro koncového uživatele

<h2>4. Lidský dohled — opatření</h2>
<h3>4.1 Kill switch — nouzové vypnutí</h3>
- Pro KAŽDÝ AI systém: existuje možnost okamžitého vypnutí?
- Kdo má pravomoc vypnout AI systém
- Za jakých podmínek (reference na Plán řízení incidentů z Kitu)
- Technická implementace: přístupové právo, postup

<h3>4.2 Human override — lidský přezkum</h3>
- Které výstupy AI MUSÍ být zkontrolovány člověkem
- Kdo kontroluje (odpovědná osoba, operátor, vedoucí)
- Frekvence kontrol (reference na Monitoring plán z Kitu)

<h3>4.3 Kompetence dohledové osoby</h3>
- Požadavky na kvalifikaci (AI gramotnost, čl. 4)
- Školení (reference na Plán školení z Kitu)
- Pravomoci a odpovědnosti

<h2>5. Čtvrtletní kontrola transparentnosti a dohledu</h2>
- Záznamový formulář (checklist):
<table>:
| Kontrolní bod | Otázka | ANO/NE | Poznámka |
| Oznámení aktivní | Jsou všechna AI oznámení na webu viditelná? | | |
| Transparenční stránka | Je stránka aktuální a přístupná? | | |
| Kill switch funkční | Byl kill switch otestován? | | |
| Registr aktuální | Jsou všechny AI systémy v registru? | | |
| Logy uchovávány | Jsou logy za posledních 6 měsíců dostupné? | | |
| Monitoring aktivní | Probíhá monitoring dle plánu? | | |
| Stížnosti řešeny | Byly stížnosti na AI řešeny? | | |
- .info box: „Tuto kontrolní tabulku vyplňujte čtvrtletně a archivujte ji."

<h2>6. Archivace a evidence</h2>
- Čl. 18 AI Act: archivace po dobu provozu + 10 let
- Co archivovat: záznamy o transparentnosti, kontrolní listy, logy dohledu
- Kde a jak archivovat
- Přístupová pravidla

<h2>7. Doporučení pro firmu</h2>
- Shrnutí konkrétních kroků, které klient musí udělat
- Reference na relevantní dokumenty z Compliance Kitu
- Sig-block

DŮLEŽITÉ:
- Dokument je DODÁN v Compliance Kitu včetně čtvrtletního kontrolního formuláře
- Klient musí SÁM implementovat opatření do svých systémů a procesů
- Konkrétní příklady pro KAŽDÝ AI systém firmy
"""


# ══════════════════════════════════════════════════════════════════════
# TRANSPARENCY PAGE — standalone HTML stránka pro web klienta
# ══════════════════════════════════════════════════════════════════════

def _prompt_transparency_page(ctx: str) -> str:
    return f"""KONTEXT FIRMY:
{ctx}

=== TVŮJ ÚKOL ===
Vygeneruj KOMPLETNÍ standalone HTML transparenční stránku pro web KLIENTA.
Stránka se umístí na web klienta (typicky /ai-transparence).

PRÁVNÍ RÁMEC (MUSÍŠ DODRŽET):
Toto je DOBROVOLNÉ prohlášení o využívání AI — nadstandardní opatření.
Článek 50 AI Act NEVYŽADUJE centralizovanou webovou stránku se seznamem
všech AI systémů. Čl. 50 vyžaduje konkrétní oznámení v konkrétních situacích:
- Chatbot/voicebot → oznámení při první interakci ("Komunikujete s AI")
- Deepfake/AI obsah → označení jako AI-generovaný
- Rozpoznávání emocí/biometrie → informování dotčených osob
Proto tuto stránku PREZENTUJ jako "Dobrovolné prohlášení o transparentním
využívání AI" — NIKDY jako zákonem vyžadovanou povinnost v tomto formátu.

NEBALÍ výstup do markdown bloku. Piš přímo HTML.

=== KRITICKÉ ZÁKAZY ===
1. NIKDY nezmiňuj článek 5 AI Act (zakázané praktiky) — ani slovo
   o "pozastavených systémech", "zakázaných praktikách", "sociálním
   skóringu" nebo "rozpoznávání emocí na pracovišti" na veřejné stránce.
   Toto patří VÝHRADNĚ do interní dokumentace.

2. NIKDY neuváděj systémy, které firma NEMÁ v kontextu. Používej POUZE
   systémy z "DEKLAROVANÉ AI SYSTÉMY" a "NALEZENÉ AI SYSTÉMY".
   Nevymýšlej žádné další.

3. NIKDY neuváděj nerealistické počty. Pokud je firma malá (1-50 lidí),
   nemůže mít 17 vysokorizikových systémů. Buď realistický.

4. NIKDY nekombinuj role Provider a Deployer — pokud firma POUŽÍVÁ
   LinkedIn Recruiter, je Deployer, NE Provider. Provider je ten, kdo
   systém vyvinul (Microsoft/LinkedIn). Toto rozlišení musí být správné.

5. NIKDY neuváděj interní audit informace na veřejné stránce.
   FRIA, DPIA, CE certifikace — to patří do interních dokumentů,
   ne na marketingový web.

6. ŽÁDNÉ anglické nadpisy — vše česky.

=== A) <head> — NEVIDITELNÁ METADATA ===

1. HTML komentáře:
   <!-- ai-content-declaration: Tato stránka byla vygenerována platformou AIshield.cz -->
   <!-- ai-summary: Transparenční stránka [FIRMA] o využití AI dle AI Act -->

2. Meta tagy:
   - <title>Jak využíváme umělou inteligenci — [FIRMA]</title>
   - meta description, robots: index,follow, keywords, author = klient

3. Dublin Core (15 tagů) — DC.creator=klient, DC.contributor=AIshield.cz

4. Open Graph + Twitter Card

5. JSON-LD (DŮLEŽITÉ):
   a) WebPage: publisher=klient, datePublished
   b) FAQPage: 4-5 otázek (Jaké AI používáte? Jak chráníte data? atd.)
   c) Organization: klientova firma
   d) BreadcrumbList: Domů > Transparence AI
   e) Vnořený Organization: AIshield.cz jako "provider" služby

6. link rel=canonical href=/ai-transparence

=== B) <style> — CSS PŘIZPŮSOBENÉ KLIENTOVI ===
EXTRÉMNĚ DŮLEŽITÉ: Stránka MUSÍ vizuálně sedět na web klienta.

V kontextu najdeš sekci "BRAND BARVY" s extrahovanými barvami z webu klienta.
Použij tyto barvy jako základ CSS:
- --ait-primary → primární barva klienta (pro nadpisy, akcentní prvky)
- --ait-secondary → sekundární barva
- --ait-bg → barva pozadí (obvykle bílá/světlá)
- --ait-text → barva textu
- --ait-accent → akcentní barva (odkazy, tlačítka)

Pokud jsou brand barvy "default", použij neutrální profesionální paletu:
- Tlumené modré/šedé tóny, bílé pozadí, tmavý text

CSS pravidla:
- Prefix .ait-* pro všechny třídy (aby nenarazily na CSS klienta)
- Responzivní, max-width: 720px
- Čitelné na mobilu
- Žádné animace, žádné obrázky
- Profesionální a čistý design
- Zaoblené rohy (4-8px), jemné stíny
- ARIA labels pro přístupnost, kontrast > 4.5:1

=== C) <body> — VIDITELNÝ OBSAH ===
MAX 300-500 slov. Stránka MUSÍ být krátká, přehledná, pozitivní.
Tón: profesionální, vstřícný, srozumitelný běžnému člověku.
Žádný právní žargon, žádné paragrafy v textu (jen v metadatech).

STRUKTURA:

1. HLAVIČKA:
   <h1>Jak využíváme umělou inteligenci</h1>
   (BEZ "Nařízení EU 2024/1689" — to je pro běžného čtenáře nesrozumitelné)
   2-3 věty: "[Firma] využívá umělou inteligenci zodpovědně a transparentně.
   Na této stránce informujeme o AI systémech, které používáme,
   a o vašich právech."

2. KDE POTKÁTE AI (nejdůležitější sekce — splnění čl. 50):
   Toto je klíčová sekce. Pro KAŽDÝ systém, kde člověk přímo interaguje s AI:
   a) "Chatbot na webu" → "Na našem webu používáme AI chatbota [název].
      Při zahájení konverzace jste vždy informováni, že komunikujete s AI.
      Kdykoli můžete požádat o přepojení na živého člověka."
   b) "AI generovaný obsah" → "Některé texty a materiály na našem webu
      využívají AI. Vždy probíhá lidská kontrola finálního obsahu."
   c) Další relevantní interakce z kontextu.
   POUZE systémy z kontextu. NIKDY nevymýšlej.

3. PŘEHLED AI SYSTÉMŮ (krátká tabulka):
   | Systém | K čemu slouží (1 věta) | Kategorie |
   - Kategorie: "Vysoké riziko", "Omezené riziko", "Minimální riziko"
   - SESKUPUJ podle účelu: "Náborové nástroje (LinkedIn, Teamio, ...)"
     místo individuálních řádků pro každý API.
   - MAX 8-12 řádků tabulky. Seskupuj příbuzné systémy.
   - Žádné citace článků AI Act v tabulce.
   - Jako "deployer" (nasazovatel) neuvádíme technickou dokumentaci
     providera — pouze informujeme o využití.

4. VAŠE PRÁVA (4-5 odrážek, srozumitelný jazyk):
   - Právo vědět, že komunikujete s AI
   - Právo na lidský přezkum automatizovaného rozhodnutí
   - Právo na vysvětlení, jak AI dospěla k výsledku
   - Právo podat stížnost (kontakt + ČOI jako dozorový orgán)
   - Právo požádat o další informace

5. KONTAKT (1-2 řádky):
   Odpovědná osoba: [jméno] | [email] | [telefon]
   "Pro dotazy ohledně AI nás kontaktujte na výše uvedeném kontaktu."

6. ZÁPATÍ:
   Poslední aktualizace: [datum] | IČO: [IČO]
   <small>Prohlášení vygenerováno platformou
   <a href="https://www.aishield.cz?utm_source=transparency&utm_medium=referral&utm_campaign=client_page"
      rel="dofollow" target="_blank">AIshield.cz</a></small>

=== TEXT NESMÍ OBSAHOVAT ===
- Emoji, anglické fráze
- Článek 5 AI Act, zakázané praktiky, self-incrimination
- Interní audit údaje (FRIA, DPIA, CE certifikace)
- Nerealistické počty systémů
- Detailní právní citace v textu (jen v metadatech)
- Časové termíny a ultimáta
- Slova jako "audit", "compliance", "posouzení shody"
- Jakýkoli viditelný text o AIshield.cz MIMO zápatí

=== CELKOVÝ ROZSAH ===
<head> metadata: bohatý SEO/GEO — JSON-LD, Dublin Core, OpenGraph.
<body> viditelný text: MAX 300-500 slov. Pozitivní, vstřícný tón.
Celý HTML soubor: max 8000-12000 znaků (vč. metadat).
"""


# TRAINING PRESENTATION — obsah slidů pro PPTX prezentaci
# ══════════════════════════════════════════════════════════════════════

def _prompt_training_presentation(ctx: str) -> str:
    return f"""KONTEXT FIRMY:
{ctx}

TVŮJ ÚKOL:
Vygeneruj obsah školící prezentace o AI gramotnosti (čl. 4 AI Act).
Prezentace bude automaticky převedena do PowerPoint (PPTX).

═══ ZÁSADNÍ PRAVIDLA STYLU ═══

1. PIŠ LIDSKY, NE PRÁVNICKY. Představ si, že mluvíš k běžným zaměstnancům
   v kanceláři. Žádné „dle článku XY“, žádné paragrafové odkazy v odrážkách.
   Články zákona patří do speaker notes pro přednášejícího, NE na slide.

2. MAX 5–6 ODRÁŽEK NA SLIDE. Každá odrážka max 12–15 slov.
   Pokud máš víc bodů, rozděl na dva slidy.

3. KAŽDÝ SLIDE = 1 MYŠLENKA. Nemíchej témata. Raději udělej víc slidů
   než narvat všechno do jednoho.

4. PŘÍKLADY > DEFINICE. Místo „AI = stroj který...“ napiš
   „Když vám Netflix doporučí film — to je AI.“

5. KONKRÉTNÍ > OBECNÉ. Vždycky uváděj příklad z praxe firmy
   nebo z běžného života. Žádné akademické definice.

6. KRÁTKÁ SLOVA. Používej „musíme“ místo „jsme povinni dle nařízení“.
   „Pozor na“ místo „Je nezbytné věnovat pozornost“.

═══ FORMÁT HTML ═══

- Každý slide = <h2>Nadpis slidu</h2> + <ul><li>...</li></ul>
- Začni <h1> tagem s názvem prezentace
- KAŽDÝ slide MUSÍ mít <div class='speaker-notes'>...</div>
  (2–4 věty pro přednášejícího — sem patří čísla článků a detaily)

═══ STRUKTURA — 18–24 SLIDŮ ═══

<h1>AI ve firmě [Firma] — co potřebujete vědět</h1>

<h2>Slide 1: Titulní</h2>
<p>Školení AI gramotnosti pro [Firma]</p>
<p>[odvětví] | [velikost firmy]</p>

<h2>Slide 2: O čem dnes bude řeč</h2>
- 5–6 krátkých bodů agendy (bez minutáže!)
- Napiš je lidsky: „Co je AI a kde ji potkáváte“, „Na co si dát pozor“

<h2>Slide 3: Proč jsme tady</h2>
- 3–4 body: zákon to vyžaduje, firma používá AI, musíme vědět jak bezpečně
- Speaker notes: zde uvést čl. 4 AI Act a pokuty

<h2>Slide 4: Co je AI — jednoduše</h2>
- 3–4 odrážky s PŘÍKLADY z běžného života (NE definice!)
- Např.: „Když Google dokončí vaši větu — to je AI“
- „Když banka zablokuje podezřelou platbu — to je AI“

<h2>Slide 5: Kde všude potkáváte AI</h2>
- 5–6 příkladů z každodenního života (navigace, překlad, filtry, doporučení)
- Pointa: AI je všude kolem nás, není to sci-fi

<h2>Slide 6: Proč EU začala AI regulovat</h2>
- 3–4 body: ochrana lidí, férovost, bezpečnost
- Příklad: „AI v náboru diskriminovala ženy“ (Amazon 2018)
- „AI rozpoznávání obličejů mělo problém s tmavou pletí“
- Speaker notes: zde vysvětlit EU AI Act podrobněji

<h2>Slide 7: 4 úrovně rizika AI</h2>
- POUZE 4 krátké řádky, každý s jedním příkladem:
  „[CERVENA] Zakázané — např. bodování lidí podle chování“
  „[ORANZOVA] Vysoké riziko — např. AI výběr zaměstnanců“
  „[ZLUTA] Omezené — např. chatbot na webu“
  „[ZELENA] Minimální — např. spamový filtr“

<h2>Slide 8: Co nesmíme dělat</h2>
- 4–5 zakázaných věcí LIDSKÝM JAZYKEM:
  „Hodnotit lidi podle chování na sociálních sítích“
  „Používat AI k manipulaci lidí“
  „Skenovat obličeje zaměstnanců bez souhlasu“
- Speaker notes: zde uvést čl. 5 a pokuty

<h2>Slide 9: Jaké AI nástroje používáme</h2>
- PERSONALIZUJ z kontextu firmy
- Max 5–6 hlavních AI nástrojů s KRATŠÍM popisem co dělají
  Např.: „ChatGPT — pomáhá psát emaily a texty“
  „Google Analytics — analyzuje návštěvnost webu“
- Pokud je víc než 6 nástrojů, rozděl na 2 slidy

<h2>Slide 10: Rizikový profil našich AI systémů</h2>
- Tabulkový formát: název | účel | riziko (barva)
- MAX 8 položek na slide. Přesahuje? → další slide!
- U každého nástroje STRUČNĚ co dělá a proč má danou kategorii
- Pokud <table> — použij <tr><td> formát

<h2>Slide 11: Největší past — slepá důvěra v AI</h2>
- Vysvětli automation bias JEDNODUŠE: „AI říká něco → my tomu věříme“
- 2–3 KONKRÉTNÍ příklady z odvětví firmy
- Např.: „AI napíše smlouvu s neexistujícím paragrafem“
- „AI vypočítá cenu špatně — a vy ji pošlete klientovi“

<h2>Slide 12: 5 zlatých pravidel pro AI</h2>
- PŘESNĚ 5 krátkých pravidel:
  1. Nedávej do AI osobní údaje
  2. Nedávej do AI hesla a interní dokumenty
  3. Vždycky ověř důležité výstupy
  4. Řekni, že text psála AI
  5. Nevíš? Zeptej se [odpovědné osoby]

<h2>Slide 13: Co do AI NIKDY nedávat</h2>
- 4–5 konkrétních příkladů (ne kategorií!):
  „Jméno a adresu klienta“
  „Interní smlouvy a cenové nabídky“
  „Přístupové údaje do systémů“
- PERSONALIZUJ pro odvětví firmy

<h2>Slide 14: AI a osobní údaje</h2>
- 4 body JEDNODUŠE:
  „AI pracuje s daty — platí GDPR“
  „Do AI dávejte jen to, co je nutné“
  „Každý má právo vědět, že o něm rozhoduje AI“
  „Pokud AI rozhoduje o lidech — musí to jít zkontrolovat“
- Speaker notes: čl. 22 GDPR, DPIA detaily

<h2>Slide 15: Kdy musíme říct, že používáme AI</h2>
- 3–4 situace:
  „Chatbot na webu — musí být označený“
  „Texty psané pomocí AI — upřesnit pokud jdou ven“
  „AI-generované obrázky/videa — označit“
- Transparenční stránka na webu (součást Kitu)

<h2>Slide 16: Kdo je za AI odpovědný</h2>
- PERSONALIZUJ: jméno answeré osoby z kontextu
- Role nasazovatele vs. poskytovatele JEDNODUŠE:
  „My AI používáme — jsme nasazovatel“
  „OpenAI/Google AI vyvíjí — oni jsou poskytovatel“
  „Oba máme povinnosti, ale různé“

<h2>Slide 17: Co když se něco pokazí</h2>
- Postákuček při AI incidentu:
  1. ZASTAVIT — přestat AI používat
  2. ZAPSAT — co se stalo, kdy, kde
  3. NAHÁSIT — komu (jméno/email z kontextu)
- Příklad: „AI poslala špatné údaje klientovi“

<h2>Slide 18: Jak na tom jsme</h2>
- PERSONALIZUJ checklist ze stavu firmy:
  ✅/⚠ u každé položky (max 5–6)
  Školení, registr AI, transparentnost, incident plán, AI politika
- Speaker notes: co už je hotovo díky Kitu

<h2>Slide 19: Co si zapamatovat</h2>
- MAX 4–5 bodů, každý 1 věta:
  „AI nám pomáhá, ale musíme jí rozumět“
  „Nikdy do AI nedávej citlivé údaje“
  „Vždycky ověř důležité výstupy“
  „Pokud si nejsi jistý — zeptej se“

<h2>Slide 20: Co dělat dál</h2>
- 3–4 body:
  „Opakujeme 1× ročně“
  „Nový AI nástroj? Hlaš odpovědné osobě“
  „Problém s AI? Postupuj dle plánu“
  „Kontakt: [jméno, email z kontextu]“

<h2>Slide 21: Děkujeme</h2>
<p>Vytvořeno platformou AIshield.cz</p>
<p>Tento materál slouží jako vzdělávácí pomůcka, není právní poradenství.</p>

═══ PERSONALIZACE ═══
- POVINNĚ personalizuj slidy 9, 10, 11, 13, 16, 17, 18 z dat firmy
- Pokud firma má oversight osobu → jméno a email na slidy 12, 16, 17, 20
- Příklady z odvětví firmy — NE obecné akademické

═══ SPEAKER NOTES ═══
- KAŽDÝ slide MUSÍ mít <div class='speaker-notes'>...</div>
- Do speaker notes patří: čísla článků zákona, pokuty, technické detaily
- Piš jako mluvené slovo — co říct publiku
- 2–4 věty na slide

═══ STRIKTNĚ ZAKÁZÁNO ═══
- Více než 6 odrážek na slide
- Odrážky delší než 15 slov
- Právnický žargon na slidech (patří do speaker notes)
- „V dnešní digitální době“ a podobná klišé
- Obecné statistiky bez vztahu k firmě
- Emoji (kromě ✅ a ⚠ pro stav povinností na slide 18 a barevné kolečka na slide 7)
- Zmínky o testech, kvízech nebo certifikacích (AIshield je neposkytuje)
- Odkazování na články zákona PŘÍMO v odrážkách slidů (patří do speaker notes)
"""

# ══════════════════════════════════════════════════════════════════════
# PROMPT REGISTRY — mapování doc_key → prompt builder
# ══════════════════════════════════════════════════════════════════════

PROMPT_BUILDERS = {
    "compliance_report":            _prompt_compliance_report,
    "action_plan":                  _prompt_action_plan,
    "ai_register":                  _prompt_ai_register,
    "training_outline":             _prompt_training_outline,
    "chatbot_notices":              _prompt_chatbot_notices,
    "ai_policy":                    _prompt_ai_policy,
    "incident_response_plan":       _prompt_incident_response_plan,
    "dpia_template":                _prompt_dpia_template,
    "vendor_checklist":             _prompt_vendor_checklist,
    "monitoring_plan":              _prompt_monitoring_plan,
    "transparency_human_oversight": _prompt_transparency_human_oversight,
    "transparency_page":            _prompt_transparency_page,
    "training_presentation":        _prompt_training_presentation,
}

DOCUMENT_NAMES = {
    "compliance_report":            "Compliance Report",
    "action_plan":                  "Akční plán",
    "ai_register":                  "Registr AI systémů",
    "training_outline":             "Plán školení",
    "chatbot_notices":              "Texty oznámení",
    "ai_policy":                    "Interní AI politika",
    "incident_response_plan":       "Plán řízení incidentů",
    "dpia_template":                "Posouzení dopadů (DPIA/FRIA)",
    "vendor_checklist":             "Dodavatelský checklist",
    "monitoring_plan":              "Monitoring plán",
    "transparency_human_oversight": "Transparentnost a lidský dohled",
    "transparency_page":            "Transparenční stránka (HTML)",
    "training_presentation":        "Školící prezentace (PPTX)",
}


# ══════════════════════════════════════════════════════════════════════
# GENERATE DRAFT — hlavní vstupní bod modulu
# ══════════════════════════════════════════════════════════════════════

async def generate_draft(company_context: str, doc_key: str) -> Tuple[str, dict]:
    """
    Generuje koncept dokumentu pomocí Gemini 3.1 Pro.

    Args:
        company_context: kompletní kontext firmy (z pipeline)
        doc_key: klíč dokumentu (např. 'compliance_report')

    Returns:
        (html_draft, metadata) — HTML obsah a metadata LLM volání
    """
    builder = PROMPT_BUILDERS.get(doc_key)
    if not builder:
        raise ValueError(f"Neznámý doc_key: {doc_key}. Dostupné: {list(PROMPT_BUILDERS.keys())}")

    prompt = builder(company_context)
    label = f"M1_{doc_key}"

    # M5 enhanced prompt — přidá pravidla z předchozích generací
    enhanced_prompt = get_enhanced_system_prompt_m1(SYSTEM_PROMPT_M1)
    if enhanced_prompt != SYSTEM_PROMPT_M1:
        extra_chars = len(enhanced_prompt) - len(SYSTEM_PROMPT_M1)
        logger.info(f"[M1 Generator] M5 pravidla aktivní (+{extra_chars} znaků runtime pravidel)")
    else:
        logger.info(f"[M1 Generator] M5 runtime pravidla: žádná (hardcoded pravidla v SYSTEM_PROMPT stále platí)")

    logger.info(f"[M1 Generator] Generuji draft: {DOCUMENT_NAMES.get(doc_key, doc_key)} "
                f"(prompt: {len(prompt)} znaků)")

    text, meta = await call_claude(
        system=enhanced_prompt,
        prompt=prompt,
        label=label,
        temperature=0.3,
        max_tokens=10000,
        model="claude-sonnet-4-6",
    )

    html = extract_html_content(text)

    # G: Quality check — délka + počet sekcí
    h2_count = len(re.findall(r'<h2[^>]*>', html)) if html else 0
    too_short = not html or len(html) < 500
    missing_sections = h2_count < 3 and doc_key not in ("chatbot_notices", "vendor_checklist")

    if too_short or missing_sections:
        reason = f"krátký ({len(html or '')} znaků)" if too_short else f"málo sekcí ({h2_count} H2)"
        logger.warning(f"[M1 Generator] {doc_key}: {reason}, zkouším znovu...")
        text2, meta2 = await call_claude(
            system=enhanced_prompt,
            prompt=prompt + "\n\nDoplň chybějící sekce. KVALITA důležitější než délka. Piš stručně.",
            label=f"{label}_retry",
            temperature=0.4,
            max_tokens=10000,
            model="claude-sonnet-4-6",
        )
        html2 = extract_html_content(text2)
        if len(html2) > len(html):
            html = html2
            meta = meta2

    logger.info(f"[M1 Generator] {doc_key}: draft hotov ({len(html)} znaků)")
    return html, meta


# ══════════════════════════════════════════════════════════════════════
# REFINE DRAFT — M1 Pass 2 (nahrazuje bývalý M4 Refiner)
# ══════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT_REFINE = """Jsi přední český expert na EU AI Act compliance dokumentaci.
Tvým úkolem je vzít DRAFT dokumentu a KRITIKY dvou nezávislých inspektorů
a vyprodukovat FINÁLNÍ DOKONALOU verzi dokumentu.

TVŮJ PROCES:
1. Přečti draft — pochop strukturu a obsah
2. Přečti kritiku EU inspektora (M2) — právní přesnost, správné citace, úplnost
3. Přečti kritiku klienta (M3) — srozumitelnost, personalizace, praktičnost
4. Adresuj VŠECHNY kritické a důležité nálezy OBOU kritiků
5. Zachovej identifikované silné stránky
6. Přidej chybějící obsah identifikovaný kritiky
7. Odpověz na otázky klienta přímo v textu dokumentu
8. Vyprodukuj FINÁLNÍ HTML dokument

VÝSTUPNÍ PRAVIDLA:
1. Piš přímo HTML — začni <h1> tagem.
2. NEBALÍ do ```html```, ```json```, markdown bloků.
3. NEPIŠ žádný komentář před nebo za HTML.
4. NEPIŠ poznámky o editačním procesu.
5. Výstup je ČISTÝ HTML dokument připravený pro PDF.
6. ZACHOVEJ všechny CSS třídy z draftu:
   .highlight, .warning, .info, .callout, .badge-high, .badge-limited,
   .badge-minimal, .metric-grid, .metric-card, .sig-block, .sig-field, .no-break
7. Jednoduché uvozovky v atributech: class='highlight'
8. České typografické uvozovky v textu: „text"
9. NEPOUŽÍVEJ emoji ani Unicode symboly (★, ●, ▸, →, ✓, ✗)

ABSOLUTNÍ ZÁKAZ PLACEHOLDERŮ:
NIKDY nevkládej [DOPLŇTE], [NÁZEV], [TODO], [XXX] ani jakékoliv hranaté závorky
s instrukcemi. Pokud údaj chybí, napiš obecně ale konkrétně.

PRIORITY PŘI KONFLIKTU:
1. PRÁVNÍ PŘESNOST (M2) má VŽDY přednost
2. SROZUMITELNOST (M3) — právní fakt přepiš lidsky
3. Délka — zachovej rozsah, nemaž celé sekce

ZAKÁZÁNO:
- Mazat celé sekce nebo tabulky z draftu
- Meta-komentáře o editačním procesu
- Měnit fakticky správné informace
- Klišé: „V dnešní digitální době", „Závěrem lze říci"
- Časové lhůty mimo zákonné deadliny
- Zmínky o testech, certifikacích, kvízech
"""


def _format_critique(critique: dict, source: str) -> str:
    """Formátuje kritiku do čitelného textu pro refine prompt."""
    parts = []
    parts.append(f"══ KRITIKA: {source} ══")
    parts.append(f"Celkové hodnocení: {critique.get('celkove_hodnoceni', '?')}")
    parts.append(f"Skóre: {critique.get('skore', '?')}/10")

    nalezy = critique.get("nalezy", [])
    if nalezy:
        parts.append(f"\nNÁLEZY ({len(nalezy)}):")
        for i, n in enumerate(nalezy, 1):
            severity = n.get("zavaznost", "?").upper()
            parts.append(f"  [{severity}] {n.get('oblast', '?')}: {n.get('popis', '?')}")
            if n.get("doporuceni"):
                parts.append(f"    Doporučení: {n['doporuceni']}")
            if n.get("reference_ai_act"):
                parts.append(f"    Reference: {n['reference_ai_act']}")

    missing = critique.get("chybejici_obsah", [])
    if missing:
        parts.append("\nCHYBĚJÍCÍ OBSAH:")
        for m in missing:
            parts.append(f"  - {m}")

    strengths = critique.get("silne_stranky", [])
    if strengths:
        parts.append("\nSILNÉ STRÁNKY (zachovej!):")
        for s in strengths:
            parts.append(f"  + {s}")

    questions = critique.get("otazky_klienta", [])
    if questions:
        parts.append("\nOTÁZKY KLIENTA (odpověz v dokumentu!):")
        for q in questions:
            parts.append(f"  ? {q}")

    overall = critique.get("celkove_doporuceni", "")
    if overall:
        parts.append(f"\nCELKOVÉ DOPORUČENÍ: {overall}")

    return "\n".join(parts)


async def refine_draft(
    draft_html: str,
    eu_critique: dict,
    client_critique: dict,
    company_context: str,
    doc_key: str,
) -> tuple:
    """
    M1 Pass 2 — finalizuje dokument na základě draftu a obou kritik.
    Nahrazuje bývalý M4 Refiner. Používá stejný LLM engine (Gemini).

    Args:
        draft_html: HTML koncept z M1 Pass 1
        eu_critique: kritika EU inspektora z M2
        client_critique: kritika klienta z M3
        company_context: kontext firmy
        doc_key: klíč dokumentu

    Returns:
        (final_html, metadata)
    """
    doc_name = DOCUMENT_NAMES.get(doc_key, doc_key)

    eu_text = _format_critique(eu_critique, "EU AI Act Inspektor")
    client_text = _format_critique(client_critique, "Klient (podnikatel)")

    eu_score = eu_critique.get("skore", 0)
    client_score = client_critique.get("skore", 0)
    eu_findings = len(eu_critique.get("nalezy", []))
    client_findings = len(client_critique.get("nalezy", []))

    # M5 enhanced prompt pro refine pass
    enhanced_prompt = get_enhanced_system_prompt_m1(SYSTEM_PROMPT_REFINE)

    prompt = f"""VYLEPŠI NÁSLEDUJÍCÍ DOKUMENT na základě DVOU NEZÁVISLÝCH KRITIK.

══ KONTEXT FIRMY ══
{company_context}

══ DRAFT DOKUMENTU: {doc_name} ══
(EU skóre: {eu_score}/10, {eu_findings} nálezů | Klient skóre: {client_score}/10, {client_findings} nálezů)

{draft_html}

══ KRITIKA #1: EU AI ACT INSPEKTOR ══
(Zaměření: právní přesnost, úplnost, správné citace)

{eu_text}

══ KRITIKA #2: KLIENT / PODNIKATEL ══
(Zaměření: srozumitelnost, praktičnost, personalizace, hodnota)

{client_text}

══ TVŮJ ÚKOL ══
1. Adresuj VŠECHNY kritické a důležité nálezy OBOU kritiků.
2. Zachovej identifikované silné stránky.
3. Přidej chybějící obsah.
4. Odpověz na otázky klienta přímo v textu dokumentu.
5. Nemaž celé sekce — můžeš zkrátit redundance, ale zachovej povinné bloky.
6. NESMÍŠ vkládat žádné placeholdery [DOPLŇTE] atd.
7. Piš přímo HTML — začni <h1>. Žádné komentáře, žádný wrapper.
"""

    # Special instructions for non-standard formats
    if doc_key == "transparency_page":
        prompt += """
SPECIÁLNÍ: Transparenční stránka — zachovej CELOU HTML strukturu včetně
<!-- komentářů -->, <meta> tagů, JSON-LD, CSS, <html>...</html>.
NEZAČÍNEJ <h1> — zachovej kompletní HTML od prvního komentáře po </html>.
"""
    elif doc_key == "training_presentation":
        prompt += """
SPECIÁLNÍ: Školící prezentace — bude převedena do PPTX.
Zachovej: <h1> pro název, <h2> pro slidy, <ul><li> pro odrážky.
Pouze vylepši OBSAH slidů, neměň formát.
"""

    label = f"M1p2_{doc_key}"
    logger.info(
        f"[M1 Refine] Finalizuji: {doc_name} "
        f"(draft: {len(draft_html)} znaků, EU: {eu_score}/10, Klient: {client_score}/10)"
    )

    text, meta = await call_claude(
        system=enhanced_prompt,
        prompt=prompt,
        label=label,
        temperature=0.15,
        max_tokens=10000,
        model="claude-sonnet-4-6",
    )

    html = extract_html_content(text)

    # Quality check — final HTML should be >= 50% of draft
    if html and len(html) < len(draft_html) * 0.5:
        logger.warning(
            f"[M1 Refine] {doc_key}: výrazně kratší ({len(html)} vs {len(draft_html)}), "
            f"zkouším znovu"
        )
        text2, meta2 = await call_claude(
            system=enhanced_prompt,
            prompt=prompt + f"""

DŮLEŽITÉ: Tvá předchozí odpověď měla pouze {len(html)} znaků vs draft {len(draft_html)}.
Zachovej VŠECHNY povinné sekce a tabulky. Zkrať redundance, ale nemaž celé bloky.
""",
            label=f"{label}_retry",
            temperature=0.2,
            max_tokens=10000,
            model="claude-sonnet-4-6",
        )
        html2 = extract_html_content(text2)
        if html2 and len(html2) > len(html):
            html = html2
            meta = meta2

    # Fallback: if refine completely fails, return draft
    if not html or len(html) < 200:
        logger.error(f"[M1 Refine] {doc_key}: refine selhal, vracím original draft")
        html = draft_html
        meta["fallback"] = True
        meta["fallback_reason"] = "M1p2 refine output empty or < 200 chars"

    logger.info(
        f"[M1 Refine] {doc_key}: finální verze ({len(html)} znaků, "
        f"draft: {len(draft_html)} znaků)"
    )

    return html, meta
