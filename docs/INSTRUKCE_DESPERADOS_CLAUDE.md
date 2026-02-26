# INSTRUKCE PRO CLAUDA — Desperados Design workspace
## Integrace AIshield.cz do desperados-design.cz

Martin ti dá tyto instrukce. Ty pracuješ na webu desperados-design.cz.
Druhý Claude pracuje na projektu AIshield.cz (separátní Next.js app).
Tvůj úkol: přidat 2 věci do stávajícího desperados webu.

---

## ÚKOL 1: Přidat novou službu "AI Act Compliance" do sekce #sluzby

### Kde přesně editovat:
- Soubor: `index.html`
- Sekce `#sluzby` je na řádcích ~1062-1171
- Grid se službami: řádek ~1073 (`<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">`)
- **Poslední karta** (AI Chatboty) končí na řádku ~1168
- Grid se zavírá na řádku ~1169

### Co udělat:
Přidej **7. kartu** mezi řádek 1168 (konec AI Chatboty) a řádek 1169 (closing `</div>` gridu).

### HTML nové karty (zkopíruj přesně):
```html
            <!-- AI Act Compliance — NEW -->
            <div class="glass-card p-10 rounded-3xl border border-slate-700/50 relative overflow-hidden group text-center bg-gradient-to-b from-surface to-slate-900 hover:border-primary hover:shadow-neon-strong transition-all duration-300 cursor-default">
                <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-primary via-secondary to-primary"></div>
                <div class="w-16 h-16 bg-slate-900 rounded-2xl flex items-center justify-center mb-6 mx-auto border border-primary/50 shadow-neon group-hover:scale-110 group-hover:shadow-neon-strong transition duration-300">
                    <span class="text-3xl">🛡️</span>
                </div>
                <h3 class="text-xl font-bold text-white mb-4" data-i18n="card_aiact_title">AI Act Compliance</h3>
                <p class="text-slate-400 leading-relaxed mb-3" data-i18n-html="card_aiact_desc">
                    Nový zákon EU o umělé inteligenci platí <strong class="text-white">od srpna 2026</strong>.
                    Automatický audit vašeho webu, generování dokumentů a monitoring.
                    <strong class="text-primary">Zjistěte za 60 sekund</strong>, jestli splňujete požadavky.
                </p>
                <a href="https://aishield.cz/scan?utm_source=desperados&utm_medium=web&utm_campaign=service_card"
                   class="inline-flex items-center gap-2 mt-2 px-6 py-2 bg-primary/20 text-primary border border-primary/30 rounded-xl text-sm font-semibold hover:bg-primary/30 hover:shadow-neon transition-all duration-300">
                    🔍 Skenovat web ZDARMA →
                </a>
                <p class="text-slate-500 text-sm italic mt-3" data-i18n="card_aiact_example">Ve spolupráci s AIshield.cz</p>
            </div>
```

### Přidej překlady do `translations` objektu (~řádek 1696):

V objektu `cs:` přidej:
```javascript
card_aiact_title: "AI Act Compliance",
card_aiact_desc: 'Nový zákon EU o umělé inteligenci platí <strong class="text-white">od srpna 2026</strong>. Automatický audit vašeho webu, generování dokumentů a monitoring. <strong class="text-primary">Zjistěte za 60 sekund</strong>, jestli splňujete požadavky.',
card_aiact_example: "Ve spolupráci s AIshield.cz",
```

V objektu `en:` přidej:
```javascript
card_aiact_title: "AI Act Compliance",
card_aiact_desc: 'The new EU AI regulation applies <strong class="text-white">from August 2026</strong>. Automatic website audit, document generation & monitoring. <strong class="text-primary">Check in 60 seconds</strong> if you comply.',
card_aiact_example: "Powered by AIshield.cz",
```

V objektu `de:` přidej:
```javascript
card_aiact_title: "AI Act Compliance",
card_aiact_desc: 'Die neue EU-KI-Verordnung gilt <strong class="text-white">ab August 2026</strong>. Automatisches Website-Audit, Dokumentenerstellung & Monitoring. <strong class="text-primary">In 60 Sekunden prüfen</strong>, ob Sie konform sind.',
card_aiact_example: "Powered by AIshield.cz",
```

