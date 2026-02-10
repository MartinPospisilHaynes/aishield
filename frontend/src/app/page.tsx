"use client";

import { useState } from "react";
import Countdown from "@/components/countdown";

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
};

/* ─── Deliverables data ─── */
const DELIVERABLES = [
    {
        icon: ICONS.report,
        name: "Compliance Report",
        desc: "Hlavní přehled stavu vašeho webu",
        detail: null,
        bullets: [
            "Přehled všech AI systémů nalezených na vašem webu (chatboty, analytika, doporučovací systémy)",
            "U každého systému jasně napsáno, jestli je v pořádku nebo jestli porušuje zákon",
            "Odkaz na konkrétní článek AI Actu, který se vás týká — v srozumitelné češtině",
            "Celkové hodnocení: jak na tom váš web je a co musíte udělat jako první",
            "Žádný právnický žargon — dokument pochopí i naprostý laik",
        ],
    },
    {
        icon: ICONS.plan,
        name: "Akční plán",
        desc: "Co udělat a do kdy — krok za krokem",
        detail: null,
        bullets: [
            "Konkrétní seznam kroků, které musíte udělat — jako nákupní seznam",
            "U každého kroku jasný termín, do kdy to musí být hotové",
            "Seřazeno podle priority — co je nejdůležitější, to je nahoře",
            "Můžete si odškrtávat splněné body — máte přehled o postupu",
            "Obsahuje i kroky, které za vás může udělat váš webař nebo IT technik",
        ],
    },
    {
        icon: ICONS.registry,
        name: "Registr AI systémů",
        desc: "Evidence vašich AI nástrojů pro úřady",
        detail: null,
        bullets: [
            "Kompletní tabulka všech AI nástrojů, které ve firmě používáte",
            "U každého nástroje: název, co dělá, kdo ho používá a proč",
            "Kategorizace podle rizika — jaký typ systému to je dle AI Actu",
            "Přijde-li kontrola, stačí ukázat tento jeden dokument",
            "Aktualizovatelný — když přidáte nový nástroj, snadno ho dopíšete",
        ],
    },
    {
        icon: ICONS.web,
        name: "Transparenční stránka",
        desc: "Hotová stránka pro váš web",
        detail: null,
        bullets: [
            "Hotový HTML kód stránky — stačí jen vložit na váš web",
            "Přehledně napsáno, jaké AI nástroje používáte a k čemu",
            "Splňuje povinnost transparentnosti dle článku 50 AI Actu",
            "Funguje na WordPress, Shoptet, Webnode, WooCommerce i vlastní weby",
            "Design se automaticky přizpůsobí vašemu webu",
        ],
    },
    {
        icon: ICONS.chatbot,
        name: "Chatbot oznámení",
        desc: "Texty, které musí vidět vaši zákazníci",
        detail: null,
        bullets: [
            "Přesné texty oznámení pro chatboty (Smartsupp, Tidio, LiveChat, Crisp...)",
            "Návštěvník musí vědět, že komunikuje s AI — ne s člověkem",
            "Připravené k okamžitému zkopírování do nastavení chatbotu",
            "Verze v češtině i angličtině (pro zahraniční návštěvníky)",
            "Návod krok za krokem, kam přesně text vložit v administraci chatbotu",
        ],
    },
    {
        icon: ICONS.policy,
        name: "AI politika firmy",
        desc: "Interní pravidla pro vaše zaměstnance",
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
        desc: "Osnova povinného školení o AI",
        detail: null,
        bullets: [
            "Kompletní osnova školení — co musíte s týmem probrat",
            "Témata: co je AI, jaká jsou rizika, co říká zákon, jak AI bezpečně používat",
            "Praktické příklady z praxe srozumitelné i pro neodborníky",
            "Splňuje povinnost dle článku 4 AI Actu (AI gramotnost)",
            "Můžete použít jako podklad pro interní školení nebo e-learning",
        ],
    },
    {
        icon: ICONS.shield,
        name: "Podpora souladu se zákonem",
        desc: "Rozsáhlý balíček podkladů — klid na duši",
        detail: null,
        bullets: [
            "Všech 7 dokumentů dohromady = solidní základ pro soulad s AI Actem",
            "Připraveni na případnou kontrolu ze strany úřadů",
            "Dokumenty můžete vzít k právníkovi — jsou připravené k odborné revizi",
            "Platnost dokumentů se vztahuje na dobu, po kterou používáte dané AI systémy",
        ],
    },
];

