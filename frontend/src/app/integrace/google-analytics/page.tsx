import type { Metadata } from "next";
import ContentPage from "@/components/content-page";

export const metadata: Metadata = {
    title: "Google Analytics 4 a AI Act \u2014 ML predikce, predictive audiences",
    description:
        "Google Analytics 4 vyu\u017e\u00edv\u00e1 machine learning k predikci chov\u00e1n\u00ed. Jak\u00e9 m\u00e1te povinnosti dle AI Act?",
    alternates: { canonical: "https://aishield.cz/integrace/google-analytics" },
};

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Dom\u016f", href: "/" },
                { label: "Integrace", href: "/integrace" },
                { label: "Google Analytics" },
            ]}
            title="Google Analytics 4 a"
            titleAccent="AI Act"
            subtitle="GA4 pou\u017e\u00edv\u00e1 ML predikce, smart audiences a AI-driven insights. Co to znamen\u00e1 pro v\u00e1s?"
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">AI funkce v GA4</h2>
                <ul className="list-disc pl-6 space-y-1 text-slate-400">
                    <li><strong className="text-white">Predictive audiences</strong> \u2014 ML model predikuje, kte\u0159\u00ed u\u017eivatel\u00e9 nakoup\u00ed</li>
                    <li><strong className="text-white">Anomaly detection</strong> \u2014 automatick\u00e9 rozpozn\u00e1v\u00e1n\u00ed neobvykl\u00e9ho chov\u00e1n\u00ed</li>
                    <li><strong className="text-white">AI-driven insights</strong> \u2014 automatick\u00e9 zji\u0161t\u011bn\u00ed trend\u016f</li>
                    <li><strong className="text-white">Smart audiences</strong> \u2014 ML segmentace u\u017eivatel\u016f pro remarketing</li>
                </ul>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">AI Act klasifikace</h2>
                <div className="rounded-xl border border-green-500/30 bg-green-500/5 p-5">
                    <span className="text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full bg-green-500/20 text-green-400">
                        Minim\u00e1ln\u00ed riziko
                    </span>
                    <p className="text-slate-400 mt-3">
                        GA4 analytick\u00e9 AI funkce spadaj\u00ed do <strong className="text-white">minim\u00e1ln\u00edho rizika</strong>.
                        \u017d\u00e1dn\u00e9 povinn\u00e9 regulatorn\u00ed po\u017eadavky, ale doporu\u010dujeme zm\u00ednit na transparen\u010dn\u00ed str\u00e1nce.
                    </p>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Doporu\u010den\u00e9 kroky</h2>
                <ol className="list-decimal pl-6 space-y-2 text-slate-400">
                    <li><strong className="text-white">Uv\u00e9st na transparen\u010dn\u00ed str\u00e1nce</strong> \u2014 Google Analytics, \u00fa\u010del: anal\u00fdza n\u00e1v\u0161t\u011bvnosti</li>
                    <li><strong className="text-white">Zm\u00ednit ML funkce</strong> \u2014 pokud vyu\u017e\u00edv\u00e1te predictive audiences, uv\u00e9st to</li>
                    <li><strong className="text-white">GDPR synegie</strong> \u2014 GA4 vy\u017eaduje consent \u2014 propojte s AI Act dokumentac\u00ed</li>
                </ol>
            </section>
        </ContentPage>
    );
}
