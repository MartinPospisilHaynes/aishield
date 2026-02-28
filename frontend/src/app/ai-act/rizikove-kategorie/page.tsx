import type { Metadata } from "next";
import ContentPage from "@/components/content-page";

export const metadata: Metadata = {
    title: "Rizikové kategorie AI Act — nepřijatelné, vysoké, omezené, minimální",
    description:
        "AI Act rozděluje AI systémy do 4 rizikových kategorií. Zjistěte, kam spadá váš chatbot, " +
        "analytika nebo doporučovací systém a jaké povinnosti z toho plynou.",
    alternates: { canonical: "https://aishield.cz/ai-act/rizikove-kategorie" },
};

const categories = [
    {
        level: "Nepřijatelné riziko",
        border: "border-red-500/30 bg-red-500/5",
        badge: "bg-red-500/20 text-red-400",
        desc: "AI systémy, které jsou v EU zcela zakázány od února 2025.",
        examples: ["Sociální bodování (social scoring)", "Biometrická identifikace v reálném čase na veřejnosti", "Manipulativní techniky zneužívající slabosti osob", "Prediktivní policing"],
        duty: "Absolutní zákaz. Pokuta až 35 mil. EUR nebo 7 % obratu.",
    },
    {
        level: "Vysoké riziko",
        border: "border-orange-500/30 bg-orange-500/5",
        badge: "bg-orange-500/20 text-orange-400",
        desc: "AI systémy s významným dopadem na lidská práva a bezpečnost.",
        examples: ["AI v náboru a hodnocení zaměstnanců", "AI v kreditním scoringu", "AI v zdravotnictví", "AI v kritické infrastruktuře"],
        duty: "Risk assessment, technická dokumentace, lidský dohled. Pokuta až 15 mil. EUR.",
    },
    {
        level: "Omezené riziko",
        border: "border-amber-500/30 bg-amber-500/5",
        badge: "bg-amber-500/20 text-amber-400",
        desc: "AI systémy, kde musíte uživatele informovat o interakci s AI. Sem spadá většina webových AI.",
        examples: ["Chatboty (Smartsupp, Tidio, Crisp)", "AI generovaný obsah", "Deepfakes a syntetická média", "Emoční rozpoznávání"],
        duty: "Transparenční povinnost dle čl. 50. Pokuta až 7,5 mil. EUR.",
    },
    {
        level: "Minimální riziko",
        border: "border-green-500/30 bg-green-500/5",
        badge: "bg-green-500/20 text-green-400",
        desc: "AI systémy bez specifických regulatorních povinností.",
        examples: ["Spam filtry", "AI ve videohrách", "Automatické doplňování textu", "Doporučování obsahu"],
        duty: "Žádné povinné požadavky. Doporučené dodržování kodexu chování.",
    },
];

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "AI Act", href: "/ai-act" },
                { label: "Rizikové kategorie" },
            ]}
            title="Rizikové kategorie"
            titleAccent="AI Act"
            subtitle="AI Act rozděluje AI systémy do 4 úrovní rizika. Čím vyšší riziko, tím přísnější povinnosti."
        >
            {categories.map((cat) => (
                <section key={cat.level} className={`rounded-2xl border ${cat.border} p-6`}>
                    <div className="flex items-center gap-3 mb-4">
                        <span className={`text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full ${cat.badge}`}>
                            {cat.level}
                        </span>
                    </div>
                    <p className="text-slate-300 mb-4">{cat.desc}</p>
                    <h3 className="text-sm font-semibold text-white mb-2">Příklady:</h3>
                    <ul className="list-disc pl-6 space-y-1 text-slate-400 mb-4">
                        {cat.examples.map((ex) => (
                            <li key={ex}>{ex}</li>
                        ))}
                    </ul>
                    <div className="rounded-lg bg-white/[0.03] p-3">
                        <p className="text-sm text-slate-400">
                            <strong className="text-white">Povinnosti: </strong>{cat.duty}
                        </p>
                    </div>
                </section>
            ))}
        </ContentPage>
    );
}
