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

    // Pokud přišel URL z homepage (?url=...)
    useEffect(() => {
        const urlParam = searchParams.get("url");
        if (urlParam) setUrl(urlParam);
    }, [searchParams]);

    // Cleanup polling on unmount
    useEffect(() => {
        return () => {
            if (pollingRef.current) clearInterval(pollingRef.current);
        };
    }, []);

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
            case "queued": return "bg-yellow-100 text-yellow-800";
            case "running": return "bg-blue-100 text-blue-800";
            case "done": return "bg-green-100 text-green-800";
            case "error": return "bg-red-100 text-red-800";
            default: return "bg-gray-100 text-gray-800";
        }
    };

    const riskBadge = (level: string) => {
        switch (level) {
            case "high": return "bg-red-100 text-red-800 border-red-200";
            case "limited": return "bg-orange-100 text-orange-800 border-orange-200";
            case "minimal": return "bg-green-100 text-green-800 border-green-200";
            default: return "bg-gray-100 text-gray-800 border-gray-200";
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
            // Aktualizujeme lokální stav
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
            case "confirmed": return { label: "✅ Potvrzeno", cls: "bg-green-50 text-green-700 border-green-200" };
            case "rejected": return { label: "❌ Zamítnuto", cls: "bg-red-50 text-red-700 border-red-200" };
            default: return null;
        }
    };

    return (
        <section className="py-20">
            <div className="mx-auto max-w-4xl px-6">
                {/* Nadpis */}
                <div className="text-center">
                    <h1 className="text-3xl font-bold text-gray-900">🔍 Skenovat web</h1>
                    <p className="mt-4 text-gray-500">
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
                        className="flex-1 rounded-lg border border-gray-300 px-4 py-3 focus:ring-2 focus:ring-shield-500 focus:border-shield-500"
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
                    <div className="mt-6 rounded-lg bg-red-50 border border-red-200 p-4 text-center">
                        <p className="text-sm text-red-700">❌ {error}</p>
                        <p className="mt-1 text-xs text-red-500">
                            Zkontrolujte, zda je URL správná a zkuste to znovu.
                        </p>
                    </div>
                )}

                {/* Průběh skenování */}
                {scanResult && (scanResult.status === "queued" || scanResult.status === "running") && (
                    <div className="mt-8 card text-center">
                        <div className="animate-pulse">
                            <div className="text-4xl mb-4">🛡️</div>
                            <h2 className="text-lg font-semibold text-gray-900">
                                {statusLabel(scanResult.status)}
                            </h2>
                            <p className="mt-2 text-sm text-gray-500">
                                Analyzujeme {scanResult.url} — hledáme AI systémy,
                                kontrolujeme cookies, skripty a síťové požadavky...
                            </p>
                            <div className="mt-4 flex justify-center">
                                <div className="h-2 w-48 bg-gray-200 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-shield-500 rounded-full animate-[loading_2s_ease-in-out_infinite]"
                                        style={{ width: "60%" }}
                                    />
                                </div>
                            </div>
                            <p className="mt-2 text-xs text-gray-400">Scan ID: {scanResult.scan_id}</p>
                        </div>
                    </div>
                )}

                {/* Výsledek — hotový sken */}
                {scanResult && scanResult.status === "done" && (
                    <div className="mt-8 space-y-6">
                        {/* Summary karta */}
                        <div className="card">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-lg font-semibold text-gray-900">Výsledek skenu</h2>
                                <span className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ${statusColor(scanResult.status)}`}>
                                    {statusLabel(scanResult.status)}
                                </span>
                            </div>

                            <div className="space-y-3 text-sm">
                                <div className="flex justify-between border-b border-gray-100 pb-2">
                                    <span className="text-gray-500">URL</span>
                                    <span className="font-medium text-gray-900">{scanResult.url}</span>
                                </div>
                                {scanResult.company_name && (
                                    <div className="flex justify-between border-b border-gray-100 pb-2">
                                        <span className="text-gray-500">Firma</span>
                                        <span className="font-medium text-gray-900">{scanResult.company_name}</span>
                                    </div>
                                )}
                                <div className="flex justify-between border-b border-gray-100 pb-2">
                                    <span className="text-gray-500">Nalezené AI systémy</span>
                                    <span className="font-bold text-xl text-gray-900">{findings.length}</span>
                                </div>
                                {aiClassified && (
                                    <div className="flex justify-between border-b border-gray-100 pb-2">
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
                                    <div className="flex justify-between border-b border-gray-100 pb-2">
                                        <span className="text-gray-500">Zahájeno</span>
                                        <span className="text-gray-600">
                                            {new Date(scanResult.started_at).toLocaleString("cs-CZ")}
                                        </span>
                                    </div>
                                )}
                                {scanResult.finished_at && (
                                    <div className="flex justify-between">
                                        <span className="text-gray-500">Dokončeno</span>
                                        <span className="text-gray-600">
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
                                                    <h4 className="font-semibold text-gray-900">
                                                        {categoryIcon(f.category)} {f.name}
                                                    </h4>
                                                    <p className="text-xs text-gray-500 mt-1">
                                                        {categoryLabel(f.category)}
                                                    </p>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    {f.source === "ai_classified" && (
                                                        <span className="inline-flex items-center rounded-full bg-purple-50 border border-purple-200 px-2 py-0.5 text-xs font-medium text-purple-700">
                                                            🧠 AI verified
                                                        </span>
                                                    )}
                                                    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${riskBadge(f.risk_level)}`}>
                                                        {riskLabel(f.risk_level)}
                                                    </span>
                                                </div>
                                            </div>

                                            {f.ai_classification_text && (
                                                <p className="mt-2 text-sm text-gray-600 italic">
                                                    {f.ai_classification_text}
                                                </p>
                                            )}

                                            <div className="mt-3 space-y-2 text-sm">
                                                {f.ai_act_article && (
                                                    <div className="flex gap-2">
                                                        <span className="text-gray-500 shrink-0">📜 Článek:</span>
                                                        <span className="text-gray-700">{f.ai_act_article}</span>
                                                    </div>
                                                )}
                                                {f.action_required && (
                                                    <div className="flex gap-2">
                                                        <span className="text-gray-500 shrink-0">⚡ Požadovaná akce:</span>
                                                        <span className="text-gray-700">{f.action_required}</span>
                                                    </div>
                                                )}
                                                {f.signature_matched && (
                                                    <div className="flex gap-2">
                                                        <span className="text-gray-500 shrink-0">🔎 Detekováno:</span>
                                                        <span className="font-mono text-xs text-gray-600">{f.signature_matched}</span>
                                                    </div>
                                                )}
                                            </div>

                                            {/* Potvrzení klientem */}
                                            <div className="mt-3 pt-3 border-t border-gray-100 flex items-center justify-between">
                                                {confirmBadge(f.confirmed_by_client) ? (
                                                    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${confirmBadge(f.confirmed_by_client)!.cls}`}>
                                                        {confirmBadge(f.confirmed_by_client)!.label}
                                                    </span>
                                                ) : (
                                                    <span className="text-xs text-gray-400">Čeká na potvrzení</span>
                                                )}
                                                <div className="flex gap-2">
                                                    <button
                                                        onClick={() => handleConfirm(f.id, true)}
                                                        className="text-xs px-3 py-1 rounded-full bg-green-50 text-green-700 border border-green-200 hover:bg-green-100 transition-colors"
                                                        disabled={f.confirmed_by_client === "confirmed"}
                                                    >
                                                        ✅ Potvrdit
                                                    </button>
                                                    <button
                                                        onClick={() => handleConfirm(f.id, false)}
                                                        className="text-xs px-3 py-1 rounded-full bg-red-50 text-red-700 border border-red-200 hover:bg-red-100 transition-colors"
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
                                <h3 className="font-semibold text-gray-900">Žádné AI systémy nenalezeny</h3>
                                <p className="text-sm text-gray-500 mt-1">
                                    Na tomto webu jsme nezjistili žádné AI systémy spadající pod EU AI Act.
                                </p>
                            </div>
                        )}

                        {/* False Positives — kolapsovatená sekce */}
                        {falsePositives.length > 0 && (
                            <details className="group">
                                <summary className="cursor-pointer text-sm text-gray-400 hover:text-gray-600 transition-colors">
                                    👻 Vyřazené false-positives ({falsePositives.length}) — AI systémy zmíněné, ale nenasazené
                                </summary>
                                <div className="mt-3 space-y-2">
                                    {falsePositives.map((f) => (
                                        <div key={f.id} className="rounded-lg bg-gray-50 border border-gray-200 p-3 opacity-60">
                                            <div className="flex items-center justify-between">
                                                <span className="text-sm text-gray-500 line-through">
                                                    {categoryIcon(f.category)} {f.name}
                                                </span>
                                                <span className="text-xs bg-gray-200 text-gray-500 rounded-full px-2 py-0.5">
                                                    false-positive
                                                </span>
                                            </div>
                                            {f.action_required && (
                                                <p className="text-xs text-gray-400 mt-1">{f.action_required}</p>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </details>
                        )}

                        {/* CTA */}
                        <div className="card bg-shield-50 border border-shield-200 text-center">
                            <h3 className="font-semibold text-shield-900">� Stáhnout compliance report</h3>
                            <p className="text-sm text-shield-700 mt-2">
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

                        <div className="card bg-gray-50 border border-gray-200 text-center">
                            <h3 className="font-semibold text-gray-900">� Interní AI dotazník</h3>
                            <p className="text-sm text-gray-600 mt-2">
                                Skener vidí jen web — vyplňte 5minutový dotazník o interních AI systémech
                                (ChatGPT, Copilot, HR AI...) pro kompletní compliance přehled.
                            </p>
                            {scanId && scanResult && (
                                <a
                                    href={`/dotaznik?company_id=${scanResult.company_id}&scan_id=${scanId}`}
                                    className="inline-block mt-4 bg-purple-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-purple-700 transition"
                                >
                                    📝 Vyplnit dotazník →
                                </a>
                            )}
                        </div>

                        <div className="card bg-gray-50 border border-gray-200 text-center">
                            <h3 className="font-semibold text-gray-900">�💡 Chcete podrobnou analýzu?</h3>
                            <p className="text-sm text-gray-600 mt-2">
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
                        <h2 className="text-lg font-semibold text-gray-900">Skenování selhalo</h2>
                        <p className="mt-2 text-sm text-gray-500">
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
                        <h3 className="font-semibold text-gray-900 mb-2">Co skenujeme?</h3>
                        <ul className="text-sm text-gray-500 space-y-1">
                            <li>🤖 Chatboty (Smartsupp, Tidio, Intercom...)</li>
                            <li>📊 AI analytiku (GA4, Hotjar s AI features...)</li>
                            <li>🎯 AI doporučovací systémy</li>
                            <li>🖼️ AI generovaný obsah</li>
                            <li>🔍 AI vyhledávání na webu</li>
                        </ul>
                        <p className="mt-4 text-xs text-gray-400">
                            Skenování trvá 15–30 sekund. Používáme Playwright headless browser
                            pro realistickou simulaci.
                        </p>
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