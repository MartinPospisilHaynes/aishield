"use client";

import { useState, useEffect, useCallback, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
    startScan,
    getScanStatus,
    getScanFindings,
    type ScanStatus,
    type Finding,
    type TrackerInfo,
} from "@/lib/api";
import { useAnalytics, useApiErrorTracking } from "@/lib/analytics";

/* ── ScrollReveal — Intersection Observer animation wrapper ── */
function ScrollReveal({
    children,
    className = "",
    variant = "fade-up",
    delay = 0,
}: {
    children: React.ReactNode;
    className?: string;
    variant?: "fade-up" | "slide-left" | "slide-right" | "scale-up";
    delay?: number;
}) {
    const ref = useRef<HTMLDivElement>(null);
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        const el = ref.current;
        if (!el) return;
        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting) {
                    setVisible(true);
                    observer.unobserve(el);
                }
            },
            { threshold: 0.08, rootMargin: "0px 0px -40px 0px" }
        );
        observer.observe(el);
        return () => observer.disconnect();
    }, []);

    const variantClass = variant === "fade-up" ? "" : variant;

    return (
        <div
            ref={ref}
            className={`scroll-reveal ${variantClass} ${visible ? "visible" : ""} ${className}`}
            data-delay={delay}
        >
            {children}
        </div>
    );
}

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
const IconCode = ({ className = "w-5 h-5" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" />
    </svg>
);
const IconEye = ({ className = "w-5 h-5" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
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
const IconLockClosed = ({ className = "w-5 h-5" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
    </svg>
);
const IconGlobeAlt = ({ className = "w-5 h-5" }: { className?: string }) => (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 0 0 8.716-6.747M12 21a9.004 9.004 0 0 1-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 0 1 7.843 4.582M12 3a8.997 8.997 0 0 0-7.843 4.582m15.686 0A11.953 11.953 0 0 1 12 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0 1 21 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0 1 12 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 0 1 3 12c0-1.605.42-3.113 1.157-4.418" />
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
                    <div className="fixed sm:absolute z-50 sm:bottom-full left-4 right-4 sm:left-auto sm:right-auto sm:-translate-x-1/2 bottom-20 sm:mb-2 w-auto sm:w-72 rounded-xl bg-slate-800 border border-white/10 p-3 text-xs text-slate-300 leading-relaxed shadow-xl">
                        {explanations[level] || "Kategorie rizika dle EU AI Act."}
                        <div className="hidden sm:block absolute top-full left-1/2 -translate-x-1/2 -mt-px">
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
    const { track } = useAnalytics();
    const trackApiError = useApiErrorTracking();
    const [url, setUrl] = useState("");
    const scanStartTimeRef = useRef<number>(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [scanResult, setScanResult] = useState<ScanStatus | null>(null);
    const [findings, setFindings] = useState<Finding[]>([]);
    const [trackers, setTrackers] = useState<TrackerInfo[]>([]);
    const [aiClassified, setAiClassified] = useState(false);
    const [scanId, setScanId] = useState<string | null>(null);
    const [currentStage, setCurrentStage] = useState(0);

    // Check if user is logged in (for dashboard redirect)
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    useEffect(() => {
        try {
            // Check supabase auth without importing full context
            const raw = localStorage.getItem('sb-rsxwqcrkttlfnqbjgpgc-auth-token');
            if (raw) {
                const parsed = JSON.parse(raw);
                if (parsed?.access_token && parsed?.user?.email) {
                    setIsLoggedIn(true);
                }
            }
        } catch { }
    }, []);
    const [reportEmail, setReportEmail] = useState("");
    const [emailSent, setEmailSent] = useState(false);
    const [emailSending, setEmailSending] = useState(false);
    const [isCached, setIsCached] = useState(false);
    const [countdown, setCountdown] = useState(120); // 2 min static countdown
    const countdownRef = useRef<NodeJS.Timeout | null>(null);
    const pollingRef = useRef<NodeJS.Timeout | null>(null);
    const stageRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const autoStartedRef = useRef(false);
    const pollCountRef = useRef(0);
    const MAX_POLL_ATTEMPTS = 70; // 70 × 3s = ~3.5 min

    useEffect(() => {
        return () => {
            if (pollingRef.current) clearInterval(pollingRef.current);
            if (stageRef.current) clearTimeout(stageRef.current);
            if (countdownRef.current) clearInterval(countdownRef.current);
        };
    }, []);

    // Countdown timer — ticks every second while loading
    useEffect(() => {
        if (loading && !isCached) {
            setCountdown(120);
            countdownRef.current = setInterval(() => {
                setCountdown(prev => (prev > 0 ? prev - 1 : 0));
            }, 1000);
        } else {
            if (countdownRef.current) { clearInterval(countdownRef.current); countdownRef.current = null; }
        }
        return () => { if (countdownRef.current) { clearInterval(countdownRef.current); countdownRef.current = null; } };
    }, [loading, isCached]);

    const fetchFindings = useCallback(async (id: string) => {
        try {
            const res = await getScanFindings(id);
            setFindings(res.findings);
            setTrackers(res.trackers || []);
            setAiClassified(res.ai_classified || false);
        } catch { /* tiché selhání */ }
    }, []);

    const startPolling = useCallback(
        (id: string) => {
            pollCountRef.current = 0;
            pollingRef.current = setInterval(async () => {
                pollCountRef.current += 1;
                // Timeout ochrana — po MAX_POLL_ATTEMPTS přestaneme pollovat
                if (pollCountRef.current > MAX_POLL_ATTEMPTS) {
                    if (pollingRef.current) clearInterval(pollingRef.current);
                    pollingRef.current = null;
                    if (stageRef.current) clearTimeout(stageRef.current);
                    stageRef.current = null;
                    setCurrentStage(SCAN_STAGES.length);
                    setLoading(false);
                    setScanResult((prev) => prev ? { ...prev, status: "error" } : null);
                    track("scan_error", { scan_id: id, error: "polling_timeout" }, Date.now() - scanStartTimeRef.current);
                    return;
                }
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
                        const duration = Date.now() - scanStartTimeRef.current;
                        if (status.status === "done") {
                            track("scan_completed", { scan_id: id, findings_count: status.total_findings || 0 }, duration);
                            await fetchFindings(id);
                        } else {
                            track("scan_error", { scan_id: id, error: "scan_failed" }, duration);
                        }
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
        scanStartTimeRef.current = Date.now();
        track("scan_url_entered", { url: normalizedUrl });
        setError(null);
        setScanResult(null);
        setFindings([]);
        setTrackers([]);
        setAiClassified(false);
        setEmailSent(false);
        setReportEmail("");
        setIsCached(false);
        if (pollingRef.current) clearInterval(pollingRef.current);
        if (stageRef.current) clearTimeout(stageRef.current);

        try {
            const result = await startScan(normalizedUrl);
            setScanId(result.scan_id);
            track("scan_started", { url: normalizedUrl, scan_id: result.scan_id });

            // Cached result — skip animation, show results immediately
            if (result.status === "cached") {
                setIsCached(true);
                track("scan_cached", { url: normalizedUrl, scan_id: result.scan_id });
                const status = await getScanStatus(result.scan_id);
                setScanResult(status);
                setLoading(false);
                setCurrentStage(SCAN_STAGES.length);
                if (status.status === "done") await fetchFindings(result.scan_id);
                return;
            }

            startStageAnimation();
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
            const errMsg = err instanceof Error ? err.message : "Nastala neočekávaná chyba";
            setError(errMsg);
            setLoading(false);
            if (stageRef.current) clearTimeout(stageRef.current);
            track("scan_failed", { url: normalizedUrl, error: errMsg });
            trackApiError("/api/scan", err, { url: normalizedUrl });
        }
    }, [startPolling, fetchFindings, startStageAnimation, track, trackApiError]);

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
        track("email_entered", { context: "scan_report" });
        try {
            const API = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").trim();
            const resp = await fetch(API + "/api/scan/" + scanId + "/send-report", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: reportEmail }),
            });
            if (resp.ok) {
                setEmailSent(true);
                track("report_email_sent", { scan_id: scanId });
            }
        } catch { /* silent */ }
        setEmailSending(false);
    };

    const riskBadge = (level: string) => {
        switch (level) {
            case "high": return "bg-red-500/12 text-red-400 border-red-500/30";
            case "limited": return "bg-cyan-500/12 text-cyan-400 border-cyan-500/30";
            case "minimal": return "bg-slate-500/12 text-slate-300 border-slate-400/25";
            default: return "bg-white/10 text-slate-400 border-white/[0.08]";
        }
    };
    const riskLabel = (level: string) => {
        switch (level) {
            case "high": return "Čl. 6 — vysoce rizikový systém";
            case "limited": return "Čl. 50 — transparenční povinnosti";
            case "minimal": return "Minimální riziko";
            default: return level;
        }
    };
    const riskDotColor = (level: string) => {
        switch (level) {
            case "high": return "bg-red-500";
            case "limited": return "bg-cyan-500";
            case "minimal": return "bg-slate-400";
            default: return "bg-slate-500";
        }
    };
    const categoryIcon = (cat: string) => {
        switch (cat) {
            case "chatbot": return <IconCpu className="w-4 h-4 text-fuchsia-400" />;
            case "analytics": return <IconChartBar className="w-4 h-4 text-cyan-400" />;
            case "recommender": return <IconTarget className="w-4 h-4 text-cyan-400" />;
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
            <div className="mx-auto max-w-4xl px-4 sm:px-6">
                {/* Nadpis */}
                <div className="text-center">
                    <h1 className="text-3xl font-bold text-white inline-flex items-center gap-3 justify-center">
                        <IconSearch className="w-8 h-8 text-fuchsia-400" />
                        Skenovat web
                    </h1>
                    <p className="mt-4 text-slate-400">
                        Zadejte URL vašeho webu a zjistěte, jaké AI systémy na něm
                        běží a jaké povinnosti z EU AI Actu vám z toho plynou.
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
                        <div className="flex items-center justify-between mb-6">
                            <div className="flex items-center gap-3">
                                <IconShield className="w-8 h-8 text-fuchsia-400 animate-pulse" />
                                <div>
                                    <h2 className="text-lg font-semibold text-white">Skenování probíhá...</h2>
                                    <p className="text-sm text-slate-400">Analyzujeme {scanResult?.url || url}</p>
                                </div>
                            </div>
                            {/* Countdown timer */}
                            <div className="text-right flex-shrink-0 ml-4">
                                <div className="inline-flex items-center gap-2 rounded-xl bg-white/[0.04] border border-white/[0.08] px-4 py-2">
                                    <svg className="w-4 h-4 text-fuchsia-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6l4 2m6-2a10 10 0 11-20 0 10 10 0 0120 0z" />
                                    </svg>
                                    <span className="font-mono text-lg font-bold text-white tabular-nums">
                                        {countdown > 0
                                            ? `${Math.floor(countdown / 60)}:${(countdown % 60).toString().padStart(2, '0')}`
                                            : '0:00'}
                                    </span>
                                </div>
                                <p className="text-[10px] text-slate-500 mt-1">
                                    {countdown > 0 ? 'odhadovaný zbývající čas' : 'ještě chvíli…'}
                                </p>
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
                                        Generování reportu může trvat 30–60 sekund. Umělá inteligence právě vyhodnocuje každý nález — prosím vyčkejte.
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* Waiting message when animation is done but scan still running */}
                        {currentStage >= SCAN_STAGES.length - 1 && (
                            <div className="mt-4 flex items-center gap-3 rounded-xl bg-fuchsia-500/10 border border-fuchsia-500/25 px-4 py-3">
                                <div className="w-5 h-5 rounded-full border-2 border-fuchsia-400 border-t-transparent animate-spin flex-shrink-0" />
                                <div>
                                    <p className="text-sm font-medium text-fuchsia-300">Finalizujeme report, vyčkejte prosím…</p>
                                    <p className="text-xs text-fuchsia-400/60 mt-0.5">
                                        Výsledky se zobrazí automaticky. Obvykle to trvá ještě 15–30 sekund.
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* ═══ VÝSLEDKY ═══ */}
                {scanResult && scanResult.status === "done" && (
                    <div className="mt-8 space-y-5">

                        {/* ── INFO BANNER: cached výsledky ── */}
                        {isCached && (
                            <div className="rounded-lg bg-slate-500/8 border border-slate-500/20 px-4 py-3 flex items-center gap-2.5">
                                <IconInfo className="w-4 h-4 text-slate-400 flex-shrink-0" />
                                <p className="text-xs text-slate-400">
                                    Zobrazujeme výsledky z předchozího skenu (posledních 24 h). Nový sken bude možný zítra.
                                </p>
                            </div>
                        )}

                        {/* ── ZELENÝ POZITIVNÍ BANNER ── */}
                        {hasFindings && (
                            <ScrollReveal variant="scale-up">
                                <div className="rounded-2xl bg-green-500/10 border-2 border-green-500/40 p-5">
                                    <div className="flex items-start gap-3">
                                        <IconCheckCircle className="w-7 h-7 text-green-400 flex-shrink-0 mt-0.5" />
                                        <div>
                                            <h2 className="text-lg font-bold text-white">
                                                ✓ Skvělá zpráva — váš web využívá umělou inteligenci!
                                            </h2>
                                            <p className="mt-2 text-sm text-white/90 leading-relaxed">
                                                Používáním AI technologií na svém webu máte významnou konkurenční výhodu.
                                                Chatboty, analytika a doporučovací systémy zlepšují zákaznický zážitek a konverze.
                                                Teď jen potřebujete mít vše legislativně v pořádku, aby vám tato výhoda
                                                zůstala i po začátku platnosti EU AI Act.{" "}
                                                <strong className="text-white font-bold">A navíc — weby a e-shopy,
                                                    které budou mít tuto zákonnou povinnost splněnou, budou upřednostňovány
                                                    ve vyhledávačích.</strong>
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </ScrollReveal>
                        )}

                        {/* ── HLAVNÍ VÝSLEDKOVÁ KARTA ── */}
                        <ScrollReveal delay={1}>
                            <div className="rounded-2xl border-2 border-white/[0.08] bg-white/[0.02] overflow-hidden">
                                {/* Status bar */}
                                <div className={"px-5 py-3 flex items-center justify-between " + (hasFindings ? "bg-red-500/10 border-b border-red-500/20" : "bg-green-500/8 border-b border-green-500/15")}>
                                    <div className="flex items-center gap-2">
                                        {hasFindings ? (
                                            <IconExclamation className="w-6 h-6 text-red-400" />
                                        ) : (
                                            <IconCheckCircle className="w-6 h-6 text-green-400" />
                                        )}
                                        <span className={"text-lg font-bold " + (hasFindings ? "text-red-300" : "text-green-300")}>
                                            {hasFindings
                                                ? `Nalezeno ${findings.length} AI ${findings.length === 1 ? "systém" : findings.length < 5 ? "systémy" : "systémů"} bez povinného označení`
                                                : "Žádné AI systémy nebyly zachyceny"
                                            }
                                        </span>
                                    </div>
                                    <span className="text-xs text-slate-500 hidden sm:inline">Sken dokončen</span>
                                </div>

                                {/* Tělo karty */}
                                <div className="p-5 space-y-4">
                                    {/* URL + firma */}
                                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                                        <div>
                                            <p className="text-white font-medium">{scanResult.url}</p>
                                            {scanResult.company_name && (
                                                <p className="text-sm text-slate-400">{scanResult.company_name}</p>
                                            )}
                                        </div>
                                        {aiClassified && (
                                            <span className="inline-flex items-center gap-1.5 text-xs font-medium text-purple-400 bg-purple-500/10 border border-purple-500/20 rounded-full px-3 py-1">
                                                <IconSparkles className="w-3.5 h-3.5" /> Ověřeno AI klasifikací
                                            </span>
                                        )}
                                    </div>

                                    {/* Pokud jsou nálezy — co to znamená */}
                                    {hasFindings && (
                                        <div className="rounded-xl bg-white/[0.03] border border-white/[0.06] p-4 space-y-3">
                                            <p className="text-sm text-slate-300 leading-relaxed">
                                                Na vašem webu {findings.length === 1 ? "běží AI systém, který není" : `běží ${findings.length} AI ${findings.length < 5 ? "systémy, které nejsou" : "systémů, které nejsou"}`} jasně označen{findings.length === 1 ? "" : "y"} pro návštěvníky.
                                                Od <strong className="text-white">2. srpna 2026</strong> je toto porušením EU AI Act (čl. 50)
                                                s pokutou <strong className="text-white">až 15 mil. € nebo 3 % obratu</strong>.
                                            </p>

                                            {/* Risk counters — inline (only high shown, others too cryptic) */}
                                            <div className="flex flex-wrap gap-2">
                                                {highCount > 0 && (
                                                    <RiskTooltip level="high">
                                                        <span className="inline-flex items-center gap-1.5 rounded-lg bg-red-500/10 border border-red-500/20 px-3 py-1.5 text-xs font-medium text-red-400">
                                                            <span className="w-2 h-2 rounded-full bg-red-500" />
                                                            {highCount}× Plná regulace
                                                        </span>
                                                    </RiskTooltip>
                                                )}
                                            </div>
                                        </div>
                                    )}

                                    {/* Dynamic scan warning */}
                                    {hasFindings && (
                                        <div className="rounded-lg bg-amber-500/5 border border-amber-500/15 px-4 py-3">
                                            <p className="text-xs text-amber-200/70 leading-relaxed">
                                                <strong className="text-amber-300">⚠ Proč se může počet lišit?</strong>{" "}
                                                Moderní weby načítají AI skripty dynamicky — podle geolokace, zařízení, denní doby
                                                či cookies. Skutečný počet AI systémů na webu může být vyšší.
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </ScrollReveal>

                        {/* ── Non-AI trackery (pro důvěryhodnost) ── */}
                        {trackers.length > 0 && (
                            <ScrollReveal variant="slide-left" delay={2}>
                                <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] overflow-hidden">
                                    <div className="px-5 py-3 bg-slate-500/8 border-b border-slate-500/15">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <IconChartBar className="w-5 h-5 text-slate-400" />
                                                <span className="text-sm font-semibold text-slate-300">
                                                    Dalších {trackers.length} sledovacích {trackers.length === 1 ? "systém" : trackers.length < 5 ? "systémy" : "systémů"} (non-AI)
                                                </span>
                                            </div>
                                            <span className="inline-flex items-center gap-1 rounded-full bg-green-500/10 border border-green-500/20 px-2.5 py-0.5 text-[11px] font-medium text-green-400">
                                                ✓ Nespadá pod AI Act
                                            </span>
                                        </div>
                                        <p className="text-xs text-slate-500 mt-1.5">
                                            Tyto technologie <strong className="text-slate-400">nejsou umělou inteligencí</strong> a nevyžadují regulaci dle EU AI Act.
                                            Zobrazujeme je pro úplnost — aby bylo vidět, že náš skener zachytí vše.
                                        </p>
                                    </div>
                                    <div className="p-4">
                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                            {trackers.map((t, idx) => (
                                                <div key={idx} className="flex items-center gap-3 rounded-lg bg-white/[0.02] border border-white/[0.05] px-3 py-2.5">
                                                    <span className="text-lg flex-shrink-0">{t.icon}</span>
                                                    <div className="min-w-0">
                                                        <p className="text-sm font-medium text-white truncate">{t.name}</p>
                                                        <p className="text-[11px] text-slate-500 truncate">{t.description_cs}</p>
                                                    </div>
                                                    <span className="ml-auto inline-flex items-center rounded bg-slate-500/10 px-1.5 py-0.5 text-[10px] text-slate-500 flex-shrink-0">
                                                        {t.category}
                                                    </span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </ScrollReveal>
                        )}

                        {/* ── CTA: 24h hloubkový scan — ZDARMA ── */}
                        {hasFindings && (
                            <ScrollReveal variant="scale-up" delay={3}>
                                <div className="rounded-2xl bg-gradient-to-br from-fuchsia-500/8 via-purple-500/5 to-fuchsia-500/8 border-2 border-fuchsia-500/25 p-6 text-center relative overflow-hidden">
                                    <div className="absolute -top-8 -right-8 w-32 h-32 rounded-full bg-fuchsia-500/10 blur-3xl" />
                                    <h3 className="font-bold text-white text-lg">
                                        Kompletní obraz získáte <span className="neon-text">24h hloubkovým skenem</span>
                                    </h3>
                                    <p className="text-sm text-slate-300 mt-2 max-w-lg mx-auto leading-relaxed">
                                        Jeden scan nemusí odhalit vše — AI systémy se chovají různě podle času, lokace i zařízení.
                                        Zaregistrujte se a spustíme <strong className="text-white">24 nezávislých skenů v 6 kolech ze 7 zemí</strong> (desktop + mobil, rezidenční proxy) +
                                        {" "}<strong className="text-white">dotazník</strong>, který pokryje i interní AI (ChatGPT, účetnictví, HR automatizace).
                                    </p>
                                    <div className="flex flex-wrap justify-center gap-1.5 mt-4">
                                        {["🇨🇿 CZ", "🇬🇧 GB", "🇺🇸 US", "🇧🇷 BR", "🇯🇵 JP", "🇿🇦 ZA", "🇦🇺 AU"].map(c => (
                                            <span key={c} className="inline-flex items-center gap-1 rounded-md bg-white/5 border border-white/10 px-2 py-0.5 text-xs text-slate-400">
                                                {c}
                                            </span>
                                        ))}
                                    </div>
                                    <a href="/registrace" className="inline-flex items-center justify-center gap-2 mt-5 btn-primary text-base px-10 py-3.5 font-bold">
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M15.59 14.37a6 6 0 0 1-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 0 0 6.16-12.12A14.98 14.98 0 0 0 9.631 8.41m5.96 5.96a14.926 14.926 0 0 1-5.841 2.58m-.119-8.54a6 6 0 0 0-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 0 0-2.58 5.84m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 0 1-2.448-2.448 14.9 14.9 0 0 1 .06-.312m-2.24 2.39a4.493 4.493 0 0 0-1.757 4.306 4.493 4.493 0 0 0 4.306-1.758M16.5 9a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0Z" /></svg>
                                        Spustit 24h hloubkový scan — ZDARMA
                                    </a>
                                    <p className="text-xs text-slate-500 mt-2">Registrace zdarma • Výsledek na email do 24 h</p>
                                </div>
                            </ScrollReveal>
                        )}

                        {/* ── Seznam nálezů ── */}
                        {hasFindings ? (
                            <ScrollReveal variant="slide-right" delay={4}>
                                <div>
                                    <h3 className="text-base font-semibold text-white mb-3 flex items-center gap-2">
                                        <IconCpu className="w-5 h-5 text-fuchsia-400" />
                                        Nalezené AI systémy
                                    </h3>
                                    <div className="space-y-3">
                                        {findings.map((f) => (
                                            <div key={f.id} className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-4">
                                                <div className="flex items-start justify-between gap-3">
                                                    <div className="flex items-center gap-2.5 min-w-0">
                                                        {categoryIcon(f.category)}
                                                        <div className="min-w-0">
                                                            <h4 className="font-semibold text-white text-sm truncate">{f.name}</h4>
                                                            <p className="text-xs text-slate-500">{categoryLabel(f.category)}</p>
                                                        </div>
                                                    </div>
                                                    <RiskTooltip level={f.risk_level}>
                                                        <span className={"inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-medium flex-shrink-0 " + riskBadge(f.risk_level)}>
                                                            <span className={"w-1.5 h-1.5 rounded-full " + riskDotColor(f.risk_level)} />
                                                            {riskLabel(f.risk_level)}
                                                        </span>
                                                    </RiskTooltip>
                                                </div>

                                                {f.ai_classification_text && (
                                                    <p className="mt-2 text-xs text-slate-400 italic leading-relaxed">{f.ai_classification_text}</p>
                                                )}

                                                {(f.ai_act_article || f.action_required) && (
                                                    <div className="mt-2.5 pt-2.5 border-t border-white/[0.05] space-y-1.5">
                                                        {f.ai_act_article && (
                                                            <p className="text-xs text-slate-500">
                                                                <span className="text-slate-400 font-medium">Článek:</span> {f.ai_act_article}
                                                            </p>
                                                        )}
                                                        {f.action_required && (
                                                            <p className="text-xs text-slate-500">
                                                                <span className="text-fuchsia-400 font-medium">Co musíte udělat:</span>{" "}
                                                                <span className="text-slate-300">{f.action_required}</span>
                                                            </p>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </ScrollReveal>
                        ) : (
                            <ScrollReveal>
                                <div className="space-y-4">
                                    {/* Hlavní karta — varování nebo žádné nálezy */}
                                    {scanResult.scan_warning ? (() => {
                                        const warnType = scanResult.scan_warning.split("|")[0];
                                        const warnMsg = scanResult.scan_warning.split("|").slice(1).join("|");
                                        const isLogin = warnType === "LOGIN_WALL";
                                        const isSpa = warnType === "SPA_APP";
                                        const isOauth = warnType === "OAUTH_REDIRECT";
                                        return (
                                            <div className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-6 text-center">
                                                <div className="flex justify-center mb-3">
                                                    {isLogin || isOauth ? (
                                                        <IconLockClosed className="w-10 h-10 text-amber-400" />
                                                    ) : (
                                                        <IconGlobeAlt className="w-10 h-10 text-amber-400" />
                                                    )}
                                                </div>
                                                <h3 className="text-base font-bold text-white">
                                                    {isLogin && "Stránka vyžaduje přihlášení"}
                                                    {isOauth && "Stránka přesměrovala na přihlášení"}
                                                    {isSpa && "Detekována webová aplikace"}
                                                </h3>
                                                <p className="text-sm text-amber-300/80 mt-2 max-w-lg mx-auto leading-relaxed">
                                                    {warnMsg}
                                                </p>
                                                <p className="text-sm text-slate-400 mt-2 max-w-lg mx-auto leading-relaxed">
                                                    {(isLogin || isOauth)
                                                        ? "Náš skener analyzuje pouze veřejně dostupné stránky. Webové aplikace za přihlášením často využívají AI systémy intenzivněji."
                                                        : "Dynamická webová aplikace (SPA) — automatický sken nemohl analyzovat skutečný obsah. Tyto aplikace typicky využívají AI intenzivněji."
                                                    }
                                                </p>
                                            </div>
                                        );
                                    })() : (
                                        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] p-6 text-center">
                                            <IconCheckBadge className="w-10 h-10 text-slate-400 mx-auto mb-3" />
                                            <h3 className="text-base font-bold text-white">Sken nezachytil žádné aktivní AI systémy</h3>
                                            <p className="text-sm text-slate-400 mt-2 max-w-lg mx-auto leading-relaxed">
                                                To <strong className="text-white">neznamená, že žádné nepoužíváte</strong>.
                                                Mnoho AI nástrojů se načítá dynamicky — jen v určitou denní dobu, z konkrétní geolokace,
                                                po interakci uživatele, nebo běží na pozadí přes API.
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </ScrollReveal>
                        )}

                        {/* ── Odeslat report / Dashboard redirect ── */}
                        <ScrollReveal delay={5}>
                            {isLoggedIn ? (
                                <div className="rounded-xl border border-green-500/15 bg-green-500/5 p-5 text-center">
                                    <div className="flex items-center justify-center gap-2 mb-2">
                                        <IconCheckBadge className="w-5 h-5 text-green-400" />
                                        <h3 className="font-semibold text-white">Výsledky najdete ve vašem dashboardu</h3>
                                    </div>
                                    <p className="text-xs text-slate-400 mb-3">
                                        Jste přihlášeni — tento sken byl automaticky uložen do vašeho účtu.
                                    </p>
                                    <a href="/dashboard" className="inline-block btn-primary text-sm px-6 py-2.5">
                                        Přejít na dashboard →
                                    </a>
                                </div>
                            ) : (
                                <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-5 text-center">
                                    <div className="flex items-center justify-center gap-2 mb-2">
                                        <IconEnvelope className="w-5 h-5 text-fuchsia-400" />
                                        <h3 className="font-semibold text-white">Pošleme vám report na e-mail</h3>
                                    </div>
                                    <p className="text-xs text-slate-400 mb-3">
                                        Podrobný přehled nálezů, doporučení a ceník — vše v jednom e-mailu.
                                    </p>

                                    {emailSent ? (
                                        <div className="inline-flex items-center gap-2 text-green-400 font-medium text-sm">
                                            <IconCheckCircle className="w-4 h-4" /> Report odeslán na {reportEmail}
                                        </div>
                                    ) : (
                                        <div className="flex gap-2 max-w-sm mx-auto">
                                            <input
                                                type="email"
                                                value={reportEmail}
                                                onChange={(e) => setReportEmail(e.target.value)}
                                                placeholder="vas@email.cz"
                                                className="flex-1 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-white placeholder:text-slate-500 focus:ring-2 focus:ring-fuchsia-500/50 transition text-sm"
                                                required
                                            />
                                            <button
                                                onClick={handleSendReport}
                                                disabled={emailSending || !reportEmail}
                                                className="btn-primary text-sm disabled:opacity-50 px-4"
                                            >
                                                {emailSending ? "..." : "Odeslat"}
                                            </button>
                                        </div>
                                    )}
                                    <p className="text-[10px] text-slate-600 mt-2">Odesláním souhlasíte se zpracováním dle <a href="/vop" className="underline hover:text-slate-400">VOP</a>.</p>
                                </div>
                            )}
                        </ScrollReveal>

                        {/* ── CTA ceník ── */}
                        <ScrollReveal variant="scale-up" delay={6}>
                            <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 text-center">
                                <h3 className="font-semibold text-white">Chcete to vyřešit za vás?</h3>
                                <p className="text-sm text-slate-400 mt-1">
                                    Kompletní dokumentaci, transparenční stránku a vše potřebné pro soulad s AI Act.
                                </p>
                                <a href="/pricing" className="inline-block mt-3 btn-primary text-sm px-6 py-2.5">
                                    Zobrazit ceník služeb →
                                </a>
                            </div>
                        </ScrollReveal>
                    </div>
                )}

                {/* Error stav */}
                {scanResult && scanResult.status === "error" && (
                    <div className="mt-8 card text-center">
                        <IconExclamation className="w-10 h-10 text-red-400 mx-auto mb-2" />
                        <h2 className="text-lg font-semibold text-white">Skenování selhalo</h2>
                        <p className="mt-2 text-sm text-slate-500">
                            {scanResult.error_message?.includes("Timeout") || scanResult.error_message?.includes("timeout") ? (
                                <>Skenování {scanResult.url} trvalo příliš dlouho a bylo ukončeno. Web může být pomalý nebo blokuje automatické přístupy.</>
                            ) : scanResult.error_message?.includes("Stale") ? (
                                <>Skenování {scanResult.url} se zaseklo a bylo automaticky ukončeno. Zkuste to prosím znovu.</>
                            ) : (
                                <>Nepodařilo se naskenovat {scanResult.url}. Web může být nedostupný nebo blokuje automatické přístupy.</>
                            )}
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
                                    { icon: <IconCpu className="w-5 h-5 text-fuchsia-400" />, label: "Chatboty a konverzační AI", desc: "Smartsupp, Tidio, Intercom, LiveChat, Drift, Crisp a 30+ dalších" },
                                    { icon: <IconChartBar className="w-5 h-5 text-cyan-400" />, label: "AI analytika a sledování", desc: "GA4, Hotjar, Microsoft Clarity, Google Tag Manager" },
                                    { icon: <IconTarget className="w-5 h-5 text-cyan-400" />, label: "Doporučovací systémy", desc: "Algolia, Recombee, Nosto, Bloomreach, Luigi's Box" },
                                    { icon: <IconPhoto className="w-5 h-5 text-purple-400" />, label: "AI generovaný obsah", desc: "Copy.ai, Jasper, DALL-E, DeepL překlady, Surfer SEO" },
                                    { icon: <IconSearch className="w-5 h-5 text-green-400" />, label: "AI cílení reklam", desc: "Meta Pixel, TikTok Pixel, LinkedIn Insight, Seznam" },
                                    { icon: <IconShield className="w-5 h-5 text-blue-400" />, label: "A/B testování a personalizace", desc: "VWO, Optimizely, AB Tasty, Dynamic Yield" },
                                    { icon: <IconCode className="w-5 h-5 text-amber-400" />, label: "AI API a proxy detekce", desc: "OpenAI, Gemini, Claude, Cohere, Hugging Face endpointy" },
                                    { icon: <IconEye className="w-5 h-5 text-rose-400" />, label: "Heuristická AI analýza", desc: "WebSocket, WASM inference, CSP hlavičky, Schema.org" },
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
