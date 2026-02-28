import type { Metadata } from "next";
import ContentPage from "@/components/content-page";

export const metadata: Metadata = {
    title: "AIshield vs Excel checklist — automatická detekce vs tabulka",
    description:
        "Excel checklist vyžaduje manuální odpovědi. AIshield automaticky detekuje AI systémy. Srovnání přístupů.",
    alternates: { canonical: "https://aishield.cz/srovnani/aishield-vs-excel" },
};

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Srovnání", href: "/srovnani" },
                { label: "vs Excel" },
            ]}
            title="AIshield vs"
            titleAccent="Excel checklist"
            subtitle="Automatická detekce vs 100+ řádků v tabulce. Co je efektivnější?"
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Problém s Excel checklistem</h2>
                <ul className="list-disc pl-6 space-y-1 text-slate-400">
                    <li>Vyžaduje <strong className="text-white">technické znalosti</strong> — musíte vědět, že reCAPTCHA v3 je AI</li>
                    <li><strong className="text-white">Subjektivní odpovědi</strong> — každý odpoví jinak</li>
                    <li><strong className="text-white">Rychle zastarává</strong> — přidáte nový plugin a Excel neví</li>
                    <li><strong className="text-white">Žádný výstup</strong> — nevygeneruje transparenční stránku</li>
                </ul>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Co AIshield dělá jinak</h2>
                <div className="space-y-3">
                    {[
                        { label: "Automatická detekce", desc: "Není třeba nic vyplňovat — stačí zadat URL" },
                        { label: "Objektivní výsledky", desc: "Technická analýza, ne názory" },
                        { label: "Aktuální při re-skenu", desc: "Každý sken zachytí aktuální stav" },
                        { label: "Report + transparenční stránka", desc: "Okamžitý výstup k nasazení" },
                    ].map((item) => (
                        <div key={item.label} className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-4">
                            <h3 className="font-semibold text-white text-sm">{item.label}</h3>
                            <p className="text-sm text-slate-400 mt-1">{item.desc}</p>
                        </div>
                    ))}
                </div>
            </section>
        </ContentPage>
    );
}
