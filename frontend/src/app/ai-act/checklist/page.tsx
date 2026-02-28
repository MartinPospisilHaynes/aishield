import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "AI Act checklist \u2014 10 krok\u016f ke compliance pro \u010desk\u00e9 firmy",
    description:
        "Praktick\u00fd 10bodov\u00fd checklist pro spln\u011bn\u00ed AI Act. Od identifikace AI syst\u00e9m\u016f po vytvo\u0159en\u00ed dokumentace.",
    alternates: { canonical: "https://aishield.cz/ai-act/checklist" },
};

const steps = [
    { n: 1, title: "Identifikujte AI syst\u00e9my na webu", desc: "Spus\u0165te AIshield sken \u2014 automaticky najde chatboty, analytiku, ML modely.", action: "Skenovat zdarma", href: "/scan" },
    { n: 2, title: "Zmapujte intern\u00ed AI", desc: "Pou\u017e\u00edv\u00e1te ChatGPT, Copilot, AI v \u00fa\u010detnictv\u00ed? I to spad\u00e1 pod AI Act.", action: "Vyplnit dotazn\u00edk", href: "/dotaznik" },
    { n: 3, title: "Klasifikujte riziko", desc: "Za\u0159a\u010fte ka\u017ed\u00fd AI syst\u00e9m do kategorie.", action: "Rizikov\u00e9 kategorie", href: "/ai-act/rizikove-kategorie" },
    { n: 4, title: "Vytvo\u0159te registr AI syst\u00e9m\u016f", desc: "Centr\u00e1ln\u00ed dokument se seznamem v\u0161ech AI, jejich \u00fa\u010delem a rizikovou kategori\u00ed." },
    { n: 5, title: "Napi\u0161te transparen\u010dn\u00ed str\u00e1nku", desc: "HTML str\u00e1nka informuj\u00edc\u00ed u\u017eivatele o AI na webu dle \u010dl. 50.", action: "\u010cl\u00e1nek 50", href: "/ai-act/clanek-50" },
    { n: 6, title: "Ozna\u010dte chatbot", desc: "Vidieln\u00fd banner: Komunikujete s um\u011blou inteligenc\u00ed." },
    { n: 7, title: "Ozna\u010dte AI obsah", desc: "Pokud generujete texty nebo obr\u00e1zky pomoc\u00ed AI \u2014 ozna\u010dte je." },
    { n: 8, title: "Vytvo\u0159te intern\u00ed AI politiku", desc: "Pravidla pro zam\u011bstnance: jak sm\u00ed AI pou\u017e\u00edvat, co je zak\u00e1zan\u00e9." },
    { n: 9, title: "Zajist\u011bte AI gramotnost", desc: "\u010cl\u00e1nek 4 vy\u017eaduje dostate\u010dn\u00e9 znalosti osob pracuj\u00edc\u00edch s AI." },
    { n: 10, title: "Nastavte monitoring", desc: "AI syst\u00e9my se m\u011bn\u00ed. Nastavte pravideln\u00fd re-sken." },
];

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Dom\u016f", href: "/" },
                { label: "AI Act", href: "/ai-act" },
                { label: "Checklist" },
            ]}
            title="AI Act"
            titleAccent="checklist"
            subtitle="10 krok\u016f ke compliance. Praktick\u00fd n\u00e1vod, kter\u00fd zvl\u00e1dne i mal\u00e1 firma bez pr\u00e1vn\u00edka."
        >
            <div className="space-y-4">
                {steps.map((s) => (
                    <div key={s.n} className="flex gap-4 rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
                        <span className="flex-shrink-0 w-10 h-10 rounded-xl bg-fuchsia-500/20 text-fuchsia-400 flex items-center justify-center text-lg font-bold">
                            {s.n}
                        </span>
                        <div>
                            <h3 className="font-semibold text-white">{s.title}</h3>
                            <p className="text-sm text-slate-400 mt-1">{s.desc}</p>
                            {s.action && s.href && (
                                <Link href={s.href} className="text-sm text-fuchsia-400 hover:text-fuchsia-300 mt-2 inline-block">
                                    {s.action} \u2192
                                </Link>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </ContentPage>
    );
}
