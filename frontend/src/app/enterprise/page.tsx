"use client";

import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ═══════════════════════════════════════════
   ENTERPRISE INQUIRY PAGE
   Dotazník / poptávkový formulář pro velké firmy
   ═══════════════════════════════════════════ */

const INDUSTRIES = [
    "Bankovnictví a finance",
    "Pojišťovnictví",
    "Zdravotnictví",
    "E-commerce / Retail",
    "Výroba / Manufacturing",
    "IT a technologie",
    "Telekomunikace",
    "Energetika",
    "Logistika a doprava",
    "Stavebnictví",
    "Veřejná správa",
    "Vzdělávání",
    "Právní služby",
    "Marketing a média",
    "Jiné",
];

const COMPANY_SIZES = [
    "50–249 zaměstnanců",
    "250–999 zaměstnanců",
    "1 000–4 999 zaměstnanců",
    "5 000+ zaměstnanců",
];

const AI_SYSTEMS = [
    "Chatbot na webu (Smartsupp, Tidio, LiveAgent …)",
    "AI analytika (GA4 s ML, Mixpanel …)",
    "AI doporučovací systém (e-shop personalizace)",
    "AI generování obsahu (texty, obrázky, video)",
    "AI cílení reklam (Meta AI, Google Performance Max)",
    "AI v interních procesech (HR, účetnictví, ERP)",
    "AI v zákaznickém servisu (voiceboty, emailboty)",
    "AI v bezpečnosti (detekce podvodů, SIEM)",
    "Vlastní / interně vyvinutý AI systém",
    "Nevím přesně — potřebuji audit",
];

const SERVICES_NEEDED = [
    "Kompletní AI Act compliance audit",
    "Vygenerování dokumentace (Compliance Kit)",
    "Implementace transparenčních oznámení na web",
    "Školení AI gramotnosti pro zaměstnance (čl. 4)",
    "Klasifikace rizik AI systémů",
    "FRIA (Fundamental Rights Impact Assessment)",
    "Měsíční monitoring a aktualizace",
    "Konzultace s compliance specialistou",
    "Pomoc s registrem AI systémů",
    "Integrace do stávajícího compliance rámce (ISO, GDPR)",
];

const URGENCY_OPTIONS = [
    { value: "asap", label: "Co nejdříve — máme deadline" },
    { value: "month", label: "Do 1 měsíce" },
    { value: "quarter", label: "Do 3 měsíců" },
    { value: "exploring", label: "Zatím mapujeme možnosti" },
];

interface FormData {
    companyName: string;
    ico: string;
    website: string;
    industry: string;
    companySize: string;
    contactName: string;
    contactRole: string;
    contactEmail: string;
    contactPhone: string;
    aiSystems: string[];
    servicesNeeded: string[];
    urgency: string;
    budget: string;
    notes: string;
    gdprConsent: boolean;
}

const initialForm: FormData = {
    companyName: "",
    ico: "",
    website: "",
    industry: "",
    companySize: "",
    contactName: "",
    contactRole: "",
    contactEmail: "",
    contactPhone: "",
    aiSystems: [],
    servicesNeeded: [],
    urgency: "",
    budget: "",
    notes: "",
    gdprConsent: false,
};

