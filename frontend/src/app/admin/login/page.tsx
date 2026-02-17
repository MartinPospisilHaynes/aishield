"use client";

import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { adminLogin, isAdminLoggedIn } from "@/lib/admin-api";

// Generate random math captcha
function generateCaptcha(): { question: string; answer: number } {
    const ops = ["+", "-", "×"] as const;
    const op = ops[Math.floor(Math.random() * ops.length)];
    let a: number, b: number, answer: number;
    if (op === "+") {
        a = Math.floor(Math.random() * 20) + 1;
        b = Math.floor(Math.random() * 20) + 1;
        answer = a + b;
    } else if (op === "-") {
        a = Math.floor(Math.random() * 20) + 10;
        b = Math.floor(Math.random() * a);
        answer = a - b;
    } else {
        a = Math.floor(Math.random() * 10) + 1;
        b = Math.floor(Math.random() * 10) + 1;
        answer = a * b;
    }
    return { question: `${a} ${op} ${b} = ?`, answer };
}

export default function AdminLoginPage() {
    const router = useRouter();

    const [username, setUsername] = useState("ADMIN");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    // Security: honeypot (hidden field — bots fill it, humans don't)
    const [honeypot, setHoneypot] = useState("");

    // Security: math captcha
    const [captcha, setCaptcha] = useState(() => generateCaptcha());
    const [captchaAnswer, setCaptchaAnswer] = useState("");

    // Security: lockout countdown
    const [lockoutUntil, setLockoutUntil] = useState<number>(0);
    const [lockoutRemaining, setLockoutRemaining] = useState(0);

    // Security: attempt counter (visual)
    const [failedAttempts, setFailedAttempts] = useState(0);

    // Already logged in → redirect
    useEffect(() => {
        if (isAdminLoggedIn()) {
            router.replace("/admin");
        }
    }, [router]);

    // Lockout countdown timer
    useEffect(() => {
        if (lockoutUntil <= 0) return;
        const interval = setInterval(() => {
            const remaining = Math.max(0, Math.ceil((lockoutUntil - Date.now()) / 1000));
            setLockoutRemaining(remaining);
            if (remaining <= 0) {
                setLockoutUntil(0);
                setLockoutRemaining(0);
                setFailedAttempts(0);
                setError("");
            }
        }, 1000);
        return () => clearInterval(interval);
    }, [lockoutUntil]);

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

    async function handleLogin(e: React.FormEvent) {
        e.preventDefault();
        setError("");

        // Check lockout
        if (lockoutUntil > Date.now()) {
            setError(`Účet uzamčen. Zkuste za ${lockoutRemaining} sekund.`);
            return;
        }

        // Check captcha
        if (parseInt(captchaAnswer, 10) !== captcha.answer) {
            setError("Nesprávná odpověď na bezpečnostní otázku.");
            setCaptcha(generateCaptcha());
            setCaptchaAnswer("");
            return;
        }

        setLoading(true);
        try {
            await adminLogin(username, password, honeypot);
            router.push("/admin");
        } catch (err) {
            const msg = err instanceof Error ? err.message : "Nesprávné přihlašovací údaje";

            // Check if lockout (429)
            if (msg.includes("Příliš mnoho") || msg.includes("429")) {
                // Extract seconds from message or default to 900
                const match = msg.match(/(\d+)\s*(sekund|minut)/);
                const seconds = match ? (msg.includes("minut") ? parseInt(match[1]) * 60 : parseInt(match[1])) : 900;
                setLockoutUntil(Date.now() + seconds * 1000);
                setLockoutRemaining(seconds);
            }

            setFailedAttempts(prev => prev + 1);
            setError(msg);

            // Refresh captcha after failed attempt
            setCaptcha(generateCaptcha());
            setCaptchaAnswer("");
        } finally {
            setLoading(false);
        }
    }

    const isLocked = lockoutUntil > Date.now();

    const inputCls = "w-full bg-black/30 border border-white/10 rounded-xl px-4 py-3 pr-12 text-white placeholder-gray-500 focus:border-cyan-500/50 focus:outline-none focus:ring-1 focus:ring-cyan-500/30 transition-all";

    return (
        <div className="min-h-screen bg-[#0f172a] flex items-center justify-center px-4">
            <div className="w-full max-w-md">
                <div className="text-center mb-8">
                    <div className="text-5xl mb-4">🛡️</div>
                    <h1 className="text-3xl font-bold text-white">AIshield Admin</h1>
                    <p className="text-gray-400 mt-2">Řídící panel systému</p>
                </div>

                <form onSubmit={handleLogin} className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8 space-y-6">

                    {/* Lockout warning banner */}
                    {isLocked && (
                        <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-4 text-center">
                            <div className="text-red-400 text-lg font-bold mb-1">🔒 Účet dočasně uzamčen</div>
                            <div className="text-red-300 text-sm">Příliš mnoho neúspěšných pokusů</div>
                            <div className="text-3xl font-mono text-red-400 mt-2">{Math.floor(lockoutRemaining / 60)}:{String(lockoutRemaining % 60).padStart(2, "0")}</div>
                        </div>
                    )}

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">Uživatel</label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className={inputCls}
                            placeholder="ADMIN"
                            autoFocus
                            required
                            disabled={isLocked}
                            autoComplete="off"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">Heslo</label>
                        <div className="relative">
                            <input
                                type={showPassword ? "text" : "password"}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className={inputCls}
                                placeholder="••••••••"
                                required
                                disabled={isLocked}
                                autoComplete="off"
                            />
                            <EyeToggle show={showPassword} onToggle={() => setShowPassword(!showPassword)} />
                        </div>
                    </div>

                    {/* Honeypot — hidden field, bots fill it */}
                    <div className="absolute opacity-0 pointer-events-none h-0 overflow-hidden" aria-hidden="true" tabIndex={-1}>
                        <label>Website</label>
                        <input
                            type="text"
                            name="website"
                            value={honeypot}
                            onChange={(e) => setHoneypot(e.target.value)}
                            tabIndex={-1}
                            autoComplete="off"
                        />
                    </div>

                    {/* Math CAPTCHA */}
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            🔢 Bezpečnostní otázka: <span className="text-cyan-400 font-mono font-bold">{captcha.question}</span>
                        </label>
                        <div className="flex items-stretch gap-2">
                            <button
                                type="button"
                                onClick={() => setCaptchaAnswer(String((parseInt(captchaAnswer, 10) || 0) - 1))}
                                disabled={isLocked}
                                className="w-12 flex items-center justify-center rounded-xl bg-black/30 border border-white/10 text-white text-xl font-bold hover:bg-white/10 hover:border-cyan-500/40 active:scale-95 transition-all disabled:opacity-30 disabled:cursor-not-allowed select-none"
                                tabIndex={-1}
                            >
                                −
                            </button>
                            <input
                                type="number"
                                value={captchaAnswer}
                                onChange={(e) => setCaptchaAnswer(e.target.value)}
                                className="flex-1 bg-black/30 border border-white/10 rounded-xl px-4 py-3 text-white text-center text-lg font-mono placeholder-gray-500 focus:border-cyan-500/50 focus:outline-none focus:ring-1 focus:ring-cyan-500/30 transition-all [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                                placeholder="Odpověď"
                                required
                                disabled={isLocked}
                                autoComplete="off"
                            />
                            <button
                                type="button"
                                onClick={() => setCaptchaAnswer(String((parseInt(captchaAnswer, 10) || 0) + 1))}
                                disabled={isLocked}
                                className="w-12 flex items-center justify-center rounded-xl bg-black/30 border border-white/10 text-white text-xl font-bold hover:bg-white/10 hover:border-cyan-500/40 active:scale-95 transition-all disabled:opacity-30 disabled:cursor-not-allowed select-none"
                                tabIndex={-1}
                            >
                                +
                            </button>
                        </div>
                    </div>

                    {error && (
                        <div className="bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 text-red-400 text-sm">
                            ❌ {error}
                        </div>
                    )}

                    {/* Failed attempts indicator */}
                    {failedAttempts > 0 && failedAttempts < 5 && !isLocked && (
                        <div className="text-xs text-yellow-400/60 text-center">
                            ⚠️ Neúspěšných pokusů: {failedAttempts}/5
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading || !username || !password || !captchaAnswer || isLocked}
                        className="w-full py-3 rounded-xl font-semibold text-white bg-gradient-to-r from-cyan-500 to-fuchsia-500 hover:from-cyan-400 hover:to-fuchsia-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-lg shadow-cyan-500/20"
                    >
                        {isLocked ? `🔒 Uzamčeno (${lockoutRemaining}s)` : loading ? "⏳ Přihlašuji..." : "🔐 Vstoupit do Adminu"}
                    </button>
                </form>

                <p className="text-center text-gray-500 text-xs mt-6">
                    AIshield.cz — AI Act Compliance Platform
                </p>
            </div>
        </div>
    );
}
