"use client";

/**
 * BlogCta — CTA box pro blog články.
 * Vloží se na konec článku nebo do prostředku textu.
 */
export default function BlogCta({
    heading = "Zjistěte stav vašeho webu",
    text = "Bezplatný sken odhalí všechny AI systémy na vašem webu za 60 sekund. Bez registrace.",
    buttonText = "Skenovat web ZDARMA",
    href = "/scan",
}: {
    heading?: string;
    text?: string;
    buttonText?: string;
    href?: string;
}) {
    return (
        <section className="my-8 sm:my-12 rounded-2xl border border-fuchsia-500/20 bg-gradient-to-br from-fuchsia-500/10 via-transparent to-cyan-500/10 p-6 sm:p-8 text-center">
            <h3 className="text-lg sm:text-xl font-bold text-white mb-2">
                {heading}
            </h3>
            <p className="text-sm text-slate-400 mb-5 max-w-lg mx-auto">
                {text}
            </p>
            <a
                href={href}
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-fuchsia-600 to-purple-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-fuchsia-500/25 hover:from-fuchsia-500 hover:to-purple-500 transition-all"
            >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                </svg>
                {buttonText}
            </a>
        </section>
    );
}
