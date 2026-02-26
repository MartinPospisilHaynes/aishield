# AUDIT REPORT — Gen15 Pipeline Performance
## AIshield.cz Compliance Kit Generation
### Datum: 25. 2. 2026 | Verze pipeline: v3 | Model: Gemini 3.1 Pro (Vertex AI)

---

## ČÁST 1: Přehled generace Gen15

| Metrika | Hodnota |
|---|---|
| Celkem dokumentů | 13 (12 v hlavním běhu + 1 oprava) |
| Úspěšnost | 12/13 = 92 % (transparency_page opravena zvlášť) |
| Celkový čas | 62.8 min (hlavní) + ~5 min (fix) = ~68 min |
| Celkové náklady | $4.46 (hlavní) + $0.41 (fix) + $0.24 (M5) = **$5.11** |
| Celkem tokenů | ~754K (hlavní) + ~50K (fix) + ~37K (M5) = **~841K** |
| Backend | Vertex AI (SA key, region: global) |
| PDF výstup | 11 PDF + 1 Unified PDF (421 KB) + 1 PPTX (54 KB) + 1 HTML |

### Náklady per modul

| Modul | Model | Volání | Celkem $ | Průměr/dok | % z celku |
|---|---|---|---|---|---|
| M1 Generator | Gemini 3.1 Pro | 13* | $1.00 | $0.077 | 24 % |
| M2 EU Critic | Claude Sonnet 4.6 | 12 | $1.54 | $0.128 | 36 % |
| M3 Client Critic | Gemini 3.1 Pro | 12 | $0.41 | $0.034 | 10 % |
| M4 Refiner | Gemini 3.1 Pro | 12 | $1.27 | $0.106 | 30 % |
| **Subtotal pipeline** | | | **$4.22** | | 100 % |
| M5 Optimizer | Claude Opus 4.6 | 1 | $0.24 | — | — |
| Fix transparency | Gemini + Claude | 4 | $0.41 | — | — |

*M1 měl 13 volání, z toho 2 pro transparency_page (oba vrátily 0 znaků kvůli parser bugu — opraveno).

**Klíčový nález o nákladech:** M2 (Claude Sonnet) je NEJDRAŽŠÍ modul (36 % pipeline). Je 3.7× dražší než M3 (Gemini). Přitom oba dělají review — M2 z pohledu EU, M3 z pohledu klienta. Otázka pro budoucnost: stojí Claude za tu cenu, nebo by Gemini zvládl EU review taky?

---

## ČÁST 2: Skóre per dokument

| # | Dokument | EU /10 | Klient /10 | Náklady | Čas | Znaky |
|---|---|---|---|---|---|---|
| 1 | Compliance Report | 7 | 9 | $0.37 | 291s | 23 125 |
| 2 | Akční plán | 7 | 9 | $0.33 | 286s | 17 913 |
| 3 | Registr AI systémů | 7 | **6** | $0.41 | 342s | 26 905 |
| 4 | Plán školení | 7 | 9 | $0.32 | 255s | 21 496 |
| 5 | Texty oznámení | **5** | 9 | $0.28 | 250s | 13 920 |
| 6 | Interní AI politika | 7 | 8 | $0.35 | 310s | 21 653 |
| 7 | Plán řízení incidentů | 7 | 9 | $0.38 | 302s | 23 526 |
| 8 | DPIA/FRIA | 7 | 9 | $0.37 | 306s | 20 107 |
| 9 | Dodavatelský checklist | 7 | 9 | $0.36 | 291s | 23 252 |
| 10 | Monitoring plán | 7 | 9 | $0.34 | 288s | 19 035 |
| 11 | Transparentnost a lidský dohled | 7 | 9 | $0.35 | 290s | 18 947 |
| 12 | Transparenční stránka (HTML) | 5* | 8* | $0.41* | — | 29 878* |
| 13 | Školící prezentace (PPTX) | 7 | **6** | $0.25 | 233s | 10 149 |
| | **PRŮMĚR** | **6.8** | **8.4** | | | |
| | **CELKEM** | | | **$5.11** | ~68 min | ~269 906 |

*Transparency_page: skóre z opravného běhu (v hlavním běhu selhala).

### Hodnocení M2 EU Critic

