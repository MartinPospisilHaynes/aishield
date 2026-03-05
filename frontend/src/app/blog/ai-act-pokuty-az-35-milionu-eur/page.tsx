import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import BlogCta from "@/components/blog-cta";
import Link from "next/link";

export const metadata: Metadata = {
    title: "AI Act pokuty — až 35 milionů EUR. Kolik riskujete?",
    description:
        "Přehled pokut za porušení EU AI Actu. Až 35 mil. EUR nebo 7 % obratu. Zjistěte, co hrozí vaší firmě a jak se vyhnout sankci.",
    alternates: { canonical: "https://aishield.cz/blog/ai-act-pokuty-az-35-milionu-eur" },
    openGraph: {
        images: [{ url: "/blog/ai-act-pokuty-az-35-milionu-eur.png", width: 1200, height: 630 }],
    },
    keywords: [
        "AI Act pokuty",
        "EU AI Act sankce",
        "pokuta za AI",
        "AI Act Česko pokuty",
        "35 milionů EUR pokuta",
        "AI regulace sankce",
    ],
};

/* Struktury pokut dle AI Actu */
const fines = [
    {
        tier: "Nejvyšší pokuta",
        amount: "35 000 000 €",
        percent: "7 % celosvětového obratu",
        color: "red",
        violations: [
            "Nasazení zakázaných AI praktik (čl. 5)",
            "Sociální scoring občanů",
            "Biometrická identifikace v reálném čase (mimo povolené výjimky)",
            "Manipulativní techniky využívající zranitelnosti osob",
            "Prediktivní policejní profilování",
        ],
    },
    {
        tier: "Střední pokuta",
        amount: "15 000 000 €",
        percent: "3 % celosvětového obratu",
        color: "amber",
        violations: [
            "Nesplnění povinností pro vysokorizikové AI systémy (Příloha III)",
            "Chybějící posouzení shody (conformity assessment)",
            "Nedostatečný systém řízení rizik",
            "Porušení požadavků na data a datovou governance",
            "Chybějící technická dokumentace",
        ],
    },
    {
        tier: "Nižší pokuta",
        amount: "7 500 000 €",
        percent: "1 % celosvětového obratu",
        color: "cyan",
        violations: [
            "Nesplnění transparenčních povinností (čl. 50)",
            "Chatbot bez označení jako AI",
            "AI generovaný obsah bez označení",
            "Chybějící transparenční stránka",
            "Neposkytnutí informací dozorovým orgánům",
        ],
    },
];

