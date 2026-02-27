"use client";

import { useState, useEffect, useCallback } from "react";
import {
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
    AdminStats,
    EmailHealth,
    AgencyClient,
} from "@/lib/api";

// ── Typy ──
interface EmailLogEntry {
    id: string;
    company_ico: string;
    to_email: string;
    subject: string;
    variant: string;
    status: string;
    sent_at: string;
}

interface CompanyEntry {
    ico: string;
    name: string;
    url: string;
    email: string;
    scan_status: string;
    emails_sent: number;
    created_at: string;
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

type Tab = "prehled" | "emaily" | "firmy" | "logy" | "monitoring" | "agentura";

const TASKS = [
    { name: "monitoring", label: "🔍 Monitoring klientů", desc: "Skenuj nasmlouvané klienty" },
    { name: "prospecting", label: "🏭 Prospecting (3 zdroje)", desc: "Shoptet + Heureka + ARES" },
    { name: "scanning", label: "🌐 Sken + kvalifikace", desc: "Skenuj weby → filtruj firmy s AI" },
    { name: "find_emails", label: "📧 Hledání emailů", desc: "Najdi kontakty kvalifikovaných leadů" },
    { name: "emailing", label: "🚀 Email kampaň", desc: "Pošli emaily HOT leadům" },
    { name: "reporting", label: "📊 Reporting", desc: "Měsíční reporty (1. den)" },
];

export default function AdminPage() {
    const [stats, setStats] = useState<AdminStats | null>(null);
    const [emails, setEmails] = useState<EmailLogEntry[]>([]);
    const [companies, setCompanies] = useState<CompanyEntry[]>([]);
    const [health, setHealth] = useState<EmailHealth | null>(null);
    const [tab, setTab] = useState<Tab>("prehled");
    const [loading, setLoading] = useState(true);
    const [runningTask, setRunningTask] = useState<string | null>(null);
    const [taskResult, setTaskResult] = useState<string | null>(null);
    const [alerts, setAlerts] = useState<AlertEntry[]>([]);
    const [diffs, setDiffs] = useState<DiffEntry[]>([]);
    const [legTitle, setLegTitle] = useState("");
    const [legBody, setLegBody] = useState("");
    const [legSending, setLegSending] = useState(false);
    const [legResult, setLegResult] = useState<string | null>(null);
    const [agencyClients, setAgencyClients] = useState<AgencyClientEntry[]>([]);
    const [batchInput, setBatchInput] = useState("");
    const [batchRunning, setBatchRunning] = useState(false);
    const [batchResult, setBatchResult] = useState<string | null>(null);
    const [emailPreview, setEmailPreview] = useState<{subject: string; body: string} | null>(null);

    const loadStats = useCallback(async () => {
        try {
            const [data, h] = await Promise.all([getAdminStats(), getEmailHealth()]);
            setStats(data);
            setHealth(h);
        } catch {
            console.error("Chyba při načítání stats");
        }
    }, []);

    useEffect(() => {
        setLoading(true);
        loadStats().finally(() => setLoading(false));
    }, [loadStats]);

    useEffect(() => {
        if (tab === "emaily") {
            getAdminEmailLog(100).then((d) => setEmails(d.emails || [])).catch(console.error);
        }
        if (tab === "firmy") {
            getAdminCompanies("all", 100).then((d) => setCompanies(d.companies || [])).catch(console.error);
        }
        if (tab === "monitoring") {
            Promise.all([
                getAdminAlerts(50).then((d) => setAlerts(d.alerts || [])),
                getAdminDiffs(50).then((d) => setDiffs(d.diffs || [])),
            ]).catch(console.error);
        }
        if (tab === "agentura") {
            getAgencyClients().then((d) => setAgencyClients(d.clients || [])).catch(console.error);
        }
    }, [tab]);

    const handleRunTask = async (taskName: string) => {
        setRunningTask(taskName);
        setTaskResult(null);
        try {
            const result = await runAdminTask(taskName);
            setTaskResult(JSON.stringify(result, null, 2));
            await loadStats();
        } catch (e) {
            setTaskResult(`Chyba: ${e}`);
        } finally {
            setRunningTask(null);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-[#0f172a] flex items-center justify-center">
                <div className="text-cyan-400 text-xl animate-pulse">⚙️ Načítám admin panel...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[#0f172a] text-white">
            {/* Header */}
            <div className="border-b border-white/10 bg-black/30 backdrop-blur-xl">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold">
                            <span className="text-fuchsia-400">⚙️</span> AIshield Admin
                        </h1>
                        <p className="text-sm text-gray-400">Řídící panel orchestrátoru</p>
                    </div>
                    <a href="/" className="text-cyan-400 hover:text-cyan-300 text-sm">← Zpět na web</a>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-6 py-8">
                {/* Stat karty */}
                {stats && (
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
                        <StatCard label="Firmy celkem" value={stats.companies_total} icon="🏭" />
                        <StatCard label="Naskenováno" value={stats.companies_scanned} icon="✅" />
                        <StatCard label="Emaily dnes" value={stats.emails_today} icon="📧" />
                        <StatCard label="Emaily celkem" value={stats.emails_total} icon="📬" />
                        <StatCard label="Objednávky" value={stats.orders_paid} icon="💰" />
                        <StatCard label="Konverze" value={`${stats.conversion_pct}%`} icon="📈" />
                    </div>
                )}

                {/* Tabs */}
                <div className="flex gap-2 mb-6 border-b border-white/10 pb-4 overflow-x-auto">
                    {([
                        { id: "prehled" as Tab, label: "📊 Přehled" },
                        { id: "emaily" as Tab, label: "📧 Emaily" },
                        { id: "firmy" as Tab, label: "🏭 Firmy" },
                        { id: "logy" as Tab, label: "📋 Logy" },
                        { id: "monitoring" as Tab, label: "🔔 Monitoring" },
                        { id: "agentura" as Tab, label: "🤝 Agentura" },
                    ]).map((t) => (
                        <button
                            key={t.id}
                            onClick={() => setTab(t.id)}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${tab === t.id
                                ? "bg-fuchsia-500/20 text-fuchsia-400 border border-fuchsia-500/30"
                                : "text-gray-400 hover:text-white hover:bg-white/5"
                                }`}
                        >
                            {t.label}
                        </button>
                    ))}
                </div>

                {/* Tab content */}
                {tab === "prehled" && (
                    <div className="space-y-6">
                        {/* Manuální spuštění úloh */}
                        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                            <h2 className="text-lg font-semibold mb-4 text-cyan-400">🚀 Manuální spuštění</h2>
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
                                        <div className="font-medium">{task.label}</div>
                                        <div className="text-xs text-gray-400 mt-1">{task.desc}</div>
                                        {runningTask === task.name && (
                                            <div className="text-xs text-cyan-400 mt-2">⏳ Běží...</div>
                                        )}
                                    </button>
                                ))}
                            </div>
                            {taskResult && (
                                <pre className="mt-4 p-4 bg-black/50 rounded-lg text-xs text-green-400 overflow-x-auto">
                                    {taskResult}
                                </pre>
                            )}
                        </div>

                        {/* Email Health — Adaptivní */}
                        {health && (
                            <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                                <div className="flex items-center justify-between mb-4">
                                    <h2 className="text-lg font-semibold text-cyan-400">🛡️ Doručitelnost emailů</h2>
                                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${health.mode === "stopped" ? "bg-red-500/20 text-red-400 border border-red-500/30" :
                                            health.mode === "braking" ? "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30" :
                                                health.mode === "accelerating" ? "bg-green-500/20 text-green-400 border border-green-500/30" :
                                                    health.mode === "startup" ? "bg-fuchsia-500/20 text-fuchsia-400 border border-fuchsia-500/30" :
                                                        "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
                                        }`}>
                                        {health.mode === "stopped" ? "🚨 ZASTAVENO" :
                                            health.mode === "braking" ? "⚠️ BRZDA" :
                                                health.mode === "accelerating" ? "🚀 ZRYCHLUJE" :
                                                    health.mode === "startup" ? "🏁 START" : "✈️ CRUISE"}
                                    </span>
                                </div>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                                    <div className="bg-black/30 rounded-xl p-3">
                                        <div className="text-xs text-gray-400">Adaptivní limit</div>
                                        <div className="text-xl font-bold text-cyan-400">{health.sent_today} / {health.daily_limit}</div>
                                        <div className="w-full bg-white/10 rounded-full h-1.5 mt-1">
                                            <div className="bg-cyan-500 h-1.5 rounded-full" style={{ width: `${health.daily_limit > 0 ? Math.min(100, (health.sent_today / health.daily_limit) * 100) : 0}%` }} />
                                        </div>
                                    </div>
                                    <div className="bg-black/30 rounded-xl p-3">
                                        <div className="text-xs text-gray-400">Bounce rate (7d)</div>
                                        <div className={`text-xl font-bold ${(health.bounce_rate * 100) > 5 ? "text-red-400" : (health.bounce_rate * 100) > 2 ? "text-yellow-400" : "text-green-400"}`}>{(health.bounce_rate * 100).toFixed(1)}%</div>
                                        <div className="text-xs text-gray-500">{health.bounced_7d} z {health.sent_7d}</div>
                                    </div>
                                    <div className="bg-black/30 rounded-xl p-3">
                                        <div className="text-xs text-gray-400">Spam rate (7d)</div>
                                        <div className={`text-xl font-bold ${(health.complaint_rate * 100) > 0.1 ? "text-red-400" : (health.complaint_rate * 100) > 0.05 ? "text-yellow-400" : "text-green-400"}`}>{(health.complaint_rate * 100).toFixed(2)}%</div>
                                        <div className="text-xs text-gray-500">{health.complained_7d} stížností</div>
                                    </div>
                                    <div className="bg-black/30 rounded-xl p-3">
                                        <div className="text-xs text-gray-400">Open rate (7d)</div>
                                        <div className={`text-xl font-bold ${(health.open_rate * 100) > 20 ? "text-green-400" : (health.open_rate * 100) > 10 ? "text-cyan-400" : "text-gray-400"}`}>{(health.open_rate * 100).toFixed(0)}%</div>
                                        <div className="text-xs text-gray-500">{health.opened_7d} otevřeno</div>
                                    </div>
                                </div>
                                <div className="bg-black/20 rounded-lg px-4 py-2 mb-3 text-sm text-gray-300">
                                    {health.adjustment_reason}
                                </div>
                                <div className="flex gap-4 text-xs text-gray-400 mb-3">
                                    <span>📅 Den {health.days_active}</span>
                                    <span>🚫 Blacklist: {health.blacklisted_count}</span>
                                    <span>📭 Odhlášeno: {health.unsubscribed_count}</span>
                                    <span>📧 Za 7 dní: {health.sent_7d}</span>
                                </div>
                                {health.warnings.length > 0 && (
                                    <div className="space-y-1">
                                        {health.warnings.map((w, i) => (
                                            <div key={i} className={`text-xs rounded-lg px-3 py-2 ${w.includes("STOP") || w.includes("KRITICKÉ") ? "text-red-400 bg-red-500/10 border border-red-500/20" :
                                                    w.includes("⚠️") ? "text-yellow-400 bg-yellow-500/10 border border-yellow-500/20" :
                                                        w.includes("🚀") ? "text-green-400 bg-green-500/10 border border-green-500/20" :
                                                            "text-cyan-400 bg-cyan-500/10 border border-cyan-500/20"
                                                }`}>
                                                {w}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Cron schedule */}
                        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                            <h2 className="text-lg font-semibold mb-4 text-cyan-400">🕐 Cron Schedule (VPS)</h2>
                            <div className="space-y-2 text-sm font-mono">
                                <div className="flex gap-4"><span className="text-fuchsia-400 w-16">03:00</span><span className="text-gray-300">Monitoring nasmlouvaných klientů</span></div>
                                <div className="flex gap-4"><span className="text-fuchsia-400 w-16">04:00</span><span className="text-gray-300">Prospecting — Shoptet + Heureka + ARES</span></div>
                                <div className="flex gap-4"><span className="text-fuchsia-400 w-16">05:00</span><span className="text-gray-300">Skenování webů + kvalifikace leadů</span></div>
                                <div className="flex gap-4"><span className="text-fuchsia-400 w-16">06:00</span><span className="text-gray-300">Hledání emailů (Playwright + Vision)</span></div>
                                <div className="flex gap-4"><span className="text-fuchsia-400 w-16">08:00</span><span className="text-gray-300">Email kampaň — pouze HOT leady</span></div>
                                <div className="flex gap-4"><span className="text-fuchsia-400 w-16">20:00</span><span className="text-gray-300">Měsíční reporty (1. den)</span></div>
                            </div>
                        </div>
                    </div>
                )}

                {tab === "emaily" && (
                    <div className="bg-white/5 border border-white/10 rounded-2xl overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="bg-white/5">
                                <tr>
                                    <th className="text-left p-3 text-gray-400">Čas</th>
                                    <th className="text-left p-3 text-gray-400">Email</th>
                                    <th className="text-left p-3 text-gray-400">Předmět</th>
                                    <th className="text-left p-3 text-gray-400">Varianta</th>
                                    <th className="text-left p-3 text-gray-400">Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {emails.length === 0 ? (
                                    <tr><td colSpan={5} className="p-8 text-center text-gray-500">Zatím žádné emaily</td></tr>
                                ) : (
                                    emails.map((e) => (
                                        <tr key={e.id} className="border-t border-white/5 hover:bg-white/5">
                                            <td className="p-3 text-gray-400 whitespace-nowrap">{new Date(e.sent_at).toLocaleString("cs")}</td>
                                            <td className="p-3 text-cyan-400">{e.to_email}</td>
                                            <td className="p-3 text-gray-300 truncate max-w-xs">{e.subject}</td>
                                            <td className="p-3"><span className="px-2 py-0.5 rounded bg-fuchsia-500/20 text-fuchsia-400 text-xs">{e.variant}</span></td>
                                            <td className="p-3">
                                                <span className={`px-2 py-0.5 rounded text-xs ${e.status === "sent" ? "bg-green-500/20 text-green-400"
                                                    : e.status === "dry_run" ? "bg-yellow-500/20 text-yellow-400"
                                                        : "bg-gray-500/20 text-gray-400"
                                                    }`}>{e.status}</span>
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                )}

                {tab === "firmy" && (
                    <div className="bg-white/5 border border-white/10 rounded-2xl overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="bg-white/5">
                                <tr>
                                    <th className="text-left p-3 text-gray-400">IČO</th>
                                    <th className="text-left p-3 text-gray-400">Název</th>
                                    <th className="text-left p-3 text-gray-400">URL</th>
                                    <th className="text-left p-3 text-gray-400">Email</th>
                                    <th className="text-left p-3 text-gray-400">Sken</th>
                                    <th className="text-left p-3 text-gray-400">Emaily</th>
                                </tr>
                            </thead>
                            <tbody>
                                {companies.length === 0 ? (
                                    <tr><td colSpan={6} className="p-8 text-center text-gray-500">Zatím žádné firmy</td></tr>
                                ) : (
                                    companies.map((c) => (
                                        <tr key={c.ico} className="border-t border-white/5 hover:bg-white/5">
                                            <td className="p-3 text-gray-400 font-mono">{c.ico}</td>
                                            <td className="p-3 text-white font-medium">{c.name}</td>
                                            <td className="p-3 text-cyan-400 truncate max-w-[200px]">{c.url}</td>
                                            <td className="p-3 text-gray-300">{c.email || "—"}</td>
                                            <td className="p-3">
                                                <span className={`px-2 py-0.5 rounded text-xs ${c.scan_status === "scanned" ? "bg-green-500/20 text-green-400"
                                                    : c.scan_status === "pending" ? "bg-yellow-500/20 text-yellow-400"
                                                        : "bg-gray-500/20 text-gray-400"
                                                    }`}>{c.scan_status}</span>
                                            </td>
                                            <td className="p-3 text-gray-400">{c.emails_sent || 0}</td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                )}

                {tab === "logy" && stats && (
                    <div className="bg-white/5 border border-white/10 rounded-2xl overflow-x-auto">
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
                                {stats.recent_logs.length === 0 ? (
                                    <tr><td colSpan={4} className="p-8 text-center text-gray-500">Zatím žádné logy</td></tr>
                                ) : (
                                    stats.recent_logs.map((log) => (
                                        <tr key={log.id} className="border-t border-white/5 hover:bg-white/5">
                                            <td className="p-3 text-gray-400 whitespace-nowrap">{new Date(log.started_at).toLocaleString("cs")}</td>
                                            <td className="p-3 text-white font-medium">{log.task_name}</td>
                                            <td className="p-3">
                                                <span className={`px-2 py-0.5 rounded text-xs ${log.status === "completed" ? "bg-green-500/20 text-green-400"
                                                    : log.status === "running" ? "bg-cyan-500/20 text-cyan-400"
                                                        : "bg-red-500/20 text-red-400"
                                                    }`}>{log.status}</span>
                                            </td>
                                            <td className="p-3 text-gray-300 text-xs font-mono truncate max-w-md">
                                                {log.error || (log.result ? JSON.stringify(log.result) : "—")}
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                )}

                {tab === "monitoring" && (
                    <div className="space-y-6">
                        {/* Legislativní alert */}
                        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                            <h2 className="text-lg font-semibold mb-4 text-cyan-400">📢 Legislativní upozornění</h2>
                            <p className="text-sm text-gray-400 mb-4">Odeslat upozornění VŠEM placeným klientům (např. změna AI Act)</p>
                            <div className="space-y-3">
                                <input
                                    type="text"
                                    placeholder="Titulek upozornění..."
                                    value={legTitle}
                                    onChange={(e) => setLegTitle(e.target.value)}
                                    className="w-full bg-black/30 border border-white/10 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:border-fuchsia-500/50 focus:outline-none"
                                />
                                <textarea
                                    placeholder="Text upozornění..."
                                    value={legBody}
                                    onChange={(e) => setLegBody(e.target.value)}
                                    rows={4}
                                    className="w-full bg-black/30 border border-white/10 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:border-fuchsia-500/50 focus:outline-none resize-none"
                                />
                                <div className="flex items-center gap-4">
                                    <button
                                        onClick={async () => {
                                            if (!legTitle || !legBody) return;
                                            setLegSending(true);
                                            setLegResult(null);
                                            try {
                                                const r = await sendLegislativeAlert(legTitle, legBody);
                                                setLegResult(`✅ Odesláno ${r.sent_count} klientům`);
                                                setLegTitle("");
                                                setLegBody("");
                                            } catch (e) {
                                                setLegResult(`❌ Chyba: ${e}`);
                                            } finally {
                                                setLegSending(false);
                                            }
                                        }}
                                        disabled={legSending || !legTitle || !legBody}
                                        className="px-6 py-2 bg-fuchsia-500/20 text-fuchsia-400 border border-fuchsia-500/30 rounded-lg hover:bg-fuchsia-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        {legSending ? "⏳ Odesílám..." : "🚀 Odeslat všem klientům"}
                                    </button>
                                    {legResult && <span className="text-sm">{legResult}</span>}
                                </div>
                            </div>
                        </div>

                        {/* Alerty */}
                        <div className="bg-white/5 border border-white/10 rounded-2xl overflow-x-auto">
                            <div className="p-4 border-b border-white/10">
                                <h2 className="text-lg font-semibold text-cyan-400">🔔 Poslední alerty</h2>
                            </div>
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
                                        <tr><td colSpan={6} className="p-8 text-center text-gray-500">Zatím žádné alerty</td></tr>
                                    ) : (
                                        alerts.map((a) => (
                                            <tr key={a.id} className="border-t border-white/5 hover:bg-white/5">
                                                <td className="p-3 text-gray-400 whitespace-nowrap">{new Date(a.created_at).toLocaleString("cs")}</td>
                                                <td className="p-3">
                                                    <span className="px-2 py-0.5 rounded text-xs bg-fuchsia-500/20 text-fuchsia-400">
                                                        {a.alert_type}
                                                    </span>
                                                </td>
                                                <td className="p-3">
                                                    <span className={`px-2 py-0.5 rounded text-xs ${
                                                        a.severity === "critical" ? "bg-red-500/20 text-red-400" :
                                                        a.severity === "high" ? "bg-orange-500/20 text-orange-400" :
                                                        a.severity === "medium" ? "bg-yellow-500/20 text-yellow-400" :
                                                        "bg-cyan-500/20 text-cyan-400"
                                                    }`}>
                                                        {a.severity}
                                                    </span>
                                                </td>
                                                <td className="p-3 text-gray-300 truncate max-w-xs">{a.title}</td>
                                                <td className="p-3 text-cyan-400 text-xs">{a.to_email}</td>
                                                <td className="p-3">
                                                    {a.email_sent
                                                        ? <span className="text-green-400">✅</span>
                                                        : <span className="text-gray-500">—</span>
                                                    }
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>

                        {/* Diffy */}
                        <div className="bg-white/5 border border-white/10 rounded-2xl overflow-x-auto">
                            <div className="p-4 border-b border-white/10">
                                <h2 className="text-lg font-semibold text-cyan-400">🔄 Změny ve skenech (Diffy)</h2>
                            </div>
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
                                        <tr><td colSpan={7} className="p-8 text-center text-gray-500">Zatím žádné diffy</td></tr>
                                    ) : (
                                        diffs.map((d) => (
                                            <tr key={d.id} className="border-t border-white/5 hover:bg-white/5">
                                                <td className="p-3 text-gray-400 whitespace-nowrap">{new Date(d.created_at).toLocaleString("cs")}</td>
                                                <td className="p-3 text-white font-mono text-xs">{d.company_id}</td>
                                                <td className="p-3">
                                                    {d.added_count > 0
                                                        ? <span className="text-green-400 font-medium">+{d.added_count}</span>
                                                        : <span className="text-gray-500">0</span>
                                                    }
                                                </td>
                                                <td className="p-3">
                                                    {d.removed_count > 0
                                                        ? <span className="text-red-400 font-medium">-{d.removed_count}</span>
                                                        : <span className="text-gray-500">0</span>
                                                    }
                                                </td>
                                                <td className="p-3">
                                                    {d.changed_count > 0
                                                        ? <span className="text-yellow-400 font-medium">~{d.changed_count}</span>
                                                        : <span className="text-gray-500">0</span>
                                                    }
                                                </td>
                                                <td className="p-3 text-gray-500">{d.unchanged_count}</td>
                                                <td className="p-3 text-gray-300 truncate max-w-xs text-xs">{d.summary || "—"}</td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {tab === "agentura" && (
                    <div className="space-y-6">
                        {/* Hromadný sken */}
                        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                            <h2 className="text-lg font-semibold mb-2 text-cyan-400">🏭 Hromadný sken klientů agentury</h2>
                            <p className="text-sm text-gray-400 mb-4">Zadejte klienty (1 řádek = 1 klient, formát: <code className="text-fuchsia-400">název | url | email | kontakt | poznámka</code>)</p>
                            <textarea
                                placeholder={`Pekárna U Míly | pekarnaumíly.cz | info@pekarna.cz | Milan Novák | dělali jsme web + chatbot\nRestaurace Mlýn | restaurace-mlyn.cz | info@mlyn.cz | Jana Králová | web + GA4`}
                                value={batchInput}
                                onChange={(e) => setBatchInput(e.target.value)}
                                rows={6}
                                className="w-full bg-black/30 border border-white/10 rounded-lg px-4 py-3 text-white placeholder-gray-600 focus:border-fuchsia-500/50 focus:outline-none resize-none font-mono text-sm"
                            />
                            <div className="flex items-center gap-4 mt-4">
                                <button
                                    onClick={async () => {
                                        const lines = batchInput.trim().split("\n").filter(Boolean);
                                        if (lines.length === 0) return;
                                        const clients: AgencyClient[] = lines.map(line => {
                                            const [name, url, email, contact_name, notes] = line.split("|").map(s => s.trim());
                                            return { name: name || "", url: url || "", email, contact_name, notes };
                                        });
                                        setBatchRunning(true);
                                        setBatchResult(null);
                                        try {
                                            const r = await startAgencyBatchScan(clients);
                                            setBatchResult(`✅ Spuštěn batch scan ${r.total_clients} klientů (batch_id: ${r.batch_id})`);
                                            setBatchInput("");
                                            // Reload clients
                                            getAgencyClients().then((d) => setAgencyClients(d.clients || []));
                                        } catch (e) {
                                            setBatchResult(`❌ Chyba: ${e}`);
                                        } finally {
                                            setBatchRunning(false);
                                        }
                                    }}
                                    disabled={batchRunning || !batchInput.trim()}
                                    className="px-6 py-2 bg-fuchsia-500/20 text-fuchsia-400 border border-fuchsia-500/30 rounded-lg hover:bg-fuchsia-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {batchRunning ? "⏳ Skenuju..." : "🚀 Spustit hromadný sken"}
                                </button>
                                {batchResult && <span className="text-sm">{batchResult}</span>}
                            </div>
                        </div>

                        {/* Generátor emailu */}
                        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                            <h2 className="text-lg font-semibold mb-2 text-cyan-400">✉️ Generátor personálního emailu</h2>
                            <p className="text-sm text-gray-400 mb-4">Vyberte klienta pro vygenerování osobního emailu (k ručnímu odeslání)</p>
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
                                                setEmailPreview({ subject: r.subject, body: r.body });
                                            } catch (e) {
                                                setEmailPreview({ subject: "Chyba", body: String(e) });
                                            }
                                        }}
                                        className="px-3 py-1.5 bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 rounded-lg text-xs hover:bg-cyan-500/20 transition-all"
                                    >
                                        ✉️ {c.name}
                                    </button>
                                ))}
                            </div>
                            {emailPreview && (
                                <div className="mt-4 bg-black/30 rounded-xl p-4 space-y-2">
                                    <div className="text-sm text-fuchsia-400 font-medium">Předmět: {emailPreview.subject}</div>
                                    <pre className="text-xs text-gray-300 whitespace-pre-wrap leading-relaxed">{emailPreview.body}</pre>
                                    <button
                                        onClick={() => navigator.clipboard.writeText(emailPreview.body)}
                                        className="px-3 py-1 bg-white/5 border border-white/10 rounded text-xs text-gray-400 hover:text-white transition-all"
                                    >
                                        📋 Zkopírovat do schránky
                                    </button>
                                </div>
                            )}
                        </div>

                        {/* Seznam klientů agentury */}
                        <div className="bg-white/5 border border-white/10 rounded-2xl overflow-x-auto">
                            <div className="p-4 border-b border-white/10">
                                <h2 className="text-lg font-semibold text-cyan-400">🤝 Klienti agentury ({agencyClients.length})</h2>
                            </div>
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
                                        <tr><td colSpan={6} className="p-8 text-center text-gray-500">Zatím žádní klienti agentury — použijte hromadný sken výše</td></tr>
                                    ) : (
                                        agencyClients.map((c) => (
                                            <tr key={c.id} className="border-t border-white/5 hover:bg-white/5">
                                                <td className="p-3 text-white font-medium">{c.name}</td>
                                                <td className="p-3 text-cyan-400 text-xs truncate max-w-[200px]">{c.url}</td>
                                                <td className="p-3 text-gray-300">{c.contact_name || "—"}</td>
                                                <td className="p-3 text-gray-400 text-xs">{c.email || "—"}</td>
                                                <td className="p-3">
                                                    <span className={`px-2 py-0.5 rounded text-xs ${
                                                        c.scan_status === "scanned" ? "bg-green-500/20 text-green-400" :
                                                        c.scan_status === "pending" ? "bg-yellow-500/20 text-yellow-400" :
                                                        "bg-gray-500/20 text-gray-400"
                                                    }`}>{c.scan_status}</span>
                                                </td>
                                                <td className="p-3 text-gray-400 text-xs whitespace-nowrap">{new Date(c.created_at).toLocaleDateString("cs")}</td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

function StatCard({ label, value, icon }: { label: string; value: string | number; icon: string }) {
    return (
        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
            <div className="text-2xl mb-1">{icon}</div>
            <div className="text-2xl font-bold text-white">{value}</div>
            <div className="text-xs text-gray-400">{label}</div>
        </div>
    );
}
