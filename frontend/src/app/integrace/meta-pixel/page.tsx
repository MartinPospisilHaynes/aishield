import type { Metadata } from "next";
import ContentPage from "@/components/content-page";

export const metadata: Metadata = {
    title: "Meta Pixel a AI Act — reklamní AI na Facebooku a Instagramu",
    description:
        "Meta Pixel využívá AI k optimalizaci reklam a cílení. Jaké máte povinnosti dle AI Act?",
    alternates: { canonical: "https://aishield.cz/integrace/meta-pixel" },
};

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Integrace", href: "/integrace" },
                { label: "Meta Pixel" },
            ]}
            title="Meta Pixel a"
            titleAccent="AI Act"
            subtitle="Facebook & Instagram Pixel využívá AI pro remarketing a Lookalike Audiences."
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">AI funkce v Meta Pixel</h2>
                <ul className="list-disc pl-6 space-y-1 text-slate-400">
                    <li><strong className="text-white">Conversion optimization</strong> — ML model optimalizuje, komu se reklama zobrazí</li>
                    <li><strong className="text-white">Lookalike Audiences</strong> — AI najde podobné uživatele</li>
                    <li><strong className="text-white">Advantage+ Shopping</strong> — plně automatizované AI kampaně</li>
                    <li><strong className="text-white">Event matching</strong> — ML přiřazování konverzí</li>
                </ul>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">AI Act klasifikace</h2>
                <div className="rounded-xl border border-green-500/30 bg-green-500/5 p-5">
                    <span className="text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full bg-green-500/20 text-green-400">
                        Minimální riziko
                    </span>
                    <p className="text-slate-400 mt-3">
                        Reklamní cílení spadá do <strong className="text-white">minimálního rizika</strong>.
                        Není povinnost označovat, ale doporučujeme uvést v dokumentaci.
                    </p>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Doporučené kroky</h2>
                <ol className="list-decimal pl-6 space-y-2 text-slate-400">
                    <li><strong className="text-white">Zmínit v transparenční stránce</strong> — Meta Pixel, účel: reklamní cílení</li>
                    <li><strong className="text-white">GDPR consent</strong> — Meta Pixel vyžaduje souhlas — propojte s AI Act</li>
                    <li><strong className="text-white">Dokumentovat interně</strong> — zahřňte do registru AI systémů</li>
                </ol>
            </section>
        </ContentPage>
    );
}