export default function EnterprisePage() {
    const [form, setForm] = useState<FormData>(initialForm);
    const [step, setStep] = useState(0); // 0=intro, 1=company, 2=contact, 3=needs, 4=summary, 5=success
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState("");

    function updateField<K extends keyof FormData>(key: K, value: FormData[K]) {
        setForm((prev) => ({ ...prev, [key]: value }));
    }

    function toggleArray(key: "aiSystems" | "servicesNeeded", value: string) {
        setForm((prev) => {
            const arr = prev[key];
            return {
                ...prev,
                [key]: arr.includes(value)
                    ? arr.filter((v) => v !== value)
                    : [...arr, value],
            };
        });
    }

    function canProceed(): boolean {
        switch (step) {
            case 1:
                return !!(form.companyName && form.industry && form.companySize);
            case 2:
                return !!(form.contactName && form.contactEmail);
            case 3:
                return !!(form.aiSystems.length > 0 && form.servicesNeeded.length > 0 && form.urgency);
            case 4:
                return form.gdprConsent;
            default:
                return true;
        }
    }

    async function handleSubmit() {
        if (!form.gdprConsent) return;
        setSubmitting(true);
        setError("");

        try {
            const res = await fetch(`${API_URL}/api/enterprise-inquiry`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    company_name: form.companyName,
                    ico: form.ico,
                    website: form.website,
                    industry: form.industry,
                    company_size: form.companySize,
                    contact_name: form.contactName,
                    contact_role: form.contactRole,
                    contact_email: form.contactEmail,
                    contact_phone: form.contactPhone,
                    ai_systems: form.aiSystems,
                    services_needed: form.servicesNeeded,
                    urgency: form.urgency,
                    budget: form.budget,
                    notes: form.notes,
                }),
            });

            if (!res.ok) throw new Error("Nepodařilo se odeslat poptávku");
            setStep(5);
        } catch {
            // Fallback — open mailto with form data
            const subject = encodeURIComponent(
                `AIshield ENTERPRISE poptávka — ${form.companyName}`
            );
            const body = encodeURIComponent(
                `ENTERPRISE POPTÁVKA\n` +
                `═══════════════════\n\n` +
                `Firma: ${form.companyName}\n` +
                `IČO: ${form.ico || "neuvedeno"}\n` +
                `Web: ${form.website || "neuvedeno"}\n` +
                `Odvětví: ${form.industry}\n` +
                `Velikost: ${form.companySize}\n\n` +
                `KONTAKT\n` +
                `Jméno: ${form.contactName}\n` +
                `Pozice: ${form.contactRole || "neuvedeno"}\n` +
                `Email: ${form.contactEmail}\n` +
                `Telefon: ${form.contactPhone || "neuvedeno"}\n\n` +
                `AI SYSTÉMY\n` +
                form.aiSystems.map((s) => `• ${s}`).join("\n") + `\n\n` +
                `POŽADOVANÉ SLUŽBY\n` +
                form.servicesNeeded.map((s) => `• ${s}`).join("\n") + `\n\n` +
                `Urgence: ${form.urgency}\n` +
                `Budget: ${form.budget || "neuvedeno"}\n\n` +
                `Poznámka: ${form.notes || "—"}\n`
            );
            window.location.href = `mailto:info@aishield.cz?subject=${subject}&body=${body}`;
            // Still show success after fallback
            setStep(5);
            setError("");
        } finally {
            setSubmitting(false);
        }
    }

    /* ── Stepper dots ── */
    const steps = ["Úvod", "Firma", "Kontakt", "Potřeby", "Souhrn"];

    return (
        <section className="py-16 relative min-h-screen">
            {/* BG effects */}
            <div className="absolute inset-0 -z-10">
                <div className="absolute top-[5%] left-[20%] h-[500px] w-[500px] rounded-full bg-fuchsia-600/8 blur-[140px]" />
                <div className="absolute bottom-[10%] right-[15%] h-[400px] w-[400px] rounded-full bg-blue-600/6 blur-[120px]" />
            </div>

            <div className="mx-auto max-w-3xl px-6">

                {/* ══════════════ STEP 5: SUCCESS ══════════════ */}
                {step === 5 ? (
                    <div className="text-center py-20">
                        <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-emerald-500/20 ring-2 ring-emerald-500/40">
                            <svg className="h-10 w-10 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                        </div>
                        <h1 className="text-3xl font-bold text-white mb-4">
                            Děkujeme za vaši poptávku!
                        </h1>
                        <p className="text-slate-400 text-lg max-w-md mx-auto mb-2">
                            Vaši poptávku jsme přijali. Ozveme se vám do <strong className="text-white">24 hodin</strong> s individuální cenovou nabídkou.
                        </p>
                        <p className="text-slate-500 text-sm mb-10">
                            Pro urgentní záležitosti nás můžete kontaktovat přímo na{" "}
                            <a href="tel:+420732716141" className="text-fuchsia-400 hover:underline">+420 732 716 141</a>
                        </p>

                        <div className="flex flex-col sm:flex-row gap-4 justify-center">
                            <a
                                href="/"
                                className="inline-flex items-center justify-center rounded-xl bg-white/10 px-6 py-3 text-sm font-medium text-white hover:bg-white/15 transition"
                            >
                                ← Zpět na úvod
                            </a>
                            <a
                                href="/pricing"
                                className="inline-flex items-center justify-center rounded-xl bg-fuchsia-600 px-6 py-3 text-sm font-medium text-white hover:bg-fuchsia-500 transition"
                            >
                                Zobrazit ceník
                            </a>
                        </div>
                    </div>
                ) : (
                    <>
                        {/* Header */}
                        <div className="text-center mb-10">
                            <div className="inline-flex items-center gap-2 rounded-full bg-fuchsia-500/10 border border-fuchsia-500/20 px-4 py-1.5 text-sm text-fuchsia-300 mb-4">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                                        d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008z" />
                                </svg>
                                ENTERPRISE
                            </div>
                            <h1 className="text-3xl sm:text-4xl font-bold text-white mb-3">
                                Řešení na míru pro vaši firmu
                            </h1>
                            <p className="text-slate-400 max-w-xl mx-auto">
                                Vyplňte krátký dotazník a my vám do 24 hodin připravíme
                                individuální cenovou nabídku s přesným rozsahem služeb.
                            </p>
                        </div>

                        {/* Stepper */}
                        {step > 0 && (
                            <div className="flex items-center justify-center gap-2 mb-10">
                                {steps.slice(1).map((label, i) => (
                                    <div key={label} className="flex items-center gap-2">
                                        <button
                                            onClick={() => i + 1 < step ? setStep(i + 1) : undefined}
                                            className={`flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full transition ${i + 1 === step
                                                    ? "bg-fuchsia-500/20 text-fuchsia-300 border border-fuchsia-500/30"
                                                    : i + 1 < step
                                                        ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/20 cursor-pointer hover:bg-emerald-500/25"
                                                        : "bg-white/5 text-slate-500 border border-white/10"
                                                }`}
                                        >
                                            {i + 1 < step && (
                                                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                                </svg>
                                            )}
                                            {label}
                                        </button>
                                        {i < steps.length - 2 && (
                                            <div className={`w-6 h-px ${i + 1 < step ? "bg-emerald-500/40" : "bg-white/10"}`} />
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* ══════════════ STEP 0: INTRO ══════════════ */}
                        {step === 0 && (
                            <div className="space-y-6">
                                {/* Benefits */}
                                <div className="grid sm:grid-cols-2 gap-4">
                                    {[
                                        {
                                            icon: "🏢",
                                            title: "Individuální přístup",
                                            desc: "Každá firma je jiná. Připravíme řešení přesně na míru vašim potřebám a AI systémům.",
                                        },
                                        {
                                            icon: "👨‍💼",
                                            title: "Osobní konzultace",
                                            desc: "Dedikovaný compliance specialista vás provede celým procesem od auditu po implementaci.",
                                        },
                                        {
                                            icon: "📋",
                                            title: "Kompletní dokumentace",
                                            desc: "Registr AI, interní politiky, transparenční oznámení, školení — vše v jednom balíčku.",
                                        },
                                        {
                                            icon: "🔄",
                                            title: "Průběžný monitoring",
                                            desc: "Měsíční kontroly, aktualizace dokumentace při změnách legislativy i vašich AI systémů.",
                                        },
                                    ].map((b) => (
                                        <div
                                            key={b.title}
                                            className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-5"
                                        >
                                            <div className="text-2xl mb-2">{b.icon}</div>
                                            <h3 className="font-semibold text-white mb-1">{b.title}</h3>
                                            <p className="text-sm text-slate-400">{b.desc}</p>
                                        </div>
                                    ))}
                                </div>

                                {/* Pricing hint */}
                                <div className="rounded-2xl border border-fuchsia-500/20 bg-fuchsia-500/5 p-6 text-center">
                                    <p className="text-slate-300 mb-1">
                                        Enterprise balíčky začínají od{" "}
                                        <strong className="text-white text-lg">49 999 Kč</strong>
                                    </p>
                                    <p className="text-sm text-slate-500">
                                        Přesná cena závisí na počtu AI systémů, rozsahu služeb a velikosti firmy.
                                        Vyplňte dotazník a my vám připravíme nabídku na míru.
                                    </p>
                                </div>

                                <div className="text-center pt-2">
                                    <button
                                        onClick={() => setStep(1)}
                                        className="inline-flex items-center gap-2 rounded-xl bg-fuchsia-600 px-8 py-3.5 text-sm font-semibold text-white shadow-lg shadow-fuchsia-500/25 hover:bg-fuchsia-500 transition"
                                    >
                                        Začít poptávku
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                                        </svg>
                                    </button>
                                    <p className="text-xs text-slate-600 mt-3">Zabere to cca 3 minuty</p>
                                </div>
                            </div>
                        )}

                        {/* ══════════════ STEP 1: FIRMA ══════════════ */}
                        {step === 1 && (
                            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-6 sm:p-8 space-y-6">
                                <div>
                                    <h2 className="text-xl font-semibold text-white mb-1">O vaší firmě</h2>
                                    <p className="text-sm text-slate-500">Základní informace pro přípravu nabídky</p>
                                </div>

                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium text-slate-300 mb-1.5">
                                            Název firmy <span className="text-red-400">*</span>
                                        </label>
                                        <input
                                            type="text"
                                            value={form.companyName}
                                            onChange={(e) => updateField("companyName", e.target.value)}
                                            placeholder="např. Acme s.r.o."
                                            className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-slate-600 focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/30 outline-none transition"
                                        />
                                    </div>

                                    <div className="grid sm:grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium text-slate-300 mb-1.5">IČO</label>
                                            <input
                                                type="text"
                                                value={form.ico}
                                                onChange={(e) => updateField("ico", e.target.value)}
                                                placeholder="12345678"
                                                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-slate-600 focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/30 outline-none transition"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-slate-300 mb-1.5">Web firmy</label>
                                            <input
                                                type="url"
                                                value={form.website}
                                                onChange={(e) => updateField("website", e.target.value)}
                                                placeholder="https://www.firma.cz"
                                                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-slate-600 focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/30 outline-none transition"
                                            />
                                        </div>
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-slate-300 mb-2">
                                            Odvětví <span className="text-red-400">*</span>
                                        </label>
                                        <div className="flex flex-wrap gap-2">
                                            {INDUSTRIES.map((ind) => (
                                                <button
                                                    key={ind}
                                                    type="button"
                                                    onClick={() => updateField("industry", ind)}
                                                    className={`px-3 py-1.5 rounded-lg text-sm border transition ${form.industry === ind
                                                            ? "bg-fuchsia-500/20 border-fuchsia-500/40 text-fuchsia-300"
                                                            : "bg-white/5 border-white/10 text-slate-400 hover:bg-white/10 hover:text-white"
                                                        }`}
                                                >
                                                    {ind}
                                                </button>
                                            ))}
                                        </div>
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-slate-300 mb-2">
                                            Velikost firmy <span className="text-red-400">*</span>
                                        </label>
                                        <div className="grid grid-cols-2 gap-2">
                                            {COMPANY_SIZES.map((size) => (
                                                <button
                                                    key={size}
                                                    type="button"
                                                    onClick={() => updateField("companySize", size)}
                                                    className={`px-4 py-3 rounded-xl text-sm border transition text-left ${form.companySize === size
                                                            ? "bg-fuchsia-500/20 border-fuchsia-500/40 text-fuchsia-300"
                                                            : "bg-white/5 border-white/10 text-slate-400 hover:bg-white/10 hover:text-white"
                                                        }`}
                                                >
                                                    {size}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* ══════════════ STEP 2: CONTACT ══════════════ */}
                        {step === 2 && (
                            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-6 sm:p-8 space-y-6">
                                <div>
                                    <h2 className="text-xl font-semibold text-white mb-1">Kontaktní osoba</h2>
                                    <p className="text-sm text-slate-500">Na koho se máme obrátit s nabídkou</p>
                                </div>

                                <div className="space-y-4">
                                    <div className="grid sm:grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium text-slate-300 mb-1.5">
                                                Jméno a příjmení <span className="text-red-400">*</span>
                                            </label>
                                            <input
                                                type="text"
                                                value={form.contactName}
                                                onChange={(e) => updateField("contactName", e.target.value)}
                                                placeholder="Jan Novák"
                                                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-slate-600 focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/30 outline-none transition"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-slate-300 mb-1.5">Pozice ve firmě</label>
                                            <input
                                                type="text"
                                                value={form.contactRole}
                                                onChange={(e) => updateField("contactRole", e.target.value)}
                                                placeholder="CTO, DPO, Compliance manager …"
                                                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-slate-600 focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/30 outline-none transition"
                                            />
                                        </div>
                                    </div>

                                    <div className="grid sm:grid-cols-2 gap-4">
                                        <div>
                                            <label className="block text-sm font-medium text-slate-300 mb-1.5">
                                                Email <span className="text-red-400">*</span>
                                            </label>
                                            <input
                                                type="email"
                                                value={form.contactEmail}
                                                onChange={(e) => updateField("contactEmail", e.target.value)}
                                                placeholder="jan.novak@firma.cz"
                                                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-slate-600 focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/30 outline-none transition"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-slate-300 mb-1.5">Telefon</label>
                                            <input
                                                type="tel"
                                                value={form.contactPhone}
                                                onChange={(e) => updateField("contactPhone", e.target.value)}
                                                placeholder="+420 …"
                                                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-slate-600 focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/30 outline-none transition"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* ══════════════ STEP 3: NEEDS ══════════════ */}
                        {step === 3 && (
                            <div className="space-y-6">
                                {/* AI Systems */}
                                <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-6 sm:p-8">
                                    <h2 className="text-xl font-semibold text-white mb-1">Jaké AI systémy používáte?</h2>
                                    <p className="text-sm text-slate-500 mb-4">Vyberte všechny, které se vás týkají <span className="text-red-400">*</span></p>
                                    <div className="space-y-2">
                                        {AI_SYSTEMS.map((sys) => (
                                            <button
                                                key={sys}
                                                type="button"
                                                onClick={() => toggleArray("aiSystems", sys)}
                                                className={`w-full text-left px-4 py-3 rounded-xl text-sm border transition flex items-center gap-3 ${form.aiSystems.includes(sys)
                                                        ? "bg-fuchsia-500/15 border-fuchsia-500/30 text-white"
                                                        : "bg-white/5 border-white/10 text-slate-400 hover:bg-white/10 hover:text-white"
                                                    }`}
                                            >
                                                <span className={`flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center transition ${form.aiSystems.includes(sys)
                                                        ? "bg-fuchsia-500 border-fuchsia-500"
                                                        : "border-slate-600"
                                                    }`}>
                                                    {form.aiSystems.includes(sys) && (
                                                        <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                                        </svg>
                                                    )}
                                                </span>
                                                {sys}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Services needed */}
                                <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-6 sm:p-8">
                                    <h2 className="text-xl font-semibold text-white mb-1">Co potřebujete?</h2>
                                    <p className="text-sm text-slate-500 mb-4">Vyberte požadované služby <span className="text-red-400">*</span></p>
                                    <div className="space-y-2">
                                        {SERVICES_NEEDED.map((svc) => (
                                            <button
                                                key={svc}
                                                type="button"
                                                onClick={() => toggleArray("servicesNeeded", svc)}
                                                className={`w-full text-left px-4 py-3 rounded-xl text-sm border transition flex items-center gap-3 ${form.servicesNeeded.includes(svc)
                                                        ? "bg-fuchsia-500/15 border-fuchsia-500/30 text-white"
                                                        : "bg-white/5 border-white/10 text-slate-400 hover:bg-white/10 hover:text-white"
                                                    }`}
                                            >
                                                <span className={`flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center transition ${form.servicesNeeded.includes(svc)
                                                        ? "bg-fuchsia-500 border-fuchsia-500"
                                                        : "border-slate-600"
                                                    }`}>
                                                    {form.servicesNeeded.includes(svc) && (
                                                        <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                                        </svg>
                                                    )}
                                                </span>
                                                {svc}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Urgency */}
                                <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-6 sm:p-8">
                                    <h2 className="text-xl font-semibold text-white mb-1">Časový rámec</h2>
                                    <p className="text-sm text-slate-500 mb-4">Kdy potřebujete compliance řešení? <span className="text-red-400">*</span></p>
                                    <div className="grid sm:grid-cols-2 gap-2">
                                        {URGENCY_OPTIONS.map((opt) => (
                                            <button
                                                key={opt.value}
                                                type="button"
                                                onClick={() => updateField("urgency", opt.value)}
                                                className={`px-4 py-3 rounded-xl text-sm border transition text-left ${form.urgency === opt.value
                                                        ? "bg-fuchsia-500/20 border-fuchsia-500/40 text-fuchsia-300"
                                                        : "bg-white/5 border-white/10 text-slate-400 hover:bg-white/10 hover:text-white"
                                                    }`}
                                            >
                                                {opt.label}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Budget & notes */}
                                <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-6 sm:p-8 space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium text-slate-300 mb-1.5">Orientační budget (volitelné)</label>
                                        <input
                                            type="text"
                                            value={form.budget}
                                            onChange={(e) => updateField("budget", e.target.value)}
                                            placeholder="např. 50 000 – 100 000 Kč"
                                            className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-slate-600 focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/30 outline-none transition"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-300 mb-1.5">Poznámka (volitelné)</label>
                                        <textarea
                                            value={form.notes}
                                            onChange={(e) => updateField("notes", e.target.value)}
                                            rows={3}
                                            placeholder="Cokoliv dalšího, co bychom měli vědět …"
                                            className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-slate-600 focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/30 outline-none transition resize-none"
                                        />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* ══════════════ STEP 4: SUMMARY ══════════════ */}
                        {step === 4 && (
                            <div className="space-y-6">
                                <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-6 sm:p-8">
                                    <h2 className="text-xl font-semibold text-white mb-6">Souhrn vaší poptávky</h2>

                                    <div className="space-y-5">
                                        <SummaryBlock title="Firma">
                                            <SummaryRow label="Název" value={form.companyName} />
                                            {form.ico && <SummaryRow label="IČO" value={form.ico} />}
                                            {form.website && <SummaryRow label="Web" value={form.website} />}
                                            <SummaryRow label="Odvětví" value={form.industry} />
                                            <SummaryRow label="Velikost" value={form.companySize} />
                                        </SummaryBlock>

                                        <SummaryBlock title="Kontakt">
                                            <SummaryRow label="Jméno" value={form.contactName} />
                                            {form.contactRole && <SummaryRow label="Pozice" value={form.contactRole} />}
                                            <SummaryRow label="Email" value={form.contactEmail} />
                                            {form.contactPhone && <SummaryRow label="Telefon" value={form.contactPhone} />}
                                        </SummaryBlock>

                                        <SummaryBlock title="AI systémy">
                                            <ul className="space-y-1">
                                                {form.aiSystems.map((s) => (
                                                    <li key={s} className="text-slate-300 text-sm flex items-start gap-2">
                                                        <span className="text-fuchsia-400 mt-0.5">•</span>
                                                        {s}
                                                    </li>
                                                ))}
                                            </ul>
                                        </SummaryBlock>

                                        <SummaryBlock title="Požadované služby">
                                            <ul className="space-y-1">
                                                {form.servicesNeeded.map((s) => (
                                                    <li key={s} className="text-slate-300 text-sm flex items-start gap-2">
                                                        <span className="text-fuchsia-400 mt-0.5">•</span>
                                                        {s}
                                                    </li>
                                                ))}
                                            </ul>
                                        </SummaryBlock>

                                        <SummaryBlock title="Časový rámec">
                                            <p className="text-slate-300 text-sm">
                                                {URGENCY_OPTIONS.find((o) => o.value === form.urgency)?.label || form.urgency}
                                            </p>
                                        </SummaryBlock>

                                        {(form.budget || form.notes) && (
                                            <SummaryBlock title="Doplňující info">
                                                {form.budget && <SummaryRow label="Budget" value={form.budget} />}
                                                {form.notes && <SummaryRow label="Poznámka" value={form.notes} />}
                                            </SummaryBlock>
                                        )}
                                    </div>
                                </div>

                                {/* GDPR consent */}
                                <div className="rounded-2xl border border-white/[0.08] bg-white/[0.03] p-6">
                                    <label className="flex items-start gap-3 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={form.gdprConsent}
                                            onChange={(e) => updateField("gdprConsent", e.target.checked)}
                                            className="mt-1 h-5 w-5 rounded border-slate-600 bg-white/5 text-fuchsia-500 focus:ring-fuchsia-500/30"
                                        />
                                        <span className="text-sm text-slate-400">
                                            Souhlasím se zpracováním osobních údajů za účelem připravení cenové nabídky
                                            v souladu se{" "}
                                            <a href="/privacy" className="text-fuchsia-400 hover:underline" target="_blank">
                                                Zásadami ochrany soukromí
                                            </a>{" "}
                                            a{" "}
                                            <a href="/terms" className="text-fuchsia-400 hover:underline" target="_blank">
                                                Obchodními podmínkami
                                            </a>
                                            . <span className="text-red-400">*</span>
                                        </span>
                                    </label>
                                </div>

                                {error && (
                                    <div className="rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-3 text-red-300 text-sm">
                                        {error}
                                    </div>
                                )}
                            </div>
                        )}

                        {/* ══════════════ NAVIGATION BUTTONS ══════════════ */}
                        {step > 0 && step < 5 && (
                            <div className="flex items-center justify-between mt-8">
                                <button
                                    onClick={() => setStep(step - 1)}
                                    className="inline-flex items-center gap-2 rounded-xl bg-white/5 border border-white/10 px-5 py-3 text-sm font-medium text-slate-300 hover:bg-white/10 hover:text-white transition"
                                >
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 17l-5-5m0 0l5-5m-5 5h12" />
                                    </svg>
                                    Zpět
                                </button>

                                {step < 4 ? (
                                    <button
                                        onClick={() => setStep(step + 1)}
                                        disabled={!canProceed()}
                                        className="inline-flex items-center gap-2 rounded-xl bg-fuchsia-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-fuchsia-500/25 hover:bg-fuchsia-500 transition disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-fuchsia-600"
                                    >
                                        Další
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                                        </svg>
                                    </button>
                                ) : (
                                    <button
                                        onClick={handleSubmit}
                                        disabled={!canProceed() || submitting}
                                        className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-emerald-500/25 hover:bg-emerald-500 transition disabled:opacity-40 disabled:cursor-not-allowed"
                                    >
                                        {submitting ? (
                                            <>
                                                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                                </svg>
                                                Odesílám…
                                            </>
                                        ) : (
                                            <>
                                                Odeslat poptávku
                                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                                </svg>
                                            </>
                                        )}
                                    </button>
                                )}
                            </div>
                        )}
                    </>
                )}
            </div>
        </section>
    );
}

/* ── Helper components ── */

function SummaryBlock({ title, children }: { title: string; children: React.ReactNode }) {
    return (
        <div className="border-b border-white/[0.06] pb-4 last:border-0 last:pb-0">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">{title}</h3>
            {children}
        </div>
    );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
    return (
        <div className="flex items-start gap-3 text-sm">
            <span className="text-slate-500 min-w-[80px]">{label}:</span>
            <span className="text-slate-300">{value}</span>
        </div>
    );
}
