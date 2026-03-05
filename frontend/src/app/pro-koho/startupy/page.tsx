import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "AI Act pro startupy a tech firmy — provider povinnosti — AIshield.cz",
    description:
        "Vyvíjíte AI produkt? Jako provider máte nejpřísnější povinnosti v AI Act. " +
        "Risk assessment, CE marking, technická dokumentace. AIshield pomáhá startupům s compliance.",
    alternates: { canonical: "/pro-koho/startupy" },
};

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Pro koho", href: "/pro-koho" },
                { label: "Startupy a tech firmy" },
            ]}
            title="AI Act pro startupy a tech firmy"
            titleAccent="— provider povinnosti"
            subtitle="Jako tvůrce AI produktu jste provider — máte nejpřísnější povinnosti v celém AI Act. Ale existuje i sandbox pro inovace."
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Provider vs. Deployer — klíčový rozdíl</h2>
                <div className="grid gap-4 sm:grid-cols-2">
                    <div className="rounded-xl border border-fuchsia-500/30 bg-slate-800/50 p-5">
                        <h3 className="text-lg font-semibold text-fuchsia-400 mb-2">Provider (vy)</h3>
                        <p className="text-slate-300 text-sm">
                            Vyvíjíte, trénujete nebo distribuujete AI systém. Máte plnou odpovědnost za risk assessment,
                            technickou dokumentaci, conformity assessment a CE marking (u high-risk systémů).
                        </p>
                    </div>
                    <div className="rounded-xl border border-cyan-500/30 bg-slate-800/50 p-5">
                        <h3 className="text-lg font-semibold text-cyan-400 mb-2">Deployer (váš klient)</h3>
                        <p className="text-slate-300 text-sm">
                            Váš klient, který AI nasazuje v provozu. Má transparenční povinnosti, lidský dohled
                            a musí sledovat reálný provoz systému.
                        </p>
                    </div>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Provider povinnosti podle AI Act</h2>
                <div className="space-y-3">
                    {[
                        { title: "Risk Management System", desc: "Článek 9 — průběžné hodnocení rizik po celý životní cyklus AI systému.", mandatory: true },
                        { title: "Technická dokumentace", desc: "Článek 11 — podrobný popis systému, dat, výkonu, testování.", mandatory: true },
                        { title: "Quality Management System", desc: "Článek 17 — procesy pro vývoj, testování, monitoring, incident management.", mandatory: true },
                        { title: "Conformity Assessment", desc: "Článek 43 — prokázání shody s AI Act před uvedením na trh.", mandatory: true },
                        { title: "CE Marking", desc: "Článek 48 — for high-risk systems, CE značka je povinná.", mandatory: false },
                        { title: "EU Database registrace", desc: "Článek 49 — registrace high-risk systémů v EU database.", mandatory: false },
                        { title: "Post-market monitoring", desc: "Článek 72 — sledování systému po nasazení, hlášení incidentů.", mandatory: true },
                    ].map((item) => (
                        <div key={item.title} className="flex items-start gap-3 rounded-lg border border-slate-700/50 bg-slate-800/30 p-4">
                            <span className={`shrink-0 text-sm font-bold ${item.mandatory ? "text-red-400" : "text-yellow-400"}`}>
                                {item.mandatory ? "POVINNÉ" : "HIGH-RISK"}
                            </span>
                            <div>
                                <h3 className="font-semibold text-white">{item.title}</h3>
                                <p className="text-sm text-slate-400 mt-1">{item.desc}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-4">AI Regulatory Sandbox — šance pro startupy</h2>
                <div className="space-y-4 text-slate-300">
                    <p>
                        AI Act zavádí <strong className="text-white">regulatorní sandbox</strong> (článek 57) —
                        kontrolované prostředí, kde startupy mohou testovat AI systémy pod dohledem regulátora
                        bez plného compliance burden. Česko musí sandbox zpřístupnit do <strong className="text-white">2. srpna 2026</strong>.
                    </p>
                    <p>
                        SME a startupy navíc mají právo na <strong className="text-white">prioritní přístup</strong> do sandboxu
                        a snížené poplatky za conformity assessment.
                    </p>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Jak AIshield pomáhá startupům</h2>
                <ul className="space-y-3">
                    {[
                        "Automatická detekce AI systémů na vašem webu a produktu",
                        "Risk assessment — zařazení do správné rizikové kategorie",
                        "Generování technické dokumentace (článek 11)",
                        "Transparenční stránka pro váš produkt i klienty",
                        "Příprava na conformity assessment",
                        "Monitoring compliance v čase (ongoing)",
                    ].map((item) => (
                        <li key={item} className="flex items-start gap-3">
                            <span className="text-fuchsia-400 mt-0.5">→</span>
                            <span className="text-slate-300">{item}</span>
                        </li>
                    ))}
                </ul>
            </section>

            <section>
                <div className="rounded-xl border border-fuchsia-500/30 bg-gradient-to-r from-fuchsia-900/20 to-cyan-900/20 p-8 text-center">
                    <h2 className="text-2xl font-bold text-white mb-3">
                        Bezplatný sken vašeho AI produktu
                    </h2>
                    <p className="text-slate-400 mb-6 max-w-lg mx-auto">
                        Zjistěte za 60 sekund, jaké povinnosti máte jako AI provider.
                    </p>
                    <div className="flex flex-col sm:flex-row gap-3 justify-center">
                        <Link
                            href="/scan"
                            className="inline-block rounded-lg bg-fuchsia-600 px-8 py-3 font-semibold text-white hover:bg-fuchsia-500 transition-colors"
                        >
                            Spustit bezplatný sken →
                        </Link>
                        <Link
                            href="/enterprise"
                            className="inline-block rounded-lg border border-slate-600 px-8 py-3 font-semibold text-white hover:border-fuchsia-500/50 transition-colors"
                        >
                            Enterprise pro tech firmy
                        </Link>
                    </div>
                </div>
            </section>
        </ContentPage>
    );
}
