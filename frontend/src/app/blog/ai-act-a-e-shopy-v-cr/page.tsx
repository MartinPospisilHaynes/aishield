import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "AI Act a \u010desk\u00e9 e-shopy: co mus\u00edte splnit do srpna 2026",
    description:
        "Praktick\u00fd pr\u016fvodce pro majitele \u010desk\u00fdch e-shop\u016f. Chatboty, doporu\u010dov\u00e1n\u00ed produkt\u016f, " +
        "remarketing \u2014 co mus\u00edte splnit dle AI Actu a jak za\u010d\u00edt.",
    alternates: { canonical: "https://aishield.cz/blog/ai-act-a-e-shopy-v-cr" },
};

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Dom\u016f", href: "/" },
                { label: "Blog", href: "/blog" },
                { label: "AI Act a e-shopy v \u010cR" },
            ]}
            title="AI Act a \u010desk\u00e9 e-shopy:"
            titleAccent="co mus\u00edte splnit do srpna 2026"
            subtitle="15. \u00fanora 2026 \u2022 8 min \u010dten\u00ed"
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Typick\u00fd \u010desk\u00fd e-shop a AI</h2>
                <p>
                    Pr\u016fm\u011brn\u00fd \u010desk\u00fd e-shop na <Link href="/integrace/shoptet" className="text-fuchsia-400 hover:text-fuchsia-300">Shoptetu</Link> nebo
                    WooCommerce pou\u017e\u00edv\u00e1 <strong className="text-white">3\u20137 AI syst\u00e9m\u016f</strong>, ani\u017e by si to majitel
                    uv\u011bdomoval. Chatbot, doporu\u010dov\u00e1n\u00ed, analytika, reklamn\u00ed pixely \u2014 to v\u0161e obsahuje AI.
                </p>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">5 nej\u010dast\u011bj\u0161\u00edch AI syst\u00e9m\u016f na e-shopech</h2>
                <ol className="list-decimal pl-6 space-y-1 text-slate-400">
                    <li><strong className="text-white">Chatbot</strong> (Smartsupp, Tidio) \u2014 omezen\u00e9 riziko</li>
                    <li><strong className="text-white">Doporu\u010dov\u00e1n\u00ed produkt\u016f</strong> \u2014 minim\u00e1ln\u00ed riziko</li>
                    <li><strong className="text-white">Google Analytics 4</strong> \u2014 minim\u00e1ln\u00ed riziko</li>
                    <li><strong className="text-white">Meta Pixel</strong> \u2014 minim\u00e1ln\u00ed riziko</li>
                    <li><strong className="text-white">AI antispam</strong> (reCAPTCHA) \u2014 minim\u00e1ln\u00ed riziko</li>
                </ol>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Co mus\u00edte ud\u011blat?</h2>
                <div className="rounded-2xl border border-fuchsia-500/20 bg-fuchsia-500/5 p-6">
                    <ol className="list-decimal pl-6 space-y-2 text-slate-400">
                        <li><Link href="/scan" className="text-fuchsia-400 hover:text-fuchsia-300">Skenovat web</Link> \u2014 AIshield najde v\u0161echny AI syst\u00e9my</li>
                        <li>Vytvo\u0159it <Link href="/ai-act/clanek-50" className="text-fuchsia-400 hover:text-fuchsia-300">transparen\u010dn\u00ed str\u00e1nku</Link></li>
                        <li>Ozna\u010dit chatbot jako AI</li>
                        <li>Pro\u0161kolit t\u00fdm \u2014 AI gramotnost (\u010dl. 4)</li>
                        <li>Nastavit pravideln\u00fd monitoring</li>
                    </ol>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Jak\u00e9 jsou pokuty?</h2>
                <p>
                    Za nesplnit\u00ed transparen\u010dn\u00edch povinnost\u00ed hroz\u00ed a\u017e <strong className="text-white">7,5 mil. EUR
                    nebo 1,5 % obratu</strong>. Pro e-shop s obratem 10 mil. K\u010d to znamen\u00e1 a\u017e 150 000 K\u010d za ka\u017ed\u00fd
                    neozna\u010den\u00fd AI syst\u00e9m. V\u00edce v na\u0161em <Link href="/ai-act/pokuty" className="text-fuchsia-400 hover:text-fuchsia-300">p\u0159ehledu pokut</Link>.
                </p>
            </section>
        </ContentPage>
    );
}
