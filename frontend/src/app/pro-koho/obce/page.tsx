import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "AI Act pro obce a veřejnou správu — AIshield.cz",
    description:
        "Obce, městské úřady a veřejné instituce s chatboty, AI dopravou nebo energetikou " +
        "mají přísnější pravidla v AI Act. AIshield pomáhá veřejnému sektoru s compliance.",
    alternates: { canonical: "/pro-koho/obce" },
};

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Pro koho", href: "/pro-koho" },
                { label: "Obce a veřejná správa" },
            ]}
            title="AI Act pro obce a veřejnou správu"
            titleAccent="— přísnější pravidla"
            subtitle="Veřejný sektor má v AI Act speciální postavení — některé AI systémy ve veřejné správě jsou automaticky vysoce rizikové. Připravte se včas."
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Proč veřejná správa musí řešit AI Act víc než soukromý sektor</h2>
                <div className="space-y-4 text-slate-300">
                    <p>
                        AI Act zařazuje některé systémy ve veřejné správě přímo do kategorie
                        <strong className="text-white"> vysoce rizikových</strong> (High-risk, příloha III).
                        To zahrnuje AI v přístupu k veřejným službám, sociální scoring, biometrii
                        a automatické rozhodování o občanech.
                    </p>
                    <p>
                        I chatbot na webových stránkách obce spadá minimálně pod
                        <strong className="text-white"> transparenční povinnost</strong> (článek 50).
                        Občan musí vědět, že komunikuje s AI systémem.
                    </p>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Typické AI systémy ve veřejné správě</h2>
                <div className="grid gap-4 sm:grid-cols-2">
                    {[
                        { name: "Chatbot na webu obce", risk: "Minimální riziko", duty: "Transparenční povinnost" },
                        { name: "AI v dopravě (semafory, analytika)", risk: "Může být HIGH-RISK", duty: "Plný risk assessment + audit" },
                        { name: "Rozpoznávání obličejů (CCTV)", risk: "ZAKÁZÁNO (s výjimkami)", duty: "Článek 5 — zákaz real-time surveillance" },
                        { name: "Automatické zpracování žádostí", risk: "HIGH-RISK", duty: "Lidský dohled + transparence" },
                        { name: "AI predikce kriminality", risk: "ZAKÁZÁNO", duty: "Článek 5 — explicitní zákaz" },
                        { name: "Energetický management s AI", risk: "Minimální riziko", duty: "Transparenční povinnost" },
                    ].map((item) => (
                        <div key={item.name} className="rounded-lg border border-slate-700/50 bg-slate-800/30 p-4">
                            <h3 className="font-semibold text-white">{item.name}</h3>
                            <p className={`text-xs mt-1 ${item.risk.includes("ZAKÁZ") ? "text-red-400" :
                                    item.risk.includes("HIGH") ? "text-orange-400" : "text-cyan-400"
                                }`}>{item.risk}</p>
                            <p className="text-sm text-slate-400 mt-1">{item.duty}</p>
                        </div>
                    ))}
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Co obce musí udělat</h2>
                <ol className="space-y-4">
                    {[
                        { step: "1", title: "Inventura AI systémů", desc: "Zmapujte všechny AI systémy — web, energetika, doprava, CCTV, administrativní procesy." },
                        { step: "2", title: "Kategorizace rizik", desc: "Rozdělte systémy do rizikových kategorií: zakázané → high-risk → limited → minimal." },
                        { step: "3", title: "Transparenční stránka", desc: "Každý web obce musí mít přístupný registr AI systémů a transparenční informace." },
                        { step: "4", title: "Lidský dohled", desc: "Pro high-risk systémy zajistěte lidský dohled (human oversight) a právo na vysvětlení." },
                        { step: "5", title: "Školení zaměstnanců", desc: "Článek 4 AI Act vyžaduje AI gramotnost pro zaměstnance, kteří pracují s AI." },
                    ].map((item) => (
                        <li key={item.step} className="flex gap-4">
                            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-fuchsia-600 text-sm font-bold text-white">
                                {item.step}
                            </span>
                            <div>
                                <h3 className="font-semibold text-white">{item.title}</h3>
                                <p className="text-sm text-slate-400 mt-1">{item.desc}</p>
                            </div>
                        </li>
                    ))}
                </ol>
            </section>

            <section>
                <div className="rounded-xl border border-fuchsia-500/30 bg-gradient-to-r from-fuchsia-900/20 to-cyan-900/20 p-8 text-center">
                    <h2 className="text-2xl font-bold text-white mb-3">
                        Bezplatný sken webu vaší obce
                    </h2>
                    <p className="text-slate-400 mb-6 max-w-lg mx-auto">
                        Zadejte URL webu obce — za 60 sekund zjistíte, jaké AI systémy provozujete a co musíte řešit.
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
                            Enterprise pro města
                        </Link>
                    </div>
                </div>
            </section>
        </ContentPage>
    );
}
