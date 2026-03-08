"use client";

/**
 * Shoptet Addon — Dotazník v2 (20 otázek v 7 sekcích)
 * E-shopař odpovídá na otázky o AI systémech.
 * Sekce: Komunikace → Obsah → Provoz → Riziko → Zaměstnanci → Data → Transparentnost
 */

import { useState, useCallback } from "react";
import { submitQuestionnaire, type QuestionnaireRequest, type QuestionnaireResponse } from "@/lib/shoptet-api";

interface WizardProps {
    installationId: string;
    eshopName: string;
    onComplete: () => void;
}

// ── Definice sekcí a otázek ──

type AnswerValue = string | string[];

interface YesNoQuestion {
    type: "yesno";
    key: string;
    label: string;
    hint?: string;
}

interface MultiSelectQuestion {
    type: "multiselect";
    key: string;
    label: string;
    options: string[];
    showWhen?: { key: string; value: string };
}

type Question = YesNoQuestion | MultiSelectQuestion;

interface Section {
    title: string;
    subtitle: string;
    icon: string;
    questions: Question[];
}

const SECTIONS: Section[] = [
    {
        title: "AI komunikace",
        subtitle: "Chatboty, live chat a automatické emaily",
        icon: "\uD83D\uDCAC",
        questions: [
            { type: "yesno", key: "uses_ai_chatbot", label: "Používáte na e-shopu AI chatbot nebo live chat s AI odpověďmi?", hint: "Např. Smartsupp AI, Tidio AI, vlastní ChatGPT widget" },
            { type: "multiselect", key: "chatbot_providers", label: "Které služby používáte?", options: ["Smartsupp", "Tidio", "LiveChat", "Zendesk Chat", "Drift", "Intercom", "ChatGPT widget", "Jiný"], showWhen: { key: "uses_ai_chatbot", value: "ano" } },
            { type: "yesno", key: "uses_ai_email_auto", label: "Používáte AI pro automatizaci emailů zákazníkům?", hint: "Automatické odpovědi, AI personalizace, smart kampaně" },
        ],
    },
    {
        title: "AI obsah",
        subtitle: "Generování textů, obrázků a dalšího obsahu",
        icon: "\u270D\uFE0F",
        questions: [
            { type: "yesno", key: "uses_chatgpt", label: "Používáte ChatGPT, Claude nebo podobný AI nástroj?", hint: "Pro popisky produktů, texty na web, interní práci" },
            { type: "multiselect", key: "chatgpt_purposes", label: "K čemu jej využíváte?", options: ["Popisky produktů", "Texty na web", "Marketingové texty", "Zákaznická podpora", "Interní práce", "Analýzy"], showWhen: { key: "uses_chatgpt", value: "ano" } },
            { type: "yesno", key: "uses_ai_content", label: "Generujete AI obsah viditelný přímo zákazníkům na webu?", hint: "SEO texty, popisky kategorií, automatické překlady" },
            { type: "multiselect", key: "content_types", label: "Jaký obsah generujete?", options: ["Produktové popisky", "SEO texty", "Kategorie", "Blog články", "Automatické překlady", "Jiný"], showWhen: { key: "uses_ai_content", value: "ano" } },
            { type: "yesno", key: "uses_ai_images", label: "Generujete obrázky nebo videa pomocí AI?", hint: "Midjourney, DALL·E, Stable Diffusion, AI pozadí produktů" },
            { type: "multiselect", key: "image_providers", label: "Které generátory používáte?", options: ["Midjourney", "DALL·E / ChatGPT", "Stable Diffusion", "Adobe Firefly", "Canva AI", "Jiný"], showWhen: { key: "uses_ai_images", value: "ano" } },
        ],
    },
    {
        title: "AI v provozu",
        subtitle: "Doporučení, vyhledávání, ceny a rozhodování",
        icon: "\u2699\uFE0F",
        questions: [
            { type: "yesno", key: "uses_dynamic_pricing", label: "Používáte dynamické ceny řízené algoritmem nebo AI?", hint: "Automatické úpravy cen podle poptávky, konkurence apod." },
            { type: "yesno", key: "uses_ai_recommendation", label: "Máte AI doporučovací systém produktů?", hint: "Zákazníci také koupili, personalizované nabídky" },
            { type: "multiselect", key: "recommendation_providers", label: "Který systém využíváte?", options: ["Shoptet nativní", "Luigi's Box", "Recombee", "Algolia Recommend", "Jiný"], showWhen: { key: "uses_ai_recommendation", value: "ano" } },
            { type: "yesno", key: "uses_ai_search", label: "Máte AI-powered vyhledávání na e-shopu?", hint: "Chytré vyhledávání s NLP, autocomplete, semantic search" },
            { type: "multiselect", key: "search_providers", label: "Kterou službu používáte?", options: ["Luigi's Box", "Algolia", "Doofinder", "Shoptet nativní", "Jiný"], showWhen: { key: "uses_ai_search", value: "ano" } },
            { type: "yesno", key: "uses_ai_decision", label: "Rozhoduje AI o zákaznících nebo objednávkách?", hint: "Automatické schvalování/zamítání, credit scoring, fraud detekce" },
            { type: "multiselect", key: "decision_types", label: "O čem AI rozhoduje?", options: ["Schválení objednávek", "Fraud detekce", "Zákaznický scoring", "Vrácení zboží", "Jiný"], showWhen: { key: "uses_ai_decision", value: "ano" } },
        ],
    },
    {
        title: "Rizikové oblasti",
        subtitle: "Děti, vysokorizikové AI systémy",
        icon: "\u26A0\uFE0F",
        questions: [
            { type: "yesno", key: "uses_ai_for_children", label: "Cílíte s AI systémy na děti do 18 let?", hint: "Hračky, dětské oblečení, edukační produkty s AI personalizací" },
        ],
    },
    {
        title: "Zaměstnanci a AI",
        subtitle: "Školení a informovanost o AI Act",
        icon: "\uD83D\uDC65",
        questions: [
            { type: "yesno", key: "has_ai_training", label: "Prošli vaši zaměstnanci školením o AI gramotnosti?", hint: "Article 4 AI Act vyžaduje dostatečnou úroveň AI gramotnosti personálu" },
            { type: "yesno", key: "informs_employees", label: "Jsou zaměstnanci informováni o AI systémech, které při práci používají?", hint: "Interní dokumentace, onboarding, pravidla pro použití AI" },
        ],
    },
    {
        title: "Data a governance",
        subtitle: "Osobní údaje, pravidla, dohled",
        icon: "\uD83D\uDD12",
        questions: [
            { type: "yesno", key: "ai_processes_personal_data", label: "Zpracovávají vaše AI systémy osobní údaje zákazníků?", hint: "Jméno, email, nákupní historie, chování na webu" },
            { type: "yesno", key: "ai_data_stored_eu", label: "Jsou data zpracovávaná AI uložena v EU?", hint: "GDPR + AI Act vyžaduje znalost místa zpracování" },
            { type: "yesno", key: "has_ai_guidelines", label: "Máte interní pravidla pro používání AI?", hint: "Směrnice, kdo smí co používat, jaká data se smí sdílet s AI" },
            { type: "yesno", key: "has_ai_register", label: "Vedete evidenci (registr) AI systémů?", hint: "Seznam AI nástrojů, jejich účel, dodavatel, riziko" },
            { type: "yesno", key: "has_oversight_person", label: "Má někdo ve firmě zodpovědnost za AI compliance?", hint: "Osoba odpovědná za AI systémy, jejich kontrolu a dodržování předpisů" },
        ],
    },
    {
        title: "Transparentnost",
        subtitle: "Informovanost zákazníků a lidský dohled",
        icon: "\uD83D\uDD0D",
        questions: [
            { type: "yesno", key: "can_override_ai", label: "Lze rozhodnutí AI systémů přepsat člověkem?", hint: "Lidský dohled — zákazník nebo pracovník může rozporovat AI rozhodnutí" },
            { type: "yesno", key: "has_transparency_page", label: "Máte na webu stránku o používání AI?", hint: "Podobně jako GDPR stránka — seznam AI systémů, účel, kontakt" },
            { type: "yesno", key: "wants_compliance_page", label: "Přejete si, aby AIshield vygeneroval compliance stránku automaticky?", hint: "Stránka se vloží do patičky webu přes Shoptet Pages API" },
        ],
    },
];

