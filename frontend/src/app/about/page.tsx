export default function AboutPage() {
    return (
        <section className="py-20 relative">
            {/* BG glow */}
            <div className="absolute inset-0 -z-10">
                <div className="absolute top-[10%] left-[30%] h-[400px] w-[400px] rounded-full bg-fuchsia-600/8 blur-[120px]" />
            </div>

            <div className="mx-auto max-w-3xl px-6">
                <h1 className="text-3xl font-bold text-white">Jak to funguje</h1>

                <div className="mt-8 max-w-none space-y-8 text-slate-300 leading-relaxed">
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-xl font-semibold text-white mb-3">Co je AI Act?</h2>
                        <p className="text-slate-400">
                            AI Act (Nařízení EU 2024/1689) je první komplexní zákon na světě,
                            který reguluje umělou inteligenci. Je to obdoba GDPR, ale pro AI.
                            Platí pro <strong className="text-white">každou firmu v EU</strong>, která používá nebo
                            nasazuje AI systémy.
                        </p>
                    </div>

                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-xl font-semibold text-white mb-3">Týká se to mé firmy?</h2>
                        <p className="text-slate-400 mb-3">Pokud máte na webu cokoliv z tohoto, tak <strong className="text-white">ANO</strong>:</p>
                        <ul className="space-y-2 text-slate-400">
                            <li>🤖 Chatbot (Smartsupp, Tidio, LiveAgent...)</li>
                            <li>📊 AI analytiku (Google Analytics 4 s ML predikcemi)</li>
                            <li>🛒 AI doporučovací systém (e-shop &quot;mohlo by se vám líbit&quot;)</li>
                            <li>📝 AI generovaný obsah (texty, obrázky)</li>
                            <li>🎯 AI cílení reklam</li>
                        </ul>
                    </div>

                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-xl font-semibold text-white mb-3">Jaké jsou pokuty?</h2>
                        <ul className="space-y-2 text-slate-400">
                            <li><strong className="text-white">35 milionů EUR / 7% obratu</strong> — zakázané AI praktiky (čl. 5)</li>
                            <li><strong className="text-white">15 milionů EUR / 3% obratu</strong> — porušení povinností nasazovače (čl. 26, 50)</li>
                            <li><strong className="text-white">7,5 milionu EUR / 1% obratu</strong> — nepravdivé informace</li>
                        </ul>
                    </div>

                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-xl font-semibold text-white mb-3">Klíčové deadliny</h2>
                        <ul className="space-y-2 text-slate-400">
                            <li>✅ <strong className="text-white">2. února 2025</strong> — AI gramotnost (čl. 4) + zakázané praktiky (čl. 5) — JIŽ PLATÍ!</li>
                            <li>⚠️ <strong className="text-white">2. srpna 2026</strong> — Transparenční povinnosti (čl. 50) + povinnosti nasazovačů (čl. 26)</li>
                        </ul>
                    </div>

                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-xl font-semibold text-white mb-3">Co AIshield dělá?</h2>
                        <ol className="space-y-2 text-slate-400 list-decimal list-inside">
                            <li>Proskenuje váš web a najde všechny AI systémy</li>
                            <li>Klasifikuje rizika podle AI Act</li>
                            <li>Vygeneruje kompletní dokumentaci</li>
                            <li>Dodá widget pro transparenční oznámení</li>
                            <li>Měsíčně monitoruje změny</li>
                        </ol>
                    </div>

                    {/* CTA sekce */}
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
                </div>
            </div>
        </section>
    );
}
