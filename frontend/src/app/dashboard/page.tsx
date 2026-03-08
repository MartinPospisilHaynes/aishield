"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useAuth } from "@/lib/auth-context";
import { getDashboardData, toggleActionPlanItem, triggerDeepScan, startScan, getScanStatus, getScanFindings, type DashboardData } from "@/lib/api";
import QuestionnaireNavigator from "@/components/questionnaire-navigator";

type Tab = "prehled" | "firma" | "findings" | "dokumenty" | "plan" | "skeny" | "dotaznik";

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
        key: "firma",
        label: "Firma",
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
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
        key: "dotaznik",
        label: "Dotazník",
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
        ),
    },
];

// Format display values — clean || separators in addresses into postal format
function formatDisplayValue(key: string, value: string): string {
    if (key === "company_address" || key.includes("address") || key.includes("adresa")) {
        // "Ulice 123 || PSČ || Město" → "Ulice 123, PSČ Město"
        const parts = value.split(/\s*\|\|\s*/).map(p => p.trim()).filter(Boolean);
        if (parts.length >= 3) {
            // parts: [ulice, PSČ, město, ...ostatní]
            return `${parts[0]}, ${parts.slice(1).join(" ")}`;
        }
        return parts.join(", ");
    }
    return value;
}

const TEMPLATE_NAMES: Record<string, string> = {
    compliance_report: "Zpráva o souladu s AI Act",
    transparency_page: "Transparentní stránka",
    action_plan: "Akční plán",
    ai_register: "Registr AI systémů",
    chatbot_notices: "Oznámení o AI",
    ai_policy: "Interní AI politika",
    training_outline: "Školení AI gramotnosti",
    incident_response_plan: "Plán řízení incidentů",
    dpia_template: "Posouzení vlivu na práva",
    vendor_checklist: "Kontrolní seznam dodavatelů",
    monitoring_plan: "Plán monitoringu AI",
    transparency_human_oversight: "Transparentnost a lidský dohled",
    training_presentation: "Školení AI gramotnosti — Prezentace",
};

const RISK_COLORS: Record<string, string> = {
    high: "text-red-400 bg-red-500/10 border-red-500/20",
    medium: "text-amber-400 bg-amber-500/10 border-amber-500/20",
    low: "text-green-400 bg-green-500/10 border-green-500/20",
};

const QUESTION_LABELS: Record<string, string> = {
    company_legal_name: "Název firmy",
    company_ico: "IČO",
    company_address: "Adresa sídla",
    company_contact_email: "Kontaktní e-mail",
    company_industry: "Obor podnikání",
    company_size: "Velikost firmy",
    company_annual_revenue: "Roční obrat",
    eshop_platform: "E-shop platforma",
    develops_own_ai: "Vyvíjí vlastní AI",
    uses_chatgpt: "Používá ChatGPT",
    uses_copilot: "Používá GitHub Copilot",
    uses_ai_content: "Generuje AI obsah",
    uses_deepfake: "Používá deepfake / syntetická média",
    uses_ai_chatbot: "Provozuje AI chatbot",
    uses_ai_email_auto: "AI automatizace e-mailů",
    uses_ai_decision: "AI rozhodování",
    uses_dynamic_pricing: "Dynamické ceny (AI)",
    uses_ai_for_children: "AI pro děti",
    uses_ai_recruitment: "AI nábor zaměstnanců",
    uses_ai_employee_monitoring: "AI monitoring zaměstnanců",
    uses_emotion_recognition: "Rozpoznávání emocí",
    uses_ai_accounting: "AI účetnictví",
    uses_ai_creditscoring: "AI credit scoring",
    uses_ai_insurance: "AI pojištění",
    uses_social_scoring: "Sociální skóring",
    uses_subliminal_manipulation: "Sublimální manipulace",
    uses_realtime_biometric: "Biometrická identifikace v reálném čase",
    uses_ai_critical_infra: "AI v kritické infrastruktuře",
    uses_ai_safety_component: "AI jako bezpečnostní komponenta",
    ai_processes_personal_data: "AI zpracovává osobní údaje",
    ai_data_stored_eu: "Data uložena v EU",
    has_ai_vendor_contracts: "Smlouvy s dodavateli AI",
    has_ai_training: "Školení zaměstnanců k AI",
    has_ai_guidelines: "Interní směrnice pro AI",
    has_oversight_person: "Odpovědná osoba za AI",
    can_override_ai: "Možnost zásahu do AI rozhodování",
    ai_decision_logging: "Logování AI rozhodnutí",
    has_ai_register: "Registr AI systémů",
    modifies_ai_purpose: "Modifikace účelu AI",
    uses_gpai_api: "Používá GPAI API",
    has_incident_plan: "Plán řízení incidentů",
    monitors_ai_outputs: "Monitoring výstupů AI",
    tracks_ai_changes: "Sledování změn v AI",
    has_ai_bias_check: "Kontrola předsudků AI",
    transparency_page_implementation: "Implementace transparentní stránky",
};

