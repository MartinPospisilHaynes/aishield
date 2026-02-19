"use client";

import { useState, useEffect, useRef } from "react";
import Countdown from "@/components/countdown";
import ContactForm from "@/components/contact-form";
import { useScrollTracking } from "@/lib/analytics";

/* ─── Inline SVG icons (no emoji) ─── */
const ICONS = {
    report: (
        <svg className="w-7 h-7 text-neon-fuchsia" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 3v18h18M7 16l4-4 4 4 5-6" />
        </svg>
    ),
    plan: (
        <svg className="w-7 h-7 text-neon-cyan" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
    ),
    registry: (
        <svg className="w-7 h-7 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
        </svg>
    ),
    web: (
        <svg className="w-7 h-7 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5a17.92 17.92 0 01-8.716-2.247m0 0A9.015 9.015 0 003 12c0-1.605.42-3.113 1.157-4.418" />
        </svg>
    ),
    chatbot: (
        <svg className="w-7 h-7 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
        </svg>
    ),
    policy: (
        <svg className="w-7 h-7 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
        </svg>
    ),
    training: (
        <svg className="w-7 h-7 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.902 59.902 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.697 50.697 0 0112 13.489a50.702 50.702 0 017.74-3.342M6.75 15a.75.75 0 100-1.5.75.75 0 000 1.5zm0 0v-3.675A55.378 55.378 0 0112 8.443m-7.007 11.55A5.981 5.981 0 006.75 15.75v-1.5" />
        </svg>
    ),
    shield: (
        <svg className="w-7 h-7 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
        </svg>
    ),
    dpia: (
        <svg className="w-7 h-7 text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m0-10.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.75c0 5.592 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.57-.598-3.75h-.152c-3.196 0-6.1-1.249-8.25-3.286zm0 13.036h.008v.008H12v-.008z" />
        </svg>
    ),
    vendor: (
        <svg className="w-7 h-7 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
        </svg>
    ),
    monitoring: (
        <svg className="w-7 h-7 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 6a7.5 7.5 0 107.5 7.5h-7.5V6z" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 10.5H21A7.5 7.5 0 0013.5 3v7.5z" />
        </svg>
    ),
};

/* ─── Deliverables data ─── */
const DELIVERABLES = [
    {
        icon: ICONS.report,
        name: "Compliance Report",
        desc: "Přehled stavu webu a vašich povinností",
        detail: null,
        bullets: [
            "Přehled všech AI systémů nalezených na vašem webu — chatboty, analytika, doporučovací systémy",
            "Ke každému systému konkrétní povinnosti dle AI Actu s odkazem na příslušný článek",
            "Celkové hodnocení stavu a jasné doporučení, co řešit jako první",
            "Srozumitelná čeština — bez právnického žargonu, pochopí i laik",
            "V PDF ke stažení i tisku — připraveno k předložení při kontrole",
        ],
    },
    {
        icon: ICONS.registry,
        name: "Registr AI systémů",
        desc: "Povinná evidence pro případ kontroly",
        detail: null,
        bullets: [
            "Kompletní tabulka všech AI nástrojů, které ve firmě používáte",
            "U každého: název, účel, kdo ho používá, kategorizace dle AI Actu",
            "Přijde-li kontrola, stačí ukázat tento jeden dokument",
            "Aktualizovatelný — když přidáte nový nástroj, snadno ho dopíšete",
            "Bez evidence riskujete sankce — registr je základ pro úřady",
        ],
    },
    {
        icon: ICONS.web,
        name: "Transparenční stránka",
        desc: "Hotová podstránka pro váš web",
        detail: null,
        bullets: [
            "Hotový HTML kód stránky — stačí jen vložit na váš web",
            "Přehledně napsáno, jaké AI nástroje používáte a k čemu",
            "Splňuje požadavek transparentnosti dle článku 50 AI Actu",
            "Funguje na WordPress, Shoptet, Webnode, WooCommerce i vlastní weby",
            "Design se automaticky přizpůsobí vašemu webu",
        ],
    },
    {
        icon: ICONS.chatbot,
        name: "Texty oznámení pro AI nástroje",
        desc: "Povinné oznámení pro vaše návštěvníky",
        detail: null,
        bullets: [
            "Přesné texty pro chatboty (Smartsupp, Tidio, LiveChat, Crisp...) i další AI nástroje",
            "Návštěvník musí vědět, že komunikuje s AI — nestačí zmínka v cookies",
            "Připravené k okamžitému zkopírování do nastavení nástroje",
            "Verze v češtině i angličtině (pro zahraniční návštěvníky)",
            "Návod krok za krokem, kam přesně text v administraci vložit",
        ],
    },
    {
        icon: ICONS.policy,
        name: "AI politika firmy",
        desc: "Interní pravidla pro zaměstnance",
        detail: null,
        bullets: [
            "Jasná pravidla, co zaměstnanci smí a nesmí dělat s AI nástroji",
            "Konkrétně řeší ChatGPT, Copilot, AI v účetním softwaru i další",
            "Co se smí psát do AI chatů a jaká data se nesmí sdílet",
            "Jak zacházet s výstupy z AI — co kontrolovat, co ne",
            "Připraveno k vytisknutí a podpisu zaměstnanci",
        ],
    },
    {
        icon: ICONS.training,
        name: "Školení zaměstnanců",
        desc: "Prezentace na míru v PowerPointu",
        detail: null,
        bullets: [
            "Prezentace na míru ve formátu PowerPoint — stačí promítnout a projít s týmem",
            "Témata: co je AI, jaká jsou rizika, co říká zákon, jak AI bezpečně používat",
            "Praktické příklady z praxe — srozumitelné i pro neodborníky",
            "Splňuje povinnost AI gramotnosti dle článku 4 AI Actu",
            "Připravena i k zaslání e-mailem zaměstnancům na home office",
        ],
    },
    {
        icon: ICONS.plan,
        name: "Záznamový list o proškolení",
        desc: "Doklad pro splnění čl. 4 AI Actu",
        detail: null,
        bullets: [
            "Připravený dokument s místem pro jména, data a podpisy zaměstnanců",
            "Při kontrole musíte prokázat, že zaměstnanci prošli školením",
            "Zákon nevyžaduje certifikát — ale důkaz o proškolení ano",
            "Stačí vytisknout, nechat podepsat a archivovat",
            "Bez záznamu riskujete, že školení nikdo neuzná",
        ],
    },
    {
        icon: ICONS.shield,
        name: "Plán řízení AI incidentů",
        desc: "Připravenost na selhání AI systému",
        detail: null,
        bullets: [
            "Jasný postup, co dělat, když AI systém udělá chybu nebo způsobí škodu",
            "Kdo je zodpovědný, koho kontaktovat, jak eskalovat",
            "Splňuje požadavek čl. 73 AI Actu na hlášení závažných incidentů",
            "Personalizovaný podle AI systémů, které skutečně používáte",
            "Připraveno k okamžitému použití — stačí vytisknout a založit",
        ],
    },
    {
        icon: ICONS.dpia,
        name: "DPIA — Posouzení vlivu",
        desc: "Předvyplněná šablona dle GDPR + AI Act",
        detail: null,
        bullets: [
            "Posouzení vlivu na ochranu osobních údajů — povinné při zpracování dat přes AI",
            "Předvyplněná šablona s údaji z dotazníku — seznam AI systémů, rizikové úrovně, firemní data",
            "Strukturovaná dle GDPR čl. 35 a AI Act čl. 27 — úřady přesně tohle vyžadují",
            "Stačí doplnit specifika vaší firmy a nechat podepsat DPO / vedením",
            "Bez DPIA riskujete sankce i ze strany ÚOOÚ, nejen z AI Actu",
        ],
    },
    {
        icon: ICONS.vendor,
        name: "Dodavatelský checklist",
        desc: "Kontrola smluv s dodavateli AI",
        detail: null,
        bullets: [
            "Kontrolní seznam, co musí pokrývat vaše smlouvy s dodavateli AI (OpenAI, Google, Microsoft…)",
            "Povinné dle čl. 25–26 AI Actu — nasazovatel odpovídá i za dodavatele",
            "Checkboxy pro DPA, SLA, GDPR záruky, opt-out z trénování a další náležitosti",
            "Personalizovaný — obsahuje konkrétní AI systémy nalezené u vás",
            "Formulář pro každého dodavatele zvlášť — vytisknout a vyplnit",
        ],
    },
    {
        icon: ICONS.monitoring,
        name: "Monitoring plán AI",
        desc: "Co, jak a jak často kontrolovat",
        detail: null,
        bullets: [
            "Plán monitoringu výstupů AI — povinný dle čl. 9 a 72 AI Actu",
            "KPI a metriky: přesnost, halucinace, bias, bezpečnost, compliance",
            "Zahrnuje testování férovosti (bias testing) — genderový, etnický, věkový",
            "Měsíční checklist s konkrétními úkoly pro každý týden",
            "Záznamový list pro archivaci — důkaz pravidelného monitoringu při kontrole",
        ],
    },
];

