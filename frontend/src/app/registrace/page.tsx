"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { createClient } from "@/lib/supabase-browser";
import { Suspense } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://api.aishield.cz";

/** Testovací emaily — pro tyto se automaticky resetuje účet při registraci */
const TEST_EMAILS = new Set(["info@desperados-design.cz"]);

/** Normalize URL: accept "www.firma.cz" or "firma.cz" and prepend https:// */
function normalizeUrl(raw: string): string {
    const trimmed = raw.trim();
    if (!trimmed) return "";
    if (/^https?:\/\//i.test(trimmed)) return trimmed;
    return `https://${trimmed}`;
}

function RegistraceInner() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [companyName, setCompanyName] = useState("");
    const [ico, setIco] = useState("");
    const [webUrl, setWebUrl] = useState("");
    const [gdprConsent, setGdprConsent] = useState(false);
    const [loading, setLoading] = useState(false);
    const [oauthLoading, setOauthLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);
    const [testResetDone, setTestResetDone] = useState(false);
    const [partner, setPartner] = useState<string | null>(null);
    const [aresLoading, setAresLoading] = useState(false);
    const [aresStatus, setAresStatus] = useState<"idle" | "found" | "not-found">("idle");
    const router = useRouter();
    const searchParams = useSearchParams();
    const supabase = createClient();

    useEffect(() => {
        const p = searchParams.get("partner");
        if (p) setPartner(p);
    }, [searchParams]);

    const redirectTo = searchParams.get("redirect") || "/dashboard";

    // ── ARES lookup when IČO has 8 digits ──
    const lookupAres = useCallback(async (icoValue: string) => {
        if (icoValue.length !== 8) {
            setAresStatus("idle");
            return;
        }
        setAresLoading(true);
        setAresStatus("idle");
        try {
            const res = await fetch(`${API_URL}/api/ares/${icoValue}`);
            if (res.ok) {
                const data = await res.json();
                setCompanyName(data.name || "");
                setAresStatus("found");
            } else {
                setAresStatus("not-found");
            }
        } catch {
            setAresStatus("not-found");
        } finally {
            setAresLoading(false);
        }
    }, []);

    function handleIcoChange(e: React.ChangeEvent<HTMLInputElement>) {
        const cleaned = e.target.value.replace(/\D/g, "").slice(0, 8);
        setIco(cleaned);
        if (cleaned.length === 8) {
            lookupAres(cleaned);
        } else {
            setAresStatus("idle");
        }
    }

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
        const normalizedWeb = normalizeUrl(webUrl);

        // ── TESTOVACÍ REŽIM: automatický reset + auto-potvrzení ──
        const isTestEmail = TEST_EMAILS.has(email.trim().toLowerCase());
        if (isTestEmail) {
            try {
                const resetRes = await fetch(`${API_URL}/api/admin/test-reset`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        email: email.trim().toLowerCase(),
                        password,
                        web_url: normalizedWeb || "https://www.desperados-design.cz",
                    }),
                });
                if (!resetRes.ok) {
                    const detail = await resetRes.json().catch(() => ({}));
                    setError(detail.detail || "Chyba při resetu testovacího účtu");
                    setLoading(false);
                    return;
                }
                // Účet je vytvořený a auto-potvrzený → přesměrování na login
                setTestResetDone(true);
                setLoading(false);
                return;
            } catch (err) {
                setError("Nepodařilo se resetovat testovací účet. Zkuste to znovu.");
                setLoading(false);
                return;
            }
        }

        // ── NORMÁLNÍ REGISTRACE ──
        const { data, error: authError } = await supabase.auth.signUp({
            email,
            password,
            options: {
                data: {
                    company_name: companyName,
                    ico: ico || undefined,
                    web_url: normalizedWeb || undefined,
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

        // 2. Detekce už existujícího účtu — Supabase vrátí user bez identit
        //    (bezpečnostní ochrana proti zjišťování existujících emailů)
        const identities = data.user?.identities ?? [];
        if (identities.length === 0) {
            setError(
                "Tento email je už registrovaný. Přihlaste se na stránce přihlášení, " +
                "nebo použijte funkci 'Zapomenuté heslo' pro reset hesla."
            );
            setLoading(false);
            return;
        }

        // 3. Pokud Supabase potvrdil email automaticky (dev mode), jít na dashboard
        if (data.session) {
            router.push(redirectTo);
            return;
        }

        // 4. Jinak zobrazit hlášku o potvrzení emailu
        setSuccess(true);
        setLoading(false);
    }

    // ── TESTOVACÍ ÚČET: reset proběhl úspěšně ──
    if (testResetDone) {
        return (
            <section className="py-20 relative">
                <div className="absolute inset-0 -z-10">
                    <div className="absolute top-[20%] left-[40%] h-[400px] w-[400px] rounded-full bg-cyan-500/8 blur-[120px]" />
                </div>
                <div className="mx-auto max-w-md px-4 sm:px-6">
                    <div className="glass text-center py-12">
                        <div className="mx-auto mb-4 w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                            <span className="text-3xl">🧪</span>
                        </div>
                        <h2 className="text-xl font-bold mb-2 text-emerald-400">
                            Testovací účet resetován
                        </h2>
                        <p className="text-slate-400 text-sm leading-relaxed mb-2">
                            Účet <strong className="text-slate-200">{email}</strong> byl kompletně
                            vyčištěn a znovu vytvořen.
                        </p>
                        <p className="text-slate-500 text-xs mb-6">
                            Email je auto-potvrzený — žádné čekání na potvrzovací odkaz.
                            Všechna stará data (skeny, dotazník, dokumenty) byla smazána.
                        </p>

                        <div className="flex items-start gap-3 rounded-xl bg-emerald-500/8 border border-emerald-500/15 px-4 py-3 mb-4 text-left">
                            <span className="text-emerald-400 text-lg mt-0.5">✅</span>
                            <div className="text-xs text-emerald-300/80 leading-relaxed">
                                <strong className="text-emerald-300">Přihlašovací údaje:</strong>
                                <br />Email: {email}
                                <br />Heslo: zůstává stejné jak jste zadali
                            </div>
                        </div>

                        <a
                            href="/login"
                            className="btn-primary mt-4 inline-flex items-center gap-2"
                        >
                            Přihlásit se →
                        </a>
                    </div>
                </div>
            </section>
        );
    }

    if (success) {
        return (
            <section className="py-20 relative">
                <div className="absolute inset-0 -z-10">
                    <div className="absolute top-[20%] left-[40%] h-[400px] w-[400px] rounded-full bg-cyan-500/8 blur-[120px]" />
                </div>
                <div className="mx-auto max-w-md px-4 sm:px-6">
                    <div className="glass text-center py-12">
                        <div className="mx-auto mb-4 w-16 h-16 rounded-2xl bg-green-500/10 border border-green-500/20 flex items-center justify-center">
                            <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                            </svg>
                        </div>
                        <h2 className="text-xl font-bold mb-2">Zkontrolujte svůj email</h2>
                        <p className="text-slate-400 text-sm leading-relaxed">
                            Na adresu <strong className="text-slate-200">{email}</strong> jsme
                            odeslali potvrzovací odkaz. Klikněte na něj pro aktivaci účtu.
                        </p>

                        <div className="mt-5 space-y-3 text-left">
                            <div className="flex items-start gap-3 rounded-xl bg-amber-500/8 border border-amber-500/15 px-4 py-3">
                                <span className="text-amber-400 text-lg mt-0.5">⏱️</span>
                                <p className="text-xs text-amber-300/80 leading-relaxed">
                                    <strong className="text-amber-300">Doručení může trvat 1–5 minut.</strong>{" "}
                                    Mějte prosím strpení — email je na cestě.
                                </p>
                            </div>
                            <div className="flex items-start gap-3 rounded-xl bg-slate-500/8 border border-slate-500/15 px-4 py-3">
                                <span className="text-slate-400 text-lg mt-0.5">📂</span>
                                <p className="text-xs text-slate-400 leading-relaxed">
                                    <strong className="text-slate-300">Zkontrolujte složku SPAM / Hromadné.</strong>{" "}
                                    Potvrzovací email může skončit ve spamu — podívejte se i tam.
                                </p>
                            </div>
                            <div className="flex items-start gap-3 rounded-xl bg-slate-500/8 border border-slate-500/15 px-4 py-3">
                                <span className="text-slate-400 text-lg mt-0.5">🔄</span>
                                <p className="text-xs text-slate-400 leading-relaxed">
                                    Email stále nepřišel? Zkuste se{" "}
                                    <a href="/registrace" className="text-fuchsia-400 hover:underline font-medium">registrovat znovu</a>{" "}
                                    a pečlivě zkontrolujte, zda je email zadaný správně.
                                </p>
                            </div>
                        </div>

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

            <div className="mx-auto max-w-md px-4 sm:px-6">
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

                        {/* IČO — first field, triggers ARES auto-fill */}
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-1.5">
                                IČO <span className="text-slate-500">(volitelné)</span>
                            </label>
                            <div className="relative">
                                <input
                                    type="text"
                                    inputMode="numeric"
                                    value={ico}
                                    onChange={handleIcoChange}
                                    placeholder="12345678"
                                    maxLength={8}
                                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3
                                        text-white placeholder:text-slate-500
                                        focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/30
                                        transition-all"
                                />
                                {aresLoading && (
                                    <div className="absolute right-3 top-1/2 -translate-y-1/2">
                                        <svg className="animate-spin h-5 w-5 text-cyan-400" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                                        </svg>
                                    </div>
                                )}
                                {aresStatus === "found" && !aresLoading && (
                                    <div className="absolute right-3 top-1/2 -translate-y-1/2">
                                        <svg className="h-5 w-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                        </svg>
                                    </div>
                                )}
                            </div>
                            {aresStatus === "found" && (
                                <p className="mt-1 text-xs text-green-400">Firma nalezena v ARES — údaje předvyplněny</p>
                            )}
                            {aresStatus === "not-found" && (
                                <p className="mt-1 text-xs text-amber-400">IČO nebylo nalezeno v ARES — vyplňte údaje ručně</p>
                            )}
                        </div>

                        {/* Company name — auto-filled from ARES */}
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
                                className={`w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3
                                    text-white placeholder:text-slate-500
                                    focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/30
                                    transition-all ${aresStatus === "found" ? "border-green-500/30 bg-green-500/5" : ""}`}
                            />
                        </div>

                        {/* Web URL — accepts www.firma.cz, firma.cz, or full URL */}
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-1.5">
                                Web <span className="text-slate-500">(volitelné)</span>
                            </label>
                            <input
                                type="text"
                                value={webUrl}
                                onChange={(e) => setWebUrl(e.target.value)}
                                placeholder="www.vasefirma.cz"
                                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3
                                    text-white placeholder:text-slate-500
                                    focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/30
                                    transition-all"
                            />
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
                            {TEST_EMAILS.has(email.trim().toLowerCase()) && (
                                <p className="mt-1.5 text-xs text-emerald-400 flex items-center gap-1.5">
                                    <span>🧪</span>
                                    <span>
                                        <strong>Testovací režim</strong> — účet bude automaticky resetován
                                        a potvrzený bez emailu
                                    </span>
                                </p>
                            )}
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
                        onClick={async () => {
                            setOauthLoading(true);
                            setError("");
                            const { error } = await supabase.auth.signInWithOAuth({
                                provider: "google",
                                options: {
                                    redirectTo: `${window.location.origin}/auth/callback?next=${encodeURIComponent(redirectTo)}`,
                                },
                            });
                            if (error) {
                                setError(error.message);
                                setOauthLoading(false);
                            }
                        }}
                        disabled={oauthLoading}
                        className="w-full flex items-center justify-center gap-3 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-medium text-slate-200 hover:bg-white/10 hover:border-white/20 transition-all disabled:opacity-50"
                    >
                        <svg className="w-5 h-5" viewBox="0 0 24 24">
                            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
                            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
                            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                        </svg>
                        {oauthLoading ? "Přesměrování..." : "Registrovat přes Google"}
                    </button>
                    <p className="text-[10px] text-slate-600 text-center mt-2">
                        Registrací přes Google souhlasíte se zpracováním údajů a obchodními podmínkami.
                    </p>

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
