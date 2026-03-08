"use client";

import { useState, useEffect, useCallback } from "react";

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

/* ─── Typy ─── */
interface Question {
    key: string;
    text: string;
    type: string;
    risk_hint: string;
    ai_act_article: string | null;
}

interface Section {
    id: string;
    title: string;
    description: string;
    questions: Question[];
}

interface CanEditResponse {
    can_edit: boolean;
    reason: string;
    plan: string;
    days_remaining: number | null;
    edit_deadline: string | null;
}

interface Props {
    open: boolean;
    onClose: () => void;
    companyId: string;
    answers: Record<string, string>;
}

/* ─── Pomocná funkce pro formátování odpovědí ─── */
function formatAnswer(value: string): string {
    if (value === "yes") return "Ano";
    if (value === "no") return "Ne";
    if (value === "not_applicable") return "Neaplikováno";
    if (value === "unknown") return "Nevím";
    if (value.length > 60) return value.slice(0, 57) + "…";
    return value;
}

/* ═══════════════════════════════════════════════════════════
   QUESTIONNAIRE NAVIGATOR — rozcestník pro úpravu odpovědí
   ═══════════════════════════════════════════════════════════ */
export default function QuestionnaireNavigator({ open, onClose, companyId, answers }: Props) {
    const [sections, setSections] = useState<Section[]>([]);
    const [canEdit, setCanEdit] = useState<CanEditResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [expandedSection, setExpandedSection] = useState<string | null>(null);

    // Načti strukturu dotazníku a oprávnění k editaci
    const loadData = useCallback(async () => {
        if (!open || !companyId) return;
        setLoading(true);
        try {
            const [structRes, editRes] = await Promise.all([
                fetch(`${API_URL}/api/questionnaire/structure`),
                fetch(`${API_URL}/api/questionnaire/can-edit/${companyId}`),
            ]);
            if (structRes.ok) {
                const structData = await structRes.json();
                setSections(structData.sections || []);
            }
            if (editRes.ok) {
                setCanEdit(await editRes.json());
            }
        } catch {
            // Tiché selhání — zobrazí se fallback
        } finally {
            setLoading(false);
        }
    }, [open, companyId]);

    useEffect(() => { loadData(); }, [loadData]);

    if (!open) return null;

    // Počet zodpovězených vs celkových v sekci
    const sectionStats = (section: Section) => {
        const answered = section.questions.filter((q) => answers[q.key] && answers[q.key] !== "").length;
        return { answered, total: section.questions.length };
    };

    // Barva rizika
    const riskColor = (hint: string) => {
        if (hint === "unacceptable" || hint === "high") return "text-red-400";
        if (hint === "limited") return "text-amber-400";
        return "text-slate-500";
    };

    const editBlocked = canEdit && !canEdit.can_edit;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Překrytí */}
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

            {/* Modal */}
            <div className="relative w-full max-w-2xl max-h-[85vh] flex flex-col rounded-2xl border border-white/[0.12] bg-slate-900/95 backdrop-blur-xl shadow-2xl shadow-fuchsia-500/10 animate-fade-in">
                {/* Header */}
                <div className="flex items-center justify-between p-6 pb-4 border-b border-white/[0.06]">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-fuchsia-500/15 border border-fuchsia-500/25 flex items-center justify-center">
                            <svg className="w-5 h-5 text-fuchsia-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                            </svg>
                        </div>
                        <div>
                            <h2 className="text-lg font-bold text-white">Navigátor dotazníku</h2>
                            <p className="text-xs text-slate-400">Vyberte otázku, kterou chcete upravit</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 rounded-lg hover:bg-white/[0.06] transition-colors">
                        <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* Blokace editace */}
                {editBlocked && (
                    <div className="mx-6 mt-4 rounded-xl bg-red-500/10 border border-red-500/20 p-4">
                        <div className="flex items-center gap-2 mb-1">
                            <svg className="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m0 0v2m0-2h2m-2 0H10m11-7a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span className="text-sm font-medium text-red-400">Editace uzamčena</span>
                        </div>
                        <p className="text-xs text-red-300/80">{canEdit?.reason}</p>
                    </div>
                )}

                {/* Zbývající dny */}
                {canEdit && canEdit.can_edit && canEdit.days_remaining !== null && (
                    <div className="mx-6 mt-4 rounded-xl bg-cyan-500/10 border border-cyan-500/20 p-3 flex items-center gap-2">
                        <svg className="w-4 h-4 text-cyan-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span className="text-xs text-cyan-300">
                            Editační okno: zbývá {canEdit.days_remaining} {canEdit.days_remaining === 1 ? "den" : canEdit.days_remaining >= 2 && canEdit.days_remaining <= 4 ? "dny" : "dní"}
                        </span>
                    </div>
                )}

                {/* Tělo — seznam sekcí */}
                <div className="flex-1 overflow-y-auto p-6 pt-4 space-y-2">
                    {loading ? (
                        <div className="flex items-center justify-center py-12">
                            <div className="w-8 h-8 border-2 border-fuchsia-500/30 border-t-fuchsia-500 rounded-full animate-spin" />
                        </div>
                    ) : sections.length === 0 ? (
                        <p className="text-sm text-slate-400 text-center py-8">Nelze načíst strukturu dotazníku.</p>
                    ) : (
                        sections.map((section) => {
                            const stats = sectionStats(section);
                            const isExpanded = expandedSection === section.id;
                            return (
                                <div key={section.id} className="rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden">
                                    {/* Hlavička sekce */}
                                    <button
                                        onClick={() => setExpandedSection(isExpanded ? null : section.id)}
                                        className="w-full flex items-center justify-between px-4 py-3 hover:bg-white/[0.03] transition-colors"
                                    >
                                        <div className="flex items-center gap-3">
                                            <span className="text-sm font-semibold text-slate-200">{section.title}</span>
                                            <span className="text-[10px] rounded-full px-2 py-0.5 bg-white/[0.06] text-slate-400">
                                                {stats.answered}/{stats.total}
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            {stats.answered === stats.total && stats.total > 0 && (
                                                <span className="text-[10px] rounded-full px-2 py-0.5 bg-green-500/10 text-green-400 border border-green-500/20">Kompletní</span>
                                            )}
                                            <svg className={`w-4 h-4 text-slate-400 transition-transform ${isExpanded ? "rotate-180" : ""}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                                            </svg>
                                        </div>
                                    </button>

                                    {/* Otázky v sekci */}
                                    {isExpanded && (
                                        <div className="border-t border-white/[0.04] px-4 pb-3">
                                            {section.questions.map((q) => {
                                                const currentAnswer = answers[q.key];
                                                const hasAnswer = currentAnswer && currentAnswer !== "";
                                                return (
                                                    <div key={q.key} className="flex items-center justify-between gap-3 py-2.5 border-b border-white/[0.03] last:border-0">
                                                        <div className="flex-1 min-w-0">
                                                            <p className="text-sm text-slate-300 truncate">{q.text}</p>
                                                            <div className="flex items-center gap-2 mt-0.5">
                                                                {hasAnswer && (
                                                                    <span className="text-xs text-slate-500">{formatAnswer(currentAnswer)}</span>
                                                                )}
                                                                {q.risk_hint && q.risk_hint !== "minimal" && (
                                                                    <span className={`text-[10px] ${riskColor(q.risk_hint)}`}>{q.risk_hint}</span>
                                                                )}
                                                            </div>
                                                        </div>
                                                        {editBlocked ? (
                                                            <span className="flex-shrink-0 w-7 h-7 rounded-lg bg-white/[0.03] border border-white/[0.06] flex items-center justify-center">
                                                                <svg className="w-3.5 h-3.5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                                                                </svg>
                                                            </span>
                                                        ) : (
                                                            <a
                                                                href={`/dotaznik?company_id=${companyId}&edit=true&q=${q.key}`}
                                                                className="flex-shrink-0 w-7 h-7 rounded-lg bg-fuchsia-500/10 border border-fuchsia-500/20 hover:bg-fuchsia-500/20 flex items-center justify-center transition-colors"
                                                                title="Upravit odpověď"
                                                            >
                                                                <svg className="w-3.5 h-3.5 text-fuchsia-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                                                </svg>
                                                            </a>
                                                        )}
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    )}
                                </div>
                            );
                        })
                    )}
                </div>

                {/* Footer */}
                <div className="p-6 pt-4 border-t border-white/[0.06]">
                    {editBlocked ? (
                        <p className="text-xs text-slate-500 text-center">
                            Pro úpravu odpovědí přejděte na vyšší plán nebo kontaktujte podporu.
                        </p>
                    ) : (
                        <a
                            href={`/dotaznik?company_id=${companyId}&edit=true`}
                            className="block w-full text-center px-4 py-3 rounded-xl bg-gradient-to-r from-fuchsia-600 to-purple-600 hover:from-fuchsia-500 hover:to-purple-500 text-white text-sm font-medium transition-all"
                        >
                            Otevřít celý dotazník
                        </a>
                    )}
                </div>
            </div>
        </div>
    );
}
