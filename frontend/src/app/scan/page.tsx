"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { startScan, getScanStatus, type ScanStatus } from "@/lib/api";

export default function ScanPage() {
    const searchParams = useSearchParams();
    const [url, setUrl] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [scanResult, setScanResult] = useState<ScanStatus | null>(null);
    const [scanId, setScanId] = useState<string | null>(null);

    // Pokud přišel URL z homepage (?url=...)
    useEffect(() => {
        const urlParam = searchParams.get("url");
        if (urlParam) {
            setUrl(urlParam);
        }
    }, [searchParams]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!url.trim()) return;

        setLoading(true);
        setError(null);
        setScanResult(null);

        try {
            // 1. Spustíme sken
            const result = await startScan(url);
            setScanId(result.scan_id);

            // 2. Hned načteme stav
            const status = await getScanStatus(result.scan_id);
            setScanResult(status);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Nastala neočekávaná chyba");
        } finally {
            setLoading(false);
        }
    };

    const statusLabel = (status: string) => {
        switch (status) {
            case "queued": return "⏳ Ve frontě";
            case "running": return "🔄 Probíhá skenování...";
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

    return (
        <section className="py-20">
            <div className="mx-auto max-w-3xl px-6">
                {/* Nadpis */}
                <div className="text-center">
                    <h1 className="text-3xl font-bold text-gray-900">
                        🔍 Skenovat web
                    </h1>
                    <p className="mt-4 text-gray-500">
                        Zadejte URL vašeho webu a zjistěte, jaké AI systémy na něm běží
                        a jestli splňujete EU AI Act.
                    </p>
                </div>

                {/* Formulář */}
                <form onSubmit={handleSubmit} className="mt-8 flex gap-3 max-w-xl mx-auto">
                    <input
                        type="text"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        placeholder="https://vasefirma.cz"
                        className="flex-1 rounded-lg border border-gray-300 px-4 py-3
                            focus:ring-2 focus:ring-shield-500 focus:border-shield-500"
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

                {/* Výsledek */}
                {scanResult && (
                    <div className="mt-8 card">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-lg font-semibold text-gray-900">
                                Výsledek skenu
                            </h2>
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
                                <span className="text-gray-500">Scan ID</span>
                                <span className="font-mono text-xs text-gray-600">{scanResult.scan_id}</span>
                            </div>
                            <div className="flex justify-between border-b border-gray-100 pb-2">
                                <span className="text-gray-500">Počet nálezů</span>
                                <span className="font-bold text-gray-900">{scanResult.total_findings}</span>
                            </div>
                            {scanResult.started_at && (
                                <div className="flex justify-between">
                                    <span className="text-gray-500">Zahájeno</span>
                                    <span className="text-gray-600">
                                        {new Date(scanResult.started_at).toLocaleString("cs-CZ")}
                                    </span>
                                </div>
                            )}
                        </div>

                        {/* Info banner pro queued stav */}
                        {scanResult.status === "queued" && (
                            <div className="mt-6 rounded-lg bg-shield-50 border border-shield-200 p-4">
                                <p className="text-sm text-shield-800">
                                    🛡️ <strong>Sken byl zařazen do fronty.</strong>{" "}
                                    Plný AI Act scanner bude aktivní po dokončení Fáze B.
                                    Prozatím byl vytvořen záznam o vaší firmě a skenu v databázi.
                                </p>
                            </div>
                        )}
                    </div>
                )}

                {/* Info box */}
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
                    </div>
                )}
            </div>
        </section>
    );
}