const TOTAL_SECTIONS = SECTIONS.length;

// ── Inicializace formuláře ──

function createInitialFormData(): Record<string, AnswerValue> {
    const data: Record<string, AnswerValue> = {};
    for (const section of SECTIONS) {
        for (const q of section.questions) {
            if (q.type === "yesno") data[q.key] = "";
            if (q.type === "multiselect") data[q.key] = [];
        }
    }
    return data;
}

// ── Hlavní komponenta ──

export default function ShoptetWizard({ installationId, eshopName, onComplete }: WizardProps) {
    const [phase, setPhase] = useState<"intro" | "form" | "submitting" | "done">("intro");
    const [sectionIndex, setSectionIndex] = useState(0);
    const [formData, setFormData] = useState<Record<string, AnswerValue>>(createInitialFormData);
    const [result, setResult] = useState<QuestionnaireResponse | null>(null);
    const [error, setError] = useState("");

    const updateField = useCallback((key: string, value: AnswerValue) => {
        setFormData((prev) => ({ ...prev, [key]: value }));
    }, []);

    const currentSection = SECTIONS[sectionIndex];

    // Viditelné otázky (podmíněné se zobrazí jen při splnění showWhen)
    const visibleQuestions = currentSection?.questions.filter((q) => {
        if (q.type === "multiselect" && q.showWhen) {
            return formData[q.showWhen.key] === q.showWhen.value;
        }
        return true;
    }) || [];

    // Jsou zodpovězeny všechny povinné yesno v sekci?
    const sectionComplete = visibleQuestions
        .filter((q) => q.type === "yesno")
        .every((q) => formData[q.key] !== "");

    const handleNext = () => {
        if (sectionIndex < TOTAL_SECTIONS - 1) {
            setSectionIndex((i) => i + 1);
        } else {
            handleSubmit();
        }
    };

    const handleBack = () => {
        if (sectionIndex > 0) {
            setSectionIndex((i) => i - 1);
        } else {
            setPhase("intro");
        }
    };

    const handleSubmit = async () => {
        setPhase("submitting");
        setError("");
        try {
            const payload = {} as QuestionnaireRequest;
            for (const section of SECTIONS) {
                for (const q of section.questions) {
                    const val = formData[q.key];
                    if (q.type === "yesno") {
                        (payload as unknown as Record<string, string>)[q.key] = (val as string) || "nevim";
                    } else {
                        (payload as unknown as Record<string, string[]>)[q.key] = (val as string[]) || [];
                    }
                }
            }
            const res = await submitQuestionnaire(installationId, payload);
            setResult(res);
            setPhase("done");
        } catch (e) {
            setError(e instanceof Error ? e.message : "Odeslání selhalo");
            setPhase("form");
        }
    };

    // ── INTRO ──
    if (phase === "intro") {
        return (
            <div className="max-w-2xl mx-auto">
                <div className="glass p-8">
                    <h1 className="text-2xl font-bold text-white mb-2">
                        AI Act Compliance — Dotazník
                    </h1>
                    <p className="text-slate-400 mb-6">
                        Vítejte, <span className="text-white font-medium">{eshopName}</span>.
                        Dotazník zjistí, jaké AI systémy na e-shopu používáte
                        a jak jste připraveni na nařízení EU o AI (AI Act).
                    </p>

                    <div className="bg-dark-800/50 rounded-lg p-4 mb-6 border border-white/5">
                        <h3 className="text-sm font-semibold text-neon-cyan mb-2">Proč je to důležité?</h3>
                        <ul className="text-sm text-slate-400 space-y-1.5">
                            <li>{"\u2022"} <b className="text-white">Article 50</b> — chatboty a AI obsah musí informovat zákazníky (deadline: 2. 8. 2026)</li>
                            <li>{"\u2022"} <b className="text-white">Article 4</b> — zaměstnanci musí mít AI gramotnost (platí od 2. 2. 2025)</li>
                            <li>{"\u2022"} Pokuta až <b className="text-white">35 mil. EUR</b> nebo 7 % obratu</li>
                        </ul>
                    </div>

                    <div className="grid grid-cols-3 gap-3 mb-6">
                        <div className="bg-dark-800/50 rounded-lg p-3 text-center border border-white/5">
                            <div className="text-lg font-bold text-neon-cyan">{TOTAL_SECTIONS}</div>
                            <div className="text-xs text-slate-500">sekcí</div>
                        </div>
                        <div className="bg-dark-800/50 rounded-lg p-3 text-center border border-white/5">
                            <div className="text-lg font-bold text-neon-fuchsia">20</div>
                            <div className="text-xs text-slate-500">otázek</div>
                        </div>
                        <div className="bg-dark-800/50 rounded-lg p-3 text-center border border-white/5">
                            <div className="text-lg font-bold text-white">3 min</div>
                            <div className="text-xs text-slate-500">doba vyplnění</div>
                        </div>
                    </div>

                    <button
                        onClick={() => setPhase("form")}
                        className="btn-primary w-full py-3 text-base"
                    >
                        Začít dotazník
                    </button>
                </div>
            </div>
        );
    }

    // ── SUBMITTING ──
    if (phase === "submitting") {
        return (
            <div className="flex items-center justify-center min-h-[300px]">
                <div className="text-center">
                    <div className="w-8 h-8 border-2 border-neon-cyan/30 border-t-neon-cyan rounded-full animate-spin mx-auto mb-3" />
                    <p className="text-slate-400">Analyzuji vaše odpovědi a klasifikuji AI systémy...</p>
                </div>
            </div>
        );
    }

    // ── DONE ──
    if (phase === "done" && result) {
        const breakdown = result.score_breakdown || {};
        return (
            <div className="max-w-2xl mx-auto">
                <div className="glass p-8 text-center">
                    <div className="text-5xl mb-4">{"\u2705"}</div>
                    <h2 className="text-xl font-bold text-white mb-2">Dotazník dokončen</h2>
                    <p className="text-slate-400 mb-6">{result.message}</p>

                    {/* Score */}
                    <div className="bg-dark-800/50 rounded-xl p-6 mb-6 border border-white/5">
                        <div className="text-4xl font-bold text-neon-cyan mb-1">{result.compliance_score}%</div>
                        <div className="text-sm text-slate-500 mb-4">Compliance skóre</div>

                        <div className="grid grid-cols-2 gap-3 text-left">
                            {Object.entries(breakdown).map(([key, val]) => (
                                <div key={key} className="bg-dark-900/50 rounded-lg p-2.5">
                                    <div className="text-xs text-slate-500 capitalize">{key.replace(/_/g, " ")}</div>
                                    <div className="text-sm font-bold text-white">{val} b.</div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Metriky */}
                    <div className="grid grid-cols-3 gap-4 mb-6">
                        <div className="bg-dark-800/50 rounded-lg p-3">
                            <div className="text-2xl font-bold text-white">{result.ai_systems_count}</div>
                            <div className="text-xs text-slate-500">AI systémů</div>
                        </div>
                        <div className="bg-dark-800/50 rounded-lg p-3">
                            <div className="text-2xl font-bold text-neon-fuchsia">{result.art50_relevant}</div>
                            <div className="text-xs text-slate-500">Article 50</div>
                        </div>
                        <div className="bg-dark-800/50 rounded-lg p-3">
                            <div className="text-2xl font-bold text-yellow-400">{result.risk_areas?.length || 0}</div>
                            <div className="text-xs text-slate-500">Rizikových oblastí</div>
                        </div>
                    </div>

                    {/* Doporučení */}
                    {result.recommendations && result.recommendations.length > 0 && (
                        <div className="text-left bg-dark-800/50 rounded-lg p-4 mb-6 border border-white/5">
                            <h3 className="text-sm font-semibold text-neon-fuchsia mb-2">Klíčová doporučení</h3>
                            <ul className="text-sm text-slate-400 space-y-1">
                                {result.recommendations.slice(0, 5).map((r, i) => (
                                    <li key={i}>{"\u2022"} {r}</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    <button onClick={onComplete} className="btn-primary w-full py-3">
                        Přejít na dashboard
                    </button>
                </div>
            </div>
        );
    }

    // ── FORM ──
    return (
        <div className="max-w-2xl mx-auto">
            {/* Progress bar */}
            <div className="flex gap-1 mb-2">
                {SECTIONS.map((_, i) => (
                    <div
                        key={i}
                        className={`h-1 flex-1 rounded-full transition-colors ${
                            i <= sectionIndex ? "bg-neon-cyan" : "bg-dark-700"
                        }`}
                    />
                ))}
            </div>
            <div className="text-xs text-slate-500 text-right mb-4">
                {sectionIndex + 1} / {TOTAL_SECTIONS}
            </div>

            <div className="glass p-6">
                {/* Hlavička sekce */}
                <div className="flex items-center gap-3 mb-1">
                    <span className="text-2xl">{currentSection.icon}</span>
                    <h2 className="text-lg font-bold text-white">{currentSection.title}</h2>
                </div>
                <p className="text-sm text-slate-400 mb-6 ml-[44px]">{currentSection.subtitle}</p>

                {/* Otázky */}
                <div className="space-y-5">
                    {currentSection.questions.map((q) => {
                        if (q.type === "multiselect" && q.showWhen) {
                            if (formData[q.showWhen.key] !== q.showWhen.value) return null;
                        }

                        if (q.type === "yesno") {
                            return (
                                <YesNoField
                                    key={q.key}
                                    label={q.label}
                                    hint={q.hint}
                                    value={formData[q.key] as string}
                                    onChange={(v) => updateField(q.key, v)}
                                />
                            );
                        }

                        if (q.type === "multiselect") {
                            return (
                                <MultiSelectField
                                    key={q.key}
                                    label={q.label}
                                    options={q.options}
                                    value={formData[q.key] as string[]}
                                    onChange={(v) => updateField(q.key, v)}
                                />
                            );
                        }

                        return null;
                    })}
                </div>

                {/* Chyba */}
                {error && (
                    <div className="mt-4 p-3 rounded-lg bg-red-900/30 border border-red-500/30 text-red-300 text-sm">
                        {error}
                    </div>
                )}

                {/* Navigace */}
                <div className="flex gap-3 pt-6 mt-6 border-t border-white/5">
                    <button onClick={handleBack} className="btn-secondary flex-1 py-2.5">
                        Zpět
                    </button>
                    <button
                        onClick={handleNext}
                        disabled={!sectionComplete}
                        className={`btn-primary flex-1 py-2.5 ${!sectionComplete ? "opacity-40 cursor-not-allowed" : ""}`}
                    >
                        {sectionIndex === TOTAL_SECTIONS - 1 ? "Odeslat dotazník" : "Pokračovat"}
                    </button>
                </div>
            </div>
        </div>
    );
}

// ── Ano / Ne / Nevím pole ──

function YesNoField({ label, hint, value, onChange }: {
    label: string;
    hint?: string;
    value: string;
    onChange: (v: string) => void;
}) {
    const options = [
        { val: "ano", label: "Ano", color: "bg-neon-cyan/20 border-neon-cyan/50 text-neon-cyan" },
        { val: "ne", label: "Ne", color: "bg-emerald-900/30 border-emerald-500/40 text-emerald-400" },
        { val: "nevim", label: "Nevím", color: "bg-yellow-900/20 border-yellow-500/30 text-yellow-400" },
    ];

    return (
        <div className="bg-dark-800/30 rounded-lg p-4 border border-white/5">
            <p className="text-sm text-white font-medium mb-1">{label}</p>
            {hint && <p className="text-xs text-slate-500 mb-3">{hint}</p>}
            <div className="flex gap-2">
                {options.map((opt) => (
                    <button
                        key={opt.val}
                        onClick={() => onChange(opt.val)}
                        className={`px-4 py-1.5 rounded-full text-sm border transition-colors ${
                            value === opt.val
                                ? opt.color
                                : "bg-dark-800/50 border-white/10 text-slate-400 hover:border-white/20"
                        }`}
                    >
                        {opt.label}
                    </button>
                ))}
            </div>
        </div>
    );
}

// ── Multi-select chipy ──

function MultiSelectField({ label, options, value, onChange }: {
    label: string;
    options: string[];
    value: string[];
    onChange: (v: string[]) => void;
}) {
    const toggle = (opt: string) => {
        if (value.includes(opt)) {
            onChange(value.filter((v) => v !== opt));
        } else {
            onChange([...value, opt]);
        }
    };

    return (
        <div className="ml-4 bg-dark-900/30 rounded-lg p-3 border border-white/5">
            <p className="text-xs text-slate-400 mb-2">{label}</p>
            <div className="flex flex-wrap gap-2">
                {options.map((opt) => {
                    const selected = value.includes(opt);
                    return (
                        <button
                            key={opt}
                            onClick={() => toggle(opt)}
                            className={`px-3 py-1 rounded-full text-xs border transition-colors ${
                                selected
                                    ? "bg-neon-cyan/20 border-neon-cyan/50 text-neon-cyan"
                                    : "bg-dark-800/50 border-white/10 text-slate-400 hover:border-white/20 hover:text-white"
                            }`}
                        >
                            {selected ? "\u2713 " : ""}{opt}
                        </button>
                    );
                })}
            </div>
        </div>
    );
}
