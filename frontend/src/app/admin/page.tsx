"use client";

import { useState, useEffect, useCallback } from "react";
import {
    isAdminLoggedIn,
    verifyAdminToken,
    clearAdminToken,
    getCrmDashboardStats,
    getCrmPipeline,
    updateCompanyStatus,
    WORKFLOW_STATUSES,
    PAYMENT_STATUSES,
    PRIORITIES,
    getAdminStats,
    runAdminTask,
    getAdminEmailLog,
    getAdminCompanies,
    getEmailHealth,
    getAdminAlerts,
    getAdminDiffs,
    sendLegislativeAlert,
    getAgencyClients,
    startAgencyBatchScan,
    generateAgencyEmail,
    getClientManagement,
    triggerClientRescan,
    getBusinessOverview,
    getAdminOrders,
    getAdminOrderStats,
    confirmBankPayment,
    getClientQuestionnaire,
    getClientFindings,
    getAnalyticsStats,
    getAnalyticsSessions,
    getAnalyticsEvents,
    getSubscriptions,
    sendSubscriptionReminder,
    getAdminInvoices,
    getLLMUsage,
    checkLLMKeys,
    factoryReset,
    stopAllScans,
    getScanMonitor,
    getScanFindings,
    resendScanReport,
    cancelDeepScan,
    previewScanReport,
    getChatFeedback,
    getChatFeedbackStats,
} from "@/lib/admin-api";
import type {
    CrmDashboardStats,
    PipelineStats,
    CompanyBrief,
    Activity,
    AdminStats,
    EmailHealth,
    AgencyClient,
    ClientManagementData,
    ManagedClient,
    RescanResult,
    BusinessOverview,
    DetailedOrder,
    AdminOrder,
    AdminOrderStats,
    ClientQuestionnaireData,
    ClientFindingsData,
    FindingDetail,
    AnalyticsStats,
    AnalyticsSession,
    AnalyticsEvent,
    SubscriptionInfo,
    ScanMonitorData,
    MonitoredScan,
    ScanFindingsData,
    ScanFinding,
    ChatFeedbackEntry,
    ChatFeedbackStats,
    LLMUsageSummary,
    LLMApiHealth,
} from "@/lib/admin-api";

// ── Local types ──

interface EmailLogEntry {
    id: string;
    company_ico: string;
    to_email: string;
    subject: string;
    variant: string;
    status: string;
    sent_at: string;
    opened_at?: string | null;
    clicked_at?: string | null;
}

interface CompanyEntry {
    id?: string;
    ico: string;
    name: string;
    url: string;
    email: string;
    scan_status: string;
    emails_sent: number;
    created_at: string;
    workflow_status?: string;
    payment_status?: string;
    priority?: string;
    lead_score?: number;
}

interface AlertEntry {
    id: string;
    company_id: string;
    alert_type: string;
    title: string;
    severity: string;
    to_email: string;
    email_sent: boolean;
    created_at: string;
}

interface DiffEntry {
    id: string;
    company_id: string;
    has_changes: boolean;
    added_count: number;
    removed_count: number;
    changed_count: number;
    unchanged_count: number;
    summary: string;
    created_at: string;
}

interface AgencyClientEntry {
    id: string;
    name: string;
    url: string;
    email: string;
    contact_name: string;
    partner: string;
    scan_status: string;
    created_at: string;
}

type Tab =
    | "prehled"
    | "firmy"
    | "pipeline"
    | "emaily"
    | "monitoring"
    | "klienti"
    | "objednavky"
    | "agentura"
    | "nastroje"
    | "analytika"
    | "predplatne"
    | "testy24h"
    | "zpetnavazba"
    | "llm";

const NAV_ITEMS: { id: Tab; icon: string; label: string }[] = [
    { id: "prehled", icon: "📊", label: "Přehled" },
    { id: "testy24h", icon: "🔬", label: "24h Testy" },
    { id: "klienti", icon: "💼", label: "Klienti & Platby" },
    { id: "objednavky", icon: "🧾", label: "Objednávky" },
    { id: "firmy", icon: "🏭", label: "Firmy" },
    { id: "pipeline", icon: "📈", label: "Pipeline" },
    { id: "emaily", icon: "📧", label: "Emaily" },
    { id: "monitoring", icon: "🔔", label: "Monitoring" },
    { id: "agentura", icon: "🤝", label: "Agentura" },
    { id: "nastroje", icon: "⚙️", label: "Nástroje" },
    { id: "analytika", icon: "📉", label: "Analytika" },
    { id: "predplatne", icon: "💳", label: "Předplatné" },
    { id: "zpetnavazba", icon: "💬", label: "Zpětná vazba" },
    { id: "llm", icon: "🧠", label: "LLM API" },
];

const TASKS = [
    { name: "monitoring", label: "🔍 Monitoring", desc: "Skenuj nasmlouvané klienty" },
    { name: "prospecting", label: "🏭 Prospecting", desc: "Shoptet + Heureka + ARES" },
    { name: "scanning", label: "🌐 Skenování", desc: "Skenuj weby → kvalifikace" },
    { name: "find_emails", label: "📧 Hledání emailů", desc: "Najdi kontakty leadů" },
    { name: "emailing", label: "🚀 Email kampaň", desc: "Pošli emaily HOT leadům" },
    { name: "reporting", label: "📊 Reporting", desc: "Měsíční reporty (1. den)" },
];

const CRON_SCHEDULE = [
    { time: "03:00", desc: "Monitoring nasmlouvaných klientů" },
    { time: "04:00", desc: "Prospecting — Shoptet + Heureka + ARES" },
    { time: "05:00", desc: "Skenování webů + kvalifikace leadů" },
    { time: "06:00", desc: "Hledání emailů (Playwright + Vision)" },
    { time: "08:00", desc: "Email kampaň — pouze HOT leady" },
    { time: "20:00", desc: "Měsíční reporty (1. den)" },
];

// ── Format helpers ──

function fmtDate(s: string | null | undefined): string {
    if (!s) return "—";
    try {
        return new Date(s).toLocaleDateString("cs-CZ", { day: "2-digit", month: "2-digit", year: "numeric" });
    } catch {
        return "—";
    }
}

function fmtDateTime(s: string | null | undefined): string {
    if (!s) return "—";
    try {
        return new Date(s).toLocaleString("cs-CZ", {
            day: "2-digit",
            month: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
        });
    } catch {
        return "—";
    }
}

function fmtNum(n: number | null | undefined): string {
    if (n == null) return "0";
    return n.toLocaleString("cs-CZ");
}

function fmtPct(n: number | null | undefined): string {
    if (n == null) return "0%";
    return `${(n * 100).toFixed(1)}%`;
}

function fmtMoney(n: number | null | undefined): string {
    if (n == null) return "0 Kč";
    return `${n.toLocaleString("cs-CZ")} Kč`;
}

// ── Helper components ──

function StatCard({
    label,
    value,
    icon,
    sub,
    accent = "cyan",
}: {
    label: string;
    value: string | number;
    icon: string;
    sub?: string;
    accent?: "cyan" | "fuchsia" | "green" | "yellow" | "red" | "orange";
}) {
    const accentMap: Record<string, string> = {
        cyan: "border-cyan-500/20 group-hover:border-cyan-500/40",
        fuchsia: "border-fuchsia-500/20 group-hover:border-fuchsia-500/40",
        green: "border-green-500/20 group-hover:border-green-500/40",
        yellow: "border-yellow-500/20 group-hover:border-yellow-500/40",
        red: "border-red-500/20 group-hover:border-red-500/40",
        orange: "border-orange-500/20 group-hover:border-orange-500/40",
    };
    const textMap: Record<string, string> = {
        cyan: "text-cyan-400",
        fuchsia: "text-fuchsia-400",
        green: "text-green-400",
        yellow: "text-yellow-400",
        red: "text-red-400",
        orange: "text-orange-400",
    };
    return (
        <div
            className={`group bg-white/5 border ${accentMap[accent]} rounded-xl p-4 transition-all hover:bg-white/[0.07]`}
        >
            <div className="flex items-center justify-between mb-2">
                <span className="text-2xl">{icon}</span>
                <span className={`text-xs font-medium ${textMap[accent]}`}>{label}</span>
            </div>
            <div className="text-2xl font-bold text-white">{value}</div>
            {sub && <div className="text-xs text-gray-500 mt-1">{sub}</div>}
        </div>
    );
}

