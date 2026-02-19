"use client";

import { useState, useEffect, useRef, useCallback, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase-browser";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ═══════════════════════════════════════════
   TYPES
   ═══════════════════════════════════════════ */

interface ExtractedAnswer {
    question_key: string;
    section: string;
    answer: string;
    details?: Record<string, unknown>;
    tool_name?: string;
}

interface MultiMessage {
    text: string;
    delay_ms: number;
    bubbles?: string[];
}

interface Mart1nMessage {
    role: "user" | "assistant";
    content: string;          // display text (markdown for assistant)
    bubbles?: string[];       // quick-reply buttons
    progress?: number;
    isComplete?: boolean;
    timestamp: number;
}

/* ═══════════════════════════════════════════
   MARKDOWN RENDERER (simple)
   ═══════════════════════════════════════════ */

function renderMarkdown(text: string) {
    // Split into paragraphs
    const paragraphs = text.split(/\n\n+/);
    return paragraphs.map((p, pi) => {
        // Check if paragraph is a bullet list
        const lines = p.split(/\n/);
        const isList = lines.every(l => /^[-•*]\s/.test(l.trim()) || l.trim() === "");
        if (isList) {
            const items = lines.filter(l => /^[-•*]\s/.test(l.trim()));
            return (
                <ul key={pi} className="list-disc list-inside space-y-1 my-2">
                    {items.map((item, ii) => (
                        <li key={ii} className="text-sm leading-relaxed">
                            {renderInlineMarkdown(item.replace(/^[-•*]\s/, ""))}
                        </li>
                    ))}
                </ul>
            );
        }
        return (
            <p key={pi} className="text-sm leading-relaxed mb-2 last:mb-0">
                {renderInlineMarkdown(p.replace(/\n/g, " "))}
            </p>
        );
    });
}

function renderInlineMarkdown(text: string) {
    // Bold **text**
    const parts = text.split(/\*\*(.*?)\*\*/g);
    return parts.map((part, i) =>
        i % 2 === 1
            ? <strong key={i} className="font-semibold text-white">{part}</strong>
            : <span key={i}>{part}</span>
    );
}

/* ═══════════════════════════════════════════
   MART1N AVATAR SVG
   ═══════════════════════════════════════════ */

function Mart1nAvatar({ size = 40 }: { size?: number }) {
    return (
        <svg width={size} height={size} viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Shield body */}
            <path
                d="M24 3L6 10v12c0 11 8 20 18 23 10-3 18-12 18-23V10L24 3z"
                fill="url(#mart1n-grad)"
                fillOpacity="0.2"
                stroke="url(#mart1n-grad)"
                strokeWidth="2"
                strokeLinejoin="round"
            />
            {/* Inner glow */}
            <path
                d="M24 8L10 13.5v9c0 8.5 6.2 15.8 14 18 7.8-2.2 14-9.5 14-18v-9L24 8z"
                fill="url(#mart1n-grad)"
                fillOpacity="0.1"
                stroke="url(#mart1n-grad)"
                strokeWidth="0.5"
                opacity="0.5"
            />
            {/* "M" letter — stylized */}
            <path
                d="M15 30V18l4.5 7 4.5-7 4.5 7 4.5-7v12"
                stroke="url(#mart1n-grad)"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                fill="none"
            />
            {/* "1" accent — small */}
            <path
                d="M35 14l-2 1v5"
                stroke="#22d3ee"
                strokeWidth="1.5"
                strokeLinecap="round"
                opacity="0.8"
            />
            <defs>
                <linearGradient id="mart1n-grad" x1="6" y1="3" x2="42" y2="45" gradientUnits="userSpaceOnUse">
                    <stop stopColor="#e879f9" />
                    <stop offset="0.5" stopColor="#a855f7" />
                    <stop offset="1" stopColor="#22d3ee" />
                </linearGradient>
            </defs>
        </svg>
    );
}

