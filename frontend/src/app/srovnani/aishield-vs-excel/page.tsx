import type { Metadata } from "next";
import ContentPage from "@/components/content-page";

export const metadata: Metadata = {
    title: "AIshield vs Excel checklist \u2014 automatick\u00e1 detekce vs tabulka",
    description:
        "Excel checklist vy\u017eaduje manu\u00e1ln\u00ed odpov\u011bdi. AIshield automaticky detekuje AI syst\u00e9my. Srovn\u00e1n\u00ed p\u0159\u00edstup\u016f.",
    alternates: { canonical: "https://aishield.cz/srovnani/aishield-vs-excel" },
};

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Dom\u016f", href: "/" },
                { label: "Srovn\u00e1n\u00ed", href: "/srovnani" },
                { label: "vs Excel" },
            ]}
            title="AIshield vs"
            titleAccent="Excel checklist"
            subtitle="Automatick\u00e1 detekce vs 100+ \u0159\u00e1dk\u016f v tabulce. Co je efektivn\u011bj\u0161\u00ed?"
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Probl\u00e9m s Excel checklistem</h2>
                <ul className="list-disc pl-6 space-y-1 text-slate-400">
                    <li>Vy\u017eaduje <strong className="text-white">technick\u00e9 znalosti</strong> \u2014 mus\u00edte v\u011bd\u011bt, \u017ee reCAPTCHA v3 je AI</li>
                    <li><strong className="text-white">Subjektivn\u00ed odpov\u011bdi</strong> \u2014 ka\u017ed\u00fd odpov\u00ed jinak</li>
                    <li><strong className="text-white">Rychle zastar\u00e1v\u00e1</strong> \u2014 p\u0159id\u00e1te nov\u00fd plugin a Excel nev\u00ed</li>
                    <li><strong className="text-white">\u017d\u00e1dn\u00fd v\u00fdstup</strong> \u2014 nevygeneruje transparen\u010dn\u00ed str\u00e1nku</li>
                </ul>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Co AIshield d\u011bl\u00e1 jinak</h2>
                <div className="space-y-3">
                    {[
                        { label: "Automatick\u00e1 detekce", desc: "Nen\u00ed t\u0159eba nic vypl\u0148ovat \u2014 sta\u010d\u00ed zadat URL" },
                        { label: "Objektivn\u00ed v\u00fdsledky", desc: "Technick\u00e1 anal\u00fdza, ne n\u00e1zory" },
                        { label: "Aktu\u00e1ln\u00ed p\u0159i re-skenu", desc: "Ka\u017ed\u00fd sken zachyt\u00ed aktu\u00e1ln\u00ed stav" },
                        { label: "Report + transparen\u010dn\u00ed str\u00e1nka", desc: "Okam\u017eit\u00fd v\u00fdstup k nasazen\u00ed" },
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
