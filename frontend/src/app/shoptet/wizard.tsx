"use client";

/**
 * Shoptet Addon — Wizard (sebehodnocení AI systémů)
 * E-shopař odpovídá na otázky o AI systémech na svém webu.
 * 3 kroky: chatboty → AI obsah → ostatní AI → souhrn
 */

import { useState } from "react";
import { submitWizard, type AISystemEntry, type WizardRequest, type WizardResponse } from "@/lib/shoptet-api";

interface WizardProps {
    installationId: string;
    eshopName: string;
    onComplete: () => void;
}

// Známí chatbot/AI poskytovatelé na Shoptet eshopech
const KNOWN_CHATBOTS = ["Smartsupp", "Tidio", "LiveChat", "Zendesk Chat", "Drift", "Intercom", "ChatGPT widget"];
const KNOWN_CONTENT_AI = ["ChatGPT / OpenAI", "Jasper AI", "Copy.ai", "Writesonic", "AI popisky produktů"];

type Step = "intro" | "chatbots" | "content" | "other" | "submitting" | "done";

export default function ShoptetWizard({ installationId, eshopName, onComplete }: WizardProps) {
    const [step, setStep] = useState<Step>("intro");
    const [chatbots, setChatbots] = useState<AISystemEntry[]>([]);
    const [contentAi, setContentAi] = useState<AISystemEntry[]>([]);
    const [otherAi, setOtherAi] = useState<AISystemEntry[]>([]);
    const [result, setResult] = useState<WizardResponse | null>(null);
    const [error, setError] = useState("");

    const handleSubmit = async () => {
        setStep("submitting");
        setError("");
        try {
            const payload: WizardRequest = {
                chatbots,
                content_ai: contentAi,
                other_ai: otherAi,
            };
            const res = await submitWizard(installationId, payload);
            setResult(res);
            setStep("done");
        } catch (e) {
            setError(e instanceof Error ? e.message : "Odeslání selhalo");
            setStep("other"); // vrátit se na poslední krok
        }
    };

    // ── INTRO ──
    if (step === "intro") {
        return (
            <div className="max-w-2xl mx-auto">
                <div className="glass p-8">
                    <h1 className="text-2xl font-bold text-white mb-2">
                        AI Act Compliance Wizard
                    </h1>
                    <p className="text-slate-400 mb-6">
                        Vítejte, <span className="text-white font-medium">{eshopName}</span>.
                        Tento průvodce vám pomůže zjistit, jaké AI systémy na vašem e-shopu
                        používáte a co vyžaduje nařízení EU o AI (AI Act).
                    </p>

                    <div className="bg-dark-800/50 rounded-lg p-4 mb-6 border border-white/5">
                        <h3 className="text-sm font-semibold text-neon-cyan mb-2">Proč je to důležité?</h3>
                        <ul className="text-sm text-slate-400 space-y-1.5">
                            <li>&#x2022; <b className="text-white">Article 50</b> — chatboty a AI obsah musí informovat zákazníky (deadline: 2. 8. 2026)</li>
                            <li>&#x2022; <b className="text-white">Article 4</b> — všechny AI systémy musí být evidovány (platí od 2. 2. 2025)</li>
                            <li>&#x2022; Pokuta až <b className="text-white">35 mil. EUR</b> nebo 7 % obratu</li>
                        </ul>
                    </div>

                    <div className="text-sm text-slate-500 mb-6">
                        Průvodce zabere cca 2–3 minuty. Odpovídejte podle nejlepšího vědomí.
                    </div>

                    <button
                        onClick={() => setStep("chatbots")}
                        className="btn-primary w-full py-3 text-base"
                    >
                        Začít sebehodnocení
                    </button>
                </div>
            </div>
        );
    }

    // ── SUBMITTING ──
    if (step === "submitting") {
        return (
            <div className="flex items-center justify-center min-h-[300px]">
                <div className="text-center">
                    <div className="w-8 h-8 border-2 border-neon-cyan/30 border-t-neon-cyan rounded-full animate-spin mx-auto mb-3" />
                    <p className="text-slate-400">Klasifikuji AI systémy...</p>
                </div>
            </div>
        );
    }

    // ── DONE ──
    if (step === "done" && result) {
        return (
            <div className="max-w-2xl mx-auto">
                <div className="glass p-8 text-center">
                    <div className="text-5xl mb-4">&#x2705;</div>
                    <h2 className="text-xl font-bold text-white mb-2">Sebehodnocení dokončeno</h2>
                    <p className="text-slate-400 mb-6">{result.message}</p>

                    <div className="grid grid-cols-3 gap-4 mb-6">
                        <div className="bg-dark-800/50 rounded-lg p-3">
                            <div className="text-2xl font-bold text-white">{result.ai_systems_count}</div>
                            <div className="text-xs text-slate-500">AI systémů</div>
                        </div>
                        <div className="bg-dark-800/50 rounded-lg p-3">
                            <div className="text-2xl font-bold text-neon-fuchsia">{result.art50_relevant}</div>
                            <div className="text-xs text-slate-500">Article 50</div>
                        </div>
                        <div className="bg-dark-800/50 rounded-lg p-3">
                            <div className="text-2xl font-bold text-neon-cyan">{result.compliance_score}%</div>
                            <div className="text-xs text-slate-500">Compliance</div>
                        </div>
                    </div>

                    <button onClick={onComplete} className="btn-primary w-full py-3">
                        Přejít na dashboard
                    </button>
                </div>
            </div>
        );
    }

    // ── STEP FORM (chatbots / content / other) ──
    return (
        <div className="max-w-2xl mx-auto">
            {/* Progress bar */}
            <div className="flex gap-1 mb-6">
                {(["chatbots", "content", "other"] as const).map((s, i) => (
                    <div
                        key={s}
                        className={`h-1 flex-1 rounded-full transition-colors ${
                            (step === "chatbots" && i === 0) ||
                            (step === "content" && i <= 1) ||
                            (step === "other" && i <= 2)
                                ? "bg-neon-cyan"
                                : "bg-dark-700"
                        }`}
                    />
                ))}
            </div>

            <div className="glass p-6">
                {step === "chatbots" && (
                    <AISystemStep
                        title="Krok 1/3 — Chatboty a live chat"
                        description="Používáte na e-shopu chatbot nebo live chat s AI odpověďmi? Toto spadá pod Article 50 — zákazník musí být informován, že komunikuje s AI."
                        suggestions={KNOWN_CHATBOTS}
                        aiType="chatbot"
                        entries={chatbots}
                        onChange={setChatbots}
                        onNext={() => setStep("content")}
                        onBack={() => setStep("intro")}
                    />
                )}
                {step === "content" && (
                    <AISystemStep
                        title="Krok 2/3 — AI-generovaný obsah"
                        description="Generujete popisky produktů, texty na web nebo marketingové materiály pomocí AI? Pokud je obsah viditelný zákazníkům, spadá pod Article 50."
                        suggestions={KNOWN_CONTENT_AI}
                        aiType="content"
                        entries={contentAi}
                        onChange={setContentAi}
                        onNext={() => setStep("other")}
                        onBack={() => setStep("chatbots")}
                    />
                )}
                {step === "other" && (
                    <AISystemStep
                        title="Krok 3/3 — Ostatní AI systémy"
                        description="Používáte AI pro doporučení produktů, vyhledávání, dynamické ceny nebo jinou automatizaci? Tyto systémy spadají pod Article 4 (evidenční povinnost)."
                        suggestions={["Doporučovací engine", "AI vyhledávání", "Dynamické ceny", "Predikce poptávky", "AI customer scoring"]}
                        aiType="other"
                        entries={otherAi}
                        onChange={setOtherAi}
                        onNext={handleSubmit}
                        onBack={() => setStep("content")}
                        isLast
                    />
                )}

                {error && (
                    <div className="mt-4 p-3 rounded-lg bg-red-900/30 border border-red-500/30 text-red-300 text-sm">
                        {error}
                    </div>
                )}
            </div>
        </div>
    );
}

