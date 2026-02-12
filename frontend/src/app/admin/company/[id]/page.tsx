"use client";

import { useState, useEffect, useCallback } from "react";
import {
    isAdminLoggedIn,
    getCrmCompanyDetail,
    updateCompanyStatus,
    addCompanyNote,
    WORKFLOW_STATUSES,
    PAYMENT_STATUSES,
    PRIORITIES,
    type CompanyDetail,
    type Activity,
    type EmailLogEntry,
    type OrderEntry,
    type ScanInfo,
} from "@/lib/admin-api";

// ── Helpers ──

function relativeTime(dateStr: string): string {
    if (!dateStr) return "—";
    const now = Date.now();
    const then = new Date(dateStr).getTime();
    const diff = now - then;
    if (diff < 0) return "v budoucnu";
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "právě teď";
    if (mins < 60) return `před ${mins}m`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `před ${hours}h`;
    const days = Math.floor(hours / 24);
    if (days < 30) return `před ${days}d`;
    return new Date(dateStr).toLocaleDateString("cs");
}

function formatDate(dateStr: string | null | undefined): string {
    if (!dateStr) return "—";
    return new Date(dateStr).toLocaleString("cs");
}

function formatCZK(amount: number | null | undefined): string {
    if (amount == null) return "—";
    return amount.toLocaleString("cs-CZ") + " Kč";
}

function val(v: string | number | null | undefined): string {
    if (v == null || v === "") return "—";
    return String(v);
}

const ACTIVITY_ICONS: Record<string, string> = {
    status_change: "🔄",
    note: "📝",
    email_sent: "📧",
    email_opened: "👁️",
    scan_completed: "🔍",
    questionnaire_submitted: "📋",
    payment_received: "💰",
    document_generated: "📄",
    call: "📞",
    meeting: "🤝",
    manual: "✏️",
};

const COLOR_MAP: Record<string, string> = {
    gray: "bg-gray-500/20 text-gray-300 border-gray-500/30",
    blue: "bg-blue-500/20 text-blue-300 border-blue-500/30",
    yellow: "bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
    cyan: "bg-cyan-500/20 text-cyan-300 border-cyan-500/30",
    purple: "bg-purple-500/20 text-purple-300 border-purple-500/30",
    indigo: "bg-indigo-500/20 text-indigo-300 border-indigo-500/30",
    green: "bg-green-500/20 text-green-300 border-green-500/30",
    red: "bg-red-500/20 text-red-300 border-red-500/30",
    orange: "bg-orange-500/20 text-orange-300 border-orange-500/30",
};

// ── Sub-components ──

