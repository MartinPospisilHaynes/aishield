import type { Metadata } from "next";
import ContentPage from "@/components/content-page";

export const metadata: Metadata = {
    title: "Google Analytics 4 a AI Act — ML predikce, predictive audiences",
    description:
        "Google Analytics 4 využívá machine learning k predikci chování. Jaké máte povinnosti dle AI Act?",
    alternates: { canonical: "https://aishield.cz/integrace/google-analytics" },
};

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Integrace", href: "/integrace" },
                { label: "Google Analytics" },
            ]}
            title="Google Analytics 4 a"
            titleAccent="AI Act"
            subtitle="GA4 používá ML predikce, smart audiences a AI-driven insights. Co to znamená pro vás?"
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">AI funkce v GA4</h2>
                <ul className="list-disc pl-6 space-y-1 text-slate-400">
                    <li><strong className="text-white">Predictive audiences</strong> — ML model predikuje, kteří uživatelé nakoupí</li>
                    <li><strong className="text-white">Anomaly detection</strong> — automatické rozpoznávání neobvyklého chování</li>
                    <li><strong className="text-white">AI-driven insights</strong> — automatické zjištění trendů</li>
                    <li><strong className="text-white">Smart audiences</strong> — ML segmentace uživatelů pro remarketing</li>
                </ul>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">AI Act klasifikace</h2>
                <div className="rounded-xl border border-green-500/30 bg-green-500/5 p-5">
                    <span className="text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full bg-green-500/20 text-green-400">
                        Minimální riziko
                    </span>
                    <p className="text-slate-400 mt-3">
                        GA4 analytické AI funkce spadají do <strong className="text-white">minimálního rizika</strong>.
                        Žádné povinné regulatorní požadavky, ale doporučujeme zmínit na transparenční stránce.
                    </p>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Doporučené kroky</h2>
                <ol className="list-decimal pl-6 space-y-2 text-slate-400">
                    <li><strong className="text-white">Uvést na transparenční stránce</strong> — Google Analytics, účel: analýza návštěvnosti</li>
                    <li><strong className="text-white">Zmínit ML funkce</strong> — pokud využíváte predictive audiences, uvést to</li>
                    <li><strong className="text-white">GDPR synegie</strong> — GA4 vyžaduje consent — propojte s AI Act dokumentací</li>
                </ol>
            </section>
        </ContentPage>
    );
}