function StatusBadge({
    status,
    map,
}: {
    status: string | undefined;
    map: Record<string, { label: string; color: string; icon: string }>;
}) {
    const s = status || "new";
    const info = map[s] || { label: s, color: "gray", icon: "•" };
    const colorMap: Record<string, string> = {
        gray: "bg-gray-500/20 text-gray-400 border-gray-500/30",
        blue: "bg-blue-500/20 text-blue-400 border-blue-500/30",
        yellow: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
        cyan: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
        purple: "bg-purple-500/20 text-purple-400 border-purple-500/30",
        indigo: "bg-indigo-500/20 text-indigo-400 border-indigo-500/30",
        green: "bg-green-500/20 text-green-400 border-green-500/30",
        red: "bg-red-500/20 text-red-400 border-red-500/30",
        orange: "bg-orange-500/20 text-orange-400 border-orange-500/30",
    };
    const cls = colorMap[info.color] || colorMap.gray;
    return (
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs border ${cls}`}>
            <span>{info.icon}</span>
            <span>{info.label}</span>
        </span>
    );
}

function ScanBadge({ status }: { status: string | undefined }) {
    const s = status || "unknown";
    const cls =
        s === "scanned"
            ? "bg-green-500/20 text-green-400"
            : s === "pending" || s === "scanning"
                ? "bg-yellow-500/20 text-yellow-400"
                : s === "error"
                    ? "bg-red-500/20 text-red-400"
                    : "bg-gray-500/20 text-gray-400";
    return <span className={`px-2 py-0.5 rounded text-xs ${cls}`}>{s}</span>;
}

function Panel({ children, className = "" }: { children: React.ReactNode; className?: string }) {
    return (
        <div className={`bg-white/5 border border-white/10 rounded-2xl ${className}`}>{children}</div>
    );
}

// ── Main Component ──

export default function AdminPage() {
    // Auth
    const [authed, setAuthed] = useState<boolean | null>(null);
    const [saveToast, setSaveToast] = useState<string | null>(null);
    // Track unsaved inline edits: { [companyId]: { field: newValue } }
    const [dirtyFields, setDirtyFields] = useState<Record<string, Record<string, string>>>({});

    // Navigation
    const [tab, setTab] = useState<Tab>("prehled");

    // Dashboard
    const [crmStats, setCrmStats] = useState<CrmDashboardStats | null>(null);
    const [adminStats, setAdminStats] = useState<AdminStats | null>(null);

    // Companies
    const [companies, setCompanies] = useState<CompanyEntry[]>([]);
    const [companySearch, setCompanySearch] = useState("");
    const [companyWfFilter, setCompanyWfFilter] = useState("all");
    const [companyPayFilter, setCompanyPayFilter] = useState("all");

    // Pipeline
    const [pipeline, setPipeline] = useState<PipelineStats | null>(null);

    // Emails
    const [emails, setEmails] = useState<EmailLogEntry[]>([]);
    const [health, setHealth] = useState<EmailHealth | null>(null);

    // Tasks
    const [runningTask, setRunningTask] = useState<string | null>(null);
    const [taskResult, setTaskResult] = useState<string | null>(null);

    // Monitoring
    const [alerts, setAlerts] = useState<AlertEntry[]>([]);
    const [diffs, setDiffs] = useState<DiffEntry[]>([]);
    const [legTitle, setLegTitle] = useState("");
    const [legBody, setLegBody] = useState("");
    const [legSending, setLegSending] = useState(false);
    const [legResult, setLegResult] = useState<string | null>(null);

    // Agency
    const [agencyClients, setAgencyClients] = useState<AgencyClientEntry[]>([]);
    const [batchInput, setBatchInput] = useState("");
    const [batchRunning, setBatchRunning] = useState(false);
    const [batchResult, setBatchResult] = useState<string | null>(null);
    const [emailPreview, setEmailPreview] = useState<{ subject: string; body: string } | null>(null);

    // Business overview
    const [bizOverview, setBizOverview] = useState<BusinessOverview | null>(null);
    const [revenueMode, setRevenueMode] = useState<"day" | "week" | "month">("day");
    const [autoRefresh, setAutoRefresh] = useState(false);

    // Client management
    const [clientData, setClientData] = useState<ClientManagementData | null>(null);
    const [clientSearch, setClientSearch] = useState("");
    const [clientFilter, setClientFilter] = useState<"all" | "subscription" | "one_time" | "needs_rescan" | "overdue">("all");
    const [rescanning, setRescanning] = useState<string | null>(null);
    const [rescanResult, setRescanResult] = useState<RescanResult | null>(null);
    const [expandedClient, setExpandedClient] = useState<string | null>(null);
    const [clientDetailTab, setClientDetailTab] = useState<"overview" | "questionnaire" | "findings">("overview");
    const [clientQuestionnaire, setClientQuestionnaire] = useState<ClientQuestionnaireData | null>(null);
    const [clientFindings, setClientFindings] = useState<ClientFindingsData | null>(null);
    const [loadingDetail, setLoadingDetail] = useState(false);

    // Tools
    const [toolResult, setToolResult] = useState<string | null>(null);

    // Orders
    const [adminOrders, setAdminOrders] = useState<AdminOrder[]>([]);
    const [orderStats, setOrderStats] = useState<AdminOrderStats | null>(null);
    const [orderFilter, setOrderFilter] = useState<"all" | "PAID" | "AWAITING_PAYMENT" | "EXPIRED">("all");
    const [orderGwFilter, setOrderGwFilter] = useState<"all" | "stripe" | "bank_transfer">("all");
    const [confirmingOrder, setConfirmingOrder] = useState<string | null>(null);

    // Analytics
    const [analyticsStats, setAnalyticsStats] = useState<AnalyticsStats | null>(null);
    const [analyticsSessions, setAnalyticsSessions] = useState<AnalyticsSession[]>([]);
    const [analyticsEvents, setAnalyticsEvents] = useState<AnalyticsEvent[]>([]);
    const [analyticsLoading, setAnalyticsLoading] = useState(false);
    const [analyticsDays, setAnalyticsDays] = useState(30);
    const [analyticsEventFilter, setAnalyticsEventFilter] = useState("");
    const [analyticsTab, setAnalyticsTab] = useState<"funnel" | "events" | "sessions" | "questionnaire">("funnel");

    // Subscriptions
    const [subscriptions, setSubscriptions] = useState<SubscriptionInfo[]>([]);
    const [subscriptionsLoading, setSubscriptionsLoading] = useState(false);
    const [reminderSending, setReminderSending] = useState<string | null>(null);
    const [subscriptionFilter, setSubscriptionFilter] = useState<"all" | "active" | "overdue" | "cancelled">("all");

    // Invoices
    const [adminInvoices, setAdminInvoices] = useState<import("@/lib/admin-api").AdminInvoice[]>([]);
    const [invoicesLoading, setInvoicesLoading] = useState(false);

    // 24h Test Monitor
    const [scanMonitor, setScanMonitor] = useState<ScanMonitorData | null>(null);
    const [scanMonitorLoading, setScanMonitorLoading] = useState(false);
    const [expandedScan, setExpandedScan] = useState<string | null>(null);
    const [scanFindings, setScanFindings] = useState<ScanFindingsData | null>(null);
    const [scanFindingsLoading, setScanFindingsLoading] = useState(false);
    const [resendingScan, setResendingScan] = useState<string | null>(null);
    const [resendResult, setResendResult] = useState<string | null>(null);

    // Chat Feedback
    const [chatFeedback, setChatFeedback] = useState<ChatFeedbackEntry[]>([]);
    const [chatFeedbackStats, setChatFeedbackStats] = useState<ChatFeedbackStats | null>(null);
    const [feedbackLoading, setFeedbackLoading] = useState(false);
    const [feedbackFilter, setFeedbackFilter] = useState<string>("all");

    // LLM Usage
    const [llmUsage, setLlmUsage] = useState<LLMUsageSummary | null>(null);
    const [llmLoading, setLlmLoading] = useState(false);
    const [llmCheckingKeys, setLlmCheckingKeys] = useState(false);

    // Loading
    const [loading, setLoading] = useState(true);
    const [loadError, setLoadError] = useState<string | null>(null);

    // ── Auth check — ověření tokenu proti backendu ──
    useEffect(() => {
        const verify = async () => {
            if (!isAdminLoggedIn()) {
                window.location.href = "/admin/login";
                return;
            }
            const valid = await verifyAdminToken();
            if (!valid) {
                window.location.href = "/admin/login";
                return;
            }
            setAuthed(true);
        };
        verify();
    }, []);

    // ── Data loaders ──

    const loadDashboard = useCallback(async () => {
        try {
            const [crm, admin, h, biz] = await Promise.all([
                getCrmDashboardStats().catch(() => null),
                getAdminStats().catch(() => null),
                getEmailHealth().catch(() => null),
                getBusinessOverview().catch(() => null),
            ]);
            if (crm) setCrmStats(crm);
            if (admin) setAdminStats(admin);
            if (h) setHealth(h);
            if (biz) setBizOverview(biz);
        } catch (e) {
            console.error("Dashboard load error:", e);
            setLoadError(`Dashboard: ${e}`);
        }
    }, []);

    const loadCompanies = useCallback(async () => {
        try {
            const d = await getAdminCompanies("all", 500);
            setCompanies(d.companies || []);
        } catch (e) {
            console.error("Companies load error:", e);
            setLoadError(`Firmy: ${e}`);
        }
    }, []);

    const loadPipeline = useCallback(async () => {
        try {
            const d = await getCrmPipeline();
            setPipeline(d);
        } catch (e) {
            console.error("Pipeline load error:", e);
            setLoadError(`Pipeline: ${e}`);
        }
    }, []);

    const loadEmails = useCallback(async () => {
        try {
            const el = await getAdminEmailLog(200);
            setEmails(el.emails || []);
            // health is already loaded by loadDashboard — no duplicate call
        } catch (e) {
            console.error("Emails load error:", e);
            setLoadError(`Emaily: ${e}`);
        }
    }, []);

    const loadMonitoring = useCallback(async () => {
        try {
            const [a, d] = await Promise.all([getAdminAlerts(50), getAdminDiffs(50)]);
            setAlerts(a.alerts || []);
            setDiffs(d.diffs || []);
        } catch (e) {
            console.error("Monitoring load error:", e);
            setLoadError(`Monitoring: ${e}`);
        }
    }, []);

    const loadAgency = useCallback(async () => {
        try {
            const d = await getAgencyClients();
            setAgencyClients(d.clients || []);
        } catch (e) {
            console.error("Agency load error:", e);
            setLoadError(`Agentura: ${e}`);
        }
    }, []);

    const loadClientManagement = useCallback(async () => {
        try {
            const d = await getClientManagement();
            setClientData(d);
        } catch (e) {
            console.error("Client management load error:", e);
            setLoadError(`Klienti: ${e}`);
        }
    }, []);

    const loadOrders = useCallback(async () => {
        try {
            const [orders, stats] = await Promise.all([
                getAdminOrders(),
                getAdminOrderStats(),
            ]);
            setAdminOrders(orders);
            setOrderStats(stats);
        } catch (e) {
            console.error("Orders load error:", e);
            setLoadError(`Objednávky: ${e}`);
        }
    }, []);

    const loadAnalytics = useCallback(async () => {
        setAnalyticsLoading(true);
        try {
            const [stats, sess, evts] = await Promise.all([
                getAnalyticsStats(analyticsDays),
                getAnalyticsSessions(50),
                getAnalyticsEvents(200),
            ]);
            setAnalyticsStats(stats);
            setAnalyticsSessions(sess.sessions || []);
            setAnalyticsEvents(evts.events || []);
        } catch (e) {
            console.error("Analytics load error:", e);
            setLoadError(`Analytika: ${e}`);
        } finally {
            setAnalyticsLoading(false);
        }
    }, [analyticsDays]);

    const loadSubscriptions = useCallback(async () => {
        setSubscriptionsLoading(true);
        try {
            const d = await getSubscriptions();
            setSubscriptions(d.subscriptions || []);
        } catch (e) {
            console.error("Subscriptions load error:", e);
            setLoadError(`Předplatné: ${e}`);
        } finally {
            setSubscriptionsLoading(false);
        }
    }, []);

    const loadInvoices = useCallback(async () => {
        setInvoicesLoading(true);
        try {
            const d = await getAdminInvoices();
            setAdminInvoices(d.invoices || []);
        } catch (e) {
            console.error("Invoices load error:", e);
            setLoadError(`Faktury: ${e}`);
        } finally {
            setInvoicesLoading(false);
        }
    }, []);

    const loadScanMonitor = useCallback(async () => {
        setScanMonitorLoading(true);
        try {
            const d = await getScanMonitor();
            setScanMonitor(d);
        } catch (e) {
            console.error("Scan monitor load error:", e);
            setLoadError(`24h Testy: ${e}`);
        } finally {
            setScanMonitorLoading(false);
        }
    }, []);

    const loadChatFeedback = useCallback(async () => {
        setFeedbackLoading(true);
        try {
            const [fb, stats] = await Promise.all([
                getChatFeedback(100, feedbackFilter === "all" ? undefined : feedbackFilter),
                getChatFeedbackStats(),
            ]);
            setChatFeedback(fb.feedback || []);
            setChatFeedbackStats(stats);
        } catch (e) {
            console.error("Chat feedback load error:", e);
            setLoadError(`Zpětná vazba: ${e}`);
        } finally {
            setFeedbackLoading(false);
        }
    }, [feedbackFilter]);

    const loadLLMUsage = useCallback(async () => {
        setLlmLoading(true);
        try {
            const d = await getLLMUsage();
            setLlmUsage(d);
        } catch (e) {
            console.error("LLM usage load error:", e);
            setLoadError(`LLM API: ${e}`);
        } finally {
            setLlmLoading(false);
        }
    }, []);

    const handleCheckKeys = useCallback(async () => {
        setLlmCheckingKeys(true);
        try {
            const health = await checkLLMKeys();
            setLlmUsage(prev => prev ? { ...prev, api_health: health } : prev);
        } catch (e) {
            console.error("LLM key check error:", e);
        } finally {
            setLlmCheckingKeys(false);
        }
    }, []);

    // ── Initial load ──
    useEffect(() => {
        if (!authed) return;
        setLoading(true);
        loadDashboard().finally(() => setLoading(false));
    }, [authed, loadDashboard]);

    // Auto-refresh every 60s
    useEffect(() => {
        if (!autoRefresh || !authed) return;
        const interval = setInterval(() => {
            if (tab === "prehled") loadDashboard();
        }, 60000);
        return () => clearInterval(interval);
    }, [autoRefresh, authed, tab, loadDashboard]);

    // ── Tab data load ──
    useEffect(() => {
        if (!authed) return;
        if (tab === "firmy") loadCompanies();
        if (tab === "pipeline") loadPipeline();
        if (tab === "emaily") loadEmails();
        if (tab === "monitoring") loadMonitoring();
        if (tab === "agentura") loadAgency();
        if (tab === "klienti") loadClientManagement();
        if (tab === "objednavky") { loadOrders(); loadInvoices(); }
        if (tab === "analytika") loadAnalytics();
        if (tab === "predplatne") loadSubscriptions();
        if (tab === "testy24h") loadScanMonitor();
        if (tab === "zpetnavazba") loadChatFeedback();
        if (tab === "llm") loadLLMUsage();
    }, [tab, authed, loadCompanies, loadPipeline, loadEmails, loadMonitoring, loadAgency, loadClientManagement, loadOrders, loadAnalytics, loadSubscriptions, loadInvoices, loadScanMonitor, loadChatFeedback, loadLLMUsage]);

    // Reload feedback when filter changes
    useEffect(() => {
        if (!authed || tab !== "zpetnavazba") return;
        loadChatFeedback();
    }, [feedbackFilter, authed, tab, loadChatFeedback]);

    // ── Task runner ──
    const handleRunTask = useCallback(
        async (taskName: string) => {
            setRunningTask(taskName);
            setTaskResult(null);
            try {
                const result = await runAdminTask(taskName);
                setTaskResult(JSON.stringify(result, null, 2));
                await loadDashboard();
            } catch (e) {
                setTaskResult(`❌ Chyba: ${e}`);
            } finally {
                setRunningTask(null);
            }
        },
        [loadDashboard]
    );

    // ── Inline status change ──
    const handleStatusChange = useCallback(
        async (companyId: string, field: string, value: string) => {
            try {
                await updateCompanyStatus(companyId, { [field]: value });
                await loadCompanies();
                setSaveToast("✅ Uloženo");
                setTimeout(() => setSaveToast(null), 2500);
            } catch {
                setSaveToast("❌ Chyba při ukládání");
                setTimeout(() => setSaveToast(null), 3000);
            }
        },
        [loadCompanies]
    );

    // ── Stage a field change (don't save yet — wait for explicit save button) ──
    const stageFieldChange = useCallback(
        (companyId: string, field: string, value: string, originalValue: string) => {
            setDirtyFields((prev) => {
                const companyDirty = { ...(prev[companyId] || {}), [field]: value };
                // If value matches original, remove that field from dirty
                if (value === originalValue) {
                    delete companyDirty[field];
                }
                // If no dirty fields left for this company, remove entry
                if (Object.keys(companyDirty).length === 0) {
                    const next = { ...prev };
                    delete next[companyId];
                    return next;
                }
                return { ...prev, [companyId]: companyDirty };
            });
        },
        []
    );

    // ── Save staged changes for a company ──
    const saveStagedChanges = useCallback(
        async (companyId: string) => {
            const fields = dirtyFields[companyId];
            if (!fields) return;
            try {
                await updateCompanyStatus(companyId, fields);
                setDirtyFields((prev) => {
                    const next = { ...prev };
                    delete next[companyId];
                    return next;
                });
                await loadCompanies();
                setSaveToast("✅ Uloženo");
                setTimeout(() => setSaveToast(null), 2500);
            } catch {
                setSaveToast("❌ Chyba při ukládání");
                setTimeout(() => setSaveToast(null), 3000);
            }
        },
        [dirtyFields, loadCompanies]
    );

    // ── Logout ──
    const handleLogout = useCallback(() => {
        clearAdminToken();
        window.location.href = "/admin/login";
    }, []);

    // ── Filtered companies ──
    const filteredCompanies = companies.filter((c) => {
        const q = companySearch.toLowerCase();
        const matchSearch =
            !q ||
            (c.name || "").toLowerCase().includes(q) ||
            (c.url || "").toLowerCase().includes(q) ||
            (c.email || "").toLowerCase().includes(q) ||
            (c.ico || "").toLowerCase().includes(q);
        const matchWf = companyWfFilter === "all" || (c as any).workflow_status === companyWfFilter;
        const matchPay = companyPayFilter === "all" || (c as any).payment_status === companyPayFilter;
        return matchSearch && matchWf && matchPay;
    });

    // ── Guard / Loading ──

    if (authed === null || loading) {
        return (
            <div className="min-h-screen bg-[#0f172a] flex items-center justify-center">
                <div className="text-center">
                    <div className="text-5xl mb-4 animate-bounce">🛡️</div>
                    <div className="text-cyan-400 text-lg animate-pulse">Načítám admin panel…</div>
                </div>
            </div>
        );
    }

    // ── Pipeline funnel bar helper ──
    function FunnelBar({
        label,
        count,
        total,
        color,
    }: {
        label: string;
        count: number;
        total: number;
        color: string;
    }) {
        const pct = total > 0 ? (count / total) * 100 : 0;
        const colorMap: Record<string, string> = {
            gray: "bg-gray-500",
            blue: "bg-blue-500",
            yellow: "bg-yellow-500",
            cyan: "bg-cyan-500",
            purple: "bg-purple-500",
            indigo: "bg-indigo-500",
            green: "bg-green-500",
            red: "bg-red-500",
            orange: "bg-orange-500",
        };
        return (
            <div className="flex items-center gap-3">
                <div className="w-40 text-sm text-gray-300 truncate">{label}</div>
                <div className="flex-1 bg-white/5 rounded-full h-6 overflow-hidden">
                    <div
                        className={`h-full rounded-full ${colorMap[color] || "bg-cyan-500"} transition-all duration-700`}
                        style={{ width: `${Math.max(pct, 2)}%` }}
                    />
                </div>
                <div className="w-16 text-right text-sm font-mono text-white">{count}</div>
                <div className="w-14 text-right text-xs text-gray-500">{pct.toFixed(1)}%</div>
            </div>
        );
    }

    // ══════════════════════════════════════════
    //  RENDER
    // ══════════════════════════════════════════

    return (
        <div className="min-h-screen bg-[#0f172a] text-white flex">
            {/* ── Sidebar ── */}
            <aside className="w-[260px] min-h-screen bg-black/40 border-r border-white/10 flex flex-col sticky top-0 h-screen">
                {/* Logo */}
                <div className="px-5 py-5 border-b border-white/10">
                    <div className="flex items-center gap-3">
                        <span className="text-3xl">🛡️</span>
                        <div>
                            <div className="font-bold text-lg text-white">AIshield</div>
                            <div className="text-xs text-gray-500">Administrátorský panel</div>
                        </div>
                    </div>
                </div>

                {/* Navigation */}
                <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
                    {NAV_ITEMS.map((item) => (
                        <button
                            key={item.id}
                            onClick={() => setTab(item.id)}
                            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${tab === item.id
                                ? "bg-gradient-to-r from-cyan-500/20 to-fuchsia-500/20 text-white border border-cyan-500/30"
                                : "text-gray-400 hover:text-white hover:bg-white/5"
                                }`}
                        >
                            <span className="text-lg">{item.icon}</span>
                            <span>{item.label}</span>
                        </button>
                    ))}
                </nav>

                {/* Quick stats mini */}
                {adminStats && (
                    <div className="px-4 py-3 border-t border-white/10 space-y-1">
                        <div className="flex justify-between text-xs">
                            <span className="text-gray-500">Firmy</span>
                            <span className="text-cyan-400 font-medium">{adminStats.companies_total}</span>
                        </div>
                        <div className="flex justify-between text-xs">
                            <span className="text-gray-500">Emaily dnes</span>
                            <span className="text-fuchsia-400 font-medium">{adminStats.emails_today}</span>
                        </div>
                        <div className="flex justify-between text-xs">
                            <span className="text-gray-500">Konverze</span>
                            <span className="text-green-400 font-medium">{adminStats.conversion_pct}%</span>
                        </div>
                    </div>
                )}

                {/* User + logout */}
                <div className="px-4 py-4 border-t border-white/10">
                    <div className="flex items-center gap-3 mb-3">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-fuchsia-500 flex items-center justify-center text-xs font-bold">
                            A
                        </div>
                        <div>
                            <div className="text-sm font-medium text-white">Admin</div>
                            <div className="text-xs text-gray-500">admin@aishield.cz</div>
                        </div>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="w-full px-3 py-2 rounded-lg text-xs text-gray-400 hover:text-red-400 hover:bg-red-500/10 border border-white/10 transition-all"
                    >
                        🚪 Odhlásit se
                    </button>
                </div>
            </aside>

            {/* ── Main Content ── */}
            <main className="flex-1 min-h-screen overflow-y-auto">
                {/* Top bar */}
                <div className="sticky top-0 z-10 bg-[#0f172a]/80 backdrop-blur-xl border-b border-white/10 px-8 py-4 flex items-center justify-between">
                    <div>
                        <h1 className="text-xl font-bold flex items-center gap-2">
                            <span>
                                {NAV_ITEMS.find((n) => n.id === tab)?.icon}{" "}
                                {NAV_ITEMS.find((n) => n.id === tab)?.label}
                            </span>
                        </h1>
                    </div>
                    <div className="flex items-center gap-3">
                        <a
                            href="/"
                            className="text-xs text-gray-400 hover:text-cyan-400 transition-colors"
                        >
                            ← Zpět na web
                        </a>
                        {tab === "prehled" && (
                            <button
                                onClick={() => setAutoRefresh(!autoRefresh)}
                                className={`px-3 py-1.5 rounded-lg text-xs border transition-all ${autoRefresh ? "bg-green-500/20 border-green-500/30 text-green-400" : "bg-white/5 border-white/10 text-gray-400 hover:text-white hover:bg-white/10"}`}
                            >
                                {autoRefresh ? "⏸ Auto 60s" : "▶ Auto-refresh"}
                            </button>
                        )}
                        <button
                            onClick={() => {
                                if (tab === "prehled") loadDashboard();
                                if (tab === "firmy") loadCompanies();
                                if (tab === "pipeline") loadPipeline();
                                if (tab === "emaily") loadEmails();
                                if (tab === "monitoring") loadMonitoring();
                                if (tab === "agentura") loadAgency();
                                if (tab === "klienti") loadClientManagement();
                                if (tab === "objednavky") { loadOrders(); loadInvoices(); }
                                if (tab === "analytika") loadAnalytics();
                                if (tab === "predplatne") loadSubscriptions();
                                if (tab === "nastroje") loadDashboard();
                                if (tab === "testy24h") loadScanMonitor();
                                if (tab === "zpetnavazba") loadChatFeedback();
                            }}
                            className="px-3 py-1.5 rounded-lg text-xs bg-white/5 border border-white/10 text-gray-400 hover:text-white hover:bg-white/10 transition-all"
                        >
                            🔄 Obnovit
                        </button>
                    </div>
                </div>

                <div className="px-8 py-6 space-y-6">
                    {/* Error banner */}
                    {loadError && (
                        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <span className="text-red-400 text-lg">⚠️</span>
                                <div>
                                    <div className="text-red-400 font-medium text-sm">Chyba při načítání dat</div>
                                    <div className="text-red-300/70 text-xs mt-0.5">{loadError}</div>
                                </div>
                            </div>
                            <button onClick={() => setLoadError(null)} className="text-red-400/60 hover:text-red-400 text-sm">✕</button>
                        </div>
                    )}
                    {/* ══════════════════════════════════════════ */}
                    {/*  TAB: Přehled (Dashboard)                 */}
                    {/* ══════════════════════════════════════════ */}
                    {tab === "prehled" && (
                        <>
                            {/* ═══ SEKCE 1: HLAVNÍ KPI ═══ */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-4">
                                <StatCard icon="💰" label="Tržby celkem" value={fmtMoney(bizOverview?.revenue?.total ?? crmStats?.orders?.paid_amount ?? 0)} accent="green" />
                                <StatCard icon="📈" label="Tržby tento měsíc" value={fmtMoney(bizOverview?.revenue?.this_month ?? 0)} accent="green" />
                                <StatCard icon="🛒" label="Objednávky" value={`${bizOverview?.orders?.breakdown?.paid ?? 0} / ${bizOverview?.orders?.breakdown?.total ?? crmStats?.orders?.total ?? 0}`} sub="zaplaceno / celkem" accent="cyan" />
                                <StatCard icon="🔁" label="Předplatné (MRR)" value={fmtMoney(bizOverview?.subscriptions?.monthly_recurring_revenue ?? 0)} sub={`${bizOverview?.subscriptions?.active ?? 0} aktivních`} accent="fuchsia" />
                                <StatCard icon="✅" label="Doručeno" value={fmtNum(bizOverview?.fulfillment?.delivered ?? 0)} accent="green" />
                                <StatCard icon="🚨" label="Po deadline" value={fmtNum(bizOverview?.fulfillment?.overdue ?? 0)} accent="red" />
                                <StatCard icon="👥" label="Aktivní zákazníci" value={fmtNum(bizOverview?.health?.active_customers ?? 0)} accent="cyan" />
                                <StatCard icon="📉" label="Churn (30d)" value={`${((bizOverview?.health?.churn_rate ?? 0) * 100).toFixed(1)}%`} sub={`${bizOverview?.health?.cancelled_last_30d ?? 0} zrušeno`} accent={((bizOverview?.health?.churn_rate ?? 0) > 0.05) ? "red" : "green"} />
                            </div>

                            {/* ═══ SEKCE 2: REVENUE GRAF ═══ */}
                            {bizOverview?.revenue?.chart && bizOverview.revenue.chart.length > 0 && (
                                <Panel className="p-6">
                                    <div className="flex items-center justify-between mb-4">
                                        <h2 className="text-lg font-semibold text-green-400">📊 Tržby (časový graf)</h2>
                                        <div className="flex gap-1">
                                            {(["day", "week", "month"] as const).map(m => (
                                                <button key={m} onClick={() => setRevenueMode(m)} className={`px-3 py-1 rounded text-xs font-medium transition-all ${revenueMode === m ? "bg-green-500/20 text-green-400 border border-green-500/30" : "text-gray-500 hover:text-gray-300"}`}>
                                                    {m === "day" ? "Den" : m === "week" ? "Týden" : "Měsíc"}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                    <div className="h-48 flex items-end gap-1">
                                        {(() => {
                                            const raw = bizOverview.revenue.chart;
                                            // Aggregate by mode
                                            let chart = raw;
                                            if (revenueMode === "week" || revenueMode === "month") {
                                                const grouped: Record<string, number> = {};
                                                for (const p of raw) {
                                                    const d = new Date(p.date);
                                                    const key = revenueMode === "week"
                                                        ? (() => { const mon = new Date(d); mon.setDate(d.getDate() - d.getDay() + 1); return mon.toISOString().slice(0, 10); })()
                                                        : p.date.slice(0, 7);
                                                    grouped[key] = (grouped[key] || 0) + p.amount;
                                                }
                                                chart = Object.entries(grouped).sort(([a], [b]) => a.localeCompare(b)).map(([date, amount]) => ({ date, amount }));
                                            }
                                            const maxVal = Math.max(...chart.map(c => c.amount), 1);
                                            return chart.map((point, i) => (
                                                <div key={i} className="flex-1 flex flex-col items-center gap-1 group relative">
                                                    <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-black/80 px-2 py-1 rounded text-xs text-white opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                                                        {fmtMoney(point.amount)} — {point.date}
                                                    </div>
                                                    <div
                                                        className="w-full bg-gradient-to-t from-green-600 to-green-400 rounded-t transition-all hover:from-green-500 hover:to-green-300"
                                                        style={{ height: `${Math.max((point.amount / maxVal) * 100, 4)}%`, minHeight: "4px" }}
                                                    />
                                                    {i % Math.max(1, Math.floor(chart.length / 8)) === 0 && (
                                                        <span className="text-[9px] text-gray-500 -rotate-45 origin-top-left mt-1">{revenueMode === "month" ? point.date : point.date.slice(5)}</span>
                                                    )}
                                                </div>
                                            ));
                                        })()}
                                    </div>
                                    <div className="flex flex-wrap justify-between mt-4 text-sm gap-2">
                                        <span className="text-gray-400">🟢 Zaplaceno: <strong className="text-green-400">{fmtMoney(bizOverview.revenue.total)}</strong></span>
                                        <span className="text-gray-400">🟡 Čeká na platbu: <strong className="text-yellow-400">{fmtMoney(bizOverview.revenue.pending)}</strong></span>
                                        <span className="text-gray-400">🔴 Refundováno: <strong className="text-red-400">{fmtMoney(bizOverview.revenue.refunded)}</strong></span>
                                    </div>
                                </Panel>
                            )}

                            {/* ═══ SEKCE 3: KONVERZNÍ FUNNEL ═══ */}
                            {bizOverview?.funnel && (
                                <Panel className="p-6">
                                    <h2 className="text-lg font-semibold text-fuchsia-400 mb-4">🎯 Konverzní funnel</h2>
                                    <div className="space-y-3">
                                        {[
                                            { label: "🏭 Firmy v databázi", count: bizOverview.funnel.total_companies, color: "gray" },
                                            { label: "🔍 Naskenovano", count: bizOverview.funnel.scanned, color: "blue" },
                                            { label: "📝 Dotazník vyplněn", count: bizOverview.funnel.questionnaire_filled, color: "purple" },
                                            { label: "🛒 Objednáno", count: bizOverview.funnel.ordered, color: "yellow" },
                                            { label: "💳 Zaplaceno", count: bizOverview.funnel.paid, color: "green" },
                                            { label: "📦 Doku. doručeny", count: bizOverview.funnel.documents_delivered, color: "cyan" },
                                        ].map(step => (
                                            <FunnelBar key={step.label} label={step.label} count={step.count} total={bizOverview.funnel.total_companies || 1} color={step.color} />
                                        ))}
                                    </div>
                                </Panel>
                            )}

                            {/* ═══ SEKCE 4: FULFILLMENT & DEADLINE TRACKER ═══ */}
                            {bizOverview?.orders?.detailed && (() => {
                                const paidOrders = bizOverview.orders.detailed.filter((o: DetailedOrder) => o.fulfillment !== "not_paid");
                                const overdue = paidOrders.filter((o: DetailedOrder) => o.deadline_status === "overdue");
                                const warning = paidOrders.filter((o: DetailedOrder) => o.deadline_status === "warning");
                                const pending = paidOrders.filter((o: DetailedOrder) => o.fulfillment === "pending" && o.deadline_status === "ok");
                                const urgentOrders = [...overdue, ...warning, ...pending].slice(0, 20);
                                return urgentOrders.length > 0 ? (
                                    <Panel className="p-6">
                                        <h2 className="text-lg font-semibold text-orange-400 mb-2">⏰ Plnění & Deadliny</h2>
                                        <p className="text-xs text-gray-500 mb-4">Objednávky, které ještě nebyly plně doručeny (SLA: 7 pracovních dnů od platby, bez víkendů a CZ svátků)</p>
                                        <div className="overflow-x-auto">
                                            <table className="w-full text-sm">
                                                <thead>
                                                    <tr className="text-left text-gray-500 border-b border-white/10">
                                                        <th className="pb-2">Zákazník</th>
                                                        <th className="pb-2">Balíček</th>
                                                        <th className="pb-2">Částka</th>
                                                        <th className="pb-2">Zaplaceno</th>
                                                        <th className="pb-2">Dnů od platby</th>
                                                        <th className="pb-2">Zbývá</th>
                                                        <th className="pb-2">Stav</th>
                                                    </tr>
                                                </thead>
                                                <tbody className="divide-y divide-white/5">
                                                    {urgentOrders.map((o: DetailedOrder) => (
                                                        <tr key={o.id} className={`${o.deadline_status === "overdue" ? "bg-red-500/5" : o.deadline_status === "warning" ? "bg-yellow-500/5" : ""}`}>
                                                            <td className="py-2">
                                                                <div className="text-white font-medium">{o.company_name || o.email}</div>
                                                                <div className="text-xs text-gray-500">{o.email}</div>
                                                            </td>
                                                            <td className="py-2">
                                                                <span className={`px-2 py-0.5 rounded text-xs font-medium ${o.plan === "enterprise" ? "bg-purple-500/20 text-purple-400" : o.plan === "pro" ? "bg-cyan-500/20 text-cyan-400" : "bg-blue-500/20 text-blue-400"}`}>
                                                                    {(o.plan || "").toUpperCase()}
                                                                </span>
                                                            </td>
                                                            <td className="py-2 text-green-400 font-medium">{fmtMoney(o.amount)}</td>
                                                            <td className="py-2 text-gray-300">{o.paid_at ? fmtDate(o.paid_at) : "—"}</td>
                                                            <td className="py-2 text-gray-300">{o.days_since_payment}d</td>
                                                            <td className="py-2">
                                                                {o.days_remaining !== null ? (
                                                                    <span className={`font-bold ${o.deadline_status === "overdue" ? "text-red-400" : o.deadline_status === "warning" ? "text-yellow-400" : "text-green-400"}`}>
                                                                        {o.deadline_status === "overdue" ? `❗ ${Math.abs(o.days_remaining || 0)}d po DL` : `${o.days_remaining}d`}
                                                                    </span>
                                                                ) : <span className="text-gray-500">—</span>}
                                                            </td>
                                                            <td className="py-2">
                                                                {o.fulfillment === "delivered" ? <span className="text-green-400">✅ Doručeno</span>
                                                                    : o.fulfillment === "subscription" ? <span className="text-cyan-400">🔁 Předplatné</span>
                                                                        : <span className="text-yellow-400">⏳ Čeká ({o.docs_count}/7 doc{o.has_scan ? ", sken ✅" : ", sken ❌"})</span>}
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </Panel>
                                ) : null;
                            })()}

                            {/* ═══ SEKCE 5: OBJEDNÁVKY PO BALÍČCÍCH (donut) ═══ */}
                            {bizOverview?.orders?.by_plan && (
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                                    <Panel className="p-6">
                                        <h2 className="text-lg font-semibold text-cyan-400 mb-4">📦 Objednávky podle balíčků</h2>
                                        <div className="space-y-3">
                                            {Object.entries(bizOverview.orders.by_plan).map(([plan, data]) => (
                                                <div key={plan} className="flex items-center justify-between p-3 bg-black/20 rounded-xl">
                                                    <div className="flex items-center gap-3">
                                                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${plan === "enterprise" ? "bg-purple-500/20 text-purple-400" : plan === "pro" ? "bg-cyan-500/20 text-cyan-400" : plan.includes("monitoring") ? "bg-orange-500/20 text-orange-400" : "bg-blue-500/20 text-blue-400"}`}>
                                                            {plan.toUpperCase()}
                                                        </span>
                                                        <span className="text-gray-400 text-sm">{data.count}x objednáno, {data.paid}x zaplaceno</span>
                                                    </div>
                                                    <span className="text-green-400 font-bold">{fmtMoney(data.revenue)}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </Panel>

                                    <Panel className="p-6">
                                        <h2 className="text-lg font-semibold text-cyan-400 mb-4">💳 Podle typu platby</h2>
                                        <div className="space-y-3">
                                            {Object.entries(bizOverview.orders.by_type).map(([type, data]) => (
                                                <div key={type} className="flex items-center justify-between p-3 bg-black/20 rounded-xl">
                                                    <div className="flex items-center gap-3">
                                                        <span className="text-lg">{type === "one_time" ? "🛒" : type === "subscription" ? "🔁" : "💵"}</span>
                                                        <span className="text-white font-medium">{type === "one_time" ? "Jednorázové" : type === "subscription" ? "Předplatné" : type === "subscription_recurrence" ? "Opakovaná platba" : type}</span>
                                                        <span className="text-gray-500 text-sm">{data.count}x, {data.paid}x zaplaceno</span>
                                                    </div>
                                                    <span className="text-green-400 font-bold">{fmtMoney(data.revenue)}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </Panel>
                                </div>
                            )}

                            {/* ═══ SEKCE 6: OUTREACH STATISTIKY ═══ */}
                            {bizOverview?.outreach && (
                                <Panel className="p-6">
                                    <h2 className="text-lg font-semibold text-fuchsia-400 mb-4">📡 Outreach (email kampaně)</h2>
                                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4 mb-4">
                                        <div className="bg-black/20 rounded-xl p-3 text-center">
                                            <div className="text-2xl font-bold text-white">{fmtNum(bizOverview.outreach.total_in_database)}</div>
                                            <div className="text-xs text-gray-500">Firem v DB</div>
                                        </div>
                                        <div className="bg-black/20 rounded-xl p-3 text-center">
                                            <div className="text-2xl font-bold text-fuchsia-400">{fmtNum(bizOverview.outreach.emailed)}</div>
                                            <div className="text-xs text-gray-500">Osloveno</div>
                                        </div>
                                        <div className="bg-black/20 rounded-xl p-3 text-center">
                                            <div className="text-2xl font-bold text-cyan-400">{fmtNum(bizOverview.outreach.emails_sent_total)}</div>
                                            <div className="text-xs text-gray-500">Emailů odesláno</div>
                                        </div>
                                        <div className="bg-black/20 rounded-xl p-3 text-center">
                                            <div className="text-2xl font-bold text-green-400">{fmtNum(bizOverview.outreach.emails_delivered)}</div>
                                            <div className="text-xs text-gray-500">Doručeno</div>
                                        </div>
                                        <div className="bg-black/20 rounded-xl p-3 text-center">
                                            <div className="text-2xl font-bold text-yellow-400">{fmtNum(bizOverview.outreach.emails_opened)}</div>
                                            <div className="text-xs text-gray-500">Otevřeno ({(bizOverview.outreach.open_rate * 100).toFixed(1)}%)</div>
                                        </div>
                                        <div className="bg-black/20 rounded-xl p-3 text-center">
                                            <div className="text-2xl font-bold text-orange-400">{fmtNum(bizOverview.outreach.emails_clicked)}</div>
                                            <div className="text-xs text-gray-500">Proklik ({(bizOverview.outreach.click_rate * 100).toFixed(1)}%)</div>
                                        </div>
                                    </div>
                                    {/* Outreach funnel bar */}
                                    <div className="space-y-2">
                                        {[
                                            { label: "Osloveno emailem", val: bizOverview.outreach.emailed, color: "fuchsia" },
                                            { label: "Email doručen", val: bizOverview.outreach.emails_delivered, color: "cyan" },
                                            { label: "Email otevřen", val: bizOverview.outreach.emails_opened, color: "yellow" },
                                            { label: "Proklik na web", val: bizOverview.outreach.emails_clicked, color: "orange" },
                                        ].map(s => (
                                            <FunnelBar key={s.label} label={s.label} count={s.val} total={bizOverview.outreach.emailed || 1} color={s.color} />
                                        ))}
                                    </div>
                                </Panel>
                            )}

                            {/* ═══ SEKCE 7: SKENY ═══ */}
                            {bizOverview?.scans && (
                                <Panel className="p-6">
                                    <h2 className="text-lg font-semibold text-yellow-400 mb-4">🔍 Skeny</h2>
                                    <div className="grid grid-cols-3 gap-4 mb-4">
                                        <div className="bg-black/20 rounded-xl p-3 text-center">
                                            <div className="text-2xl font-bold text-white">{fmtNum(bizOverview.scans.total)}</div>
                                            <div className="text-xs text-gray-500">Celkem</div>
                                        </div>
                                        <div className="bg-black/20 rounded-xl p-3 text-center">
                                            <div className="text-2xl font-bold text-green-400">{fmtNum(bizOverview.scans.done)}</div>
                                            <div className="text-xs text-gray-500">Hotovo</div>
                                        </div>
                                        <div className="bg-black/20 rounded-xl p-3 text-center">
                                            <div className="text-2xl font-bold text-red-400">{fmtNum(bizOverview.scans.error)}</div>
                                            <div className="text-xs text-gray-500">Chyby</div>
                                        </div>
                                    </div>
                                    {Object.entries(bizOverview.scans.by_trigger).length > 0 && (
                                        <div className="space-y-2">
                                            <div className="text-xs text-gray-500 uppercase tracking-wider">Podle zdroje</div>
                                            {Object.entries(bizOverview.scans.by_trigger).map(([trigger, count]) => (
                                                <div key={trigger} className="flex justify-between text-sm">
                                                    <span className="text-gray-300">{trigger}</span>
                                                    <span className="text-white font-medium">{count}x</span>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </Panel>
                            )}

                            {/* ═══ SEKCE 8: POSLEDNÍ UDÁLOSTI ═══ */}
                            {bizOverview?.recent_events && bizOverview.recent_events.length > 0 && (
                                <Panel className="p-6">
                                    <h2 className="text-lg font-semibold text-cyan-400 mb-4">📝 Poslední události</h2>
                                    <div className="space-y-2 max-h-96 overflow-y-auto">
                                        {bizOverview.recent_events.map((ev, i) => (
                                            <div key={i} className={`flex items-center gap-3 p-3 rounded-xl ${ev.status === "PAID" ? "bg-green-500/5 border border-green-500/10" : ev.status === "active" ? "bg-cyan-500/5 border border-cyan-500/10" : "bg-black/20"}`}>
                                                <span className="text-lg">{ev.type === "order" ? "🛒" : "🔁"}</span>
                                                <div className="flex-1 min-w-0">
                                                    <span className="text-sm text-white font-medium">{ev.email}</span>
                                                    <span className="text-xs text-gray-400 ml-2">{ev.detail}</span>
                                                </div>
                                                <span className="text-xs text-gray-500 whitespace-nowrap">{fmtDateTime(ev.date)}</span>
                                            </div>
                                        ))}
                                    </div>
                                </Panel>
                            )}

                            {/* ═══ SEKCE 9: POTŘEBUJE POZORNOST ═══ */}
                            {crmStats?.needing_attention && crmStats.needing_attention.length > 0 && (
                                <Panel className="p-6">
                                    <h2 className="text-lg font-semibold text-red-400 mb-4">
                                        🔥 Vyžaduje pozornost ({crmStats.needing_attention.length})
                                    </h2>
                                    <div className="space-y-2">
                                        {crmStats.needing_attention.map((c: CompanyBrief) => (
                                            <div
                                                key={c.id}
                                                className="flex items-center justify-between p-3 bg-red-500/5 border border-red-500/10 rounded-xl hover:bg-red-500/10 transition-all"
                                            >
                                                <div>
                                                    <span className="font-medium text-white">{c.name}</span>
                                                    <span className="text-gray-500 text-sm ml-3">{c.url}</span>
                                                </div>
                                                <div className="flex items-center gap-3">
                                                    <StatusBadge status={c.workflow_status} map={WORKFLOW_STATUSES} />
                                                    {c.next_action && <span className="text-xs text-yellow-400">📌 {c.next_action}</span>}
                                                    {c.next_action_at && <span className="text-xs text-red-400">⏰ {fmtDate(c.next_action_at)}</span>}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </Panel>
                            )}

                        </>
                    )}

                    {/* ══════════════════════════════════════════ */}
                    {/*  TAB: Firmy (Companies)                   */}
                    {/* ══════════════════════════════════════════ */}
                    {tab === "firmy" && (
                        <>
                            {/* Save toast */}
                            {saveToast && (
                                <div className="fixed top-6 right-6 z-50 bg-gray-900 border border-cyan-500/30 rounded-xl px-5 py-3 text-sm text-white shadow-lg shadow-cyan-500/10 animate-pulse">
                                    {saveToast}
                                </div>
                            )}
                            {/* Filters */}
                            <div className="flex flex-wrap gap-3">
                                <input
                                    type="text"
                                    placeholder="🔍 Hledat firma, URL, email, IČO…"
                                    value={companySearch}
                                    onChange={(e) => setCompanySearch(e.target.value)}
                                    className="flex-1 min-w-[250px] bg-black/30 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-gray-500 focus:border-cyan-500/50 focus:outline-none focus:ring-1 focus:ring-cyan-500/30 transition-all text-sm"
                                />
                                <select
                                    value={companyWfFilter}
                                    onChange={(e) => setCompanyWfFilter(e.target.value)}
                                    className="bg-black/30 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-gray-300 focus:border-cyan-500/50 focus:outline-none"
                                >
                                    <option value="all">Všechny stavy</option>
                                    {Object.entries(WORKFLOW_STATUSES).map(([k, v]) => (
                                        <option key={k} value={k}>
                                            {v.icon} {v.label}
                                        </option>
                                    ))}
                                </select>
                                <select
                                    value={companyPayFilter}
                                    onChange={(e) => setCompanyPayFilter(e.target.value)}
                                    className="bg-black/30 border border-white/10 rounded-xl px-3 py-2.5 text-sm text-gray-300 focus:border-cyan-500/50 focus:outline-none"
                                >
                                    <option value="all">Všechny platby</option>
                                    {Object.entries(PAYMENT_STATUSES).map(([k, v]) => (
                                        <option key={k} value={k}>
                                            {v.icon} {v.label}
                                        </option>
                                    ))}
                                </select>
                                <div className="flex items-center text-xs text-gray-500">
                                    {filteredCompanies.length} / {companies.length} firem
                                </div>
                            </div>

                            {/* Table */}
                            <Panel className="overflow-hidden">
                                <div>
                                    <table className="w-full text-sm table-fixed">
                                        <thead className="bg-white/5">
                                            <tr>
                                                <th className="text-left p-3 text-gray-400 font-medium w-[18%]">Název</th>
                                                <th className="text-left p-3 text-gray-400 font-medium w-[15%]">URL</th>
                                                <th className="text-left p-3 text-gray-400 font-medium w-[16%]">Email</th>
                                                <th className="text-left p-3 text-gray-400 font-medium w-[13%]">Stav</th>
                                                <th className="text-left p-3 text-gray-400 font-medium w-[13%]">Platba</th>
                                                <th className="text-left p-3 text-gray-400 font-medium w-[9%]">Priorita</th>
                                                <th className="text-left p-3 text-gray-400 font-medium w-[4%]">📧</th>
                                                <th className="text-left p-3 text-gray-400 font-medium w-[4%]">📊</th>
                                                <th className="text-left p-3 text-gray-400 font-medium w-[8%]"></th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {filteredCompanies.length === 0 ? (
                                                <tr>
                                                    <td colSpan={9} className="p-12 text-center text-gray-500">
                                                        {companies.length === 0
                                                            ? "Zatím žádné firmy"
                                                            : "Žádné firmy neodpovídají filtru"}
                                                    </td>
                                                </tr>
                                            ) : (
                                                filteredCompanies.map((c) => {
                                                    const cid = (c as any).id || c.ico;
                                                    const isDirty = !!dirtyFields[cid];
                                                    const wfValue = dirtyFields[cid]?.workflow_status ?? (c as any).workflow_status;
                                                    const payValue = dirtyFields[cid]?.payment_status ?? (c as any).payment_status;
                                                    return (
                                                        <tr
                                                            key={cid}
                                                            onClick={() =>
                                                                (window.location.href = `/admin/company/${cid}`)
                                                            }
                                                            className={`border-t border-white/5 hover:bg-white/5 cursor-pointer transition-colors ${isDirty ? "bg-cyan-500/[0.04]" : ""}`}
                                                        >
                                                            <td className="p-3 text-white font-medium truncate overflow-hidden">
                                                                {c.name || "—"}
                                                            </td>
                                                            <td className="p-3 text-cyan-400 text-xs truncate overflow-hidden">
                                                                {c.url || "—"}
                                                            </td>
                                                            <td className="p-3 text-gray-300 text-xs truncate overflow-hidden">
                                                                {c.email || "—"}
                                                            </td>
                                                            <td className="p-3" onClick={(e) => e.stopPropagation()}>
                                                                {(c as any).workflow_status ? (
                                                                    <select
                                                                        value={wfValue || "new"}
                                                                        onChange={(e) =>
                                                                            stageFieldChange(cid, "workflow_status", e.target.value, (c as any).workflow_status || "new")
                                                                        }
                                                                        className={`bg-transparent border rounded px-1 py-0.5 text-xs text-gray-300 focus:outline-none focus:border-cyan-500/50 ${dirtyFields[cid]?.workflow_status ? "border-cyan-500/50 ring-1 ring-cyan-500/30" : "border-white/10"}`}
                                                                    >
                                                                        {Object.entries(WORKFLOW_STATUSES).map(([k, v]) => (
                                                                            <option key={k} value={k}>
                                                                                {v.icon} {v.label}
                                                                            </option>
                                                                        ))}
                                                                    </select>
                                                                ) : (
                                                                    <ScanBadge status={c.scan_status} />
                                                                )}
                                                            </td>
                                                            <td className="p-3" onClick={(e) => e.stopPropagation()}>
                                                                {(c as any).payment_status ? (
                                                                    <select
                                                                        value={payValue || "none"}
                                                                        onChange={(e) =>
                                                                            stageFieldChange(cid, "payment_status", e.target.value, (c as any).payment_status || "none")
                                                                        }
                                                                        className={`bg-transparent border rounded px-1 py-0.5 text-xs text-gray-300 focus:outline-none focus:border-cyan-500/50 ${dirtyFields[cid]?.payment_status ? "border-cyan-500/50 ring-1 ring-cyan-500/30" : "border-white/10"}`}
                                                                    >
                                                                        {Object.entries(PAYMENT_STATUSES).map(([k, v]) => (
                                                                            <option key={k} value={k}>
                                                                                {v.icon} {v.label}
                                                                            </option>
                                                                        ))}
                                                                    </select>
                                                                ) : (
                                                                    <span className="text-gray-500 text-xs">—</span>
                                                                )}
                                                            </td>
                                                            <td className="p-3">
                                                                {(c as any).priority ? (
                                                                    <StatusBadge
                                                                        status={(c as any).priority}
                                                                        map={PRIORITIES}
                                                                    />
                                                                ) : (
                                                                    <span className="text-gray-500 text-xs">—</span>
                                                                )}
                                                            </td>
                                                            <td className="p-3 text-gray-400 text-center">
                                                                {c.emails_sent || 0}
                                                            </td>
                                                            <td className="p-3">
                                                                {(c as any).lead_score != null ? (
                                                                    <span
                                                                        className={`font-mono text-sm font-bold ${(c as any).lead_score >= 80
                                                                            ? "text-green-400"
                                                                            : (c as any).lead_score >= 50
                                                                                ? "text-yellow-400"
                                                                                : "text-gray-400"
                                                                            }`}
                                                                    >
                                                                        {(c as any).lead_score}
                                                                    </span>
                                                                ) : (
                                                                    <span className="text-gray-500 text-xs">—</span>
                                                                )}
                                                            </td>
                                                            <td className="p-3" onClick={(e) => e.stopPropagation()}>
                                                                {isDirty ? (
                                                                    <button
                                                                        onClick={() => saveStagedChanges(cid)}
                                                                        className="px-3 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-black text-xs font-bold transition-all shadow-lg shadow-cyan-500/25 animate-pulse"
                                                                    >
                                                                        💾 Uložit
                                                                    </button>
                                                                ) : null}
                                                            </td>
                                                        </tr>
                                                    );
                                                })
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </Panel>
                        </>
                    )}

                    {/* ══════════════════════════════════════════ */}
                    {/*  TAB: Pipeline                            */}
                    {/* ══════════════════════════════════════════ */}
                    {tab === "pipeline" && (
                        <>
                            {pipeline ? (
                                <>
                                    {/* Workflow funnel */}
                                    <Panel className="p-6">
                                        <h2 className="text-lg font-semibold text-cyan-400 mb-5">
                                            🔄 Stavový přehled
                                        </h2>
                                        <div className="space-y-3">
                                            {Object.entries(WORKFLOW_STATUSES).map(([key, info]) => (
                                                <FunnelBar
                                                    key={key}
                                                    label={`${info.icon} ${info.label}`}
                                                    count={pipeline.by_workflow_status[key] || 0}
                                                    total={pipeline.total_companies}
                                                    color={info.color}
                                                />
                                            ))}
                                        </div>
                                        <div className="mt-4 pt-4 border-t border-white/10 text-sm text-gray-400">
                                            Celkem: <span className="text-white font-semibold">{pipeline.total_companies}</span> firem
                                        </div>
                                    </Panel>

                                    {/* Stav plateb */}
                                    <Panel className="p-6">
                                        <h2 className="text-lg font-semibold text-fuchsia-400 mb-5">
                                            💳 Stav plateb
                                        </h2>
                                        <div className="space-y-3">
                                            {Object.entries(PAYMENT_STATUSES).map(([key, info]) => (
                                                <FunnelBar
                                                    key={key}
                                                    label={`${info.icon} ${info.label}`}
                                                    count={pipeline.by_payment_status[key] || 0}
                                                    total={pipeline.total_companies}
                                                    color={info.color}
                                                />
                                            ))}
                                        </div>
                                    </Panel>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        {/* Revenue */}
                                        <Panel className="p-6">
                                            <h2 className="text-lg font-semibold text-green-400 mb-4">💰 Tržby</h2>
                                            <div className="space-y-4">
                                                <div>
                                                    <div className="text-xs text-gray-500">Celkový počet objednávek</div>
                                                    <div className="text-2xl font-bold text-white">
                                                        {pipeline.revenue.total_orders}
                                                    </div>
                                                </div>
                                                <div>
                                                    <div className="text-xs text-gray-500">Zaplaceno</div>
                                                    <div className="text-2xl font-bold text-green-400">
                                                        {fmtMoney(pipeline.revenue.paid_amount)}
                                                    </div>
                                                </div>
                                                <div>
                                                    <div className="text-xs text-gray-500">Čeká na platbu</div>
                                                    <div className="text-xl font-bold text-yellow-400">
                                                        {fmtMoney(pipeline.revenue.pending_amount)}
                                                    </div>
                                                </div>
                                            </div>
                                        </Panel>

                                        {/* Priority distribution */}
                                        <Panel className="p-6">
                                            <h2 className="text-lg font-semibold text-orange-400 mb-4">
                                                🎯 Distribuce priorit
                                            </h2>
                                            <div className="space-y-3">
                                                {Object.entries(PRIORITIES).map(([key, info]) => (
                                                    <FunnelBar
                                                        key={key}
                                                        label={`${info.icon} ${info.label}`}
                                                        count={pipeline.by_priority[key] || 0}
                                                        total={pipeline.total_companies}
                                                        color={info.color}
                                                    />
                                                ))}
                                            </div>
                                        </Panel>
                                    </div>
                                </>
                            ) : (
                                <div className="text-center text-gray-500 py-12">
                                    <div className="text-4xl mb-3">📈</div>
                                    <div>Načítám pipeline data…</div>
                                </div>
                            )}
                        </>
                    )}

                    {/* ══════════════════════════════════════════ */}
                    {/*  TAB: Emaily                              */}
                    {/* ══════════════════════════════════════════ */}
                    {tab === "emaily" && (
                        <>
                            {/* Email Health */}
                            {health && (
                                <Panel className="p-6">
                                    <div className="flex items-center justify-between mb-4">
                                        <h2 className="text-lg font-semibold text-cyan-400">
                                            🛡️ Doručitelnost emailů
                                        </h2>
                                        <span
                                            className={`px-3 py-1 rounded-full text-xs font-medium border ${health.mode === "stopped"
                                                ? "bg-red-500/20 text-red-400 border-red-500/30"
                                                : health.mode === "braking"
                                                    ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
                                                    : health.mode === "accelerating"
                                                        ? "bg-green-500/20 text-green-400 border-green-500/30"
                                                        : health.mode === "startup"
                                                            ? "bg-fuchsia-500/20 text-fuchsia-400 border-fuchsia-500/30"
                                                            : "bg-cyan-500/20 text-cyan-400 border-cyan-500/30"
                                                }`}
                                        >
                                            {health.mode === "stopped"
                                                ? "🚨 ZASTAVENO"
                                                : health.mode === "braking"
                                                    ? "⚠️ BRZDA"
                                                    : health.mode === "accelerating"
                                                        ? "🚀 ZRYCHLUJE"
                                                        : health.mode === "startup"
                                                            ? "🏁 START"
                                                            : "✈️ CRUISE"}
                                        </span>
                                    </div>
                                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4">
                                        <div className="bg-black/30 rounded-xl p-3">
                                            <div className="text-xs text-gray-400">Adaptivní limit</div>
                                            <div className="text-xl font-bold text-cyan-400">
                                                {health.sent_today} / {health.daily_limit}
                                            </div>
                                            <div className="w-full bg-white/10 rounded-full h-1.5 mt-1">
                                                <div
                                                    className="bg-cyan-500 h-1.5 rounded-full"
                                                    style={{
                                                        width: `${health.daily_limit > 0
                                                            ? Math.min(100, (health.sent_today / health.daily_limit) * 100)
                                                            : 0
                                                            }%`,
                                                    }}
                                                />
                                            </div>
                                        </div>
                                        <div className="bg-black/30 rounded-xl p-3">
                                            <div className="text-xs text-gray-400">Bounce rate (7d)</div>
                                            <div
                                                className={`text-xl font-bold ${health.bounce_rate * 100 > 5
                                                    ? "text-red-400"
                                                    : health.bounce_rate * 100 > 2
                                                        ? "text-yellow-400"
                                                        : "text-green-400"
                                                    }`}
                                            >
                                                {(health.bounce_rate * 100).toFixed(1)}%
                                            </div>
                                            <div className="text-xs text-gray-500">
                                                {health.bounced_7d} z {health.sent_7d}
                                            </div>
                                        </div>
                                        <div className="bg-black/30 rounded-xl p-3">
                                            <div className="text-xs text-gray-400">Spam rate (7d)</div>
                                            <div
                                                className={`text-xl font-bold ${health.complaint_rate * 100 > 0.1
                                                    ? "text-red-400"
                                                    : health.complaint_rate * 100 > 0.05
                                                        ? "text-yellow-400"
                                                        : "text-green-400"
                                                    }`}
                                            >
                                                {(health.complaint_rate * 100).toFixed(2)}%
                                            </div>
                                            <div className="text-xs text-gray-500">{health.complained_7d} stížností</div>
                                        </div>
                                        <div className="bg-black/30 rounded-xl p-3">
                                            <div className="text-xs text-gray-400">Open rate (7d)</div>
                                            <div
                                                className={`text-xl font-bold ${health.open_rate * 100 > 20
                                                    ? "text-green-400"
                                                    : health.open_rate * 100 > 10
                                                        ? "text-cyan-400"
                                                        : "text-gray-400"
                                                    }`}
                                            >
                                                {(health.open_rate * 100).toFixed(0)}%
                                            </div>
                                            <div className="text-xs text-gray-500">{health.opened_7d} otevřeno</div>
                                        </div>
                                        <div className="bg-black/30 rounded-xl p-3">
                                            <div className="text-xs text-gray-400">Stav systému</div>
                                            <div className="flex items-center gap-2 mt-1">
                                                <span
                                                    className={`w-2.5 h-2.5 rounded-full ${health.is_healthy ? "bg-green-400" : "bg-red-400"
                                                        }`}
                                                />
                                                <span
                                                    className={`text-sm font-medium ${health.is_healthy ? "text-green-400" : "text-red-400"
                                                        }`}
                                                >
                                                    {health.is_healthy ? "Zdravý" : "Problém"}
                                                </span>
                                            </div>
                                            <div className="text-xs text-gray-500 mt-1">
                                                Den {health.days_active} · BL: {health.blacklisted_count}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="bg-black/20 rounded-lg px-4 py-2 mb-3 text-sm text-gray-300">
                                        {health.adjustment_reason}
                                    </div>
                                    {health.warnings.length > 0 && (
                                        <div className="space-y-1">
                                            {health.warnings.map((w, i) => (
                                                <div
                                                    key={i}
                                                    className={`text-xs rounded-lg px-3 py-2 ${w.includes("STOP") || w.includes("KRITICKÉ")
                                                        ? "text-red-400 bg-red-500/10 border border-red-500/20"
                                                        : w.includes("⚠️")
                                                            ? "text-yellow-400 bg-yellow-500/10 border border-yellow-500/20"
                                                            : w.includes("🚀")
                                                                ? "text-green-400 bg-green-500/10 border border-green-500/20"
                                                                : "text-cyan-400 bg-cyan-500/10 border border-cyan-500/20"
                                                        }`}
                                                >
                                                    {w}
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </Panel>
                            )}

                            {/* Email log table */}
                            <Panel className="overflow-hidden">
                                <div className="p-4 border-b border-white/10 flex items-center justify-between">
                                    <h2 className="text-lg font-semibold text-cyan-400">
                                        📧 Historie emailů ({emails.length})
                                    </h2>
                                </div>
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead className="bg-white/5">
                                            <tr>
                                                <th className="text-left p-3 text-gray-400">Čas</th>
                                                <th className="text-left p-3 text-gray-400">Příjemce</th>
                                                <th className="text-left p-3 text-gray-400">Předmět</th>
                                                <th className="text-left p-3 text-gray-400">Varianta</th>
                                                <th className="text-left p-3 text-gray-400">Status</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {emails.length === 0 ? (
                                                <tr>
                                                    <td colSpan={5} className="p-12 text-center text-gray-500">
                                                        Zatím žádné emaily
                                                    </td>
                                                </tr>
                                            ) : (
                                                emails.map((e) => (
                                                    <tr
                                                        key={e.id}
                                                        className="border-t border-white/5 hover:bg-white/5"
                                                    >
                                                        <td className="p-3 text-gray-400 whitespace-nowrap text-xs">
                                                            {fmtDateTime(e.sent_at)}
                                                        </td>
                                                        <td className="p-3 text-cyan-400 text-xs">{e.to_email}</td>
                                                        <td className="p-3 text-gray-300 truncate max-w-xs text-xs">
                                                            {e.subject}
                                                        </td>
                                                        <td className="p-3">
                                                            <span className="px-2 py-0.5 rounded bg-fuchsia-500/20 text-fuchsia-400 text-xs">
                                                                {e.variant}
                                                            </span>
                                                        </td>
                                                        <td className="p-3">
                                                            <span
                                                                className={`px-2 py-0.5 rounded text-xs ${e.status === "sent"
                                                                    ? "bg-green-500/20 text-green-400"
                                                                    : e.status === "opened"
                                                                        ? "bg-cyan-500/20 text-cyan-400"
                                                                        : e.status === "clicked"
                                                                            ? "bg-fuchsia-500/20 text-fuchsia-400"
                                                                            : e.status === "bounced"
                                                                                ? "bg-red-500/20 text-red-400"
                                                                                : e.status === "dry_run"
                                                                                    ? "bg-yellow-500/20 text-yellow-400"
                                                                                    : "bg-gray-500/20 text-gray-400"
                                                                    }`}
                                                            >
                                                                {e.status}
                                                            </span>
                                                        </td>
                                                    </tr>
                                                ))
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </Panel>
                        </>
                    )}

                    {/* TAB Úlohy odstraněn — obsah přesunut do Nástroje */}

                    {/* ══════════════════════════════════════════ */}
                    {/*  TAB: Monitoring                          */}
                    {/* ══════════════════════════════════════════ */}
                    {tab === "monitoring" && (
                        <>
                            {/* Legislative alert sender */}
                            <Panel className="p-6">
                                <h2 className="text-lg font-semibold text-cyan-400 mb-2">
                                    📢 Legislativní upozornění
                                </h2>
                                <p className="text-sm text-gray-400 mb-4">
                                    Odeslat upozornění VŠEM placeným klientům (např. změna AI Act)
                                </p>
                                <div className="space-y-3">
                                    <input
                                        type="text"
                                        placeholder="Titulek upozornění…"
                                        value={legTitle}
                                        onChange={(e) => setLegTitle(e.target.value)}
                                        className="w-full bg-black/30 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-gray-500 focus:border-fuchsia-500/50 focus:outline-none text-sm"
                                    />
                                    <textarea
                                        placeholder="Text upozornění…"
                                        value={legBody}
                                        onChange={(e) => setLegBody(e.target.value)}
                                        rows={4}
                                        className="w-full bg-black/30 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-gray-500 focus:border-fuchsia-500/50 focus:outline-none resize-none text-sm"
                                    />
                                    <div className="flex items-center gap-4">
                                        <button
                                            onClick={async () => {
                                                if (!legTitle || !legBody) return;
                                                setLegSending(true);
                                                setLegResult(null);
                                                try {
                                                    const r = await sendLegislativeAlert(legTitle, legBody);
                                                    setLegResult(`✅ Odesláno ${(r as any).sent_count} klientům`);
                                                    setLegTitle("");
                                                    setLegBody("");
                                                } catch (e) {
                                                    setLegResult(`❌ Chyba: ${e}`);
                                                } finally {
                                                    setLegSending(false);
                                                }
                                            }}
                                            disabled={legSending || !legTitle || !legBody}
                                            className="px-6 py-2.5 bg-gradient-to-r from-fuchsia-500/20 to-cyan-500/20 text-fuchsia-400 border border-fuchsia-500/30 rounded-xl hover:from-fuchsia-500/30 hover:to-cyan-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
                                        >
                                            {legSending ? "⏳ Odesílám…" : "🚀 Odeslat všem klientům"}
                                        </button>
                                        {legResult && (
                                            <span className="text-sm text-gray-300">{legResult}</span>
                                        )}
                                    </div>
                                </div>
                            </Panel>

                            {/* Alerts table */}
                            <Panel className="overflow-hidden">
                                <div className="p-4 border-b border-white/10">
                                    <h2 className="text-lg font-semibold text-cyan-400">
                                        🔔 Poslední alerty ({alerts.length})
                                    </h2>
                                </div>
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead className="bg-white/5">
                                            <tr>
                                                <th className="text-left p-3 text-gray-400">Čas</th>
                                                <th className="text-left p-3 text-gray-400">Typ</th>
                                                <th className="text-left p-3 text-gray-400">Závažnost</th>
                                                <th className="text-left p-3 text-gray-400">Titulek</th>
                                                <th className="text-left p-3 text-gray-400">Email</th>
                                                <th className="text-left p-3 text-gray-400">Odesláno</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {alerts.length === 0 ? (
                                                <tr>
                                                    <td colSpan={6} className="p-12 text-center text-gray-500">
                                                        Zatím žádné alerty
                                                    </td>
                                                </tr>
                                            ) : (
                                                alerts.map((a) => (
                                                    <tr key={a.id} className="border-t border-white/5 hover:bg-white/5">
                                                        <td className="p-3 text-gray-400 whitespace-nowrap text-xs">
                                                            {fmtDateTime(a.created_at)}
                                                        </td>
                                                        <td className="p-3">
                                                            <span className="px-2 py-0.5 rounded text-xs bg-fuchsia-500/20 text-fuchsia-400">
                                                                {a.alert_type}
                                                            </span>
                                                        </td>
                                                        <td className="p-3">
                                                            <span
                                                                className={`px-2 py-0.5 rounded text-xs ${a.severity === "critical"
                                                                    ? "bg-red-500/20 text-red-400"
                                                                    : a.severity === "high"
                                                                        ? "bg-orange-500/20 text-orange-400"
                                                                        : a.severity === "medium"
                                                                            ? "bg-yellow-500/20 text-yellow-400"
                                                                            : "bg-cyan-500/20 text-cyan-400"
                                                                    }`}
                                                            >
                                                                {a.severity}
                                                            </span>
                                                        </td>
                                                        <td className="p-3 text-gray-300 truncate max-w-xs text-xs">
                                                            {a.title}
                                                        </td>
                                                        <td className="p-3 text-cyan-400 text-xs">{a.to_email}</td>
                                                        <td className="p-3">
                                                            {a.email_sent ? (
                                                                <span className="text-green-400">✅</span>
                                                            ) : (
                                                                <span className="text-gray-500">—</span>
                                                            )}
                                                        </td>
                                                    </tr>
                                                ))
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </Panel>

                            {/* Diffs table */}
                            <Panel className="overflow-hidden">
                                <div className="p-4 border-b border-white/10">
                                    <h2 className="text-lg font-semibold text-cyan-400">
                                        🔄 Změny ve skenech ({diffs.length})
                                    </h2>
                                </div>
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead className="bg-white/5">
                                            <tr>
                                                <th className="text-left p-3 text-gray-400">Čas</th>
                                                <th className="text-left p-3 text-gray-400">Firma</th>
                                                <th className="text-left p-3 text-gray-400">Přidáno</th>
                                                <th className="text-left p-3 text-gray-400">Odebráno</th>
                                                <th className="text-left p-3 text-gray-400">Změněno</th>
                                                <th className="text-left p-3 text-gray-400">Beze změn</th>
                                                <th className="text-left p-3 text-gray-400">Souhrn</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {diffs.length === 0 ? (
                                                <tr>
                                                    <td colSpan={7} className="p-12 text-center text-gray-500">
                                                        Zatím žádné diffy
                                                    </td>
                                                </tr>
                                            ) : (
                                                diffs.map((d) => (
                                                    <tr key={d.id} className="border-t border-white/5 hover:bg-white/5">
                                                        <td className="p-3 text-gray-400 whitespace-nowrap text-xs">
                                                            {fmtDateTime(d.created_at)}
                                                        </td>
                                                        <td className="p-3 text-white font-mono text-xs">{d.company_id}</td>
                                                        <td className="p-3">
                                                            {d.added_count > 0 ? (
                                                                <span className="text-green-400 font-medium">+{d.added_count}</span>
                                                            ) : (
                                                                <span className="text-gray-500">0</span>
                                                            )}
                                                        </td>
                                                        <td className="p-3">
                                                            {d.removed_count > 0 ? (
                                                                <span className="text-red-400 font-medium">-{d.removed_count}</span>
                                                            ) : (
                                                                <span className="text-gray-500">0</span>
                                                            )}
                                                        </td>
                                                        <td className="p-3">
                                                            {d.changed_count > 0 ? (
                                                                <span className="text-yellow-400 font-medium">
                                                                    ~{d.changed_count}
                                                                </span>
                                                            ) : (
                                                                <span className="text-gray-500">0</span>
                                                            )}
                                                        </td>
                                                        <td className="p-3 text-gray-500">{d.unchanged_count}</td>
                                                        <td className="p-3 text-gray-300 truncate max-w-xs text-xs">
                                                            {d.summary || "—"}
                                                        </td>
                                                    </tr>
                                                ))
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </Panel>
                        </>
                    )}

                    {/* ══════════════════════════════════════════ */}
                    {/*  TAB: Agentura                            */}
                    {/* ══════════════════════════════════════════ */}
                    {tab === "agentura" && (
                        <>
                            {/* Batch scan */}
                            <Panel className="p-6">
                                <h2 className="text-lg font-semibold text-cyan-400 mb-2">
                                    🏭 Hromadný sken klientů agentury
                                </h2>
                                <p className="text-sm text-gray-400 mb-4">
                                    Zadejte klienty (1 řádek = 1 klient, formát:{" "}
                                    <code className="text-fuchsia-400">
                                        název | url | email | kontakt | poznámka
                                    </code>
                                    )
                                </p>
                                <textarea
                                    placeholder={`Pekárna U Míly | pekarnaumily.cz | info@pekarna.cz | Milan Novák | dělali jsme web\nRestaurace Mlýn | restaurace-mlyn.cz | info@mlyn.cz | Jana Králová | web + GA4`}
                                    value={batchInput}
                                    onChange={(e) => setBatchInput(e.target.value)}
                                    rows={5}
                                    className="w-full bg-black/30 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-600 focus:border-fuchsia-500/50 focus:outline-none resize-none font-mono text-sm"
                                />
                                <div className="flex items-center gap-4 mt-4">
                                    <button
                                        onClick={async () => {
                                            const lines = batchInput.trim().split("\n").filter(Boolean);
                                            if (lines.length === 0) return;
                                            const clients: AgencyClient[] = lines.map((line) => {
                                                const [name, url, email, contact_name, notes] = line
                                                    .split("|")
                                                    .map((s) => s.trim());
                                                return {
                                                    name: name || "",
                                                    url: url || "",
                                                    email,
                                                    contact_name,
                                                    notes,
                                                };
                                            });
                                            setBatchRunning(true);
                                            setBatchResult(null);
                                            try {
                                                const r = await startAgencyBatchScan(clients);
                                                setBatchResult(
                                                    `✅ Spuštěn batch scan ${(r as any).total_clients} klientů (batch_id: ${(r as any).batch_id})`
                                                );
                                                setBatchInput("");
                                                loadAgency();
                                            } catch (e) {
                                                setBatchResult(`❌ Chyba: ${e}`);
                                            } finally {
                                                setBatchRunning(false);
                                            }
                                        }}
                                        disabled={batchRunning || !batchInput.trim()}
                                        className="px-6 py-2.5 bg-gradient-to-r from-fuchsia-500/20 to-cyan-500/20 text-fuchsia-400 border border-fuchsia-500/30 rounded-xl hover:from-fuchsia-500/30 hover:to-cyan-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
                                    >
                                        {batchRunning ? "⏳ Skenuju…" : "🚀 Spustit hromadný sken"}
                                    </button>
                                    {batchResult && (
                                        <span className="text-sm text-gray-300">{batchResult}</span>
                                    )}
                                </div>
                            </Panel>

                            {/* Email generator */}
                            <Panel className="p-6">
                                <h2 className="text-lg font-semibold text-cyan-400 mb-2">
                                    ✉️ Generátor personálního emailu
                                </h2>
                                <p className="text-sm text-gray-400 mb-4">
                                    Vyberte klienta pro vygenerování osobního emailu (k ručnímu odeslání)
                                </p>
                                <div className="flex flex-wrap gap-2">
                                    {agencyClients.map((c) => (
                                        <button
                                            key={c.id}
                                            onClick={async () => {
                                                try {
                                                    const r = await generateAgencyEmail({
                                                        client_name: c.name,
                                                        contact_name: c.contact_name || c.name,
                                                        url: c.url,
                                                        email: c.email,
                                                    });
                                                    setEmailPreview({
                                                        subject: (r as any).subject,
                                                        body: (r as any).body,
                                                    });
                                                } catch (e) {
                                                    setEmailPreview({ subject: "Chyba", body: String(e) });
                                                }
                                            }}
                                            className="px-3 py-1.5 bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 rounded-lg text-xs hover:bg-cyan-500/20 transition-all"
                                        >
                                            ✉️ {c.name}
                                        </button>
                                    ))}
                                    {agencyClients.length === 0 && (
                                        <span className="text-gray-500 text-sm">
                                            Žádní klienti — použijte hromadný sken výše
                                        </span>
                                    )}
                                </div>
                                {emailPreview && (
                                    <div className="mt-4 bg-black/30 rounded-xl p-4 space-y-2">
                                        <div className="text-sm text-fuchsia-400 font-medium">
                                            Předmět: {emailPreview.subject}
                                        </div>
                                        <pre className="text-xs text-gray-300 whitespace-pre-wrap leading-relaxed">
                                            {emailPreview.body}
                                        </pre>
                                        <button
                                            onClick={() => navigator.clipboard.writeText(emailPreview.body)}
                                            className="px-3 py-1 bg-white/5 border border-white/10 rounded text-xs text-gray-400 hover:text-white transition-all"
                                        >
                                            📋 Zkopírovat do schránky
                                        </button>
                                    </div>
                                )}
                            </Panel>

                            {/* Agency clients table */}
                            <Panel className="overflow-hidden">
                                <div className="p-4 border-b border-white/10">
                                    <h2 className="text-lg font-semibold text-cyan-400">
                                        🤝 Klienti agentury ({agencyClients.length})
                                    </h2>
                                </div>
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead className="bg-white/5">
                                            <tr>
                                                <th className="text-left p-3 text-gray-400">Název</th>
                                                <th className="text-left p-3 text-gray-400">URL</th>
                                                <th className="text-left p-3 text-gray-400">Kontakt</th>
                                                <th className="text-left p-3 text-gray-400">Email</th>
                                                <th className="text-left p-3 text-gray-400">Sken</th>
                                                <th className="text-left p-3 text-gray-400">Přidáno</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {agencyClients.length === 0 ? (
                                                <tr>
                                                    <td colSpan={6} className="p-12 text-center text-gray-500">
                                                        Zatím žádní klienti agentury
                                                    </td>
                                                </tr>
                                            ) : (
                                                agencyClients.map((c) => (
                                                    <tr key={c.id} className="border-t border-white/5 hover:bg-white/5">
                                                        <td className="p-3 text-white font-medium">{c.name}</td>
                                                        <td className="p-3 text-cyan-400 text-xs truncate max-w-[200px]">
                                                            {c.url}
                                                        </td>
                                                        <td className="p-3 text-gray-300">{c.contact_name || "—"}</td>
                                                        <td className="p-3 text-gray-400 text-xs">{c.email || "—"}</td>
                                                        <td className="p-3">
                                                            <ScanBadge status={c.scan_status} />
                                                        </td>
                                                        <td className="p-3 text-gray-400 text-xs whitespace-nowrap">
                                                            {fmtDate(c.created_at)}
                                                        </td>
                                                    </tr>
                                                ))
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </Panel>
                        </>
                    )}

                    {/* ══════════════════════════════════════════ */}
                    {/*  TAB: Klienti & Platby                    */}
                    {/* ══════════════════════════════════════════ */}
                    {tab === "klienti" && (
                        <>
                            {/* Summary KPI cards */}
                            {clientData && (
                                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                                    <StatCard
                                        icon="👥"
                                        label="Klienti celkem"
                                        value={fmtNum(clientData.summary.total_clients)}
                                        accent="cyan"
                                    />
                                    <StatCard
                                        icon="💰"
                                        label="Celkový příjem"
                                        value={fmtMoney(clientData.summary.total_revenue)}
                                        accent="green"
                                    />
                                    <StatCard
                                        icon="🔄"
                                        label="Aktivní předplatné"
                                        value={fmtNum(clientData.summary.active_subscriptions)}
                                        accent="fuchsia"
                                    />
                                    <StatCard
                                        icon="🚨"
                                        label="Nezaplacené"
                                        value={fmtNum(clientData.summary.overdue_subscriptions)}
                                        accent="red"
                                    />
                                    <StatCard
                                        icon="🔍"
                                        label="Potřebuje rescan"
                                        value={fmtNum(clientData.summary.needs_rescan)}
                                        accent="orange"
                                    />
                                </div>
                            )}

                            {/* Filters */}
                            <Panel className="p-4">
                                <div className="flex flex-wrap items-center gap-3">
                                    <input
                                        type="text"
                                        placeholder="Hledat klienta (email, firma)…"
                                        value={clientSearch}
                                        onChange={(e) => setClientSearch(e.target.value)}
                                        className="flex-1 min-w-[200px] px-3 py-2 bg-black/30 border border-white/10 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500/50"
                                    />
                                    {(["all", "subscription", "one_time", "needs_rescan", "overdue"] as const).map((f) => {
                                        const labels: Record<string, string> = {
                                            all: "Všichni",
                                            subscription: "📆 Předplatné",
                                            one_time: "💳 Jednorázové",
                                            needs_rescan: "🔍 Potřeba rescanu",
                                            overdue: "🚨 Nezaplacené",
                                        };
                                        return (
                                            <button
                                                key={f}
                                                onClick={() => setClientFilter(f)}
                                                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${clientFilter === f
                                                    ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
                                                    : "bg-white/5 text-gray-400 border border-white/10 hover:text-white"
                                                    }`}
                                            >
                                                {labels[f]}
                                            </button>
                                        );
                                    })}
                                </div>
                            </Panel>

                            {/* Rescan result toast */}
                            {rescanResult && (
                                <Panel className={`p-4 border ${rescanResult.changes_detected ? "border-yellow-500/30 bg-yellow-500/5" : "border-green-500/30 bg-green-500/5"}`}>
                                    <div className="flex items-start justify-between">
                                        <div>
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className="text-lg">{rescanResult.changes_detected ? "⚠️" : "✅"}</span>
                                                <span className="font-semibold text-white">
                                                    Rescan {rescanResult.company_name}
                                                </span>
                                            </div>
                                            <div className="text-sm text-gray-300">
                                                {rescanResult.changes_detected ? (
                                                    <>
                                                        <span className="text-yellow-400 font-medium">Změny detekovány:</span>{" "}
                                                        +{rescanResult.added_count} nové, −{rescanResult.removed_count} odstraněné.
                                                        {rescanResult.documents_regenerated && " 📄 Dokumenty přegenerovány."}
                                                        {rescanResult.email_sent && " 📧 Email odeslán."}
                                                    </>
                                                ) : (
                                                    <span className="text-green-400">Beze změn — vše je aktuální.</span>
                                                )}
                                            </div>
                                        </div>
                                        <button
                                            onClick={() => setRescanResult(null)}
                                            className="text-gray-500 hover:text-white text-sm"
                                        >
                                            ✕
                                        </button>
                                    </div>
                                </Panel>
                            )}

                            {/* Client list */}
                            <Panel className="overflow-hidden">
                                {!clientData ? (
                                    <div className="p-8 text-center text-gray-500 animate-pulse">Načítám klienty…</div>
                                ) : (
                                    <div className="divide-y divide-white/5">
                                        {(() => {
                                            const q = clientSearch.toLowerCase();
                                            const filtered = (clientData.clients || []).filter((c) => {
                                                const matchSearch = !q
                                                    || c.email.toLowerCase().includes(q)
                                                    || c.company_name.toLowerCase().includes(q)
                                                    || (c.company_url || "").toLowerCase().includes(q);
                                                if (!matchSearch) return false;
                                                if (clientFilter === "subscription") return !!c.subscription;
                                                if (clientFilter === "one_time") return !c.subscription;
                                                if (clientFilter === "needs_rescan") return c.needs_rescan;
                                                if (clientFilter === "overdue") return c.subscription && !c.subscription.payment_ok;
                                                return true;
                                            });

                                            if (filtered.length === 0) {
                                                return (
                                                    <div className="p-8 text-center text-gray-500">
                                                        Žádní klienti nenalezeni.
                                                    </div>
                                                );
                                            }

                                            return filtered.map((client) => {
                                                const isExpanded = expandedClient === client.email;
                                                const paidOrders = client.orders.filter((o) => o.status === "PAID" || o.status === "paid");
                                                const totalPaid = paidOrders.reduce((sum, o) => sum + (o.amount || 0), 0);

                                                return (
                                                    <div key={client.email} className="hover:bg-white/[0.02] transition-colors">
                                                        {/* Main row */}
                                                        <div
                                                            className="p-4 flex items-center gap-4 cursor-pointer"
                                                            onClick={() => {
                                                                if (isExpanded) {
                                                                    setExpandedClient(null);
                                                                    setClientDetailTab("overview");
                                                                    setClientQuestionnaire(null);
                                                                    setClientFindings(null);
                                                                } else {
                                                                    setExpandedClient(client.email);
                                                                    setClientDetailTab("overview");
                                                                }
                                                            }}
                                                        >
                                                            {/* Expand arrow */}
                                                            <span className={`text-gray-500 text-xs transition-transform ${isExpanded ? "rotate-90" : ""}`}>▶</span>

                                                            {/* Company info */}
                                                            <div className="flex-1 min-w-0">
                                                                <div className="flex items-center gap-2 mb-0.5">
                                                                    <span className="font-medium text-white truncate">{client.company_name}</span>
                                                                    {client.plan && (
                                                                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${client.plan === "enterprise" ? "bg-fuchsia-500/20 text-fuchsia-400 border border-fuchsia-500/30" :
                                                                            client.plan === "pro" ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30" :
                                                                                "bg-green-500/20 text-green-400 border border-green-500/30"
                                                                            }`}>
                                                                            {client.plan}
                                                                        </span>
                                                                    )}
                                                                    {client.subscription && (
                                                                        <span className="px-2 py-0.5 rounded-full text-[10px] bg-purple-500/20 text-purple-400 border border-purple-500/30">
                                                                            📆 {client.subscription.plan === "monitoring_plus" ? "Monitoring+" : "Monitoring"}
                                                                        </span>
                                                                    )}
                                                                </div>
                                                                <div className="text-xs text-gray-500">{client.email}</div>
                                                                {client.company_url && (
                                                                    <div className="text-[10px] text-cyan-400/60 truncate max-w-[200px]">{client.company_url.replace(/^https?:\/\//, "")}</div>
                                                                )}
                                                            </div>

                                                            {/* Revenue */}
                                                            <div className="text-right">
                                                                <div className="text-sm font-bold text-green-400">{fmtMoney(totalPaid)}</div>
                                                                <div className="text-[10px] text-gray-500">{paidOrders.length} plateb</div>
                                                            </div>

                                                            {/* Subscription payment status */}
                                                            <div className="w-24 text-center">
                                                                {client.subscription ? (
                                                                    client.subscription.payment_ok ? (
                                                                        <span className="px-2 py-1 rounded-full text-xs bg-green-500/20 text-green-400 border border-green-500/30">
                                                                            ✅ Placeno
                                                                        </span>
                                                                    ) : (
                                                                        <span className="px-2 py-1 rounded-full text-xs bg-red-500/20 text-red-400 border border-red-500/30 animate-pulse">
                                                                            🚨 Dluh
                                                                        </span>
                                                                    )
                                                                ) : (
                                                                    <span className="text-xs text-gray-600">—</span>
                                                                )}
                                                            </div>

                                                            {/* Fulfillment status */}
                                                            <div className="w-32 text-center">
                                                                {client.fulfillment === "ok" && (
                                                                    <span className="px-2 py-1 rounded-full text-xs bg-green-500/20 text-green-400 border border-green-500/30">
                                                                        ✅ Aktuální
                                                                    </span>
                                                                )}
                                                                {client.fulfillment === "needs_rescan" && (
                                                                    <span className="px-2 py-1 rounded-full text-xs bg-orange-500/20 text-orange-400 border border-orange-500/30">
                                                                        🔍 Rescan
                                                                    </span>
                                                                )}
                                                                {client.fulfillment === "needs_documents" && (
                                                                    <span className="px-2 py-1 rounded-full text-xs bg-yellow-500/20 text-yellow-400 border border-yellow-500/30">
                                                                        📄 Dokumenty
                                                                    </span>
                                                                )}
                                                                {client.fulfillment === "no_scan" && (
                                                                    <span className="px-2 py-1 rounded-full text-xs bg-red-500/20 text-red-400 border border-red-500/30">
                                                                        ❌ Bez skenu
                                                                    </span>
                                                                )}
                                                            </div>

                                                            {/* Last scan age */}
                                                            <div className="w-20 text-right">
                                                                {client.scan_age_days != null ? (
                                                                    <div className={`text-xs font-mono ${client.scan_age_days > 30 ? "text-orange-400" : "text-gray-400"}`}>
                                                                        před {client.scan_age_days}d
                                                                    </div>
                                                                ) : (
                                                                    <div className="text-xs text-gray-600">—</div>
                                                                )}
                                                            </div>

                                                            {/* Rescan button */}
                                                            <button
                                                                onClick={async (e) => {
                                                                    e.stopPropagation();
                                                                    setRescanning(client.email);
                                                                    setRescanResult(null);
                                                                    try {
                                                                        const result = await triggerClientRescan(client.email);
                                                                        setRescanResult(result);
                                                                        await loadClientManagement();
                                                                    } catch (err) {
                                                                        setRescanResult({
                                                                            status: "error",
                                                                            email: client.email,
                                                                            company_name: client.company_name,
                                                                            scan_id: "",
                                                                            changes_detected: false,
                                                                            added_count: 0,
                                                                            removed_count: 0,
                                                                            documents_regenerated: false,
                                                                            email_sent: false,
                                                                        });
                                                                    } finally {
                                                                        setRescanning(null);
                                                                    }
                                                                }}
                                                                disabled={rescanning === client.email || !client.company_url}
                                                                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all whitespace-nowrap ${rescanning === client.email
                                                                    ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 animate-pulse cursor-wait"
                                                                    : "bg-white/5 text-gray-400 border border-white/10 hover:text-cyan-400 hover:border-cyan-500/30 hover:bg-cyan-500/10"
                                                                    }`}
                                                            >
                                                                {rescanning === client.email ? "⏳ Skenuji…" : "🔄 Rescan"}
                                                            </button>
                                                        </div>

                                                        {/* Expanded detail */}
                                                        {isExpanded && (
                                                            <div className="px-4 pb-4 pl-10 space-y-4">
                                                                {/* Detail tabs */}
                                                                <div className="flex gap-2 border-b border-white/10 pb-2">
                                                                    {([
                                                                        { id: "overview" as const, label: "Přehled", icon: "📋" },
                                                                        { id: "questionnaire" as const, label: "Dotazník", icon: "📝" },
                                                                        { id: "findings" as const, label: "AI Nálezy", icon: "🔍" },
                                                                    ]).map(t => (
                                                                        <button
                                                                            key={t.id}
                                                                            onClick={async (e) => {
                                                                                e.stopPropagation();
                                                                                setClientDetailTab(t.id);
                                                                                if (t.id === "questionnaire" && !clientQuestionnaire) {
                                                                                    setLoadingDetail(true);
                                                                                    try {
                                                                                        const data = await getClientQuestionnaire(client.email);
                                                                                        setClientQuestionnaire(data);
                                                                                    } catch (err) { console.error(err); }
                                                                                    finally { setLoadingDetail(false); }
                                                                                }
                                                                                if (t.id === "findings" && !clientFindings) {
                                                                                    setLoadingDetail(true);
                                                                                    try {
                                                                                        const data = await getClientFindings(client.email);
                                                                                        setClientFindings(data);
                                                                                    } catch (err) { console.error(err); }
                                                                                    finally { setLoadingDetail(false); }
                                                                                }
                                                                            }}
                                                                            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${clientDetailTab === t.id
                                                                                ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
                                                                                : "text-gray-400 border border-white/10 hover:text-white hover:bg-white/5"
                                                                                }`}
                                                                        >
                                                                            {t.icon} {t.label}
                                                                        </button>
                                                                    ))}
                                                                </div>

                                                                {/* Tab: Questionnaire */}
                                                                {clientDetailTab === "questionnaire" && (
                                                                    <div className="space-y-3">
                                                                        {loadingDetail ? (
                                                                            <div className="text-cyan-400 text-sm animate-pulse">Načítám dotazník...</div>
                                                                        ) : !clientQuestionnaire || clientQuestionnaire.total_responses === 0 ? (
                                                                            <div className="text-gray-500 text-sm">Dotazník nebyl vyplněn.</div>
                                                                        ) : (
                                                                            <>
                                                                                <div className="text-xs text-gray-400 mb-2">Celkem odpovědí: {clientQuestionnaire.total_responses}</div>
                                                                                {Object.entries(clientQuestionnaire.sections).map(([section, responses]) => (
                                                                                    <Panel key={section} className="p-4">
                                                                                        <h4 className="text-xs font-bold text-fuchsia-400 uppercase tracking-wider mb-3">
                                                                                            {section.replace(/_/g, " ")}
                                                                                        </h4>
                                                                                        <div className="space-y-2">
                                                                                            {responses.map((r, i) => (
                                                                                                <div key={i} className="flex flex-col gap-1 bg-black/20 rounded-lg p-3 text-xs">
                                                                                                    <div className="flex items-start justify-between gap-2">
                                                                                                        <span className="text-gray-300 font-medium">{r.question_key.replace(/_/g, " ")}</span>
                                                                                                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold shrink-0 ${r.answer === "yes" ? "bg-green-500/20 text-green-400" :
                                                                                                            r.answer === "no" ? "bg-gray-500/20 text-gray-400" :
                                                                                                                "bg-cyan-500/20 text-cyan-400"
                                                                                                            }`}>
                                                                                                            {r.answer}
                                                                                                        </span>
                                                                                                    </div>
                                                                                                    {r.tool_name && (
                                                                                                        <div className="text-cyan-400/70">Nástroj: {r.tool_name}</div>
                                                                                                    )}
                                                                                                    {r.details && Object.keys(r.details).length > 0 && (
                                                                                                        <div className="text-gray-500 mt-1 space-y-0.5">
                                                                                                            {Object.entries(r.details).map(([k, v]) => (
                                                                                                                <div key={k}><span className="text-gray-400">{k.replace(/_/g, " ")}:</span> {String(v)}</div>
                                                                                                            ))}
                                                                                                        </div>
                                                                                                    )}
                                                                                                </div>
                                                                                            ))}
                                                                                        </div>
                                                                                    </Panel>
                                                                                ))}
                                                                            </>
                                                                        )}
                                                                    </div>
                                                                )}

                                                                {/* Tab: Findings */}
                                                                {clientDetailTab === "findings" && (
                                                                    <div className="space-y-3">
                                                                        {loadingDetail ? (
                                                                            <div className="text-cyan-400 text-sm animate-pulse">Načítám nálezy...</div>
                                                                        ) : !clientFindings || clientFindings.total === 0 ? (
                                                                            <div className="text-gray-500 text-sm">Žádné nálezy ze skenování.</div>
                                                                        ) : (
                                                                            <>
                                                                                <div className="text-xs text-gray-400 mb-2">
                                                                                    Celkem nálezů: {clientFindings.total} | Firma: {clientFindings.company_name}
                                                                                </div>
                                                                                <div className="space-y-2">
                                                                                    {clientFindings.findings.map((f: FindingDetail) => (
                                                                                        <Panel key={f.id} className="p-4">
                                                                                            <div className="flex items-start justify-between gap-3">
                                                                                                <div className="flex-1">
                                                                                                    <div className="flex items-center gap-2 mb-1">
                                                                                                        <span className="text-white font-medium text-sm">{f.name}</span>
                                                                                                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${f.risk_level === "high" ? "bg-red-500/20 text-red-400" :
                                                                                                            f.risk_level === "limited" ? "bg-orange-500/20 text-orange-400" :
                                                                                                                f.risk_level === "minimal" ? "bg-green-500/20 text-green-400" :
                                                                                                                    "bg-gray-500/20 text-gray-400"
                                                                                                            }`}>
                                                                                                            {f.risk_level}
                                                                                                        </span>
                                                                                                        <span className="text-[10px] text-gray-500">{f.category}</span>
                                                                                                    </div>
                                                                                                    <div className="text-xs text-gray-400 mb-1">{f.ai_classification_text}</div>
                                                                                                    {f.ai_act_article && (
                                                                                                        <div className="text-xs text-fuchsia-400/70 mb-1">AI Act: {f.ai_act_article}</div>
                                                                                                    )}
                                                                                                    <div className="text-xs text-cyan-400/70">{f.action_required}</div>
                                                                                                </div>
                                                                                                <span className={`text-[10px] px-2 py-0.5 rounded border shrink-0 ${f.status === "open" ? "border-yellow-500/30 text-yellow-400" :
                                                                                                    f.status === "resolved" ? "border-green-500/30 text-green-400" :
                                                                                                        "border-white/10 text-gray-500"
                                                                                                    }`}>
                                                                                                    {f.status}
                                                                                                </span>
                                                                                            </div>
                                                                                        </Panel>
                                                                                    ))}
                                                                                </div>
                                                                            </>
                                                                        )}
                                                                    </div>
                                                                )}

                                                                {/* Tab: Overview (existing content) */}
                                                                {clientDetailTab === "overview" && (
                                                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                                                        {/* Orders history */}
                                                                        <Panel className="p-4">
                                                                            <h4 className="text-xs font-semibold text-cyan-400 mb-3 uppercase tracking-wider">📋 Objednávky</h4>
                                                                            {client.orders.length === 0 ? (
                                                                                <div className="text-xs text-gray-500">Žádné objednávky</div>
                                                                            ) : (
                                                                                <div className="space-y-2">
                                                                                    {client.orders.map((o) => (
                                                                                        <div key={o.id} className="flex items-center justify-between text-xs bg-black/20 rounded-lg p-2">
                                                                                            <div>
                                                                                                <div className="text-white font-medium">{o.order_number}</div>
                                                                                                <div className="text-gray-500">
                                                                                                    {o.plan?.toUpperCase()} • {o.order_type === "subscription_recurrence" ? "Opakovaná" : o.order_type === "subscription" ? "Předplatné" : "Jednorázová"}
                                                                                                </div>
                                                                                            </div>
                                                                                            <div className="text-right">
                                                                                                <div className={`font-bold ${o.status === "PAID" || o.status === "paid" ? "text-green-400" : "text-yellow-400"}`}>
                                                                                                    {fmtMoney(o.amount)}
                                                                                                </div>
                                                                                                <div className="text-gray-500">{fmtDate(o.paid_at || o.created_at)}</div>
                                                                                            </div>
                                                                                        </div>
                                                                                    ))}
                                                                                </div>
                                                                            )}
                                                                        </Panel>

                                                                        {/* Subscription detail */}
                                                                        <Panel className="p-4">
                                                                            <h4 className="text-xs font-semibold text-fuchsia-400 mb-3 uppercase tracking-wider">📆 Předplatné</h4>
                                                                            {!client.subscription ? (
                                                                                <div className="text-xs text-gray-500">Žádné aktivní předplatné</div>
                                                                            ) : (
                                                                                <div className="space-y-2 text-xs">
                                                                                    <div className="flex justify-between">
                                                                                        <span className="text-gray-400">Plán</span>
                                                                                        <span className="text-white font-medium">
                                                                                            {client.subscription.plan === "monitoring_plus" ? "Monitoring Plus" : "Monitoring"}
                                                                                        </span>
                                                                                    </div>
                                                                                    <div className="flex justify-between">
                                                                                        <span className="text-gray-400">Částka</span>
                                                                                        <span className="text-white">{fmtMoney(client.subscription.amount)}/měs</span>
                                                                                    </div>
                                                                                    <div className="flex justify-between">
                                                                                        <span className="text-gray-400">Stav</span>
                                                                                        <span className={client.subscription.payment_ok ? "text-green-400" : "text-red-400"}>
                                                                                            {client.subscription.payment_ok ? "✅ OK" : "🚨 Nezaplaceno"}
                                                                                        </span>
                                                                                    </div>
                                                                                    <div className="flex justify-between">
                                                                                        <span className="text-gray-400">Aktivováno</span>
                                                                                        <span className="text-gray-300">{fmtDate(client.subscription.activated_at)}</span>
                                                                                    </div>
                                                                                    <div className="flex justify-between">
                                                                                        <span className="text-gray-400">Poslední platba</span>
                                                                                        <span className="text-gray-300">{fmtDate(client.subscription.last_charged_at)}</span>
                                                                                    </div>
                                                                                    <div className="flex justify-between">
                                                                                        <span className="text-gray-400">Další platba</span>
                                                                                        <span className={`font-medium ${client.subscription.payment_ok ? "text-cyan-400" : "text-red-400"
                                                                                            }`}>
                                                                                            {fmtDate(client.subscription.next_charge_at)}
                                                                                        </span>
                                                                                    </div>
                                                                                    <div className="flex justify-between border-t border-white/5 pt-2">
                                                                                        <span className="text-gray-400">Celkem strženo</span>
                                                                                        <span className="text-green-400 font-bold">
                                                                                            {fmtMoney(client.subscription.total_charged)}
                                                                                        </span>
                                                                                    </div>
                                                                                </div>
                                                                            )}
                                                                        </Panel>

                                                                        {/* Scan + Fulfillment */}
                                                                        <Panel className="p-4">
                                                                            <h4 className="text-xs font-semibold text-green-400 mb-3 uppercase tracking-wider">🛡️ Plnění povinností</h4>
                                                                            <div className="space-y-2 text-xs">
                                                                                <div className="flex justify-between">
                                                                                    <span className="text-gray-400">Poslední sken</span>
                                                                                    <span className="text-gray-300">
                                                                                        {client.last_scan
                                                                                            ? `${fmtDate(client.last_scan.created_at)} (${client.scan_age_days ?? "?"}d)`
                                                                                            : "—"
                                                                                        }
                                                                                    </span>
                                                                                </div>
                                                                                <div className="flex justify-between">
                                                                                    <span className="text-gray-400">Nálezy</span>
                                                                                    <span className="text-white">{client.last_scan?.total_findings ?? "—"}</span>
                                                                                </div>
                                                                                <div className="flex justify-between">
                                                                                    <span className="text-gray-400">Dokumenty</span>
                                                                                    <span className="text-white">{client.documents_count} ks</span>
                                                                                </div>
                                                                                <div className="flex justify-between">
                                                                                    <span className="text-gray-400">Dokumenty vygenerovány</span>
                                                                                    <span className="text-gray-300">{fmtDate(client.documents_last_at)}</span>
                                                                                </div>
                                                                                <div className="flex justify-between">
                                                                                    <span className="text-gray-400">Dotazník</span>
                                                                                    <span className={client.questionnaire_done ? "text-green-400" : "text-gray-500"}>
                                                                                        {client.questionnaire_done ? "✅ Vyplněn" : "❌ Nevyplněn"}
                                                                                    </span>
                                                                                </div>
                                                                                {client.last_diff && (
                                                                                    <div className="border-t border-white/5 pt-2 mt-2">
                                                                                        <div className="text-gray-400 mb-1">Poslední porovnání:</div>
                                                                                        <div className={`rounded-lg p-2 ${client.last_diff.has_changes ? "bg-yellow-500/10" : "bg-green-500/10"}`}>
                                                                                            {client.last_diff.has_changes ? (
                                                                                                <span className="text-yellow-400">
                                                                                                    ⚠️ +{client.last_diff.added} / −{client.last_diff.removed}
                                                                                                </span>
                                                                                            ) : (
                                                                                                <span className="text-green-400">✅ Beze změn</span>
                                                                                            )}
                                                                                            <div className="text-gray-500 text-[10px] mt-0.5">
                                                                                                {fmtDate(client.last_diff.created_at)}
                                                                                            </div>
                                                                                        </div>
                                                                                    </div>
                                                                                )}
                                                                                <div className="border-t border-white/5 pt-2 mt-2">
                                                                                    <div className="flex justify-between items-center">
                                                                                        <span className="text-gray-400">Stav plnění</span>
                                                                                        {client.fulfillment === "ok" && <span className="text-green-400 font-medium">✅ Vše splněno</span>}
                                                                                        {client.fulfillment === "needs_rescan" && <span className="text-orange-400 font-medium">🔍 Potřeba sken</span>}
                                                                                        {client.fulfillment === "needs_documents" && <span className="text-yellow-400 font-medium">📄 Chybí dokumenty</span>}
                                                                                        {client.fulfillment === "no_scan" && <span className="text-red-400 font-medium">❌ Bez skenu</span>}
                                                                                    </div>
                                                                                </div>
                                                                            </div>
                                                                        </Panel>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        )}
                                                    </div>
                                                );
                                            });
                                        })()}
                                    </div>
                                )}
                            </Panel>
                        </>
                    )}

                    {/* ══════════════════════════════════════════ */}
                    {/*  TAB: Objednávky (Orders)                 */}
                    {/* ══════════════════════════════════════════ */}
                    {tab === "objednavky" && (
                        <>
                            {/* KPI cards */}
                            {orderStats && (
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <StatCard
                                        icon="🧾"
                                        label="Objednávek celkem"
                                        value={fmtNum(orderStats.total_orders)}
                                        accent="cyan"
                                    />
                                    <StatCard
                                        icon="💰"
                                        label="Tržby celkem"
                                        value={fmtMoney(orderStats.total_revenue)}
                                        accent="green"
                                    />
                                    <StatCard
                                        icon="⏳"
                                        label="Čeká na platbu"
                                        value={fmtNum(orderStats.awaiting_payment?.length || 0)}
                                        accent="yellow"
                                    />
                                    <StatCard
                                        icon="🏦"
                                        label="Bankovní převody"
                                        value={fmtNum(orderStats.by_gateway?.bank_transfer?.count || 0)}
                                        accent="orange"
                                    />
                                </div>
                            )}

                            {/* Awaiting bank transfers */}
                            {orderStats && orderStats.awaiting_payment && orderStats.awaiting_payment.length > 0 && (
                                <Panel className="p-4">
                                    <h3 className="text-sm font-semibold text-yellow-400 mb-3 flex items-center gap-2">
                                        ⏳ Čekající platby — k potvrzení
                                    </h3>
                                    <div className="space-y-2">
                                        {orderStats.awaiting_payment.map((o) => (
                                            <div
                                                key={o.order_number}
                                                className="flex items-center justify-between bg-yellow-500/5 border border-yellow-500/20 rounded-xl p-3"
                                            >
                                                <div>
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-white font-mono text-sm font-medium">{o.order_number}</span>
                                                        <span className="px-2 py-0.5 rounded-full text-[10px] bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 uppercase font-bold">
                                                            {o.payment_gateway}
                                                        </span>
                                                    </div>
                                                    <div className="text-xs text-gray-400 mt-0.5">
                                                        {o.email} • {o.plan?.toUpperCase()} • VS: {o.variable_symbol || "—"}
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-3">
                                                    <div className="text-right">
                                                        <div className="text-sm font-bold text-yellow-400">{fmtMoney(o.amount)}</div>
                                                        <div className="text-[10px] text-gray-500">{fmtDate(o.created_at)}</div>
                                                    </div>
                                                    <button
                                                        onClick={async () => {
                                                            if (!confirm(`Opravdu potvrdit platbu ${o.order_number}?`)) return;
                                                            setConfirmingOrder(o.order_number);
                                                            try {
                                                                await confirmBankPayment(o.order_number);
                                                                await loadOrders();
                                                            } catch (err) {
                                                                alert(err instanceof Error ? err.message : "Chyba");
                                                            } finally {
                                                                setConfirmingOrder(null);
                                                            }
                                                        }}
                                                        disabled={confirmingOrder === o.order_number}
                                                        className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all ${confirmingOrder === o.order_number
                                                            ? "bg-green-500/20 text-green-400 border border-green-500/30 animate-pulse cursor-wait"
                                                            : "bg-green-500/20 text-green-400 border border-green-500/30 hover:bg-green-500/30"
                                                            }`}
                                                    >
                                                        {confirmingOrder === o.order_number ? "⏳ Potvrzuji…" : "✅ Potvrdit platbu"}
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </Panel>
                            )}

                            {/* Filters */}
                            <Panel className="p-4">
                                <div className="flex flex-wrap items-center gap-3">
                                    <span className="text-xs text-gray-500 font-medium">Stav:</span>
                                    {(["all", "PAID", "AWAITING_PAYMENT", "EXPIRED"] as const).map((f) => {
                                        const labels: Record<string, string> = {
                                            all: "Všechny",
                                            PAID: "✅ Zaplacené",
                                            AWAITING_PAYMENT: "⏳ Čekající",
                                            EXPIRED: "❌ Expirované",
                                        };
                                        return (
                                            <button
                                                key={f}
                                                onClick={() => setOrderFilter(f)}
                                                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${orderFilter === f
                                                    ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
                                                    : "bg-white/5 text-gray-400 border border-white/10 hover:text-white"
                                                    }`}
                                            >
                                                {labels[f]}
                                            </button>
                                        );
                                    })}
                                    <span className="text-xs text-gray-500 font-medium ml-4">Brána:</span>
                                    {(["all", "stripe", "bank_transfer"] as const).map((f) => {
                                        const labels: Record<string, string> = {
                                            all: "Všechny",
                                            stripe: "💳 Stripe",
                                            bank_transfer: "🏦 Převod",
                                        };
                                        return (
                                            <button
                                                key={f}
                                                onClick={() => setOrderGwFilter(f)}
                                                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${orderGwFilter === f
                                                    ? "bg-fuchsia-500/20 text-fuchsia-400 border border-fuchsia-500/30"
                                                    : "bg-white/5 text-gray-400 border border-white/10 hover:text-white"
                                                    }`}
                                            >
                                                {labels[f]}
                                            </button>
                                        );
                                    })}
                                </div>
                            </Panel>

                            {/* Orders table */}
                            <Panel className="overflow-hidden">
                                {adminOrders.length === 0 ? (
                                    <div className="p-8 text-center text-gray-500 animate-pulse">Načítám objednávky…</div>
                                ) : (
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-sm">
                                            <thead>
                                                <tr className="border-b border-white/10">
                                                    <th className="text-left px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Objednávka</th>
                                                    <th className="text-left px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Email</th>
                                                    <th className="text-left px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Plán</th>
                                                    <th className="text-left px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Brána</th>
                                                    <th className="text-right px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Částka</th>
                                                    <th className="text-center px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Stav</th>
                                                    <th className="text-right px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Datum</th>
                                                    <th className="text-center px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Akce</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-white/5">
                                                {adminOrders
                                                    .filter((o) => orderFilter === "all" || o.status === orderFilter)
                                                    .filter((o) => orderGwFilter === "all" || o.payment_gateway === orderGwFilter)
                                                    .map((o) => {
                                                        const isPaid = o.status === "PAID" || o.status === "paid";
                                                        const isAwaiting = o.status === "AWAITING_PAYMENT";
                                                        return (
                                                            <tr key={o.id} className="hover:bg-white/[0.02] transition-colors">
                                                                <td className="px-4 py-3">
                                                                    <span className="text-white font-mono text-xs">{o.order_number}</span>
                                                                    {o.variable_symbol && (
                                                                        <div className="text-[10px] text-gray-500">VS: {o.variable_symbol}</div>
                                                                    )}
                                                                </td>
                                                                <td className="px-4 py-3 text-xs text-gray-300 max-w-[200px] truncate">{o.email}</td>
                                                                <td className="px-4 py-3">
                                                                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-white/5 border border-white/10 text-gray-300">
                                                                        {o.plan}
                                                                    </span>
                                                                </td>
                                                                <td className="px-4 py-3">
                                                                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${o.payment_gateway === "stripe"
                                                                        ? "bg-purple-500/20 text-purple-400 border border-purple-500/30"
                                                                        : o.payment_gateway === "bank_transfer"
                                                                            ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
                                                                            : "bg-white/5 text-gray-400 border border-white/10"
                                                                        }`}>
                                                                        {o.payment_gateway === "stripe" ? "💳 Stripe" :
                                                                            o.payment_gateway === "bank_transfer" ? "🏦 Převod" :
                                                                                o.payment_gateway}
                                                                    </span>
                                                                </td>
                                                                <td className="px-4 py-3 text-right">
                                                                    <span className={`font-bold text-xs ${isPaid ? "text-green-400" : isAwaiting ? "text-yellow-400" : "text-gray-500"}`}>
                                                                        {fmtMoney(o.amount)}
                                                                    </span>
                                                                </td>
                                                                <td className="px-4 py-3 text-center">
                                                                    <span className={`px-2 py-1 rounded-full text-[10px] font-semibold ${isPaid
                                                                        ? "bg-green-500/20 text-green-400 border border-green-500/30"
                                                                        : isAwaiting
                                                                            ? "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 animate-pulse"
                                                                            : "bg-red-500/20 text-red-400 border border-red-500/30"
                                                                        }`}>
                                                                        {isPaid ? "✅ Zaplaceno" : isAwaiting ? "⏳ Čeká" : o.status}
                                                                    </span>
                                                                </td>
                                                                <td className="px-4 py-3 text-right text-[11px] text-gray-500">
                                                                    {fmtDate(o.paid_at || o.created_at)}
                                                                </td>
                                                                <td className="px-4 py-3 text-center">
                                                                    {isAwaiting && (
                                                                        <button
                                                                            onClick={async () => {
                                                                                if (!confirm(`Potvrdit platbu ${o.order_number}?\n\nBude odeslán email s fakturou zákazníkovi.`)) return;
                                                                                setConfirmingOrder(o.order_number);
                                                                                try {
                                                                                    const result = await confirmBankPayment(o.order_number);
                                                                                    if (result.invoice_sent) {
                                                                                        alert(`✅ Platba potvrzena!\n📄 Faktura ${result.invoice_number} odeslána emailem.`);
                                                                                    } else {
                                                                                        alert(`✅ Platba potvrzena!\n⚠️ Fakturu se nepodařilo vygenerovat — zkontrolujte logy.`);
                                                                                    }
                                                                                    await loadOrders();
                                                                                } catch (err) {
                                                                                    alert(err instanceof Error ? err.message : "Chyba");
                                                                                } finally {
                                                                                    setConfirmingOrder(null);
                                                                                }
                                                                            }}
                                                                            disabled={confirmingOrder === o.order_number}
                                                                            className="px-3 py-1.5 rounded-lg text-[11px] font-medium bg-green-500/10 text-green-400 border border-green-500/20 hover:bg-green-500/20 transition-all disabled:animate-pulse disabled:cursor-wait"
                                                                        >
                                                                            {confirmingOrder === o.order_number ? "⏳" : "✅ Potvrdit"}
                                                                        </button>
                                                                    )}
                                                                </td>
                                                            </tr>
                                                        );
                                                    })}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </Panel>

                            {/* ═══ FAKTURY (sloučeno z původního tabu Faktury) ═══ */}
                            {invoicesLoading ? (
                                <div className="text-center py-8 text-gray-400">Načítám faktury…</div>
                            ) : adminInvoices.length > 0 && (
                                <Panel className="p-6">
                                    <h3 className="font-semibold mb-4 flex items-center gap-2 text-lg">
                                        📄 Vydané faktury
                                        <span className="ml-2 inline-flex items-center rounded-full bg-cyan-500/10 text-cyan-400 px-2.5 py-0.5 text-xs font-medium">{adminInvoices.length}</span>
                                    </h3>
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-sm">
                                            <thead>
                                                <tr className="text-left text-gray-500 border-b border-white/5">
                                                    <th className="py-2 px-3">Číslo faktury</th>
                                                    <th className="py-2 px-3">Objednávka</th>
                                                    <th className="py-2 px-3">Email</th>
                                                    <th className="py-2 px-3">Odběratel</th>
                                                    <th className="py-2 px-3">Plán</th>
                                                    <th className="py-2 px-3 text-right">Částka</th>
                                                    <th className="py-2 px-3">Datum</th>
                                                    <th className="py-2 px-3">PDF</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {adminInvoices.map((inv) => (
                                                    <tr key={inv.id} className="border-b border-white/5 hover:bg-white/[0.02]">
                                                        <td className="py-2.5 px-3 font-mono text-xs text-cyan-400">{inv.invoice_number}</td>
                                                        <td className="py-2.5 px-3 font-mono text-xs text-slate-400">{inv.order_number}</td>
                                                        <td className="py-2.5 px-3 text-slate-300">{inv.email}</td>
                                                        <td className="py-2.5 px-3 text-slate-300">
                                                            <div>{inv.buyer_name}</div>
                                                            {inv.buyer_ico && <div className="text-xs text-slate-500">IČO: {inv.buyer_ico}</div>}
                                                        </td>
                                                        <td className="py-2.5 px-3">
                                                            <span className="inline-flex rounded-full px-2 py-0.5 text-xs font-medium bg-purple-500/10 text-purple-400">
                                                                {inv.plan?.toUpperCase()}
                                                            </span>
                                                        </td>
                                                        <td className="py-2.5 px-3 text-right font-medium text-slate-200">
                                                            {new Intl.NumberFormat("cs-CZ").format(inv.amount)} Kč
                                                        </td>
                                                        <td className="py-2.5 px-3 text-slate-400 text-xs">
                                                            {new Date(inv.issued_at).toLocaleDateString("cs-CZ")}
                                                        </td>
                                                        <td className="py-2.5 px-3">
                                                            {inv.pdf_url ? (
                                                                <a href={inv.pdf_url} target="_blank" rel="noopener noreferrer"
                                                                    className="inline-flex items-center gap-1 text-emerald-400 hover:text-emerald-300 text-xs">
                                                                    📥 Stáhnout
                                                                </a>
                                                            ) : (
                                                                <span className="text-gray-600 text-xs">—</span>
                                                            )}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </Panel>
                            )}
                        </>
                    )}

                    {/* ══════════════════════════════════════════ */}
                    {/*  TAB: Nástroje (Tools)                    */}
                    {/* ══════════════════════════════════════════ */}
                    {tab === "nastroje" && (
                        <>
                            {/* ═══ Manuální spuštění úloh (přesunuto z Úlohy) ═══ */}
                            <Panel className="p-6">
                                <h2 className="text-lg font-semibold text-cyan-400 mb-4">
                                    🚀 Manuální spuštění úloh
                                </h2>
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                                    {TASKS.map((task) => (
                                        <button
                                            key={task.name}
                                            onClick={() => handleRunTask(task.name)}
                                            disabled={runningTask !== null}
                                            className={`p-4 rounded-xl border text-left transition-all ${runningTask === task.name
                                                ? "border-cyan-500/50 bg-cyan-500/10 animate-pulse"
                                                : "border-white/10 bg-white/5 hover:bg-white/10 hover:border-fuchsia-500/30"
                                                }`}
                                        >
                                            <div className="font-medium text-white">{task.label}</div>
                                            <div className="text-xs text-gray-400 mt-1">{task.desc}</div>
                                            {runningTask === task.name && (
                                                <div className="text-xs text-cyan-400 mt-2 animate-pulse">⏳ Běží…</div>
                                            )}
                                        </button>
                                    ))}
                                </div>
                                {taskResult && (
                                    <pre className="mt-4 p-4 bg-black/50 rounded-xl text-xs text-green-400 overflow-x-auto max-h-80">
                                        {taskResult}
                                    </pre>
                                )}
                            </Panel>

                            {/* Poslední logy úloh */}
                            {adminStats && adminStats.recent_logs.length > 0 && (
                                <Panel className="overflow-hidden">
                                    <div className="p-4 border-b border-white/10">
                                        <h2 className="text-lg font-semibold text-cyan-400">📋 Poslední logy úloh</h2>
                                    </div>
                                    <table className="w-full text-sm">
                                        <thead className="bg-white/5">
                                            <tr>
                                                <th className="text-left p-3 text-gray-400">Čas</th>
                                                <th className="text-left p-3 text-gray-400">Úloha</th>
                                                <th className="text-left p-3 text-gray-400">Status</th>
                                                <th className="text-left p-3 text-gray-400">Výsledek / Chyba</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {adminStats.recent_logs.map((log) => (
                                                <tr key={log.id} className="border-t border-white/5 hover:bg-white/5">
                                                    <td className="p-3 text-gray-400 whitespace-nowrap text-xs">
                                                        {fmtDateTime(log.started_at)}
                                                    </td>
                                                    <td className="p-3 text-white font-medium">{log.task_name}</td>
                                                    <td className="p-3">
                                                        <span
                                                            className={`px-2 py-0.5 rounded text-xs ${log.status === "completed"
                                                                ? "bg-green-500/20 text-green-400"
                                                                : log.status === "running"
                                                                    ? "bg-cyan-500/20 text-cyan-400"
                                                                    : "bg-red-500/20 text-red-400"
                                                                }`}
                                                        >
                                                            {log.status}
                                                        </span>
                                                    </td>
                                                    <td className="p-3 text-gray-300 text-xs font-mono truncate max-w-md">
                                                        {log.error || (log.result ? JSON.stringify(log.result) : "—")}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </Panel>
                            )}

                            {/* Plán úloh (CRON) */}
                            <Panel className="p-6">
                                <h2 className="text-lg font-semibold text-cyan-400 mb-4">🕐 Plán úloh (CRON)</h2>
                                <div className="space-y-2 text-sm font-mono">
                                    {CRON_SCHEDULE.map((c) => (
                                        <div key={c.time} className="flex gap-4">
                                            <span className="text-fuchsia-400 w-16">{c.time}</span>
                                            <span className="text-gray-300">{c.desc}</span>
                                        </div>
                                    ))}
                                </div>
                            </Panel>

                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {/* Data cleanup */}
                                <Panel className="p-6">
                                    <div className="text-3xl mb-3">🧹</div>
                                    <h3 className="font-semibold text-white mb-2">Čištění dat</h3>
                                    <p className="text-xs text-gray-400 mb-4">
                                        Vyčistí duplicitní firmy, opraví formáty URL/email, odstraní test záznamy.
                                    </p>
                                    <button
                                        onClick={async () => {
                                            setToolResult(null);
                                            try {
                                                const r = await runAdminTask("cleanup");
                                                setToolResult(`✅ Cleanup: ${JSON.stringify(r, null, 2)}`);
                                            } catch (e) {
                                                setToolResult(`❌ Chyba: ${e}`);
                                            }
                                        }}
                                        className="w-full px-4 py-2 bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 rounded-xl hover:bg-cyan-500/20 transition-all text-sm font-medium"
                                    >
                                        🧹 Spustit Cleanup
                                    </button>
                                </Panel>

                                {/* Export */}
                                <Panel className="p-6">
                                    <div className="text-3xl mb-3">📤</div>
                                    <h3 className="font-semibold text-white mb-2">Export dat</h3>
                                    <p className="text-xs text-gray-400 mb-4">
                                        Exportuje seznam firem s CRM daty do CSV. Stáhne se do prohlížeče.
                                    </p>
                                    <button
                                        onClick={async () => {
                                            setToolResult(null);
                                            try {
                                                const d = await getAdminCompanies("all", 9999);
                                                const rows = (d.companies || []) as any[];
                                                const header =
                                                    "ICO,Name,URL,Email,Workflow,Payment,Priority,Score,Emails,Created\n";
                                                const csv =
                                                    header +
                                                    rows
                                                        .map(
                                                            (c: any) =>
                                                                `"${c.ico || ""}","${c.name || ""}","${c.url || ""}","${c.email || ""}","${c.workflow_status || ""}","${c.payment_status || ""}","${c.priority || ""}","${c.lead_score || ""}","${c.emails_sent || 0}","${c.created_at || ""}"`
                                                        )
                                                        .join("\n");
                                                const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
                                                const url = URL.createObjectURL(blob);
                                                const a = document.createElement("a");
                                                a.href = url;
                                                a.download = `aishield_export_${new Date().toISOString().slice(0, 10)}.csv`;
                                                a.click();
                                                URL.revokeObjectURL(url);
                                                setToolResult(`✅ Export ${rows.length} firem dokončen`);
                                            } catch (e) {
                                                setToolResult(`❌ Chyba: ${e}`);
                                            }
                                        }}
                                        className="w-full px-4 py-2 bg-fuchsia-500/10 text-fuchsia-400 border border-fuchsia-500/20 rounded-xl hover:bg-fuchsia-500/20 transition-all text-sm font-medium"
                                    >
                                        📤 Exportovat CSV
                                    </button>
                                </Panel>

                                {/* STOP ALL SCANS */}
                                <Panel className="p-6 border-2 border-orange-500/30 bg-orange-950/20">
                                    <div className="text-3xl mb-3">🛑</div>
                                    <h3 className="font-semibold text-orange-400 mb-2">Zastavit všechny 24h scany</h3>
                                    <p className="text-xs text-orange-300/70 mb-4">
                                        Okamžitě zastaví VŠECHNY probíhající a čekající 24h deep scany. Workers se zastaví při dalším checku (do ~5 min).
                                    </p>
                                    <button
                                        onClick={async () => {
                                            const typed = window.prompt(
                                                "⚠️ POZOR: Toto zastaví VŠECHNY aktivní 24h deep scany!\n\nPro potvrzení napište STOP:"
                                            );
                                            if (typed !== "STOP") {
                                                if (typed !== null) setToolResult("❌ Zastavení zrušeno — nesprávné potvrzení.");
                                                return;
                                            }
                                            setToolResult("⏳ Zastavuji všechny scany...");
                                            try {
                                                const r = await stopAllScans();
                                                const lines = [
                                                    `${r.status === "ok" ? "✅" : "⚠️"} ${r.message}`,
                                                    ...r.scans.map(s => `  🔴 ${s.url} (${s.previous_status} → cancelled)`),
                                                ];
                                                if (r.errors?.length) {
                                                    lines.push(`\nChyby: ${r.errors.join(", ")}`);
                                                }
                                                setToolResult(lines.join("\n"));
                                                // Refresh scan monitor
                                                await loadScanMonitor();
                                            } catch (e) {
                                                setToolResult(`❌ Chyba: ${e}`);
                                            }
                                        }}
                                        className="w-full px-4 py-2.5 bg-orange-600 text-white border border-orange-500 rounded-xl hover:bg-orange-700 transition-all text-sm font-bold"
                                    >
                                        🛑 STOP ALL — Zastavit vše
                                    </button>
                                </Panel>

                                {/* FACTORY RESET */}
                                <Panel className="p-6 border-2 border-red-500/30 bg-red-950/20">
                                    <div className="text-3xl mb-3">💣</div>
                                    <h3 className="font-semibold text-red-400 mb-2">Tovární reset</h3>
                                    <p className="text-xs text-red-300/70 mb-4">
                                        Smaže VŠECHNA data: uživatele, firmy, objednávky, skeny, emaily, dokumenty. Ponechá RAG knowledge base.
                                    </p>
                                    <button
                                        onClick={async () => {
                                            const typed = window.prompt(
                                                "⚠️ POZOR: Toto smaže VŠECHNA data!\n\nPro potvrzení napište VYMAZ:"
                                            );
                                            if (typed !== "VYMAZ") {
                                                if (typed !== null) setToolResult("❌ Factory reset zrušen — nesprávné potvrzení.");
                                                return;
                                            }
                                            setToolResult("⏳ Factory reset probíhá...");
                                            try {
                                                const r = await factoryReset("VYMAZ");
                                                const lines = [
                                                    `${r.status === "ok" ? "✅" : "⚠️"} ${r.message}`,
                                                    `Auth: ${r.results.auth}`,
                                                    `DB: ${typeof r.results.db === "string" ? r.results.db : `${r.results.db.tables} tabulek — ${r.results.db.verification}`}`,
                                                    `Storage: ${r.results.storage}`,
                                                ];
                                                if (r.results.errors?.length) {
                                                    lines.push(`\nChyby: ${r.results.errors.join(", ")}`);
                                                }
                                                setToolResult(lines.join("\n"));
                                            } catch (e) {
                                                setToolResult(`❌ Chyba: ${e}`);
                                            }
                                        }}
                                        className="w-full px-4 py-2.5 bg-red-600 text-white border border-red-500 rounded-xl hover:bg-red-700 transition-all text-sm font-bold"
                                    >
                                        💣 FACTORY RESET — Vymazat vše
                                    </button>
                                </Panel>

                                {/* Data retention */}
                                <Panel className="p-6">
                                    <div className="text-3xl mb-3">🗑️</div>
                                    <h3 className="font-semibold text-white mb-2">Retence dat (90 dní)</h3>
                                    <p className="text-xs text-gray-400 mb-4">
                                        Agreguje staré analytické eventy do denních souhrnů a maže raw data starší 90 dní.
                                    </p>
                                    <button
                                        onClick={async () => {
                                            setToolResult(null);
                                            try {
                                                const res = await fetch(
                                                    `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/analytics/retention/cleanup?days=90`,
                                                    { method: "POST" }
                                                );
                                                const data = await res.json();
                                                setToolResult(`✅ Retence: smazáno ${data.deleted} eventů, agregováno ${data.aggregated} souhrnů (cutoff: ${data.cutoff_date})`);
                                            } catch (e) {
                                                setToolResult(`❌ Chyba: ${e}`);
                                            }
                                        }}
                                        className="w-full px-4 py-2 bg-red-500/10 text-red-400 border border-red-500/20 rounded-xl hover:bg-red-500/20 transition-all text-sm font-medium"
                                    >
                                        🗑️ Spustit Cleanup
                                    </button>
                                </Panel>
                            </div>

                            {toolResult && (
                                <Panel className="p-6">
                                    <pre className="text-xs text-green-400 overflow-x-auto whitespace-pre-wrap">
                                        {toolResult}
                                    </pre>
                                </Panel>
                            )}

                        </>
                    )}

                    {/* ══════════════════════════════════════════ */}
                    {tab === "analytika" && (
                        <>
                            {analyticsLoading && !analyticsStats ? (
                                <Panel className="p-12 text-center">
                                    <div className="text-2xl animate-spin inline-block mb-3">⏳</div>
                                    <div className="text-gray-400">Načítám analytiku…</div>
                                </Panel>
                            ) : analyticsStats ? (
                                <>
                                    {/* Period selector */}
                                    <div className="flex items-center gap-2 mb-2">
                                        {[7, 14, 30, 90].map(d => (
                                            <button
                                                key={d}
                                                onClick={() => setAnalyticsDays(d)}
                                                className={`px-3 py-1.5 rounded-lg text-xs border transition-all ${analyticsDays === d ? "bg-cyan-500/20 text-cyan-400 border-cyan-500/30" : "bg-white/5 text-gray-400 border-white/10 hover:bg-white/10"}`}
                                            >
                                                {d} dní
                                            </button>
                                        ))}
                                        <button
                                            onClick={loadAnalytics}
                                            disabled={analyticsLoading}
                                            className="ml-auto px-3 py-1.5 rounded-lg text-xs bg-white/5 border border-white/10 text-gray-400 hover:text-white hover:bg-white/10 transition-all"
                                        >
                                            {analyticsLoading ? "⏳" : "🔄"} Obnovit
                                        </button>
                                    </div>

                                    {/* Overview stats */}
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                        <StatCard icon="👁️" label="Celkem eventů" value={fmtNum(Object.values(analyticsStats.event_types).reduce((a, b) => a + b, 0))} accent="cyan" />
                                        <StatCard icon="🧑" label="Unikátní relace" value={fmtNum(analyticsSessions.length)} accent="fuchsia" />
                                        <StatCard icon="📄" label="Zobrazení stránek" value={fmtNum(analyticsStats.event_types["page_view"] || 0)} accent="green" />
                                        <StatCard icon="🔍" label="Skenů" value={fmtNum((analyticsStats.event_types["scan_started"] || 0))} accent="yellow" />
                                    </div>

                                    {/* Sub-tabs */}
                                    <div className="flex gap-2">
                                        {([
                                            { id: "funnel" as const, icon: "📊", label: "Konverzní funnel" },
                                            { id: "events" as const, icon: "📋", label: "Živé události" },
                                            { id: "sessions" as const, icon: "🧑", label: "Relace" },
                                            { id: "questionnaire" as const, icon: "📝", label: "Dotazník" },
                                        ]).map(st => (
                                            <button
                                                key={st.id}
                                                onClick={() => setAnalyticsTab(st.id)}
                                                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${analyticsTab === st.id ? "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30" : "bg-white/5 text-gray-400 border border-white/10 hover:bg-white/10"}`}
                                            >
                                                {st.icon} {st.label}
                                            </button>
                                        ))}
                                    </div>

                                    {/* Funnel tab */}
                                    {analyticsTab === "funnel" && (
                                        <>
                                            <Panel className="p-6">
                                                <h2 className="text-lg font-semibold text-cyan-400 mb-4">📊 Konverzní trychtýř</h2>
                                                <div className="space-y-2">
                                                    {(() => {
                                                        const funnelOrder = [
                                                            "page_view", "scan_url_entered", "scan_started", "scan_completed",
                                                            "email_entered", "email_verified", "registration_completed",
                                                            "questionnaire_started", "questionnaire_completed",
                                                            "pricing_page_viewed", "checkout_started", "payment_completed",
                                                        ];
                                                        const funnelLabels: Record<string, string> = {
                                                            page_view: "Návštěva stránky",
                                                            scan_url_entered: "Zadání URL",
                                                            scan_started: "Spuštění skenu",
                                                            scan_completed: "Dokončení skenu",
                                                            email_entered: "Zadání emailu",
                                                            email_verified: "Ověření emailu",
                                                            registration_completed: "Registrace",
                                                            questionnaire_started: "Zahájení dotazníku",
                                                            questionnaire_completed: "Dokončení dotazníku",
                                                            pricing_page_viewed: "Zobrazení ceníku",
                                                            checkout_started: "Zahájení objednávky",
                                                            payment_completed: "Platba dokončena",
                                                        };
                                                        const steps = funnelOrder.map(k => ({ stage: funnelLabels[k] || k, count: analyticsStats.funnel[k] || 0 }));
                                                        const maxCount = Math.max(...steps.map(s => s.count), 1);
                                                        const colors = [
                                                            "bg-cyan-500", "bg-blue-500", "bg-indigo-500", "bg-purple-500",
                                                            "bg-fuchsia-500", "bg-pink-500", "bg-rose-500", "bg-orange-500",
                                                            "bg-yellow-500", "bg-green-500", "bg-teal-500", "bg-emerald-500",
                                                        ];
                                                        return steps.map((step, i) => {
                                                            const pct = maxCount > 0 ? (step.count / maxCount) * 100 : 0;
                                                            const convRate = i > 0 && steps[i - 1].count > 0
                                                                ? ((step.count / steps[i - 1].count) * 100).toFixed(1)
                                                                : "100";
                                                            return (
                                                                <div key={step.stage} className="group">
                                                                    <div className="flex items-center justify-between mb-1">
                                                                        <span className="text-sm text-gray-300">{step.stage}</span>
                                                                        <div className="flex items-center gap-3">
                                                                            <span className="text-sm font-bold text-white">{fmtNum(step.count)}</span>
                                                                            {i > 0 && (
                                                                                <span className={`text-xs px-2 py-0.5 rounded-full ${Number(convRate) > 50 ? "bg-green-500/20 text-green-400" : Number(convRate) > 20 ? "bg-yellow-500/20 text-yellow-400" : "bg-red-500/20 text-red-400"}`}>
                                                                                    {convRate}%
                                                                                </span>
                                                                            )}
                                                                        </div>
                                                                    </div>
                                                                    <div className="h-6 bg-white/5 rounded-lg overflow-hidden">
                                                                        <div
                                                                            className={`h-full ${colors[i % colors.length]} opacity-60 rounded-lg transition-all duration-500`}
                                                                            style={{ width: `${Math.max(pct, 2)}%` }}
                                                                        />
                                                                    </div>
                                                                </div>
                                                            );
                                                        });
                                                    })()}
                                                </div>
                                            </Panel>

                                            {/* Top pages & daily */}
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                <Panel className="p-6">
                                                    <h3 className="font-semibold text-fuchsia-400 mb-3">🔝 Top stránky</h3>
                                                    <div className="space-y-2">
                                                        {analyticsStats.top_pages.slice(0, 10).map(p => (
                                                            <div key={p.page} className="flex items-center justify-between text-sm">
                                                                <span className="text-gray-300 truncate max-w-[200px]" title={p.page}>{p.page}</span>
                                                                <span className="text-white font-mono">{fmtNum(p.views)}</span>
                                                            </div>
                                                        ))}
                                                        {analyticsStats.top_pages.length === 0 && (
                                                            <div className="text-gray-500 text-sm">Zatím žádná data</div>
                                                        )}
                                                    </div>
                                                </Panel>
                                                <Panel className="p-6">
                                                    <h3 className="font-semibold text-green-400 mb-3">📆 Denní aktivita</h3>
                                                    <div className="space-y-1">
                                                        {analyticsStats.daily.slice(-14).map(d => {
                                                            const maxD = Math.max(...analyticsStats.daily.map(x => x.count), 1);
                                                            const w = (d.count / maxD) * 100;
                                                            return (
                                                                <div key={d.date} className="flex items-center gap-2 text-xs">
                                                                    <span className="text-gray-500 w-16 shrink-0">{d.date.slice(5)}</span>
                                                                    <div className="flex-1 h-4 bg-white/5 rounded overflow-hidden">
                                                                        <div className="h-full bg-green-500/50 rounded" style={{ width: `${Math.max(w, 2)}%` }} />
                                                                    </div>
                                                                    <span className="text-white font-mono w-8 text-right">{d.count}</span>
                                                                </div>
                                                            );
                                                        })}
                                                        {analyticsStats.daily.length === 0 && (
                                                            <div className="text-gray-500 text-sm">Zatím žádná data</div>
                                                        )}
                                                    </div>
                                                </Panel>
                                            </div>

                                            {/* Event types breakdown */}
                                            <Panel className="p-6">
                                                <h3 className="font-semibold text-orange-400 mb-3">🏷️ Typy eventů</h3>
                                                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                                                    {Object.entries(analyticsStats.event_types)
                                                        .sort(([, a], [, b]) => b - a)
                                                        .map(([name, count]) => (
                                                            <button
                                                                key={name}
                                                                onClick={() => { setAnalyticsEventFilter(name); setAnalyticsTab("events"); }}
                                                                className="flex items-center justify-between bg-black/30 rounded-lg px-3 py-2 hover:bg-white/10 transition-all cursor-pointer"
                                                            >
                                                                <span className="text-xs text-gray-300 truncate">{name}</span>
                                                                <span className="text-xs font-bold text-white ml-2">{count}</span>
                                                            </button>
                                                        ))}
                                                </div>
                                            </Panel>
                                        </>
                                    )}

                                    {/* Events tab */}
                                    {analyticsTab === "events" && (
                                        <Panel className="p-6">
                                            <div className="flex items-center justify-between mb-4">
                                                <h2 className="text-lg font-semibold text-cyan-400">📋 Živé události</h2>
                                                <div className="flex items-center gap-2">
                                                    <select
                                                        value={analyticsEventFilter}
                                                        onChange={e => setAnalyticsEventFilter(e.target.value)}
                                                        className="bg-black/30 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-gray-300"
                                                    >
                                                        <option value="">Všechny eventy</option>
                                                        {Object.keys(analyticsStats.event_types).sort().map(name => (
                                                            <option key={name} value={name}>{name}</option>
                                                        ))}
                                                    </select>
                                                </div>
                                            </div>
                                            <div className="overflow-x-auto">
                                                <table className="w-full text-xs">
                                                    <thead>
                                                        <tr className="text-gray-500 border-b border-white/5">
                                                            <th className="text-left py-2 pr-4">Čas</th>
                                                            <th className="text-left py-2 pr-4">Event</th>
                                                            <th className="text-left py-2 pr-4">Stránka</th>
                                                            <th className="text-left py-2 pr-4">Session</th>
                                                            <th className="text-left py-2 pr-4">User</th>
                                                            <th className="text-left py-2 pr-4">Zařízení</th>
                                                            <th className="text-left py-2">Properties</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {analyticsEvents
                                                            .filter(e => !analyticsEventFilter || e.event_name === analyticsEventFilter)
                                                            .slice(0, 100)
                                                            .map(ev => (
                                                                <tr key={ev.id} className="border-b border-white/5 hover:bg-white/5">
                                                                    <td className="py-2 pr-4 text-gray-500 whitespace-nowrap">{fmtDateTime(ev.created_at)}</td>
                                                                    <td className="py-2 pr-4">
                                                                        <span className="px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-400 text-xs">{ev.event_name}</span>
                                                                    </td>
                                                                    <td className="py-2 pr-4 text-gray-300 truncate max-w-[150px]" title={ev.page_url}>{ev.page_url?.replace(/https?:\/\/[^/]+/, "") || "—"}</td>
                                                                    <td className="py-2 pr-4 text-gray-500 font-mono">{ev.session_id?.slice(0, 12) || "—"}</td>
                                                                    <td className="py-2 pr-4 text-gray-400">{ev.user_email || "—"}</td>
                                                                    <td className="py-2 pr-4 text-gray-500">{[ev.device, ev.browser].filter(Boolean).join(" / ") || "—"}</td>
                                                                    <td className="py-2">
                                                                        {Object.keys(ev.properties || {}).length > 0 ? (
                                                                            <span className="text-gray-500 cursor-help" title={JSON.stringify(ev.properties, null, 2)}>
                                                                                {JSON.stringify(ev.properties).slice(0, 60)}{JSON.stringify(ev.properties).length > 60 ? "…" : ""}
                                                                            </span>
                                                                        ) : "—"}
                                                                    </td>
                                                                </tr>
                                                            ))}
                                                    </tbody>
                                                </table>
                                                {analyticsEvents.filter(e => !analyticsEventFilter || e.event_name === analyticsEventFilter).length === 0 && (
                                                    <div className="text-center text-gray-500 py-8">Zatím žádné eventy</div>
                                                )}
                                            </div>
                                        </Panel>
                                    )}

                                    {/* Sessions tab */}
                                    {analyticsTab === "sessions" && (
                                        <Panel className="p-6">
                                            <h2 className="text-lg font-semibold text-fuchsia-400 mb-4">🧑 Relace ({analyticsSessions.length})</h2>
                                            <div className="overflow-x-auto">
                                                <table className="w-full text-xs">
                                                    <thead>
                                                        <tr className="text-gray-500 border-b border-white/5">
                                                            <th className="text-left py-2 pr-4">Session ID</th>
                                                            <th className="text-left py-2 pr-4">Zařízení</th>
                                                            <th className="text-left py-2 pr-4">Prohlížeč</th>
                                                            <th className="text-left py-2 pr-4">OS</th>
                                                            <th className="text-left py-2 pr-4">User</th>
                                                            <th className="text-right py-2 pr-4">Stránky</th>
                                                            <th className="text-right py-2 pr-4">Eventy</th>
                                                            <th className="text-left py-2 pr-4">První</th>
                                                            <th className="text-left py-2">Poslední</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {analyticsSessions.map(s => (
                                                            <tr key={s.session_id} className="border-b border-white/5 hover:bg-white/5">
                                                                <td className="py-2 pr-4 text-cyan-400 font-mono">{s.session_id.slice(0, 16)}</td>
                                                                <td className="py-2 pr-4 text-gray-300">{s.device || "—"}</td>
                                                                <td className="py-2 pr-4 text-gray-300">{s.browser || "—"}</td>
                                                                <td className="py-2 pr-4 text-gray-500">{s.os || "—"}</td>
                                                                <td className="py-2 pr-4 text-gray-400">{s.user_email || "—"}</td>
                                                                <td className="py-2 pr-4 text-right text-white font-mono">{s.page_count}</td>
                                                                <td className="py-2 pr-4 text-right text-white font-mono">{s.event_count}</td>
                                                                <td className="py-2 pr-4 text-gray-500 whitespace-nowrap">{fmtDateTime(s.first_seen)}</td>
                                                                <td className="py-2 text-gray-500 whitespace-nowrap">{fmtDateTime(s.last_seen)}</td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                                {analyticsSessions.length === 0 && (
                                                    <div className="text-center text-gray-500 py-8">Zatím žádné relace</div>
                                                )}
                                            </div>
                                        </Panel>
                                    )}

                                    {/* Questionnaire analytics tab */}
                                    {analyticsTab === "questionnaire" && (
                                        <>
                                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                                <StatCard icon="❓" label="Nevím odpovědi" value={fmtNum(analyticsStats.questionnaire.total_nevim_answers)} accent="red" sub="Celkem &apos;Nevím&apos; odpovědí" />
                                                <StatCard icon="✏️" label="Otázek sledovaných" value={Object.keys(analyticsStats.questionnaire.avg_time_per_question).length.toString()} accent="cyan" sub="Otázek s daty" />
                                                <StatCard icon="🔄" label="Změn odpovědí" value={fmtNum(Object.values(analyticsStats.questionnaire.changes_per_question).reduce((a, b) => a + b, 0))} accent="yellow" sub="Celkem přehodnocení" />
                                            </div>

                                            <Panel className="p-6">
                                                <h2 className="text-lg font-semibold text-cyan-400 mb-4">⏱️ Průměrný čas na otázku (sekundy)</h2>
                                                <div className="space-y-2">
                                                    {Object.entries(analyticsStats.questionnaire.avg_time_per_question)
                                                        .sort(([a], [b]) => Number(a) - Number(b))
                                                        .map(([q, ms]) => {
                                                            const sec = (ms / 1000).toFixed(1);
                                                            const maxMs = Math.max(...Object.values(analyticsStats.questionnaire.avg_time_per_question), 1);
                                                            const w = (ms / maxMs) * 100;
                                                            return (
                                                                <div key={q} className="flex items-center gap-3">
                                                                    <span className="text-sm text-gray-400 w-20 shrink-0">Otázka {q}</span>
                                                                    <div className="flex-1 h-5 bg-white/5 rounded overflow-hidden">
                                                                        <div
                                                                            className={`h-full rounded transition-all ${Number(sec) > 60 ? "bg-red-500/50" : Number(sec) > 30 ? "bg-yellow-500/50" : "bg-cyan-500/50"}`}
                                                                            style={{ width: `${Math.max(w, 3)}%` }}
                                                                        />
                                                                    </div>
                                                                    <span className="text-sm font-mono text-white w-16 text-right">{sec}s</span>
                                                                </div>
                                                            );
                                                        })}
                                                    {Object.keys(analyticsStats.questionnaire.avg_time_per_question).length === 0 && (
                                                        <div className="text-gray-500 text-sm">Zatím žádná data z dotazníku</div>
                                                    )}
                                                </div>
                                            </Panel>

                                            <Panel className="p-6">
                                                <h2 className="text-lg font-semibold text-yellow-400 mb-4">🔄 Změny odpovědí na otázku</h2>
                                                <div className="space-y-2">
                                                    {Object.entries(analyticsStats.questionnaire.changes_per_question)
                                                        .sort(([, a], [, b]) => b - a)
                                                        .map(([q, count]) => {
                                                            const maxC = Math.max(...Object.values(analyticsStats.questionnaire.changes_per_question), 1);
                                                            const w = (count / maxC) * 100;
                                                            return (
                                                                <div key={q} className="flex items-center gap-3">
                                                                    <span className="text-sm text-gray-400 w-20 shrink-0">Otázka {q}</span>
                                                                    <div className="flex-1 h-5 bg-white/5 rounded overflow-hidden">
                                                                        <div className="h-full bg-yellow-500/50 rounded" style={{ width: `${Math.max(w, 3)}%` }} />
                                                                    </div>
                                                                    <span className="text-sm font-mono text-white w-8 text-right">{count}</span>
                                                                </div>
                                                            );
                                                        })}
                                                    {Object.keys(analyticsStats.questionnaire.changes_per_question).length === 0 && (
                                                        <div className="text-gray-500 text-sm">Zatím žádné změny odpovědí</div>
                                                    )}
                                                </div>
                                            </Panel>
                                        </>
                                    )}
                                </>
                            ) : (
                                <Panel className="p-12 text-center">
                                    <div className="text-4xl mb-3">📉</div>
                                    <div className="text-gray-400">Analytika není k dispozici</div>
                                    <button onClick={loadAnalytics} className="mt-4 px-4 py-2 bg-cyan-500/10 text-cyan-400 rounded-lg hover:bg-cyan-500/20 transition-all text-sm">
                                        🔄 Zkusit znovu
                                    </button>
                                </Panel>
                            )}
                        </>
                    )}

                    {/* ══════════════════════════════════════════ */}
                    {tab === "predplatne" && (
                        <>
                            {subscriptionsLoading && subscriptions.length === 0 ? (
                                <Panel className="p-12 text-center">
                                    <div className="text-2xl animate-spin inline-block mb-3">⏳</div>
                                    <div className="text-gray-400">Načítám předplatné…</div>
                                </Panel>
                            ) : (
                                <>
                                    {/* Summary cards */}
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                        <StatCard icon="💳" label="Celkem" value={subscriptions.length.toString()} accent="cyan" />
                                        <StatCard icon="✅" label="Aktivní" value={subscriptions.filter(s => s.status === "active").length.toString()} accent="green" />
                                        <StatCard icon="⚠️" label="Po splatnosti" value={subscriptions.filter(s => s.days_overdue > 0).length.toString()} accent="red" />
                                        <StatCard icon="💰" label="MRR" value={fmtMoney(subscriptions.filter(s => s.status === "active").reduce((sum, s) => sum + (s.amount || 0), 0))} accent="fuchsia" sub="Měsíční příjem" />
                                    </div>

                                    {/* Filter */}
                                    <div className="flex items-center gap-2">
                                        {(["all", "active", "overdue", "cancelled"] as const).map(f => {
                                            const labels: Record<string, string> = { all: "Vše", active: "Aktivní", overdue: "Po splatnosti", cancelled: "Zrušené" };
                                            const counts: Record<string, number> = {
                                                all: subscriptions.length,
                                                active: subscriptions.filter(s => s.status === "active").length,
                                                overdue: subscriptions.filter(s => s.days_overdue > 0).length,
                                                cancelled: subscriptions.filter(s => s.status === "cancelled").length,
                                            };
                                            return (
                                                <button
                                                    key={f}
                                                    onClick={() => setSubscriptionFilter(f)}
                                                    className={`px-3 py-1.5 rounded-lg text-xs border transition-all ${subscriptionFilter === f ? "bg-cyan-500/20 text-cyan-400 border-cyan-500/30" : "bg-white/5 text-gray-400 border-white/10 hover:bg-white/10"}`}
                                                >
                                                    {labels[f]} ({counts[f]})
                                                </button>
                                            );
                                        })}
                                    </div>

                                    {/* Subscriptions table */}
                                    <Panel className="p-6">
                                        <div className="overflow-x-auto">
                                            <table className="w-full text-xs">
                                                <thead>
                                                    <tr className="text-gray-500 border-b border-white/5">
                                                        <th className="text-left py-2 pr-4">Firma</th>
                                                        <th className="text-left py-2 pr-4">Email</th>
                                                        <th className="text-left py-2 pr-4">Plán</th>
                                                        <th className="text-right py-2 pr-4">Částka</th>
                                                        <th className="text-left py-2 pr-4">Status</th>
                                                        <th className="text-left py-2 pr-4">Další platba</th>
                                                        <th className="text-right py-2 pr-4">Po splatnosti</th>
                                                        <th className="text-left py-2 pr-4">Upomínka</th>
                                                        <th className="text-left py-2">Akce</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {subscriptions
                                                        .filter(s => {
                                                            if (subscriptionFilter === "active") return s.status === "active";
                                                            if (subscriptionFilter === "overdue") return s.days_overdue > 0;
                                                            if (subscriptionFilter === "cancelled") return s.status === "cancelled";
                                                            return true;
                                                        })
                                                        .sort((a, b) => b.days_overdue - a.days_overdue)
                                                        .map(sub => (
                                                            <tr key={sub.id} className={`border-b border-white/5 hover:bg-white/5 ${sub.days_overdue > 0 ? "bg-red-500/5" : ""}`}>
                                                                <td className="py-2 pr-4 text-white font-medium">{sub.company_name || "—"}</td>
                                                                <td className="py-2 pr-4 text-gray-400">{sub.company_email || "—"}</td>
                                                                <td className="py-2 pr-4">
                                                                    <span className="px-2 py-0.5 rounded-full bg-fuchsia-500/20 text-fuchsia-400 text-xs">{sub.plan || "—"}</span>
                                                                </td>
                                                                <td className="py-2 pr-4 text-right text-white font-mono">{fmtMoney(sub.amount)}</td>
                                                                <td className="py-2 pr-4">
                                                                    <span className={`px-2 py-0.5 rounded-full text-xs ${sub.status === "active" ? "bg-green-500/20 text-green-400" : sub.status === "cancelled" ? "bg-red-500/20 text-red-400" : "bg-yellow-500/20 text-yellow-400"}`}>
                                                                        {sub.status}
                                                                    </span>
                                                                </td>
                                                                <td className="py-2 pr-4 text-gray-400">{fmtDate(sub.next_payment_date)}</td>
                                                                <td className={`py-2 pr-4 text-right font-mono ${sub.days_overdue > 0 ? "text-red-400 font-bold" : "text-gray-500"}`}>
                                                                    {sub.days_overdue > 0 ? `${sub.days_overdue} dní` : "—"}
                                                                </td>
                                                                <td className="py-2 pr-4">
                                                                    {sub.reminder_sent ? (
                                                                        <span className="text-yellow-400 text-xs">✉️ Odesláno</span>
                                                                    ) : (
                                                                        <span className="text-gray-500 text-xs">—</span>
                                                                    )}
                                                                </td>
                                                                <td className="py-2">
                                                                    {sub.days_overdue > 0 && (
                                                                        <button
                                                                            disabled={reminderSending === sub.id}
                                                                            onClick={async () => {
                                                                                setReminderSending(sub.id);
                                                                                try {
                                                                                    await sendSubscriptionReminder(sub.id);
                                                                                    await loadSubscriptions();
                                                                                } catch (e) {
                                                                                    console.error("Reminder error:", e);
                                                                                } finally {
                                                                                    setReminderSending(null);
                                                                                }
                                                                            }}
                                                                            className="px-3 py-1 rounded-lg text-xs bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 transition-all disabled:opacity-50"
                                                                        >
                                                                            {reminderSending === sub.id ? "⏳" : "📧"} Upomínka
                                                                        </button>
                                                                    )}
                                                                </td>
                                                            </tr>
                                                        ))}
                                                </tbody>
                                            </table>
                                            {subscriptions.length === 0 && (
                                                <div className="text-center text-gray-500 py-8">
                                                    <div className="text-3xl mb-2">💳</div>
                                                    Zatím žádná předplatná
                                                </div>
                                            )}
                                        </div>
                                    </Panel>
                                </>
                            )}
                        </>
                    )}

                    {/* TAB Faktury odstraněn — obsah sloučen do Objednávky */}
                    {/* ══════════════════════════════════════════ */}
                    {/*  TAB: 24h Testy (Scan Monitor)           */}
                    {/* ══════════════════════════════════════════ */}
                    {tab === "testy24h" && (
                        <>
                            {scanMonitorLoading && !scanMonitor ? (
                                <div className="text-center py-12">
                                    <div className="text-4xl mb-3 animate-bounce">🔬</div>
                                    <div className="text-cyan-400 animate-pulse">Načítám data o testech…</div>
                                </div>
                            ) : scanMonitor ? (
                                <>
                                    {/* KPI karty */}
                                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                                        <StatCard icon="🔄" label="Aktivní deep scany" value={scanMonitor.stats.active_deep_scans} accent="fuchsia" />
                                        <StatCard icon="⏳" label="Aktivní quick scany" value={scanMonitor.stats.active_quick_scans} accent="yellow" />
                                        <StatCard icon="✅" label="Dokončeno (rok)" value={scanMonitor.stats.total_deep_done} accent="green" />
                                        <StatCard icon="❌" label="Chyby (rok)" value={scanMonitor.stats.total_deep_error} accent="red" />
                                        <StatCard icon="📊" label="Celkem (rok)" value={scanMonitor.stats.completed_deep_scans_year} accent="cyan" />
                                    </div>

                                    {/* Aktivní 24h deep scany */}
                                    {scanMonitor.active_deep.length > 0 && (
                                        <Panel className="overflow-hidden">
                                            <div className="px-5 py-4 border-b border-white/10">
                                                <h3 className="text-base font-bold text-white flex items-center gap-2">
                                                    <span className="text-fuchsia-400">🔬</span> Probíhající 24h testy
                                                    <span className="ml-2 px-2 py-0.5 rounded-full bg-fuchsia-500/20 text-fuchsia-400 text-xs border border-fuchsia-500/30">
                                                        {scanMonitor.active_deep.length}
                                                    </span>
                                                </h3>
                                            </div>
                                            <div className="divide-y divide-white/5">
                                                {scanMonitor.active_deep.map((scan) => {
                                                    const flags: Record<string, string> = { cz: "🇨🇿", gb: "🇬🇧", us: "🇺🇸", br: "🇧🇷", jp: "🇯🇵", za: "🇿🇦", au: "🇦🇺" };
                                                    const countryNames: Record<string, string> = { cz: "Česko", gb: "Británie", us: "USA", br: "Brazílie", jp: "Japonsko", za: "J. Afrika", au: "Austrálie" };
                                                    return (
                                                        <div key={scan.id} className="px-5 py-4 hover:bg-white/[0.02] transition-colors">
                                                            <div className="flex items-center justify-between mb-2">
                                                                <div className="flex items-center gap-3">
                                                                    <div className="w-2 h-2 rounded-full bg-fuchsia-400 animate-pulse" />
                                                                    <span className="font-medium text-white">{scan.company_name}</span>
                                                                    <span className="text-xs text-gray-500">{scan.url_scanned}</span>
                                                                </div>
                                                                <span className={`px-2 py-0.5 rounded text-xs ${scan.deep_scan_status === "running" ? "bg-fuchsia-500/20 text-fuchsia-400" : "bg-yellow-500/20 text-yellow-400"}`}>
                                                                    {scan.deep_scan_status === "running" ? "🔄 Probíhá" : "⏳ Čeká"}
                                                                </span>
                                                            </div>
                                                            {/* Progress bar */}
                                                            {scan.deep_scan_status === "running" && (
                                                                <div className="mt-2">
                                                                    <div className="flex justify-between text-xs text-gray-400 mb-1">
                                                                        <span>Průběh: {scan.deep_scan_progress ?? 0}%</span>
                                                                        <span>{scan.elapsed_hours ?? 0}h / 24h</span>
                                                                    </div>
                                                                    <div className="w-full bg-white/5 rounded-full h-2 overflow-hidden">
                                                                        <div
                                                                            className="h-full rounded-full bg-gradient-to-r from-fuchsia-500 to-cyan-500 transition-all duration-1000"
                                                                            style={{ width: `${scan.deep_scan_progress ?? 0}%` }}
                                                                        />
                                                                    </div>
                                                                </div>
                                                            )}
                                                            {/* ── Round Schedule (collapsible) ── */}
                                                            {scan.round_schedule && scan.round_schedule.length > 0 && (
                                                                <details className="mt-3 rounded-lg border border-white/[0.08] bg-white/[0.02] overflow-hidden group">
                                                                    <summary className="px-3 py-2 border-b border-white/[0.06] bg-white/[0.02] cursor-pointer select-none flex items-center gap-2 hover:bg-white/[0.04] transition-colors list-none">
                                                                        <svg className="w-3 h-3 text-slate-500 transition-transform group-open:rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
                                                                        <span className="text-xs font-semibold text-slate-300">📋 Rozpis 6 kol · 4h intervaly · 4 země/kolo</span>
                                                                        <span className="ml-auto text-[10px] text-slate-500">{scan.round_schedule.filter(r => r.status === 'done').length}/{scan.round_schedule.length} dokončeno</span>
                                                                    </summary>
                                                                    <div className="divide-y divide-white/[0.04]">
                                                                        {scan.round_schedule.map((round) => {
                                                                            const isRunning = round.status === "running";
                                                                            const isDone = round.status === "done";
                                                                            const isScheduled = round.status === "scheduled";
                                                                            const startDate = new Date(round.starts_at);
                                                                            const endDate = new Date(round.ends_at);
                                                                            const now = new Date();
                                                                            // Countdown
                                                                            let countdown = "";
                                                                            if (isScheduled) {
                                                                                const diffMs = startDate.getTime() - now.getTime();
                                                                                const diffH = Math.floor(diffMs / 3600000);
                                                                                const diffM = Math.floor((diffMs % 3600000) / 60000);
                                                                                countdown = diffH > 0 ? `za ${diffH}h ${diffM}min` : `za ${diffM}min`;
                                                                            } else if (isRunning) {
                                                                                const diffMs = endDate.getTime() - now.getTime();
                                                                                const diffH = Math.floor(diffMs / 3600000);
                                                                                const diffM = Math.floor((diffMs % 3600000) / 60000);
                                                                                countdown = diffH > 0 ? `zbývá ${diffH}h ${diffM}min` : `zbývá ${diffM}min`;
                                                                            }
                                                                            const timeStr = startDate.toLocaleTimeString("cs-CZ", { hour: "2-digit", minute: "2-digit", timeZone: "Europe/Prague" });
                                                                            const endTimeStr = endDate.toLocaleTimeString("cs-CZ", { hour: "2-digit", minute: "2-digit", timeZone: "Europe/Prague" });
                                                                            return (
                                                                                <div key={round.round} className={`px-3 py-2 flex items-center gap-3 text-xs ${isRunning ? "bg-fuchsia-500/[0.06]" : ""}`}>
                                                                                    {/* Round number + status icon */}
                                                                                    <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold ${isDone ? "bg-green-500/20 text-green-400 border border-green-500/30" : isRunning ? "bg-fuchsia-500/20 text-fuchsia-400 border border-fuchsia-500/30 animate-pulse" : "bg-white/[0.05] text-slate-500 border border-white/10"}`}>
                                                                                        {isDone ? "✓" : round.round}
                                                                                    </div>
                                                                                    {/* Time */}
                                                                                    <div className={`w-[90px] flex-shrink-0 font-mono ${isDone ? "text-green-400/70" : isRunning ? "text-fuchsia-300" : "text-slate-500"}`}>
                                                                                        {timeStr}–{endTimeStr}
                                                                                    </div>
                                                                                    {/* Countries */}
                                                                                    <div className="flex items-center gap-1 flex-shrink-0">
                                                                                        {round.countries.map((c, ci) => (
                                                                                            <span key={ci} className={`${isDone ? "opacity-60" : isRunning ? "" : "opacity-40"}`} title={`${flags[c] || ""} ${countryNames[c] || c.toUpperCase()}`}>
                                                                                                {flags[c] || c.toUpperCase()}
                                                                                            </span>
                                                                                        ))}
                                                                                    </div>
                                                                                    {/* Country names */}
                                                                                    <div className={`hidden sm:block text-[10px] ${isDone ? "text-green-400/50" : isRunning ? "text-fuchsia-300/70" : "text-slate-600"}`}>
                                                                                        {round.countries.map((c) => countryNames[c] || c.toUpperCase()).join(", ")}
                                                                                    </div>
                                                                                    {/* Status badge + countdown */}
                                                                                    <div className="ml-auto flex items-center gap-2">
                                                                                        {isDone && <span className="text-green-400 text-[10px]">✅ Dokončeno</span>}
                                                                                        {isRunning && (
                                                                                            <span className="flex items-center gap-1">
                                                                                                <span className="relative flex h-1.5 w-1.5">
                                                                                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-fuchsia-400 opacity-75" />
                                                                                                    <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-fuchsia-500" />
                                                                                                </span>
                                                                                                <span className="text-fuchsia-400 text-[10px] font-medium">Probíhá · {countdown}</span>
                                                                                            </span>
                                                                                        )}
                                                                                        {isScheduled && (
                                                                                            <span className="text-slate-500 text-[10px]">⏱ {countdown}</span>
                                                                                        )}
                                                                                    </div>
                                                                                </div>
                                                                            );
                                                                        })}
                                                                    </div>
                                                                </details>
                                                            )}
                                                            {/* Geo countries scanned so far */}
                                                            {scan.geo_countries_scanned && scan.geo_countries_scanned.length > 0 && (
                                                                <div className="mt-2 flex items-center gap-1">
                                                                    <span className="text-xs text-gray-500">Otestované země:</span>
                                                                    {scan.geo_countries_scanned.map((c) => (
                                                                        <span key={c} className="text-sm" title={c.toUpperCase()}>{flags[c.toLowerCase()] || c}</span>
                                                                    ))}
                                                                    <span className="text-xs text-gray-600 ml-1">({scan.geo_countries_scanned.length}/7)</span>
                                                                </div>
                                                            )}
                                                            <div className="mt-1 text-xs text-gray-500">
                                                                Zahájeno: {fmtDateTime(scan.deep_scan_started_at)} · Email: {scan.company_email || "—"}
                                                                {scan.deep_scan_total_findings != null && scan.deep_scan_total_findings > 0 && (
                                                                    <span className="ml-2 text-cyan-400">· Nalezeno: {scan.deep_scan_total_findings} AI systémů</span>
                                                                )}
                                                            </div>
                                                            {/* Cancel button */}
                                                            <div className="mt-3 flex items-center gap-3">
                                                                <button
                                                                    onClick={async () => {
                                                                        if (!confirm(`Opravdu chcete zrušit 24h test pro ${scan.company_name}?\n\nURL: ${scan.url_scanned}\n\nTest bude zastaven do ~5 minut.`)) return;
                                                                        try {
                                                                            const result = await cancelDeepScan(scan.id);
                                                                            alert(`✅ ${result.message}`);
                                                                            await loadScanMonitor();
                                                                        } catch (err: unknown) {
                                                                            alert(`❌ Chyba: ${err instanceof Error ? err.message : "Neznámá chyba"}`);
                                                                        }
                                                                    }}
                                                                    className="px-3 py-1.5 rounded-lg text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 hover:border-red-500/40 transition-all"
                                                                >
                                                                    ⛔ Zastavit test
                                                                </button>
                                                                <span className="text-[10px] text-gray-600">Worker zastaví do ~5 min</span>
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </Panel>
                                    )}

                                    {/* Aktivní quick scany */}
                                    {scanMonitor.active_quick.length > 0 && (
                                        <Panel className="overflow-hidden">
                                            <div className="px-5 py-4 border-b border-white/10">
                                                <h3 className="text-base font-bold text-white flex items-center gap-2">
                                                    <span className="text-yellow-400">⚡</span> Aktivní quick scany
                                                    <span className="ml-2 px-2 py-0.5 rounded-full bg-yellow-500/20 text-yellow-400 text-xs border border-yellow-500/30">
                                                        {scanMonitor.active_quick.length}
                                                    </span>
                                                </h3>
                                            </div>
                                            <div className="overflow-x-auto">
                                                <table className="w-full text-sm">
                                                    <thead>
                                                        <tr className="text-xs text-gray-500 border-b border-white/5">
                                                            <th className="text-left px-4 py-2">Firma</th>
                                                            <th className="text-left px-4 py-2">URL</th>
                                                            <th className="text-left px-4 py-2">Status</th>
                                                            <th className="text-left px-4 py-2">Zahájeno</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody className="divide-y divide-white/5">
                                                        {scanMonitor.active_quick.map((scan) => (
                                                            <tr key={scan.id} className="hover:bg-white/[0.02]">
                                                                <td className="px-4 py-2 text-white">{scan.company_name}</td>
                                                                <td className="px-4 py-2 text-gray-400 truncate max-w-[200px]">{scan.url_scanned}</td>
                                                                <td className="px-4 py-2">
                                                                    <span className={`px-2 py-0.5 rounded text-xs ${scan.status === "running" ? "bg-yellow-500/20 text-yellow-400" : "bg-gray-500/20 text-gray-400"}`}>
                                                                        {scan.status}
                                                                    </span>
                                                                </td>
                                                                <td className="px-4 py-2 text-gray-500 text-xs">{fmtDateTime(scan.started_at || scan.created_at)}</td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                        </Panel>
                                    )}

                                    {/* Dokončené 24h testy (30 dní) */}
                                    <Panel className="overflow-hidden">
                                        <div className="px-5 py-4 border-b border-white/10">
                                            <h3 className="text-base font-bold text-white flex items-center gap-2">
                                                <span className="text-green-400">📋</span> Dokončené 24h testy (posledních 12 měsíců)
                                                <span className="ml-2 px-2 py-0.5 rounded-full bg-green-500/20 text-green-400 text-xs border border-green-500/30">
                                                    {scanMonitor.completed_deep.length}
                                                </span>
                                            </h3>
                                        </div>
                                        <div className="divide-y divide-white/5">
                                            {scanMonitor.completed_deep.length === 0 ? (
                                                <div className="text-center text-gray-500 py-8">
                                                    <div className="text-3xl mb-2">🔬</div>
                                                    Žádné dokončené 24h testy za poslední rok
                                                </div>
                                            ) : (
                                                scanMonitor.completed_deep.map((scan) => (
                                                    <div key={scan.id} className="hover:bg-white/[0.02] transition-colors">
                                                        {/* Hlavní řádek */}
                                                        <div
                                                            className="px-5 py-4 cursor-pointer"
                                                            onClick={async () => {
                                                                if (expandedScan === scan.id) {
                                                                    setExpandedScan(null);
                                                                    setScanFindings(null);
                                                                } else {
                                                                    setExpandedScan(scan.id);
                                                                    setScanFindingsLoading(true);
                                                                    try {
                                                                        const f = await getScanFindings(scan.id);
                                                                        setScanFindings(f);
                                                                    } catch (e) {
                                                                        console.error("Findings load error:", e);
                                                                    } finally {
                                                                        setScanFindingsLoading(false);
                                                                    }
                                                                }
                                                            }}
                                                        >
                                                            <div className="flex items-center justify-between">
                                                                <div className="flex items-center gap-3">
                                                                    <span className="text-lg">
                                                                        {scan.deep_scan_status === "done" ? "✅" : "❌"}
                                                                    </span>
                                                                    <div>
                                                                        <div className="font-medium text-white">{scan.company_name}</div>
                                                                        <div className="text-xs text-gray-500">{scan.url_scanned}</div>
                                                                    </div>
                                                                </div>
                                                                <div className="flex items-center gap-4">
                                                                    {/* Findings count */}
                                                                    <div className="text-right">
                                                                        <div className="text-lg font-bold text-white">
                                                                            {scan.deep_scan_total_findings ?? scan.total_findings ?? 0}
                                                                        </div>
                                                                        <div className="text-xs text-gray-500">nálezů</div>
                                                                    </div>
                                                                    {/* Email status */}
                                                                    <div className="text-right min-w-[100px]">
                                                                        {scan.email_status?.sent ? (
                                                                            <div>
                                                                                <span className="px-2 py-0.5 rounded text-xs bg-green-500/20 text-green-400">
                                                                                    📧 Odesláno
                                                                                </span>
                                                                                {scan.email_status.opened_at && (
                                                                                    <div className="text-xs text-cyan-400 mt-0.5">👁 Otevřeno</div>
                                                                                )}
                                                                                {scan.email_status.clicked_at && (
                                                                                    <div className="text-xs text-fuchsia-400 mt-0.5">🔗 Kliknuto</div>
                                                                                )}
                                                                            </div>
                                                                        ) : (
                                                                            <span className="px-2 py-0.5 rounded text-xs bg-orange-500/20 text-orange-400">
                                                                                ⚠️ Neodesláno
                                                                            </span>
                                                                        )}
                                                                    </div>
                                                                    {/* Resend button */}
                                                                    <button
                                                                        onClick={async (e) => {
                                                                            e.stopPropagation();
                                                                            try {
                                                                                await previewScanReport(scan.id);
                                                                            } catch (err) {
                                                                                alert(`Chyba náhledu: ${err}`);
                                                                            }
                                                                        }}
                                                                        className="px-3 py-1.5 rounded-lg text-xs bg-purple-500/10 border border-purple-500/30 text-purple-400 hover:bg-purple-500/20 transition-all"
                                                                        title="Náhled emailu, který se odešle klientovi"
                                                                    >
                                                                        👁 Náhled
                                                                    </button>
                                                                    <button
                                                                        onClick={async (e) => {
                                                                            e.stopPropagation();
                                                                            setResendingScan(scan.id);
                                                                            setResendResult(null);
                                                                            try {
                                                                                const r = await resendScanReport(scan.id);
                                                                                setResendResult(`✅ Email odeslán na ${r.email_to} (${r.findings_count} nálezů)`);
                                                                                // Refresh data
                                                                                await loadScanMonitor();
                                                                            } catch (err) {
                                                                                setResendResult(`❌ ${err}`);
                                                                            } finally {
                                                                                setResendingScan(null);
                                                                                setTimeout(() => setResendResult(null), 5000);
                                                                            }
                                                                        }}
                                                                        disabled={resendingScan === scan.id}
                                                                        className="px-3 py-1.5 rounded-lg text-xs bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/20 transition-all disabled:opacity-40"
                                                                        title="Znovu odeslat report email klientovi"
                                                                    >
                                                                        {resendingScan === scan.id ? "⏳" : "📤"} Odeslat report
                                                                    </button>
                                                                    {/* Expand arrow */}
                                                                    <span className={`text-gray-500 transition-transform ${expandedScan === scan.id ? "rotate-180" : ""}`}>
                                                                        ▼
                                                                    </span>
                                                                </div>
                                                            </div>
                                                            {/* Meta info */}
                                                            <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                                                                <span>Trvání: {scan.elapsed_hours ?? "?"}h</span>
                                                                <span>Dokončeno: {fmtDateTime(scan.deep_scan_finished_at)}</span>
                                                                <span>Email: {scan.company_email || "—"}</span>
                                                                {scan.geo_countries_scanned && (
                                                                    <span className="flex items-center gap-0.5">
                                                                        Země: {scan.geo_countries_scanned.map((c) => {
                                                                            const flags: Record<string, string> = { cz: "🇨🇿", gb: "🇬🇧", us: "🇺🇸", br: "🇧🇷", jp: "🇯🇵", za: "🇿🇦", au: "🇦🇺" };
                                                                            return <span key={c} title={c.toUpperCase()}>{flags[c.toLowerCase()] || c}</span>;
                                                                        })}
                                                                    </span>
                                                                )}
                                                                {scan.error_message && (
                                                                    <span className="text-red-400">⚠ {scan.error_message}</span>
                                                                )}
                                                            </div>
                                                        </div>

                                                        {/* Rozbalený detail — findings */}
                                                        {expandedScan === scan.id && (
                                                            <div className="px-5 pb-4">
                                                                {scanFindingsLoading ? (
                                                                    <div className="text-center py-4 text-cyan-400 animate-pulse text-sm">Načítám výsledky…</div>
                                                                ) : scanFindings ? (
                                                                    <div className="bg-white/[0.03] rounded-xl border border-white/10 overflow-hidden">
                                                                        <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between">
                                                                            <div className="text-sm font-medium text-white">
                                                                                🔍 Výsledky: {scanFindings.total_deployed} nasazených AI systémů
                                                                                {scanFindings.total_fp > 0 && (
                                                                                    <span className="text-gray-500 ml-2">+ {scanFindings.total_fp} falešně pozitivních</span>
                                                                                )}
                                                                            </div>
                                                                        </div>
                                                                        {scanFindings.deployed.length > 0 ? (
                                                                            <table className="w-full text-sm">
                                                                                <thead>
                                                                                    <tr className="text-xs text-gray-500 border-b border-white/5">
                                                                                        <th className="text-left px-4 py-2">Název</th>
                                                                                        <th className="text-left px-4 py-2">Kategorie</th>
                                                                                        <th className="text-left px-4 py-2">Riziko</th>
                                                                                        <th className="text-left px-4 py-2">AI Act článek</th>
                                                                                        <th className="text-left px-4 py-2">Zdroj</th>
                                                                                    </tr>
                                                                                </thead>
                                                                                <tbody className="divide-y divide-white/5">
                                                                                    {scanFindings.deployed.map((f) => {
                                                                                        const riskColors: Record<string, string> = {
                                                                                            unacceptable: "bg-red-500/20 text-red-400 border-red-500/30",
                                                                                            high: "bg-orange-500/20 text-orange-400 border-orange-500/30",
                                                                                            limited: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
                                                                                            minimal: "bg-green-500/20 text-green-400 border-green-500/30",
                                                                                        };
                                                                                        const riskLabels: Record<string, string> = {
                                                                                            unacceptable: "Nepřijatelné",
                                                                                            high: "Vysoké",
                                                                                            limited: "Omezené",
                                                                                            minimal: "Minimální",
                                                                                        };
                                                                                        return (
                                                                                            <tr key={f.id} className="hover:bg-white/[0.02]">
                                                                                                <td className="px-4 py-2 text-white font-medium">{f.name}</td>
                                                                                                <td className="px-4 py-2 text-gray-400">{f.category}</td>
                                                                                                <td className="px-4 py-2">
                                                                                                    <span className={`px-2 py-0.5 rounded text-xs border ${riskColors[f.risk_level] || "bg-gray-500/20 text-gray-400 border-gray-500/30"}`}>
                                                                                                        {riskLabels[f.risk_level] || f.risk_level}
                                                                                                    </span>
                                                                                                </td>
                                                                                                <td className="px-4 py-2 text-gray-400 text-xs">{f.ai_act_article || "—"}</td>
                                                                                                <td className="px-4 py-2 text-gray-500 text-xs">{f.source}</td>
                                                                                            </tr>
                                                                                        );
                                                                                    })}
                                                                                </tbody>
                                                                            </table>
                                                                        ) : (
                                                                            <div className="text-center text-gray-500 py-6 text-sm">
                                                                                Žádné nasazené AI systémy nebyly nalezeny
                                                                            </div>
                                                                        )}
                                                                    </div>
                                                                ) : null}
                                                            </div>
                                                        )}
                                                    </div>
                                                ))
                                            )}
                                        </div>
                                    </Panel>

                                    {/* Resend result toast */}
                                    {resendResult && (
                                        <div className={`fixed bottom-6 right-6 z-50 px-5 py-3 rounded-xl border shadow-2xl text-sm font-medium ${resendResult.startsWith("✅") ? "bg-green-500/20 border-green-500/30 text-green-400" : "bg-red-500/20 border-red-500/30 text-red-400"}`}>
                                            {resendResult}
                                        </div>
                                    )}
                                </>
                            ) : (
                                <div className="text-center text-gray-500 py-12">
                                    <div className="text-3xl mb-2">🔬</div>
                                    Nepodařilo se načíst data o testech
                                </div>
                            )}
                        </>
                    )}

                    {/* ══════════════════════════════════════════ */}
                    {/*  ZPĚTNÁ VAZBA                             */}
                    {/* ══════════════════════════════════════════ */}
                    {tab === "zpetnavazba" && (
                        <>
                            {feedbackLoading && (
                                <div className="text-center text-gray-500 py-12 animate-pulse">Načítám zpětnou vazbu...</div>
                            )}

                            {!feedbackLoading && chatFeedbackStats && (
                                <>
                                    {/* Stats cards */}
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                        <StatCard icon="💬" label="Celkem" value={chatFeedbackStats.total} accent="cyan" />
                                        <StatCard icon="😊" label="Pozitivní" value={chatFeedbackStats.sentiment?.positive || 0} accent="green" />
                                        <StatCard icon="😤" label="Negativní" value={chatFeedbackStats.sentiment?.negative || 0} accent="red" />
                                        <StatCard icon="📝" label="Prům. otázek" value={chatFeedbackStats.avg_questions} accent="fuchsia" />
                                    </div>

                                    {/* Humor reception */}
                                    <Panel className="p-5">
                                        <h3 className="text-sm font-semibold text-white mb-3">Recepce humoru</h3>
                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                            {Object.entries(chatFeedbackStats.humor || {}).map(([key, val]) => {
                                                const labels: Record<string, string> = {
                                                    enjoyed: "😂 Bavily ho vtipy",
                                                    tolerated: "🙂 Toleroval",
                                                    disliked: "😒 Nelíbily se",
                                                    unknown: "❓ Neurčeno",
                                                };
                                                return (
                                                    <div key={key} className="bg-white/5 rounded-lg p-3 text-center">
                                                        <div className="text-lg font-bold text-white">{val}</div>
                                                        <div className="text-xs text-gray-400 mt-1">{labels[key] || key}</div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </Panel>

                                    {/* Filter */}
                                    <div className="flex gap-2">
                                        {["all", "positive", "negative", "neutral", "mixed"].map((f) => {
                                            const labels: Record<string, string> = {
                                                all: "Vše",
                                                positive: "😊 Pozitivní",
                                                negative: "😤 Negativní",
                                                neutral: "😐 Neutrální",
                                                mixed: "🤔 Smíšené",
                                            };
                                            return (
                                                <button
                                                    key={f}
                                                    onClick={() => setFeedbackFilter(f)}
                                                    className={`px-3 py-1.5 rounded-lg text-xs border transition-all ${feedbackFilter === f ? "bg-cyan-500/20 border-cyan-500/30 text-cyan-400" : "bg-white/5 border-white/10 text-gray-400 hover:text-white"}`}
                                                >
                                                    {labels[f]}
                                                </button>
                                            );
                                        })}
                                    </div>

                                    {/* Feedback list */}
                                    <Panel className="divide-y divide-white/5">
                                        {chatFeedback.length === 0 ? (
                                            <div className="text-center text-gray-500 py-12">
                                                <div className="text-3xl mb-2">💬</div>
                                                Zatím žádná zpětná vazba
                                            </div>
                                        ) : (
                                            chatFeedback.map((fb) => {
                                                const sentimentEmoji: Record<string, string> = {
                                                    positive: "😊",
                                                    negative: "😤",
                                                    neutral: "😐",
                                                    mixed: "🤔",
                                                };
                                                const humorLabels: Record<string, string> = {
                                                    enjoyed: "😂 Bavily ho",
                                                    tolerated: "🙂 Toleroval",
                                                    disliked: "😒 Nelíbily se",
                                                    unknown: "❓",
                                                };
                                                return (
                                                    <div key={fb.id} className="p-4 hover:bg-white/[0.02]">
                                                        <div className="flex items-start justify-between gap-4">
                                                            <div className="flex-1 min-w-0">
                                                                <div className="flex items-center gap-2 mb-1">
                                                                    <span className="text-lg">{sentimentEmoji[fb.ai_sentiment] || "❓"}</span>
                                                                    <span className="font-medium text-white text-sm truncate">
                                                                        {fb.company_name || fb.company_id?.slice(0, 12) + "..."}
                                                                    </span>
                                                                    <span className="text-xs text-gray-500">{fb.company_email || ""}</span>
                                                                    <span className={`px-2 py-0.5 rounded text-xs ${fb.ai_sentiment === "positive" ? "bg-green-500/20 text-green-400" : fb.ai_sentiment === "negative" ? "bg-red-500/20 text-red-400" : "bg-gray-500/20 text-gray-400"}`}>
                                                                        {fb.ai_sentiment}
                                                                    </span>
                                                                    <span className="text-xs text-gray-600">{humorLabels[fb.ai_humor_reception] || ""}</span>
                                                                </div>
                                                                {/* Client feedback */}
                                                                <div className="bg-white/5 rounded-lg p-3 mb-2">
                                                                    <div className="text-xs text-gray-500 mb-1">Zpětná vazba klienta:</div>
                                                                    <div className="text-sm text-gray-200">
                                                                        &ldquo;{fb.feedback_text}&rdquo;
                                                                    </div>
                                                                </div>
                                                                {/* AI Summary */}
                                                                {fb.ai_summary && (
                                                                    <div className="bg-cyan-500/5 rounded-lg p-3 mb-2">
                                                                        <div className="text-xs text-cyan-400/60 mb-1">AI shrnutí konverzace:</div>
                                                                        <div className="text-sm text-gray-300">{fb.ai_summary}</div>
                                                                    </div>
                                                                )}
                                                                {/* Key moments & frustrations */}
                                                                <div className="flex flex-wrap gap-4 text-xs">
                                                                    {fb.ai_key_moments && fb.ai_key_moments.length > 0 && (
                                                                        <div>
                                                                            <span className="text-gray-500">Klíčové momenty: </span>
                                                                            {fb.ai_key_moments.map((m, i) => (
                                                                                <span key={i} className="inline-block bg-white/5 rounded px-1.5 py-0.5 mr-1 text-gray-400">{m}</span>
                                                                            ))}
                                                                        </div>
                                                                    )}
                                                                    {fb.ai_frustrations && fb.ai_frustrations.length > 0 && (
                                                                        <div>
                                                                            <span className="text-red-400/60">Frustrace: </span>
                                                                            {fb.ai_frustrations.map((f2, i) => (
                                                                                <span key={i} className="inline-block bg-red-500/10 rounded px-1.5 py-0.5 mr-1 text-red-400">{f2}</span>
                                                                            ))}
                                                                        </div>
                                                                    )}
                                                                </div>
                                                                {/* Meta */}
                                                                <div className="flex gap-4 mt-2 text-xs text-gray-600">
                                                                    <span>Q: {fb.questions_answered}</span>
                                                                    <span>{fb.completion_status === "completed" ? "✅ Dokončeno" : fb.completion_status === "abandoned" ? "🚪 Opuštěno" : fb.completion_status}</span>
                                                                    <span>{fmtDateTime(fb.created_at)}</span>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                );
                                            })
                                        )}
                                    </Panel>
                                </>
                            )}
                        </>
                    )}

                    {/* ══════════════════════════════════════════ */}
                    {/*  TAB: LLM API                             */}
                    {/* ══════════════════════════════════════════ */}
                    {tab === "llm" && (
                        <>
                            {llmLoading && !llmUsage && (
                                <div className="text-center py-12 text-gray-400">Načítám LLM data…</div>
                            )}
                            {llmUsage && (() => {
                                const claude = llmUsage.monthly?.claude;
                                const gemini = llmUsage.monthly?.gemini;
                                const claudeToday = llmUsage.today?.claude;
                                const geminiToday = llmUsage.today?.gemini;
                                const claudeHealth = llmUsage.api_health?.claude;
                                const geminiHealth = llmUsage.api_health?.gemini;
                                const claudeBudget = llmUsage.budgets?.claude || 100;
                                const geminiBudget = llmUsage.budgets?.gemini || 20;
                                const claudeSpent = claude?.cost_usd || 0;
                                const geminiSpent = gemini?.cost_usd || 0;
                                const claudePct = Math.min(100, Math.round((claudeSpent / claudeBudget) * 100));
                                const geminiPct = Math.min(100, Math.round((geminiSpent / geminiBudget) * 100));

                                const healthColor = (s?: string) =>
                                    s === "ok" ? "text-green-400" :
                                        s === "depleted" ? "text-red-500" :
                                            s === "rate_limited" ? "text-yellow-400" :
                                                s === "missing" ? "text-gray-500" : "text-red-400";
                                const healthDot = (s?: string) =>
                                    s === "ok" ? "bg-green-400" :
                                        s === "depleted" ? "bg-red-500 animate-pulse" :
                                            s === "rate_limited" ? "bg-yellow-400" :
                                                s === "missing" ? "bg-gray-500" : "bg-red-400";
                                const barColor = (pct: number) =>
                                    pct >= 95 ? "from-red-500 to-red-600" :
                                        pct >= 80 ? "from-amber-500 to-orange-500" :
                                            "from-cyan-500 to-blue-500";

                                const fmtTokens = (n: number) => n >= 1_000_000 ? `${(n / 1_000_000).toFixed(1)}M` : n >= 1_000 ? `${(n / 1_000).toFixed(0)}k` : `${n}`;

                                return (
                                    <>
                                        {/* API Key Health */}
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                                            {[
                                                { name: "Anthropic (Claude)", key: "claude", health: claudeHealth },
                                                { name: "Google (Gemini)", key: "gemini", health: geminiHealth },
                                            ].map(p => (
                                                <Panel key={p.key} className="p-5">
                                                    <div className="flex items-center justify-between mb-3">
                                                        <div className="flex items-center gap-2">
                                                            <span className={`w-2.5 h-2.5 rounded-full ${healthDot(p.health?.status)}`} />
                                                            <h3 className="text-sm font-semibold text-white">{p.name}</h3>
                                                        </div>
                                                        <span className={`text-xs font-medium ${healthColor(p.health?.status)}`}>
                                                            {p.health?.status === "ok" ? "✓ Aktivní" :
                                                                p.health?.status === "depleted" ? "✗ Vyčerpáno" :
                                                                    p.health?.status === "missing" ? "— Nenastaveno" :
                                                                        p.health?.status === "rate_limited" ? "⚡ Rate limited" :
                                                                            "✗ Chyba"}
                                                        </span>
                                                    </div>
                                                    <p className="text-xs text-gray-400">{p.health?.message || "—"}</p>
                                                    {p.health?.key_prefix && (
                                                        <p className="text-[10px] text-gray-600 mt-1 font-mono">{p.health.key_prefix}</p>
                                                    )}
                                                </Panel>
                                            ))}
                                        </div>

                                        <button
                                            onClick={handleCheckKeys}
                                            disabled={llmCheckingKeys}
                                            className="mb-6 text-xs px-4 py-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 hover:bg-cyan-500/20 transition-all disabled:opacity-50"
                                        >
                                            {llmCheckingKeys ? "Ověřuji…" : "🔑 Ověřit API klíče"}
                                        </button>

                                        {/* Monthly Budget Bars */}
                                        <Panel className="p-6 mb-6">
                                            <h2 className="text-lg font-semibold text-white mb-4">📊 Měsíční spotřeba — {llmUsage.month}</h2>
                                            <div className="space-y-5">
                                                {[
                                                    { name: "Anthropic (Claude)", spent: claudeSpent, budget: claudeBudget, pct: claudePct, data: claude },
                                                    { name: "Google (Gemini)", spent: geminiSpent, budget: geminiBudget, pct: geminiPct, data: gemini },
                                                ].map(p => (
                                                    <div key={p.name}>
                                                        <div className="flex items-center justify-between mb-1.5">
                                                            <span className="text-sm text-white font-medium">{p.name}</span>
                                                            <span className={`text-sm font-bold ${p.pct >= 95 ? "text-red-400" : p.pct >= 80 ? "text-amber-400" : "text-green-400"}`}>
                                                                ${p.spent.toFixed(2)} / ${p.budget.toFixed(0)}
                                                            </span>
                                                        </div>
                                                        <div className="h-3 rounded-full bg-white/5 overflow-hidden">
                                                            <div
                                                                className={`h-full rounded-full bg-gradient-to-r ${barColor(p.pct)} transition-all duration-500`}
                                                                style={{ width: `${p.pct}%` }}
                                                            />
                                                        </div>
                                                        <div className="flex justify-between mt-1 text-[10px] text-gray-500">
                                                            <span>{p.pct}% budgetu</span>
                                                            <span>
                                                                {p.data ? `${fmtTokens(p.data.input_tokens)} in · ${fmtTokens(p.data.output_tokens)} out · ${p.data.calls} volání` : "—"}
                                                            </span>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        </Panel>

                                        {/* Today */}
                                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                                            <StatCard icon="🤖" label="Claude dnes" value={`$${(claudeToday?.cost_usd || 0).toFixed(3)}`} sub={claudeToday ? `${claudeToday.calls} volání · ${fmtTokens(claudeToday.input_tokens + claudeToday.output_tokens)} tokenů` : "—"} accent="cyan" />
                                            <StatCard icon="✨" label="Gemini dnes" value={`$${(geminiToday?.cost_usd || 0).toFixed(3)}`} sub={geminiToday ? `${geminiToday.calls} volání · ${fmtTokens(geminiToday.input_tokens + geminiToday.output_tokens)} tokenů` : "—"} accent="fuchsia" />
                                            <StatCard icon="📞" label="Celkem volání" value={(claude?.calls || 0) + (gemini?.calls || 0)} sub={`Claude: ${claude?.calls || 0} · Gemini: ${gemini?.calls || 0}`} accent="green" />
                                            <StatCard icon="💸" label="Celkem měsíc" value={`$${(claudeSpent + geminiSpent).toFixed(2)}`} sub={`zbývá $${Math.max(0, claudeBudget + geminiBudget - claudeSpent - geminiSpent).toFixed(2)}`} accent={claudePct >= 80 || geminiPct >= 80 ? "red" : "green"} />
                                        </div>

                                        {/* In-Memory Stats (since restart) */}
                                        <Panel className="p-6 mb-6">
                                            <h2 className="text-sm font-semibold text-gray-400 mb-3">🔄 Od posledního restartu serveru</h2>
                                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
                                                <div>
                                                    <div className="text-xl font-bold text-white">{llmUsage.memory_stats?.total_calls || 0}</div>
                                                    <div className="text-[10px] text-gray-500">Volání celkem</div>
                                                </div>
                                                <div>
                                                    <div className="text-xl font-bold text-white">{fmtTokens((llmUsage.memory_stats?.total_input_tokens || 0) + (llmUsage.memory_stats?.total_output_tokens || 0))}</div>
                                                    <div className="text-[10px] text-gray-500">Tokenů celkem</div>
                                                </div>
                                                <div>
                                                    <div className="text-xl font-bold text-white">${(llmUsage.memory_stats?.total_cost_usd || 0).toFixed(4)}</div>
                                                    <div className="text-[10px] text-gray-500">Náklady</div>
                                                </div>
                                                <div>
                                                    <div className={`text-xl font-bold ${(llmUsage.memory_stats?.fallback_count || 0) > 0 ? "text-amber-400" : "text-green-400"}`}>
                                                        {llmUsage.memory_stats?.fallback_count || 0}
                                                    </div>
                                                    <div className="text-[10px] text-gray-500">Fallbacků</div>
                                                </div>
                                            </div>
                                        </Panel>

                                        {/* Daily trend */}
                                        {llmUsage.daily_trend && llmUsage.daily_trend.length > 0 && (
                                            <Panel className="p-6">
                                                <h2 className="text-sm font-semibold text-gray-400 mb-3">📈 Denní trend (posledních 30 dní)</h2>
                                                <div className="overflow-x-auto">
                                                    <table className="w-full text-xs">
                                                        <thead>
                                                            <tr className="text-gray-500 border-b border-white/5">
                                                                <th className="text-left py-2 pr-4">Datum</th>
                                                                <th className="text-left py-2 pr-4">Provider</th>
                                                                <th className="text-right py-2 pr-4">Volání</th>
                                                                <th className="text-right py-2 pr-4">Input tok.</th>
                                                                <th className="text-right py-2 pr-4">Output tok.</th>
                                                                <th className="text-right py-2">Cena</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {llmUsage.daily_trend.slice().reverse().map((d, i) => (
                                                                <tr key={i} className="border-b border-white/[0.03] hover:bg-white/[0.03]">
                                                                    <td className="py-1.5 pr-4 text-gray-300">{d.date}</td>
                                                                    <td className="py-1.5 pr-4">
                                                                        <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${d.provider === "claude" ? "bg-cyan-500/10 text-cyan-400" : "bg-fuchsia-500/10 text-fuchsia-400"}`}>
                                                                            {d.provider}
                                                                        </span>
                                                                    </td>
                                                                    <td className="py-1.5 pr-4 text-right text-gray-300">{d.calls}</td>
                                                                    <td className="py-1.5 pr-4 text-right text-gray-400">{fmtTokens(d.input_tokens)}</td>
                                                                    <td className="py-1.5 pr-4 text-right text-gray-400">{fmtTokens(d.output_tokens)}</td>
                                                                    <td className="py-1.5 text-right text-white font-medium">${d.cost_usd.toFixed(4)}</td>
                                                                </tr>
                                                            ))}
                                                        </tbody>
                                                    </table>
                                                </div>
                                            </Panel>
                                        )}

                                        <div className="mt-4 flex items-center gap-3">
                                            <button
                                                onClick={loadLLMUsage}
                                                disabled={llmLoading}
                                                className="text-xs px-4 py-2 rounded-lg bg-white/5 text-gray-400 border border-white/10 hover:bg-white/10 hover:text-white transition-all disabled:opacity-50"
                                            >
                                                {llmLoading ? "Načítám…" : "🔄 Obnovit data"}
                                            </button>
                                            <span className="text-[10px] text-gray-600">
                                                Aktualizováno: {llmUsage.timestamp ? new Date(llmUsage.timestamp).toLocaleString("cs") : "—"}
                                            </span>
                                        </div>
                                    </>
                                );
                            })()}
                        </>
                    )}

                </div>
            </main>
        </div>
    );
}
