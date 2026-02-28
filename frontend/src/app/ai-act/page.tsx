import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
    title: "AI Act — kompletní průvodce pro české firmy",
    description:
        "Vše o EU AI Act (Nařízení 2024/1689) na jednom místě. Rizikové kategorie, povinnosti, " +
        "pokuty, deadliny a praktické kroky pro české firmy a e-shopy. Aktualizováno únor 2026.",
    alternates: { canonical: "https://aishield.cz/ai-act" },
};

const topics = [
    {
        href: "/ai-act/co-je-ai-act",
        title: "Co je AI Act?",
        desc: "Základní přehled nařízení EU 2024/1689 — proč vznikl, koho se týká a kdy začíná platit.",
        icon: "📜",
    },
    {
        href: "/ai-act/rizikove-kategorie",
        title: "Rizikové kategorie AI",
        desc: "4 úrovně rizika: nepřijatelné, vysoké, omezené a minimální. Kam spadá váš AI systém?",
        icon: "⚠️",
    },
    {
        href: "/ai-act/clanek-50",
        title: "Článek 50 — transparenční povinnosti",
        desc: "Povinnost informovat uživatele o AI. Jak vytvořit transparenční stránku a kam ji umístit.",
        icon: "📋",
    },
    {
        href: "/ai-act/pokuty",
        title: "Pokuty a sankce",
        desc: "Až 35 mil. EUR nebo 7 % obratu. Přehled pokut podle typu porušení s příklady.",
        icon: "💰",
    },
    {
        href: "/ai-act/e-shopy",
        title: "AI Act pro e-shopy",
        desc: "Chatboty, doporučování produktů, dynamické ceny, remarketing — co musí e-shop splnit.",
        icon: "🛒",
    },
    {
        href: "/ai-act/checklist",
        title: "AI Act checklist",
        desc: "10 kroků ke compliance. Praktický návod, který zvládne i malá firma bez právníka.",
        icon: "✅",
    },
];

export default function AIActHub() {
    return (
        <section className="py-20 sm:py-28">
            <div className="mx-auto max-w-4xl px-4 sm:px-6">
                <header className="text-center mb-16">
                    <p className="text-sm font-semibold uppercase tracking-wider text-fuchsia-400 mb-3">
                        Kompletní průvodce
                    </p>
                    <h1 className="text-4xl font-extrabold sm:text-5xl mb-4">
                        EU <span className="neon-text">AI Act</span> pro české firmy
                    </h1>
                    <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                        Nařízení EU 2024/1689 mění pravidla hry pro každého, kdo používá umělou
                        inteligenci. Připravili jsme kompletní průvodce — od základů po praktický checklist.
                    </p>
                </header>

                <div className="grid sm:grid-cols-2 gap-4">
                    {topics.map((t) => (
                        <Link
                            key={t.href}
                            href={t.href}
                            className="group rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 hover:bg-white/[0.04] hover:border-fuchsia-500/20 transition-all"
                        >
                            <div className="text-3xl mb-3">{t.icon}</div>
                            <h2 className="text-lg font-semibold text-white group-hover:text-fuchsia-400 transition-colors mb-2">
                                {t.title}
                            </h2>
                            <p className="text-sm text-slate-400">{t.desc}</p>
                        </Link>
                    ))}
                </div>

                <div className="mt-16 text-center">
                    <p className="text-slate-400 mb-4">
                        Nechcete číst? Zjistěte to rovnou.
                    </p>
                    <Link
                        href="/scan"
                        className="btn-primary cta-pulse text-base px-8 py-3.5 inline-flex items-center justify-center gap-2"
                    >
                        Skenovat web ZDARMA za 60 sekund
                    </Link>
                </div>
            </div>
        </section>
    );
}
