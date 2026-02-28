import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Časté otázky o AI Act compliance",
    description:
        "Odpovědi na nejčastější otázky o EU AI Act, povinnostech pro české firmy, " +
        "pokutách, deadlinu 2. srpna 2026 a službách AIshield.cz.",
    alternates: { canonical: "https://aishield.cz/faq" },
};

const FAQ_ITEMS = [
    {
        q: "Co je AI Act a proč se mě týká?",
        a: "AI Act (Nařízení EU 2024/1689) je první zákon na světě, který komplexně reguluje umělou inteligenci. Platí pro každého, kdo v EU provozuje nebo nasazuje AI systémy — bez ohledu na velikost firmy. Chatbot, Google Analytics, doporučovací systém produktů, reklamní pixel — to vše jsou AI systémy ve smyslu zákona.",
    },
    {
        q: "Jaké pokuty hrozí za porušení AI Act?",
        a: "Až 35 milionů EUR nebo 7 % obratu za zakázané AI praktiky. Až 15 mil. EUR nebo 3 % za chybějící dokumentaci a neoznačený chatbot. Až 7,5 mil. EUR za nepravdivé informace. Pokuty se počítají za každé porušení zvlášť — 3 neoznačené AI systémy = 3 sankce.",
    },
    {
        q: "Týká se AI Act malých firem a e-shopů?",
        a: "Ano. Zákon platí pro všechny, kdo v EU provozují AI systémy. Používáte Smartsupp chatbot? Google Analytics? Doporučování produktů na Shoptetu? To vše jsou AI systémy. Pro malé firmy platí nižší stropy pokut, ale povinnost transparence (čl. 50) zůstává.",
    },
    {
        q: "Co když nevím, jestli mám AI na webu?",
        a: "To je naprosto normální — většina firem netuší, jaké AI nástroje na jejich webu běží. Právě proto nabízíme bezplatný sken. Zadáte URL a za minutu dostanete kompletní přehled. Žádná registrace, žádné platební údaje.",
    },
    {
        q: "Jak AIshield scanner funguje?",
        a: "Scanner automaticky prochází web pomocí 24 nezávislých skenů z 8 zemí (desktop + mobil). Detekuje chatboty, analytiku, ML modely, cookies a JavaScriptové knihovny. Základní sken trvá 60 sekund. Hloubkový audit (24h) opakuje sken v různých denních dobách pro zachycení dynamicky načítaných nástrojů.",
    },
    {
        q: "Jaký je deadline pro splnění AI Act?",
        a: "Klíčové datum je 2. srpen 2026 — plná účinnost AI Actu. Ale pozor: zákaz nepřijatelných AI praktik (čl. 5) platí od února 2025. Povinnost AI gramotnosti zaměstnanců (čl. 4) platí rovněž od února 2025. Příprava dokumentace zabere 2–4 týdny.",
    },
    {
        q: "Co je transparenční stránka?",
        a: "Transparenční stránka je HTML dokument, který musíte umístit na web, abyste informovali uživatele o používání AI systémů. Vyžaduje ji článek 50 AI Actu. AIshield ji generuje automaticky se všemi požadovanými informacemi — stačí ji vložit do patičky webu.",
    },
    {
        q: "Nahradíte advokáta?",
        a: "Ne — jsme technický nástroj, ne právní poradna. Automaticky identifikujeme AI systémy, připravíme dokumentaci, vygenerujeme transparenční stránku a interní AI politiku. Pro většinu malých firem to stačí. Pokud máte high-risk AI nebo specifickou situaci, doporučujeme dokumenty konzultovat s právníkem.",
    },
    {
        q: "Je skenování webu opravdu zdarma?",
        a: "Ano, zcela zdarma, nezávazné a bez skrytých podmínek. Nemusíte se registrovat ani zadávat platební údaje. Sken si můžete spustit opakovaně. Platíte pouze za compliance dokumenty, pokud se rozhodnete je objednat.",
    },
    {
        q: "Jak se liší BASIC, PRO a ENTERPRISE balíček?",
        a: "BASIC pokrývá základní povinnosti (transparenční stránka, registr AI). PRO přidává kompletní dokumentaci včetně risk assessmentu a interní AI politiky. ENTERPRISE zahrnuje konzultaci, právní revizi a white-label řešení pro agentury. Podrobnosti na stránce Ceník.",
    },
];

export default function FAQPage() {
    return (
        <section className="py-20 sm:py-28">
            <div className="mx-auto max-w-3xl px-4 sm:px-6">
                {/* Headline */}
                <div className="text-center mb-16">
                    <h1 className="text-4xl font-extrabold sm:text-5xl mb-4">
                        Časté <span className="neon-text">otázky</span>
                    </h1>
                    <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                        Odpovědi na nejčastější dotazy o EU AI Act, povinnostech pro české firmy
                        a službách AIshield.cz.
                    </p>
                </div>

                {/* FAQ Items */}
                <div className="space-y-6">
                    {FAQ_ITEMS.map((item, i) => (
                        <details
                            key={i}
                            className="group rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden"
                        >
                            <summary className="flex cursor-pointer items-center justify-between px-6 py-5 text-left font-semibold text-slate-100 hover:bg-white/[0.03] transition-colors">
                                <span className="pr-4">{item.q}</span>
                                <svg
                                    className="w-5 h-5 flex-shrink-0 text-fuchsia-400 transition-transform group-open:rotate-45"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                    strokeWidth={2}
                                >
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                                </svg>
                            </summary>
                            <div className="px-6 pb-5 text-slate-400 leading-relaxed">
                                {item.a}
                            </div>
                        </details>
                    ))}
                </div>

                {/* CTA */}
                <div className="mt-16 text-center">
                    <p className="text-slate-400 mb-6">Nenašli jste odpověď?</p>
                    <div className="flex flex-col sm:flex-row gap-4 justify-center">
                        <a
                            href="/scan"
                            className="btn-primary cta-pulse text-base px-8 py-3.5 inline-flex items-center justify-center gap-2"
                        >
                            Skenovat web ZDARMA
                        </a>
                        <a
                            href="mailto:info@aishield.cz"
                            className="rounded-xl border border-white/[0.1] bg-white/[0.03] px-8 py-3.5 text-base font-medium text-slate-200 hover:bg-white/[0.06] transition-colors inline-flex items-center justify-center gap-2"
                        >
                            Napsat nám
                        </a>
                    </div>
                </div>
            </div>
        </section>
    );
}
