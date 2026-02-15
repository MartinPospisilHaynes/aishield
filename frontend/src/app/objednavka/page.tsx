"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { createCheckout } from "@/lib/api";

const PLANS: Record<string, { name: string; price: number; features: string[] }> = {
    basic: {
        name: "BASIC",
        price: 4999,
        features: [
            "AI Act compliance dokumenty",
            "Transparentní stránka",
            "Školící prezentace (PowerPoint)",
            "Šablona prezenční listiny",
        ],
    },
    pro: {
        name: "PRO",
        price: 14999,
        features: [
            "Vše z BASIC",
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
    const planKey = searchParams.get("plan") || "basic";
    const plan = PLANS[planKey];

    const [email, setEmail] = useState("");
    const [company, setCompany] = useState("");
    const [ico, setIco] = useState("");
    const [dic, setDic] = useState("");
    const [street, setStreet] = useState("");
    const [city, setCity] = useState("");
    const [zip, setZip] = useState("");
    const [phone, setPhone] = useState("");
    const [gateway, setGateway] = useState<Gateway>("stripe");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [userLoaded, setUserLoaded] = useState(false);

    // Load user email from supabase session
    useEffect(() => {
        (async () => {
            try {
                const { createClient } = await import("@supabase/supabase-js");
                const supabase = createClient(
                    process.env.NEXT_PUBLIC_SUPABASE_URL || "",
                    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ""
                );
                const { data: { user } } = await supabase.auth.getUser();
                if (user?.email) setEmail(user.email);
                if (!user) {
                    router.push(`/registrace?redirect=/objednavka&plan=${planKey}`);
                    return;
                }
            } catch {
                // ignore
            }
            setUserLoaded(true);
        })();
    }, [planKey, router]);

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
        setLoading(true);

        try {
            // Store billing info in localStorage for now (could be sent to backend)
            const billing = { company, ico, dic, street, city, zip, phone, email };
            localStorage.setItem("aishield_billing", JSON.stringify(billing));

            const data = await createCheckout(planKey, email, gateway);
            window.location.href = data.gateway_url;
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Nepodařilo se vytvořit platbu");
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
                    {/* Left — billing form */}
                    <div className="lg:col-span-3 space-y-6">
                        {/* Company section */}
                        <div className="bg-white/[0.03] border border-white/[0.08] rounded-2xl p-6">
                            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M19 21V5a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v5m-4 0h4" /></svg>
                                Fakturační údaje
                            </h2>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm text-slate-400 mb-1">Název firmy / Jméno *</label>
                                    <input
                                        type="text"
                                        required
                                        value={company}
                                        onChange={(e) => setCompany(e.target.value)}
                                        placeholder="AIshield s.r.o."
                                        className="w-full bg-white/[0.04] border border-white/[0.1] rounded-xl px-4 py-3 text-white text-sm outline-none focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/25 transition-all placeholder:text-slate-600"
                                    />
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm text-slate-400 mb-1">IČO</label>
                                        <input
                                            type="text"
                                            value={ico}
                                            onChange={(e) => setIco(e.target.value)}
                                            placeholder="12345678"
                                            className="w-full bg-white/[0.04] border border-white/[0.1] rounded-xl px-4 py-3 text-white text-sm outline-none focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/25 transition-all placeholder:text-slate-600"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm text-slate-400 mb-1">DIČ</label>
                                        <input
                                            type="text"
                                            value={dic}
                                            onChange={(e) => setDic(e.target.value)}
                                            placeholder="CZ12345678"
                                            className="w-full bg-white/[0.04] border border-white/[0.1] rounded-xl px-4 py-3 text-white text-sm outline-none focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/25 transition-all placeholder:text-slate-600"
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-sm text-slate-400 mb-1">Ulice a číslo *</label>
                                    <input
                                        type="text"
                                        required
                                        value={street}
                                        onChange={(e) => setStreet(e.target.value)}
                                        placeholder="Václavské náměstí 1"
                                        className="w-full bg-white/[0.04] border border-white/[0.1] rounded-xl px-4 py-3 text-white text-sm outline-none focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/25 transition-all placeholder:text-slate-600"
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
                                            className="w-full bg-white/[0.04] border border-white/[0.1] rounded-xl px-4 py-3 text-white text-sm outline-none focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/25 transition-all placeholder:text-slate-600"
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
                                            className="w-full bg-white/[0.04] border border-white/[0.1] rounded-xl px-4 py-3 text-white text-sm outline-none focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/25 transition-all placeholder:text-slate-600"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Contact section */}
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
                                        placeholder="info@firma.cz"
                                        className="w-full bg-white/[0.04] border border-white/[0.1] rounded-xl px-4 py-3 text-white text-sm outline-none focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/25 transition-all placeholder:text-slate-600"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm text-slate-400 mb-1">Telefon</label>
                                    <input
                                        type="tel"
                                        value={phone}
                                        onChange={(e) => setPhone(e.target.value)}
                                        placeholder="+420 123 456 789"
                                        className="w-full bg-white/[0.04] border border-white/[0.1] rounded-xl px-4 py-3 text-white text-sm outline-none focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/25 transition-all placeholder:text-slate-600"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Payment method */}
                        <div className="bg-white/[0.03] border border-white/[0.08] rounded-2xl p-6">
                            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" /></svg>
                                Způsob platby
                            </h2>

                            <div className="space-y-3">
                                <button
                                    type="button"
                                    onClick={() => setGateway("stripe")}
                                    className={`w-full flex items-center gap-4 p-4 rounded-xl border transition-all ${
                                        gateway === "stripe"
                                            ? "bg-fuchsia-500/10 border-fuchsia-500/40"
                                            : "bg-white/[0.02] border-white/[0.08] hover:bg-white/[0.04]"
                                    }`}
                                >
                                    <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                                        gateway === "stripe" ? "border-fuchsia-500" : "border-slate-500"
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
                                    className={`w-full flex items-center gap-4 p-4 rounded-xl border transition-all ${
                                        gateway === "bank_transfer"
                                            ? "bg-fuchsia-500/10 border-fuchsia-500/40"
                                            : "bg-white/[0.02] border-white/[0.08] hover:bg-white/[0.04]"
                                    }`}
                                >
                                    <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                                        gateway === "bank_transfer" ? "border-fuchsia-500" : "border-slate-500"
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

                            {/* Price */}
                            <div className="border-t border-white/[0.06] pt-4 mb-6">
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
