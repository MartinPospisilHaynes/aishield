import type { Metadata } from "next";
import ContentPage from "@/components/content-page";

export const metadata: Metadata = {
    title: "AIshield vs Manuální audit — porovnání přístupů k AI Act compliance",
    description:
        "Porovnání automatického skenu AIshield a manuálního auditu. Rychlost, cena, přesnost, srovnávací tabulka.",
    alternates: { canonical: "https://aishield.cz/srovnani/aishield-vs-manualni-audit" },
};

const rows = [
    { criterion: "Čas", aishield: "60 sekund", manual: "2–4 týdny" },
    { criterion: "Cena", aishield: "Od 0 Kč (free sken)", manual: "50 000–200 000 Kč" },
    { criterion: "Pokrytí", aishield: "50+ AI systémů", manual: "Záleží na auditorovi" },
    { criterion: "Aktualizace", aishield: "Průběžně (re-sken)", manual: "Nový audit = nová faktura" },
    { criterion: "Transparenční stránka", aishield: "Generována automaticky", manual: "Musíte napsat sami" },
    { criterion: "Právní kontext", aishield: "Základní doporučení", manual: "Dle kvalifikace auditora" },
];

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Srovnání", href: "/srovnani" },
                { label: "vs Manuální audit" },
            ]}
            title="AIshield vs"
            titleAccent="manuální audit"
            subtitle="Automatický sken za 60 sekund vs týdny manuální práce. Jak si stojí?"
        >
            <section>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-white/[0.08]">
                                <th className="text-left py-3 pr-4 text-slate-500 font-medium">Kritérium</th>
                                <th className="text-left py-3 px-4 text-fuchsia-400 font-medium">AIshield</th>
                                <th className="text-left py-3 pl-4 text-slate-400 font-medium">Manuální audit</th>
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
                <h2 className="text-xl font-semibold text-white mb-3">Závěr</h2>
                <p>
                    AIshield je ideální pro <strong className="text-white">první orientaci a průběžný
                    monitoring</strong>. Pro složitější případy (vysokorizikové AI) doporučujeme
                    kombinaci s odborným auditem.
                </p>
            </section>
        </ContentPage>
    );
}
