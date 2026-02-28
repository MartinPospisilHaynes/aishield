import type { Metadata } from "next";
import ContentPage from "@/components/content-page";

export const metadata: Metadata = {
    title: "Pokuty za porušení AI Act — až 35 milionů EUR",
    description:
        "Přehled pokut za porušení EU AI Act. Až 35 mil. EUR za zakázané praktiky, " +
        "15 mil. za chybějící dokumentaci. Příklady pro české firmy.",
    alternates: { canonical: "https://aishield.cz/ai-act/pokuty" },
};

const fines = [
    { level: "Zakázané AI praktiky (čl. 5)", amount: "35 mil. EUR / 7 % obratu", border: "border-red-500/30 bg-red-500/5", examples: "Sociální bodování, manipulativní dark patterns" },
    { level: "Porušení povinností pro vysoké riziko", amount: "15 mil. EUR / 3 % obratu", border: "border-orange-500/30 bg-orange-500/5", examples: "Chybějící dokumentace, risk assessment" },
    { level: "Porušení transparenčních povinností (čl. 50)", amount: "7,5 mil. EUR / 1,5 % obratu", border: "border-amber-500/30 bg-amber-500/5", examples: "Neoznačený chatbot, chybějící transparenční stránka" },
];

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "AI Act", href: "/ai-act" },
                { label: "Pokuty" },
            ]}
            title="Pokuty za porušení"
            titleAccent="AI Act"
            subtitle="Přehled sankcí podle typu porušení. Pokuty se počítají za každé porušení zvlášť."
        >
            <section>
                <div className="space-y-4">
                    {fines.map((f) => (
                        <div key={f.level} className={`rounded-xl border ${f.border} p-5`}>
                            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-3">
                                <h3 className="font-semibold text-white">{f.level}</h3>
                                <span className="text-sm font-mono font-bold text-fuchsia-400 whitespace-nowrap">
                                    až {f.amount}
                                </span>
                            </div>
                            <p className="text-sm text-slate-400">Příklady: {f.examples}</p>
                        </div>
                    ))}
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Příklad pro český e-shop</h2>
                <div className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-5">
                    <p className="text-slate-400 mb-3">E-shop s obratem <strong className="text-white">50 mil. Kč/rok</strong>, který má neoznačený AI chatbot:</p>
                    <ul className="list-disc pl-6 space-y-1 text-slate-400">
                        <li>Pokuta: 1,5 % z 50 mil. = <strong className="text-white">750 000 Kč</strong></li>
                        <li>3 neoznačené systémy = 3 × 750 000 = <strong className="text-red-400">2,25 mil. Kč</strong></li>
                    </ul>
                </div>
            </section>
        </ContentPage>
    );
}
