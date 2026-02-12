import { Metadata } from "next";

export const metadata: Metadata = {
    title: "AI Act Souhlas — AIshield.cz",
    description:
        "Informace o použití umělé inteligence na AIshield.cz dle požadavků EU AI Act (Nařízení 2024/1689).",
};

export default function AiActSouhlasPage() {
    return (
        <section className="py-20 relative">
            <div className="absolute inset-0 -z-10">
                <div className="absolute top-[10%] left-[20%] h-[400px] w-[400px] rounded-full bg-cyan-600/8 blur-[120px]" />
            </div>

            <div className="mx-auto max-w-3xl px-6">
                <h1 className="text-3xl font-bold text-white">
                    Transparenční oznámení o AI (AI Act)
                </h1>
                <p className="mt-2 text-sm text-slate-500">
                    Dle čl. 50 Nařízení EU 2024/1689 (AI Act) — účinnost od 2. srpna 2026
                </p>

                <div className="mt-8 space-y-8 text-slate-300 leading-relaxed">
                    {/* Úvod */}
                    <div className="rounded-2xl border border-cyan-500/20 bg-gradient-to-br from-cyan-500/5 via-purple-500/5 to-fuchsia-500/5 p-6 text-center">
                        <p className="text-slate-300 leading-relaxed">
                            V souladu s požadavky EU AI Act (Nařízení 2024/1689) vás transparentně
                            informujeme o tom, jaké systémy umělé inteligence používáme na našem webu
                            a jakým způsobem s nimi zacházíme.
                        </p>
                    </div>

                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-xl font-semibold text-white mb-3">1. AI systémy na AIshield.cz</h2>
                        <p className="text-slate-400 mb-4">Na našem webu a v rámci našich služeb využíváme následující AI systémy:</p>

                        <div className="space-y-4">
                            <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
                                <h3 className="font-semibold text-slate-200 mb-1">AI Scanner webu</h3>
                                <p className="text-sm text-slate-400">
                                    <strong className="text-slate-300">Účel:</strong> Automatická detekce AI systémů na webových stránkách klientů.<br />
                                    <strong className="text-slate-300">Kategorie:</strong> Systém s omezeným rizikem dle AI Act.<br />
                                    <strong className="text-slate-300">Poskytovatel:</strong> Vlastní řešení AIshield.cz.<br />
                                    <strong className="text-slate-300">Lidský dohled:</strong> Výsledky jsou verifikovány AI klasifikací (Claude AI) a podléhají ověření klientem.
                                </p>
                            </div>

                            <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
                                <h3 className="font-semibold text-slate-200 mb-1">Claude AI (Anthropic)</h3>
                                <p className="text-sm text-slate-400">
                                    <strong className="text-slate-300">Účel:</strong> Klasifikace nalezených AI systémů, generování compliance dokumentace.<br />
                                    <strong className="text-slate-300">Kategorie:</strong> AI systém obecného účelu.<br />
                                    <strong className="text-slate-300">Poskytovatel:</strong> Anthropic, PBC (USA, přenos dle EU-US Data Privacy Framework).<br />
                                    <strong className="text-slate-300">Data:</strong> Zpracováváme pouze technické údaje z veřejně dostupných webových stránek. Osobní data nejsou do AI systému předávána.
                                </p>
                            </div>

                            <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
                                <h3 className="font-semibold text-slate-200 mb-1">OpenAI</h3>
                                <p className="text-sm text-slate-400">
                                    <strong className="text-slate-300">Účel:</strong> Analýza AI systémů a generování compliance dokumentace.<br />
                                    <strong className="text-slate-300">Kategorie:</strong> AI systém obecného účelu.<br />
                                    <strong className="text-slate-300">Poskytovatel:</strong> OpenAI, L.L.C. (USA, přenos dle EU-US Data Privacy Framework).<br />
                                    <strong className="text-slate-300">Data:</strong> Zpracováváme pouze technické údaje z veřejně dostupných webových stránek. Osobní data nejsou do AI systému předávána.
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-xl font-semibold text-white mb-3">2. Vaše práva</h2>
                        <ul className="space-y-2 text-slate-400">
                            <li className="flex items-start gap-2">
                                <svg className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
                                <span><strong className="text-white">Právo na informace</strong> — víte, že interagujete s AI systémem</span>
                            </li>
                            <li className="flex items-start gap-2">
                                <svg className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
                                <span><strong className="text-white">Právo na vysvětlení</strong> — můžete se nás zeptat, jak AI systém dospěl k výsledku</span>
                            </li>
                            <li className="flex items-start gap-2">
                                <svg className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
                                <span><strong className="text-white">Právo na lidský přezkum</strong> — výsledky skenu můžete manuálně potvrdit nebo zamítnout</span>
                            </li>
                            <li className="flex items-start gap-2">
                                <svg className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
                                <span><strong className="text-white">Právo na námitku</strong> — můžete vznést námitku proti rozhodnutí AI systému</span>
                            </li>
                        </ul>
                    </div>

                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-xl font-semibold text-white mb-3">3. Právní základ</h2>
                        <p className="text-slate-400 mb-3">
                            Toto oznámení je zveřejněno v souladu s:
                        </p>
                        <ul className="space-y-2 text-slate-400 text-sm">
                            <li className="flex items-start gap-2">
                                <span className="text-cyan-400 mt-0.5">§</span>
                                <span>
                                    <a href="https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689" target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:text-cyan-300 underline">
                                        Nařízení EU 2024/1689 (AI Act)
                                    </a>{" "}
                                    — čl. 50 (transparenční povinnosti)
                                </span>
                            </li>
                            <li className="flex items-start gap-2">
                                <span className="text-cyan-400 mt-0.5">§</span>
                                <span>
                                    <a href="https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689" target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:text-cyan-300 underline">
                                        Nařízení EU 2024/1689 (AI Act)
                                    </a>{" "}
                                    — čl. 26 (povinnosti nasazovačů)
                                </span>
                            </li>
                            <li className="flex items-start gap-2">
                                <span className="text-cyan-400 mt-0.5">§</span>
                                <span>
                                    <a href="https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689" target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:text-cyan-300 underline">
                                        Nařízení EU 2024/1689 (AI Act)
                                    </a>{" "}
                                    — čl. 4 (AI gramotnost)
                                </span>
                            </li>
                        </ul>
                    </div>

                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-xl font-semibold text-white mb-3">4. Kontakt</h2>
                        <p className="text-slate-400">
                            Máte dotaz ohledně používání AI na našem webu? Kontaktujte nás:{" "}
                        </p>
                        <ul className="mt-3 space-y-1 text-sm text-slate-400">
                            <li>
                                <a href="mailto:info@aishield.cz" className="text-neon-fuchsia hover:underline">info@aishield.cz</a>
                            </li>
                            <li>
                                <a href="tel:+420732716141" className="text-neon-cyan hover:underline">+420 732 716 141</a>
                            </li>
                        </ul>
                    </div>

                    {/* Poznámka */}
                    <div className="rounded-2xl border border-fuchsia-500/20 bg-fuchsia-500/5 p-6 text-center">
                        <p className="text-slate-400 text-sm">
                            <strong className="text-white">Tato stránka je zároveň vzorem</strong> toho, jak by měla
                            transparenční stránka vypadat na vašem webu. Přesně takovou vám připravíme
                            v rámci AI Act Compliance Kitu.{" "}
                            <a href="/pricing" className="text-neon-fuchsia hover:underline">Více v ceníku →</a>
                        </p>
                    </div>
                </div>
            </div>
        </section>
    );
}