V objektu `es:` přidej:
```javascript
card_aiact_title: "AI Act Compliance",
card_aiact_desc: 'La nueva regulación de IA de la UE se aplica <strong class="text-white">desde agosto de 2026</strong>. Auditoría web automática, generación de documentos y monitoreo. <strong class="text-primary">Verifica en 60 segundos</strong> si cumples.',
card_aiact_example: "Powered by AIshield.cz",
```

---

## ÚKOL 2: Vytvořit stránku /klient/ pro vstup klientů agentury do AIshield

### Co vytvořit:
Nový soubor `klient/index.html` (nebo `klient.html` v rootu — dle tvé preference) 

### Design požadavky:
- Použij **STEJNÝ** design systém jako hlavní web:
  - `--color-bg: #0f172a`, `--color-surface: #1e293b`
  - `--color-primary: #e879f9`, `--color-secondary: #22d3ee`
  - Font Inter, glass-card efekt, neon shadows
- Minimalistická single-page stránka (ne celý web)
- **Responsivní** (mobile-first)

### Obsah stránky:
1. **Logo bar**: "Desperados Design × 🛡️ AIshield"
2. **Hlavní karta** (glass-card, centrovaná, max-width ~500px):
   - Ikona 🛡️
   - Badge: "🎁 Sleva 20 % pro klienty agentury"
   - Nadpis: "AI Act Compliance portál"
   - Popis: "Jste náš klient a potřebujete řešit soulad s novým zákonem EU o umělé inteligenci? Vstupte do portálu — máme pro vás zvýhodněný přístup."
   - 4 benefity s checkmarky:
     - ✓ **Známe váš web** — víme, co na něm běží. Nemusíte nic vysvětlovat.
     - ✓ **20% sleva** na všechny balíčky automaticky po registraci.
     - ✓ **Prioritní podpora** — řešíme vaše požadavky přednostně.
     - ✓ **Widget nainstalujeme** za vás — nula práce na vaší straně.
   - **CTA tlačítko** (primary gradient): "🚀 Registrovat se do portálu"
     → odkaz: `https://aishield.cz/registrace?partner=desperados&utm_source=desperados&utm_medium=klient_portal&utm_campaign=agency_clients`
   - **Sekundární odkaz**: "Už mám účet — přihlásit se"
     → odkaz: `https://aishield.cz/login?partner=desperados&utm_source=desperados&utm_medium=klient_portal`
3. **Footer**: "Provozováno technologií AIshield.cz · Martin Haynes, IČO: 17889251"

### Důležité:
- VŠECHNY odkazy na aishield.cz musí mít UTM parametry: `utm_source=desperados`
- Parametr `partner=desperados` je klíčový — AIshield registrace ho ukládá do user metadata

---

## ÚKOL 3: Přidat odkaz do navigace

V hlavní navigaci (`#main-nav`) přidej nový odkaz **před** CTA tlačítko "Chci web":

```html
<a href="/klient/" class="text-primary hover:text-secondary transition font-semibold" data-i18n="nav_aiact">🛡️ AI Act</a>
```

A do mobilního menu (`#mobile-menu`) přidej stejný odkaz.

Do translations přidej:
- `cs: nav_aiact: "🛡️ AI Act"`
- `en: nav_aiact: "🛡️ AI Act"`
- `de: nav_aiact: "🛡️ AI Act"`
- `es: nav_aiact: "🛡️ AI Act"`

---

## SOUHRN:
1. ✅ Nová 7. service karta v #sluzby s odkazem na aishield.cz/scan (+ překlady 4 jazyky)
2. ✅ Nová stránka /klient/ pro vstup klientů agentury do AIshield portálu
3. ✅ Odkaz v navigaci na /klient/

Všechny změny by měly být vizuálně konzistentní se stávajícím designem webu.
