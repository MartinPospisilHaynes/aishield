"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useAuth } from "@/lib/auth-context";
import {
    getDashboardData,
    startScan,
    getScanStatus,
    getScanFindings,
    getQuestionnaireProgress,
    createCheckout,
    type DashboardData,
    type ScanStatus,
    type Finding,
    type QuestionnaireProgress,
    type QuestionnaireFinding,
    type QuestionnaireUnknown,
} from "@/lib/api";
import { createClient } from "@/lib/supabase-browser";
import ContactForm from "@/components/contact-form";

type Tab = "prehled" | "findings" | "dokumenty" | "plan" | "skeny" | "ucet";


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


const TABS: { key: Tab; label: string; icon: React.ReactNode }[] = [
    {
        key: "prehled",
        label: "Přehled",
        icon: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zm10 0a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>),
    },
    {
        key: "findings",
        label: "AI systémy",
        icon: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>),
    },
    {
        key: "dokumenty",
        label: "Dokumenty",
        icon: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>),
    },
    {
        key: "plan",
        label: "Musíte doplnit",
        icon: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" /></svg>),
    },
    {
        key: "skeny",
        label: "Historie skenů",
        icon: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>),
    },
    {
        key: "ucet",
        label: "Můj účet",
        icon: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>),
    },
];


const TEMPLATE_NAMES: Record<string, string> = {
    compliance_report: "Compliance Report",
    transparency_page: "Transparenční stránka",
    action_plan: "Kroky ke splnění",
    ai_register: "Registr AI systémů",
    chatbot_notices: "Chatbot oznámení",
    ai_policy: "Interní AI Policy",
    training_outline: "Osnova školení",
};

const RISK_COLORS: Record<string, string> = {
    high: "bg-red-500/20 text-red-400 border border-red-500/30",
    medium: "bg-amber-500/20 text-amber-400 border border-amber-500/30",
    limited: "bg-cyan-500/15 text-cyan-300 border border-cyan-400/25",
    low: "bg-cyan-500/15 text-cyan-300 border border-cyan-400/25",
    minimal: "bg-slate-500/15 text-slate-400 border border-slate-500/25",
};

/* ── Obligation labels per risk level — dle skutečného znění EU AI Act ── */
const OBLIGATION_LABEL: Record<string, string> = {
    high: "Čl. 6 — vysoce rizikový systém",
    medium: "Čl. 50 — transparenční povinnosti",
    limited: "Čl. 50 — transparenční povinnosti",
    low: "Čl. 50 — transparenční povinnosti",
    minimal: "Minimální riziko",
};

/* ── Layman-friendly AI system explanations ── */
const AI_SYSTEM_EXPLANATIONS: Record<string, string> = {
    "Google Analytics": "Sleduje n\u00e1vštěvnost webu \u2013 Google ho může používat k trénování AI modelů pro cílení reklam.",
    "Google Tag Manager": "Správce měřicích skriptů \u2013 s\u00e1m o sobě AI není, ale může nač\u00edtat AI n\u00e1stroje třetích stran.",
    "Google Ads": "Reklamní systém Google s AI optimalizací \u2013 automaticky cílí reklamy na z\u00e1kladě chov\u00e1ní uživatelů.",
    "Google reCAPTCHA": "Ochrana proti botům pomocí AI \u2013 analyzuje chov\u00e1ní uživatele a rozhoduje, zda je člověk.",
    "Facebook Pixel": "Sledovací k\u00f3d Facebooku/Meta \u2013 AI vyhodnocuje chov\u00e1ní n\u00e1vštěvníků pro cílenou reklamu.",
    "Meta Pixel": "Sledovací k\u00f3d Meta \u2013 AI vyhodnocuje chov\u00e1ní n\u00e1vštěvníků pro cílenou reklamu.",
    "Hotjar": "N\u00e1stroj pro analýzu chov\u00e1ní na webu \u2013 zaznamen\u00e1v\u00e1 pohyb myši a klik\u00e1ní, AI vytv\u00e1ří heatmapy.",
    "ChatGPT": "AI chatbot od OpenAI \u2013 generuje odpovědi na dotazy uživatelů.",
    "Intercom": "Z\u00e1kaznický chat s AI asistencí \u2013 AI navrhuje odpovědi a automatizuje konverzace.",
    "Tidio": "Chatbot s AI \u2013 odpov\u00edd\u00e1 na dotazy z\u00e1kazníků a pom\u00e1h\u00e1 s prodejem.",
    "HubSpot": "Marketingov\u00e1 platforma s AI \u2013 personalizuje obsah a automatizuje kampaně.",
    "Cloudflare": "CDN a bezpečnost \u2013 AI detekce botů a DDoS \u00fatolů.",
    "YouTube": "Video platforma Google \u2013 AI doporučuje videa, pokud m\u00e1te embed.",
    "Stripe": "Platební br\u00e1na \u2013 AI detekuje podvodn\u00e9 transakce.",
    "Clarity": "Microsoft Clarity \u2013 AI heatmapy a nahr\u00e1v\u00e1ní sessions.",
    "LinkedIn Insight Tag": "Sledovací k\u00f3d LinkedIn \u2013 AI cílení B2B reklam.",
};

/* ── Count unique AI systems (group by name) ── */
function countUniqueSystems(findings: DashboardData["findings"]): number {
    const names = new Set(findings.map(f => f.name));
    return names.size;
}

/** Czech declension helper: 1 krok / 2–4 kroky / 5+ kroků */
function cz(n: number, one: string, twoFour: string, fivePlus: string): string {
    if (n === 1) return one;
    if (n >= 2 && n <= 4) return twoFour;
    return fivePlus;
}

/* ── Group findings by unique name ── */
function groupFindings(findings: DashboardData["findings"]): Array<{ name: string; risk_level: string; category: string; action_required: string; ai_act_article: string; count: number }> {
    const map = new Map<string, typeof findings[0] & { count: number }>();
    for (const f of findings) {
        if (!map.has(f.name)) {
            map.set(f.name, { ...f, count: 1 });
        } else {
            map.get(f.name)!.count++;
        }
    }
    return Array.from(map.values());
}


