"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase-browser";

export default function NoveHesloPage() {
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);
    const [sessionReady, setSessionReady] = useState(false);
    const router = useRouter();
    const supabase = createClient();

    useEffect(() => {
        // Check if user has a valid session (from the reset link callback)
        supabase.auth.getSession().then(({ data: { session } }) => {
            if (session) {
                setSessionReady(true);
            } else {
                setError("Neplatný nebo vypršený odkaz. Požádejte o nový odkaz pro obnovení hesla.");
            }
        });
    }, [supabase]);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setError("");

        if (password !== confirmPassword) {
            setError("Hesla se neshodují.");
            return;
        }

        if (password.length < 6) {
            setError("Heslo musí mít alespoň 6 znaků.");
            return;
        }

        setLoading(true);

        const { error } = await supabase.auth.updateUser({ password });

        if (error) {
            setError(error.message);
            setLoading(false);
            return;
        }

        setSuccess(true);
        setLoading(false);

        // Redirect to dashboard after 3 seconds
        setTimeout(() => {
            router.push("/dashboard");
        }, 3000);
    }

    return (
        <section className="py-20 relative">
            {/* BG glow */}
            <div className="absolute inset-0 -z-10">
                <div className="absolute top-[20%] left-[40%] h-[400px] w-[400px] rounded-full bg-fuchsia-600/8 blur-[120px]" />
            </div>

            <div className="mx-auto max-w-md px-6">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-extrabold">Nastavení nového hesla</h1>
                    <p className="mt-2 text-sm text-slate-400">
                        Zadejte své nové heslo pro přihlášení.
                    </p>
                </div>

                <div className="glass">
                    {success ? (
                        <div className="text-center space-y-4">
                            <div className="mx-auto w-16 h-16 rounded-full bg-green-500/10 border border-green-500/30 flex items-center justify-center">
                                <svg className="w-8 h-8 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                            </div>
                            <h2 className="text-xl font-bold text-white">Heslo změněno</h2>
                            <p className="text-sm text-slate-400">
                                Vaše heslo bylo úspěšně změněno. Za okamžik budete přesměrováni na nástěnku.
                            </p>
                        </div>
                    ) : (
                        <form className="space-y-5" onSubmit={handleSubmit}>
                            {error && (
                                <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                                    {error}
                                </div>
                            )}

                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                                    Nové heslo
                                </label>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="••••••••"
                                    required
                                    minLength={6}
                                    disabled={!sessionReady}
                                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3
                                        text-white placeholder:text-slate-500
                                        focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/30
                                        transition-all disabled:opacity-50"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                                    Potvrzení nového hesla
                                </label>
                                <input
                                    type="password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    placeholder="••••••••"
                                    required
                                    minLength={6}
                                    disabled={!sessionReady}
                                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3
                                        text-white placeholder:text-slate-500
                                        focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/30
                                        transition-all disabled:opacity-50"
                                />
                            </div>

                            <button
                                type="submit"
                                disabled={loading || !sessionReady}
                                className="btn-primary w-full py-3.5 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {loading ? "Ukládání..." : "Nastavit nové heslo"}
                            </button>
                        </form>
                    )}

                    {!success && !sessionReady && (
                        <div className="mt-6 text-center">
                            <a
                                href="/zapomenute-heslo"
                                className="text-sm text-neon-fuchsia hover:text-fuchsia-300 transition-colors font-medium"
                            >
                                Požádat o nový odkaz
                            </a>
                        </div>
                    )}
                </div>
            </div>
        </section>
    );
}
