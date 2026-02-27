"use client";

import { useState, useMemo } from "react";

function generateMathChallenge(): { a: number; b: number; answer: number } {
    const a = Math.floor(Math.random() * 9) + 1;
    const b = Math.floor(Math.random() * 9) + 1;
    return { a, b, answer: a + b };
}

export default function ContactForm() {
    const [form, setForm] = useState({ name: "", email: "", phone: "", company: "", message: "" });
    const [gdprConsent, setGdprConsent] = useState(false);
    const [honeypot, setHoneypot] = useState("");
    const [submitted, setSubmitted] = useState(false);
    const [sending, setSending] = useState(false);
    const [captcha] = useState(() => generateMathChallenge());
    const [captchaInput, setCaptchaInput] = useState("");
    const [captchaError, setCaptchaError] = useState(false);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        // Honeypot check — bots fill hidden fields
        if (honeypot) return;
        if (!gdprConsent) return;

        // Math captcha check
        if (parseInt(captchaInput, 10) !== captcha.answer) {
            setCaptchaError(true);
            return;
        }
        setCaptchaError(false);

        setSending(true);
        try {
            const API = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").trim();
            await fetch(`${API}/api/contact`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(form),
            });
        } catch {
            // silently continue — form still shows success
        }
        setSending(false);
        setSubmitted(true);
    }

    return (
        <div id="kontakt" className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6 sm:p-8">
            <div className="text-center mb-6">
                <h2 className="text-2xl font-bold text-white mb-2">Napište nám</h2>
                <p className="text-slate-400 text-sm">
                    Máte dotaz ohledně AI Actu nebo našich služeb?{" "}
                    Zanechte nám zprávu a ozveme se vám co nejdříve.
                </p>
            </div>

            {submitted ? (
                <div className="text-center py-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-500/15 border border-green-500/30 mb-4">
                        <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
                    </div>
                    <h3 className="text-xl font-semibold text-white mb-2">Děkujeme za váš zájem!</h3>
                    <p className="text-slate-400">Ozveme se vám co nejdříve — obvykle do 24 hodin.</p>
                </div>
            ) : (
                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Honeypot — hidden from real users, bots fill it */}
                    <div className="absolute opacity-0 -z-50 pointer-events-none" aria-hidden="true" tabIndex={-1}>
                        <label htmlFor="cf-website-url">Website</label>
                        <input
                            id="cf-website-url"
                            type="text"
                            name="website_url"
                            autoComplete="off"
                            tabIndex={-1}
                            value={honeypot}
                            onChange={e => setHoneypot(e.target.value)}
                        />
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                            <label htmlFor="c-name" className="block text-sm font-medium text-slate-300 mb-1.5">Jméno a příjmení *</label>
                            <input
                                id="c-name"
                                type="text"
                                required
                                value={form.name}
                                onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                                className="w-full rounded-xl bg-white/[0.06] border border-white/[0.1] px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/50 transition"
                                placeholder="Jan Novák"
                            />
                        </div>
                        <div>
                            <label htmlFor="c-company" className="block text-sm font-medium text-slate-300 mb-1.5">Firma / Web</label>
                            <input
                                id="c-company"
                                type="text"
                                value={form.company}
                                onChange={e => setForm(f => ({ ...f, company: e.target.value }))}
                                className="w-full rounded-xl bg-white/[0.06] border border-white/[0.1] px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/50 transition"
                                placeholder="www.example.cz"
                            />
                        </div>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                            <label htmlFor="c-email" className="block text-sm font-medium text-slate-300 mb-1.5">E-mail *</label>
                            <input
                                id="c-email"
                                type="email"
                                required
                                value={form.email}
                                onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                                className="w-full rounded-xl bg-white/[0.06] border border-white/[0.1] px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/50 transition"
                                placeholder="jan@firma.cz"
                            />
                        </div>
                        <div>
                            <label htmlFor="c-phone" className="block text-sm font-medium text-slate-300 mb-1.5">Telefon</label>
                            <input
                                id="c-phone"
                                type="tel"
                                value={form.phone}
                                onChange={e => setForm(f => ({ ...f, phone: e.target.value }))}
                                className="w-full rounded-xl bg-white/[0.06] border border-white/[0.1] px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/50 transition"
                                placeholder="+420 ..."
                            />
                        </div>
                    </div>
                    <div>
                        <label htmlFor="c-msg" className="block text-sm font-medium text-slate-300 mb-1.5">Vaše otázka / zpráva *</label>
                        <textarea
                            id="c-msg"
                            required
                            rows={4}
                            value={form.message}
                            onChange={e => setForm(f => ({ ...f, message: e.target.value }))}
                            className="w-full rounded-xl bg-white/[0.06] border border-white/[0.1] px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/50 transition resize-none"
                            placeholder="Popište, s čím vám můžeme pomoci..."
                        />
                    </div>

                    {/* Math captcha — anti-robot */}
                    <div>
                        <label htmlFor="c-captcha" className="block text-sm font-medium text-slate-300 mb-1.5">
                            Ověření: Kolik je {captcha.a} + {captcha.b}? *
                        </label>
                        <div className="flex items-center">
                            <button
                                type="button"
                                onClick={() => { setCaptchaInput(String(Math.max(0, Number(captchaInput || 0) - 1))); setCaptchaError(false); }}
                                className="w-11 h-11 rounded-l-xl border border-white/10 bg-white/[0.06] text-slate-300 hover:bg-white/10 transition-all text-lg font-bold flex items-center justify-center"
                            >−</button>
                            <input
                                id="c-captcha"
                                type="text"
                                inputMode="numeric"
                                required
                                value={captchaInput}
                                onChange={e => { setCaptchaInput(e.target.value.replace(/\D/g, '').slice(0, 3)); setCaptchaError(false); }}
                                className={`w-16 border-y px-2 py-2.5 text-sm text-white text-center placeholder-slate-500 bg-white/[0.06] focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/50 transition [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none ${captchaError ? "border-red-500/50" : "border-white/[0.1]"}`}
                                placeholder="?"
                            />
                            <button
                                type="button"
                                onClick={() => { setCaptchaInput(String(Number(captchaInput || 0) + 1)); setCaptchaError(false); }}
                                className="w-11 h-11 rounded-r-xl border border-white/10 bg-white/[0.06] text-slate-300 hover:bg-white/10 transition-all text-lg font-bold flex items-center justify-center"
                            >+</button>
                        </div>
                        {captchaError && (
                            <p className="text-xs text-red-400 mt-1">Špatná odpověď, zkuste to znovu.</p>
                        )}
                    </div>

                    {/* GDPR souhlas */}
                    <div className="flex items-start gap-3">
                        <input
                            id="c-gdpr"
                            type="checkbox"
                            required
                            checked={gdprConsent}
                            onChange={e => setGdprConsent(e.target.checked)}
                            className="mt-1 h-4 w-4 rounded border-white/20 bg-white/[0.06] text-fuchsia-500 focus:ring-fuchsia-500/50 focus:ring-offset-0 cursor-pointer accent-fuchsia-500"
                        />
                        <label htmlFor="c-gdpr" className="text-xs text-slate-400 leading-relaxed cursor-pointer">
                            Souhlasím se{" "}
                            <a href="/privacy" className="text-slate-300 hover:text-neon-fuchsia underline inline-block py-3" target="_blank">zpracováním osobních údajů</a>{" "}
                            v souladu s{" "}
                            <a href="/gdpr" className="text-slate-300 hover:text-neon-fuchsia underline inline-block py-3" target="_blank">GDPR</a>{" "}
                            za účelem odpovědi na můj dotaz. *
                        </label>
                    </div>

                    <div className="text-center pt-2">
                        <button
                            type="submit"
                            disabled={sending || !gdprConsent}
                            className="inline-flex items-center justify-center gap-2 rounded-xl bg-fuchsia-600 px-8 py-3 text-sm font-semibold text-white shadow-lg shadow-fuchsia-500/25 hover:bg-fuchsia-500 transition disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {sending ? (
                                <>
                                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                                    Odesílám...
                                </>
                            ) : (
                                <>
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M6 12 3.269 3.125A59.769 59.769 0 0 1 21.485 12 59.768 59.768 0 0 1 3.27 20.875L5.999 12Zm0 0h7.5" /></svg>
                                    Odeslat zprávu
                                </>
                            )}
                        </button>
                    </div>
                </form>
            )}
        </div>
    );
}
