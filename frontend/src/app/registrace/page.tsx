"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { createClient } from "@/lib/supabase-browser";
import { Suspense } from "react";

function RegistraceInner() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [companyName, setCompanyName] = useState("");
    const [ico, setIco] = useState("");
    const [webUrl, setWebUrl] = useState("");
    const [gdprConsent, setGdprConsent] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);
    const [partner, setPartner] = useState<string | null>(null);
    const router = useRouter();
    const searchParams = useSearchParams();
    const supabase = createClient();

    useEffect(() => {
        const p = searchParams.get("partner");
        if (p) setPartner(p);
    }, [searchParams]);

    const redirectTo = searchParams.get("redirect") || "/dashboard";

    async function handleRegister(e: React.FormEvent) {
        e.preventDefault();
        setLoading(true);
        setError("");

        if (password !== confirmPassword) {
            setError("Hesla se neshodují");
            setLoading(false);
            return;
        }

        if (!gdprConsent) {
            setError("Pro registraci je nutný souhlas se zpracováním údajů");
            setLoading(false);
            return;
        }

        // 1. Registrace v Supabase Auth
        const { data, error: authError } = await supabase.auth.signUp({
            email,
            password,
            options: {
                data: {
                    company_name: companyName,
                    ico: ico || undefined,
                    web_url: webUrl || undefined,
                    gdpr_consent: true,
                    gdpr_consent_at: new Date().toISOString(),
                    partner: partner || undefined,
                    utm_source: searchParams.get("utm_source") || undefined,
                    utm_medium: searchParams.get("utm_medium") || undefined,
                    utm_campaign: searchParams.get("utm_campaign") || undefined,
                },
                emailRedirectTo: `${window.location.origin}/auth/callback`,
            },
        });

        if (authError) {
            setError(
                authError.message === "User already registered"
                    ? "Tento email je už registrovaný. Zkuste se přihlásit."
                    : authError.message,
            );
            setLoading(false);
            return;
        }

        // 2. Pokud Supabase potvrdil email automaticky (dev mode), jít na dashboard
        if (data.session) {
            router.push(redirectTo);
            return;
        }

        // 3. Jinak zobrazit hlášku o potvrzení emailu
        setSuccess(true);
        setLoading(false);
    }

    if (success) {
        return (
            <section className="py-20 relative">
                <div className="absolute inset-0 -z-10">
                    <div className="absolute top-[20%] left-[40%] h-[400px] w-[400px] rounded-full bg-cyan-500/8 blur-[120px]" />
                </div>
                <div className="mx-auto max-w-md px-6">
                    <div className="glass text-center py-12">
                        <div className="mx-auto mb-4 w-16 h-16 rounded-2xl bg-green-500/10 border border-green-500/20 flex items-center justify-center">
                            <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                            </svg>
                        </div>
                        <h2 className="text-xl font-bold mb-2">Zkontrolujte email</h2>
                        <p className="text-slate-400 text-sm">
                            Na adresu <strong className="text-slate-200">{email}</strong> jsme
                            odeslali potvrzovací odkaz. Klikněte na něj pro aktivaci účtu.
                        </p>
                        <a href="/login" className="btn-secondary mt-6 inline-flex">
                            Zpět na přihlášení
                        </a>
                    </div>
                </div>
            </section>
        );
    }

    return (
        <section className="py-20 relative">
            {/* BG glow */}
            <div className="absolute inset-0 -z-10">
                <div className="absolute top-[20%] right-[30%] h-[400px] w-[400px] rounded-full bg-cyan-500/8 blur-[120px]" />
            </div>

            <div className="mx-auto max-w-md px-6">
                <div className="text-center mb-8">
                    {partner === "desperados" && (
                        <div className="mb-4 inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-sm font-medium">
                            🤝 Klient Desperados Design — sleva 20 %
                        </div>
                    )}
                    <h1 className="text-3xl font-extrabold">
                        Registrace
                    </h1>
                    <p className="mt-2 text-sm text-slate-400">
                        Vytvořte si účet a získejte přístup k plné compliance analýze.
                    </p>
                </div>

                <div className="glass">
                    <form className="space-y-5" onSubmit={handleRegister}>
                        {error && (
                            <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                                {error}
                            </div>
                        )}

                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-1.5">
                                Název firmy
                            </label>
                            <input
                                type="text"
                                value={companyName}
                                onChange={(e) => setCompanyName(e.target.value)}
                                placeholder="Vaše firma s.r.o."
                                required
                                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3
                                    text-white placeholder:text-slate-500
                                    focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/30
                                    transition-all"
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                                    IČO <span className="text-slate-500">(volitelné)</span>
                                </label>
                                <input
                                    type="text"
                                    value={ico}
                                    onChange={(e) => setIco(e.target.value.replace(/\D/g, "").slice(0, 8))}
                                    placeholder="12345678"
                                    maxLength={8}
                                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3
                                        text-white placeholder:text-slate-500
                                        focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/30
                                        transition-all"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-1.5">
                                    Web <span className="text-slate-500">(volitelné)</span>
                                </label>
                                <input
                                    type="url"
                                    value={webUrl}
                                    onChange={(e) => setWebUrl(e.target.value)}
                                    placeholder="https://vasefirma.cz"
                                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3
                                        text-white placeholder:text-slate-500
                                        focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/30
                                        transition-all"
                                />
                            </div>
                        </div>

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
                                placeholder="Minimálně 6 znaků"
                                required
                                minLength={6}
                                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3
                                    text-white placeholder:text-slate-500
                                    focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/30
                                    transition-all"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-1.5">
                                Potvrdit heslo
                            </label>
                            <input
                                type="password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                placeholder="Zadejte heslo znovu"
                                required
                                minLength={6}
                                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3
                                    text-white placeholder:text-slate-500
                                    focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/30
                                    transition-all"
                            />
                        </div>

                        {/* GDPR souhlas */}
                        <label className="flex items-start gap-3 cursor-pointer group">
                            <input
                                type="checkbox"
                                checked={gdprConsent}
                                onChange={(e) => setGdprConsent(e.target.checked)}
                                className="mt-1 h-4 w-4 rounded border-white/20 bg-white/5 text-fuchsia-500 
                                    focus:ring-fuchsia-500/50 focus:ring-offset-0 cursor-pointer"
                            />
                            <span className="text-xs text-slate-400 leading-relaxed group-hover:text-slate-300 transition-colors">
                                Souhlasím se{" "}
                                <a href="/privacy" target="_blank" className="text-fuchsia-400 hover:text-fuchsia-300 underline">
                                    zpracováním osobních údajů
                                </a>
                                {" "}a{" "}
                                <a href="/terms" target="_blank" className="text-fuchsia-400 hover:text-fuchsia-300 underline">
                                    obchodními podmínkami
                                </a>
                                . Vaše data zpracováváme výhradně pro poskytování služby
                                AI Act compliance v souladu s GDPR.
                            </span>
                        </label>

                        <button
                            type="submit"
                            disabled={loading || !gdprConsent}
                            className="btn-primary w-full py-3.5 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? "Registruji..." : "Vytvořit účet"}
                        </button>
                    </form>

                    <div className="mt-6 text-center">
                        <p className="text-sm text-slate-500">
                            Už máte účet?{" "}
                            <a href="/login" className="text-neon-fuchsia hover:text-fuchsia-300 transition-colors font-medium">
                                Přihlaste se
                            </a>
                        </p>
                    </div>
                </div>
            </div>
        </section>
    );
}

export default function RegistracePage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-cyan-400 animate-pulse">Načítám...</div>
            </div>
        }>
            <RegistraceInner />
        </Suspense>
    );
}
