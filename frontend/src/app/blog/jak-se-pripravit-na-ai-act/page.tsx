import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import BlogCta from "@/components/blog-cta";
import Link from "next/link";

export const metadata: Metadata = {
    title: "Jak se připravit na AI Act — 10 kroků pro vaši firmu",
    description:
        "Praktický návod na přípravu na EU AI Act v 10 krocích. Od auditu AI systémů přes dokumentaci po školení zaměstnanců.",
    alternates: { canonical: "https://aishield.cz/blog/jak-se-pripravit-na-ai-act" },
    openGraph: {
        images: [{ url: "/blog/jak-se-pripravit-na-ai-act.png", width: 1200, height: 630 }],
    },
    keywords: [
        "příprava na AI Act",
        "jak splnit AI Act",
        "AI Act kroky",
        "AI Act compliance návod",
        "AI Act postup",
        "AI Act pro firmy",
    ],
};

const steps = [
    {
        num: 1,
        title: "Zmapujte AI systémy ve firmě",
        desc: "Prvním krokem je zjistit, kde všude ve vaší firmě se AI používá. Nejde jen o chatboty — AI může být v CRM, e-mailovém marketingu, HR nástrojích, účetnictví nebo i v analytice webu.",
        action: "Vytvořte seznam všech nástrojů a služeb, které vaše firma používá, a u každého zjistěte, zda využívá AI/ML.",
        tip: "Náš bezplatný sken za 60 sekund odhalí AI systémy na vašem webu automaticky.",
        href: "/scan",
    },
    {
        num: 2,
        title: "Určete rizikovou kategorii",
        desc: "AI Act rozlišuje 4 úrovně rizika: nepřijatelné (zakázané), vysoké (Příloha III), omezené (čl. 50) a minimální. Vaše povinnosti závisí na tom, do které kategorie vaše AI spadá.",
        action: "Pro každý AI systém ze seznamu určete rizikovou kategorii podle definic v nařízení.",
        tip: "Většina webů a e-shopů spadá do kategorie omezeného rizika (chatboty, doporučovací systémy).",
    },
    {
        num: 3,
        title: "Zkontrolujte, zda nepoužíváte zakázanou AI",
        desc: "Od února 2025 jsou některé AI praktiky zakázané: sociální scoring, manipulativní techniky cílené na zranitelné skupiny, biometrická identifikace v reálném čase (s výjimkami) a prediktivní profilování.",
        action: "Projděte článek 5 AI Actu a ověřte, že žádný váš systém nespadá do zakázané kategorie.",
        tip: "Za zakázané praktiky hrozí nejvyšší pokuta: až 35 mil. EUR.",
        href: "/blog/ai-act-pokuty-az-35-milionu-eur",
    },
    {
        num: 4,
        title: "Zaveďte transparenční povinnosti",
        desc: "Článek 50 vyžaduje, aby uživatelé věděli, že komunikují s AI. To znamená: označení chatbotů, transparenční stránku na webu a označení AI-generovaného obsahu.",
        action: "Přidejte na web transparenční stránku, označte chatboty a AI generovaný obsah.",
        tip: "Transparenční stránku vám vygenerujeme automaticky v rámci Compliance Kitu.",
        href: "/blog/co-je-transparencni-stranka",
    },
    {
        num: 5,
        title: "Vypracujte technickou dokumentaci",
        desc: "Pro omezené i vysoké riziko potřebujete dokumentaci: popis AI systému, účel použití, riziková kategorie, opatření, odpovědné osoby a záznamy o rozhodnutích.",
        action: "Vytvořte strukturovanou dokumentaci pro každý AI systém. Obsahuje: účel, kategorie rizik, ovládací opatření, audit trail.",
    },
    {
        num: 6,
        title: "Nastavte interní AI politiku",
        desc: "Interní pravidla pro používání AI ve firmě — kdo smí nasadit nový AI nástroj, jaký je schvalovací proces, kdo nese odpovědnost.",
        action: "Sepište AI politiku s jasnými pravidly pro nákup, nasazení a provoz AI nástrojů.",
        tip: "Interní AI politiku generujeme jako součást BASIC balíčku.",
        href: "/pricing",
    },
    {
        num: 7,
        title: "Proškolte zaměstnance (AI gramotnost)",
        desc: "Článek 4 AI Actu vyžaduje od února 2025 zajistit AI gramotnost zaměstnanců, kteří s AI pracují. Nestačí jednorázový e-mail — potřebujete prokazatelné školení.",
        action: "Připravte školící materiály a proveďte školení s podpisovým archem (záznamový list).",
        tip: "V našem Compliance Kitu najdete prezentaci v PowerPointu i záznamový list.",
    },
    {
        num: 8,
        title: "Určete odpovědnou osobu",
        desc: "Stejně jako GDPR má DPO, AI Act vyžaduje, aby někdo byl odpovědný za AI compliance. U menších firem to může být existující DPO, CTO nebo compliance officer.",
        action: "Jmenujte osobu odpovědnou za AI compliance — zajistí dokumentaci, školení a komunikaci s dozorem.",
    },
    {
        num: 9,
        title: "Nastavte monitoring a revize",
        desc: "AI Act nen\u00ed jednor\u00e1zov\u00fd checkbox. Legislativa se vyv\u00edj\u00ed, va\u0161e AI syst\u00e9my se m\u011bn\u00ed. Pot\u0159ebujete pravideln\u00fd p\u0159ehled.",
        action: "Nastavte \u010dtvrtletn\u00ed revizi AI syst\u00e9m\u016f a dokumentace. Sledujte legislativn\u00ed v\u00fdvoj.",
        tip: "Náš ENTERPRISE balíček zahrnuje 2 roky automatického monitoringu.",
        href: "/pricing",
    },
    {
        num: 10,
        title: "Připravte se na dozorový audit",
        desc: "Dozorový orgán může kdykoliv vyžádat dokumentaci, provést audit nebo zažádat o vysvětlení. Mějte vše připravené.",
        action: "Soustřeďte dokumentaci na jedno místo, otestujte, že ji najdete do 24 hodin. Mějte připravený kontaktní postup.",
        tip: "Tištěná dokumentace v profesionální vazbě — připravená na kontrolu. Součást BASIC, PRO i ENTERPRISE.",
    },
];

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Blog", href: "/blog" },
                { label: "10 kroků přípravy" },
            ]}
            title="Jak se připravit na AI Act:"
            titleAccent="10 kroků"
            subtitle="1. března 2026 • 12 min čtení"
        >
            {/* Úvod */}
            <section>
                <p className="text-lg text-slate-300">
                    EU AI Act je realita. Nejde o otázku &ldquo;jestli&rdquo;, ale <strong className="text-white">&ldquo;kdy&rdquo;</strong>.
                    Transparenční povinnosti dle článku 50 platí od srpna 2026, vysokorizikové systémy od srpna 2027.
                    Připravit se včas je levnější než řešit pokuty zpětně.
                </p>
                <p className="text-slate-400 mt-2">
                    Zde je praktický 10bodový postup, jak se na AI Act připravit krok za krokem.
                </p>
            </section>

            {/* Progress overview */}
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Přehled kroků</h2>
                <div className="grid sm:grid-cols-2 gap-3">
                    {steps.map((s) => (
                        <div key={s.num} className="flex items-center gap-3 rounded-lg border border-white/[0.06] bg-white/[0.02] p-3">
                            <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-fuchsia-500/10 text-fuchsia-400 font-bold text-sm flex-shrink-0">
                                {s.num}
                            </span>
                            <span className="text-sm text-slate-300">{s.title}</span>
                        </div>
                    ))}
                </div>
            </section>

            {/* 10 kroků detailně */}
            {steps.map((s) => (
                <section key={s.num}>
                    <div className="flex items-center gap-3 mb-3">
                        <span className="flex items-center justify-center w-10 h-10 rounded-xl bg-fuchsia-500/10 text-fuchsia-400 font-bold">
                            {s.num}
                        </span>
                        <h2 className="text-xl font-semibold text-white">{s.title}</h2>
                    </div>
                    <p className="text-slate-300">{s.desc}</p>
                    <div className="mt-3 rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-4">
                        <p className="text-sm text-cyan-400 font-medium mb-1">Co udělat:</p>
                        <p className="text-sm text-slate-300">{s.action}</p>
                    </div>
                    {s.tip && (
                        <div className="mt-2 rounded-xl border border-fuchsia-500/15 bg-fuchsia-500/5 p-3">
                            <p className="text-sm text-slate-400">
                                💡 <strong className="text-fuchsia-400">Tip:</strong>{" "}
                                {s.href ? (
                                    <>
                                        <Link href={s.href} className="text-fuchsia-400 hover:text-fuchsia-300">{s.tip}</Link>
                                    </>
                                ) : (
                                    s.tip
                                )}
                            </p>
                        </div>
                    )}
                </section>
            ))}

            <BlogCta
                heading="Začněte krokem č. 1 — bezplatný sken"
                text="Zmapujte AI systémy na vašem webu za 60 sekund. Bez registrace, bez závazků."
                buttonText="Skenovat web ZDARMA"
            />

            {/* Shrnutí */}
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Shrnutí: na co nezapomenout</h2>
                <div className="rounded-2xl border border-fuchsia-500/20 bg-fuchsia-500/5 p-6">
                    <ul className="space-y-2 text-slate-300">
                        <li className="flex items-start gap-2">
                            <span className="text-fuchsia-400 flex-shrink-0">✓</span>
                            <strong className="text-white">Únor 2025:</strong> Zakázané praktiky + AI gramotnost — už platí!
                        </li>
                        <li className="flex items-start gap-2">
                            <span className="text-fuchsia-400 flex-shrink-0">✓</span>
                            <strong className="text-white">Srpen 2026:</strong> Transparenční povinnosti (čl. 50) — označení AI, transparenční stránka
                        </li>
                        <li className="flex items-start gap-2">
                            <span className="text-fuchsia-400 flex-shrink-0">✓</span>
                            <strong className="text-white">Srpen 2027:</strong> Plné povinnosti pro vysokorizikové systémy (Příloha III)
                        </li>
                    </ul>
                    <p className="mt-4 text-sm text-slate-400">
                        Nenechávejte to na poslední chvíli. <Link href="/pricing" className="text-fuchsia-400 hover:text-fuchsia-300">Compliance Kit od 4 999 Kč</Link> vám
                        pokryje kroky 4-7 automaticky.
                    </p>
                </div>
            </section>

            {/* FAQ */}
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Časté dotazy</h2>
                <div className="space-y-4">
                    {[
                        { q: "Kolik času příprava na AI Act zabere?", a: "Záleží na velikosti firmy a počtu AI systémů. Pro malou firmu s chatbotem jde o dny, pro velkou korporaci s desítkami AI nástrojů o měsíce." },
                        { q: "Musím se připravit, i když používám jen ChatGPT?", a: "Pokud ChatGPT používáte interně, povinnosti jsou minimální. Pokud jeho výstupy prezentujete zákazníkům (chatbot, generovaný obsah), musíte to označit jako AI." },
                        { q: "Kolik příprava stojí?", a: "Náš Compliance Kit začíná na 4 999 Kč a pokrývá dokumentaci, transparenční stránku i školení. Individuální konzultace s právníkem může stát 10-50 tisíc Kč." },
                        { q: "Můžu si vše udělat sám?", a: "Ano, ale AI Act má 113 článků a 13 příloh. Automatizovaný nástroj vám ušetří desítky hodin a zajistí, že na nic nezapomenete." },
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
                            { "@type": "Question", name: "Kolik času příprava na AI Act zabere?", acceptedAnswer: { "@type": "Answer", text: "Pro malou firmu dny, pro velkou korporaci měsíce. Záleží na počtu AI systémů." } },
                            { "@type": "Question", name: "Musím se připravit i s ChatGPT?", acceptedAnswer: { "@type": "Answer", text: "Interní použití má minimální povinnosti. Pokud výstupy AI prezentujete zákazníkům, musíte to označit." } },
                            { "@type": "Question", name: "Kolik příprava stojí?", acceptedAnswer: { "@type": "Answer", text: "Compliance Kit od 4 999 Kč. Právník 10-50 tisíc Kč." } },
                        ],
                    }),
                }}
            />
        </ContentPage>
    );
}
