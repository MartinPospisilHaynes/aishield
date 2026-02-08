"use client";

import { useState, useEffect, useCallback } from "react";
import {
    getAdminStats,
    runAdminTask,
    getAdminEmailLog,
    getAdminCompanies,
    AdminStats,
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

type Tab = "prehled" | "emaily" | "firmy" | "logy";

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
    const [tab, setTab] = useState<Tab>("prehled");
    const [loading, setLoading] = useState(true);
    const [runningTask, setRunningTask] = useState<string | null>(null);
    const [taskResult, setTaskResult] = useState<string | null>(null);

    const loadStats = useCallback(async () => {
        try {
            const data = await getAdminStats();
            setStats(data);
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
                <div className="flex gap-2 mb-6 border-b border-white/10 pb-4">
                    {([
                        { id: "prehled" as Tab, label: "📊 Přehled" },
                        { id: "emaily" as Tab, label: "📧 Emaily" },
                        { id: "firmy" as Tab, label: "🏭 Firmy" },
                        { id: "logy" as Tab, label: "📋 Logy" },
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
                    <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
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
                    <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
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
                    <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
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