export default function DashboardPage() {
    const { user, loading: authLoading } = useAuth();
    const [data, setData] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [activeTab, setActiveTab] = useState<Tab>("prehled");

    const fetchData = useCallback(() => {
        if (!user?.email) return;
        getDashboardData(user.email)
            .then(setData)
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    }, [user?.email]);

    useEffect(() => {
        if (!user?.email) return;
        setLoading(true);
        fetchData();
    }, [user?.email, fetchData]);

    // Polling: auto-refresh every 15s while documents are generating
    const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
    useEffect(() => {
        const docsGenerating = data?.process_status?.documents_done === false && data?.process_status?.payment_done === true;
        if (docsGenerating) {
            pollingRef.current = setInterval(fetchData, 15_000);
        } else if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
        }
        return () => { if (pollingRef.current) clearInterval(pollingRef.current); };
    }, [data?.process_status?.documents_done, data?.process_status?.payment_done, fetchData]);

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
                        <button onClick={() => window.location.reload()} className="btn-primary text-sm px-6 py-2">
                            Zkusit znovu
                        </button>
                    </div>
                </div>
            </section>
        );
    }

    const companyName = data?.company?.name || user?.user_metadata?.company_name || "Vaše firma";

    // Process status from API
    const qAnswered = data?.questionnaire_answered_count ?? 0;
    const qTotal = data?.questionnaire_total_questions ?? 0;
    const qUnknowns = data?.questionnaire_unknowns || [];
    const qUnknownCount = data?.questionnaire_unknown_count ?? 0;
    const questionnaireIsComplete = qTotal > 0 && qAnswered >= qTotal && qUnknownCount === 0;
    const questionnaireAllAnswered = qTotal > 0 && qAnswered >= qTotal;
    const ps = data?.process_status || {
        scan_done: (data?.scans?.length || 0) > 0,
        questionnaire_done: questionnaireIsComplete,
        payment_done: data?.orders?.some((o) => o.status === "PAID") || false,
        documents_done: (data?.documents?.length || 0) > 0,
        steps_completed: 0,
        steps_total: 4,
    };
    const stepsCompleted = ps.steps_completed || [ps.scan_done, ps.questionnaire_done, ps.payment_done, ps.documents_done].filter(Boolean).length;

    // AI systems: merge scan findings + questionnaire findings
    const scanFindings = data?.findings?.length || 0;
    const questFindings = data?.questionnaire_findings?.length || 0;
    const totalAiSystems = scanFindings + questFindings;
    const highRisk = data?.findings?.filter((f) => f.risk_level === "high").length || 0;

    // Documents: unique by template_key
    const uniqueDocs = getUniqueDocs(data?.documents || []);
    const docsCount = uniqueDocs.length;

    return (
        <section className="py-8 relative">
            <div className="absolute inset-0 -z-10">
                <div className="absolute top-[5%] right-[25%] h-[400px] w-[400px] rounded-full bg-fuchsia-500/5 blur-[130px]" />
            </div>

            <div className="mx-auto max-w-7xl px-6">
                <div id="pipeline-scan" className="mb-6">
                    <PipelineProgress data={data} onRefresh={fetchData} />
                </div>

                <div className="mb-6">
                    <h1 className="text-2xl font-extrabold">Dashboard</h1>
                    <p className="text-sm text-slate-400 mt-1">
                        {companyName} — {data?.company?.url || ""}
                    </p>
                </div>

                {/* Banner: „Nevím" odpovědi v dotazníku */}
                {(data?.questionnaire_unknowns?.length ?? 0) > 0 && data?.company?.id && (
                    <a
                        href={`/dotaznik?company_id=${data.company.id}&edit=true&q=${data.questionnaire_unknowns[0]?.question_key || ""}`}
                        className="group mb-6 flex items-center gap-4 rounded-xl border border-amber-500/30 bg-amber-500/[0.06] p-4 transition-all hover:border-amber-400/50 hover:bg-amber-500/[0.10]"
                    >
                        <span className="flex-shrink-0 flex items-center justify-center h-10 w-10 rounded-full bg-amber-500/20 border border-amber-400/30 animate-pulse">
                            <span className="text-lg">⚠️</span>
                        </span>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-amber-300">
                                U {data.questionnaire_unknowns.length} otázek jste zvolili &bdquo;Nevím&ldquo;
                            </p>
                            <p className="text-xs text-slate-400 mt-0.5">
                                Doplňte odpovědi pro přesnější compliance analýzu — čím více víme, tím kvalitnější dokumenty připravíme
                            </p>
                        </div>
                        <span className="flex-shrink-0 text-sm font-bold text-amber-400 group-hover:text-amber-300 transition-colors">
                            Doplnit →
                        </span>
                    </a>
                )}

                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                    <StatCard
                        label="Stav procesu"
                        value={`${stepsCompleted}/4`}
                        sub={stepsCompleted === 4 ? "Compliance kompletní" : stepsCompleted >= 3 ? "Téměř hotovo" : "Dokončete kroky níže"}
                        color={stepsCompleted === 4 ? "text-green-400" : stepsCompleted >= 2 ? "text-amber-400" : "text-cyan-400"}
                    />
                    <StatCard
                        label="AI systémy"
                        value={String(totalAiSystems)}
                        sub={totalAiSystems === 0 ? "Žádné nalezeny" : highRisk > 0 ? `${highRisk} vysoké riziko` : `${scanFindings} ze skenu, ${questFindings} z dotazníku`}
                        color={highRisk > 0 ? "text-red-400" : totalAiSystems > 0 ? "text-cyan-400" : "text-slate-500"}
                    />
                    <StatCard
                        label="Dokumenty"
                        value={String(docsCount)}
                        sub={docsCount >= 7 ? "Kompletní kit" : docsCount > 0 ? "Ke stažení" : "Zatím negenerováno"}
                        color={docsCount >= 7 ? "text-green-400" : docsCount > 0 ? "text-cyan-400" : "text-slate-500"}
                    />
                    <StatCard
                        label="Dotazník"
                        value={questionnaireIsComplete ? "Hotovo" : questionnaireAllAnswered ? `${qUnknownCount}× nevím` : qAnswered > 0 ? `${qAnswered}/${qTotal}` : "Čeká"}
                        sub={questionnaireIsComplete ? "Kompletní" : questionnaireAllAnswered ? "Doplňte odpovědi" : qAnswered > 0 ? "Pokračujte ve vyplňování" : "Vyplňte pro přesnější analýzu"}
                        color={questionnaireIsComplete ? "text-green-400" : questionnaireAllAnswered ? "text-amber-400" : qAnswered > 0 ? "text-cyan-400" : "text-amber-400"}
                        href={questionnaireIsComplete ? undefined : (questionnaireAllAnswered && qUnknowns[0]?.question_key && data?.company?.id) ? `/dotaznik?company_id=${data.company.id}&edit=true&q=${qUnknowns[0].question_key}` : (data?.company?.id ? `/dotaznik?company_id=${data.company.id}` : "/dotaznik")}
                    />
                </div>

                {/* Desktop tabs */}
                <div className="hidden md:flex gap-6">
                    {/* Levý sidebar */}
                    <nav className="w-56 flex-shrink-0 space-y-1">
                        {TABS.map((tab) => (
                            <button
                                key={tab.key}
                                onClick={() => setActiveTab(tab.key)}
                                className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm font-medium rounded-xl transition-all ${activeTab === tab.key
                                    ? "text-fuchsia-400 bg-fuchsia-500/10 border border-fuchsia-500/20 shadow-[0_0_12px_-3px_rgba(217,70,239,0.2)]"
                                    : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.04] border border-transparent"
                                    }`}
                            >
                                {tab.icon}
                                {tab.label}
                            </button>
                        ))}
                    </nav>

                    {/* Hlavní obsah */}
                    <div className="flex-1 min-w-0 min-h-[400px]">
                        {activeTab === "prehled" && <TabPrehled data={data} onRefresh={fetchData} />}
                        {activeTab === "firma" && <TabFirma company={data?.company || null} answers={data?.questionnaire_answers || {}} scans={data?.scans || []} />}
                        {activeTab === "findings" && <TabFindings findings={data?.findings || []} questFindings={data?.questionnaire_findings || []} />}
                        {activeTab === "dokumenty" && <TabDokumenty documents={uniqueDocs} />}
                        {activeTab === "plan" && <TabPlan findings={data?.findings || []} questFindings={data?.questionnaire_findings || []} resolvedIds={data?.action_plan_resolved || []} onResolvedChange={fetchData} />}
                        {activeTab === "skeny" && <TabSkeny scans={data?.scans || []} />}
                        {activeTab === "dotaznik" && <TabDotaznik answers={data?.questionnaire_answers || {}} status={data?.questionnaire_status || ""} companyId={data?.company?.id} answeredCount={qAnswered} totalQuestions={qTotal} isComplete={questionnaireIsComplete} />}
                    </div>
                </div>
                {/* Mobile accordion tabs — obsah se rozbalí přímo pod zvoleným tabem */}
                <div className="md:hidden mb-6 space-y-1">
                    {TABS.map((tab) => (
                        <div key={tab.key}>
                            <button
                                onClick={() => setActiveTab(activeTab === tab.key ? "" as Tab : tab.key)}
                                className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-xl transition-all ${activeTab === tab.key
                                    ? "text-fuchsia-400 bg-fuchsia-500/10 border border-fuchsia-500/20"
                                    : "text-slate-400 bg-white/[0.02] border border-white/[0.06] hover:bg-white/[0.04]"
                                    }`}
                            >
                                {tab.icon}
                                {tab.label}
                                <svg className={`w-4 h-4 ml-auto transition-transform ${activeTab === tab.key ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                            </button>
                            {activeTab === tab.key && (
                                <div className="mt-1 mb-2 rounded-xl border border-white/[0.06] bg-white/[0.01] p-4">
                                    {tab.key === "prehled" && <TabPrehled data={data} onRefresh={fetchData} />}
                                    {tab.key === "firma" && <TabFirma company={data?.company || null} answers={data?.questionnaire_answers || {}} scans={data?.scans || []} />}
                                    {tab.key === "findings" && <TabFindings findings={data?.findings || []} questFindings={data?.questionnaire_findings || []} />}
                                    {tab.key === "dokumenty" && <TabDokumenty documents={uniqueDocs} />}
                                    {tab.key === "plan" && <TabPlan findings={data?.findings || []} questFindings={data?.questionnaire_findings || []} resolvedIds={data?.action_plan_resolved || []} onResolvedChange={fetchData} />}
                                    {tab.key === "skeny" && <TabSkeny scans={data?.scans || []} />}
                                    {tab.key === "dotaznik" && <TabDotaznik answers={data?.questionnaire_answers || {}} status={data?.questionnaire_status || ""} companyId={data?.company?.id} answeredCount={qAnswered} totalQuestions={qTotal} isComplete={questionnaireIsComplete} />}
                                </div>
                            )}
                        </div>
                    ))}
                </div>

                {/* Cenové balíčky + srovnání — pod taby, zobrazí se pouze po kompletním dotazníku a bez zaplacené objednávky */}
                {!ps.payment_done && (data?.scans?.length || 0) > 0 && (
                    <div className="mt-8">
                        {questionnaireIsComplete ? (
                            <PricingComparisonTable />
                        ) : (
                            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.02] p-6 text-center">
                                <div className="w-12 h-12 rounded-xl bg-amber-500/15 border border-amber-500/25 flex items-center justify-center mx-auto mb-3">
                                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>
                                </div>
                                <h4 className="text-sm font-semibold text-slate-200 mb-1">{questionnaireAllAnswered ? "Doplňte odpovědi v dotazníku" : "Nejprve dokončete dotazník"}</h4>
                                <p className="text-xs text-slate-400 mb-4">
                                    {questionnaireAllAnswered ? `U ${qUnknownCount} otázek jste zvolili „Nevím" — doplňte je pro přesnější dokumenty` : qAnswered > 0 ? `Zodpovězeno ${qAnswered} z ${qTotal} otázek` : "Vyplňte dotazník pro přesnější analýzu"} — po dokončení si budete moci vybrat balíček.
                                </p>
                                <a
                                    href={(questionnaireAllAnswered && qUnknowns[0]?.question_key && data?.company?.id) ? `/dotaznik?company_id=${data.company.id}&edit=true&q=${qUnknowns[0].question_key}` : data?.company?.id ? `/dotaznik?company_id=${data.company.id}` : "/dotaznik"}
                                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 text-white text-sm font-semibold transition-all hover:shadow-lg hover:shadow-amber-500/25 active:scale-[0.98]"
                                >
                                    {questionnaireAllAnswered ? "Doplnit dotazník" : qAnswered > 0 ? "Pokračovat v dotazníku" : "Vyplnit dotazník"}
                                </a>
                            </div>
                        )}
                    </div>
                )}

            </div>
        </section>
    );
}

function getUniqueDocs(documents: DashboardData["documents"]) {
    const seen = new Set<string>();
    const result: DashboardData["documents"] = [];
    for (const doc of documents) {
        const key = doc.template_key || doc.name;
        if (!seen.has(key)) {
            seen.add(key);
            result.push(doc);
        }
    }
    return result;
}

function StatCard({ label, value, sub, color, href }: {
    label: string; value: string; sub: string; color: string; href?: string;
}) {
    const card = (
        <div className={`rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 ${href ? "hover:bg-white/[0.04] cursor-pointer transition-colors" : ""}`}>
            <p className="text-xs text-slate-500 uppercase tracking-wider">{label}</p>
            <p className={`text-xl sm:text-3xl font-extrabold mt-1 truncate ${color}`}>{value}</p>
            <p className="text-xs text-slate-500 mt-1 truncate">{sub}</p>
        </div>
    );
    if (href) return <a href={href}>{card}</a>;
    return card;
}

/* ── Kroky skenování — vizuální progress ── */
const SCAN_STAGES = [
    { label: "Připojování k webu", desc: "Otevíráme váš web v bezpečném prohlížeči" },
    { label: "Načítání stránky", desc: "Čekáme, až se web kompletně načte" },
    { label: "Souhlas s cookies", desc: "Klikáme na cookie lištu" },
    { label: "Analýza HTML kódu", desc: "Procházíme zdrojový kód stránky" },
    { label: "Kontrola skriptů", desc: "Hledáme JavaScript knihovny třetích stran" },
    { label: "Procházení podstránek", desc: "Scrollujeme a klikáme na záložky" },
    { label: "Detekce chatbotů a AI", desc: "Zjišťujeme přítomnost chatbotů a AI nástrojů" },
    { label: "Analýza cookies a trackerů", desc: "Kontrolujeme analytické a sledovací cookies" },
    { label: "Síťové požadavky", desc: "Sledujeme komunikaci s AI službami" },
    { label: "AI klasifikace nálezů", desc: "AI vyhodnocuje a ověřuje každý nález" },
    { label: "Vyhodnocení rizik", desc: "Klasifikujeme rizika podle EU AI Act" },
    { label: "Příprava reportu", desc: "Generujeme kompletní compliance report" },
];
const EXPECTED_SCAN_MS = 90_000;

/* ═══════════════════════════════════════════
   PIPELINE PROGRESS — vždy viditelná nad stat kartami
   ═══════════════════════════════════════════ */
