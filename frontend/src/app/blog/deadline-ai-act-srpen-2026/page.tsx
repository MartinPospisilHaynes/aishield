import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import BlogCta from "@/components/blog-cta";
import Link from "next/link";

export const metadata: Metadata = {
    title: "Deadline AI Act: srpen 2026 — co se stane a jak se připravit",
    description:
        "Přehled všech deadlinů EU AI Act od února 2025 po srpen 2027. Co platí už dnes a co přijde.",
    alternates: { canonical: "https://aishield.cz/blog/deadline-ai-act-srpen-2026" },
    openGraph: {
        images: [{ url: "/blog/deadline-ai-act-srpen-2026.png", width: 1200, height: 630 }],
    },
    keywords: [
        "AI Act deadline",
        "AI Act srpen 2026",
        "AI Act časová osa",
        "kdy platí AI Act",
        "AI Act termíny",
        "EU AI Act účinnost",
    ],
};

const timeline = [
    { date: "1. 8. 2024", label: "AI Act vstoupil v platnost", status: "done" },
    { date: "2. 2. 2025", label: "Zákaz nepřijatelných praktik (čl. 5) + AI gramotnost (čl. 4)", status: "done" },
    { date: "2. 8. 2025", label: "Pravidla pro GPAI modely (GPT, Gemini, Claude)", status: "active" },
    { date: "2. 8. 2026", label: "Plná účinnost — povinnosti pro omezené riziko (čl. 50)", status: "upcoming" },
    { date: "2. 8. 2027", label: "Povinnosti pro vysokorizikové AI systémy (Annex III)", status: "upcoming" },
];

const jsonLd = {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    headline: "Deadline AI Act: srpen 2026 — co se stane a jak se připravit",
    description: "Přehled všech deadlinů EU AI Act od února 2025 po srpen 2027. Co platí už dnes a co přijde.",
    datePublished: "2026-02-05",
    dateModified: "2026-02-05",
    author: { "@type": "Organization", name: "AIshield.cz", url: "https://aishield.cz" },
    publisher: { "@type": "Organization", name: "AIshield.cz", logo: { "@type": "ImageObject", url: "https://aishield.cz/icon.png" } },
    mainEntityOfPage: { "@type": "WebPage", "@id": "https://aishield.cz/blog/deadline-ai-act-srpen-2026" },
    inLanguage: "cs",
    image: "https://aishield.cz/blog/deadline-ai-act-srpen-2026.png",
    keywords: "AI Act deadline, AI Act srpen 2026, AI Act časová osa, kdy platí AI Act",
};

export default function Page() {
    return (
        <>
            <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
            <ContentPage
                heroImage="/blog/deadline-ai-act-srpen-2026.png"
                breadcrumbs={[
                    { label: "Domů", href: "/" },
                    { label: "Blog", href: "/blog" },
                    { label: "Deadline srpen 2026" },
                ]}
                title="Deadline AI Act:"
                titleAccent="srpen 2026"
                subtitle="5. února 2026 • 6 min čtení"
            >
                <section>
                    <h2 className="text-xl font-semibold text-white mb-4">Časová osa AI Act</h2>
                    <div className="space-y-4">
                        {timeline.map((t) => (
                            <div key={t.date} className={`flex gap-4 rounded-xl border p-4 ${t.status === "done" ? "border-green-500/20 bg-green-500/5" :
                                    t.status === "active" ? "border-amber-500/20 bg-amber-500/5" :
                                        "border-white/[0.06] bg-white/[0.02]"
                                }`}>
                                <span className={`flex-shrink-0 w-3 h-3 rounded-full mt-1.5 ${t.status === "done" ? "bg-green-500" :
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
                    <h2 className="text-xl font-semibold text-white mb-3">Srpen 2026: co to znamená pro vás?</h2>
                    <p>
                        Od 2. srpna 2026 musí každý web a e-shop v EU, který používá AI systémy s omezeným
                        rizikem, plnit <Link href="/ai-act/clanek-50" className="text-fuchsia-400 hover:text-fuchsia-300">transparenční povinnosti dle čl. 50</Link>.
                    </p>
                    <p>To znamená:</p>
                    <ul className="list-disc pl-6 space-y-1 text-slate-400">
                        <li>Chatboty musí být označené jako AI</li>
                        <li>Web musí mít transparenční stránku</li>
                        <li>AI generovaný obsah musí být označen</li>
                    </ul>
                </section>

                <section>
                    <h2 className="text-xl font-semibold text-white mb-3">Jak se připravit?</h2>
                    <div className="rounded-2xl border border-fuchsia-500/20 bg-fuchsia-500/5 p-6">
                        <ol className="list-decimal pl-6 space-y-2 text-slate-400">
                            <li><Link href="/scan" className="text-fuchsia-400 hover:text-fuchsia-300">Skenujte svůj web</Link> — zjistěte, jaké AI používáte</li>
                            <li>Projděte <Link href="/ai-act/checklist" className="text-fuchsia-400 hover:text-fuchsia-300">10bodový checklist</Link></li>
                            <li>Nasadte transparenční stránku</li>
                            <li>Nastavte pravidelný monitoring</li>
                        </ol>
                    </div>
                </section>

                <BlogCta />
            </ContentPage>
        </>
    );
}
