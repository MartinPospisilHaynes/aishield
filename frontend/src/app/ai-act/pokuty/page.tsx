import type { Metadata } from "next";
import ContentPage from "@/components/content-page";

export const metadata: Metadata = {
    title: "Pokuty za poru\u0161en\u00ed AI Act \u2014 a\u017e 35 milion\u016f EUR",
    description:
        "P\u0159ehled pokut za poru\u0161en\u00ed EU AI Act. A\u017e 35 mil. EUR za zak\u00e1zan\u00e9 praktiky, " +
        "15 mil. za chyb\u011bj\u00edc\u00ed dokumentaci. P\u0159\u00edklady pro \u010desk\u00e9 firmy.",
    alternates: { canonical: "https://aishield.cz/ai-act/pokuty" },
};

const fines = [
    { level: "Zak\u00e1zan\u00e9 AI praktiky (\u010dl. 5)", amount: "35 mil. EUR / 7 % obratu", border: "border-red-500/30 bg-red-500/5", examples: "Soci\u00e1ln\u00ed bodov\u00e1n\u00ed, manipulativn\u00ed dark patterns" },
    { level: "Poru\u0161en\u00ed povinnost\u00ed pro vysok\u00e9 riziko", amount: "15 mil. EUR / 3 % obratu", border: "border-orange-500/30 bg-orange-500/5", examples: "Chyb\u011bj\u00edc\u00ed dokumentace, risk assessment" },
    { level: "Poru\u0161en\u00ed transparen\u010dn\u00edch povinnost\u00ed (\u010dl. 50)", amount: "7,5 mil. EUR / 1,5 % obratu", border: "border-amber-500/30 bg-amber-500/5", examples: "Neozna\u010den\u00fd chatbot, chyb\u011bj\u00edc\u00ed transparen\u010dn\u00ed str\u00e1nka" },
];

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Dom\u016f", href: "/" },
                { label: "AI Act", href: "/ai-act" },
                { label: "Pokuty" },
            ]}
            title="Pokuty za poru\u0161en\u00ed"
            titleAccent="AI Act"
            subtitle="P\u0159ehled sankc\u00ed podle typu poru\u0161en\u00ed. Pokuty se po\u010d\u00edtaj\u00ed za ka\u017ed\u00e9 poru\u0161en\u00ed zvl\u00e1\u0161\u0165."
        >
            <section>
                <div className="space-y-4">
                    {fines.map((f) => (
                        <div key={f.level} className={`rounded-xl border ${f.border} p-5`}>
                            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-3">
                                <h3 className="font-semibold text-white">{f.level}</h3>
                                <span className="text-sm font-mono font-bold text-fuchsia-400 whitespace-nowrap">
                                    a\u017e {f.amount}
                                </span>
                            </div>
                            <p className="text-sm text-slate-400">P\u0159\u00edklady: {f.examples}</p>
                        </div>
                    ))}
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">P\u0159\u00edklad pro \u010desk\u00fd e-shop</h2>
                <div className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-5">
                    <p className="text-slate-400 mb-3">E-shop s obratem <strong className="text-white">50 mil. K\u010d/rok</strong>, kter\u00fd m\u00e1 neozna\u010den\u00fd AI chatbot:</p>
                    <ul className="list-disc pl-6 space-y-1 text-slate-400">
                        <li>Pokuta: 1,5 % z 50 mil. = <strong className="text-white">750 000 K\u010d</strong></li>
                        <li>3 neozna\u010den\u00e9 syst\u00e9my = 3 \u00d7 750 000 = <strong className="text-red-400">2,25 mil. K\u010d</strong></li>
                    </ul>
                </div>
            </section>
        </ContentPage>
    );
}
