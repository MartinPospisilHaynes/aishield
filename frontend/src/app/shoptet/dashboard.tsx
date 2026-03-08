"use client";

/**
 * Shoptet Addon — Dashboard v2
 * Hlavní panel: compliance skóre s breakdown, AI systémy,
 * compliance stránka (jen pro Standard), upsell CTA, deadliny.
 */

import { useState } from "react";
import { publishCompliancePage, triggerScan, type DashboardData, type AISystemRecord, type DocumentInfo } from "@/lib/shoptet-api";

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").trim();

interface DashboardProps {
    data: DashboardData;
    installationId: string;
    onRefresh: () => void;
}

export default function ShoptetDashboard({ data, installationId, onRefresh }: DashboardProps) {
    const [publishing, setPublishing] = useState(false);
    const [publishError, setPublishError] = useState("");
    const [publishSuccess, setPublishSuccess] = useState(false);
    const [scanning, setScanning] = useState(false);
    const [scanError, setScanError] = useState("");

    const { installation, ai_systems, compliance_score, score_breakdown, compliance_page_published, documents, scan_completed, upsell } = data;
    const isStandard = installation.plan === "standard";

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

    const handleScan = async () => {
        setScanning(true);
        setScanError("");
        try {
            await triggerScan(installationId);
            onRefresh();
        } catch (e) {
            setScanError(e instanceof Error ? e.message : "Scan selhal");
        } finally {
            setScanning(false);
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
                <div className="flex items-center gap-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                        isStandard
                            ? "bg-neon-cyan/20 text-neon-cyan"
                            : "bg-slate-700/50 text-slate-400"
                    }`}>
                        {isStandard ? "Standard" : "Free"}
                    </span>
                    <span className={`inline-block w-2 h-2 rounded-full ${
                        installation.status === "active" ? "bg-green-400" : "bg-red-400"
                    }`} />
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

            {/* Score breakdown */}
            {score_breakdown && Object.keys(score_breakdown).length > 0 && (
                <div className="glass p-5">
                    <h2 className="font-bold text-white mb-3">Rozklad skóre</h2>
                    <div className="space-y-3">
                        {Object.entries(score_breakdown).filter(([key]) => !key.endsWith("_max")).map(([key, val]) => {
                            const maxKey = `${key}_max`;
                            const maxPoints: Record<string, number> = { scan: 15, detection: 25, governance: 30, transparency: 30 };
                            const max = (score_breakdown[maxKey] as number) || maxPoints[key] || 30;
                            const pct = Math.min(100, Math.round((val / max) * 100));
                            const barColor = pct >= 80 ? "bg-green-400" : pct >= 50 ? "bg-yellow-400" : "bg-red-400";
                            const labels: Record<string, string> = {
                                scan: "Sken webu",
                                detection: "Detekce AI systémů",
                                governance: "Governance a řízení",
                                transparency: "Transparentnost",
                            };
                            return (
                                <div key={key}>
                                    <div className="flex justify-between text-xs mb-1">
                                        <span className="text-slate-400">{labels[key] || key}</span>
                                        <span className="text-white font-medium">{val} / {max}</span>
                                    </div>
                                    <div className="h-2 bg-dark-800 rounded-full overflow-hidden">
                                        <div className={`h-full rounded-full transition-all ${barColor}`} style={{ width: `${pct}%` }} />
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Dokumenty */}
            {documents && documents.length > 0 && (
                <div className="glass p-5">
                    <h2 className="font-bold text-white mb-3">Dokumenty ke stažení</h2>
                    <div className="space-y-2">
                        {documents.map((doc) => (
                            <a
                                key={doc.id}
                                href={`${API_URL}${doc.download_url}`}
                                target="_blank"
                                rel="noopener"
                                className="flex items-center justify-between p-3 rounded-lg bg-dark-800/50 hover:bg-dark-800 transition-colors group"
                            >
                                <div className="flex items-center gap-3">
                                    <span className="text-neon-cyan text-lg">{"\uD83D\uDCC4"}</span>
                                    <div>
                                        <div className="text-sm text-white font-medium group-hover:text-neon-cyan transition-colors">{doc.title}</div>
                                        <div className="text-xs text-slate-500">
                                            PDF &bull; {doc.file_size ? `${Math.round(doc.file_size / 1024)} KB` : ""}
                                            {doc.generated_at && ` \u2022 ${new Date(doc.generated_at).toLocaleDateString("cs")}`}
                                        </div>
                                    </div>
                                </div>
                                <span className="text-slate-500 group-hover:text-neon-cyan text-sm transition-colors">{"\u2193"}</span>
                            </a>
                        ))}
                    </div>
                </div>
            )}

            {/* Scan webu */}
            <div className="glass p-5">
                <div className="flex items-center justify-between mb-3">
                    <h2 className="font-bold text-white">Scan e-shopu</h2>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                        scan_completed
                            ? "bg-green-500/20 text-green-400"
                            : "bg-slate-700/50 text-slate-400"
                    }`}>
                        {scan_completed ? "Dokon\u010Deno" : "ček\u00E1 na scan"}
                    </span>
                </div>
                <p className="text-sm text-slate-400 mb-3">
                    {scan_completed
                        ? "Va\u0161 e-shop byl automaticky naskenov\u00E1n. Nalezen\u00E9 AI systémy jsou zahrnuty v tabulce v\u00FD\u0161e."
                        : "Spus\u0165te scan pro automatick\u00E9 rozpozn\u00E1n\u00ed AI skript\u016F na va\u0161em webu."}
                </p>
                <button
                    onClick={handleScan}
                    disabled={scanning}
                    className="btn-secondary py-2 px-4 text-sm disabled:opacity-50"
                >
                    {scanning ? "Skenuji..." : scan_completed ? "Znovu naskenovat" : "Spustit scan"}
                </button>
                {scanError && <p className="mt-2 text-sm text-red-400">{scanError}</p>}
            </div>

            {/* Compliance str\u00E1nka \u2014 jen pro Standard */}
            <div className="glass p-5">
                <div className="flex items-center justify-between mb-3">
                    <h2 className="font-bold text-white">Compliance stránka</h2>
                    {isStandard && (
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                            compliance_page_published
                                ? "bg-green-500/20 text-green-400"
                                : "bg-yellow-500/20 text-yellow-400"
                        }`}>
                            {compliance_page_published ? "Publikováno" : "Nepublikováno"}
                        </span>
                    )}
                </div>

                {isStandard ? (
                    <>
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
                                {"\u2713"} Stránka úspěšně {compliance_page_published ? "aktualizována" : "publikována"}.
                            </p>
                        )}
                        {publishError && (
                            <p className="mt-3 text-sm text-red-400">{publishError}</p>
                        )}
                    </>
                ) : (
                    <div className="text-center py-4">
                        <p className="text-sm text-slate-400 mb-2">
                            Automatická compliance stránka je dostupná v plánu <b className="text-neon-cyan">Standard</b>.
                        </p>
                        <p className="text-xs text-slate-500">
                            Upgradujte v nastavení addonu na Shoptet.
                        </p>
                    </div>
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
                    <p className="text-xs text-slate-600 mt-1">Vyplňte dotazník pro přidání systémů.</p>
                </div>
            )}

            {/* Upsell CTA */}
            {upsell && (
                <div className="glass p-5 border border-neon-fuchsia/20 bg-gradient-to-br from-dark-900 to-neon-fuchsia/5">
                    <h2 className="font-bold text-white mb-2">Kompletní AI Act řešení</h2>
                    <p className="text-sm text-slate-400 mb-4">
                        {upsell.description}
                    </p>

                    <div className="flex items-center gap-3 mb-4">
                        <span className="text-slate-500 line-through text-sm">{upsell.original_price.toLocaleString("cs")} Kč</span>
                        <span className="text-2xl font-bold text-neon-fuchsia">{upsell.price_after_discount.toLocaleString("cs")} Kč</span>
                        <span className="text-xs px-2 py-0.5 rounded-full bg-neon-fuchsia/20 text-neon-fuchsia">
                            -{upsell.discount_percent}% kód {upsell.discount_code}
                        </span>
                    </div>

                    <a
                        href={upsell.url}
                        target="_blank"
                        rel="noopener"
                        className="btn-primary inline-block py-2.5 px-6 text-sm"
                    >
                        Zjistit více na AIshield.cz
                    </a>
                </div>
            )}

            {/* Akce */}
            <div className="glass p-5">
                <h2 className="font-bold text-white mb-3">Co dělat dál?</h2>
                <div className="space-y-3">
                    <ActionItem
                        done={ai_systems.length > 0}
                        text="Vyplnit dotazník o AI systémech"
                    />
                    <ActionItem
                        done={scan_completed}
                        text="Naskenovat e-shop na AI skripty"
                    />
                    <ActionItem
                        done={documents.length > 0}
                        text="Stáhnout AI Registr a Compliance Checklist"
                    />
                    <ActionItem
                        done={compliance_page_published}
                        text={isStandard ? "Publikovat compliance stránku na e-shop" : "Upgradujte na Standard pro compliance stránku"}
                    />
                    <ActionItem
                        done={compliance_score >= 80}
                        text="Dosáhnout 80%+ compliance skóre"
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