const colorMap: Record<string, { border: string; bg: string; text: string; dot: string }> = {
    red: { border: "border-red-500/20", bg: "bg-red-500/5", text: "text-red-400", dot: "bg-red-500" },
    amber: { border: "border-amber-500/20", bg: "bg-amber-500/5", text: "text-amber-400", dot: "bg-amber-500" },
    cyan: { border: "border-cyan-500/20", bg: "bg-cyan-500/5", text: "text-cyan-400", dot: "bg-cyan-500" },
};

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Blog", href: "/blog" },
                { label: "AI Act pokuty" },
            ]}
            title="AI Act pokuty:"
            titleAccent="až 35 milionů EUR"
            subtitle="1. března 2026 • 8 min čtení"
        >
            {/* Úvod */}
            <section>
                <p className="text-lg text-slate-300">
                    EU AI Act přináší jedny z <strong className="text-white">nejvyšších pokut v historii evropské regulace</strong>.
                    Maximální sankce dosahuje 35 milionů EUR nebo 7 % celosvětového ročního obratu — podle toho,
                    co je vyšší. Pro srovnání: GDPR umožňuje &ldquo;jen&rdquo; 20 milionů EUR nebo 4 % obratu.
                </p>
            </section>

            {/* 3 úrovně pokut */}
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">3 úrovně pokut v AI Actu</h2>
                <div className="space-y-6">
                    {fines.map((f) => {
                        const c = colorMap[f.color];
                        return (
                            <div key={f.tier} className={`rounded-xl border ${c.border} ${c.bg} p-5`}>
                                <div className="flex flex-col sm:flex-row sm:items-center gap-2 mb-3">
                                    <span className={`inline-flex items-center gap-2 text-lg font-bold ${c.text}`}>
                                        <span className={`w-3 h-3 rounded-full ${c.dot}`} />
                                        {f.tier}
                                    </span>
                                    <span className="text-sm text-slate-400 sm:ml-auto">
                                        až <strong className="text-white">{f.amount}</strong> nebo <strong className="text-white">{f.percent}</strong>
                                    </span>
                                </div>
                                <p className="text-sm text-slate-400 mb-2">Za co hrozí:</p>
                                <ul className="space-y-1.5">
                                    {f.violations.map((v) => (
                                        <li key={v} className="flex items-start gap-2 text-sm text-slate-300">
                                            <span className={`flex-shrink-0 mt-1 w-1.5 h-1.5 rounded-full ${c.dot}`} />
                                            {v}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        );
                    })}
                </div>
            </section>

            {/* Kdo pokutuje */}
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Kdo v Česku pokutuje?</h2>
                <p>
                    Každý členský stát EU musí ustanovit <strong className="text-white">národní dozorový orgán</strong> (National Competent Authority).
                    V ČR to bude pravděpodobně NÚKIB, ČTÚ nebo ÚOOÚ — definitivní rozhodnutí se očekává v průběhu roku 2026.
                </p>
                <p>
                    Dozorový orgán bude mít pravomoc provádět audity, vyžadovat dokumentaci a ukládat sankce.
                    Pro <Link href="/blog/vysoko-rizikove-ai-systemy-priloha-iii" className="text-fuchsia-400 hover:text-fuchsia-300">vysoce rizikové systémy</Link> bude
                    vyžadovat i posouzení shody třetí stranou.
                </p>
            </section>

            {/* Praktické příklady */}
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Kolik riskuje typická česká firma?</h2>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-white/10">
                                <th className="text-left py-2 text-slate-400 font-medium">Typ firmy</th>
                                <th className="text-left py-2 text-slate-400 font-medium">Obrat</th>
                                <th className="text-left py-2 text-slate-400 font-medium">Transparence (1 %)</th>
                                <th className="text-left py-2 text-slate-400 font-medium">Vysoké riziko (3 %)</th>
                            </tr>
                        </thead>
                        <tbody className="text-slate-300">
                            <tr className="border-b border-white/5">
                                <td className="py-2">E-shop (malý)</td>
                                <td>10 mil. Kč</td>
                                <td className="text-cyan-400">100 000 Kč</td>
                                <td className="text-amber-400">300 000 Kč</td>
                            </tr>
                            <tr className="border-b border-white/5">
                                <td className="py-2">SaaS startup</td>
                                <td>50 mil. Kč</td>
                                <td className="text-cyan-400">500 000 Kč</td>
                                <td className="text-amber-400">1 500 000 Kč</td>
                            </tr>
                            <tr className="border-b border-white/5">
                                <td className="py-2">Střední firma</td>
                                <td>500 mil. Kč</td>
                                <td className="text-cyan-400">5 000 000 Kč</td>
                                <td className="text-amber-400">15 000 000 Kč</td>
                            </tr>
                            <tr>
                                <td className="py-2">Velká korporace</td>
                                <td>5 mld. Kč</td>
                                <td className="text-cyan-400">50 000 000 Kč</td>
                                <td className="text-amber-400">150 000 000 Kč</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <p className="mt-3 text-sm text-slate-400">
                    * Pokuty se počítají jako procento z celosvětového ročního obratu nebo pevná částka — platí vyšší z obou.
                    Pro MSP a startupy AI Act stanoví mírnější úpravu, ale stále jde o značné částky.
                </p>
            </section>

            {/* Přitěžující a polehčující okolnosti */}
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Co ovlivňuje výši pokuty?</h2>
                <div className="grid sm:grid-cols-2 gap-4">
                    <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4">
                        <h3 className="text-sm font-bold text-red-400 mb-2">Přitěžující okolnosti</h3>
                        <ul className="space-y-1 text-sm text-slate-300">
                            <li>• Opakované porušení</li>
                            <li>• Úmyslné jednání</li>
                            <li>• Neposkytnutí součinnosti dozoru</li>
                            <li>• Zatajení porušení</li>
                            <li>• Počet dotčených osob</li>
                        </ul>
                    </div>
                    <div className="rounded-xl border border-green-500/20 bg-green-500/5 p-4">
                        <h3 className="text-sm font-bold text-green-400 mb-2">Polehčující okolnosti</h3>
                        <ul className="space-y-1 text-sm text-slate-300">
                            <li>• Dobrovolná náprava</li>
                            <li>• Spolupráce s dozorovým orgánem</li>
                            <li>• Nahlášení porušení z vlastní iniciativy</li>
                            <li>• Zavedení compliance programu</li>
                            <li>• Malá velikost podniku (MSP)</li>
                        </ul>
                    </div>
                </div>
            </section>

            {/* Srovnání s GDPR */}
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">AI Act vs GDPR — pokuty</h2>
                <div className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-5">
                    <div className="grid grid-cols-3 gap-4 text-center text-sm">
                        <div />
                        <div className="font-bold text-fuchsia-400">AI Act</div>
                        <div className="font-bold text-cyan-400">GDPR</div>

                        <div className="text-left text-slate-400">Max. pokuta</div>
                        <div className="text-white font-mono">35 mil. €</div>
                        <div className="text-white font-mono">20 mil. €</div>

                        <div className="text-left text-slate-400">Max. % obratu</div>
                        <div className="text-white font-mono">7 %</div>
                        <div className="text-white font-mono">4 %</div>

                        <div className="text-left text-slate-400">Účinnost</div>
                        <div className="text-white">srpen 2026</div>
                        <div className="text-white">květen 2018</div>
                    </div>
                </div>
                <p className="mt-3 text-sm text-slate-400">
                    AI Act je o <strong className="text-white">75 % přísnější</strong> než GDPR co do maximální výše pokut.
                    Přečtěte si kompletní <Link href="/blog/ai-act-vs-gdpr-rozdily" className="text-fuchsia-400 hover:text-fuchsia-300">srovnání AI Act vs GDPR</Link>.
                </p>
            </section>

            {/* Jak se vyhnout */}
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Jak se pokutám vyhnout?</h2>
                <div className="rounded-2xl border border-fuchsia-500/20 bg-fuchsia-500/5 p-6">
                    <ol className="list-decimal pl-6 space-y-2 text-slate-300">
                        <li><Link href="/scan" className="text-fuchsia-400 hover:text-fuchsia-300">Skenujte svůj web</Link> — zjistěte, jaké AI systémy používáte a jaká je jejich riziková kategorie</li>
                        <li>Implementujte <Link href="/blog/co-je-transparencni-stranka" className="text-fuchsia-400 hover:text-fuchsia-300">transparenční stránku</Link> — povinnost dle čl. 50 pro všechny AI systémy</li>
                        <li>Vypracujte interní AI politiku a dokumentaci — <Link href="/pricing" className="text-fuchsia-400 hover:text-fuchsia-300">náš Compliance Kit</Link> za vás vygeneruje až 12 dokumentů</li>
                        <li>Nastavte pravidelný monitoring — legislativa se stále vyvíjí</li>
                        <li>Proškolte zaměstnance — AI gramotnost (čl. 4) je povinná od února 2025</li>
                    </ol>
                </div>
            </section>

            <BlogCta
                heading="Nechcete riskovat pokutu?"
                text="Bezplatný sken za 60 sekund ukáže, jaká rizika najdete na vašem webu. Bez registrace."
                buttonText="Skenovat web ZDARMA"
            />

            {/* FAQ schema */}
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Časté dotazy</h2>
                <div className="space-y-4">
                    {[
                        { q: "Kolik je maximální pokuta za porušení AI Actu?", a: "Až 35 milionů EUR nebo 7 % celosvětového ročního obratu — podle toho, co je vyšší." },
                        { q: "Platí pokuty i pro malé firmy a živnostníky?", a: "Ano, AI Act se vztahuje na všechny, kdo nasazují nebo provozují AI systémy v EU. Pro MSP jsou ale stanoveny mírnější podmínky." },
                        { q: "Od kdy se pokuty budou udělovat?", a: "Zákaz nepřijatelných praktik platí od února 2025. Plné vymáhání včetně transparenčních povinností od srpna 2026." },
                        { q: "Kdo v Česku bude pokuty udělovat?", a: "Národní dozorový orgán — pravděpodobně NÚKIB, ČTÚ nebo ÚOOÚ. Definitivní rozhodnutí se očekává v roce 2026." },
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
                            { "@type": "Question", name: "Kolik je maximální pokuta za porušení AI Actu?", acceptedAnswer: { "@type": "Answer", text: "Až 35 milionů EUR nebo 7 % celosvětového ročního obratu." } },
                            { "@type": "Question", name: "Platí pokuty i pro malé firmy?", acceptedAnswer: { "@type": "Answer", text: "Ano, AI Act se vztahuje na všechny, ale pro MSP jsou mírnější podmínky." } },
                            { "@type": "Question", name: "Od kdy se pokuty budou udělovat?", acceptedAnswer: { "@type": "Answer", text: "Plné vymáhání od srpna 2026. Zákaz nepřijatelných praktik platí od února 2025." } },
                        ],
                    }),
                }}
            />
        </ContentPage>
    );
}
