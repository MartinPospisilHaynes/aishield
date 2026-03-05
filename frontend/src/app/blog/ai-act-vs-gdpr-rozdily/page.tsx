import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import BlogCta from "@/components/blog-cta";
import Link from "next/link";

export const metadata: Metadata = {
    title: "AI Act vs GDPR — 10 rozdílů které musíte znát",
    description:
        "Srovnání EU AI Actu a GDPR: pokuty, povinnosti, dozor, lhůty. 10 klíčových rozdílů pro české firmy.",
    alternates: { canonical: "https://aishield.cz/blog/ai-act-vs-gdpr-rozdily" },
    openGraph: {
        images: [{ url: "/blog/ai-act-vs-gdpr-rozdily.png", width: 1200, height: 630 }],
    },
    keywords: [
        "AI Act vs GDPR",
        "rozdíl AI Act GDPR",
        "EU AI regulace",
        "AI Act srovnání",
        "GDPR a AI",
        "AI compliance Česko",
    ],
};

const differences = [
    {
        num: 1,
        title: "Co regulují",
        aiAct: "Umělou inteligenci — AI systémy, modely a jejich nasazení v EU.",
        gdpr: "Osobní údaje — sběr, zpracování a ukládání dat o fyzických osobách.",
    },
    {
        num: 2,
        title: "Rizikový přístup",
        aiAct: "4 úrovně rizika: nepřijatelné → vysoké → omezené → minimální. Povinnosti se liší podle kategorie.",
        gdpr: "Jednotný režim. Platí stejná pravidla pro všechny zpracovatele osobních údajů.",
    },
    {
        num: 3,
        title: "Maximální pokuta",
        aiAct: "35 milionů EUR nebo 7 % obratu — za zakázané AI praktiky.",
        gdpr: "20 milionů EUR nebo 4 % obratu — za nejzávažnější porušení.",
    },
    {
        num: 4,
        title: "Účinnost",
        aiAct: "Postupná: únor 2025 (zákazy) → srpen 2025 (GPAI) → srpen 2026 (čl. 50) → srpen 2027 (Příloha III).",
        gdpr: "Jednorázová: 25. května 2018 pro všechny povinnosti najednou.",
    },
    {
        num: 5,
        title: "Souhlas uživatele",
        aiAct: "Nevyžaduje souhlas. Povinnost je transparence — informovat, že AI se používá.",
        gdpr: "Souhlas je jedním z 6 právních základů zpracování. Klíčový pro marketing a cookies.",
    },
    {
        num: 6,
        title: "Dokumentace",
        aiAct: "Technická dokumentace AI systému, registr rizik, posouzení shody, transparenční stránka.",
        gdpr: "Záznamy o zpracování, DPIA (posouzení vlivu), informační povinnost, DPO.",
    },
    {
        num: 7,
        title: "Dozorový orgán v ČR",
        aiAct: "Zatím neurčen — pravděpodobně NÚKIB, ČTÚ nebo nový orgán. Rozhodnutí se čeká v 2026.",
        gdpr: "ÚOOÚ (Úřad pro ochranu osobních údajů) — funguje od roku 2000.",
    },
    {
        num: 8,
        title: "Extrateritoriální dosah",
        aiAct: "Ano — platí pro každého, kdo nasazuje AI systém s dopadem na osoby v EU.",
        gdpr: "Ano — platí pro každého, kdo zpracovává údaje osob v EU, bez ohledu na sídlo.",
    },
    {
        num: 9,
        title: "Povinnost oznámení",
        aiAct: "Hlášení incidentů u vysokorizikových systémů. Registrace v EU databázi pro Přílohu III.",
        gdpr: "Oznámení porušení zabezpečení (data breach) do 72 hodin dozorovému orgánu.",
    },
    {
        num: 10,
        title: "Průnik & překryv",
        aiAct: "AI Act nenahrazuje GDPR. Pokud AI systém zpracovává osobní údaje, platí OBĚ regulace současně.",
        gdpr: "GDPR již nyní pokrývá automatizované rozhodování (čl. 22), ale AI Act jde dále.",
    },
];

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Blog", href: "/blog" },
                { label: "AI Act vs GDPR" },
            ]}
            title="AI Act vs GDPR:"
            titleAccent="10 klíčových rozdílů"
            subtitle="1. března 2026 • 10 min čtení"
        >
            {/* Úvod */}
            <section>
                <p className="text-lg text-slate-300">
                    &ldquo;Je AI Act jako GDPR pro umělou inteligenci?&rdquo; Tuto otázku slyšíme nejčastěji.
                    Odpověď je: <strong className="text-white">ano i ne</strong>. Obě regulace chrání občany EU,
                    ale přistupují k tomu zásadně odlišně. Navíc se <strong className="text-white">vzájemně doplňují</strong> —
                    pokud vaše AI zpracovává osobní údaje, musíte plnit obě.
                </p>
            </section>

            {/* 10 rozdílů */}
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">10 rozdílů v přehledu</h2>
                <div className="space-y-4">
                    {differences.map((d) => (
                        <div key={d.num} className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-5">
                            <div className="flex items-center gap-3 mb-3">
                                <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-fuchsia-500/10 text-fuchsia-400 font-bold text-sm">
                                    {d.num}
                                </span>
                                <h3 className="text-base font-semibold text-white">{d.title}</h3>
                            </div>
                            <div className="grid sm:grid-cols-2 gap-3">
                                <div className="rounded-lg border border-fuchsia-500/15 bg-fuchsia-500/5 p-3">
                                    <span className="text-xs font-bold text-fuchsia-400 uppercase tracking-wider">AI Act</span>
                                    <p className="text-sm text-slate-300 mt-1">{d.aiAct}</p>
                                </div>
                                <div className="rounded-lg border border-cyan-500/15 bg-cyan-500/5 p-3">
                                    <span className="text-xs font-bold text-cyan-400 uppercase tracking-wider">GDPR</span>
                                    <p className="text-sm text-slate-300 mt-1">{d.gdpr}</p>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            <BlogCta
                heading="Splňte AI Act i GDPR najednou"
                text="Náš sken odhalí povinnosti dle obou regulací. Za 60 sekund, bez registrace."
                buttonText="Skenovat web ZDARMA"
            />

            {/* Klíčový poznatek */}
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Klíčový poznatek: obě regulace platí současně</h2>
                <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-5">
                    <p className="text-slate-300">
                        Pokud provozujete chatbot, který sbírá osobní údaje návštěvníků, musíte splnit:
                    </p>
                    <ul className="mt-3 space-y-2 text-sm text-slate-300">
                        <li className="flex items-start gap-2">
                            <span className="flex-shrink-0 mt-0.5 text-fuchsia-400 font-bold">AI Act:</span>
                            Označit chatbot jako AI, mít transparenční stránku, vést dokumentaci
                        </li>
                        <li className="flex items-start gap-2">
                            <span className="flex-shrink-0 mt-0.5 text-cyan-400 font-bold">GDPR:</span>
                            Získat souhlas se zpracováním údajů, informovat o účelu, umožnit výmaz
                        </li>
                    </ul>
                    <p className="mt-3 text-sm text-slate-400">
                        Více o povinnostech pro vaši firmu: <Link href="/blog/ai-act-co-musi-splnit-ceske-firmy" className="text-fuchsia-400 hover:text-fuchsia-300">AI Act a české firmy</Link>
                    </p>
                </div>
            </section>

            {/* Praktický dopad */}
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Co to znamená pro vaši firmu?</h2>
                <div className="rounded-2xl border border-fuchsia-500/20 bg-fuchsia-500/5 p-6">
                    <ol className="list-decimal pl-6 space-y-2 text-slate-300">
                        <li><strong className="text-white">Nemůžete ignorovat ani jednu regulaci</strong> — pokuty za AI Act jsou dokonce vyšší než za GDPR (<Link href="/blog/ai-act-pokuty-az-35-milionu-eur" className="text-fuchsia-400 hover:text-fuchsia-300">až 35 mil. EUR</Link>)</li>
                        <li><strong className="text-white">GDPR dodržujete? Dobrý základ.</strong> Procesy pro dokumentaci a risk assessment můžete rozšířit i na AI Act</li>
                        <li><strong className="text-white">DPO + AI Officer</strong> — zvažte, zda potřebujete osobu odpovědnou za AI compliance</li>
                        <li><strong className="text-white">Audit AI systémů</strong> — zmapujte, kde všude ve firmě používáte AI (<Link href="/scan" className="text-fuchsia-400 hover:text-fuchsia-300">náš sken vám pomůže</Link>)</li>
                        <li><strong className="text-white">Jeden compliance kit pro obě regulace</strong> — <Link href="/pricing" className="text-fuchsia-400 hover:text-fuchsia-300">náš balíček</Link> pokrývá povinnosti AI Actu a doplňuje GDPR dokumentaci</li>
                    </ol>
                </div>
            </section>

            {/* FAQ */}
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Časté dotazy</h2>
                <div className="space-y-4">
                    {[
                        { q: "Nahrazuje AI Act nařízení GDPR?", a: "Ne. AI Act a GDPR jsou různé regulace, které platí současně. AI Act reguluje umělou inteligenci, GDPR osobní údaje." },
                        { q: "Musím plnit obě regulace najednou?", a: "Pokud váš AI systém zpracovává osobní údaje (chatbot, doporučovací systém, personalizace), ano — musíte plnit obě." },
                        { q: "Která regulace má vyšší pokuty?", a: "AI Act. Maximální pokuta je 35 mil. EUR / 7 % obratu, oproti 20 mil. EUR / 4 % u GDPR." },
                        { q: "Mám GDPR v pořádku — kolik práce navíc je AI Act?", a: "Záleží na rizikovosti vašich AI systémů. Pro většinu firem (omezené riziko) jde zejména o transparenční povinnosti a dokumentaci." },
                    ].map((faq) => (
                        <details key={faq.q} className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-4 group">
                            <summary className="cursor-pointer font-medium text-white flex items-center justify-between">
                                {faq.q}
                                <span className="text-slate-500 group-open:rotate-180 transition-transform">▼</span>
                            </summary>
                            <p className="mt-2 text-slate-400 text-sm">{faq.a}</p>
                        </details>
                    ))}
                </div>
            </section>

            {/* FAQ JsonLd */}
            <script
                type="application/ld+json"
                dangerouslySetInnerHTML={{
                    __html: JSON.stringify({
                        "@context": "https://schema.org",
                        "@type": "FAQPage",
                        mainEntity: [
                            { "@type": "Question", name: "Nahrazuje AI Act GDPR?", acceptedAnswer: { "@type": "Answer", text: "Ne. AI Act a GDPR platí současně. AI Act reguluje AI systémy, GDPR osobní údaje." } },
                            { "@type": "Question", name: "Která regulace má vyšší pokuty?", acceptedAnswer: { "@type": "Answer", text: "AI Act — až 35 mil. EUR / 7 % obratu oproti 20 mil. EUR / 4 % u GDPR." } },
                            { "@type": "Question", name: "Musím plnit AI Act i GDPR?", acceptedAnswer: { "@type": "Answer", text: "Pokud váš AI systém zpracovává osobní údaje, musíte plnit obě regulace současně." } },
                        ],
                    }),
                }}
            />
        </ContentPage>
    );
}
