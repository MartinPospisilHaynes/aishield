import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "Co je transparen\u010dn\u00ed str\u00e1nka a pro\u010d ji pot\u0159ebujete",
    description:
        "\u010cl\u00e1nek 50 AI Actu vy\u017eaduje informovat u\u017eivatele o AI syst\u00e9mech na webu. " +
        "N\u00e1vod na vytvo\u0159en\u00ed transparen\u010dn\u00ed str\u00e1nky krok za krokem.",
    alternates: { canonical: "https://aishield.cz/blog/co-je-transparencni-stranka" },
};

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Dom\u016f", href: "/" },
                { label: "Blog", href: "/blog" },
                { label: "Transparen\u010dn\u00ed str\u00e1nka" },
            ]}
            title="Co je transparen\u010dn\u00ed str\u00e1nka"
            titleAccent="a pro\u010d ji pot\u0159ebujete"
            subtitle="10. \u00fanora 2026 \u2022 5 min \u010dten\u00ed"
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Nov\u00e1 povinnost od AI Act</h2>
                <p>
                    Tak jako GDPR p\u0159ineslo cookies li\u0161tu a privacy policy, AI Act p\u0159in\u00e1\u0161\u00ed nov\u00fd
                    prvek: <strong className="text-white">transparen\u010dn\u00ed str\u00e1nku o AI</strong>.
                </p>
                <p>
                    Jde o ve\u0159ejn\u011b p\u0159\u00edstupnou str\u00e1nku na va\u0161em webu, kde informujete n\u00e1v\u0161t\u011bvn\u00edky o tom,
                    jak\u00e9 AI syst\u00e9my pou\u017e\u00edv\u00e1te, pro\u010d je pou\u017e\u00edv\u00e1te a jak\u00e1 pr\u00e1va maj\u00ed u\u017eivatel\u00e9.
                </p>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Co mus\u00ed obsahovat?</h2>
                <ol className="list-decimal pl-6 space-y-2 text-slate-400">
                    <li><strong className="text-white">Seznam AI syst\u00e9m\u016f</strong> \u2014 ka\u017ed\u00fd n\u00e1stroj s AI na webu</li>
                    <li><strong className="text-white">\u00da\u010del pou\u017eit\u00ed</strong> \u2014 pro\u010d ka\u017ed\u00fd AI pou\u017e\u00edv\u00e1te</li>
                    <li><strong className="text-white">Poskytovatel</strong> \u2014 kdo AI vyvinul</li>
                    <li><strong className="text-white">Rizikov\u00e1 kategorie</strong> \u2014 dle <Link href="/ai-act/rizikove-kategorie" className="text-fuchsia-400 hover:text-fuchsia-300">AI Act klasifikace</Link></li>
                    <li><strong className="text-white">Kontaktn\u00ed osoba</strong> \u2014 kdo zodpov\u00edd\u00e1 za AI compliance</li>
                    <li><strong className="text-white">Pr\u00e1va u\u017eivatel\u016f</strong> \u2014 jak podat st\u00ed\u017enost nebo AI odm\u00edtnout</li>
                </ol>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Kde str\u00e1nku um\u00edstit?</h2>
                <p>
                    Doporu\u010dujeme um\u00edstit odkaz do <strong className="text-white">patičky webu</strong> vedle
                    cookies a GDPR politik. Typick\u00e1 URL: <code className="text-fuchsia-400">/ai-act-souhlas</code> nebo
                    <code className="text-fuchsia-400"> /ai-transparency</code>.
                </p>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">AIshield ji vygeneruje za v\u00e1s</h2>
                <p>
                    Po <Link href="/scan" className="text-fuchsia-400 hover:text-fuchsia-300">skenu webu</Link> AIshield automaticky:
                </p>
                <ul className="list-disc pl-6 space-y-1 text-slate-400">
                    <li>Identifikuje v\u0161echny AI syst\u00e9my</li>
                    <li>Klasifikuje riziko</li>
                    <li>Vygeneruje HTML k\u00f3d transparen\u010dn\u00ed str\u00e1nky</li>
                    <li>Sta\u010d\u00ed vlo\u017eit na web a je hotovo</li>
                </ul>
            </section>
        </ContentPage>
    );
}
