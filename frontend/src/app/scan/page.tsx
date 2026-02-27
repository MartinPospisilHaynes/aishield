"use client";

import { useState, useEffect, useCallback, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
    startScan,
    getScanStatus,
    getScanFindings,
    confirmFinding,
    type ScanStatus,
    type Finding,
} from "@/lib/api";

// ── Progress stepper fáze ──
interface ScanPhase {
    id: string;
    label: string;
    icon: string;
    description: string;
    startSecond: number;  // Kdy se tato fáze typicky aktivuje
}

const SCAN_PHASES: ScanPhase[] = [
    {
        id: "connecting",
        label: "Připojování",
        icon: "🌐",
        description: "Spouštíme headless Chromium a připojujeme se k webu...",
        startSecond: 0,
    },
    {
        id: "loading",
        label: "Načítání stránky",
        icon: "📄",
        description: "Načítáme HTML, skripty, obrázky, cookies, zavíráme cookie lištu...",
        startSecond: 5,
    },
    {
        id: "network",
        label: "Síťová analýza",
        icon: "📡",
        description: "Zachytáváme všechny síťové požadavky a hledáme volání na AI API endpointy...",
        startSecond: 18,
    },
    {
        id: "detection",
        label: "AI detekce",
        icon: "🔎",
        description: "Signaturová detekce (75 vzorů) + heuristická analýza JavaScriptu, cookies, meta...",
        startSecond: 25,
    },
    {
        id: "classification",
        label: "AI klasifikace",
        icon: "🧠",
        description: "Claude AI ověřuje každý nález — je skutečně nasazený, nebo jen zmíněný v kódu?",
        startSecond: 32,
    },
    {
        id: "verification",
        label: "Verifikační sken",
        icon: "🔁",
        description: "Druhý nezávislý sken ověřuje stabilitu nálezů — double-scan consensus...",
        startSecond: 42,
    },
    {
        id: "saving",
        label: "Ukládání výsledků",
        icon: "💾",
        description: "Ukládáme výsledky do databáze a připravujeme report...",
        startSecond: 70,
    },
];

