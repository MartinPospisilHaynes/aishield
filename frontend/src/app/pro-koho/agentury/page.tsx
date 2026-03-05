import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "AI Act pro webové a digitální agentury — AIshield.cz",
    description:
        "Jako agentura nasazujete AI nástroje klientům — chatboty, AI analytiku, personalizaci. " +
        "AI Act se týká i vás jako deployera. Zjistěte, co musí agentury splnit.",
    alternates: { canonical: "/pro-koho/agentury" },
};

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Pro koho", href: "/pro-koho" },
                { label: "Agentury" },
            ]}
            title="AI Act pro webové a digitální agentury"
            titleAccent="— deployer povinnosti"
            subtitle="Nasazujete chatboty, AI analytiku nebo personalizaci klientům? Podle AI Act jste deployer a máte specifické povinnosti."
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Proč se AI Act týká agentur</h2>
                <div className="space-y-4 text-slate-300">
                    <p>
                        EU AI Act rozlišuje tři hlavní role: <strong className="text-white">provider</strong> (tvůrce AI),
                        <strong className="text-white"> deployer</strong> (kdo AI nasazuje) a <strong className="text-white">uživatel</strong>.
                        Jako agentura, která implementuje Smartsupp chatbot, Google Analytics 4, Meta Pixel nebo OpenAI
                        API do webů klientů, jste v roli <strong className="text-white">deployer</strong>.
                    </p>
                    <p>
                        To znamená, že máte povinnosti podle článků 26 a 50 AI Act — především zajistit transparenci
                        a informovat koncové uživatele o tom, že interagují s AI systémem.
                    </p>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Typické AI systémy v agenturní praxi</h2>
                <div className="grid gap-4 sm:grid-cols-2">
                    {[
                        { name: "Smartsupp / Tidio chatbot", risk: "Minimální riziko", duty: "Transparenční povinnost (čl. 50)" },
                        { name: "Google Analytics 4", risk: "Minimální riziko", duty: "AI-powered insights = transparence" },
                        { name: "Meta Pixel + Conversions API", risk: "Minimální riziko", duty: "AI targeting = transparence" },
                        { name: "OpenAI API integrace", risk: "Záleží na použití", duty: "Transparence + možná vyšší riziko" },
                        { name: "AI doporučování produktů", risk: "Minimální riziko", duty: "Transparenční povinnost" },
                        { name: "AI copywriting (Jasper, Copy.ai)", risk: "Minimální riziko", duty: "Označení AI-generovaného obsahu" },
                    ].map((item) => (
                        <div key={item.name} className="rounded-lg border border-slate-700/50 bg-slate-800/30 p-4">
                            <h3 className="font-semibold text-white">{item.name}</h3>
                            <p className="text-xs text-cyan-400 mt-1">{item.risk}</p>
                            <p className="text-sm text-slate-400 mt-1">{item.duty}</p>
                        </div>
                    ))}
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Co musí agentury udělat</h2>
                <ol className="space-y-4">
                    {[
                        { step: "1", title: "Audit AI systémů", desc: "Projděte všechny klienty a identifikujte, kde jste nasadili AI. AIshield to umí automaticky." },
                        { step: "2", title: "Transparenční stránka", desc: "Každý klientský web potřebuje transparenční stránku s registrem AI systémů." },
                        { step: "3", title: "Risk assessment", desc: "Pro každý AI systém vyhodnoťte rizikovou kategorii podle AI Act přílohy III." },
                        { step: "4", title: "Smlouvy s klienty", desc: "Aktualizujte smlouvy — kdo nese odpovědnost za compliance (agentura vs. klient)." },
                        { step: "5", title: "Školení týmu", desc: "Váš tým musí rozumět AI Act minimálně na úrovni deployer povinností." },
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
                <h2 className="text-xl font-semibold text-white mb-4">AIshield pro agentury — hromadný sken</h2>
                <div className="space-y-4 text-slate-300">
                    <p>
                        S balíčkem <strong className="text-white">ENTERPRISE</strong> můžete skenovat weby všech
                        vašich klientů najednou. Automaticky identifikujeme AI systémy, vygenerujeme dokumentaci
                        a transparenční stránky — vy dodáte compliance jako službu.
                    </p>
                    <p>
                        <strong className="text-white">AI Act compliance jako nová služba.</strong> Nabídněte klientům
                        compliance balíček a vytvořte si nový revenue stream.
                    </p>
                </div>
            </section>

            <section>
                <div className="rounded-xl border border-fuchsia-500/30 bg-gradient-to-r from-fuchsia-900/20 to-cyan-900/20 p-8 text-center">
                    <h2 className="text-2xl font-bold text-white mb-3">
                        Vyzkoušejte sken na webu vašeho klienta
                    </h2>
                    <p className="text-slate-400 mb-6 max-w-lg mx-auto">
                        Bezplatný sken za 60 sekund — ukažte klientovi, jaké AI systémy má a co musí řešit.
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
                            Enterprise pro agentury
                        </Link>
                    </div>
                </div>
            </section>
        </ContentPage>
    );
}
