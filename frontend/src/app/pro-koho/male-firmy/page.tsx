import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "AI Act pro malé a střední firmy (SME) — AIshield.cz",
    description:
        "I malá firma s chatbotem musí splnit EU AI Act. AIshield pomáhá malým a středním podnikům " +
        "v celé ČR — automatický sken, transparenční stránka, risk assessment od 4 999 Kč.",
    alternates: { canonical: "/pro-koho/male-firmy" },
};

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Pro koho", href: "/pro-koho" },
                { label: "Malé a střední firmy" },
            ]}
            title="AI Act pro malé a střední firmy"
            titleAccent="— SME compliance za dostupnou cenu"
            subtitle="Máte chatbot na webu? AI analytiku? EU AI Act se týká i firem s 5 zaměstnanci. Ale má pro SME mírnější pravidla — využijte je."
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Mýty vs. realita: AI Act a malé firmy</h2>
                <div className="space-y-4">
                    {[
                        { myth: "AI Act se týká jen velkých korporátů", reality: "Vztahuje se na KAŽDÉHO, kdo provozuje AI systém v EU — bez ohledu na velikost firmy." },
                        { myth: "Malá firma nedostane pokutu", reality: "Pokuty jsou odstupňované podle obratu (až 3 % pro SME místo 7 %), ale stále mohou být likvidační." },
                        { myth: "Chatbot není AI systém", reality: "Chatbot s NLP (Smartsupp, Tidio, OpenAI) JE AI systém podle definice v článku 3 AI Act." },
                        { myth: "Stačí napsat do GDPR stránky, že používáme AI", reality: "AI Act vyžaduje SAMOSTATNOU transparenční stránku s technickými detaily o každém AI systému." },
                    ].map((item) => (
                        <div key={item.myth} className="rounded-lg border border-slate-700/50 bg-slate-800/30 p-4">
                            <div className="flex items-start gap-3">
                                <span className="text-red-400 font-bold shrink-0">✗</span>
                                <div>
                                    <p className="text-slate-400 line-through">{item.myth}</p>
                                    <p className="text-slate-300 mt-1">
                                        <span className="text-green-400 font-bold">✓</span> {item.reality}
                                    </p>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Typické AI systémy v malých firmách</h2>
                <ul className="space-y-3">
                    {[
                        "Chatbot na webu (Smartsupp, Tidio, vlastní GPT)",
                        "Google Analytics 4 s AI-powered insights",
                        "Meta Pixel s AI cílením reklam",
                        "AI doporučování produktů v e-shopu",
                        "AI nástroje pro zákaznickou podporu",
                        "AI účetní software (automatická kategorizace)",
                        "AI CRM s prediktivním scoringem",
                    ].map((item) => (
                        <li key={item} className="flex items-start gap-3">
                            <span className="text-fuchsia-400 mt-0.5">→</span>
                            <span className="text-slate-300">{item}</span>
                        </li>
                    ))}
                </ul>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-4">3 kroky ke compliance pro malou firmu</h2>
                <div className="grid gap-4 sm:grid-cols-3">
                    {[
                        { step: "1", title: "Bezplatný sken", desc: "Zadejte URL webu → za 60 sekund víte, jaké AI systémy máte.", time: "1 minuta" },
                        { step: "2", title: "Dotazník", desc: "Odpovězte na 15 otázek o vašem podnikání a využití AI.", time: "10 minut" },
                        { step: "3", title: "Dokumentace", desc: "Automaticky vygenerujeme transparenční stránku a risk assessment.", time: "24 hodin" },
                    ].map((item) => (
                        <div key={item.step} className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-5 text-center">
                            <div className="text-3xl font-bold text-fuchsia-400 mb-2">{item.step}</div>
                            <h3 className="font-semibold text-white">{item.title}</h3>
                            <p className="text-sm text-slate-400 mt-2">{item.desc}</p>
                            <p className="text-xs text-cyan-400 mt-2">⏱ {item.time}</p>
                        </div>
                    ))}
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Cenová dostupnost pro SME</h2>
                <div className="space-y-4 text-slate-300">
                    <p>
                        Rozumíme, že malá firma nemá budget na právní kancelář za 100 000 Kč.
                        Proto nabízíme <strong className="text-white">BASIC balíček od 4 999 Kč</strong> —
                        kompletní transparenční stránka, registr AI systémů a základní risk assessment.
                    </p>
                    <p>
                        Vše je automatizované díky AI, takže cena zůstává dostupná i pro živnostníky a mikrofirmy.
                    </p>
                </div>
            </section>

            <section>
                <div className="rounded-xl border border-fuchsia-500/30 bg-gradient-to-r from-fuchsia-900/20 to-cyan-900/20 p-8 text-center">
                    <h2 className="text-2xl font-bold text-white mb-3">
                        Zjistěte, co musí vaše firma udělat
                    </h2>
                    <p className="text-slate-400 mb-6 max-w-lg mx-auto">
                        Bezplatný sken za 60 sekund — žádná registrace, žádné závazky.
                    </p>
                    <div className="flex flex-col sm:flex-row gap-3 justify-center">
                        <Link
                            href="/scan"
                            className="inline-block rounded-lg bg-fuchsia-600 px-8 py-3 font-semibold text-white hover:bg-fuchsia-500 transition-colors"
                        >
                            Spustit bezplatný sken →
                        </Link>
                        <Link
                            href="/pricing"
                            className="inline-block rounded-lg border border-slate-600 px-8 py-3 font-semibold text-white hover:border-fuchsia-500/50 transition-colors"
                        >
                            Zobrazit ceník
                        </Link>
                    </div>
                </div>
            </section>
        </ContentPage>
    );
}
