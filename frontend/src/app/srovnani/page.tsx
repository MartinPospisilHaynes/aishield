import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
    title: "Srovnání — AIshield vs alternativy AI Act compliance",
    description:
        "Jak si stojí AIshield ve srovnání s manuálním auditem, právníkem nebo Excel tabulkou?",
    alternates: { canonical: "https://aishield.cz/srovnani" },
};

const comparisons = [
    {
        href: "/srovnani/aishield-vs-manualni-audit",
        title: "AIshield vs Manuální audit",
        desc: "Automatický sken za 60 sekund vs týdny manuální práce.",
        winner: "60 s vs 2–4 týdny",
    },
    {
        href: "/srovnani/aishield-vs-pravnik",
        title: "AIshield vs Právník",
        desc: "Technická detekce + právní kontext. Doplněte, nenahrazujte.",
        winner: "Od 0 Kč vs od 50 000 Kč",
    },
    {
        href: "/srovnani/aishield-vs-excel",
        title: "AIshield vs Excel checklist",
        desc: "Automatická detekce vs manuální odpovědi v tabulce.",
        winner: "Automatizace vs 100+ řádků",
    },
];

export default function SrovnaniHub() {
    return (
        <section className="py-20 sm:py-28">
            <div className="mx-auto max-w-3xl px-4 sm:px-6">
                <header className="text-center mb-16">
                    <p className="text-sm font-semibold uppercase tracking-wider text-fuchsia-400 mb-3">Srovnání</p>
                    <h1 className="text-4xl font-extrabold sm:text-5xl mb-4">
                        AIshield vs <span className="neon-text">alternativy</span>
                    </h1>
                    <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                        Jak vyřešit AI Act compliance? Porovnejte přístupy.
                    </p>
                </header>
                <div className="space-y-4">
                    {comparisons.map((c) => (
                        <Link
                            key={c.href}
                            href={c.href}
                            className="group flex items-center justify-between rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 hover:bg-white/[0.04] hover:border-fuchsia-500/20 transition-all"
                        >
                            <div>
                                <h2 className="text-lg font-semibold text-white group-hover:text-fuchsia-400 transition-colors mb-1">
                                    {c.title}
                                </h2>
                                <p className="text-sm text-slate-400">{c.desc}</p>
                            </div>
                            <span className="text-sm font-mono text-fuchsia-400 whitespace-nowrap ml-4">
                                {c.winner}
                            </span>
                        </Link>
                    ))}
                </div>
            </div>
        </section>
    );
}
