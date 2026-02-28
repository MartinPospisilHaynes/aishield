import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
    title: "Integrace — AI Act a populární nástroje na českých webech",
    description:
        "Jak AI Act ovlivňuje Smartsupp, Google Analytics, Shoptet, ChatGPT a Meta Pixel? " +
        "Praktický průvodce pro každý nástroj.",
    alternates: { canonical: "https://aishield.cz/integrace" },
};

const integrations = [
    { href: "/integrace/smartsupp", name: "Smartsupp", desc: "Chatbot a live chat s AI asistencí", icon: "💬", cat: "Chatbot" },
    { href: "/integrace/google-analytics", name: "Google Analytics 4", desc: "Analytika s ML predikcemi a smart audiences", icon: "📊", cat: "Analytika" },
    { href: "/integrace/shoptet", name: "Shoptet", desc: "Česká e-shop platforma s AI funkcemi", icon: "🛒", cat: "E-commerce" },
    { href: "/integrace/openai-chatgpt", name: "OpenAI / ChatGPT", desc: "Generativní AI pro obsah, zákaznický servis", icon: "🧠", cat: "Generativní AI" },
    { href: "/integrace/meta-pixel", name: "Meta Pixel", desc: "Reklamní AI pro Facebook a Instagram", icon: "📡", cat: "Reklama" },
];

export default function IntegraceHub() {
    return (
        <section className="py-20 sm:py-28">
            <div className="mx-auto max-w-4xl px-4 sm:px-6">
                <header className="text-center mb-16">
                    <p className="text-sm font-semibold uppercase tracking-wider text-fuchsia-400 mb-3">Integrace</p>
                    <h1 className="text-4xl font-extrabold sm:text-5xl mb-4">
                        AI Act a <span className="neon-text">vaše nástroje</span>
                    </h1>
                    <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                        Každý nástroj s AI na vašem webu spadá pod AI Act. Zjistěte, co musíte udělat pro konkrétní službu.
                    </p>
                </header>
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {integrations.map((i) => (
                        <Link
                            key={i.href}
                            href={i.href}
                            className="group rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 hover:bg-white/[0.04] hover:border-fuchsia-500/20 transition-all"
                        >
                            <div className="text-3xl mb-3">{i.icon}</div>
                            <span className="text-xs uppercase tracking-wider text-fuchsia-400/70">{i.cat}</span>
                            <h2 className="text-lg font-semibold text-white group-hover:text-fuchsia-400 transition-colors mt-1 mb-2">
                                {i.name}
                            </h2>
                            <p className="text-sm text-slate-400">{i.desc}</p>
                        </Link>
                    ))}
                </div>
                <div className="mt-16 text-center">
                    <Link href="/scan" className="btn-primary cta-pulse text-base px-8 py-3.5 inline-flex items-center justify-center gap-2">
                        Skenovat můj web ZDARMA
                    </Link>
                </div>
            </div>
        </section>
    );
}
