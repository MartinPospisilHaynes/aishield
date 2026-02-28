import type { Metadata } from "next";
import ContentPage from "@/components/content-page";

export const metadata: Metadata = {
    title: "Metodika AIshield — jak skenujeme AI systémy na webech",
    description:
        "Transparentní popis metodiky AIshield skaneru. 3 fáze analýzy: crawler, AI detektor, " +
        "klasifikátor rizik. Co detekujeme a jak hodnocení funguje.",
    alternates: { canonical: "https://aishield.cz/metodika" },
};

const detections = [
    { cat: "Chatboty", items: "Smartsupp, Tidio, Crisp, Drift, Intercom, Zendesk, LiveChat, Tawk.to" },
    { cat: "Analytika", items: "Google Analytics 4 (ML predikce), Hotjar (AI Surveys), Mixpanel" },
    { cat: "Reklama", items: "Meta Pixel (Advantage+), Google Ads (Smart Bidding), TikTok Pixel" },
    { cat: "Generativní AI", items: "OpenAI API, Anthropic Claude, Google Gemini API, AI generovaný obsah" },
    { cat: "E-commerce AI", items: "Doporučování produktů, dynamic pricing, personalizace, Luigis Box" },
    { cat: "Antispam / Security", items: "reCAPTCHA v3, hCaptcha, Cloudflare Bot Management" },
];

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Metodika" },
            ]}
            title="Metodika"
            titleAccent="AIshield"
            subtitle="Jak skenujeme AI systémy na webech? Transparentní popis naší 3fázové analýzy."
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">3 fáze analýzy</h2>
                <div className="space-y-4">
                    {[
                        {
                            phase: "1",
                            title: "Crawler & Script Detection",
                            desc: "Naš crawler načte vaši stránku v headless prohlížeči (Chromium) a analyzuje všechny načtené skripty, iframe, cookie a network requesty. Identifikuje známé AI SDK a API volání.",
                        },
                        {
                            phase: "2",
                            title: "AI Detektor",
                            desc: "Druhá fáze používá patternové rozpoznávání a heuristiky k identifikaci AI systémů. Kontrolujeme DOM elementy, WebSocket spojení, API endpointy a metadata.",
                        },
                        {
                            phase: "3",
                            title: "Klasifikátor rizik",
                            desc: "Každý detekovaný AI systém zařadíme do rizikové kategorie dle AI Act a vypočítáme celkové rizikové skóre. Výstupem je přehledný report s doporučeními.",
                        },
                    ].map((p) => (
                        <div key={p.phase} className="flex gap-4">
                            <span className="flex-shrink-0 w-10 h-10 rounded-xl bg-fuchsia-500/20 text-fuchsia-400 flex items-center justify-center text-lg font-bold">
                                {p.phase}
                            </span>
                            <div>
                                <h3 className="font-semibold text-white">{p.title}</h3>
                                <p className="text-sm text-slate-400 mt-1">{p.desc}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-4">Co detekujeme</h2>
                <div className="space-y-3">
                    {detections.map((d) => (
                        <div key={d.cat} className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-4">
                            <h3 className="text-sm font-semibold text-fuchsia-400 mb-1">{d.cat}</h3>
                            <p className="text-sm text-slate-400">{d.items}</p>
                        </div>
                    ))}
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Objektivita a nezávislost</h2>
                <p>
                    AIshield je <strong className="text-white">nezávislý nástroj</strong>. Nemáme žádné
                    partnerství s dodavateli AI systémů. Naše hodnocení je založeno výhradně na
                    technické analýze a textu AI Actu.
                </p>
            </section>
        </ContentPage>
    );
}
