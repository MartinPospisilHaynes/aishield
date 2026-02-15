"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { createClient } from "@/lib/supabase-browser";
import { useAnalytics } from "@/lib/analytics";

function LoginForm() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [oauthLoading, setOauthLoading] = useState(false);
    const [error, setError] = useState("");
    const router = useRouter();
    const searchParams = useSearchParams();
    const redirect = searchParams.get('redirect') || '/dashboard';
    const authError = searchParams.get('error');
    const verified = searchParams.get('verified');
    const supabase = createClient();
    const { track } = useAnalytics();

    // Show auth callback errors or verification success
    useEffect(() => {
        if (authError === 'auth_callback_failed') {
            setError('Ověření se nezdařilo. Zkuste se prosím přihlásit znovu.');
        }
    }, [authError]);

    async function handleGoogleLogin() {
        setOauthLoading(true);
        setError("");
        const { error } = await supabase.auth.signInWithOAuth({
            provider: "google",
            options: {
                redirectTo: `${window.location.origin}/auth/callback?next=${encodeURIComponent(redirect)}`,
            },
        });
        if (error) {
            setError(error.message);
            setOauthLoading(false);
        }
    }

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

        router.push(redirect);
        track("login_completed", { method: "email" });
    }

    return (
        <section className="py-20 relative">
            {/* BG glow */}
            <div className="absolute inset-0 -z-10">
                <div className="absolute top-[20%] left-[40%] h-[400px] w-[400px] rounded-full bg-fuchsia-600/8 blur-[120px]" />
            </div>

            <div className="mx-auto max-w-md px-4 sm:px-6">
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
                        {verified && (
                            <div className="rounded-xl border border-green-500/30 bg-green-500/10 px-4 py-3 text-sm text-green-300">
                                ✓ Email úspěšně ověřen! Nyní se přihlaste.
                            </div>
                        )}
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
                            <div className="relative">
                                <input
                                    type={showPassword ? "text" : "password"}
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="••••••••"
                                    required
                                    minLength={6}
                                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 pr-12
                                        text-white placeholder:text-slate-500
                                        focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/30
                                        transition-all"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white transition-colors p-1"
                                    tabIndex={-1}
                                >
                                    {showPassword ? (
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 0 0 1.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.451 10.451 0 0 1 12 4.5c4.756 0 8.773 3.162 10.065 7.498a10.522 10.522 0 0 1-4.293 5.774M6.228 6.228 3 3m3.228 3.228 3.65 3.65m7.894 7.894L21 21m-3.228-3.228-3.65-3.65m0 0a3 3 0 1 0-4.243-4.243m4.242 4.242L9.88 9.88" /></svg>
                                    ) : (
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" /></svg>
                                    )}
                                </button>
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="btn-primary w-full py-3.5 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? "Přihlašování..." : "Přihlásit se"}
                        </button>
                    </form>

                    {/* Divider */}
                    <div className="relative my-6">
                        <div className="absolute inset-0 flex items-center">
                            <div className="w-full border-t border-white/[0.06]" />
                        </div>
                        <div className="relative flex justify-center text-xs">
                            <span className="bg-[#0f172a] px-3 text-slate-500">nebo</span>
                        </div>
                    </div>

                    {/* Google OAuth */}
                    <button
                        onClick={handleGoogleLogin}
                        disabled={oauthLoading}
                        className="w-full flex items-center justify-center gap-3 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-medium text-slate-200 hover:bg-white/10 hover:border-white/20 transition-all disabled:opacity-50"
                    >
                        <svg className="w-5 h-5" viewBox="0 0 24 24">
                            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
                            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                        </svg>
                        {oauthLoading ? "Přesměrování..." : "Pokračovat přes Google"}
                    </button>

                    <div className="mt-6 text-center space-y-3">
                        <p className="text-sm text-slate-500">
                            Nemáte účet?{" "}
                            <a href="/registrace" className="text-neon-fuchsia hover:text-fuchsia-300 transition-colors font-medium">
                                Zaregistrujte se
                            </a>
                        </p>
                        <p className="text-sm">
                            <a href="/zapomenute-heslo" className="text-slate-500 hover:text-slate-300 transition-colors">
                                Zapomenuté heslo?
                            </a>
                        </p>
                    </div>
                </div>
            </div>
        </section>
    );
}

export default function LoginPage() {
    return (
        <Suspense fallback={<div className="py-20 text-center text-slate-400">Načítání...</div>}>
            <LoginForm />
        </Suspense>
    );
}
