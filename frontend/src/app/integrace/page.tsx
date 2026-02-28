import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
    title: "Integrace \u2014 AI Act a popul\u00e1rn\u00ed n\u00e1stroje na \u010desk\u00fdch webech",
    description:
        "Jak AI Act ovliv\u0148uje Smartsupp, Google Analytics, Shoptet, ChatGPT a Meta Pixel? " +
        "Praktick\u00fd pr\u016fvodce pro ka\u017ed\u00fd n\u00e1stroj.",
    alternates: { canonical: "https://aishield.cz/integrace" },
};

const integrations = [
    { href: "/integrace/smartsupp", name: "Smartsupp", desc: "Chatbot a live chat s AI asistenc\u00ed", icon: "💬", cat: "Chatbot" },
    { href: "/integrace/google-analytics", name: "Google Analytics 4", desc: "Analytika s ML predikcemi a smart audiences", icon: "📊", cat: "Analytika" },
    { href: "/integrace/shoptet", name: "Shoptet", desc: "\u010cesk\u00e1 e-shop platforma s AI funkcemi", icon: "🛒", cat: "E-commerce" },
    { href: "/integrace/openai-chatgpt", name: "OpenAI / ChatGPT", desc: "Generativn\u00ed AI pro obsah, z\u00e1kaznick\u00fd servis", icon: "🧠", cat: "Generativn\u00ed AI" },
    { href: "/integrace/meta-pixel", name: "Meta Pixel", desc: "Reklamn\u00ed AI pro Facebook a Instagram", icon: "📡", cat: "Reklama" },
];

export default function IntegraceHub() {
    return (
        <section className="py-20 sm:py-28">
            <div className="mx-auto max-w-4xl px-4 sm:px-6">
                <header className="text-center mb-16">
                    <p className="text-sm font-semibold uppercase tracking-wider text-fuchsia-400 mb-3">Integrace</p>
                    <h1 className="text-4xl font-extrabold sm:text-5xl mb-4">
                        AI Act a <span className="neon-text">va\u0161e n\u00e1stroje</span>
                    </h1>
                    <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                        Ka\u017ed\u00fd n\u00e1stroj s AI na va\u0161em webu spad\u00e1 pod AI Act. Zjist\u011bte, co mus\u00edte ud\u011blat pro konkr\u00e9tn\u00ed slu\u017ebu.
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
                        Skenovat m\u016fj web ZDARMA
                    </Link>
                </div>
            </div>
        </section>
    );
}
