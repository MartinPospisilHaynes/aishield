"use client";

import { useState, useEffect } from "react";

const CONSENT_KEY = "aishield_consent_v1";

interface ConsentState {
    cookies: boolean;
    aiAct: boolean;
    timestamp: string;
}

export default function ConsentBanner() {
    const [visible, setVisible] = useState(false);
    const [showDetails, setShowDetails] = useState(false);

    useEffect(() => {
        // Check if user has already consented
        const stored = localStorage.getItem(CONSENT_KEY);
        if (!stored) {
            // Small delay so it doesn't flash on page load
            const timer = setTimeout(() => setVisible(true), 800);
            return () => clearTimeout(timer);
        }
    }, []);

    function handleAcceptAll() {
        const consent: ConsentState = {
            cookies: true,
            aiAct: true,
            timestamp: new Date().toISOString(),
        };
        localStorage.setItem(CONSENT_KEY, JSON.stringify(consent));
        setVisible(false);
    }

    function handleAcceptNecessary() {
        const consent: ConsentState = {
            cookies: false,
            aiAct: true,
            timestamp: new Date().toISOString(),
        };
        localStorage.setItem(CONSENT_KEY, JSON.stringify(consent));
        setVisible(false);
    }

    if (!visible) return null;

    return (
        <div className="fixed bottom-0 left-0 right-0 z-[100] p-4 sm:p-6 animate-slideUp">
            <div className="mx-auto max-w-3xl rounded-2xl border border-white/[0.1] bg-dark-900/95 backdrop-blur-xl shadow-2xl shadow-black/50">
                <div className="p-5 sm:p-6">
                    {/* Header */}
                    <div className="flex items-start gap-3 mb-4">
                        <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-fuchsia-500/10 border border-fuchsia-500/20 flex items-center justify-center">
                            <svg className="w-5 h-5 text-fuchsia-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                            </svg>
                        </div>
                        <div>
                            <h3 className="font-semibold text-white text-sm">
                                Cookies a informace dle EU AI Act
                            </h3>
                            <p className="text-xs text-slate-500 mt-0.5">
                                Transparentnost v souladu s nařízením EU 2024/1689 (AI Act) a GDPR
                            </p>
                        </div>
                    </div>

                    {/* Main content */}
                    <div className="space-y-3 text-sm text-slate-400 leading-relaxed">
                        <p>
                            Tento web používá <strong className="text-slate-300">nezbytné cookies</strong> pro
                            správné fungování (autentizace, preference).
                            S vaším souhlasem používáme i <strong className="text-slate-300">analytické cookies</strong> pro
                            zlepšování služeb.
                        </p>

                        {/* AI Act disclosure — always visible */}
                        <div className="rounded-xl bg-fuchsia-500/5 border border-fuchsia-500/15 p-3.5">
                            <div className="flex items-center gap-2 mb-1.5">
                                <svg className="w-4 h-4 text-fuchsia-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
                                </svg>
                                <span className="text-xs font-semibold text-fuchsia-300 uppercase tracking-wider">
                                    Oznámení dle AI Act (čl. 50)
                                </span>
                            </div>
                            <p className="text-xs text-slate-400">
                                Tento web je z velké části <strong className="text-slate-300">generován pomocí umělé inteligence</strong> —
                                včetně textů, grafických prvků a kódu.
                                Náš scanner využívá AI (Claude, Anthropic) pro klasifikaci nalezených systémů.
                                Veškerý AI-generovaný obsah prochází lidskou kontrolou.
                            </p>
                        </div>

                        {/* Expandable details */}
                        {showDetails && (
                            <div className="space-y-2 pt-1">
                                <div className="rounded-lg bg-white/[0.03] border border-white/[0.06] p-3">
                                    <h4 className="text-xs font-semibold text-slate-300 mb-1.5">Nezbytné cookies (vždy aktivní)</h4>
                                    <ul className="text-xs text-slate-500 space-y-0.5">
                                        <li>Přihlášení a autentizace (Supabase session)</li>
                                        <li>Preference cookie souhlasu</li>
                                        <li>CSRF ochrana a bezpečnostní tokeny</li>
                                    </ul>
                                </div>
                                <div className="rounded-lg bg-white/[0.03] border border-white/[0.06] p-3">
                                    <h4 className="text-xs font-semibold text-slate-300 mb-1.5">Analytické cookies (volitelné)</h4>
                                    <ul className="text-xs text-slate-500 space-y-0.5">
                                        <li>Vercel Analytics — anonymní návštěvnost</li>
                                        <li>Měření výkonu stránek (Web Vitals)</li>
                                    </ul>
                                </div>
                                <div className="rounded-lg bg-white/[0.03] border border-white/[0.06] p-3">
                                    <h4 className="text-xs font-semibold text-slate-300 mb-1.5">AI systémy na tomto webu</h4>
                                    <ul className="text-xs text-slate-500 space-y-0.5">
                                        <li>Claude AI (Anthropic) — klasifikace AI systémů při skenování</li>
                                        <li>AI-generované texty a grafika — celý web</li>
                                        <li>Riziko: minimální — žádné automatizované rozhodování o uživatelích</li>
                                    </ul>
                                </div>
                                <p className="text-xs text-slate-600">
                                    Podrobnosti v{" "}
                                    <a href="/privacy" className="text-fuchsia-400 hover:underline">Zásadách ochrany soukromí</a>
                                    {" "}a{" "}
                                    <a href="/gdpr" className="text-fuchsia-400 hover:underline">GDPR informacích</a>.
                                </p>
                            </div>
                        )}
                    </div>

                    {/* Actions */}
                    <div className="mt-4 flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3">
                        <button
                            onClick={handleAcceptAll}
                            className="flex-1 sm:flex-none rounded-xl bg-fuchsia-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-fuchsia-500 transition shadow-lg shadow-fuchsia-500/25"
                        >
                            Přijmout vše
                        </button>
                        <button
                            onClick={handleAcceptNecessary}
                            className="flex-1 sm:flex-none rounded-xl bg-white/5 border border-white/10 px-5 py-2.5 text-sm font-medium text-slate-300 hover:bg-white/10 transition"
                        >
                            Jen nezbytné
                        </button>
                        <button
                            onClick={() => setShowDetails(!showDetails)}
                            className="text-xs text-slate-500 hover:text-slate-300 transition underline underline-offset-2 py-1"
                        >
                            {showDetails ? "Skrýt podrobnosti" : "Zobrazit podrobnosti"}
                        </button>
                    </div>
                </div>
            </div>

            <style jsx>{`
                @keyframes slideUp {
                    from { transform: translateY(100%); opacity: 0; }
                    to { transform: translateY(0); opacity: 1; }
                }
                .animate-slideUp {
                    animation: slideUp 0.4s ease-out;
                }
            `}</style>
        </div>
    );
}
