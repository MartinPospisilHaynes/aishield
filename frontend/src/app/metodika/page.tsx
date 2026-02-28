import type { Metadata } from "next";
import ContentPage from "@/components/content-page";

export const metadata: Metadata = {
    title: "Metodika AIshield \u2014 jak skenujeme AI syst\u00e9my na webech",
    description:
        "Transparentn\u00ed popis metodiky AIshield skaneru. 3 f\u00e1ze anal\u00fdzy: crawler, AI detektor, " +
        "klasifik\u00e1tor rizik. Co detekujeme a jak hodnocen\u00ed funguje.",
    alternates: { canonical: "https://aishield.cz/metodika" },
};

const detections = [
    { cat: "Chatboty", items: "Smartsupp, Tidio, Crisp, Drift, Intercom, Zendesk, LiveChat, Tawk.to" },
    { cat: "Analytika", items: "Google Analytics 4 (ML predikce), Hotjar (AI Surveys), Mixpanel" },
    { cat: "Reklama", items: "Meta Pixel (Advantage+), Google Ads (Smart Bidding), TikTok Pixel" },
    { cat: "Generativn\u00ed AI", items: "OpenAI API, Anthropic Claude, Google Gemini API, AI generovan\u00fd obsah" },
    { cat: "E-commerce AI", items: "Doporu\u010dov\u00e1n\u00ed produkt\u016f, dynamic pricing, personalizace, Luigis Box" },
    { cat: "Antispam / Security", items: "reCAPTCHA v3, hCaptcha, Cloudflare Bot Management" },
];

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Dom\u016f", href: "/" },
                { label: "Metodika" },
            ]}
            title="Metodika"
            titleAccent="AIshield"
            subtitle="Jak skenujeme AI syst\u00e9my na webech? Transparentn\u00ed popis na\u0161\u00ed 3f\u00e1zov\u00e9 anal\u00fdzy."
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-4">3 f\u00e1ze anal\u00fdzy</h2>
                <div className="space-y-4">
                    {[
                        {
                            phase: "1",
                            title: "Crawler & Script Detection",
                            desc: "Na\u0161 crawler na\u010dte va\u0161i str\u00e1nku v headless prohl\u00ed\u017ee\u010di (Chromium) a analyzuje v\u0161echny na\u010dten\u00e9 skripty, iframe, cookie a network requesty. Identifikuje zn\u00e1m\u00e9 AI SDK a API vol\u00e1n\u00ed.",
                        },
                        {
                            phase: "2",
                            title: "AI Detektor",
                            desc: "Druh\u00e1 f\u00e1ze pou\u017e\u00edv\u00e1 patternov\u00e9 rozpozn\u00e1v\u00e1n\u00ed a heuristiky k identifikaci AI syst\u00e9m\u016f. Kontrolujeme DOM elementy, WebSocket spojen\u00ed, API endpointy a metadata.",
                        },
                        {
                            phase: "3",
                            title: "Klasifik\u00e1tor rizik",
                            desc: "Ka\u017ed\u00fd detekovan\u00fd AI syst\u00e9m za\u0159ad\u00edme do rizikov\u00e9 kategorie dle AI Act a vypo\u010d\u00edt\u00e1me celkov\u00e9 rizikov\u00e9 sk\u00f3re. V\u00fdstupem je p\u0159ehledn\u00fd report s doporu\u010den\u00edmi.",
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
                <h2 className="text-xl font-semibold text-white mb-3">Objektivita a nez\u00e1vislost</h2>
                <p>
                    AIshield je <strong className="text-white">nez\u00e1visl\u00fd n\u00e1stroj</strong>. Nem\u00e1me \u017e\u00e1dn\u00e9
                    partnerstv\u00ed s dodavateli AI syst\u00e9m\u016f. Na\u0161e hodnocen\u00ed je zalo\u017eeno v\u00fdhradn\u011b na
                    technick\u00e9 anal\u00fdze a textu AI Actu.
                </p>
            </section>
        </ContentPage>
    );
}
