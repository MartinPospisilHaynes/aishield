export default function HomePage() {
    return (
        <>
            {/* ── HERO SEKCE ── */}
            <section className="relative overflow-hidden bg-gradient-to-b from-shield-950 to-shield-900 text-white">
                <div className="mx-auto max-w-7xl px-6 py-24 text-center">
                    {/* Badge */}
                    <div className="mb-6 inline-flex items-center rounded-full border border-shield-400/30 bg-shield-500/10 px-4 py-2 text-sm text-shield-300">
                        ⚠️ Deadline: 2. srpna 2026 — zbývá méně než 6 měsíců
                    </div>

                    {/* Headline */}
                    <h1 className="mx-auto max-w-4xl text-4xl font-extrabold tracking-tight sm:text-6xl">
                        Váš web porušuje{" "}
                        <span className="text-shield-400">nový zákon EU</span>
                        {" "}o umělé inteligenci?
                    </h1>

                    {/* Subheadline */}
                    <p className="mx-auto mt-6 max-w-2xl text-lg text-gray-300">
                        Zjistěte to za <strong>60 sekund</strong>. Náš robot proskenuje váš web,
                        najde AI systémy a řekne vám přesně, co musíte udělat.
                        Pokuta až <strong className="text-danger-500">35 milionů EUR</strong>.
                    </p>

                    {/* CTA — Scanner Input */}
                    <div className="mx-auto mt-10 max-w-xl">
                        <form className="flex gap-3" action="/scan">
                            <input
                                type="url"
                                name="url"
                                placeholder="https://vasefirma.cz"
                                className="flex-1 rounded-lg border-0 bg-white/10 px-4 py-3 text-white
                           placeholder:text-gray-400 focus:ring-2 focus:ring-shield-400
                           backdrop-blur-sm"
                            />
                            <button type="submit" className="btn-primary whitespace-nowrap">
                                🔍 Skenovat ZDARMA
                            </button>
                        </form>
                        <p className="mt-3 text-sm text-gray-400">
                            Žádná registrace. Žádná kreditní karta. Výsledky za 60 sekund.
                        </p>
                    </div>
                </div>
            </section>

            {/* ── JAK TO FUNGUJE ── */}
            <section className="py-20">
                <div className="mx-auto max-w-7xl px-6">
                    <h2 className="text-center text-3xl font-bold text-gray-900">
                        Jak to funguje?
                    </h2>
                    <p className="mx-auto mt-4 max-w-2xl text-center text-gray-500">
                        Tři kroky a víte, na čem jste.
                    </p>

                    <div className="mt-16 grid grid-cols-1 gap-8 md:grid-cols-3">
                        {/* Krok 1 */}
                        <div className="card text-center">
                            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-shield-100 text-3xl">
                                🔍
                            </div>
                            <h3 className="text-lg font-semibold">1. Zadáte URL</h3>
                            <p className="mt-2 text-sm text-gray-500">
                                Zadejte adresu vašeho webu. Náš robot ho proskenuje
                                stejně jako ho vidí váš zákazník.
                            </p>
                        </div>

                        {/* Krok 2 */}
                        <div className="card text-center">
                            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-shield-100 text-3xl">
                                🤖
                            </div>
                            <h3 className="text-lg font-semibold">2. Robot analyzuje</h3>
                            <p className="mt-2 text-sm text-gray-500">
                                Najdeme chatboty, analytiku, AI doporučení — vše,
                                co spadá pod AI Act. Se screenshoty jako důkazy.
                            </p>
                        </div>

                        {/* Krok 3 */}
                        <div className="card text-center">
                            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-shield-100 text-3xl">
                                📋
                            </div>
                            <h3 className="text-lg font-semibold">3. Dostanete řešení</h3>
                            <p className="mt-2 text-sm text-gray-500">
                                Kompletní report + dokumenty + akční plán.
                                Přesně víte, co udělat a do kdy.
                            </p>
                        </div>
                    </div>
                </div>
            </section>

            {/* ── STATISTIKY ── */}
            <section className="bg-shield-950 py-16 text-white">
                <div className="mx-auto max-w-7xl px-6">
                    <div className="grid grid-cols-2 gap-8 md:grid-cols-4 text-center">
                        <div>
                            <div className="text-4xl font-extrabold text-shield-400">35M €</div>
                            <div className="mt-2 text-sm text-gray-400">Maximální pokuta</div>
                        </div>
                        <div>
                            <div className="text-4xl font-extrabold text-shield-400">80 000+</div>
                            <div className="mt-2 text-sm text-gray-400">Dotčených firem v ČR</div>
                        </div>
                        <div>
                            <div className="text-4xl font-extrabold text-shield-400">90%</div>
                            <div className="mt-2 text-sm text-gray-400">Firem o zákonu neví</div>
                        </div>
                        <div>
                            <div className="text-4xl font-extrabold text-shield-400">6 měsíců</div>
                            <div className="mt-2 text-sm text-gray-400">Do hlavního deadline</div>
                        </div>
                    </div>
                </div>
            </section>

            {/* ── CTA ── */}
            <section className="py-20">
                <div className="mx-auto max-w-3xl px-6 text-center">
                    <h2 className="text-3xl font-bold text-gray-900">
                        Nečekejte na pokutu. Zjistěte stav vašeho webu teď.
                    </h2>
                    <p className="mt-4 text-gray-500">
                        Skenování je zdarma a trvá méně než minutu.
                    </p>
                    <div className="mt-8">
                        <a href="/scan" className="btn-primary text-lg px-8 py-4">
                            🔍 Skenovat můj web ZDARMA
                        </a>
                    </div>
                </div>
            </section>
        </>
    );
}
