import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "Článek 50 AI Act — transparenční povinnosti pro weby a e-shopy",
    description:
        "Článek 50 AI Actu vyžaduje informovat uživatele o interakci s AI systémy. " +
        "Praktický návod na vytvoření transparenční stránky pro český web.",
    alternates: { canonical: "https://aishield.cz/ai-act/clanek-50" },
};

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "AI Act", href: "/ai-act" },
                { label: "Článek 50" },
            ]}
            title="Článek 50 AI Act —"
            titleAccent="transparenční povinnosti"
            subtitle="Co musíte zveřejnit na webu, aby vaši uživatelé věděli, že interagují s umělou inteligencí."
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Co říká článek 50?</h2>
                <p>
                    Článek 50 Nařízení (EU) 2024/1689 ukládá nasazovatelům AI systémů povinnost
                    informovat uživatele, že interagují s umělou inteligencí. Platí zejména pro chatboty,
                    AI generovaný obsah a systémy rozpoznávání emocí.
                </p>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Co musí transparenční stránka obsahovat?</h2>
                <div className="space-y-3">
                    {[
                        { n: "1", title: "Seznam AI systémů", desc: "Výčet všech AI nástrojů na webu — chatbot, analytika, doporučování, antispam." },
                        { n: "2", title: "Účel každého systému", desc: "Proč AI používáte — zákaznický servis, analýza návštěvnosti, personalizace." },
                        { n: "3", title: "Poskytovatel AI", desc: "Kdo AI vyvinul — Google (Analytics), Smartsupp (chatbot), Meta (pixel)." },
                        { n: "4", title: "Riziková kategorie", desc: "Klasifikace dle AI Act — většina webových nástrojů = omezené riziko." },
                        { n: "5", title: "Kontakt", desc: "Kdo ve firmě zodpovídá za AI compliance." },
                        { n: "6", title: "Práva uživatelů", desc: "Jak může uživatel AI odmítnout nebo podat stížnost." },
                    ].map((item) => (
                        <div key={item.n} className="flex gap-4">
                            <span className="flex-shrink-0 w-8 h-8 rounded-lg bg-fuchsia-500/20 text-fuchsia-400 flex items-center justify-center text-sm font-bold">
                                {item.n}
                            </span>
                            <div>
                                <h3 className="font-semibold text-white">{item.title}</h3>
                                <p className="text-sm text-slate-400">{item.desc}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">AIshield ji vygeneruje automaticky</h2>
                <p>
                    Po <Link href="/scan" className="text-fuchsia-400 hover:text-fuchsia-300">bezplatném skenu</Link> vašeho
                    webu AIshield automaticky identifikuje všechny AI systémy a vygeneruje kompletní transparenční stránku připravenou k nasazení.
                </p>
            </section>
        </ContentPage>
    );
}
