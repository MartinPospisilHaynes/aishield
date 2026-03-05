import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "AI Act compliance pro firmy v Olomouci a Olomouckém kraji — AIshield.cz",
    description:
        "AIshield.cz sídlí v Olomouci. Pomáháme firmám v Olomouckém kraji splnit EU AI Act — " +
        "bezplatný sken webu, transparenční stránka, risk assessment. Olomouc, Prostějov, Šumperk, Přerov.",
    alternates: { canonical: "/pro-koho/olomouc" },
};

const stats = [
    { label: "Firem s AI v Olomouckém kraji", value: "2 400+" },
    { label: "E-shopů s chatbotem", value: "820+" },
    { label: "Deadline AI Act", value: "2. 8. 2026" },
    { label: "Maximální pokuta", value: "35 mil. €" },
];

const cities = [
    "Olomouc", "Prostějov", "Přerov", "Šumperk", "Jeseník", "Zábřeh", "Šternberk", "Hranice",
    "Litovel", "Uničov", "Kojetín", "Lipník nad Bečvou",
];

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Pro koho", href: "/pro-koho" },
                { label: "Olomouc" },
            ]}
            title="AI Act compliance pro firmy v Olomouci"
            titleAccent="a Olomouckém kraji"
            subtitle="AIshield.cz má sídlo přímo v Olomouci. Pomáháme místním firmám, e-shopům i živnostníkům splnit EU AI Act — rychle, online a v češtině."
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

            {/* Proč AIshield v Olomouci */}
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Proč AIshield pro Olomoucký kraj</h2>
                <div className="space-y-4 text-slate-300">
                    <p>
                        EU AI Act (Nařízení 2024/1689) vstupuje plně v platnost <strong className="text-white">2. srpna 2026</strong>.
                        Každá firma v Olomouckém kraji, která provozuje chatbot, AI analytiku, personalizované doporučování
                        nebo automatické rozhodování, musí splnit minimálně <strong className="text-white">transparenční povinnosti</strong> podle článku 50.
                    </p>
                    <p>
                        AIshield.cz je <strong className="text-white">jediný český compliance scanner</strong>, který automaticky
                        detekuje AI systémy na vašem webu a vygeneruje kompletní dokumentaci — transparenční stránku,
                        registr AI systémů a risk assessment.
                    </p>
                    <p>
                        Sídlíme na Dolním náměstí 38/5 v Olomouci. Rozumíme místnímu podnikatelskému prostředí
                        a nabízíme osobní konzultace pro firmy v regionu.
                    </p>
                </div>
            </section>

            {/* Kdo musí řešit AI Act */}
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Kdo v Olomouckém kraji musí řešit AI Act</h2>
                <ul className="space-y-3">
                    {[
                        "E-shopy s chatbotem nebo AI doporučováním produktů",
                        "Výrobní firmy s prediktivní údržbou nebo AI quality control",
                        "Restaurace a hotely s AI rezervačním systémem",
                        "Marketingové agentury nasazující AI nástroje klientům",
                        "Zdravotnická zařízení s AI triáží nebo diagnostikou",
                        "Univerzita Palackého — výzkumné projekty s AI",
                        "Obce a městské úřady s chatboty na webu",
                    ].map((item) => (
                        <li key={item} className="flex items-start gap-3">
                            <span className="text-fuchsia-400 mt-0.5">→</span>
                            <span className="text-slate-300">{item}</span>
                        </li>
                    ))}
                </ul>
            </section>

            {/* Pokryté města */}
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Pokrytá města v Olomouckém kraji</h2>
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
                        Bezplatný AI Act sken pro vaši firmu
                    </h2>
                    <p className="text-slate-400 mb-6 max-w-lg mx-auto">
                        Zjistěte za 60 sekund, jaké AI systémy máte na webu a co musíte udělat pro compliance.
                        Bez registrace, zdarma.
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
