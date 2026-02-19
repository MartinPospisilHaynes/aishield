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
   PRIVACY SHIELD BADGE
   ═══════════════════════════════════════════ */

function PrivacyBadge() {
    const [expanded, setExpanded] = useState(false);
    return (
        <div className="mb-4">
            <button
                onClick={() => setExpanded(!expanded)}
                className="flex items-center gap-2 text-xs text-slate-400 hover:text-neon-cyan transition-colors group"
            >
                <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                </svg>
                <span className="group-hover:text-emerald-300 transition-colors">Vaše data jsou v bezpečí — GDPR</span>
                <svg className={`w-3 h-3 transition-transform ${expanded ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                </svg>
            </button>
            {expanded && (
                <div className="mt-2 p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/10 text-xs text-slate-400 leading-relaxed space-y-1">
                    <p>Veškeré informace zůstávají výhradně u nás v AIshield.cz. Žádná třetí strana k nim nemá přístup.</p>
                    <p>Všechna data jsou šifrovaná (AES-256) a uložená na zabezpečených serverech v EU.</p>
                    <p>Porušení ochrany dat by nás stálo pokutu až <strong className="text-emerald-400">20 milionů EUR</strong> nebo <strong className="text-emerald-400">4 % celosvětového obratu</strong> dle Nařízení GDPR (EU 2016/679, čl. 83 odst. 5).</p>
                    <p>Podléháme dozoru <strong className="text-white">ÚOOÚ</strong> dle zákona č. 110/2019 Sb. Kdykoli můžete požádat o smazání svých dat (GDPR čl. 17).</p>
                </div>
            )}
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

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    // Scroll to bottom when messages change
    const scrollToBottom = useCallback(() => {
        setTimeout(() => {
            messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
        }, 100);
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages, sending, scrollToBottom]);

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

    // Load initial greeting from API
    useEffect(() => {
        if (!companyId) return;
        (async () => {
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
                    content: "Dobrý den! Jsem **MART1N**, umělá inteligence platformy AIshield.cz. Omlouvám se, mám momentálně technické potíže. Zkuste stránku obnovit.",
                    bubbles: [],
                    timestamp: Date.now(),
                }]);
            } finally {
                setInitLoading(false);
            }
        })();
    }, [companyId]);

    // Send message to MART1N API
    const sendMessage = useCallback(async (text: string) => {
        if (!text.trim() || sending || isComplete) return;

        const userMsg: Mart1nMessage = {
            role: "user",
            content: text.trim(),
            timestamp: Date.now(),
        };

        const newMessages = [...messages, userMsg];
        setMessages(newMessages);
        setInput("");
        setSending(true);

        // Build messages payload for API (only role + content)
        const apiMessages = newMessages.map(m => ({
            role: m.role,
            content: m.content,
        }));

        try {
            const res = await fetch(`${API_URL}/api/mart1n/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    session_id: sessionId,
                    company_id: companyId,
                    messages: apiMessages,
                }),
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || `HTTP ${res.status}`);
            }

            const data = await res.json();

            const assistantMsg: Mart1nMessage = {
                role: "assistant",
                content: data.message,
                bubbles: data.bubbles || [],
                progress: data.progress || 0,
                isComplete: data.is_complete || false,
                timestamp: Date.now(),
            };

            setMessages(prev => [...prev, assistantMsg]);
            setProgress(data.progress || 0);

            if (data.is_complete) {
                setIsComplete(true);
            }
        } catch (err: unknown) {
            const errorMsg = err instanceof Error ? err.message : "Neočekávaná chyba";
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
    }, [messages, sending, isComplete, sessionId, companyId]);

    // Handle bubble click
    const handleBubbleClick = useCallback((bubble: string) => {
        sendMessage(bubble);
    }, [sendMessage]);

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
                                MART<span className="text-neon-cyan">1</span>N
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
            <div className="flex-1 overflow-y-auto">
                <div className="max-w-3xl mx-auto px-4 py-6 space-y-1">
                    {/* Privacy badge at top */}
                    <PrivacyBadge />

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

                    <div ref={messagesEndRef} />
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
                        MART1N je umělá inteligence (čl. 50 AI Act). Data chráněna dle GDPR.
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
                    <p className="text-sm text-slate-500">Načítám MART1N...</p>
                </div>
            </div>
        }>
            <Mart1nPageInner />
        </Suspense>
    );
}
