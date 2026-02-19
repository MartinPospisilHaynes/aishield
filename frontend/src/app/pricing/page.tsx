"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { createGuestCheckout } from "@/lib/api";
import { useAnalytics, useScrollTracking } from "@/lib/analytics";
import ScrollReveal from "@/components/scroll-reveal";

const plans = [
    {
        key: "basic",
        name: "BASIC",
        price: "4 999",
        priceNote: "jednorázově",
        description: "Compliance Kit — dokumenty ke stažení",
        features: [
            "Sken webu + AI Act report",
            "AI Act Compliance Kit (až 12 dokumentů dle rizika)",
            "Tištěná dokumentace v profesionální vazbě — připravená na kontrolu",
            "Elektronická záloha veškeré dokumentace",
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
            "Tištěná dokumentace v profesionální vazbě — připravená na kontrolu",
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
            "Tištěná dokumentace v profesionální vazbě — připravená na kontrolu",
            "10 hodin konzultací s compliance specialistou",
            "Metodická kontrola veškeré dokumentace",
            "Rozšířený audit interních AI systémů",
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
    const [coffeeEmail, setCoffeeEmail] = useState("");
    const [showCoffeeEmail, setShowCoffeeEmail] = useState(false);

    const { user } = useAuth();
    const router = useRouter();
    const { track } = useAnalytics();
    useScrollTracking();

    useEffect(() => {
        track("pricing_page_viewed");
    }, [track]);

    async function handleCheckout(planKey: string) {
        track("plan_selected", { plan: planKey });
        // Coffee = guest checkout, nevyžaduje přihlášení
        if (planKey === "coffee") {
            const emailToUse = user?.email || coffeeEmail;
            if (!emailToUse) {
                setShowCoffeeEmail(true);
                return;
            }
            setLoading(planKey);
            setError("");
            try {
                const data = await createGuestCheckout("coffee", emailToUse, "stripe");
                window.location.href = data.gateway_url;
            } catch (err: unknown) {
                setError(err instanceof Error ? err.message : "Nepodařilo se vytvořit platbu");
                setLoading(null);
            }
            return;
        }

        // Pokud není přihlášen, přesměrovat na registraci
        if (!user) {
            router.push(`/registrace?redirect=/objednavka&plan=${planKey}`);
            return;
        }

        // Přesměrovat na objednávkovou stránku s fakturačními údaji
        router.push(`/objednavka?plan=${planKey}`);
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
                <ScrollReveal variant="fade-up" delay={0}>
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
                        Jednorázové balíčky — dokumentace, implementace i odborná kontrola.
                        Platba kartou, Apple Pay nebo Google Pay. Bezpečně přes Stripe.
                    </p>
                </div>
                </ScrollReveal>

                {/* Error */}
                {error && (
                    <div className="mt-8 mx-auto max-w-md rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300 text-center">
                        {error}
                    </div>
                )}

                {/* Plans grid */}
                <div className="mt-16 grid grid-cols-1 gap-6 lg:grid-cols-3">
                    {plans.map((plan, idx) => (
                        <ScrollReveal key={plan.key} variant="fade-up" delay={idx + 1}>
                        <div
                            className={`relative rounded-2xl border p-5 sm:p-8 flex flex-col h-full transition-all duration-300 hover:-translate-y-1 ${plan.highlighted
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
                        </ScrollReveal>
                    ))}
                </div>



                {/* Payment methods */}
                <ScrollReveal variant="fade-up" delay={1}>
                <div className="mt-10 text-center">
                    <p className="text-xs text-slate-500 mb-4">Akceptujeme</p>
                    <div className="flex items-center justify-center gap-6 text-slate-500 flex-wrap">
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
                </ScrollReveal>



                {/* Monitoring */}
                <div className="mt-20">
                    <ScrollReveal variant="fade-up" delay={0}>
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
                    </ScrollReveal>

                    <ScrollReveal variant="slide-left" delay={1}>
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
                                    "Aktualizace všech vygenerovaných dokumentů",
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
                    </ScrollReveal>

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
                    <ScrollReveal variant="fade-up" delay={0}>
                    <div className="text-center mb-10">
                        <h2 className="text-2xl font-bold">
                            Podrobné <span className="neon-text">srovnání</span> balíčků
                        </h2>
                        <p className="mt-3 text-slate-400 max-w-xl mx-auto text-sm leading-relaxed">
                            Co přesně obsahuje každý balíček — na jednom místě.
                        </p>
                    </div>
                    </ScrollReveal>

                    <ScrollReveal variant="slide-right" delay={1}>
                    {(() => {
                        const FEATURES = [
                            { label: "Sken webu + AI Act report", basic: true, pro: true, enterprise: true },
                            { label: "Compliance Kit (až 12 dokumentů dle rizika)", basic: true, pro: true, enterprise: true },
                            { label: "Registr AI systémů", basic: true, pro: true, enterprise: true },
                            { label: "Transparenční stránka (HTML)", basic: true, pro: true, enterprise: true },
                            { label: "Texty oznámení pro AI nástroje", basic: true, pro: true, enterprise: true },
                            { label: "Interní AI politika firmy", basic: true, pro: true, enterprise: true },
                            { label: "Školení — prezentace v PPT", basic: true, pro: true, enterprise: true },
                            { label: "Záznamový list o proškolení", basic: true, pro: true, enterprise: true },
                            { label: "Tištěná dokumentace v profesionální vazbě (do 14 dnů)", basic: true, pro: true, enterprise: true },
                            { label: "Implementace na váš web na klíč", basic: false, pro: true, enterprise: true },
                            { label: "Nastavení transparenční stránky", basic: false, pro: true, enterprise: true },
                            { label: "Úprava cookie lišty a chatbotů", basic: false, pro: true, enterprise: true },
                            { label: "Podpora po dodání (30 dní)", basic: false, pro: true, enterprise: true },
                            { label: "Prioritní zpracování", basic: false, pro: true, enterprise: true },
                            { label: "10 h konzultací se specialistou", basic: false, pro: false, enterprise: true },
                            { label: "Metodická kontrola dokumentace", basic: false, pro: false, enterprise: true },
                            { label: "Rozšířený audit AI systémů", basic: false, pro: false, enterprise: true },
                            { label: "2 roky měsíčního monitoringu", basic: false, pro: false, enterprise: true },
                            { label: "Dedikovaný specialista", basic: false, pro: false, enterprise: true },
                            { label: "SLA 4h odezva v prac. době", basic: false, pro: false, enterprise: true },
                        ];
                        const CHECK = <svg className="w-5 h-5 text-green-400 mx-auto flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" /></svg>;
                        const CROSS = <svg className="w-4 h-4 text-slate-600 mx-auto flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 12H6" /></svg>;

                        const PLAN_META = [
                            { key: "basic" as const, name: "BASIC", price: "4 999 Kč", color: "slate", fieldKey: "basic" as const },
                            { key: "pro" as const, name: "PRO", price: "14 999 Kč", color: "fuchsia", fieldKey: "pro" as const },
                            { key: "enterprise" as const, name: "ENTERPRISE", price: "39 999 Kč", color: "slate", fieldKey: "enterprise" as const },
                        ];

                        return (
                            <>
                                {/* ── DESKTOP TABLE (hidden below lg) ── */}
                                <div className="hidden lg:block mx-auto max-w-4xl rounded-2xl border border-white/[0.06] bg-white/[0.02] overflow-hidden">
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="border-b border-white/[0.08]">
                                                <th className="text-left pl-6 pr-4 py-4 text-xs text-slate-500 uppercase tracking-wider font-medium w-[45%]">Služba</th>
                                                <th className="text-center px-4 py-4 w-[18%]">
                                                    <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">BASIC</div>
                                                    <div className="text-fuchsia-400/60 text-[11px] font-normal mt-0.5">4 999 Kč</div>
                                                </th>
                                                <th className="text-center px-4 py-4 w-[18%] bg-fuchsia-500/[0.04] border-x border-fuchsia-500/10">
                                                    <div className="text-xs font-bold text-fuchsia-400 uppercase tracking-wider">PRO</div>
                                                    <div className="text-fuchsia-300 text-[11px] font-normal mt-0.5">14 999 Kč</div>
                                                </th>
                                                <th className="text-center px-4 py-4 w-[19%]">
                                                    <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">ENTERPRISE</div>
                                                    <div className="text-fuchsia-400/60 text-[11px] font-normal mt-0.5">39 999 Kč</div>
                                                </th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {FEATURES.map((feat, i) => (
                                                <tr key={feat.label} className={`border-b border-white/[0.04] ${i % 2 === 1 ? "bg-white/[0.01]" : ""}`}>
                                                    <td className="pl-6 pr-4 py-3 text-[13px] text-slate-300 leading-snug">{feat.label}</td>
                                                    <td className="px-4 py-3 text-center">{feat.basic ? CHECK : CROSS}</td>
                                                    <td className="px-4 py-3 text-center bg-fuchsia-500/[0.02] border-x border-fuchsia-500/[0.06]">{feat.pro ? CHECK : CROSS}</td>
                                                    <td className="px-4 py-3 text-center">{feat.enterprise ? CHECK : CROSS}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>

                                    <div className="flex gap-3 p-5 pt-4 border-t border-white/[0.06]">
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

                                {/* ── MOBILE / TABLET CARDS (visible below lg) ── */}
                                <div className="lg:hidden space-y-4 max-w-lg mx-auto">
                                    {PLAN_META.map((plan) => {
                                        const isPro = plan.key === "pro";
                                        const included = FEATURES.filter((f) => f[plan.fieldKey]);
                                        const excluded = FEATURES.filter((f) => !f[plan.fieldKey]);
                                        return (
                                            <details
                                                key={plan.key}
                                                className={`group rounded-2xl border overflow-hidden ${isPro
                                                    ? "border-fuchsia-500/25 bg-gradient-to-b from-fuchsia-500/[0.08] to-transparent"
                                                    : "border-white/[0.08] bg-white/[0.02]"
                                                    }`}
                                                open={isPro}
                                            >
                                                <summary className="flex items-center justify-between px-5 py-4 cursor-pointer select-none">
                                                    <div className="flex items-center gap-3 min-w-0">
                                                        <span className={`text-sm font-bold tracking-wide ${isPro ? "text-fuchsia-400" : "text-white"}`}>{plan.name}</span>
                                                        {isPro && (
                                                            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-fuchsia-500/20 text-fuchsia-300 uppercase">Nejoblíbenější</span>
                                                        )}
                                                    </div>
                                                    <div className="flex items-center gap-3 flex-shrink-0">
                                                        <span className={`text-sm font-bold ${isPro ? "text-fuchsia-300" : "text-slate-300"}`}>{plan.price}</span>
                                                        <svg className="w-4 h-4 text-slate-500 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                                        </svg>
                                                    </div>
                                                </summary>

                                                <div className="px-5 pb-5">
                                                    {/* Included */}
                                                    <div className="space-y-1.5 mb-3">
                                                        {included.map((f) => (
                                                            <div key={f.label} className="flex items-start gap-2.5 text-[13px]">
                                                                <svg className="w-4 h-4 mt-0.5 text-green-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" /></svg>
                                                                <span className="text-slate-300">{f.label}</span>
                                                            </div>
                                                        ))}
                                                    </div>

                                                    {/* Excluded */}
                                                    {excluded.length > 0 && (
                                                        <div className="space-y-1.5 mb-4 pt-2 border-t border-white/[0.04]">
                                                            {excluded.map((f) => (
                                                                <div key={f.label} className="flex items-start gap-2.5 text-[13px]">
                                                                    <svg className="w-4 h-4 mt-0.5 text-slate-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 12H6" /></svg>
                                                                    <span className="text-slate-600">{f.label}</span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    )}

                                                    {/* CTA */}
                                                    <button
                                                        onClick={() => handleCheckout(plan.key)}
                                                        disabled={loading === plan.key}
                                                        className={`w-full py-3 rounded-xl text-sm font-semibold transition-all disabled:opacity-50 ${isPro
                                                            ? "bg-gradient-to-r from-fuchsia-600 to-fuchsia-500 text-white hover:from-fuchsia-500 hover:to-fuchsia-400 shadow-lg shadow-fuchsia-500/20"
                                                            : "border border-white/10 bg-white/5 text-slate-300 hover:bg-white/10"
                                                            }`}
                                                    >
                                                        {loading === plan.key ? "Přesměrování…" : `Objednat ${plan.name}`}
                                                    </button>
                                                </div>
                                            </details>
                                        );
                                    })}
                                </div>
                            </>
                        );
                    })()}
                    </ScrollReveal>
                </div>

                {/* FAQ */}
                <ScrollReveal variant="fade-up" delay={0}>
                <div className="mt-20 max-w-2xl mx-auto">
                    <h2 className="text-2xl font-bold text-center mb-8">Časté dotazy k platbám</h2>
                    <div className="space-y-3">
                        {[
                            {
                                q: "Jak platba probíhá?",
                                a: "Po kliknutí na tlačítko Objednat budete přesměrováni na zabezpečenou platební stránku Stripe, kde zaplatíte kartou, Apple Pay nebo Google Pay. Pokud preferujete bankovní převod, zašleme vám po objednávce fakturu s platebními údaji."
                            },
                            {
                                q: "Je to jednorázová platba?",
                                a: "Balíčky BASIC a PRO jsou jednorázové. Monitoring je volitelný měsíční doplněk — můžete ho přidat ke kterémukoliv balíčku, ale nemusíte."
                            },
                            {
                                q: "Co dostanu po zaplacení?",
                                a: "Po zaplacení se vám okamžitě odemkne Dashboard. Něž obdržíte dokumenty, provedeme hloubkový 24hodinový sken vašeho webu — 24 nezávislých skenů v 6 kolech ze 7 zemí světa (CZ, GB, US, BR, JP, ZA, AU), střídavě z desktopu i mobilu přes rezidenční proxy. Poté naše dokumenty projdou interní kontrolou kvality (obvykle do 48 hodin, max. 7 pracovních dnů). Výsledkem je sada až 12 compliance dokumentů v PDF přizpůsobená vašemu rizikovému profilu. Do 14 dnů vám navíc všechny dokumenty doručíme v tištěné podobě v profesionální vazbě — připravené na případnou kontrolu."
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
                </ScrollReveal>

                {/* ── Pozvi mě na kafé ── */}
                <ScrollReveal variant="scale-up" delay={1}>
                <div className="mt-20 max-w-md mx-auto">
                    <div className="rounded-2xl border border-amber-500/20 bg-gradient-to-b from-amber-500/[0.06] to-transparent p-8 text-center">
                        <div className="mx-auto w-14 h-14 rounded-2xl bg-amber-500/10 flex items-center justify-center mb-4">
                            <svg className="w-7 h-7 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M5 8h12v5a4 4 0 0 1-4 4H9a4 4 0 0 1-4-4V8Z" />
                                <path strokeLinecap="round" strokeLinejoin="round" d="M17 10h1.5a2.5 2.5 0 0 1 0 5H17" />
                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 20h10" />
                                <path strokeLinecap="round" strokeLinejoin="round" d="M8 4v2m3-2v2m3-2v2" />
                            </svg>
                        </div>
                        <h3 className="text-xl font-bold text-white mb-2">Pozvi nás na kafé</h3>
                        <p className="text-sm text-slate-400 mb-6 leading-relaxed">
                            Chcete nás podpořit? Kupte nám kafé za 50&nbsp;Kč
                            a&nbsp;zároveň si odzkoušíte, že platební brána funguje.
                        </p>
                        <div className="mb-5">
                            <span className="text-4xl font-extrabold text-amber-400">50</span>
                            <span className="text-slate-500 ml-1">Kč</span>
                        </div>
                        {showCoffeeEmail && !user && (
                            <div className="mb-4">
                                <label className="block text-xs text-slate-400 mb-1.5 text-left">Váš email (ať víme, kdo nás zve)</label>
                                <input
                                    type="email"
                                    value={coffeeEmail}
                                    onChange={(e) => setCoffeeEmail(e.target.value)}
                                    placeholder="vas@email.cz"
                                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:border-amber-500/40 focus:outline-none focus:ring-1 focus:ring-amber-500/20"
                                />
                            </div>
                        )}
                        <button
                            onClick={() => handleCheckout("coffee")}
                            disabled={loading === "coffee"}
                            className="inline-flex items-center justify-center gap-2 rounded-xl bg-amber-500 px-8 py-3.5 text-sm font-bold text-black hover:bg-amber-400 transition-all shadow-lg shadow-amber-500/25 active:scale-[0.97] disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading === "coffee" ? (
                                "Přesměrování na platbu…"
                            ) : (
                                <>
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 8h12v5a4 4 0 0 1-4 4H9a4 4 0 0 1-4-4V8Z" />
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M17 10h1.5a2.5 2.5 0 0 1 0 5H17" />
                                    </svg>
                                    Kup kafé
                                </>
                            )}
                        </button>
                        <p className="text-xs text-slate-600 mt-4">
                            Bezpečná platba přes Stripe.
                        </p>
                    </div>
                </div>
                </ScrollReveal>

                {/* Powered by */}
                <ScrollReveal variant="fade-up" delay={1}>
                <div className="mt-12 text-center">
                    <p className="text-xs text-slate-600">
                        Platby zpracovává{" "}
                        <a href="https://stripe.com" target="_blank" rel="noopener noreferrer" className="text-slate-500 hover:text-slate-400 transition-colors underline">
                            Stripe
                        </a>
                        {" "}— globální platební brána s PCI DSS certifikací
                    </p>
                </div>
                </ScrollReveal>
            </div>

        </section>
    );
}