// ── Generická step komponenta pro přidávání AI systémů ──

interface AISystemStepProps {
    title: string;
    description: string;
    suggestions: string[];
    aiType: string;
    entries: AISystemEntry[];
    onChange: (entries: AISystemEntry[]) => void;
    onNext: () => void;
    onBack: () => void;
    isLast?: boolean;
}

function AISystemStep({ title, description, suggestions, aiType, entries, onChange, onNext, onBack, isLast }: AISystemStepProps) {
    const [showCustom, setShowCustom] = useState(false);
    const [customName, setCustomName] = useState("");

    const addEntry = (provider: string) => {
        // Zamezit duplicitám
        if (entries.some((e) => e.provider === provider)) return;
        onChange([...entries, {
            provider,
            ai_type: aiType as AISystemEntry["ai_type"],
            custom_note: "",
        }]);
    };

    const removeEntry = (index: number) => {
        onChange(entries.filter((_, i) => i !== index));
    };

    const addCustom = () => {
        const name = customName.trim();
        if (name && !entries.some((e) => e.provider === name)) {
            addEntry(name);
            setCustomName("");
            setShowCustom(false);
        }
    };

    return (
        <div>
            <h2 className="text-lg font-bold text-white mb-1">{title}</h2>
            <p className="text-sm text-slate-400 mb-5">{description}</p>

            {/* Suggestions chips */}
            <div className="mb-4">
                <p className="text-xs text-slate-500 mb-2">Klikněte na služby, které používáte:</p>
                <div className="flex flex-wrap gap-2">
                    {suggestions.map((s) => {
                        const isSelected = entries.some((e) => e.provider === s);
                        return (
                            <button
                                key={s}
                                onClick={() => isSelected ? removeEntry(entries.findIndex((e) => e.provider === s)) : addEntry(s)}
                                className={`px-3 py-1.5 rounded-full text-sm border transition-colors ${
                                    isSelected
                                        ? "bg-neon-cyan/20 border-neon-cyan/50 text-neon-cyan"
                                        : "bg-dark-800/50 border-white/10 text-slate-400 hover:border-white/20 hover:text-white"
                                }`}
                            >
                                {isSelected ? "\u2713 " : ""}{s}
                            </button>
                        );
                    })}
                </div>
            </div>

            {/* Vlastní */}
            {!showCustom ? (
                <button
                    onClick={() => setShowCustom(true)}
                    className="text-sm text-neon-cyan hover:text-neon-cyan/80 mb-4 inline-block"
                >
                    + Přidat jiný systém
                </button>
            ) : (
                <div className="flex gap-2 mb-4">
                    <input
                        type="text"
                        value={customName}
                        onChange={(e) => setCustomName(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && addCustom()}
                        placeholder="Název AI systému…"
                        className="flex-1 px-3 py-2 rounded-lg bg-dark-800 border border-white/10 text-white text-sm placeholder:text-slate-600 focus:border-neon-cyan/50 focus:outline-none"
                        maxLength={200}
                        autoFocus
                    />
                    <button onClick={addCustom} className="btn-primary px-4 py-2 text-sm">
                        Přidat
                    </button>
                    <button onClick={() => { setShowCustom(false); setCustomName(""); }} className="btn-secondary px-3 py-2 text-sm">
                        Zrušit
                    </button>
                </div>
            )}

            {/* Vybrané systémy */}
            {entries.length > 0 && (
                <div className="mb-6 space-y-2">
                    <p className="text-xs text-slate-500 mb-1">Vybrané ({entries.length}):</p>
                    {entries.map((entry, i) => (
                        <div key={i} className="flex items-center justify-between bg-dark-800/50 rounded-lg px-3 py-2 border border-white/5">
                            <span className="text-sm text-white">{entry.provider}</span>
                            <button
                                onClick={() => removeEntry(i)}
                                className="text-slate-500 hover:text-red-400 text-xs"
                            >
                                &#x2715;
                            </button>
                        </div>
                    ))}
                </div>
            )}

            {/* Navigace */}
            <div className="flex gap-3 pt-4 border-t border-white/5">
                <button onClick={onBack} className="btn-secondary flex-1 py-2.5">
                    Zpět
                </button>
                <button onClick={onNext} className="btn-primary flex-1 py-2.5">
                    {isLast ? "Dokončit sebehodnocení" : "Pokračovat"}
                </button>
            </div>

            {entries.length === 0 && (
                <p className="text-xs text-slate-600 text-center mt-3">
                    Žádné nevybrané? Nevadí — pokračujte dál.
                </p>
            )}
        </div>
    );
}
