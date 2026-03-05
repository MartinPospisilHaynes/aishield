"use client";

import { useState, useEffect, useRef, useCallback, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { createCheckout, validateVoucher } from "@/lib/api";
import { createClient } from "@/lib/supabase-browser";
import { useAnalytics, useApiErrorTracking } from "@/lib/analytics";

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

const PLANS: Record<string, { name: string; price: number; features: string[] }> = {
    basic: {
        name: "BASIC",
        price: 4999,
        features: [
            "AI Act compliance dokumenty (až 12 dokumentů dle rizika)",
            "Tištěná dokumentace v profesionální vazbě",
            "Elektronická záloha dokumentace",
            "Transparentní stránka",
            "Školící prezentace (PowerPoint)",
            "Prezenční listina o proškolení",
            "Plán řízení AI incidentů",
            "Transparentnost a lidský dohled",
        ],
    },
    pro: {
        name: "PRO",
        price: 14999,
        features: [
            "Vše z BASIC",
            "Tištěná dokumentace v profesionální vazbě",
            "Implementace na klíč",
            "Konzultace s odborníkem",
            "Úpravy webu dle AI Act",
        ],
    },
    enterprise: {
        name: "ENTERPRISE",
        price: 39999,
        features: [
            "Vše z PRO",
            "Tištěná dokumentace v profesionální vazbě",
            "Komplexní audit AI systémů",
            "2 roky průběžné péče",
            "Prioritní podpora",
        ],
    },
};

type Gateway = "stripe" | "bank_transfer";

function CheckoutInner() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const { track } = useAnalytics();
    const trackApiError = useApiErrorTracking();
    const planKey = searchParams.get("plan") || "basic";
    const plan = PLANS[planKey];

    const [email, setEmail] = useState("");
    const [ico, setIco] = useState("");
    const [company, setCompany] = useState("");
    const [dic, setDic] = useState("");
    const [street, setStreet] = useState("");
    const [city, setCity] = useState("");
    const [zip, setZip] = useState("");
    const [phone, setPhone] = useState("");
    const [gateway, setGateway] = useState<Gateway>("stripe");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [userLoaded, setUserLoaded] = useState(false);

    // ARES auto-fill states
    const [aresLoading, setAresLoading] = useState(false);
    const [aresError, setAresError] = useState<string | null>(null);
    const [aresFilled, setAresFilled] = useState(false);

    // Slevový kód (voucher)
    const [voucherCode, setVoucherCode] = useState("");
    const [voucherLoading, setVoucherLoading] = useState(false);
    const [voucherApplied, setVoucherApplied] = useState(false);
    const [voucherDiscount, setVoucherDiscount] = useState(0);
    const [voucherError, setVoucherError] = useState<string | null>(null);
    const [voucherMessage, setVoucherMessage] = useState<string | null>(null);

    // Anti-bot: honeypot + timing
    const [honeypot, setHoneypot] = useState("");
    const formLoadedAt = useRef(Date.now());

    // Ověření slevového kódu
    async function handleVoucherApply() {
        if (!voucherCode.trim()) return;
        setVoucherLoading(true);
        setVoucherError(null);
        setVoucherMessage(null);
        try {
            const result = await validateVoucher(voucherCode.trim());
            if (result.valid) {
                setVoucherApplied(true);
                setVoucherDiscount(result.discount_percent);
                setVoucherMessage(result.message);
            } else {
                setVoucherError(result.message || "Neplatný kód");
                setVoucherApplied(false);
                setVoucherDiscount(0);
            }
        } catch {
            setVoucherError("Chyba při ověřování kódu");
        } finally {
            setVoucherLoading(false);
        }
    }

    function handleVoucherRemove() {
        setVoucherCode("");
        setVoucherApplied(false);
        setVoucherDiscount(0);
        setVoucherError(null);
        setVoucherMessage(null);
    }

    // ARES lookup when IČO reaches 8 digits
    const lookupAres = useCallback(async (icoValue: string) => {
        const cleaned = icoValue.replace(/\s/g, "");
        if (cleaned.length !== 8 || !/^\d{8}$/.test(cleaned)) return;

        setAresLoading(true);
        setAresError(null);
        try {
            const res = await fetch(`${API_URL}/api/ares/${cleaned}`);
            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: "Firma nenalezena" }));
                setAresError(err.detail || "Firma nenalezena v ARES");
                return;
            }
            const data = await res.json();
            if (data.name) setCompany(data.name);
            if (data.street) setStreet(data.street);
            if (data.city) setCity(data.city);
            if (data.zip) setZip(data.zip);
            setAresFilled(true);
        } catch {
            setAresError("Nepodařilo se spojit s ARES");
        } finally {
            setAresLoading(false);
        }
    }, []);

    // Load user email + IČO from supabase session
    useEffect(() => {
        (async () => {
            try {
                const supabase = createClient();
                const { data: { user } } = await supabase.auth.getUser();
                if (user?.email) setEmail(user.email);
                if (!user) {
                    router.push(`/registrace?redirect=/objednavka&plan=${planKey}`);
                    return;
                }
                // Pre-fill IČO from onboarding metadata
                const meta = user.user_metadata;
                if (meta?.ico) {
                    setIco(meta.ico);
                    // Trigger ARES lookup to fill company details
                    lookupAres(meta.ico);
                }
            } catch {
                // ignore
            }
            setUserLoaded(true);
        })();
    }, [planKey, router, lookupAres]);

    function handleIcoChange(value: string) {
        setIco(value);
        setAresFilled(false);
        setAresError(null);
        const cleaned = value.replace(/\s/g, "");
        if (cleaned.length === 8 && /^\d{8}$/.test(cleaned)) {
            lookupAres(value);
        }
    }

    if (!plan) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center">
                <div className="text-center">
                    <h1 className="text-2xl font-bold text-white mb-4">Neznámý balíček</h1>
                    <button onClick={() => router.push("/pricing")} className="text-fuchsia-400 hover:underline">
                        ← Zpět na ceník
                    </button>
                </div>
            </div>
        );
    }

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setError(null);

        // Anti-bot checks
        if (honeypot) return;
        const elapsed = Date.now() - formLoadedAt.current;
        if (elapsed < 3000) {
            setError("Formulář byl odeslán příliš rychle. Zkuste to prosím znovu.");
            return;
        }

        setLoading(true);
        track("checkout_started", { plan: planKey, gateway });

        try {
            const billing = { company, ico, dic, street, city, zip, phone };
            const data = await createCheckout(planKey, email, gateway, billing, voucherApplied ? voucherCode.trim() : undefined);
            track("checkout_redirected", { plan: planKey, gateway: data.gateway || gateway });
            window.location.href = data.gateway_url;
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Nepodařilo se vytvořit platbu");
            track("checkout_failed", { plan: planKey, error: err instanceof Error ? err.message : "unknown" });
            trackApiError("/api/payments/checkout", err, { plan: planKey, gateway });
            setLoading(false);
        }
    }

    if (!userLoaded) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center">
                <div className="w-8 h-8 border-2 border-fuchsia-500 border-t-transparent rounded-full animate-spin" />
            </div>
        );
    }

    const inputClass = "w-full bg-white/[0.04] border border-white/[0.1] rounded-xl px-4 py-3 text-white text-sm outline-none focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/25 transition-all placeholder:text-slate-600";

    return (
        <div className="min-h-screen bg-slate-950 text-white">
            {/* Background */}
            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute top-[-200px] right-[-100px] w-[500px] h-[500px] bg-fuchsia-600/8 rounded-full blur-[150px]" />
                <div className="absolute bottom-[-200px] left-[-100px] w-[400px] h-[400px] bg-cyan-500/8 rounded-full blur-[120px]" />
            </div>

            <div className="relative z-10 max-w-4xl mx-auto px-4 py-12">
                {/* Back link */}
                <button onClick={() => router.back()} className="text-slate-400 hover:text-white text-sm mb-8 flex items-center gap-1 transition-colors">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 12H5m7-7l-7 7 7 7" /></svg>
                    Zpět
                </button>

                <h1 className="text-3xl sm:text-4xl font-bold mb-2">Dokončení objednávky</h1>
                <p className="text-slate-400 mb-8">Vyplňte fakturační údaje a zvolte způsob platby</p>

                <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-5 gap-8">
                    {/* Honeypot — invisible to humans */}
                    <div className="absolute" style={{ left: "-9999px", top: "-9999px" }} aria-hidden="true">
                        <label>
                            Nechte prázdné
                            <input
                                type="text"
                                tabIndex={-1}
                                autoComplete="off"
                                value={honeypot}
                                onChange={(e) => setHoneypot(e.target.value)}
                            />
                        </label>
                    </div>

                    {/* Left — billing form */}
                    <div className="lg:col-span-3 space-y-6">
                        {/* 1. IČO — first, with ARES auto-fill */}
                        <div className="bg-white/[0.03] border border-white/[0.08] rounded-2xl p-6">
                            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" /></svg>
                                Identifikace firmy
                            </h2>

                            <div>
                                <label className="block text-sm text-slate-400 mb-1">IČO — zadejte a údaje se načtou automaticky z ARES</label>
                                <div className="relative">
                                    <input
                                        type="text"
                                        inputMode="numeric"
                                        maxLength={8}
                                        value={ico}
                                        onChange={(e) => handleIcoChange(e.target.value)}
                                        placeholder="např. 04291247"
                                        className={`${inputClass} ${aresFilled ? "border-emerald-500/40 bg-emerald-500/5" : ""} ${aresError ? "border-red-500/40" : ""}`}
                                    />
                                    {aresLoading && (
                                        <div className="absolute right-3 top-1/2 -translate-y-1/2">
                                            <div className="w-5 h-5 border-2 border-fuchsia-500 border-t-transparent rounded-full animate-spin" />
                                        </div>
                                    )}
                                    {aresFilled && !aresLoading && (
                                        <div className="absolute right-3 top-1/2 -translate-y-1/2 text-emerald-400">
                                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 6L9 17l-5-5" /></svg>
                                        </div>
                                    )}
                                </div>
                                {aresError && (
                                    <p className="text-xs text-red-400 mt-1">{aresError}</p>
                                )}
                                {aresFilled && (
                                    <p className="text-xs text-emerald-400 mt-1">Údaje načteny z ARES ✓</p>
                                )}
                            </div>
                        </div>

                        {/* 2. Company details (auto-filled from ARES) */}
                        <div className="bg-white/[0.03] border border-white/[0.08] rounded-2xl p-6">
                            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M19 21V5a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v5m-4 0h4" /></svg>
                                Fakturační údaje
                                {aresFilled && <span className="text-xs bg-emerald-500/15 text-emerald-400 px-2 py-0.5 rounded-full ml-auto">z ARES</span>}
                            </h2>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm text-slate-400 mb-1">Název firmy / Jméno *</label>
                                    <input
                                        type="text"
                                        required
                                        value={company}
                                        onChange={(e) => setCompany(e.target.value)}
                                        placeholder="Vaše firma s.r.o."
                                        className={inputClass}
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm text-slate-400 mb-1">DIČ</label>
                                    <input
                                        type="text"
                                        value={dic}
                                        onChange={(e) => setDic(e.target.value)}
                                        placeholder="CZ04291247"
                                        className={inputClass}
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm text-slate-400 mb-1">Ulice a číslo *</label>
                                    <input
                                        type="text"
                                        required
                                        value={street}
                                        onChange={(e) => setStreet(e.target.value)}
                                        placeholder="Hlavní 123/4"
                                        className={inputClass}
                                    />
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm text-slate-400 mb-1">Město *</label>
                                        <input
                                            type="text"
                                            required
                                            value={city}
                                            onChange={(e) => setCity(e.target.value)}
                                            placeholder="Praha"
                                            className={inputClass}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm text-slate-400 mb-1">PSČ *</label>
                                        <input
                                            type="text"
                                            required
                                            value={zip}
                                            onChange={(e) => setZip(e.target.value)}
                                            placeholder="110 00"
                                            className={inputClass}
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* 3. Contact section */}
                        <div className="bg-white/[0.03] border border-white/[0.08] rounded-2xl p-6">
                            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                                Kontakt
                            </h2>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm text-slate-400 mb-1">E-mail *</label>
                                    <input
                                        type="email"
                                        required
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        placeholder="jan.novak@vase-firma.cz"
                                        className={inputClass}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-slate-400 mb-1">Telefon</label>
                                    <input
                                        type="tel"
                                        value={phone}
                                        onChange={(e) => setPhone(e.target.value)}
                                        placeholder="+420 777 123 456"
                                        className={inputClass}
                                    />
                                </div>
                            </div>
                        </div>

                        {/* 4. Payment method */}
                        <div className="bg-white/[0.03] border border-white/[0.08] rounded-2xl p-6">
                            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" /></svg>
                                Způsob platby
                            </h2>

                            <div className="space-y-3">
                                <button
                                    type="button"
                                    onClick={() => setGateway("stripe")}
                                    className={`w-full flex items-center gap-4 p-4 rounded-xl border transition-all ${gateway === "stripe"
                                        ? "bg-fuchsia-500/10 border-fuchsia-500/40"
                                        : "bg-white/[0.02] border-white/[0.08] hover:bg-white/[0.04]"
                                        }`}
                                >
                                    <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${gateway === "stripe" ? "border-fuchsia-500" : "border-slate-500"
                                        }`}>
                                        {gateway === "stripe" && <div className="w-2.5 h-2.5 rounded-full bg-fuchsia-500" />}
                                    </div>
                                    <div className="flex-1 text-left">
                                        <p className="font-medium text-sm">Platební karta</p>
                                        <p className="text-xs text-slate-400">Visa, Mastercard — okamžité zpracování</p>
                                    </div>
                                    <span className="text-xs bg-emerald-500/15 text-emerald-400 px-2 py-0.5 rounded-full">Doporučeno</span>
                                </button>

                                <button
                                    type="button"
                                    onClick={() => setGateway("bank_transfer")}
                                    className={`w-full flex items-center gap-4 p-4 rounded-xl border transition-all ${gateway === "bank_transfer"
                                        ? "bg-fuchsia-500/10 border-fuchsia-500/40"
                                        : "bg-white/[0.02] border-white/[0.08] hover:bg-white/[0.04]"
                                        }`}
                                >
                                    <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${gateway === "bank_transfer" ? "border-fuchsia-500" : "border-slate-500"
                                        }`}>
                                        {gateway === "bank_transfer" && <div className="w-2.5 h-2.5 rounded-full bg-fuchsia-500" />}
                                    </div>
                                    <div className="flex-1 text-left">
                                        <p className="font-medium text-sm">Bankovní převod</p>
                                        <p className="text-xs text-slate-400">Proforma faktura — aktivace po připsání platby</p>
                                    </div>
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Right — order summary */}
                    <div className="lg:col-span-2">
                        <div className="bg-white/[0.03] border border-white/[0.08] rounded-2xl p-6 sticky top-8">
                            <h2 className="text-lg font-semibold mb-4">Shrnutí objednávky</h2>

                            {/* Plan badge */}
                            <div className="flex items-center gap-3 mb-4 pb-4 border-b border-white/[0.06]">
                                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-fuchsia-500/20 to-purple-500/20 border border-fuchsia-500/30 flex items-center justify-center">
                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-fuchsia-400"><path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
                                </div>
                                <div>
                                    <p className="font-bold text-white">AIshield {plan.name}</p>
                                    <p className="text-xs text-slate-400">Jednorázová licence</p>
                                </div>
                            </div>

                            {/* Features */}
                            <ul className="space-y-2 mb-6">
                                {plan.features.map((f) => (
                                    <li key={f} className="flex items-start gap-2 text-sm text-slate-300">
                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="text-emerald-400 mt-0.5 flex-shrink-0"><path d="M20 6L9 17l-5-5" /></svg>
                                        {f}
                                    </li>
                                ))}
                            </ul>

                            {/* Slevový kód */}
                            <div className="border-t border-white/[0.06] pt-4 mb-4">
                                <label className="block text-sm text-slate-400 mb-2">Slevový kód</label>
                                {voucherApplied ? (
                                    <div className="flex items-center gap-2 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30">
                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="text-emerald-400 flex-shrink-0"><path d="M20 6L9 17l-5-5" /></svg>
                                        <span className="text-sm text-emerald-300 flex-1">{voucherMessage}</span>
                                        <button type="button" onClick={handleVoucherRemove} className="text-slate-400 hover:text-red-400 transition-colors">
                                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 6L6 18M6 6l12 12" /></svg>
                                        </button>
                                    </div>
                                ) : (
                                    <div className="flex gap-2">
                                        <input
                                            type="text"
                                            value={voucherCode}
                                            onChange={(e) => { setVoucherCode(e.target.value.toUpperCase()); setVoucherError(null); }}
                                            placeholder="Zadejte kód"
                                            className="flex-1 bg-white/[0.04] border border-white/[0.1] rounded-xl px-3 py-2.5 text-white text-sm outline-none focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/25 transition-all placeholder:text-slate-600 font-mono tracking-wider"
                                        />
                                        <button
                                            type="button"
                                            onClick={handleVoucherApply}
                                            disabled={voucherLoading || !voucherCode.trim()}
                                            className="px-4 py-2.5 rounded-xl bg-white/[0.06] border border-white/[0.1] text-sm text-white hover:bg-white/[0.1] transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                                        >
                                            {voucherLoading ? (
                                                <div className="w-4 h-4 border-2 border-fuchsia-500 border-t-transparent rounded-full animate-spin" />
                                            ) : "Uplatnit"}
                                        </button>
                                    </div>
                                )}
                                {voucherError && (
                                    <p className="text-xs text-red-400 mt-1.5">{voucherError}</p>
                                )}
                            </div>

                            {/* Price */}
                            <div className="border-t border-white/[0.06] pt-4 mb-6">
                                {voucherApplied && voucherDiscount === 100 ? (
                                    <>
                                        <div className="flex justify-between text-sm text-slate-500 mb-1">
                                            <span>Původní cena</span>
                                            <span className="line-through">{plan.price.toLocaleString("cs-CZ")} Kč</span>
                                        </div>
                                        <div className="flex justify-between text-sm text-emerald-400 mb-2">
                                            <span>Sleva 100 %</span>
                                            <span>−{plan.price.toLocaleString("cs-CZ")} Kč</span>
                                        </div>
                                        <div className="flex justify-between text-lg font-bold border-t border-white/[0.06] pt-2">
                                            <span>Celkem</span>
                                            <span className="text-emerald-400">ZDARMA</span>
                                        </div>
                                    </>
                                ) : (
                                    <>
                                        <div className="flex justify-between text-sm text-slate-400 mb-1">
                                            <span>Cena bez DPH</span>
                                            <span>{Math.round(plan.price / 1.21).toLocaleString("cs-CZ")} Kč</span>
                                        </div>
                                        <div className="flex justify-between text-sm text-slate-400 mb-2">
                                            <span>DPH 21 %</span>
                                            <span>{(plan.price - Math.round(plan.price / 1.21)).toLocaleString("cs-CZ")} Kč</span>
                                        </div>
                                        <div className="flex justify-between text-lg font-bold border-t border-white/[0.06] pt-2">
                                            <span>Celkem</span>
                                            <span className="text-fuchsia-400">{plan.price.toLocaleString("cs-CZ")} Kč</span>
                                        </div>
                                    </>
                                )}
                            </div>

                            {/* Submit */}
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full py-3.5 rounded-xl bg-gradient-to-r from-fuchsia-600 to-purple-600 text-white font-semibold transition-all hover:shadow-lg hover:shadow-fuchsia-500/25 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {loading ? (
                                    <span className="flex items-center justify-center gap-2">
                                        <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" className="opacity-25" /><path d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" fill="currentColor" className="opacity-75" /></svg>
                                        Zpracovávám…
                                    </span>
                                ) : voucherApplied && voucherDiscount === 100 ? (
                                    "Dokončit objednávku zdarma"
                                ) : gateway === "bank_transfer" ? (
                                    "Odeslat objednávku"
                                ) : (
                                    "Pokračovat k platbě"
                                )}
                            </button>

                            {/* Error */}
                            {error && (
                                <div className="mt-3 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-300 text-xs">
                                    {error}
                                </div>
                            )}

                            {/* Trust badges */}
                            <div className="mt-4 flex items-center justify-center gap-4 text-xs text-slate-500">
                                <span className="flex items-center gap-1">
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
                                    Zabezpečená platba
                                </span>
                                <span className="flex items-center gap-1">
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 12l2 2 4-4" /><circle cx="12" cy="12" r="10" /></svg>
                                    SSL šifrování
                                </span>
                            </div>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default function ObjednavkaPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen bg-slate-950 flex items-center justify-center">
                <div className="w-8 h-8 border-2 border-fuchsia-500 border-t-transparent rounded-full animate-spin" />
            </div>
        }>
            <CheckoutInner />
        </Suspense>
    );
}
