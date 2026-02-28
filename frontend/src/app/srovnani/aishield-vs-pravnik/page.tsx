import type { Metadata } from "next";
import ContentPage from "@/components/content-page";

export const metadata: Metadata = {
    title: "AIshield vs Právník — technická detekce + právní kontext",
    description:
        "AIshield automaticky detekuje AI systémy. Právník zajistí právní kontext. Ideálně oba.",
    alternates: { canonical: "https://aishield.cz/srovnani/aishield-vs-pravnik" },
};

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Domů", href: "/" },
                { label: "Srovnání", href: "/srovnani" },
                { label: "vs Právník" },
            ]}
            title="AIshield vs"
            titleAccent="právník"
            subtitle="Technická detekce a právní kontext. Nenahrazujte — doplňte."
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Co dělá AIshield lépe</h2>
                <ul className="list-disc pl-6 space-y-1 text-slate-400">
                    <li><strong className="text-white">Technická detekce</strong> — právník neví, že na webu běží reCAPTCHA v3</li>
                    <li><strong className="text-white">Rychlost</strong> — 60 sekund vs týdny konzultací</li>
                    <li><strong className="text-white">Cena</strong> — základní sken je zdarma</li>
                    <li><strong className="text-white">Průběžný monitoring</strong> — při čtvrtletním re-skenu zachytí změny</li>
                </ul>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Co dělá právník lépe</h2>
                <ul className="list-disc pl-6 space-y-1 text-slate-400">
                    <li><strong className="text-white">Právní výklad</strong> — interpretace AI Actu pro váš konkrétní business</li>
                    <li><strong className="text-white">Interní procesy</strong> — nastavení AI politiky, školení týmu</li>
                    <li><strong className="text-white">Rizikové hodnocení</strong> — hluboká analýza pro vysokorizikové AI</li>
                    <li><strong className="text-white">Zastoupení</strong> — komunikace s dozorovým orgánem</li>
                </ul>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Ideální kombinace</h2>
                <div className="rounded-xl border border-fuchsia-500/20 bg-fuchsia-500/5 p-5">
                    <ol className="list-decimal pl-6 space-y-2 text-slate-400">
                        <li>AIshield sken — technická mapa AI systémů (60 s, zdarma)</li>
                        <li>Právník — interpretace a doporučení na základě reportu</li>
                        <li>AIshield monitoring — čtvrtletní re-sken a upozornění na změny</li>
                    </ol>
                </div>
            </section>
        </ContentPage>
    );
}
