import type { Metadata } from "next";
import ContentPage from "@/components/content-page";

export const metadata: Metadata = {
    title: "OpenAI / ChatGPT a AI Act — interní i externí použití",
    description:
        "Používáte ChatGPT, GPT API nebo DALL-E? Jaké povinnosti plynou z AI Act pro české firmy?",
    alternates: { canonical: "https://aishield.cz/integrace/openai-chatgpt" },
};

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Integrace", href: "/integrace" },
                { label: "OpenAI / ChatGPT" },
            ]}
            title="OpenAI / ChatGPT a"
            titleAccent="AI Act"
            subtitle="GPT-4, DALL-E, Whisper — modely obecného účelu (GPAI) mají specifické povinnosti."
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Dvě roviny použití</h2>
                <div className="grid sm:grid-cols-2 gap-4">
                    <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-5">
                        <h3 className="font-semibold text-white mb-2">Interní použití</h3>
                        <p className="text-sm text-slate-400">Zaměstnanci používají ChatGPT pro texty, analýzy, e-maily.</p>
                        <p className="text-sm text-fuchsia-400 mt-2">Povinnost: AI gramotnost (čl. 4)</p>
                    </div>
                    <div className="rounded-xl border border-fuchsia-500/20 bg-fuchsia-500/5 p-5">
                        <h3 className="font-semibold text-white mb-2">Zákaznické použití</h3>
                        <p className="text-sm text-slate-400">GPT API v chatbotu, generování obsahu na webu.</p>
                        <p className="text-sm text-fuchsia-400 mt-2">Povinnost: Transparentnost (čl. 50)</p>
                    </div>
                </div>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">GPAI modely a AI Act</h2>
                <p>
                    OpenAI modely jsou klasifikovány jako <strong className="text-white">modely obecného účelu (GPAI)</strong>.
                    OpenAI jako poskytovatel musí od srpna 2025 plnit povinnosti dle kapitoly V AI Actu —
                    technická dokumentace, transparentnost, copyright politika.
                </p>
                <p>
                    Pro vás jako <strong className="text-white">nasazovatele (deployer)</strong> platí povinnosti
                    podle toho, jak AI používáte na webu.
                </p>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Co musíte udělat?</h2>
                <ol className="list-decimal pl-6 space-y-2 text-slate-400">
                    <li><strong className="text-white">Označit AI obsah</strong> — pokud text/obrázky generuje AI, informovat uživatele</li>
                    <li><strong className="text-white">AI gramotnost</strong> — proškolit tým, který s ChatGPT pracuje</li>
                    <li><strong className="text-white">Interní politika</strong> — co smí/nesmí být do ChatGPT vloženo (osobní údaje!)</li>
                    <li><strong className="text-white">Transparenční stránka</strong> — pokud GPT API běží na webu</li>
                </ol>
            </section>
        </ContentPage>
    );
}
