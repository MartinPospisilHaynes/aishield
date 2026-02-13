"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { createCheckout } from "@/lib/api";

const plans = [
    {
        key: "basic",
        name: "BASIC",
        price: "4 999",
        priceNote: "jednorázově",
        description: "Compliance Kit — dokumenty ke stažení",
        features: [
            "Sken webu + AI Act report",
            "AI Act Compliance Kit (7 dokumentů)",
            "Transparenční stránka (HTML)",
            "Registr AI systémů",
            "Interní AI politika firmy",
            "Školení — prezentace v PowerPointu",
            "Záznamový list o proškolení",
        ],
        notIncluded: [
            "Implementace na klíč",
            "Podpora po dodání",
        ],
        cta: "Objednat BASIC",
        highlighted: false,
        icon: (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15a2.25 2.25 0 012.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25z" />
            </svg>
        ),
    },
    {
        key: "pro",
        name: "PRO",
        price: "14 999",
        priceNote: "jednorázově",
        description: "Vše z BASIC + implementace na klíč",
        features: [
            "Vše z BASIC",
            "Instalace widgetu na váš web",
            "Nastavení transparenční stránky",
            "Úprava chatbot oznámení",
            "Podpora po dobu 30 dní",
            "WordPress, Shoptet i custom",
            "Prioritní zpracování",
        ],
        notIncluded: [],
        cta: "Objednat PRO",
        highlighted: true,
        badge: "Nejoblíbenější",
        icon: (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
            </svg>
        ),
    },
    {
        key: "enterprise",
        name: "ENTERPRISE",
        price: "39 999",
        priceNote: "jednorázově",
        description: "Komplexní řešení pro větší firmy + 2 roky průběžné péče",
        features: [
            "Vše z PRO",
            "10 hodin konzultací s compliance specialistou",
            "Metodická kontrola veškeré dokumentace",
            "Rozšířený audit interních AI systémů",
            "Multi-domain (více webů / e-shopů)",
            "2 roky měsíčního monitoringu — automatický sken, propsání změn, hlášení a aktualizace dokumentů",
            "Dedikovaný specialista",
            "SLA 4h odezva v pracovní době",
        ],
        notIncluded: [],
        cta: "Objednat ENTERPRISE",
        highlighted: false,
        icon: (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008z" />
            </svg>
        ),
    },
];

