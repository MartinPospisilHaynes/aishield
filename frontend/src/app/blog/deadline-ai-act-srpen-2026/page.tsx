import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "Deadline AI Act: srpen 2026 \u2014 co se stane a jak se p\u0159ipravit",
    description:
        "P\u0159ehled v\u0161ech deadlin\u016f EU AI Act od \u00fanora 2025 po srpen 2027. Co plat\u00ed u\u017e dnes a co přijde.",
    alternates: { canonical: "https://aishield.cz/blog/deadline-ai-act-srpen-2026" },
};

const timeline = [
    { date: "1. 8. 2024", label: "AI Act vstoupil v platnost", status: "done" },
    { date: "2. 2. 2025", label: "Z\u00e1kaz nep\u0159ijateln\u00fdch praktik (\u010dl. 5) + AI gramotnost (\u010dl. 4)", status: "done" },
    { date: "2. 8. 2025", label: "Pravidla pro GPAI modely (GPT, Gemini, Claude)", status: "active" },
    { date: "2. 8. 2026", label: "Pln\u00e1 \u00fa\u010dinnost \u2014 povinnosti pro omezen\u00e9 riziko (\u010dl. 50)", status: "upcoming" },
    { date: "2. 8. 2027", label: "Povinnosti pro vysokorizikov\u00e9 AI syst\u00e9my (Annex III)", status: "upcoming" },
];

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Dom\u016f", href: "/" },
                { label: "Blog", href: "/blog" },
                { label: "Deadline srpen 2026" },
            ]}
            title="Deadline AI Act:"
            titleAccent="srpen 2026"
            subtitle="5. \u00fanora 2026 \u2022 6 min \u010dten\u00ed"
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">\u010casov\u00e1 osa AI Act</h2>
                <div className="space-y-4">
                    {timeline.map((t) => (
                        <div key={t.date} className={`flex gap-4 rounded-xl border p-4 ${
                            t.status === "done" ? "border-green-500/20 bg-green-500/5" :
                            t.status === "active" ? "border-amber-500/20 bg-amber-500/5" :
                            "border-white/[0.06] bg-white/[0.02]"
                        }`}>
                            <span className={`flex-shrink-0 w-3 h-3 rounded-full mt-1.5 ${
                                t.status === "done" ? "bg-green-500" :
                                t.status === "active" ? "bg-amber-500 animate-pulse" :
                                "bg-slate-600"
                            }`} />
                            <div>
                                <span className="text-sm font-mono text-fuchsia-400">{t.date}</span>
                                <p className="text-slate-300 mt-0.5">{t.label}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Srpen 2026: co to znamen\u00e1 pro v\u00e1s?</h2>
                <p>
                    Od 2. srpna 2026 mus\u00ed ka\u017ed\u00fd web a e-shop v EU, kter\u00fd pou\u017e\u00edv\u00e1 AI syst\u00e9my s omezen\u00fdm
                    rizikem, plnit <Link href="/ai-act/clanek-50" className="text-fuchsia-400 hover:text-fuchsia-300">transparen\u010dn\u00ed povinnosti dle \u010dl. 50</Link>.
                </p>
                <p>To znamen\u00e1:</p>
                <ul className="list-disc pl-6 space-y-1 text-slate-400">
                    <li>Chatboty mus\u00ed b\u00fdt ozna\u010den\u00e9 jako AI</li>
                    <li>Web mus\u00ed m\u00edt transparen\u010dn\u00ed str\u00e1nku</li>
                    <li>AI generovan\u00fd obsah mus\u00ed b\u00fdt ozna\u010den</li>
                </ul>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Jak se p\u0159ipravit?</h2>
                <div className="rounded-2xl border border-fuchsia-500/20 bg-fuchsia-500/5 p-6">
                    <ol className="list-decimal pl-6 space-y-2 text-slate-400">
                        <li><Link href="/scan" className="text-fuchsia-400 hover:text-fuchsia-300">Skenujte sv\u016fj web</Link> \u2014 zjist\u011bte, jak\u00e9 AI pou\u017e\u00edv\u00e1te</li>
                        <li>Projd\u011bte <Link href="/ai-act/checklist" className="text-fuchsia-400 hover:text-fuchsia-300">10bodov\u00fd checklist</Link></li>
                        <li>Nasadte transparen\u010dn\u00ed str\u00e1nku</li>
                        <li>Nastavte pravideln\u00fd monitoring</li>
                    </ol>
                </div>
            </section>
        </ContentPage>
    );
}
