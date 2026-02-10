"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { getDashboardData, type DashboardData } from "@/lib/api";

type Tab = "prehled" | "findings" | "dokumenty" | "plan" | "skeny";

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
        return (
            <section className="py-20">
                <div className="mx-auto max-w-md px-6">
                    <div className="glass text-center py-12">
                        <p className="text-red-400 mb-4">{error}</p>
                        <a href="/scan" className="btn-primary text-sm px-6 py-2">
                            Spustit první sken
                        </a>
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
                        <a href="/scan" className="btn-secondary text-sm px-4 py-2">
                            Nový sken
                        </a>
                        <a href="/dotaznik" className="btn-primary text-sm px-4 py-2">
                            Vyplnit dotazník
                        </a>
                    </div>
                </div>

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
                        sub={highRisk > 0 ? `${highRisk} vysoké riziko` : "Žádné kritické"}
                        color={highRisk > 0 ? "text-red-400" : "text-green-400"}
                        icon={<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>}
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
                        sub={data?.questionnaire_status === "dokončen" ? "Vyplněn" : "Vyplňte pro přesnější analýzu"}
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
                    {activeTab === "prehled" && <TabPrehled data={data} />}
                    {activeTab === "findings" && <TabFindings findings={data?.findings || []} />}
                    {activeTab === "dokumenty" && <TabDokumenty documents={data?.documents || []} />}
                    {activeTab === "plan" && <TabPlan findings={data?.findings || []} />}
                    {activeTab === "skeny" && <TabSkeny scans={data?.scans || []} />}
                </div>
            </div>
        </section>
    );
}

/* ── Stat Card ── */
function StatCard({ label, value, sub, color, icon }: {
    label: string; value: string; sub: string; color: string; icon?: React.ReactNode;
}) {
    return (
        <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 hover:border-white/[0.12] transition-all">
            <div className="flex items-center justify-between mb-1">
                <p className="text-xs text-slate-500 uppercase tracking-wider">{label}</p>
                {icon && <span className="text-slate-600">{icon}</span>}
            </div>
            <p className={`text-3xl font-extrabold mt-1 ${color}`}>{value}</p>
            <p className="text-xs text-slate-500 mt-1">{sub}</p>
        </div>
    );
}

/* ── Tab: Přehled ── */
function TabPrehled({ data }: { data: DashboardData | null }) {
    const hasPaidOrder = data?.orders.some((o) => o.status === "PAID") || false;
    const hasScans = (data?.scans.length || 0) > 0;
    const hasQuest = data?.questionnaire_status === "dokončen";
    const hasDocs = (data?.documents.length || 0) > 0;

    const steps = [
        {
            done: hasScans,
            label: "Sken webu",
            desc: "Automatická detekce AI systémů na vašem webu",
            href: "/scan",
            cta: "Spustit sken",
        },
        {
            done: hasQuest,
            label: "Dotazník",
            desc: "Upřesní analýzu o interní AI nástroje (ChatGPT, Copilot...)",
            href: "/dotaznik",
            cta: "Vyplnit dotazník",
        },
        {
            done: hasPaidOrder,
            label: "Objednávka",
            desc: "Odemkněte compliance dokumenty a akční plán",
            href: "/pricing",
            cta: "Vybrat balíček",
        },
        {
            done: hasDocs,
            label: "Dokumenty",
            desc: "7 PDF dokumentů pro splnění AI Act",
            href: "#",
            cta: "Viz tab Dokumenty",
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
                        {currentStep.href !== "#" && (
                            <a href={currentStep.href} className="btn-primary text-sm px-5 py-2 ml-9 inline-block">
                                {currentStep.cta}
                            </a>
                        )}
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
function TabFindings({ findings }: { findings: DashboardData["findings"] }) {
    if (findings.length === 0) {
        return (
            <EmptyState
                title="Zatím žádné AI systémy"
                description="Spusťte sken webu pro automatickou detekci AI systémů na vašem webu."
                href="/scan"
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
function TabPlan({ findings }: { findings: DashboardData["findings"] }) {
    if (findings.length === 0) {
        return (
            <EmptyState
                title="Akční plán je prázdný"
                description="Nejdříve proveďte sken webu — akční plán se vygeneruje z nálezů."
                href="/scan"
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
function TabSkeny({ scans }: { scans: DashboardData["scans"] }) {
    if (scans.length === 0) {
        return (
            <EmptyState
                title="Zatím žádné skeny"
                description="Spusťte první sken pro detekci AI systémů na vašem webu."
                href="/scan"
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

/* ── Empty State ── */
function EmptyState({ title, description, href, cta, illustration }: {
    title: string; description: string; href: string; cta: string; illustration?: React.ReactNode;
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
            <a href={href} className="btn-primary text-sm px-6 py-2.5">
                {cta}
            </a>
        </div>
    );
}
