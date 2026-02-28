import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "Smartsupp a AI Act \u2014 povinnosti pro \u010desk\u00e9 weby s chatbotem",
    description:
        "Smartsupp pou\u017e\u00edv\u00e1 AI chatbot automation. Jak splnit AI Act? Transparen\u010dn\u00ed povinnosti, ozna\u010den\u00ed, checklist.",
    alternates: { canonical: "https://aishield.cz/integrace/smartsupp" },
};

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Dom\u016f", href: "/" },
                { label: "Integrace", href: "/integrace" },
                { label: "Smartsupp" },
            ]}
            title="Smartsupp a"
            titleAccent="AI Act"
            subtitle="Jak splnit AI Act, pokud na webu pou\u017e\u00edv\u00e1te Smartsupp chatbot?"
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Co je Smartsupp?</h2>
                <p>
                    <a href="https://www.smartsupp.com/cs/" target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:text-cyan-300">Smartsupp</a> je
                    \u010desk\u00fd n\u00e1stroj pro live chat a chatbot automation. Pou\u017e\u00edv\u00e1 ho p\u0159es <strong className="text-white">50 000 web\u016f</strong>.
                    Od roku 2023 nab\u00edz\u00ed AI chatbot, kter\u00fd automaticky odpov\u00edd\u00e1 na dotazy z\u00e1kazn\u00edk\u016f.
                </p>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">AI Act klasifikace</h2>
                <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-5">
                    <div className="flex items-center gap-3 mb-2">
                        <span className="text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full bg-amber-500/20 text-amber-400">
                            Omezen\u00e9 riziko
                        </span>
                    </div>
                    <p className="text-slate-400">
                        Smartsupp chatbot spad\u00e1 do kategorie <strong className="text-white">omezen\u00e9ho rizika</strong> dle
                        AI Act. Hlavn\u00ed povinnost\u00ed je <Link href="/ai-act/clanek-50" className="text-fuchsia-400 hover:text-fuchsia-300">transparentnost dle \u010dl. 50</Link>.
                    </p>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Co mus\u00edte ud\u011blat?</h2>
                <ol className="list-decimal pl-6 space-y-2 text-slate-400">
                    <li><strong className="text-white">Ozna\u010dte chatbot</strong> \u2014 viditeln\u00fd text: &quot;Komunikujete s um\u011blou inteligenc\u00ed&quot;</li>
                    <li><strong className="text-white">P\u0159idejte na transparen\u010dn\u00ed str\u00e1nku</strong> \u2014 uv\u00e9st Smartsupp, \u00fa\u010del, kategorii rizika</li>
                    <li><strong className="text-white">Umo\u017en\u011bte opt-out</strong> \u2014 mo\u017enost p\u0159epnout na lidsk\u00e9ho oper\u00e1tora</li>
                    <li><strong className="text-white">Dokumentujte intern\u011b</strong> \u2014 zah\u0159\u0148te do registru AI syst\u00e9m\u016f</li>
                </ol>
            </section>
        </ContentPage>
    );
}