- **10/12 dokumentů: EU = 7/10** ("dobré") — konzistentní, ale ne vynikající
- **2 dokumenty pod 7**: chatbot_notices (5), transparency_page (5)
- **Počet nálezů per dokument**: 10–18 (průměr ~13 nálezů)
- **Nejčastější nálezy M2** (z M5 analýzy):
  1. Záměna provider/deployer článků (čl. 16–18 vs čl. 26) — **v 8 z 12 dokumentů**
  2. Chybějící GPAI povinnosti (čl. 51–54) — **v 10 z 12 dokumentů**
  3. Nesprávná aplikace FRIA (čl. 27) na soukromé firmy — **v 10 dokumentech**
  4. Emoji a neformální výrazy v regulatorní dokumentaci — **v 8 dokumentech**
  5. Explicitní konstatování non-compliance (právní riziko) — **v několika dokumentech**

### Hodnocení M3 Client Critic

- **9/12 dokumentů: Klient = 9/10** ("vynikající") — klienti budou spokojeni
- **2 dokumenty pod 8**: Registr AI (6), Školící prezentace (6)
- **Slabiny**: Registr AI příliš technický, Prezentace příliš stručná

### Celkový verdikt pipeline

**Pipeline funguje dobře, ale ne dokonale.** Klientská spokojenost (8.4) je solidní — dokumenty jsou čitelné, konkrétní a praktické. Právní přesnost (6.8) je slabší stránka — systematické chyby v citacích článků AI Act, absence GPAI povinností, nesprávná aplikace FRIA.

**M5 Self-Improvement identifikoval 5 pravidel**, která by měla v další iteraci zvýšit EU skóre na ~7.5–8.0. Pravidla jsou kvalitní a adresují skutečné systémové problémy.

---

## ČÁST 3: Jsou všechny dokumenty potřeba? (AI Act audit)

### Mapování na AI Act články

| # | Dokument | Článek AI Act | Klasifikace | Nezbytnost |
|---|---|---|---|---|
| 1 | Compliance Report | Souhrnný přehled | **Best practice** | VYSOKÁ — klient čte první |
| 2 | Akční plán | čl. 4, 26, 16 | **Best practice** | VYSOKÁ — implementační roadmap |
| 3 | Registr AI systémů | **čl. 49, Příloha VIII** | **ZÁKONNÁ POVINNOST** | NUTNÝ — high-risk registrace |
| 4 | Plán školení | **čl. 4** | **ZÁKONNÁ POVINNOST** | NUTNÝ — AI gramotnost je povinná |
| 5 | Texty oznámení | **čl. 50** | **ZÁKONNÁ POVINNOST** | NUTNÝ — transparentnost pro chatboty |
| 6 | Interní AI politika | čl. 26 odst. 5, Rec. 95 | **Silná best practice** | VYSOKÁ — governance framework |
| 7 | Plán řízení incidentů | **čl. 73, čl. 62** | **ZÁKONNÁ POVINNOST** | NUTNÝ — hlášení incidentů |
| 8 | DPIA/FRIA | **čl. 27, GDPR čl. 35** | **ZÁKONNÁ POVINNOST** | NUTNÝ — DPIA povinná pod GDPR |
| 9 | Dodavatelský checklist | čl. 26 odst. 1, čl. 25 | **Silná best practice** | STŘEDNÍ — due diligence dodavatelů |
| 10 | Monitoring plán | **čl. 72, čl. 26 odst. 1b** | **ZÁKONNÁ POVINNOST** | NUTNÝ — post-market monitoring |
| 11 | Transparentnost a lidský dohled | **čl. 13, 14, 50** | **ZÁKONNÁ POVINNOST** | NUTNÝ — čl. 14 pro high-risk |
| 12 | Transparenční stránka (HTML) | čl. 50 (best practice) | **Value-add** | STŘEDNÍ — pěkný deliverable |
| 13 | Školící prezentace (PPTX) | čl. 4 (implementace) | **Value-add** | STŘEDNÍ — praktická pomůcka |

### Verdikt: Generujeme zbytečné dokumenty?

**NE.** Žádný z 13 dokumentů není zbytečný. Rozdělení:

- **7 dokumentů = právně vyžadované** (D3, D4, D5, D7, D8, D10, D11) — přímo z AI Act
- **3 dokumenty = silná best practice** (D1, D2, D6) — nemají dedikovaný článek, ale bez nich by kit nedával klientovi smysl
- **2 dokumenty = value-add** (D12, D13) — nejsou právně nutné, ale zvyšují hodnotu pro klienta
- **1 dokument = due diligence** (D9) — relevatní pro každou firmu používající 3rd-party AI

