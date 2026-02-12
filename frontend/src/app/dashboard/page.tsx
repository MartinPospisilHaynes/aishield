"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useAuth } from "@/lib/auth-context";
import {
    getDashboardData,
    startScan,
    getScanStatus,
    getScanFindings,
    type DashboardData,
    type ScanStatus,
    type Finding,
} from "@/lib/api";
import { createClient } from "@/lib/supabase-browser";

type Tab = "prehled" | "findings" | "dokumenty" | "plan" | "skeny" | "ucet";

/* ── Scan progress stages (reused from /scan) ── */
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

const TABS: { key: Tab; label: string; icon: React.ReactNode }[] = [
    {
        key: "prehled",
        label: "Přehled",
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
            </svg>
        ),
    },
    {
        key: "findings",
        label: "AI systémy",
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
        ),
    },
    {
        key: "dokumenty",
        label: "Dokumenty",
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
        ),
    },
    {
        key: "plan",
        label: "Akční plán",
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
        ),
    },
    {
        key: "skeny",
        label: "Historie skenů",
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
        ),
    },
    {
        key: "ucet",
        label: "Můj účet",
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
        ),
    },
];

const TEMPLATE_NAMES: Record<string, string> = {
    compliance_report: "Compliance Report",
    transparency_page: "Transparenční stránka",
    action_plan: "Akční plán",
    ai_register: "Registr AI systémů",
    chatbot_notices: "Chatbot oznámení",
    ai_policy: "Interní AI Policy",
    training_outline: "Osnova školení",
};

const RISK_COLORS: Record<string, string> = {
    high: "bg-red-500/20 text-red-400 border border-red-500/30",
    medium: "bg-amber-500/20 text-amber-400 border border-amber-500/30",
    low: "bg-green-500/20 text-green-400 border border-green-500/30",
};

