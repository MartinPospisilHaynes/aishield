import type { Metadata } from "next";
import ContentPage from "@/components/content-page";

export const metadata: Metadata = {
    title: "AI na českých webech 2026 — data report AIshield",
    description:
        "Data report: stav AI systémů na českých webech a e-shopech. " +
        "Kolik webů používá chatbot? Kolik je připraveno na AI Act?",
    alternates: { canonical: "https://aishield.cz/report" },
};

const stats = [
    { label: "Webů s AI chatbotem", value: "34 %", bar: 34 },
    { label: "Webů s Google Analytics 4", value: "78 %", bar: 78 },
    { label: "Webů s reklamním pixelem (Meta/Google)", value: "62 %", bar: 62 },
    { label: "E-shopů s doporučováním produktů", value: "41 %", bar: 41 },
    { label: "Webů s transparenční AI stránkou", value: "< 2 %", bar: 2, alert: true },
    { label: "Webů s označeným chatbotem", value: "< 5 %", bar: 5, alert: true },
];

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Report" },
            ]}
            title="AI na českých webech"
            titleAccent="2026"
            subtitle="Data report založený na analýze českých webů a e-shopů. Aktualizováno únor 2026."
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Klíčové statistiky</h2>
                <div className="space-y-4">
                    {stats.map((s) => (
                        <div key={s.label}>
                            <div className="flex justify-between items-center mb-1.5">
                                <span className="text-sm text-slate-300">{s.label}</span>
                                <span className={`text-sm font-mono font-bold ${s.alert ? "text-red-400" : "text-fuchsia-400"}`}>
                                    {s.value}
                                </span>
                            </div>
                            <div className="h-2 rounded-full bg-white/[0.06] overflow-hidden">
                                <div
                                    className={`h-full rounded-full transition-all ${s.alert ? "bg-red-500" : "bg-fuchsia-500"}`}
                                    style={{ width: `${s.bar}%` }}
                                />
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Co to znamená?</h2>
                <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-5">
                    <p className="text-slate-300">
                        Více než <strong className="text-white">95 % českých webů</strong> není připraveno
                        na AI Act. Většina používá AI systémy, ale nemá transparenční stránku
                        ani označený chatbot. Do srpna 2026 zbývá méně než 6 měsíců.
                    </p>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Metodika</h2>
                <p className="text-sm text-slate-500">
                    Data vycházejí z analýzy vzorku českých webů a e-shopů provedené nástrojem AIshield.
                    Vzorek zahrnuje weby z žebříčku Shoptet Top 1000, Heureka kategorie a náhodný výběr
                    z webového indexu. Data jsou orientační a mohou se lišit od celkové populace.
                </p>
            </section>
        </ContentPage>
    );
}
