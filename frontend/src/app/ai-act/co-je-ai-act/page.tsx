import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "Co je AI Act — první zákon o umělé inteligenci na světě",
    description:
        "AI Act (Nařízení EU 2024/1689) je první komplexní právní rámec pro umělou inteligenci. " +
        "Zjistěte, proč vznikl, koho se týká a jaké jsou klíčové deadliny.",
    alternates: { canonical: "https://aishield.cz/ai-act/co-je-ai-act" },
};

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "AI Act", href: "/ai-act" },
                { label: "Co je AI Act" },
            ]}
            title="Co je"
            titleAccent="AI Act?"
            subtitle="Nařízení EU 2024/1689 — první komplexní zákon o umělé inteligenci na světě."
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Proč AI Act vznikl?</h2>
                <p>
                    Evropská unie přijala <strong className="text-white">AI Act</strong> (oficiálně
                    Nařízení (EU) 2024/1689) jako odpověď na rychlý rozvoj umělé inteligence.
                    Cílem je zajistit, aby AI systémy v EU byly <strong className="text-white">bezpečné,
                    transparentní a respektovaly základní práva</strong>.
                </p>
                <p>
                    Zákon je často přirovnáván ke GDPR — ale zatímco GDPR reguluje osobní údaje,
                    AI Act reguluje <strong className="text-white">samotné AI systémy</strong> a jejich
                    dopady na lidi.
                </p>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Koho se AI Act týká?</h2>
                <p>
                    AI Act platí pro <strong className="text-white">každého, kdo v EU vyvíjí, nasazuje
                    nebo používá AI systémy</strong>. To zahrnuje:
                </p>
                <ul className="list-disc pl-6 space-y-1 text-slate-400">
                    <li><strong className="text-white">Poskytovatele (providers)</strong> — firmy, které AI vyvíjí</li>
                    <li><strong className="text-white">Nasazovatele (deployers)</strong> — firmy, které AI používají na svém webu</li>
                    <li><strong className="text-white">Distributory a importéry</strong> — kdo AI systémy prodává v EU</li>
                </ul>
                <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4 mt-4">
                    <p className="text-amber-300 font-medium">
                        Pokud máte na webu chatbot, Google Analytics nebo doporučovací systém — jste nasazovatel AI systému a AI Act se vás týká.
                    </p>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Klíčové deadliny</h2>
                <div className="space-y-3">
                    {[
                        { date: "1. srpna 2024", event: "AI Act vstoupil v platnost" },
                        { date: "2. února 2025", event: "Zákaz nepřijatelných AI praktik (čl. 5) + povinnost AI gramotnosti (čl. 4)" },
                        { date: "2. srpna 2025", event: "Pravidla pro modely obecného účelu (GPAI)" },
                        { date: "2. srpna 2026", event: "Plná účinnost — povinnosti pro omezené a minimální riziko" },
                        { date: "2. srpna 2027", event: "Povinnosti pro vysokorizikové AI systémy" },
                    ].map((d) => (
                        <div key={d.date} className="flex gap-4 items-start">
                            <span className="text-sm font-mono text-fuchsia-400 whitespace-nowrap mt-0.5">{d.date}</span>
                            <span className="text-slate-400">{d.event}</span>
                        </div>
                    ))}
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Oficiální zdroje</h2>
                <ul className="list-disc pl-6 space-y-1 text-slate-400">
                    <li>
                        <a href="https://eur-lex.europa.eu/eli/reg/2024/1689/oj" target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:text-cyan-300 underline underline-offset-2">
                            Plné znění AI Actu na EUR-Lex (CS)
                        </a>
                    </li>
                    <li>
                        <a href="https://artificialintelligenceact.eu/" target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:text-cyan-300 underline underline-offset-2">
                            AI Act Explorer — interaktivní průvodce
                        </a>
                    </li>
                </ul>
            </section>
        </ContentPage>
    );
}
