import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
    title: "Srovn\u00e1n\u00ed \u2014 AIshield vs alternativy AI Act compliance",
    description:
        "Jak si stoj\u00ed AIshield ve srovn\u00e1n\u00ed s manu\u00e1ln\u00edm auditem, pr\u00e1vn\u00edkem nebo Excel tabulkou?",
    alternates: { canonical: "https://aishield.cz/srovnani" },
};

const comparisons = [
    {
        href: "/srovnani/aishield-vs-manualni-audit",
        title: "AIshield vs Manu\u00e1ln\u00ed audit",
        desc: "Automatick\u00fd sken za 60 sekund vs t\u00fddny manu\u00e1ln\u00ed pr\u00e1ce.",
        winner: "60 s vs 2\u20134 t\u00fddny",
    },
    {
        href: "/srovnani/aishield-vs-pravnik",
        title: "AIshield vs Pr\u00e1vn\u00edk",
        desc: "Technick\u00e1 detekce + pr\u00e1vn\u00ed kontext. Dopln\u011bte, nenahrazujte.",
        winner: "Od 0 K\u010d vs od 50 000 K\u010d",
    },
    {
        href: "/srovnani/aishield-vs-excel",
        title: "AIshield vs Excel checklist",
        desc: "Automatick\u00e1 detekce vs manu\u00e1ln\u00ed odpov\u011bdi v tabulce.",
        winner: "Automatizace vs 100+ \u0159\u00e1dk\u016f",
    },
];

export default function SrovnaniHub() {
    return (
        <section className="py-20 sm:py-28">
            <div className="mx-auto max-w-3xl px-4 sm:px-6">
                <header className="text-center mb-16">
                    <p className="text-sm font-semibold uppercase tracking-wider text-fuchsia-400 mb-3">Srovn\u00e1n\u00ed</p>
                    <h1 className="text-4xl font-extrabold sm:text-5xl mb-4">
                        AIshield vs <span className="neon-text">alternativy</span>
                    </h1>
                    <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                        Jak vy\u0159e\u0161it AI Act compliance? Porovnejte p\u0159\u00edstupy.
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
