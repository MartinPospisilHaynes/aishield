import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "AI Act compliance pro firmy v Brně a Jihomoravském kraji — AIshield.cz",
    description:
        "Brno je českým tech hubem. AIshield pomáhá brněnským firmám, startupům a e-shopům " +
        "splnit EU AI Act — sken webu, transparenční stránka, risk assessment. Brno, Znojmo, Hodonín, Břeclav.",
    alternates: { canonical: "/pro-koho/brno" },
};

const stats = [
    { label: "Firem s AI v Jihomoravském kraji", value: "6 500+" },
    { label: "Tech startupů v JIC", value: "1 100+" },
    { label: "Deadline AI Act", value: "2. 8. 2026" },
    { label: "Maximální pokuta", value: "35 mil. €" },
];

const cities = [
    "Brno", "Znojmo", "Hodonín", "Břeclav", "Vyškov", "Blansko",
    "Boskovice", "Tišnov", "Ivančice", "Mikulov", "Kyjov", "Veselí nad Moravou",
];

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Pro koho", href: "/pro-koho" },
                { label: "Brno" },
            ]}
            title="AI Act compliance pro firmy v Brně"
            titleAccent="a Jihomoravském kraji"
            subtitle="Brno je druhým největším tech hubem v ČR. JIC, CzechInvest South Moravia, univerzitní startupy — AI je tu všude. Od srpna 2026 musíte být compliant."
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
                <h2 className="text-xl font-semibold text-white mb-4">Brno a EU AI Act</h2>
                <div className="space-y-4 text-slate-300">
                    <p>
                        Brno je domovem <strong className="text-white">JIC (Jihomoravské inovační centrum)</strong>,
                        stovek startupů a poboček mezinárodních tech firem jako Red Hat, Kiwi.com nebo Y Soft.
                        AI se tu používá v e-commerce, logistice, zdravotnictví i výrobě.
                    </p>
                    <p>
                        EU AI Act vyžaduje od <strong className="text-white">2. srpna 2026</strong> povinnou transparenci
                        a dokumentaci všech AI systémů. To znamená chatboty, AI analytiku, prediktivní modely,
                        automatické rozhodování — vše musí mít transparenční stránku a risk assessment.
                    </p>
                    <p>
                        AIshield.cz automaticky naskenuje váš web, detekuje AI systémy a vygeneruje dokumentaci.
                        100 % online, bez nutnosti osobní schůzky.
                    </p>
                </div>
            </section>

            {/* Typické brněnské firmy */}
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Kdo v Jihomoravském kraji musí řešit AI Act</h2>
                <ul className="space-y-3">
                    {[
                        "Tech startupy z JIC a inkubátorů s AI produkty",
                        "E-shopy s chatbotem a personalizovaným doporučováním",
                        "Výrobní podniky s prediktivní údržbou a AI quality control",
                        "Vinařství a potravinářské firmy s AI optimalizací produkce",
                        "Masarykova univerzita — výzkumné AI projekty",
                        "Nemocnice a kliniky s AI diagnostikou nebo triáží",
                        "Logistické firmy (blízkost dálničního uzlu D1/D2/D52)",
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
                <h2 className="text-xl font-semibold text-white mb-4">Pokrytá města v Jihomoravském kraji</h2>
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
                        Bezplatný AI Act sken pro vaši brněnskou firmu
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
