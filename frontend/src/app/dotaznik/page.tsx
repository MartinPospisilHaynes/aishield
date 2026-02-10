"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ═══════════════════════════════════════════
   TYPES
   ═══════════════════════════════════════════ */

interface FollowupField {
    key: string;
    label: string;
    type: "text" | "select" | "multi_select";
    options?: string[];
}

interface Question {
    key: string;
    text: string;
    type: string;               // "yes_no_unknown" | "single_select"
    options?: string[];          // for single_select (industry)
    help_text?: string;
    followup?: { condition: string; fields: FollowupField[] };
    risk_hint: string;
    ai_act_article: string | null;
}

interface Section {
    id: string;
    title: string;
    description: string;
    questions: Question[];
}

interface Answer {
    question_key: string;
    section: string;
    answer: string;
    details: Record<string, string | string[]>;
    tool_name: string;
}

interface Recommendation {
    question_key: string;
    tool_name: string;
    risk_level: string;
    ai_act_article: string;
    recommendation: string;
    priority: string;
}

interface AnalysisResult {
    total_answers: number;
    ai_systems_declared: number;
    risk_breakdown: Record<string, number>;
    recommendations: Recommendation[];
}

/* ═══════════════════════════════════════════
   INDUSTRY ICONS (emoji map)
   ═══════════════════════════════════════════ */

const INDUSTRY_ICONS: Record<string, string> = {
    "E-shop / Online obchod": "🛒",
    "Účetnictví / Finance": "💰",
    "Zdravotnictví": "🏥",
    "Vzdělávání / Školství": "🎓",
    "Výroba / Průmysl": "🏭",
    "IT / Technologie": "💻",
    "Stavebnictví": "🏗️",
    "Doprava / Logistika": "🚛",
    "Restaurace / Gastronomie": "🍽️",
    "Kadeřnictví / Kosmetika": "💇",
    "Právní služby": "⚖️",
    "Nemovitosti / Reality": "🏠",
    "Zemědělství": "🌾",
    "Jiné": "📦",
};

/* ═══════════════════════════════════════════
   INNER COMPONENT (uses useSearchParams)
   ═══════════════════════════════════════════ */

