import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "Shoptet a AI Act \u2014 povinnosti pro \u010desk\u00e9 e-shopy na Shoptetu",
    description:
        "Shoptet nab\u00edz\u00ed AI doporu\u010dov\u00e1n\u00ed, chatbot a smart search. Jak\u00e9 m\u00e1te povinnosti dle AI Act?",
    alternates: { canonical: "https://aishield.cz/integrace/shoptet" },
};

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Dom\u016f", href: "/" },
                { label: "Integrace", href: "/integrace" },
                { label: "Shoptet" },
            ]}
            title="Shoptet a"
            titleAccent="AI Act"
            subtitle="Nejpopul\u00e1rn\u011bj\u0161\u00ed \u010desk\u00e1 e-shopov\u00e1 platforma. Jak\u00e9 AI funkce pou\u017e\u00edv\u00e1 a co mus\u00edte splnit?"
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">AI funkce na Shoptetu</h2>
                <div className="space-y-3">
                    {[
                        { name: "Doporu\u010dov\u00e1n\u00ed produkt\u016f", risk: "Minim\u00e1ln\u00ed\u2013Omezen\u00e9", desc: "Automatick\u00e9 zobrazov\u00e1n\u00ed souvisej\u00edc\u00edch produkt\u016f" },
                        { name: "Smart search (Luigis Box)", risk: "Minim\u00e1ln\u00ed", desc: "AI-enhanced vyhled\u00e1v\u00e1n\u00ed s autocomplete" },
                        { name: "Chatbot dopl\u0148ky", risk: "Omezen\u00e9", desc: "Smartsupp, Tidio a dal\u0161\u00ed chatbot pluginy" },
                        { name: "Personalizace obsahu", risk: "Minim\u00e1ln\u00ed", desc: "A/B testov\u00e1n\u00ed, dynamick\u00fd obsah" },
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
                    <li>Spus\u0165te <Link href="/scan" className="text-fuchsia-400 hover:text-fuchsia-300">sken webu</Link> \u2014 AIshield detekuje v\u0161echny AI syst\u00e9my</li>
                    <li>Zm\u00ednit doporu\u010dov\u00e1n\u00ed a search na transparen\u010dn\u00ed str\u00e1nce</li>
                    <li>Pokud m\u00e1te chatbot \u2014 ozna\u010dit jako AI dle <Link href="/ai-act/clanek-50" className="text-fuchsia-400 hover:text-fuchsia-300">\u010dl. 50</Link></li>
                    <li>Propojit s GDPR pr\u00e1vn\u00edm textem</li>
                </ol>
            </section>
        </ContentPage>
    );
}