/* ═══════════════════════════════════════════
   TYPING INDICATOR
   ═══════════════════════════════════════════ */

function TypingIndicator() {
    return (
        <div className="flex items-start gap-3 mb-4">
            <div className="flex-shrink-0 mt-1">
                <Mart1nAvatar size={36} />
            </div>
            <div className="glass px-4 py-3 max-w-[80%]">
                <div className="flex gap-1.5">
                    <span className="w-2 h-2 bg-neon-fuchsia/60 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                    <span className="w-2 h-2 bg-neon-purple/60 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                    <span className="w-2 h-2 bg-neon-cyan/60 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
            </div>
        </div>
    );
}





/* ═══════════════════════════════════════════
   PROGRESS BAR
   ═══════════════════════════════════════════ */

function ProgressBar({ progress }: { progress: number }) {
    return (
        <div className="w-full">
            <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-slate-500">Průběh analýzy</span>
                <span className="text-xs font-mono text-neon-cyan">{progress}%</span>
            </div>
            <div className="h-1.5 bg-dark-800 rounded-full overflow-hidden">
                <div
                    className="h-full rounded-full transition-all duration-700 ease-out"
                    style={{
                        width: `${progress}%`,
                        background: "linear-gradient(90deg, #e879f9, #a855f7, #22d3ee)",
                    }}
                />
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════════
   MAIN PAGE COMPONENT (inner, with searchParams)
   ═══════════════════════════════════════════ */

function Mart1nPageInner() {
    const searchParams = useSearchParams();
    const router = useRouter();

    // State
    const [messages, setMessages] = useState<Mart1nMessage[]>([]);
    const [input, setInput] = useState("");
    const [sending, setSending] = useState(false);
    const [sessionId, setSessionId] = useState("");
    const [companyId, setCompanyId] = useState<string>("");
    const [progress, setProgress] = useState(0);
    const [isComplete, setIsComplete] = useState(false);
    const [initLoading, setInitLoading] = useState(true);
    const [isResuming, setIsResuming] = useState(false);
    const [bubbleOverrides, setBubbleOverrides] = useState<Record<string, string>>({});

    const inputRef = useRef<HTMLTextAreaElement>(null);



    // Get company_id from URL or Supabase user
    useEffect(() => {
        (async () => {
            const urlCid = searchParams.get("company_id");
            if (urlCid) {
                setCompanyId(urlCid);
                return;
            }
            // Try to get from Supabase auth
            try {
                const supabase = createClient();
                const { data: { user } } = await supabase.auth.getUser();
                if (user) {
                    // Look up company by user email
                    const { data } = await supabase
                        .from("companies")
                        .select("id")
                        .eq("email", user.email)
                        .limit(1);
                    if (data && data.length > 0) {
                        setCompanyId(data[0].id);
                        return;
                    }
                }
            } catch { /* ignore */ }
            // Fallback: generate a temporary ID
            setCompanyId(crypto.randomUUID());
        })();
    }, [searchParams]);

    // Load session: check for existing conversation, then init or resume
    useEffect(() => {
        if (!companyId) return;
        (async () => {
            try {
                // 1. Check for existing conversation (server-side)
                const sessionRes = await fetch(`${API_URL}/api/mart1n/session/${companyId}`);
                const sessionData = await sessionRes.json();

                if (sessionData.has_session && sessionData.messages?.length > 0) {
                    // RESUMPTION: Load existing conversation from server
                    setSessionId(sessionData.session_id);
                    setProgress(sessionData.progress || 0);
                    setIsResuming(true);

                    // Convert server messages to frontend format
                    const loadedMessages: Mart1nMessage[] = sessionData.messages.map(
                        (m: { role: string; content: string }) => ({
                            role: m.role as "user" | "assistant",
                            content: m.content,
                            timestamp: Date.now(),
                        })
                    );

                    // Add resumption greeting
                    const pct = sessionData.progress || 0;
                    const unknownCount = sessionData.answered_keys
                        ? (sessionData.answered_keys.length)
                        : 0;
                    loadedMessages.push({
                        role: "assistant",
                        content: `Vítejte zpět! Vidím, že Váš dotazník je na **${pct}%** `
                            + `(${unknownCount} zodpovězených otázek). `
                            + `Chcete pokračovat tam, kde jste skončili, nebo doplnit odpovědi na některé otázky?`,
                        bubbles: [
                            "Pokračovat kde jsem skončil/a",
                            "Doplnit přeskočené otázky",
                            "Začít od začátku",
                        ],
                        timestamp: Date.now(),
                    });

                    setMessages(loadedMessages);
                    setInitLoading(false);
                    return;
                }
            } catch {
                // Session check failed — continue to fresh init
            }

            // 2. No existing session — fresh start with init greeting
            try {
                const res = await fetch(`${API_URL}/api/mart1n/init`);
                const data = await res.json();
                setSessionId(data.session_id || crypto.randomUUID());
                setMessages([{
                    role: "assistant",
                    content: data.message,
                    bubbles: data.bubbles || [],
                    progress: 0,
                    timestamp: Date.now(),
                }]);
            } catch {
                setMessages([{
                    role: "assistant",
                    content: "Ahoj! Jsem **Uršula**, umělá inteligence platformy AIshield.cz. Omlouvám se, mám momentálně technické potíže. Zkuste stránku obnovit.",
                    bubbles: [],
                    timestamp: Date.now(),
                }]);
            } finally {
                setInitLoading(false);
            }
        })();
    }, [companyId]);

    // Send message to Uršula API (server-side mode — sends single message)
    const sendMessage = useCallback(async (text: string, displayText?: string) => {
        if (!text.trim() || sending || isComplete) return;

        const userMsg: Mart1nMessage = {
            role: "user",
            content: (displayText || text).trim(),
            timestamp: Date.now(),
        };

        setMessages(prev => [...prev, userMsg]);
        setInput("");
        setSending(true);
        setIsResuming(false);

        try {
            const res = await fetch(`${API_URL}/api/mart1n/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    session_id: sessionId,
                    company_id: companyId,
                    message: text.trim(),   // Send original text to backend
                }),
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || `HTTP ${res.status}`);
            }

            const data = await res.json();

            // Store bubble overrides for next interaction
            if (data.bubble_overrides && Object.keys(data.bubble_overrides).length > 0) {
                setBubbleOverrides(data.bubble_overrides);
            } else {
                setBubbleOverrides({});
            }

            // ── Multi-message sequential display ──
            if (data.multi_messages && data.multi_messages.length > 0) {
                for (let i = 0; i < data.multi_messages.length; i++) {
                    const mm = data.multi_messages[i] as MultiMessage;

                    // Show typing indicator during delay
                    if (mm.delay_ms > 0) {
                        setSending(true);
                        await new Promise(resolve => setTimeout(resolve, mm.delay_ms));
                    }

                    setSending(false);
                    const assistantMsg: Mart1nMessage = {
                        role: "assistant",
                        content: mm.text,
                        bubbles: mm.bubbles || [],
                        progress: data.progress || 0,
                        isComplete: i === data.multi_messages.length - 1 ? (data.is_complete || false) : false,
                        timestamp: Date.now(),
                    };
                    setMessages(prev => [...prev, assistantMsg]);

                    // Brief typing pause between messages (even without explicit delay)
                    if (i < data.multi_messages.length - 1) {
                        setSending(true);
                        await new Promise(resolve => setTimeout(resolve, 600));
                    }
                }
            } else {
                // ── Normal single message ──
                setSending(false);
                const assistantMsg: Mart1nMessage = {
                    role: "assistant",
                    content: data.message,
                    bubbles: data.bubbles || [],
                    progress: data.progress || 0,
                    isComplete: data.is_complete || false,
                    timestamp: Date.now(),
                };
                setMessages(prev => [...prev, assistantMsg]);
            }

            setProgress(data.progress || 0);

            if (data.is_complete) {
                setIsComplete(true);
            }
        } catch (err: unknown) {
            const errorMsg = err instanceof Error ? err.message : "Neočekávaná chyba";
            setSending(false);
            setMessages(prev => [...prev, {
                role: "assistant",
                content: `Omlouvám se, nepodařilo se zpracovat odpověď: ${errorMsg}. Zkuste to prosím znovu.`,
                bubbles: ["Zkusit znovu"],
                timestamp: Date.now(),
            }]);
        } finally {
            setSending(false);
            inputRef.current?.focus();
        }
    }, [sending, isComplete, sessionId, companyId]);

    // Handle bubble click (with optional text override for NE→ANO swap)
    const handleBubbleClick = useCallback((bubble: string) => {
        const displayText = bubbleOverrides[bubble] || bubble;
        sendMessage(bubble, displayText);
    }, [sendMessage, bubbleOverrides]);

    // Handle textarea submit (Enter key)
    const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage(input);
        }
    }, [input, sendMessage]);

    // Auto-resize textarea
    const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setInput(e.target.value);
        // Auto-resize
        const ta = e.target;
        ta.style.height = "auto";
        ta.style.height = Math.min(ta.scrollHeight, 120) + "px";
    }, []);

    return (
        <div className="flex flex-col h-screen bg-dark-950">
            {/* ── Header ── */}
            <header className="flex-shrink-0 border-b border-white/[0.06] bg-dark-900/80 backdrop-blur-xl z-10">
                <div className="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <Mart1nAvatar size={32} />
                        <div>
                            <h1 className="text-sm font-bold text-white tracking-tight">
                                Uršula
                            </h1>
                            <p className="text-xs text-slate-500">AI Act compliance analýza</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="w-48 hidden sm:block">
                            <ProgressBar progress={progress} />
                        </div>
                        <a
                            href="/dashboard"
                            className="text-xs text-slate-500 hover:text-neon-fuchsia transition-colors flex items-center gap-1"
                        >
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
                            </svg>
                            Dashboard
                        </a>
                    </div>
                </div>
                {/* Mobile progress */}
                <div className="sm:hidden px-4 pb-2">
                    <ProgressBar progress={progress} />
                </div>
            </header>

            {/* ── Chat Messages ── */}
            <div className="flex-1 overflow-y-auto flex flex-col-reverse">
                <div className="max-w-3xl mx-auto px-4 py-6 space-y-1 w-full">
                    {/* Resumption badge */}
                    {isResuming && (
                        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-neon-cyan/5 border border-neon-cyan/20 mb-2">
                            <svg className="w-4 h-4 text-neon-cyan flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182" />
                            </svg>
                            <span className="text-xs text-slate-400">
                                Pokračujete v rozpracovaném dotazníku — <span className="text-neon-cyan font-medium">{progress}% dokončeno</span>
                            </span>
                        </div>
                    )}

                    {initLoading ? (
                        <TypingIndicator />
                    ) : (
                        messages.map((msg, i) => (
                            <div key={i}>
                                {msg.role === "assistant" ? (
                                    /* ── Assistant message ── */
                                    <div className="flex items-start gap-3 mb-4">
                                        <div className="flex-shrink-0 mt-1">
                                            <Mart1nAvatar size={36} />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="glass px-4 py-3 max-w-[90%]">
                                                <div className="text-slate-300">
                                                    {renderMarkdown(msg.content)}
                                                </div>
                                            </div>
                                            {/* Bubbles */}
                                            {msg.bubbles && msg.bubbles.length > 0 && i === messages.length - 1 && !sending && (
                                                <div className="flex flex-wrap gap-2 mt-3 ml-1">
                                                    {msg.bubbles.map((bubble, bi) => (
                                                        <button
                                                            key={bi}
                                                            onClick={() => handleBubbleClick(bubble)}
                                                            disabled={isComplete}
                                                            className="px-3 py-1.5 text-sm rounded-full border border-neon-fuchsia/30
                                                                       bg-neon-fuchsia/5 text-neon-fuchsia hover:bg-neon-fuchsia/15
                                                                       hover:border-neon-fuchsia/50 transition-all duration-200
                                                                       disabled:opacity-40 disabled:cursor-not-allowed"
                                                        >
                                                            {bubble}
                                                        </button>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ) : (
                                    /* ── User message ── */
                                    <div className="flex justify-end mb-4">
                                        <div className="max-w-[80%] px-4 py-3 rounded-2xl rounded-br-md
                                                        bg-gradient-to-r from-neon-fuchsia/20 to-neon-purple/20
                                                        border border-neon-fuchsia/20
                                                        text-sm text-slate-200 leading-relaxed">
                                            {msg.content}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))
                    )}

                    {/* Typing indicator */}
                    {sending && <TypingIndicator />}

                    {/* Completion card */}
                    {isComplete && (
                        <div className="glass border-emerald-500/20 bg-emerald-500/5 p-6 text-center mt-6">
                            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-emerald-500/10 flex items-center justify-center">
                                <svg className="w-8 h-8 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                            <h3 className="text-lg font-bold text-white mb-2">Analýza dokončena!</h3>
                            <p className="text-sm text-slate-400 mb-4">
                                Děkujeme za Váš čas. Všechny odpovědi byly uloženy a zpracovány.
                                Výsledky najdete v dashboardu.
                            </p>
                            <button
                                onClick={() => router.push("/dashboard")}
                                className="btn-primary px-6 py-2.5 text-sm"
                            >
                                Přejít na dashboard
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* ── Input Area ── */}
            <div className="flex-shrink-0 border-t border-white/[0.06] bg-dark-900/80 backdrop-blur-xl">
                <div className="max-w-3xl mx-auto px-4 py-3">
                    <div className="flex items-end gap-3">
                        <div className="flex-1 relative">
                            <textarea
                                ref={inputRef}
                                value={input}
                                onChange={handleInputChange}
                                onKeyDown={handleKeyDown}
                                placeholder={isComplete ? "Analýza je dokončena" : "Napište odpověď..."}
                                disabled={sending || isComplete || initLoading}
                                rows={1}
                                className="w-full resize-none rounded-xl border border-white/[0.08] bg-dark-800
                                           px-4 py-3 text-sm text-slate-200 placeholder:text-slate-600
                                           focus:outline-none focus:border-neon-fuchsia/30 focus:ring-1 focus:ring-neon-fuchsia/20
                                           disabled:opacity-50 disabled:cursor-not-allowed
                                           transition-colors"
                                style={{ maxHeight: "120px" }}
                            />
                        </div>
                        <button
                            onClick={() => sendMessage(input)}
                            disabled={!input.trim() || sending || isComplete || initLoading}
                            className="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center
                                       bg-gradient-to-r from-neon-fuchsia to-neon-purple
                                       hover:brightness-110 transition-all
                                       disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:brightness-100"
                        >
                            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
                            </svg>
                        </button>
                    </div>
                    <p className="text-[10px] text-slate-600 mt-2 text-center">
                        Uršula je umělá inteligence (čl. 50 AI Act). Data chráněna dle GDPR.
                    </p>
                </div>
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════════
   PAGE EXPORT (Suspense wrapper for useSearchParams)
   ═══════════════════════════════════════════ */

export default function Mart1nPage() {
    return (
        <Suspense fallback={
            <div className="flex items-center justify-center h-screen bg-dark-950">
                <div className="flex flex-col items-center gap-4">
                    <Mart1nAvatar size={64} />
                    <p className="text-sm text-slate-500">Načítám Uršulu...</p>
                </div>
            </div>
        }>
            <Mart1nPageInner />
        </Suspense>
    );
}