function PipelineProgress({ data, onRefresh }: { data: DashboardData | null; onRefresh: () => void }) {
    const [deepScanLoading, setDeepScanLoading] = useState(false);
    const [deepScanError, setDeepScanError] = useState<string | null>(null);
    const [inlineScanLoading, setInlineScanLoading] = useState(false);
    const [inlineScanError, setInlineScanError] = useState<string | null>(null);
    const [inlineScanProgress, setInlineScanProgress] = useState<string | null>(null);
    const inlineScanPollRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const [inlineScanStage, setInlineScanStage] = useState(0);
    const [inlineScanCountdown, setInlineScanCountdown] = useState(120);
    const inlineStageRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const inlineCountdownRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const inlineScanStartRef = useRef<number>(0);

    const ps = data?.process_status;
    const hasPaidOrder = ps?.payment_done ?? data?.orders.some((o) => o.status === "PAID") ?? false;
    const hasScans = ps?.scan_done ?? (data?.scans.length || 0) > 0;
    const qAns = data?.questionnaire_answered_count ?? 0;
    const qTot = data?.questionnaire_total_questions ?? 0;
    const qUnknownCount = data?.questionnaire_unknown_count ?? 0;
    const hasQuest = (qTot > 0 && qAns >= qTot && qUnknownCount === 0) || (ps?.questionnaire_done ?? false);
    const questStarted = !hasQuest && (qAns > 0 || qUnknownCount > 0 || (data?.questionnaire_status?.startsWith("rozpracován") ?? false));
    const allAnsweredWithUnknowns = !hasQuest && qUnknownCount > 0 && (qAns + qUnknownCount) >= qTot;
    const hasDocs = ps?.documents_done ?? (data?.documents.length || 0) > 0;
    const hasOrder = (data?.orders || []).length > 0;
    const ws = data?.company?.workflow_status || 'new';
    const isProcessingDocs = ws === 'processing' || ws === 'documents_sent';
    const qUnknowns = data?.questionnaire_unknowns || [];

    const latestScan = data?.scans?.[0];
    const deepStatus = latestScan?.deep_scan_status;
    const deepDone = deepStatus === 'done' || deepStatus === 'cooldown';
    const deepRunning = deepStatus === 'pending' || deepStatus === 'running';

    const handleTriggerDeepScan = async () => {
        if (!latestScan?.id) return;
        setDeepScanLoading(true);
        setDeepScanError(null);
        try {
            await triggerDeepScan(latestScan.id);
            onRefresh();
        } catch (e: unknown) {
            setDeepScanError((e as Error).message || "Nepodařilo se spustit");
        } finally {
            setDeepScanLoading(false);
        }
    };

    // Vyčištění scan animací
    const cleanupScanAnimation = useCallback(() => {
        if (inlineStageRef.current) { clearInterval(inlineStageRef.current); inlineStageRef.current = null; }
        if (inlineCountdownRef.current) { clearInterval(inlineCountdownRef.current); inlineCountdownRef.current = null; }
    }, []);

    // Spuštění stage animace + countdown
    const startScanAnimation = useCallback(() => {
        setInlineScanStage(0);
        setInlineScanCountdown(120);
        inlineScanStartRef.current = Date.now();
        cleanupScanAnimation();
        // Countdown — tik každou sekundu
        inlineCountdownRef.current = setInterval(() => {
            setInlineScanCountdown(prev => (prev > 0 ? prev - 1 : 0));
        }, 1000);
        // Stage progrese — plynule podle uplynulého času
        inlineStageRef.current = setInterval(() => {
            const elapsed = Date.now() - inlineScanStartRef.current;
            const progress = Math.min(elapsed / EXPECTED_SCAN_MS, 0.92);
            const target = Math.min(Math.floor(progress * SCAN_STAGES.length), SCAN_STAGES.length - 1);
            setInlineScanStage(prev => Math.max(prev, target));
        }, 1000);
    }, [cleanupScanAnimation]);

    // Cleanup při unmount
    useEffect(() => {
        return () => {
            cleanupScanAnimation();
            if (inlineScanPollRef.current) clearInterval(inlineScanPollRef.current);
        };
    }, [cleanupScanAnimation]);

    const handleInlineScan = async () => {
        const website = data?.company?.url;
        if (!website) return;
        setInlineScanLoading(true);
        setInlineScanError(null);
        setInlineScanProgress("Spouštím sken…");
        startScanAnimation();
        try {
            let url = website.trim();
            if (!url.match(/^https?:\/\//i)) url = "https://" + url;
            const result = await startScan(url);
            setInlineScanProgress("Skenování probíhá…");

            if (result.status === "cached" || result.status === "done") {
                setInlineScanProgress(null);
                setInlineScanLoading(false);
                setInlineScanStage(SCAN_STAGES.length);
                cleanupScanAnimation();
                onRefresh();
                return;
            }

            // Poll for completion
            let attempts = 0;
            const maxAttempts = 60;
            if (inlineScanPollRef.current) clearInterval(inlineScanPollRef.current);
            inlineScanPollRef.current = setInterval(async () => {
                attempts++;
                try {
                    const status = await getScanStatus(result.scan_id);
                    if (status.status === "done" || status.status === "error") {
                        if (inlineScanPollRef.current) clearInterval(inlineScanPollRef.current);
                        setInlineScanProgress(null);
                        setInlineScanLoading(false);
                        setInlineScanStage(SCAN_STAGES.length);
                        cleanupScanAnimation();
                        if (status.status === "error") {
                            setInlineScanError("Sken selhal — zkuste to znovu.");
                        }
                        onRefresh();
                    }
                } catch {
                    // ignore poll errors
                }
                if (attempts >= maxAttempts) {
                    if (inlineScanPollRef.current) clearInterval(inlineScanPollRef.current);
                    setInlineScanProgress(null);
                    setInlineScanLoading(false);
                    setInlineScanStage(SCAN_STAGES.length);
                    cleanupScanAnimation();
                    onRefresh();
                }
            }, 3000);
        } catch (e: unknown) {
            setInlineScanError((e as Error).message || "Nepodařilo se spustit sken");
            setInlineScanProgress(null);
            setInlineScanLoading(false);
            cleanupScanAnimation();
        }
    };

    const steps = [
        {
            done: hasScans,
            label: "Sken webu",
            desc: "Automatická detekce AI systémů na vašem webu",
            detail: null as string | null,
            href: null as string | null,
            cta: "__inline_scan__",
        },
        {
            done: deepDone || deepRunning || (hasQuest && hasPaidOrder),
            optional: true,
            label: deepRunning && !deepDone ? "24h test ⏳" : deepDone ? "24h test ✅" : "24h test",
            desc: deepDone
                ? `Dokončen — nalezeno ${(data?.findings?.length || 0)} AI ${(data?.findings?.length || 0) === 1 ? "systém" : (data?.findings?.length || 0) < 5 ? "systémy" : "systémů"} ze ${latestScan?.geo_countries_scanned?.length || 8} zemí`
                : deepRunning
                    ? "Hloubkový scan probíhá na pozadí ze 8 zemí — mezitím pokračujte dotazníkem"
                    : hasScans
                        ? "Spusťte 24hodinový hloubkový test ze 8 zemí a 6 kontinentů"
                        : "Nejprve dokončete rychlý sken webu",
            detail: null,
            href: null,
            cta: "__deep_scan_custom__",
        },
        {
            done: hasQuest,
            label: "Dotazník",
            desc: hasQuest
                ? (qUnknowns.length > 0 ? `U ${qUnknowns.length} otázek jste zvolili „Nevím" — doplňte je` : "Všechny odpovědi jsou kompletní")
                : allAnsweredWithUnknowns
                    ? `U ${qUnknownCount} ${qUnknownCount === 1 ? "otázky" : "otázek"} jste zvolili „Nevím" — doplňte je pro kompletní analýzu`
                    : questStarted
                        ? `Rozpracovaný dotazník — ${qAns}/${qTot} odpovědí`
                        : "Upřesní analýzu o interní AI nástroje (ChatGPT, Copilot…)",
            detail: hasQuest || questStarted ? null : "EU AI Act se netýká jen toho, co je vidět na webu. Regulace zahrnuje i interní AI systémy — nástroje pro HR, účetnictví, rozhodování, generování obsahu nebo komunikaci se zaměstnanci. Automatický sken odhalí jen veřejně viditelné nástroje. Dotazník pokrývá celou AI politiku firmy, včetně toho, co zákazník nikdy neuvidí.",
            href: allAnsweredWithUnknowns && data?.company?.id ? `/dotaznik?company_id=${data.company.id}&edit=true&q=${qUnknowns[0]?.question_key || ""}` : (hasScans || questStarted) && !hasQuest && data?.company?.id ? `/dotaznik?company_id=${data.company.id}` : hasQuest && qUnknowns.length > 0 && data?.company?.id ? `/dotaznik?company_id=${data.company.id}&edit=true&q=${qUnknowns[0]?.question_key || ""}` : null,
            cta: !hasScans ? "🔒 Nejprve skenujte web" : !data?.company?.id ? "⏳ Čekáme na výsledky skenu" : allAnsweredWithUnknowns ? `Doplnit ${qUnknownCount} ${qUnknownCount === 1 ? "odpověď" : "odpovědi"} s Nevím` : !hasQuest ? (questStarted ? "Pokračovat v dotazníku" : "Vyplnit dotazník") : qUnknowns.length > 0 ? "Doplnit odpovědi" : "✓ Kompletní",
        },
        {
            done: hasOrder,
            label: "Objednávka",
            desc: hasOrder ? "Objednávka byla přijata" : !hasQuest && qUnknownCount > 0 ? `Doplňte ${qUnknownCount} odpověd${qUnknownCount === 1 ? "ě" : "í"} označen${qUnknownCount === 1 ? "ou" : "ých"} jako „Nevím"` : !hasQuest ? "Nejprve dokončete dotazník" : "Odemkněte compliance dokumenty a školení",
            detail: null,
            href: hasOrder ? null : !hasQuest ? null : "/pricing",
            cta: hasOrder ? "✓ Objednáno" : !hasQuest ? (qUnknownCount > 0 ? "Doplňte odpovědi" : "Nejprve dokončete dotazník") : "Vybrat balíček",
        },
        {
            done: hasPaidOrder,
            label: "Platba",
            desc: hasPaidOrder ? "Platba byla přijata" : hasOrder ? "Čekáme na připsání platby na účet" : "Po objednání obdržíte platební údaje",
            detail: null,
            href: null,
            cta: hasPaidOrder ? "✓ Zaplaceno" : hasOrder ? "Čeká na platbu" : "",
        },
        {
            done: isProcessingDocs || ws === 'generating' || ws === 'awaiting_approval',
            label: "Tvorba dokumentace",
            desc: ws === 'awaiting_approval'
                ? "Dokumenty byly vygenerovány — probíhá kontrola kvality"
                : ws === 'generating'
                    ? "Pracujeme na vaší dokumentaci — elektronické PDF do 7 pracovních dnů"
                    : isProcessingDocs
                        ? "Pracujeme na vaší dokumentaci — elektronické PDF do 7 pracovních dnů"
                        : !deepDone && deepRunning
                            ? "Čekáme na výsledky 24hodinového hloubkového testu"
                            : deepDone && hasPaidOrder
                                ? "24h test dokončen — výrobu dokumentů spustí náš tým po kontrole výsledků"
                                : deepDone
                                    ? "24h test dokončen — po zaplacení spustíme výrobu dokumentů"
                                    : hasPaidOrder
                                        ? "Jakmile doběhne 24h test, budeme moci spustit výrobu dokumentů"
                                        : "Po zaplacení a dokončení 24h testu začneme s tvorbou",
            detail: null,
            href: null,
            cta: ws === 'awaiting_approval'
                ? "Kontrola kvality"
                : ws === 'generating'
                    ? "Zpracováváme"
                    : isProcessingDocs
                        ? "Zpracováváme"
                        : !deepDone && deepRunning
                            ? "⏳ 24h test probíhá"
                            : deepDone && hasPaidOrder
                                ? "Čeká na spuštění výroby"
                                : "",
        },
        {
            done: hasDocs,
            label: "Dodání",
            desc: hasDocs ? "Dokumenty jsou připraveny ke stažení — tištěnou verzi doručíme do 14 dnů" : "14 compliance dokumentů v PDF, HTML a PPTX + tištěná verze v profesionální vazbě",
            detail: null,
            href: null,
            cta: hasDocs ? "Viz tab Dokumenty" : "",
        },
    ];

    const rawStepIndex = steps.findIndex((s) => !s.done);
    const currentStepIndex = (rawStepIndex === 1 && steps[2]?.done) ? steps.findIndex((s, i) => i > 1 && !s.done) : rawStepIndex;
    const currentStep = currentStepIndex >= 0 ? steps[currentStepIndex] : null;
    const progressTarget = currentStepIndex >= 0 ? currentStepIndex : steps.length - 1;
    const lineWidthPercent = progressTarget <= 0 ? 0 : (progressTarget / (steps.length - 1)) * ((steps.length - 1) / steps.length * 100);
    const verticalProgressPercent = progressTarget <= 0 ? 0 : (progressTarget / (steps.length - 1)) * 100;

    return (
        <div className="mb-8 space-y-4">
            {/* Pipeline vizualizace — zelená čára s body */}
            <div className="glass">
                <h3 className="font-semibold mb-8">Váš postup k AI Act compliance</h3>
                {/* Mobile: vertikální timeline */}
                <div className="md:hidden relative mb-8">
                    <div className="absolute left-[17px] top-[26px] bottom-[26px] w-1 rounded-full bg-gradient-to-b from-white/[0.04] via-white/[0.08] to-white/[0.04]" />
                    {verticalProgressPercent > 0 && (
                        <div
                            className="absolute left-[17px] top-[26px] w-1 rounded-full transition-all duration-700"
                            style={{
                                height: `calc((100% - 52px) * ${verticalProgressPercent / 100})`,
                                background: 'linear-gradient(180deg, #22c55e, #10b981, #06b6d4, #a855f7)',
                                boxShadow: '0 0 12px rgba(34,197,94,0.4), 0 0 24px rgba(6,182,212,0.2)',
                            }}
                        />
                    )}
                    {steps.map((step, i) => {
                        const isCurrent = i === currentStepIndex;
                        const isSkipped = !step.done && (step as { optional?: boolean }).optional && i < (currentStepIndex >= 0 ? currentStepIndex : steps.length);
                        const isRunning = i === 1 && deepRunning && !deepDone;
                        return (
                            <div key={i} className="flex items-center gap-3 relative z-10 py-2">
                                <div className={`flex-shrink-0 flex items-center justify-center h-9 w-9 rounded-full text-xs font-bold transition-all duration-500 ${step.done && !isRunning
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
                                        <svg className="w-5 h-5 drop-shadow-[0_0_4px_rgba(34,197,94,0.6)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                                <span className={`text-xs font-semibold ${step.done
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

                {/* Desktop: horizontální grid */}
                <div className="hidden md:grid grid-cols-7 relative mb-8">
                    <div className="absolute top-[22px] left-[7%] right-[7%] h-1 rounded-full bg-gradient-to-r from-white/[0.04] via-white/[0.08] to-white/[0.04]" />
                    {lineWidthPercent > 0 && (
                        <div
                            className="absolute top-[22px] left-[7%] h-1 rounded-full transition-all duration-700"
                            style={{
                                width: `${lineWidthPercent}%`,
                                background: 'linear-gradient(90deg, #22c55e, #10b981, #06b6d4, #a855f7)',
                                boxShadow: '0 0 12px rgba(34,197,94,0.4), 0 0 24px rgba(6,182,212,0.2)',
                            }}
                        />
                    )}
                    {steps.map((step, i) => {
                        const isCurrent = i === currentStepIndex;
                        const isSkipped = !step.done && (step as { optional?: boolean }).optional && i < (currentStepIndex >= 0 ? currentStepIndex : steps.length);
                        const isRunning = i === 1 && deepRunning && !deepDone;
                        return (
                            <div key={i} className="flex flex-col items-center relative z-10">
                                <div className={`flex items-center justify-center h-11 w-11 rounded-full text-sm font-bold transition-all duration-500 ${step.done && !isRunning
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
                                        <svg className="w-6 h-6 drop-shadow-[0_0_4px_rgba(34,197,94,0.6)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                                <span className={`text-[11px] mt-2.5 font-semibold text-center leading-tight ${step.done
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

                {/* Aktuální krok — JEDINÉ CTA */}
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
                        {currentStep.cta === "__inline_scan__" ? (
                            <div className="ml-0 sm:ml-9 space-y-3">
                                {inlineScanLoading ? (
                                    <div className="space-y-4">
                                        {/* Záhlaví + countdown */}
                                        <div className="flex items-center justify-between gap-2">
                                            <div className="flex items-center gap-3 min-w-0">
                                                <div className="w-6 h-6 rounded-full border-2 border-fuchsia-400 border-t-transparent animate-spin flex-shrink-0" />
                                                <div className="min-w-0">
                                                    <p className="text-sm font-semibold text-white">Skenování probíhá…</p>
                                                    <p className="text-xs text-slate-400 truncate">{data?.company?.url}</p>
                                                </div>
                                            </div>
                                            <div className="text-right flex-shrink-0">
                                                <div className="inline-flex items-center gap-1.5 rounded-xl bg-white/[0.04] border border-white/[0.08] px-2.5 py-1.5">
                                                    <svg className="w-3.5 h-3.5 text-fuchsia-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6l4 2m6-2a10 10 0 11-20 0 10 10 0 0120 0z" />
                                                    </svg>
                                                    <span className="font-mono text-sm font-bold text-white tabular-nums">
                                                        {inlineScanCountdown > 0
                                                            ? `${Math.floor(inlineScanCountdown / 60)}:${(inlineScanCountdown % 60).toString().padStart(2, '0')}`
                                                            : '0:00'}
                                                    </span>
                                                </div>
                                                <p className="text-[10px] text-slate-500 mt-0.5">
                                                    {inlineScanCountdown > 0 ? 'zbývající čas' : 'ještě chvíli…'}
                                                </p>
                                            </div>
                                        </div>

                                        {/* Progress bar */}
                                        <div>
                                            <div className="flex justify-between text-xs text-slate-500 mb-1">
                                                <span>{SCAN_STAGES[Math.min(inlineScanStage, SCAN_STAGES.length - 1)]?.label}</span>
                                                <span>{Math.round(((inlineScanStage + 1) / SCAN_STAGES.length) * 100)} %</span>
                                            </div>
                                            <div className="h-2.5 bg-white/[0.06] rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-gradient-to-r from-fuchsia-600 via-purple-500 to-cyan-500 rounded-full transition-all duration-1000 ease-out"
                                                    style={{ width: ((inlineScanStage + 1) / SCAN_STAGES.length) * 100 + "%" }}
                                                />
                                            </div>
                                        </div>

                                        {/* Jednotlivé kroky */}
                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                                            {SCAN_STAGES.map((stage, i) => {
                                                const done = i < inlineScanStage;
                                                const active = i === inlineScanStage;
                                                return (
                                                    <div
                                                        key={i}
                                                        className={"flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-xs transition-all duration-500 " +
                                                            (done ? "bg-green-500/8 border border-green-500/15" :
                                                                active ? "bg-fuchsia-500/10 border border-fuchsia-500/20" :
                                                                    "bg-white/[0.02] border border-white/[0.04] opacity-40")
                                                        }
                                                    >
                                                        <div className="flex-shrink-0">
                                                            {done ? (
                                                                <svg className="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                                </svg>
                                                            ) : active ? (
                                                                <div className="w-4 h-4 rounded-full border-2 border-fuchsia-400 border-t-transparent animate-spin" />
                                                            ) : (
                                                                <div className="w-4 h-4 rounded-full border border-white/10" />
                                                            )}
                                                        </div>
                                                        <div className="min-w-0">
                                                            <p className={"font-medium leading-tight " + (done ? "text-green-400" : active ? "text-white" : "text-slate-500")}>
                                                                {stage.label}
                                                            </p>
                                                            {active && <p className="text-[10px] text-slate-400 leading-tight mt-0.5">{stage.desc}</p>}
                                                        </div>
                                                    </div>
                                                );
                                            })}
                                        </div>

                                        {/* Varování u posledních kroků */}
                                        {inlineScanStage >= SCAN_STAGES.length - 2 && (
                                            <div className="flex items-start gap-2 rounded-lg bg-amber-500/10 border border-amber-500/25 px-3 py-2">
                                                <svg className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M12 3l9.66 16.5a1 1 0 01-.87 1.5H3.21a1 1 0 01-.87-1.5L12 3z" />
                                                </svg>
                                                <div>
                                                    <p className="text-xs font-medium text-amber-300">Neopouštějte stránku</p>
                                                    <p className="text-[10px] text-amber-400/70 mt-0.5">AI vyhodnocuje nálezy — prosím vyčkejte.</p>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    <>
                                        {data?.company?.url && (
                                            <p className="text-xs text-slate-400">
                                                Web: <strong className="text-white truncate max-w-[220px] inline-block align-bottom">{data.company.url}</strong>
                                            </p>
                                        )}
                                        <button
                                            onClick={handleInlineScan}
                                            disabled={!data?.company?.url}
                                            className="relative overflow-hidden w-full sm:w-auto rounded-xl bg-gradient-to-r from-purple-600 to-fuchsia-600 px-6 py-3 text-sm font-bold text-white shadow-lg shadow-purple-500/25 hover:shadow-purple-500/40 hover:from-purple-500 hover:to-fuchsia-500 transition-all disabled:opacity-50 group"
                                        >
                                            <span className="absolute inset-0 rounded-xl animate-pulse bg-gradient-to-r from-purple-400/20 to-fuchsia-400/20" />
                                            <span className="relative flex items-center justify-center gap-2">
                                                🔍 Spustit sken webu
                                            </span>
                                        </button>
                                        {inlineScanError && (
                                            <p className="text-xs text-red-400">{inlineScanError}</p>
                                        )}
                                    </>
                                )}
                            </div>
                        ) : currentStep.cta === "__deep_scan_custom__" ? (
                            <div className="ml-0 sm:ml-9 space-y-3">
                                {!deepRunning && !deepDone && (
                                    <div className="space-y-3">
                                        <p className="text-xs text-slate-400 leading-relaxed">
                                            Chatboti a AI nástroje se často zobrazují jen v určitou hodinu, z určité lokace nebo na mobilním zařízení — rychlý scan je nemůže odhalit všechny.
                                        </p>
                                        <button
                                            onClick={handleTriggerDeepScan}
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
                                            🇨🇿 🇬🇧 🇺🇸 🇧🇷 🇯🇵 🇿🇦 🇦🇺 🇩🇪 — 8 zemí, 6 kontinentů, desktop i mobil
                                        </p>
                                    </div>
                                )}
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
                                        {!hasQuest && data?.company?.id && (
                                            <a
                                                href={`/dotaznik?company_id=${data.company.id}`}
                                                className="relative overflow-hidden inline-flex items-center justify-center w-full sm:w-auto rounded-xl bg-gradient-to-r from-fuchsia-600 to-purple-600 px-8 py-4 text-base font-bold text-white shadow-lg shadow-fuchsia-500/30 hover:shadow-fuchsia-500/50 hover:from-fuchsia-500 hover:to-purple-500 transition-all"
                                            >
                                                <span className="absolute inset-0 rounded-xl animate-pulse bg-gradient-to-r from-fuchsia-400/20 to-purple-400/20" />
                                                <span className="relative">{questStarted ? "📝 Pokračovat v dotazníku" : "📝 Vyplnit dotazník"}</span>
                                            </a>
                                        )}
                                    </div>
                                )}
                            </div>
                        ) : currentStep.href && currentStep.href !== "#" ? (
                            <a href={currentStep.href} className="btn-primary text-sm px-5 py-2 ml-0 sm:ml-9 inline-block">{currentStep.cta}</a>
                        ) : !currentStep.href && currentStep.cta ? (
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

                {/* Stav procesu — přehledný seznam */}
                {steps.some(s => s.done) && (
                    <div className="mt-6 rounded-xl border border-white/[0.08] bg-white/[0.02] p-5 sm:p-6">
                        <p className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Stav procesu</p>
                        <div className="space-y-3">
                            {steps.map((step, i) => {
                                const isOptionalSkipped = (step as { optional?: boolean }).optional && !step.done;
                                const isRunning = i === 1 && !step.done && step.label.includes("⏳");
                                return (
                                    <div key={i} className={`flex items-start gap-3 rounded-lg px-3 py-2.5 transition-colors ${
                                        step.done
                                            ? "bg-green-500/[0.06] border border-green-500/15"
                                            : isRunning
                                                ? "bg-cyan-500/[0.06] border border-cyan-500/15"
                                                : "bg-white/[0.01] border border-white/[0.04]"
                                    }`}>
                                        <div className="flex-shrink-0 mt-0.5">
                                            {step.done ? (
                                                <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                </svg>
                                            ) : isRunning ? (
                                                <div className="w-5 h-5 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin" />
                                            ) : isOptionalSkipped ? (
                                                <div className="w-5 h-5 rounded-full border-2 border-dashed border-slate-600 flex items-center justify-center">
                                                    <span className="text-[10px] text-slate-600">—</span>
                                                </div>
                                            ) : (
                                                <div className="w-5 h-5 rounded-full border-2 border-slate-600 flex items-center justify-center">
                                                    <span className="text-[10px] text-slate-600">{i + 1}</span>
                                                </div>
                                            )}
                                        </div>
                                        <div className="min-w-0 flex-1">
                                            <span className={`text-sm font-medium ${
                                                step.done
                                                    ? "text-green-400"
                                                    : isRunning
                                                        ? "text-cyan-300"
                                                        : "text-slate-500"
                                            }`}>{step.label}</span>
                                            <p className={`text-xs mt-0.5 leading-relaxed ${
                                                step.done ? "text-slate-400" : "text-slate-600"
                                            }`}>{step.desc?.split("—")[0]?.trim()}</p>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}
            </div>

            {/* 24h deep scan running banner */}
            {deepRunning && !deepDone && currentStepIndex !== 1 && (
                <DeepScanBanner startedAt={latestScan?.deep_scan_started_at} />
            )}

            {/* Výsledky deep scanu po dokončení */}
            {deepDone && (data?.findings || []).length > 0 && (
                <DeepScanResultsCard
                    findings={data?.findings || []}
                    totalScans={latestScan?.deep_scan_total_findings ?? null}
                    countries={latestScan?.geo_countries_scanned ?? null}
                    finishedAt={latestScan?.deep_scan_finished_at ?? null}
                />
            )}
        </div>
    );
}

/* ═══════════════════════════════════════════
   Výsledky deep scanu — karta s nalezmi
   ═══════════════════════════════════════════ */

const AI_ACT_ARTICLE_URLS: Record<string, string> = {
    "čl. 4": "https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689#art_4",
    "čl. 5": "https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689#art_5",
    "čl. 6": "https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689#art_6",
    "čl. 26": "https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689#art_26",
    "čl. 27": "https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689#art_27",
    "čl. 50": "https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689#art_50",
    "čl. 52": "https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689#art_52",
};

const COUNTRY_FLAGS: Record<string, string> = {
    cz: "🇨🇿", gb: "🇬🇧", us: "🇺🇸", br: "🇧🇷", jp: "🇯🇵", za: "🇿🇦", au: "🇦🇺", de: "🇩🇪",
};

function DeepScanResultsCard({
    findings,
    totalScans,
    countries,
    finishedAt,
}: {
    findings: DashboardData["findings"];
    totalScans: number | null;
    countries: string[] | null;
    finishedAt: string | null;
}) {
    const [expanded, setExpanded] = useState(false);

    const highCount = findings.filter(f => f.risk_level === "high").length;
    const limitedCount = findings.filter(f => f.risk_level === "limited").length;
    const minimalCount = findings.filter(f => f.risk_level === "minimal").length;

    const riskColor = (level: string) => {
        switch (level) {
            case "high": return "bg-red-500/12 text-red-400 border-red-500/30";
            case "limited": return "bg-amber-500/12 text-amber-400 border-amber-500/30";
            case "minimal": return "bg-slate-500/12 text-slate-300 border-slate-400/25";
            default: return "bg-white/10 text-slate-400 border-white/[0.08]";
        }
    };
    const riskText = (level: string) => {
        switch (level) {
            case "high": return "Vysoké riziko";
            case "limited": return "Omezené riziko";
            case "minimal": return "Minimální riziko";
            default: return level;
        }
    };
    const categoryText = (cat: string) => {
        switch (cat) {
            case "chatbot": return "Chatbot";
            case "analytics": return "Analytika";
            case "recommender": return "Doporučování";
            case "content_gen": return "Generování obsahu";
            default: return cat;
        }
    };

    // Odkaz na článek AI Act
    const articleLink = (article: string) => {
        const key = article.split(",")[0]?.trim();
        const url = AI_ACT_ARTICLE_URLS[key];
        if (url) {
            return (
                <a href={url} target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:text-cyan-300 underline underline-offset-2 transition-colors">
                    {article}
                </a>
            );
        }
        return <span>{article}</span>;
    };

    const finishedDate = finishedAt ? new Date(finishedAt).toLocaleDateString("cs-CZ", { day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit" }) : null;

    return (
        <div className="glass border-green-500/20">
            {/* Hlavička */}
            <div className="flex items-start gap-4">
                <div className="flex-shrink-0 h-10 w-10 rounded-full bg-green-500/15 border border-green-500/30 flex items-center justify-center">
                    <span className="text-lg">✅</span>
                </div>
                <div className="flex-1 min-w-0">
                    <h4 className="font-semibold text-green-300 text-sm">24h hloubkový test dokončen</h4>
                    <p className="text-xs text-slate-400 mt-1">
                        Nalezeno <strong className="text-white">{findings.length} AI {findings.length === 1 ? "systém" : findings.length < 5 ? "systémy" : "systémů"}</strong>
                        {countries && countries.length > 0 && (
                            <> — skenováno z {countries.length} {countries.length === 1 ? "země" : countries.length < 5 ? "zemí" : "zemí"}</>
                        )}
                    </p>
                    {finishedDate && <p className="text-[10px] text-slate-500 mt-0.5">Dokončeno: {finishedDate}</p>}
                </div>
            </div>

            {/* Souhrn rizik */}
            <div className="flex flex-wrap gap-2 mt-4">
                {highCount > 0 && (
                    <span className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium bg-red-500/10 text-red-400 border-red-500/25">
                        <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                        {highCount}× vysoké riziko
                    </span>
                )}
                {limitedCount > 0 && (
                    <span className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium bg-amber-500/10 text-amber-400 border-amber-500/25">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                        {limitedCount}× omezené riziko
                    </span>
                )}
                {minimalCount > 0 && (
                    <span className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium bg-slate-500/10 text-slate-300 border-slate-500/25">
                        <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                        {minimalCount}× minimální
                    </span>
                )}
                {countries && countries.length > 0 && (
                    <span className="inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs text-slate-400 border-white/[0.08] bg-white/[0.03]">
                        {countries.map(c => COUNTRY_FLAGS[c] || c).join(" ")}
                    </span>
                )}
            </div>

            {/* Rozbalit/Sbalit */}
            <button
                onClick={() => setExpanded(!expanded)}
                className="mt-4 text-xs text-cyan-400 hover:text-cyan-300 transition-colors flex items-center gap-1"
            >
                <svg className={`w-3.5 h-3.5 transition-transform ${expanded ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
                {expanded ? "Skrýt detaily" : "Zobrazit nalezené AI systémy"}
            </button>

            {/* Detailní seznam */}
            {expanded && (
                <div className="mt-4 space-y-2.5">
                    {findings.map((f) => (
                        <div key={f.id} className="rounded-lg border border-white/[0.06] bg-white/[0.02] p-3.5">
                            <div className="flex items-start justify-between gap-3">
                                <div className="min-w-0 flex-1">
                                    <h5 className="font-semibold text-sm text-slate-200">{f.name}</h5>
                                    <p className="text-[11px] text-slate-500 mt-0.5">{categoryText(f.category)}</p>
                                </div>
                                <span className={"inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[10px] font-medium flex-shrink-0 " + riskColor(f.risk_level)}>
                                    {riskText(f.risk_level)}
                                </span>
                            </div>

                            {(f.ai_act_article || f.action_required) && (
                                <div className="mt-2.5 pt-2.5 border-t border-white/[0.05] space-y-1.5">
                                    {f.ai_act_article && (
                                        <p className="text-xs text-slate-500">
                                            <span className="text-slate-400 font-medium">Článek AI Act:</span>{" "}
                                            {articleLink(f.ai_act_article)}
                                        </p>
                                    )}
                                    {f.action_required && (
                                        <p className="text-xs">
                                            <span className="text-fuchsia-400 font-medium">Co musíte udělat:</span>{" "}
                                            <span className="text-slate-300">{f.action_required}</span>
                                        </p>
                                    )}
                                </div>
                            )}
                        </div>
                    ))}

                    {/* Varování o pokutě */}
                    <div className="rounded-lg border border-red-500/20 bg-red-500/[0.04] p-3.5 mt-3">
                        <p className="text-xs text-red-300/80 leading-relaxed">
                            ⚠️ <strong>Povinnost dle AI Act:</strong> Článek 50 ukládá provozovatelům AI systémů povinnost transparentně informovat uživatele.
                            Nesplnění hrozí pokutou až <strong className="text-red-300">35 mil. € / 7 % obratu</strong>.
                            Termín: <strong className="text-red-300">2. srpna 2026</strong>.
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
}

/* ═══════════════════════════════════════════
   Deep Scan Banner s odpočtem
   ═══════════════════════════════════════════ */
function DeepScanBanner({ startedAt }: { startedAt?: string | null }) {
    const [remaining, setRemaining] = useState("");
    const [progress, setProgress] = useState(0);

    useEffect(() => {
        const start = startedAt ? new Date(startedAt).getTime() : Date.now();
        const deadline = start + 24 * 60 * 60 * 1000;

        const tick = () => {
            const now = Date.now();
            const diff = deadline - now;
            if (diff <= 0) {
                setRemaining("dokončení co nevidět…");
                setProgress(100);
                return;
            }
            const h = Math.floor(diff / 3_600_000);
            const m = Math.floor((diff % 3_600_000) / 60_000);
            const s = Math.floor((diff % 60_000) / 1_000);
            setRemaining(`${h}h ${String(m).padStart(2, "0")}m ${String(s).padStart(2, "0")}s`);
            const elapsed = now - start;
            const total = 24 * 60 * 60 * 1000;
            setProgress(Math.min(100, Math.round((elapsed / total) * 100)));
        };

        tick();
        const id = setInterval(tick, 1000);
        return () => clearInterval(id);
    }, [startedAt]);

    return (
        <div className="glass border-cyan-500/20">
            <div className="flex items-start gap-4">
                <div className="flex-shrink-0 h-10 w-10 rounded-full bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center">
                    <span className="text-lg animate-pulse">⏳</span>
                </div>
                <div className="flex-1">
                    <h4 className="font-semibold text-cyan-300 text-sm">24h hloubkový test probíhá</h4>
                    <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                        Testujeme váš web ze <strong className="text-slate-300">8 zemí a 6 kontinentů</strong> (desktop i mobil).
                        Výsledky pošleme e-mailem.
                    </p>
                    {/* Countdown */}
                    <div className="mt-3 space-y-1.5">
                        <div className="flex items-center justify-between text-xs">
                            <span className="text-slate-400">Zbývající čas</span>
                            <span className="font-mono text-cyan-300 font-semibold">{remaining}</span>
                        </div>
                        <div className="w-full h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                            <div
                                className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-fuchsia-500 transition-all duration-1000"
                                style={{ width: `${progress}%` }}
                            />
                        </div>
                        <div className="text-[10px] text-slate-500 text-right">{progress}% dokončeno</div>
                    </div>
                    <div className="flex items-center gap-2 mt-2">
                        <span className="text-[10px] text-slate-500">🇨🇿 🇬🇧 🇺🇸 🇧🇷 🇯🇵 🇿🇦 🇦🇺 🇩🇪</span>
                    </div>
                </div>
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════════
   TAB FIRMA — přehled informací o firmě
   ═══════════════════════════════════════════ */
function TabFirma({ company, answers, scans }: { company: DashboardData["company"]; answers: Record<string, string>; scans: DashboardData["scans"] }) {
    const name = answers.company_legal_name || company?.name || "—";
    const ico = answers.company_ico || "—";
    const web = company?.url || "—";
    const email = answers.company_contact_email || "—";
    const address = answers.company_address ? formatDisplayValue("company_address", answers.company_address) : "—";
    const industry = answers.company_industry || "—";
    const size = answers.company_size || "—";
    const revenue = answers.company_annual_revenue || "—";
    const platform = answers.eshop_platform || "—";
    const phone = company?.phone || "—";
    const registeredAt = company?.created_at ? new Date(company.created_at).toLocaleDateString("cs-CZ") : "—";
    const lastScanUrl = scans.length > 0 ? scans[0].url : null;

    const InfoRow = ({ label, value, href }: { label: string; value: string; href?: string }) => (
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-1 sm:gap-4 py-2.5 border-b border-white/[0.04] last:border-0">
            <span className="text-sm text-slate-400 flex-shrink-0">{label}</span>
            {href && value !== "—" ? (
                <a href={href} target="_blank" rel="noopener noreferrer" className="text-sm text-cyan-400 hover:text-cyan-300 transition-colors sm:text-right break-all">
                    {value}
                </a>
            ) : (
                <span className={`text-sm sm:text-right ${value === "—" ? "text-slate-600" : "text-slate-200"}`}>{value}</span>
            )}
        </div>
    );

    return (
        <div className="space-y-6">
            {/* Hlavička s názvem firmy */}
            <div className="glass">
                <div className="flex items-start gap-4">
                    <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-fuchsia-500/20 to-cyan-500/20 border border-white/[0.08] flex items-center justify-center flex-shrink-0">
                        <svg className="w-6 h-6 text-fuchsia-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                        </svg>
                    </div>
                    <div className="min-w-0">
                        <h3 className="font-semibold text-lg text-slate-100 truncate">{name}</h3>
                        {ico !== "—" && <p className="text-xs text-slate-500 mt-0.5">IČO: {ico}</p>}
                        {web !== "—" && (
                            <a href={web.startsWith("http") ? web : `https://${web}`} target="_blank" rel="noopener noreferrer" className="text-xs text-cyan-400 hover:text-cyan-300 mt-1 block truncate">
                                {web}
                            </a>
                        )}
                    </div>
                </div>
            </div>

            {/* Základní údaje */}
            <div className="glass">
                <h4 className="text-sm font-semibold text-slate-300 mb-3">Základní údaje</h4>
                <div>
                    <InfoRow label="Název firmy" value={name} />
                    <InfoRow label="IČO" value={ico} />
                    <InfoRow label="Web" value={web} href={web !== "—" ? (web.startsWith("http") ? web : `https://${web}`) : undefined} />
                    {lastScanUrl && lastScanUrl !== web && (
                        <InfoRow label="Skenovaný web" value={lastScanUrl} href={lastScanUrl.startsWith("http") ? lastScanUrl : `https://${lastScanUrl}`} />
                    )}
                    <InfoRow label="E-shop platforma" value={platform} />
                </div>
            </div>

            {/* Kontaktní údaje */}
            <div className="glass">
                <h4 className="text-sm font-semibold text-slate-300 mb-3">Kontaktní údaje</h4>
                <div>
                    <InfoRow label="E-mail" value={email} href={email !== "—" ? `mailto:${email}` : undefined} />
                    <InfoRow label="Telefon" value={phone} href={phone !== "—" ? `tel:${phone}` : undefined} />
                    <InfoRow label="Adresa" value={address} />
                </div>
            </div>

            {/* Profil firmy */}
            <div className="glass">
                <h4 className="text-sm font-semibold text-slate-300 mb-3">Profil firmy</h4>
                <div>
                    <InfoRow label="Obor podnikání" value={industry} />
                    <InfoRow label="Velikost firmy" value={size} />
                    <InfoRow label="Roční obrat" value={revenue} />
                    <InfoRow label="Registrace" value={registeredAt} />
                </div>
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════════
   TAB PŘEHLED — objednávky, zpracování, pricing
   ═══════════════════════════════════════════ */
function TabPrehled({ data, onRefresh }: { data: DashboardData | null; onRefresh: () => void }) {
    const ps = data?.process_status;
    const hasPaidOrder = ps?.payment_done ?? data?.orders.some((o) => o.status === "PAID") ?? false;
    const hasScans = ps?.scan_done ?? (data?.scans.length || 0) > 0;
    const hasDocs = ps?.documents_done ?? (data?.documents.length || 0) > 0;
    const isProcessing = hasPaidOrder && !hasDocs && hasScans;

    return (
        <div className="space-y-6">
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
                                Elektronické PDF dokumenty doručíme do 7 pracovních dnů. Tištěnou verzi v profesionální vazbě do 14 dnů. Jakmile budou hotové, pošleme vám e-mail.
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Orders */}
            {data?.orders && data.orders.length > 0 && (
                <div className="glass">
                    <h3 className="font-semibold mb-4">Objednávky</h3>
                    <div className="space-y-2">
                        {data.orders.map((order) => (
                            <div key={order.order_number} className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 rounded-lg border border-white/[0.06] bg-white/[0.02] px-4 py-3 text-sm">
                                <div>
                                    <span className="text-slate-300 font-medium">{order.order_number}</span>
                                    <span className="text-slate-500 ml-2">({order.plan.toUpperCase()})</span>
                                </div>
                                <div className="flex items-center gap-3 flex-wrap">
                                    <span className="text-slate-400 whitespace-nowrap">{new Intl.NumberFormat("cs-CZ").format(order.amount)}&nbsp;Kč</span>
                                    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${order.status === "PAID" ? "bg-green-500/10 text-green-400" : order.status === "CREATED" ? "bg-amber-500/10 text-amber-400" : "bg-red-500/10 text-red-400"}`}>
                                        {order.status === "PAID" ? "Zaplaceno" : order.status === "CREATED" ? "Čeká" : order.status}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Pokud nemá objednávky ani není processing — info */}
            {!isProcessing && (!data?.orders || data.orders.length === 0) && !hasScans && (
                <div className="glass text-center py-12">
                    <div className="mx-auto mb-4 w-14 h-14 rounded-2xl bg-fuchsia-500/10 border border-fuchsia-500/20 flex items-center justify-center">
                        <svg className="w-7 h-7 text-fuchsia-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-white mb-2">Začněte skenem webu</h3>
                    <p className="text-sm text-slate-400 max-w-sm mx-auto">
                        Spusťte orientační sken a vyplňte dotazník — pak si budete moci vybrat balíček a objednat dokumentaci.
                    </p>
                    <a href="#pipeline-scan" className="btn-primary text-sm px-6 py-2.5 mt-4 inline-block">
                        Přejít na sken
                    </a>
                </div>
            )}

            {/* Má sken ale žádnou objednávku — ukaž přehledovou kartu */}
            {!isProcessing && (!data?.orders || data.orders.length === 0) && hasScans && (
                <div className="glass text-center py-12">
                    <div className="mx-auto mb-4 w-14 h-14 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
                        <svg className="w-7 h-7 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-white mb-2">Sken dokončen</h3>
                    <p className="text-sm text-slate-400 max-w-sm mx-auto">
                        Rychlý sken webu proběhl. Nyní vyplňte dotazník a vyberte si balíček dokumentace.
                    </p>
                    <a href="#pipeline-scan" className="btn-primary text-sm px-6 py-2.5 mt-4 inline-block">
                        Pokračovat
                    </a>
                </div>
            )}

        </div>
    );
}

function TabFindings({ findings, questFindings }: { findings: DashboardData["findings"]; questFindings: DashboardData["questionnaire_findings"] }) {
    if (findings.length === 0 && questFindings.length === 0) {
        return <EmptyState title="Žádné AI systémy nalezeny" description="Spusťte sken webu pro automatickou detekci AI systémů." href="#pipeline-scan" cta="Spustit sken" />;
    }

    return (
        <div className="space-y-3">
            {findings.length > 0 && (
                <>
                    <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2">Nalezeno skenem webu ({findings.length})</h3>
                    {findings.map((f) => (
                        <div key={f.id} className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
                            <div className="flex items-start justify-between gap-4">
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-3 mb-2">
                                        <h4 className="font-semibold text-slate-200">{f.name}</h4>
                                    </div>
                                    <p className="text-sm text-slate-400 mb-2">{f.action_required}</p>
                                    <div className="flex items-center gap-4 text-xs text-slate-500">
                                        <span>Kategorie: {f.category}</span>
                                        <span>AI Act: {f.ai_act_article}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </>
            )}

            {questFindings.length > 0 && (
                <>
                    <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mt-6 mb-2">Deklarováno v dotazníku ({questFindings.length})</h3>
                    {questFindings.map((f, i) => (
                        <div key={`q-${i}`} className="rounded-xl border border-cyan-500/10 bg-cyan-500/[0.03] p-5">
                            <div className="flex items-start justify-between gap-4">
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-3 mb-2">
                                        <h4 className="font-semibold text-slate-200">{f.name}</h4>
                                        <span className="inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">Dotazník</span>
                                    </div>
                                    <p className="text-sm text-slate-400 mb-2">{f.action_required}</p>
                                    <div className="flex items-center gap-4 text-xs text-slate-500">
                                        <span>AI Act: {f.ai_act_article}</span>
                                        <span>Priorita: {f.priority}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </>
            )}
        </div>
    );
}

function TabDokumenty({ documents }: { documents: DashboardData["documents"] }) {
    if (documents.length === 0) {
        return <EmptyState title="Žádné dokumenty" description="Dokumenty se vygenerují po skenování, vyplnění dotazníku a objednání balíčku." href="/pricing" cta="Objednat balíček" />;
    }

    // Oddělení dodatků od běžných dokumentů
    const regularDocs = documents.filter((d) => !d.template_key?.startsWith("amendment"));
    const amendments = documents.filter((d) => d.template_key?.startsWith("amendment"));

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {regularDocs.map((doc) => (
                    <div key={doc.id} className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-5 flex items-center gap-4">
                        <div className="flex-shrink-0 h-12 w-12 rounded-xl bg-fuchsia-500/10 flex items-center justify-center">
                            <svg className="w-6 h-6 text-fuchsia-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                            </svg>
                        </div>
                        <div className="flex-1 min-w-0">
                            <h4 className="font-medium text-slate-200 text-sm">{TEMPLATE_NAMES[doc.template_key] || doc.name || doc.template_key}</h4>
                            <p className="text-xs text-slate-500 mt-0.5">{new Date(doc.created_at).toLocaleDateString("cs-CZ")}</p>
                        </div>
                        {doc.file_url && (() => {
                            const url = doc.file_url.toLowerCase();
                            const isPptx = url.includes('.pptx');
                            const isHtml = url.includes('.html');
                            const label = isPptx ? 'Stáhnout PPTX' : isHtml ? 'Stáhnout HTML' : 'Stáhnout PDF';
                            return (
                                <a href={doc.file_url} target="_blank" rel="noopener noreferrer" className="btn-secondary text-xs px-3 py-1.5 flex-shrink-0">{label}</a>
                            );
                        })()}
                    </div>
                ))}
            </div>

            {/* Dodatky (amendments) */}
            {amendments.length > 0 && (
                <div>
                    <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Dodatky ke compliance dokumentaci</h3>
                    <div className="space-y-3">
                        {amendments.map((doc) => {
                            const isApproved = doc.approval_status === "approved";
                            const isPending = doc.approval_status === "pending_review";
                            return (
                                <div key={doc.id} className={`rounded-xl border p-5 flex items-center gap-4 ${isPending ? "border-amber-500/20 bg-amber-500/[0.03]" : "border-cyan-500/20 bg-cyan-500/[0.03]"}`}>
                                    <div className={`flex-shrink-0 h-12 w-12 rounded-xl flex items-center justify-center ${isPending ? "bg-amber-500/10" : "bg-cyan-500/10"}`}>
                                        <svg className={`w-6 h-6 ${isPending ? "text-amber-400" : "text-cyan-400"}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                        </svg>
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2">
                                            <h4 className="font-medium text-slate-200 text-sm">{doc.name || "Dodatek"}</h4>
                                            <span className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium ${isPending ? "bg-amber-500/10 text-amber-400 border border-amber-500/20" : isApproved ? "bg-green-500/10 text-green-400 border border-green-500/20" : "bg-slate-500/10 text-slate-400 border border-slate-500/20"}`}>
                                                {isPending ? "Čeká na schválení" : isApproved ? "Schváleno" : "Zpracovává se"}
                                            </span>
                                        </div>
                                        <p className="text-xs text-slate-500 mt-0.5">{new Date(doc.created_at).toLocaleDateString("cs-CZ")}</p>
                                    </div>
                                    {isApproved && doc.file_url && (
                                        <a href={doc.file_url} target="_blank" rel="noopener noreferrer" className="btn-secondary text-xs px-3 py-1.5 flex-shrink-0">Stáhnout PDF</a>
                                    )}
                                    {isPending && (
                                        <span className="text-xs text-amber-400/70 flex-shrink-0">Probíhá kontrola kvality</span>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
}

function TabPlan({ findings, questFindings, resolvedIds, onResolvedChange }: { findings: DashboardData["findings"]; questFindings: DashboardData["questionnaire_findings"]; resolvedIds: string[]; onResolvedChange: () => void }) {
    const [toggling, setToggling] = useState<string | null>(null);
    const [optimisticIds, setOptimisticIds] = useState<Set<string>>(new Set(resolvedIds));
    useEffect(() => { setOptimisticIds(new Set(resolvedIds)); }, [resolvedIds]);
    const resolvedSet = optimisticIds;

    // Akční plán = POUZE body z dotazníku (questionnaire_findings)
    const items: { id: string; text: string; risk: string; article: string; resolved: boolean }[] = [];

    for (const f of questFindings) {
        const itemId = `q-${f.question_key}`;
        items.push({ id: itemId, text: f.action_required || f.name, risk: f.risk_level, article: f.ai_act_article, resolved: resolvedSet.has(itemId) });
    }

    if (items.length === 0) {
        return (
            <div className="glass text-center py-12">
                <div className="mx-auto mb-4 w-14 h-14 rounded-2xl bg-green-500/10 border border-green-500/20 flex items-center justify-center">
                    <svg className="w-7 h-7 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Žádné úkoly z dotazníku</h3>
                <p className="text-sm text-slate-400 max-w-sm mx-auto">
                    Na základě vašich odpovědí v dotazníku nejsou potřeba žádné další kroky.
                    Kompletní dokumentaci připravujeme v rámci vašeho balíčku.
                </p>
            </div>
        );
    }

    const riskOrder: Record<string, number> = { high: 0, medium: 1, limited: 2, low: 3, info: 4 };
    const sorted = [...items].sort((a, b) => (riskOrder[a.risk] ?? 5) - (riskOrder[b.risk] ?? 5));
    const total = sorted.length;
    const resolved = sorted.filter((i) => i.resolved).length;

    return (
        <div className="space-y-4">
            <div className="glass">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-slate-300">Postup</span>
                    <span className="text-sm text-slate-400">{resolved}/{total} splněno</span>
                </div>
                <div className="h-2 rounded-full bg-white/5 overflow-hidden">
                    <div className="h-full rounded-full bg-gradient-to-r from-fuchsia-500 to-cyan-500 transition-all duration-500" style={{ width: `${total > 0 ? (resolved / total) * 100 : 0}%` }} />
                </div>
            </div>

            {sorted.map((item) => {
                const handleToggle = async () => {
                    if (toggling) return;
                    const newResolved = !item.resolved;
                    setOptimisticIds(prev => {
                        const next = new Set(prev);
                        if (newResolved) next.add(item.id);
                        else next.delete(item.id);
                        return next;
                    });
                    setToggling(item.id);
                    try {
                        await toggleActionPlanItem(item.id, newResolved);
                    } catch (e) {
                        console.error("Toggle failed", e);
                        setOptimisticIds(prev => {
                            const next = new Set(prev);
                            if (newResolved) next.delete(item.id);
                            else next.add(item.id);
                            return next;
                        });
                    } finally {
                        setToggling(null);
                    }
                };
                return (
                    <div key={item.id} className={`flex items-start gap-4 rounded-xl border px-5 py-4 ${item.resolved ? "border-green-500/10 bg-green-500/[0.03]" : "border-white/[0.06] bg-white/[0.02]"}`}>
                        <button
                            type="button"
                            onClick={handleToggle}
                            disabled={toggling === item.id}
                            title={item.resolved ? "Zrušit splnění" : "Označit jako vyřešené"}
                            className={`flex-shrink-0 mt-0.5 h-5 w-5 rounded-md border ${item.resolved ? "border-green-500/30 bg-green-500/20" : "border-white/10 bg-white/5 hover:border-green-500/30 hover:bg-green-500/10"} flex items-center justify-center transition-colors cursor-pointer ${toggling === item.id ? "animate-pulse" : ""}`}
                        >
                            {item.resolved && (
                                <svg className="w-3 h-3 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                </svg>
                            )}
                        </button>
                        <div className="flex-1 min-w-0">
                            <p className={`text-sm font-medium ${item.resolved ? "text-slate-500 opacity-50" : "text-slate-200"}`}>{item.text}</p>
                            {item.article && (
                            <div className="flex items-center gap-3 mt-1 flex-wrap">
                                <span className="text-[10px] text-slate-500">{item.article}</span>
                            </div>
                            )}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

function TabSkeny({ scans }: { scans: DashboardData["scans"] }) {
    if (scans.length === 0) {
        return <EmptyState title="Žádné skeny" description="Spusťte první sken pro detekci AI systémů na vašem webu." href="#pipeline-scan" cta="Spustit sken" />;
    }

    return (
        <div className="space-y-3">
            {scans.map((scan, i) => {
                const effectiveStatus = scan.deep_scan_status === "done" ? "completed" : scan.status === "completed" || scan.status === "done" ? "completed" : scan.status === "running" || scan.deep_scan_status === "running" ? "running" : scan.status;
                return (
                    <div key={scan.id} className="flex items-center gap-4 rounded-xl border border-white/[0.06] bg-white/[0.02] px-5 py-4">
                        <div className="flex flex-col items-center gap-1">
                            <div className={`h-3 w-3 rounded-full ${effectiveStatus === "completed" ? "bg-green-500" : effectiveStatus === "running" ? "bg-amber-500 animate-pulse" : "bg-red-500"}`} />
                            {i < scans.length - 1 && <div className="w-px h-8 bg-white/[0.06]" />}
                        </div>
                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-3 flex-wrap">
                                <p className="text-sm font-medium text-slate-200 truncate">{scan.url}</p>
                                <span className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium ${effectiveStatus === "completed" ? "bg-green-500/10 text-green-400" : effectiveStatus === "running" ? "bg-amber-500/10 text-amber-400" : "bg-red-500/10 text-red-400"}`}>
                                    {effectiveStatus === "completed" ? "Dokončen" : effectiveStatus === "running" ? "Probíhá" : effectiveStatus}
                                </span>
                                {scan.deep_scan_status === "done" && (
                                    <span className="inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium bg-fuchsia-500/10 text-fuchsia-400">Deep scan</span>
                                )}
                            </div>
                            <div className="flex items-center gap-4 text-xs text-slate-500 mt-1 flex-wrap">
                                <span>{new Date(scan.created_at).toLocaleDateString("cs-CZ", { day: "numeric", month: "long", year: "numeric", hour: "2-digit", minute: "2-digit" })}</span>
                                <span>{scan.total_findings} nálezů</span>
                                {scan.scan_type !== "quick" && scan.geo_countries_scanned && scan.geo_countries_scanned.length > 0 && <span>{scan.geo_countries_scanned.length} {scan.geo_countries_scanned.length === 1 ? "země" : scan.geo_countries_scanned.length >= 2 && scan.geo_countries_scanned.length <= 4 ? "země" : "zemí"}</span>}
                            </div>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

function TabDotaznik({ answers, status, companyId, answeredCount, totalQuestions, isComplete }: { answers: Record<string, string>; status: string; companyId?: string; answeredCount: number; totalQuestions: number; isComplete: boolean }) {
    const entries = Object.entries(answers);
    const [showNavigator, setShowNavigator] = useState(false);

    if (entries.length === 0) {
        return <EmptyState title="Dotazník nebyl vyplněn" description="Vyplňte dotazník pro přesnější analýzu vašeho AI compliance stavu." href={companyId ? `/dotaznik?company_id=${companyId}` : "/dotaznik"} cta="Vyplnit dotazník" />;
    }

    const formatAnswer = (value: string) => {
        if (value === "yes") return "Ano";
        if (value === "no") return "Ne";
        if (value === "not_applicable") return "Neaplikováno";
        return value;
    };

    const companyKeys = ["company_legal_name", "company_ico", "company_address", "company_contact_email", "company_industry", "company_size", "company_annual_revenue", "eshop_platform"];
    const aiKeys = entries.filter(([k]) => k.startsWith("uses_") || k.startsWith("develops_") || k.startsWith("ai_")).map(([k]) => k);
    const complianceKeys = entries.filter(([k]) => k.startsWith("has_") || k.startsWith("can_") || k.startsWith("monitors_") || k.startsWith("tracks_") || k.startsWith("modifies_") || k === "transparency_page_implementation").map(([k]) => k);

    const sections = [
        { title: "Údaje o firmě", keys: companyKeys },
        { title: "Používané AI systémy", keys: aiKeys },
        { title: "Stav compliance", keys: complianceKeys },
    ];

    return (
        <div className="space-y-6">
            <div className="glass flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                    <h3 className="font-semibold">{isComplete ? "Vyplněný dotazník" : "Rozpracovaný dotazník"}</h3>
                    <p className="text-xs text-slate-500 mt-1">{answeredCount}/{totalQuestions} odpovědí{isComplete ? " — kompletní" : " — zbývá doplnit"}</p>
                </div>
                <div className="flex items-center gap-2">
                    {!isComplete && (
                        <a
                            href={companyId ? `/dotaznik?company_id=${companyId}` : "/dotaznik"}
                            className="btn-primary text-xs px-4 py-1.5"
                        >
                            Doplnit dotazník
                        </a>
                    )}
                    {isComplete && companyId && (
                        <button
                            onClick={() => setShowNavigator(true)}
                            className="btn-secondary text-xs px-4 py-1.5"
                        >
                            Upravit odpovědi
                        </button>
                    )}
                    <span className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${isComplete ? "bg-green-500/10 text-green-400" : "bg-amber-500/10 text-amber-400"}`}>
                        {isComplete ? "Dokončeno" : `${answeredCount}/${totalQuestions}`}
                    </span>
                </div>
            </div>

            {sections.map((section) => {
                const sectionEntries = entries.filter(([k]) => section.keys.includes(k));
                if (sectionEntries.length === 0) return null;
                return (
                    <div key={section.title} className="glass">
                        <h4 className="text-sm font-semibold text-slate-300 mb-3">{section.title}</h4>
                        <div className="space-y-2">
                            {sectionEntries.map(([key, value]) => (
                                <div key={key} className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-1 sm:gap-4 py-2 border-b border-white/[0.04] last:border-0">
                                    <span className="text-sm text-slate-400 flex-shrink-0">{QUESTION_LABELS[key] || key}</span>
                                    <span className={`text-sm sm:text-right ${value === "yes" ? "text-amber-400" : value === "no" ? "text-slate-500" : "text-slate-200"}`}>
                                        {key === "company_address" || key.includes("address") ? formatDisplayValue(key, formatAnswer(value)).split(", ").map((line, i) => (<span key={i} className="block">{line}</span>)) : formatAnswer(value)}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                );
            })}

            {/* Navigátor pro úpravu odpovědí */}
            {companyId && (
                <QuestionnaireNavigator
                    open={showNavigator}
                    onClose={() => setShowNavigator(false)}
                    companyId={companyId}
                    answers={answers}
                />
            )}
        </div>
    );
}

function EmptyState({ title, description, href, cta }: { title: string; description: string; href: string; cta: string }) {
    return (
        <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="h-16 w-16 rounded-2xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
            </div>
            <h3 className="font-semibold text-slate-300 mb-1">{title}</h3>
            <p className="text-sm text-slate-500 max-w-sm mb-6">{description}</p>
            <a href={href} className="btn-primary text-sm px-6 py-2.5">{cta}</a>
        </div>
    );
}

/* ═══════════════════════════════════════════
   PRICING DATA & TABLE
   ═══════════════════════════════════════════ */

const DASHBOARD_PLANS = [
    {
        key: "basic",
        name: "BASIC",
        price: "4 999",
        priceNote: "jednorázově",
        description: "Compliance Kit — dokumenty ke stažení",
        features: [
            "Sken webu + AI Act report",
            "AI Act Compliance Kit (14 dokumentů)",
            "Transparenční stránka (HTML)",
            "Registr AI systémů",
            "Interní AI politika firmy",
            "Školení — prezentace v PowerPointu",
            "Záznamový list o proškolení",
            "Plán řízení AI incidentů",
            "Transparentnost a lidský dohled",
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
            "Sken webu + AI Act report",
            "AI Act Compliance Kit (14 dokumentů)",
            "Transparenční stránka (HTML)",
            "Registr AI systémů",
            "Interní AI politika firmy",
            "Školení — prezentace v PowerPointu",
            "Záznamový list o proškolení",
            "Plán řízení AI incidentů",
            "Transparentnost a lidský dohled",
            "Tištěná dokumentace v profesionální vazbě do 14 dnů",
            "Implementace na váš web na klíč",
            "Nastavení transparenční stránky na webu",
            "Úprava chatbot oznámení",
            "Podpora po dobu 30 dní",
            "WordPress, Shoptet i custom",
            "Prioritní zpracování",
            "10 hodin on-line konzultací s compliance specialistou",
            "Metodická kontrola veškeré dokumentace",
            "★ 2 roky měsíčního monitoringu — automatický sken, propsání změn, hlášení a aktualizace dokumentů",
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
    { label: "Compliance Kit (14 dokumentů)", basic: true, pro: true, enterprise: true },
    { label: "Registr AI systémů", basic: true, pro: true, enterprise: true },
    { label: "Transparenční stránka (HTML)", basic: true, pro: true, enterprise: true },
    { label: "Texty oznámení pro AI nástroje", basic: true, pro: true, enterprise: true },
    { label: "Interní AI politika firmy", basic: true, pro: true, enterprise: true },
    { label: "Školení — prezentace v PowerPointu", basic: true, pro: true, enterprise: true },
    { label: "Záznamový list o proškolení", basic: true, pro: true, enterprise: true },
    { label: "Plán řízení AI incidentů", basic: true, pro: true, enterprise: true },
    { label: "Transparentnost a lidský dohled", basic: true, pro: true, enterprise: true },
    { label: "Tištěná dokumentace v profesionální vazbě (do 14 dnů)", basic: true, pro: true, enterprise: true },
    { label: "Implementace na váš web na klíč", basic: false, pro: true, enterprise: true },
    { label: "Nastavení transparenční stránky na webu", basic: false, pro: true, enterprise: true },
    { label: "Úprava cookie lišty a chatbot oznámení", basic: false, pro: true, enterprise: true },
    { label: "Podpora po dodání (30 dní)", basic: false, pro: true, enterprise: true },
    { label: "Prioritní zpracování", basic: false, pro: true, enterprise: true },
    { label: "10 hodin on-line konzultací se specialistou", basic: false, pro: false, enterprise: true },
    { label: "Metodická kontrola veškeré dokumentace", basic: false, pro: false, enterprise: true },
    { label: "2 roky měsíčního monitoringu — automatický sken, propsání změn, hlášení a aktualizace", basic: false, pro: false, enterprise: true },
    { label: "Dedikovaný specialista", basic: false, pro: false, enterprise: true },
    { label: "SLA 4h odezva v pracovní době", basic: false, pro: false, enterprise: true },
];

function PricingComparisonTable() {
    const { user } = useAuth();

    function handleCheckout(planKey: string) {
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

                            <div className="flex items-center gap-3 mb-3">
                                <div className={`p-2 rounded-xl ${plan.highlighted ? "bg-fuchsia-500/10 text-fuchsia-400" : "bg-white/5 text-slate-400"}`}>
                                    {plan.icon}
                                </div>
                                <h4 className="text-base font-bold tracking-wide">{plan.name}</h4>
                            </div>

                            <div className="mb-1">
                                <span className={`text-3xl font-extrabold ${plan.highlighted ? "neon-text" : "text-white"}`}>{plan.price}</span>
                                <span className="text-slate-500 ml-1 text-sm">Kč</span>
                            </div>
                            <p className="text-[11px] text-slate-500 mb-2">{plan.priceNote}</p>
                            <p className="text-xs text-slate-300 mb-4">{plan.description}</p>

                            <div className="h-px bg-gradient-to-r from-transparent via-white/10 to-transparent mb-4" />

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

                            <button
                                onClick={() => handleCheckout(plan.key)}
                                className={`block w-full text-center text-sm font-semibold py-2.5 rounded-xl transition-all ${plan.highlighted
                                    ? "bg-gradient-to-r from-fuchsia-600 to-fuchsia-500 text-white hover:from-fuchsia-500 hover:to-fuchsia-400 shadow-lg shadow-fuchsia-500/20"
                                    : "border border-white/10 bg-white/5 text-slate-300 hover:bg-white/10 hover:border-white/20"
                                    }`}
                            >
                                {plan.cta}
                            </button>
                        </div>
                    ))}
                </div>
            </div>

            {/* Comparison Table */}
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
                    <button onClick={() => handleCheckout("basic")} className="flex-1 text-center text-sm font-medium py-2.5 rounded-xl border border-white/10 bg-white/5 text-slate-300 hover:bg-white/10 transition-all">
                        Objednat BASIC
                    </button>
                    <button onClick={() => handleCheckout("pro")} className="flex-1 text-center text-sm font-medium py-2.5 rounded-xl bg-gradient-to-r from-fuchsia-600 to-fuchsia-500 text-white hover:from-fuchsia-500 hover:to-fuchsia-400 shadow-lg shadow-fuchsia-500/20 transition-all">
                        Objednat PRO ★
                    </button>
                    <button onClick={() => handleCheckout("enterprise")} className="flex-1 text-center text-sm font-medium py-2.5 rounded-xl border border-white/10 bg-white/5 text-slate-300 hover:bg-white/10 transition-all">
                        Objednat ENTERPRISE
                    </button>
                </div>
            </div>
        </div>
    );
}