import type { Metadata } from "next";
import ContentPage from "@/components/content-page";

export const metadata: Metadata = {
    title: "AI na \u010desk\u00fdch webech 2026 \u2014 data report AIshield",
    description:
        "Data report: stav AI syst\u00e9m\u016f na \u010desk\u00fdch webech a e-shopech. " +
        "Kolik web\u016f pou\u017e\u00edv\u00e1 chatbot? Kolik je p\u0159ipraveno na AI Act?",
    alternates: { canonical: "https://aishield.cz/report" },
};

const stats = [
    { label: "Web\u016f s AI chatbotem", value: "34 %", bar: 34 },
    { label: "Web\u016f s Google Analytics 4", value: "78 %", bar: 78 },
    { label: "Web\u016f s reklamn\u00edm pixelem (Meta/Google)", value: "62 %", bar: 62 },
    { label: "E-shop\u016f s doporu\u010dov\u00e1n\u00edm produkt\u016f", value: "41 %", bar: 41 },
    { label: "Web\u016f s transparen\u010dn\u00ed AI str\u00e1nkou", value: "< 2 %", bar: 2, alert: true },
    { label: "Web\u016f s ozna\u010den\u00fdm chatbotem", value: "< 5 %", bar: 5, alert: true },
];

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Dom\u016f", href: "/" },
                { label: "Report" },
            ]}
            title="AI na \u010desk\u00fdch webech"
            titleAccent="2026"
            subtitle="Data report zalo\u017een\u00fd na anal\u00fdze \u010desk\u00fdch web\u016f a e-shop\u016f. Aktualizov\u00e1no \u00fanor 2026."
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Kl\u00ed\u010dov\u00e9 statistiky</h2>
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
                <h2 className="text-xl font-semibold text-white mb-3">Co to znamen\u00e1?</h2>
                <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-5">
                    <p className="text-slate-300">
                        V\u00edce ne\u017e <strong className="text-white">95 % \u010desk\u00fdch web\u016f</strong> nen\u00ed p\u0159ipraveno
                        na AI Act. V\u011bt\u0161ina pou\u017e\u00edv\u00e1 AI syst\u00e9my, ale nem\u00e1 transparen\u010dn\u00ed str\u00e1nku
                        ani ozna\u010den\u00fd chatbot. Do srpna 2026 zb\u00fdv\u00e1 m\u00e9n\u011b ne\u017e 6 m\u011bs\u00edc\u016f.
                    </p>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Metodika</h2>
                <p className="text-sm text-slate-500">
                    Data vych\u00e1zej\u00ed z anal\u00fdzy vzorku \u010desk\u00fdch web\u016f a e-shop\u016f proveden\u00e9 n\u00e1strojem AIshield.
                    Vzorek zahrnuje weby z \u017eeb\u0159\u00ed\u010dku Shoptet Top 1000, Heureka kategorie a n\u00e1hodn\u00fd v\u00fdb\u011br
                    z webov\u00e9ho indexu. Data jsou orienta\u010dn\u00ed a mohou se li\u0161it od celkov\u00e9 populace.
                </p>
            </section>
        </ContentPage>
    );
}
