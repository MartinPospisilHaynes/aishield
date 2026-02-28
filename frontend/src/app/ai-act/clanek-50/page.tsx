import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "\u010cl\u00e1nek 50 AI Act \u2014 transparen\u010dn\u00ed povinnosti pro weby a e-shopy",
    description:
        "\u010cl\u00e1nek 50 AI Actu vy\u017eaduje informovat u\u017eivatele o interakci s AI syst\u00e9my. " +
        "Praktick\u00fd n\u00e1vod na vytvo\u0159en\u00ed transparen\u010dn\u00ed str\u00e1nky pro \u010desk\u00fd web.",
    alternates: { canonical: "https://aishield.cz/ai-act/clanek-50" },
};

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Dom\u016f", href: "/" },
                { label: "AI Act", href: "/ai-act" },
                { label: "\u010cl\u00e1nek 50" },
            ]}
            title="\u010cl\u00e1nek 50 AI Act \u2014"
            titleAccent="transparen\u010dn\u00ed povinnosti"
            subtitle="Co mus\u00edte zve\u0159ejnit na webu, aby va\u0161i u\u017eivatel\u00e9 v\u011bd\u011bli, \u017ee interaguj\u00ed s um\u011blou inteligenc\u00ed."
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Co \u0159\u00edk\u00e1 \u010dl\u00e1nek 50?</h2>
                <p>
                    \u010cl\u00e1nek 50 Na\u0159\u00edzen\u00ed (EU) 2024/1689 ukl\u00e1d\u00e1 nasazovatel\u016fm AI syst\u00e9m\u016f povinnost
                    informovat u\u017eivatele, \u017ee interaguj\u00ed s um\u011blou inteligenc\u00ed. Plat\u00ed zejm\u00e9na pro chatboty,
                    AI generovan\u00fd obsah a syst\u00e9my rozpozn\u00e1v\u00e1n\u00ed emoc\u00ed.
                </p>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Co mus\u00ed transparen\u010dn\u00ed str\u00e1nka obsahovat?</h2>
                <div className="space-y-3">
                    {[
                        { n: "1", title: "Seznam AI syst\u00e9m\u016f", desc: "V\u00fd\u010det v\u0161ech AI n\u00e1stroj\u016f na webu \u2014 chatbot, analytika, doporu\u010dov\u00e1n\u00ed, antispam." },
                        { n: "2", title: "\u00da\u010del ka\u017ed\u00e9ho syst\u00e9mu", desc: "Pro\u010d AI pou\u017e\u00edv\u00e1te \u2014 z\u00e1kaznick\u00fd servis, anal\u00fdza n\u00e1v\u0161t\u011bvnosti, personalizace." },
                        { n: "3", title: "Poskytovatel AI", desc: "Kdo AI vyvinul \u2014 Google (Analytics), Smartsupp (chatbot), Meta (pixel)." },
                        { n: "4", title: "Rizikov\u00e1 kategorie", desc: "Klasifikace dle AI Act \u2014 v\u011bt\u0161ina webov\u00fdch n\u00e1stroj\u016f = omezen\u00e9 riziko." },
                        { n: "5", title: "Kontakt", desc: "Kdo ve firm\u011b zodpov\u00edd\u00e1 za AI compliance." },
                        { n: "6", title: "Pr\u00e1va u\u017eivatel\u016f", desc: "Jak m\u016f\u017ee u\u017eivatel AI odm\u00edtnout nebo podat st\u00ed\u017enost." },
                    ].map((item) => (
                        <div key={item.n} className="flex gap-4">
                            <span className="flex-shrink-0 w-8 h-8 rounded-lg bg-fuchsia-500/20 text-fuchsia-400 flex items-center justify-center text-sm font-bold">
                                {item.n}
                            </span>
                            <div>
                                <h3 className="font-semibold text-white">{item.title}</h3>
                                <p className="text-sm text-slate-400">{item.desc}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">AIshield ji vygeneruje automaticky</h2>
                <p>
                    Po <Link href="/scan" className="text-fuchsia-400 hover:text-fuchsia-300">bezplatn\u00e9m skenu</Link> va\u0161eho
                    webu AIshield automaticky identifikuje v\u0161echny AI syst\u00e9my a vygeneruje kompletní transparen\u010dn\u00ed str\u00e1nku p\u0159ipravenou k nasazen\u00ed.
                </p>
            </section>
        </ContentPage>
    );
}
