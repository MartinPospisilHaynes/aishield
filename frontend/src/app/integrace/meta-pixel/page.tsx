import type { Metadata } from "next";
import ContentPage from "@/components/content-page";

export const metadata: Metadata = {
    title: "Meta Pixel a AI Act \u2014 reklamn\u00ed AI na Facebooku a Instagramu",
    description:
        "Meta Pixel vyu\u017e\u00edv\u00e1 AI k optimalizaci reklam a c\u00edlen\u00ed. Jak\u00e9 m\u00e1te povinnosti dle AI Act?",
    alternates: { canonical: "https://aishield.cz/integrace/meta-pixel" },
};

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Dom\u016f", href: "/" },
                { label: "Integrace", href: "/integrace" },
                { label: "Meta Pixel" },
            ]}
            title="Meta Pixel a"
            titleAccent="AI Act"
            subtitle="Facebook & Instagram Pixel vyu\u017e\u00edv\u00e1 AI pro remarketing a Lookalike Audiences."
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">AI funkce v Meta Pixel</h2>
                <ul className="list-disc pl-6 space-y-1 text-slate-400">
                    <li><strong className="text-white">Conversion optimization</strong> \u2014 ML model optimalizuje, komu se reklama zobraz\u00ed</li>
                    <li><strong className="text-white">Lookalike Audiences</strong> \u2014 AI najde podobn\u00e9 u\u017eivatele</li>
                    <li><strong className="text-white">Advantage+ Shopping</strong> \u2014 plně automatizovan\u00e9 AI kampan\u011b</li>
                    <li><strong className="text-white">Event matching</strong> \u2014 ML p\u0159i\u0159azov\u00e1n\u00ed konverz\u00ed</li>
                </ul>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">AI Act klasifikace</h2>
                <div className="rounded-xl border border-green-500/30 bg-green-500/5 p-5">
                    <span className="text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full bg-green-500/20 text-green-400">
                        Minim\u00e1ln\u00ed riziko
                    </span>
                    <p className="text-slate-400 mt-3">
                        Reklamn\u00ed c\u00edlen\u00ed spadá do <strong className="text-white">minim\u00e1ln\u00edho rizika</strong>.
                        Nen\u00ed povinnost ozna\u010dovat, ale doporu\u010dujeme uv\u00e9st v dokumentaci.
                    </p>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Doporu\u010den\u00e9 kroky</h2>
                <ol className="list-decimal pl-6 space-y-2 text-slate-400">
                    <li><strong className="text-white">Zm\u00ednit v transparen\u010dn\u00ed str\u00e1nce</strong> \u2014 Meta Pixel, \u00fa\u010del: reklamn\u00ed c\u00edlen\u00ed</li>
                    <li><strong className="text-white">GDPR consent</strong> \u2014 Meta Pixel vy\u017eaduje souhlas \u2014 propojte s AI Act</li>
                    <li><strong className="text-white">Dokumentovat intern\u011b</strong> \u2014 zah\u0159ňte do registru AI syst\u00e9m\u016f</li>
                </ol>
            </section>
        </ContentPage>
    );
}
