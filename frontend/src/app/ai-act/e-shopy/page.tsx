import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "AI Act pro e-shopy \u2014 chatboty, doporu\u010dov\u00e1n\u00ed, remarketing",
    description:
        "Jak AI Act ovlivn\u00ed \u010desk\u00e9 e-shopy? Chatboty, doporu\u010dov\u00e1n\u00ed produkt\u016f, dynamick\u00e9 ceny \u2014 co mus\u00edte splnit do srpna 2026.",
    alternates: { canonical: "https://aishield.cz/ai-act/e-shopy" },
};

const aiSystems = [
    { name: "Chatbot (Smartsupp, Tidio, Crisp)", risk: "Omezen\u00e9", duty: "Informovat z\u00e1kazn\u00edka", icon: "\ud83d\udcac" },
    { name: "Doporu\u010dov\u00e1n\u00ed produkt\u016f", risk: "Minim\u00e1ln\u00ed\u2013Omezen\u00e9", duty: "Ozna\u010dit jako AI-generovan\u00e9", icon: "\ud83d\udecd\ufe0f" },
    { name: "Google Analytics 4 (ML predikce)", risk: "Minim\u00e1ln\u00ed", duty: "Zm\u00ednit v transparen\u010dn\u00ed str\u00e1nce", icon: "\ud83d\udcca" },
    { name: "Reklamn\u00ed pixely (Meta, Google Ads)", risk: "Minim\u00e1ln\u00ed", duty: "Zm\u00ednit v dokumentaci", icon: "\ud83d\udce1" },
    { name: "AI antispam (reCAPTCHA v3)", risk: "Minim\u00e1ln\u00ed", duty: "Zm\u00ednit v dokumentaci", icon: "\ud83d\udee1\ufe0f" },
    { name: "AI generovan\u00e9 popisy produkt\u016f", risk: "Omezen\u00e9", duty: "Ozna\u010dit jako AI obsah", icon: "\u270d\ufe0f" },
];

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Dom\u016f", href: "/" },
                { label: "AI Act", href: "/ai-act" },
                { label: "E-shopy" },
            ]}
            title="AI Act pro"
            titleAccent="e-shopy"
            subtitle="V\u011bt\u0161ina \u010desk\u00fdch e-shop\u016f pou\u017e\u00edv\u00e1 minim\u00e1ln\u011b 3\u20135 AI syst\u00e9m\u016f. Kter\u00e9 to jsou a co s nimi?"
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">AI syst\u00e9my typick\u00e9 pro e-shop</h2>
                <div className="space-y-3">
                    {aiSystems.map((s) => (
                        <div key={s.name} className="flex gap-4 rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
                            <span className="text-2xl flex-shrink-0">{s.icon}</span>
                            <div className="min-w-0">
                                <h3 className="font-semibold text-white text-sm">{s.name}</h3>
                                <p className="text-xs text-fuchsia-400 mt-0.5">Riziko: {s.risk}</p>
                                <p className="text-sm text-slate-400 mt-1">{s.duty}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Co mus\u00ed e-shop ud\u011blat?</h2>
                <ol className="list-decimal pl-6 space-y-2 text-slate-400">
                    <li><strong className="text-white">Zmapovat AI syst\u00e9my</strong> \u2014 AIshield to ud\u011bl\u00e1 za 60 sekund</li>
                    <li><strong className="text-white">Klasifikovat riziko</strong> \u2014 za\u0159adit ka\u017ed\u00fd syst\u00e9m do kategorie</li>
                    <li><strong className="text-white">Vytvo\u0159it transparen\u010dn\u00ed str\u00e1nku</strong> \u2014 <Link href="/ai-act/clanek-50" className="text-fuchsia-400 hover:text-fuchsia-300">dle \u010dl. 50</Link></li>
                    <li><strong className="text-white">Ozna\u010dit chatbot</strong> \u2014 informovat, \u017ee z\u00e1kazn\u00edk komunikuje s AI</li>
                    <li><strong className="text-white">Dokumentovat</strong> \u2014 registr AI syst\u00e9m\u016f, intern\u00ed AI politika</li>
                </ol>
            </section>
        </ContentPage>
    );
}
