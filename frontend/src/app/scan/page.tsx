"use client";

import { useState, useEffect, useCallback, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
    startScan,
    getScanStatus,
    getScanFindings,
    type ScanStatus,
    type Finding,
} from "@/lib/api";

/* ── Inline SVG Icon helpers ── */
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
const IconCheckBadge = ({ className = "w-5 h-5" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 0 1-1.043 3.296 3.745 3.745 0 0 1-3.296 1.043A3.745 3.745 0 0 1 12 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 0 1-3.296-1.043 3.745 3.745 0 0 1-1.043-3.296A3.745 3.745 0 0 1 3 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 0 1 1.043-3.296 3.746 3.746 0 0 1 3.296-1.043A3.746 3.746 0 0 1 12 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 0 1 3.296 1.043 3.745 3.745 0 0 1 1.043 3.296A3.745 3.745 0 0 1 21 12Z" />
    </svg>
);
const IconExclamation = ({ className = "w-5 h-5" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
    </svg>
);
const IconInfo = ({ className = "w-5 h-5" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z" />
    </svg>
);
const IconEnvelope = ({ className = "w-5 h-5" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 0 1-2.25 2.25h-15a2.25 2.25 0 0 1-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25m19.5 0v.243a2.25 2.25 0 0 1-1.07 1.916l-7.5 4.615a2.25 2.25 0 0 1-2.36 0L3.32 8.91a2.25 2.25 0 0 1-1.07-1.916V6.75" />
    </svg>
);

/* ── Scan progress stages ── */
const SCAN_STAGES = [
    { label: "Připojování k webu", desc: "Otevíráme váš web v bezpečném prohlížeči" },
    { label: "Načítání stránky", desc: "Čekáme, až se web kompletně načte" },
    { label: "Analýza HTML kódu", desc: "Procházíme zdrojový kód stránky" },
    { label: "Kontrola skriptů", desc: "Hledáme JavaScript knihovny třetích stran" },
    { label: "Detekce chatbotů a AI nástrojů", desc: "Zjišťujeme, zda web obsahuje chatbota, personalizaci nebo AI vyhledávání" },
    { label: "Analýza cookies a trackerů", desc: "Kontrolujeme analytické a sledovací cookies" },
    { label: "Monitorování síťových požadavků", desc: "Sledujeme komunikaci s AI službami třetích stran" },
    { label: "AI klasifikace nálezů", desc: "Umělá inteligence vyhodnocuje a ověřuje každý nález" },
    { label: "Vyhodnocení rizik dle AI Act", desc: "Klasifikujeme rizika podle kategorií EU AI Act" },
    { label: "Příprava vašeho reportu", desc: "Generujeme kompletní compliance report" },
];

/* ── Risk level tooltip ── */
function RiskTooltip({ level, children }: { level: string; children: React.ReactNode }) {
    const [show, setShow] = useState(false);

    const explanations: Record<string, string> = {
        high: "Vysoké riziko — AI systém, který přímo ovlivňuje rozhodnutí o lidech (např. scoring, biometrie). Dle AI Act vyžaduje nejpřísnější regulaci včetně registrace, auditu a lidského dohledu.",
        limited: "Omezené riziko — AI systém, který interaguje s uživateli (chatbot, doporučovací engine). Dle AI Act musí být jasně označen, aby návštěvník věděl, že komunikuje s AI. Toto je nejčastější kategorie na českých webech.",
        minimal: "Minimální riziko — AI systém běžící v pozadí (analytika, antispam). Dle AI Act stačí vést interní evidenci a zajistit AI gramotnost zaměstnanců. I tato kategorie ale vyžaduje vaši pozornost!",
    };

    return (
        <span className="relative inline-flex items-center">
            {children}
            <button
                onClick={(e) => { e.stopPropagation(); setShow(!show); }}
                className="ml-1 text-slate-500 hover:text-slate-300 transition-colors"
                aria-label="Vysvětlení rizika"
            >
                <IconInfo className="w-3.5 h-3.5" />
            </button>
            {show && (
                <>
                    <div className="fixed inset-0 z-40" onClick={() => setShow(false)} />
                    <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 rounded-xl bg-slate-800 border border-white/10 p-3 text-xs text-slate-300 leading-relaxed shadow-xl">
                        {explanations[level] || "Kategorie rizika dle EU AI Act."}
                        <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-px">
                            <div className="w-2 h-2 bg-slate-800 border-r border-b border-white/10 rotate-45" />
                        </div>
                    </div>
                </>
            )}
        </span>
    );
}

function ScanPageInner() {
    const searchParams = useSearchParams();
    const [url, setUrl] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [scanResult, setScanResult] = useState<ScanStatus | null>(null);
    const [findings, setFindings] = useState<Finding[]>([]);
    const [aiClassified, setAiClassified] = useState(false);
    const [scanId, setScanId] = useState<string | null>(null);
    const [currentStage, setCurrentStage] = useState(0);
    const [reportEmail, setReportEmail] = useState("");
    const [emailSent, setEmailSent] = useState(false);
    const [emailSending, setEmailSending] = useState(false);
    const pollingRef = useRef<NodeJS.Timeout | null>(null);
    const stageRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const autoStartedRef = useRef(false);

    useEffect(() => {
        return () => {
            if (pollingRef.current) clearInterval(pollingRef.current);
            if (stageRef.current) clearTimeout(stageRef.current);
        };
    }, []);

    const fetchFindings = useCallback(async (id: string) => {
        try {
            const res = await getScanFindings(id);
            setFindings(res.findings);
            setAiClassified(res.ai_classified || false);
        } catch { /* tiché selhání */ }
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
                        if (stageRef.current) clearTimeout(stageRef.current);
                        stageRef.current = null;
                        setCurrentStage(SCAN_STAGES.length);
                        setLoading(false);
                        if (status.status === "done") await fetchFindings(id);
                    }
                } catch { /* keep polling */ }
            }, 3000);
        },
        [fetchFindings]
    );

    // Animated stage progression
    const startStageAnimation = useCallback(() => {
        setCurrentStage(0);
        let stage = 0;
        const intervals = [1800, 2200, 2500, 2800, 3200, 3000, 3500, 4000, 3000, 2500];
        const advanceStage = () => {
            stage++;
            if (stage < SCAN_STAGES.length) {
                setCurrentStage(stage);
                stageRef.current = setTimeout(advanceStage, intervals[stage] || 2500);
            }
        };
        stageRef.current = setTimeout(advanceStage, intervals[0]);
    }, []);

    const doScan = useCallback(async (rawUrl: string) => {
        let normalizedUrl = rawUrl.trim();
        if (!normalizedUrl) return;
        if (!normalizedUrl.match(/^https?:\/\//i)) normalizedUrl = "https://" + normalizedUrl;
        setUrl(normalizedUrl);
        setLoading(true);
        setError(null);
        setScanResult(null);
        setFindings([]);
        setAiClassified(false);
        setEmailSent(false);
        setReportEmail("");
        if (pollingRef.current) clearInterval(pollingRef.current);
        if (stageRef.current) clearTimeout(stageRef.current);

        startStageAnimation();

        try {
            const result = await startScan(normalizedUrl);
            setScanId(result.scan_id);
            const status = await getScanStatus(result.scan_id);
            setScanResult(status);
            if (status.status === "queued" || status.status === "running") {
                startPolling(result.scan_id);
            } else {
                setLoading(false);
                if (stageRef.current) clearTimeout(stageRef.current);
                setCurrentStage(SCAN_STAGES.length);
                if (status.status === "done") await fetchFindings(result.scan_id);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "Nastala neočekávaná chyba");
            setLoading(false);
            if (stageRef.current) clearTimeout(stageRef.current);
        }
    }, [startPolling, fetchFindings, startStageAnimation]);

    useEffect(() => {
        const urlParam = searchParams.get("url");
        if (urlParam && !autoStartedRef.current) {
            autoStartedRef.current = true;
            setUrl(urlParam);
            doScan(urlParam);
        }
    }, [searchParams, doScan]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        await doScan(url);
    };

    const handleSendReport = async () => {
        if (!reportEmail || !scanId) return;
        setEmailSending(true);
        try {
            const API = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").trim();
            const resp = await fetch(API + "/api/scan/" + scanId + "/send-report", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: reportEmail }),
            });
            if (resp.ok) setEmailSent(true);
        } catch { /* silent */ }
        setEmailSending(false);
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
            case "high": return "Vysoké riziko";
            case "limited": return "Omezené riziko";
            case "minimal": return "Minimální riziko";
            default: return level;
        }
    };
    const riskDotColor = (level: string) => {
        switch (level) {
            case "high": return "bg-red-500";
            case "limited": return "bg-yellow-500";
            case "minimal": return "bg-green-500";
            default: return "bg-slate-500";
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
            case "other": return "Ostatní AI systém";
            default: return cat;
        }
    };

    // Compute overall verdict
    const hasFindings = findings.length > 0;
    const highCount = findings.filter(f => f.risk_level === "high").length;
    const limitedCount = findings.filter(f => f.risk_level === "limited").length;
    const minimalCount = findings.filter(f => f.risk_level === "minimal").length;

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
                        placeholder="vasefirma.cz"
                        className="flex-1 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-white placeholder:text-slate-500 focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/50 transition-all"
                        required
                        disabled={loading}
                    />
                    <button type="submit" className="btn-primary whitespace-nowrap disabled:opacity-50 gap-2" disabled={loading}>
                        {loading ? <><IconClock className="w-4 h-4 animate-pulse" /> Skenuji...</> : <><IconSearch className="w-4 h-4" /> Skenovat</>}
                    </button>
                </form>
                <p className="text-xs text-slate-600 mt-2 text-center">Stačí zadat doménu — např. vasefirma.cz</p>

                {/* Chyba */}
                {error && (
                    <div className="mt-6 rounded-2xl bg-red-500/10 border border-red-500/30 p-4 text-center">
                        <p className="text-sm text-red-400 inline-flex items-center gap-1.5"><IconXCircle className="w-4 h-4" /> {error}</p>
                        <p className="mt-1 text-xs text-red-500/70">Zkontrolujte, zda je URL správná a zkuste to znovu.</p>
                    </div>
                )}

                {/* ═══ PRŮBĚH SKENOVÁNÍ — multi-stage progress ═══ */}
                {loading && (
                    <div className="mt-10 card">
                        <div className="flex items-center gap-3 mb-6">
                            <IconShield className="w-8 h-8 text-fuchsia-400 animate-pulse" />
                            <div>
                                <h2 className="text-lg font-semibold text-white">Skenování probíhá...</h2>
                                <p className="text-sm text-slate-400">Analyzujeme {scanResult?.url || url}</p>
                            </div>
                        </div>

                        {/* Overall progress bar */}
                        <div className="mb-6">
                            <div className="flex justify-between text-xs text-slate-500 mb-1.5">
                                <span>{SCAN_STAGES[Math.min(currentStage, SCAN_STAGES.length - 1)]?.label}</span>
                                <span>{Math.round(((currentStage + 1) / SCAN_STAGES.length) * 100)} %</span>
                            </div>
                            <div className="h-3 bg-white/[0.06] rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-fuchsia-600 via-purple-500 to-cyan-500 rounded-full transition-all duration-1000 ease-out"
                                    style={{ width: ((currentStage + 1) / SCAN_STAGES.length) * 100 + "%" }}
                                />
                            </div>
                        </div>

                        {/* Individual stages */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            {SCAN_STAGES.map((stage, i) => {
                                const done = i < currentStage;
                                const active = i === currentStage;
                                return (
                                    <div
                                        key={i}
                                        className={"flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-all duration-500 " +
                                            (done ? "bg-green-500/8 border border-green-500/15" :
                                                active ? "bg-fuchsia-500/10 border border-fuchsia-500/20" :
                                                    "bg-white/[0.02] border border-white/[0.04] opacity-40")
                                        }
                                    >
                                        <div className="flex-shrink-0">
                                            {done ? (
                                                <IconCheckCircle className="w-5 h-5 text-green-400" />
                                            ) : active ? (
                                                <div className="w-5 h-5 rounded-full border-2 border-fuchsia-400 border-t-transparent animate-spin" />
                                            ) : (
                                                <div className="w-5 h-5 rounded-full border border-white/10" />
                                            )}
                                        </div>
                                        <div>
                                            <p className={"font-medium " + (done ? "text-green-400" : active ? "text-white" : "text-slate-500")}>
                                                {stage.label}
                                            </p>
                                            <p className={"text-xs " + (active ? "text-slate-400" : "text-slate-600")}>
                                                {stage.desc}
                                            </p>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>

                        {/* Warning: do not leave page during final stage */}
                        {currentStage >= SCAN_STAGES.length - 2 && (
                            <div className="mt-4 flex items-start gap-3 rounded-xl bg-amber-500/10 border border-amber-500/25 px-4 py-3 animate-in fade-in duration-500">
                                <svg className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M12 3l9.66 16.5a1 1 0 01-.87 1.5H3.21a1 1 0 01-.87-1.5L12 3z" />
                                </svg>
                                <div>
                                    <p className="text-sm font-medium text-amber-300">Neopouštějte prosím tuto stránku</p>
                                    <p className="text-xs text-amber-400/70 mt-0.5">
                                        Generování compliance reportu může trvat 30–60 sekund. Umělá inteligence právě vyhodnocuje každý nález — prosím vyčkejte.
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* ═══ VÝSLEDKY ═══ */}
                {scanResult && scanResult.status === "done" && (
                    <div className="mt-8 space-y-6">

                        {/* ── ČERVENÝ VAROVNÝ BANNER (nahoře) ── */}
                        {hasFindings && (
                            <div className="rounded-2xl bg-red-500/10 border-2 border-red-500/40 p-5">
                                <div className="flex items-start gap-3">
                                    <IconExclamation className="w-7 h-7 text-red-400 flex-shrink-0 mt-0.5" />
                                    <div>
                                        <h2 className="text-lg font-bold text-red-400">
                                            Na vašem webu byly nalezeny AI systémy bez povinného označení
                                        </h2>
                                        <p className="mt-2 text-sm text-red-300/80 leading-relaxed">
                                            Skenováním jsme zjistili, že váš web používá <strong className="text-white">{findings.length} AI {findings.length === 1 ? "systém" : findings.length < 5 ? "systémy" : "systémů"}</strong>,
                                            {" "}které nejsou jasně a zřetelně označeny pro návštěvníky vašeho webu.
                                            Od <strong className="text-white">2. srpna 2026</strong> je toto porušením EU AI Act
                                            (Nařízení 2024/1689, čl. 50) a hrozí pokuta{" "}
                                            <strong className="text-white">až 15 milionů EUR nebo 3 % obratu</strong>.
                                        </p>
                                        <p className="mt-3 text-sm font-semibold text-white bg-red-500/20 rounded-lg px-4 py-2.5 leading-relaxed border border-red-500/30">
                                            ⚠️ Pokud tyto nedostatky odhalil náš software, mohou je najít i kontrolní orgány EU.
                                            Po nabytí plné účinnosti zákona začnou evropské úřady provádět systematické inspekce
                                            webových stránek a e-shopů.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* ── Summary karta ── */}
                        <div className="card">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-lg font-semibold text-white">Přehled výsledků</h2>
                                <span className="inline-flex items-center rounded-full px-3 py-1 text-sm font-medium bg-green-500/20 text-green-400">
                                    <IconCheckCircle className="w-4 h-4 mr-1" /> Dokončeno
                                </span>
                            </div>
                            <div className="space-y-3 text-sm">
                                <div className="flex justify-between border-b border-white/[0.06] pb-2">
                                    <span className="text-white">Skenovaný web</span>
                                    <span className="font-medium text-white">{scanResult.url}</span>
                                </div>
                                {scanResult.company_name && (
                                    <div className="flex justify-between border-b border-white/[0.06] pb-2">
                                        <span className="text-white">Firma</span>
                                        <span className="font-medium text-white">{scanResult.company_name}</span>
                                    </div>
                                )}
                                <div className="flex justify-between border-b border-white/[0.06] pb-2">
                                    <span className="text-white">Nalezené AI systémy</span>
                                    <span className="font-bold text-xl text-white">{findings.length}</span>
                                </div>
                                {aiClassified && (
                                    <div className="flex justify-between border-b border-white/[0.06] pb-2">
                                        <span className="text-white">Ověřeno</span>
                                        <span className="inline-flex items-center gap-1.5 text-sm font-medium text-purple-400">
                                            <IconSparkles className="w-4 h-4" /> Claude Opus 4.6
                                        </span>
                                    </div>
                                )}
                            </div>

                            {/* Risk summary */}
                            {hasFindings && (
                                <div className="mt-5 pt-5 border-t border-white/[0.06]">
                                    <h3 className="font-semibold text-white mb-3">Co to znamená pro vás?</h3>
                                    <div className="rounded-xl bg-amber-500/10 border border-amber-500/20 p-4">
                                        <p className="text-sm text-amber-200 leading-relaxed">
                                            <strong className="text-white">Váš web musí být upraven.</strong>{" "}
                                            Nalezli jsme {findings.length} AI {findings.length === 1 ? "systém" : findings.length < 5 ? "systémy" : "systémů"},
                                            {" "}které vyžadují buď označení pro návštěvníky, interní evidenci, nebo obojí.
                                            Bez úprav riskujete pokutu dle EU AI Act.
                                        </p>
                                    </div>

                                    <div className="grid grid-cols-3 gap-3 mt-4">
                                        {highCount > 0 && (
                                            <div className="rounded-xl bg-red-500/8 border border-red-500/20 p-3 text-center">
                                                <div className="text-2xl font-bold text-red-400">{highCount}</div>
                                                <RiskTooltip level="high">
                                                    <span className="text-xs text-red-400/70">Vysoké riziko</span>
                                                </RiskTooltip>
                                            </div>
                                        )}
                                        {limitedCount > 0 && (
                                            <div className="rounded-xl bg-yellow-500/8 border border-yellow-500/20 p-3 text-center">
                                                <div className="text-2xl font-bold text-yellow-400">{limitedCount}</div>
                                                <RiskTooltip level="limited">
                                                    <span className="text-xs text-yellow-400/70">Omezené riziko</span>
                                                </RiskTooltip>
                                            </div>
                                        )}
                                        {minimalCount > 0 && (
                                            <div className="rounded-xl bg-green-500/8 border border-green-500/20 p-3 text-center">
                                                <div className="text-2xl font-bold text-green-400">{minimalCount}</div>
                                                <RiskTooltip level="minimal">
                                                    <span className="text-xs text-green-400/70">Minimální riziko</span>
                                                </RiskTooltip>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* ── Findings list ── */}
                        {hasFindings ? (
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
                                                    f.risk_level === "high" ? "#ef4444" :
                                                        f.risk_level === "limited" ? "#f97316" : "#22c55e",
                                            }}
                                        >
                                            <div className="flex items-start justify-between">
                                                <div>
                                                    <h4 className="font-semibold text-white inline-flex items-center gap-2">
                                                        {categoryIcon(f.category)} {f.name}
                                                    </h4>
                                                    <p className="text-xs text-slate-500 mt-1">{categoryLabel(f.category)}</p>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <RiskTooltip level={f.risk_level}>
                                                        <span className={"inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium " + riskBadge(f.risk_level)}>
                                                            <span className={"inline-block w-2 h-2 rounded-full " + riskDotColor(f.risk_level)} />
                                                            {riskLabel(f.risk_level)}
                                                        </span>
                                                    </RiskTooltip>
                                                </div>
                                            </div>

                                            {f.ai_classification_text && (
                                                <p className="mt-2 text-sm text-slate-400 italic">{f.ai_classification_text}</p>
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
                                                        <span className="text-slate-500 shrink-0 inline-flex items-center gap-1"><IconBolt className="w-4 h-4" /> Co musíte udělat:</span>
                                                        <span className="text-slate-300">{f.action_required}</span>
                                                    </div>
                                                )}
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

                        {/* ── Info: výsledky se mohou lišit ── */}
                        {hasFindings && (
                            <div className="rounded-xl bg-slate-500/5 border border-slate-500/15 p-4">
                                <div className="flex items-start gap-3">
                                    <IconInfo className="w-5 h-5 text-slate-400 flex-shrink-0 mt-0.5" />
                                    <div className="text-xs text-slate-400 leading-relaxed space-y-1.5">
                                        <p>
                                            <strong className="text-slate-300">Výsledky opakovaných skenů se mohou mírně lišit.</strong>{" "}
                                            Moderní weby dynamicky načítají AI skripty (chatboty, analytiku, personalizaci) na základě
                                            geolokace návštěvníka, typu zařízení, denní doby, A/B testování nebo cookies.
                                            Některé systémy se aktivují až po interakci uživatele — proto nemusí být při každém skenu viditelné.
                                        </p>
                                        <p>
                                            Kompletní audit všech AI systémů na vašem webu — včetně těch skrytých v backendu —
                                            provádíme v rámci placeného plánu po{" "}
                                            <a href="/registrace" className="text-fuchsia-400 hover:text-fuchsia-300 underline">registraci</a>{" "}
                                            a vyplnění detailního dotazníku.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* ── ČERVENÝ VAROVNÝ BANNER (dole) ── */}
                        {hasFindings && (
                            <div className="rounded-2xl bg-red-500/10 border-2 border-red-500/40 p-5">
                                <div className="flex items-start gap-3">
                                    <IconExclamation className="w-6 h-6 text-red-400 flex-shrink-0 mt-0.5" />
                                    <div>
                                        <h3 className="font-bold text-red-400">Důležité: Toto musíte řešit</h3>
                                        <p className="mt-1 text-sm text-red-300/80 leading-relaxed">
                                            Výše uvedené AI systémy na vašem webu <strong className="text-white">nemají povinné oznámení pro návštěvníky</strong>.
                                            Dle EU AI Act (čl. 50) musí být návštěvníkům jasně sděleno, že komunikují s AI nebo že web používá AI systémy.
                                            <strong className="text-white"> Povinnost platí od 2. srpna 2026.</strong>
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* ── Odeslat report na e-mail (lead capture) ── */}
                        <div className="card bg-gradient-to-br from-fuchsia-500/5 via-purple-500/5 to-cyan-500/5 border border-fuchsia-500/20 text-center">
                            <IconEnvelope className="w-8 h-8 text-fuchsia-400 mx-auto mb-3" />
                            <h3 className="font-semibold text-white text-lg">Pošleme vám kompletní report na e-mail</h3>
                            <p className="text-sm text-slate-400 mt-2">
                                Podrobný přehled nálezů, doporučení k nápravě, ceník služeb a kontakt —
                                vše přehledně v jednom e-mailu.
                            </p>

                            {emailSent ? (
                                <div className="mt-4 inline-flex items-center gap-2 text-green-400 font-medium">
                                    <IconCheckCircle className="w-5 h-5" /> Report odeslán na {reportEmail}
                                </div>
                            ) : (
                                <div className="mt-4 flex gap-2 max-w-md mx-auto">
                                    <input
                                        type="email"
                                        value={reportEmail}
                                        onChange={(e) => setReportEmail(e.target.value)}
                                        placeholder="vas@email.cz"
                                        className="flex-1 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-white placeholder:text-slate-500 focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/50 transition text-sm"
                                        required
                                    />
                                    <button
                                        onClick={handleSendReport}
                                        disabled={emailSending || !reportEmail}
                                        className="btn-primary text-sm disabled:opacity-50 px-5"
                                    >
                                        {emailSending ? "Odesílám..." : "Odeslat report"}
                                    </button>
                                </div>
                            )}
                            <p className="text-xs text-slate-600 mt-3">Odesláním souhlasíte se zpracováním e-mailu dle <a href="/vop" className="underline hover:text-slate-400">VOP</a>.</p>
                        </div>

                        {/* CTA */}
                        <div className="card bg-white/[0.04] border border-white/[0.08] text-center">
                            <h3 className="font-semibold text-white text-lg">Chcete to vyřešit za vás?</h3>
                            <p className="text-sm text-slate-400 mt-2">
                                Připravíme kompletní dokumentaci, transparenční stránku a vše potřebné
                                pro soulad s AI Act — jednoduše a rychle.
                            </p>
                            <a href="/pricing" className="inline-block mt-4 btn-primary">
                                Zobrazit ceník služeb →
                            </a>
                        </div>
                    </div>
                )}

                {/* Error stav */}
                {scanResult && scanResult.status === "error" && (
                    <div className="mt-8 card text-center">
                        <IconExclamation className="w-10 h-10 text-amber-400 mx-auto mb-2" />
                        <h2 className="text-lg font-semibold text-white">Skenování selhalo</h2>
                        <p className="mt-2 text-sm text-slate-500">
                            Nepodařilo se naskenovat {scanResult.url}. Web může být nedostupný
                            nebo blokuje automatické přístupy.
                        </p>
                        <button
                            onClick={() => handleSubmit({ preventDefault: () => { } } as React.FormEvent)}
                            className="mt-4 btn-primary"
                        >
                            Zkusit znovu
                        </button>
                    </div>
                )}

                {/* Info box (pred skenem) */}
                {!scanResult && !loading && (
                    <div className="mt-12 space-y-6">
                        <div className="card">
                            <h3 className="font-semibold text-white mb-4 text-center">Co analyzujeme</h3>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                {[
                                    { icon: <IconCpu className="w-5 h-5 text-fuchsia-400" />, label: "Chatboty a konverzační AI", desc: "Smartsupp, Tidio, Intercom, LiveAgent a další" },
                                    { icon: <IconChartBar className="w-5 h-5 text-cyan-400" />, label: "AI analytika a sledování", desc: "GA4, Hotjar, Mixpanel s ML predikcemi" },
                                    { icon: <IconTarget className="w-5 h-5 text-amber-400" />, label: "Doporučovací systémy", desc: "Personalizace produktů, obsahu a reklam" },
                                    { icon: <IconPhoto className="w-5 h-5 text-purple-400" />, label: "AI generovaný obsah", desc: "Texty, obrázky, automatické překlady" },
                                    { icon: <IconSearch className="w-5 h-5 text-green-400" />, label: "AI vyhledávání na webu", desc: "Sémantické vyhledávání, autocomplete" },
                                    { icon: <IconShield className="w-5 h-5 text-blue-400" />, label: "Bezpečnostní AI systémy", desc: "Detekce podvodů, anti-spam, CAPTCHA" },
                                ].map((item) => (
                                    <div key={item.label} className="flex items-start gap-3 rounded-xl bg-white/[0.03] border border-white/[0.06] p-3">
                                        <div className="flex-shrink-0 mt-0.5">{item.icon}</div>
                                        <div>
                                            <p className="text-sm font-medium text-slate-300">{item.label}</p>
                                            <p className="text-xs text-slate-500">{item.desc}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="text-center">
                            <p className="text-xs text-slate-600">
                                Skenování trvá 15–30 sekund. Používáme headless browser pro realistickou simulaci návštěvy.
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
        <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><p className="text-slate-400">Načítám...</p></div>}>
            <ScanPageInner />
        </Suspense>
    );
}
