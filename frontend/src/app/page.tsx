"use client";

import { useState, useEffect } from "react";

function useCountdown() {
    const [days, setDays] = useState(0);
    const [hours, setHours] = useState(0);
    const [mins, setMins] = useState(0);

    useEffect(() => {
        const update = () => {
            const deadline = new Date("2026-08-02T00:00:00Z").getTime();
            const now = Date.now();
            const diff = Math.max(0, deadline - now);
            setDays(Math.floor(diff / 86400000));
            setHours(Math.floor((diff % 86400000) / 3600000));
            setMins(Math.floor((diff % 3600000) / 60000));
        };
        update();
        const id = setInterval(update, 60000);
        return () => clearInterval(id);
    }, []);

    return { days, hours, mins };
}

export default function HomePage() {
    const { days, hours, mins } = useCountdown();

    return (
        <>
            {/* ══════ HERO ══════ */}
            <section className="relative overflow-hidden">
                {/* BG glow effects */}
                <div className="absolute inset-0 -z-10">
                    <div className="absolute top-[-20%] left-[10%] h-[600px] w-[600px] rounded-full bg-fuchsia-600/10 blur-[120px]" />
                    <div className="absolute bottom-[-10%] right-[10%] h-[500px] w-[500px] rounded-full bg-cyan-500/10 blur-[120px]" />
                </div>

                <div className="mx-auto max-w-7xl px-6 py-20 lg:py-32 text-center">
                    {/* Countdown badge */}
                    <div className="mb-8 inline-flex items-center gap-3 rounded-full border border-red-500/30 bg-red-500/10 px-5 py-2.5">
                        <span className="relative flex h-2.5 w-2.5">
                            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75" />
                            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-red-500" />
                        </span>
                        <span className="text-sm font-medium text-red-300">
                            Deadline: 2. srpna 2026 — zbývá{" "}
                            <span className="font-bold text-red-200">{days} dní {hours}h {mins}m</span>
                        </span>
                    </div>

                    {/* Headline */}
                    <h1 className="mx-auto max-w-5xl text-4xl font-extrabold tracking-tight sm:text-6xl lg:text-7xl leading-tight">
                        Váš web porušuje{" "}
                        <span className="neon-text">nový zákon EU</span>
                        {" "}o umělé inteligenci?
                    </h1>

                    {/* Subheadline */}
                    <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-400 leading-relaxed">
                        Zjistěte to za <strong className="text-slate-200">60 sekund</strong>. Náš robot proskenuje váš web,
                        najde AI systémy a řekne vám přesně, co musíte udělat.
                        Pokuta až <strong className="text-red-400">35 milionů EUR</strong>.
                    </p>

                    {/* CTA — Scanner Input */}
                    <div className="mx-auto mt-10 max-w-xl">
                        <form className="flex gap-3" action="/scan">
                            <input
                                type="url"
                                name="url"
                                placeholder="https://vasefirma.cz"
                                className="flex-1 rounded-xl border border-white/10 bg-white/5 px-5 py-3.5 text-white
                                    placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50
                                    focus:border-fuchsia-500/30 backdrop-blur-sm transition-all"
                            />
                            <button type="submit" className="btn-primary whitespace-nowrap text-base px-8">
                                Skenovat ZDARMA
                            </button>
                        </form>
                        <p className="mt-4 text-sm text-slate-500">
                            Žádná registrace. Žádná kreditní karta. Výsledky za 60 sekund.
                        </p>
                    </div>
                </div>
            </section>

            {/* ══════ PROBLÉM ══════ */}
            <section className="border-t border-white/[0.06] py-20">
                <div className="mx-auto max-w-7xl px-6">
                    <div className="text-center mb-16">
                        <div className="neon-divider mb-6" />
                        <h2 className="text-3xl font-extrabold sm:text-4xl">
                            Proč by vás to mělo <span className="text-red-400">zajímat</span>?
                        </h2>
                        <p className="mt-4 text-slate-400 max-w-2xl mx-auto">
                            Od 2. srpna 2026 platí EU AI Act — nejtvrdší regulace umělé inteligence na světě.
                            A týká se i VAŠÍ firmy.
                        </p>
                    </div>

                    <div className="grid md:grid-cols-3 gap-6">
                        <div className="glass p-8">
                            <div className="text-4xl font-extrabold text-red-400 mb-3">35M &euro;</div>
                            <h3 className="text-lg font-semibold mb-2">Maximální pokuta</h3>
                            <p className="text-sm text-slate-400">
                                Nebo 7 % ročního obratu — podle toho, co je vyšší.
                                Nejde o teoretické číslo — EU už pokutuje za GDPR.
                            </p>
                        </div>
                        <div className="glass p-8">
                            <div className="text-4xl font-extrabold text-neon-fuchsia mb-3">80 000+</div>
                            <h3 className="text-lg font-semibold mb-2">Dotčených firem v ČR</h3>
                            <p className="text-sm text-slate-400">
                                Každá firma s chatbotem, analytíkou nebo AI doporučením
                                na webu spadá pod regulaci. To je většina e-shopů a služeb.
                            </p>
                        </div>
                        <div className="glass p-8">
                            <div className="text-4xl font-extrabold text-yellow-400 mb-3">90 %</div>
                            <h3 className="text-lg font-semibold mb-2">Firem o tom neví</h3>
                            <p className="text-sm text-slate-400">
                                O GDPR věděli všichni. O AI Act skoro nikdo. Kdo se připraví
                                teď, má konkurenční výhodu.
                            </p>
                        </div>
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
                            Tři kroky — a víte přesně, na čem jste.
                        </p>
                    </div>

                    <div className="grid md:grid-cols-3 gap-8">
                        {/* Krok 1 */}
                        <div className="glass p-8 text-center relative">
                            <div className="absolute -top-4 left-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-gradient-to-br from-fuchsia-500 to-purple-600 flex items-center justify-center text-sm font-bold">1</div>
                            <div className="mt-4 mb-4 mx-auto w-16 h-16 rounded-2xl bg-fuchsia-500/10 border border-fuchsia-500/20 flex items-center justify-center">
                                <svg className="w-8 h-8 text-neon-fuchsia" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" /></svg>
                            </div>
                            <h3 className="text-lg font-semibold mb-2">Zadáte URL</h3>
                            <p className="text-sm text-slate-400">
                                Zadejte adresu svého webu. Náš robot ho proskenuje
                                stejně jako ho vidí návštěvník.
                            </p>
                        </div>

                        {/* Krok 2 */}
                        <div className="glass p-8 text-center relative">
                            <div className="absolute -top-4 left-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-sm font-bold">2</div>
                            <div className="mt-4 mb-4 mx-auto w-16 h-16 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
                                <svg className="w-8 h-8 text-neon-cyan" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" /></svg>
                            </div>
                            <h3 className="text-lg font-semibold mb-2">AI robot analyzuje</h3>
                            <p className="text-sm text-slate-400">
                                Najdeme chatboty, analytiku, AI doporučení — vše,
                                co spadá pod AI Act. Se screenshoty jako důkazy.
                            </p>
                        </div>

                        {/* Krok 3 */}
                        <div className="glass p-8 text-center relative">
                            <div className="absolute -top-4 left-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center text-sm font-bold">3</div>
                            <div className="mt-4 mb-4 mx-auto w-16 h-16 rounded-2xl bg-green-500/10 border border-green-500/20 flex items-center justify-center">
                                <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" /></svg>
                            </div>
                            <h3 className="text-lg font-semibold mb-2">Dostanete řešení</h3>
                            <p className="text-sm text-slate-400">
                                Kompletní compliance report + 7 dokumentů + akční plán.
                                Přesně víte, co udělat a do kdy.
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
                            7 dokumentů v jednom balíčku
                        </h2>
                        <p className="mt-4 text-slate-400 max-w-2xl mx-auto">
                            Kompletní AI Act Compliance Kit — všechno, co potřebujete na jedno kliknutí.
                        </p>
                    </div>

                    <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        {[
                            { icon: "📊", name: "Compliance Report", desc: "Hlavní report s klasifikací rizik" },
                            { icon: "📋", name: "Akční plán", desc: "Konkrétní kroky s checkboxy a deadliny" },
                            { icon: "🗂️", name: "Registr AI systémů", desc: "Interní evidence dle čl. 49" },
                            { icon: "🌐", name: "Transparenční stránka", desc: "HTML pro váš web (/ai-transparence)" },
                            { icon: "💬", name: "Chatbot oznámení", desc: "Copy-paste texty pro čl. 50" },
                            { icon: "📜", name: "AI politika", desc: "Interní pravidla používání AI" },
                            { icon: "🎓", name: "Školení AI Literacy", desc: "Osnova povinného školení dle čl. 4" },
                            { icon: "🛡️", name: "Plný soulad", desc: "Vše potřebné pro audit" },
                        ].map((item, i) => (
                            <div key={i} className="glass p-5 flex items-start gap-4">
                                <span className="text-2xl flex-shrink-0 mt-0.5">{item.icon}</span>
                                <div>
                                    <h4 className="text-sm font-semibold text-slate-200">{item.name}</h4>
                                    <p className="text-xs text-slate-500 mt-1">{item.desc}</p>
                                </div>
                            </div>
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
                        {[
                            {
                                q: "Týká se AI Act i mé firmy?",
                                a: "Pokud máte na webu chatbot, analytiku, AI doporučení nebo jakýkoliv systém umělé inteligence — ano. Zákon se vztahuje na poskytovatele i provozovatele AI systémů v EU.",
                            },
                            {
                                q: "Co když nemám žádnou AI na webu?",
                                a: "I tehdy vás zákon může ovlivnit — interní používání ChatGPT, AI v účetnictví nebo HR screening spadají pod AI Act. Proto nabízíme i dotazník pro interní AI systémy.",
                            },
                            {
                                q: "Jak přesný je váš scanner?",
                                a: "Náš robot používá 22 signatur pro detekci AI systémů + klasifikaci přes Claude AI. Detekuje chatboty (Smartsupp, Tidio, LiveChat...), analytiku (GA4, Hotjar...) a další AI nástroje.",
                            },
                            {
                                q: "Jaký je deadline?",
                                a: "2. srpna 2026 — od tohoto data se AI Act plně vztahuje na všechny AI systémy. Zákaz nepřijatelných praktik (čl. 5) platí už od února 2025.",
                            },
                            {
                                q: "Nahradíte advokáta?",
                                a: "Ne — jsme technický nástroj, ne právní poradna. Identifikujeme problémy, generujeme dokumenty a akční plány. Pro finální právní revizi doporučujeme advokáta.",
                            },
                        ].map((item, i) => (
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
                    <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center">
                        <a href="/scan" className="btn-primary text-base px-10 py-4">
                            Skenovat můj web ZDARMA
                        </a>
                        <a href="/dotaznik" className="btn-secondary text-base px-10 py-4">
                            Vyplnit dotazník
                        </a>
                    </div>
                    <p className="mt-6 text-sm text-slate-600">
                        Zbývá <span className="text-red-400 font-semibold">{days} dní</span> do plné účinnosti AI Act.
                    </p>
                </div>
            </section>
        </>
    );
}