export default function DashboardPage() {
    const { user, loading: authLoading } = useAuth();
    const [data, setData] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [activeTab, setActiveTab] = useState<Tab>("prehled");

    // ── Inline scan state ──
    const [scanActive, setScanActive] = useState(false);
    const [scanLoading, setScanLoading] = useState(false);
    const [scanError, setScanError] = useState<string | null>(null);
    const [scanResult, setScanResult] = useState<ScanStatus | null>(null);
    const [scanFindings, setScanFindings] = useState<Finding[]>([]);
    const [scanStage, setScanStage] = useState(0);
    const [scanDone, setScanDone] = useState(false);
    const pollingRef = useRef<NodeJS.Timeout | null>(null);
    const stageRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    // Clean up timers on unmount
    useEffect(() => {
        return () => {
            if (pollingRef.current) clearInterval(pollingRef.current);
            if (stageRef.current) clearTimeout(stageRef.current);
        };
    }, []);

    const reloadDashboard = useCallback(() => {
        if (!user?.email) return;
        getDashboardData(user.email)
            .then(setData)
            .catch(() => { /* silent */ });
    }, [user?.email]);

    const startStageAnimation = useCallback(() => {
        setScanStage(0);
        let stage = 0;
        const intervals = [1800, 2200, 2500, 2800, 3200, 3000, 3500, 4000, 3000, 2500];
        const advanceStage = () => {
            stage++;
            if (stage < SCAN_STAGES.length) {
                setScanStage(stage);
                stageRef.current = setTimeout(advanceStage, intervals[stage] || 2500);
            }
        };
        stageRef.current = setTimeout(advanceStage, intervals[0]);
    }, []);

    const fetchScanFindings = useCallback(async (id: string) => {
        try {
            const res = await getScanFindings(id);
            setScanFindings(res.findings);
        } catch { /* silent */ }
    }, []);

    const startScanPolling = useCallback(
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
                        setScanStage(SCAN_STAGES.length);
                        setScanLoading(false);
                        setScanDone(true);
                        if (status.status === "done") {
                            await fetchScanFindings(id);
                            // Reload dashboard data after scan completes
                            reloadDashboard();
                        }
                    }
                } catch { /* keep polling */ }
            }, 3000);
        },
        [fetchScanFindings, reloadDashboard]
    );

    const handleStartScan = useCallback(async () => {
        const scanUrl = data?.company?.url || user?.user_metadata?.web_url;
        if (!scanUrl) {
            setScanError("Nemáme URL vašeho webu. Zadejte URL při registraci.");
            setScanActive(true);
            return;
        }

        setScanActive(true);
        setScanLoading(true);
        setScanError(null);
        setScanResult(null);
        setScanFindings([]);
        setScanDone(false);
        if (pollingRef.current) clearInterval(pollingRef.current);
        if (stageRef.current) clearTimeout(stageRef.current);

        startStageAnimation();

        try {
            const result = await startScan(scanUrl);
            const status = await getScanStatus(result.scan_id);
            setScanResult(status);
            if (status.status === "queued" || status.status === "running") {
                startScanPolling(result.scan_id);
            } else {
                setScanLoading(false);
                if (stageRef.current) clearTimeout(stageRef.current);
                setScanStage(SCAN_STAGES.length);
                setScanDone(true);
                if (status.status === "done") {
                    await fetchScanFindings(result.scan_id);
                    reloadDashboard();
                }
            }
        } catch (err) {
            setScanError(err instanceof Error ? err.message : "Nastala neočekávaná chyba");
            setScanLoading(false);
            if (stageRef.current) clearTimeout(stageRef.current);
        }
    }, [data?.company?.url, user?.user_metadata?.web_url, startStageAnimation, startScanPolling, fetchScanFindings, reloadDashboard]);

    const closeScanPanel = () => {
        setScanActive(false);
        setScanDone(false);
        setScanError(null);
    };

    useEffect(() => {
        if (!user?.email) return;
        setLoading(true);
        getDashboardData(user.email)
            .then(setData)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, [user?.email]);

    if (authLoading || loading) {
        return (
            <section className="py-20">
                <div className="mx-auto max-w-7xl px-6">
                    <div className="flex items-center justify-center gap-3 py-20">
                        <div className="h-5 w-5 animate-spin rounded-full border-2 border-fuchsia-500 border-t-transparent" />
                        <span className="text-slate-400">Načítám dashboard...</span>
                    </div>
                </div>
            </section>
        );
    }

    if (error) {
        // Token errors → instruct user to re-login
        const isTokenError = error.includes("token") || error.includes("401") || error.includes("Neplatný");
        return (
            <section className="py-20">
                <div className="mx-auto max-w-md px-6">
                    <div className="glass text-center py-12">
                        {isTokenError ? (
                            <>
                                <div className="mx-auto mb-4 w-14 h-14 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
                                    <svg className="w-7 h-7 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m0 0v2m0-2h2m-2 0H10m2-6V4" />
                                    </svg>
                                </div>
                                <p className="text-amber-300 font-medium mb-2">Platnost přihlášení vypršela</p>
                                <p className="text-slate-400 text-sm mb-6">Přihlaste se prosím znovu.</p>
                                <a href="/login" className="btn-primary text-sm px-6 py-2">
                                    Přihlásit se
                                </a>
                            </>
                        ) : (
                            <>
                                <p className="text-red-400 mb-4">{error}</p>
                                <button onClick={handleStartScan} className="btn-primary text-sm px-6 py-2">
                                    Spustit první sken
                                </button>
                            </>
                        )}
                    </div>
                </div>
            </section>
        );
    }

    const companyName = data?.company?.name || user?.user_metadata?.company_name || "Vaše firma";
    const score = data?.compliance_score;
    const findingsCount = data?.findings.length || 0;
    const highRisk = data?.findings.filter((f) => f.risk_level === "high").length || 0;
    const docsCount = data?.documents.length || 0;

    return (
        <section className="py-8 relative">
            {/* BG glow */}
            <div className="absolute inset-0 -z-10">
                <div className="absolute top-[5%] right-[25%] h-[400px] w-[400px] rounded-full bg-fuchsia-500/5 blur-[130px]" />
            </div>

            <div className="mx-auto max-w-7xl px-6">
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
                    <div>
                        <h1 className="text-2xl font-extrabold">
                            Dashboard
                        </h1>
                        <p className="text-sm text-slate-400 mt-1">
                            {companyName} — {data?.company?.url || ""}
                        </p>
                    </div>
                    <div className="flex gap-3">
                        <button onClick={handleStartScan} disabled={scanLoading} className="btn-secondary text-sm px-4 py-2 disabled:opacity-50">
                            {scanLoading ? "Skenuji..." : "Nový sken"}
                        </button>
                        {(data?.scans.length || 0) > 0 ? (
                            <a href={`/dotaznik?company_id=${data?.company?.id || ''}${data?.questionnaire_status === 'dokončen' ? '&edit=true' : ''}`} className="btn-primary text-sm px-4 py-2">
                                {data?.questionnaire_status === 'dokončen' ? 'Upravit odpovědi' : 'Vyplnit dotazník'}
                            </a>
                        ) : (
                            <button disabled className="btn-primary text-sm px-4 py-2 opacity-40 cursor-not-allowed" title="Nejprve proveďte sken webu">
                                🔒 Dotazník
                            </button>
                        )}
                    </div>
                </div>

                {/* ═══ INLINE SCAN PANEL ═══ */}
                {scanActive && (
                    <div className="mb-8 rounded-2xl border border-fuchsia-500/20 bg-fuchsia-500/[0.03] p-6 relative">
                        {/* Close button (only when not loading) */}
                        {!scanLoading && (
                            <button onClick={closeScanPanel} className="absolute top-4 right-4 text-slate-500 hover:text-slate-300 transition-colors">
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        )}

                        {/* Error state */}
                        {scanError && !scanLoading && (
                            <div className="text-center py-4">
                                <div className="inline-flex items-center gap-2 text-red-400 mb-2">
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                    <span className="font-medium">{scanError}</span>
                                </div>
                                <button onClick={handleStartScan} className="btn-secondary text-sm px-4 py-2 mt-2">
                                    Zkusit znovu
                                </button>
                            </div>
                        )}

                        {/* Scanning progress */}
                        {scanLoading && (
                            <>
                                <div className="flex items-center gap-3 mb-5">
                                    <svg className="w-7 h-7 text-fuchsia-400 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                                    </svg>
                                    <div>
                                        <h3 className="font-semibold text-white">Skenování probíhá...</h3>
                                        <p className="text-sm text-slate-400">Analyzujeme {scanResult?.url || data?.company?.url || ""}</p>
                                    </div>
                                </div>

                                {/* Progress bar */}
                                <div className="mb-4">
                                    <div className="flex justify-between text-xs text-slate-500 mb-1.5">
                                        <span>{SCAN_STAGES[Math.min(scanStage, SCAN_STAGES.length - 1)]?.label}</span>
                                        <span>{Math.round(((scanStage + 1) / SCAN_STAGES.length) * 100)} %</span>
                                    </div>
                                    <div className="h-2.5 bg-white/[0.06] rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-gradient-to-r from-fuchsia-600 via-purple-500 to-cyan-500 rounded-full transition-all duration-1000 ease-out"
                                            style={{ width: ((scanStage + 1) / SCAN_STAGES.length) * 100 + "%" }}
                                        />
                                    </div>
                                </div>

                                {/* Stage list */}
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                                    {SCAN_STAGES.map((stage, i) => {
                                        const done = i < scanStage;
                                        const active = i === scanStage;
                                        return (
                                            <div key={i} className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs transition-all ${done ? "text-green-400/70" : active ? "text-fuchsia-300 bg-fuchsia-500/10" : "text-slate-600"}`}>
                                                {done ? (
                                                    <svg className="w-3.5 h-3.5 text-green-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" /></svg>
                                                ) : active ? (
                                                    <div className="w-3.5 h-3.5 flex-shrink-0"><div className="h-2 w-2 rounded-full bg-fuchsia-400 animate-pulse mx-auto mt-[3px]" /></div>
                                                ) : (
                                                    <div className="w-3.5 h-3.5 flex-shrink-0"><div className="h-1.5 w-1.5 rounded-full bg-slate-700 mx-auto mt-1" /></div>
                                                )}
                                                {stage.label}
                                            </div>
                                        );
                                    })}
                                </div>
                            </>
                        )}

                        {/* Scan complete */}
                        {scanDone && !scanLoading && !scanError && (
                            <div className="text-center py-4">
                                <div className="inline-flex items-center justify-center h-14 w-14 rounded-2xl bg-green-500/10 border border-green-500/20 mb-4">
                                    <svg className="w-7 h-7 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                </div>
                                <h3 className="font-semibold text-green-400 text-lg mb-1">Sken dokončen!</h3>
                                <p className="text-sm text-slate-400 mb-1">
                                    Nalezeno <span className="text-white font-bold">{scanFindings.length}</span> AI {scanFindings.length === 1 ? "systém" : scanFindings.length < 5 ? "systémy" : "systémů"}
                                </p>
                                {scanResult?.total_findings != null && scanResult.total_findings > 0 && (
                                    <p className="text-xs text-slate-500 mb-4">Výsledky byly uloženy do vašeho profilu</p>
                                )}
                                <div className="flex gap-3 justify-center">
                                    <button onClick={() => { closeScanPanel(); setActiveTab("findings"); }} className="btn-secondary text-sm px-4 py-2">
                                        Zobrazit nálezy
                                    </button>
                                    {(data?.scans.length || 0) > 0 && (
                                        <a href={`/dotaznik?company_id=${data?.company?.id || ''}${data?.questionnaire_status === 'dokončen' ? '&edit=true' : ''}`} className="btn-primary text-sm px-4 py-2">
                                            {data?.questionnaire_status === 'dokončen' ? 'Upravit odpovědi' : 'Vyplnit dotazník'}
                                        </a>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Stats cards */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                    <StatCard
                        label="Compliance skóre"
                        value={score != null ? `${score}%` : "—"}
                        sub={score != null ? (score >= 80 ? "Dobrý stav" : score >= 50 ? "Vyžaduje pozornost" : "Kritický stav") : "Sken zatím nebyl proveden"}
                        color={score != null ? (score >= 80 ? "text-green-400" : score >= 50 ? "text-amber-400" : "text-red-400") : "text-slate-500"}
                        icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>}
                    />
                    <StatCard
                        label="AI systémy nalezeny"
                        value={String(findingsCount)}
                        sub={highRisk > 0 ? `${highRisk} vysoké riziko · pouze ze skenu webu` : findingsCount > 0 ? "Pouze ze skenu webu" : "Sken zatím nebyl proveden"}
                        color={highRisk > 0 ? "text-red-400" : "text-green-400"}
                        icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>}
                        tooltip="Toto číslo zahrnuje pouze AI systémy nalezené skenem webu. Vyplněním dotazníku získáte přesnější analýzu včetně interních AI nástrojů."
                    />
                    <StatCard
                        label="Dokumenty"
                        value={`${docsCount}/7`}
                        sub={docsCount === 7 ? "Kompletní kit" : "Ke stažení"}
                        color={docsCount === 7 ? "text-green-400" : "text-cyan-400"}
                        icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>}
                    />
                    <StatCard
                        label="Dotazník"
                        value={data?.questionnaire_status === "dokončen" ? "Hotovo" : "Čeká"}
                        sub={data?.questionnaire_status === "dokončen" ? "Vyplněn — klikněte pro úpravu" : "Vyplňte pro přesnější analýzu"}
                        color={data?.questionnaire_status === "dokončen" ? "text-green-400" : "text-amber-400"}
                        icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" /></svg>}
                    />
                </div>

                {/* Tabs */}
                <div className="flex gap-1 overflow-x-auto border-b border-white/[0.06] mb-6">
                    {TABS.map((tab) => (
                        <button
                            key={tab.key}
                            onClick={() => setActiveTab(tab.key)}
                            className={`relative flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-all whitespace-nowrap ${activeTab === tab.key
                                ? "text-fuchsia-400"
                                : "text-slate-500 hover:text-slate-300"
                                }`}
                        >
                            {tab.icon}
                            {tab.label}
                            {activeTab === tab.key && (
                                <span className="absolute bottom-0 left-2 right-2 h-0.5 bg-gradient-to-r from-fuchsia-500 to-fuchsia-400 rounded-full" />
                            )}
                        </button>
                    ))}
                </div>

                {/* Tab content */}
                <div className="min-h-[400px]">
                    {activeTab === "prehled" && <TabPrehled data={data} onStartScan={handleStartScan} scanLoading={scanLoading} hasScans={(data?.scans.length || 0) > 0} />}
                    {activeTab === "findings" && <TabFindings findings={data?.findings || []} onStartScan={handleStartScan} />}
                    {activeTab === "dokumenty" && <TabDokumenty documents={data?.documents || []} />}
                    {activeTab === "plan" && <TabPlan findings={data?.findings || []} onStartScan={handleStartScan} />}
                    {activeTab === "skeny" && <TabSkeny scans={data?.scans || []} onStartScan={handleStartScan} />}
                    {activeTab === "ucet" && <TabUcet user={user} data={data} />}
                </div>
            </div>
        </section>
    );
}

/* ── Stat Card ── */
function StatCard({ label, value, sub, color, icon, tooltip }: {
    label: string; value: string; sub: string; color: string; icon?: React.ReactNode; tooltip?: string;
}) {
    const [showTip, setShowTip] = useState(false);
    return (
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 hover:border-white/[0.12] transition-all relative">
            <div className="flex items-center justify-between mb-1">
                <p className="text-xs text-slate-500 uppercase tracking-wider">{label}</p>
                <div className="flex items-center gap-1.5">
                    {tooltip && (
                        <button
                            onClick={() => setShowTip(!showTip)}
                            onMouseEnter={() => setShowTip(true)}
                            onMouseLeave={() => setShowTip(false)}
                            className="text-slate-600 hover:text-slate-400 transition-colors"
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </button>
                    )}
                    {icon && <span className="text-slate-600">{icon}</span>}
                </div>
            </div>
            <p className={`text-3xl font-extrabold mt-1 ${color}`}>{value}</p>
            <p className="text-xs text-slate-500 mt-1">{sub}</p>
            {tooltip && showTip && (
                <div className="absolute z-20 top-full left-0 right-0 mt-2 p-3 rounded-xl bg-slate-800 border border-white/[0.1] shadow-xl text-xs text-slate-300 leading-relaxed">
                    {tooltip}
                </div>
            )}
        </div>
    );
}

/* ── Tab: Přehled ── */
function TabPrehled({ data, onStartScan, scanLoading, hasScans: hasScansOverride }: { data: DashboardData | null; onStartScan: () => void; scanLoading: boolean; hasScans: boolean }) {
    const hasPaidOrder = data?.orders.some((o) => o.status === "PAID") || false;
    const hasScans = hasScansOverride || (data?.scans.length || 0) > 0;
    const hasQuest = data?.questionnaire_status === "dokončen";
    const hasDocs = (data?.documents.length || 0) > 0;

    const steps = [
        {
            done: hasScans,
            label: "Sken webu",
            desc: "Automatická detekce AI systémů na vašem webu",
            href: null as string | null, // handled by button
            cta: scanLoading ? "Skenuji..." : "Spustit sken",
            onClick: onStartScan,
        },
        {
            done: hasQuest,
            label: "Dotazník",
            desc: hasQuest ? "Odpovědi můžete kdykoli upravit" : "Upřesní analýzu o interní AI nástroje (ChatGPT, Copilot...)",
            href: hasScans ? `/dotaznik?company_id=${data?.company?.id || ''}${hasQuest ? '&edit=true' : ''}` : null,
            cta: hasScans ? (hasQuest ? "Upravit odpovědi" : "Vyplnit dotazník") : "🔒 Nejprve skenujte web",
            onClick: undefined as (() => void) | undefined,
        },
        {
            done: hasPaidOrder,
            label: "Objednávka",
            desc: "Odemkněte compliance dokumenty a akční plán",
            href: "/pricing",
            cta: "Vybrat balíček",
            onClick: undefined as (() => void) | undefined,
        },
        {
            done: hasDocs,
            label: "Dokumenty",
            desc: "7 PDF dokumentů pro splnění AI Act",
            href: "#",
            cta: "Viz tab Dokumenty",
            onClick: undefined as (() => void) | undefined,
        },
    ];

    const currentStepIndex = steps.findIndex((s) => !s.done);
    const currentStep = currentStepIndex >= 0 ? steps[currentStepIndex] : null;
    const completedCount = steps.filter((s) => s.done).length;
    const lineWidthPercent = completedCount <= 1 ? 0 : ((completedCount - 1) / (steps.length - 1)) * 75;

    // Processing timer: order paid but documents not yet generated
    const isProcessing = hasPaidOrder && !hasDocs;
    const currentHour = new Date().getHours();
    const isBusinessHours = currentHour >= 8 && currentHour < 16;

    return (
        <div className="space-y-6">
            {/* Progress Timeline */}
            <div className="glass">
                <h3 className="font-semibold mb-8">Postup k compliance</h3>

                {/* Horizontal step progress bar */}
                <div className="grid grid-cols-4 relative mb-8">
                    {/* Background connecting line */}
                    <div className="absolute top-5 left-[12.5%] right-[12.5%] h-0.5 bg-white/[0.06]" />
                    {/* Completed portion of line */}
                    {lineWidthPercent > 0 && (
                        <div
                            className="absolute top-5 left-[12.5%] h-0.5 bg-gradient-to-r from-green-500 to-emerald-400 transition-all duration-700 rounded-full"
                            style={{ width: `${lineWidthPercent}%` }}
                        />
                    )}

                    {steps.map((step, i) => {
                        const isCurrent = i === currentStepIndex;
                        return (
                            <div key={i} className="flex flex-col items-center relative z-10">
                                <div
                                    className={`flex items-center justify-center h-10 w-10 rounded-full text-sm font-bold transition-all duration-300 ${step.done
                                        ? "bg-green-500/20 text-green-400 border-2 border-green-500/40 shadow-[0_0_12px_rgba(34,197,94,0.15)]"
                                        : isCurrent
                                            ? "bg-fuchsia-500/20 text-fuchsia-400 border-2 border-fuchsia-500/40 shadow-[0_0_12px_rgba(217,70,239,0.15)] animate-pulse"
                                            : "bg-slate-900 text-slate-600 border-2 border-white/[0.08]"
                                        }`}
                                >
                                    {step.done ? (
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                                        </svg>
                                    ) : (
                                        i + 1
                                    )}
                                </div>
                                <span
                                    className={`text-xs mt-2.5 font-medium text-center ${step.done
                                        ? "text-green-400/80"
                                        : isCurrent
                                            ? "text-fuchsia-400"
                                            : "text-slate-600"
                                        }`}
                                >
                                    {step.label}
                                </span>
                            </div>
                        );
                    })}
                </div>

                {/* Current step detail card */}
                {currentStep && (
                    <div className="rounded-xl border border-fuchsia-500/20 bg-fuchsia-500/[0.04] p-5">
                        <div className="flex items-center gap-3 mb-2">
                            <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-fuchsia-500/20 text-fuchsia-400 text-xs font-bold">
                                {currentStepIndex + 1}
                            </span>
                            <h4 className="font-semibold text-fuchsia-300">{currentStep.label}</h4>
                        </div>
                        <p className="text-sm text-slate-400 mb-4 ml-9">{currentStep.desc}</p>
                        {currentStep.onClick ? (
                            <button onClick={currentStep.onClick} disabled={scanLoading} className="btn-primary text-sm px-5 py-2 ml-9 inline-block disabled:opacity-50">
                                {currentStep.cta}
                            </button>
                        ) : currentStep.href && currentStep.href !== "#" ? (
                            <a href={currentStep.href} className="btn-primary text-sm px-5 py-2 ml-9 inline-block">
                                {currentStep.cta}
                            </a>
                        ) : !currentStep.href ? (
                            <span className="text-sm text-slate-500 ml-9 inline-block opacity-60">
                                {currentStep.cta}
                            </span>
                        ) : null}
                    </div>
                )}

                {/* All steps done */}
                {!currentStep && (
                    <div className="rounded-xl border border-green-500/20 bg-green-500/[0.04] p-5 text-center">
                        <svg className="w-8 h-8 text-green-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <h4 className="font-semibold text-green-400">Všechny kroky dokončeny!</h4>
                        <p className="text-sm text-slate-400 mt-1">Vaše compliance dokumenty jsou připraveny ke stažení.</p>
                    </div>
                )}
            </div>

            {/* Processing timer — shown when paid but docs not ready */}
            {isProcessing && (
                <div className="glass border-fuchsia-500/20">
                    <div className="flex items-center gap-5">
                        {/* Animated circular progress */}
                        <div className="relative flex-shrink-0 h-16 w-16">
                            <svg className="w-16 h-16 animate-spin" style={{ animationDuration: "3s" }} viewBox="0 0 64 64" fill="none">
                                <circle cx="32" cy="32" r="28" stroke="currentColor" strokeWidth="3" className="text-white/[0.06]" />
                                <circle
                                    cx="32" cy="32" r="28"
                                    stroke="url(#proc-grad)"
                                    strokeWidth="3"
                                    strokeLinecap="round"
                                    strokeDasharray="80 96"
                                />
                                <defs>
                                    <linearGradient id="proc-grad" x1="0" y1="0" x2="64" y2="64">
                                        <stop offset="0%" stopColor="#d946ef" />
                                        <stop offset="100%" stopColor="#06b6d4" />
                                    </linearGradient>
                                </defs>
                            </svg>
                            <div className="absolute inset-0 flex items-center justify-center">
                                <svg className="w-6 h-6 text-fuchsia-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                        </div>
                        <div>
                            <h3 className="font-semibold text-slate-200">Zpracováváme vaši objednávku</h3>
                            <p className="text-sm text-slate-400 mt-1">
                                {isBusinessHours
                                    ? "Obvykle do 4 hodin (doručujeme 8:00\u201316:00)"
                                    : "Výsledky budou doručeny zítra ráno v 8:00"}
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Poslední objednávky */}
            {data?.orders && data.orders.length > 0 && (
                <div className="glass">
                    <h3 className="font-semibold mb-4">Objednávky</h3>
                    <div className="space-y-2">
                        {data.orders.map((order) => (
                            <div key={order.order_number} className="flex items-center justify-between rounded-lg border border-white/[0.06] bg-white/[0.02] px-4 py-3 text-sm hover:border-white/[0.12] transition-all">
                                <div>
                                    <span className="text-slate-300 font-medium">{order.order_number}</span>
                                    <span className="text-slate-500 ml-2">({order.plan.toUpperCase()})</span>
                                </div>
                                <div className="flex items-center gap-4">
                                    <span className="text-slate-400">
                                        {new Intl.NumberFormat("cs-CZ").format(order.amount)} Kč
                                    </span>
                                    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${order.status === "PAID"
                                        ? "bg-green-500/10 text-green-400"
                                        : order.status === "CREATED"
                                            ? "bg-amber-500/10 text-amber-400"
                                            : "bg-red-500/10 text-red-400"
                                        }`}>
                                        {order.status === "PAID" ? "Zaplaceno" : order.status === "CREATED" ? "Čeká" : order.status}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

/* ── Tab: AI systémy (Findings) ── */
function TabFindings({ findings, onStartScan }: { findings: DashboardData["findings"]; onStartScan: () => void }) {
    if (findings.length === 0) {
        return (
            <EmptyState
                title="Zatím žádné AI systémy"
                description="Spusťte sken webu pro automatickou detekci AI systémů na vašem webu."
                onAction={onStartScan}
                cta="Spustit sken"
                illustration={
                    <svg className="w-10 h-10 text-fuchsia-500/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                }
            />
        );
    }

    return (
        <div className="space-y-3">
            {findings.map((f) => (
                <div key={f.id} className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 hover:border-white/[0.12] transition-all">
                    <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-3 mb-2">
                                <h4 className="font-semibold text-slate-200">{f.name}</h4>
                                <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${RISK_COLORS[f.risk_level] || RISK_COLORS.low
                                    }`}>
                                    {f.risk_level === "high" ? "Vysoké" : f.risk_level === "medium" ? "Střední" : "Nízké"} riziko
                                </span>
                            </div>
                            <p className="text-sm text-slate-400 mb-2">{f.action_required}</p>
                            <div className="flex items-center gap-4 text-xs text-slate-500">
                                <span>Kategorie: {f.category}</span>
                                <span>AI Act: {f.ai_act_article}</span>
                                {f.confirmed_by_client && (
                                    <span className={
                                        f.confirmed_by_client === "false_positive"
                                            ? "text-slate-500"
                                            : "text-amber-400"
                                    }>
                                        {f.confirmed_by_client === "false_positive" ? "Falešný poplach" : "Potvrzeno"}
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}

/* ── Tab: Dokumenty ── */
function TabDokumenty({ documents }: { documents: DashboardData["documents"] }) {
    if (documents.length === 0) {
        return (
            <EmptyState
                title="Zatím žádné dokumenty"
                description="Dokumenty se generují po zaplacení balíčku."
                href="/pricing"
                cta="Vybrat balíček"
                illustration={
                    <svg className="w-10 h-10 text-cyan-500/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                    </svg>
                }
            />
        );
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {documents.map((doc) => (
                <div key={doc.id} className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 flex items-center gap-4 hover:border-white/[0.12] transition-all">
                    <div className="flex-shrink-0 h-12 w-12 rounded-xl bg-fuchsia-500/10 flex items-center justify-center">
                        <svg className="w-6 h-6 text-fuchsia-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-slate-200 text-sm">
                            {TEMPLATE_NAMES[doc.template_key] || doc.name || doc.template_key}
                        </h4>
                        <p className="text-xs text-slate-500 mt-0.5">
                            {new Date(doc.created_at).toLocaleDateString("cs-CZ")}
                        </p>
                    </div>
                    {doc.file_url && (
                        <a
                            href={doc.file_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="btn-secondary text-xs px-3 py-1.5 flex-shrink-0"
                        >
                            Stáhnout PDF
                        </a>
                    )}
                </div>
            ))}
        </div>
    );
}

/* ── Tab: Akční plán ── */
function TabPlan({ findings, onStartScan }: { findings: DashboardData["findings"]; onStartScan: () => void }) {
    if (findings.length === 0) {
        return (
            <EmptyState
                title="Akční plán je prázdný"
                description="Nejdříve proveďte sken webu — akční plán se vygeneruje z nálezů."
                onAction={onStartScan}
                cta="Spustit sken"
                illustration={
                    <svg className="w-10 h-10 text-amber-500/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                    </svg>
                }
            />
        );
    }

    // Seřadit: high → medium → low, nepotvrzené první
    const sorted = [...findings].sort((a, b) => {
        const riskOrder: Record<string, number> = { high: 0, medium: 1, low: 2 };
        const rA = riskOrder[a.risk_level] ?? 3;
        const rB = riskOrder[b.risk_level] ?? 3;
        if (rA !== rB) return rA - rB;
        // Nevyřešené první
        const aResolved = a.confirmed_by_client === "false_positive" || a.status === "resolved";
        const bResolved = b.confirmed_by_client === "false_positive" || b.status === "resolved";
        if (aResolved !== bResolved) return aResolved ? 1 : -1;
        return 0;
    });

    const total = sorted.length;
    const resolved = sorted.filter(
        (f) => f.confirmed_by_client === "false_positive" || f.status === "resolved"
    ).length;

    return (
        <div className="space-y-4">
            {/* Progress bar */}
            <div className="glass">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-slate-300">Postup</span>
                    <span className="text-sm text-slate-400">{resolved}/{total} vyřešeno</span>
                </div>
                <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                    <div
                        className="h-full rounded-full bg-gradient-to-r from-fuchsia-500 to-cyan-500 transition-all duration-500"
                        style={{ width: `${total > 0 ? (resolved / total) * 100 : 0}%` }}
                    />
                </div>
            </div>

            {/* Action items */}
            {sorted.map((f) => {
                const isResolved = f.confirmed_by_client === "false_positive" || f.status === "resolved";
                return (
                    <div
                        key={f.id}
                        className={`flex items-start gap-4 rounded-xl border px-5 py-4 ${isResolved
                            ? "border-green-500/10 bg-green-500/[0.03] opacity-60"
                            : "border-white/[0.06] bg-white/[0.02]"
                            }`}
                    >
                        <div className={`flex-shrink-0 mt-0.5 h-5 w-5 rounded-md border ${isResolved
                            ? "border-green-500/30 bg-green-500/20"
                            : "border-white/10 bg-white/5"
                            } flex items-center justify-center`}>
                            {isResolved && (
                                <svg className="w-3 h-3 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                </svg>
                            )}
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className={`text-sm font-medium ${isResolved ? "line-through text-slate-500" : "text-slate-200"}`}>
                                {f.action_required || f.name}
                            </p>
                            <div className="flex items-center gap-3 mt-1">
                                <span className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium ${RISK_COLORS[f.risk_level] || RISK_COLORS.low
                                    }`}>
                                    {f.risk_level === "high" ? "Vysoká priorita" : f.risk_level === "medium" ? "Střední" : "Nízká"}
                                </span>
                                <span className="text-[10px] text-slate-500">{f.ai_act_article}</span>
                            </div>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

/* ── Tab: Historie skenů ── */
function TabSkeny({ scans, onStartScan }: { scans: DashboardData["scans"]; onStartScan: () => void }) {
    if (scans.length === 0) {
        return (
            <EmptyState
                title="Zatím žádné skeny"
                description="Spusťte první sken pro detekci AI systémů na vašem webu."
                onAction={onStartScan}
                cta="Spustit sken"
                illustration={
                    <svg className="w-10 h-10 text-emerald-500/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                }
            />
        );
    }

    return (
        <div className="space-y-3">
            {scans.map((scan, i) => (
                <div key={scan.id} className="flex items-center gap-4 rounded-xl border border-white/[0.06] bg-white/[0.02] px-5 py-4 hover:border-white/[0.12] transition-all">
                    {/* Timeline dot */}
                    <div className="flex flex-col items-center gap-1">
                        <div className={`h-3 w-3 rounded-full ${scan.status === "completed"
                            ? "bg-green-500"
                            : scan.status === "running"
                                ? "bg-amber-500 animate-pulse"
                                : "bg-red-500"
                            }`} />
                        {i < scans.length - 1 && <div className="w-px h-8 bg-white/[0.06]" />}
                    </div>

                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3">
                            <p className="text-sm font-medium text-slate-200 truncate">{scan.url}</p>
                            <span className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium ${scan.status === "completed"
                                ? "bg-green-500/10 text-green-400"
                                : scan.status === "running"
                                    ? "bg-amber-500/10 text-amber-400"
                                    : "bg-red-500/10 text-red-400"
                                }`}>
                                {scan.status === "completed" ? "Dokončen" : scan.status === "running" ? "Probíhá" : scan.status}
                            </span>
                        </div>
                        <div className="flex items-center gap-4 text-xs text-slate-500 mt-1">
                            <span>{new Date(scan.created_at).toLocaleDateString("cs-CZ", {
                                day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit"
                            })}</span>
                            <span>{scan.total_findings} nálezů</span>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}

/* ── Tab: Můj účet ── */
function TabUcet({ user, data }: { user: any; data: DashboardData | null }) {
    const [passwordLoading, setPasswordLoading] = useState(false);
    const [passwordMsg, setPasswordMsg] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");

    const meta = user?.user_metadata || {};
    const companyName = meta.company_name || data?.company?.name || "—";
    const ico = meta.ico || "—";
    const webUrl = meta.web_url || data?.company?.url || "—";
    const registeredAt = user?.created_at
        ? new Date(user.created_at).toLocaleDateString("cs-CZ", {
            day: "numeric", month: "long", year: "numeric"
        })
        : "—";

    const handlePasswordChange = async (e: React.FormEvent) => {
        e.preventDefault();
        if (newPassword !== confirmPassword) {
            setPasswordMsg("Hesla se neshodují");
            return;
        }
        if (newPassword.length < 6) {
            setPasswordMsg("Heslo musí mít alespoň 6 znaků");
            return;
        }
        setPasswordLoading(true);
        setPasswordMsg("");
        try {
            const supabase = createClient();
            const { error } = await supabase.auth.updateUser({ password: newPassword });
            if (error) throw error;
            setPasswordMsg("✅ Heslo bylo změněno");
            setNewPassword("");
            setConfirmPassword("");
        } catch (err: any) {
            setPasswordMsg(`❌ ${err.message || "Chyba při změně hesla"}`);
        } finally {
            setPasswordLoading(false);
        }
    };

    return (
        <div className="space-y-6 max-w-2xl">
            {/* Údaje o firmě */}
            <div className="glass">
                <h3 className="font-semibold mb-5 flex items-center gap-2">
                    <svg className="w-5 h-5 text-fuchsia-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                    Údaje o firmě
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <InfoRow label="Název firmy" value={companyName} />
                    <InfoRow label="IČO" value={ico} />
                    <InfoRow label="Web" value={webUrl} isUrl />
                    <InfoRow label="Email" value={user?.email || "—"} />
                    <InfoRow label="Registrace" value={registeredAt} />
                    <InfoRow label="Partner" value={meta.partner || "—"} />
                </div>
            </div>

            {/* Objednávky */}
            {data?.orders && data.orders.length > 0 && (
                <div className="glass">
                    <h3 className="font-semibold mb-5 flex items-center gap-2">
                        <svg className="w-5 h-5 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                        Historie objednávek
                    </h3>
                    <div className="space-y-2">
                        {data.orders.map((order) => (
                            <div key={order.order_number} className="flex flex-col sm:flex-row sm:items-center justify-between rounded-lg border border-white/[0.06] bg-white/[0.02] px-4 py-3 text-sm gap-2">
                                <div className="flex items-center gap-3">
                                    <span className="text-slate-300 font-medium font-mono text-xs">{order.order_number}</span>
                                    <span className="text-slate-500 text-xs">{order.plan.toUpperCase()}</span>
                                </div>
                                <div className="flex items-center gap-4">
                                    <span className="text-slate-400 text-xs">
                                        {new Date(order.created_at).toLocaleDateString("cs-CZ")}
                                    </span>
                                    <span className="text-slate-300 font-medium">
                                        {new Intl.NumberFormat("cs-CZ").format(order.amount)} Kč
                                    </span>
                                    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${order.status === "PAID"
                                        ? "bg-green-500/10 text-green-400"
                                        : order.status === "CREATED"
                                            ? "bg-amber-500/10 text-amber-400"
                                            : "bg-red-500/10 text-red-400"
                                        }`}>
                                        {order.status === "PAID" ? "Zaplaceno" : order.status === "CREATED" ? "Čeká na platbu" : order.status}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Změna hesla */}
            <div className="glass">
                <h3 className="font-semibold mb-5 flex items-center gap-2">
                    <svg className="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                    </svg>
                    Změna hesla
                </h3>
                <form onSubmit={handlePasswordChange} className="space-y-4 max-w-sm">
                    <div>
                        <label className="block text-sm text-slate-400 mb-1">Nové heslo</label>
                        <input
                            type="password"
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            placeholder="Minimálně 6 znaků"
                            minLength={6}
                            required
                            className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5
                                text-white placeholder:text-slate-500 text-sm
                                focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/30
                                transition-all"
                        />
                    </div>
                    <div>
                        <label className="block text-sm text-slate-400 mb-1">Potvrdit nové heslo</label>
                        <input
                            type="password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            placeholder="Zadejte heslo znovu"
                            minLength={6}
                            required
                            className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5
                                text-white placeholder:text-slate-500 text-sm
                                focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/30
                                transition-all"
                        />
                    </div>
                    {passwordMsg && (
                        <p className={`text-sm ${passwordMsg.startsWith("✅") ? "text-green-400" : "text-red-400"}`}>
                            {passwordMsg}
                        </p>
                    )}
                    <button
                        type="submit"
                        disabled={passwordLoading}
                        className="btn-secondary text-sm px-5 py-2 disabled:opacity-50"
                    >
                        {passwordLoading ? "Ukládám..." : "Změnit heslo"}
                    </button>
                </form>
            </div>
        </div>
    );
}

/* ── Info Row ── */
function InfoRow({ label, value, isUrl }: { label: string; value: string; isUrl?: boolean }) {
    return (
        <div className="rounded-lg border border-white/[0.04] bg-white/[0.01] px-4 py-3">
            <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-0.5">{label}</p>
            {isUrl && value !== "—" ? (
                <a href={value.startsWith("http") ? value : `https://${value}`}
                    target="_blank" rel="noopener noreferrer"
                    className="text-sm text-cyan-400 hover:text-cyan-300 truncate block">
                    {value}
                </a>
            ) : (
                <p className="text-sm text-slate-200 truncate">{value}</p>
            )}
        </div>
    );
}

/* ── Empty State ── */
function EmptyState({ title, description, href, cta, onAction, illustration }: {
    title: string; description: string; href?: string; cta: string; onAction?: () => void; illustration?: React.ReactNode;
}) {
    return (
        <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="h-20 w-20 rounded-2xl bg-white/[0.02] border border-white/[0.06] flex items-center justify-center mb-5">
                {illustration || (
                    <svg className="w-10 h-10 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                    </svg>
                )}
            </div>
            <h3 className="font-semibold text-slate-300 mb-1">{title}</h3>
            <p className="text-sm text-slate-500 max-w-sm mb-6">{description}</p>
            {onAction ? (
                <button onClick={onAction} className="btn-primary text-sm px-6 py-2.5">
                    {cta}
                </button>
            ) : href ? (
                <a href={href} className="btn-primary text-sm px-6 py-2.5">
                    {cta}
                </a>
            ) : null}
        </div>
    );
}
