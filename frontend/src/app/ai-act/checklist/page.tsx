import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import Link from "next/link";

export const metadata: Metadata = {
    title: "AI Act checklist — 10 kroků ke compliance pro české firmy",
    description:
        "Praktický 10bodový checklist pro splnění AI Act. Od identifikace AI systémů po vytvoření dokumentace.",
    alternates: { canonical: "https://aishield.cz/ai-act/checklist" },
};

const steps = [
    { n: 1, title: "Identifikujte AI systémy na webu", desc: "Spusťte AIshield sken — automaticky najde chatboty, analytiku, ML modely.", action: "Skenovat zdarma", href: "/scan" },
    { n: 2, title: "Zmapujte interní AI", desc: "Používáte ChatGPT, Copilot, AI v účetnictví? I to spadá pod AI Act.", action: "Vyplnit dotazník", href: "/dotaznik" },
    { n: 3, title: "Klasifikujte riziko", desc: "Zařaďte každý AI systém do kategorie.", action: "Rizikové kategorie", href: "/ai-act/rizikove-kategorie" },
    { n: 4, title: "Vytvořte registr AI systémů", desc: "Centrální dokument se seznamem všech AI, jejich účelem a rizikovou kategorií." },
    { n: 5, title: "Napište transparenční stránku", desc: "HTML stránka informující uživatele o AI na webu dle čl. 50.", action: "Článek 50", href: "/ai-act/clanek-50" },
    { n: 6, title: "Označte chatbot", desc: "Vidielný banner: Komunikujete s umělou inteligencí." },
    { n: 7, title: "Označte AI obsah", desc: "Pokud generujete texty nebo obrázky pomocí AI — označte je." },
    { n: 8, title: "Vytvořte interní AI politiku", desc: "Pravidla pro zaměstnance: jak smí AI používat, co je zakázané." },
    { n: 9, title: "Zajistěte AI gramotnost", desc: "Článek 4 vyžaduje dostatečné znalosti osob pracujících s AI." },
    { n: 10, title: "Nastavte monitoring", desc: "AI systémy se mění. Nastavte pravidelný re-sken." },
];

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "AI Act", href: "/ai-act" },
                { label: "Checklist" },
            ]}
            title="AI Act"
            titleAccent="checklist"
            subtitle="10 kroků ke compliance. Praktický návod, který zvládne i malá firma bez právníka."
        >
            <div className="space-y-4">
                {steps.map((s) => (
                    <div key={s.n} className="flex gap-4 rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
                        <span className="flex-shrink-0 w-10 h-10 rounded-xl bg-fuchsia-500/20 text-fuchsia-400 flex items-center justify-center text-lg font-bold">
                            {s.n}
                        </span>
                        <div>
                            <h3 className="font-semibold text-white">{s.title}</h3>
                            <p className="text-sm text-slate-400 mt-1">{s.desc}</p>
                            {s.action && s.href && (
                                <Link href={s.href} className="text-sm text-fuchsia-400 hover:text-fuchsia-300 mt-2 inline-block">
                                    {s.action} →
                                </Link>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </ContentPage>
    );
}
