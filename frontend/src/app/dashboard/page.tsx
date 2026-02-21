"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useAnalytics } from "@/lib/analytics";
import {
    getDashboardData,
    startScan,
    getScanStatus,
    getScanFindings,
    getQuestionnaireProgress,
    getQuestionnaireResults,
    createCheckout,
    triggerDeepScan,
    type DashboardData,
    type ScanStatus,
    type Finding,
    type QuestionnaireProgress,
    type QuestionnaireFinding,
    type QuestionnaireUnknown,
    type QuestionnaireResultsResponse,
    type QuestionnaireAnswer,
} from "@/lib/api";
import { createClient } from "@/lib/supabase-browser";
import ContactForm from "@/components/contact-form";

type Tab = "prehled" | "findings" | "dokumenty" | "plan" | "dotaznik" | "skeny" | "ucet";


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
        key: "dotaznik",
        label: "Dotazník",
        icon: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>),
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

/* ── Human-readable category labels ── */
const CATEGORY_LABELS: Record<string, string> = {
    chatbot: "Chatbot / Konverzační AI",
    analytics: "Analytika / Sledování",
    recommender: "Doporučovací systém",
    content_gen: "Generování obsahu",
    other: "Ostatní AI systém",
};

function categoryLabel(cat: string): string {
    return CATEGORY_LABELS[cat] || cat;
}

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
    "Google Gemini Chatbot": "AI chatbot od Google \u2013 odpov\u00edd\u00e1 na dotazy n\u00e1v\u0161t\u011bvn\u00edk\u016f p\u0159\u00edmo na webu.",
    "AI Transparency Notice": "Ozn\u00e1men\u00ed o pou\u017e\u00edv\u00e1n\u00ed AI \u2013 v\u00e1\u0161 web informuje n\u00e1v\u0161t\u011bvn\u00edky, \u017ee pou\u017e\u00edv\u00e1 um\u011blou inteligenci.",
    "AI API Proxy (geminiproxy)": "Prox\u00ed server pro AI API \u2013 zprost\u0159edkov\u00e1v\u00e1 komunikaci mezi webem a AI modelem (nap\u0159. Google Gemini).",
    "Zendesk Chat": "Z\u00e1kaznick\u00fd chat od Zendesku \u2013 m\u016f\u017ee obsahovat AI chatbota pro automatick\u00e9 odpov\u011bdi.",
    "LiveChat": "Live chat s AI funkcemi \u2013 automatick\u00e9 odpov\u011bdi a sm\u011brov\u00e1n\u00ed konverzac\u00ed.",
    "Shoptet AI": "AI funkce e-shopu Shoptet \u2013 personalizace produkt\u016f a doporu\u010den\u00ed.",
    "Help Scout Beacon": "Z\u00e1kaznick\u00fd widget Help Scout \u2013 AI navrhuje \u010dl\u00e1nky a odpov\u011bdi.",
    "Vercel AI Chatbot": "AI chatbot b\u011b\u017e\u00edc\u00ed na platformě Vercel \u2013 generuje odpov\u011bdi pomoc\u00ed jazykov\u00e9ho modelu.",
    "Frase.io": "AI n\u00e1stroj pro tvorbu obsahu \u2013 generuje a optimalizuje texty pro SEO.",
    "Generický AI chatbot": "AI chatbot neznámého poskytovatele \u2013 komunikuje s n\u00e1v\u0161t\u011bvn\u00edky automaticky.",
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
    const { track, setUserEmail } = useAnalytics();
    const router = useRouter();
    const [data, setData] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [activeTab, setActiveTab] = useState<Tab>("prehled");

    // ── Questionnaire progress ──
    const [questProgress, setQuestProgress] = useState<QuestionnaireProgress | null>(null);
    const [questResults, setQuestResults] = useState<QuestionnaireResultsResponse | null>(null);
    const [questResultsLoading, setQuestResultsLoading] = useState(false);

    // ── AI systems card expand ──
    const [aiCardOpen, setAiCardOpen] = useState(false);
    const [qCardOpen, setQCardOpen] = useState(false);

    // ── Inline scan state ──
    const [scanActive, setScanActive] = useState(false);
    const [scanLoading, setScanLoading] = useState(false);
    const [scanError, setScanError] = useState<string | null>(null);
    const [scanResult, setScanResult] = useState<ScanStatus | null>(null);
    const [scanFindings, setScanFindings] = useState<Finding[]>([]);
    const [scanStage, setScanStage] = useState(0);
    const [scanDone, setScanDone] = useState(false);
    const [scanCountdown, setScanCountdown] = useState(120);
    const pollingRef = useRef<NodeJS.Timeout | null>(null);
    const stageRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const countdownRef = useRef<NodeJS.Timeout | null>(null);

    // ── Scan cooldown lock (1 hodina) ──
    const [scanCooldownUntil, setScanCooldownUntil] = useState<number | null>(null);
    const [scanCooldownMsg, setScanCooldownMsg] = useState<string | null>(null);
    const scanLocked = scanCooldownUntil !== null && Date.now() < scanCooldownUntil;

    // ── Deep scan manual trigger ──
    const [deepScanLoading, setDeepScanLoading] = useState(false);
    const [deepScanTriggered, setDeepScanTriggered] = useState(false);
    const [deepScanError, setDeepScanError] = useState<string | null>(null);

    // Restore scan cooldown from localStorage on mount
    useEffect(() => {
        try {
            const saved = localStorage.getItem('aishield_scan_cooldown');
            if (saved) {
                const until = Number(saved);
                if (until > Date.now()) {
                    setScanCooldownUntil(until);
                } else {
                    localStorage.removeItem('aishield_scan_cooldown');
                }
            }
        } catch { }
    }, []);

    // Countdown timer — ticks every second while scan is loading
    useEffect(() => {
        if (scanLoading) {
            setScanCountdown(120);
            countdownRef.current = setInterval(() => {
                setScanCountdown(prev => (prev > 0 ? prev - 1 : 0));
            }, 1000);
        } else {
            if (countdownRef.current) { clearInterval(countdownRef.current); countdownRef.current = null; }
        }
        return () => { if (countdownRef.current) { clearInterval(countdownRef.current); countdownRef.current = null; } };
    }, [scanLoading]);

    // Clean up timers on unmount
    useEffect(() => {
        return () => {
            if (pollingRef.current) clearInterval(pollingRef.current);
            if (stageRef.current) clearTimeout(stageRef.current);
            if (countdownRef.current) clearInterval(countdownRef.current);
        };
    }, []);

    const reloadDashboard = useCallback(() => {
        if (!user?.email) return;
        setUserEmail(user.email);
        getDashboardData(user.email)
            .then(setData)
            .catch(() => { /* silent */ });
    }, [user?.email, setUserEmail]);

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
        // ── Kontrola cooldownu — 1 hodina mezi skeny ──
        if (scanLocked) {
            const mins = Math.ceil(((scanCooldownUntil || 0) - Date.now()) / 60000);
            setScanCooldownMsg(`Další sken bude možný za ${mins} min. Mezi skeny musí uplynout alespoň 1 hodina.`);
            return;
        }
        setScanCooldownMsg(null);

        const scanUrl = data?.company?.url || user?.user_metadata?.web_url;
        track("scan_started", { context: "dashboard", url: scanUrl || "" });
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
            // Zamknout tlačítko na 1 hodinu po spuštění
            const lockUntil = Date.now() + 60 * 60 * 1000;
            setScanCooldownUntil(lockUntil);
            try { localStorage.setItem('aishield_scan_cooldown', String(lockUntil)); } catch { }

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

    const handleTriggerDeepScan = useCallback(async () => {
        const latestScan = data?.scans?.[0];
        if (!latestScan?.id) {
            console.warn("[Dashboard] handleTriggerDeepScan: žádný scan k dispozici");
            return;
        }
        console.log(`[Dashboard] Deep scan trigger: scan_id=${latestScan.id}, deep_scan_status=${latestScan.deep_scan_status}`);
        setDeepScanLoading(true);
        setDeepScanError(null);
        track("deep_scan_triggered", { scan_id: latestScan.id });
        try {
            const result = await triggerDeepScan(latestScan.id);
            console.log(`[Dashboard] Deep scan trigger úspěch:`, result);
            setDeepScanTriggered(true);
            // Reload dashboard to get updated deep_scan_status
            reloadDashboard();
        } catch (err) {
            const msg = err instanceof Error ? err.message : "Nepodařilo se spustit hloubkový scan";
            console.error(`[Dashboard] Deep scan trigger CHYBA: ${msg}`, err);
            setDeepScanError(msg);
        } finally {
            setDeepScanLoading(false);
        }
    }, [data?.scans, track, reloadDashboard]);

    const closeScanPanel = () => {
        setScanActive(false);
        setScanDone(false);
        setScanError(null);
    };

    useEffect(() => {
        if (!user?.email) return;
        console.log(`[Dashboard] Načítám data pro: ${user.email}`);
        setLoading(true);
        getDashboardData(user.email)
            .then((d) => {
                const scan = d?.scans?.[0];
                console.log(`[Dashboard] Data načtena: scans=${d?.scans?.length || 0}, latest_scan_status=${scan?.status}, deep_scan_status=${scan?.deep_scan_status}`);
                setData(d);
            })
            .catch((e) => {
                console.error(`[Dashboard] Chyba načítání dat: ${e.message}`);
                setError(e.message);
            })
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

    // Google OAuth uživatel bez doplněných údajů → onboarding
    if (user && !user.user_metadata?.web_url && !data?.company?.url) {
        router.replace("/onboarding");
        return null;
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
                            <button onClick={handleStartScan} disabled={scanLoading || scanLocked} className={`btn-secondary text-sm px-3 sm:px-4 py-2 disabled:opacity-50 ${scanLocked ? 'cursor-not-allowed' : ''}`}>
                                {scanLoading ? "Skenuji..." : scanLocked ? `Zamčeno (${Math.ceil(((scanCooldownUntil || 0) - Date.now()) / 60000)} min)` : "Nový sken"}
                            </button>
                            {scanCooldownMsg && (
                                <div className="w-full rounded-lg bg-amber-500/10 border border-amber-500/20 px-3 py-2 text-xs text-amber-300">
                                    <span className="font-medium">⏳ </span>{scanCooldownMsg}
                                </div>
                            )}
                            {hasScans ? (
                                hasQuest ? (
                                    qUnknowns.length > 0 ? (
                                        <button onClick={() => setActiveTab("plan")} className="btn-primary text-sm px-4 py-2 animate-pulse">
                                            Doplnit odpovědi ({qUnknowns.length})
                                        </button>
                                    ) : (
                                        <a href="#pricing" className="btn-primary text-sm px-4 py-2">
                                            Objednat dokumenty
                                        </a>
                                    )
                                ) : (
                                    <a href={`/dotaznik?company_id=${data?.company?.id || ''}`} className="btn-primary text-sm px-4 py-2">
                                        Vyplnit dotazník
                                    </a>
                                )
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
                                        <div className="text-right flex-shrink-0 ml-4">
                                            <div className="inline-flex items-center gap-2 rounded-xl bg-white/[0.04] border border-white/[0.08] px-3 py-1.5">
                                                <svg className="w-3.5 h-3.5 text-fuchsia-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6l4 2m6-2a10 10 0 11-20 0 10 10 0 0120 0z" />
                                                </svg>
                                                <span className="font-mono text-sm font-bold text-white tabular-nums">
                                                    {scanCountdown > 0
                                                        ? `${Math.floor(scanCountdown / 60)}:${(scanCountdown % 60).toString().padStart(2, '0')}`
                                                        : '0:00'}
                                                </span>
                                            </div>
                                            <p className="text-[10px] text-slate-500 mt-0.5">
                                                {scanCountdown > 0 ? 'odhadovaný čas' : 'ještě chvíli…'}
                                            </p>
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
                                        {hasScans && !hasQuest && (
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
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8 items-start">
                        {/* Panel 1: Sken webu */}
                        {(() => {
                            const latestScan = data?.scans?.[0];
                            const deepStatus = latestScan?.deep_scan_status;
                            const deepDone = deepStatus === 'done';
                            const deepRunning = deepStatus === 'pending' || deepStatus === 'running';
                            const deepTotal = latestScan?.deep_scan_total_findings ?? 0;
                            const deepStarted = latestScan?.deep_scan_started_at;
                            // Countdown: estimate 24h from deep_scan_started_at
                            const deepEta = deepStarted ? (() => {
                                const endTime = new Date(deepStarted).getTime() + 25 * 60 * 1000; // Testing: ~25 min max
                                const remaining = endTime - Date.now();
                                if (remaining <= 0) return 'dokončení každou chvíli…';
                                const hours = Math.floor(remaining / (60 * 60 * 1000));
                                const mins = Math.floor((remaining % (60 * 60 * 1000)) / (60 * 1000));
                                return hours > 0 ? `~${hours}h ${mins}min` : `~${mins}min`;
                            })() : null;
                            const countryFlags: Record<string, string> = { CZ: '🇨🇿', GB: '🇬🇧', US: '🇺🇸', BR: '🇧🇷', JP: '🇯🇵', ZA: '🇿🇦', AU: '🇦🇺' };
                            const scannedFlags = (latestScan?.geo_countries_scanned || []).map(c => countryFlags[c] || c).join(' ');

                            return (
                                <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 hover:border-white/[0.12] transition-all flex flex-col">
                                    <p className="text-xs text-slate-400 uppercase tracking-wider mb-2">Sken webu</p>
                                    {!hasScans ? (
                                        <>
                                            <p className="text-2xl font-extrabold mt-1 text-slate-500">—</p>
                                            <p className="text-xs text-slate-400 mt-1 leading-relaxed">Sken zatím nebyl proveden.</p>
                                        </>
                                    ) : deepDone ? (
                                        /* ═══ Deep scan DONE ═══ */
                                        <>
                                            <p className="text-2xl font-extrabold mt-1 text-amber-400">{deepTotal}</p>
                                            <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                                                Hloubkový 24h scan dokončen — nalezeno <strong className="text-white">{deepTotal}</strong> AI {deepTotal === 1 ? 'systém' : deepTotal >= 2 && deepTotal <= 4 ? 'systémy' : 'systémů'}.
                                            </p>
                                            <div className="mt-2 flex items-center gap-1.5">
                                                <span className="inline-block w-2 h-2 rounded-full bg-green-400" />
                                                <span className="text-[10px] text-green-400 font-medium">Dokončeno</span>
                                                {scannedFlags && <span className="text-[10px] text-slate-500 ml-1">· {scannedFlags}</span>}
                                            </div>
                                        </>
                                    ) : (
                                        /* ═══ Quick scan results ═══ */
                                        <>
                                            <div className="flex items-center gap-1.5 mb-1">
                                                <span className="inline-block w-2 h-2 rounded-full bg-cyan-400" />
                                                <span className="text-[10px] text-cyan-400 font-medium uppercase tracking-wide">Rychlý orientační scan</span>
                                            </div>
                                            {uniqueSystemsCount > 0 ? (
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
                                                        Rychlý scan na webu nezjistil žádné AI systémy spadající pod EU AI Act.
                                                    </p>
                                                    <p className="text-[10px] text-slate-500 mt-1 leading-relaxed">
                                                        Řada AI nástrojů se načítá dynamicky. Doporučujeme 24h hloubkový scan a dotazník.
                                                    </p>
                                                </>
                                            )}
                                        </>
                                    )}
                                    {/* Deep scan running — compact indicator */}
                                    {hasScans && deepRunning && (
                                        <div className="mt-3 flex items-start gap-2.5 rounded-lg bg-purple-500/[0.07] px-3 py-2.5">
                                            <span className="relative flex h-2 w-2 mt-0.5 shrink-0">
                                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75" />
                                                <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-500" />
                                            </span>
                                            <div>
                                                <p className="text-[11px] font-semibold text-purple-300">Hloubkový scan probíhá</p>
                                                <p className="text-[10px] text-slate-400 mt-0.5">
                                                    Skenování z více zemí · zbývá {deepEta || 'odhad není k dispozici'}
                                                    {scannedFlags && <span className="text-slate-500"> · {scannedFlags}</span>}
                                                </p>
                                            </div>
                                        </div>
                                    )}
                                    {hasScans && uniqueSystemsCount === 0 && !deepDone && !hasQuest && (
                                        <p className="text-[10px] text-amber-400/80 mt-2">Scan prověřuje jen web — AI Act se týká i interních nástrojů.</p>
                                    )}
                                    {/* Expandable scan findings */}
                                    {hasScans && uniqueSystemsCount > 0 && !deepDone && (
                                        <div className="mt-3 border-t border-white/[0.06] pt-2.5">
                                            <button onClick={() => setAiCardOpen(!aiCardOpen)} className="text-[11px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors">
                                                {aiCardOpen ? 'Skrýt nálezy' : `Zobrazit nálezy (${uniqueSystemsCount})`}
                                                <svg className={`w-3 h-3 transition-transform ${aiCardOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                                </svg>
                                            </button>
                                            {aiCardOpen && (
                                                <div className="mt-2 space-y-1">
                                                    {groupFindings(data?.findings || []).map((f) => (
                                                        <div key={f.name} className="flex items-baseline justify-between px-2.5 py-1.5 rounded bg-white/[0.03]">
                                                            <p className="text-xs text-white">{f.name}</p>
                                                            <p className="text-[10px] text-slate-500 shrink-0 ml-2">{categoryLabel(f.category)}{f.count > 1 ? ` · ${f.count}×` : ''}</p>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                    <div className="mt-auto pt-3 space-y-2">
                                        {/* Deep scan CTA — quest not done */}
                                        {hasScans && !deepDone && !deepRunning && deepStatus !== 'cooldown' && !hasQuest && (
                                            <div className="space-y-2">
                                                <button
                                                    onClick={handleTriggerDeepScan}
                                                    disabled={deepScanLoading}
                                                    className="w-full relative overflow-hidden rounded-xl bg-gradient-to-r from-purple-600 to-fuchsia-600 px-4 py-3 text-sm font-bold text-white shadow-lg shadow-purple-500/25 hover:shadow-purple-500/40 hover:from-purple-500 hover:to-fuchsia-500 transition-all disabled:opacity-50 group"
                                                >
                                                    <span className="absolute inset-0 rounded-xl animate-pulse bg-gradient-to-r from-purple-400/20 to-fuchsia-400/20" />
                                                    <span className="relative flex items-center justify-center gap-2">
                                                        {deepScanLoading ? (
                                                            <>
                                                                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                                                                Spouštím…
                                                            </>
                                                        ) : '🔍 Spustit 24h hloubkový scan'}
                                                    </span>
                                                </button>
                                                <p className="text-[10px] text-slate-500 text-center">24 skenů ze 7 zemí za 24 hodin</p>
                                                {deepScanError && (
                                                    <p className="text-[10px] text-red-400">{deepScanError}</p>
                                                )}
                                            </div>
                                        )}
                                        {/* Deep scan CTA — quest done, subtle */}
                                        {hasScans && !deepDone && !deepRunning && deepStatus !== 'cooldown' && hasQuest && (
                                            <button
                                                onClick={handleTriggerDeepScan}
                                                disabled={deepScanLoading}
                                                className="text-[10px] text-purple-400 hover:text-purple-300 transition-colors disabled:opacity-50"
                                            >
                                                {deepScanLoading ? 'Spouštím…' : '🔍 Volitelné: 24h hloubkový scan'}
                                            </button>
                                        )}

                                        {/* Cooldown */}
                                        {deepStatus === 'cooldown' && (
                                            <p className="text-[10px] text-slate-500">
                                                24h scan proveden v posledních 7 dnech — další bude dostupný za týden.
                                            </p>
                                        )}
                                        {/* Re-scan */}
                                        {(deepDone || deepStatus === 'cooldown') && !scanLocked && (
                                            <button onClick={handleStartScan} disabled={scanLoading || scanLocked} className="text-xs px-3 py-1.5 rounded-lg bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 hover:bg-cyan-500/20 transition-all disabled:opacity-50">
                                                {scanLoading ? 'Skenuji…' : 'Opakovat rychlý sken'}
                                            </button>
                                        )}
                                        {(deepDone || deepStatus === 'cooldown') && scanLocked && (
                                            <p className="text-[10px] text-amber-400/80">Další sken za {Math.ceil(((scanCooldownUntil || 0) - Date.now()) / 60000)} min.</p>
                                        )}
                                    </div>
                                </div>
                            );
                        })()}

                        {/* Panel 2: Výsledky dotazníku */}
                        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 hover:border-white/[0.12] transition-all flex flex-col">
                            <p className="text-xs text-slate-400 uppercase tracking-wider mb-2">Výsledky dotazníku</p>
                            {!hasQuest ? (
                                <>
                                    <p className="text-2xl font-extrabold mt-1 text-slate-500">—</p>
                                    <p className="text-xs text-slate-400 mt-1 leading-relaxed">Sken prověřuje jen web. AI Act reguluje i interní systémy — vyplňte dotazník.</p>
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
                                    U {qUnknowns.length} {cz(qUnknowns.length, 'otázky', 'otázek', 'otázek')} jste odpověděli &bdquo;Nevím&ldquo;. Tyto informace je nutné zjistit a doplnit, abychom Vám mohli poskytnout 100% jistotu krytí.
                                </p>
                            )}
                            {/* Expandable questionnaire findings */}
                            {hasQuest && qFindings.length > 0 && (
                                <div className="mt-3 border-t border-white/[0.06] pt-3">
                                    <button onClick={() => setQCardOpen(!qCardOpen)} className="text-xs text-fuchsia-400 hover:text-fuchsia-300 flex items-center gap-1 transition-colors">
                                        {qCardOpen ? 'Skrýt nálezy' : 'Zobrazit nálezy'}
                                        <svg className={`w-3 h-3 transition-transform ${qCardOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                        </svg>
                                    </button>
                                    {qCardOpen && (
                                        <div className="mt-2 space-y-1.5">
                                            {qFindings.map((f) => (
                                                <div key={f.question_key} className={`rounded-md px-3 py-2 border ${f.risk_level === 'high'
                                                    ? 'bg-red-500/[0.05] border-red-500/[0.15]'
                                                    : f.risk_level === 'limited'
                                                        ? 'bg-amber-500/[0.05] border-amber-500/[0.15]'
                                                        : 'bg-cyan-500/[0.03] border-cyan-500/[0.1]'
                                                    }`}>
                                                    <p className={`text-[10px] font-semibold uppercase tracking-wider ${f.risk_level === 'high' ? 'text-red-400' : f.risk_level === 'limited' ? 'text-amber-400' : 'text-cyan-400'
                                                        }`}>
                                                        {f.risk_level === 'high' ? '⚠ Vysoké riziko' : f.risk_level === 'limited' ? '⚡ Omezené riziko' : '✓ Minimální riziko'}
                                                    </p>
                                                    <p className="text-xs font-medium text-white mt-1">{f.human_summary || f.name}</p>
                                                    {f.name && f.name !== f.human_summary && (
                                                        <p className="text-[10px] text-slate-500 mt-0.5">Nástroj: {f.name}</p>
                                                    )}
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            )}
                            <div className="mt-auto pt-3">
                                {hasScans && !hasQuest && (
                                    <a href={`/dotaznik?company_id=${data?.company?.id || ''}`}
                                        className="text-xs px-3 py-1.5 rounded-lg bg-fuchsia-500/10 text-fuchsia-300 border border-fuchsia-500/20 hover:bg-fuchsia-500/20 transition-all inline-block">
                                        Vyplnit dotazník
                                    </a>
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

                                // Deep scan state (local to this panel)
                                const latestScan = data?.scans?.[0];
                                const ds = latestScan?.deep_scan_status;
                                const deepRunningLocal = ds === 'pending' || ds === 'running';
                                const deepDoneLocal = ds === 'done' || ds === 'cooldown';
                                const noDeepYet = !ds || (!['pending', 'running', 'done', 'cooldown'].includes(ds));

                                // Summary line: findings count
                                const scanCount = uniqueSystemsCount || 0;
                                const questCount = qFindings?.length || 0;

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

                                // Quest done (even with some unknowns) → show "Objednejte" with findings summary
                                if (hasQuest && hasScans) {
                                    return (
                                        <>
                                            <p className="text-2xl font-extrabold mt-1 text-fuchsia-400">Objednejte</p>
                                            {/* Findings summary */}
                                            <div className="mt-2 space-y-1">
                                                {scanCount > 0 && (
                                                    <div className="flex items-center gap-1.5">
                                                        <span className="inline-block w-1.5 h-1.5 rounded-full bg-cyan-400" />
                                                        <span className="text-[10px] text-slate-300">{scanCount} AI {scanCount === 1 ? 'systém' : 'systémů'} ze skenu</span>
                                                    </div>
                                                )}
                                                {questCount > 0 && (
                                                    <div className="flex items-center gap-1.5">
                                                        <span className="inline-block w-1.5 h-1.5 rounded-full bg-amber-400" />
                                                        <span className="text-[10px] text-slate-300">{questCount} {questCount === 1 ? 'nález' : 'nálezů'} z dotazníku</span>
                                                    </div>
                                                )}
                                            </div>
                                            <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                                                {questIncomplete
                                                    ? `Můžete objednat nyní. U ${qUnknowns.length} otázek zbývá doplnit „Nevím".`
                                                    : 'Analýza dokončena. Vyberte si balíček pro vygenerování compliance dokumentace.'
                                                }
                                            </p>
                                            {/* Deep scan running indicator */}
                                            {deepRunningLocal && (
                                                <div className="mt-2 flex items-center gap-1.5">
                                                    <span className="relative flex h-2 w-2">
                                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75" />
                                                        <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-500" />
                                                    </span>
                                                    <span className="text-[10px] text-purple-300">24h test probíhá — výsledky doplníme automaticky</span>
                                                </div>
                                            )}
                                            {deepDoneLocal && (
                                                <div className="mt-2 flex items-center gap-1.5">
                                                    <span className="inline-block w-2 h-2 rounded-full bg-green-400" />
                                                    <span className="text-[10px] text-green-400">24h test ✓</span>
                                                </div>
                                            )}
                                        </>
                                    );
                                }

                                // Active scan running → show "Skenujeme" state
                                if (scanLoading) {
                                    return (
                                        <>
                                            <p className="text-2xl font-extrabold mt-1 text-cyan-400">Skenujeme</p>
                                            <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                                                Probíhá analýza Vašeho webu. Výsledky se zobrazí automaticky.
                                            </p>
                                            <div className="mt-2 flex items-center gap-1.5">
                                                <span className="relative flex h-2 w-2">
                                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
                                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500" />
                                                </span>
                                                <span className="text-[10px] text-cyan-300">
                                                    {scanCountdown > 0
                                                        ? `~${Math.floor(scanCountdown / 60)}:${(scanCountdown % 60).toString().padStart(2, '0')} zbývá`
                                                        : 'Dokončujeme…'}
                                                </span>
                                            </div>
                                        </>
                                    );
                                }

                                // Waiting state — quest not done
                                const waitItems: string[] = [];
                                if (!hasQuest) waitItems.push('vyplnění dotazníku');
                                if (deepRunningLocal) waitItems.push('dokončení 24h testu');
                                return (
                                    <>
                                        <p className="text-2xl font-extrabold mt-1 text-amber-400">Čekáme</p>
                                        <p className="text-xs text-slate-300 mt-1 leading-relaxed">
                                            {waitItems.length > 0
                                                ? `Čekáme na ${waitItems.join(' a ')}.`
                                                : 'Čekáme na dokončení analýzy.'
                                            }
                                        </p>
                                        {scanCount > 0 && (
                                            <div className="mt-2 flex items-center gap-1.5">
                                                <span className="inline-block w-1.5 h-1.5 rounded-full bg-cyan-400" />
                                                <span className="text-[10px] text-slate-400">{scanCount} AI {scanCount === 1 ? 'systém' : 'systémů'} ze skenu</span>
                                            </div>
                                        )}
                                        {deepRunningLocal && (
                                            <div className="mt-2 flex items-center gap-1.5">
                                                <span className="relative flex h-2 w-2">
                                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75" />
                                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-purple-500" />
                                                </span>
                                                <span className="text-[10px] text-purple-300">24h test probíhá</span>
                                            </div>
                                        )}
                                        {noDeepYet && hasScans && (
                                            <div className="mt-2 flex items-center gap-1.5">
                                                <span className="inline-block w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                                                <span className="text-[10px] text-amber-300">Hloubkový test zatím nespuštěn</span>
                                            </div>
                                        )}
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
                                Doplnit {qUnknowns.length} {cz(qUnknowns.length, 'odpověď', 'odpovědi', 'odpovědí')} →
                            </button>
                        </div>
                    )}

                    {/* Tabs */}
                    <div className="flex gap-1 overflow-x-auto border-b border-white/[0.06] mb-6 scrollbar-hide">
                        {TABS.map((tab) => (
                            <button
                                key={tab.key}
                                onClick={() => { setActiveTab(tab.key); track("dashboard_tab_clicked", { tab: tab.key }); }}
                                className={`relative flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-4 py-2 sm:py-2.5 text-xs sm:text-sm font-medium transition-all whitespace-nowrap ${activeTab === tab.key
                                    ? "text-fuchsia-400"
                                    : "text-slate-500 hover:text-slate-300"
                                    }`}
                            >
                                {tab.icon}
                                <span className={tab.key === "plan" && qUnknowns.length > 0 && activeTab !== "plan" ? "text-amber-400 animate-pulse font-bold" : ""}>
                                    {tab.label}
                                </span>
                                {tab.key === "plan" && qUnknowns.length > 0 && activeTab !== "plan" && (
                                    <span className="ml-1 flex h-5 w-5 items-center justify-center rounded-full bg-amber-500 text-[10px] font-bold text-black animate-pulse shadow-lg shadow-amber-500/50">
                                        {qUnknowns.length}
                                    </span>
                                )}
                                {activeTab === tab.key && (
                                    <span className="absolute bottom-0 left-2 right-2 h-0.5 bg-gradient-to-r from-fuchsia-500 to-fuchsia-400 rounded-full" />
                                )}
                            </button>
                        ))}
                    </div>

                    {/* Tab content */}
                    <div className="min-h-[400px]">
                        {activeTab === "prehled" && <TabPrehled data={data} onStartScan={handleStartScan} scanLoading={scanLoading} hasScans={hasScans} onShowPlan={() => setActiveTab("plan")} onTriggerDeepScan={handleTriggerDeepScan} deepScanLoading={deepScanLoading} deepScanTriggered={deepScanTriggered} deepScanError={deepScanError} />}
                        {activeTab === "findings" && <TabFindings findings={data?.findings || []} questionnaireFindings={qFindings} questionnaireUnknowns={qUnknowns} hasQuest={hasQuest} companyId={data?.company?.id || ''} onStartScan={handleStartScan} />}
                        {activeTab === "dokumenty" && <TabDokumenty documents={data?.documents || []} />}
                        {activeTab === "plan" && <TabPlan questionnaireUnknowns={qUnknowns} companyId={data?.company?.id || ''} />}
                        {activeTab === "dotaznik" && <TabDotaznik companyId={data?.company?.id || ''} questResults={questResults} questResultsLoading={questResultsLoading} setQuestResults={setQuestResults} setQuestResultsLoading={setQuestResultsLoading} hasQuest={hasQuest} />}
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
function TabPrehled({ data, onStartScan, scanLoading, hasScans: hasScansOverride, onShowPlan, onTriggerDeepScan, deepScanLoading, deepScanTriggered, deepScanError }: { data: DashboardData | null; onStartScan: () => void; scanLoading: boolean; hasScans: boolean; onShowPlan: () => void; onTriggerDeepScan: () => void; deepScanLoading: boolean; deepScanTriggered: boolean; deepScanError: string | null }) {
    const hasScans = hasScansOverride || (data?.scans.length || 0) > 0;
    const hasQuest = data?.questionnaire_status === "dokončen";
    const hasDocs = (data?.documents.length || 0) > 0;
    const hasOrder = (data?.orders || []).length > 0;
    const hasPaidOrder = data?.orders.some((o) => o.status === "PAID") || false;
    const ws = data?.company?.workflow_status || 'new';
    const isProcessingDocs = ws === 'processing' || ws === 'documents_sent';
    const qUnknowns = data?.questionnaire_unknowns || [];

    const latestScan = data?.scans?.[0];
    const deepStatus = latestScan?.deep_scan_status;
    const deepDone = deepStatus === 'done' || deepStatus === 'cooldown';
    const deepRunning = deepStatus === 'pending' || deepStatus === 'running';

    const steps = [
        {
            done: hasScans,
            label: "Sken webu",
            desc: "Automatická detekce AI systémů na vašem webu",
            detail: null as string | null,
            href: null as string | null,
            cta: scanLoading ? "Skenuji..." : "Spustit sken",
            onClick: onStartScan,
        },
        {
            done: deepDone || deepRunning,
            optional: true,
            label: deepRunning && !deepDone ? "24h test ⏳" : "24h test",
            desc: deepDone
                ? "Hloubkový scan ze 7 zemí a 6 kontinentů byl úspěšně dokončen"
                : deepRunning
                    ? "Hloubkový scan probíhá na pozadí ze 7 zemí — mezitím pokračujte dotazníkem"
                    : hasScans
                        ? "Spusťte 24hodinový hloubkový test ze 7 zemí a 6 kontinentů"
                        : "Nejprve dokončete rychlý sken webu",
            detail: null,
            href: null,
            cta: "__deep_scan_custom__",  // Custom rendering handled below
            onClick: undefined as (() => void) | undefined,
        },
        {
            done: hasQuest,
            label: "Dotazník",
            desc: hasQuest
                ? (qUnknowns.length > 0 ? `U ${qUnknowns.length} otázek jste zvolili „Nevím" — doplňte je` : "Všechny odpovědi jsou kompletní")
                : "Upřesní analýzu o interní AI nástroje (ChatGPT, Copilot…)",
            detail: hasQuest ? null : "EU AI Act se netýká jen toho, co je vidět na webu. Regulace zahrnuje i interní AI systémy — nástroje pro HR, účetnictví, rozhodování, generování obsahu nebo komunikaci se zaměstnanci. Automatický sken odhalí jen veřejně viditelné nástroje. Dotazník pokrývá celou AI politiku firmy, včetně toho, co zákazník nikdy neuvidí.",
            href: hasScans && !hasQuest ? `/dotaznik?company_id=${data?.company?.id || ''}` : null,
            cta: !hasScans ? "🔒 Nejprve skenujte web" : !hasQuest ? "Vyplnit dotazník" : qUnknowns.length > 0 ? "Doplnit odpovědi" : "✓ Kompletní",
            onClick: (hasScans && hasQuest && qUnknowns.length > 0) ? onShowPlan : undefined as (() => void) | undefined,
        },
        {
            done: hasOrder,
            label: "Objednávka",
            desc: hasOrder ? "Objednávka byla přijata" : "Odemkněte compliance dokumenty a školení",
            detail: null,
            href: hasOrder ? null : "#pricing",
            cta: hasOrder ? "✓ Objednáno" : "Vybrat balíček",
            onClick: undefined as (() => void) | undefined,
        },
        {
            done: hasPaidOrder,
            label: "Platba",
            desc: hasPaidOrder ? "Platba byla přijata" : hasOrder ? "Čekáme na připsání platby na účet" : "Po objednání obdržíte platební údaje",
            detail: null,
            href: null,
            cta: hasPaidOrder ? "✓ Zaplaceno" : hasOrder ? "Čeká na platbu" : "",
            onClick: undefined as (() => void) | undefined,
        },
        {
            done: isProcessingDocs,
            label: "Tvorba dokumentace",
            desc: isProcessingDocs ? "Pracujeme na vaší dokumentaci" : hasPaidOrder ? "Připravujeme vaše dokumenty" : "Po zaplacení začneme s tvorbou",
            detail: null,
            href: null,
            cta: isProcessingDocs ? "Zpracováváme" : "",
            onClick: undefined as (() => void) | undefined,
        },
        {
            done: hasDocs,
            label: "Dodání",
            desc: hasDocs ? "Dokumenty jsou připraveny ke stažení — tištěnou verzi doručíme do 14 dnů" : "Až 12 dokumentů v PDF + tištěná verze v profesionální vazbě",
            detail: null,
            href: hasDocs ? "#" : null,
            cta: hasDocs ? "Viz tab Dokumenty" : "",
            onClick: undefined as (() => void) | undefined,
        },
    ];

    // Smart step index: skip optional steps (24h test) when later steps are done
    const rawStepIndex = steps.findIndex((s) => !s.done);
    const currentStepIndex = (rawStepIndex === 1 && steps[2]?.done) ? steps.findIndex((s, i) => i > 1 && !s.done) : rawStepIndex;
    const currentStep = currentStepIndex >= 0 ? steps[currentStepIndex] : null;
    const completedCount = steps.filter((s) => s.done).length;
    // Line extends TO the current active step (not just to last completed)
    const progressTarget = currentStepIndex >= 0 ? currentStepIndex : steps.length - 1;
    const lineWidthPercent = progressTarget <= 0 ? 0 : (progressTarget / (steps.length - 1)) * ((steps.length - 1) / steps.length * 100);

    const isProcessing = hasPaidOrder && !hasDocs;
    const currentHour = new Date().getHours();
    const isBusinessHours = currentHour >= 8 && currentHour < 16;

    return (
        <div className="space-y-6">
            {/* Progress Timeline */}
            <div className="glass">
                <h3 className="font-semibold mb-8">Postup k compliance</h3>
                <div className="grid grid-cols-7 relative mb-8">
                    {/* Background track line */}
                    <div className="absolute top-[18px] sm:top-[22px] left-[7%] right-[7%] h-1 rounded-full bg-gradient-to-r from-white/[0.04] via-white/[0.08] to-white/[0.04]" />
                    {/* Active progress line */}
                    {lineWidthPercent > 0 && (
                        <div
                            className="absolute top-[18px] sm:top-[22px] left-[7%] h-1 rounded-full transition-all duration-700"
                            style={{
                                width: `${lineWidthPercent}%`,
                                background: 'linear-gradient(90deg, #22c55e, #10b981, #06b6d4, #a855f7)',
                                boxShadow: '0 0 12px rgba(34,197,94,0.4), 0 0 24px rgba(6,182,212,0.2)',
                            }}
                        />
                    )}
                    {steps.map((step, i) => {
                        const isCurrent = i === currentStepIndex;
                        const isSkipped = !step.done && (step as any).optional && i < (currentStepIndex >= 0 ? currentStepIndex : steps.length);
                        const isRunning = i === 1 && deepRunning && !deepDone;
                        return (
                            <div key={i} className="flex flex-col items-center relative z-10">
                                {/* Node circle */}
                                <div className={`flex items-center justify-center h-9 w-9 sm:h-11 sm:w-11 rounded-full text-xs sm:text-sm font-bold transition-all duration-500 ${step.done && !isRunning
                                    ? "bg-gradient-to-br from-green-500/30 to-emerald-500/20 text-green-300 border-2 border-green-400/50 shadow-[0_0_16px_rgba(34,197,94,0.3),0_0_4px_rgba(34,197,94,0.5)]"
                                    : isRunning
                                        ? "bg-gradient-to-br from-cyan-500/25 to-blue-500/15 text-cyan-300 border-2 border-cyan-400/50 shadow-[0_0_16px_rgba(6,182,212,0.3)] animate-pulse"
                                        : isSkipped
                                            ? "bg-slate-700/80 text-slate-400 border-2 border-dashed border-slate-500/40"
                                            : isCurrent
                                                ? "bg-gradient-to-br from-fuchsia-500/30 to-purple-500/20 text-fuchsia-300 border-2 border-fuchsia-400/60 shadow-[0_0_20px_rgba(217,70,239,0.35),0_0_6px_rgba(217,70,239,0.5)] animate-pulse"
                                                : "bg-slate-800/80 text-slate-500 border-2 border-white/[0.1] shadow-[0_0_6px_rgba(0,0,0,0.3)]"
                                    }`}>
                                    {step.done && !isRunning ? (
                                        <svg className="w-5 h-5 sm:w-6 sm:h-6 drop-shadow-[0_0_4px_rgba(34,197,94,0.6)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                                        </svg>
                                    ) : isRunning ? (
                                        <span className="text-sm">⏳</span>
                                    ) : isSkipped ? (
                                        <span className="text-[10px] text-slate-500">—</span>
                                    ) : (
                                        <span className={isCurrent ? "drop-shadow-[0_0_4px_rgba(217,70,239,0.6)]" : ""}>{i + 1}</span>
                                    )}
                                </div>
                                {/* Label */}
                                <span className={`text-[8px] sm:text-[11px] mt-1.5 sm:mt-2.5 font-semibold text-center leading-tight max-w-[60px] sm:max-w-none ${step.done
                                    ? "text-green-400/90 drop-shadow-[0_0_4px_rgba(34,197,94,0.3)]"
                                    : isCurrent
                                        ? "text-fuchsia-400 drop-shadow-[0_0_4px_rgba(217,70,239,0.3)]"
                                        : "text-slate-500"
                                    }`}>
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
                        <p className="text-sm text-slate-300 mb-2 ml-0 sm:ml-9">{currentStep.desc}</p>
                        {currentStep.detail && (
                            <div className="ml-0 sm:ml-9 mb-4 rounded-lg bg-cyan-500/[0.06] border border-cyan-500/15 p-3">
                                <p className="text-xs font-semibold text-cyan-400 mb-1">Proč je dotazník potřeba?</p>
                                <p className="text-xs text-slate-400 leading-relaxed">{currentStep.detail}</p>
                            </div>
                        )}
                        {/* Custom deep scan step rendering */}
                        {currentStep.cta === "__deep_scan_custom__" ? (
                            <div className="ml-0 sm:ml-9 space-y-3">
                                {/* Not triggered yet → Big pulsating button */}
                                {!deepRunning && !deepDone && (
                                    <div className="space-y-3">
                                        <p className="text-xs text-slate-400 leading-relaxed">
                                            Chatboti a AI nástroje se často zobrazují jen v určitou hodinu, z určité lokace nebo na mobilním zařízení — rychlý scan je nemůže odhalit všechny.
                                        </p>
                                        <button
                                            onClick={onTriggerDeepScan}
                                            disabled={deepScanLoading || !hasScans}
                                            className="relative overflow-hidden w-full sm:w-auto rounded-xl bg-gradient-to-r from-purple-600 to-fuchsia-600 px-4 py-3 text-sm font-bold text-white shadow-lg shadow-purple-500/25 hover:shadow-purple-500/40 hover:from-purple-500 hover:to-fuchsia-500 transition-all disabled:opacity-50 group"
                                        >
                                            <span className="absolute inset-0 rounded-xl animate-pulse bg-gradient-to-r from-purple-400/20 to-fuchsia-400/20" />
                                            <span className="relative flex items-center justify-center gap-2">
                                                {deepScanLoading ? (
                                                    <>
                                                        <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                                                        Spouštím...
                                                    </>
                                                ) : (
                                                    <>🔍 Spustit hloubkový test</>
                                                )}
                                            </span>
                                        </button>
                                        {deepScanError && (
                                            <p className="text-xs text-red-400">{deepScanError}</p>
                                        )}
                                        <p className="text-xs text-slate-400">
                                            🇨🇿 🇬🇧 🇺🇸 🇧🇷 🇯🇵 🇿🇦 🇦🇺 — 7 zemí, 6 kontinentů, desktop i mobil
                                        </p>
                                    </div>
                                )}
                                {/* Running → Success message + dotazník */}
                                {deepRunning && !deepDone && (
                                    <div className="space-y-4">
                                        <div className="rounded-xl border border-green-500/20 bg-green-500/[0.04] p-5">
                                            <div className="flex items-center gap-3 mb-3">
                                                <span className="text-2xl">✅</span>
                                                <h4 className="font-bold text-green-300 text-base">Výborně! Hloubkový test běží</h4>
                                            </div>
                                            <p className="text-sm text-slate-300 leading-relaxed">
                                                Za přibližně <strong className="text-white">24 hodin</strong> vám napíšeme e-mail s kompletními výsledky.
                                                Mezitím můžete vyplnit dotazník — upřesní analýzu o interní AI systémy.
                                            </p>
                                        </div>
                                        {!hasQuest && (
                                            <a
                                                href={`/dotaznik?company_id=${data?.company?.id || ''}`}
                                                className="relative overflow-hidden inline-flex items-center justify-center w-full sm:w-auto rounded-xl bg-gradient-to-r from-fuchsia-600 to-purple-600 px-8 py-4 text-base font-bold text-white shadow-lg shadow-fuchsia-500/30 hover:shadow-fuchsia-500/50 hover:from-fuchsia-500 hover:to-purple-500 transition-all"
                                            >
                                                <span className="absolute inset-0 rounded-xl animate-pulse bg-gradient-to-r from-fuchsia-400/20 to-purple-400/20" />
                                                <span className="relative">📝 Vyplnit dotazník</span>
                                            </a>
                                        )}
                                    </div>
                                )}
                            </div>
                        ) : currentStep.onClick ? (
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

            {/* 24h deep scan running banner — always visible when test is in progress */}
            {deepRunning && !deepDone && currentStepIndex !== 1 && (
                <div className="glass border-cyan-500/20">
                    <div className="flex items-start gap-4">
                        <div className="flex-shrink-0 h-10 w-10 rounded-full bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center">
                            <span className="text-lg animate-pulse">⏳</span>
                        </div>
                        <div>
                            <h4 className="font-semibold text-cyan-300 text-sm">24h hloubkový test probíhá</h4>
                            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                                Testujeme váš web ze <strong className="text-slate-300">7 zemí a 6 kontinentů</strong> (desktop i mobil).
                                Výsledky budou přibližně za <strong className="text-slate-300">24 hodin</strong> — pošleme vám e-mail.
                            </p>
                            <div className="flex items-center gap-2 mt-2">
                                <span className="text-[10px] text-slate-500">🇨🇿 🇬🇧 🇺🇸 🇧🇷 🇯🇵 🇿🇦 🇦🇺</span>
                            </div>
                        </div>
                    </div>
                </div>
            )}

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
                            <strong className="text-cyan-300"> To je báječné!</strong> Využívání těchto nástrojů Vám dává <strong className="text-cyan-300">ohromnou konkurenční výhodu</strong> před weby, které AI nepoužívají.
                            Jen je potřeba mít vše správně ošetřeno tak, jak to vyžaduje legislativa EU &mdash; správně informovat návštěvníky a mít k tomu příslušnou dokumentaci.
                            <strong className="text-cyan-300"> Vše zařídíme za Vás!</strong>
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
                                                {f.category && <span>Kategorie: {categoryLabel(f.category)}</span>}
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
                                            href={`/dotaznik?company_id=${companyId}`}
                                            className="btn-primary !text-xs !px-4 !py-2 !rounded-lg mt-3 inline-block"
                                        >
                                            Už vím! Chci změnit odpověď v dotazníku
                                        </a>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                    <a href={`/dotaznik?company_id=${companyId}`}
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
                        Sken odhalil AI systémy na webu, ale <strong className="text-white">EU AI Act reguluje i interní nástroje</strong>,
                        které zákazník nikdy neuvidí — ChatGPT pro zaměstnance, AI v účetnictví, automatizaci HR nebo AI rozhodování.
                        Vyplňte dotazník a pokryjte celou AI politiku firmy.
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
                            Do 14 dnů vám vše doručíme i v tištěné podobě v profesionální vazbě — připravené na kontrolu.
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
    // Auto-expand the first item so user immediately sees the pattern
    const [expanded, setExpanded] = useState<Record<string, boolean>>(
        questionnaireUnknowns.length > 0
            ? { [`plan_unk_${questionnaireUnknowns[0].question_key}`]: true }
            : {}
    );

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

    const completedCount = 0; // All items here are "unknown", so 0 completed

    return (
        <div className="space-y-5">
            {/* Header with progress */}
            <div className="rounded-xl border border-amber-500/25 bg-gradient-to-r from-amber-500/[0.06] to-orange-500/[0.04] p-5">
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center">
                            <svg className="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                        </div>
                        <div>
                            <h4 className="text-sm font-bold text-white">Doplňte {questionnaireUnknowns.length} {cz(questionnaireUnknowns.length, 'odpověď', 'odpovědi', 'odpovědí')}</h4>
                            <p className="text-xs text-slate-400 mt-0.5">Bez těchto informací nemůžeme dokončit vaši dokumentaci</p>
                        </div>
                    </div>
                    <div className="text-right">
                        <span className="text-2xl font-bold text-amber-400">{completedCount}/{questionnaireUnknowns.length}</span>
                        <p className="text-[10px] text-slate-500 uppercase tracking-wider">doplněno</p>
                    </div>
                </div>
                {/* Progress bar */}
                <div className="w-full h-2 bg-white/[0.06] rounded-full overflow-hidden">
                    <div
                        className="h-full bg-gradient-to-r from-amber-500 to-orange-500 rounded-full transition-all duration-500"
                        style={{ width: `${questionnaireUnknowns.length > 0 ? (completedCount / questionnaireUnknowns.length) * 100 : 0}%` }}
                    />
                </div>
            </div>

            {/* Items */}
            <div className="space-y-3">
                {questionnaireUnknowns.map((u, idx) => {
                    const dotColor = u.severity_color === "red" ? "bg-red-500" : u.severity_color === "orange" ? "bg-orange-500" : u.severity_color === "yellow" ? "bg-amber-400" : "bg-slate-500";
                    const labelColor = u.severity_color === "red" ? "text-red-400"
                        : u.severity_color === "orange" ? "text-orange-400"
                            : u.severity_color === "yellow" ? "text-amber-400"
                                : "text-slate-400";
                    const borderColor = u.severity_color === "red" ? "border-red-500/25 hover:border-red-500/40"
                        : u.severity_color === "orange" ? "border-orange-500/25 hover:border-orange-500/40"
                            : u.severity_color === "yellow" ? "border-amber-500/25 hover:border-amber-500/40"
                                : "border-white/[0.1] hover:border-white/[0.2]";
                    const isExp = expanded[`plan_unk_${u.question_key}`] || false;
                    return (
                        <div key={u.question_key} className={`rounded-xl border ${borderColor} bg-white/[0.02] overflow-hidden transition-all duration-200`}>
                            <button
                                onClick={() => setExpanded(prev => ({ ...prev, [`plan_unk_${u.question_key}`]: !prev[`plan_unk_${u.question_key}`] }))}
                                className="w-full flex items-center gap-3 px-4 sm:px-5 py-4 text-left hover:bg-white/[0.03] transition-colors group"
                            >
                                {/* Number badge */}
                                <span className="w-7 h-7 rounded-full bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-xs font-bold text-amber-400 flex-shrink-0">
                                    {idx + 1}
                                </span>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-slate-200">{u.question_text}</p>
                                    <div className="flex items-center gap-2 mt-1">
                                        <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${dotColor}`} />
                                        <p className={`text-xs ${labelColor}`}>{u.severity_label}</p>
                                    </div>
                                </div>
                                {/* CTA visible even when collapsed */}
                                <span className={`hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex-shrink-0 ${isExp
                                    ? "bg-white/[0.06] text-slate-400"
                                    : "bg-fuchsia-500/15 border border-fuchsia-500/30 text-fuchsia-300 group-hover:bg-fuchsia-500/25"
                                    }`}>
                                    {isExp ? "Skrýt" : "Zobrazit postup →"}
                                </span>
                                <svg className={`w-5 h-5 text-slate-400 flex-shrink-0 transition-transform duration-200 sm:hidden ${isExp ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                </svg>
                            </button>
                            {isExp && (
                                <div className="px-4 sm:px-5 pb-5 pt-2 border-t border-white/[0.06]">
                                    {u.checklist && u.checklist.length > 0 && (
                                        <div className="rounded-lg bg-slate-800/50 p-4 mb-4">
                                            <h5 className="text-xs font-semibold text-cyan-400 uppercase tracking-wider mb-3">Jak to zjistit:</h5>
                                            <ul className="space-y-2">
                                                {u.checklist.map((item, cidx) => (
                                                    <li key={cidx} className="flex items-start gap-2.5 text-sm text-slate-200">
                                                        <span className="w-5 h-5 rounded-full bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-[10px] font-bold text-cyan-400 flex-shrink-0 mt-0.5">{cidx + 1}</span>
                                                        <span>{item}</span>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                    <p className="text-xs text-slate-300 mb-4 leading-relaxed">{u.recommendation}</p>
                                    <a
                                        href={`/dotaznik?company_id=${companyId}`}
                                        className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-fuchsia-600 to-purple-600 text-white text-sm font-semibold transition-all hover:shadow-lg hover:shadow-fuchsia-500/25 active:scale-[0.98]"
                                    >
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                                        </svg>
                                        Už vím — změnit odpověď
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


/* ── Tab: Dotazník (odpovědi) ── */
const SECTION_LABELS: Record<string, string> = {
    "O vaší firmě": "🏢 O vaší firmě",
    "Zakázané praktiky": "🚫 Zakázané praktiky",
    "AI nástroje ve firmě": "🤖 AI nástroje ve firmě",
    "Lidské zdroje a zaměstnanci": "👥 Lidské zdroje a zaměstnanci",
    "Finance a rozhodování": "💰 Finance a rozhodování",
    "Zákazníci a komunikace": "💬 Zákazníci a komunikace",
    "Bezpečnost a infrastruktura": "🔒 Bezpečnost a infrastruktura",
    "Ochrana dat": "🛡️ Ochrana dat",
    "AI gramotnost (čl. 4)": "📚 AI gramotnost (čl. 4)",
    "Lidský dohled nad AI": "👁️ Lidský dohled nad AI",
    "Vaše role v AI ekosystému": "🏷️ Vaše role v AI ekosystému",
    "Řízení AI incidentů": "⚡ Řízení AI incidentů",
};

const ANSWER_LABELS: Record<string, { label: string; color: string }> = {
    yes: { label: "Ano", color: "bg-green-500/15 text-green-400 border-green-500/25" },
    no: { label: "Ne", color: "bg-red-500/15 text-red-400 border-red-500/25" },
    unknown: { label: "Nevím", color: "bg-amber-500/15 text-amber-400 border-amber-500/25" },
};

function TabDotaznik({ companyId, questResults, questResultsLoading, setQuestResults, setQuestResultsLoading, hasQuest }: {
    companyId: string;
    questResults: QuestionnaireResultsResponse | null;
    questResultsLoading: boolean;
    setQuestResults: (r: QuestionnaireResultsResponse | null) => void;
    setQuestResultsLoading: (l: boolean) => void;
    hasQuest: boolean;
}) {
    const [showDetails, setShowDetails] = useState(false);

    useEffect(() => {
        if (!companyId || questResults) return;
        setQuestResultsLoading(true);
        getQuestionnaireResults(companyId)
            .then(setQuestResults)
            .catch(() => { /* silent */ })
            .finally(() => setQuestResultsLoading(false));
    }, [companyId]);

    if (!hasQuest) {
        return (
            <div className="text-center py-16">
                <div className="mx-auto mb-4 w-14 h-14 rounded-2xl bg-fuchsia-500/10 border border-fuchsia-500/20 flex items-center justify-center">
                    <svg className="w-7 h-7 text-fuchsia-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                </div>
                <p className="text-white font-semibold text-lg mb-2">Dotazník zatím nebyl dokončen</p>
                <p className="text-slate-400 text-sm mb-6">Po vyplnění dotazníku zde uvidíte přehled vašich odpovědí.</p>
                <a
                    href={`/dotaznik?company_id=${companyId}`}
                    className="inline-flex items-center gap-2 bg-gradient-to-r from-fuchsia-600 to-fuchsia-500 hover:from-fuchsia-500 hover:to-fuchsia-400 text-white font-semibold py-2.5 px-6 rounded-xl transition-all shadow-lg shadow-fuchsia-500/25"
                >
                    📝 Vyplnit dotazník
                </a>
            </div>
        );
    }

    if (questResultsLoading) {
        return (
            <div className="flex items-center justify-center gap-3 py-20">
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-fuchsia-500 border-t-transparent" />
                <span className="text-slate-400">Načítám odpovědi…</span>
            </div>
        );
    }

    if (!questResults) {
        return (
            <div className="text-center py-16">
                <p className="text-slate-400">Nepodařilo se načíst odpovědi.</p>
            </div>
        );
    }

    // Risk breakdown with Czech labels
    const riskLabels: Record<string, { label: string; color: string; bg: string; icon: string }> = {
        high: { label: "Vysoké riziko", color: "text-red-400", bg: "bg-red-500/10 border-red-500/20", icon: "🔴" },
        limited: { label: "Střední riziko", color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20", icon: "🟡" },
        minimal: { label: "Minimální riziko", color: "text-cyan-400", bg: "bg-cyan-500/10 border-cyan-500/20", icon: "🟢" },
    };

    const { risk_breakdown, total_answers, ai_systems_declared, recommendations } = questResults.analysis;

    // Count "no risk" answers (yes answers that aren't in risk breakdown)
    const totalRiskAnswers = Object.values(risk_breakdown).reduce((a, b) => a + b, 0);
    const noRiskCount = total_answers - totalRiskAnswers;

    // Determine overall risk level
    const overallRisk = risk_breakdown.high > 0 ? "high" : risk_breakdown.limited > 0 ? "limited" : "minimal";
    const overallLabel = overallRisk === "high" ? "Vyžaduje pozornost" : overallRisk === "limited" ? "Částečně v souladu" : "V pořádku";
    const overallColor = overallRisk === "high" ? "from-red-600 to-red-500" : overallRisk === "limited" ? "from-amber-600 to-amber-500" : "from-emerald-600 to-emerald-500";

    // Group high-risk recommendations
    const highRiskRecs = (recommendations || []).filter((r: any) => r.risk_level === "high");
    const limitedRiskRecs = (recommendations || []).filter((r: any) => r.risk_level === "limited");

    return (
        <div className="space-y-6">
            {/* Overall status banner */}
            <div className={`bg-gradient-to-r ${overallColor} rounded-2xl p-6 text-white`}>
                <div className="flex items-center gap-4 mb-3">
                    <div className="w-12 h-12 rounded-xl bg-white/20 flex items-center justify-center text-2xl">
                        {overallRisk === "high" ? "⚠️" : overallRisk === "limited" ? "📋" : "✅"}
                    </div>
                    <div>
                        <h3 className="text-xl font-bold">{overallLabel}</h3>
                        <p className="text-white/80 text-sm">Vyhodnoceno {new Date(questResults.submitted_at).toLocaleDateString("cs-CZ")}</p>
                    </div>
                </div>
                <p className="text-white/90 text-sm">
                    Na základě {total_answers} odpovědí jsme identifikovali {ai_systems_declared} AI {ai_systems_declared === 1 ? "systém" : ai_systems_declared < 5 ? "systémy" : "systémů"} ve vaší firmě.
                </p>
            </div>

            {/* Risk breakdown cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {Object.entries(riskLabels).map(([key, meta]) => (
                    <div key={key} className={`${meta.bg} border rounded-xl p-4 text-center`}>
                        <div className="text-2xl mb-1">{meta.icon}</div>
                        <div className={`text-2xl font-bold ${meta.color}`}>{risk_breakdown[key] || 0}</div>
                        <div className="text-slate-400 text-xs mt-1">{meta.label}</div>
                    </div>
                ))}
                <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl p-4 text-center">
                    <div className="text-2xl mb-1">✅</div>
                    <div className="text-2xl font-bold text-emerald-400">{noRiskCount}</div>
                    <div className="text-slate-400 text-xs mt-1">Bez rizika</div>
                </div>
            </div>

            {/* High-risk alerts */}
            {highRiskRecs.length > 0 && (
                <div className="bg-red-500/5 border border-red-500/15 rounded-2xl p-5">
                    <h4 className="text-red-400 font-semibold text-sm mb-3 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                        Vysoce rizikové oblasti ({highRiskRecs.length})
                    </h4>
                    <div className="space-y-2">
                        {highRiskRecs.map((rec: any, i: number) => (
                            <div key={i} className="flex items-start gap-3 bg-white/[0.02] rounded-xl px-4 py-3">
                                <span className="text-red-400 shrink-0 mt-0.5">🔴</span>
                                <div>
                                    <p className="text-slate-300 text-sm">{rec.recommendation}</p>
                                    {rec.ai_act_article && (
                                        <p className="text-slate-500 text-xs mt-1">{rec.ai_act_article}</p>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Limited risk alerts */}
            {limitedRiskRecs.length > 0 && (
                <div className="bg-amber-500/5 border border-amber-500/15 rounded-2xl p-5">
                    <h4 className="text-amber-400 font-semibold text-sm mb-3">
                        Oblasti se středním rizikem ({limitedRiskRecs.length})
                    </h4>
                    <div className="space-y-2">
                        {limitedRiskRecs.map((rec: any, i: number) => (
                            <div key={i} className="flex items-start gap-3 bg-white/[0.02] rounded-xl px-4 py-3">
                                <span className="text-amber-400 shrink-0 mt-0.5">🟡</span>
                                <p className="text-slate-300 text-sm">{rec.recommendation}</p>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Detailed answers toggle */}
            <div className="border-t border-white/[0.06] pt-4">
                <button
                    onClick={() => setShowDetails(!showDetails)}
                    className="flex items-center gap-2 text-sm text-slate-400 hover:text-slate-300 transition-colors"
                >
                    <svg className={`w-4 h-4 transition-transform ${showDetails ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                    {showDetails ? "Skrýt podrobné odpovědi" : "Zobrazit podrobné odpovědi"}
                </button>

                {showDetails && (
                    <div className="mt-4 space-y-2">
                        {questResults.answers.map((ans) => {
                            const ansStyle = ANSWER_LABELS[ans.answer] || { label: ans.answer, color: "bg-slate-500/15 text-slate-400 border-slate-500/25" };
                            return (
                                <div key={ans.question_key} className="flex items-center justify-between gap-3 bg-white/[0.02] rounded-lg px-4 py-2">
                                    <span className="text-slate-400 text-xs truncate">{ans.question_key.replace(/_/g, " ")}</span>
                                    <span className={`inline-flex items-center shrink-0 rounded-lg border px-2 py-0.5 text-xs font-medium ${ansStyle.color}`}>
                                        {ansStyle.label}
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            {/* Action buttons */}
            <div className="flex flex-col sm:flex-row gap-3 pt-2">
                <a
                    href={`/dotaznik?company_id=${companyId}`}
                    className="inline-flex items-center justify-center gap-2 bg-white/[0.05] border border-white/[0.1] hover:bg-white/[0.08] text-white font-medium py-2.5 px-6 rounded-xl transition-all text-sm"
                >
                    ✏️ Upravit odpovědi
                </a>
                <a
                    href={`/dotaznik?company_id=${companyId}`}
                    className="inline-flex items-center justify-center gap-2 text-sm text-fuchsia-400 hover:text-fuchsia-300 transition-colors py-2.5 px-6"
                >
                    🔄 Vyplnit dotazník znovu
                </a>
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
                                ? (scan.total_findings === 0 ? "bg-green-500/10 text-green-400" : "bg-cyan-500/10 text-cyan-400")
                                : scan.status === "running"
                                    ? "bg-amber-500/10 text-amber-400"
                                    : "bg-red-500/10 text-red-400"
                                }`}>
                                {scan.status === "completed" ? (scan.total_findings === 0 ? "Bez nálezů ✓" : "Dokončen") : scan.status === "running" ? "Probíhá" : scan.status}
                            </span>
                            {scan.scan_type === "quick" && (
                                <span className="inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium bg-slate-500/10 text-slate-400">Rychlý</span>
                            )}
                            {scan.deep_scan_status === "running" || scan.deep_scan_status === "pending" ? (
                                <span className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium bg-purple-500/10 text-purple-400">
                                    <span className="relative flex h-1.5 w-1.5"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75" /><span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-purple-500" /></span>
                                    24h scan běží
                                </span>
                            ) : scan.deep_scan_status === "done" || scan.deep_scan_status === "cooldown" ? (
                                <span className="inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium bg-green-500/10 text-green-400">24h scan ✓</span>
                            ) : null}
                        </div>
                        <div className="flex items-center gap-2 sm:gap-4 text-xs text-slate-500 mt-1 flex-wrap">
                            <span>{new Date(scan.created_at).toLocaleDateString("cs-CZ", {
                                day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit"
                            })}</span>
                            <span>{scan.total_findings} {cz(scan.total_findings, 'nález', 'nálezy', 'nálezů')}</span>
                            {(scan.deep_scan_status === "done" || scan.deep_scan_status === "cooldown") && scan.deep_scan_total_findings != null && (
                                <span className="text-green-400">+ {scan.deep_scan_total_findings} z 24h skenu</span>
                            )}
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
    const [passwordAttempts, setPasswordAttempts] = useState(0);
    const [passwordLockUntil, setPasswordLockUntil] = useState(0);

    const meta = user?.user_metadata || {};
    const companyName = meta.company_name || data?.company?.name || "—";
    const ico = meta.ico || "—";
    const webUrl = meta.web_url || data?.company?.url || "—";
    const registeredAt = user?.created_at
        ? new Date(user.created_at).toLocaleDateString("cs-CZ", { day: "numeric", month: "long", year: "numeric" })
        : "—";

    const handlePasswordChange = async (e: React.FormEvent) => {
        e.preventDefault();
        // Anti-bot: throttle after 3 failed attempts (30 sec lock)
        if (Date.now() < passwordLockUntil) {
            const secs = Math.ceil((passwordLockUntil - Date.now()) / 1000);
            setPasswordMsg(`Příliš mnoho pokusů. Zkuste to za ${secs} s.`);
            return;
        }
        if (newPassword !== confirmPassword) { setPasswordMsg("Hesla se neshodují"); return; }
        if (newPassword.length < 8) { setPasswordMsg("Heslo musí mít alespoň 8 znaků"); return; }
        if (!/[A-Z]/.test(newPassword)) { setPasswordMsg("Heslo musí obsahovat alespoň jedno velké písmeno"); return; }
        if (!/[0-9]/.test(newPassword)) { setPasswordMsg("Heslo musí obsahovat alespoň jednu číslici"); return; }
        if (!/[^A-Za-z0-9]/.test(newPassword)) { setPasswordMsg("Heslo musí obsahovat alespoň jeden speciální znak (!@#$%...)"); return; }
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
            const attempts = passwordAttempts + 1;
            setPasswordAttempts(attempts);
            if (attempts >= 3) {
                setPasswordLockUntil(Date.now() + 30000);
                setPasswordAttempts(0);
            }
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

            {data?.invoices && data.invoices.length > 0 && (
                <div className="glass">
                    <h3 className="font-semibold mb-5 flex items-center gap-2">
                        <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        Faktury
                    </h3>
                    <div className="space-y-2">
                        {data.invoices.map((inv: { invoice_number: string; order_number: string; plan: string; amount: number; pdf_url: string; issued_at: string }) => (
                            <div key={inv.invoice_number} className="flex flex-col sm:flex-row sm:items-center justify-between rounded-lg border border-white/[0.06] bg-white/[0.02] px-4 py-3 text-sm gap-2">
                                <div className="flex items-center gap-3">
                                    <span className="text-slate-300 font-medium font-mono text-xs">{inv.invoice_number}</span>
                                    <span className="text-slate-500 text-xs">{inv.plan?.toUpperCase()}</span>
                                </div>
                                <div className="flex items-center gap-4">
                                    <span className="text-slate-400 text-xs">{new Date(inv.issued_at).toLocaleDateString("cs-CZ")}</span>
                                    <span className="text-slate-300 font-medium">{new Intl.NumberFormat("cs-CZ").format(inv.amount)} Kč</span>
                                    {inv.pdf_url && (
                                        <a href={inv.pdf_url} target="_blank" rel="noopener noreferrer"
                                            className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 text-emerald-400 px-3 py-0.5 text-xs font-medium hover:bg-emerald-500/20 transition-colors">
                                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                            </svg>
                                            Stáhnout PDF
                                        </a>
                                    )}
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
                        <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} placeholder="Min. 8 znaků, velké písmeno, číslo, speciální znak" minLength={8} required
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
            "AI Act Compliance Kit (8 dokumentů)",
            "Transparenční stránka (HTML)",
            "Registr AI systémů",
            "Interní AI politika firmy",
            "Školení — prezentace v PowerPointu",
            "Záznamový list o proškolení",
            "Plán řízení AI incidentů",
            "Tištěná dokumentace v profesionální vazbě do 14 dnů",
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
            "Tištěná dokumentace v profesionální vazbě do 14 dnů",
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
            "2 roky měsíčního monitoringu — automatický sken, propsání změn, hlášení a aktualizace dokumentů",
            "Dedikovaný specialista",
            "SLA 4h odezva v pracovní době",
            "Tištěná dokumentace v profesionální vazbě do 14 dnů",
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
    { label: "Compliance Kit (8 dokumentů)", basic: true, pro: true, enterprise: true },
    { label: "Registr AI systémů", basic: true, pro: true, enterprise: true },
    { label: "Transparenční stránka (HTML)", basic: true, pro: true, enterprise: true },
    { label: "Texty oznámení pro AI nástroje", basic: true, pro: true, enterprise: true },
    { label: "Interní AI politika firmy", basic: true, pro: true, enterprise: true },
    { label: "Školení — prezentace v PowerPointu", basic: true, pro: true, enterprise: true },
    { label: "Záznamový list o proškolení", basic: true, pro: true, enterprise: true },
    { label: "Plán řízení AI incidentů", basic: true, pro: true, enterprise: true },
    { label: "Tištěná dokumentace v profesionální vazbě (do 14 dnů)", basic: true, pro: true, enterprise: true },
    { label: "Implementace na váš web na klíč", basic: false, pro: true, enterprise: true },
    { label: "Nastavení transparenční stránky na webu", basic: false, pro: true, enterprise: true },
    { label: "Úprava cookie lišty a chatbot oznámení", basic: false, pro: true, enterprise: true },
    { label: "Podpora po dodání (30 dní)", basic: false, pro: true, enterprise: true },
    { label: "Prioritní zpracování", basic: false, pro: true, enterprise: true },
    { label: "10 hodin konzultací se specialistou", basic: false, pro: false, enterprise: true },
    { label: "Metodická kontrola veškeré dokumentace", basic: false, pro: false, enterprise: true },
    { label: "Rozšířený audit interních AI systémů", basic: false, pro: false, enterprise: true },
    { label: "2 roky měsíčního monitoringu — automatický sken, propsání změn, hlášení a aktualizace", basic: false, pro: false, enterprise: true },
    { label: "Dedikovaný specialista", basic: false, pro: false, enterprise: true },
    { label: "SLA 4h odezva v pracovní době", basic: false, pro: false, enterprise: true },
];

function PricingComparisonTable() {
    const { user } = useAuth();
    const [loading, setLoading] = useState<string | null>(null);

    async function handleCheckout(planKey: string) {
        if (!user) {
            window.location.href = `/registrace?redirect=/objednavka&plan=${planKey}`;
            return;
        }
        window.location.href = `/objednavka?plan=${planKey}`;
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

            {/* ═══ Monitoring cards ═══ */}
            <div className="mt-12" id="monitoring">
                <div className="text-center mb-8">
                    <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/20 bg-cyan-500/5 px-4 py-1.5 text-xs font-medium text-cyan-300 mb-3">
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        Volitelný doplněk
                    </div>
                    <h2 className="text-xl font-bold text-white">
                        Měsíční <span className="neon-text">monitoring</span> webu
                    </h2>
                    <p className="mt-2 text-sm text-slate-400 max-w-xl mx-auto leading-relaxed">
                        AI systémy se na vašem webu mohou objevit kdykoliv — po aktualizaci pluginu,
                        upgradu platformy nebo změně služby třetí strany. Monitoring vás ochrání.
                    </p>
                </div>

                <div className="grid md:grid-cols-2 gap-6">
                    {/* Monitoring */}
                    <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 flex flex-col">
                        <h3 className="text-lg font-bold text-white mb-1">Monitoring</h3>
                        <div className="mb-3">
                            <span className="text-2xl font-extrabold text-white">299</span>
                            <span className="text-slate-500 ml-1">Kč/měsíc</span>
                        </div>
                        <ul className="space-y-2 text-sm mb-6 mt-4">
                            {[
                                "1× měsíčně automatický sken webu",
                                "Srovnání s předchozím skenem (diff)",
                                "Emailové upozornění při nálezu",
                                "Aktualizovaný Compliance Report",
                                "Aktualizovaný Registr AI systémů",
                                "Historie skenů v dashboardu",
                            ].map((f) => (
                                <li key={f} className="flex items-start gap-2">
                                    <svg className="w-4 h-4 mt-0.5 text-cyan-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                    </svg>
                                    <span className="text-slate-300">{f}</span>
                                </li>
                            ))}
                        </ul>
                        <div className="mt-auto text-center">
                            <a
                                href="mailto:info@aishield.cz?subject=Monitoring%20—%20AIshield.cz&body=Mám%20zájem%20o%20měsíční%20monitoring%20webu%20(299%20Kč/měsíc)."
                                className="inline-flex items-center justify-center gap-2 w-full rounded-xl border border-cyan-500/30 bg-cyan-500/10 px-6 py-2.5 text-sm font-semibold text-cyan-300 hover:bg-cyan-500/20 transition"
                            >
                                Sjednat Monitoring
                            </a>
                        </div>
                    </div>

                    {/* Monitoring Plus */}
                    <div className="rounded-2xl border border-fuchsia-500/20 bg-gradient-to-b from-fuchsia-500/[0.06] to-transparent p-6 flex flex-col">
                        <h3 className="text-lg font-bold text-white mb-1">Monitoring Plus</h3>
                        <div className="mb-3">
                            <span className="text-2xl font-extrabold neon-text">599</span>
                            <span className="text-slate-500 ml-1">Kč/měsíc</span>
                        </div>
                        <ul className="space-y-2 text-sm mb-6 mt-4">
                            {[
                                "2× měsíčně automatický sken webu",
                                "Vše z Monitoring",
                                "Aktualizace VŠECH 8 dokumentů",
                                "Implementace změn na webu klienta",
                                "Prioritní emailová podpora",
                                "Čtvrtletní souhrnný přehled",
                            ].map((f) => (
                                <li key={f} className="flex items-start gap-2">
                                    <svg className="w-4 h-4 mt-0.5 text-fuchsia-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                    </svg>
                                    <span className="text-slate-300">{f}</span>
                                </li>
                            ))}
                        </ul>
                        <div className="mt-auto text-center">
                            <a
                                href="mailto:info@aishield.cz?subject=Monitoring%20Plus%20—%20AIshield.cz&body=Mám%20zájem%20o%20Monitoring%20Plus%20(599%20Kč/měsíc)."
                                className="inline-flex items-center justify-center gap-2 w-full rounded-xl bg-fuchsia-600 px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-fuchsia-500/25 hover:bg-fuchsia-500 transition"
                            >
                                Sjednat Monitoring Plus
                            </a>
                        </div>
                    </div>
                </div>

                <div className="mt-4 text-center space-y-1">
                    <p className="text-xs text-slate-500">
                        Monitoring je volitelný doplněk — lze aktivovat pouze po zakoupení balíčku BASIC, PRO nebo ENTERPRISE.
                    </p>
                    <p className="text-xs text-slate-500">
                        Minimální doba: 3 měsíce. Výpověď: 1 měsíc. U balíčku ENTERPRISE je 2 roky monitoringu již v ceně.
                    </p>
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
