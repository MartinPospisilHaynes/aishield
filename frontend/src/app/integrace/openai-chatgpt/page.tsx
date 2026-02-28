import type { Metadata } from "next";
import ContentPage from "@/components/content-page";

export const metadata: Metadata = {
    title: "OpenAI / ChatGPT a AI Act \u2014 intern\u00ed i extern\u00ed pou\u017eit\u00ed",
    description:
        "Pou\u017e\u00edv\u00e1te ChatGPT, GPT API nebo DALL-E? Jak\u00e9 povinnosti plynou z AI Act pro \u010desk\u00e9 firmy?",
    alternates: { canonical: "https://aishield.cz/integrace/openai-chatgpt" },
};

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Dom\u016f", href: "/" },
                { label: "Integrace", href: "/integrace" },
                { label: "OpenAI / ChatGPT" },
            ]}
            title="OpenAI / ChatGPT a"
            titleAccent="AI Act"
            subtitle="GPT-4, DALL-E, Whisper \u2014 modely obecn\u00e9ho \u00fa\u010delu (GPAI) maj\u00ed specifick\u00e9 povinnosti."
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Dv\u011b roviny pou\u017eit\u00ed</h2>
                <div className="grid sm:grid-cols-2 gap-4">
                    <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-5">
                        <h3 className="font-semibold text-white mb-2">Intern\u00ed pou\u017eit\u00ed</h3>
                        <p className="text-sm text-slate-400">Zam\u011bstnanci pou\u017e\u00edvaj\u00ed ChatGPT pro texty, anal\u00fdzy, e-maily.</p>
                        <p className="text-sm text-fuchsia-400 mt-2">Povinnost: AI gramotnost (\u010dl. 4)</p>
                    </div>
                    <div className="rounded-xl border border-fuchsia-500/20 bg-fuchsia-500/5 p-5">
                        <h3 className="font-semibold text-white mb-2">Z\u00e1kaznick\u00e9 pou\u017eit\u00ed</h3>
                        <p className="text-sm text-slate-400">GPT API v chatbotu, generov\u00e1n\u00ed obsahu na webu.</p>
                        <p className="text-sm text-fuchsia-400 mt-2">Povinnost: Transparentnost (\u010dl. 50)</p>
                    </div>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">GPAI modely a AI Act</h2>
                <p>
                    OpenAI modely jsou klasifikov\u00e1ny jako <strong className="text-white">modely obecn\u00e9ho \u00fa\u010delu (GPAI)</strong>.
                    OpenAI jako poskytovatel mus\u00ed od srpna 2025 plnit povinnosti dle kapitoly V AI Actu \u2014
                    technick\u00e1 dokumentace, transparentnost, copyright politika.
                </p>
                <p>
                    Pro v\u00e1s jako <strong className="text-white">nasazovatele (deployer)</strong> plat\u00ed povinnosti
                    podle toho, jak AI pou\u017e\u00edv\u00e1te na webu.
                </p>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Co mus\u00edte ud\u011blat?</h2>
                <ol className="list-decimal pl-6 space-y-2 text-slate-400">
                    <li><strong className="text-white">Ozna\u010dit AI obsah</strong> \u2014 pokud text/obr\u00e1zky generuje AI, informovat u\u017eivatele</li>
                    <li><strong className="text-white">AI gramotnost</strong> \u2014 pro\u0161kolit t\u00fdm, kter\u00fd s ChatGPT pracuje</li>
                    <li><strong className="text-white">Intern\u00ed politika</strong> \u2014 co sm\u00ed/nesm\u00ed b\u00fdt do ChatGPT vlo\u017eeno (osobn\u00ed \u00fadaje!)</li>
                    <li><strong className="text-white">Transparen\u010dn\u00ed str\u00e1nka</strong> \u2014 pokud GPT API b\u011b\u017e\u00ed na webu</li>
                </ol>
            </section>
        </ContentPage>
    );
}
