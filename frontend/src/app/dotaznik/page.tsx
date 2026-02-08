"use client";

import { useState, useEffect, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ═══════════════════════════════════════════
   TYPY
   ═══════════════════════════════════════════ */

interface FollowupField {
    key: string;
    label: string;
    type: "text" | "select";
    options?: string[];
}

interface Question {
    key: string;
    text: string;
    type: string;
    followup?: { condition: string; fields: FollowupField[] };
    risk_hint: string;
    ai_act_article: string;
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
    answer: "yes" | "no" | "unknown" | "";
    details: Record<string, string>;
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
   DESIGN TOKENS (matching desperados-design.cz)
   ═══════════════════════════════════════════ */

const tokens = {
    bg: "#0f172a",
    surface: "#1e293b",
    primary: "#e879f9",
    primaryDark: "#c026d3",
    secondary: "#22d3ee",
    secondaryDark: "#0891b2",
    text: "#f1f5f9",
    textMuted: "#cbd5e1",
    textDim: "#94a3b8",
    border: "rgba(255,255,255,0.05)",
    borderHover: "rgba(232,121,249,0.3)",
    glass: "rgba(30,41,59,0.7)",
    glassHover: "rgba(30,41,59,0.9)",
    neon: "0 0 25px rgba(232,121,249,0.4)",
    neonStrong: "0 0 50px rgba(232,121,249,0.6)",
    neonBlue: "0 0 25px rgba(34,211,238,0.3)",
};

/* ═══════════════════════════════════════════
   RISK BADGE (pill style, no emoji)
   ═══════════════════════════════════════════ */

function RiskPill({ level }: { level: string }) {
    const cfg: Record<string, { bg: string; border: string; color: string; label: string }> = {
        high: {
            bg: "rgba(239,68,68,0.12)",
            border: "rgba(239,68,68,0.4)",
            color: "#f87171",
            label: "Vysoké riziko",
        },
        limited: {
            bg: "rgba(234,179,8,0.12)",
            border: "rgba(234,179,8,0.35)",
            color: "#facc15",
            label: "Omezené riziko",
        },
        minimal: {
            bg: "rgba(34,197,94,0.12)",
            border: "rgba(34,197,94,0.35)",
            color: "#4ade80",
            label: "Minimální riziko",
        },
    };
    const c = cfg[level] || cfg.minimal;
    return (
        <span
            style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 6,
                fontSize: "0.75rem",
                fontWeight: 600,
                padding: "0.3rem 0.7rem",
                borderRadius: "2rem",
                background: c.bg,
                border: `1px solid ${c.border}`,
                color: c.color,
                letterSpacing: "0.01em",
                whiteSpace: "nowrap",
            }}
        >
            <span
                style={{
                    width: 7,
                    height: 7,
                    borderRadius: "50%",
                    background: c.color,
                    boxShadow: `0 0 6px ${c.color}`,
                }}
            />
            {c.label}
        </span>
    );
}

/* ═══════════════════════════════════════════
   PROGRESS BAR (neon gradient)
   ═══════════════════════════════════════════ */

