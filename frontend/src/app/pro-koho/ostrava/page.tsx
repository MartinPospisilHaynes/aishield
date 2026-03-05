import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "AI Act compliance pro firmy v Ostravě a Moravskoslezském kraji — AIshield.cz",
    description:
        "Ostrava a Moravskoslezský kraj — průmysl, IT a AI. AIshield pomáhá ostravským firmám " +
        "splnit EU AI Act — automatický sken, transparenční stránka, dokumentace. Ostrava, Opava, Frýdek-Místek, Karviná.",
    alternates: { canonical: "/pro-koho/ostrava" },
};

const stats = [
    { label: "Firem s AI v MSK", value: "4 100+" },
    { label: "Průmyslových podniků s AI", value: "950+" },
    { label: "Deadline AI Act", value: "2. 8. 2026" },
    { label: "Maximální pokuta", value: "35 mil. €" },
];

const cities = [
    "Ostrava", "Opava", "Frýdek-Místek", "Karviná", "Havířov", "Český Těšín",
    "Nový Jičín", "Třinec", "Kopřivnice", "Bruntál", "Krnov", "Hlučín",
];

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Pro koho", href: "/pro-koho" },
                { label: "Ostrava" },
            ]}
            title="AI Act compliance pro firmy v Ostravě"
            titleAccent="a Moravskoslezském kraji"
            subtitle="Moravskoslezský kraj prochází průmyslovou transformací — AI je klíčová technologie. Od srpna 2026 musí být každý AI systém v souladu s EU AI Act."
        >
            {/* Statistiky */}
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

            {/* Kontext */}
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Ostrava a EU AI Act</h2>
                <div className="space-y-4 text-slate-300">
                    <p>
                        Moravskoslezský kraj je třetím největším regionem ČR a prochází intenzivní
                        <strong className="text-white"> digitální transformací</strong>. Těžký průmysl přechází na
                        prediktivní údržbu, AI quality control a automatizaci. IT parky v Ostravě-Porubě
                        hostí stovky tech firem.
                    </p>
                    <p>
                        EU AI Act vyžaduje od <strong className="text-white">2. srpna 2026</strong> dokumentaci
                        všech AI systémů — chatboty, prediktivní modely, automatické rozhodování,
                        AI personalizace. Nesplnění znamená pokuty až{" "}
                        <strong className="text-white">35 milionů EUR</strong>.
                    </p>
                    <p>
                        AIshield.cz je plně online služba — stačí zadat URL webu a za 60 sekund víte,
                        jaké AI systémy provozujete a co musíte udělat.
                    </p>
                </div>
            </section>

            {/* Typické firmy */}
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Kdo v Moravskoslezském kraji musí řešit AI Act</h2>
                <ul className="space-y-3">
                    {[
                        "Ocelárny a strojírenské podniky s prediktivní údržbou",
                        "IT firmy v Ostravě-Porubě a Technologickém parku",
                        "Automobilky a dodavatelé s AI quality control (Kopřivnice, Nošovice)",
                        "E-shopy s chatbotem a dynamickým pricingem",
                        "VŠB-TUO — výzkumné AI projekty (IT4Innovations)",
                        "Energetické společnosti s AI optimalizací sítě",
                        "Logistické firmy s prediktivní optimalizací",
                    ].map((item) => (
                        <li key={item} className="flex items-start gap-3">
                            <span className="text-fuchsia-400 mt-0.5">→</span>
                            <span className="text-slate-300">{item}</span>
                        </li>
                    ))}
                </ul>
            </section>

            {/* Pokrytá města */}
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Pokrytá města v Moravskoslezském kraji</h2>
                <div className="flex flex-wrap gap-2">
                    {cities.map((city) => (
                        <span
                            key={city}
                            className="rounded-full border border-slate-700/50 bg-slate-800/30 px-3 py-1 text-sm text-slate-300"
                        >
                            {city}
                        </span>
                    ))}
                </div>
            </section>

            {/* CTA */}
            <section>
                <div className="rounded-xl border border-fuchsia-500/30 bg-gradient-to-r from-fuchsia-900/20 to-cyan-900/20 p-8 text-center">
                    <h2 className="text-2xl font-bold text-white mb-3">
                        Bezplatný AI Act sken pro vaši ostravskou firmu
                    </h2>
                    <p className="text-slate-400 mb-6 max-w-lg mx-auto">
                        Zjistěte za 60 sekund, jaké AI systémy máte na webu. Bez registrace, zdarma.
                    </p>
                    <Link
                        href="/scan"
                        className="inline-block rounded-lg bg-fuchsia-600 px-8 py-3 font-semibold text-white hover:bg-fuchsia-500 transition-colors"
                    >
                        Spustit bezplatný sken →
                    </Link>
                </div>
            </section>
        </ContentPage>
    );
}
