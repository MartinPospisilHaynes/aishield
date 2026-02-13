"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { adminLogin, isAdminLoggedIn } from "@/lib/admin-api";
import { createClient } from "@/lib/supabase-browser";

export default function AdminLoginPage() {
    const router = useRouter();
    const supabase = createClient();

    // Step 1 = Supabase login, Step 2 = CRM password
    const [step, setStep] = useState<1 | 2>(1);

    // Step 1 fields
    const [email, setEmail] = useState("");
    const [supabasePassword, setSupabasePassword] = useState("");
    const [showSupabasePassword, setShowSupabasePassword] = useState(false);

    // Step 2 fields
    const [adminUser, setAdminUser] = useState("ADMIN");
    const [adminPassword, setAdminPassword] = useState("");
    const [showAdminPassword, setShowAdminPassword] = useState(false);

    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    // Check if already fully logged in
    useEffect(() => {
        (async () => {
            const { data: { user } } = await supabase.auth.getUser();
            if (user && isAdminLoggedIn()) {
                router.replace("/admin");
            } else if (user) {
                // Supabase session exists, skip to step 2
                setStep(2);
            }
        })();
    }, [router, supabase]);

    // Eye toggle icon component
    function EyeToggle({ show, onToggle }: { show: boolean; onToggle: () => void }) {
        return (
            <button type="button" onClick={onToggle} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors p-1" tabIndex={-1}>
                {show ? (
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 0 0 1.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.451 10.451 0 0 1 12 4.5c4.756 0 8.773 3.162 10.065 7.498a10.522 10.522 0 0 1-4.293 5.774M6.228 6.228 3 3m3.228 3.228 3.65 3.65m7.894 7.894L21 21m-3.228-3.228-3.65-3.65m0 0a3 3 0 1 0-4.243-4.243m4.242 4.242L9.88 9.88" /></svg>
                ) : (
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" /></svg>
                )}
            </button>
        );
    }

    // Step 1: Supabase login
    async function handleSupabaseLogin(e: React.FormEvent) {
        e.preventDefault();
        setError("");
        setLoading(true);
        try {
            const { error: authError } = await supabase.auth.signInWithPassword({ email, password: supabasePassword });
            if (authError) {
                setError(authError.message === "Invalid login credentials" ? "Nesprávný email nebo heslo." : authError.message);
                return;
            }
            setStep(2);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Chyba přihlášení");
        } finally {
            setLoading(false);
        }
    }

    // Step 2: CRM admin login
    async function handleAdminLogin(e: React.FormEvent) {
        e.preventDefault();
        setError("");
        setLoading(true);
        try {
            await adminLogin(adminUser, adminPassword);
            router.push("/admin");
        } catch (err) {
            setError(err instanceof Error ? err.message : "Nesprávné admin heslo");
        } finally {
            setLoading(false);
        }
    }

    const inputCls = "w-full bg-black/30 border border-white/10 rounded-xl px-4 py-3 pr-12 text-white placeholder-gray-500 focus:border-cyan-500/50 focus:outline-none focus:ring-1 focus:ring-cyan-500/30 transition-all";

    return (
        <div className="min-h-screen bg-[#0f172a] flex items-center justify-center px-4">
            <div className="w-full max-w-md">
                <div className="text-center mb-8">
                    <div className="text-5xl mb-4">🛡️</div>
                    <h1 className="text-3xl font-bold text-white">AIshield Admin</h1>
                    <p className="text-gray-400 mt-2">Řídící panel systému</p>
                </div>

                {/* Step indicator */}
                <div className="flex items-center justify-center gap-3 mb-6">
                    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${step === 1 ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30" : "bg-green-500/20 text-green-400 border border-green-500/30"}`}>
                        {step > 1 ? "✓" : "1"} Účet
                    </div>
                    <div className="w-6 h-px bg-white/20" />
                    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${step === 2 ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30" : "bg-white/5 text-gray-500 border border-white/10"}`}>
                        2 Admin
                    </div>
                </div>

                {step === 1 ? (
                    <form onSubmit={handleSupabaseLogin} className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8 space-y-6">
                        <p className="text-sm text-gray-400 text-center">
                            Přihlaste se svým admin účtem
                        </p>

                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">Admin Email</label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className={inputCls}
                                placeholder="martin@desperados-design.cz"
                                autoFocus
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">Heslo účtu</label>
                            <div className="relative">
                                <input
                                    type={showSupabasePassword ? "text" : "password"}
                                    value={supabasePassword}
                                    onChange={(e) => setSupabasePassword(e.target.value)}
                                    className={inputCls}
                                    placeholder="••••••••"
                                    required
                                />
                                <EyeToggle show={showSupabasePassword} onToggle={() => setShowSupabasePassword(!showSupabasePassword)} />
                            </div>
                        </div>

                        {error && (
                            <div className="bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 text-red-400 text-sm">
                                ❌ {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={loading || !email || !supabasePassword}
                            className="w-full py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-cyan-500 to-fuchsia-500 hover:from-cyan-400 hover:to-fuchsia-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg shadow-cyan-500/20"
                        >
                            {loading ? "⏳ Ověřuji..." : "Pokračovat →"}
                        </button>
                    </form>
                ) : (
                    <form onSubmit={handleAdminLogin} className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8 space-y-6">
                        <p className="text-sm text-gray-400 text-center">
                            Zadejte administrátorské přístupové údaje
                        </p>

                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">Admin uživatel</label>
                            <input
                                type="text"
                                value={adminUser}
                                onChange={(e) => setAdminUser(e.target.value)}
                                className={inputCls}
                                placeholder="ADMIN"
                                autoFocus
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">Admin heslo</label>
                            <div className="relative">
                                <input
                                    type={showAdminPassword ? "text" : "password"}
                                    value={adminPassword}
                                    onChange={(e) => setAdminPassword(e.target.value)}
                                    className={inputCls}
                                    placeholder="••••••••"
                                    required
                                />
                                <EyeToggle show={showAdminPassword} onToggle={() => setShowAdminPassword(!showAdminPassword)} />
                            </div>
                        </div>

                        {error && (
                            <div className="bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 text-red-400 text-sm">
                                ❌ {error}
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={loading || !adminUser || !adminPassword}
                            className="w-full py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-cyan-500 to-fuchsia-500 hover:from-cyan-400 hover:to-fuchsia-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg shadow-cyan-500/20"
                        >
                            {loading ? "⏳ Přihlašuji..." : "🔐 Vstoupit do Adminu"}
                        </button>

                        <button
                            type="button"
                            onClick={() => { setStep(1); setError(""); }}
                            className="w-full text-sm text-gray-500 hover:text-gray-300 transition-colors"
                        >
                            ← Zpět na přihlášení
                        </button>
                    </form>
                )}

                <p className="text-center text-gray-500 text-xs mt-6">
                    AIshield.cz — AI Act Compliance Platform
                </p>
            </div>
        </div>
    );
}