export default function PricingPage() {
    const [loading, setLoading] = useState<string | null>(null);
    const [error, setError] = useState("");
    const { user } = useAuth();
    const router = useRouter();

    async function handleCheckout(planKey: string) {
        // Pokud není přihlášen, přesměrovat na registraci
        if (!user) {
            router.push(`/registrace?redirect=/pricing&plan=${planKey}`);
            return;
        }

        setLoading(planKey);
        setError("");

        try {
            const data = await createCheckout(planKey, user.email || "");
            // Přesměrovat na GoPay platební bránu
            window.location.href = data.gateway_url;
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Nepodařilo se vytvořit platbu");
            setLoading(null);
        }
    }

    return (
        <section className="py-20 relative">
            {/* BG effects */}
            <div className="absolute inset-0 -z-10">
                <div className="absolute top-[10%] left-[20%] h-[500px] w-[500px] rounded-full bg-fuchsia-500/5 blur-[130px]" />
                <div className="absolute bottom-[10%] right-[20%] h-[400px] w-[400px] rounded-full bg-cyan-500/5 blur-[120px]" />
            </div>

            <div className="mx-auto max-w-7xl px-4 sm:px-6">
                {/* Header */}
                <div className="text-center max-w-2xl mx-auto">
                    <div className="inline-flex items-center gap-2 rounded-full border border-fuchsia-500/20 bg-fuchsia-500/5 px-4 py-1.5 text-xs font-medium text-fuchsia-300 mb-6">
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                        </svg>
                        Transparentní ceny
                    </div>
                    <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
                        Vyberte si svůj{" "}
                        <span className="neon-text">compliance balíček</span>
                    </h1>
                    <p className="mt-4 text-slate-400 text-lg leading-relaxed">
                        Jednorázové balíčky — dokumentace, implementace i odborná kontrola. Platba kartou,
                        bankovním převodem, Apple Pay nebo Google Pay.
                    </p>
                </div>

                {/* Error */}
                {error && (
                    <div className="mt-8 mx-auto max-w-md rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300 text-center">
                        {error}
                    </div>
                )}

                {/* Plans grid */}
                <div className="mt-16 grid grid-cols-1 gap-6 lg:grid-cols-3">
                    {plans.map((plan) => (
                        <div
                            key={plan.key}
                            className={`relative rounded-2xl border p-5 sm:p-8 flex flex-col transition-all duration-300 hover:-translate-y-1 ${plan.highlighted
                                ? "border-fuchsia-500/30 bg-gradient-to-b from-fuchsia-500/[0.08] to-transparent shadow-[0_0_40px_rgba(232,121,249,0.08)]"
                                : "border-white/[0.06] bg-white/[0.02] hover:border-white/[0.12]"
                                }`}
                        >
                            {/* Badge */}
                            {"badge" in plan && plan.badge && (
                                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                                    <span className="inline-flex items-center gap-1.5 rounded-full bg-gradient-to-r from-fuchsia-500 to-purple-600 px-4 py-1 text-xs font-semibold text-white shadow-lg">
                                        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
                                        </svg>
                                        {plan.badge}
                                    </span>
                                </div>
                            )}

                            {/* Icon + Name */}
                            <div className="flex items-center gap-3 mb-4">
                                <div className={`p-2.5 rounded-xl ${plan.highlighted
                                    ? "bg-fuchsia-500/10 text-fuchsia-400"
                                    : "bg-white/5 text-slate-400"
                                    }`}>
                                    {plan.icon}
                                </div>
                                <h3 className="text-lg font-bold tracking-wide">{plan.name}</h3>
                            </div>

                            {/* Price */}
                            <div className="mb-1">
                                <span className={`text-4xl font-extrabold ${plan.highlighted ? "neon-text" : "text-white"
                                    }`}>
                                    {plan.price}
                                </span>
                                <span className="text-slate-500 ml-1">Kč</span>
                            </div>
                            <p className="text-xs text-slate-500 mb-4">{plan.priceNote}</p>
                            <p className="text-sm text-slate-400 mb-6">{plan.description}</p>

                            {/* Divider */}
                            <div className="h-px bg-gradient-to-r from-transparent via-white/10 to-transparent mb-6" />

                            {/* Features */}
                            <ul className="flex-1 space-y-3 mb-8">
                                {plan.features.map((feature) => (
                                    <li key={feature} className="flex items-start gap-2.5 text-sm">
                                        <svg className={`w-4 h-4 mt-0.5 flex-shrink-0 ${plan.highlighted ? "text-fuchsia-400" : "text-cyan-400"
                                            }`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                        </svg>
                                        <span className="text-slate-300">{feature}</span>
                                    </li>
                                ))}
                                {plan.notIncluded.map((feature) => (
                                    <li key={feature} className="flex items-start gap-2.5 text-sm">
                                        <svg className="w-4 h-4 mt-0.5 flex-shrink-0 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                        </svg>
                                        <span className="text-slate-600">{feature}</span>
                                    </li>
                                ))}
                            </ul>

                            {/* CTA */}
                            <button
                                onClick={() => handleCheckout(plan.key)}
                                disabled={loading === plan.key}
                                className={`w-full py-3.5 rounded-xl font-semibold text-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed ${plan.highlighted
                                    ? "btn-primary"
                                    : plan.key === "enterprise"
                                        ? "border border-white/10 bg-white/5 text-slate-300 hover:bg-white/10 hover:border-white/20"
                                        : "btn-secondary"
                                    }`}
                            >
                                {loading === plan.key ? "Přesměrování na platbu..." : plan.cta}
                            </button>
                        </div>
                    ))}
                </div>

                {/* Payment methods */}
                <div className="mt-16 text-center">
                    <p className="text-xs text-slate-500 mb-4">Akceptujeme</p>
                    <div className="flex items-center justify-center gap-6 text-slate-500">
                        <div className="flex items-center gap-2 text-xs">
                            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M2 6.5A2.5 2.5 0 014.5 4h15A2.5 2.5 0 0122 6.5v11a2.5 2.5 0 01-2.5 2.5h-15A2.5 2.5 0 012 17.5v-11zM4 9h16v2H4V9z" />
                            </svg>
                            Platební karty
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M3 6a3 3 0 013-3h12a3 3 0 013 3v12a3 3 0 01-3 3H6a3 3 0 01-3-3V6zm3-1a1 1 0 00-1 1v12a1 1 0 001 1h12a1 1 0 001-1V6a1 1 0 00-1-1H6zm2 4h8v2H8V9zm0 4h5v2H8v-2z" />
                            </svg>
                            Bankovní převod
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M17.0425 12.8656C17.0258 10.7904 18.7566 9.78103 18.8345 9.73195C17.8576 8.30979 16.3438 8.11469 15.8186 8.09808C14.5163 7.9637 13.2524 8.89476 12.5894 8.89476C11.9126 8.89476 10.8888 8.11195 9.79262 8.13407C8.36772 8.15619 7.04268 8.98889 6.30983 10.2884C4.80725 12.9293 5.93041 16.8154 7.36637 19.0447C8.08541 20.1367 8.92431 21.3524 10.0199 21.3138C11.0929 21.2724 11.4892 20.6264 12.7777 20.6264C14.0538 20.6264 14.4266 21.3138 15.5427 21.2889C16.6934 21.2724 17.4166 20.1781 18.1112 19.0778C18.9432 17.8207 19.2691 16.5885 19.2829 16.5305C19.2588 16.5222 17.0618 15.6475 17.0425 12.8656z" />
                            </svg>
                            Apple Pay
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M20.2 10.5c-.18-.64-.74-1.18-1.5-1.18h-2.44l-1.64-2.76C14.24 6.02 13.64 5.7 13 5.68H11c-.64.02-1.24.34-1.62.88L7.74 9.32H5.3c-.76 0-1.32.54-1.5 1.18L3 14.86c-.14.5.04 1.06.44 1.42.32.28.72.42 1.12.42H19.44c.4 0 .8-.14 1.12-.42.4-.36.58-.92.44-1.42l-.8-4.36z" />
                            </svg>
                            Google Pay
                        </div>
                    </div>
                </div>

                {/* Monitoring */}
                <div className="mt-20">
                    <div className="text-center mb-10">
                        <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/20 bg-cyan-500/5 px-4 py-1.5 text-xs font-medium text-cyan-300 mb-4">
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                            Volitelný doplněk
                        </div>
                        <h2 className="text-2xl font-bold">
                            Měsíční <span className="neon-text">monitoring</span> webu
                        </h2>
                        <p className="mt-3 text-slate-400 max-w-xl mx-auto text-sm leading-relaxed">
                            AI systémy se na vašem webu mohou objevit kdykoliv — po aktualizaci pluginu,
                            upgradu platformy nebo změně služby třetí strany. Monitoring vás ochrání.
                        </p>
                    </div>

                    <div className="grid md:grid-cols-2 gap-6 max-w-3xl mx-auto">
                        {/* Monitoring BASIC */}
                        <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 flex flex-col">
                            <h3 className="text-lg font-bold text-white mb-1">Monitoring</h3>
                            <div className="mb-3">
                                <span className="text-2xl font-extrabold text-white">299</span>
                                <span className="text-slate-500 ml-1">Kč/měsíc</span>
                            </div>
                            <ul className="space-y-2 text-sm mb-6 mt-4">
                                {[
                                    "1× měsíčně automatický sken webu",
                                    "Srovnání s předchozím skenem (diff)",
                                    "Emailové upozornění při nálezu",
                                    "Aktualizovaný Compliance Report",
                                    "Aktualizovaný Registr AI systémů",
                                    "Historie skenů v dashboardu",
                                ].map((f) => (
                                    <li key={f} className="flex items-start gap-2">
                                        <svg className="w-4 h-4 mt-0.5 text-cyan-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                        </svg>
                                        <span className="text-slate-300">{f}</span>
                                    </li>
                                ))}
                            </ul>
                            <div className="mt-auto text-center">
                                <a
                                    href="/dashboard#monitoring"
                                    className="inline-flex items-center justify-center gap-2 w-full rounded-xl border border-cyan-500/30 bg-cyan-500/10 px-6 py-2.5 text-sm font-semibold text-cyan-300 hover:bg-cyan-500/20 transition"
                                >
                                    Sjednat Monitoring
                                </a>
                            </div>
                        </div>

                        {/* Monitoring PRO */}
                        <div className="rounded-2xl border border-fuchsia-500/20 bg-gradient-to-b from-fuchsia-500/[0.06] to-transparent p-6 flex flex-col">
                            <h3 className="text-lg font-bold text-white mb-1">Monitoring Plus</h3>
                            <div className="mb-3">
                                <span className="text-2xl font-extrabold neon-text">599</span>
                                <span className="text-slate-500 ml-1">Kč/měsíc</span>
                            </div>
                            <ul className="space-y-2 text-sm mb-6 mt-4">
                                {[
                                    "2× měsíčně automatický sken webu",
                                    "Vše z Monitoring",
                                    "Aktualizace VŠECH 7 dokumentů",
                                    "Implementace změn na webu klienta",
                                    "Prioritní emailová podpora",
                                    "Čtvrtletní souhrnný přehled",
                                ].map((f) => (
                                    <li key={f} className="flex items-start gap-2">
                                        <svg className="w-4 h-4 mt-0.5 text-fuchsia-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                        </svg>
                                        <span className="text-slate-300">{f}</span>
                                    </li>
                                ))}
                            </ul>
                            <div className="mt-auto text-center">
                                <a
                                    href="/dashboard#monitoring"
                                    className="inline-flex items-center justify-center gap-2 w-full rounded-xl bg-fuchsia-600 px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-fuchsia-500/25 hover:bg-fuchsia-500 transition"
                                >
                                    Sjednat Monitoring Plus
                                </a>
                            </div>
                        </div>
                    </div>

                    <div className="mt-6 text-center space-y-1">
                        <p className="text-xs text-slate-500">
                            Monitoring je volitelný doplněk — lze aktivovat pouze po zakoupení balíčku BASIC, PRO nebo ENTERPRISE.
                        </p>
                        <p className="text-xs text-slate-500">
                            Minimální doba: 3 měsíce. Výpověď: 1 měsíc. U balíčku ENTERPRISE je 2 roky monitoringu již v ceně.
                        </p>
                    </div>
                </div>

                {/* Comparison Table */}
                <div className="mt-20">
                    <div className="text-center mb-10">
                        <h2 className="text-2xl font-bold">
                            Podrobné <span className="neon-text">srovnání</span> balíčků
                        </h2>
                        <p className="mt-3 text-slate-400 max-w-xl mx-auto text-sm leading-relaxed">
                            Co přesně obsahuje každý balíček — na jednom místě.
                        </p>
                    </div>

                    <div className="mx-auto max-w-4xl rounded-2xl border border-white/[0.06] bg-white/[0.02] overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm min-w-[540px]">
                                <thead>
                                    <tr className="border-b border-white/[0.06]">
                                        <th className="text-left px-5 py-3 text-xs text-slate-500 uppercase tracking-wider font-medium">Služba</th>
                                        <th className="text-center px-3 py-3 text-xs font-bold text-slate-400 uppercase tracking-wider">
                                            BASIC
                                            <div className="text-fuchsia-400/60 text-[10px] font-normal mt-0.5">4 999 Kč</div>
                                        </th>
                                        <th className="text-center px-3 py-3 text-xs font-bold text-fuchsia-400 uppercase tracking-wider bg-fuchsia-500/[0.04]">
                                            PRO
                                            <div className="text-fuchsia-300 text-[10px] font-normal mt-0.5">14 999 Kč</div>
                                        </th>
                                        <th className="text-center px-3 py-3 text-xs font-bold text-slate-400 uppercase tracking-wider">
                                            ENTERPRISE
                                            <div className="text-fuchsia-400/60 text-[10px] font-normal mt-0.5">39 999 Kč</div>
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {[
                                        { label: "Sken webu + AI Act report", basic: true, pro: true, enterprise: true },
                                        { label: "Compliance Kit (7 dokumentů)", basic: true, pro: true, enterprise: true },
                                        { label: "Registr AI systémů", basic: true, pro: true, enterprise: true },
                                        { label: "Transparenční stránka (HTML)", basic: true, pro: true, enterprise: true },
                                        { label: "Texty oznámení pro AI nástroje", basic: true, pro: true, enterprise: true },
                                        { label: "Interní AI politika firmy", basic: true, pro: true, enterprise: true },
                                        { label: "Školení — prezentace v PowerPointu", basic: true, pro: true, enterprise: true },
                                        { label: "Záznamový list o proškolení", basic: true, pro: true, enterprise: true },
                                        { label: "Implementace na váš web na klíč", basic: false, pro: true, enterprise: true },
                                        { label: "Nastavení transparenční stránky na webu", basic: false, pro: true, enterprise: true },
                                        { label: "Úprava cookie lišty a chatbot oznámení", basic: false, pro: true, enterprise: true },
                                        { label: "Podpora po dodání (30 dní)", basic: false, pro: true, enterprise: true },
                                        { label: "Prioritní zpracování", basic: false, pro: true, enterprise: true },
                                        { label: "10 hodin konzultací se specialistou", basic: false, pro: false, enterprise: true },
                                        { label: "Metodická kontrola veškeré dokumentace", basic: false, pro: false, enterprise: true },
                                        { label: "Rozšířený audit interních AI systémů", basic: false, pro: false, enterprise: true },
                                        { label: "Multi-domain (více webů / e-shopů)", basic: false, pro: false, enterprise: true },
                                        { label: "2 roky měsíčního monitoringu — automatický sken, propsání změn, hlášení a aktualizace", basic: false, pro: false, enterprise: true },
                                        { label: "Dedikovaný specialista", basic: false, pro: false, enterprise: true },
                                        { label: "SLA 4h odezva v pracovní době", basic: false, pro: false, enterprise: true },
                                    ].map((feat, i) => (
                                        <tr key={feat.label} className={`border-b border-white/[0.04] ${i % 2 === 0 ? '' : 'bg-white/[0.01]'}`}>
                                            <td className="px-5 py-2.5 text-sm text-slate-300">{feat.label}</td>
                                            <td className="px-3 py-2.5 text-center">
                                                {feat.basic ? (
                                                    <svg className="w-5 h-5 text-green-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" /></svg>
                                                ) : (
                                                    <svg className="w-4 h-4 text-red-400/40 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                                                )}
                                            </td>
                                            <td className="px-3 py-2.5 text-center bg-fuchsia-500/[0.02]">
                                                {feat.pro ? (
                                                    <svg className="w-5 h-5 text-green-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" /></svg>
                                                ) : (
                                                    <svg className="w-4 h-4 text-red-400/40 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                                                )}
                                            </td>
                                            <td className="px-3 py-2.5 text-center">
                                                {feat.enterprise ? (
                                                    <svg className="w-5 h-5 text-green-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" /></svg>
                                                ) : (
                                                    <svg className="w-4 h-4 text-red-400/40 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        <div className="flex flex-col sm:flex-row gap-3 p-5 pt-4 border-t border-white/[0.06]">
                            <button onClick={() => handleCheckout("basic")} className="flex-1 text-center text-sm font-medium py-2.5 rounded-xl border border-white/10 bg-white/5 text-slate-300 hover:bg-white/10 transition-all">
                                {loading === "basic" ? "Přesměrování…" : "Objednat BASIC"}
                            </button>
                            <button onClick={() => handleCheckout("pro")} className="flex-1 text-center text-sm font-medium py-2.5 rounded-xl bg-gradient-to-r from-fuchsia-600 to-fuchsia-500 text-white hover:from-fuchsia-500 hover:to-fuchsia-400 shadow-lg shadow-fuchsia-500/20 transition-all">
                                {loading === "pro" ? "Přesměrování…" : "Objednat PRO ★"}
                            </button>
                            <button onClick={() => handleCheckout("enterprise")} className="flex-1 text-center text-sm font-medium py-2.5 rounded-xl border border-white/10 bg-white/5 text-slate-300 hover:bg-white/10 transition-all">
                                {loading === "enterprise" ? "Přesměrování…" : "Objednat ENTERPRISE"}
                            </button>
                        </div>
                    </div>
                </div>

                {/* FAQ */}
                <div className="mt-20 max-w-2xl mx-auto">
                    <h2 className="text-2xl font-bold text-center mb-8">Časté dotazy k platbám</h2>
                    <div className="space-y-3">
                        {[
                            {
                                q: "Jak platba probíhá?",
                                a: "Po kliknutí na tlačítko budete přesměrováni na zabezpečenou platební bránu GoPay. Můžete platit kartou, bankovním převodem, Apple Pay nebo Google Pay."
                            },
                            {
                                q: "Je to jednorázová platba?",
                                a: "Balíčky BASIC a PRO jsou jednorázové. Monitoring je volitelný měsíční doplněk — můžete ho přidat ke kterémukoliv balíčku, ale nemusíte."
                            },
                            {
                                q: "Co dostanu po zaplacení?",
                                a: "Okamžitě po platbě se vám odemkne Dashboard, kde najdete všech 7 compliance dokumentů v PDF — report, registr, transparenční stránku, oznámení, AI politiku, školení i záznamový list."
                            },
                            {
                                q: "Proč potřebuji měsíční monitoring?",
                                a: "AI systémy se na webu objevují i bez vašeho vědomí — po aktualizaci pluginu, upgradu e-shopové platformy, změně chatbotu nebo aktivaci AI funkcí třetí stranou (analytika, reklamy, platební brána). Monitoring každý měsíc váš web proskenuje a upozorní vás na změny."
                            },
                            {
                                q: "Můžu monitoring kdykoliv zrušit?",
                                a: "Ano. Minimální doba je 3 měsíce, poté můžete kdykoliv vypovědět s 1měsíční výpovědní lhůtou. Při roční platbě ušetříte 17 %."
                            },
                            {
                                q: "Nahradíte advokáta?",
                                a: "Ne — jsme technický nástroj, ne právní poradna. Připravíme vám dokumentační podklady, které můžete vzít k právníkovi k odborné revizi."
                            },
                            {
                                q: "Můžu dostat fakturu?",
                                a: "Samozřejmě. Faktura se automaticky vygeneruje a odešle na váš email. Nejsme plátci DPH — uvedená cena je konečná."
                            },
                        ].map((faq) => (
                            <details
                                key={faq.q}
                                className="group rounded-xl border border-white/[0.06] bg-white/[0.02]"
                            >
                                <summary className="flex cursor-pointer items-center justify-between px-6 py-4 text-sm font-medium text-slate-200 hover:text-fuchsia-300 transition-colors">
                                    {faq.q}
                                    <svg className="w-4 h-4 text-slate-500 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                    </svg>
                                </summary>
                                <p className="px-6 pb-4 text-sm text-slate-400 leading-relaxed">
                                    {faq.a}
                                </p>
                            </details>
                        ))}
                    </div>
                </div>

                {/* Powered by */}
                <div className="mt-12 text-center">
                    <p className="text-xs text-slate-600">
                        Platby zpracovává{" "}
                        <a href="https://www.gopay.com" target="_blank" rel="noopener noreferrer" className="text-slate-500 hover:text-slate-400 transition-colors underline">
                            GoPay
                        </a>
                        {" "}— certifikovaná platební brána s PCI DSS
                    </p>
                </div>
            </div>
        </section>
    );
}
