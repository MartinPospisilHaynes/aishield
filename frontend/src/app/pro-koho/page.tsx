import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "Pro koho je AIshield — AI Act compliance pro české firmy",
    description:
        "AIshield pomáhá firmám, e-shopům, agenturám, obcím i živnostníkům v celé ČR " +
        "splnit EU AI Act. Praha, Brno, Ostrava, Olomouc a další města.",
    alternates: { canonical: "/pro-koho" },
};

const faqItems = [
    {
        question: "Musím mít sídlo v Praze, abych mohl AIshield využít?",
        answer: "Ne. AIshield je 100% online služba. Skenování, dotazník i generování dokumentace probíhá přes web. Fungujeme pro firmy z celé ČR — Praha, Brno, Ostrava, Olomouc, Plzeň i menší města.",
    },
    {
        question: "Týká se AI Act i malých firem s 5 zaměstnanci?",
        answer: "Ano. AI Act se vztahuje na každého, kdo provozuje AI systém v EU — bez ohledu na velikost firmy. Pro SME platí nižší stropy pokut, ale povinnost transparence (článek 50) zůstává stejná.",
    },
    {
        question: "Kolik stojí compliance dokumentace?",
        answer: "Bezplatný sken webu je zdarma. Compliance balíčky začínají na 4 999 Kč (BASIC) a zahrnují transparenční stránku, registr AI systémů a risk assessment.",
    },
];

function FaqJsonLd() {
    const schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        mainEntity: faqItems.map((item) => ({
            "@type": "Question",
            name: item.question,
            acceptedAnswer: {
                "@type": "Answer",
                text: item.answer,
            },
        })),
    };
    return (
        <script
            type="application/ld+json"
            dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
        />
    );
}

const segments = [
    {
        title: "E-shopy a online obchody",
        href: "/ai-act/e-shopy",
        desc: "Chatboty, doporučování produktů, remarketing. Průměrný e-shop má 3–7 AI systémů.",
        icon: "🛒",
    },
    {
        title: "Webové a digitální agentury",
        href: "/pro-koho/agentury",
        desc: "Implementujete AI nástroje klientům? AI Act se týká i vás jako deployera.",
        icon: "💻",
    },
    {
        title: "Malé a střední firmy (SME)",
        href: "/pro-koho/male-firmy",
        desc: "I malá firma s chatbotem nebo AI analytikou musí splnit transparenční povinnosti.",
        icon: "🏢",
    },
    {
        title: "Obce a veřejná správa",
        href: "/pro-koho/obce",
        desc: "Chatboty na úřednických webech, AI v dopravě, energetice. Veřejný sektor má přísnější pravidla.",
        icon: "🏛️",
    },
    {
        title: "Startupy a tech firmy",
        href: "/pro-koho/startupy",
        desc: "Vyvíjíte AI produkt? Potřebujete risk assessment, technickou dokumentaci a CE marking.",
        icon: "🚀",
    },
];

const regions = [
    { name: "Praha", desc: "Hlavní město — nejvíc firem s AI", href: "/pro-koho/praha" },
    { name: "Brno", desc: "Jihomoravský kraj — tech hub", href: "/pro-koho/brno" },
    { name: "Ostrava", desc: "Moravskoslezský kraj — průmysl + AI", href: "/pro-koho/ostrava" },
    { name: "Olomouc", desc: "Olomoucký kraj — sídlo AIshield", href: "/pro-koho/olomouc" },
    { name: "Plzeň", desc: "Plzeňský kraj — strojírenství + AI", href: "/pro-koho/plzen" },
    { name: "Liberec", desc: "Liberecký kraj", href: "/pro-koho/liberec" },
    { name: "České Budějovice", desc: "Jihočeský kraj", href: "/pro-koho/ceske-budejovice" },
    { name: "Hradec Králové", desc: "Královéhradecký kraj", href: "/pro-koho/hradec-kralove" },
];

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Pro koho" },
            ]}
            title="Pro koho je AIshield"
            titleAccent="— AI Act compliance pro celou ČR"
            subtitle="Pomáháme firmám, e-shopům, agenturám i obcím splnit EU AI Act. Kdekoliv v České republice."
        >
            {/* Segmenty */}
            <section>
                <h2 className="text-xl font-semibold text-white mb-6">Podle typu podnikání</h2>
                <div className="grid gap-4 sm:grid-cols-2">
                    {segments.map((s) => (
                        <Link
                            key={s.title}
                            href={s.href}
                            className="group block rounded-xl border border-slate-700/50 bg-slate-800/50 p-5 hover:border-fuchsia-500/40 transition-colors"
                        >
                            <div className="text-2xl mb-2">{s.icon}</div>
                            <h3 className="text-lg font-semibold text-white group-hover:text-fuchsia-400 transition-colors">
                                {s.title}
                            </h3>
                            <p className="text-sm text-slate-400 mt-1">{s.desc}</p>
                        </Link>
                    ))}
                </div>
            </section>

            {/* Regiony */}
            <section>
                <h2 className="text-xl font-semibold text-white mb-6">Podle regionu</h2>
                <p className="text-slate-400 mb-6">
                    AIshield.cz má sídlo v Olomouci, ale služby poskytujeme firmám v celé České republice.
                    Compliance dokumentace, transparenční stránky i školení — vše online, bez nutnosti osobní schůzky.
                </p>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                    {regions.map((r) => (
                        <Link
                            key={r.name}
                            href={r.href}
                            className="block rounded-lg border border-slate-700/50 bg-slate-800/30 p-4 hover:border-cyan-500/40 transition-colors"
                        >
                            <h3 className="font-semibold text-white">{r.name}</h3>
                            <p className="text-xs text-slate-500 mt-1">{r.desc}</p>
                        </Link>
                    ))}
                </div>
            </section>

            {/* FAQ pro lokální SEO */}
            <section>
                <FaqJsonLd />
                <h2 className="text-xl font-semibold text-white mb-4">Často kladené otázky</h2>
                <div className="space-y-4">
                    {faqItems.map((item) => (
                        <details key={item.question} className="group rounded-lg border border-slate-700/50 bg-slate-800/30 p-4">
                            <summary className="cursor-pointer font-semibold text-white group-open:text-fuchsia-400">
                                {item.question}
                            </summary>
                            <p className="mt-2 text-slate-400">{item.answer}</p>
                        </details>
                    ))}
                </div>
            </section>
        </ContentPage>
    );
}