function ScanPageInner() {
    const searchParams = useSearchParams();
    const [url, setUrl] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [scanResult, setScanResult] = useState<ScanStatus | null>(null);
    const [findings, setFindings] = useState<Finding[]>([]);
    const [falsePositives, setFalsePositives] = useState<Finding[]>([]);
    const [aiClassified, setAiClassified] = useState(false);
    const [scanId, setScanId] = useState<string | null>(null);
    const pollingRef = useRef<NodeJS.Timeout | null>(null);

    // ── Progress tracking ──
    const [elapsedSeconds, setElapsedSeconds] = useState(0);
    const timerRef = useRef<NodeJS.Timeout | null>(null);
    const startTimeRef = useRef<number | null>(null);

    // Pokud přišel URL z homepage (?url=...)
    useEffect(() => {
        const urlParam = searchParams.get("url");
        if (urlParam) setUrl(urlParam);
    }, [searchParams]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (pollingRef.current) clearInterval(pollingRef.current);
            if (timerRef.current) clearInterval(timerRef.current);
        };
    }, []);

    // Start elapsed timer when loading begins
    useEffect(() => {
        if (loading) {
            startTimeRef.current = Date.now();
            setElapsedSeconds(0);
            timerRef.current = setInterval(() => {
                if (startTimeRef.current) {
                    setElapsedSeconds(
                        Math.floor((Date.now() - startTimeRef.current) / 1000)
                    );
                }
            }, 1000);
        } else {
            if (timerRef.current) {
                clearInterval(timerRef.current);
                timerRef.current = null;
            }
        }
    }, [loading]);

    // Determine current phase based on elapsed time
    const getCurrentPhaseIndex = () => {
        for (let i = SCAN_PHASES.length - 1; i >= 0; i--) {
            if (elapsedSeconds >= SCAN_PHASES[i].startSecond) return i;
        }
        return 0;
    };

    const currentPhaseIndex = getCurrentPhaseIndex();
    const currentPhase = SCAN_PHASES[currentPhaseIndex];

    // Progress percentage (0-100)
    const progressPercent = Math.min(
        95,
        Math.round((elapsedSeconds / 80) * 100)
    );

    const fetchFindings = useCallback(async (id: string) => {
        try {
            const res = await getScanFindings(id);
            setFindings(res.findings);
            setFalsePositives(res.false_positives || []);
            setAiClassified(res.ai_classified || false);
        } catch {
            // Tiché selhání
        }
    }, []);

    const startPolling = useCallback(
        (id: string) => {
            pollingRef.current = setInterval(async () => {
                try {
                    const status = await getScanStatus(id);
                    setScanResult(status);

                    if (status.status === "done" || status.status === "error") {
                        if (pollingRef.current) clearInterval(pollingRef.current);
                        pollingRef.current = null;
                        setLoading(false);
                        if (status.status === "done") {
                            await fetchFindings(id);
                        }
                    }
                } catch {
                    // Keep polling on transient errors
                }
            }, 3000);
        },
        [fetchFindings]
    );

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!url.trim()) return;

        setLoading(true);
        setError(null);
        setScanResult(null);
        setFindings([]);
        setFalsePositives([]);
        setAiClassified(false);
        setElapsedSeconds(0);
        if (pollingRef.current) clearInterval(pollingRef.current);

        try {
            const result = await startScan(url);
            setScanId(result.scan_id);
            const status = await getScanStatus(result.scan_id);
            setScanResult(status);

            if (status.status === "queued" || status.status === "running") {
                startPolling(result.scan_id);
            } else {
                setLoading(false);
                if (status.status === "done") {
                    await fetchFindings(result.scan_id);
                }
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "Nastala neočekávaná chyba");
            setLoading(false);
        }
    };

    const statusLabel = (status: string) => {
        switch (status) {
            case "queued": return "⏳ Ve frontě";
            case "running": return "🔄 Skenování probíhá...";
            case "done": return "✅ Dokončeno";
            case "error": return "❌ Chyba";
            default: return status;
        }
    };

    const statusColor = (status: string) => {
        switch (status) {
            case "queued": return "bg-yellow-500/10 text-yellow-400";
            case "running": return "bg-cyan-500/10 text-cyan-400";
            case "done": return "bg-green-500/10 text-green-400";
            case "error": return "bg-red-500/10 text-red-400";
            default: return "bg-white/10 text-slate-400";
        }
    };

    const riskBadge = (level: string) => {
        switch (level) {
            case "high": return "bg-red-500/10 text-red-400 border-red-500/20";
            case "limited": return "bg-amber-500/10 text-amber-400 border-amber-500/20";
            case "minimal": return "bg-green-500/10 text-green-400 border-green-500/20";
            default: return "bg-white/10 text-slate-400 border-white/10";
        }
    };

    const riskLabel = (level: string) => {
        switch (level) {
            case "high": return "🔴 Vysoké riziko";
            case "limited": return "🟡 Omezené riziko";
            case "minimal": return "🟢 Minimální riziko";
            default: return level;
        }
    };

    const categoryIcon = (cat: string) => {
        switch (cat) {
            case "chatbot": return "🤖";
            case "analytics": return "📊";
            case "recommender": return "🎯";
            case "content_gen": return "🖼️";
            default: return "🔍";
        }
    };

    const categoryLabel = (cat: string) => {
        switch (cat) {
            case "chatbot": return "Chatbot / Konverzační AI";
            case "analytics": return "Analytika / Sledování";
            case "recommender": return "Doporučovací systém";
            case "content_gen": return "Generování obsahu";
            default: return cat;
        }
    };

    const handleConfirm = async (findingId: string, confirmed: boolean) => {
        try {
            await confirmFinding(findingId, confirmed);
            setFindings((prev) =>
                prev.map((f) =>
                    f.id === findingId
                        ? { ...f, confirmed_by_client: confirmed ? "confirmed" : "rejected" }
                        : f
                )
            );
        } catch {
            // Tiché selhání
        }
    };

    const confirmBadge = (status: string | boolean | null) => {
        switch (status) {
            case "confirmed": return { label: "✅ Potvrzeno", cls: "bg-green-500/10 text-green-400 border-green-500/20" };
            case "rejected": return { label: "❌ Zamítnuto", cls: "bg-red-500/10 text-red-400 border-red-500/20" };
            default: return null;
        }
    };

    return (
        <section className="py-20">
            <div className="mx-auto max-w-4xl px-6">
                {/* Nadpis */}
                <div className="text-center">
                    <h1 className="text-3xl font-extrabold">🔍 Skenovat web</h1>
                    <p className="mt-4 text-slate-400">
                        Zadejte URL vašeho webu a zjistěte, jaké AI systémy na něm
                        běží a jestli splňujete EU AI Act.
                    </p>
                </div>

                {/* Formulář */}
                <form onSubmit={handleSubmit} className="mt-8 flex gap-3 max-w-xl mx-auto">
                    <input
                        type="text"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        placeholder="https://vasefirma.cz"
                        className="flex-1 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/30 transition-all"
                        required
                        disabled={loading}
                    />
                    <button
                        type="submit"
                        className="btn-primary whitespace-nowrap disabled:opacity-50"
                        disabled={loading}
                    >
                        {loading ? "⏳ Skenuji..." : "🔍 Skenovat"}
                    </button>
                </form>

                {/* Chyba */}
                {error && (
                    <div className="mt-6 rounded-xl bg-red-500/10 border border-red-500/20 p-4 text-center">
                        <p className="text-sm text-red-400">❌ {error}</p>
                        <p className="mt-1 text-xs text-red-300">
                            Zkontrolujte, zda je URL správná a zkuste to znovu.
                        </p>
                    </div>
                )}

                {/* ═══════════════════════════════════════════════════════ */}
                {/* PROGRESS STEPPER — běží během skenování              */}
                {/* ═══════════════════════════════════════════════════════ */}
                {scanResult && (scanResult.status === "queued" || scanResult.status === "running") && (
                    <div className="mt-8 card">
                        {/* Hlavička s timerem */}
                        <div className="text-center mb-6">
                            <div className="text-4xl mb-2">🛡️</div>
                            <h2 className="text-lg font-semibold text-gray-900">
                                {statusLabel(scanResult.status)}
                            </h2>
                            <p className="mt-1 text-sm text-gray-500">
                                Hloubková analýza {scanResult.url}
                            </p>
                            {/* Timer */}
                            <div className="mt-3 inline-flex items-center gap-2 bg-cyan-500/10 border border-cyan-500/20 rounded-full px-4 py-1.5">
                                <span className="text-lg font-mono font-bold text-cyan-400">
                                    {Math.floor(elapsedSeconds / 60)}:{String(elapsedSeconds % 60).padStart(2, "0")}
                                </span>
                                <span className="text-xs text-cyan-400/60">uplynulo</span>
                            </div>
                        </div>

                        {/* Progress bar */}
                        <div className="relative mb-6">
                            <div className="h-2 w-full bg-white/10 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-fuchsia-500 to-cyan-500 rounded-full transition-all duration-1000 ease-out"
                                    style={{ width: `${progressPercent}%` }}
                                />
                            </div>
                            <div className="mt-1 flex justify-between text-xs text-gray-400">
                                <span>{progressPercent}%</span>
                                <span>~45–90 s</span>
                            </div>
                        </div>

                        {/* Aktuální fáze — zvýrazněná */}
                        <div className="mb-4 rounded-xl bg-cyan-500/10 border border-cyan-500/20 p-4">
                            <div className="flex items-center gap-3">
                                <span className="text-2xl animate-pulse">{currentPhase.icon}</span>
                                <div>
                                    <p className="font-semibold text-cyan-300 text-sm">
                                        Fáze {currentPhaseIndex + 1}/{SCAN_PHASES.length}: {currentPhase.label}
                                    </p>
                                    <p className="text-xs text-cyan-400/70 mt-0.5">
                                        {currentPhase.description}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Stepper — všechny fáze */}
                        <div className="space-y-1">
                            {SCAN_PHASES.map((phase, idx) => {
                                const isCompleted = idx < currentPhaseIndex;
                                const isCurrent = idx === currentPhaseIndex;
                                const isPending = idx > currentPhaseIndex;

                                return (
                                    <div
                                        key={phase.id}
                                        className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-500 ${
                                            isCurrent
                                                ? "bg-cyan-500/5"
                                                : isCompleted
                                                    ? "opacity-60"
                                                    : "opacity-30"
                                        }`}
                                    >
                                        {/* Ikona stavu */}
                                        <div className="w-6 h-6 flex items-center justify-center shrink-0">
                                            {isCompleted ? (
                                                <span className="text-green-400 text-sm">✓</span>
                                            ) : isCurrent ? (
                                                <span className="text-sm animate-spin">⏳</span>
                                            ) : (
                                                <span className="w-2 h-2 rounded-full bg-slate-600 block" />
                                            )}
                                        </div>

                                        {/* Label */}
                                        <span className={`text-sm ${
                                            isCurrent
                                                ? "font-medium text-cyan-300"
                                                : isCompleted
                                                    ? "text-slate-500 line-through"
                                                    : "text-slate-600"
                                        }`}>
                                            {phase.icon} {phase.label}
                                        </span>
                                    </div>
                                );
                            })}
                        </div>

                        {/* Footer */}
                        <div className="mt-4 pt-3 border-t border-white/[0.06] flex justify-between items-center text-xs text-slate-500">
                            <span>Scan ID: {scanResult.scan_id.slice(0, 8)}...</span>
                            <span>
                                7 fází analýzy • headless Chromium • AI klasifikace
                            </span>
                        </div>
                    </div>
                )}

                {/* Výsledek — hotový sken */}
                {scanResult && scanResult.status === "done" && (
                    <div className="mt-8 space-y-6">
                        {/* Summary karta */}
                        <div className="card">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-lg font-semibold text-white">Výsledek skenu</h2>
                                <span className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ${statusColor(scanResult.status)}`}>
                                    {statusLabel(scanResult.status)}
                                </span>
                            </div>

                            <div className="space-y-3 text-sm">
                                <div className="flex justify-between border-b border-white/[0.06] pb-2">
                                    <span className="text-slate-500">URL</span>
                                    <span className="font-medium text-slate-200">{scanResult.url}</span>
                                </div>
                                {scanResult.company_name && (
                                    <div className="flex justify-between border-b border-white/[0.06] pb-2">
                                        <span className="text-slate-500">Firma</span>
                                        <span className="font-medium text-slate-200">{scanResult.company_name}</span>
                                    </div>
                                )}
                                <div className="flex justify-between border-b border-white/[0.06] pb-2">
                                    <span className="text-slate-500">Nalezené AI systémy</span>
                                    <span className="font-bold text-xl text-white">{findings.length}</span>
                                </div>
                                {/* Metody analýzy */}
                                <div className="flex justify-between border-b border-white/[0.06] pb-2">
                                    <span className="text-slate-500">Metody analýzy</span>
                                    <div className="flex flex-wrap gap-1 justify-end">
                                        <span className="inline-flex items-center rounded-full bg-white/10 px-2 py-0.5 text-xs text-slate-400">📡 Síťová</span>
                                        <span className="inline-flex items-center rounded-full bg-white/10 px-2 py-0.5 text-xs text-slate-400">🔎 Signaturová</span>
                                        <span className="inline-flex items-center rounded-full bg-white/10 px-2 py-0.5 text-xs text-slate-400">🔁 Double-scan</span>
                                        {aiClassified && (
                                            <span className="inline-flex items-center rounded-full bg-purple-500/10 border border-purple-500/20 px-2 py-0.5 text-xs text-purple-400">🧠 AI verified</span>
                                        )}
                                    </div>
                                </div>
                                {aiClassified && (
                                    <div className="flex justify-between border-b border-white/[0.06] pb-2">
                                        <span className="text-gray-500">AI ověření</span>
                                        <span className="inline-flex items-center gap-1 text-sm font-medium text-purple-700">
                                            🧠 Claude AI verified
                                            {falsePositives.length > 0 && (
                                                <span className="text-xs text-gray-400 ml-1">
                                                    ({falsePositives.length} false-positive vyřazeno)
                                                </span>
                                            )}
                                        </span>
                                    </div>
                                )}
                                {scanResult.started_at && (
                                    <div className="flex justify-between border-b border-white/[0.06] pb-2">
                                        <span className="text-slate-500">Zahájeno</span>
                                        <span className="text-slate-400">
                                            {new Date(scanResult.started_at).toLocaleString("cs-CZ")}
                                        </span>
                                    </div>
                                )}
                                {scanResult.finished_at && (
                                    <div className="flex justify-between">
                                        <span className="text-slate-500">Dokončeno</span>
                                        <span className="text-slate-400">
                                            {new Date(scanResult.finished_at).toLocaleString("cs-CZ")}
                                        </span>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Findings list */}
                        {findings.length > 0 ? (
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                                    🤖 Nalezené AI systémy ({findings.length})
                                </h3>
                                <div className="space-y-4">
                                    {findings.map((f) => (
                                        <div
                                            key={f.id}
                                            className="card border-l-4"
                                            style={{
                                                borderLeftColor:
                                                    f.risk_level === "high"
                                                        ? "#ef4444"
                                                        : f.risk_level === "limited"
                                                            ? "#f97316"
                                                            : "#22c55e",
                                            }}
                                        >
                                            <div className="flex items-start justify-between">
                                                <div>
                                                    <h4 className="font-semibold text-slate-200">
                                                        {categoryIcon(f.category)} {f.name}
                                                    </h4>
                                                    <p className="text-xs text-slate-500 mt-1">
                                                        {categoryLabel(f.category)}
                                                    </p>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    {f.source === "ai_classified" && (
                                                        <span className="inline-flex items-center rounded-full bg-purple-50 border border-purple-200 px-2 py-0.5 text-xs font-medium text-purple-700">
                                                            🧠 AI verified
                                                        </span>
                                                    )}
                                                    {f.signature_matched?.includes("network_intercept") && (
                                                        <span className="inline-flex items-center rounded-full bg-blue-50 border border-blue-200 px-2 py-0.5 text-xs font-medium text-blue-700">
                                                            📡 Síťový důkaz
                                                        </span>
                                                    )}
                                                    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${riskBadge(f.risk_level)}`}>
                                                        {riskLabel(f.risk_level)}
                                                    </span>
                                                </div>
                                            </div>

                                            {f.ai_classification_text && (
                                                <p className="mt-2 text-sm text-slate-400 italic">
                                                    {f.ai_classification_text}
                                                </p>
                                            )}

                                            <div className="mt-3 space-y-2 text-sm">
                                                {f.ai_act_article && (
                                                    <div className="flex gap-2">
                                                        <span className="text-slate-500 shrink-0">📜 Článek:</span>
                                                        <span className="text-slate-300">{f.ai_act_article}</span>
                                                    </div>
                                                )}
                                                {f.action_required && (
                                                    <div className="flex gap-2">
                                                        <span className="text-slate-500 shrink-0">⚡ Požadovaná akce:</span>
                                                        <span className="text-slate-300">{f.action_required}</span>
                                                    </div>
                                                )}
                                                {f.signature_matched && (
                                                    <div className="flex gap-2">
                                                        <span className="text-slate-500 shrink-0">🔎 Detekováno:</span>
                                                        <span className="font-mono text-xs text-slate-400">{f.signature_matched}</span>
                                                    </div>
                                                )}
                                            </div>

                                            {/* Potvrzení klientem */}
                                            <div className="mt-3 pt-3 border-t border-white/[0.06] flex items-center justify-between">
                                                {confirmBadge(f.confirmed_by_client) ? (
                                                    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${confirmBadge(f.confirmed_by_client)!.cls}`}>
                                                        {confirmBadge(f.confirmed_by_client)!.label}
                                                    </span>
                                                ) : (
                                                    <span className="text-xs text-slate-500">Čeká na potvrzení</span>
                                                )}
                                                <div className="flex gap-2">
                                                    <button
                                                        onClick={() => handleConfirm(f.id, true)}
                                                        className="text-xs px-3 py-1 rounded-full bg-green-500/10 text-green-400 border border-green-500/20 hover:bg-green-500/20 transition-colors"
                                                        disabled={f.confirmed_by_client === "confirmed"}
                                                    >
                                                        ✅ Potvrdit
                                                    </button>
                                                    <button
                                                        onClick={() => handleConfirm(f.id, false)}
                                                        className="text-xs px-3 py-1 rounded-full bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 transition-colors"
                                                        disabled={f.confirmed_by_client === "rejected"}
                                                    >
                                                        ❌ Zamítnout
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ) : (
                            <div className="card text-center">
                                <div className="text-4xl mb-2">🎉</div>
                                <h3 className="font-semibold text-white">Žádné AI systémy nenalezeny</h3>
                                <p className="text-sm text-gray-500 mt-1">
                                    Na tomto webu jsme nezjistili žádné AI systémy spadající pod EU AI Act.
                                </p>
                            </div>
                        )}

                        {/* False Positives */}
                        {falsePositives.length > 0 && (
                            <details className="group">
                                <summary className="cursor-pointer text-sm text-slate-500 hover:text-slate-300 transition-colors">
                                    👻 Vyřazené false-positives ({falsePositives.length}) — AI systémy zmíněné, ale nenasazené
                                </summary>
                                <div className="mt-3 space-y-2">
                                    {falsePositives.map((f) => (
                                        <div key={f.id} className="rounded-xl bg-white/5 border border-white/10 p-3 opacity-60">
                                            <div className="flex items-center justify-between">
                                                <span className="text-sm text-slate-500 line-through">
                                                    {categoryIcon(f.category)} {f.name}
                                                </span>
                                                <span className="text-xs bg-white/10 text-slate-500 rounded-full px-2 py-0.5">
                                                    false-positive
                                                </span>
                                            </div>
                                            {f.action_required && (
                                                <p className="text-xs text-slate-500 mt-1">{f.action_required}</p>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </details>
                        )}

                        {/* CTA */}
                        <div className="glass text-center border-fuchsia-500/20">
                            <h3 className="font-semibold text-white">📄 Stáhnout compliance report</h3>
                            <p className="text-sm text-slate-400 mt-2">
                                Kompletní HTML report s doporučeními dle EU AI Act — pro tisk nebo sdílení.
                            </p>
                            {scanId && (
                                <a
                                    href={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/scan/${scanId}/report`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-block mt-4 btn-primary"
                                >
                                    📄 Zobrazit report →
                                </a>
                            )}
                        </div>

                        <div className="glass text-center">
                            <h3 className="font-semibold text-white">📝 Interní AI dotazník</h3>
                            <p className="text-sm text-slate-400 mt-2">
                                Skener vidí jen web — vyplňte 5minutový dotazník o interních AI systémech
                                (ChatGPT, Copilot, HR AI...) pro kompletní compliance přehled.
                            </p>
                            {scanId && scanResult && (
                                <a
                                    href={`/dotaznik?company_id=${scanResult.company_id}&scan_id=${scanId}`}
                                    className="inline-block mt-4 btn-primary"
                                >
                                    📝 Vyplnit dotazník →
                                </a>
                            )}
                        </div>

                        <div className="glass text-center">
                            <h3 className="font-semibold text-white">💡 Chcete podrobnou analýzu?</h3>
                            <p className="text-sm text-slate-400 mt-2">
                                Tento sken je základní (FREE). Pro detailní AI Act compliance audit
                                s právními doporučeními objednejte placenou verzi.
                            </p>
                            <a href="/pricing" className="inline-block mt-4 btn-primary">
                                Zobrazit ceník →
                            </a>
                        </div>
                    </div>
                )}

                {/* Error stav */}
                {scanResult && scanResult.status === "error" && (
                    <div className="mt-8 card text-center">
                        <div className="text-4xl mb-2">⚠️</div>
                        <h2 className="text-lg font-semibold text-white">Skenování selhalo</h2>
                        <p className="mt-2 text-sm text-slate-400">
                            Nepodařilo se naskenovat {scanResult.url}. Web může být nedostupný
                            nebo blokuje automatické přístupy.
                        </p>
                        <button
                            onClick={() => handleSubmit({ preventDefault: () => { } } as React.FormEvent)}
                            className="mt-4 btn-primary"
                        >
                            🔄 Zkusit znovu
                        </button>
                    </div>
                )}

                {/* Info box (před skenem) */}
                {!scanResult && !loading && (
                    <div className="mt-12 card text-center">
                        <h3 className="font-semibold text-white mb-3">Jak skenování funguje?</h3>

                        {/* Fáze jako mini timeline */}
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                            <div className="rounded-xl bg-white/5 border border-white/[0.06] p-3">
                                <div className="text-xl mb-1">📡</div>
                                <p className="text-xs font-medium text-slate-300">Síťová analýza</p>
                                <p className="text-xs text-slate-500 mt-0.5">Zachytáváme požadavky na AI API</p>
                            </div>
                            <div className="rounded-xl bg-white/5 border border-white/[0.06] p-3">
                                <div className="text-xl mb-1">🔎</div>
                                <p className="text-xs font-medium text-slate-300">75 signatur</p>
                                <p className="text-xs text-slate-500 mt-0.5">Ověřené vzory AI systémů</p>
                            </div>
                            <div className="rounded-xl bg-white/5 border border-white/[0.06] p-3">
                                <div className="text-xl mb-1">🧠</div>
                                <p className="text-xs font-medium text-slate-300">AI klasifikace</p>
                                <p className="text-xs text-slate-500 mt-0.5">Claude ověřuje každý nález</p>
                            </div>
                            <div className="rounded-xl bg-white/5 border border-white/[0.06] p-3">
                                <div className="text-xl mb-1">🔁</div>
                                <p className="text-xs font-medium text-slate-300">Double-scan</p>
                                <p className="text-xs text-slate-500 mt-0.5">Druhý sken ověří stabilitu</p>
                            </div>
                        </div>

                        <ul className="text-sm text-slate-400 space-y-1 text-left max-w-xs mx-auto">
                            <li>🤖 Chatboty (Smartsupp, Tidio, Intercom...)</li>
                            <li>📊 AI analytiku (GA4, Hotjar s AI features...)</li>
                            <li>🎯 AI doporučovací systémy</li>
                            <li>🖼️ AI generovaný obsah</li>
                            <li>📡 Skryté AI API volání (OpenAI, Gemini...)</li>
                        </ul>

                        <div className="mt-4 rounded-xl bg-amber-500/10 border border-amber-500/20 p-3">
                            <p className="text-sm font-medium text-amber-400">
                                ⏱️ Hloubková analýza trvá 45–90 sekund
                            </p>
                            <p className="text-xs text-amber-300/70 mt-1">
                                Provádíme 7 fází analýzy včetně síťové interceptace,
                                AI klasifikace a verifikačního double-skenu.
                                Prosím vyčkejte — jde o důkladný test, ne rychlý povrchní sken.
                            </p>
                        </div>
                    </div>
                )}
            </div>
        </section>
    );
}

export default function ScanPage() {
    return (
        <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><p>Načítám...</p></div>}>
            <ScanPageInner />
        </Suspense>
    );
}
