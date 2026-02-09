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

/* ── Inline SVG Icon helpers (Heroicons-style) ── */

const IconSearch = ({ className = "w-5 h-5" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
    </svg>
);

const IconCpu = ({ className = "w-5 h-5" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 3v1.5M4.5 8.25H3m18 0h-1.5M4.5 12H3m18 0h-1.5m-15 3.75H3m18 0h-1.5M8.25 19.5V21M12 3v1.5m0 15V21m3.75-18v1.5m0 15V21m-9-1.5h10.5a2.25 2.25 0 0 0 2.25-2.25V6.75a2.25 2.25 0 0 0-2.25-2.25H6.75A2.25 2.25 0 0 0 4.5 6.75v10.5a2.25 2.25 0 0 0 2.25 2.25Zm.75-12h9v9h-9v-9Z" />
    </svg>
);

const IconChartBar = ({ className = "w-5 h-5" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
    </svg>
);

const IconTarget = ({ className = "w-5 h-5" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-3-2.818.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
    </svg>
);

const IconPhoto = ({ className = "w-5 h-5" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909M2.25 18V6a2.25 2.25 0 0 1 2.25-2.25h15A2.25 2.25 0 0 1 21.75 6v12A2.25 2.25 0 0 1 19.5 20.25H4.5A2.25 2.25 0 0 1 2.25 18Z" />
    </svg>
);

const IconShield = ({ className = "w-5 h-5" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" />
    </svg>
);

const IconCheckCircle = ({ className = "w-5 h-5" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
    </svg>
);

const IconXCircle = ({ className = "w-5 h-5" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="m9.75 9.75 4.5 4.5m0-4.5-4.5 4.5M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
    </svg>
);

const IconClock = ({ className = "w-5 h-5" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
    </svg>
);

const IconArrowPath = ({ className = "w-5 h-5" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.992 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182M2.985 19.644l3.181-3.182" />
    </svg>
);

const IconSparkles = ({ className = "w-5 h-5" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 0 0-2.455 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" />
    </svg>
);

const IconDocument = ({ className = "w-5 h-5" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
    </svg>
);

const IconBolt = ({ className = "w-5 h-5" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="m3.75 13.5 10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75Z" />
    </svg>
);

const IconExclamationTriangle = ({ className = "w-5 h-5" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
    </svg>
);

const IconEyeSlash = ({ className = "w-5 h-5" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 0 0 1.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.451 10.451 0 0 1 12 4.5c4.756 0 8.773 3.162 10.065 7.498a10.522 10.522 0 0 1-4.293 5.774M6.228 6.228 3 3m3.228 3.228 3.65 3.65m7.894 7.894L21 21m-3.228-3.228-3.65-3.65m0 0a3 3 0 1 0-4.243-4.243m4.242 4.242L9.88 9.88" />
    </svg>
);

const IconPencilSquare = ({ className = "w-5 h-5" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10" />
    </svg>
);

const IconLightBulb = ({ className = "w-5 h-5" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 0 0 1.5-.189m-1.5.189a6.01 6.01 0 0 1-1.5-.189m3.75 7.478a12.06 12.06 0 0 1-4.5 0m3.75 2.383a14.406 14.406 0 0 1-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 1 0-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />
    </svg>
);

const IconCheckBadge = ({ className = "w-5 h-5" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 0 1-1.043 3.296 3.745 3.745 0 0 1-3.296 1.043A3.745 3.745 0 0 1 12 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 0 1-3.296-1.043 3.745 3.745 0 0 1-1.043-3.296A3.745 3.745 0 0 1 3 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 0 1 1.043-3.296 3.746 3.746 0 0 1 3.296-1.043A3.746 3.746 0 0 1 12 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 0 1 3.296 1.043 3.745 3.745 0 0 1 1.043 3.296A3.745 3.745 0 0 1 21 12Z" />
    </svg>
);

const IconArrowRight = ({ className = "w-4 h-4" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
    </svg>
);

const RiskDot = ({ color }: { color: string }) => (
    <span className={`inline-block w-2.5 h-2.5 rounded-full ${color}`} />
);

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
            case "queued": return <span className="inline-flex items-center gap-1.5"><IconClock className="w-4 h-4" /> Ve frontě</span>;
            case "running": return <span className="inline-flex items-center gap-1.5"><IconArrowPath className="w-4 h-4 animate-spin" /> Skenování probíhá...</span>;
            case "done": return <span className="inline-flex items-center gap-1.5"><IconCheckCircle className="w-4 h-4" /> Dokončeno</span>;
            case "error": return <span className="inline-flex items-center gap-1.5"><IconXCircle className="w-4 h-4" /> Chyba</span>;
            default: return status;
        }
    };

    const statusColor = (status: string) => {
        switch (status) {
            case "queued": return "bg-yellow-500/20 text-yellow-400";
            case "running": return "bg-blue-500/20 text-blue-400";
            case "done": return "bg-green-500/20 text-green-400";
            case "error": return "bg-red-500/20 text-red-400";
            default: return "bg-white/10 text-slate-400";
        }
    };

    const riskBadge = (level: string) => {
        switch (level) {
            case "high": return "bg-red-500/12 text-red-400 border-red-500/30";
            case "limited": return "bg-yellow-500/12 text-yellow-400 border-yellow-500/30";
            case "minimal": return "bg-green-500/12 text-green-400 border-green-500/30";
            default: return "bg-white/10 text-slate-400 border-white/[0.08]";
        }
    };

    const riskLabel = (level: string) => {
        switch (level) {
            case "high": return <span className="inline-flex items-center gap-1.5"><RiskDot color="bg-red-500" /> Vysoké riziko</span>;
            case "limited": return <span className="inline-flex items-center gap-1.5"><RiskDot color="bg-yellow-500" /> Omezené riziko</span>;
            case "minimal": return <span className="inline-flex items-center gap-1.5"><RiskDot color="bg-green-500" /> Minimální riziko</span>;
            default: return level;
        }
    };

    const categoryIcon = (cat: string) => {
        switch (cat) {
            case "chatbot": return <IconCpu className="w-4 h-4 text-fuchsia-400" />;
            case "analytics": return <IconChartBar className="w-4 h-4 text-cyan-400" />;
            case "recommender": return <IconTarget className="w-4 h-4 text-amber-400" />;
            case "content_gen": return <IconPhoto className="w-4 h-4 text-purple-400" />;
            default: return <IconSearch className="w-4 h-4 text-slate-400" />;
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
            case "confirmed": return { label: <span className="inline-flex items-center gap-1"><IconCheckCircle className="w-3.5 h-3.5" /> Potvrzeno</span>, cls: "bg-green-500/20 text-green-400 border-green-500/30" };
            case "rejected": return { label: <span className="inline-flex items-center gap-1"><IconXCircle className="w-3.5 h-3.5" /> Zamítnuto</span>, cls: "bg-red-500/20 text-red-400 border-red-500/30" };
            default: return null;
        }
    };

    return (
        <section className="py-20">
            <div className="mx-auto max-w-4xl px-6">
                {/* Nadpis */}
                <div className="text-center">
                    <h1 className="text-3xl font-bold text-white inline-flex items-center gap-3 justify-center">
                        <IconSearch className="w-8 h-8 text-fuchsia-400" />
                        Skenovat web
                    </h1>
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
                        className="flex-1 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-slate-500 focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/50 transition-all"
                        required
                        disabled={loading}
                    />
                    <button
                        type="submit"
                        className="btn-primary whitespace-nowrap disabled:opacity-50 gap-2"
                        disabled={loading}
                    >
                        {loading ? (
                            <><IconClock className="w-4 h-4 animate-pulse" /> Skenuji...</>
                        ) : (
                            <><IconSearch className="w-4 h-4" /> Skenovat</>
                        )}
                    </button>
                </form>

                {/* Chyba */}
                {error && (
                    <div className="mt-6 rounded-2xl bg-red-500/10 border border-red-500/30 p-4 text-center">
                        <p className="text-sm text-red-400 inline-flex items-center gap-1.5"><IconXCircle className="w-4 h-4" /> {error}</p>
                        <p className="mt-1 text-xs text-red-500/70">
                            Zkontrolujte, zda je URL správná a zkuste to znovu.
                        </p>
                    </div>
                )}

                {/* Průběh skenování */}
                {scanResult && (scanResult.status === "queued" || scanResult.status === "running") && (
                    <div className="mt-8 card text-center">
                        <div className="animate-pulse">
                            <div className="flex justify-center mb-4">
                                <IconShield className="w-10 h-10 text-fuchsia-400" />
                            </div>
                            <h2 className="text-lg font-semibold text-white">
                                {statusLabel(scanResult.status)}
                            </h2>
                            <p className="mt-2 text-sm text-slate-400">
                                Analyzujeme {scanResult.url} — hledáme AI systémy,
                                kontrolujeme cookies, skripty a síťové požadavky...
                            </p>
                            <div className="mt-4 flex justify-center">
                                <div className="h-2 w-48 bg-white/10 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-gradient-to-r from-fuchsia-600 to-purple-600 rounded-full animate-[loading_2s_ease-in-out_infinite]"
                                        style={{ width: "60%" }}
                                    />
                                </div>
                            </div>
                            <p className="mt-2 text-xs text-slate-500">Scan ID: {scanResult.scan_id}</p>
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
                                    <span className="font-medium text-white">{scanResult.url}</span>
                                </div>
                                {scanResult.company_name && (
                                    <div className="flex justify-between border-b border-white/[0.06] pb-2">
                                        <span className="text-slate-500">Firma</span>
                                        <span className="font-medium text-white">{scanResult.company_name}</span>
                                    </div>
                                )}
                                <div className="flex justify-between border-b border-white/[0.06] pb-2">
                                    <span className="text-slate-500">Nalezené AI systémy</span>
                                    <span className="font-bold text-xl text-white">{findings.length}</span>
                                </div>
                                {aiClassified && (
                                    <div className="flex justify-between border-b border-white/[0.06] pb-2">
                                        <span className="text-slate-500">AI ověření</span>
                                        <span className="inline-flex items-center gap-1.5 text-sm font-medium text-purple-400">
                                            <IconSparkles className="w-4 h-4" /> Claude AI verified
                                            {falsePositives.length > 0 && (
                                                <span className="text-xs text-slate-500 ml-1">
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
                                <h3 className="text-lg font-semibold text-white mb-4 inline-flex items-center gap-2">
                                    <IconCpu className="w-5 h-5 text-fuchsia-400" /> Nalezené AI systémy ({findings.length})
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
                                                    <h4 className="font-semibold text-white inline-flex items-center gap-2">
                                                        {categoryIcon(f.category)} {f.name}
                                                    </h4>
                                                    <p className="text-xs text-slate-500 mt-1">
                                                        {categoryLabel(f.category)}
                                                    </p>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    {f.source === "ai_classified" && (
                                                        <span className="inline-flex items-center gap-1 rounded-full bg-purple-500/15 border border-purple-500/30 px-2 py-0.5 text-xs font-medium text-purple-400">
                                                            <IconSparkles className="w-3.5 h-3.5" /> AI verified
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
                                                        <span className="text-slate-500 shrink-0 inline-flex items-center gap-1"><IconDocument className="w-4 h-4" /> Článek:</span>
                                                        <span className="text-slate-300">{f.ai_act_article}</span>
                                                    </div>
                                                )}
                                                {f.action_required && (
                                                    <div className="flex gap-2">
                                                        <span className="text-slate-500 shrink-0 inline-flex items-center gap-1"><IconBolt className="w-4 h-4" /> Požadovaná akce:</span>
                                                        <span className="text-slate-300">{f.action_required}</span>
                                                    </div>
                                                )}
                                                {f.signature_matched && (
                                                    <div className="flex gap-2">
                                                        <span className="text-slate-500 shrink-0 inline-flex items-center gap-1"><IconSearch className="w-4 h-4" /> Detekováno:</span>
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
                                                        className="text-xs px-3 py-1 rounded-full bg-green-500/15 text-green-400 border border-green-500/30 hover:bg-green-500/25 transition-colors inline-flex items-center gap-1"
                                                        disabled={f.confirmed_by_client === "confirmed"}
                                                    >
                                                        <IconCheckCircle className="w-3.5 h-3.5" /> Potvrdit
                                                    </button>
                                                    <button
                                                        onClick={() => handleConfirm(f.id, false)}
                                                        className="text-xs px-3 py-1 rounded-full bg-red-500/15 text-red-400 border border-red-500/30 hover:bg-red-500/25 transition-colors inline-flex items-center gap-1"
                                                        disabled={f.confirmed_by_client === "rejected"}
                                                    >
                                                        <IconXCircle className="w-3.5 h-3.5" /> Zamítnout
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ) : (
                            <div className="card text-center">
                                <div className="flex justify-center mb-2">
                                    <IconCheckBadge className="w-10 h-10 text-green-400" />
                                </div>
                                <h3 className="font-semibold text-white">Žádné AI systémy nenalezeny</h3>
                                <p className="text-sm text-slate-400 mt-1">
                                    Na tomto webu jsme nezjistili žádné AI systémy spadající pod EU AI Act.
                                </p>
                            </div>
                        )}

                        {/* False Positives — kolapsovatená sekce */}
                        {falsePositives.length > 0 && (
                            <details className="group">
                                <summary className="cursor-pointer text-sm text-slate-500 hover:text-slate-300 transition-colors">
                                    👻 Vyřazené false-positives ({falsePositives.length}) — AI systémy zmíněné, ale nenasazené
                                </summary>
                                <div className="mt-3 space-y-2">
                                    {falsePositives.map((f) => (
                                        <div key={f.id} className="rounded-lg bg-white/[0.04] border border-white/[0.08] p-3 opacity-60">
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
                        <div className="card bg-white/[0.04] border border-white/[0.08] text-center">
                            <h3 className="font-semibold text-white">📥 Stáhnout compliance report</h3>
                            <p className="text-sm text-slate-300 mt-2">
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

                        <div className="card bg-white/[0.04] border border-white/[0.08] text-center">
                            <h3 className="font-semibold text-white">📋 Interní AI dotazník</h3>
                            <p className="text-sm text-slate-400 mt-2">
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

                        <div className="card bg-white/[0.04] border border-white/[0.08] text-center">
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
                        <p className="mt-2 text-sm text-slate-500">
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
                        <h3 className="font-semibold text-white mb-2">Co skenujeme?</h3>
                        <ul className="text-sm text-slate-500 space-y-1">
                            <li>🤖 Chatboty (Smartsupp, Tidio, Intercom...)</li>
                            <li>📊 AI analytiku (GA4, Hotjar s AI features...)</li>
                            <li>🎯 AI doporučovací systémy</li>
                            <li>🖼️ AI generovaný obsah</li>
                            <li>🔍 AI vyhledávání na webu</li>
                        </ul>
                        <p className="mt-4 text-xs text-slate-500">
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