### Co zvážit do budoucna

1. **Transparenční stránka (D12)** — nejnižší EU skóre (5/10), parser problém. Ale stojí jen $0.41 a klient dostane hotovou HTML stránku pro svůj web. **Nechat — dobrý value-add.**

2. **Školící prezentace (D13)** — nejnížší klientské skóre (6/10), nejmenší výstup (10K znaků). PPTX formát je limitující pro LLM. **Zvážit přepracování promptu — prezentace potřebuje více obsahu a méně textu.**

3. **Dodavatelský checklist (D9)** — relevantní jen pro firmy s 3rd-party AI dodavateli. Ale to jsou téměř všechny firmy (ChatGPT, Google AI, atd.). **Nechat.**

---

## ČÁST 4: Duplikace a plýtvání tokeny

### Identifikované překryvy

| Oblast překryvu | Dokumenty | Odhad překryvu | Komentář |
|---|---|---|---|
| Inventář AI systémů | D1 ↔ D3 | ~40 % obsahu D3 | Compliance report obsahuje vlastní tabulku AI systémů, která je téměř identická s Registrem |
| Přehled povinností | D1 ↔ D2 | ~30 % | Oba mapují povinnosti; report popisuje "co je", plán "co dělat" |
| Transparentnost čl. 50 | D5 ↔ D11 | ~20 % | Oba pokrývají čl. 50; oznámení texty vs. framework |
| Transparenční texty | D5 ↔ D12 | ~15 % | Override texty z oznámení se objeví i na HTML stránce |
| Školení obsah | D4 ↔ D13 | ~25 % | Plán popisuje co školit, prezentace to pak opakuje |
| Governance/akce | D2 ↔ D6 | ~25 % | Akční plán i politika popisují "co dělat" |
| Monitoring/oversight | D10 ↔ D11 | ~20 % | Oba obsahují čtvrtletní kontrolní checklisty |

### Kvantifikace

- **Celkový výstup**: ~270K znaků (11 PDF dokumentů + HTML + PPTX)
- **Odhadovaná duplikace**: ~20–25 % = **~55–65K znaků duplicitního obsahu**
- **Tokenový ekvivalent**: ~15–18K tokenů duplicitních v outputu
- **Nákladový dopad**: Duplikace v outputu je relativně malá (output tokeny jsou levnější než input). Hlavní náklad je v INPUT tokenech — každý dokument dostává celý company context (~6–7K tokenů) + prompt (~2–4K tokenů) × 4 moduly = **~40K input tokenů per dokument jen z kontextu.**

### Kde se skutečně plýtvá tokeny

1. **Company context se posílá 4× per dokument** (M1, M2, M3, M4) × 13 dokumentů = 52 volání LLM, z toho 52× se posílá stejný kontext (~6K tokenů). To je ~312K tokenů jen na opakovaný kontext. **Toto je ~37 % celkových tokenů.**

2. **M2 a M3 dostávají celý draft** — ale M3 (Client Critic) dává téměř vždy 9/10 a generuje jen ~3K znaků odpovědi. Za $0.034 per dokument je to levné, ale otázka je, zda M3 přidává dostatečnou hodnotu.

3. **M4 Refiner dostává draft + obě kritiky** — největší input per volání (~15K tokenů), ale výstup je výrazně delší než draft (typicky +20 %). To naznačuje, že refiner skutečně pracuje.

### Doporučení k optimalizaci (nepodnikat teď — jen pro info)

| Optimalizace | Úspora tokenů | Úspora $ | Riziko |
|---|---|---|---|
| Context caching (Gemini) | ~200K tokenů | ~$0.80 | Nízké — Vertex AI to podporuje |
| Zkrácení company context | ~100K tokenů | ~$0.40 | Střední — méně kontextu = méně přesnost |
| Sloučení D5+D12 (oznámení+transparenční stránka) | ~50K tokenů | ~$0.40 | Nízké — přirozené sloučení |
| Odstranění inventáře z D1 (odkaz na D3) | ~30K tokenů | ~$0.15 | Střední — D1 by nebyl self-contained |
| M3 skip při EU≥8 | ~50K tokenů | ~$0.20 | Střední — ztráta klientského pohledu |