function QuestionnaireInner() {
    const searchParams = useSearchParams();
    const router = useRouter();

    /* ── State ── */
    const [sections, setSections] = useState<Section[]>([]);
    const [currentQuestion, setCurrentQuestion] = useState(-1); // -1=welcome, 0..N=flat index
    const [answers, setAnswers] = useState<Record<string, Answer>>({});
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [result, setResult] = useState<AnalysisResult | null>(null);
    const [companyId, setCompanyId] = useState<string | null>(null);
    const [scanId, setScanId] = useState<string | null>(null);
    const [direction, setDirection] = useState<"forward" | "back">("forward");
    const [sectionFlash, setSectionFlash] = useState<string | null>(null);
    const [multiSelections, setMultiSelections] = useState<Record<string, string[]>>({});

    /* ── Flat question list ── */
    const allQuestions: (Question & { _section: string })[] = sections.flatMap((s) =>
        s.questions.map((q) => ({ ...q, _section: s.id }))
    );
    const totalQuestions = allQuestions.length;

    /* ── Fetch structure ── */
    useEffect(() => {
        fetch(`${API_URL}/api/questionnaire/structure`)
            .then((r) => r.json())
            .then((data) => {
                setSections(data.sections || []);
                const init: Record<string, Answer> = {};
                for (const s of data.sections || []) {
                    for (const q of s.questions) {
                        init[q.key] = {
                            question_key: q.key,
                            section: s.id,
                            answer: "",
                            details: {},
                            tool_name: "",
                        };
                    }
                }
                setAnswers(init);
                setLoading(false);
            })
            .catch(() => setLoading(false));
    }, []);

    /* ── URL params ── */
    useEffect(() => {
        const cid = searchParams.get("company_id");
        const sid = searchParams.get("scan_id");
        if (cid) setCompanyId(cid);
        if (sid) setScanId(sid);
    }, [searchParams]);

    /* ── Navigation helpers ── */
    const goNext = useCallback(() => {
        setDirection("forward");
        // Check section transition
        if (currentQuestion >= 0 && currentQuestion < totalQuestions - 1) {
            const cur = allQuestions[currentQuestion];
            const nxt = allQuestions[currentQuestion + 1];
            if (cur._section !== nxt._section) {
                const sec = sections.find((s) => s.id === nxt._section);
                if (sec) {
                    setSectionFlash(sec.title);
                    setTimeout(() => {
                        setSectionFlash(null);
                        setCurrentQuestion((p) => p + 1);
                    }, 800);
                    return;
                }
            }
        }
        setCurrentQuestion((p) => p + 1);
    }, [currentQuestion, totalQuestions, allQuestions, sections]);

    const goBack = useCallback(() => {
        setDirection("back");
        setCurrentQuestion((p) => Math.max(-1, p - 1));
    }, []);

    /* ── Set answer ── */
    const setAnswer = useCallback(
        (key: string, value: string) => {
            setAnswers((prev) => ({
                ...prev,
                [key]: { ...prev[key], answer: value },
            }));
        },
        []
    );

    /* ── Set detail (single select / text) ── */
    const setDetail = useCallback((qKey: string, fKey: string, value: string) => {
        setAnswers((prev) => ({
            ...prev,
            [qKey]: {
                ...prev[qKey],
                details: { ...prev[qKey].details, [fKey]: value },
                tool_name:
                    fKey.includes("tool_name") || fKey.endsWith("_tool")
                        ? value
                        : prev[qKey].tool_name,
            },
        }));
    }, []);

    /* ── Toggle multi-select ── */
    const toggleMulti = useCallback((qKey: string, fKey: string, value: string) => {
        setMultiSelections((prev) => {
            const mkey = `${qKey}__${fKey}`;
            const current = prev[mkey] || [];
            const next = current.includes(value)
                ? current.filter((v) => v !== value)
                : [...current, value];
            // Also update answers details
            setAnswers((ap) => ({
                ...ap,
                [qKey]: {
                    ...ap[qKey],
                    details: { ...ap[qKey].details, [fKey]: next.join(", ") },
                },
            }));
            return { ...prev, [mkey]: next };
        });
    }, []);

    /* ── Submit ── */
    const handleSubmit = async () => {
        setSubmitting(true);
        const list = Object.values(answers)
            .filter((a) => a.answer !== "")
            .map((a) => ({
                question_key: a.question_key,
                section: a.section,
                answer: a.answer,
                details: Object.keys(a.details).length > 0 ? a.details : null,
                tool_name: a.tool_name || null,
            }));
        try {
            const res = await fetch(`${API_URL}/api/questionnaire/submit`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    company_id: companyId || "anonymous",
                    scan_id: scanId,
                    answers: list,
                }),
            });
            if (!res.ok) throw new Error("Chyba serveru");
            const data = await res.json();
            setResult(data.analysis);
            setCurrentQuestion(totalQuestions + 1); // results screen
        } catch {
            // still show results screen with null
            setCurrentQuestion(totalQuestions + 1);
        } finally {
            setSubmitting(false);
        }
    };

    /* ── Keyboard handler ── */
    useEffect(() => {
        const handler = (e: KeyboardEvent) => {
            if (currentQuestion < 0 || currentQuestion > totalQuestions) return;
            if (currentQuestion < totalQuestions) {
                const q = allQuestions[currentQuestion];
                if (q.type === "yes_no_unknown") {
                    if (e.key === "1") { setAnswer(q.key, "yes"); setTimeout(goNext, 300); }
                    if (e.key === "2") { setAnswer(q.key, "no"); setTimeout(goNext, 300); }
                    if (e.key === "3") { setAnswer(q.key, "unknown"); setTimeout(goNext, 300); }
                }
            }
            if (e.key === "Enter") goNext();
        };
        window.addEventListener("keydown", handler);
        return () => window.removeEventListener("keydown", handler);
    }, [currentQuestion, totalQuestions, allQuestions, goNext, setAnswer]);

    /* ── Progress ── */
    const progressPct =
        currentQuestion <= 0
            ? 0
            : Math.min(100, Math.round((currentQuestion / totalQuestions) * 100));

    /* ═══════════════════════════════════════════
       RENDERS
       ═══════════════════════════════════════════ */

    /* ── Loading ── */
    if (loading) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center">
                <div className="text-center">
                    <div className="w-12 h-12 border-4 border-fuchsia-500/30 border-t-fuchsia-500 rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-slate-400">Připravuji dotazník…</p>
                </div>
            </div>
        );
    }

    /* ── Section flash overlay ── */
    if (sectionFlash) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center">
                <div className="text-center animate-fade-in">
                    <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-fuchsia-600 to-purple-600 flex items-center justify-center mx-auto mb-6">
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" /></svg>
                    </div>
                    <h2 className="text-3xl font-bold text-white">{sectionFlash}</h2>
                </div>
            </div>
        );
    }

    /* ── Results screen ── */
    if (currentQuestion > totalQuestions) {
        const high = result?.risk_breakdown?.high || 0;
        const limited = result?.risk_breakdown?.limited || 0;
        const minimal = result?.risk_breakdown?.minimal || 0;

        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
                <div className="w-full max-w-xl animate-fade-in">
                    {submitting ? (
                        <div className="text-center">
                            <div className="w-16 h-16 border-4 border-fuchsia-500/30 border-t-fuchsia-500 rounded-full animate-spin mx-auto mb-6" />
                            <h2 className="text-2xl font-bold text-white mb-2">Hotovo! Analyzujeme vaše odpovědi…</h2>
                            <p className="text-slate-400">Chvilku strpení.</p>
                        </div>
                    ) : (
                        <>
                            <div className="text-center mb-8">
                                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center mx-auto mb-6">
                                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3"><path d="M20 6L9 17l-5-5" /></svg>
                                </div>
                                <h2 className="text-3xl font-bold text-white mb-2">Analýza dokončena</h2>
                                <p className="text-slate-400">Zde je váš rizikový profil</p>
                            </div>

                            {/* Risk summary cards */}
                            <div className="grid grid-cols-3 gap-3 mb-8">
                                {[
                                    { n: high, label: "Vysoce rizikových", color: "text-red-400", bg: "bg-red-500/10 border-red-500/20" },
                                    { n: limited, label: "Omezeného rizika", color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" },
                                    { n: minimal, label: "Minimální riziko", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
                                ].map((item, i) => (
                                    <div key={i} className={`rounded-2xl border p-4 text-center backdrop-blur-xl ${item.bg}`}>
                                        <div className={`text-3xl font-black ${item.color}`}>{item.n}</div>
                                        <div className="text-slate-400 text-xs mt-1">{item.label}</div>
                                    </div>
                                ))}
                            </div>

                            {/* Recommendations preview */}
                            {result && result.recommendations.length > 0 && (
                                <div className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.08] rounded-2xl p-6 mb-6">
                                    <h3 className="text-white font-bold mb-4">Top doporučení</h3>
                                    <div className="space-y-3">
                                        {result.recommendations.slice(0, 3).map((rec, i) => (
                                            <div key={i} className="flex items-start gap-3">
                                                <span className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${rec.risk_level === "high" ? "bg-red-400" : rec.risk_level === "limited" ? "bg-amber-400" : "bg-emerald-400"
                                                    }`} />
                                                <p className="text-slate-300 text-sm leading-relaxed">{rec.recommendation}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* CTAs */}
                            <div className="space-y-3">
                                <button
                                    onClick={() => router.push("/dashboard")}
                                    className="w-full py-4 rounded-xl bg-gradient-to-r from-fuchsia-600 to-purple-600 text-white font-semibold text-lg transition-all hover:shadow-lg hover:shadow-fuchsia-500/25 active:scale-[0.98]"
                                >
                                    Zobrazit výsledky v dashboardu
                                </button>
                                <button
                                    onClick={() => router.push("/pricing")}
                                    className="w-full py-4 rounded-xl bg-white/[0.06] border border-white/[0.1] text-slate-300 font-medium transition-all hover:bg-white/[0.1]"
                                >
                                    Objednat compliance balíček
                                </button>
                            </div>
                        </>
                    )}
                </div>
            </div>
        );
    }

    /* ── Welcome screen (currentQuestion === -1) ── */
    if (currentQuestion === -1) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
                {/* Decorative blobs */}
                <div className="fixed top-[-200px] right-[-100px] w-[500px] h-[500px] bg-fuchsia-600/15 rounded-full blur-[120px] pointer-events-none" />
                <div className="fixed bottom-[-200px] left-[-100px] w-[500px] h-[500px] bg-cyan-500/10 rounded-full blur-[120px] pointer-events-none" />

                <div className="relative z-10 w-full max-w-lg text-center animate-fade-in">
                    <h1 className="text-3xl sm:text-4xl font-black text-white leading-tight mb-3">
                        Pojďme zjistit,{" "}
                        <span className="bg-gradient-to-r from-fuchsia-400 to-cyan-400 bg-clip-text text-transparent">
                            jak na tom jste
                        </span>
                    </h1>
                    <p className="text-slate-400 text-lg mb-10">
                        {totalQuestions} krátkých otázek. Stačí klikat. Hotovo za 5 minut.
                    </p>

                    {/* Feature cards */}
                    <div className="grid grid-cols-3 gap-3 mb-10">
                        {[
                            { icon: "🖱️", label: "Jen klikáte" },
                            { icon: "🔒", label: "Data v bezpečí" },
                            { icon: "⏱️", label: "5 minut" },
                        ].map((f, i) => (
                            <div
                                key={i}
                                className="bg-white/[0.04] backdrop-blur-xl border border-white/[0.08] rounded-2xl p-4 sm:p-5"
                            >
                                <div className="text-2xl mb-2">{f.icon}</div>
                                <div className="text-slate-300 text-sm font-medium">{f.label}</div>
                            </div>
                        ))}
                    </div>

                    <button
                        onClick={() => { setDirection("forward"); setCurrentQuestion(0); }}
                        className="w-full sm:w-auto px-12 py-4 rounded-xl bg-gradient-to-r from-fuchsia-600 to-purple-600 text-white font-semibold text-lg transition-all hover:shadow-lg hover:shadow-fuchsia-500/25 active:scale-[0.98]"
                    >
                        Začít →
                    </button>
                </div>
            </div>
        );
    }

    /* ═══════════════════════════════════════════
       QUESTION SCREENS (0..N)
       ═══════════════════════════════════════════ */

    const q = allQuestions[currentQuestion];
    if (!q) return null;

    const ans = answers[q.key];
    const isLast = currentQuestion === totalQuestions - 1;
    const showFollowup = ans?.answer === "yes" && q.followup;

    /* ── Industry select (first question, type single_select) ── */
    if (q.type === "single_select" && q.options) {
        return (
            <div className="min-h-screen bg-slate-950 flex flex-col">
                {/* Progress bar */}
                <ProgressBarUI current={currentQuestion} total={totalQuestions} />

                <div className="flex-1 flex items-center justify-center p-4 pt-16">
                    <div className={`w-full max-w-2xl animate-slide-${direction === "forward" ? "in" : "in-back"}`}>
                        <h2 className="text-2xl sm:text-3xl font-bold text-white mb-8 text-center">
                            {q.text}
                        </h2>

                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                            {q.options.map((opt) => {
                                const selected = ans?.answer === opt;
                                return (
                                    <button
                                        key={opt}
                                        onClick={() => {
                                            setAnswer(q.key, opt);
                                            setTimeout(goNext, 350);
                                        }}
                                        className={`
                      p-4 rounded-2xl border text-left transition-all duration-200
                      ${selected
                                                ? "bg-fuchsia-500/20 border-fuchsia-500/50 text-fuchsia-300 shadow-lg shadow-fuchsia-500/10"
                                                : "bg-white/[0.04] border-white/[0.08] text-slate-300 hover:bg-white/[0.08] hover:border-white/[0.15]"
                                            }
                    `}
                                    >
                                        <span className="text-2xl block mb-2">
                                            {INDUSTRY_ICONS[opt] || "📦"}
                                        </span>
                                        <span className="text-sm font-medium leading-tight block">{opt}</span>
                                    </button>
                                );
                            })}
                        </div>

                        {/* Back button */}
                        <div className="flex justify-between mt-8">
                            <button
                                onClick={goBack}
                                className="px-6 py-3 rounded-xl bg-white/[0.06] border border-white/[0.1] text-slate-400 font-medium transition-all hover:bg-white/[0.1]"
                            >
                                ← Zpět
                            </button>
                            {ans?.answer && (
                                <button
                                    onClick={goNext}
                                    className="px-8 py-3 rounded-xl bg-gradient-to-r from-fuchsia-600 to-purple-600 text-white font-semibold transition-all hover:shadow-lg hover:shadow-fuchsia-500/25 active:scale-[0.98]"
                                >
                                    Další →
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    /* ── Yes / No / Unknown question ── */
    return (
        <div className="min-h-screen bg-slate-950 flex flex-col">
            {/* Progress bar */}
            <ProgressBarUI current={currentQuestion} total={totalQuestions} />

            {/* Decorative blobs */}
            <div className="fixed top-[-200px] right-[-100px] w-[400px] h-[400px] bg-fuchsia-600/10 rounded-full blur-[120px] pointer-events-none" />
            <div className="fixed bottom-[-150px] left-[-80px] w-[350px] h-[350px] bg-cyan-500/8 rounded-full blur-[100px] pointer-events-none" />

            <div className="flex-1 flex items-center justify-center p-4 pt-16">
                <div className={`w-full max-w-xl animate-slide-${direction === "forward" ? "in" : "in-back"}`}>

                    {/* Question text */}
                    <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3 leading-snug">
                        {q.text}
                    </h2>

                    {/* Help text */}
                    {q.help_text && (
                        <p className="text-slate-400 text-sm mb-8 flex items-start gap-2">
                            <span className="text-slate-500 mt-0.5 flex-shrink-0">ℹ️</span>
                            {q.help_text}
                        </p>
                    )}
                    {!q.help_text && <div className="mb-8" />}

                    {/* Answer tiles */}
                    <div className="grid grid-cols-3 gap-3 mb-4">
                        {([
                            { value: "yes", label: "Ano", sub: "1", activeClass: "bg-emerald-500/15 border-emerald-500/40 text-emerald-300", icon: "✓" },
                            { value: "no", label: "Ne", sub: "2", activeClass: "bg-slate-500/15 border-slate-400/30 text-slate-300", icon: "✕" },
                            { value: "unknown", label: "Nevím", sub: "3", activeClass: "bg-amber-500/15 border-amber-500/40 text-amber-300", icon: "?" },
                        ] as const).map((opt) => {
                            const selected = ans?.answer === opt.value;
                            return (
                                <button
                                    key={opt.value}
                                    onClick={() => {
                                        setAnswer(q.key, opt.value);
                                        // Auto-advance for "no" and "unknown" (no followup), delayed for "yes" if followup
                                        if (opt.value !== "yes" || !q.followup) {
                                            setTimeout(goNext, 350);
                                        }
                                    }}
                                    className={`
                    relative py-5 px-4 rounded-2xl border text-center transition-all duration-200 cursor-pointer
                    ${selected
                                            ? `${opt.activeClass} shadow-lg`
                                            : "bg-white/[0.04] border-white/[0.08] text-slate-300 hover:bg-white/[0.08] hover:border-white/[0.15]"
                                        }
                  `}
                                >
                                    <span className="text-2xl block mb-1">{opt.icon}</span>
                                    <span className="text-base font-semibold block">{opt.label}</span>
                                    <span className="text-[10px] text-slate-500 absolute top-2 right-3">{opt.sub}</span>
                                </button>
                            );
                        })}
                    </div>

                    {/* AI Act reference pill */}
                    {q.ai_act_article && (
                        <div className="mb-6">
                            <span className="inline-flex items-center gap-1.5 bg-fuchsia-500/10 border border-fuchsia-500/20 rounded-lg px-3 py-1.5 text-xs text-fuchsia-300">
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
                                {q.ai_act_article}
                            </span>
                        </div>
                    )}

                    {/* ── Followup fields (slides down when "Ano") ── */}
                    {showFollowup && q.followup && (
                        <div className="animate-slide-down mb-6">
                            <div className="bg-white/[0.04] backdrop-blur-xl border border-cyan-500/20 rounded-2xl p-5">
                                <p className="text-cyan-300 text-sm font-semibold mb-4">Upřesněte prosím:</p>
                                <div className="space-y-4">
                                    {q.followup.fields.map((field) => (
                                        <div key={field.key}>
                                            <label className="block text-slate-400 text-sm mb-2 font-medium">
                                                {field.label}
                                            </label>

                                            {/* Select → tile grid */}
                                            {field.type === "select" && field.options && (
                                                <div className="flex flex-wrap gap-2">
                                                    {field.options.map((opt) => {
                                                        const selected = (ans?.details[field.key] as string) === opt;
                                                        return (
                                                            <button
                                                                key={opt}
                                                                onClick={() => setDetail(q.key, field.key, opt)}
                                                                className={`
                                  px-4 py-2.5 rounded-xl border text-sm font-medium transition-all duration-200
                                  ${selected
                                                                        ? "bg-fuchsia-500/20 border-fuchsia-500/50 text-fuchsia-300"
                                                                        : "bg-white/[0.04] border-white/[0.08] text-slate-300 hover:bg-white/[0.08]"
                                                                    }
                                `}
                                                            >
                                                                {opt}
                                                            </button>
                                                        );
                                                    })}
                                                </div>
                                            )}

                                            {/* Multi-select → tile grid with checkmarks */}
                                            {field.type === "multi_select" && field.options && (
                                                <div className="flex flex-wrap gap-2">
                                                    {field.options.map((opt) => {
                                                        const mkey = `${q.key}__${field.key}`;
                                                        const selected = (multiSelections[mkey] || []).includes(opt);
                                                        return (
                                                            <button
                                                                key={opt}
                                                                onClick={() => toggleMulti(q.key, field.key, opt)}
                                                                className={`
                                  px-4 py-2.5 rounded-xl border text-sm font-medium transition-all duration-200 flex items-center gap-2
                                  ${selected
                                                                        ? "bg-fuchsia-500/20 border-fuchsia-500/50 text-fuchsia-300"
                                                                        : "bg-white/[0.04] border-white/[0.08] text-slate-300 hover:bg-white/[0.08]"
                                                                    }
                                `}
                                                            >
                                                                {selected && (
                                                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><path d="M20 6L9 17l-5-5" /></svg>
                                                                )}
                                                                {opt}
                                                            </button>
                                                        );
                                                    })}
                                                </div>
                                            )}

                                            {/* Text → minimal input (fallback) */}
                                            {field.type === "text" && (
                                                <input
                                                    type="text"
                                                    placeholder="Napište…"
                                                    className="w-full bg-white/[0.04] border border-white/[0.1] rounded-xl px-4 py-3 text-white text-sm outline-none focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/25 transition-all placeholder:text-slate-500"
                                                    value={(ans?.details[field.key] as string) || ""}
                                                    onChange={(e) => setDetail(q.key, field.key, e.target.value)}
                                                />
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Navigation */}
                    <div className="flex justify-between items-center mt-6">
                        <button
                            onClick={goBack}
                            className="px-6 py-3 rounded-xl bg-white/[0.06] border border-white/[0.1] text-slate-400 font-medium transition-all hover:bg-white/[0.1]"
                        >
                            ← Zpět
                        </button>

                        {isLast ? (
                            <button
                                onClick={handleSubmit}
                                disabled={submitting}
                                className="px-8 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-emerald-500 text-white font-semibold transition-all hover:shadow-lg hover:shadow-cyan-500/25 active:scale-[0.98] disabled:opacity-50"
                            >
                                {submitting ? "Odesílám…" : "Odeslat dotazník →"}
                            </button>
                        ) : (
                            <button
                                onClick={goNext}
                                className="px-8 py-3 rounded-xl bg-gradient-to-r from-fuchsia-600 to-purple-600 text-white font-semibold transition-all hover:shadow-lg hover:shadow-fuchsia-500/25 active:scale-[0.98]"
                            >
                                Další →
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* Inline animations */}
            <style>{`
        @keyframes fade-in {
          from { opacity: 0; transform: scale(0.98); }
          to { opacity: 1; transform: scale(1); }
        }
        .animate-fade-in {
          animation: fade-in 0.4s ease-out;
        }
        @keyframes slide-in {
          from { opacity: 0; transform: translateX(40px); }
          to { opacity: 1; transform: translateX(0); }
        }
        .animate-slide-in {
          animation: slide-in 0.35s ease-out;
        }
        @keyframes slide-in-back {
          from { opacity: 0; transform: translateX(-40px); }
          to { opacity: 1; transform: translateX(0); }
        }
        .animate-slide-in-back {
          animation: slide-in-back 0.35s ease-out;
        }
        @keyframes slide-down {
          from { opacity: 0; transform: translateY(-12px); max-height: 0; }
          to { opacity: 1; transform: translateY(0); max-height: 800px; }
        }
        .animate-slide-down {
          animation: slide-down 0.4s ease-out;
        }
      `}</style>
        </div>
    );
}

/* ═══════════════════════════════════════════
   PROGRESS BAR COMPONENT
   ═══════════════════════════════════════════ */

function ProgressBarUI({ current, total }: { current: number; total: number }) {
    const pct = Math.min(100, Math.round(((current + 1) / total) * 100));
    return (
        <div className="fixed top-0 left-0 right-0 z-50 bg-slate-950/90 backdrop-blur-md">
            <div className="max-w-2xl mx-auto px-4 py-2.5">
                <div className="flex justify-between items-center mb-1.5">
                    <span className="text-xs text-slate-400 font-medium">
                        Otázka {current + 1} z {total}
                    </span>
                    <span className="text-xs text-fuchsia-400 font-bold">
                        {pct} %
                    </span>
                </div>
                <div className="w-full h-1 bg-white/[0.08] rounded-full overflow-hidden">
                    <div
                        className="h-full rounded-full bg-gradient-to-r from-fuchsia-500 to-cyan-400 transition-all duration-500 ease-out"
                        style={{ width: `${pct}%`, boxShadow: "0 0 12px rgba(217, 70, 239, 0.5)" }}
                    />
                </div>
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════════
   PAGE EXPORT (Suspense wrapper)
   ═══════════════════════════════════════════ */

export default function QuestionnairePage() {
    return (
        <Suspense
            fallback={
                <div className="min-h-screen bg-slate-950 flex items-center justify-center">
                    <div className="w-10 h-10 border-4 border-fuchsia-500/30 border-t-fuchsia-500 rounded-full animate-spin" />
                </div>
            }
        >
            <QuestionnaireInner />
        </Suspense>
    );
}
