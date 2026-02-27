"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { createClient } from "@/lib/supabase-browser";
import { Suspense } from "react";
import { useAnalytics } from "@/lib/analytics";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://api.aishield.cz";

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
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [companyName, setCompanyName] = useState("");
    const [ico, setIco] = useState("");
    const [webUrl, setWebUrl] = useState("");
    const [gdprConsent, setGdprConsent] = useState(false);
    const [loading, setLoading] = useState(false);
    const [oauthLoading, setOauthLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);
    const [partner, setPartner] = useState<string | null>(null);
    const [aresLoading, setAresLoading] = useState(false);
    const [aresStatus, setAresStatus] = useState<"idle" | "found" | "not-found">("idle");
    // Anti-bot: math CAPTCHA
    const [captchaA, setCaptchaA] = useState(0);
    const [captchaB, setCaptchaB] = useState(0);
    const [captchaAnswer, setCaptchaAnswer] = useState("");
    const router = useRouter();
    const searchParams = useSearchParams();
    const supabase = createClient();
    const { track } = useAnalytics();

    useEffect(() => {
        const p = searchParams.get("partner");
        if (p) setPartner(p);
    }, [searchParams]);

    // Generate math CAPTCHA on mount
    useEffect(() => {
        setCaptchaA(Math.floor(Math.random() * 10) + 1);
        setCaptchaB(Math.floor(Math.random() * 10) + 1);
    }, []);

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
        track("registration_started", { has_ico: !!ico, has_web: !!webUrl });
        track("registration_started", { has_ico: !!ico, has_web: !!webUrl });

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

        // Anti-bot: ověření matematického příkladu
        if (parseInt(captchaAnswer, 10) !== captchaA + captchaB) {
            setError("Nesprávná odpověď na ověřovací otázku. Zkuste to znovu.");
            setLoading(false);
            // Nový příklad
            setCaptchaA(Math.floor(Math.random() * 10) + 1);
            setCaptchaB(Math.floor(Math.random() * 10) + 1);
            setCaptchaAnswer("");
            return;
        }

        // 1. Registrace v Supabase Auth
        const normalizedWeb = normalizeUrl(webUrl);
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
        track("registration_completed", { method: "email" });
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

                        {/* Otevřít schránku — detekce webmail providera */}
                        <div className="flex flex-col items-center gap-3 mt-5">
                        {(() => {
                            const domain = email.split("@")[1]?.toLowerCase() || "";
                            const providers: Record<string, { url: string; label: string; icon: string }> = {
                                "gmail.com": { url: "https://mail.google.com", label: "Otevřít Gmail", icon: "📧" },
                                "googlemail.com": { url: "https://mail.google.com", label: "Otevřít Gmail", icon: "📧" },
                                "seznam.cz": { url: "https://email.seznam.cz", label: "Otevřít Seznam Email", icon: "📧" },
                                "email.cz": { url: "https://email.seznam.cz", label: "Otevřít Seznam Email", icon: "📧" },
                                "post.cz": { url: "https://email.seznam.cz", label: "Otevřít Seznam Email", icon: "📧" },
                                "outlook.com": { url: "https://outlook.live.com/mail", label: "Otevřít Outlook", icon: "📧" },
                                "hotmail.com": { url: "https://outlook.live.com/mail", label: "Otevřít Hotmail", icon: "📧" },
                                "live.com": { url: "https://outlook.live.com/mail", label: "Otevřít Outlook", icon: "📧" },
                                "yahoo.com": { url: "https://mail.yahoo.com", label: "Otevřít Yahoo Mail", icon: "📧" },
                                "icloud.com": { url: "https://www.icloud.com/mail", label: "Otevřít iCloud Mail", icon: "📧" },
                                "me.com": { url: "https://www.icloud.com/mail", label: "Otevřít iCloud Mail", icon: "📧" },
                                "mac.com": { url: "https://www.icloud.com/mail", label: "Otevřít iCloud Mail", icon: "📧" },
                                "centrum.cz": { url: "https://mail.centrum.cz", label: "Otevřít Centrum.cz", icon: "📧" },
                                "volny.cz": { url: "https://mail.volny.cz", label: "Otevřít Volný.cz", icon: "📧" },
                                "tiscali.cz": { url: "https://mail.tiscali.cz", label: "Otevřít Tiscali", icon: "📧" },
                            };
                            const provider = providers[domain];
                            return (
                                <a
                                    href={provider ? provider.url : `https://mail.google.com/mail/u/0/#search/from%3Aaishield`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="btn-primary inline-flex items-center gap-2 px-6 py-3 text-sm"
                                >
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 0 1-2.25 2.25h-15a2.25 2.25 0 0 1-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25m19.5 0v.243a2.25 2.25 0 0 1-1.07 1.916l-7.5 4.615a2.25 2.25 0 0 1-2.36 0L3.32 8.91a2.25 2.25 0 0 1-1.07-1.916V6.75" />
                                    </svg>
                                    {provider ? provider.label : "Otevřít emailovou schránku"}
                                </a>
                            );
                        })()}

                        <a href="/login" className="btn-secondary inline-flex">
                            Zpět na přihlášení
                        </a>
                        </div>
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
                                    placeholder="Minimálně 6 znaků"
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
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white transition-colors p-2.5 -mr-1 min-w-[44px] min-h-[44px] flex items-center justify-center"
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

                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-1.5">
                                Potvrdit heslo
                            </label>
                            <div className="relative">
                                <input
                                    type={showConfirmPassword ? "text" : "password"}
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    placeholder="Zadejte heslo znovu"
                                    required
                                    minLength={6}
                                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 pr-12
                                        text-white placeholder:text-slate-500
                                        focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/30
                                        transition-all"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white transition-colors p-2.5 -mr-1 min-w-[44px] min-h-[44px] flex items-center justify-center"
                                    tabIndex={-1}
                                >
                                    {showConfirmPassword ? (
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 0 0 1.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.451 10.451 0 0 1 12 4.5c4.756 0 8.773 3.162 10.065 7.498a10.522 10.522 0 0 1-4.293 5.774M6.228 6.228 3 3m3.228 3.228 3.65 3.65m7.894 7.894L21 21m-3.228-3.228-3.65-3.65m0 0a3 3 0 1 0-4.243-4.243m4.242 4.242L9.88 9.88" /></svg>
                                    ) : (
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" /><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" /></svg>
                                    )}
                                </button>
                            </div>
                        </div>

                        {/* GDPR souhlas */}
                        <label className="flex items-start gap-3 cursor-pointer group">
                            <input
                                type="checkbox"
                                checked={gdprConsent}
                                onChange={(e) => setGdprConsent(e.target.checked)}
                                className="mt-0 h-5 w-5 min-w-[44px] min-h-[44px] rounded border-white/20 bg-white/5 text-fuchsia-500 appearance-none 
                                    focus:ring-fuchsia-500/50 focus:ring-offset-0 cursor-pointer"
                            />
                            <span className="text-xs text-slate-400 leading-relaxed group-hover:text-slate-300 transition-colors">
                                Souhlasím se{" "}
                                <a href="/privacy" target="_blank" className="text-fuchsia-400 hover:text-fuchsia-300 underline inline-block py-3 min-h-[44px]">
                                    zpracováním osobních údajů
                                </a>
                                {" "}a{" "}
                                <a href="/terms" target="_blank" className="text-fuchsia-400 hover:text-fuchsia-300 underline inline-block py-3 min-h-[44px]">
                                    obchodními podmínkami
                                </a>
                                . Vaše data zpracováváme výhradně pro poskytování služby
                                AI Act compliance v souladu s GDPR.
                            </span>
                        </label>

                        {/* Anti-bot: matematický příklad */}
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-1.5">
                                Ověření <span className="text-slate-500">(ochrana proti robotům)</span>
                            </label>
                            <div className="flex items-center gap-3">
                                <span className="text-sm text-slate-300 font-mono whitespace-nowrap">
                                    {captchaA} + {captchaB} =
                                </span>
                                <div className="flex items-center">
                                    <button
                                        type="button"
                                        onClick={() => setCaptchaAnswer(String(Math.max(0, Number(captchaAnswer || 0) - 1)))}
                                        className="w-10 h-11 rounded-l-xl border border-white/10 bg-white/5 text-slate-300 hover:bg-white/10 transition-all text-lg font-bold flex items-center justify-center"
                                    >−</button>
                                    <input
                                        type="text"
                                        inputMode="numeric"
                                        value={captchaAnswer}
                                        onChange={(e) => setCaptchaAnswer(e.target.value.replace(/\D/g, "").slice(0, 3))}
                                        placeholder="?"
                                        required
                                        maxLength={3}
                                        className="w-16 border-y border-white/10 bg-white/5 px-2 py-3
                                            text-white text-center placeholder:text-slate-500
                                            focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/30
                                            transition-all [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setCaptchaAnswer(String(Number(captchaAnswer || 0) + 1))}
                                        className="w-10 h-11 rounded-r-xl border border-white/10 bg-white/5 text-slate-300 hover:bg-white/10 transition-all text-lg font-bold flex items-center justify-center"
                                    >+</button>
                                </div>
                            </div>
                        </div>

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
