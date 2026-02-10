"use client";

import { useState } from "react";
import { createClient } from "@/lib/supabase-browser";

export default function ZapomenuteHesloPage() {
    const [email, setEmail] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);
    const supabase = createClient();

    async function handleReset(e: React.FormEvent) {
        e.preventDefault();
        setLoading(true);
        setError("");

        const { error } = await supabase.auth.resetPasswordForEmail(email, {
            redirectTo: `${window.location.origin}/auth/callback?next=/nove-heslo`,
        });

        if (error) {
            setError(error.message);
            setLoading(false);
            return;
        }

        setSuccess(true);
        setLoading(false);
    }

    return (
        <section className="py-20 relative">
            {/* BG glow */}
            <div className="absolute inset-0 -z-10">
                <div className="absolute top-[20%] left-[40%] h-[400px] w-[400px] rounded-full bg-fuchsia-600/8 blur-[120px]" />
            </div>

            <div className="mx-auto max-w-md px-6">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-extrabold">Zapomenuté heslo</h1>
                    <p className="mt-2 text-sm text-slate-400">
                        Zadejte svůj email a pošleme vám odkaz pro obnovení hesla.
                    </p>
                </div>

                <div className="glass">
                    {success ? (
                        <div className="text-center space-y-4">
                            <div className="mx-auto w-16 h-16 rounded-full bg-green-500/10 border border-green-500/30 flex items-center justify-center">
                                <svg className="w-8 h-8 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                </svg>
                            </div>
                            <h2 className="text-xl font-bold text-white">Email odeslán</h2>
                            <p className="text-sm text-slate-400">
                                Pokud existuje účet s emailem <span className="text-white font-medium">{email}</span>,
                                obdržíte odkaz pro obnovení hesla. Zkontrolujte i složku spam.
                            </p>
                            <a
                                href="/login"
                                className="inline-block mt-4 text-sm text-neon-fuchsia hover:text-fuchsia-300 transition-colors font-medium"
                            >
                                ← Zpět na přihlášení
                            </a>
                        </div>
                    ) : (
                        <form className="space-y-5" onSubmit={handleReset}>
                            {error && (
                                <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                                    {error}
                                </div>
                            )}

                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                                    Email
                                </label>
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="vas@email.cz"
                                    required
                                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3
                                        text-white placeholder:text-slate-500
                                        focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/30
                                        transition-all"
                                />
                            </div>

                            <button
                                type="submit"
                                disabled={loading}
                                className="btn-primary w-full py-3.5 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {loading ? "Odesílání..." : "Obnovit heslo"}
                            </button>
                        </form>
                    )}

                    {!success && (
                        <div className="mt-6 text-center">
                            <a
                                href="/login"
                                className="text-sm text-slate-500 hover:text-slate-300 transition-colors"
                            >
                                ← Zpět na přihlášení
                            </a>
                        </div>
                    )}
                </div>
            </div>
        </section>
    );
}
