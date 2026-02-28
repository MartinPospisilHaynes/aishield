import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "Shoptet a AI Act — povinnosti pro české e-shopy na Shoptetu",
    description:
        "Shoptet nabízí AI doporučování, chatbot a smart search. Jaké máte povinnosti dle AI Act?",
    alternates: { canonical: "https://aishield.cz/integrace/shoptet" },
};

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Integrace", href: "/integrace" },
                { label: "Shoptet" },
            ]}
            title="Shoptet a"
            titleAccent="AI Act"
            subtitle="Nejpopulárnější česká e-shopová platforma. Jaké AI funkce používá a co musíte splnit?"
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">AI funkce na Shoptetu</h2>
                <div className="space-y-3">
                    {[
                        { name: "Doporučování produktů", risk: "Minimální–Omezené", desc: "Automatické zobrazování souvisejících produktů" },
                        { name: "Smart search (Luigis Box)", risk: "Minimální", desc: "AI-enhanced vyhledávání s autocomplete" },
                        { name: "Chatbot doplňky", risk: "Omezené", desc: "Smartsupp, Tidio a další chatbot pluginy" },
                        { name: "Personalizace obsahu", risk: "Minimální", desc: "A/B testování, dynamický obsah" },
                    ].map((f) => (
                        <div key={f.name} className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-4">
                            <div className="flex justify-between items-start gap-2">
                                <h3 className="font-semibold text-white text-sm">{f.name}</h3>
                                <span className="text-xs text-fuchsia-400 whitespace-nowrap">Riziko: {f.risk}</span>
                            </div>
                            <p className="text-sm text-slate-400 mt-1">{f.desc}</p>
                        </div>
                    ))}
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Checklist pro Shoptet majitele</h2>
                <ol className="list-decimal pl-6 space-y-2 text-slate-400">
                    <li>Spusťte <Link href="/scan" className="text-fuchsia-400 hover:text-fuchsia-300">sken webu</Link> — AIshield detekuje všechny AI systémy</li>
                    <li>Zmínit doporučování a search na transparenční stránce</li>
                    <li>Pokud máte chatbot — označit jako AI dle <Link href="/ai-act/clanek-50" className="text-fuchsia-400 hover:text-fuchsia-300">čl. 50</Link></li>
                    <li>Propojit s GDPR právním textem</li>
                </ol>
            </section>
        </ContentPage>
    );
}
