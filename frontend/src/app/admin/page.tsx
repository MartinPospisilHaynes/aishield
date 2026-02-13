"use client";

import { useState, useEffect, useCallback } from "react";
import {
    isAdminLoggedIn,
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
    | "ulohy"
    | "monitoring"
    | "klienti"
    | "agentura"
    | "nastroje";

const NAV_ITEMS: { id: Tab; icon: string; label: string }[] = [
    { id: "prehled", icon: "📊", label: "Přehled" },
    { id: "klienti", icon: "💼", label: "Klienti & Platby" },
    { id: "firmy", icon: "🏭", label: "Firmy" },
    { id: "pipeline", icon: "📈", label: "Pipeline" },
    { id: "emaily", icon: "📧", label: "Emaily" },
    { id: "ulohy", icon: "🚀", label: "Úlohy" },
    { id: "monitoring", icon: "🔔", label: "Monitoring" },
    { id: "agentura", icon: "🤝", label: "Agentura" },
    { id: "nastroje", icon: "⚙️", label: "Nástroje" },
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

    // Client management
    const [clientData, setClientData] = useState<ClientManagementData | null>(null);
    const [clientSearch, setClientSearch] = useState("");
    const [clientFilter, setClientFilter] = useState<"all" | "subscription" | "one_time" | "needs_rescan" | "overdue">("all");
    const [rescanning, setRescanning] = useState<string | null>(null);
    const [rescanResult, setRescanResult] = useState<RescanResult | null>(null);
    const [expandedClient, setExpandedClient] = useState<string | null>(null);

    // Tools
    const [toolResult, setToolResult] = useState<string | null>(null);

    // Loading
    const [loading, setLoading] = useState(true);

    // ── Auth check ──
    useEffect(() => {
        const ok = isAdminLoggedIn();
        if (!ok) {
            window.location.href = "/admin/login";
            return;
        }
        setAuthed(true);
    }, []);

    // ── Data loaders ──

    const loadDashboard = useCallback(async () => {
        try {
            const [crm, admin, h] = await Promise.all([
                getCrmDashboardStats().catch(() => null),
                getAdminStats().catch(() => null),
                getEmailHealth().catch(() => null),
            ]);
            if (crm) setCrmStats(crm);
            if (admin) setAdminStats(admin);
            if (h) setHealth(h);
        } catch {
            // silent
        }
    }, []);

    const loadCompanies = useCallback(async () => {
        try {
            const d = await getAdminCompanies("all", 500);
            setCompanies(d.companies || []);
        } catch {
            // silent
        }
    }, []);

    const loadPipeline = useCallback(async () => {
        try {
            const d = await getCrmPipeline();
            setPipeline(d);
        } catch {
            // silent
        }
    }, []);

    const loadEmails = useCallback(async () => {
        try {
            const [el, h] = await Promise.all([getAdminEmailLog(200), getEmailHealth()]);
            setEmails(el.emails || []);
            setHealth(h);
        } catch {
            // silent
        }
    }, []);

    const loadMonitoring = useCallback(async () => {
        try {
            const [a, d] = await Promise.all([getAdminAlerts(50), getAdminDiffs(50)]);
            setAlerts(a.alerts || []);
            setDiffs(d.diffs || []);
        } catch {
            // silent
        }
    }, []);

    const loadAgency = useCallback(async () => {
        try {
            const d = await getAgencyClients();
            setAgencyClients(d.clients || []);
        } catch {
            // silent
        }
    }, []);

    const loadClientManagement = useCallback(async () => {
        try {
            const d = await getClientManagement();
            setClientData(d);
        } catch {
            // silent
        }
    }, []);

    // ── Initial load ──
    useEffect(() => {
        if (!authed) return;
        setLoading(true);
        loadDashboard().finally(() => setLoading(false));
    }, [authed, loadDashboard]);

    // ── Tab data load ──
    useEffect(() => {
        if (!authed) return;
        if (tab === "firmy") loadCompanies();
        if (tab === "pipeline") loadPipeline();
        if (tab === "emaily") loadEmails();
        if (tab === "monitoring") loadMonitoring();
        if (tab === "agentura") loadAgency();
        if (tab === "klienti") loadClientManagement();
    }, [tab, authed, loadCompanies, loadPipeline, loadEmails, loadMonitoring, loadAgency, loadClientManagement]);

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
            } catch {
                // silent
            }
        },
        [loadCompanies]
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
                            <div className="text-xs text-gray-500">Admin CRM Dashboard</div>
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
                        <button
                            onClick={() => {
                                if (tab === "prehled") loadDashboard();
                                if (tab === "firmy") loadCompanies();
                                if (tab === "pipeline") loadPipeline();
                                if (tab === "emaily") loadEmails();
                                if (tab === "monitoring") loadMonitoring();
                                if (tab === "agentura") loadAgency();
                                if (tab === "klienti") loadClientManagement();
                            }}
                            className="px-3 py-1.5 rounded-lg text-xs bg-white/5 border border-white/10 text-gray-400 hover:text-white hover:bg-white/10 transition-all"
                        >
                            🔄 Obnovit
                        </button>
                    </div>
                </div>

                <div className="px-8 py-6 space-y-6">
                    {/* ══════════════════════════════════════════ */}
                    {/*  TAB: Přehled (Dashboard)                 */}
                    {/* ══════════════════════════════════════════ */}
                    {tab === "prehled" && (
                        <>
                            {/* KPI Cards */}
                            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-4 gap-4">
                                <StatCard
                                    icon="🏭"
                                    label="Firmy celkem"
                                    value={fmtNum(crmStats?.companies?.total ?? adminStats?.companies_total ?? 0)}
                                    accent="cyan"
                                />
                                <StatCard
                                    icon="✅"
                                    label="Naskenováno"
                                    value={fmtNum(adminStats?.companies_scanned ?? crmStats?.scans?.total ?? 0)}
                                    accent="green"
                                />
                                <StatCard
                                    icon="📧"
                                    label="Emaily dnes"
                                    value={fmtNum(crmStats?.emails?.today ?? adminStats?.emails_today ?? 0)}
                                    accent="fuchsia"
                                />
                                <StatCard
                                    icon="📬"
                                    label="Emaily celkem"
                                    value={fmtNum(crmStats?.emails?.total ?? adminStats?.emails_total ?? 0)}
                                    accent="cyan"
                                />
                                <StatCard
                                    icon="👁️"
                                    label="Open rate"
                                    value={fmtPct(crmStats?.emails?.open_rate ?? health?.open_rate ?? 0)}
                                    accent="green"
                                />
                                <StatCard
                                    icon="🔍"
                                    label="Skeny tento týden"
                                    value={fmtNum(crmStats?.scans?.this_week ?? 0)}
                                    accent="yellow"
                                />
                                <StatCard
                                    icon="💰"
                                    label="Objednávky / Revenue"
                                    value={fmtMoney(crmStats?.orders?.paid_amount ?? 0)}
                                    sub={`${crmStats?.orders?.total ?? adminStats?.orders_paid ?? 0} objednávek`}
                                    accent="green"
                                />
                                <StatCard
                                    icon="📝"
                                    label="Dotazníky"
                                    value={fmtNum(crmStats?.questionnaires?.total ?? 0)}
                                    accent="fuchsia"
                                />
                            </div>

                            {/* Needing attention */}
                            {crmStats?.needing_attention && crmStats.needing_attention.length > 0 && (
                                <Panel className="p-6">
                                    <h2 className="text-lg font-semibold text-red-400 mb-4">
                                        🔥 Vyžaduje pozornost ({crmStats.needing_attention.length})
                                    </h2>
                                    <div className="space-y-2">
                                        {crmStats.needing_attention.map((c: CompanyBrief) => (
                                            <div
                                                key={c.id}
                                                onClick={() => (window.location.href = `/admin/company/${c.id}`)}
                                                className="flex items-center justify-between p-3 bg-red-500/5 border border-red-500/10 rounded-xl cursor-pointer hover:bg-red-500/10 transition-all"
                                            >
                                                <div>
                                                    <span className="font-medium text-white">{c.name}</span>
                                                    <span className="text-gray-500 text-sm ml-3">{c.url}</span>
                                                </div>
                                                <div className="flex items-center gap-3">
                                                    <StatusBadge status={c.workflow_status} map={WORKFLOW_STATUSES} />
                                                    {c.next_action && (
                                                        <span className="text-xs text-yellow-400">📌 {c.next_action}</span>
                                                    )}
                                                    {c.next_action_at && (
                                                        <span className="text-xs text-red-400">
                                                            ⏰ {fmtDate(c.next_action_at)}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </Panel>
                            )}

                            {/* Recent activity */}
                            {crmStats?.recent_activity && crmStats.recent_activity.length > 0 && (
                                <Panel className="p-6">
                                    <h2 className="text-lg font-semibold text-cyan-400 mb-4">📋 Poslední aktivita</h2>
                                    <div className="space-y-3">
                                        {crmStats.recent_activity.slice(0, 15).map((a: Activity) => (
                                            <div
                                                key={a.id}
                                                className="flex items-start gap-3 p-3 bg-black/20 rounded-xl"
                                            >
                                                <div className="text-lg mt-0.5">
                                                    {a.activity_type === "email_sent"
                                                        ? "📧"
                                                        : a.activity_type === "scan"
                                                            ? "🔍"
                                                            : a.activity_type === "status_change"
                                                                ? "🔄"
                                                                : a.activity_type === "note"
                                                                    ? "📝"
                                                                    : "•"}
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <div className="text-sm font-medium text-white truncate">{a.title}</div>
                                                    {a.description && (
                                                        <div className="text-xs text-gray-400 mt-0.5 truncate">
                                                            {a.description}
                                                        </div>
                                                    )}
                                                </div>
                                                <div className="text-xs text-gray-500 whitespace-nowrap">
                                                    {fmtDateTime(a.created_at)}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </Panel>
                            )}

                            {/* Cron schedule */}
                            <Panel className="p-6">
                                <h2 className="text-lg font-semibold text-cyan-400 mb-4">🕐 Cron Schedule (VPS)</h2>
                                <div className="space-y-2 text-sm font-mono">
                                    {CRON_SCHEDULE.map((c) => (
                                        <div key={c.time} className="flex gap-4">
                                            <span className="text-fuchsia-400 w-16">{c.time}</span>
                                            <span className="text-gray-300">{c.desc}</span>
                                        </div>
                                    ))}
                                </div>
                            </Panel>
                        </>
                    )}

                    {/* ══════════════════════════════════════════ */}
                    {/*  TAB: Firmy (Companies)                   */}
                    {/* ══════════════════════════════════════════ */}
                    {tab === "firmy" && (
                        <>
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
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead className="bg-white/5">
                                            <tr>
                                                <th className="text-left p-3 text-gray-400 font-medium">Název</th>
                                                <th className="text-left p-3 text-gray-400 font-medium">URL</th>
                                                <th className="text-left p-3 text-gray-400 font-medium">Email</th>
                                                <th className="text-left p-3 text-gray-400 font-medium">Stav</th>
                                                <th className="text-left p-3 text-gray-400 font-medium">Platba</th>
                                                <th className="text-left p-3 text-gray-400 font-medium">Priorita</th>
                                                <th className="text-left p-3 text-gray-400 font-medium">Emaily</th>
                                                <th className="text-left p-3 text-gray-400 font-medium">Skóre</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {filteredCompanies.length === 0 ? (
                                                <tr>
                                                    <td colSpan={8} className="p-12 text-center text-gray-500">
                                                        {companies.length === 0
                                                            ? "Zatím žádné firmy"
                                                            : "Žádné firmy neodpovídají filtru"}
                                                    </td>
                                                </tr>
                                            ) : (
                                                filteredCompanies.map((c) => {
                                                    const cid = (c as any).id || c.ico;
                                                    return (
                                                        <tr
                                                            key={cid}
                                                            onClick={() =>
                                                                (window.location.href = `/admin/company/${cid}`)
                                                            }
                                                            className="border-t border-white/5 hover:bg-white/5 cursor-pointer transition-colors"
                                                        >
                                                            <td className="p-3 text-white font-medium max-w-[200px] truncate">
                                                                {c.name || "—"}
                                                            </td>
                                                            <td className="p-3 text-cyan-400 text-xs truncate max-w-[180px]">
                                                                {c.url || "—"}
                                                            </td>
                                                            <td className="p-3 text-gray-300 text-xs truncate max-w-[180px]">
                                                                {c.email || "—"}
                                                            </td>
                                                            <td className="p-3" onClick={(e) => e.stopPropagation()}>
                                                                {(c as any).workflow_status ? (
                                                                    <select
                                                                        value={(c as any).workflow_status || "new"}
                                                                        onChange={(e) =>
                                                                            handleStatusChange(cid, "workflow_status", e.target.value)
                                                                        }
                                                                        className="bg-transparent border border-white/10 rounded px-1 py-0.5 text-xs text-gray-300 focus:outline-none focus:border-cyan-500/50"
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
                                                                        value={(c as any).payment_status || "none"}
                                                                        onChange={(e) =>
                                                                            handleStatusChange(cid, "payment_status", e.target.value)
                                                                        }
                                                                        className="bg-transparent border border-white/10 rounded px-1 py-0.5 text-xs text-gray-300 focus:outline-none focus:border-cyan-500/50"
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
                                            🔄 Workflow Status Pipeline
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

                                    {/* Payment Status */}
                                    <Panel className="p-6">
                                        <h2 className="text-lg font-semibold text-fuchsia-400 mb-5">
                                            💳 Payment Status
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
                                            <h2 className="text-lg font-semibold text-green-400 mb-4">💰 Revenue</h2>
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
                                        📧 Email Log ({emails.length})
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

                    {/* ══════════════════════════════════════════ */}
                    {/*  TAB: Úlohy (Tasks)                       */}
                    {/* ══════════════════════════════════════════ */}
                    {tab === "ulohy" && (
                        <>
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

                            {/* Recent logs */}
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

                            {/* Cron schedule */}
                            <Panel className="p-6">
                                <h2 className="text-lg font-semibold text-cyan-400 mb-4">🕐 Cron Schedule</h2>
                                <div className="space-y-2 text-sm font-mono">
                                    {CRON_SCHEDULE.map((c) => (
                                        <div key={c.time} className="flex gap-4">
                                            <span className="text-fuchsia-400 w-16">{c.time}</span>
                                            <span className="text-gray-300">{c.desc}</span>
                                        </div>
                                    ))}
                                </div>
                            </Panel>
                        </>
                    )}

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
                                                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                                                    clientFilter === f
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
                                                            onClick={() => setExpandedClient(isExpanded ? null : client.email)}
                                                        >
                                                            {/* Expand arrow */}
                                                            <span className={`text-gray-500 text-xs transition-transform ${isExpanded ? "rotate-90" : ""}`}>▶</span>

                                                            {/* Company info */}
                                                            <div className="flex-1 min-w-0">
                                                                <div className="flex items-center gap-2 mb-0.5">
                                                                    <span className="font-medium text-white truncate">{client.company_name}</span>
                                                                    {client.plan && (
                                                                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                                                                            client.plan === "enterprise" ? "bg-fuchsia-500/20 text-fuchsia-400 border border-fuchsia-500/30" :
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
                                                                        {client.scan_age_days}d ago
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
                                                                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all whitespace-nowrap ${
                                                                    rescanning === client.email
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
                                                                                    <span className={`font-medium ${
                                                                                        client.subscription.payment_ok ? "text-cyan-400" : "text-red-400"
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
                    {/*  TAB: Nástroje (Tools)                    */}
                    {/* ══════════════════════════════════════════ */}
                    {tab === "nastroje" && (
                        <>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {/* Data cleanup */}
                                <Panel className="p-6">
                                    <div className="text-3xl mb-3">🧹</div>
                                    <h3 className="font-semibold text-white mb-2">Data Cleanup</h3>
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

                                {/* Legislative alert shortcut */}
                                <Panel className="p-6">
                                    <div className="text-3xl mb-3">📢</div>
                                    <h3 className="font-semibold text-white mb-2">Legislativní alert</h3>
                                    <p className="text-xs text-gray-400 mb-4">
                                        Rychlý přístup k odeslání legislativního upozornění klientům.
                                    </p>
                                    <button
                                        onClick={() => setTab("monitoring")}
                                        className="w-full px-4 py-2 bg-orange-500/10 text-orange-400 border border-orange-500/20 rounded-xl hover:bg-orange-500/20 transition-all text-sm font-medium"
                                    >
                                        📢 Přejít na Monitoring
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

                            {/* System info */}
                            <Panel className="p-6">
                                <h2 className="text-lg font-semibold text-cyan-400 mb-4">ℹ️ Systémové informace</h2>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <div className="bg-black/30 rounded-xl p-4">
                                        <div className="text-xs text-gray-500 mb-1">Backend API</div>
                                        <div className="text-sm text-cyan-400 font-mono">
                                            {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}
                                        </div>
                                    </div>
                                    <div className="bg-black/30 rounded-xl p-4">
                                        <div className="text-xs text-gray-500 mb-1">Frontend</div>
                                        <div className="text-sm text-fuchsia-400 font-mono">Next.js 14 + Tailwind</div>
                                    </div>
                                    <div className="bg-black/30 rounded-xl p-4">
                                        <div className="text-xs text-gray-500 mb-1">Verze</div>
                                        <div className="text-sm text-green-400 font-mono">CRM Dashboard v2.0</div>
                                    </div>
                                </div>
                            </Panel>
                        </>
                    )}
                </div>
            </main>
        </div>
    );
}
