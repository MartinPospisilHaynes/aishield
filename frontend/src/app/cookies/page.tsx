import { Metadata } from "next";

export const metadata: Metadata = {
    title: "Zásady používání cookies",
    description:
        "Informace o používání cookies na AIshield.cz. Jaké cookies používáme, proč a jak je spravovat.",
    alternates: { canonical: "/cookies" },
    openGraph: {
        title: "Zásady používání cookies — AIshield.cz",
        description: "Jaké cookies používáme na AIshield.cz a proč. Nastavení a správa souhlasu.",
    },
};

export default function CookiesPage() {
    return (
        <section className="py-20 relative">
            <div className="absolute inset-0 -z-10">
                <div className="absolute top-[10%] left-[20%] h-[400px] w-[400px] rounded-full bg-amber-600/8 blur-[120px]" />
            </div>

            <div className="mx-auto max-w-3xl px-6">
                <h1 className="text-3xl font-bold text-white">
                    Zásady používání cookies
                </h1>
                <p className="mt-2 text-sm text-slate-500">
                    Poslední aktualizace: 14. února 2026 &bull; Verze 1.0
                </p>

                <div className="mt-8 prose prose-invert max-w-none space-y-8 text-slate-300 leading-relaxed">
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-xl font-semibold text-white mb-3">Co jsou cookies?</h2>
                        <p className="text-slate-400">
                            Cookies jsou malé textové soubory, které se ukládají do vašeho prohlížeče při
                            návštěvě webových stránek. Slouží k zapamatování vašich preferencí, analýze
                            návštěvnosti a zajištění správného fungování webu.
                        </p>
                    </div>

                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-xl font-semibold text-white mb-3">Jaké cookies používáme?</h2>

                        <h3 className="text-lg font-medium text-slate-200 mt-4 mb-2">1. Nezbytné cookies</h3>
                        <p className="text-slate-400 mb-2">
                            Tyto cookies jsou nutné pro základní fungování webu. Nelze je vypnout.
                        </p>
                        <ul className="space-y-1 text-sm text-slate-500">
                            <li className="flex items-start gap-2">
                                <span className="text-fuchsia-400/70 mt-0.5">•</span>
                                <span><strong className="text-slate-300">consent_preferences</strong> — uložení vašeho souhlasu s cookies (12 měsíců)</span>
                            </li>
                            <li className="flex items-start gap-2">
                                <span className="text-fuchsia-400/70 mt-0.5">•</span>
                                <span><strong className="text-slate-300">session</strong> — identifikátor relace pro správné fungování skeneru (do zavření prohlížeče)</span>
                            </li>
                        </ul>

                        <h3 className="text-lg font-medium text-slate-200 mt-6 mb-2">2. Analytické cookies</h3>
                        <p className="text-slate-400 mb-2">
                            Pomáhají nám pochopit, jak návštěvníci web používají. Data jsou anonymizována.
                        </p>
                        <ul className="space-y-1 text-sm text-slate-500">
                            <li className="flex items-start gap-2">
                                <span className="text-cyan-400/70 mt-0.5">•</span>
                                <span><strong className="text-slate-300">Vercel Analytics</strong> — anonymní data o návštěvnosti (bez sledovacích cookies třetích stran)</span>
                            </li>
                        </ul>

                        <h3 className="text-lg font-medium text-slate-200 mt-6 mb-2">3. Funkční cookies</h3>
                        <p className="text-slate-400 mb-2">
                            Zlepšují funkcionalitu webu — například zapamatování vyplněného formuláře.
                        </p>
                        <ul className="space-y-1 text-sm text-slate-500">
                            <li className="flex items-start gap-2">
                                <span className="text-green-400/70 mt-0.5">•</span>
                                <span><strong className="text-slate-300">scan_history</strong> — historie vašich skenů pro snazší návrat k výsledkům (30 dní)</span>
                            </li>
                        </ul>
                    </div>

                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-xl font-semibold text-white mb-3">Jak spravovat cookies?</h2>
                        <p className="text-slate-400 mb-3">
                            Při první návštěvě webu se zobrazí banner, kde můžete cookies přijmout nebo
                            odmítnout. Svůj souhlas můžete kdykoliv změnit:
                        </p>
                        <ul className="space-y-2 text-slate-400 text-sm">
                            <li className="flex items-start gap-2">
                                <span className="text-fuchsia-400">1.</span>
                                <span>V nastavení prohlížeče — můžete smazat nebo zablokovat cookies</span>
                            </li>
                            <li className="flex items-start gap-2">
                                <span className="text-fuchsia-400">2.</span>
                                <span>Vymazáním cookies v prohlížeči se banner zobrazí znovu</span>
                            </li>
                        </ul>
                    </div>

                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-xl font-semibold text-white mb-3">Cookies třetích stran</h2>
                        <p className="text-slate-400">
                            AIshield.cz <strong className="text-white">nepoužívá</strong> sledovací cookies třetích stran
                            (Facebook Pixel, Google Ads apod.). Nesbíráme data pro reklamní účely.
                            Používáme pouze Vercel Analytics s anonymizovanými daty bez cookies.
                        </p>
                    </div>

                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-xl font-semibold text-white mb-3">Kontakt</h2>
                        <p className="text-slate-400">
                            Máte dotaz ohledně cookies? Kontaktujte nás na{" "}
                            <a href="mailto:info@aishield.cz" className="text-neon-fuchsia hover:underline">info@aishield.cz</a>.
                        </p>
                    </div>

                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-xl font-semibold text-white mb-3">Související dokumenty</h2>
                        <ul className="space-y-2 text-slate-400 text-sm">
                            <li>
                                <a href="/privacy" className="text-neon-fuchsia hover:underline">Ochrana soukromí</a>{" "}
                                — zásady zpracování osobních údajů
                            </li>
                            <li>
                                <a href="/gdpr" className="text-neon-fuchsia hover:underline">GDPR</a>{" "}
                                — informace o zpracování osobních údajů dle GDPR
                            </li>
                            <li>
                                <a href="/terms" className="text-neon-fuchsia hover:underline">Obchodní podmínky</a>{" "}
                                — všeobecné obchodní podmínky služby
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </section>
    );
}