function StatusBadge({ value, map }: { value: string; map: Record<string, { label: string; color: string; icon: string }> }) {
    const entry = map[value] || { label: value, color: "gray", icon: "•" };
    const cls = COLOR_MAP[entry.color] || COLOR_MAP.gray;
    return (
        <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium border ${cls}`}>
            {entry.icon} {entry.label}
        </span>
    );
}

function InfoField({ label, value }: { label: string; value: string | number | null | undefined }) {
    return (
        <div>
            <div className="text-[11px] uppercase tracking-wider text-gray-500 mb-0.5">{label}</div>
            <div className={`text-sm ${val(value) === "—" ? "text-gray-600" : "text-gray-200"}`}>{val(value)}</div>
        </div>
    );
}

function TimelineEntry({ activity }: { activity: Activity }) {
    const icon = ACTIVITY_ICONS[activity.activity_type] || "•";
    return (
        <div className="flex gap-3 group">
            <div className="flex flex-col items-center">
                <div className="w-8 h-8 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-sm flex-shrink-0">
                    {icon}
                </div>
                <div className="w-px flex-1 bg-white/10 mt-1" />
            </div>
            <div className="pb-6 flex-1 min-w-0">
                <div className="text-sm font-medium text-gray-200">{activity.title}</div>
                {activity.description && (
                    <div className="text-xs text-gray-400 mt-0.5 whitespace-pre-wrap">{activity.description}</div>
                )}
                <div className="flex items-center gap-2 mt-1">
                    {activity.actor && <span className="text-[11px] text-cyan-400">{activity.actor}</span>}
                    <span className="text-[11px] text-gray-600">{relativeTime(activity.created_at)}</span>
                </div>
            </div>
        </div>
    );
}

// ── Tabs ──

function ScanTab({ scan, findingsCount }: { scan: ScanInfo | null; findingsCount: number }) {
    if (!scan) {
        return <div className="text-gray-500 text-sm py-8 text-center">Žádný scan nebyl proveden.</div>;
    }
    return (
        <div className="bg-white/5 border border-white/10 rounded-xl p-5 space-y-3">
            <h4 className="text-sm font-semibold text-gray-300 mb-3">Poslední scan</h4>
            <div className="grid grid-cols-2 gap-4">
                <InfoField label="Skenovaná URL" value={scan.url_scanned} />
                <InfoField label="Stav" value={scan.status} />
                <InfoField label="Doba trvání" value={scan.duration_seconds != null ? `${scan.duration_seconds}s` : undefined} />
                <InfoField label="Počet nálezů" value={findingsCount} />
                <InfoField label="Zahájeno" value={formatDate(scan.started_at)} />
                <InfoField label="Dokončeno" value={formatDate(scan.finished_at)} />
                <InfoField label="Vytvořeno" value={formatDate(scan.created_at)} />
            </div>
        </div>
    );
}

function EmailTab({ emails }: { emails: EmailLogEntry[] }) {
    if (!emails.length) {
        return <div className="text-gray-500 text-sm py-8 text-center">Žádné emaily.</div>;
    }
    return (
        <div className="overflow-x-auto">
            <table className="w-full text-sm">
                <thead>
                    <tr className="text-left text-[11px] uppercase tracking-wider text-gray-500 border-b border-white/10">
                        <th className="py-2 pr-3">Čas</th>
                        <th className="py-2 pr-3">Předmět</th>
                        <th className="py-2 pr-3">Varianta</th>
                        <th className="py-2 pr-3">Stav</th>
                        <th className="py-2">Otevřen / Klik</th>
                    </tr>
                </thead>
                <tbody>
                    {emails.map((e) => (
                        <tr key={e.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                            <td className="py-2 pr-3 text-gray-400 whitespace-nowrap">{formatDate(e.sent_at)}</td>
                            <td className="py-2 pr-3 text-gray-200 max-w-[200px] truncate">{e.subject}</td>
                            <td className="py-2 pr-3 text-gray-400">{val(e.variant)}</td>
                            <td className="py-2 pr-3">
                                <span className={`px-2 py-0.5 rounded text-xs ${e.status === "sent" ? "bg-green-500/20 text-green-300" : e.status === "failed" ? "bg-red-500/20 text-red-300" : "bg-gray-500/20 text-gray-300"}`}>
                                    {e.status}
                                </span>
                            </td>
                            <td className="py-2 flex items-center gap-2">
                                {e.opened_at ? <span className="text-xs bg-cyan-500/20 text-cyan-300 px-2 py-0.5 rounded">👁️ Otevřen</span> : <span className="text-xs text-gray-600">—</span>}
                                {e.clicked_at ? <span className="text-xs bg-fuchsia-500/20 text-fuchsia-300 px-2 py-0.5 rounded">🔗 Klik</span> : null}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

function OrdersTab({ orders }: { orders: OrderEntry[] }) {
    if (!orders.length) {
        return <div className="text-gray-500 text-sm py-8 text-center">Žádné objednávky.</div>;
    }
    return (
        <div className="overflow-x-auto">
            <table className="w-full text-sm">
                <thead>
                    <tr className="text-left text-[11px] uppercase tracking-wider text-gray-500 border-b border-white/10">
                        <th className="py-2 pr-3">Číslo</th>
                        <th className="py-2 pr-3">Plán</th>
                        <th className="py-2 pr-3">Částka</th>
                        <th className="py-2 pr-3">Stav</th>
                        <th className="py-2 pr-3">Zaplaceno</th>
                        <th className="py-2">Vytvořeno</th>
                    </tr>
                </thead>
                <tbody>
                    {orders.map((o) => (
                        <tr key={o.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                            <td className="py-2 pr-3 text-gray-200 font-mono text-xs">{val(o.order_number)}</td>
                            <td className="py-2 pr-3 text-gray-300">{val(o.plan)}</td>
                            <td className="py-2 pr-3 text-gray-200 font-medium">{formatCZK(o.amount)}</td>
                            <td className="py-2 pr-3">
                                <span className={`px-2 py-0.5 rounded text-xs ${o.status === "paid" ? "bg-green-500/20 text-green-300" : o.status === "pending" ? "bg-yellow-500/20 text-yellow-300" : "bg-gray-500/20 text-gray-300"}`}>
                                    {o.status}
                                </span>
                            </td>
                            <td className="py-2 pr-3 text-gray-400">{formatDate(o.paid_at)}</td>
                            <td className="py-2 text-gray-400">{formatDate(o.created_at)}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

function QuestionnaireTab({ count }: { count: number }) {
    return (
        <div className="py-8 text-center">
            <div className="text-4xl mb-3">📋</div>
            <div className="text-gray-300 font-medium">Vyplněných dotazníků: <span className="text-cyan-400 font-bold">{count}</span></div>
            {count > 0 && (
                <p className="text-gray-500 text-xs mt-2">Dotazníky jsou dostupné v sekci dotazníků.</p>
            )}
            {count === 0 && (
                <p className="text-gray-600 text-xs mt-2">Firma zatím nevyplnila žádný dotazník.</p>
            )}
        </div>
    );
}

// ── Main Page ──

export default function CompanyDetailPage({ params }: { params: { id: string } }) {
    const [data, setData] = useState<CompanyDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [activeTab, setActiveTab] = useState<"scan" | "emails" | "orders" | "questionnaire">("scan");

    // Status form
    const [formWorkflow, setFormWorkflow] = useState("");
    const [formPayment, setFormPayment] = useState("");
    const [formPriority, setFormPriority] = useState("");
    const [formAssigned, setFormAssigned] = useState("");
    const [formNextAction, setFormNextAction] = useState("");
    const [formNextActionAt, setFormNextActionAt] = useState("");
    const [saving, setSaving] = useState(false);
    const [saveMsg, setSaveMsg] = useState("");

    // Note form
    const [noteType, setNoteType] = useState("note");
    const [noteTitle, setNoteTitle] = useState("");
    const [noteDesc, setNoteDesc] = useState("");
    const [noteSaving, setNoteSaving] = useState(false);

    const loadData = useCallback(async () => {
        try {
            setLoading(true);
            const detail = await getCrmCompanyDetail(params.id);
            setData(detail);
            // Init form
            const c = detail.company;
            setFormWorkflow(c.workflow_status || "new");
            setFormPayment(c.payment_status || "none");
            setFormPriority(c.priority || "normal");
            setFormAssigned(c.assigned_to || "");
            setFormNextAction(c.next_action || "");
            setFormNextActionAt(c.next_action_at ? c.next_action_at.slice(0, 16) : "");
        } catch (err) {
            setError(err instanceof Error ? err.message : "Nepodařilo se načíst data");
        } finally {
            setLoading(false);
        }
    }, [params.id]);

    useEffect(() => {
        if (!isAdminLoggedIn()) {
            window.location.href = "/admin/login";
            return;
        }
        loadData();
    }, [loadData]);

    async function handleSaveStatus() {
        setSaving(true);
        setSaveMsg("");
        try {
            await updateCompanyStatus(params.id, {
                workflow_status: formWorkflow,
                payment_status: formPayment,
                priority: formPriority,
                assigned_to: formAssigned,
                next_action: formNextAction,
                next_action_at: formNextActionAt || undefined,
            });
            setSaveMsg("✅ Uloženo");
            await loadData();
            setTimeout(() => setSaveMsg(""), 3000);
        } catch {
            setSaveMsg("❌ Chyba při ukládání");
        } finally {
            setSaving(false);
        }
    }

    async function handleAddNote() {
        if (!noteTitle.trim()) return;
        setNoteSaving(true);
        try {
            await addCompanyNote(params.id, {
                activity_type: noteType,
                title: noteTitle.trim(),
                description: noteDesc.trim() || undefined,
            });
            setNoteTitle("");
            setNoteDesc("");
            setNoteType("note");
            await loadData();
        } catch {
            // silent
        } finally {
            setNoteSaving(false);
        }
    }

    // ── Loading / Error ──

    if (loading && !data) {
        return (
            <div className="min-h-screen bg-[#0f172a] flex items-center justify-center">
                <div className="text-center">
                    <div className="text-4xl animate-pulse mb-4">🏢</div>
                    <div className="text-gray-400">Načítám detail firmy…</div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-[#0f172a] flex items-center justify-center">
                <div className="text-center">
                    <div className="text-4xl mb-4">❌</div>
                    <div className="text-red-400 mb-4">{error}</div>
                    <button onClick={() => (window.location.href = "/admin")} className="text-cyan-400 hover:underline text-sm">
                        ← Zpět na přehled
                    </button>
                </div>
            </div>
        );
    }

    if (!data) return null;

    const c = data.company;
    const tabs = [
        { key: "scan" as const, label: "🔍 Scan" },
        { key: "emails" as const, label: "📧 Emaily" },
        { key: "orders" as const, label: "🛒 Objednávky" },
        { key: "questionnaire" as const, label: "📋 Dotazník" },
    ];

    const inputCls =
        "w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-cyan-500/50 focus:outline-none focus:ring-1 focus:ring-cyan-500/30 transition-all";
    const selectCls =
        "w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:border-cyan-500/50 focus:outline-none focus:ring-1 focus:ring-cyan-500/30 transition-all appearance-none";

    return (
        <div className="min-h-screen bg-[#0f172a] text-white">
            {/* ── Header Bar ── */}
            <div className="border-b border-white/10 bg-white/[0.02] backdrop-blur-xl sticky top-0 z-30">
                <div className="max-w-[1600px] mx-auto px-6 py-4">
                    <div className="flex items-center gap-4 flex-wrap">
                        <button
                            onClick={() => (window.location.href = "/admin")}
                            className="text-sm text-gray-400 hover:text-cyan-400 transition-colors flex items-center gap-1"
                        >
                            ← Zpět
                        </button>

                        <div className="flex-1 min-w-0">
                            <h1 className="text-xl font-bold text-white truncate">{c.name}</h1>
                            {c.url && (
                                <a
                                    href={c.url.startsWith("http") ? c.url : `https://${c.url}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-xs text-cyan-400 hover:underline truncate block"
                                >
                                    {c.url}
                                </a>
                            )}
                        </div>

                        <div className="flex items-center gap-2 flex-wrap">
                            {c.ico && (
                                <span className="px-2.5 py-1 rounded-full text-xs font-mono bg-white/10 text-gray-300 border border-white/10">
                                    IČO {c.ico}
                                </span>
                            )}
                            {c.lead_score != null && (
                                <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${c.lead_score >= 70 ? "bg-green-500/20 text-green-300 border-green-500/30" : c.lead_score >= 40 ? "bg-yellow-500/20 text-yellow-300 border-yellow-500/30" : "bg-gray-500/20 text-gray-300 border-gray-500/30"}`}>
                                    Score {c.lead_score}
                                </span>
                            )}
                            <StatusBadge value={c.workflow_status} map={WORKFLOW_STATUSES} />
                            <StatusBadge value={c.payment_status} map={PAYMENT_STATUSES} />
                        </div>
                    </div>
                </div>
            </div>

            {/* ── Body ── */}
            <div className="max-w-[1600px] mx-auto px-6 py-6">
                <div className="flex gap-6 flex-col lg:flex-row">
                    {/* ── Left Column (2/3) ── */}
                    <div className="flex-[2] min-w-0 space-y-6">
                        {/* Company Info Card */}
                        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Informace o firmě</h3>
                            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                                <InfoField label="Email" value={c.email} />
                                <InfoField label="Telefon" value={c.phone} />
                                <InfoField label="Kontaktní osoba" value={c.contact_name} />
                                <InfoField label="Adresa" value={c.address} />
                                <InfoField label="IČO" value={c.ico} />
                                <InfoField label="NACE" value={c.nace_code} />
                                <InfoField label="Zdroj" value={c.source} />
                                <InfoField label="Zaměstnanci" value={c.employee_count} />
                            </div>
                        </div>

                        {/* Status Management Card */}
                        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Správa statusů</h3>
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                <div>
                                    <label className="block text-xs text-gray-500 mb-1">Workflow stav</label>
                                    <select value={formWorkflow} onChange={(e) => setFormWorkflow(e.target.value)} className={selectCls} aria-label="Workflow stav">
                                        {Object.entries(WORKFLOW_STATUSES).map(([k, v]) => (
                                            <option key={k} value={k}>{v.icon} {v.label}</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs text-gray-500 mb-1">Stav platby</label>
                                    <select value={formPayment} onChange={(e) => setFormPayment(e.target.value)} className={selectCls} aria-label="Stav platby">
                                        {Object.entries(PAYMENT_STATUSES).map(([k, v]) => (
                                            <option key={k} value={k}>{v.icon} {v.label}</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs text-gray-500 mb-1">Priorita</label>
                                    <select value={formPriority} onChange={(e) => setFormPriority(e.target.value)} className={selectCls} aria-label="Priorita">
                                        {Object.entries(PRIORITIES).map(([k, v]) => (
                                            <option key={k} value={k}>{v.icon} {v.label}</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs text-gray-500 mb-1">Přiřazeno</label>
                                    <input
                                        type="text"
                                        value={formAssigned}
                                        onChange={(e) => setFormAssigned(e.target.value)}
                                        placeholder="Jméno"
                                        className={inputCls}
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs text-gray-500 mb-1">Další akce</label>
                                    <input
                                        type="text"
                                        value={formNextAction}
                                        onChange={(e) => setFormNextAction(e.target.value)}
                                        placeholder="Popis další akce…"
                                        className={inputCls}
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs text-gray-500 mb-1">Termín akce</label>
                                    <input
                                        type="datetime-local"
                                        value={formNextActionAt}
                                        onChange={(e) => setFormNextActionAt(e.target.value)}
                                        className={inputCls}
                                        aria-label="Termín akce"
                                    />
                                </div>
                            </div>
                            <div className="mt-4 flex items-center gap-3">
                                <button
                                    onClick={handleSaveStatus}
                                    disabled={saving}
                                    className="px-5 py-2 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-cyan-500 to-fuchsia-500 hover:from-cyan-400 hover:to-fuchsia-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-cyan-500/20"
                                >
                                    {saving ? "⏳ Ukládám…" : "💾 Uložit změny"}
                                </button>
                                {saveMsg && (
                                    <span className="text-sm text-gray-300 animate-pulse">{saveMsg}</span>
                                )}
                            </div>
                        </div>

                        {/* Tabs */}
                        <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
                            <div className="flex border-b border-white/10">
                                {tabs.map((t) => (
                                    <button
                                        key={t.key}
                                        onClick={() => setActiveTab(t.key)}
                                        className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${activeTab === t.key
                                                ? "text-cyan-400 bg-cyan-500/10 border-b-2 border-cyan-400"
                                                : "text-gray-500 hover:text-gray-300 hover:bg-white/5"
                                            }`}
                                    >
                                        {t.label}
                                    </button>
                                ))}
                            </div>
                            <div className="p-5">
                                {activeTab === "scan" && <ScanTab scan={data.latest_scan} findingsCount={data.findings_count} />}
                                {activeTab === "emails" && <EmailTab emails={data.email_log} />}
                                {activeTab === "orders" && <OrdersTab orders={data.orders} />}
                                {activeTab === "questionnaire" && <QuestionnaireTab count={data.questionnaire_count} />}
                            </div>
                        </div>
                    </div>

                    {/* ── Right Column (1/3) ── */}
                    <div className="flex-1 min-w-[300px] space-y-6">
                        {/* Add Note Form */}
                        <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
                            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Přidat poznámku</h3>
                            <div className="space-y-3">
                                <div>
                                    <label className="block text-xs text-gray-500 mb-1">Typ aktivity</label>
                                    <select value={noteType} onChange={(e) => setNoteType(e.target.value)} className={selectCls} aria-label="Typ aktivity">
                                        <option value="note">📝 Poznámka</option>
                                        <option value="call">📞 Hovor</option>
                                        <option value="meeting">🤝 Schůzka</option>
                                        <option value="manual">✏️ Manuální</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs text-gray-500 mb-1">Nadpis</label>
                                    <input
                                        type="text"
                                        value={noteTitle}
                                        onChange={(e) => setNoteTitle(e.target.value)}
                                        placeholder="Nadpis poznámky…"
                                        className={inputCls}
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs text-gray-500 mb-1">Popis</label>
                                    <textarea
                                        value={noteDesc}
                                        onChange={(e) => setNoteDesc(e.target.value)}
                                        placeholder="Podrobnosti…"
                                        rows={3}
                                        className={`${inputCls} resize-none`}
                                    />
                                </div>
                                <button
                                    onClick={handleAddNote}
                                    disabled={noteSaving || !noteTitle.trim()}
                                    className="w-full px-4 py-2 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-cyan-500 to-fuchsia-500 hover:from-cyan-400 hover:to-fuchsia-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-cyan-500/20"
                                >
                                    {noteSaving ? "⏳ Ukládám…" : "📝 Přidat poznámku"}
                                </button>
                            </div>
                        </div>

                        {/* Activity Timeline */}
                        <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
                            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">
                                Aktivita ({data.activities.length})
                            </h3>
                            <div className="max-h-[600px] overflow-y-auto pr-1 custom-scrollbar">
                                {data.activities.length === 0 ? (
                                    <div className="text-gray-600 text-sm text-center py-6">Žádná aktivita.</div>
                                ) : (
                                    data.activities.map((a) => <TimelineEntry key={a.id} activity={a} />)
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
