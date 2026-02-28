import type { Metadata } from "next";
import Link from "next/link";
import manifest from "@/data/blog-manifest.json";

export const metadata: Metadata = {
    title: "Blog — AI Act novinky, návody a tipy pro české firmy",
    description:
        "Aktuální informace o EU AI Act, praktické návody na compliance a tipy pro české weby a e-shopy.",
    alternates: { canonical: "https://aishield.cz/blog" },
};

interface Article {
    slug: string;
    href: string;
    title: string;
    desc: string;
    date: string;
    date_human: string;
    tag: string;
    image?: string;
}

export default function BlogHub() {
    const articles: Article[] = manifest as Article[];

    return (
        <section className="py-20 sm:py-28">
            <div className="mx-auto max-w-3xl px-4 sm:px-6">
                <header className="text-center mb-16">
                    <p className="text-sm font-semibold uppercase tracking-wider text-fuchsia-400 mb-3">Blog</p>
                    <h1 className="text-4xl font-extrabold sm:text-5xl mb-4">
                        AI Act <span className="neon-text">novinky</span>
                    </h1>
                    <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                        Praktické návody, analýzy a novinky o EU AI Act pro české firmy.
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
                                <span className="text-xs text-slate-500">{a.date_human}</span>
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