---

## ČÁST 5: M5 Self-Improvement — analýza

### 5 pravidel z M5 v1 (Claude Opus 4.6, $0.24)

| # | Pravidlo | Frekvence v Gen15 | Dopad |
|---|---|---|---|
| 1 | Rozlišovat provider (čl. 16–18) vs deployer (čl. 26) | 8/12 dokumentů | **KRITICKÝ** — právní nepřesnost |
| 2 | Doplnit GPAI povinnosti (čl. 51–54) | 10/12 dokumentů | **KRITICKÝ** — kompletní absence |
| 3 | Nekonstatovat explicitní non-compliance | Několik dokumentů | **STŘEDNÍ** — právní/PR riziko |
| 4 | Bez emoji/Unicode v compliance dokumentech | 8/12 dokumentů | **NÍZKÝ** — kosmetické |
| 5 | FRIA (čl. 27) jen pro veřejné subjekty | 10 dokumentů | **STŘEDNÍ** — právní nepřesnost |

### Hodnocení M5

**M5 je nejcennější modul z celého pipeline.** Za $0.24 (Claude Opus) identifikoval 5 systémových pravidel, která adresují skutečné právní chyby. Pravidla #1 a #2 jsou kritická — záměna provider/deployer a absence GPAI povinností jsou nejčastější a nejzávažnější problémy.

**Očekávaný dopad**: Po implementaci pravidel do M1 promptů by EU skóre mělo vzrůst z 6.8 na ~7.5–8.0 v další generaci.

**Doporučení**: M5 běžet po KAŽDÉ generaci. Je to nejlevnější investice s nejvyšším ROI v celém pipeline.

---

## ČÁST 6: Celkový verdikt a doporučení

### Co funguje dobře ✓

1. **Pipeline architektura M1→M2→M3→M4 je solidní** — 4-modulový systém produkuje konzistentní, kvalitní output
2. **Klientská spokojenost 8.4/10** — dokumenty jsou praktické a čitelné
3. **Náklady $5.11 za celý kit** — přijatelné (cílová cena kitu: 10 000–30 000 Kč → náklady = 0.1–0.3 %)
4. **Vertex AI stabilní** — žádné rate limity, žádné výpadky
5. **M5 Self-Improvement** — skvělý meta-learning mechanismus
6. **Všech 13 dokumentů má opodstatnění** — žádný není zbytečný

### Co potřebuje zlepšení ✗

1. **EU právní přesnost 6.8/10** — pod cílem, systematické chyby v citacích článků
2. **Provider/deployer záměna** v 8/12 dokumentů — nejkritičtější problém
3. **Absence GPAI povinností** v 10/12 dokumentů — velká mezera
4. **Parser bug u transparency_page** — opraven, ale odhalil křehkost extract_html_content()
5. **Přílišná benevolence M3** — skóre 9/10 u 9 z 12 dokumentů naznačuje, že M3 je příliš mírný
6. **Školící prezentace (PPTX)** — nejslabší klientské skóre (6/10), potřebuje lepší prompt

### Prioritní akce (pro budoucí iteraci)

| Priorita | Akce | Očekávaný dopad |
|---|---|---|
| P1 | Implementovat M5 pravidla #1 a #2 do M1 promptů | EU skóre +1.0 |
| P2 | Zpřísnit M3 Client Critic prompt (méně benevolentní) | Realističtější feedback |
| P3 | Vylepšit prompt pro training_presentation | Klient skóre +2–3 |
| P4 | Zvážit Gemini context caching | Úspora ~$0.80 per generaci |
| P5 | Zvážit sloučení D5 (oznámení) + D12 (transparenční stránka) | Úspora ~$0.40 + menší duplikace |

---

### Finanční shrnutí pro 1 zákazníka

| Položka | Cena |
|---|---|
| LLM náklady (pipeline) | $5.11 (~120 Kč) |
| VPS provoz (alokace) | ~20 Kč |
| **Celkem variabilní náklady** | **~140 Kč per kit** |
| Prodejní cena kitu | 10 000–30 000 Kč |
| **Marže** | **98.5–99.5 %** |

---

*Tento report byl vytvořen automatizovaně z gen15.log dat. Žádné změny v kódu nebyly provedeny.*
*Připraveno pro ranní review — Martine, dobré ráno! ☕*
