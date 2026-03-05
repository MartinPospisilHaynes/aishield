import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import BlogCta from "@/components/blog-cta";
import Link from "next/link";

export const metadata: Metadata = {
    title: "Co je transparenční stránka a proč ji potřebujete",
    description:
        "Článek 50 AI Actu vyžaduje informovat uživatele o AI systémech na webu. " +
        "Návod na vytvoření transparenční stránky krok za krokem.",
    alternates: { canonical: "https://aishield.cz/blog/co-je-transparencni-stranka" },
    openGraph: {
        images: [{ url: "/blog/co-je-transparencni-stranka.png", width: 1200, height: 630 }],
    },
    keywords: [
        "transparenční stránka AI",
        "AI Act článek 50",
        "AI transparenční povinnost",
        "AI Act web povinnost",
        "transparence AI systémy",
        "AI disclosur stránka",
    ],
};

const jsonLd = {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    headline: "Co je transparenční stránka a proč ji potřebujete",
    description: "Článek 50 AI Actu vyžaduje informovat uživatele o AI systémech na webu. Návod na vytvoření transparenční stránky krok za krokem.",
    datePublished: "2026-02-10",
    dateModified: "2026-02-10",
    author: { "@type": "Organization", name: "AIshield.cz", url: "https://aishield.cz" },
    publisher: { "@type": "Organization", name: "AIshield.cz", logo: { "@type": "ImageObject", url: "https://aishield.cz/icon.png" } },
    mainEntityOfPage: { "@type": "WebPage", "@id": "https://aishield.cz/blog/co-je-transparencni-stranka" },
    inLanguage: "cs",
    image: "https://aishield.cz/blog/co-je-transparencni-stranka.png",
    keywords: "transparenční stránka AI, AI Act článek 50, AI transparency page",
};

export default function Page() {
    return (
        <>
            <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />
            <ContentPage
                heroImage="/blog/co-je-transparencni-stranka.png"
                breadcrumbs={[
                    { label: "Domů", href: "/" },
                    { label: "Blog", href: "/blog" },
                    { label: "Transparenční stránka" },
                ]}
                title="Co je transparenční stránka"
                titleAccent="a proč ji potřebujete"
                subtitle="10. února 2026 • 5 min čtení"
            >
                <section>
                    <h2 className="text-xl font-semibold text-white mb-3">Nová povinnost od AI Act</h2>
                    <p>
                        Tak jako GDPR přineslo cookies lištu a privacy policy, AI Act přináší nový
                        prvek: <strong className="text-white">transparenční stránku o AI</strong>.
                    </p>
                    <p>
                        Jde o veřejně přístupnou stránku na vašem webu, kde informujete návštěvníky o tom,
                        jaké AI systémy používáte, proč je používáte a jaká práva mají uživatelé.
                    </p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold text-white mb-3">Co musí obsahovat?</h2>
                    <ol className="list-decimal pl-6 space-y-2 text-slate-400">
                        <li><strong className="text-white">Seznam AI systémů</strong> — každý nástroj s AI na webu</li>
                        <li><strong className="text-white">Účel použití</strong> — proč každý AI používáte</li>
                        <li><strong className="text-white">Poskytovatel</strong> — kdo AI vyvinul</li>
                        <li><strong className="text-white">Riziková kategorie</strong> — dle <Link href="/ai-act/rizikove-kategorie" className="text-fuchsia-400 hover:text-fuchsia-300">AI Act klasifikace</Link></li>
                        <li><strong className="text-white">Kontaktní osoba</strong> — kdo zodpovídá za AI compliance</li>
                        <li><strong className="text-white">Práva uživatelů</strong> — jak podat stížnost nebo AI odmítnout</li>
                    </ol>
                </section>

                <section>
                    <h2 className="text-xl font-semibold text-white mb-3">Kde stránku umístit?</h2>
                    <p>
                        Doporučujeme umístit odkaz do <strong className="text-white">patičky webu</strong> vedle
                        cookies a GDPR politik. Typická URL: <code className="text-fuchsia-400">/ai-act-souhlas</code> nebo
                        <code className="text-fuchsia-400"> /ai-transparency</code>.
                    </p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold text-white mb-3">AIshield ji vygeneruje za vás</h2>
                    <p>
                        Po <Link href="/scan" className="text-fuchsia-400 hover:text-fuchsia-300">skenu webu</Link> AIshield automaticky:
                    </p>
                    <ul className="list-disc pl-6 space-y-1 text-slate-400">
                        <li>Identifikuje všechny AI systémy</li>
                        <li>Klasifikuje riziko</li>
                        <li>Vygeneruje HTML kód transparenční stránky</li>
                        <li>Stačí vložit na web a je hotovo</li>
                    </ul>
                </section>

                <BlogCta />
            </ContentPage>
        </>
    );
}
