import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "AI Act compliance pro firmy v Praze — AIshield.cz",
    description:
        "Praha má nejvíc firem využívajících AI v ČR. AIshield pomáhá pražským firmám, " +
        "e-shopům a startupům splnit EU AI Act — bezplatný sken, transparenční stránka, dokumentace.",
    alternates: { canonical: "/pro-koho/praha" },
};

const stats = [
    { label: "Firem s AI v Praze", value: "18 000+" },
    { label: "Tech startupů", value: "4 200+" },
    { label: "Deadline AI Act", value: "2. 8. 2026" },
    { label: "Maximální pokuta", value: "35 mil. €" },
];

const districts = [
    "Praha 1", "Praha 2", "Praha 3", "Praha 4", "Praha 5", "Praha 6",
    "Praha 7", "Praha 8", "Praha 9", "Praha 10", "Karlín", "Smíchov",
    "Holešovice", "Vinohrady", "Žižkov", "Letná",
];

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Pro koho", href: "/pro-koho" },
                { label: "Praha" },
            ]}
            title="AI Act compliance pro firmy v Praze"
            titleAccent="— hlavní město AI v ČR"
            subtitle="Praha je epicentrem české AI scény. Tisíce firem tu provozují chatboty, AI analytiku nebo automatizace. Od srpna 2026 musí všechny splnit EU AI Act."
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
                <h2 className="text-xl font-semibold text-white mb-4">Praha a EU AI Act</h2>
                <div className="space-y-4 text-slate-300">
                    <p>
                        V Praze sídlí přes <strong className="text-white">70 % českých tech firem</strong>.
                        Od fintechů v Karlíně přes e-commerce giganty na Smíchově až po AI startupy v CzechInvestu —
                        prakticky každá pražská digitální firma provozuje minimálně jeden AI systém.
                    </p>
                    <p>
                        EU AI Act (Nařízení 2024/1689) vyžaduje od <strong className="text-white">2. srpna 2026</strong> povinnou
                        transparenci u každého AI systému nasazeného v EU. Chatbot na webu? AI personalizace?
                        Automatické hodnocení zákazníků? Vše musí být zdokumentované.
                    </p>
                    <p>
                        AIshield.cz automaticky naskenuje váš web, detekuje AI systémy a vygeneruje kompletní
                        compliance dokumentaci — transparenční stránku, registr AI a risk assessment.
                    </p>
                </div>
            </section>

            {/* Typické pražské firmy */}
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Typické pražské firmy, které musí řešit AI Act</h2>
                <ul className="space-y-3">
                    {[
                        "Fintech a bankovní startupy s AI scoringem a fraud detection",
                        "E-commerce firmy s chatbotem, doporučováním a dynamickým pricingem",
                        "SaaS startupy vyvíjející AI produkty (provider povinnosti)",
                        "Marketingové agentury nasazující Meta Pixel, GA4, AI copywriting",
                        "Právní kanceláře využívající AI pro analýzu smluv",
                        "Healthtech startupy s AI diagnostikou",
                        "Logistické firmy s prediktivní optimalizací tras",
                    ].map((item) => (
                        <li key={item} className="flex items-start gap-3">
                            <span className="text-fuchsia-400 mt-0.5">→</span>
                            <span className="text-slate-300">{item}</span>
                        </li>
                    ))}
                </ul>
            </section>

            {/* Městské části */}
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Pokryté městské části</h2>
                <div className="flex flex-wrap gap-2">
                    {districts.map((d) => (
                        <span
                            key={d}
                            className="rounded-full border border-slate-700/50 bg-slate-800/30 px-3 py-1 text-sm text-slate-300"
                        >
                            {d}
                        </span>
                    ))}
                </div>
            </section>

            {/* CTA */}
            <section>
                <div className="rounded-xl border border-fuchsia-500/30 bg-gradient-to-r from-fuchsia-900/20 to-cyan-900/20 p-8 text-center">
                    <h2 className="text-2xl font-bold text-white mb-3">
                        Bezplatný AI Act sken pro vaši pražskou firmu
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
