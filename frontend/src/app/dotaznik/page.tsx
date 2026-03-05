"use client";

import { useState, useEffect, useCallback, Suspense, useRef } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAnalytics } from "@/lib/analytics";
import { createClient } from "@/lib/supabase-browser";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ── Helper: render warning text with **bold** markers as white bold spans ── */
function renderWarningText(text: string) {
    // Split by newlines first, then handle bold within each line
    const lines = text.split(/\n/);
    return lines.map((line, li) => {
        const parts = line.split(/\*\*(.*?)\*\*/g);
        const rendered = parts.map((part, i) =>
            i % 2 === 1
                ? <span key={i} className="text-white font-bold">{part}</span>
                : <span key={i}>{part}</span>
        );
        return <span key={li}>{li > 0 && <br />}{rendered}</span>;
    });
}

/* ═══════════════════════════════════════════
   TYPES
   ═══════════════════════════════════════════ */

interface FollowupField {
    key: string;
    label: string;
    type: "text" | "select" | "single_select" | "multi_select" | "info";
    options?: string[];
    warning?: Record<string, string>;
}

interface Question {
    key: string;
    text: string;
    type: string;               // "yes_no_unknown" | "single_select" | "conditional_fields"
    options?: string[];          // for single_select (industry)
    help_text?: string;
    followup?: { condition: string; fields: FollowupField[] };
    followup_no?: { fields: FollowupField[] };
    followup_yes?: { fields: FollowupField[] };
    risk_hint: string;
    ai_act_article: string | null;
    show_when?: string;          // e.g. "transparency_page_implementation == 'Náš webdesignér'"
    fields?: FollowupField[];    // for conditional_fields type
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
   INDUSTRY ICONS (professional SVG)
   ═══════════════════════════════════════════ */

const INDUSTRY_SVG: Record<string, React.ReactNode> = {
    "E-shop / Online obchod": (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 00-3 3h15.75m-12.75-3h11.218c1.121-2.3 2.1-4.684 2.924-7.138a60.114 60.114 0 00-16.536-1.84M7.5 14.25L5.106 5.272M6 20.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm12.75 0a.75.75 0 11-1.5 0 .75.75 0 011.5 0z" /></svg>
    ),
    "Účetnictví / Finance": (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
    ),
    "Zdravotnictví": (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" /></svg>
    ),
    "Vzdělávání / Školství": (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.902 59.902 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.697 50.697 0 0112 13.489a50.702 50.702 0 017.74-3.342M6.75 15a.75.75 0 100-1.5.75.75 0 000 1.5zm0 0v-3.675A55.378 55.378 0 0112 8.443m-7.007 11.55A5.981 5.981 0 006.75 15.75v-1.5" /></svg>
    ),
    "Výroba / Průmysl": (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M11.42 15.17l-5.67 3.1a.75.75 0 01-1.12-.66V6.57a.75.75 0 01.38-.66l5.67-3.1a.75.75 0 01.74 0l5.67 3.1a.75.75 0 01.38.66v11.04a.75.75 0 01-1.12.66l-5.67-3.1a.75.75 0 00-.74 0zM12 8.25v7.5" /></svg>
    ),
    "IT / Technologie": (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" /></svg>
    ),
    "Stavebnictví": (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 0h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008z" /></svg>
    ),
    "Doprava / Logistika": (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M8.25 18.75a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h6m-9 0H3.375a1.125 1.125 0 01-1.125-1.125V14.25m17.25 4.5a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0H21M3.375 14.25h.008v.008h-.008v-.008zm0-3h17.25V6.375a1.125 1.125 0 00-1.125-1.125H3.375A1.125 1.125 0 002.25 6.375v4.875h.008z" /></svg>
    ),
    "Restaurace / Gastronomie": (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 8.25v-1.5m0 1.5c-1.355 0-2.697.056-4.024.166C6.845 8.51 6 9.473 6 10.608v2.513m6-4.871c1.355 0 2.697.056 4.024.166C17.155 8.51 18 9.473 18 10.608v2.513M15 8.25v-1.5m-6 1.5v-1.5m12 9.75l-1.5.75a3.354 3.354 0 01-3 0 3.354 3.354 0 00-3 0 3.354 3.354 0 01-3 0 3.354 3.354 0 00-3 0 3.354 3.354 0 01-3 0L3 16.5m15-3.379a48.474 48.474 0 00-6-.371c-2.032 0-4.034.126-6 .371m12 0c.39.049.777.102 1.163.16 1.07.16 1.837 1.094 1.837 2.175v5.169c0 .621-.504 1.125-1.125 1.125H4.125A1.125 1.125 0 013 20.625v-5.17c0-1.08.768-2.014 1.837-2.174A47.78 47.78 0 016 13.12M12.265 3.11a.375.375 0 11-.53 0L12 2.845l.265.265z" /></svg>
    ),
    "Kadeřnictví / Kosmetika": (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M7.848 8.25l1.536.887M7.848 8.25a3 3 0 11-5.196-3 3 3 0 015.196 3zm1.536.887a2.165 2.165 0 011.083 1.839c.005.351.054.695.14 1.024M9.384 9.137l2.077 1.199M7.848 15.75l1.536-.887m-1.536.887a3 3 0 11-5.196 3 3 3 0 015.196-3zm1.536-.887a2.165 2.165 0 001.083-1.838c.005-.352.054-.696.14-1.025m-1.223 2.863l2.077-1.199m0-3.328a4.323 4.323 0 012.068-1.379l5.325-1.628a4.5 4.5 0 012.48-.044l.803.215-7.794 4.5m-2.882-1.664A4.331 4.331 0 0010.607 12m3.736 0l7.794 4.5-.802.215a4.5 4.5 0 01-2.48-.043l-5.326-1.629a4.324 4.324 0 01-2.068-1.379M14.343 12l-2.882 1.664" /></svg>
    ),
    "Právní služby": (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 3v17.25m0 0c-1.472 0-2.882.265-4.185.75M12 20.25c1.472 0 2.882.265 4.185.75M18.75 4.97A48.416 48.416 0 0012 4.5c-2.291 0-4.545.16-6.75.47m13.5 0c1.01.143 2.01.317 3 .52m-3-.52l2.62 10.726c.122.499-.106 1.028-.589 1.202a5.988 5.988 0 01-2.031.352 5.988 5.988 0 01-2.031-.352c-.483-.174-.711-.703-.59-1.202L18.75 4.971zm-16.5.52c.99-.203 1.99-.377 3-.52m0 0l2.62 10.726c.122.499-.106 1.028-.589 1.202a5.989 5.989 0 01-2.031.352 5.989 5.989 0 01-2.031-.352c-.483-.174-.711-.703-.59-1.202L5.25 4.971z" /></svg>
    ),
    "Nemovitosti / Reality": (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" /></svg>
    ),
    "Zemědělství": (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" /></svg>
    ),
    "Jiné": (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M6.75 12a.75.75 0 11-1.5 0 .75.75 0 011.5 0zM12.75 12a.75.75 0 11-1.5 0 .75.75 0 011.5 0zM18.75 12a.75.75 0 11-1.5 0 .75.75 0 011.5 0z" /></svg>
    ),
    /* Company size */
    "Jen já (OSVČ)": (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" /></svg>
    ),
    "2–9 zaměstnanců": (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" /></svg>
    ),
    "10–49 zaměstnanců": (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" /></svg>
    ),
    "50–249 zaměstnanců": (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21" /></svg>
    ),
    "250+ zaměstnanců": (
        <svg className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 21v-8.25M15.75 21v-8.25M8.25 21v-8.25M3 9l9-6 9 6m-1.5 12V10.332A48.36 48.36 0 0012 9.75c-2.551 0-5.056.2-7.5.582V21M3 21h18M12 6.75h.008v.008H12V6.75z" /></svg>
    ),
};

/* ═══════════════════════════════════════════
   INNER COMPONENT (uses useSearchParams)
   ═══════════════════════════════════════════ */

function QuestionnaireInner() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const { track } = useAnalytics();
    const questionStartTimeRef = useRef<number>(Date.now());
    const questionChangeCountRef = useRef<Record<string, number>>({});
    const questStartTimeRef = useRef<number>(Date.now());
    const answersRef = useRef<Record<string, Answer>>({});
    const followupRef = useRef<HTMLDivElement>(null);
    const navRef = useRef<HTMLDivElement>(null);

    /* ── State ── */
    const [sections, setSections] = useState<Section[]>([]);
    const [currentQuestion, setCurrentQuestion] = useState(-1); // -1=welcome, 0..N=flat index
    const [answers, setAnswers] = useState<Record<string, Answer>>({});
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [submitError, setSubmitError] = useState<string | null>(null);
    const [result, setResult] = useState<AnalysisResult | null>(null);
    const [companyId, setCompanyId] = useState<string | null>(null);
    const [scanId, setScanId] = useState<string | null>(null);
    const [direction, setDirection] = useState<"forward" | "back">("forward");
    const [sectionFlash, setSectionFlash] = useState<string | null>(null);
    const [multiSelections, setMultiSelections] = useState<Record<string, string[]>>({});
    const [isEditMode, setIsEditMode] = useState(false);
    const [fromDashboard, setFromDashboard] = useState(false); // came from dashboard to answer specific Q
    const [serverAnswersLoaded, setServerAnswersLoaded] = useState(false); // flag to trigger resume-position
    const [customAnswers, setCustomAnswers] = useState<Record<string, string>>({}); // question_key → custom text

