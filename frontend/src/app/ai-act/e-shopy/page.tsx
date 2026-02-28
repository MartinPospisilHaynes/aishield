import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "AI Act a e-shopy — co musí český e-shop splnit | AIshield.cz",
    description:
        "Kompletní průvodce AI Actem pro české e-shopy. Chatboty, doporučování produktů, " +
        "remarketing — co musíte splnit dle AI Actu a jak začít.",
    alternates: { canonical: "https://aishield.cz/ai-act/e-shopy" },
};

const aiSystems = [
    { name: "Chatbot (Smartsupp, Tidio)", risk: "Omezené riziko", color: "text-amber-400", desc: "Musí být označen jako AI dle čl. 50" },
    { name: "Doporučování produktů", risk: "Minimální riziko", color: "text-green-400", desc: "Personalizace nabídky pomocí ML algoritmů" },
    { name: "Google Analytics 4", risk: "Minimální riziko", color: "text-green-400", desc: "Prediktivní metriky používají strojové učení" },
    { name: "Meta Pixel / CAPI", risk: "Minimální riziko", color: "text-green-400", desc: "Reklamní optimalizace s AI cílením" },
    { name: "AI antispam (reCAPTCHA)", risk: "Minimální riziko", color: "text-green-400", desc: "Automatická detekce botů" },
];

const steps = [
    { num: "1", title: "Skenovat web", desc: "AIshield automaticky najde všechny AI systémy na vašem e-shopu za 60 sekund." },
    { num: "2", title: "Vytvořit transparenční stránku", desc: "Povinná stránka s přehledem všech AI systémů dle článku 50 AI Act." },
    { num: "3", title: "Označit chatbot jako AI", desc: "Každý chatbot musí jasně informovat uživatele, že komunikují s AI." },
    { num: "4", title: "Proškolit tým", desc: "AI gramotnost zaměstnanců je povinná dle článku 4 AI Actu." },
    { num: "5", title: "Nastavit monitoring", desc: "Pravidelný re-sken pro zachycení nových AI systémů na webu." },
];

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "AI Act", href: "/ai-act" },
                { label: "E-shopy" },
            ]}
            title="AI Act a české e-shopy:"
            titleAccent="co musíte splnit do srpna 2026"
            subtitle="Průměrný český e-shop používá 3–7 AI systémů. Většina majitelů o tom neví."
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Typický český e-shop a AI</h2>
                <p>
                    Průměrný český e-shop na{" "}
                    <Link href="/integrace/shoptet" className="text-fuchsia-400 hover:text-fuchsia-300">Shoptetu</Link> nebo
                    WooCommerce používá <strong className="text-white">3–7 AI systémů</strong>, aniž by si to majitel
                    uvědomoval. Chatbot, doporučování, analytika, reklamní pixely — to vše obsahuje AI.
                </p>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-4">5 nejčastějších AI systémů na e-shopech</h2>
                <div className="space-y-3">
                    {aiSystems.map((s) => (
                        <div key={s.name} className="rounded-xl border border-white/[0.08] bg-white/[0.03] p-4">
                            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 mb-1">
                                <h3 className="font-semibold text-white">{s.name}</h3>
                                <span className={`text-sm font-medium ${s.color}`}>{s.risk}</span>
                            </div>
                            <p className="text-sm text-slate-400">{s.desc}</p>
                        </div>
                    ))}
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Co musíte udělat?</h2>
                <div className="space-y-4">
                    {steps.map((s) => (
                        <div key={s.num} className="flex gap-4 items-start">
                            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-fuchsia-500/20 border border-fuchsia-500/30 flex items-center justify-center text-fuchsia-400 text-sm font-bold">
                                {s.num}
                            </div>
                            <div>
                                <h3 className="font-semibold text-white">{s.title}</h3>
                                <p className="text-sm text-slate-400">{s.desc}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Jaké jsou pokuty?</h2>
                <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-5">
                    <p className="text-slate-300">
                        Za nesplnění transparenčních povinností hrozí až{" "}
                        <strong className="text-red-400">7,5 mil. EUR</strong> nebo 1,5 % obratu. Pro e-shop
                        s obratem 10 mil. Kč to znamená až <strong className="text-white">150 000 Kč</strong> za
                        každý neoznačený AI systém. Více v našem{" "}
                        <Link href="/ai-act/pokuty" className="text-fuchsia-400 hover:text-fuchsia-300">přehledu pokut</Link>.
                    </p>
                </div>
            </section>
        </ContentPage>
    );
}
