import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "AI Act compliance pro firmy v Českých Budějovicích a Jihočeském kraji — AIshield.cz",
    description:
        "AIshield pomáhá firmám v Českých Budějovicích a Jihočeském kraji splnit EU AI Act. " +
        "České Budějovice, Tábor, Písek, Strakonice, Jindřichův Hradec, Prachatice.",
    alternates: { canonical: "/pro-koho/ceske-budejovice" },
};

const cities = [
    "České Budějovice", "Tábor", "Písek", "Strakonice",
    "Jindřichův Hradec", "Prachatice", "Český Krumlov", "Třeboň",
    "Blatná", "Milevsko", "Vimperk",
];

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Pro koho", href: "/pro-koho" },
                { label: "České Budějovice" },
            ]}
            title="AI Act compliance pro firmy v Českých Budějovicích"
            titleAccent="a Jihočeském kraji"
            subtitle="Jihočeský kraj — potravinářství, strojírenství, energetika a turistický ruch. AI v těchto odvětvích musí být od srpna 2026 compliant."
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Jihočeský kraj a EU AI Act</h2>
                <div className="space-y-4 text-slate-300">
                    <p>
                        V Jihočeském kraji sídlí firmy jako <strong className="text-white">Budějovický Budvar</strong>,
                        desítky potravinářských podniků, energetických firem (Temelín) a strojírenských závodů.
                        AI se tu stále častěji používá v automatizaci, logistice i e-commerce.
                    </p>
                    <p>
                        Od <strong className="text-white">2. srpna 2026</strong> musí být každý AI systém zdokumentovaný.
                        AIshield to zvládne automaticky — sken webu, identifikace AI, generování dokumentace.
                    </p>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Kdo v Jihočeském kraji musí řešit AI Act</h2>
                <ul className="space-y-3">
                    {[
                        "Potravinářské firmy s AI optimalizací výroby",
                        "Energetické společnosti (ČEZ — Temelín, JE Dukovany)",
                        "E-shopy s chatbotem a doporučováním produktů",
                        "Jihočeská univerzita — výzkumné AI projekty",
                        "Turistický průmysl — AI chatboty, rezervační systémy (Český Krumlov)",
                        "Zemědělské podniky s precision farming a AI",
                        "Strojírenské firmy s prediktivní údržbou",
                    ].map((item) => (
                        <li key={item} className="flex items-start gap-3">
                            <span className="text-fuchsia-400 mt-0.5">→</span>
                            <span className="text-slate-300">{item}</span>
                        </li>
                    ))}
                </ul>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Pokrytá města</h2>
                <div className="flex flex-wrap gap-2">
                    {cities.map((city) => (
                        <span key={city} className="rounded-full border border-slate-700/50 bg-slate-800/30 px-3 py-1 text-sm text-slate-300">{city}</span>
                    ))}
                </div>
            </section>

            <section>
                <div className="rounded-xl border border-fuchsia-500/30 bg-gradient-to-r from-fuchsia-900/20 to-cyan-900/20 p-8 text-center">
                    <h2 className="text-2xl font-bold text-white mb-3">Bezplatný AI Act sken</h2>
                    <p className="text-slate-400 mb-6 max-w-lg mx-auto">60 sekund — bez registrace, zdarma.</p>
                    <Link href="/scan" className="inline-block rounded-lg bg-fuchsia-600 px-8 py-3 font-semibold text-white hover:bg-fuchsia-500 transition-colors">Spustit bezplatný sken →</Link>
                </div>
            </section>
        </ContentPage>
    );
}
