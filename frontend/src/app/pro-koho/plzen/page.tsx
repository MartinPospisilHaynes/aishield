import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "AI Act compliance pro firmy v Plzni a Plzeňském kraji — AIshield.cz",
    description:
        "AIshield pomáhá firmám v Plzni a Plzeňském kraji splnit EU AI Act — automatický sken webu, " +
        "transparenční stránka, risk assessment. Plzeň, Klatovy, Rokycany, Domažlice, Tachov.",
    alternates: { canonical: "/pro-koho/plzen" },
};

const stats = [
    { label: "Firem s AI v Plzeňském kraji", value: "3 200+" },
    { label: "Průmyslových podniků", value: "680+" },
    { label: "Deadline AI Act", value: "2. 8. 2026" },
    { label: "Maximální pokuta", value: "35 mil. €" },
];

const cities = [
    "Plzeň", "Klatovy", "Rokycany", "Domažlice", "Tachov",
    "Sušice", "Nýřany", "Přeštice", "Stod", "Kdyně",
];

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Pro koho", href: "/pro-koho" },
                { label: "Plzeň" },
            ]}
            title="AI Act compliance pro firmy v Plzni"
            titleAccent="a Plzeňském kraji"
            subtitle="Plzeňský kraj je centrem strojírenství a automobilového průmyslu. AI v prediktivní údržbě, kvalitě i logistice — vše musí být od srpna 2026 compliant."
        >
            <section>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    {stats.map((s) => (
                        <div key={s.label} className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-5 text-center">
                            <div className="text-2xl font-bold text-fuchsia-400">{s.value}</div>
                            <div className="text-xs text-slate-400 mt-1">{s.label}</div>
                        </div>
                    ))}
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Plzeň a EU AI Act</h2>
                <div className="space-y-4 text-slate-300">
                    <p>
                        Plzeňský kraj je domovem <strong className="text-white">Škoda Transportation</strong>,
                        desítek dodavatelů pro automobilový průmysl a rostoucího IT sektoru.
                        AI se tu používá v prediktivní údržbě, quality control, logistice i e-commerce.
                    </p>
                    <p>
                        EU AI Act vyžaduje od <strong className="text-white">2. srpna 2026</strong> dokumentaci všech AI systémů.
                        AIshield automaticky naskenuje váš web a vygeneruje kompletní compliance dokumentaci.
                    </p>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Kdo v Plzeňském kraji musí řešit AI Act</h2>
                <ul className="space-y-3">
                    {[
                        "Strojírenské podniky s prediktivní údržbou a AI quality control",
                        "Pivovarnictví a potravinářství s AI optimalizací výroby",
                        "E-shopy s chatbotem a AI personalizací",
                        "ZČU — výzkumné AI projekty a startupy",
                        "IT firmy v BIC Plzeň",
                        "Logistické firmy (dálniční uzel D5)",
                        "Energetické firmy s AI řízením sítě",
                    ].map((item) => (
                        <li key={item} className="flex items-start gap-3">
                            <span className="text-fuchsia-400 mt-0.5">→</span>
                            <span className="text-slate-300">{item}</span>
                        </li>
                    ))}
                </ul>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Pokrytá města v Plzeňském kraji</h2>
                <div className="flex flex-wrap gap-2">
                    {cities.map((city) => (
                        <span key={city} className="rounded-full border border-slate-700/50 bg-slate-800/30 px-3 py-1 text-sm text-slate-300">{city}</span>
                    ))}
                </div>
            </section>

            <section>
                <div className="rounded-xl border border-fuchsia-500/30 bg-gradient-to-r from-fuchsia-900/20 to-cyan-900/20 p-8 text-center">
                    <h2 className="text-2xl font-bold text-white mb-3">Bezplatný AI Act sken pro vaši plzeňskou firmu</h2>
                    <p className="text-slate-400 mb-6 max-w-lg mx-auto">Zjistěte za 60 sekund, jaké AI systémy máte na webu.</p>
                    <Link href="/scan" className="inline-block rounded-lg bg-fuchsia-600 px-8 py-3 font-semibold text-white hover:bg-fuchsia-500 transition-colors">Spustit bezplatný sken →</Link>
                </div>
            </section>
        </ContentPage>
    );
}
