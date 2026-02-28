import type { Metadata } from "next";
import ContentPage from "@/components/content-page";

export const metadata: Metadata = {
    title: "AIshield vs Pr\u00e1vn\u00edk \u2014 technick\u00e1 detekce + pr\u00e1vn\u00ed kontext",
    description:
        "AIshield automaticky detekuje AI syst\u00e9my. Pr\u00e1vn\u00edk zajist\u00ed pr\u00e1vn\u00ed kontext. Ide\u00e1ln\u011b oba.",
    alternates: { canonical: "https://aishield.cz/srovnani/aishield-vs-pravnik" },
};

export default function Page() {
    return (
        <ContentPage
            breadcrumbs={[
                { label: "Dom\u016f", href: "/" },
                { label: "Srovn\u00e1n\u00ed", href: "/srovnani" },
                { label: "vs Pr\u00e1vn\u00edk" },
            ]}
            title="AIshield vs"
            titleAccent="pr\u00e1vn\u00edk"
            subtitle="Technick\u00e1 detekce a pr\u00e1vn\u00ed kontext. Nenahrazujte \u2014 dopl\u0148te."
        >
            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Co d\u011bl\u00e1 AIshield l\u00e9pe</h2>
                <ul className="list-disc pl-6 space-y-1 text-slate-400">
                    <li><strong className="text-white">Technick\u00e1 detekce</strong> \u2014 pr\u00e1vn\u00edk nev\u00ed, \u017ee na webu b\u011b\u017e\u00ed reCAPTCHA v3</li>
                    <li><strong className="text-white">Rychlost</strong> \u2014 60 sekund vs t\u00fddny konzultac\u00ed</li>
                    <li><strong className="text-white">Cena</strong> \u2014 z\u00e1kladn\u00ed sken je zdarma</li>
                    <li><strong className="text-white">Pr\u016fb\u011b\u017en\u00fd monitoring</strong> \u2014 p\u0159i \u010dtvrtletn\u00edm re-skenu zachyt\u00ed zm\u011bny</li>
                </ul>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Co d\u011bl\u00e1 pr\u00e1vn\u00edk l\u00e9pe</h2>
                <ul className="list-disc pl-6 space-y-1 text-slate-400">
                    <li><strong className="text-white">Pr\u00e1vn\u00ed v\u00fdklad</strong> \u2014 interpretace AI Actu pro v\u00e1\u0161 konkr\u00e9tn\u00ed business</li>
                    <li><strong className="text-white">Intern\u00ed procesy</strong> \u2014 nastaven\u00ed AI politiky, \u0161kolen\u00ed t\u00fdmu</li>
                    <li><strong className="text-white">Rizikov\u00e9 hodnocen\u00ed</strong> \u2014 hlubok\u00e1 anal\u00fdza pro vysokorizikov\u00e9 AI</li>
                    <li><strong className="text-white">Zastoupen\u00ed</strong> \u2014 komunikace s dozorov\u00fdm org\u00e1nem</li>
                </ul>
            </section>

            <section>
                <h2 className="text-xl font-semibold text-white mb-3">Ide\u00e1ln\u00ed kombinace</h2>
                <div className="rounded-xl border border-fuchsia-500/20 bg-fuchsia-500/5 p-5">
                    <ol className="list-decimal pl-6 space-y-2 text-slate-400">
                        <li>AIshield sken \u2014 technick\u00e1 mapa AI syst\u00e9m\u016f (60 s, zdarma)</li>
                        <li>Pr\u00e1vn\u00edk \u2014 interpretace a doporu\u010den\u00ed na z\u00e1klad\u011b reportu</li>
                        <li>AIshield monitoring \u2014 \u010dtvrtletn\u00ed re-sken a upozorn\u011bn\u00ed na zm\u011bny</li>
                    </ol>
                </div>
            </section>
        </ContentPage>
    );
}
