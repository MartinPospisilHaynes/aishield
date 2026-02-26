"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase-browser";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const router = useRouter();
    const supabase = createClient();

    async function handleLogin(e: React.FormEvent) {
        e.preventDefault();
        setLoading(true);
        setError("");

        const { error } = await supabase.auth.signInWithPassword({
            email,
            password,
        });

        if (error) {
            setError(
                error.message === "Invalid login credentials"
                    ? "Nesprávný email nebo heslo."
                    : error.message,
            );
            setLoading(false);
            return;
        }

        router.push("/dashboard");
    }

    return (
        <section className="py-20 relative">
            {/* BG glow */}
            <div className="absolute inset-0 -z-10">
                <div className="absolute top-[20%] left-[40%] h-[400px] w-[400px] rounded-full bg-fuchsia-600/8 blur-[120px]" />
            </div>

            <div className="mx-auto max-w-md px-6">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-extrabold">
                        Přihlášení
                    </h1>
                    <p className="mt-2 text-sm text-slate-400">
                        Přihlaste se do svého AIshield účtu.
                    </p>
                </div>

                <div className="glass">
                    <form className="space-y-5" onSubmit={handleLogin}>
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

                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-1.5">
                                Heslo
                            </label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                required
                                minLength={6}
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
                            {loading ? "Přihlašování..." : "Přihlásit se"}
                        </button>
                    </form>

                    <div className="mt-6 text-center">
                        <p className="text-sm text-slate-500">
                            Nemáte účet?{" "}
                            <a href="/registrace" className="text-neon-fuchsia hover:text-fuchsia-300 transition-colors font-medium">
                                Zaregistrujte se
                            </a>
                        </p>
                    </div>
                </div>
            </div>
        </section>
    );
}
