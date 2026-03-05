"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useAuth } from "@/lib/auth-context";
import { getDashboardData, toggleActionPlanItem, triggerDeepScan, type DashboardData } from "@/lib/api";

type Tab = "prehled" | "findings" | "dokumenty" | "plan" | "skeny" | "dotaznik";

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
        key: "dotaznik",
        label: "Dotazník",
        icon: (
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
        ),
    },
];

// Format display values — clean || separators in addresses
function formatDisplayValue(key: string, value: string): string {
    if (key === "company_address" || key.includes("address") || key.includes("adresa")) {
        return value.replace(/\s*\|\|\s*/g, ", ");
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
                        <a href="/scan" className="btn-primary text-sm px-6 py-2">
                            Spustit první sken
                        </a>
                    </div>
                </div>
            </section>
        );
    }

    const companyName = data?.company?.name || user?.user_metadata?.company_name || "Vaše firma";

    // Process status from API
    const ps = data?.process_status || {
        scan_done: (data?.scans?.length || 0) > 0,
        questionnaire_done: data?.questionnaire_status === "dokončen",
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
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
                    <div>
                        <h1 className="text-2xl font-extrabold">Dashboard</h1>
                        <p className="text-sm text-slate-400 mt-1">
                            {companyName} — {data?.company?.url || ""}
                        </p>
                    </div>
                    <div className="flex gap-3">
                        <a href="/scan" className="btn-secondary text-sm px-4 py-2">Nový sken</a>
                        {(ps.questionnaire_done && ps.payment_done && ps.documents_done) ? (
                            <button
                                onClick={() => alert("Vaše odpovědi jsme již zpracovali a na základě Vašich odpovědí jsme Vám vygenerovali všechny potřebné dokumenty, které obdržíte e-mailem a do 14ti dní i poštou.\n\nV případě, že chcete změnit některé své odpovědi v dotazníku, protože se Vaše situace změnila, kontaktujte nás formou dotazníku na info@aishield.cz, kde nám popíšete Váš problém a my budeme Vaši žádost řešit individuálně.")}
                                className="btn-secondary text-sm px-4 py-2 opacity-70"
                            >
                                Dotazník ✓ Zpracován
                            </button>
                        ) : (
                            <a href={data?.company?.id ? `/dotaznik?company_id=${data.company.id}` : "/dotaznik"} className="btn-primary text-sm px-4 py-2">
                                {data?.questionnaire_status === "dokončen" ? "Dotazník ✓" : data?.questionnaire_status?.startsWith("rozpracován") ? "Pokračovat v dotazníku" : "Vyplnit dotazník"}
                            </a>
                        )}
                    </div>
                </div>

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
                        value={data?.questionnaire_status === "dokončen" ? "Hotovo" : data?.questionnaire_status?.startsWith("rozpracován") ? "Rozpracován" : "Čeká"}
                        sub={data?.questionnaire_status === "dokončen" ? "Vyplněn" : data?.questionnaire_status?.startsWith("rozpracován") ? "Pokračujte ve vyplňování" : "Vyplňte pro přesnější analýzu"}
                        color={data?.questionnaire_status === "dokončen" ? "text-green-400" : data?.questionnaire_status?.startsWith("rozpracován") ? "text-cyan-400" : "text-amber-400"}
                        href={(ps.questionnaire_done && ps.payment_done && ps.documents_done) ? undefined : data?.questionnaire_status === "dokončen" ? undefined : (data?.company?.id ? `/dotaznik?company_id=${data.company.id}` : "/dotaznik")}
                    />
                </div>

                {/* Desktop tabs */}
                <div className="hidden md:flex gap-1 overflow-x-auto border-b border-white/[0.06] mb-6 pb-px">
                    {TABS.map((tab) => (
                        <button
                            key={tab.key}
                            onClick={() => setActiveTab(tab.key)}
                            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-t-lg transition-colors whitespace-nowrap ${activeTab === tab.key
                                ? "text-fuchsia-400 border-b-2 border-fuchsia-400 bg-white/[0.03]"
                                : "text-slate-500 hover:text-slate-300"
                                }`}
                        >
                            {tab.icon}
                            {tab.label}
                        </button>
                    ))}
                </div>
                {/* Mobile accordion tabs */}
                <div className="md:hidden mb-6 space-y-1">
                    {TABS.map((tab) => (
                        <button
                            key={tab.key}
                            onClick={() => setActiveTab(tab.key)}
                            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-xl transition-all ${activeTab === tab.key
                                ? "text-fuchsia-400 bg-fuchsia-500/10 border border-fuchsia-500/20"
                                : "text-slate-400 bg-white/[0.02] border border-white/[0.06] hover:bg-white/[0.04]"
                                }`}
                        >
                            {tab.icon}
                            {tab.label}
                            <svg className={`w-4 h-4 ml-auto transition-transform ${activeTab === tab.key ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                        </button>
                    ))}
                </div>

                <div className="min-h-[400px]">
                    {activeTab === "prehled" && <TabPrehled data={data} onRefresh={fetchData} />}
                    {activeTab === "findings" && <TabFindings findings={data?.findings || []} questFindings={data?.questionnaire_findings || []} />}
                    {activeTab === "dokumenty" && <TabDokumenty documents={uniqueDocs} />}
                    {activeTab === "plan" && <TabPlan findings={data?.findings || []} questFindings={data?.questionnaire_findings || []} resolvedIds={data?.action_plan_resolved || []} onResolvedChange={fetchData} />}
                    {activeTab === "skeny" && <TabSkeny scans={data?.scans || []} />}
                    {activeTab === "dotaznik" && <TabDotaznik answers={data?.questionnaire_answers || {}} status={data?.questionnaire_status || ""} />}
                </div>
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
            <p className={`text-3xl font-extrabold mt-1 ${color}`}>{value}</p>
            <p className="text-xs text-slate-500 mt-1">{sub}</p>
        </div>
    );
    if (href) return <a href={href}>{card}</a>;
    return card;
}

function TabPrehled({ data, onRefresh }: { data: DashboardData | null; onRefresh: () => void }) {
    const [deepScanLoading, setDeepScanLoading] = useState(false);
    const [deepScanError, setDeepScanError] = useState<string | null>(null);

    const ps = data?.process_status;
    const hasPaidOrder = ps?.payment_done ?? data?.orders.some((o) => o.status === "PAID") ?? false;
    const hasScans = ps?.scan_done ?? (data?.scans.length || 0) > 0;
    const hasQuest = ps?.questionnaire_done ?? data?.questionnaire_status === "dokončen";
    const questStarted = !hasQuest && (data?.questionnaire_status?.startsWith("rozpracován") ?? false);
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
        } catch (e: any) {
            setDeepScanError(e.message || "Nepodařilo se spustit");
        } finally {
            setDeepScanLoading(false);
        }
    };

    const steps = [
        {
            done: hasScans,
            label: "Sken webu",
            desc: "Automatická detekce AI systémů na vašem webu",
            detail: null as string | null,
            href: "/scan" as string | null,
            cta: "Spustit sken",
        },
        {
            done: deepDone || deepRunning || (hasQuest && hasPaidOrder),
            optional: true,
            label: deepRunning && !deepDone ? "24h test ⏳" : "24h test",
            desc: deepDone
                ? "Hloubkový scan ze 8 zemí a 6 kontinentů byl úspěšně dokončen"
                : deepRunning
                    ? "Hloubkový scan probíhá na pozadí ze 7 zemí — mezitím pokračujte dotazníkem"
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
                : questStarted
                    ? `Rozpracovaný dotazník — ${data?.questionnaire_status?.match(/\d+\/\d+/)?.[0] || ""} odpovědí`
                    : "Upřesní analýzu o interní AI nástroje (ChatGPT, Copilot…)",
            detail: hasQuest || questStarted ? null : "EU AI Act se netýká jen toho, co je vidět na webu. Regulace zahrnuje i interní AI systémy — nástroje pro HR, účetnictví, rozhodování, generování obsahu nebo komunikaci se zaměstnanci. Automatický sken odhalí jen veřejně viditelné nástroje. Dotazník pokrývá celou AI politiku firmy, včetně toho, co zákazník nikdy neuvidí.",
            href: (hasScans || questStarted) && !hasQuest ? `/dotaznik?company_id=${data?.company?.id || ''}` : null,
            cta: !hasScans ? "🔒 Nejprve skenujte web" : !hasQuest ? (questStarted ? "Pokračovat v dotazníku" : "Vyplnit dotazník") : qUnknowns.length > 0 ? "Doplnit odpovědi" : "✓ Kompletní",
        },
        {
            done: hasOrder,
            label: "Objednávka",
            desc: hasOrder ? "Objednávka byla přijata" : "Odemkněte compliance dokumenty a školení",
            detail: null,
            href: hasOrder ? null : "#pricing",
            cta: hasOrder ? "✓ Objednáno" : "Vybrat balíček",
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
            done: isProcessingDocs,
            label: "Tvorba dokumentace",
            desc: isProcessingDocs ? "Pracujeme na vaší dokumentaci — elektronické PDF do 7 pracovních dnů" : hasPaidOrder ? "Připravujeme vaše dokumenty" : "Po zaplacení začneme s tvorbou",
            detail: null,
            href: null,
            cta: isProcessingDocs ? "Zpracováváme" : "",
        },
        {
            done: hasDocs,
            label: "Dodání",
            desc: hasDocs ? "Dokumenty jsou připraveny ke stažení — tištěnou verzi doručíme do 14 dnů" : "Až 12 dokumentů v PDF + tištěná verze v profesionální vazbě",
            detail: null,
            href: null,
            cta: hasDocs ? "Viz tab Dokumenty" : "",
        },
    ];

    // Smart step index: skip optional steps (24h test) when later steps are done
    const rawStepIndex = steps.findIndex((s) => !s.done);
    const currentStepIndex = (rawStepIndex === 1 && steps[2]?.done) ? steps.findIndex((s, i) => i > 1 && !s.done) : rawStepIndex;
    const currentStep = currentStepIndex >= 0 ? steps[currentStepIndex] : null;
    const progressTarget = currentStepIndex >= 0 ? currentStepIndex : steps.length - 1;
    const lineWidthPercent = progressTarget <= 0 ? 0 : (progressTarget / (steps.length - 1)) * ((steps.length - 1) / steps.length * 100);

    const isProcessing = hasPaidOrder && !hasDocs && hasScans;
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
                                            🇨🇿 🇬🇧 🇺🇸 🇧🇷 🇯🇵 🇿🇦 🇦🇺 🇩🇪 — 7 zemí, 6 kontinentů, desktop i mobil
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
                                        {!hasQuest && (
                                            <a
                                                href={`/dotaznik?company_id=${data?.company?.id || ''}`}
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

                {/* Completed steps summary */}
                {steps.some(s => s.done) && (
                    <div className="mt-4 rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
                        <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Stav procesu</p>
                        <div className="space-y-1">
                            {steps.map((step, i) => (
                                <div key={i} className="flex items-center gap-2 text-xs">
                                    {step.done ? (
                                        <span className="text-green-400">✓</span>
                                    ) : (step as any).optional && !step.done ? (
                                        <span className="text-slate-600">—</span>
                                    ) : (
                                        <span className="text-slate-600">○</span>
                                    )}
                                    <span className={step.done ? "text-green-400/80" : "text-slate-600"}>{step.label}</span>
                                    {step.done && <span className="text-slate-600 ml-auto">{step.desc?.split("—")[0]?.trim()}</span>}
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* 24h deep scan running banner */}
            {deepRunning && !deepDone && currentStepIndex !== 1 && (
                <div className="glass border-cyan-500/20">
                    <div className="flex items-start gap-4">
                        <div className="flex-shrink-0 h-10 w-10 rounded-full bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center">
                            <span className="text-lg animate-pulse">⏳</span>
                        </div>
                        <div>
                            <h4 className="font-semibold text-cyan-300 text-sm">24h hloubkový test probíhá</h4>
                            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                                Testujeme váš web ze <strong className="text-slate-300">8 zemí a 6 kontinentů</strong> (desktop i mobil).
                                Výsledky budou přibližně za <strong className="text-slate-300">24 hodin</strong> — pošleme vám e-mail.
                            </p>
                            <div className="flex items-center gap-2 mt-2">
                                <span className="text-[10px] text-slate-500">🇨🇿 🇬🇧 🇺🇸 🇧🇷 🇯🇵 🇿🇦 🇦🇺 🇩🇪</span>
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

            {/* Pricing */}
            <div id="pricing">
                <PricingComparisonTable />
            </div>
        </div>
    );
}

function TabFindings({ findings, questFindings }: { findings: DashboardData["findings"]; questFindings: DashboardData["questionnaire_findings"] }) {
    if (findings.length === 0 && questFindings.length === 0) {
        return <EmptyState title="Žádné AI systémy nalezeny" description="Spusťte sken webu pro automatickou detekci AI systémů." href="/scan" cta="Spustit sken" />;
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
                                        <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium border ${RISK_COLORS[f.risk_level] || RISK_COLORS.low}`}>
                                            {f.risk_level === "high" ? "Vysoké" : f.risk_level === "medium" ? "Střední" : "Nízké"} riziko
                                        </span>
                                    </div>
                                    <p className="text-sm text-slate-400 mb-2">{f.action_required}</p>
                                    <div className="flex items-center gap-4 text-xs text-slate-500">
                                        <span>Kategorie: {f.category}</span>
                                        <span>AI Act: {f.ai_act_article}</span>
                                        {f.confirmed_by_client && (
                                            <span className={f.confirmed_by_client === "false_positive" ? "text-slate-500" : "text-amber-400"}>
                                                {f.confirmed_by_client === "false_positive" ? "Falešný poplach" : "Potvrzeno"}
                                            </span>
                                        )}
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
                                        <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium border ${RISK_COLORS[f.risk_level] || RISK_COLORS.low}`}>
                                            {f.risk_level === "high" ? "Vysoké" : f.risk_level === "medium" ? "Střední" : "Nízké"} riziko
                                        </span>
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

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {documents.map((doc) => (
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
    );
}

function TabPlan({ findings, questFindings, resolvedIds, onResolvedChange }: { findings: DashboardData["findings"]; questFindings: DashboardData["questionnaire_findings"]; resolvedIds: string[]; onResolvedChange: () => void }) {
    const [toggling, setToggling] = useState<string | null>(null);
    const [optimisticIds, setOptimisticIds] = useState<Set<string>>(new Set(resolvedIds));
    // Synchronizace s props, pokud se změní ze serveru
    useEffect(() => { setOptimisticIds(new Set(resolvedIds)); }, [resolvedIds]);
    const resolvedSet = optimisticIds;
    const allItems: { id: string; text: string; risk: string; article: string; source: string; tag: "done" | "client" | "lawyer" | "it"; resolved: boolean }[] = [];

    const standardItems: { text: string; tag: "done" | "client" | "lawyer" | "it"; risk: string; article: string }[] = [
        { text: "Vytvořit interní registr AI systémů (čl. 49 — evidence)", tag: "done", risk: "info", article: "čl. 49" },
        { text: "Proškolit zaměstnance — AI gramotnost dle čl. 4 AI Act", tag: "done", risk: "info", article: "čl. 4" },
        { text: "Připravit DPIA pro AI systémy zpracovávající osobní údaje", tag: "done", risk: "info", article: "GDPR" },
        { text: "Naplánovat pravidelný re-sken webu (monitoring)", tag: "done", risk: "info", article: "čl. 9" },
        { text: "Jmenovat odpovědnou osobu za AI compliance (čl. 14)", tag: "client", risk: "info", article: "čl. 14" },
        { text: "Zavést proces pro zavedení nového AI nástroje", tag: "client", risk: "info", article: "čl. 9" },
        { text: "Zkontrolovat smlouvy s dodavateli AI (DPA, opt-out)", tag: "lawyer", risk: "info", article: "GDPR" },
        { text: "Nastavit logování AI výstupů s retencí min. 6 měsíců", tag: "it", risk: "info", article: "čl. 12" },
    ];

    const hasRealFindings = findings.length > 0 || questFindings.length > 0;

    for (const item of standardItems) {
        // Generické úkoly (client/lawyer/it) zobrazit jen když existují reálné nálezy
        if (!hasRealFindings && item.tag !== "done") continue;
        const itemId = `std-${item.text.slice(0, 20)}`;
        allItems.push({ id: itemId, text: item.text, risk: item.risk, article: item.article, source: "standard", tag: item.tag, resolved: item.tag === "done" || resolvedSet.has(itemId) });
    }

    for (const f of findings) {
        const isResolved = f.confirmed_by_client === "false_positive" || f.status === "resolved" || resolvedSet.has(f.id);
        allItems.push({ id: f.id, text: f.action_required || f.name, risk: f.risk_level, article: f.ai_act_article, source: "scan", tag: "client", resolved: isResolved });
    }

    for (const f of questFindings) {
        const itemId = `q-${f.question_key}`;
        allItems.push({ id: itemId, text: f.action_required || f.name, risk: f.risk_level, article: f.ai_act_article, source: "questionnaire", tag: "client", resolved: resolvedSet.has(itemId) });
    }

    if (allItems.length === 0) {
        return <EmptyState title="Akční plán je prázdný" description="Nejdříve proveďte sken webu — akční plán se vygeneruje z nálezů." href="/scan" cta="Spustit sken" />;
    }

    const riskOrder: Record<string, number> = { high: 0, medium: 1, limited: 2, low: 3, info: 4 };
    const sorted = [...allItems].sort((a, b) => {
        return (riskOrder[a.risk] ?? 5) - (riskOrder[b.risk] ?? 5);
    });

    const total = sorted.length;
    const resolved = sorted.filter((i) => i.resolved).length;

    const TAG_STYLES: Record<string, { bg: string; text: string; label: string }> = {
        done: { bg: "bg-green-500/10", text: "text-green-400", label: "✅ Součást balíčku" },
        client: { bg: "bg-amber-500/10", text: "text-amber-400", label: "✏️ Vaše akce" },
        lawyer: { bg: "bg-red-500/10", text: "text-red-400", label: "⚖️ Právník" },
        it: { bg: "bg-blue-500/10", text: "text-blue-400", label: "💻 IT oddělení" },
    };

    return (
        <div className="space-y-4">
            <div className="glass flex flex-wrap gap-3 text-xs">
                {Object.entries(TAG_STYLES).map(([key, style]) => (
                    <span key={key} className={`inline-flex items-center rounded-full px-2.5 py-1 ${style.bg} ${style.text}`}>{style.label}</span>
                ))}
            </div>

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
                const tagStyle = TAG_STYLES[item.tag] || TAG_STYLES.client;
                const canToggle = item.tag !== "done";
                const handleToggle = async () => {
                    if (!canToggle || toggling) return;
                    const newResolved = !item.resolved;
                    // Optimistický update — okamžitá odezva UI
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
                        // Revert optimistického updatu
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
                            disabled={!canToggle || toggling === item.id}
                            title={canToggle ? (item.resolved ? "Zrušit splnění" : "Máme splněno") : "Součást balíčku"}
                            className={`flex-shrink-0 mt-0.5 h-5 w-5 rounded-md border ${item.resolved ? "border-green-500/30 bg-green-500/20" : "border-white/10 bg-white/5 hover:border-green-500/30 hover:bg-green-500/10"} flex items-center justify-center transition-colors ${canToggle ? "cursor-pointer" : "cursor-default"} ${toggling === item.id ? "animate-pulse" : ""}`}
                        >
                            {item.resolved && (
                                <svg className="w-3 h-3 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                </svg>
                            )}
                        </button>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-slate-200">{item.text}</p>
                            <div className="flex items-center gap-3 mt-1 flex-wrap">
                                <span className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium ${tagStyle.bg} ${tagStyle.text}`}>{tagStyle.label}</span>
                                {canToggle && !item.resolved && (
                                    <button
                                        type="button"
                                        onClick={handleToggle}
                                        disabled={toggling === item.id}
                                        className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium bg-green-500/10 text-green-400 border border-green-500/20 hover:bg-green-500/20 transition-colors cursor-pointer"
                                    >
                                        <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                                        Máme splněno
                                    </button>
                                )}
                                {item.risk !== "info" && (
                                    <span className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-medium border ${RISK_COLORS[item.risk] || RISK_COLORS.low}`}>
                                        {item.risk === "high" ? "Vysoká" : item.risk === "medium" ? "Střední" : "Nízká"} priorita
                                    </span>
                                )}
                                <span className="text-[10px] text-slate-500">{item.article}</span>
                                {item.source === "scan" && <span className="text-[10px] text-slate-600">Ze skenu</span>}
                                {item.source === "questionnaire" && <span className="text-[10px] text-cyan-600">Z dotazníku</span>}
                            </div>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

function TabSkeny({ scans }: { scans: DashboardData["scans"] }) {
    if (scans.length === 0) {
        return <EmptyState title="Žádné skeny" description="Spusťte první sken pro detekci AI systémů na vašem webu." href="/scan" cta="Spustit sken" />;
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
                                {scan.geo_countries_scanned && scan.geo_countries_scanned.length > 0 && <span>{scan.geo_countries_scanned.length} zemí</span>}
                            </div>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

function TabDotaznik({ answers, status }: { answers: Record<string, string>; status: string }) {
    const entries = Object.entries(answers);

    if (entries.length === 0) {
        return <EmptyState title="Dotazník nebyl vyplněn" description="Vyplňte dotazník pro přesnější analýzu vašeho AI compliance stavu." href="/dotaznik" cta="Vyplnit dotazník" />;
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
            <div className="glass flex items-center justify-between">
                <div>
                    <h3 className="font-semibold">Vyplněný dotazník</h3>
                    <p className="text-xs text-slate-500 mt-1">{entries.length} odpovědí — pouze k nahlédnutí</p>
                </div>
                <span className="inline-flex rounded-full px-3 py-1 text-xs font-medium bg-green-500/10 text-green-400">
                    {status === "dokončen" ? "Dokončeno" : status}
                </span>
            </div>

            {sections.map((section) => {
                const sectionEntries = entries.filter(([k]) => section.keys.includes(k));
                if (sectionEntries.length === 0) return null;
                return (
                    <div key={section.title} className="glass">
                        <h4 className="text-sm font-semibold text-slate-300 mb-3">{section.title}</h4>
                        <div className="space-y-2">
                            {sectionEntries.map(([key, value]) => (
                                <div key={key} className="flex items-start justify-between gap-4 py-2 border-b border-white/[0.04] last:border-0">
                                    <span className="text-sm text-slate-400 flex-shrink-0">{QUESTION_LABELS[key] || key}</span>
                                    <span className={`text-sm text-right ${value === "yes" ? "text-amber-400" : value === "no" ? "text-slate-500" : "text-slate-200"}`}>
                                        {formatAnswer(value)}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                );
            })}
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
            "AI Act Compliance Kit (až 12 dokumentů dle rizika)",
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
            "AI Act Compliance Kit (až 12 dokumentů dle rizika)",
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
    { label: "Compliance Kit (až 12 dokumentů dle rizika)", basic: true, pro: true, enterprise: true },
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