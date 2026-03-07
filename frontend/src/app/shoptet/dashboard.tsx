"use client";

/**
 * Shoptet Addon — Dashboard
 * Hlavní panel po dokončení wizardu: compliance skóre, AI systémy,
 * stav compliance stránky, deadliny.
 */

import { useState } from "react";
import { publishCompliancePage, type DashboardData, type AISystemRecord } from "@/lib/shoptet-api";

interface DashboardProps {
    data: DashboardData;
    installationId: string;
    onRefresh: () => void;
}

export default function ShoptetDashboard({ data, installationId, onRefresh }: DashboardProps) {
    const [publishing, setPublishing] = useState(false);
    const [publishError, setPublishError] = useState("");
    const [publishSuccess, setPublishSuccess] = useState(false);

    const { installation, ai_systems, compliance_score, compliance_page_published } = data;

    const art50Systems = ai_systems.filter((s) => s.ai_act_article === "art50");
    const art4Systems = ai_systems.filter((s) => s.ai_act_article !== "art50");

    // Dny do Article 50 deadline
    const art50Deadline = new Date("2026-08-02");
    const now = new Date();
    const daysToDeadline = Math.ceil((art50Deadline.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

    const handlePublish = async () => {
        setPublishing(true);
        setPublishError("");
        setPublishSuccess(false);
        try {
            await publishCompliancePage(installationId);
            setPublishSuccess(true);
            onRefresh();
        } catch (e) {
            setPublishError(e instanceof Error ? e.message : "Publikace selhala");
        } finally {
            setPublishing(false);
        }
    };

    return (
        <div className="max-w-3xl mx-auto space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-xl font-bold text-white">AI Act Compliance</h1>
                    <p className="text-sm text-slate-400">{installation.eshop_name || installation.eshop_url}</p>
                </div>
                <div className="flex items-center gap-2">
                    <span className={`inline-block w-2 h-2 rounded-full ${
                        installation.status === "active" ? "bg-green-400" : "bg-red-400"
                    }`} />
                    <span className="text-xs text-slate-500">
                        {installation.status === "active" ? "Aktivní" : installation.status}
                    </span>
                </div>
            </div>

            {/* Score + Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <ScoreCard
                    label="Compliance"
                    value={`${compliance_score}%`}
                    color={compliance_score >= 80 ? "text-green-400" : compliance_score >= 50 ? "text-yellow-400" : "text-red-400"}
                />
                <ScoreCard label="AI systémů" value={String(ai_systems.length)} color="text-white" />
                <ScoreCard label="Article 50" value={String(art50Systems.length)} color="text-neon-fuchsia" />
                <ScoreCard
                    label="Do deadline"
                    value={daysToDeadline > 0 ? `${daysToDeadline}d` : "Prošel!"}
                    color={daysToDeadline > 90 ? "text-neon-cyan" : daysToDeadline > 30 ? "text-yellow-400" : "text-red-400"}
                />
            </div>

            {/* Compliance stránka */}
            <div className="glass p-5">
                <div className="flex items-center justify-between mb-3">
                    <h2 className="font-bold text-white">Compliance stránka</h2>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                        compliance_page_published
                            ? "bg-green-500/20 text-green-400"
                            : "bg-yellow-500/20 text-yellow-400"
                    }`}>
                        {compliance_page_published ? "Publikováno" : "Nepublikováno"}
                    </span>
                </div>

                <p className="text-sm text-slate-400 mb-4">
                    {compliance_page_published
                        ? "Stránka /ai-compliance je živá na vašem e-shopu a informuje zákazníky o AI systémech."
                        : "Publikujte compliance stránku na váš e-shop. Stránka informuje zákazníky o používaných AI systémech dle EU AI Act."}
                </p>

                <button
                    onClick={handlePublish}
                    disabled={publishing}
                    className="btn-primary py-2 px-5 text-sm disabled:opacity-50"
                >
                    {publishing
                        ? "Publikuji..."
                        : compliance_page_published
                            ? "Aktualizovat stránku"
                            : "Publikovat na e-shop"}
                </button>

                {publishSuccess && (
                    <p className="mt-3 text-sm text-green-400">
                        &#x2713; Stránka úspěšně {compliance_page_published ? "aktualizována" : "publikována"}.
                    </p>
                )}
                {publishError && (
                    <p className="mt-3 text-sm text-red-400">{publishError}</p>
                )}
            </div>

            {/* AI systémy — Article 50 */}
            {art50Systems.length > 0 && (
                <div className="glass p-5">
                    <h2 className="font-bold text-white mb-1">Article 50 — Povinná transparence</h2>
                    <p className="text-xs text-slate-500 mb-4">
                        Tyto AI systémy komunikují se zákazníky a vyžadují informování (deadline: 2. 8. 2026)
                    </p>
                    <AISystemTable systems={art50Systems} />
                </div>
            )}

            {/* AI systémy — Article 4 */}
            {art4Systems.length > 0 && (
                <div className="glass p-5">
                    <h2 className="font-bold text-white mb-1">Article 4 — Evidenční povinnost</h2>
                    <p className="text-xs text-slate-500 mb-4">
                        Tyto AI systémy podléhají evidenční povinnosti (platí od 2. 2. 2025)
                    </p>
                    <AISystemTable systems={art4Systems} />
                </div>
            )}

            {ai_systems.length === 0 && (
                <div className="glass p-5 text-center">
                    <p className="text-slate-400">Žádné AI systémy dosud neevidovány.</p>
                    <p className="text-xs text-slate-600 mt-1">Vyplňte wizard znovu pro přidání systémů.</p>
                </div>
            )}

            {/* Akce */}
            <div className="glass p-5">
                <h2 className="font-bold text-white mb-3">Co dělat dál?</h2>
                <div className="space-y-3">
                    <ActionItem
                        done={ai_systems.length > 0}
                        text="Vyplnit sebehodnocení AI systémů"
                    />
                    <ActionItem
                        done={compliance_page_published}
                        text="Publikovat compliance stránku na e-shop"
                    />
                    <ActionItem
                        done={compliance_score >= 100}
                        text="Dosáhnout 100% compliance skóre"
                    />
                </div>
            </div>

            {/* Footer */}
            <div className="text-center text-xs text-slate-600 pb-4">
                <a href="https://aishield.cz" target="_blank" rel="noopener" className="hover:text-slate-400 transition-colors">
                    AIshield.cz
                </a>
                {" — "}AI Act compliance pro e-shopy
            </div>
        </div>
    );
}

// ── Pomocné komponenty ──

function ScoreCard({ label, value, color }: { label: string; value: string; color: string }) {
    return (
        <div className="glass p-3 text-center">
            <div className={`text-2xl font-bold ${color}`}>{value}</div>
            <div className="text-xs text-slate-500 mt-0.5">{label}</div>
        </div>
    );
}

function AISystemTable({ systems }: { systems: AISystemRecord[] }) {
    return (
        <div className="overflow-x-auto">
            <table className="w-full text-sm">
                <thead>
                    <tr className="text-left text-xs text-slate-500 border-b border-white/5">
                        <th className="pb-2 pr-4">Poskytovatel</th>
                        <th className="pb-2 pr-4">Typ</th>
                        <th className="pb-2 pr-4">Riziko</th>
                        <th className="pb-2">Zdroj</th>
                    </tr>
                </thead>
                <tbody>
                    {systems.map((s) => (
                        <tr key={s.id} className="border-b border-white/5 last:border-0">
                            <td className="py-2.5 pr-4 text-white font-medium">{s.provider}</td>
                            <td className="py-2.5 pr-4 text-slate-400">
                                {s.details?.description_cs || s.ai_type}
                            </td>
                            <td className="py-2.5 pr-4">
                                <span className={`badge-${s.risk_level}`}>
                                    {s.risk_level === "minimal" ? "Minimální" :
                                     s.risk_level === "limited" ? "Omezené" :
                                     s.risk_level === "high" ? "Vysoké" : s.risk_level}
                                </span>
                            </td>
                            <td className="py-2.5 text-slate-500 text-xs">{s.source}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

function ActionItem({ done, text }: { done: boolean; text: string }) {
    return (
        <div className="flex items-center gap-3">
            <span className={`flex-shrink-0 w-5 h-5 rounded-full border-2 flex items-center justify-center text-xs
                ${done ? "border-green-400 bg-green-400/20 text-green-400" : "border-slate-600 text-transparent"}`}>
                {done && "\u2713"}
            </span>
            <span className={done ? "text-slate-400 line-through" : "text-white"}>{text}</span>
        </div>
    );
}
