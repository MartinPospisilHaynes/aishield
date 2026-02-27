export default function AboutPage() {
    return (
        <section className="py-20 relative">
            {/* BG glow */}
            <div className="absolute inset-0 -z-10">
                <div className="absolute top-[10%] left-[30%] h-[400px] w-[400px] rounded-full bg-fuchsia-500/5 blur-[130px]" />
            </div>
            <div className="mx-auto max-w-3xl px-6">
                <h1 className="text-3xl font-extrabold">Jak to funguje</h1>

                <div className="mt-8 prose prose-invert max-w-none prose-headings:text-white prose-p:text-slate-300 prose-li:text-slate-300 prose-strong:text-white prose-a:text-neon-fuchsia">
                    <h2>Co je AI Act?</h2>
                    <p>
                        AI Act (Nařízení EU 2024/1689) je první komplexní zákon na světě,
                        který reguluje umělou inteligenci. Je to obdoba GDPR, ale pro AI.
                        Platí pro <strong>každou firmu v EU</strong>, která používá nebo
                        nasazuje AI systémy.
                    </p>

                    <h2>Týká se to mé firmy?</h2>
                    <p>Pokud máte na webu cokoliv z tohoto, tak <strong>ANO</strong>:</p>
                    <ul>
                        <li>🤖 Chatbot (Smartsupp, Tidio, LiveAgent...)</li>
                        <li>📊 AI analytiku (Google Analytics 4 s ML predikcemi)</li>
                        <li>🛒 AI doporučovací systém (e-shop &quot;mohlo by se vám líbit&quot;)</li>
                        <li>📝 AI generovaný obsah (texty, obrázky)</li>
                        <li>🎯 AI cílení reklam</li>
                    </ul>

                    <h2>Jaké jsou pokuty?</h2>
                    <ul>
                        <li><strong>35 milionů EUR / 7% obratu</strong> — zakázané AI praktiky (čl. 5)</li>
                        <li><strong>15 milionů EUR / 3% obratu</strong> — porušení povinností nasazovače (čl. 26, 50)</li>
                        <li><strong>7,5 milionu EUR / 1% obratu</strong> — nepravdivé informace</li>
                    </ul>

                    <h2>Klíčové deadliny</h2>
                    <ul>
                        <li>✅ <strong>2. února 2025</strong> — AI gramotnost (čl. 4) + zakázané praktiky (čl. 5) — JIŽ PLATÍ!</li>
                        <li>⚠️ <strong>2. srpna 2026</strong> — Transparenční povinnosti (čl. 50) + povinnosti nasazovačů (čl. 26)</li>
                    </ul>

                    <h2>Co AIshield dělá?</h2>
                    <ol>
                        <li>Proskenuje váš web a najde všechny AI systémy</li>
                        <li>Klasifikuje rizika podle AI Act</li>
                        <li>Vygeneruje kompletní dokumentaci</li>
                        <li>Dodá widget pro transparenční oznámení</li>
                        <li>Měsíčně monitoruje změny</li>
                    </ol>
                </div>
            </div>
        </section>
    );
}
