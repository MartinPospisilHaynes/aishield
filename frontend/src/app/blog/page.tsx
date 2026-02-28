import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
    title: "Blog \u2014 AI Act novinky, n\u00e1vody a tipy pro \u010desk\u00e9 firmy",
    description:
        "Aktu\u00e1ln\u00ed informace o EU AI Act, praktick\u00e9 n\u00e1vody na compliance a tipy pro \u010desk\u00e9 weby a e-shopy.",
    alternates: { canonical: "https://aishield.cz/blog" },
};

const articles = [
    {
        href: "/blog/ai-act-a-e-shopy-v-cr",
        title: "AI Act a \u010desk\u00e9 e-shopy: Co mus\u00edte splnit do srpna 2026",
        desc: "Praktick\u00fd pr\u016fvodce pro majitele e-shop\u016f. Chatboty, doporu\u010dov\u00e1n\u00ed, remarketing.",
        date: "15. \u00fanora 2026",
        tag: "Pr\u016fvodce",
    },
    {
        href: "/blog/co-je-transparencni-stranka",
        title: "Co je transparen\u010dn\u00ed str\u00e1nka a pro\u010d ji pot\u0159ebujete",
        desc: "\u010cl\u00e1nek 50 AI Actu vy\u017eaduje informovat o AI. Jak vytvo\u0159it str\u00e1nku krok za krokem.",
        date: "10. \u00fanora 2026",
        tag: "N\u00e1vod",
    },
    {
        href: "/blog/deadline-ai-act-srpen-2026",
        title: "Deadline AI Act: srpen 2026 \u2014 co se stane a jak se p\u0159ipravit",
        desc: "P\u0159ehled v\u0161ech deadlin\u016f AI Actu. Co plat\u00ed u\u017e te\u010f a co p\u0159ijde v srpnu 2026.",
        date: "5. \u00fanora 2026",
        tag: "\u010casov\u00e1 osa",
    },
];

export default function BlogHub() {
    return (
        <section className="py-20 sm:py-28">
            <div className="mx-auto max-w-3xl px-4 sm:px-6">
                <header className="text-center mb-16">
                    <p className="text-sm font-semibold uppercase tracking-wider text-fuchsia-400 mb-3">Blog</p>
                    <h1 className="text-4xl font-extrabold sm:text-5xl mb-4">
                        AI Act <span className="neon-text">novinky</span>
                    </h1>
                    <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                        Praktick\u00e9 n\u00e1vody, anal\u00fdzy a novinky o EU AI Act pro \u010desk\u00e9 firmy.
                    </p>
                </header>
                <div className="space-y-6">
                    {articles.map((a) => (
                        <Link
                            key={a.href}
                            href={a.href}
                            className="group block rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 hover:bg-white/[0.04] hover:border-fuchsia-500/20 transition-all"
                        >
                            <div className="flex items-center gap-3 mb-3">
                                <span className="text-xs uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-fuchsia-500/10 text-fuchsia-400">
                                    {a.tag}
                                </span>
                                <span className="text-xs text-slate-500">{a.date}</span>
                            </div>
                            <h2 className="text-lg font-semibold text-white group-hover:text-fuchsia-400 transition-colors mb-2">
                                {a.title}
                            </h2>
                            <p className="text-sm text-slate-400">{a.desc}</p>
                        </Link>
                    ))}
                </div>
            </div>
        </section>
    );
}
