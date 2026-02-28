import type { Metadata } from "next";
import ContentPage from "@/components/content-page";

export const metadata: Metadata = {
    title: "AIshield vs Manu\u00e1ln\u00ed audit \u2014 porovn\u00e1n\u00ed p\u0159\u00edstup\u016f k AI Act compliance",
    description:
        "Porovn\u00e1n\u00ed automatick\u00e9ho skenu AIshield a manu\u00e1ln\u00edho auditu. Rychlost, cena, p\u0159esnost, srovn\u00e1vac\u00ed tabulka.",
    alternates: { canonical: "https://aishield.cz/srovnani/aishield-vs-manualni-audit" },
};

const rows = [
    { criterion: "\u010cas", aishield: "60 sekund", manual: "2\u20134 t\u00fddny" },
    { criterion: "Cena", aishield: "Od 0 K\u010d (free sken)", manual: "50 000\u2013200 000 K\u010d" },
    { criterion: "Pokryt\u00ed", aishield: "50+ AI syst\u00e9m\u016f", manual: "Z\u00e1le\u017e\u00ed na auditorovi" },
    { criterion: "Aktualizace", aishield: "Pr\u016fb\u011b\u017en\u011b (re-sken)", manual: "Nov\u00fd audit = nov\u00e1 faktura" },
    { criterion: "Transparen\u010dn\u00ed str\u00e1nka", aishield: "Generov\u00e1na automaticky", manual: "Mus\u00edte napsat sami" },
    { criterion: "Pr\u00e1vn\u00ed kontext", aishield: "Z\u00e1kladn\u00ed doporu\u010den\u00ed", manual: "Dle kvalifikace auditora" },
];

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Dom\u016f", href: "/" },
                { label: "Srovn\u00e1n\u00ed", href: "/srovnani" },
                { label: "vs Manu\u00e1ln\u00ed audit" },
            ]}
            title="AIshield vs"
            titleAccent="manu\u00e1ln\u00ed audit"
            subtitle="Automatick\u00fd sken za 60 sekund vs t\u00fddny manu\u00e1ln\u00ed pr\u00e1ce. Jak si stoj\u00ed?"
        >
            <section>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-white/[0.08]">
                                <th className="text-left py-3 pr-4 text-slate-500 font-medium">Krit\u00e9rium</th>
                                <th className="text-left py-3 px-4 text-fuchsia-400 font-medium">AIshield</th>
                                <th className="text-left py-3 pl-4 text-slate-400 font-medium">Manu\u00e1ln\u00ed audit</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows.map((r) => (
                                <tr key={r.criterion} className="border-b border-white/[0.04]">
                                    <td className="py-3 pr-4 text-white font-medium">{r.criterion}</td>
                                    <td className="py-3 px-4 text-slate-300">{r.aishield}</td>
                                    <td className="py-3 pl-4 text-slate-400">{r.manual}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Z\u00e1v\u011br</h2>
                <p>
                    AIshield je ide\u00e1ln\u00ed pro <strong className="text-white">prvn\u00ed orientaci a pr\u016fb\u011b\u017en\u00fd
                    monitoring</strong>. Pro slo\u017eit\u011bj\u0161\u00ed p\u0159\u00edpady (vysokorizikov\u00e9 AI) doporu\u010dujeme
                    kombinaci s odborn\u00fdm auditem.
                </p>
            </section>
        </ContentPage>
    );
}