export default function DashboardPage() {
    const { user, loading: authLoading } = useAuth();
    const [data, setData] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [activeTab, setActiveTab] = useState<Tab>("prehled");

    // ── Questionnaire progress ──
    const [questProgress, setQuestProgress] = useState<QuestionnaireProgress | null>(null);

    // ── AI systems card expand ──
    const [aiCardOpen, setAiCardOpen] = useState(false);

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

    // Fetch questionnaire progress when we have company_id
    useEffect(() => {
        if (!data?.company?.id) return;
        getQuestionnaireProgress(data.company.id)
            .then(setQuestProgress)
            .catch(() => { /* silent */ });
    }, [data?.company?.id]);

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
                                <a href="/login" className="btn-primary text-sm px-6 py-2">Přihlásit se</a>
                            </>
                        ) : (
                            <>
                                <p className="text-red-400 mb-4">{error}</p>
                                <button onClick={handleStartScan} className="btn-primary text-sm px-6 py-2">Spustit první sken</button>
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
    const uniqueSystemsCount = countUniqueSystems(data?.findings || []);
    const highRisk = data?.findings.filter((f) => f.risk_level === "high").length || 0;
    const docsCount = data?.documents.length || 0;
    const hasScans = (data?.scans.length || 0) > 0;
    const hasQuest = data?.questionnaire_status === "dokončen";
    const questPercentage = questProgress?.percentage ?? 0;
    const questStatus = questProgress?.status ?? "nezahajeno";
    const qFindings = data?.questionnaire_findings || [];
    const qUnknowns = data?.questionnaire_unknowns || [];
    const qSummary = data?.questionnaire_summary || null;
    const qHighRisk = qFindings.filter((f) => f.risk_level === "high").length;
    const totalSystems = uniqueSystemsCount + qFindings.length;

    return (
        <>
            <section className="py-8 relative">
                {/* BG glow */}
                <div className="absolute inset-0 -z-10">
                    <div className="absolute top-[5%] right-[25%] h-[400px] w-[400px] rounded-full bg-fuchsia-500/5 blur-[130px]" />
                </div>

                <div className="mx-auto max-w-7xl px-6">
                    {/* Header */}
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
                        <div>
                            <h1 className="text-2xl font-extrabold">Dashboard</h1>
                            <p className="text-sm text-slate-300 mt-1 truncate">{(data?.company?.url || "").replace(/^https?:\/\//i, "").replace(/\/+$/, "")}</p>
                        </div>
                        <div className="flex gap-2 sm:gap-3 flex-wrap">
                            <button onClick={handleStartScan} disabled={scanLoading} className="btn-secondary text-sm px-3 sm:px-4 py-2 disabled:opacity-50">
                                {scanLoading ? "Skenuji..." : "Nový sken"}
                            </button>
                            {hasScans ? (
                                <a href={`/dotaznik?company_id=${data?.company?.id || ''}${hasQuest ? '&edit=true' : ''}`} className="btn-primary text-sm px-4 py-2">
                                    {hasQuest ? 'Upravit odpovědi' : 'Vyplnit dotazník'}
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
                        <div className="mb-8 rounded-2xl border border-fuchsia-500/20 bg-fuchsia-500/[0.03] p-4 sm:p-6 relative">
                            {!scanLoading && (
                                <button onClick={closeScanPanel} className="absolute top-4 right-4 text-slate-500 hover:text-slate-300 transition-colors">
                                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>
                            )}

                            {scanError && !scanLoading && (
                                <div className="text-center py-4">
                                    <div className="inline-flex items-center gap-2 text-red-400 mb-2">
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                        <span className="font-medium">{scanError}</span>
                                    </div>
                                    <button onClick={handleStartScan} className="btn-secondary text-sm px-4 py-2 mt-2">Zkusit znovu</button>
                                </div>
                            )}

                            {scanLoading && (
                                <div className="space-y-4">
                                    <div className="flex items-center gap-4">
                                        <div className="relative h-12 w-12 flex-shrink-0">
                                            <svg className="w-12 h-12 animate-spin" style={{ animationDuration: "2.5s" }} viewBox="0 0 48 48" fill="none">
                                                <circle cx="24" cy="24" r="20" stroke="currentColor" strokeWidth="2" className="text-white/[0.06]" />
                                                <circle cx="24" cy="24" r="20" stroke="url(#scan-grad)" strokeWidth="2" strokeLinecap="round" strokeDasharray="60 66" />
                                                <defs><linearGradient id="scan-grad" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#d946ef" /><stop offset="100%" stopColor="#06b6d4" /></linearGradient></defs>
                                            </svg>
                                        </div>
                                        <div className="flex-1">
                                            <h3 className="font-semibold text-sm">{SCAN_STAGES[Math.min(scanStage, SCAN_STAGES.length - 1)]?.label}</h3>
                                            <p className="text-xs text-slate-400">{SCAN_STAGES[Math.min(scanStage, SCAN_STAGES.length - 1)]?.desc}</p>
                                        </div>
                                    </div>
                                    <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                                        <div className="h-full rounded-full bg-gradient-to-r from-fuchsia-500 to-cyan-500 transition-all duration-1000" style={{ width: `${((scanStage + 1) / SCAN_STAGES.length) * 100}%` }} />
                                    </div>
                                    {scanStage >= 7 && (
                                        <div className="flex items-start gap-2 rounded-lg bg-white/[0.03] border border-slate-700/50 px-3 py-2.5 mt-2">
                                            <svg className="w-4 h-4 text-cyan-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                            </svg>
                                            <p className="text-xs text-slate-300 leading-relaxed">
                                                Nezavírejte okno prohlížeče. Vyhodnocení umělou inteligencí může trvat až jednu minutu.
                                            </p>
                                        </div>
                                    )}
                                </div>
                            )}

                            {scanDone && !scanError && (
                                <div className="text-center py-4">
                                    <svg className="w-10 h-10 text-cyan-400 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                    </svg>
                                    <h3 className="font-semibold text-white mb-1">Sken dokončen</h3>
                                    <p className="text-sm text-slate-300 mb-1">
                                        Nalezeno {scanFindings.length} AI {scanFindings.length === 1 ? 'systém' : scanFindings.length < 5 ? 'systémy' : 'systémů'}
                                    </p>
                                    {scanResult?.company_id && (
                                        <p className="text-xs text-slate-500 mb-3">Výsledky byly uloženy do vašeho profilu</p>
                                    )}
                                    <div className="flex gap-2 sm:gap-3 justify-center flex-wrap">
                                        <button onClick={() => { closeScanPanel(); setActiveTab("findings"); }} className="btn-secondary text-sm px-4 py-2">
                                            Zobrazit nálezy
                                        </button>
                                        {hasScans && (
                                            <a href={`/dotaznik?company_id=${data?.company?.id || ''}`} className="btn-primary text-sm px-4 py-2">
                                                Vyplnit dotazník
                                            </a>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* ═══ STAT CARDS (4 equal panels) ═══ */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                        {/* Panel 1: Sken webu */}
                        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 hover:border-white/[0.12] transition-all flex flex-col">
                            <p className="text-xs text-slate-400 uppercase tracking-wider mb-2">Sken webu</p>
                            {!hasScans ? (
                                <>
                                    <p className="text-2xl font-extrabold mt-1 text-slate-500">—</p>
                                    <p className="text-xs text-slate-400 mt-1 leading-relaxed">Sken zatím nebyl proveden.</p>
                                </>
                            ) : uniqueSystemsCount > 0 ? (
                                <>
                                    <p className="text-2xl font-extrabold mt-1 text-amber-400">{uniqueSystemsCount}</p>
                                    <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                                        {cz(uniqueSystemsCount, 'AI systém nalezen', 'AI systémy nalezeny', 'AI systémů nalezeno')}, {cz(uniqueSystemsCount, 'který spadá', 'které spadají', 'které spadají')} do zákona EU o umělé inteligenci.
                                    </p>
                                </>
                            ) : (
                                <>
                                    <p className="text-2xl font-extrabold mt-1 text-green-400">0</p>
                                    <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                                        Sken na webu nezjistil žádné AI systémy, které podléhají zákonu Evropské unie o umělé inteligenci.
                                    </p>
                                </>
                            )}
                            {hasScans && uniqueSystemsCount === 0 && !hasQuest && (
                                <p className="text-[10px] text-amber-400/80 mt-2">100% jistotu budeme mít až po vyplnění dotazníku.</p>
                            )}
                            {/* Expandable scan findings */}
                            {hasScans && uniqueSystemsCount > 0 && (
                                <div className="mt-3 border-t border-white/[0.06] pt-3">
                                    <button onClick={() => setAiCardOpen(!aiCardOpen)} className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors">
                                        {aiCardOpen ? 'Skrýt nálezy' : 'Zobrazit nálezy'}
                                        <svg className={`w-3 h-3 transition-transform ${aiCardOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                        </svg>
                                    </button>
                                    {aiCardOpen && (
                                        <div className="mt-2 space-y-1.5">
                                            {groupFindings(data?.findings || []).map((f) => (
                                                <div key={f.name} className="rounded-md bg-white/[0.03] border border-white/[0.06] px-3 py-2">
                                                    <p className="text-xs font-medium text-white">{f.name}</p>
                                                    <p className="text-[10px] text-slate-400 mt-0.5">{f.category}{f.count > 1 ? ` · ${f.count}×` : ''}</p>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            )}
                            <div className="mt-auto pt-3">
                                <button onClick={handleStartScan} disabled={scanLoading} className="text-xs px-3 py-1.5 rounded-lg bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 hover:bg-cyan-500/20 transition-all disabled:opacity-50">
                                    {scanLoading ? 'Skenuji...' : 'Opakovat sken'}
                                </button>
                            </div>
                        </div>

                        {/* Panel 2: Výsledky dotazníku */}
                        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 hover:border-white/[0.12] transition-all flex flex-col">
                            <p className="text-xs text-slate-400 uppercase tracking-wider mb-2">Výsledky dotazníku</p>
                            {!hasQuest ? (
                                <>
                                    <p className="text-2xl font-extrabold mt-1 text-slate-500">—</p>
                                    <p className="text-xs text-slate-400 mt-1 leading-relaxed">Dotazník zatím nebyl vyplněn.</p>
                                </>
                            ) : qFindings.length > 0 ? (
                                <>
                                    <p className="text-2xl font-extrabold mt-1 text-amber-400">{qFindings.length}</p>
                                    <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                                        {cz(qFindings.length, 'AI systém odhalen', 'AI systémy odhaleny', 'AI systémů odhaleno')} dotazníkem.
                                    </p>
                                </>
                            ) : (
                                <>
                                    <p className="text-2xl font-extrabold mt-1 text-green-400">0</p>
                                    <p className="text-xs text-slate-300 mt-1 leading-relaxed">Dotazník neodhalil žádné AI systémy.</p>
                                </>
                            )}
                            {hasQuest && qUnknowns.length > 0 && (
                                <p className="text-[10px] text-amber-400 mt-2 leading-relaxed">
                                    U {qUnknowns.length} {cz(qUnknowns.length, 'otázky', 'otázek', 'otázek')} jste odpověděli &bdquo;Nevím&ldquo;. Tyto informace je nutné zjistit a doplnit — jinak Vám nedokážeme zaručit 100% ochranu.
                                </p>
                            )}
                            <div className="mt-auto pt-3">
                                {hasScans && (
                                    hasQuest ? (
                                        <a href={`/dotaznik?company_id=${data?.company?.id || ''}&edit=true`}
                                            className="text-xs px-3 py-1.5 rounded-lg bg-fuchsia-500/10 text-fuchsia-300 border border-fuchsia-500/20 hover:bg-fuchsia-500/20 transition-all inline-block">
                                            {qUnknowns.length > 0 ? 'Doplnit odpovědi' : 'Upravit odpovědi'}
                                        </a>
                                    ) : (
                                        <a href={`/dotaznik?company_id=${data?.company?.id || ''}`}
                                            className="text-xs px-3 py-1.5 rounded-lg bg-fuchsia-500/10 text-fuchsia-300 border border-fuchsia-500/20 hover:bg-fuchsia-500/20 transition-all inline-block">
                                            Vyplnit dotazník
                                        </a>
                                    )
                                )}
                            </div>
                        </div>

                        {/* Panel 3: Celkem systémů */}
                        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 hover:border-white/[0.12] transition-all flex flex-col">
                            <p className="text-xs text-slate-400 uppercase tracking-wider mb-2">Celkem AI systémů</p>
                            <p className={`text-2xl font-extrabold mt-1 ${totalSystems > 0 ? 'text-amber-400' : hasScans ? 'text-green-400' : 'text-slate-500'}`}>
                                {hasScans || hasQuest ? totalSystems : '—'}
                            </p>
                            <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                                {!hasScans && !hasQuest
                                    ? 'Proveďte sken a vyplňte dotazník.'
                                    : totalSystems > 0
                                        ? `${cz(totalSystems, 'Systém spadající', 'Systémy spadající', 'Systémů spadajících')} do zákona EU o umělé inteligenci.`
                                        : 'Žádné AI systémy podléhající regulaci nenalezeny.'
                                }
                            </p>
                            {(hasScans || hasQuest) && totalSystems > 0 && (
                                <p className="text-[10px] text-slate-400 mt-1">
                                    {uniqueSystemsCount > 0 ? `${uniqueSystemsCount} ze skenu` : ''}{uniqueSystemsCount > 0 && qFindings.length > 0 ? ' + ' : ''}{qFindings.length > 0 ? `${qFindings.length} z dotazníku` : ''}
                                </p>
                            )}
                            {hasQuest && qUnknowns.length > 0 && (
                                <p className="text-[10px] text-amber-400/80 mt-2">
                                    Celkový počet lze s jistotou říct až po zodpovězení všech otázek v dotazníku.
                                </p>
                            )}
                        </div>

                        {/* Panel 4: Status */}
                        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 hover:border-white/[0.12] transition-all flex flex-col">
                            <p className="text-xs text-slate-400 uppercase tracking-wider mb-2">Status</p>
                            {(() => {
                                const ws = data?.company?.workflow_status || 'new';
                                const hasPaid = (data?.orders || []).some(o => o.status === 'PAID');
                                const hasDocs = (data?.documents || []).length > 0;
                                const questIncomplete = hasQuest && qUnknowns.length > 0;

                                if (hasDocs && hasPaid && ws === 'documents_sent') {
                                    return (
                                        <>
                                            <p className="text-2xl font-extrabold mt-1 text-green-400">Dokončeno</p>
                                            <p className="text-xs text-slate-300 mt-1 leading-relaxed">Vše je připraveno. Vaše dokumenty jsou ke stažení v záložce Dokumenty.</p>
                                        </>
                                    );
                                }
                                if (hasPaid && !hasDocs) {
                                    return (
                                        <>
                                            <p className="text-2xl font-extrabold mt-1 text-cyan-400">Zpracováváme</p>
                                            <p className="text-xs text-slate-300 mt-1 leading-relaxed">Pracujeme na Vaší dokumentaci. Předáme Vám vše potřebné do 7 pracovních dní.</p>
                                        </>
                                    );
                                }
                                if (!hasQuest || questIncomplete) {
                                    return (
                                        <>
                                            <p className="text-2xl font-extrabold mt-1 text-amber-400">Čekáme</p>
                                            <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                                                {!hasQuest
                                                    ? 'Čekáme na vyplnění dotazníku.'
                                                    : `Dotazník obsahuje ${qUnknowns.length}× odpověď „Nevím". Doplňte prosím chybějící informace.`
                                                }
                                            </p>
                                        </>
                                    );
                                }
                                return (
                                    <>
                                        <p className="text-2xl font-extrabold mt-1 text-slate-400">Připraveno</p>
                                        <p className="text-xs text-slate-300 mt-1 leading-relaxed">Analýza dokončena. Vyberte si balíček pro vygenerování compliance dokumentace.</p>
                                    </>
                                );
                            })()}
                        </div>
                    </div>

                    {/* ═══ ACTION BANNER ═══ */}
                    {hasScans && hasQuest && qUnknowns.length > 0 && (
                        <div className="mb-8 rounded-2xl border border-amber-500/20 bg-gradient-to-br from-amber-500/[0.04] to-fuchsia-500/[0.04] p-4 sm:p-6">
                            <div className="flex items-center gap-3 mb-4">
                                <div className="h-10 w-10 rounded-xl bg-amber-500/20 flex items-center justify-center">
                                    <svg className="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                    </svg>
                                </div>
                                <div>
                                    <h3 className="font-semibold text-slate-200">Je potřeba doplnit odpovědi v dotazníku</h3>
                                    <p className="text-xs text-slate-300">U {qUnknowns.length} {cz(qUnknowns.length, 'otázky', 'otázek', 'otázek')} jste zvolili &bdquo;Nevím&ldquo; — podívejte se, jak tyto informace zjistit</p>
                                </div>
                            </div>
                            <button onClick={() => setActiveTab("plan")} className="btn-primary text-sm px-5 py-2">
                                Zobrazit podrobnosti
                            </button>
                        </div>
                    )}

                    {/* Tabs */}
                    <div className="flex gap-1 overflow-x-auto border-b border-white/[0.06] mb-6 scrollbar-hide">
                        {TABS.map((tab) => (
                            <button
                                key={tab.key}
                                onClick={() => setActiveTab(tab.key)}
                                className={`relative flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-4 py-2 sm:py-2.5 text-xs sm:text-sm font-medium transition-all whitespace-nowrap ${activeTab === tab.key
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
                        {activeTab === "prehled" && <TabPrehled data={data} onStartScan={handleStartScan} scanLoading={scanLoading} hasScans={hasScans} />}
                        {activeTab === "findings" && <TabFindings findings={data?.findings || []} questionnaireFindings={qFindings} questionnaireUnknowns={qUnknowns} hasQuest={hasQuest} companyId={data?.company?.id || ''} onStartScan={handleStartScan} />}
                        {activeTab === "dokumenty" && <TabDokumenty documents={data?.documents || []} />}
                        {activeTab === "plan" && <TabPlan questionnaireUnknowns={qUnknowns} companyId={data?.company?.id || ''} />}
                        {activeTab === "skeny" && <TabSkeny scans={data?.scans || []} onStartScan={handleStartScan} />}
                        {activeTab === "ucet" && <TabUcet user={user} data={data} />}
                    </div>
                </div>
            </section>

            {/* ── Kontakt + Helplinka ── */}
            <section className="mx-auto max-w-7xl px-6 pb-20">
                {/* HELPLINKA */}
                <div className="mb-8 flex flex-col sm:flex-row items-center justify-center gap-4 rounded-2xl border border-white/[0.08] bg-gradient-to-r from-fuchsia-500/10 via-purple-500/10 to-cyan-500/10 p-6">
                    <div className="flex items-center gap-3">
                        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-fuchsia-500/20 border border-fuchsia-500/30">
                            <svg className="w-6 h-6 text-fuchsia-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 0 0 2.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 0 1-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 0 0-1.091-.852H4.5A2.25 2.25 0 0 0 2.25 4.5v2.25Z" />
                            </svg>
                        </div>
                        <div>
                            <p className="text-sm text-slate-300">Potřebujete poradit? Zavolejte nám</p>
                            <p className="text-lg font-bold text-white">HELPLINKA</p>
                        </div>
                    </div>
                    <a
                        href="tel:+420732716141"
                        className="inline-flex items-center gap-2 rounded-xl bg-fuchsia-600 px-6 py-3 text-base font-bold text-white shadow-lg shadow-fuchsia-500/25 hover:bg-fuchsia-500 transition"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 0 0 2.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 0 1-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 0 0-1.091-.852H4.5A2.25 2.25 0 0 0 2.25 4.5v2.25Z" />
                        </svg>
                        +420 732 716 141
                    </a>
                </div>

                {/* Kontaktní formulář */}
                <ContactForm />
            </section>
        </>
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
                    {icon && <span className="text-slate-500">{icon}</span>}
                </div>
            </div>
            <p className={`text-2xl sm:text-3xl font-extrabold mt-1 ${color}`}>{value}</p>
            <p className="text-xs text-slate-400 mt-1">{sub}</p>
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
            href: null as string | null,
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
            desc: "Odemkněte compliance dokumenty a školení",
            href: "#pricing",
            cta: "Vybrat balíček",
            onClick: undefined as (() => void) | undefined,
        },
        {
            done: hasDocs,
            label: "Dodání dokumentace",
            desc: "7 dokumentů pro splnění AI Act (může trvat až 14 dní)",
            href: "#",
            cta: "Viz tab Dokumenty",
            onClick: undefined as (() => void) | undefined,
        },
    ];

    const currentStepIndex = steps.findIndex((s) => !s.done);
    const currentStep = currentStepIndex >= 0 ? steps[currentStepIndex] : null;
    const completedCount = steps.filter((s) => s.done).length;
    const lineWidthPercent = completedCount <= 1 ? 0 : ((completedCount - 1) / (steps.length - 1)) * 75;

    const isProcessing = hasPaidOrder && !hasDocs;
    const currentHour = new Date().getHours();
    const isBusinessHours = currentHour >= 8 && currentHour < 16;

    return (
        <div className="space-y-6">
            {/* Progress Timeline */}
            <div className="glass">
                <h3 className="font-semibold mb-8">Postup k compliance</h3>
                <div className="grid grid-cols-4 relative mb-8">
                    <div className="absolute top-5 left-[12.5%] right-[12.5%] h-0.5 bg-white/[0.06]" />
                    {lineWidthPercent > 0 && (
                        <div className="absolute top-5 left-[12.5%] h-0.5 bg-gradient-to-r from-green-500 to-emerald-400 transition-all duration-700 rounded-full" style={{ width: `${lineWidthPercent}%` }} />
                    )}
                    {steps.map((step, i) => {
                        const isCurrent = i === currentStepIndex;
                        return (
                            <div key={i} className="flex flex-col items-center relative z-10">
                                <div className={`flex items-center justify-center h-8 w-8 sm:h-10 sm:w-10 rounded-full text-xs sm:text-sm font-bold transition-all duration-300 ${step.done
                                    ? "bg-green-500/20 text-green-400 border-2 border-green-500/40 shadow-[0_0_12px_rgba(34,197,94,0.15)]"
                                    : isCurrent
                                        ? "bg-fuchsia-500/20 text-fuchsia-400 border-2 border-fuchsia-500/40 shadow-[0_0_12px_rgba(217,70,239,0.15)] animate-pulse"
                                        : "bg-slate-900 text-slate-600 border-2 border-white/[0.08]"
                                    }`}>
                                    {step.done ? (
                                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                                        </svg>
                                    ) : (i + 1)}
                                </div>
                                <span className={`text-[10px] sm:text-xs mt-1.5 sm:mt-2.5 font-medium text-center leading-tight ${step.done ? "text-green-400/80" : isCurrent ? "text-fuchsia-400" : "text-slate-600"}`}>
                                    {step.label}
                                </span>
                            </div>
                        );
                    })}
                </div>

                {currentStep && (
                    <div className="rounded-xl border border-fuchsia-500/20 bg-fuchsia-500/[0.04] p-5">
                        <div className="flex items-center gap-3 mb-2">
                            <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-fuchsia-500/20 text-fuchsia-400 text-xs font-bold">
                                {currentStepIndex + 1}
                            </span>
                            <h4 className="font-semibold text-fuchsia-300">{currentStep.label}</h4>
                        </div>
                        <p className="text-sm text-slate-300 mb-4 ml-0 sm:ml-9">{currentStep.desc}</p>
                        {currentStep.onClick ? (
                            <button onClick={currentStep.onClick} disabled={scanLoading} className="btn-primary text-sm px-5 py-2 ml-0 sm:ml-9 inline-block disabled:opacity-50">
                                {currentStep.cta}
                            </button>
                        ) : currentStep.href && currentStep.href !== "#" ? (
                            <a href={currentStep.href} className="btn-primary text-sm px-5 py-2 ml-0 sm:ml-9 inline-block">{currentStep.cta}</a>
                        ) : !currentStep.href ? (
                            <span className="text-sm text-slate-500 ml-0 sm:ml-9 inline-block opacity-60">{currentStep.cta}</span>
                        ) : null}
                    </div>
                )}

                {!currentStep && (
                    <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/[0.04] p-5 text-center">
                        <svg className="w-8 h-8 text-cyan-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <h4 className="font-semibold text-cyan-400">Všechny kroky dokončeny</h4>
                        <p className="text-sm text-slate-300 mt-1">Vaše compliance dokumenty jsou připraveny ke stažení.</p>
                    </div>
                )}
            </div>

            {/* Processing timer */}
            {isProcessing && (
                <div className="glass border-fuchsia-500/20">
                    <div className="flex flex-col sm:flex-row items-center gap-3 sm:gap-5 text-center sm:text-left">
                        <div className="relative flex-shrink-0 h-12 w-12 sm:h-16 sm:w-16">
                            <svg className="w-12 h-12 sm:w-16 sm:h-16 animate-spin" style={{ animationDuration: "3s" }} viewBox="0 0 64 64" fill="none">
                                <circle cx="32" cy="32" r="28" stroke="currentColor" strokeWidth="3" className="text-white/[0.06]" />
                                <circle cx="32" cy="32" r="28" stroke="url(#proc-grad)" strokeWidth="3" strokeLinecap="round" strokeDasharray="80 96" />
                                <defs><linearGradient id="proc-grad" x1="0" y1="0" x2="64" y2="64"><stop offset="0%" stopColor="#d946ef" /><stop offset="100%" stopColor="#06b6d4" /></linearGradient></defs>
                            </svg>
                            <div className="absolute inset-0 flex items-center justify-center">
                                <svg className="w-6 h-6 text-fuchsia-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                        </div>
                        <div>
                            <h3 className="font-semibold text-slate-200">Zpracováváme vaši objednávku</h3>
                            <p className="text-sm text-slate-300 mt-1">
                                {isBusinessHours ? "Obvykle do 4 hodin (doručujeme 8:00\u201316:00)" : "Výsledky budou doručeny zítra ráno v 8:00"}
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Objednávky */}
            {data?.orders && data.orders.length > 0 && (
                <div className="glass">
                    <h3 className="font-semibold mb-4">Objednávky</h3>
                    <div className="space-y-2">
                        {data.orders.map((order) => (
                            <div key={order.order_number} className="flex flex-col sm:flex-row sm:items-center sm:justify-between rounded-lg border border-white/[0.06] bg-white/[0.02] px-4 py-3 text-sm hover:border-white/[0.12] transition-all gap-2">
                                <div>
                                    <span className="text-slate-300 font-medium">{order.order_number}</span>
                                    <span className="text-slate-500 ml-2">({order.plan.toUpperCase()})</span>
                                </div>
                                <div className="flex items-center gap-2 sm:gap-4 flex-wrap">
                                    <span className="text-slate-400">{new Intl.NumberFormat("cs-CZ").format(order.amount)} Kč</span>
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

            {/* ═══ PRICING TABLE ═══ */}
            <div id="pricing">
                <PricingComparisonTable />
            </div>
        </div>
    );
}


/* ── Tab: AI systémy (Findings) with expandable detail ── */
function TabFindings({ findings, questionnaireFindings, questionnaireUnknowns, hasQuest, companyId, onStartScan }: {
    findings: DashboardData["findings"];
    questionnaireFindings: QuestionnaireFinding[];
    questionnaireUnknowns: QuestionnaireUnknown[];
    hasQuest: boolean;
    companyId: string;
    onStartScan: () => void;
}) {
    const [expanded, setExpanded] = useState<Record<string, boolean>>({});

    if (findings.length === 0 && questionnaireFindings.length === 0) {
        return (
            <EmptyState
                title="Sken ještě nebyl spuštěn"
                description="Každý web používající AI systémy má povinnosti dle AI Actu — spusťte sken a zjistěte, které."
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

    const grouped = groupFindings(findings);
    const totalCount = grouped.length + questionnaireFindings.length;

    return (
        <div className="space-y-3">
            <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/[0.04] p-4 mb-4">
                <div className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div>
                        <h4 className="text-sm font-semibold text-cyan-300 mb-1">{totalCount === 1 ? 'Systém umělé inteligence nalezen' : 'Systémy umělé inteligence nalezeny'}</h4>
                        <p className="text-xs text-slate-300 leading-relaxed">
                            Nalezeno <strong className="text-slate-300">{totalCount} {cz(totalCount, 'AI systém', 'AI systémy', 'AI systémů')}</strong>
                            {grouped.length > 0 && questionnaireFindings.length > 0
                                ? ` (${grouped.length} ze skenu webu, ${questionnaireFindings.length} z dotazníku)`
                                : grouped.length > 0
                                    ? ' ze skenu vašeho webu'
                                    : ' z odpovědí v dotazníku'
                            }.
                            Využívání těchto nástrojů Vám dává <strong className="text-cyan-300">konkurenční výhodu</strong> před weby, které AI nepoužívají.
                            Stačí o tom správně informovat návštěvníky a mít k tomu příslušnou dokumentaci.
                            <strong className="text-cyan-300"> Vše dokážeme zařídit za Vás</strong>, abyste se mohli soustředit na svůj byznys.
                        </p>
                    </div>
                </div>
            </div>

            {/* ── Scan findings ── */}
            {grouped.length > 0 && (
                <>
                    {questionnaireFindings.length > 0 && (
                        <h3 className="text-xs text-slate-500 uppercase tracking-wider font-medium pt-2">Ze skenu webu</h3>
                    )}
                    {grouped.map((f) => {
                        const isExpanded = expanded[f.name] || false;
                        const explanation = AI_SYSTEM_EXPLANATIONS[f.name] || `AI systém nalezený na vašem webu \u2013 doporučujeme tento nález zahrnout do analýzy a compliance dokumentace, abyste měli jistotu souladu s EU AI Act.`;

                        return (
                            <div key={f.name} className="rounded-xl border border-white/[0.06] bg-white/[0.02] hover:border-white/[0.12] transition-all overflow-hidden">
                                <button
                                    onClick={() => setExpanded(prev => ({ ...prev, [f.name]: !prev[f.name] }))}
                                    className="w-full p-4 sm:p-5 text-left flex items-start justify-between gap-3 sm:gap-4"
                                >
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 sm:gap-3 mb-1 flex-wrap">
                                            <h4 className="font-semibold text-slate-200">{f.name}</h4>
                                            <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${RISK_COLORS[f.risk_level] || RISK_COLORS.low}`}>
                                                {OBLIGATION_LABEL[f.risk_level] || OBLIGATION_LABEL.low}
                                            </span>
                                            {f.count > 1 && (
                                                <span className="text-xs text-slate-500">{f.count}x nalezeno</span>
                                            )}
                                        </div>
                                        <p className="text-sm text-slate-300">{f.action_required}</p>
                                    </div>
                                    <svg className={`w-5 h-5 text-slate-500 flex-shrink-0 transition-transform ${isExpanded ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                    </svg>
                                </button>

                                {isExpanded && (
                                    <div className="px-5 pb-5 pt-0 border-t border-white/[0.04]">
                                        <div className="rounded-lg bg-cyan-500/[0.04] border border-cyan-500/10 p-4 mt-3">
                                            <h5 className="text-xs font-semibold text-cyan-400 uppercase tracking-wider mb-2">Využíváte moderní technologii</h5>
                                            <p className="text-sm text-slate-300 leading-relaxed">{explanation}</p>
                                            <p className="text-sm text-slate-300 leading-relaxed mt-2">
                                                Tento nástroj Vám přináší <strong className="text-cyan-300">konkurenční výhodu</strong>.
                                                Stačí o jeho využití informovat návštěvníky webu a mít k tomu příslušnou dokumentaci.
                                                {(f.risk_level === 'high') && ' U vysoce rizikových systémů je navíc nutné proškolit zaměstnance, kteří s ním pracují.'}
                                            </p>
                                            <p className="text-xs text-fuchsia-400 mt-3 font-medium">Vše dokážeme zařídit za Vás — nemusíte řešit nic sami.</p>
                                        </div>
                                        {(f.category || f.ai_act_article) && (
                                            <div className="flex flex-wrap items-center gap-2 sm:gap-4 text-xs text-slate-500 mt-3">
                                                {f.category && <span>Kategorie: {f.category}</span>}
                                                {f.ai_act_article && f.ai_act_article !== "—" && <span>Článek AI Act: {f.ai_act_article}</span>}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </>
            )}

            {/* ── Questionnaire findings ── */}
            {questionnaireFindings.length > 0 && (
                <>
                    <h3 className="text-xs text-slate-500 uppercase tracking-wider font-medium pt-4">Z dotazníku — interní AI systémy</h3>
                    {questionnaireFindings.map((f) => {
                        const isExpanded = expanded[`q_${f.question_key}`] || false;
                        return (
                            <div key={f.question_key} className="rounded-xl border border-fuchsia-500/[0.12] bg-fuchsia-500/[0.02] hover:border-fuchsia-500/[0.2] transition-all overflow-hidden">
                                <button
                                    onClick={() => setExpanded(prev => ({ ...prev, [`q_${f.question_key}`]: !prev[`q_${f.question_key}`] }))}
                                    className="w-full p-4 sm:p-5 text-left flex items-start justify-between gap-3 sm:gap-4"
                                >
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 sm:gap-3 mb-1 flex-wrap">
                                            <h4 className="font-semibold text-slate-200">{f.name}</h4>
                                            <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${RISK_COLORS[f.risk_level] || RISK_COLORS.low}`}>
                                                {OBLIGATION_LABEL[f.risk_level] || OBLIGATION_LABEL.low}
                                            </span>
                                            <span className="text-[10px] text-fuchsia-400/60 font-medium">dotazník</span>
                                        </div>
                                        <p className="text-sm text-slate-300 line-clamp-2">{f.action_required}</p>
                                    </div>
                                    <svg className={`w-5 h-5 text-slate-500 flex-shrink-0 transition-transform ${isExpanded ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                    </svg>
                                </button>

                                {isExpanded && (
                                    <div className="px-5 pb-5 pt-0 border-t border-fuchsia-500/[0.08]">
                                        <div className="rounded-lg bg-slate-800/50 p-4 mt-3">
                                            <h5 className="text-xs font-semibold text-fuchsia-400 uppercase tracking-wider mb-2">Doporučení</h5>
                                            <p className="text-sm text-slate-300 leading-relaxed">{f.action_required}</p>
                                        </div>
                                        {f.ai_act_article && (
                                            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 mt-3">
                                                <span>Článek AI Act: {f.ai_act_article}</span>
                                                <span>Priorita: {f.priority}</span>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </>
            )}

            {/* ── Unknowns — color-coded by severity with checklists ── */}
            {questionnaireUnknowns.length > 0 && (
                <div className="mt-4 space-y-3">
                    <div className="flex items-start gap-3 mb-2">
                        <svg className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        <div>
                            <h4 className="text-sm font-semibold text-slate-300 mb-1">Oblasti k ověření ({questionnaireUnknowns.length})</h4>
                            <p className="text-xs text-slate-300 leading-relaxed">
                                U těchto otázek jste odpověděli &bdquo;Nevím&ldquo;. Pomůžeme vám to zjistit — u každé oblasti najdete konkrétní kroky.
                            </p>
                        </div>
                    </div>

                    {questionnaireUnknowns.map((u) => {
                        const isExp = expanded[`unk_${u.question_key}`] || false;
                        const borderColor = u.severity_color === "red" ? "border-red-500/30 hover:border-red-500/50"
                            : u.severity_color === "orange" ? "border-orange-500/25 hover:border-orange-500/40"
                                : u.severity_color === "yellow" ? "border-amber-500/20 hover:border-amber-500/35"
                                    : "border-slate-500/15 hover:border-slate-500/25";
                        const bgColor = u.severity_color === "red" ? "bg-red-500/[0.03]"
                            : u.severity_color === "orange" ? "bg-orange-500/[0.03]"
                                : u.severity_color === "yellow" ? "bg-amber-500/[0.02]"
                                    : "bg-white/[0.01]";
                        const dotColor = u.severity_color === "red" ? "bg-red-500" : u.severity_color === "orange" ? "bg-orange-500" : u.severity_color === "yellow" ? "bg-amber-400" : "bg-slate-500";
                        const labelColor = u.severity_color === "red" ? "text-red-400 bg-red-500/10"
                            : u.severity_color === "orange" ? "text-orange-400 bg-orange-500/10"
                                : u.severity_color === "yellow" ? "text-amber-400 bg-amber-500/10"
                                    : "text-slate-400 bg-slate-500/10";

                        return (
                            <div key={u.question_key} className={`rounded-xl border ${borderColor} ${bgColor} transition-all overflow-hidden`}>
                                <button
                                    onClick={() => setExpanded(prev => ({ ...prev, [`unk_${u.question_key}`]: !prev[`unk_${u.question_key}`] }))}
                                    className="w-full p-4 sm:p-5 text-left flex items-start justify-between gap-3"
                                >
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 sm:gap-3 mb-1 flex-wrap">
                                            <span className={`w-2 h-2 rounded-full flex-shrink-0 ${dotColor}`} />
                                            <h4 className="font-semibold text-slate-200 text-sm">{u.question_text}</h4>
                                        </div>
                                        <div className="flex items-center gap-2 mt-1.5">
                                            <span className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium ${labelColor}`}>
                                                {u.severity_label}
                                            </span>
                                            {u.ai_act_article && <span className="text-[10px] text-slate-400">{u.ai_act_article}</span>}
                                        </div>
                                    </div>
                                    <svg className={`w-5 h-5 text-slate-500 flex-shrink-0 transition-transform ${isExp ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                    </svg>
                                </button>

                                {isExp && (
                                    <div className="px-5 pb-5 pt-0 border-t border-white/[0.04]">
                                        {u.checklist && u.checklist.length > 0 && (
                                            <div className="rounded-lg bg-slate-800/50 p-4 mt-3">
                                                <h5 className="text-xs font-semibold text-cyan-400 uppercase tracking-wider mb-3">Jak to zjistit:</h5>
                                                <ul className="space-y-2">
                                                    {u.checklist.map((item, idx) => (
                                                        <li key={idx} className="flex items-start gap-2 text-sm text-slate-200">
                                                            <span className="text-cyan-400 font-mono text-xs mt-0.5 flex-shrink-0">{idx + 1}.</span>
                                                            <span>{item}</span>
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                        <p className="text-xs text-slate-300 mt-3 leading-relaxed">{u.recommendation}</p>
                                        <a
                                            href={`/dotaznik?company_id=${companyId}&edit=true&q=${u.question_key}`}
                                            className="btn-primary !text-xs !px-4 !py-2 !rounded-lg mt-3 inline-block"
                                        >
                                            Už vím! Chci změnit odpověď v dotazníku
                                        </a>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                    <a href={`/dotaznik?company_id=${companyId}&edit=true`}
                        className="inline-flex items-center gap-1.5 text-xs text-amber-400 hover:text-amber-300 mt-1 transition-colors">
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                        Upravit odpovědi v dotazníku
                    </a>
                </div>
            )}

            {/* CTA: fill questionnaire if not done */}
            {!hasQuest && findings.length > 0 && (
                <div className="mt-4 rounded-xl border border-fuchsia-500/15 bg-fuchsia-500/[0.03] p-4 text-center">
                    <p className="text-sm text-slate-300 mb-3">
                        Sken odhalil AI systémy na webu. <strong className="text-slate-300">Vyplňte dotazník</strong> pro odhalení interních AI nástrojů (ChatGPT, AI nábor, rozhodování…).
                    </p>
                    <a href={`/dotaznik?company_id=${companyId}`} className="btn-primary text-sm px-5 py-2 inline-block">
                        Vyplnit dotazník
                    </a>
                </div>
            )}
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
                href="#pricing"
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
        <div className="space-y-4">
            {/* 7-day processing notice */}
            <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/[0.04] p-4">
                <div className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div>
                        <h4 className="text-sm font-semibold text-cyan-300 mb-1">Doba zpracování</h4>
                        <p className="text-xs text-slate-300 leading-relaxed">
                            Kompletní dokumenty připravujeme do <strong className="text-cyan-300">7 pracovních dnů</strong> od zaplacení balíčku.
                            Pro přípravu dokumentů je nutné mít vyplněný dotazník — čím přesněji odpovíte, tím kvalitnější dokumenty obdržíte.
                        </p>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {documents.map((doc) => (
                    <div key={doc.id} className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4 hover:border-white/[0.12] transition-all">
                        <div className="flex-shrink-0 h-10 w-10 sm:h-12 sm:w-12 rounded-xl bg-fuchsia-500/10 flex items-center justify-center">
                            <svg className="w-6 h-6 text-fuchsia-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                            </svg>
                        </div>
                        <div className="flex-1 min-w-0">
                            <h4 className="font-medium text-slate-200 text-sm">{TEMPLATE_NAMES[doc.template_key] || doc.name || doc.template_key}</h4>
                            <p className="text-xs text-slate-400 mt-0.5">{new Date(doc.created_at).toLocaleDateString("cs-CZ")}</p>
                        </div>
                        {doc.file_url && (
                            <a href={doc.file_url} target="_blank" rel="noopener noreferrer" className="btn-secondary text-xs px-3 py-1.5 flex-shrink-0">
                                Stáhnout PDF
                            </a>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}


/* ── Tab: Musíte doplnit ── */
function TabPlan({ questionnaireUnknowns, companyId }: {
    questionnaireUnknowns: QuestionnaireUnknown[];
    companyId: string;
}) {
    const [expanded, setExpanded] = useState<Record<string, boolean>>({});

    if (questionnaireUnknowns.length === 0) {
        return (
            <EmptyState
                title="Žádné nezodpovězené otázky"
                description={"Výborně! Na všechny otázky v dotazníku jste odpověděli. Nemáte žádné položky \u201ENevím\u201C k doplnění."}
                illustration={
                    <svg className="w-10 h-10 text-green-500/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                }
            />
        );
    }

    return (
        <div className="space-y-4">
            <div className="rounded-xl border border-amber-500/20 bg-amber-500/[0.04] p-4">
                <div className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div>
                        <h4 className="text-sm font-semibold text-amber-300 mb-1">Potřebujeme vaši součinnost</h4>
                        <p className="text-xs text-slate-300 leading-relaxed">
                            U {questionnaireUnknowns.length} {cz(questionnaireUnknowns.length, 'otázky', 'otázek', 'otázek')} jste v dotazníku zvolili &bdquo;Nevím&ldquo;.
                            Abychom pro vás mohli připravit kompletní dokumentaci, potřebujeme znát přesné odpovědi.
                            <strong className="text-amber-300"> Rozklikněte jednotlivé položky — dozvíte se, koho se ve firmě zeptat a co přesně zjistit.</strong>
                        </p>
                    </div>
                </div>
            </div>

            <div className="space-y-2">
                {questionnaireUnknowns.map((u) => {
                    const dotColor = u.severity_color === "red" ? "bg-red-500" : u.severity_color === "orange" ? "bg-orange-500" : u.severity_color === "yellow" ? "bg-amber-400" : "bg-slate-500";
                    const labelColor = u.severity_color === "red" ? "text-red-400"
                        : u.severity_color === "orange" ? "text-orange-400"
                            : u.severity_color === "yellow" ? "text-amber-400"
                                : "text-slate-400";
                    const isExp = expanded[`plan_unk_${u.question_key}`] || false;
                    return (
                        <div key={u.question_key} className="rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden">
                            <button
                                onClick={() => setExpanded(prev => ({ ...prev, [`plan_unk_${u.question_key}`]: !prev[`plan_unk_${u.question_key}`] }))}
                                className="w-full flex items-start gap-3 px-4 py-3 text-left hover:bg-white/[0.03] transition-colors"
                            >
                                <span className={`w-2.5 h-2.5 rounded-full mt-1.5 flex-shrink-0 ${dotColor}`} />
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm text-slate-200">{u.question_text}</p>
                                    <p className={`text-xs mt-0.5 ${labelColor}`}>{u.severity_label}</p>
                                </div>
                                <svg className={`w-4 h-4 text-slate-400 flex-shrink-0 mt-1 transition-transform ${isExp ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                </svg>
                            </button>
                            {isExp && (
                                <div className="px-4 pb-4 pt-2 border-t border-white/[0.04]">
                                    {u.checklist && u.checklist.length > 0 && (
                                        <div className="rounded-lg bg-slate-800/50 p-3 mb-3">
                                            <h5 className="text-xs font-semibold text-cyan-400 uppercase tracking-wider mb-2">Jak to zjistit:</h5>
                                            <ul className="space-y-1.5">
                                                {u.checklist.map((item, idx) => (
                                                    <li key={idx} className="flex items-start gap-2 text-sm text-slate-200">
                                                        <span className="text-cyan-400 font-mono text-xs mt-0.5 flex-shrink-0">{idx + 1}.</span>
                                                        <span>{item}</span>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                    <p className="text-xs text-slate-300 mb-3 leading-relaxed">{u.recommendation}</p>
                                    <a
                                        href={`/dotaznik?company_id=${companyId}&edit=true&q=${u.question_key}`}
                                        className="btn-primary !text-xs !px-4 !py-2 !rounded-lg"
                                    >
                                        Už vím! Chci změnit odpověď v dotazníku
                                    </a>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
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
                <div key={scan.id} className="flex items-center gap-3 sm:gap-4 rounded-xl border border-white/[0.06] bg-white/[0.02] px-3 sm:px-5 py-3 sm:py-4 hover:border-white/[0.12] transition-all">
                    <div className="flex flex-col items-center gap-1">
                        <div className={`h-3 w-3 rounded-full ${scan.status === "completed"
                            ? (scan.total_findings === 0 ? "bg-green-500" : "bg-cyan-500")
                            : scan.status === "running"
                                ? "bg-amber-500 animate-pulse"
                                : "bg-red-500"
                            }`} />
                        {i < scans.length - 1 && <div className="w-px h-8 bg-white/[0.06]" />}
                    </div>
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
                            <p className="text-sm font-medium text-slate-200 truncate">{scan.url}</p>
                            <span className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium ${scan.status === "completed"
                                ? "bg-cyan-500/10 text-cyan-400"
                                : scan.status === "running"
                                    ? "bg-amber-500/10 text-amber-400"
                                    : "bg-red-500/10 text-red-400"
                                }`}>
                                {scan.status === "completed" ? "Dokončen" : scan.status === "running" ? "Probíhá" : scan.status}
                            </span>
                        </div>
                        <div className="flex items-center gap-2 sm:gap-4 text-xs text-slate-500 mt-1 flex-wrap">
                            <span>{new Date(scan.created_at).toLocaleDateString("cs-CZ", {
                                day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit"
                            })}</span>
                            <span>{scan.total_findings} {cz(scan.total_findings, 'nález', 'nálezy', 'nálezů')}</span>
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
        ? new Date(user.created_at).toLocaleDateString("cs-CZ", { day: "numeric", month: "long", year: "numeric" })
        : "—";

    const handlePasswordChange = async (e: React.FormEvent) => {
        e.preventDefault();
        if (newPassword !== confirmPassword) { setPasswordMsg("Hesla se neshodují"); return; }
        if (newPassword.length < 6) { setPasswordMsg("Heslo musí mít alespoň 6 znaků"); return; }
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
                                    <span className="text-slate-400 text-xs">{new Date(order.created_at).toLocaleDateString("cs-CZ")}</span>
                                    <span className="text-slate-300 font-medium">{new Intl.NumberFormat("cs-CZ").format(order.amount)} Kč</span>
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

            <div className="glass">
                <h3 className="font-semibold mb-5 flex items-center gap-2">
                    <svg className="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                    </svg>
                    Změna hesla
                </h3>
                <form onSubmit={handlePasswordChange} className="space-y-4 max-w-sm">
                    <div>
                        <label className="block text-sm text-slate-300 mb-1">Nové heslo</label>
                        <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} placeholder="Minimálně 6 znaků" minLength={6} required
                            className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-white placeholder:text-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/30 transition-all" />
                    </div>
                    <div>
                        <label className="block text-sm text-slate-300 mb-1">Potvrdit nové heslo</label>
                        <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} placeholder="Zadejte heslo znovu" minLength={6} required
                            className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-white placeholder:text-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-fuchsia-500/50 focus:border-fuchsia-500/30 transition-all" />
                    </div>
                    {passwordMsg && (
                        <p className={`text-sm ${passwordMsg.startsWith("✅") ? "text-green-400" : "text-red-400"}`}>{passwordMsg}</p>
                    )}
                    <button type="submit" disabled={passwordLoading} className="btn-secondary text-sm px-5 py-2 disabled:opacity-50">
                        {passwordLoading ? "Ukládám..." : "Změnit heslo"}
                    </button>
                </form>
            </div>
        </div>
    );
}


/* ── Dashboard Pricing Cards + Comparison Table ── */
const DASHBOARD_PLANS = [
    {
        key: "basic",
        name: "BASIC",
        price: "4 999",
        priceNote: "jednorázově",
        description: "Compliance Kit — dokumenty ke stažení",
        features: [
            "Sken webu + AI Act report",
            "AI Act Compliance Kit (7 dokumentů)",
            "Transparenční stránka (HTML)",
            "Registr AI systémů",
            "Interní AI politika firmy",
            "Školení — prezentace v PowerPointu",
            "Záznamový list o proškolení",
        ],
        notIncluded: [
            "Implementace na klíč",
            "Podpora po dodání",
        ],
        cta: "Objednat BASIC",
        highlighted: false,
        icon: (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15a2.25 2.25 0 012.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25z" />
            </svg>
        ),
    },
    {
        key: "pro",
        name: "PRO",
        price: "14 999",
        priceNote: "jednorázově",
        description: "Vše z BASIC + implementace na klíč",
        badge: "Nejoblíbenější",
        features: [
            "Vše z BASIC",
            "Instalace widgetu na váš web",
            "Nastavení transparenční stránky",
            "Úprava chatbot oznámení",
            "Podpora po dobu 30 dní",
            "WordPress, Shoptet i custom",
            "Prioritní zpracování",
        ],
        notIncluded: [],
        cta: "Objednat PRO",
        highlighted: true,
        icon: (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
            </svg>
        ),
    },
    {
        key: "enterprise",
        name: "ENTERPRISE",
        price: "39 999",
        priceNote: "jednorázově",
        description: "Komplexní řešení pro větší firmy + 2 roky průběžné péče",
        features: [
            "Vše z PRO",
            "10 hodin konzultací s compliance specialistou",
            "Metodická kontrola veškeré dokumentace",
            "Rozšířený audit interních AI systémů",
            "Multi-domain (více webů / e-shopů)",
            "2 roky měsíčního monitoringu — automatický sken, propsání změn, hlášení a aktualizace dokumentů",
            "Dedikovaný specialista",
            "SLA 4h odezva v pracovní době",
        ],
        notIncluded: [],
        cta: "Objednat ENTERPRISE",
        highlighted: false,
        icon: (
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008z" />
            </svg>
        ),
    },
];

const COMPARISON_FEATURES = [
    { label: "Sken webu + AI Act report", basic: true, pro: true, enterprise: true },
    { label: "Compliance Kit (7 dokumentů)", basic: true, pro: true, enterprise: true },
    { label: "Registr AI systémů", basic: true, pro: true, enterprise: true },
    { label: "Transparenční stránka (HTML)", basic: true, pro: true, enterprise: true },
    { label: "Texty oznámení pro AI nástroje", basic: true, pro: true, enterprise: true },
    { label: "Interní AI politika firmy", basic: true, pro: true, enterprise: true },
    { label: "Školení — prezentace v PowerPointu", basic: true, pro: true, enterprise: true },
    { label: "Záznamový list o proškolení", basic: true, pro: true, enterprise: true },
    { label: "Implementace na váš web na klíč", basic: false, pro: true, enterprise: true },
    { label: "Nastavení transparenční stránky na webu", basic: false, pro: true, enterprise: true },
    { label: "Úprava cookie lišty a chatbot oznámení", basic: false, pro: true, enterprise: true },
    { label: "Podpora po dodání (30 dní)", basic: false, pro: true, enterprise: true },
    { label: "Prioritní zpracování", basic: false, pro: true, enterprise: true },
    { label: "10 hodin konzultací se specialistou", basic: false, pro: false, enterprise: true },
    { label: "Metodická kontrola veškeré dokumentace", basic: false, pro: false, enterprise: true },
    { label: "Rozšířený audit interních AI systémů", basic: false, pro: false, enterprise: true },
    { label: "Multi-domain (více webů / e-shopů)", basic: false, pro: false, enterprise: true },
    { label: "2 roky měsíčního monitoringu — automatický sken, propsání změn, hlášení a aktualizace", basic: false, pro: false, enterprise: true },
    { label: "Dedikovaný specialista", basic: false, pro: false, enterprise: true },
    { label: "SLA 4h odezva v pracovní době", basic: false, pro: false, enterprise: true },
];

function PricingComparisonTable() {
    const { user } = useAuth();
    const [loading, setLoading] = useState<string | null>(null);

    async function handleCheckout(planKey: string) {
        if (!user) {
            window.location.href = `/registrace?redirect=/dashboard&plan=${planKey}`;
            return;
        }
        setLoading(planKey);
        try {
            const data = await createCheckout(planKey, user.email || "");
            window.location.href = data.gateway_url;
        } catch (err: unknown) {
            alert(err instanceof Error ? err.message : "Nepodařilo se vytvořit platbu");
            setLoading(null);
        }
    }

    const Check = () => (
        <svg className="w-5 h-5 text-green-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
        </svg>
    );
    const Cross = () => (
        <svg className="w-4 h-4 text-red-400/40 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
    );

    return (
        <div className="space-y-6">
            {/* ── Pricing Cards (same design as /pricing page) ── */}
            <div>
                <h3 className="font-semibold text-slate-200 mb-1">Cenové balíčky</h3>
                <p className="text-xs text-slate-300 mb-5">Vyberte si balíček — rozsah služeb závisí na zvoleném plánu.</p>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {DASHBOARD_PLANS.map((plan) => (
                        <div
                            key={plan.key}
                            className={`relative rounded-2xl border p-5 flex flex-col transition-all duration-300 hover:-translate-y-1 ${plan.highlighted
                                ? "border-fuchsia-500/30 bg-gradient-to-b from-fuchsia-500/[0.08] to-transparent shadow-[0_0_40px_rgba(232,121,249,0.08)]"
                                : "border-white/[0.06] bg-white/[0.02] hover:border-white/[0.12]"
                                }`}
                        >
                            {/* Badge */}
                            {"badge" in plan && plan.badge && (
                                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                                    <span className="inline-flex items-center gap-1.5 rounded-full bg-gradient-to-r from-fuchsia-500 to-purple-600 px-4 py-1 text-xs font-semibold text-white shadow-lg">
                                        <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
                                        </svg>
                                        {plan.badge}
                                    </span>
                                </div>
                            )}

                            {/* Icon + Name */}
                            <div className="flex items-center gap-3 mb-3">
                                <div className={`p-2 rounded-xl ${plan.highlighted
                                    ? "bg-fuchsia-500/10 text-fuchsia-400"
                                    : "bg-white/5 text-slate-400"
                                    }`}>
                                    {plan.icon}
                                </div>
                                <h4 className="text-base font-bold tracking-wide">{plan.name}</h4>
                            </div>

                            {/* Price */}
                            <div className="mb-1">
                                <span className={`text-3xl font-extrabold ${plan.highlighted ? "neon-text" : "text-white"}`}>
                                    {plan.price}
                                </span>
                                <span className="text-slate-500 ml-1 text-sm">Kč</span>
                            </div>
                            <p className="text-[11px] text-slate-500 mb-2">{plan.priceNote}</p>
                            <p className="text-xs text-slate-300 mb-4">{plan.description}</p>

                            {/* Divider */}
                            <div className="h-px bg-gradient-to-r from-transparent via-white/10 to-transparent mb-4" />

                            {/* Features */}
                            <ul className="flex-1 space-y-2 mb-5">
                                {plan.features.map((feature) => (
                                    <li key={feature} className="flex items-start gap-2 text-xs">
                                        <svg className={`w-3.5 h-3.5 mt-0.5 flex-shrink-0 ${plan.highlighted ? "text-fuchsia-400" : "text-cyan-400"}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                        </svg>
                                        <span className="text-slate-300">{feature}</span>
                                    </li>
                                ))}
                                {plan.notIncluded.map((feature) => (
                                    <li key={feature} className="flex items-start gap-2 text-xs">
                                        <svg className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                        </svg>
                                        <span className="text-slate-500">{feature}</span>
                                    </li>
                                ))}
                            </ul>

                            {/* CTA */}
                            <button
                                onClick={() => handleCheckout(plan.key)}
                                disabled={loading === plan.key}
                                className={`block w-full text-center text-sm font-semibold py-2.5 rounded-xl transition-all disabled:opacity-50 ${plan.highlighted
                                    ? "bg-gradient-to-r from-fuchsia-600 to-fuchsia-500 text-white hover:from-fuchsia-500 hover:to-fuchsia-400 shadow-lg shadow-fuchsia-500/20"
                                    : "border border-white/10 bg-white/5 text-slate-300 hover:bg-white/10 hover:border-white/20"
                                    }`}
                            >
                                {loading === plan.key ? "Přesměrování…" : plan.cta}
                            </button>
                        </div>
                    ))}
                </div>
            </div>

            {/* ── Comparison Table with ✓/✗ ── */}
            <div className="glass p-0 overflow-hidden">
                <div className="p-5 pb-3">
                    <h3 className="font-semibold text-slate-200 mb-1">Podrobné srovnání balíčků</h3>
                    <p className="text-xs text-slate-400">Co přesně obsahuje každý balíček — na jednom místě.</p>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-sm min-w-[500px]">
                        <thead>
                            <tr className="border-t border-b border-white/[0.06]">
                                <th className="text-left px-5 py-3 text-xs text-slate-500 uppercase tracking-wider font-medium">Služba</th>
                                <th className="text-center px-3 py-3 text-xs font-bold text-slate-400 uppercase tracking-wider">
                                    BASIC
                                    <div className="text-fuchsia-400/60 text-[10px] font-normal mt-0.5">4 999 Kč</div>
                                </th>
                                <th className="text-center px-3 py-3 text-xs font-bold text-fuchsia-400 uppercase tracking-wider bg-fuchsia-500/[0.04]">
                                    PRO
                                    <div className="text-fuchsia-300 text-[10px] font-normal mt-0.5">14 999 Kč</div>
                                </th>
                                <th className="text-center px-3 py-3 text-xs font-bold text-slate-400 uppercase tracking-wider">
                                    ENTERPRISE
                                    <div className="text-fuchsia-400/60 text-[10px] font-normal mt-0.5">39 999 Kč</div>
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {COMPARISON_FEATURES.map((feat, i) => (
                                <tr key={feat.label} className={`border-b border-white/[0.04] ${i % 2 === 0 ? '' : 'bg-white/[0.01]'}`}>
                                    <td className="px-5 py-2.5 text-sm text-slate-300">{feat.label}</td>
                                    <td className="px-3 py-2.5 text-center">{feat.basic ? <Check /> : <Cross />}</td>
                                    <td className="px-3 py-2.5 text-center bg-fuchsia-500/[0.02]">{feat.pro ? <Check /> : <Cross />}</td>
                                    <td className="px-3 py-2.5 text-center">{feat.enterprise ? <Check /> : <Cross />}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                <div className="flex flex-col sm:flex-row gap-3 p-5 pt-4">
                    <button onClick={() => handleCheckout("basic")} disabled={loading === "basic"} className="flex-1 text-center text-sm font-medium py-2.5 rounded-xl border border-white/10 bg-white/5 text-slate-300 hover:bg-white/10 transition-all disabled:opacity-50">
                        {loading === "basic" ? "Přesměrování…" : "Objednat BASIC"}
                    </button>
                    <button onClick={() => handleCheckout("pro")} disabled={loading === "pro"} className="flex-1 text-center text-sm font-medium py-2.5 rounded-xl bg-gradient-to-r from-fuchsia-600 to-fuchsia-500 text-white hover:from-fuchsia-500 hover:to-fuchsia-400 shadow-lg shadow-fuchsia-500/20 transition-all disabled:opacity-50">
                        {loading === "pro" ? "Přesměrování…" : "Objednat PRO ★"}
                    </button>
                    <button onClick={() => handleCheckout("enterprise")} disabled={loading === "enterprise"} className="flex-1 text-center text-sm font-medium py-2.5 rounded-xl border border-white/10 bg-white/5 text-slate-300 hover:bg-white/10 transition-all disabled:opacity-50">
                        {loading === "enterprise" ? "Přesměrování…" : "Objednat ENTERPRISE"}
                    </button>
                </div>
            </div>
        </div>
    );
}


/* ── Info Row ── */
function InfoRow({ label, value, isUrl }: { label: string; value: string; isUrl?: boolean }) {
    return (
        <div className="rounded-lg border border-white/[0.04] bg-white/[0.01] px-4 py-3">
            <p className="text-[10px] text-slate-400 uppercase tracking-wider mb-0.5">{label}</p>
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
    title: string; description: string; href?: string; cta?: string; onAction?: () => void; illustration?: React.ReactNode;
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
                <button onClick={onAction} className="btn-primary text-sm px-6 py-2.5">{cta}</button>
            ) : href ? (
                <a href={href} className="btn-primary text-sm px-6 py-2.5">{cta}</a>
            ) : null}
        </div>
    );
}