/* ─── FAQ data ─── */
const FAQ_ITEMS = [
    {
        q: "Co je AI Act a proč se mě týká?",
        a: "AI Act (Nařízení EU 2024/1689) je první zákon na světě, který komplexně reguluje umělou inteligenci. " +
            "Platí pro každého, kdo v EU provozuje nebo nasazuje AI systémy — a to bez ohledu na velikost firmy. " +
            "Pokud máte na webu chatbot, používáte Google Analytics, máte doporučovací systém produktů, reklamní pixel nebo jakýkoliv jiný nástroj s prvky AI, zákon se vás přímo týká. " +
            "Představte si to jako GDPR, ale pro umělou inteligenci — s tím rozdílem, že pokuty jsou ještě vyšší. " +
            "Mnoho firem si neuvědomuje, že AI systémy na jejich webu vůbec mají — proto nabízíme bezplatný sken, který vám to odhalí za minutu.",
    },
    {
        q: "Jaké pokuty hrozí?",
        a: "Zákon stanoví tři úrovně pokut podle závažnosti porušení. " +
            "Za nejzávažnější porušení (používání zakázaných AI systémů, například skryté manipulace nebo sociální skórování) hrozí pokuta až 35 milionů EUR nebo 7 % celosvětového ročního obratu — podle toho, co je vyšší. " +
            "Za nedodržení běžných povinností, jako je chybějící dokumentace, neoznačený chatbot nebo chybějící transparenční stránka, hrozí až 15 milionů EUR nebo 3 % obratu. " +
            "Za poskytnutí nepravdivých nebo zavádějících informací kontrolním úřadům až 7,5 milionu EUR nebo 1 % obratu. " +
            "Pro malé a střední firmy (do 250 zaměstnanců) platí nižší stropy, ale i tak se bavíme o statisících až milionech korun. " +
            "Důležité je, že pokuty se počítají za každé jednotlivé porušení — pokud máte na webu 3 neoznačené AI systémy, může jít o 3 samostatné sankce.",
    },
    {
        q: "Mám jen malou firmu / e-shop. Opravdu se mě to týká?",
        a: "Ano, bohužel ano. Zákon platí pro všechny, kdo v EU provozují AI systémy — ať jste kadeřnictví s jedním zaměstnancem, nebo e-shop s tisíci produkty. " +
            "Používáte Smartsupp chatbot? Google Analytics? Doporučování produktů na Shoptetu? Reklamní pixel od Facebooku nebo Google? Automatické odpovědi na e-maily? " +
            "To všechno jsou AI systémy ve smyslu zákona a všechny vyžadují minimálně označení a dokumentaci. " +
            "Dobrá zpráva je, že pro většinu malých firem spadají jejich AI systémy do kategorie s minimálními povinnostmi — hlavně transparentnost (čl. 50) a AI gramotnost zaměstnanců (čl. 4). " +
            "My vám s tím pomůžeme jednoduše a za rozumnou cenu — nemusíte platit desítky tisíc za advokáta.",
    },
    {
        q: "Co když nevím, jestli mám AI na webu?",
        a: "To je naprosto normální — většina majitelů webů nemá přehled o tom, jaké AI nástroje na jejich stránkách běží. " +
            "Mnoho AI systémů se na web dostane nepřímo: přes e-shopovou platformu (Shoptet, WooCommerce), přes chatbot plugin (Smartsupp, Tidio, Crisp), přes analytiku (Google Analytics) nebo přes reklamní systémy (Meta Pixel, Google Ads). " +
            "Přesně proto jsme vytvořili náš bezplatný scanner. Zadáte adresu webu a za minutu dostanete kompletní přehled — jaké AI nástroje na něm běží, do které kategorie dle AI Actu spadají a co s tím musíte udělat. " +
            "Žádná registrace, žádné platební údaje, žádný háček.",
    },
    {
        q: "Jak to celé funguje?",
        a: "Celý proces má 5 jednoduchých kroků a zvládnete ho za jedno odpoledne. " +
            "1) Zadáte adresu svého webu — náš robot ho automaticky proskenuje a během minuty identifikuje všechny AI systémy. " +
            "2) Dostanete přehledný report s výsledky — jaké AI nástroje máte, jaké povinnosti z nich plynou a do jaké kategorie spadáte. " +
            "3) Vyberete si balíček služeb podle vašich potřeb — od základního BASIC po kompletní ENTERPRISE s konzultací. " +
            "4) Vyplníte krátký dotazník o vaší firmě (zabere asi 5 minut, většinou jen klikáte). Dotazník je klíčový, protože EU AI Act se netýká jen vašeho webu — reguluje i interní AI systémy, které zákazník nikdy neuvidí (ChatGPT pro zaměstnance, AI v účetnictví, automatizaci HR…). Sken odhalí jen to veřejné; dotazník pokryje celou AI politiku firmy. " +
            "5) Do 7 dnů obdržíte vše, co váš balíček obsahuje — kompletní sadu dokumentů v PDF, implementaci i nastavení. Všechno vyřídime za vás, můžete být v klidu.",
    },
    {
        q: "Co musím vyplnit v dotazníku?",
        a: "Dotazník je navržený tak, aby byl co nejjednodušší — většinou jen klikáte na odpovědi, žádné dlouhé psaní. " +
            "Ptáme se na základní informace: velikost firmy, obor podnikání, jaké AI nástroje používáte interně (ChatGPT, Copilot, AI v účetním softwaru...) a jak je používají vaši zaměstnanci. " +
            "EU AI Act totiž nereguluje jen to, co je vidět na vašem webu — zahrnuje i interní AI systémy, které zákazník nikdy neuvidí: automatizaci HR, generování obsahu, rozhodovací algoritmy nebo AI komunikaci uvnitř firmy. " +
            "Automatický sken odhalí jen veřejně viditelné nástroje. Dotazník pokryje celou AI politiku vaší firmy, abychom vám mohli připravit dokumenty přesně na míru. " +
            "Vyplnění trvá asi 5 minut. Odpovědi můžete kdykoliv upravit a dokumenty se automaticky přegenerují podle nových údajů.",
    },
    {
        q: "Jaký je deadline?",
        a: "Klíčové datum je 2. srpen 2026 — od tohoto dne se AI Act plně vztahuje na všechny AI systémy bez výjimky. " +
            "Ale pozor: některé povinnosti platí už dříve. Zákaz nepřijatelných AI praktik (čl. 5) je v platnosti od února 2025. " +
            "Povinnost AI gramotnosti zaměstnanců (čl. 4) platí rovněž od února 2025 — pokud vaši zaměstnanci používají AI nástroje a nemáte doklad o jejich proškolení, už teď jste v prodlení. " +
            "Příprava kompletní dokumentace zabere cca 2–4 týdny, proto doporučujeme nenechávat to na poslední chvíli. " +
            "Kontrolní orgány budou po 2. srpnu 2026 aktivně prověřovat weby pomocí automatizovaných nástrojů — stejných, jaké používá náš scanner.",
    },
    {
        q: "Nahradíte advokáta?",
        a: "Ne — a ani to není náš cíl. Jsme technický nástroj, ne právní poradna. " +
            "Co ale uděláme: automaticky identifikujeme AI systémy na vašem webu, připravíme kompletní dokumentační podklady, vygenerujeme transparenční stránku, texty oznámení, interní AI politiku a materiály pro školení zaměstnanců. " +
            "Dokumenty, které od nás dostanete, jsou kvalitním základem pro vaši compliance — většina malých a středních firem s nimi vystačí. " +
            "Pokud ale chcete stoprocentní jistotu nebo máte specifickou situaci (high-risk AI systémy, zpracování citlivých dat), doporučujeme dokumenty vzít k advokátovi k odborné revizi. " +
            "Naše dokumenty jsou na to připravené — strukturované, srozumitelné a s odkazy na konkrétní články zákona.",
    },
    {
        q: "Je skenování webu opravdu zdarma?",
        a: "Ano, skenování je zcela zdarma, nezávazné a bez jakýchkoliv skrytých podmínek. " +
            "Nemusíte se nikam registrovat, nemusíte zadávat e-mail ani platební údaje. Prostě zadáte URL a za minutu máte výsledky. " +
            "Platíte pouze v případě, že se rozhodnete objednat balíček dokumentů — to je čistě na vašem rozhodnutí. " +
            "Sken si můžete spustit opakovaně, třeba po každé změně na webu, a vždy bude zdarma. " +
            "Proč to děláme zadarmo? Protože věříme, že když uvidíte, kolik AI systémů na vašem webu běží, pochopíte, proč je dokumentace důležitá.",
    },
];

