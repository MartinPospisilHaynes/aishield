import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "AI Act compliance pro firmy v Liberci a Libereckém kraji — AIshield.cz",
    description:
        "AIshield pomáhá firmám v Liberci a Libereckém kraji splnit EU AI Act — automatický sken, " +
        "transparenční stránka, dokumentace. Liberec, Jablonec nad Nisou, Česká Lípa, Turnov, Semily.",
    alternates: { canonical: "/pro-koho/liberec" },
};

const cities = [
    "Liberec", "Jablonec nad Nisou", "Česká Lípa", "Turnov",
    "Semily", "Tanvald", "Železný Brod", "Nový Bor", "Doksy",
];

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Pro koho", href: "/pro-koho" },
                { label: "Liberec" },
            ]}
            title="AI Act compliance pro firmy v Liberci"
            titleAccent="a Libereckém kraji"
            subtitle="Liberecký kraj — automobilky, sklářství, strojírenství a rostoucí IT sektor. AI v průmyslu musí být od srpna 2026 v souladu s EU AI Act."
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Liberecký kraj a EU AI Act</h2>
                <div className="space-y-4 text-slate-300">
                    <p>
                        Liberecký kraj je domovem automobilových dodavatelů, sklářského průmyslu
                        a <strong className="text-white">TUL (Technické univerzity v Liberci)</strong>.
                        AI se používá v prediktivní údržbě, automatizaci výroby i e-shopech.
                    </p>
                    <p>
                        Od <strong className="text-white">2. srpna 2026</strong> musí každá firma s AI systémem
                        splnit transparenci a dokumentaci podle EU AI Act.
                    </p>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Kdo v Libereckém kraji musí řešit AI Act</h2>
                <ul className="space-y-3">
                    {[
                        "Automobiloví dodavatelé s AI quality control",
                        "Sklářství a bižuterie s automatizací výroby",
                        "E-shopy s chatbotem a personalizací (Jablonec)",
                        "TUL — výzkumné AI projekty",
                        "Turistický průmysl s AI rezervačními systémy",
                        "Logistické firmy na trase D10/D35",
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
