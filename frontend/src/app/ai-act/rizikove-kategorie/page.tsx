import type { Metadata } from "next";
import ContentPage from "@/components/content-page";

export const metadata: Metadata = {
    title: "Rizikov\u00e9 kategorie AI Act \u2014 nep\u0159ijateln\u00e9, vysok\u00e9, omezen\u00e9, minim\u00e1ln\u00ed",
    description:
        "AI Act rozd\u011bluje AI syst\u00e9my do 4 rizikov\u00fdch kategori\u00ed. Zjist\u011bte, kam spad\u00e1 v\u00e1\u0161 chatbot, " +
        "analytika nebo doporu\u010dovac\u00ed syst\u00e9m a jak\u00e9 povinnosti z toho plynou.",
    alternates: { canonical: "https://aishield.cz/ai-act/rizikove-kategorie" },
};

const categories = [
    {
        level: "Nep\u0159ijateln\u00e9 riziko",
        border: "border-red-500/30 bg-red-500/5",
        badge: "bg-red-500/20 text-red-400",
        desc: "AI syst\u00e9my, kter\u00e9 jsou v EU zcela zak\u00e1z\u00e1ny od \u00fanora 2025.",
        examples: ["Soci\u00e1ln\u00ed bodov\u00e1n\u00ed (social scoring)", "Biometrick\u00e1 identifikace v re\u00e1ln\u00e9m \u010dase na ve\u0159ejnosti", "Manipulativn\u00ed techniky zneu\u017e\u00edvaj\u00edc\u00ed slabosti osob", "Prediktivn\u00ed policing"],
        duty: "Absolutn\u00ed z\u00e1kaz. Pokuta a\u017e 35 mil. EUR nebo 7 % obratu.",
    },
    {
        level: "Vysok\u00e9 riziko",
        border: "border-orange-500/30 bg-orange-500/5",
        badge: "bg-orange-500/20 text-orange-400",
        desc: "AI syst\u00e9my s v\u00fdznamn\u00fdm dopadem na lidsk\u00e1 pr\u00e1va a bezpe\u010dnost.",
        examples: ["AI v n\u00e1boru a hodnocen\u00ed zam\u011bstnanc\u016f", "AI v kreditn\u00edm scoringu", "AI v zdravotnictv\u00ed", "AI v kritick\u00e9 infrastruktu\u0159e"],
        duty: "Risk assessment, technick\u00e1 dokumentace, lidsk\u00fd dohled. Pokuta a\u017e 15 mil. EUR.",
    },
    {
        level: "Omezen\u00e9 riziko",
        border: "border-amber-500/30 bg-amber-500/5",
        badge: "bg-amber-500/20 text-amber-400",
        desc: "AI syst\u00e9my, kde mus\u00edte u\u017eivatele informovat o interakci s AI. Sem spad\u00e1 v\u011bt\u0161ina webov\u00fdch AI.",
        examples: ["Chatboty (Smartsupp, Tidio, Crisp)", "AI generovan\u00fd obsah", "Deepfakes a syntetick\u00e1 m\u00e9dia", "Emo\u010dn\u00ed rozpozn\u00e1v\u00e1n\u00ed"],
        duty: "Transparen\u010dn\u00ed povinnost dle \u010dl. 50. Pokuta a\u017e 7,5 mil. EUR.",
    },
    {
        level: "Minim\u00e1ln\u00ed riziko",
        border: "border-green-500/30 bg-green-500/5",
        badge: "bg-green-500/20 text-green-400",
        desc: "AI syst\u00e9my bez specifick\u00fdch regulatorn\u00edch povinnost\u00ed.",
        examples: ["Spam filtry", "AI ve videohr\u00e1ch", "Automatick\u00e9 dopl\u0148ov\u00e1n\u00ed textu", "Doporu\u010dov\u00e1n\u00ed obsahu"],
        duty: "\u017d\u00e1dn\u00e9 povinn\u00e9 po\u017eadavky. Doporu\u010den\u00e9 dodr\u017eov\u00e1n\u00ed kodexu chov\u00e1n\u00ed.",
    },
];

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Dom\u016f", href: "/" },
                { label: "AI Act", href: "/ai-act" },
                { label: "Rizikov\u00e9 kategorie" },
            ]}
            title="Rizikov\u00e9 kategorie"
            titleAccent="AI Act"
            subtitle="AI Act rozd\u011bluje AI syst\u00e9my do 4 \u00farovn\u00ed rizika. \u010c\u00edm vy\u0161\u0161\u00ed riziko, t\u00edm p\u0159\u00edsn\u011bj\u0161\u00ed povinnosti."
        >
            {categories.map((cat) => (
                <section key={cat.level} className={`rounded-2xl border ${cat.border} p-6`}>
                    <div className="flex items-center gap-3 mb-4">
                        <span className={`text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full ${cat.badge}`}>
                            {cat.level}
                        </span>
                    </div>
                    <p className="text-slate-300 mb-4">{cat.desc}</p>
                    <h3 className="text-sm font-semibold text-white mb-2">P\u0159\u00edklady:</h3>
                    <ul className="list-disc pl-6 space-y-1 text-slate-400 mb-4">
                        {cat.examples.map((ex) => (
                            <li key={ex}>{ex}</li>
                        ))}
                    </ul>
                    <div className="rounded-lg bg-white/[0.03] p-3">
                        <p className="text-sm text-slate-400">
                            <strong className="text-white">Povinnosti: </strong>{cat.duty}
                        </p>
                    </div>
                </section>
            ))}
        </ContentPage>
    );
}