    /* ── Realtime autosave: uloží jednu odpověď na server okamžitě ── */
    const saveToServer = useCallback(async (
        questionKey: string,
        section: string,
        answer: string,
        details: Record<string, any> | null,
        toolName: string | null,
        questionIndex: number,
        customAnswer?: string,
    ) => {
        if (!companyId || !answer) return;
        try {
            const body: any = {
                company_id: companyId,
                question_key: questionKey,
                section: section,
                answer: answer,
                details: details && Object.keys(details).length > 0 ? details : null,
                tool_name: toolName || null,
                current_question_index: questionIndex,
            };
            if (customAnswer && customAnswer.trim()) {
                body.custom_answer = customAnswer.trim();
            }
            // Fire-and-forget — neblokuje UI
            fetch(`${API_URL}/api/questionnaire/autosave`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            }).then(r => {
                if (!r.ok) console.warn(`[Autosave] Server ${r.status}`);
                else console.log(`[Autosave] OK: ${questionKey}`);
            }).catch(err => {
                console.warn(`[Autosave] Offline/chyba:`, err);
                // Nevadí — localStorage je záloha
            });
        } catch { /* ignore */ }
    }, [companyId]);

    /* ── Flat question list (with show_when filtering) ── */
    const allQuestions: (Question & { _section: string; _sectionTitle: string })[] = sections.flatMap((s) =>
        s.questions
            .filter((q) => {
                // Filter out conditional_fields questions whose show_when condition is not met
                if (q.show_when) {
                    const match = q.show_when.match(/^(\w+)\s*==\s*'(.+)'$/);
                    if (match) {
                        const [, depKey, depValue] = match;
                        const depAnswer = answers[depKey]?.answer;
                        // For single_select, the answer is stored directly
                        // Match if the answer starts with the condition value (partial match)
                        if (!depAnswer || !depAnswer.startsWith(depValue.split("'")[0])) return false;
                    }
                }
                return true;
            })
            .map((q) => ({ ...q, _section: s.id, _sectionTitle: s.title }))
    );
    const totalQuestions = allQuestions.length;

    /* ── Section emoji icons ── */
    const SECTION_EMOJI: Record<string, string> = {
        industry: "🏢",
        internal_ai: "🤖",
        customer_service: "💬",
        hr: "👤",
        finance: "💰",
        education: "🎓",
        prohibited_systems: "⚠️",
        infrastructure_safety: "🛡️",
        data_protection: "🔒",
        ai_literacy: "📚",
        human_oversight: "👁️",
        ai_role: "🔧",
        incident_management: "🚨",
        implementation: "🔨",
    };



    /* ── Fetch structure ── */
    useEffect(() => {
        fetch(`${API_URL}/api/questionnaire/structure`)
            .then((r) => r.json())
            .then((data) => {
                const secs = data.sections || [];
                const total = secs.reduce((n: number, s: Section) => n + s.questions.length, 0);
                console.log(`[Dotazník] Načteno ${secs.length} sekcí, ${total} otázek`);
                setSections(secs);
                const init: Record<string, Answer> = {};
                for (const s of secs) {
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

    /* ── Prefill from registration (Supabase user_metadata) ── */
    useEffect(() => {
        (async () => {
            try {
                const supabase = createClient();
                const { data: { user } } = await supabase.auth.getUser();
                if (!user?.user_metadata) return;
                const meta = user.user_metadata;
                setAnswers((prev) => {
                    const updated = { ...prev };
                    // Pre-fill only empty fields
                    if (meta.company_name && updated.company_legal_name && !updated.company_legal_name.answer) {
                        updated.company_legal_name = { ...updated.company_legal_name, answer: meta.company_name };
                    }
                    if (meta.ico && updated.company_ico && !updated.company_ico.answer) {
                        updated.company_ico = { ...updated.company_ico, answer: meta.ico };
                    }
                    if (user.email && updated.company_contact_email && !updated.company_contact_email.answer) {
                        updated.company_contact_email = { ...updated.company_contact_email, answer: user.email };
                    }
                    return updated;
                });
            } catch { /* not logged in — skip prefill */ }
        })();
    }, [sections]); // run after sections loaded so answer slots exist

    /* ── Restore from localStorage helper ── */
    const _restoreFromLocalStorage = useCallback((cid: string) => {
        try {
            const saved = localStorage.getItem(`aishield_quest_${cid}`);
            if (saved) {
                const parsed = JSON.parse(saved);
                if (parsed.answers) {
                    setAnswers((prev) => {
                        const updated = { ...prev };
                        for (const [k, v] of Object.entries(parsed.answers) as [string, any][]) {
                            if (updated[k]) {
                                updated[k] = { ...updated[k], answer: v.answer || "", details: v.details || {}, tool_name: v.tool_name || "" };
                            }
                        }
                        return updated;
                    });
                }
                if (typeof parsed.currentQuestion === "number") {
                    setCurrentQuestion(parsed.currentQuestion);
                }
                if (parsed.customAnswers) {
                    setCustomAnswers(parsed.customAnswers);
                }
                console.log("[Dotazník] Obnoveno z localStorage");
            }
        } catch { /* ignore localStorage errors */ }
    }, []);

    /* ── URL params + pre-fill existing answers in edit mode ── */
    useEffect(() => {
        const cid = searchParams.get("company_id");
        const sid = searchParams.get("scan_id");
        const edit = searchParams.get("edit");
        if (cid) setCompanyId(cid);
        if (sid) setScanId(sid);
        if (edit === "true") setIsEditMode(true);

        // Pre-fill existing answers if company_id present
        if (cid) {
            fetch(`${API_URL}/api/questionnaire/${cid}/results`)
                .then((r) => { if (!r.ok) throw new Error(); return r.json(); })
                .then((data) => {
                    if (data.answers && data.answers.length > 0) {
                        const multiUpdates: Record<string, string[]> = {};
                        setAnswers((prev) => {
                            const updated = { ...prev };
                            for (const a of data.answers) {
                                if (updated[a.question_key]) {
                                    updated[a.question_key] = {
                                        ...updated[a.question_key],
                                        answer: a.answer || "",
                                        details: a.details || {},
                                        tool_name: a.tool_name || "",
                                    };
                                    // Restore multi-select state for top-level multi_select
                                    if (a.answer && a.answer.includes(", ")) {
                                        const mkey = `topLevel__${a.question_key}`;
                                        multiUpdates[mkey] = a.answer.split(", ");
                                    }
                                    // Restore multi-select state for followup fields
                                    if (a.details) {
                                        for (const [fkey, fval] of Object.entries(a.details)) {
                                            if (Array.isArray(fval)) {
                                                multiUpdates[`${a.question_key}__${fkey}`] = fval;
                                            }
                                        }
                                    }
                                }
                            }
                            return updated;
                        });
                        setMultiSelections((pm) => ({ ...pm, ...multiUpdates }));
                        setServerAnswersLoaded(true);
                        // Obnovit custom answers ze serveru
                        const restoredCustom: Record<string, string> = {};
                        for (const a of data.answers) {
                            if (a.details?.custom_answer) {
                                restoredCustom[a.question_key] = a.details.custom_answer;
                            }
                        }
                        if (Object.keys(restoredCustom).length > 0) {
                            setCustomAnswers(prev => ({ ...prev, ...restoredCustom }));
                        }
                        console.log(`[Dotazník] Obnoveno ${data.answers.length} odpovědí ze serveru`);
                    } else {
                        // Server has no answers — try localStorage
                        _restoreFromLocalStorage(cid!);
                    }
                })
                .catch(() => {
                    // API error — try localStorage
                    _restoreFromLocalStorage(cid!);
                });
        }
    }, [searchParams]);

    /* ── Resume position: jump to first unanswered question after server restore ── */
    useEffect(() => {
        if (!serverAnswersLoaded || allQuestions.length === 0) return;
        // Don't override if ?q= param was provided (jump-to-question mode)
        if (searchParams.get("q")) { setServerAnswersLoaded(false); return; }
        const firstUnanswered = allQuestions.findIndex(q => !answers[q.key]?.answer);
        if (firstUnanswered >= 0) {
            setCurrentQuestion(firstUnanswered);
            console.log(`[Dotazník] Resuming at question ${firstUnanswered} (first unanswered)`);
        } else if (allQuestions.length > 0) {
            setCurrentQuestion(0);
            console.log(`[Dotazník] All answered, starting from question 0`);
        }
        setServerAnswersLoaded(false);
    }, [serverAnswersLoaded, sections, answers]);

    /* ── Jump to specific question via ?q=question_key ── */
    useEffect(() => {
        const jumpTo = searchParams.get("q");
        const cid = searchParams.get("company_id");
        if (jumpTo && allQuestions.length > 0) {
            const idx = allQuestions.findIndex((aq) => aq.key === jumpTo);
            if (idx >= 0) setCurrentQuestion(idx);
            // If coming from dashboard with specific question, set flag for auto-return
            if (cid) setFromDashboard(true);
        }
    }, [searchParams, allQuestions.length]);

    /* ── Navigation helpers ── */
    const goNext = useCallback(() => {
        setDirection("forward");
        questionStartTimeRef.current = Date.now();

        // Okamžitý autosave aktuální odpovědi na server
        const currentQ = allQuestions[currentQuestion];
        if (currentQ && companyId) {
            const currentAns = answersRef.current[currentQ.key];
            if (currentAns && currentAns.answer) {
                // Přidat custom_answer do details pokud existuje
                const customText = customAnswers[currentQ.key];
                let mergedDetails = { ...(currentAns.details || {}) };
                if (customText && customText.trim()) {
                    mergedDetails.custom_answer = customText.trim();
                }
                saveToServer(
                    currentAns.question_key,
                    currentAns.section,
                    currentAns.answer,
                    mergedDetails,
                    currentAns.tool_name,
                    currentQuestion + 1,
                    customText,
                );
            }
        }

        setCurrentQuestion((p) => {
            if (p >= totalQuestions - 1) return p;
            const next = p + 1;
            console.log(`[Dotazník] goNext: ${p} → ${next} / ${totalQuestions}`);
            // Save position to localStorage on explicit navigation
            if (companyId) {
                try {
                    const existing = localStorage.getItem(`aishield_quest_${companyId}`);
                    const data = existing ? JSON.parse(existing) : {};
                    data.currentQuestion = next;
                    data.customAnswers = customAnswers;
                    localStorage.setItem(`aishield_quest_${companyId}`, JSON.stringify(data));
                } catch { /* ignore */ }
            }
            return next;
        });
        window.scrollTo({ top: 0, behavior: "smooth" });
    }, [totalQuestions, companyId, allQuestions, currentQuestion, customAnswers, saveToServer]);

    const goBack = useCallback(() => {
        setDirection("back");
        questionStartTimeRef.current = Date.now();
        setCurrentQuestion((p) => p <= 0 ? -1 : p - 1);
        window.scrollTo({ top: 0, behavior: "smooth" });
    }, []);

    // Keep answersRef in sync with answers state
    useEffect(() => { answersRef.current = answers; }, [answers]);

    /* ── Set answer ── */
    const setAnswer = useCallback(
        (key: string, value: string) => {
            setAnswers((prev) => {
                const prevAnswer = prev[key]?.answer;
                // Track answer changes (re-answers)
                if (prevAnswer && prevAnswer !== "" && prevAnswer !== value) {
                    questionChangeCountRef.current[key] = (questionChangeCountRef.current[key] || 0) + 1;
                    track("question_changed", {
                        question_id: key,
                        from: prevAnswer,
                        to: value,
                        change_count: questionChangeCountRef.current[key],
                    });
                }
                // Track time spent on this question
                const timeSpent = Date.now() - questionStartTimeRef.current;
                track("question_answered", {
                    question_id: key,
                    answer_type: value,
                    time_spent_ms: timeSpent,
                }, timeSpent);
                return {
                    ...prev,
                    [key]: { ...prev[key], answer: value },
                };
            });
        },
        [track]
    );

    /* ── Auto-save: debounced localStorage write on answer changes ── */
    /* Only saves answers data, NOT currentQuestion position.
       Position is saved only on explicit "Další" (goNext) or "Uložit a pokračovat později" */
    useEffect(() => {
        if (!companyId || currentQuestion < 0) return;
        const timer = setTimeout(() => {
            try {
                const existing = localStorage.getItem(`aishield_quest_${companyId}`);
                const existingData = existing ? JSON.parse(existing) : {};
                const saveData = {
                    ...existingData,
                    answers: Object.fromEntries(
                        Object.entries(answers).map(([k, v]) => [k, v])
                    ),
                    customAnswers,
                    companyId,
                    timestamp: new Date().toISOString(),
                };
                localStorage.setItem(`aishield_quest_${companyId}`, JSON.stringify(saveData));
            } catch { /* ignore localStorage quota errors */ }
        }, 2000); // 2s debounce
        return () => clearTimeout(timer);
    }, [answers, companyId, customAnswers]);

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
                    details: { ...ap[qKey].details, [fKey]: next },
                },
            }));
            return { ...prev, [mkey]: next };
        });
    }, []);

    /* ── Submit & Redirect to Dashboard ── */
    const handleSubmit = useCallback(async () => {
        if (submitting) return; // prevent double-submit
        setSubmitting(true);
        setSubmitError(null);
        console.log('[Dotazník] Odesílám odpovědi...');

        // Use answersRef to always get the latest state (avoids stale closure in setTimeout)
        const latestAnswers = answersRef.current;
        const list = Object.values(latestAnswers)
            .filter((a) => a.answer !== "")
            .map((a) => {
                const mergedDetails = { ...(a.details || {}) };
                const customText = customAnswers[a.question_key];
                if (customText && customText.trim()) {
                    mergedDetails.custom_answer = customText.trim();
                }
                return {
                    question_key: a.question_key,
                    section: a.section,
                    answer: a.answer,
                    details: Object.keys(mergedDetails).length > 0 ? mergedDetails : null,
                    tool_name: a.tool_name || null,
                    custom_answer: customText?.trim() || null,
                };
            });

        const nevimCount = list.filter((a) => a.answer === "unknown").length;
        const totalDuration = Date.now() - questStartTimeRef.current;
        track("questionnaire_completed", {
            total_answers: list.length,
            nevim_count: nevimCount,
            changes: { ...questionChangeCountRef.current },
        }, totalDuration);

        console.log(`[Dotazník] Počet odpovědí: ${list.length}, company_id: ${companyId}`);

        try {
            const cid = companyId || crypto.randomUUID();
            const res = await fetch(`${API_URL}/api/questionnaire/submit`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    company_id: cid,
                    scan_id: scanId,
                    answers: list,
                }),
            });

            if (!res.ok) {
                const errText = await res.text().catch(() => 'unknown');
                console.error(`[Dotazník] Server error ${res.status}:`, errText);
                throw new Error(`Server vrátil chybu (${res.status})`);
            }

            const data = await res.json();
            console.log('[Dotazník] Úspěšně odesláno:', data);

            // Redirect to dashboard
            router.push("/dashboard");
        } catch (err) {
            console.error('[Dotazník] Chyba při odesílání:', err);
            setSubmitError(err instanceof Error ? err.message : String(err));
            setSubmitting(false);
        }
    }, [submitting, companyId, scanId, router]);

    /* ── Progress ── */
    const progressPct =
        currentQuestion <= 0
            ? 0
            : Math.min(100, Math.round(((currentQuestion + 1) / totalQuestions) * 100));

    /* ── Section transition detection ── */
    const currentQ = allQuestions[currentQuestion];
    const prevQ = currentQuestion > 0 ? allQuestions[currentQuestion - 1] : null;
    const isNewSection = currentQ && prevQ && currentQ._section !== prevQ._section;
    const isFirstQuestion = currentQuestion === 0;

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

    /* ── Submitting overlay — full screen ── */
    if (submitting) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
                <div className="text-center animate-fade-in max-w-lg">
                    <div className="w-20 h-20 border-4 border-fuchsia-500/30 border-t-fuchsia-500 rounded-full animate-spin mx-auto mb-8" />
                    <h2 className="text-2xl font-bold text-white mb-3">Odesílám váš dotazník…</h2>
                    <div className="bg-gradient-to-r from-fuchsia-500/10 to-cyan-500/10 border border-fuchsia-500/20 rounded-2xl p-5 mb-4">
                        <p className="text-base text-white leading-relaxed">
                            👋 Děkuji za váš čas! Vše dáme dohromady — do <strong className="text-fuchsia-300">7 dní</strong> dostanete kompletní dokumentaci v elektronické podobě a do <strong className="text-cyan-300">14 dní</strong> vše v tištěné podobě na vaši adresu.
                        </p>
                        <p className="text-sm text-slate-400 mt-2">— Vaše Uršula</p>
                    </div>
                    <p className="text-slate-500 text-sm">Za moment vás přesměrujeme do klientské zóny.</p>
                </div>
                <style>{`
                    @keyframes fade-in { from { opacity: 0; transform: scale(0.98); } to { opacity: 1; transform: scale(1); } }
                    .animate-fade-in { animation: fade-in 0.4s ease-out; }
                `}</style>
            </div>
        );
    }

    /* ── Submit error screen ── */
    if (submitError) {
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
                <div className="text-center animate-fade-in max-w-md">
                    <div className="w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-6">
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#f87171" strokeWidth="2"><path d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                    </div>
                    <h2 className="text-xl font-bold text-white mb-2">Odeslání se nezdařilo</h2>
                    <p className="text-slate-400 mb-2">Zkuste to prosím znovu.</p>
                    <p className="text-slate-500 text-xs mb-6 font-mono">{submitError}</p>
                    <div className="flex gap-3 justify-center">
                        <button
                            onClick={() => { setSubmitError(null); handleSubmit(); }}
                            className="px-6 py-3 rounded-xl bg-gradient-to-r from-fuchsia-600 to-purple-600 text-white font-semibold transition-all hover:shadow-lg hover:shadow-fuchsia-500/25 active:scale-[0.98]"
                        >
                            Zkusit znovu
                        </button>
                        <button
                            onClick={() => router.push("/dashboard")}
                            className="px-6 py-3 rounded-xl bg-white/[0.06] border border-white/[0.1] text-slate-300 font-medium transition-all hover:bg-white/[0.1]"
                        >
                            Dashboard
                        </button>
                    </div>
                </div>
                <style>{`
                    @keyframes fade-in { from { opacity: 0; transform: scale(0.98); } to { opacity: 1; transform: scale(1); } }
                    .animate-fade-in { animation: fade-in 0.4s ease-out; }
                `}</style>
            </div>
        );
    }

    /* ── Results screen (legacy fallback — should auto-redirect to /dashboard now) ── */
    if (currentQuestion > totalQuestions) {
        // Auto-redirect to dashboard
        router.push("/dashboard");
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center">
                <div className="text-center">
                    <div className="w-12 h-12 border-4 border-fuchsia-500/30 border-t-fuchsia-500 rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-slate-400">Přesměrování do klientské zóny…</p>
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
                        {isEditMode ? (
                            <>
                                Úprava{" "}
                                <span className="bg-gradient-to-r from-fuchsia-400 to-cyan-400 bg-clip-text text-transparent">
                                    vašich odpovědí
                                </span>
                            </>
                        ) : (
                            <>
                                Pojďme zjistit,{" "}
                                <span className="bg-gradient-to-r from-fuchsia-400 to-cyan-400 bg-clip-text text-transparent">
                                    jak na tom jste
                                </span>
                            </>
                        )}
                    </h1>

                    {/* Uršula greeting */}
                    <div className="bg-gradient-to-r from-fuchsia-500/10 to-cyan-500/10 border border-fuchsia-500/20 rounded-2xl p-5 mb-4">
                        <p className="text-lg sm:text-xl font-semibold text-white">
                            👋 Dobrý den, já jsem váš virtuální pomocník <span className="bg-gradient-to-r from-fuchsia-400 to-cyan-400 bg-clip-text text-transparent">Uršula</span> a provedu vás celým procesem.
                        </p>
                    </div>

                    <p className="text-slate-400 text-lg mb-6">
                        {isEditMode
                            ? "Vaše předchozí odpovědi jsou předvyplněné. Projděte otázky a upravte, co potřebujete."
                            : `${totalQuestions} krátkých otázek. Stačí klikat. Hotovo za 5 minut.`
                        }
                    </p>

                    {/* Why questionnaire matters */}
                    {!isEditMode && (
                        <div className="rounded-2xl bg-gradient-to-br from-cyan-500/[0.06] to-fuchsia-500/[0.06] border border-cyan-500/15 p-5 mb-8 text-left max-w-md mx-auto">
                            <div className="flex items-start gap-3">
                                <svg className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                <div>
                                    <p className="text-sm font-semibold text-white mb-1">Proč je dotazník potřeba?</p>
                                    <p className="text-xs text-slate-300 leading-relaxed">
                                        EU AI Act se netýká jen toho, co je vidět na webu. Regulace zahrnuje i <strong className="text-cyan-300">interní AI systémy</strong> — nástroje pro HR,
                                        účetnictví, rozhodování, generování obsahu nebo komunikaci se zaměstnanci.
                                        Automatický sken odhalí jen veřejně viditelné nástroje. Dotazník pokrývá <strong className="text-cyan-300">celou AI politiku firmy</strong>,
                                        včetně toho, co zákazník nikdy neuvidí.
                                    </p>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Feature cards */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-10">
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
                        onClick={() => { setDirection("forward"); setCurrentQuestion(0); questStartTimeRef.current = Date.now(); questionStartTimeRef.current = Date.now(); track("questionnaire_started", { total_questions: totalQuestions }); }}
                        className="w-full sm:w-auto px-12 py-4 rounded-xl bg-gradient-to-r from-fuchsia-600 to-purple-600 text-white font-semibold text-lg transition-all hover:shadow-lg hover:shadow-fuchsia-500/25 active:scale-[0.98]"
                    >
                        Začít →
                    </button>
                </div>
            </div>
        );
    }

    /* ═══════════════════════════════════════════
       SECTION TRANSITION CARD (renders above question when entering new section)
       ═══════════════════════════════════════════ */
    const SectionTransitionCard = () => {
        if (!isNewSection && !isFirstQuestion) return null;
        const sec = currentQ;
        if (!sec) return null;
        const emoji = SECTION_EMOJI[sec._section] || "📋";
        const sectionTitle = sec._sectionTitle || sec._section;
        const sectionQCount = allQuestions.filter(
            (aq) => aq._section === sec._section
        ).length;

        return (
            <div className="mb-6 animate-fade-in">
                <div className="rounded-2xl bg-gradient-to-r from-fuchsia-500/[0.08] to-cyan-500/[0.08] border border-fuchsia-500/20 p-4">
                    <div className="flex items-center gap-3">
                        <span className="text-2xl">{emoji}</span>
                        <div>
                            <p className="text-sm font-bold text-white">{sectionTitle}</p>
                            <p className="text-xs text-slate-400">{sectionQCount} {sectionQCount === 1 ? "otázka" : sectionQCount < 5 ? "otázky" : "otázek"} v této sekci</p>
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    /* ═══════════════════════════════════════════
       RISK WARNING BANNER (renders after answer for prohibited/high-risk)
       ═══════════════════════════════════════════ */
    const PROHIBITED_KEYS = new Set([
        "uses_social_scoring", "uses_subliminal_manipulation",
    ]);
    const LAWYER_KEYS = new Set([
        "develops_own_ai", "modifies_ai_purpose", "uses_ai_for_children",
    ]);
    const HIGH_RISK_KEYS = new Set([
        "uses_ai_recruitment", "uses_ai_employee_monitoring", "uses_emotion_recognition",
        "uses_ai_creditscoring", "uses_ai_insurance", "uses_ai_decision",
        "uses_ai_critical_infra", "uses_ai_education", "uses_realtime_biometric",
    ]);

    const RiskWarningBanner = ({ questionKey, answer }: { questionKey: string; answer: string }) => {
        if (answer !== "yes") return null;

        if (PROHIBITED_KEYS.has(questionKey)) {
            return (
                <div className="animate-slide-down mb-4">
                    <div className="rounded-2xl bg-red-500/[0.12] border-2 border-red-500/40 p-4">
                        <div className="flex items-start gap-3">
                            <span className="text-2xl flex-shrink-0">🚫</span>
                            <div>
                                <p className="text-sm font-bold text-red-300 mb-1">Toto je zakázaná praktika dle AI Act</p>
                                <p className="text-xs text-red-300/80 leading-relaxed">
                                    Článek 5 AI Act tuto praktiku výslovně zakazuje. V tomto případě <strong className="text-white">doporučujeme konzultaci s právníkem</strong> specializovaným na AI regulaci — toto je oblast, kde potřebujete odborné právní posouzení.
                                </p>
                                <p className="text-xs text-red-300/80 mt-2 leading-relaxed">
                                    ⚖️ Připravíme vám <strong className="text-white">kompletní podklady pro právní konzultaci</strong>, aby právník mohl ihned řešit vaši situaci.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            );
        }

        if (LAWYER_KEYS.has(questionKey)) {
            return (
                <div className="animate-slide-down mb-4">
                    <div className="rounded-2xl bg-amber-500/[0.10] border border-amber-500/30 p-4">
                        <div className="flex items-start gap-3">
                            <span className="text-2xl flex-shrink-0">⚖️</span>
                            <div>
                                <p className="text-sm font-bold text-amber-300 mb-1">Doporučujeme právní konzultaci</p>
                                <p className="text-xs text-amber-300/80 leading-relaxed">
                                    Tato oblast může vyžadovat <strong className="text-white">rozšířené právní posouzení</strong> podle AI Act.
                                    Nemusíte se obávat — připravíme vám veškeré podklady a dokumentaci, aby právník měl vše připraveno.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            );
        }

        if (HIGH_RISK_KEYS.has(questionKey)) {
            return (
                <div className="animate-slide-down mb-4">
                    <div className="rounded-2xl bg-cyan-500/[0.06] border border-cyan-500/20 p-4">
                        <div className="flex items-start gap-3">
                            <span className="text-xl flex-shrink-0">🛡️</span>
                            <div>
                                <p className="text-sm font-bold text-cyan-300 mb-1">Vyšší požadavky na dokumentaci</p>
                                <p className="text-xs text-cyan-300/80 leading-relaxed">
                                    Toto spadá do kategorie <strong className="text-white">vysoce rizikových AI systémů</strong>.
                                    <strong className="text-white"> Žádný stres — připravíme vám veškerou potřebnou dokumentaci</strong>, včetně záznamů o transparentnosti a lidském dohledu.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            );
        }

        return null;
    };

    /* ═══════════════════════════════════════════
       COMPLIANCE GAP WARNING ("Ne" = gap)
       ═══════════════════════════════════════════ */
    const COMPLIANCE_GAP_KEYS: Record<string, { problem: string; solution: string }> = {
        has_ai_register: {
            problem: "Registr AI systémů je povinný od 2. srpna 2025 (čl. 49).",
            solution: "Připravíme vám hotový registr AI systémů na míru vaší firmě."
        },
        has_ai_training: {
            problem: "Článek 4 AI Act vyžaduje AI gramotnost zaměstnanců (platnost od 2. 2. 2025).",
            solution: "Dodáme vám školicí materiály a prezentaci pro vaše zaměstnance."
        },
        has_ai_guidelines: {
            problem: "Interní směrnice pro používání AI je základem compliance.",
            solution: "Vytvoříme vám interní směrnici připravenou k podpisu."
        },
        has_incident_plan: {
            problem: "Plán reakce na incidenty je vyžadován pro hlášení problémů.",
            solution: "Připravíme vám šablonu incident plánu včetně kontaktních postupů."
        },
        has_oversight_person: {
            problem: "Lidský dohled nad AI je klíčový požadavek AI Act.",
            solution: "Navrhneme vám proces lidského dohledu přizpůsobený vaší firmě."
        },
        can_override_ai: {
            problem: "Možnost přepsat rozhodnutí AI je povinná u vysoce rizikových systémů (čl. 14).",
            solution: "Připravíme vám dokumentaci override procesu."
        },
        ai_decision_logging: {
            problem: "Logovací povinnost — čl. 26 vyžaduje uchovávání automaticky generovaných protokolů.",
            solution: "Navrhneme vám systém logování a dokumentaci k němu."
        },
    };

    const ComplianceGapBanner = ({ questionKey, answer }: { questionKey: string; answer: string }) => {
        if (answer !== "no" || !COMPLIANCE_GAP_KEYS[questionKey]) return null;
        const gap = COMPLIANCE_GAP_KEYS[questionKey];
        return (
            <div className="animate-slide-down mb-4">
                <div className="rounded-2xl bg-cyan-500/[0.06] border border-cyan-500/20 p-4">
                    <div className="flex items-start gap-3">
                        <span className="text-xl flex-shrink-0">✅</span>
                        <div>
                            <p className="text-sm font-bold text-cyan-300 mb-1">Tohle vyřešíme za vás</p>
                            <p className="text-xs text-slate-300 leading-relaxed">{gap.problem}</p>
                            <p className="text-xs text-cyan-300/90 mt-1.5 leading-relaxed font-medium">
                                📦 {gap.solution}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    /* ── Inline custom answer block — NESMÍ být vnořená komponenta,
       jinak React při každém stisku klávesy unmountuje textarea a klávesnice na iOS/Android mizí ── */

    /* ── AutosaveOnSelect: voláno při výběru odpovědi u yes/no/unknown ── */
    const autosaveOnSelect = (questionKey: string, value: string) => {
        // Volá se ihned při kliknutí na odpověď (dlaždici)
        const qDef = allQuestions.find(aq => aq.key === questionKey);
        if (!qDef || !companyId) return;
        const ans = answersRef.current[questionKey];
        if (!ans) return;
        const customText = customAnswers[questionKey];
        const mergedDetails = { ...(ans.details || {}) };
        if (customText && customText.trim()) {
            mergedDetails.custom_answer = customText.trim();
        }
        saveToServer(
            questionKey,
            ans.section || qDef._section,
            value,
            mergedDetails,
            ans.tool_name,
            currentQuestion,
            customText,
        );
    };

    /* ═══════════════════════════════════════════
       QUESTION SCREENS (0..N)
       ═══════════════════════════════════════════ */

    const q = allQuestions[currentQuestion];
    if (!q) {
        // Safety: should never happen, but if question index is out of bounds,
        // show the welcome screen instead of a black screen
        return (
            <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
                <div className="text-center">
                    <div className="w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-6">
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#f87171" strokeWidth="2"><path d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                    </div>
                    <h2 className="text-xl font-bold text-white mb-2">Něco se pokazilo</h2>
                    <p className="text-slate-400 mb-6">Dotazník se nepodařilo správně načíst.</p>
                    <div className="flex gap-3 justify-center">
                        <button
                            onClick={() => setCurrentQuestion(-1)}
                            className="px-6 py-3 rounded-xl bg-white/[0.06] border border-white/[0.1] text-slate-300 font-medium transition-all hover:bg-white/[0.1]"
                        >
                            Zkusit znovu
                        </button>
                        <a href="/dashboard" className="px-6 py-3 rounded-xl bg-gradient-to-r from-fuchsia-600 to-purple-600 text-white font-semibold">
                            Zpět na dashboard
                        </a>
                    </div>
                </div>
            </div>
        );
    }

    const ans = answers[q.key];
    const isLast = currentQuestion === totalQuestions - 1;
    const isNA = ans?.answer === "not_applicable";
    const showFollowup = !isNA && q.followup && (
        (q.followup.condition === "any" && !!ans?.answer) ||
        (q.followup.condition === "yes" && ans?.answer === "yes") ||
        (q.followup.condition === "unknown" && ans?.answer === "unknown") ||
        (q.followup.condition === "no" && ans?.answer === "no")
    );

    /* ── Multi-select grid (industry, etc.) ── */
    if ((q.type === "multi_select" || q.type === "single_select") && q.options) {
        const isMulti = q.type === "multi_select";
        const mkey = `topLevel__${q.key}`;
        const selectedItems = isMulti ? (multiSelections[mkey] || []) : [];

        return (
            <div className="min-h-screen bg-slate-950 flex flex-col">
                {/* Progress bar */}
                <ProgressBarUI current={currentQuestion} total={totalQuestions} />

                <div className="flex-1 flex items-center justify-center p-4 pt-16">
                    <div className={`w-full max-w-2xl animate-slide-${direction === "forward" ? "in" : "in-back"}`}>
                        <SectionTransitionCard />
                        <h2 className="text-2xl sm:text-3xl font-bold text-white mb-2 text-center">
                            {q.text}
                        </h2>

                        {/* Help text */}
                        {q.help_text && (
                            <div className="text-slate-400 text-sm mb-6 text-center whitespace-pre-line">
                                {q.help_text}
                            </div>
                        )}
                        {!q.help_text && isMulti && (
                            <p className="text-slate-500 text-sm mb-6 text-center">
                                Můžete zvolit více možností
                            </p>
                        )}
                        {!q.help_text && !isMulti && <div className="mb-6" />}

                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                            {q.options.map((opt) => {
                                const selected = isMulti
                                    ? selectedItems.includes(opt)
                                    : ans?.answer === opt;
                                return (
                                    <button
                                        key={opt}
                                        onClick={() => {
                                            if (isMulti) {
                                                // Toggle multi-select
                                                setMultiSelections((prev) => {
                                                    const current = prev[mkey] || [];
                                                    const next = current.includes(opt)
                                                        ? current.filter((v) => v !== opt)
                                                        : [...current, opt];
                                                    // Store as comma-separated in answer for submission
                                                    setAnswer(q.key, next.join(", "));
                                                    return { ...prev, [mkey]: next };
                                                });
                                            } else {
                                                setAnswer(q.key, opt);
                                            }
                                        }}
                                        className={`touch-bubble
                      p-4 rounded-2xl border text-left transition-[background-color,border-color,color,box-shadow] duration-150
                      ${selected
                                                ? "bg-fuchsia-500/20 border-fuchsia-500/50 text-fuchsia-300 shadow-lg shadow-fuchsia-500/10"
                                                : "bg-white/[0.04] border-white/[0.08] text-slate-300 hover:bg-white/[0.08] hover:border-white/[0.15]"
                                            }
                    `}
                                    >
                                        <span className="block mb-2 text-slate-400">
                                            {INDUSTRY_SVG[opt] || (
                                                <svg className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" /></svg>
                                            )}
                                        </span>
                                        <span className="text-sm font-medium leading-tight block">{opt}</span>
                                    </button>
                                );
                            })}
                        </div>

                        {/* "Jiné" text input for top-level multi_select */}
                        {isMulti && selectedItems.includes("Jiné") && (
                            <div className="mt-4">
                                <input
                                    type="text"
                                    placeholder="Upřesněte vaše odvětví…"
                                    className="w-full bg-white/[0.04] border border-white/[0.1] rounded-xl px-4 py-3 text-white text-base outline-none focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/25 transition-all placeholder:text-slate-500"
                                    value={(ans?.details[`${q.key}_other`] as string) || ""}
                                    onChange={(e) => setDetail(q.key, `${q.key}_other`, e.target.value)}
                                />
                            </div>
                        )}

                        {/* Vlastní odpověď — inline, ne jako vnořená komponenta (jinak iOS klávesnice mizí) */}
                        {!["text", "address", "conditional_fields"].includes(q.type) && (
                            <div className="mt-5 mb-2">
                                <div className="rounded-2xl border-2 border-dashed border-fuchsia-500/30 bg-white/[0.06] p-4 transition-all duration-200 hover:border-fuchsia-500/50 hover:bg-white/[0.08] focus-within:border-fuchsia-500/60 focus-within:bg-white/[0.08] focus-within:ring-2 focus-within:ring-fuchsia-500/25 focus-within:shadow-lg focus-within:shadow-fuchsia-500/5">
                                    <label className="flex items-center gap-2 text-sm font-semibold text-fuchsia-300/90 mb-2">
                                        <svg className="w-4 h-4 text-fuchsia-400" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" /></svg>
                                        Vlastní odpověď
                                    </label>
                                    <textarea
                                        placeholder="Zde napište vlastní odpověď, pokud jste v možnostech nenašli přiléhavou volbu…"
                                        className="w-full bg-white/[0.04] border border-white/[0.1] rounded-xl px-3 py-2.5 text-white text-base outline-none transition-all placeholder:text-slate-400 resize-none min-h-[56px] max-h-[120px] focus:border-fuchsia-500/40 focus:ring-1 focus:ring-fuchsia-500/20"
                                        rows={2}
                                        maxLength={2000}
                                        value={customAnswers[q.key] || ""}
                                        onChange={(e) => setCustomAnswers(prev => ({ ...prev, [q.key]: e.target.value }))}
                                    />
                                </div>
                                {customAnswers[q.key] && customAnswers[q.key].trim() && (
                                    <p className="text-xs text-fuchsia-400/70 mt-2 ml-1">
                                        ✓ Vaše odpověď bude zohledněna ({customAnswers[q.key].length}/2000 znaků)
                                    </p>
                                )}
                            </div>
                        )}

                        {/* Navigation */}
                        <div className="flex justify-between mt-8">
                            <button
                                onClick={goBack}
                                className="px-6 py-3 rounded-xl bg-white/[0.06] border border-white/[0.1] text-slate-400 font-medium transition-all hover:bg-white/[0.1]"
                            >
                                ← Zpět
                            </button>
                            {isLast ? (
                                (isMulti ? selectedItems.length > 0 : !!ans?.answer) && (
                                    <button
                                        onClick={handleSubmit}
                                        disabled={submitting}
                                        className="px-8 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-emerald-500 text-white font-semibold transition-all hover:shadow-lg hover:shadow-cyan-500/25 active:scale-[0.98] disabled:opacity-50 animate-pulse"
                                    >
                                        {submitting ? "Odesílám…" : "🚀 Odeslat dotazník"}
                                    </button>
                                )
                            ) : (isMulti ? selectedItems.length > 0 : !!ans?.answer) && (
                                <button
                                    onClick={goNext}
                                    className="px-8 py-3 rounded-xl bg-gradient-to-r from-fuchsia-600 to-purple-600 text-white font-semibold transition-all hover:shadow-lg hover:shadow-fuchsia-500/25 active:scale-[0.98]"
                                >
                                    Další →
                                </button>
                            )}
                        </div>

                        {/* Save & Continue Later */}
                        <SaveLaterButton answers={answers} currentQuestion={currentQuestion} companyId={companyId} />
                    </div>
                </div>
            </div>
        );
    }

    /* ── Conditional fields question (contact form etc.) ── */
    if (q.type === "conditional_fields" && (q as any).fields) {
        const cFields = (q as any).fields as FollowupField[];
        const allRequiredFilled = cFields
            .filter((f: any) => f.required && f.type !== "info")
            .every((f: any) => {
                const val = ans?.details?.[f.key];
                return val && String(val).trim() !== "";
            });
        return (
            <div className="min-h-screen bg-slate-950 flex flex-col">
                <ProgressBarUI current={currentQuestion} total={totalQuestions} />

                <div className="fixed top-[-200px] right-[-100px] w-[400px] h-[400px] bg-fuchsia-600/10 rounded-full blur-[120px] pointer-events-none" />
                <div className="fixed bottom-[-150px] left-[-80px] w-[350px] h-[350px] bg-cyan-500/8 rounded-full blur-[100px] pointer-events-none" />

                <div className="flex-1 flex items-center justify-center p-4 pt-16">
                    <div className={`w-full max-w-xl animate-slide-${direction === "forward" ? "in" : "in-back"}`}>

                        <SectionTransitionCard />
                        <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3 leading-snug">
                            {q.text}
                        </h2>

                        {q.help_text && (
                            <div className="text-slate-400 text-sm mb-6 flex items-start gap-2">
                                <span className="text-slate-500 mt-0.5 flex-shrink-0">ℹ️</span>
                                <span className="whitespace-pre-line">{q.help_text}</span>
                            </div>
                        )}

                        {/* Form fields */}
                        <div className="space-y-4 mb-6">
                            {cFields.map((field) => {
                                if (field.type === "info") {
                                    return (
                                        <div key={field.key} className="rounded-xl border border-cyan-500/20 bg-cyan-500/[0.04] px-4 py-3">
                                            <p className="text-sm text-cyan-200 leading-relaxed">{renderWarningText(field.label)}</p>
                                        </div>
                                    );
                                }
                                return (
                                    <div key={field.key}>
                                        <label className="block text-sm font-medium text-slate-300 mb-1.5">
                                            {field.label}
                                            {(field as any).required && <span className="text-fuchsia-400 ml-1">*</span>}
                                        </label>
                                        <input
                                            type={
                                                field.key.includes("email") ? "email" :
                                                    field.key.includes("phone") || field.key.includes("telefon") ? "tel" : "text"
                                            }
                                            placeholder={
                                                field.key.includes("email") ? "Např. technik@firma.cz" :
                                                    field.key.includes("phone") || field.key.includes("telefon") ? "Např. +420 123 456 789" :
                                                        field.key.includes("name") || field.key.includes("jméno") ? "Např. Jan Novák" :
                                                            "Napište…"
                                            }
                                            className="w-full bg-white/[0.04] border-2 border-white/[0.1] rounded-2xl px-5 py-4 text-white text-lg outline-none focus:border-fuchsia-500/50 focus:ring-2 focus:ring-fuchsia-500/25 transition-all placeholder:text-slate-600"
                                            value={String(ans?.details?.[field.key] || "")}
                                            onChange={(e) => {
                                                setDetail(q.key, field.key, e.target.value);
                                                // Mark the question as answered when has content
                                                if (e.target.value.trim()) {
                                                    setAnswer(q.key, "filled");
                                                }
                                            }}
                                        />
                                    </div>
                                );
                            })}
                        </div>

                        {/* Navigation */}
                        <div className="flex justify-between items-center">
                            <button
                                onClick={goBack}
                                className="px-4 sm:px-6 py-3 rounded-xl bg-white/[0.06] border border-white/[0.1] text-slate-400 font-medium transition-all hover:bg-white/[0.1] text-sm sm:text-base"
                            >
                                ← Zpět
                            </button>

                            {fromDashboard && allRequiredFilled ? (
                                <button
                                    onClick={handleSubmit}
                                    disabled={submitting}
                                    className="px-5 sm:px-8 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-emerald-500 text-white font-semibold text-sm sm:text-base transition-all hover:shadow-lg hover:shadow-cyan-500/25 active:scale-[0.98] disabled:opacity-50"
                                >
                                    {submitting ? "Ukládám…" : "✓ Uložit a zpět"}
                                </button>
                            ) : isLast ? (
                                <button
                                    onClick={handleSubmit}
                                    disabled={submitting || !allRequiredFilled}
                                    className="px-5 sm:px-8 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-emerald-500 text-white font-semibold text-sm sm:text-lg transition-all hover:shadow-lg hover:shadow-cyan-500/25 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-cyan-500/20"
                                >
                                    {submitting ? "Odesílám…" : "✅ Ukončit a odeslat dotazník"}
                                </button>
                            ) : allRequiredFilled ? (
                                <button
                                    onClick={goNext}
                                    className="px-8 py-3 rounded-xl bg-gradient-to-r from-fuchsia-600 to-purple-600 text-white font-semibold transition-all hover:shadow-lg hover:shadow-fuchsia-500/25 active:scale-[0.98]"
                                >
                                    Další →
                                </button>
                            ) : null}
                        </div>

                        <SaveLaterButton answers={answers} currentQuestion={currentQuestion} companyId={companyId} />
                    </div>
                </div>
            </div>
        );
    }

    /* ── Address composite field (street, house number, city, zip) ── */
    if (q.type === "address" || (q.type === "text" && q.key === "company_address")) {
        // Parse existing answer into parts (supports ARES auto-fill as fallback)
        const parts = (ans?.answer || "").split(" || ");
        const hasStructured = parts.length === 4;
        const addrStreet = hasStructured ? parts[0] : (ans?.answer || "");
        const addrHouseNum = hasStructured ? parts[1] : "";
        const addrCity = hasStructured ? parts[2] : "";
        const addrZip = hasStructured ? parts[3] : "";

        const composeAddress = (street: string, house: string, city: string, zip: string) => {
            // Store as structured " || " delimited for parsing, but display-ready
            return `${street} || ${house} || ${city} || ${zip}`;
        };

        return (
            <div className="min-h-screen bg-slate-950 flex flex-col">
                <ProgressBarUI current={currentQuestion} total={totalQuestions} />

                <div className="fixed top-[-200px] right-[-100px] w-[400px] h-[400px] bg-fuchsia-600/10 rounded-full blur-[120px] pointer-events-none" />
                <div className="fixed bottom-[-150px] left-[-80px] w-[350px] h-[350px] bg-cyan-500/8 rounded-full blur-[100px] pointer-events-none" />

                <div className="flex-1 flex items-center justify-center p-4 pt-16">
                    <div className={`w-full max-w-xl animate-slide-${direction === "forward" ? "in" : "in-back"}`}>

                        <SectionTransitionCard />
                        <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3 leading-snug">
                            {q.text}
                        </h2>

                        {q.help_text && (
                            <div className="text-slate-400 text-sm mb-6 flex items-start gap-2">
                                <span className="text-slate-500 mt-0.5 flex-shrink-0">ℹ️</span>
                                <span className="whitespace-pre-line">{q.help_text}</span>
                            </div>
                        )}
                        {!q.help_text && <div className="mb-6" />}

                        <div className="space-y-4">
                            <div>
                                <label className="text-xs text-slate-400 mb-1.5 block font-medium">Ulice</label>
                                <input
                                    type="text"
                                    placeholder="Např. Václavské náměstí"
                                    className="w-full bg-white/[0.04] border-2 border-white/[0.1] rounded-2xl px-5 py-3.5 text-white text-lg outline-none focus:border-fuchsia-500/50 focus:ring-2 focus:ring-fuchsia-500/25 transition-all placeholder:text-slate-600"
                                    value={addrStreet}
                                    onChange={(e) => setAnswer(q.key, composeAddress(e.target.value, addrHouseNum, addrCity, addrZip))}
                                    autoFocus
                                />
                            </div>
                            <div>
                                <label className="text-xs text-slate-400 mb-1.5 block font-medium">Číslo popisné</label>
                                <input
                                    type="text"
                                    placeholder="Např. 837/1"
                                    className="w-full bg-white/[0.04] border-2 border-white/[0.1] rounded-2xl px-5 py-3.5 text-white text-lg outline-none focus:border-fuchsia-500/50 focus:ring-2 focus:ring-fuchsia-500/25 transition-all placeholder:text-slate-600"
                                    value={addrHouseNum}
                                    onChange={(e) => setAnswer(q.key, composeAddress(addrStreet, e.target.value, addrCity, addrZip))}
                                />
                            </div>
                            <div className="grid grid-cols-1 xs:grid-cols-2 gap-4">
                                <div>
                                    <label className="text-xs text-slate-400 mb-1.5 block font-medium">Město</label>
                                    <input
                                        type="text"
                                        placeholder="Např. Praha 1"
                                        className="w-full bg-white/[0.04] border-2 border-white/[0.1] rounded-2xl px-5 py-3.5 text-white text-lg outline-none focus:border-fuchsia-500/50 focus:ring-2 focus:ring-fuchsia-500/25 transition-all placeholder:text-slate-600"
                                        value={addrCity}
                                        onChange={(e) => setAnswer(q.key, composeAddress(addrStreet, addrHouseNum, e.target.value, addrZip))}
                                    />
                                </div>
                                <div>
                                    <label className="text-xs text-slate-400 mb-1.5 block font-medium">PSČ</label>
                                    <input
                                        type="text"
                                        placeholder="Např. 110 00"
                                        className="w-full bg-white/[0.04] border-2 border-white/[0.1] rounded-2xl px-5 py-3.5 text-white text-lg outline-none focus:border-fuchsia-500/50 focus:ring-2 focus:ring-fuchsia-500/25 transition-all placeholder:text-slate-600"
                                        value={addrZip}
                                        onChange={(e) => setAnswer(q.key, composeAddress(addrStreet, addrHouseNum, addrCity, e.target.value))}
                                    />
                                </div>
                            </div>
                        </div>

                        {/* AI Act reference pill */}
                        {q.ai_act_article && (
                            <div className="mt-4">
                                <span className="inline-flex items-center gap-1.5 bg-fuchsia-500/10 border border-fuchsia-500/20 rounded-lg px-3 py-1.5 text-xs text-fuchsia-300">
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
                                    {q.ai_act_article}
                                </span>
                            </div>
                        )}

                        {/* Navigation */}
                        <div className="flex justify-between mt-8">
                            <button
                                onClick={goBack}
                                className="px-6 py-3 rounded-xl bg-white/[0.06] border border-white/[0.1] text-slate-400 font-medium transition-all hover:bg-white/[0.1]"
                            >
                                ← Zpět
                            </button>
                            {(() => {
                                const allFilled = addrStreet.trim() && addrHouseNum.trim() && addrCity.trim() && addrZip.trim();
                                if (isLast) {
                                    return (
                                        <button
                                            onClick={handleSubmit}
                                            disabled={submitting || !allFilled}
                                            className={`px-8 py-3 rounded-xl font-semibold transition-all active:scale-[0.98] ${allFilled ? "bg-gradient-to-r from-cyan-500 to-emerald-500 text-white hover:shadow-lg hover:shadow-cyan-500/25 animate-pulse" : "bg-white/[0.06] border border-white/[0.1] text-slate-500 cursor-not-allowed"}`}
                                        >
                                            {submitting ? "Odesílám…" : "🚀 Odeslat dotazník"}
                                        </button>
                                    );
                                }
                                return (
                                    <button
                                        onClick={goNext}
                                        disabled={!allFilled}
                                        className={`px-8 py-3 rounded-xl font-semibold transition-all active:scale-[0.98] ${allFilled ? "bg-gradient-to-r from-fuchsia-600 to-purple-600 text-white hover:shadow-lg hover:shadow-fuchsia-500/25" : "bg-white/[0.06] border border-white/[0.1] text-slate-500 cursor-not-allowed"}`}
                                    >
                                        Další →
                                    </button>
                                );
                            })()}
                        </div>
                        <SaveLaterButton answers={answers} currentQuestion={currentQuestion} companyId={companyId} />
                    </div>
                </div>
            </div>
        );
    }

    /* ── Text input question (company name, IČO, email etc.) ── */
    if (q.type === "text") {
        return (
            <div className="min-h-screen bg-slate-950 flex flex-col">
                <ProgressBarUI current={currentQuestion} total={totalQuestions} />

                <div className="fixed top-[-200px] right-[-100px] w-[400px] h-[400px] bg-fuchsia-600/10 rounded-full blur-[120px] pointer-events-none" />
                <div className="fixed bottom-[-150px] left-[-80px] w-[350px] h-[350px] bg-cyan-500/8 rounded-full blur-[100px] pointer-events-none" />

                <div className="flex-1 flex items-center justify-center p-4 pt-16">
                    <div className={`w-full max-w-xl animate-slide-${direction === "forward" ? "in" : "in-back"}`}>

                        <SectionTransitionCard />
                        <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3 leading-snug">
                            {q.text}
                        </h2>

                        {q.help_text && (
                            <div className="text-slate-400 text-sm mb-6 flex items-start gap-2">
                                <span className="text-slate-500 mt-0.5 flex-shrink-0">ℹ️</span>
                                <span className="whitespace-pre-line">{q.help_text}</span>
                            </div>
                        )}
                        {!q.help_text && <div className="mb-6" />}

                        <input
                            type={q.key === "company_contact_email" ? "email" : q.key === "company_phone" ? "tel" : "text"}
                            placeholder={
                                q.key === "company_legal_name" ? "Např. ACME Solutions s.r.o." :
                                    q.key === "company_ico" ? "Např. 12345678" :
                                        q.key === "company_address" ? "Např. Václavské nám. 1, Praha 1" :
                                            q.key === "company_contact_email" ? "Např. ai@firma.cz" :
                                                q.key === "company_phone" ? "Např. +420 123 456 789" :
                                                    "Napište…"
                            }
                            className="w-full bg-white/[0.04] border-2 border-white/[0.1] rounded-2xl px-5 py-4 text-white text-lg outline-none focus:border-fuchsia-500/50 focus:ring-2 focus:ring-fuchsia-500/25 transition-all placeholder:text-slate-600"
                            value={ans?.answer || ""}
                            onChange={(e) => setAnswer(q.key, e.target.value)}
                            autoFocus
                        />

                        {/* AI Act reference pill */}
                        {q.ai_act_article && (
                            <div className="mt-4">
                                <span className="inline-flex items-center gap-1.5 bg-fuchsia-500/10 border border-fuchsia-500/20 rounded-lg px-3 py-1.5 text-xs text-fuchsia-300">
                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
                                    {q.ai_act_article}
                                </span>
                            </div>
                        )}

                        {/* Navigation */}
                        <div className="flex justify-between mt-8">
                            <button
                                onClick={goBack}
                                className="px-6 py-3 rounded-xl bg-white/[0.06] border border-white/[0.1] text-slate-400 font-medium transition-all hover:bg-white/[0.1]"
                            >
                                ← Zpět
                            </button>
                            {ans?.answer?.trim() ? (
                                isLast ? (
                                    <button
                                        onClick={handleSubmit}
                                        disabled={submitting}
                                        className="px-8 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-emerald-500 text-white font-semibold transition-all hover:shadow-lg hover:shadow-cyan-500/25 active:scale-[0.98] disabled:opacity-50 animate-pulse"
                                    >
                                        {submitting ? "Odesílám…" : "🚀 Odeslat dotazník"}
                                    </button>
                                ) : (
                                    <button
                                        onClick={goNext}
                                        className="px-8 py-3 rounded-xl bg-gradient-to-r from-fuchsia-600 to-purple-600 text-white font-semibold transition-all hover:shadow-lg hover:shadow-fuchsia-500/25 active:scale-[0.98]"
                                    >
                                        Další →
                                    </button>
                                )
                            ) : null}
                        </div>

                        <SaveLaterButton answers={answers} currentQuestion={currentQuestion} companyId={companyId} />
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

                    {/* Section transition card */}
                    <SectionTransitionCard />

                    {/* Question text */}
                    <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3 leading-snug">
                        {q.text}
                    </h2>

                    {/* Scope hint — who is this question for */}
                    {(q as any).scope_hint && (
                        <div className="rounded-xl border border-amber-500/20 bg-amber-500/[0.06] px-4 py-3 mb-4 flex items-start gap-2">
                            <span className="text-amber-400 mt-0.5 flex-shrink-0 text-sm">👤</span>
                            <p className="text-xs text-amber-300/90 leading-relaxed">{(q as any).scope_hint}</p>
                        </div>
                    )}

                    {/* Help text */}
                    {q.help_text && (
                        <div className="text-slate-400 text-sm mb-4 flex items-start gap-2">
                            <span className="text-slate-500 mt-0.5 flex-shrink-0">ℹ️</span>
                            <span className="whitespace-pre-line">{q.help_text}</span>
                        </div>
                    )}
                    {!q.help_text && !(q as any).scope_hint && <div className="mb-4" />}

                    {/* Answer tiles */}
                    <div className={`grid ${q.type === "yes_unknown" ? "grid-cols-3" : "grid-cols-2 sm:grid-cols-4"} gap-3 mb-4`}>
                        {([
                            { value: "yes", label: "Ano", icon: "✓" },
                            ...(q.type !== "yes_unknown" ? [{ value: "no" as const, label: "Ne", icon: "✕" }] : []),
                            { value: "unknown", label: "Nevím", icon: "?" },
                            { value: "not_applicable", label: "Netýká se mě", icon: "—" },
                        ] as const).map((opt) => {
                            const selected = ans?.answer === opt.value;
                            return (
                                <button
                                    key={opt.value}
                                    onClick={() => {
                                        setAnswer(q.key, opt.value);
                                        autosaveOnSelect(q.key, opt.value);
                                        if (fromDashboard) {
                                            // Came from dashboard for specific question — submit this answer and go back
                                            if (q.followup && q.followup.condition === opt.value) {
                                                // Followup triggered — let user fill it, they'll use the "Zpět" button
                                            } else if (q.followup && q.followup.condition === "any") {
                                                // Followup always shows — let user fill it, they'll use the "Zpět" button
                                            } else if (q.followup_no && opt.value === "no") {
                                                // followup_no triggered — show warning, they'll use the "Zpět" button
                                            } else if (q.followup_yes && opt.value === "yes") {
                                                // followup_yes triggered — show fields, they'll use the "Zpět" button
                                            } else {
                                                // No followup — auto-submit and return to dashboard
                                                setTimeout(() => { handleSubmit(); }, 400);
                                            }
                                        }
                                        // Normal flow: NEVER auto-advance.
                                        // User must always click "Další →" or "Ukončit" button.

                                        // Auto-scroll k followup pod-možnostem na mobilu
                                        const willShowFollowup =
                                            (q.followup && (q.followup.condition === opt.value || q.followup.condition === "any")) ||
                                            (q.followup_no && opt.value === "no") ||
                                            (q.followup_yes && opt.value === "yes");
                                        if (willShowFollowup) {
                                            setTimeout(() => {
                                                followupRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
                                            }, 400);
                                        } else {
                                            // Scroll k tlačítku "Další" aby klient věděl jak pokračovat
                                            setTimeout(() => {
                                                navRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
                                            }, 300);
                                        }
                                    }}
                                    className={`touch-bubble
                    relative py-5 px-4 rounded-2xl border text-center transition-[background-color,border-color,color,box-shadow,ring-color] duration-150 cursor-pointer
                    ${selected
                                            ? "bg-fuchsia-500/20 border-fuchsia-500/50 text-fuchsia-300 shadow-lg shadow-fuchsia-500/10 ring-2 ring-offset-2 ring-offset-slate-950 ring-fuchsia-500/60"
                                            : "bg-white/[0.04] border-white/[0.08] text-slate-300 hover:bg-white/[0.08] hover:border-white/[0.15]"
                                        }
                  `}
                                >
                                    <span className="text-2xl block mb-1">{opt.icon}</span>
                                    <span className="font-semibold block text-base">{opt.label}</span>
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
                        <div ref={followupRef} className="animate-slide-down mb-6">
                            <div className="bg-white/[0.04] backdrop-blur-xl rounded-2xl p-5">
                                <p className="text-cyan-300 text-sm font-semibold mb-4">Upřesněte prosím:</p>
                                <div className="space-y-4">
                                    {q.followup.fields.map((field) => (
                                        <div key={field.key}>
                                            {/* Info type → informational text */}
                                            {field.type === "info" ? (
                                                <div className={`flex items-start gap-2 rounded-xl px-4 py-3 ${field.label.startsWith("🚫")
                                                    ? "bg-red-500/[0.12] border-2 border-red-500/40"
                                                    : field.label.startsWith("⚠️")
                                                        ? "bg-amber-500/[0.08] border border-amber-500/25"
                                                        : "bg-cyan-500/[0.06] border border-cyan-500/15"
                                                    }`}>
                                                    {field.label.startsWith("🚫") ? (
                                                        <span className="text-red-400 text-lg mt-0.5 flex-shrink-0">🚫</span>
                                                    ) : field.label.startsWith("⚠️") ? (
                                                        <span className="text-amber-400 text-lg mt-0.5 flex-shrink-0">⚠️</span>
                                                    ) : (
                                                        <svg className="w-4 h-4 text-cyan-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                                        </svg>
                                                    )}
                                                    <p className={`text-xs leading-relaxed ${field.label.startsWith("🚫") ? "text-red-300 font-semibold"
                                                        : field.label.startsWith("⚠️") ? "text-amber-200"
                                                            : "text-slate-400"
                                                        }`}>{renderWarningText(field.label.replace(/^[🚫⚠️ℹ️✅📦]+\s*/, ''))}</p>
                                                </div>
                                            ) : (
                                                <label className="block text-slate-400 text-sm mb-2 font-medium">
                                                    {field.label}
                                                </label>
                                            )}

                                            {/* Select → tile grid */}
                                            {field.type === "select" && field.options && (
                                                <>
                                                    <div className="flex flex-wrap gap-2">
                                                        {field.options.map((opt) => {
                                                            const selected = (ans?.details[field.key] as string) === opt;
                                                            return (
                                                                <button
                                                                    key={opt}
                                                                    onClick={() => setDetail(q.key, field.key, opt)}
                                                                    className={`touch-bubble
                                      px-4 py-2.5 rounded-xl border text-sm font-medium transition-[background-color,border-color,color] duration-150
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
                                                    {/* "Jiný" text input */}
                                                    {((ans?.details[field.key] as string) === "Jiný" || (ans?.details[field.key] as string) === "Jiné") && (
                                                        <input
                                                            type="text"
                                                            placeholder="Upřesněte…"
                                                            className="mt-2 w-full bg-white/[0.04] border border-white/[0.1] rounded-xl px-4 py-3 text-white text-base outline-none focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/25 transition-all placeholder:text-slate-500"
                                                            value={(ans?.details[`${field.key}_other`] as string) || ""}
                                                            onChange={(e) => setDetail(q.key, `${field.key}_other`, e.target.value)}
                                                            autoFocus
                                                        />
                                                    )}
                                                    {/* Warning banner */}
                                                    {field.warning && ans?.details[field.key] && (field.warning as Record<string, string>)[ans.details[field.key] as string] && (
                                                        <div className="mt-2 flex items-start gap-2 rounded-xl bg-red-500/[0.08] border border-red-500/20 px-4 py-3">
                                                            <span className="text-red-400 flex-shrink-0 mt-0.5">⚠️</span>
                                                            <div>
                                                                <p className="text-xs text-red-300 leading-relaxed">{renderWarningText((field.warning as Record<string, string>)[ans.details[field.key] as string])}</p>
                                                            </div>
                                                        </div>
                                                    )}
                                                </>
                                            )}

                                            {/* Multi-select → tile grid with checkmarks */}
                                            {field.type === "multi_select" && field.options && (
                                                <>
                                                    <div className="flex flex-wrap gap-2">
                                                        {field.options.map((opt) => {
                                                            const mkey = `${q.key}__${field.key}`;
                                                            const selected = (multiSelections[mkey] || []).includes(opt);
                                                            return (
                                                                <button
                                                                    key={opt}
                                                                    onClick={() => toggleMulti(q.key, field.key, opt)}
                                                                    className={`touch-bubble
                                      px-4 py-2.5 rounded-xl border text-sm font-medium transition-[background-color,border-color,color] duration-150 flex items-center gap-2
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
                                                    {/* "Jiné"/"Jiný" text input */}
                                                    {((multiSelections[`${q.key}__${field.key}`] || []).includes("Jiné") || (multiSelections[`${q.key}__${field.key}`] || []).includes("Jiný")) && (
                                                        <input
                                                            type="text"
                                                            placeholder="Upřesněte…"
                                                            className="mt-2 w-full bg-white/[0.04] border border-white/[0.1] rounded-xl px-4 py-3 text-white text-base outline-none focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/25 transition-all placeholder:text-slate-500"
                                                            value={(ans?.details[`${field.key}_other`] as string) || ""}
                                                            onChange={(e) => setDetail(q.key, `${field.key}_other`, e.target.value)}
                                                            autoFocus
                                                        />
                                                    )}
                                                    {/* Warning banners for multi_select — each selected warning as separate card */}
                                                    {field.warning && (() => {
                                                        const sel = multiSelections[`${q.key}__${field.key}`] || [];
                                                        const w = field.warning as Record<string, string>;
                                                        const entries = sel.map(s => ({ key: s, text: w[s] })).filter(e => e.text);
                                                        return entries.length > 0 ? (
                                                            <div className="mt-3 space-y-2">
                                                                {entries.map((entry) => (
                                                                    <div key={entry.key} className="flex items-start gap-3 rounded-xl bg-amber-500/[0.07] border border-amber-500/20 px-4 py-3 animate-slide-down">
                                                                        <span className="text-amber-400 flex-shrink-0 mt-0.5 text-base">⚠️</span>
                                                                        <div>
                                                                            <p className="text-[11px] font-semibold text-amber-300/90 mb-0.5">{entry.key}</p>
                                                                            <p className="text-xs text-amber-200/80 leading-relaxed">{renderWarningText(entry.text.replace(/^⚠️\s*/, ''))}</p>
                                                                        </div>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        ) : null;
                                                    })()}
                                                </>
                                            )}

                                            {/* Text → minimal input (fallback) */}
                                            {field.type === "text" && (
                                                <input
                                                    type={field.key.includes("phone") || field.key.includes("telefon") ? "tel" : field.key.includes("email") ? "email" : "text"}
                                                    placeholder={field.key.includes("phone") || field.key.includes("telefon") ? "+420…" : field.key.includes("email") ? "email@firma.cz" : "Napište…"}
                                                    className="w-full bg-white/[0.04] border border-white/[0.1] rounded-xl px-4 py-3 text-white text-base outline-none focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/25 transition-all placeholder:text-slate-500"
                                                    value={(ans?.details[field.key] as string) || ""}
                                                    onChange={(e) => setDetail(q.key, field.key, e.target.value)}
                                                />
                                            )}

                                            {/* Single select → tile grid (one choice) */}
                                            {field.type === "single_select" && field.options && (
                                                <>
                                                    {field.label && (
                                                        <label className="block text-slate-400 text-sm mb-2 font-medium">
                                                            {field.label}
                                                        </label>
                                                    )}
                                                    <div className="flex flex-wrap gap-2">
                                                        {field.options.map((opt) => {
                                                            const selected = (ans?.details[field.key] as string) === opt;
                                                            return (
                                                                <button
                                                                    key={opt}
                                                                    onClick={() => setDetail(q.key, field.key, opt)}
                                                                    className={`touch-bubble
                                      px-4 py-2.5 rounded-xl border text-sm font-medium transition-[background-color,border-color,color] duration-150
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
                                                </>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ── Followup_no fields (slides down when "Ne") ── */}
                    {q.followup_no && ans?.answer === "no" && (
                        <div ref={followupRef} className="animate-slide-down mb-6">
                            <div className="bg-red-500/[0.06] backdrop-blur-xl rounded-2xl p-5">
                                <div className="space-y-4">
                                    {q.followup_no.fields.map((field) => (
                                        <div key={field.key}>
                                            {/* Info → warning banner */}
                                            {field.type === "info" && (
                                                <div className="flex items-start gap-2 rounded-xl bg-red-500/[0.08] border border-red-500/20 px-4 py-3">
                                                    <span className="text-red-400 text-lg mt-0.5 flex-shrink-0">⚠️</span>
                                                    <p className="text-xs text-red-300 leading-relaxed">{renderWarningText(field.label.replace(/^⚠️\s*/, ''))}</p>
                                                </div>
                                            )}

                                            {/* Text input */}
                                            {field.type === "text" && (
                                                <>
                                                    <label className="block text-slate-400 text-sm mb-2 font-medium">
                                                        {field.label}
                                                    </label>
                                                    <input
                                                        type={field.key.includes("phone") || field.key.includes("telefon") ? "tel" : field.key.includes("email") ? "email" : "text"}
                                                        placeholder={field.key.includes("phone") || field.key.includes("telefon") ? "+420…" : field.key.includes("email") ? "email@firma.cz" : "Napište…"}
                                                        className="w-full bg-white/[0.04] border border-white/[0.1] rounded-xl px-4 py-3 text-white text-base outline-none focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/25 transition-all placeholder:text-slate-500"
                                                        value={(ans?.details[field.key] as string) || ""}
                                                        onChange={(e) => setDetail(q.key, field.key, e.target.value)}
                                                    />
                                                </>
                                            )}

                                            {/* Select → tile grid */}
                                            {field.type === "select" && field.options && (
                                                <>
                                                    <label className="block text-slate-400 text-sm mb-2 font-medium">
                                                        {field.label}
                                                    </label>
                                                    <div className="flex flex-wrap gap-2">
                                                        {field.options.map((opt) => {
                                                            const selected = (ans?.details[field.key] as string) === opt;
                                                            return (
                                                                <button
                                                                    key={opt}
                                                                    onClick={() => setDetail(q.key, field.key, opt)}
                                                                    className={`touch-bubble
                                      px-4 py-2.5 rounded-xl border text-sm font-medium transition-[background-color,border-color,color] duration-150
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
                                                    {field.warning && ans?.details[field.key] && (field.warning as Record<string, string>)[ans.details[field.key] as string] && (
                                                        <div className="mt-2 flex items-start gap-2 rounded-xl bg-red-500/[0.08] border border-red-500/20 px-4 py-3">
                                                            <span className="text-red-400 flex-shrink-0 mt-0.5">⚠️</span>
                                                            <div>
                                                                <p className="text-xs text-red-300 leading-relaxed">{renderWarningText((field.warning as Record<string, string>)[ans.details[field.key] as string])}</p>
                                                            </div>
                                                        </div>
                                                    )}
                                                </>
                                            )}

                                            {/* Single select → tile grid (one choice) */}
                                            {field.type === "single_select" && field.options && (
                                                <>
                                                    <label className="block text-slate-400 text-sm mb-2 font-medium">
                                                        {field.label}
                                                    </label>
                                                    <div className="flex flex-wrap gap-2">
                                                        {field.options.map((opt) => {
                                                            const selected = (ans?.details[field.key] as string) === opt;
                                                            return (
                                                                <button
                                                                    key={opt}
                                                                    onClick={() => setDetail(q.key, field.key, opt)}
                                                                    className={`touch-bubble
                                      px-4 py-2.5 rounded-xl border text-sm font-medium transition-[background-color,border-color,color] duration-150
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
                                                </>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ── Followup_yes fields (slides down when "Ano") ── */}
                    {q.followup_yes && ans?.answer === "yes" && (
                        <div ref={followupRef} className="animate-slide-down mb-6">
                            <div className="bg-emerald-500/[0.06] backdrop-blur-xl rounded-2xl p-5">
                                <p className="text-emerald-300 text-sm font-semibold mb-4">Doplňující informace:</p>
                                <div className="space-y-4">
                                    {q.followup_yes.fields.map((field) => (
                                        <div key={field.key}>
                                            {/* Info → green info banner */}
                                            {field.type === "info" && (
                                                <div className="flex items-start gap-2 rounded-xl bg-emerald-500/[0.08] border border-emerald-500/20 px-4 py-3">
                                                    <span className="text-emerald-400 text-lg mt-0.5 flex-shrink-0">✅</span>
                                                    <p className="text-xs text-emerald-300 leading-relaxed">{renderWarningText(field.label.replace(/^✅\s*/, ''))}</p>
                                                </div>
                                            )}

                                            {/* Text input */}
                                            {field.type === "text" && (
                                                <>
                                                    <label className="block text-slate-400 text-sm mb-2 font-medium">
                                                        {field.label}
                                                    </label>
                                                    <input
                                                        type={field.key.includes("phone") || field.key.includes("telefon") ? "tel" : field.key.includes("email") ? "email" : "text"}
                                                        placeholder={field.key.includes("phone") || field.key.includes("telefon") ? "+420…" : field.key.includes("email") ? "email@firma.cz" : "Napište…"}
                                                        className="w-full bg-white/[0.04] border border-white/[0.1] rounded-xl px-4 py-3 text-white text-base outline-none focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/25 transition-all placeholder:text-slate-500"
                                                        value={(ans?.details[field.key] as string) || ""}
                                                        onChange={(e) => setDetail(q.key, field.key, e.target.value)}
                                                    />
                                                </>
                                            )}

                                            {/* Select → tile grid */}
                                            {(field.type === "select" || field.type === "single_select") && field.options && (
                                                <>
                                                    <label className="block text-slate-400 text-sm mb-2 font-medium">
                                                        {field.label}
                                                    </label>
                                                    <div className="flex flex-wrap gap-2">
                                                        {field.options.map((opt) => {
                                                            const selected = (ans?.details[field.key] as string) === opt;
                                                            return (
                                                                <button
                                                                    key={opt}
                                                                    onClick={() => setDetail(q.key, field.key, opt)}
                                                                    className={`touch-bubble
                                      px-4 py-2.5 rounded-xl border text-sm font-medium transition-[background-color,border-color,color] duration-150
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
                                                </>
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
                                                                className={`touch-bubble
                                      px-4 py-2.5 rounded-xl border text-sm font-medium transition-[background-color,border-color,color] duration-150 flex items-center gap-2
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
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Risk / Prohibited / Lawyer warning banners */}
                    {ans?.answer && !isNA && <RiskWarningBanner questionKey={q.key} answer={ans.answer} />}
                    {ans?.answer && !isNA && <ComplianceGapBanner questionKey={q.key} answer={ans.answer} />}

                    {/* Vlastní odpověď — inline, ne jako vnořená komponenta (jinak iOS klávesnice mizí) */}
                    {!["text", "address", "conditional_fields"].includes(q.type) && (
                        <div className="mt-5 mb-2">
                            <div className="rounded-2xl border border-white/[0.12] bg-white/[0.04] p-4 transition-all duration-200 hover:border-white/[0.2] focus-within:border-fuchsia-500/50 focus-within:ring-1 focus-within:ring-fuchsia-500/25">
                                <label className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-2">
                                    <svg className="w-4 h-4 text-fuchsia-400" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" /></svg>
                                    Vlastní odpověď
                                </label>
                                <textarea
                                    placeholder="Zde napište vlastní odpověď, pokud jste v možnostech nenašli přiléhavou volbu…"
                                    className="w-full bg-transparent border-0 rounded-lg px-1 py-1 text-white text-base outline-none transition-all placeholder:text-slate-500 resize-none min-h-[56px] max-h-[120px]"
                                    rows={2}
                                    maxLength={2000}
                                    value={customAnswers[q.key] || ""}
                                    onChange={(e) => setCustomAnswers(prev => ({ ...prev, [q.key]: e.target.value }))}
                                />
                            </div>
                            {customAnswers[q.key] && customAnswers[q.key].trim() && (
                                <p className="text-xs text-fuchsia-400/70 mt-2 ml-1">
                                    ✓ Vaše odpověď bude zohledněna ({customAnswers[q.key].length}/2000 znaků)
                                </p>
                            )}
                        </div>
                    )}

                    {/* Navigation */}
                    <div ref={navRef} className="flex justify-between items-center mt-6">
                        <button
                            onClick={goBack}
                            className="px-4 sm:px-6 py-3 rounded-xl bg-white/[0.06] border border-white/[0.1] text-slate-400 font-medium transition-all hover:bg-white/[0.1] text-sm sm:text-base"
                        >
                            ← Zpět
                        </button>

                        {fromDashboard && ans?.answer ? (
                            <button
                                onClick={handleSubmit}
                                disabled={submitting}
                                className="px-5 sm:px-8 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-emerald-500 text-white font-semibold text-sm sm:text-base transition-all hover:shadow-lg hover:shadow-cyan-500/25 active:scale-[0.98] disabled:opacity-50"
                            >
                                {submitting ? "Ukládám…" : "✓ Uložit a zpět"}
                            </button>
                        ) : isLast ? (
                            <button
                                onClick={handleSubmit}
                                disabled={submitting || !ans?.answer}
                                className="px-5 sm:px-8 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-emerald-500 text-white font-semibold text-sm sm:text-lg transition-all hover:shadow-lg hover:shadow-cyan-500/25 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-cyan-500/20"
                            >
                                {submitting ? "Odesílám…" : "✅ Ukončit a odeslat dotazník"}
                            </button>
                        ) : ans?.answer ? (
                            <button
                                onClick={goNext}
                                className="px-8 py-3 rounded-xl bg-gradient-to-r from-fuchsia-600 to-purple-600 text-white font-semibold transition-all hover:shadow-lg hover:shadow-fuchsia-500/25 active:scale-[0.98]"
                            >
                                Další →
                            </button>
                        ) : null}
                    </div>

                    {/* Hint */}
                    <p className="text-xs text-slate-500 leading-relaxed mt-4 text-center">
                        {`„Nevím" = doplňte později. „Netýká se mě" = otázka pro vás není relevantní. 100\u00A0% pokrytí zákonných požadavků je možné až se všemi odpověďmi.`}
                    </p>

                    {/* Save & Continue Later */}
                    <SaveLaterButton answers={answers} currentQuestion={currentQuestion} companyId={companyId} />
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
        /* Okamžitá odezva na dotykovém zařízení — bez 300ms delay */
        .touch-bubble {
          touch-action: manipulation;
          -webkit-tap-highlight-color: transparent;
          -webkit-touch-callout: none;
          user-select: none;
          -webkit-user-select: none;
        }
      `}</style>
        </div >
    );
}

/* ═══════════════════════════════════════════
   SAVE LATER BUTTON
   ═══════════════════════════════════════════ */

function SaveLaterButton({ answers, currentQuestion, companyId }: {
    answers: Record<string, { answer: string; details: Record<string, unknown> }>;
    currentQuestion: number;
    companyId: string | null;
}) {
    const [saving, setSaving] = useState(false);
    return (
        <div className="flex justify-center mt-6 mb-4">
            <button
                disabled={saving}
                onClick={async () => {
                    setSaving(true);
                    // 1) Save to localStorage
                    const saveData = {
                        answers: Object.fromEntries(
                            Object.entries(answers).map(([k, v]) => [k, v])
                        ),
                        currentQuestion,
                        companyId,
                        timestamp: new Date().toISOString(),
                    };
                    localStorage.setItem(`aishield_quest_${companyId}`, JSON.stringify(saveData));

                    // 2) Save to server (partial submit — UPSERT keeps all answers safe)
                    if (companyId) {
                        try {
                            const list = Object.values(answers)
                                .filter((a) => a.answer !== "")
                                .map((a) => ({
                                    question_key: (a as any).question_key,
                                    section: (a as any).section,
                                    answer: a.answer,
                                    details: Object.keys(a.details).length > 0 ? a.details : null,
                                    tool_name: (a as any).tool_name || null,
                                }));
                            if (list.length > 0) {
                                await fetch(`${API_URL}/api/questionnaire/submit`, {
                                    method: "POST",
                                    headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({
                                        company_id: companyId,
                                        answers: list,
                                    }),
                                });
                            }
                        } catch {
                            // Server save failed — localStorage backup is enough
                            console.warn("[Dotazník] Server save failed, localStorage saved");
                        }
                    }

                    // 3) Show confirmation overlay
                    const overlay = document.createElement('div');
                    overlay.innerHTML = `
                        <div style="position:fixed;inset:0;z-index:9999;display:flex;align-items:center;justify-content:center;background:rgba(2,6,23,0.85);backdrop-filter:blur(8px);animation:fadeIn .3s ease">
                            <div style="background:linear-gradient(135deg,rgba(30,41,59,0.95),rgba(15,23,42,0.98));border:1px solid rgba(139,92,246,0.25);border-radius:1.25rem;padding:2.5rem;max-width:28rem;width:90%;text-align:center;box-shadow:0 25px 50px rgba(0,0,0,0.5);animation:scaleIn .3s ease">
                                <div style="width:4rem;height:4rem;border-radius:1rem;background:rgba(16,185,129,0.12);border:1px solid rgba(16,185,129,0.25);display:flex;align-items:center;justify-content:center;margin:0 auto 1.25rem">
                                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                                </div>
                                <h3 style="color:white;font-size:1.25rem;font-weight:700;margin-bottom:0.5rem">Odpovědi uloženy</h3>
                                <p style="color:rgb(148,163,184);font-size:0.875rem;line-height:1.6;margin-bottom:1.5rem">Váš pokrok je bezpečně uložen na serveru. Můžete se kdykoliv vrátit a pokračovat přesně tam, kde jste skončili.</p>
                                <a href="/dashboard" style="display:inline-flex;align-items:center;gap:0.5rem;padding:0.75rem 2rem;border-radius:0.75rem;background:linear-gradient(135deg,#a855f7,#6366f1);color:white;font-weight:600;font-size:0.875rem;text-decoration:none;transition:all .2s;box-shadow:0 4px 15px rgba(168,85,247,0.3)">Zpět na dashboard</a>
                            </div>
                        </div>
                        <style>@keyframes fadeIn{from{opacity:0}to{opacity:1}}@keyframes scaleIn{from{opacity:0;transform:scale(0.95)}to{opacity:1;transform:scale(1)}}</style>
                    `;
                    document.body.appendChild(overlay);
                }}
                className="px-5 py-2.5 rounded-xl border border-white/[0.08] bg-white/[0.04] text-slate-400 hover:text-slate-200 hover:bg-white/[0.08] hover:border-white/[0.15] transition-all flex items-center gap-2 text-sm font-medium disabled:opacity-50"
            >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                </svg>
                Uložit a pokračovat později
            </button>
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
            <div className="max-w-2xl mx-auto px-4 py-4">
                <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-slate-300 font-medium">
                        Otázka {current + 1} z {total}
                    </span>
                    <span className="text-sm text-fuchsia-400 font-bold">
                        {pct} %
                    </span>
                </div>
                <div className="w-full h-2.5 bg-white/[0.08] rounded-full overflow-hidden">
                    <div
                        className="h-full rounded-full bg-gradient-to-r from-fuchsia-500 to-cyan-400 transition-all duration-500 ease-out"
                        style={{ width: `${pct}%`, boxShadow: "0 0 16px rgba(217, 70, 239, 0.5)" }}
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