/* ─── FAQ data ─── */
const FAQ_ITEMS = [
    {
        q: "Co je AI Act a proč se mě týká?",
        a: "AI Act je nový zákon Evropské unie, který řeší pravidla pro umělou inteligenci. " +
            "Pokud máte na webu chatbot, Google Analytics, doporučovací systém, reklamní pixel nebo jakýkoliv jiný AI nástroj, " +
            "zákon se vás týká. A to i když jste malá firma — třeba kadeřnictví, e-shop nebo řemeslník. " +
            "Představte si to jako GDPR, ale pro umělou inteligenci.",
    },
    {
        q: "Jaké pokuty hrozí?",
        a: "Zákon stanoví tři úrovně pokut. Za nejzávažnější porušení (zakázané AI systémy) až 35 milionů EUR nebo 7 % obratu. " +
            "Za nedodržení povinností (chybějící dokumentace, neoznačený chatbot) až 15 milionů EUR nebo 3 % obratu. " +
            "Za poskytnutí nepravdivých informací úřadům až 7,5 milionu EUR nebo 1 % obratu. " +
            "Pro malé a střední firmy platí nižší hranice, ale i tak jde o statisíce korun.",
    },
    {
        q: "Mám jen malou firmu / e-shop. Opravdu se mě to týká?",
        a: "Ano. Zákon platí pro všechny, kdo v EU provozují AI systémy — bez ohledu na velikost firmy. " +
            "Pokud váš e-shop používá Smartsupp chatbot, Google Analytics nebo doporučování produktů, " +
            "jste povinni to označit a zdokumentovat. My vám s tím pomůžeme jednoduše a bez složitostí.",
    },
    {
        q: "Co když nevím, jestli mám AI na webu?",
        a: "Přesně proto je tu náš scanner. Zadáte adresu webu a za minutu víte, jaké AI nástroje na něm běží. " +
            "Šetří vám čas a peníze za konzultace. Skenování je zcela zdarma.",
    },
    {
        q: "Jak to celé funguje?",
        a: "1) Zadáte adresu svého webu — náš robot ho proskenuje. " +
            "2) Dostanete přehled nalezených AI systémů. " +
            "3) Vyberete si balíček služeb a zaregistrujete se. " +
            "4) Vyplníte krátký dotazník o vaší firmě (jen klikáním, žádné složité psaní). " +
            "5) Během několika hodin obdržíte veškerou dokumentaci.",
    },
    {
        q: "Co musím vyplnit v dotazníku?",
        a: "Dotazník je jednoduchý — většinou jen klikáte na odpovědi. Ptáme se vás na základní věci: " +
            "kolik máte zaměstnanců, jakou činnost provozujete, jestli používáte AI i interně (třeba ChatGPT). " +
            "Bez těchto informací vám nemůžeme připravit dokumenty přesně na míru vaší firmě. " +
            "Vyplnění trvá asi 5 minut.",
    },
    {
        q: "Jaký je deadline?",
        a: "2. srpna 2026 — od tohoto data se AI Act plně vztahuje na všechny AI systémy. " +
            "Zákaz nepřijatelných AI praktik (čl. 5) platí už od února 2025. " +
            "Příprava dokumentace zabere cca 2–4 týdny, nenechávejte to na poslední chvíli.",
    },
    {
        q: "Nahradíte advokáta?",
        a: "Ne — jsme technický nástroj, ne právní poradna. Identifikujeme AI systémy, připravíme dokumentační podklady a akční plány. " +
            "Dokumenty, které od nás dostanete, slouží jako kvalitní základ pro vaši compliance. " +
            "Klidně s nimi můžete navštívit právníka dle vašeho výběru — " +
            "naše dokumenty jsou připravené k odborné revizi.",
    },
    {
        q: "Je skenování webu opravdu zdarma?",
        a: "Ano, skenování je zcela zdarma a nezávazné. " +
            "Nemusíte se nikam registrovat ani zadávat platební údaje. " +
            "Platíte pouze v případě, že se rozhodnete objednat balíček dokumentů.",
    },
];

