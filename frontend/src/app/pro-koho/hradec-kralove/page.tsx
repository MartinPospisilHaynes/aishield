import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "AI Act compliance pro firmy v Hradci Králové a Královéhradeckém kraji — AIshield.cz",
    description:
        "AIshield pomáhá firmám v Hradci Králové a Královéhradeckém kraji splnit EU AI Act. " +
        "Hradec Králové, Trutnov, Náchod, Jičín, Rychnov nad Kněžnou, Dvůr Králové.",
    alternates: { canonical: "/pro-koho/hradec-kralove" },
};

const cities = [
    "Hradec Králové", "Trutnov", "Náchod", "Jičín",
    "Rychnov nad Kněžnou", "Dvůr Králové nad Labem", "Nová Paka",
    "Jaroměř", "Vrchlabí", "Hořice", "Broumov",
];

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Pro koho", href: "/pro-koho" },
                { label: "Hradec Králové" },
            ]}
            title="AI Act compliance pro firmy v Hradci Králové"
            titleAccent="a Královéhradeckém kraji"
            subtitle="Hradec Králové — farmaceutický průmysl, IT a zdravotnické technologie. AI v těchto odvětvích spadá často do vyšších rizikových kategorií."
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Královéhradecký kraj a EU AI Act</h2>
                <div className="space-y-4 text-slate-300">
                    <p>
                        Královéhradecký kraj je centrem <strong className="text-white">farmaceutického průmyslu</strong>
                        (Zentiva, Contipro) a zdravotnictví (FN Hradec Králové).
                        AI se tu používá v diagnostice, výrobě léků, quality control i logistice.
                    </p>
                    <p>
                        <strong className="text-white">Pozor:</strong> AI v zdravotnictví a farmacii spadá často
                        do kategorie <strong className="text-white">high-risk</strong> (příloha III AI Act),
                        což znamená přísnější povinnosti — risk management system, technická dokumentace a conformity assessment.
                    </p>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Kdo v Královéhradeckém kraji musí řešit AI Act</h2>
                <ul className="space-y-3">
                    {[
                        "Farmaceutické firmy s AI quality control a výrobní optimalizací",
                        "Nemocnice a zdravotnická zařízení s AI diagnostikou (HIGH-RISK)",
                        "E-shopy s chatbotem a AI doporučováním",
                        "UHK — výzkumné AI projekty",
                        "Turistický průmysl v Krkonoších — AI rezervační systémy",
                        "Textilní průmysl (Náchod) s AI automatizací",
                        "IT firmy v Hradci a okolí",
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