function ProgressBar({ current, total }: { current: number; total: number }) {
    const pct = Math.round(((current + 1) / total) * 100);
    return (
        <div
            style={{
                position: "fixed",
                top: 0,
                left: 0,
                right: 0,
                zIndex: 100,
                background: "rgba(15,23,42,0.95)",
                backdropFilter: "blur(10px)",
                padding: "0.75rem 1.5rem",
                borderBottom: `1px solid ${tokens.border}`,
            }}
        >
            <div style={{ maxWidth: 700, margin: "0 auto" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                    <span style={{ fontSize: "0.8rem", color: tokens.textMuted, fontWeight: 500 }}>
                        Krok {current + 1} z {total}
                    </span>
                    <span style={{ fontSize: "0.8rem", color: tokens.primary, fontWeight: 700 }}>
                        {pct}%
                    </span>
                </div>
                <div
                    style={{
                        width: "100%",
                        height: 6,
                        background: "rgba(255,255,255,0.08)",
                        borderRadius: 3,
                        overflow: "hidden",
                    }}
                >
                    <div
                        style={{
                            height: "100%",
                            width: `${pct}%`,
                            background: `linear-gradient(90deg, ${tokens.primary}, ${tokens.secondary})`,
                            borderRadius: 3,
                            transition: "width 0.5s cubic-bezier(0.4,0,0.2,1)",
                            boxShadow: "0 0 10px rgba(232,121,249,0.5)",
                        }}
                    />
                </div>
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════════
   HLAVNI KOMPONENTA
   ═══════════════════════════════════════════ */

export default function QuestionnairePage() {
    const [sections, setSections] = useState<Section[]>([]);
    const [step, setStep] = useState(-1); // -1 = welcome
    const [answers, setAnswers] = useState<Record<string, Answer>>({});
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [result, setResult] = useState<AnalysisResult | null>(null);
    const [companyId, setCompanyId] = useState<string | null>(null);
    const [scanId, setScanId] = useState<string | null>(null);

    useEffect(() => {
        fetch(`${API_URL}/api/questionnaire/structure`)
            .then((r) => r.json())
            .then((data) => {
                setSections(data.sections);
                const init: Record<string, Answer> = {};
                for (const s of data.sections) {
                    for (const q of s.questions) {
                        init[q.key] = { question_key: q.key, section: s.id, answer: "", details: {}, tool_name: "" };
                    }
                }
                setAnswers(init);
                setLoading(false);
            })
            .catch(() => {
                setError("Nepodařilo se načíst dotazník.");
                setLoading(false);
            });

        const p = new URLSearchParams(window.location.search);
        if (p.get("company_id")) setCompanyId(p.get("company_id"));
        if (p.get("scan_id")) setScanId(p.get("scan_id"));
    }, []);

    const setAnswer = useCallback((key: string, value: "yes" | "no" | "unknown") => {
        setAnswers((prev) => ({ ...prev, [key]: { ...prev[key], answer: value } }));
    }, []);

    const setDetail = useCallback((qKey: string, fKey: string, value: string) => {
        setAnswers((prev) => ({
            ...prev,
            [qKey]: {
                ...prev[qKey],
                details: { ...prev[qKey].details, [fKey]: value },
                tool_name: fKey.includes("tool_name") || fKey.endsWith("_tool") ? value : prev[qKey].tool_name,
            },
        }));
    }, []);

    const handleSubmit = async () => {
        if (!companyId) {
            setError("Chybí identifikace firmy. Nejdříve naskenujte web na stránce /scan.");
            return;
        }
        setSubmitting(true);
        setError(null);
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
                body: JSON.stringify({ company_id: companyId, scan_id: scanId, answers: list }),
            });
            if (!res.ok) {
                const e = await res.json().catch(() => ({ detail: "Chyba serveru" }));
                throw new Error(e.detail || `HTTP ${res.status}`);
            }
            const data = await res.json();
            setResult(data.analysis);
            setStep(sections.length); // results view
        } catch (e: any) {
            setError(e.message);
        } finally {
            setSubmitting(false);
        }
    };

    /* ── Shared styles ── */
    const pageStyle: React.CSSProperties = {
        minHeight: "100vh",
        background: tokens.bg,
        color: tokens.text,
        fontFamily: "'Inter',-apple-system,BlinkMacSystemFont,sans-serif",
        position: "relative",
        overflow: "hidden",
    };

    const blobStyle = (color: string, top: string, left: string, size: number): React.CSSProperties => ({
        position: "fixed",
        width: size,
        height: size,
        background: color,
        borderRadius: "50%",
        filter: "blur(120px)",
        opacity: 0.15,
        pointerEvents: "none",
        top,
        left,
    });

    const wrapperStyle: React.CSSProperties = {
        position: "relative",
        zIndex: 1,
        maxWidth: 740,
        margin: "0 auto",
        padding: "5.5rem 1.25rem 3rem",
    };

    const glassCard: React.CSSProperties = {
        background: tokens.glass,
        backdropFilter: "blur(10px)",
        border: `1px solid ${tokens.border}`,
        borderRadius: "1.5rem",
        padding: "2rem",
        marginBottom: "1.5rem",
        transition: "border-color 0.3s ease, box-shadow 0.3s ease",
    };

    const btnPrimary: React.CSSProperties = {
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        padding: "0.85rem 2rem",
        borderRadius: "2rem",
        background: `linear-gradient(135deg, ${tokens.primary}, ${tokens.primaryDark})`,
        color: "#0f172a",
        fontWeight: 700,
        fontSize: "0.95rem",
        border: "none",
        cursor: "pointer",
        boxShadow: tokens.neon,
        transition: "all 0.3s cubic-bezier(0.4,0,0.2,1)",
    };

    const btnSecondary: React.CSSProperties = {
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        padding: "0.85rem 2rem",
        borderRadius: "2rem",
        background: "rgba(255,255,255,0.06)",
        color: tokens.textMuted,
        fontWeight: 600,
        fontSize: "0.95rem",
        border: `1px solid rgba(255,255,255,0.1)`,
        cursor: "pointer",
        transition: "all 0.3s cubic-bezier(0.4,0,0.2,1)",
    };

    const stepNumber: React.CSSProperties = {
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        width: "2.5rem",
        height: "2.5rem",
        borderRadius: "50%",
        background: `linear-gradient(135deg, ${tokens.primary}, ${tokens.secondary})`,
        color: "#0f172a",
        fontWeight: 800,
        fontSize: "1rem",
        marginBottom: "1rem",
    };

    const stepTitle: React.CSSProperties = {
        fontSize: "1.75rem",
        fontWeight: 800,
        marginBottom: "0.5rem",
        lineHeight: 1.2,
        letterSpacing: "-0.03em",
    };

    const inputStyle: React.CSSProperties = {
        width: "100%",
        background: "rgba(15,23,42,0.6)",
        border: "1px solid rgba(255,255,255,0.1)",
        borderRadius: "0.75rem",
        padding: "0.85rem 1rem",
        color: tokens.text,
        fontSize: "0.95rem",
        outline: "none",
        transition: "all 0.3s ease",
    };

    const selectStyle: React.CSSProperties = { ...inputStyle, cursor: "pointer" };

    /* ── LOADING ── */
    if (loading) {
        return (
            <div style={pageStyle}>
                <div style={blobStyle(tokens.primary, "-200px", "calc(100% - 300px)", 600)} />
                <div style={blobStyle(tokens.secondary, "calc(100% - 250px)", "-150px", 500)} />
                <div style={{ ...wrapperStyle, textAlign: "center", paddingTop: "12rem" }}>
                    <div style={{ fontSize: "2rem", marginBottom: "1rem", animation: "spin 1s linear infinite" }}>
                        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke={tokens.primary} strokeWidth="2">
                            <path d="M21 12a9 9 0 11-6.219-8.56" />
                        </svg>
                    </div>
                    <p style={{ color: tokens.textMuted }}>Připravuji dotazník...</p>
                </div>
            </div>
        );
    }

    /* ── RESULTS ── */
    if (result) {
        const highCount = result.risk_breakdown.high || 0;
        const limitedCount = result.risk_breakdown.limited || 0;
        const minimalCount = result.risk_breakdown.minimal || 0;

        return (
            <div style={pageStyle}>
                <div style={blobStyle(tokens.primary, "-200px", "calc(100% - 300px)", 600)} />
                <div style={blobStyle(tokens.secondary, "calc(100% - 250px)", "-150px", 500)} />
                <div style={wrapperStyle}>
                    <div style={stepNumber}>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0f172a" strokeWidth="3">
                            <path d="M20 6L9 17l-5-5" />
                        </svg>
                    </div>
                    <h1 style={stepTitle}>
                        Analýza <span style={{ background: `linear-gradient(135deg, ${tokens.primary}, ${tokens.secondary})`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>dokončena</span>
                    </h1>
                    <p style={{ color: tokens.textMuted, marginBottom: "2rem" }}>
                        Na základě vašich odpovědí jsme vyhodnotili rizikový profil vaší firmy.
                    </p>

                    {/* Metriky */}
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "0.75rem", marginBottom: "1.5rem" }}>
                        {[
                            { value: result.ai_systems_declared, label: "AI systémů", color: tokens.primary },
                            { value: highCount, label: "Vysoce rizikové", color: "#f87171" },
                            { value: limitedCount, label: "Omezené riziko", color: "#facc15" },
                        ].map((m, i) => (
                            <div key={i} style={{ ...glassCard, textAlign: "center", padding: "1.5rem 1rem", marginBottom: 0 }}>
                                <div style={{ fontSize: "2rem", fontWeight: 800, color: m.color, textShadow: `0 0 20px ${m.color}40` }}>
                                    {m.value}
                                </div>
                                <div style={{ fontSize: "0.8rem", color: tokens.textDim, marginTop: 4 }}>{m.label}</div>
                            </div>
                        ))}
                    </div>

                    {/* Doporuceni */}
                    {result.recommendations.length > 0 && (
                        <div style={glassCard}>
                            <h2 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "1.25rem", color: tokens.text }}>
                                Doporučení ke compliance
                            </h2>
                            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                                {result.recommendations.map((rec, i) => (
                                    <div
                                        key={i}
                                        style={{
                                            borderLeft: `3px solid ${rec.risk_level === "high" ? "#f87171" : rec.risk_level === "limited" ? "#facc15" : "#4ade80"}`,
                                            paddingLeft: "1rem",
                                            paddingTop: 4,
                                            paddingBottom: 4,
                                        }}
                                    >
                                        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                                            <RiskPill level={rec.risk_level} />
                                            <span style={{ fontWeight: 600, fontSize: "0.9rem" }}>{rec.tool_name}</span>
                                            <span style={{ fontSize: "0.72rem", color: tokens.textDim }}>{rec.ai_act_article}</span>
                                        </div>
                                        <p style={{ fontSize: "0.85rem", color: tokens.textMuted, lineHeight: 1.5 }}>{rec.recommendation}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* CTA */}
                    <div style={{ ...glassCard, textAlign: "center", borderColor: tokens.borderHover }}>
                        <h3 style={{ fontWeight: 700, marginBottom: 8 }}>Kompletní compliance report</h3>
                        <p style={{ fontSize: "0.85rem", color: tokens.textMuted, marginBottom: "1.25rem" }}>
                            Kombinace výsledků automatického skenu a vašeho dotazníku.
                        </p>
                        {scanId ? (
                            <a href={`${API_URL}/api/scan/${scanId}/report`} target="_blank" rel="noopener noreferrer" style={{ ...btnPrimary, textDecoration: "none" }}>
                                Stáhnout report <span style={{ fontSize: "1.1rem" }}>→</span>
                            </a>
                        ) : (
                            <a href="/scan" style={{ ...btnPrimary, textDecoration: "none" }}>
                                Nejdříve naskenovat web <span style={{ fontSize: "1.1rem" }}>→</span>
                            </a>
                        )}
                    </div>
                </div>
            </div>
        );
    }

    /* ── WELCOME SCREEN ── */
    if (step === -1) {
        return (
            <div style={pageStyle}>
                <div style={blobStyle(tokens.primary, "-200px", "calc(100% - 300px)", 600)} />
                <div style={blobStyle(tokens.secondary, "calc(100% - 250px)", "-150px", 500)} />
                <div style={{ ...wrapperStyle, textAlign: "center", paddingTop: "6rem" }}>
                    {/* Logo / Brand */}
                    <div style={{ marginBottom: "2rem" }}>
                        <span style={{ fontSize: "2.5rem", fontWeight: 900, letterSpacing: "-0.04em" }}>
                            AI<span style={{ background: `linear-gradient(135deg, ${tokens.primary}, ${tokens.secondary})`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>shield</span>
                            <span style={{ color: tokens.textDim, fontSize: "1rem", marginLeft: 4 }}>.cz</span>
                        </span>
                    </div>

                    <h1 style={{ fontSize: "2.5rem", fontWeight: 900, letterSpacing: "-0.04em", lineHeight: 1.15, marginBottom: "1rem" }}>
                        AI Act{" "}
                        <span style={{ background: `linear-gradient(135deg, ${tokens.primary}, ${tokens.secondary})`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                            Compliance Dotazník
                        </span>
                    </h1>
                    <p style={{ fontSize: "1.1rem", color: tokens.textMuted, maxWidth: 520, margin: "0 auto 2.5rem", lineHeight: 1.6 }}>
                        Odhalíme AI systémy, které automatický skener nevidí. Stačí naklikat pár odpovědí — žádné dlouhé psaní.
                    </p>

                    {/* Features */}
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1rem", marginBottom: "2.5rem" }}>
                        {[
                            { icon: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z", label: "Hotovo za 5 minut" },
                            { icon: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2", label: `${sections.length} krátkých sekcí` },
                            { icon: "M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z", label: "Vaše data v bezpečí" },
                        ].map((f, i) => (
                            <div
                                key={i}
                                style={{
                                    textAlign: "center",
                                    padding: "1.25rem 0.75rem",
                                    background: tokens.glass,
                                    borderRadius: "1rem",
                                    border: `1px solid ${tokens.border}`,
                                    transition: "all 0.3s ease",
                                }}
                            >
                                <div style={{ display: "flex", justifyContent: "center", marginBottom: 8 }}>
                                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke={tokens.primary} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                        <path d={f.icon} />
                                    </svg>
                                </div>
                                <div style={{ fontSize: "0.85rem", color: tokens.textMuted }}>{f.label}</div>
                            </div>
                        ))}
                    </div>

                    {/* Company ID notice */}
                    {!companyId && (
                        <div style={{ ...glassCard, borderColor: "rgba(234,179,8,0.3)", textAlign: "left", marginBottom: "1.5rem" }}>
                            <p style={{ fontSize: "0.85rem", color: "#facc15", marginBottom: 8, fontWeight: 600 }}>
                                Pro uložení odpovědí potřebujeme identifikaci firmy
                            </p>
                            <p style={{ fontSize: "0.8rem", color: tokens.textMuted, marginBottom: 12 }}>
                                Nejdříve naskenujte web na stránce /scan — odkaz na dotazník se zobrazí ve výsledcích. Nebo zadejte company_id ručně:
                            </p>
                            <input
                                type="text"
                                placeholder="company_id..."
                                style={inputStyle}
                                onChange={(e) => setCompanyId(e.target.value || null)}
                            />
                        </div>
                    )}

                    <button onClick={() => setStep(0)} style={btnPrimary}>
                        Pojďme na to <span style={{ fontSize: "1.2rem" }}>→</span>
                    </button>
                </div>
            </div>
        );
    }

    /* ── WIZARD STEPS ── */
    const section = sections[step];
    if (!section) return null;
    const isLast = step === sections.length - 1;

    return (
        <div style={pageStyle}>
            <div style={blobStyle(tokens.primary, "-200px", "calc(100% - 300px)", 600)} />
            <div style={blobStyle(tokens.secondary, "calc(100% - 250px)", "-150px", 500)} />
            <ProgressBar current={step} total={sections.length} />

            <div style={wrapperStyle}>
                {/* Step number + title */}
                <div style={stepNumber}>{step + 1}</div>
                <h2 style={stepTitle}>
                    {section.title.replace(/[^\w\sáčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ&]/g, "")}
                </h2>
                <p style={{ color: tokens.textMuted, fontSize: "1rem", marginBottom: "2rem" }}>
                    {section.description}
                </p>

                {error && (
                    <div style={{ ...glassCard, borderColor: "rgba(239,68,68,0.4)", marginBottom: "1.5rem" }}>
                        <p style={{ color: "#f87171", fontSize: "0.9rem" }}>{error}</p>
                    </div>
                )}

                {/* Questions */}
                {section.questions.map((q) => {
                    const ans = answers[q.key];
                    return (
                        <div key={q.key} style={{ ...glassCard, transition: "all 0.3s ease" }}>
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: "1rem" }}>
                                <p style={{ fontWeight: 600, fontSize: "0.95rem", lineHeight: 1.4, color: tokens.text }}>
                                    {q.text}
                                </p>
                                <RiskPill level={q.risk_hint} />
                            </div>

                            {/* Answer pills */}
                            <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
                                {(["yes", "no", "unknown"] as const).map((val) => {
                                    const labels = { yes: "Ano", no: "Ne", unknown: "Nevím" };
                                    const isSelected = ans?.answer === val;
                                    return (
                                        <button
                                            key={val}
                                            onClick={() => setAnswer(q.key, val)}
                                            style={{
                                                display: "inline-flex",
                                                alignItems: "center",
                                                gap: 6,
                                                padding: "0.55rem 1rem",
                                                borderRadius: "2rem",
                                                border: isSelected ? `1px solid ${tokens.primary}` : "1px solid rgba(255,255,255,0.1)",
                                                background: isSelected ? "rgba(232,121,249,0.15)" : "rgba(15,23,42,0.5)",
                                                color: isSelected ? tokens.primary : tokens.textMuted,
                                                fontWeight: 500,
                                                fontSize: "0.88rem",
                                                cursor: "pointer",
                                                transition: "all 0.3s ease",
                                                boxShadow: isSelected ? "0 0 15px rgba(232,121,249,0.25)" : "none",
                                            }}
                                        >
                                            {labels[val]}
                                        </button>
                                    );
                                })}
                            </div>

                            {/* AI Act reference */}
                            <div
                                style={{
                                    display: "inline-block",
                                    background: "rgba(232,121,249,0.1)",
                                    border: "1px solid rgba(232,121,249,0.15)",
                                    borderRadius: "0.5rem",
                                    padding: "0.3rem 0.6rem",
                                    fontSize: "0.75rem",
                                    color: tokens.primary,
                                }}
                            >
                                {q.ai_act_article}
                            </div>

                            {/* Followup fields */}
                            {ans?.answer === "yes" && q.followup && (
                                <div
                                    style={{
                                        marginTop: "1rem",
                                        paddingLeft: "1rem",
                                        borderLeft: `2px solid rgba(34,211,238,0.3)`,
                                        animation: "fadeIn 0.3s ease",
                                    }}
                                >
                                    <p style={{ fontSize: "0.8rem", color: tokens.secondary, fontWeight: 600, marginBottom: "0.75rem" }}>
                                        Upřesněte prosím:
                                    </p>
                                    {q.followup.fields.map((field) => (
                                        <div key={field.key} style={{ marginBottom: "0.75rem" }}>
                                            <label style={{ display: "block", fontSize: "0.85rem", color: tokens.textMuted, fontWeight: 500, marginBottom: 6 }}>
                                                {field.label}
                                            </label>
                                            {field.type === "text" ? (
                                                <input
                                                    type="text"
                                                    placeholder="Vyplňte..."
                                                    style={inputStyle}
                                                    value={ans.details[field.key] || ""}
                                                    onChange={(e) => setDetail(q.key, field.key, e.target.value)}
                                                    onFocus={(e) => {
                                                        e.currentTarget.style.borderColor = tokens.primary;
                                                        e.currentTarget.style.boxShadow = `0 0 0 3px rgba(232,121,249,0.15), 0 0 20px rgba(232,121,249,0.1)`;
                                                    }}
                                                    onBlur={(e) => {
                                                        e.currentTarget.style.borderColor = "rgba(255,255,255,0.1)";
                                                        e.currentTarget.style.boxShadow = "none";
                                                    }}
                                                />
                                            ) : (
                                                <select
                                                    style={selectStyle}
                                                    value={ans.details[field.key] || ""}
                                                    onChange={(e) => setDetail(q.key, field.key, e.target.value)}
                                                >
                                                    <option value="">Vyberte...</option>
                                                    {field.options?.map((opt) => (
                                                        <option key={opt} value={opt}>{opt}</option>
                                                    ))}
                                                </select>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    );
                })}

                {/* Navigation */}
                <div style={{ display: "flex", justifyContent: "space-between", marginTop: "2rem" }}>
                    <button
                        onClick={() => setStep(step === 0 ? -1 : step - 1)}
                        style={btnSecondary}
                    >
                        <span style={{ fontSize: "1.1rem" }}>←</span> Zpět
                    </button>

                    {isLast ? (
                        <button
                            onClick={handleSubmit}
                            disabled={submitting || !companyId}
                            style={{
                                ...btnPrimary,
                                background: `linear-gradient(135deg, ${tokens.secondary}, ${tokens.secondaryDark})`,
                                boxShadow: tokens.neonBlue,
                                opacity: submitting || !companyId ? 0.5 : 1,
                                cursor: submitting || !companyId ? "not-allowed" : "pointer",
                            }}
                        >
                            {submitting ? "Odesílám..." : "Odeslat dotazník"} <span style={{ fontSize: "1.1rem" }}>→</span>
                        </button>
                    ) : (
                        <button onClick={() => setStep(step + 1)} style={btnPrimary}>
                            Další <span style={{ fontSize: "1.1rem" }}>→</span>
                        </button>
                    )}
                </div>

                {/* Step dots */}
                <div style={{ display: "flex", justifyContent: "center", gap: 8, marginTop: "2rem" }}>
                    {sections.map((_, i) => (
                        <button
                            key={i}
                            onClick={() => setStep(i)}
                            style={{
                                width: 10,
                                height: 10,
                                borderRadius: "50%",
                                border: "none",
                                cursor: "pointer",
                                transition: "all 0.3s ease",
                                background: i === step ? tokens.primary : i < step ? tokens.secondary : "rgba(255,255,255,0.15)",
                                boxShadow: i === step ? "0 0 10px rgba(232,121,249,0.5)" : "none",
                            }}
                        />
                    ))}
                </div>
            </div>

            {/* Inline keyframes */}
            <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
        </div>
    );
}