/* ─── Expandable card component ─── */
function DeliverableCard({ item }: { item: (typeof DELIVERABLES)[0] }) {
    const [open, setOpen] = useState(false);

    return (
        <div
            className="glass p-5 cursor-pointer transition-all duration-300 hover:border-fuchsia-500/30"
            onClick={() => setOpen(!open)}
        >
            <div className="flex items-start gap-4">
                <div className="flex-shrink-0 mt-0.5 w-12 h-12 rounded-xl bg-white/[0.04] border border-white/[0.08] flex items-center justify-center">
                    {item.icon}
                </div>
                <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                        <h4 className="text-sm font-semibold text-slate-200">{item.name}</h4>
                        <svg
                            className={`w-4 h-4 text-slate-500 transition-transform duration-300 flex-shrink-0 ml-2 ${open ? "rotate-180" : ""}`}
                            fill="none" stroke="currentColor" viewBox="0 0 24 24"
                        >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                    </div>
                    <p className="text-xs text-slate-500 mt-1">{item.desc}</p>
                </div>
            </div>
            {open && (
                <div className="mt-4 pt-4 border-t border-white/[0.06]">
                    {item.bullets ? (
                        <ul className="space-y-2">
                            {item.bullets.map((b, i) => (
                                <li key={i} className="flex items-start gap-2 text-sm text-slate-400 leading-relaxed">
                                    <svg className="w-4 h-4 text-fuchsia-400/70 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                                    </svg>
                                    {b}
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="text-sm text-slate-400 leading-relaxed">{item.detail}</p>
                    )}
                </div>
            )}
        </div>
    );
}

/* ═══════════════════════════════════════════
   HOMEPAGE
   ═══════════════════════════════════════════ */
export default function HomePage() {
    return (
        <>
            {/* ══════ HERO ══════ */}
            <section className="relative overflow-hidden">
                {/* BG glow effects */}
                <div className="absolute inset-0 -z-10">
                    <div className="absolute top-[-20%] left-[10%] h-[600px] w-[600px] rounded-full bg-fuchsia-600/10 blur-[120px]" />
                    <div className="absolute bottom-[-10%] right-[10%] h-[500px] w-[500px] rounded-full bg-cyan-500/10 blur-[120px]" />
                </div>

                <div className="mx-auto max-w-7xl px-6 py-20 lg:py-28 text-center">
                    {/* Countdown */}
                    <div className="mb-6">
                        <p className="text-sm font-medium uppercase tracking-wider text-red-400 mb-4">
                            Do platnosti zákona AI Act zbývá
                        </p>
                        <Countdown />
                    </div>

                    {/* Headline */}
                    <h1 className="mx-auto max-w-5xl text-4xl font-extrabold tracking-tight sm:text-6xl lg:text-7xl leading-tight mt-10">
                        Porušuje Váš web{" "}
                        <span className="neon-text">nový zákon EU</span>
                        {" "}o umělé inteligenci?
                    </h1>

                    {/* Subheadline */}
                    <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-400 leading-relaxed">
                        Zjistěte to za minutu. Náš robot proskenuje váš web,
                        najde AI systémy a řekne vám přesně, co musíte udělat.
                        Při nesplnění hrozí pokutou až 35 milionů EUR.
                    </p>

                    {/* Penalty info */}
                    <div className="mx-auto mt-6 max-w-3xl grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
                        <div className="rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3">
                            <span className="font-bold text-red-400">až 35 mil. EUR</span>
                            <p className="text-slate-500 text-xs mt-0.5">za zakázané AI praktiky (7&nbsp;%&nbsp;obratu)</p>
                        </div>
                        <div className="rounded-xl border border-orange-500/20 bg-orange-500/5 px-4 py-3">
                            <span className="font-bold text-orange-400">až 15 mil. EUR</span>
                            <p className="text-slate-500 text-xs mt-0.5">za nesplnění povinností (3&nbsp;%&nbsp;obratu)</p>
                        </div>
                        <div className="rounded-xl border border-yellow-500/20 bg-yellow-500/5 px-4 py-3">
                            <span className="font-bold text-yellow-400">až 7,5 mil. EUR</span>
                            <p className="text-slate-500 text-xs mt-0.5">za nepravdivé informace (1&nbsp;%&nbsp;obratu)</p>
                        </div>
                    </div>

                    {/* CTA — Scanner Input */}
                    <div className="mx-auto mt-10 max-w-xl">
                        <form className="flex gap-3" action="/scan" onSubmit={(e) => {
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
                                className="flex-1 rounded-xl border border-white/10 bg-white/5 px-5 py-3.5 text-white
                                    placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50
                                    focus:border-fuchsia-500/30 backdrop-blur-sm transition-all"
                            />
                            <button type="submit" className="btn-primary whitespace-nowrap text-base px-8">
                                Skenovat ZDARMA
                            </button>
                        </form>
                        <p className="text-xs text-slate-600 mt-2 text-center">Stačí zadat doménu — např. vasefirma.cz</p>
                    </div>
                </div>
            </section>

            {/* ══════ SOCIAL PROOF ══════ */}
            <section className="border-t border-white/[0.06] py-16 sm:py-20">
                <div className="mx-auto max-w-7xl px-6">

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

                    {/* ── Pro koho je AIshield ── */}
                    <div className="text-center mb-8">
                        <p className="text-sm font-medium uppercase tracking-wider text-slate-500">
                            Důvěřují nám firmy napříč obory
                        </p>
                    </div>

                    <div className="flex flex-wrap justify-center gap-3 mb-16">
                        {[
                            { icon: "🏪", label: "E-shopy" },
                            { icon: "⚖️", label: "Advokátní kanceláře" },
                            { icon: "🏭", label: "Výrobní firmy" },
                            { icon: "🏥", label: "Zdravotnictví" },
                            { icon: "🏦", label: "Finance & pojišťovny" },
                            { icon: "🎓", label: "Vzdělávací instituce" },
                            { icon: "🏗️", label: "Stavebnictví" },
                            { icon: "💼", label: "OSVČ & freelancers" },
                            { icon: "🏛️", label: "Veřejná správa" },
                            { icon: "🖥️", label: "IT & startupy" },
                        ].map((item, i) => (
                            <div
                                key={i}
                                className="flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.03] px-4 py-2 text-sm text-slate-400 hover:border-fuchsia-500/20 hover:bg-fuchsia-500/5 transition-colors"
                            >
                                <span className="text-base">{item.icon}</span>
                                {item.label}
                            </div>
                        ))}
                    </div>

                    {/* ── Testimonials ── */}
                    <div className="grid md:grid-cols-3 gap-4 sm:gap-6">
                        {[
                            {
                                quote: "Netušil jsem, že na mém e-shopu běží 5 AI systémů. Díky AIshieldu mám jasno, co musím udělat, než začnou padat pokuty.",
                                author: "Tomáš K.",
                                role: "Majitel e-shopu, Brno",
                                color: "fuchsia",
                            },
                            {
                                quote: "Klient se ptal, jestli je jejich chatbot v souladu se zákonem. Nechal jsem to proskenovat a za hodinu jsem měl odpověď i dokumentaci.",
                                author: "JUDr. Petra M.",
                                role: "Advokátka, Praha",
                                color: "cyan",
                            },
                            {
                                quote: "Jako OSVČ jsem si myslel, že se mě AI Act netýká. Scanner odhalil Google Analytics i Crisp chat — obojí vyžaduje oznámení.",
                                author: "David R.",
                                role: "Freelance vývojář, Olomouc",
                                color: "purple",
                            },
                        ].map((t, i) => (
                            <div key={i} className="glass p-6 flex flex-col">
                                {/* Stars */}
                                <div className="flex gap-0.5 mb-3">
                                    {Array.from({ length: 5 }).map((_, s) => (
                                        <svg key={s} className={`w-4 h-4 ${t.color === "fuchsia" ? "text-fuchsia-400" : t.color === "cyan" ? "text-cyan-400" : "text-purple-400"}`} fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                                        </svg>
                                    ))}
                                </div>

                                {/* Quote */}
                                <p className="text-sm text-slate-300 leading-relaxed flex-1">
                                    &ldquo;{t.quote}&rdquo;
                                </p>

                                {/* Author */}
                                <div className="mt-4 pt-4 border-t border-white/[0.06] flex items-center gap-3">
                                    <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold ${
                                        t.color === "fuchsia" ? "bg-fuchsia-500/15 text-fuchsia-400" :
                                        t.color === "cyan" ? "bg-cyan-500/15 text-cyan-400" :
                                        "bg-purple-500/15 text-purple-400"
                                    }`}>
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
            </section>

            {/* ══════ PROČ BY VÁS TO MĚLO ZAJÍMAT ══════ */}
            <section className="border-t border-white/[0.06] py-20">
                <div className="mx-auto max-w-7xl px-6">
                    <div className="text-center mb-12">
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
                    <div className="mx-auto max-w-3xl mb-16 rounded-2xl border border-fuchsia-500/20 bg-gradient-to-br from-fuchsia-500/5 via-purple-500/5 to-cyan-500/5 p-8 text-center">
                        <div className="inline-flex items-center gap-2 rounded-full bg-fuchsia-500/10 border border-fuchsia-500/20 px-4 py-1.5 mb-4">
                            <svg className="w-4 h-4 text-neon-fuchsia" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" /></svg>
                            <span className="text-sm font-semibold text-neon-fuchsia">Lídři AI Act compliance v ČR</span>
                        </div>
                        <h3 className="text-xl font-bold text-white mb-3">Nejkomplexnější AI Act řešení na českém trhu</h3>
                        <p className="text-slate-400 leading-relaxed max-w-2xl mx-auto">
                            Nikdo v Česku neposkytuje tak ucelený servis — od automatického skenu webu,
                            přes kompletní dokumentaci, až po průběžný monitoring.
                            Od OSVČ a živnostníků, přes e-shopy a střední firmy, až po velké korporáty —
                            pomůžeme vám splnit zákon jednoduše a bez stresu.
                        </p>
                    </div>
                </div>
            </section>

            {/* ══════ JAK TO FUNGUJE ══════ */}
            <section className="border-t border-white/[0.06] py-20">
                <div className="mx-auto max-w-7xl px-6">
                    <div className="text-center mb-16">
                        <div className="neon-divider mb-6" />
                        <h2 className="text-3xl font-extrabold sm:text-4xl">
                            Jak to <span className="neon-text">funguje</span>?
                        </h2>
                        <p className="mt-4 text-slate-400">
                            Čtyři jednoduché kroky — a máte vše vyřešeno.
                        </p>
                    </div>

                    <div className="grid md:grid-cols-4 gap-6">
                        {/* Krok 1 */}
                        <div className="glass p-8 text-center relative">
                            <div className="absolute -top-4 left-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-gradient-to-br from-fuchsia-500 to-purple-600 flex items-center justify-center text-sm font-bold">1</div>
                            <div className="mt-4 mb-4 mx-auto w-16 h-16 rounded-2xl bg-fuchsia-500/10 border border-fuchsia-500/20 flex items-center justify-center">
                                <svg className="w-8 h-8 text-neon-fuchsia" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" /></svg>
                            </div>
                            <h3 className="text-lg font-semibold mb-2">Sken vašeho webu</h3>
                            <p className="text-sm text-slate-400">
                                Zadáte adresu webu. Náš robot ho proskenuje
                                a najde všechny AI systémy — zcela zdarma.
                            </p>
                        </div>

                        {/* Krok 2 */}
                        <div className="glass p-8 text-center relative">
                            <div className="absolute -top-4 left-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-sm font-bold">2</div>
                            <div className="mt-4 mb-4 mx-auto w-16 h-16 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
                                <svg className="w-8 h-8 text-neon-cyan" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.75 10.5V6a3.75 3.75 0 10-7.5 0v4.5m11.356-1.993l1.263 12c.07.665-.45 1.243-1.119 1.243H4.25a1.125 1.125 0 01-1.12-1.243l1.264-12A1.125 1.125 0 015.513 7.5h12.974c.576 0 1.059.435 1.119 1.007zM8.625 10.5a.375.375 0 11-.75 0 .375.375 0 01.75 0zm7.5 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" /></svg>
                            </div>
                            <h3 className="text-lg font-semibold mb-2">Vyberete si služby</h3>
                            <p className="text-sm text-slate-400">
                                Na základě výsledků si zvolíte, co potřebujete.
                                Celý balíček nebo jen vybrané dokumenty.
                            </p>
                        </div>

                        {/* Krok 3 */}
                        <div className="glass p-8 text-center relative">
                            <div className="absolute -top-4 left-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center text-sm font-bold">3</div>
                            <div className="mt-4 mb-4 mx-auto w-16 h-16 rounded-2xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center">
                                <svg className="w-8 h-8 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15a2.25 2.25 0 012.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" /></svg>
                            </div>
                            <h3 className="text-lg font-semibold mb-2">Vyplníte dotazník</h3>
                            <p className="text-sm text-slate-400">
                                Krátký dotazník o vaší firmě — většinou jen klikáte.
                                Díky tomu přípravu dokumentů přesně na míru.
                            </p>
                        </div>

                        {/* Krok 4 */}
                        <div className="glass p-8 text-center relative">
                            <div className="absolute -top-4 left-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center text-sm font-bold">4</div>
                            <div className="mt-4 mb-4 mx-auto w-16 h-16 rounded-2xl bg-green-500/10 border border-green-500/20 flex items-center justify-center">
                                <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" /></svg>
                            </div>
                            <h3 className="text-lg font-semibold mb-2">Dostanete dokumenty</h3>
                            <p className="text-sm text-slate-400">
                                Během pár hodin obdržíte veškerou dokumentaci.
                                Máte solidní základ pro soulad se zákonem.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* ══════ CO DOSTANETE ══════ */}
            <section className="border-t border-white/[0.06] py-20">
                <div className="mx-auto max-w-7xl px-6">
                    <div className="text-center mb-16">
                        <div className="neon-divider mb-6" />
                        <h2 className="text-3xl font-extrabold sm:text-4xl">
                            7 dokumentů v jednom <span className="neon-text">balíčku</span>
                        </h2>
                        <p className="mt-4 text-slate-400 max-w-2xl mx-auto">
                            AI Act Compliance Kit — všechno, co potřebujete na jedno kliknutí.
                            Klikněte na kteroukoliv položku pro podrobný popis.
                        </p>
                    </div>

                    <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        {DELIVERABLES.map((item, i) => (
                            <DeliverableCard key={i} item={item} />
                        ))}
                    </div>
                </div>
            </section>

            {/* ══════ FAQ ══════ */}
            <section className="border-t border-white/[0.06] py-20">
                <div className="mx-auto max-w-3xl px-6">
                    <div className="text-center mb-16">
                        <div className="neon-divider mb-6" />
                        <h2 className="text-3xl font-extrabold">Časté otázky</h2>
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

            {/* ══════ FINAL CTA ══════ */}
            <section className="border-t border-white/[0.06] py-24 relative overflow-hidden">
                <div className="absolute inset-0 -z-10">
                    <div className="absolute top-[20%] left-[30%] h-[400px] w-[400px] rounded-full bg-fuchsia-600/8 blur-[100px]" />
                    <div className="absolute bottom-[20%] right-[30%] h-[300px] w-[300px] rounded-full bg-cyan-500/8 blur-[100px]" />
                </div>

                <div className="mx-auto max-w-3xl px-6 text-center">
                    <h2 className="text-3xl font-extrabold sm:text-4xl">
                        Nečekejte na pokutu.
                    </h2>
                    <p className="mt-4 text-lg text-slate-400">
                        Zjistěte stav vašeho webu teď — skenování je <strong className="text-white">zdarma</strong> a trvá méně než minutu.
                    </p>
                    <div className="mt-8 flex justify-center">
                        <a href="/scan" className="btn-primary text-base px-10 py-4">
                            Skenovat můj web ZDARMA
                        </a>
                    </div>

                    {/* Bottom countdown */}
                    <div className="mt-12">
                        <p className="text-xs font-medium uppercase tracking-wider text-red-400/70 mb-3">
                            Do platnosti AI Act zbývá
                        </p>
                        <Countdown className="scale-[0.85] sm:scale-100" />
                    </div>
                </div>
            </section>
        </>
    );
}
