import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "AI Act a české e-shopy: co musíte splnit do srpna 2026",
    description:
        "Praktický průvodce pro majitele českých e-shopů. Chatboty, doporučování produktů, " +
        "remarketing — co musíte splnit dle AI Actu a jak začít.",
    alternates: { canonical: "https://aishield.cz/blog/ai-act-a-e-shopy-v-cr" },
};

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Blog", href: "/blog" },
                { label: "AI Act a e-shopy v ČR" },
            ]}
            title="AI Act a české e-shopy:"
            titleAccent="co musíte splnit do srpna 2026"
            subtitle="15. února 2026 • 8 min čtení"
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Typický český e-shop a AI</h2>
                <p>
                    Průměrný český e-shop na <Link href="/integrace/shoptet" className="text-fuchsia-400 hover:text-fuchsia-300">Shoptetu</Link> nebo
                    WooCommerce používá <strong className="text-white">3–7 AI systémů</strong>, aniž by si to majitel
                    uvědomoval. Chatbot, doporučování, analytika, reklamní pixely — to vše obsahuje AI.
                </p>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">5 nejčastějších AI systémů na e-shopech</h2>
                <ol className="list-decimal pl-6 space-y-1 text-slate-400">
                    <li><strong className="text-white">Chatbot</strong> (Smartsupp, Tidio) — omezené riziko</li>
                    <li><strong className="text-white">Doporučování produktů</strong> — minimální riziko</li>
                    <li><strong className="text-white">Google Analytics 4</strong> — minimální riziko</li>
                    <li><strong className="text-white">Meta Pixel</strong> — minimální riziko</li>
                    <li><strong className="text-white">AI antispam</strong> (reCAPTCHA) — minimální riziko</li>
                </ol>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Co musíte udělat?</h2>
                <div className="rounded-2xl border border-fuchsia-500/20 bg-fuchsia-500/5 p-6">
                    <ol className="list-decimal pl-6 space-y-2 text-slate-400">
                        <li><Link href="/scan" className="text-fuchsia-400 hover:text-fuchsia-300">Skenovat web</Link> — AIshield najde všechny AI systémy</li>
                        <li>Vytvořit <Link href="/ai-act/clanek-50" className="text-fuchsia-400 hover:text-fuchsia-300">transparenční stránku</Link></li>
                        <li>Označit chatbot jako AI</li>
                        <li>Proškolit tým — AI gramotnost (čl. 4)</li>
                        <li>Nastavit pravidelný monitoring</li>
                    </ol>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Jaké jsou pokuty?</h2>
                <p>
                    Za nesplnití transparenčních povinností hrozí až <strong className="text-white">7,5 mil. EUR
                    nebo 1,5 % obratu</strong>. Pro e-shop s obratem 10 mil. Kč to znamená až 150 000 Kč za každý
                    neoznačený AI systém. Více v našem <Link href="/ai-act/pokuty" className="text-fuchsia-400 hover:text-fuchsia-300">přehledu pokut</Link>.
                </p>
            </section>
        </ContentPage>
    );
}
