"use client";

import ContactForm from "@/components/contact-form";
import ScrollReveal from "@/components/scroll-reveal";

export default function AboutPage() {
    return (
        <section className="py-20 relative">
            {/* BG glow */}
            <div className="absolute inset-0 -z-10">
                <div className="absolute top-[10%] left-[30%] h-[400px] w-[400px] rounded-full bg-fuchsia-600/8 blur-[120px]" />
            </div>

            <div className="mx-auto max-w-3xl px-6">
                <ScrollReveal variant="fade-up" delay={0}>
                    <h1 className="text-3xl font-bold text-white">Jak to funguje</h1>
                </ScrollReveal>

                <div className="mt-8 max-w-none space-y-8 text-slate-300 leading-relaxed">
                    <ScrollReveal variant="fade-up" delay={1}>
                        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                            <h2 className="text-xl font-semibold text-white mb-3">Co je AI Act?</h2>
                            <p className="text-slate-400 mb-3">
                                <a href="https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689" target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:text-cyan-300 underline underline-offset-2 font-semibold transition-colors">AI Act (Nařízení EU 2024/1689)</a> je první komplexní zákon na světě,
                                který reguluje umělou inteligenci. Je to obdoba GDPR, ale pro AI.
                                Platí pro <strong className="text-white">každou firmu v EU</strong>, která používá nebo
                                nasazuje AI systémy.
                            </p>
                            <p className="text-slate-400 mb-3">
                                Většina firem přitom <strong className="text-white">ani netuší, že na jejich webu AI běží</strong>.
                                Spousta pluginů a nástrojů třetích stran používá umělou inteligenci v pozadí —
                                chatboty, analytika, doporučovací systémy nebo antispam. Některé se na webu
                                objeví automaticky po aktualizaci platformy (WordPress, Shoptet, Shopify),
                                bez vědomí provozovatele.
                            </p>
                            <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4">
                                <p className="text-red-400 font-semibold">
                                    To, že jste AI systém na web vědomě nenasadili, neznamená, že tam není.
                                    A pokud tam je a není správně označen — je to porušení AI Act
                                    a hrozí vám pokuta.
                                </p>
                            </div>
                        </div>
                    </ScrollReveal>

                    <ScrollReveal variant="slide-left" delay={1}>
                        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                            <h2 className="text-xl font-semibold text-white mb-3">Týká se to mé firmy?</h2>
                            <p className="text-slate-400 mb-3">Pokud máte na webu cokoliv z tohoto, tak <strong className="text-white">ANO</strong>:</p>
                            <ul className="space-y-2 text-slate-400">
                                <li className="flex items-start gap-2">
                                    <svg className="w-5 h-5 text-fuchsia-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H8.25m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0H12m4.125 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 0 1-2.555-.337A5.972 5.972 0 0 1 5.41 20.97a5.969 5.969 0 0 1-.474-.065 4.48 4.48 0 0 0 .978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25Z" /></svg>
                                    <span>Chatbot (Smartsupp, Tidio, LiveAgent, Crisp...)</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <svg className="w-5 h-5 text-cyan-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" /></svg>
                                    <span>AI analytiku (Google Analytics 4 s ML predikcemi, Hotjar)</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <svg className="w-5 h-5 text-amber-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 0 0-3 3h15.75m-12.75-3h11.218c1.121-2.3 2.1-4.684 2.924-7.138a60.114 60.114 0 0 0-16.536-1.84M7.5 14.25 5.106 5.272M6 20.25a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Zm12.75 0a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Z" /></svg>
                                    <span>AI doporučovací systém (e-shop &quot;mohlo by se vám líbit&quot;)</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <svg className="w-5 h-5 text-purple-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909M2.25 18V6a2.25 2.25 0 0 1 2.25-2.25h15A2.25 2.25 0 0 1 21.75 6v12A2.25 2.25 0 0 1 19.5 20.25H4.5A2.25 2.25 0 0 1 2.25 18Z" /></svg>
                                    <span>AI generovaný obsah (texty, obrázky, překlady)</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <svg className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" /><path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1 1 15 0Z" /></svg>
                                    <span>AI cílení reklam (Google Performance Max, Meta Advantage+)</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <svg className="w-5 h-5 text-red-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" /></svg>
                                    <span>AI antispam a bezpečnostní filtry (reCAPTCHA, Cloudflare Bot Management)</span>
                                </li>
                            </ul>
                        </div>
                    </ScrollReveal>

                    <ScrollReveal variant="slide-right" delay={1}>
                        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                            <h2 className="text-xl font-semibold text-white mb-3">Jaké jsou pokuty?</h2>
                            <ul className="space-y-2 text-slate-400">
                                <li><strong className="text-white">35 milionů EUR / 7% obratu</strong> — zakázané AI praktiky (čl. 5)</li>
                                <li><strong className="text-white">15 milionů EUR / 3% obratu</strong> — porušení povinností nasazovače (čl. 26, 50)</li>
                                <li><strong className="text-white">7,5 milionu EUR / 1% obratu</strong> — nepravdivé informace</li>
                            </ul>
                        </div>
                    </ScrollReveal>

                    <ScrollReveal variant="fade-up" delay={1}>
                        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                            <h2 className="text-xl font-semibold text-white mb-3">Klíčové deadliny</h2>
                            <ul className="space-y-2 text-slate-400">
                                <li className="flex items-start gap-2">
                                    <svg className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
                                    <span><strong className="text-white">2. února 2025</strong> — AI gramotnost (čl. 4) + zakázané praktiky (čl. 5) — JIŽ PLATÍ!</span>
                                </li>
                                <li className="flex items-start gap-2">
                                    <svg className="w-5 h-5 text-orange-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" /></svg>
                                    <span><strong className="text-white">2. srpna 2026</strong> — Transparenční povinnosti (čl. 50) + povinnosti nasazovačů (čl. 26)</span>
                                </li>
                            </ul>
                        </div>
                    </ScrollReveal>

                    <ScrollReveal variant="slide-left" delay={1}>
                        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                            <h2 className="text-xl font-semibold text-white mb-3">Co AIshield dělá?</h2>
                            <ol className="space-y-2 text-slate-400 list-decimal list-inside">
                                <li>Proskenuje váš web a najde všechny AI systémy</li>
                                <li>Klasifikuje rizika podle AI Act</li>
                                <li>Vygeneruje kompletní dokumentační podklady (AI Act Compliance Kit)</li>
                                <li>Připraví hotovou HTML šablonu transparenční stránky pro váš web</li>
                                <li>U balíčku PRO: technická asistence s implementací na váš web</li>
                                <li>Vše doručíme i v tištěné podobě v profesionální vazbě do 14 dnů</li>
                            </ol>
                            <p className="text-slate-500 text-sm mt-3">
                                Volitelně: měsíční monitoring webu — automaticky hlídáme,
                                zda se na vašem webu neobjevily nové AI systémy.{" "}
                                <a href="/pricing" className="text-neon-fuchsia hover:underline">Více v ceníku →</a>
                            </p>
                        </div>
                    </ScrollReveal>

                    {/* Právní upozornění */}
                    <ScrollReveal variant="scale-up" delay={1}>
                        <div className="rounded-2xl border border-orange-500/20 bg-orange-500/5 p-6">
                            <h2 className="text-xl font-semibold text-white mb-3">Důležité upozornění</h2>
                            <p className="text-slate-400 mb-3">
                                AIshield.cz je <strong className="text-white">automatizovaný technický nástroj</strong>,
                                nikoliv právní služba. Výstupy slouží jako kvalitní podklad pro vaši compliance —
                                nejsou individuálním právním posouzením.
                            </p>
                            <div className="rounded-xl border border-green-500/20 bg-green-500/5 p-4 mb-3">
                                <p className="text-green-400 font-medium text-sm">
                                    <strong className="text-green-300">Potřebujete právníka nebo úřední razítko?</strong>{" "}
                                    Pokud máte na webu vše řádně splněno a disponujete kompletní dokumentací,
                                    kterou vám dodáme (AI Act Compliance Kit + transparenční stránka),{" "}
                                    <strong className="text-green-300">právník ani úřední razítko nejsou potřeba</strong>.{" "}
                                    AI Act vyžaduje transparentnost a dokumentaci — a přesně to vám připravíme.
                                </p>
                            </div>
                            <p className="text-slate-500 text-sm">
                                Samozřejmě, pokud chcete, klidně s našimi výstupy můžete navštívit
                                právníka dle vašeho výběru. Podrobnosti v{" "}
                                <a href="/terms" className="text-neon-fuchsia hover:underline">obchodních podmínkách</a>.
                            </p>
                        </div>
                    </ScrollReveal>

                    {/* Kontaktní CTA */}
                    <ScrollReveal variant="fade-up" delay={1}>
                        <div className="rounded-2xl border border-cyan-500/20 bg-cyan-500/5 p-6">
                            <h2 className="text-xl font-semibold text-white mb-2 text-center">Nejste si jistí? Ozvěte se nám</h2>
                            <p className="text-slate-400 text-sm text-center mb-5">
                                Rádi vám poradíme po telefonu nebo e-mailem — nezávazně a zdarma.
                            </p>
                            <div className="flex flex-col sm:flex-row gap-3 justify-center">
                                <a
                                    href="tel:+420732716141"
                                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-green-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-green-500/25 hover:bg-green-500 transition"
                                >
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 0 0 2.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 0 1-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 0 0-1.091-.852H4.5A2.25 2.25 0 0 0 2.25 4.5v2.25Z" /></svg>
                                    Zavolejte: +420 732 716 141
                                </a>
                                <a
                                    href="mailto:info@aishield.cz"
                                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-white/10 border border-white/10 px-6 py-3 text-sm font-semibold text-white hover:bg-white/15 transition"
                                >
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 0 1-2.25 2.25h-15a2.25 2.25 0 0 1-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25m19.5 0v.243a2.25 2.25 0 0 1-1.07 1.916l-7.5 4.615a2.25 2.25 0 0 1-2.36 0L3.32 8.91a2.25 2.25 0 0 1-1.07-1.916V6.75" /></svg>
                                    Napište: info@aishield.cz
                                </a>
                            </div>
                        </div>
                    </ScrollReveal>

                    {/* CTA sekce */}
                    <ScrollReveal variant="scale-up" delay={1}>
                        <div className="rounded-2xl border border-fuchsia-500/20 bg-fuchsia-500/5 p-6 text-center space-y-4">
                            <h2 className="text-xl font-semibold text-white">Chcete zjistit, jak jste na tom?</h2>
                            <p className="text-slate-400 text-sm">
                                Spusťte bezplatný sken vašeho webu a za 30 sekund zjistíte, které AI systémy používáte
                                a co musíte řešit.
                            </p>
                            <div className="flex flex-col sm:flex-row gap-3 justify-center pt-2">
                                <a
                                    href="/scan"
                                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-fuchsia-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-fuchsia-500/25 hover:bg-fuchsia-500 transition"
                                >
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                    </svg>
                                    Skenovat web ZDARMA
                                </a>
                                <a
                                    href="/pricing"
                                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-white/10 border border-white/10 px-6 py-3 text-sm font-medium text-white hover:bg-white/15 transition"
                                >
                                    Zobrazit ceník →
                                </a>
                            </div>
                        </div>
                    </ScrollReveal>

                    {/* Konzultační formulář */}
                    <ScrollReveal variant="fade-up" delay={1}>
                        <ContactForm />
                    </ScrollReveal>
                </div>
            </div>
        </section>
    );
}
