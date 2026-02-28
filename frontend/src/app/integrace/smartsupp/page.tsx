import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "Smartsupp a AI Act — povinnosti pro české weby s chatbotem",
    description:
        "Smartsupp používá AI chatbot automation. Jak splnit AI Act? Transparenční povinnosti, označení, checklist.",
    alternates: { canonical: "https://aishield.cz/integrace/smartsupp" },
};

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Integrace", href: "/integrace" },
                { label: "Smartsupp" },
            ]}
            title="Smartsupp a"
            titleAccent="AI Act"
            subtitle="Jak splnit AI Act, pokud na webu používáte Smartsupp chatbot?"
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Co je Smartsupp?</h2>
                <p>
                    <a href="https://www.smartsupp.com/cs/" target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:text-cyan-300">Smartsupp</a> je
                    český nástroj pro live chat a chatbot automation. Používá ho přes <strong className="text-white">50 000 webů</strong>.
                    Od roku 2023 nabízí AI chatbot, který automaticky odpovídá na dotazy zákazníků.
                </p>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">AI Act klasifikace</h2>
                <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-5">
                    <div className="flex items-center gap-3 mb-2">
                        <span className="text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full bg-amber-500/20 text-amber-400">
                            Omezené riziko
                        </span>
                    </div>
                    <p className="text-slate-400">
                        Smartsupp chatbot spadá do kategorie <strong className="text-white">omezeného rizika</strong> dle
                        AI Act. Hlavní povinností je <Link href="/ai-act/clanek-50" className="text-fuchsia-400 hover:text-fuchsia-300">transparentnost dle čl. 50</Link>.
                    </p>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Co musíte udělat?</h2>
                <ol className="list-decimal pl-6 space-y-2 text-slate-400">
                    <li><strong className="text-white">Označte chatbot</strong> — viditelný text: &quot;Komunikujete s umělou inteligencí&quot;</li>
                    <li><strong className="text-white">Přidejte na transparenční stránku</strong> — uvést Smartsupp, účel, kategorii rizika</li>
                    <li><strong className="text-white">Umožněte opt-out</strong> — možnost přepnout na lidského operátora</li>
                    <li><strong className="text-white">Dokumentujte interně</strong> — zahřňte do registru AI systémů</li>
                </ol>
            </section>
        </ContentPage>
    );
}