/* ─── Expandable panel component ─── */
function DeliverableCard({ item }: { item: (typeof DELIVERABLES)[0] }) {
    const [open, setOpen] = useState(false);

    return (
        <div
            className="group cursor-pointer rounded-xl border border-white/[0.06] bg-white/[0.02] transition-all duration-300 hover:border-fuchsia-500/20 hover:bg-white/[0.03]"
            onClick={() => setOpen(!open)}
        >
            <div className="flex items-center gap-4 px-5 py-4">
                <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-white/[0.04] border border-white/[0.08] flex items-center justify-center">
                    {item.icon}
                </div>
                <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-semibold text-slate-200">{item.name}</h4>
                    <p className="text-sm text-slate-400 mt-0.5">{item.desc}</p>
                </div>
                <svg
                    className={`w-4 h-4 text-slate-500 transition-transform duration-300 flex-shrink-0 ${open ? "rotate-180" : ""}`}
                    fill="none" stroke="currentColor" viewBox="0 0 24 24"
                >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
            </div>
            {open && item.bullets && (
                <div className="px-5 pb-4 pt-0">
                    <div className="border-t border-white/[0.06] pt-3 ml-[3.75rem]">
                        <ul className="space-y-1.5">
                            {item.bullets.map((b, i) => (
                                <li key={i} className="flex items-start gap-2 text-sm text-slate-400 leading-relaxed">
                                    <svg className="w-3.5 h-3.5 text-fuchsia-400/70 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                                    </svg>
                                    {b}
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            )}
        </div>
    );
}

/* ─── Testimonial data ─── */
const TESTIMONIALS = [
    {
        quote: "Netušil jsem, že na mém e-shopu běží 5 AI systémů. Díky AIshieldu mám jasno, co musím udělat, než začnou padat pokuty.",
        author: "Tomáš K.",
        role: "Majitel e-shopu, Brno",
    },
    {
        quote: "Klient se ptal, jestli je jejich chatbot v souladu se zákonem. Nechal jsem to proskenovat a za hodinu jsem měl odpověď i dokumentaci.",
        author: "JUDr. Petra M.",
        role: "Advokátka, Praha",
    },
    {
        quote: "Jako OSVČ jsem si myslel, že se mě AI Act netýká. Scanner odhalil Google Analytics i Crisp chat — obojí vyžaduje oznámení.",
        author: "David R.",
        role: "Freelance vývojář, Olomouc",
    },
    {
        quote: "Máme Shoptet e-shop s chatbotem a doporučovacím systémem. AIshield nám za den připravil kompletní dokumentaci. Ušetřili jsme desítky tisíc za právníka.",
        author: "Ing. Martin P.",
        role: "E-commerce manažer, Ostrava",
    },
    {
        quote: "V naší účetní kanceláři používáme AI v softwaru i pro komunikaci s klienty. Dokumenty od AIshieldu předáme auditorovi a máme klid.",
        author: "Bc. Lenka S.",
        role: "Účetní, Plzeň",
    },
    {
        quote: "Provozujeme řetězec fitness center s online rezervacemi a AI chatbotem. Vůbec jsem netušil, že na nás AI Act dopadá. Scanner mi otevřel oči.",
        author: "Jakub N.",
        role: "Provozovatel fitness, Praha",
    },
    {
        quote: "Jsem webařka a teď to doporučuju všem svým klientům. Jeden sken a hned víme, co je potřeba vyřešit. Velká úspora času.",
        author: "Mgr. Karolína V.",
        role: "Webdesignérka, Liberec",
    },
    {
        quote: "Řídím IT ve výrobní firmě. Používáme prediktivní údržbu a AI kontrolu kvality — obojí je high-risk dle AI Actu. AIshield nás na to upozornil včas.",
        author: "Ing. Pavel H.",
        role: "CTO, strojírenská firma, Zlín",
    },
    {
        quote: "Na webu naší obce běží chatbot pro občany. Díky AIshieldu máme transparenční stránku i registr AI systémů. Jsme připraveni na kontrolu.",
        author: "Mgr. Jana D.",
        role: "Tajemnice obce, Středočeský kraj",
    },
    {
        quote: "Doporučil mi to kolega advokát. Za 15 minut jsem věděl, že náš klient porušuje tři povinnosti. Okamžitě jsme to začali řešit.",
        author: "JUDr. Ondřej B.",
        role: "Advokát, Hradec Králové",
    },
];

/* ─── Testimonial carousel component ─── */
function TestimonialCarousel() {
    const scrollRef = useRef<HTMLDivElement>(null);
    const [paused, setPaused] = useState(false);

    useEffect(() => {
        const container = scrollRef.current;
        if (!container) return;

        let animId: number;
        let lastTime = 0;
        let accum = 0;
        const speed = 30; // px per second

        const step = (time: number) => {
            if (!paused && lastTime) {
                const delta = (time - lastTime) / 1000; // seconds
                accum += speed * delta;
                const px = Math.floor(accum);
                if (px >= 1) {
                    container.scrollLeft += px;
                    accum -= px;
                }

                // Seamless loop: when we've scrolled past the first set, jump back
                const halfScroll = container.scrollWidth / 2;
                if (container.scrollLeft >= halfScroll) {
                    container.scrollLeft -= halfScroll;
                }
            }
            lastTime = time;
            animId = requestAnimationFrame(step);
        };

        animId = requestAnimationFrame(step);
        return () => cancelAnimationFrame(animId);
    }, [paused]);

    // Double the testimonials for seamless looping
    const items = [...TESTIMONIALS, ...TESTIMONIALS];

    return (
        <div
            className="relative"
            onMouseEnter={() => setPaused(true)}
            onMouseLeave={() => setPaused(false)}
        >
            {/* Fade edges */}
            <div className="pointer-events-none absolute left-0 top-0 bottom-0 w-16 z-10 bg-gradient-to-r from-dark-900 to-transparent" />
            <div className="pointer-events-none absolute right-0 top-0 bottom-0 w-16 z-10 bg-gradient-to-l from-dark-900 to-transparent" />

            <div
                ref={scrollRef}
                className="flex gap-4 overflow-x-hidden py-2"
                style={{ scrollBehavior: "auto" }}
            >
                {items.map((t, i) => (
                    <div
                        key={i}
                        className="glass p-5 flex flex-col flex-shrink-0 w-[320px] sm:w-[360px]"
                    >
                        {/* Stars */}
                        <div className="flex gap-0.5 mb-3">
                            {Array.from({ length: 5 }).map((_, s) => (
                                <svg key={s} className="w-3.5 h-3.5 text-fuchsia-400" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                                </svg>
                            ))}
                        </div>

                        {/* Quote */}
                        <p className="text-sm text-slate-300 leading-relaxed flex-1">
                            &ldquo;{t.quote}&rdquo;
                        </p>

                        {/* Author */}
                        <div className="mt-4 pt-3 border-t border-white/[0.06] flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-fuchsia-500/15 flex items-center justify-center text-xs font-bold text-fuchsia-400">
                                {t.author.charAt(0)}
                            </div>
                            <div>
                                <p className="text-sm font-semibold text-slate-200">{t.author}</p>
                                <p className="text-xs text-slate-500">{t.role}</p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════════
   HOMEPAGE
   ═══════════════════════════════════════════ */
export default function HomePage() {
    useScrollTracking();
    return (
        <>
            {/* ══════ HERO ══════ */}
            <section className="relative overflow-hidden">
                {/* BG glow effects */}
                <div className="absolute inset-0 -z-10">
                    <div className="absolute top-[-20%] left-[10%] h-[600px] w-[600px] rounded-full bg-fuchsia-600/10 blur-[120px]" />
                    <div className="absolute bottom-[-10%] right-[10%] h-[500px] w-[500px] rounded-full bg-cyan-500/10 blur-[120px]" />
                </div>

                <div className="mx-auto max-w-7xl px-4 sm:px-6 py-12 sm:py-20 lg:py-28 text-center">
                    {/* Countdown */}
                    <div className="mb-6">
                        <p className="text-sm font-medium uppercase tracking-wider text-red-400 mb-4">
                            Do plné účinnosti AI Act zbývá
                        </p>
                        <Countdown />
                    </div>

                    {/* Headline */}
                    <h1 className="mx-auto max-w-5xl text-2xl xs:text-3xl font-extrabold tracking-tight sm:text-6xl lg:text-7xl leading-tight mt-8 sm:mt-10">
                        Porušuje Váš web{" "}
                        <span className="neon-text">nový zákon EU</span>
                        {" "}o umělé inteligenci?
                    </h1>

                    {/* Subheadline */}
                    <p className="mx-auto mt-4 sm:mt-6 max-w-2xl text-base sm:text-lg text-slate-400 leading-relaxed">
                        Od <strong className="text-white">2. srpna 2026</strong> platí EU AI Act.
                        Nestačí jen přidat zmínku o AI na cookie lištu — zákon vyžaduje mnohem víc.
                    </p>

                    {/* CTA — Scanner Input — hned pod subheadline */}
                    <div className="mx-auto mt-8 max-w-xl">
                        <form className="flex flex-col sm:flex-row gap-3" action="/scan" onSubmit={(e) => {
                            const form = e.currentTarget;
                            const input = form.querySelector('input[name="url"]') as HTMLInputElement;
                            let val = input.value.trim();
                            if (val && !val.match(/^https?:\/\//i)) {
                                val = 'https://' + val;
                            }
                            input.value = val;
                        }}>
                            <input
                                type="text"
                                name="url"
                                placeholder="vasefirma.cz"
                                required
                                className="flex-1 rounded-xl border border-white/10 bg-white/5 px-5 py-4 text-white text-lg
                                    placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50
                                    focus:border-fuchsia-500/30 backdrop-blur-sm transition-all"
                            />
                            <button type="submit" className="btn-primary whitespace-nowrap text-lg px-10 py-4 w-full sm:w-auto">
                                Skenovat ZDARMA
                            </button>
                        </form>
                        <p className="text-sm text-slate-400 mt-3 text-center">
                            Zjistěte za minutu, jaké AI systémy běží na vašem webu. Skenování je <strong className="text-white">zdarma a nezávazné</strong>.
                        </p>
                    </div>

                    {/* Povinnosti — odrážky */}
                    <div className="mx-auto mt-12 max-w-2xl text-left">
                        <h3 className="text-sm font-semibold uppercase tracking-wider text-fuchsia-400 mb-4 text-center">
                            Co zákon vyžaduje od webů a e-shopů
                        </h3>
                        <div className="grid sm:grid-cols-2 gap-3">
                            {[
                                {
                                    icon: (
                                        <svg className="w-5 h-5 text-fuchsia-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                                        </svg>
                                    ),
                                    title: "Zmapovat AI systémy na webu",
                                    bullets: [
                                        "Musíte vědět, jaké AI nástroje váš web používá",
                                        "Chatboty, analytika, doporučovací systémy, AI vyhledávání",
                                        "Evidence musí být průběžně aktuální",
                                    ],
                                    solution: "Automaticky proskenujeme a zapíšeme do registru",
                                },
                                {
                                    icon: (
                                        <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 15.75l1.5 1.5 3-3" />
                                        </svg>
                                    ),
                                    title: "Připravit dokumentaci pro kontrolu",
                                    bullets: [
                                        "Dozorový orgán může kdykoliv požádat o dokumenty",
                                        "Přehled AI systémů, hodnocení rizik, přijatá opatření",
                                        "Dokumenty musí být v češtině a ve formátu k tisku",
                                    ],
                                    solution: "Vygenerujeme sadu dokumentů přesně podle vašeho rizikového profilu",
                                },
                                {
                                    icon: (
                                        <svg className="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
                                        </svg>
                                    ),
                                    title: "Informovat návštěvníky (čl. 50)",
                                    bullets: [
                                        "Každý, kdo komunikuje s AI na vašem webu, o tom musí vědět",
                                        "Týká se chatbotů, AI doporučení i automatických odpovědí",
                                        "Nestačí jen zmínka v cookies — musí být u konkrétního nástroje",
                                    ],
                                    solution: "Připravíme přesné české texty ke každému systému",
                                },
                                {
                                    icon: (
                                        <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5a17.92 17.92 0 01-8.716-2.247m0 0A9.015 9.015 0 003 12c0-1.605.42-3.113 1.157-4.418" />
                                        </svg>
                                    ),
                                    title: "Zveřejnit transparenční přehled",
                                    bullets: [
                                        "Na webu musí být přehled používaných AI systémů",
                                        "Srozumitelný i pro neodborníka — bez právnického žargonu",
                                        "Praktický způsob, jak splnit požadavky čl. 50 na jednom místě",
                                    ],
                                    solution: "Dodáme hotovou stránku — stačí vložit na web",
                                },
                                {
                                    icon: (
                                        <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.902 59.902 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.697 50.697 0 0112 13.489a50.702 50.702 0 017.74-3.342M6.75 15a.75.75 0 100-1.5.75.75 0 000 1.5zm0 0v-3.675A55.378 55.378 0 0112 8.443m-7.007 11.55A5.981 5.981 0 006.75 15.75v-1.5" />
                                        </svg>
                                    ),
                                    title: "Proškolit zaměstnance (čl. 4)",
                                    bullets: [
                                        "Zaměstnanci pracující s AI musí rozumět jejím základům a rizikům",
                                        "Týká se všech — i asistentky, která používá ChatGPT",
                                        "Zákon nevyžaduje certifikát, ale musíte gramotnost prokázat",
                                    ],
                                    solution: "Připravíme prezentaci na míru v PowerPointu pro vaše zaměstnance + záznamový list o proškolení",
                                },
                                {
                                    icon: (
                                        <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                                        </svg>
                                    ),
                                    title: "Zavést interní AI pravidla",
                                    bullets: [
                                        "Firma musí mít směrnici — kdo a jak smí AI používat",
                                        "Které nástroje jsou povoleny, co se nesmí zadat do AI",
                                        "Bez pravidel riskujete únik dat i pokuty",
                                    ],
                                    solution: "Vytvoříme AI Policy na míru vaší firmě",
                                },
                            ].map((item, i) => (
                                <div key={i} className="flex items-start gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] px-4 py-3.5">
                                    <span className="mt-0.5 flex-shrink-0">{item.icon}</span>
                                    <div>
                                        <p className="text-sm font-semibold text-slate-200">{item.title}</p>
                                        <ul className="mt-1.5 space-y-1">
                                            {item.bullets.map((b, j) => (
                                                <li key={j} className="flex items-start gap-1.5 text-xs text-slate-400 leading-relaxed">
                                                    <span className="text-slate-600 mt-1 flex-shrink-0">•</span>
                                                    {b}
                                                </li>
                                            ))}
                                        </ul>
                                        <p className="text-xs text-fuchsia-400/70 mt-2 font-medium">✦ {item.solution}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Warning box */}
                    <div className="mx-auto mt-8 max-w-2xl">
                        <div className="bg-white/[0.05] border border-white/[0.08] rounded-xl px-4 sm:px-6 py-4 sm:py-5">
                            <div className="flex items-start gap-3">
                                <svg className="w-6 h-6 text-fuchsia-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m0-10.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.75c0 5.592 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.57-.598-3.75h-.152c-3.196 0-6.1-1.249-8.25-3.286zm0 13.036h.008v.008H12v-.008z" />
                                </svg>
                                <div className="text-sm sm:text-base text-slate-300 leading-relaxed">
                                    <p className="font-medium">
                                        Po 2. srpnu 2026 začne EU{" "}
                                        <strong className="text-white">systematicky kontrolovat weby a e-shopy</strong>{" "}
                                        pomocí automatizovaných nástrojů.
                                    </p>
                                    <p className="mt-2 text-slate-400">
                                        Náš sken funguje na stejném principu — odhalí přesně to, co najdou kontrolní orgány.
                                        Zjistěte stav svého webu dříve, než to udělá někdo jiný.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* ── 24H HLOUBKOVÝ SCAN ── */}
            <section className="border-t border-white/[0.06] py-16 sm:py-24 relative overflow-hidden">
                <div className="absolute inset-0 -z-10">
                    <div className="absolute top-[30%] left-[10%] h-[500px] w-[500px] rounded-full bg-cyan-600/8 blur-[120px]" />
                    <div className="absolute top-[10%] right-[15%] h-[400px] w-[400px] rounded-full bg-fuchsia-500/6 blur-[100px]" />
                </div>

                <div className="mx-auto max-w-5xl px-4 sm:px-6">
                    <div className="text-center mb-12 sm:mb-16">
                        <div className="neon-divider mb-6" />
                        <div className="inline-flex items-center gap-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 px-4 py-1.5 text-sm font-medium text-cyan-400 mb-6">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
                            </span>
                            Unikátní v ČR
                        </div>
                        <h2 className="text-3xl font-extrabold sm:text-5xl leading-tight">
                            24hodinový hloubkový <span className="neon-text">scan</span>
                        </h2>
                        <p className="mt-4 text-lg text-slate-400 max-w-2xl mx-auto">
                            Jeden rychlý scan nestačí. AI systémy se na webu chovají různě podle času, lokace i&nbsp;zařízení.
                            Proto provádíme <strong className="text-white">24 nezávislých skenů v 6 kolech ze&nbsp;7 zemí</strong> — přes rezidenční proxy, střídavě z desktopu i mobilu.
                        </p>
                    </div>

                    {/* Globe visual + features */}
                    <div className="grid md:grid-cols-2 gap-8 sm:gap-12 items-center">

                        {/* Left — Globe / map visual */}
                        <div className="relative">
                            <div className="glass p-8 sm:p-10 text-center">
                                <div className="text-6xl sm:text-7xl mb-4">🌍</div>
                                <div className="grid grid-cols-4 gap-2 max-w-xs mx-auto mb-6">
                                    {[
                                        { flag: "🇨🇿", code: "CZ" },
                                        { flag: "🇬🇧", code: "GB" },
                                        { flag: "🇺🇸", code: "US" },
                                        { flag: "🇧🇷", code: "BR" },
                                        { flag: "🇯🇵", code: "JP" },
                                        { flag: "🇿🇦", code: "ZA" },
                                        { flag: "🇦🇺", code: "AU" },
                                    ].map((c) => (
                                        <div key={c.code} className="flex flex-col items-center gap-1 rounded-lg bg-white/5 border border-white/10 py-2 px-1">
                                            <span className="text-xl">{c.flag}</span>
                                            <span className="text-[10px] text-slate-500 font-mono">{c.code}</span>
                                        </div>
                                    ))}
                                </div>
                                <p className="text-sm text-slate-400">
                                    <strong className="text-white">24 skenů</strong> z rezidenčních IP adres v&nbsp;7 zemích za 24 hodin
                                </p>
                            </div>
                        </div>

                        {/* Right — Feature list */}
                        <div className="space-y-5">
                            {[
                                {
                                    icon: (
                                        <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
                                    ),
                                    title: "6 kol po 4 hodinách",
                                    desc: "Skenujeme v 6 kolech rozložených přes 24 hodin — ráno, odpoledne, večer, v noci. Odhalíme AI systémy, které se aktivují jen v určitou hodinu."
                                },
                                {
                                    icon: (
                                        <svg className="w-5 h-5 text-fuchsia-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 0 0 8.716-6.747M12 21a9.004 9.004 0 0 1-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 0 1 7.843 4.582M12 3a8.997 8.997 0 0 0-7.843 4.582m15.686 0A11.953 11.953 0 0 1 12 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0 1 21 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0 1 12 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 0 1 3 12c0-1.605.42-3.113 1.157-4.418" /></svg>
                                    ),
                                    title: "7 zemí × 24 skenů",
                                    desc: "V každém kole skenujeme ze 4 zemí (rotace CZ, GB, US, BR, JP, ZA, AU). Chatboti se často zobrazují jen návštěvníkům z určitých regionů — tohle je odhalí."
                                },
                                {
                                    icon: (
                                        <svg className="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M10.5 1.5H8.25A2.25 2.25 0 0 0 6 3.75v16.5a2.25 2.25 0 0 0 2.25 2.25h7.5A2.25 2.25 0 0 0 18 20.25V3.75a2.25 2.25 0 0 0-2.25-2.25H13.5m-3 0V3h3V1.5m-3 0h3m-3 18.75h3" /></svg>
                                    ),
                                    title: "Desktop i mobilní zařízení",
                                    desc: "V rámci každého kola střídáme desktopové a mobilní prohlížeče — mnoho chatbotů se zobrazuje jen na mobilu, nebo naopak."
                                },
                                {
                                    icon: (
                                        <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 0 1-2.25 2.25h-15a2.25 2.25 0 0 1-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25m19.5 0v.243a2.25 2.25 0 0 1-1.07 1.916l-7.5 4.615a2.25 2.25 0 0 1-2.36 0L3.32 8.91a2.25 2.25 0 0 1-1.07-1.916V6.75" /></svg>
                                    ),
                                    title: "Agregovaný report za 24h",
                                    desc: "Po dokončení všech 24 skenů vám pošleme kompletní report — deduplikovaný přehled všech nalezených AI systémů s označením, kde a kdy byly detekovány."
                                },
                            ].map((item, i) => (
                                <div key={i} className="flex gap-4 items-start">
                                    <div className="mt-0.5 flex-shrink-0 w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center">
                                        {item.icon}
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-white">{item.title}</h3>
                                        <p className="text-sm text-slate-400 mt-0.5">{item.desc}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* CTA */}
                    <div className="mt-12 sm:mt-16 text-center">
                        <div className="glass inline-block px-8 sm:px-12 py-8 sm:py-10 max-w-2xl">
                            <h3 className="text-xl sm:text-2xl font-bold mb-3">
                                Chcete kompletní přehled?
                            </h3>
                            <p className="text-slate-400 mb-6">
                                Registrujte se a&nbsp;my spustíme <strong className="text-white">24hodinový hloubkový scan</strong> vašeho webu.
                                O&nbsp;výsledku vás budeme informovat e-mailem.
                            </p>
                            <a href="/registrace" className="btn-primary text-base px-10 py-4 inline-flex items-center gap-2">
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M15.59 14.37a6 6 0 0 1-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 0 0 6.16-12.12A14.98 14.98 0 0 0 9.631 8.41m5.96 5.96a14.926 14.926 0 0 1-5.841 2.58m-.119-8.54a6 6 0 0 0-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 0 0-2.58 5.84m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 0 1-2.448-2.448 14.9 14.9 0 0 1 .06-.312m-2.24 2.39a4.493 4.493 0 0 0-1.757 4.306 4.493 4.493 0 0 0 4.306-1.758M16.5 9a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0Z" /></svg>
                                Registrovat se a spustit 24h scan
                            </a>
                            <p className="text-xs text-slate-500 mt-3">Zdarma • Bez závazků • Výsledek do 24 hodin na email</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* ══════ SOCIAL PROOF ══════ */}
            <section className="border-t border-white/[0.06] py-12 sm:py-20">
                <div className="mx-auto max-w-7xl px-4 sm:px-6">

                    {/* ── Stats counter row ── */}
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-16">
                        {[
                            { value: "500+", label: "Proskenovaných webů", color: "text-neon-fuchsia" },
                            { value: "1 200+", label: "Nalezených AI systémů", color: "text-neon-cyan" },
                            { value: "3,4", label: "Průměr AI systémů na web", color: "text-purple-400" },
                            { value: "94 %", label: "Webů s alespoň 1 AI", color: "text-orange-400" },
                        ].map((stat, i) => (
                            <div key={i} className="glass p-5 sm:p-6 text-center">
                                <p className={`text-3xl sm:text-4xl font-extrabold tracking-tight ${stat.color}`}>
                                    {stat.value}
                                </p>
                                <p className="text-xs sm:text-sm text-slate-500 mt-1">{stat.label}</p>
                            </div>
                        ))}
                    </div>

                    {/* ── Testimonials carousel ── */}
                    <div className="text-center mb-8">
                        <div className="neon-divider mb-6" />
                        <h2 className="text-2xl font-extrabold sm:text-3xl">Co říkají naši <span className="neon-text">klienti</span></h2>
                    </div>
                    <TestimonialCarousel />
                </div>
            </section>

            <section className="border-t border-white/[0.06] py-12 sm:py-20">
                <div className="mx-auto max-w-7xl px-4 sm:px-6">
                    <div className="text-center mb-10 sm:mb-12">
                        <div className="neon-divider mb-6" />
                        <h2 className="text-3xl font-extrabold sm:text-4xl">
                            Proč by vás to mělo <span className="neon-text">zajímat</span>?
                        </h2>
                        <p className="mt-4 text-slate-400 max-w-2xl mx-auto">
                            Od 2. srpna 2026 platí EU AI Act — nejtvrdší regulace umělé inteligence na světě.
                            A týká se i VAŠÍ firmy.
                        </p>
                    </div>

                    {/* First in CZ panel */}
                    <div className="mx-auto max-w-3xl mb-16 rounded-2xl border border-fuchsia-500/20 bg-gradient-to-br from-fuchsia-500/5 via-purple-500/5 to-cyan-500/5 p-5 sm:p-8 text-center">
                        <div className="inline-flex flex-wrap items-center justify-center gap-2 rounded-full bg-fuchsia-500/10 border border-fuchsia-500/20 px-3 sm:px-4 py-1.5 mb-4">
                            <svg className="w-4 h-4 text-neon-fuchsia flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" /></svg>
                            <span className="text-xs sm:text-sm font-semibold text-neon-fuchsia text-center">My jsme průkopníci a lídři AI Act compliance v ČR</span>
                        </div>
                        <h3 className="text-xl font-bold text-white mb-3">Nabízíme nejkomplexnější AI Act řešení na českém trhu</h3>
                        <p className="text-slate-400 leading-relaxed max-w-2xl mx-auto">
                            Kromě nás v Česku neposkytuje nikdo tak ucelený servis — od automatického skenu webu,
                            přes kompletní dokumentaci, až po průběžný monitoring.
                            Od OSVČ a živnostníků, přes e-shopy a střední firmy, až po velké korporáty.
                            My Vám pomůžeme splnit zákon jednoduše a bez stresu.
                            Veškerou dokumentaci a implementaci zařídíme za vás, ať se můžete věnovat dál důležitějším věcem,
                            než je byrokracie z Bruselu. Jako je například Vaše podnikání.
                        </p>
                    </div>
                </div>
            </section>

            {/* ══════ JAK TO FUNGUJE ══════ */}
            <section className="border-t border-white/[0.06] py-12 sm:py-20">
                <div className="mx-auto max-w-7xl px-4 sm:px-6">
                    <div className="text-center mb-12 sm:mb-16">
                        <div className="neon-divider mb-6" />
                        <h2 className="text-3xl font-extrabold sm:text-4xl">
                            Jak to <span className="neon-text">funguje</span>?
                        </h2>
                        <p className="mt-4 text-slate-400">
                            Čtyři jednoduché kroky — a máte vše vyřešeno.
                        </p>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6">
                        {/* Krok 1 */}
                        <div className="glass p-5 sm:p-8 text-center relative">
                            <div className="absolute -top-4 left-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-gradient-to-br from-fuchsia-500 to-purple-600 flex items-center justify-center text-sm font-bold">1</div>
                            <div className="mt-4 mb-4 mx-auto w-12 h-12 sm:w-16 sm:h-16 rounded-2xl bg-fuchsia-500/10 border border-fuchsia-500/20 flex items-center justify-center">
                                <svg className="w-6 h-6 sm:w-8 sm:h-8 text-neon-fuchsia" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" /></svg>
                            </div>
                            <h3 className="text-base sm:text-lg font-semibold mb-2">Sken vašeho webu</h3>
                            <p className="text-xs sm:text-sm text-slate-400">
                                Zadáte adresu webu. Náš robot ho proskenuje
                                a najde všechny AI systémy — zcela zdarma.
                            </p>
                        </div>

                        {/* Krok 2 */}
                        <div className="glass p-5 sm:p-8 text-center relative">
                            <div className="absolute -top-4 left-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-sm font-bold">2</div>
                            <div className="mt-4 mb-4 mx-auto w-12 h-12 sm:w-16 sm:h-16 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
                                <svg className="w-6 h-6 sm:w-8 sm:h-8 text-neon-cyan" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007zM8.625 10.5a.375.375 0 11-.75 0 .375.375 0 01.75 0zm7.5 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" /></svg>
                            </div>
                            <h3 className="text-base sm:text-lg font-semibold mb-2">Vyberete si služby</h3>
                            <p className="text-xs sm:text-sm text-slate-400">
                                Na základě výsledků si zvolíte, co potřebujete.
                                Celý balíček nebo jen vybrané dokumenty.
                            </p>
                        </div>

                        {/* Krok 3 */}
                        <div className="glass p-5 sm:p-8 text-center relative">
                            <div className="absolute -top-4 left-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center text-sm font-bold">3</div>
                            <div className="mt-4 mb-4 mx-auto w-12 h-12 sm:w-16 sm:h-16 rounded-2xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center">
                                <svg className="w-6 h-6 sm:w-8 sm:h-8 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15a2.25 2.25 0 012.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" /></svg>
                            </div>
                            <h3 className="text-base sm:text-lg font-semibold mb-2">Vyplníte dotazník</h3>
                            <p className="text-xs sm:text-sm text-slate-400">
                                AI Act se netýká jen webu — reguluje i interní nástroje (ChatGPT, účetnictví, HR…).
                                Dotazník pokryje celou AI politiku firmy. 5 minut, většinou jen klikáte.
                            </p>
                        </div>

                        {/* Krok 4 */}
                        <div className="glass p-5 sm:p-8 text-center relative">
                            <div className="absolute -top-4 left-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center text-sm font-bold">4</div>
                            <div className="mt-4 mb-4 mx-auto w-12 h-12 sm:w-16 sm:h-16 rounded-2xl bg-green-500/10 border border-green-500/20 flex items-center justify-center">
                                <svg className="w-6 h-6 sm:w-8 sm:h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" /></svg>
                            </div>
                            <h3 className="text-base sm:text-lg font-semibold mb-2">Dostanete dokumenty</h3>
                            <p className="text-xs sm:text-sm text-slate-400">
                                Do 7 dnů obdržíte vše, co váš balíček obsahuje.
                                Kompletní servis — máte vyřešeno, můžete být v klidu.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            <section className="border-t border-white/[0.06] py-12 sm:py-20">
                <div className="mx-auto max-w-7xl px-4 sm:px-6">
                    <div className="text-center mb-10 sm:mb-16">
                        <div className="neon-divider mb-6" />
                        <h2 className="text-3xl font-extrabold sm:text-4xl">
                            Až 12 dokumentů <span className="neon-text">na míru</span>
                        </h2>
                        <p className="mt-4 text-slate-400 max-w-2xl mx-auto">
                            Generujeme jen dokumenty, které vaše firma skutečně potřebuje — podle rizikového profilu.
                            Klikněte na položku pro podrobný popis.
                        </p>
                    </div>

                    <div className="mx-auto max-w-2xl space-y-2">
                        {DELIVERABLES.map((item, i) => (
                            <DeliverableCard key={i} item={item} />
                        ))}
                    </div>
                </div>
            </section>

            <section className="border-t border-white/[0.06] py-12 sm:py-20">
                <div className="mx-auto max-w-3xl px-4 sm:px-6">
                    <div className="text-center mb-10 sm:mb-16">
                        <div className="neon-divider mb-6" />
                        <h2 className="text-3xl font-extrabold sm:text-4xl">Časté <span className="neon-text">otázky</span></h2>
                    </div>

                    <div className="space-y-4">
                        {FAQ_ITEMS.map((item, i) => (
                            <details key={i} className="glass group cursor-pointer">
                                <summary className="flex items-center justify-between font-semibold text-slate-200 list-none">
                                    {item.q}
                                    <svg className="w-5 h-5 text-slate-500 group-open:rotate-180 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                                </summary>
                                <p className="mt-3 text-sm text-slate-400 leading-relaxed">{item.a}</p>
                            </details>
                        ))}
                    </div>
                </div>
            </section>

            <section className="border-t border-white/[0.06] py-12 sm:py-20">
                <div className="mx-auto max-w-3xl px-4 sm:px-6">
                    <div className="text-center mb-10">
                        <div className="neon-divider mb-6" />
                        <h2 className="text-3xl font-extrabold sm:text-4xl">
                            Máte <span className="neon-text">otázku</span>?
                        </h2>
                        <p className="mt-4 text-slate-400 max-w-xl mx-auto">
                            Napište nám nebo zavolejte — poradíme vám nezávazně a zdarma.
                        </p>
                        <div className="flex flex-col sm:flex-row gap-3 justify-center mt-6">
                            <a
                                href="tel:+420732716141"
                                className="inline-flex items-center justify-center gap-2 rounded-xl bg-green-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-green-500/25 hover:bg-green-500 transition"
                            >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 0 0 2.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 0 1-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 0 0-1.091-.852H4.5A2.25 2.25 0 0 0 2.25 4.5v2.25Z" /></svg>
                                +420 732 716 141
                            </a>
                            <a
                                href="mailto:info@aishield.cz"
                                className="inline-flex items-center justify-center gap-2 rounded-xl bg-white/10 border border-white/10 px-5 py-2.5 text-sm font-semibold text-white hover:bg-white/15 transition"
                            >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 0 1-2.25 2.25h-15a2.25 2.25 0 0 1-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25m19.5 0v.243a2.25 2.25 0 0 1-1.07 1.916l-7.5 4.615a2.25 2.25 0 0 1-2.36 0L3.32 8.91a2.25 2.25 0 0 1-1.07-1.916V6.75" /></svg>
                                info@aishield.cz
                            </a>
                        </div>
                    </div>
                    <ContactForm />
                </div>
            </section>

            <section className="border-t border-white/[0.06] py-16 sm:py-24 relative overflow-hidden">
                <div className="absolute inset-0 -z-10">
                    <div className="absolute top-[20%] left-[30%] h-[400px] w-[400px] rounded-full bg-fuchsia-600/8 blur-[100px]" />
                    <div className="absolute bottom-[20%] right-[30%] h-[300px] w-[300px] rounded-full bg-cyan-500/8 blur-[100px]" />
                </div>

                <div className="mx-auto max-w-3xl px-4 sm:px-6 text-center">
                    <h2 className="text-3xl font-extrabold sm:text-4xl">
                        Nečekejte na pokutu.
                    </h2>
                    <p className="mt-4 text-slate-400">
                        Zjistěte stav vašeho webu teď — skenování je <strong className="text-white">zdarma</strong> a trvá méně než minutu.
                    </p>
                    <div className="mt-8 flex justify-center">
                        <a href="/scan" className="btn-primary text-base px-10 py-4">
                            Skenovat můj web ZDARMA
                        </a>
                    </div>

                    {/* Bottom countdown */}
                    <div className="mt-12">
                        <p className="text-sm font-medium uppercase tracking-wider text-red-400 mb-3">
                            Do plné účinnosti AI Act zbývá
                        </p>
                        <Countdown className="" />
                    </div>
                </div>
            </section>
        </>
    );
}
