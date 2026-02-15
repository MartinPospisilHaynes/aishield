"use client";

import { useState, useCallback, useEffect } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase-browser";
import { useAnalytics } from "@/lib/analytics";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://api.aishield.cz";

function normalizeUrl(raw: string): string {
    const trimmed = raw.trim();
    if (!trimmed) return "";
    if (/^https?:\/\//i.test(trimmed)) return trimmed;
    return `https://${trimmed}`;
}

export default function OnboardingPage() {
    const [ico, setIco] = useState("");
    const [companyName, setCompanyName] = useState("");
    const [webUrl, setWebUrl] = useState("");
    const [gdprConsent, setGdprConsent] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [aresLoading, setAresLoading] = useState(false);
    const [aresStatus, setAresStatus] = useState<"idle" | "found" | "not-found">("idle");
    // Anti-bot: math CAPTCHA
    const [captchaA, setCaptchaA] = useState(0);
    const [captchaB, setCaptchaB] = useState(0);
    const [captchaAnswer, setCaptchaAnswer] = useState("");
    const router = useRouter();
    const supabase = createClient();
    const { track } = useAnalytics();

    // Generate math CAPTCHA on mount
    useEffect(() => {
        setCaptchaA(Math.floor(Math.random() * 10) + 1);
        setCaptchaB(Math.floor(Math.random() * 10) + 1);
    }, []);

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

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setLoading(true);
        setError("");

        if (!webUrl.trim()) {
            setError("Zadejte URL vašeho webu.");
            setLoading(false);
            return;
        }

        if (!gdprConsent) {
            setError("Pro pokračování je nutný souhlas se zpracováním údajů.");
            setLoading(false);
            return;
        }

        // Anti-bot: ověření matematického příkladu
        if (parseInt(captchaAnswer, 10) !== captchaA + captchaB) {
            setError("Nesprávná odpověď na ověřovací otázku. Zkuste to znovu.");
            setLoading(false);
            setCaptchaA(Math.floor(Math.random() * 10) + 1);
            setCaptchaB(Math.floor(Math.random() * 10) + 1);
            setCaptchaAnswer("");
            return;
        }

        const normalizedWeb = normalizeUrl(webUrl);

        const { error: updateError } = await supabase.auth.updateUser({
            data: {
                company_name: companyName || undefined,
                ico: ico || undefined,
                web_url: normalizedWeb,
                gdpr_consent: true,
                gdpr_consent_at: new Date().toISOString(),
            },
        });

        if (updateError) {
            setError(updateError.message);
            setLoading(false);
            return;
        }

        track("onboarding_completed", { has_ico: !!ico, has_web: !!normalizedWeb });
        router.push("/dashboard");
    }

    return (
        <section className="min-h-screen bg-gradient-to-b from-[#0a0e1a] to-[#0f172a] flex items-center justify-center p-4">
            <div className="w-full max-w-md">
                <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-8 shadow-2xl">
                    <h1 className="text-2xl font-bold text-white text-center mb-2">
                        Doplňte údaje o firmě
                    </h1>
                    <p className="text-sm text-slate-400 text-center mb-6">
                        Pro spuštění AI auditu potřebujeme vědět URL vašeho webu.
                    </p>

                    {error && (
                        <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/30 p-3 text-sm text-red-400">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        {/* IČO */}
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-1.5">
                                IČO <span className="text-slate-500 font-normal">(nepovinné — doplní název firmy)</span>
                            </label>
                            <div className="relative">
                                <input
                                    type="text"
                                    value={ico}
                                    onChange={handleIcoChange}
                                    placeholder="12345678"
                                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all"
                                />
                                {aresLoading && (
                                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-cyan-400 animate-pulse text-xs">
                                        Hledám v ARES...
                                    </span>
                                )}
                                {aresStatus === "found" && (
                                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-green-400 text-xs">
                                        ✓ Nalezeno
                                    </span>
                                )}
                                {aresStatus === "not-found" && (
                                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-amber-400 text-xs">
                                        IČO nenalezeno
                                    </span>
                                )}
                            </div>
                        </div>

                        {/* Název firmy */}
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-1.5">
                                Název firmy
                            </label>
                            <input
                                type="text"
                                value={companyName}
                                onChange={e => setCompanyName(e.target.value)}
                                placeholder="Vaše firma s.r.o."
                                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all"
                            />
                        </div>

                        {/* Web URL */}
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-1.5">
                                URL webu <span className="text-red-400">*</span>
                            </label>
                            <input
                                type="text"
                                value={webUrl}
                                onChange={e => setWebUrl(e.target.value)}
                                placeholder="www.firma.cz"
                                required
                                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all"
                            />
                            <p className="mt-1 text-xs text-slate-500">
                                Web, který chcete prověřit na AI technologie
                            </p>
                        </div>

                        {/* Anti-bot CAPTCHA */}
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-1.5">
                                Ověření: Kolik je {captchaA} + {captchaB}? <span className="text-red-400">*</span>
                            </label>
                            <input
                                type="text"
                                value={captchaAnswer}
                                onChange={e => setCaptchaAnswer(e.target.value)}
                                placeholder="Zadejte výsledek"
                                required
                                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all"
                            />
                        </div>

                        {/* GDPR */}
                        <div className="flex items-start gap-3 pt-2">
                            <input
                                type="checkbox"
                                id="gdpr"
                                checked={gdprConsent}
                                onChange={e => setGdprConsent(e.target.checked)}
                                className="mt-1 h-4 w-4 rounded border-white/20 bg-white/5 text-cyan-500 focus:ring-cyan-500/50"
                            />
                            <label htmlFor="gdpr" className="text-xs text-slate-400 leading-relaxed">
                                Souhlasím se{" "}
                                <a href="/vop" target="_blank" className="text-cyan-400 hover:text-cyan-300 underline">
                                    zpracováním osobních údajů
                                </a>{" "}
                                a{" "}
                                <a href="/vop" target="_blank" className="text-cyan-400 hover:text-cyan-300 underline">
                                    obchodními podmínkami
                                </a>
                                .
                            </label>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-4 py-3 text-sm font-bold text-white shadow-lg shadow-cyan-500/25 hover:shadow-cyan-500/40 hover:scale-[1.02] transition-all disabled:opacity-50 disabled:hover:scale-100"
                        >
                            {loading ? "Ukládám..." : "Pokračovat na dashboard"}
                        </button>
                    </form>
                </div>
            </div>
        </section>
    );
}
