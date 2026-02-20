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

function sanitizeText(raw: string): string {
    // Strip markdown formatting except **bold** and paragraphs
    let t = raw;
    // Remove literal \n (escaped backslash-n that leaked through)
    t = t.replace(/\\n/g, '\n');
    // Remove heading markers
    t = t.replace(/^#{1,6}\s+/gm, '');
    // Bullet/list markers are allowed for readability
    // Remove italic markers (single * or _) but preserve **bold**
    t = t.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '$1');
    t = t.replace(/(?<!_)_(?!_)(.+?)(?<!_)_(?!_)/g, '$1');
    // Remove code backticks
    t = t.replace(/`([^`]*)`/g, '$1');
    // Remove underline/strikethrough
    t = t.replace(/~~(.+?)~~/g, '$1');
    return t.trim();
}

function renderMarkdown(text: string) {
    const clean = sanitizeText(text);
    // Split into paragraphs
    const paragraphs = clean.split(/\n\n+/);
    return paragraphs.map((p, pi) => {
        // Check if paragraph contains bullet lines (- or — at start)
        const lines = p.split(/\n/);
        const hasBullets = lines.some(l => /^\s*[-—•]\s+/.test(l));
        if (hasBullets) {
            return (
                <ul key={pi} className="text-sm leading-relaxed mb-2 last:mb-0 list-disc list-inside space-y-1">
                    {lines.map((line, li) => {
                        const bulletMatch = line.match(/^\s*[-—•]\s+(.*)/);
                        if (bulletMatch) {
                            return <li key={li}>{renderInlineMarkdown(bulletMatch[1])}</li>;
                        }
                        // Non-bullet line before/after bullets
                        return <p key={li} className="mb-1">{renderInlineMarkdown(line)}</p>;
                    })}
                </ul>
            );
        }
        return (
            <p key={pi} className="text-sm leading-relaxed mb-2 last:mb-0">
                {renderInlineMarkdown(lines.join(' '))}
            </p>
        );
    });
}

function renderInlineMarkdown(text: string) {
    // Bold **text** only
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
            {/* Outer circle */}
            <circle cx="24" cy="24" r="22" fill="url(#ai-grad)" fillOpacity="0.12" stroke="url(#ai-grad)" strokeWidth="2" />
            {/* Brain — left hemisphere */}
            <path d="M24 14c-2.5 0-4.5 1-5.8 2.5C17 17.8 16 19.5 16 22c0 2 .8 3.5 2 4.5.5.4.5 1 .3 1.5l-1 3c-.2.5.2 1 .7 1h6v-17z"
                fill="url(#ai-grad)" fillOpacity="0.25" stroke="url(#ai-grad)" strokeWidth="1.5" strokeLinejoin="round" />
            {/* Brain — right hemisphere */}
            <path d="M24 14c2.5 0 4.5 1 5.8 2.5C31 17.8 32 19.5 32 22c0 2-.8 3.5-2 4.5-.5.4-.5 1-.3 1.5l1 3c.2.5-.2 1-.7 1h-6v-17z"
                fill="url(#ai-grad)" fillOpacity="0.25" stroke="url(#ai-grad)" strokeWidth="1.5" strokeLinejoin="round" />
            {/* Neural connections — left */}
            <path d="M19 20h5M18.5 24h5.5" stroke="url(#ai-grad)" strokeWidth="1.2" strokeLinecap="round" />
            {/* Neural connections — right */}
            <path d="M24 20h5M24 24h5.5" stroke="url(#ai-grad)" strokeWidth="1.2" strokeLinecap="round" />
            {/* Center line */}
            <line x1="24" y1="14" x2="24" y2="32" stroke="url(#ai-grad)" strokeWidth="1" strokeDasharray="2 2" />
            {/* Neural nodes */}
            <circle cx="19" cy="20" r="1.5" fill="url(#ai-grad)" />
            <circle cx="29" cy="20" r="1.5" fill="url(#ai-grad)" />
            <circle cx="18.5" cy="24" r="1.5" fill="url(#ai-grad)" />
            <circle cx="29.5" cy="24" r="1.5" fill="url(#ai-grad)" />
            {/* Sparkle accents */}
            <circle cx="12" cy="16" r="1" fill="url(#ai-grad)" fillOpacity="0.6" />
            <circle cx="36" cy="16" r="1" fill="url(#ai-grad)" fillOpacity="0.6" />
            <circle cx="10" cy="28" r="0.8" fill="url(#ai-grad)" fillOpacity="0.4" />
            <circle cx="38" cy="28" r="0.8" fill="url(#ai-grad)" fillOpacity="0.4" />
            <defs>
                <linearGradient id="ai-grad" x1="2" y1="2" x2="46" y2="46" gradientUnits="userSpaceOnUse">
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
                <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-400">Uršula přemýšlí</span>
                    <div className="flex gap-1.5">
                        <span className="w-2 h-2 bg-neon-fuchsia/60 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                        <span className="w-2 h-2 bg-neon-purple/60 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                        <span className="w-2 h-2 bg-neon-cyan/60 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                    </div>
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
                    const answeredCount = sessionData.answered_keys?.length || 0;
                    loadedMessages.push({
                        role: "assistant",
                        content: answeredCount > 0
                            ? `Vítejte zpět! Máme uloženo **${answeredCount} zodpovězených otázek**. Chcete pokračovat tam, kde jste skončili, nebo doplnit odpovědi na některé otázky?`
                            : `Vítejte zpět! Chcete pokračovat v našem rozhovoru?`,
                        bubbles: [
                            "Pokračovat kde jsem skončil/a",
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

                // Handle multi_messages (sequential bubbles with delays)
                if (data.multi_messages && data.multi_messages.length > 0) {
                    setInitLoading(false);
                    for (let i = 0; i < data.multi_messages.length; i++) {
                        const mm = data.multi_messages[i] as MultiMessage;
                        if (mm.delay_ms > 0) {
                            setSending(true);
                            await new Promise(resolve => setTimeout(resolve, mm.delay_ms));
                        }
                        setSending(false);
                        setMessages(prev => [...prev, {
                            role: "assistant" as const,
                            content: mm.text,
                            bubbles: mm.bubbles || [],
                            progress: 0,
                            timestamp: Date.now(),
                        }]);
                    }
                } else {
                    setMessages([{
                        role: "assistant",
                        content: data.message,
                        bubbles: data.bubbles || [],
                        progress: 0,
                        timestamp: Date.now(),
                    }]);
                    setInitLoading(false);
                }
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

    // Send message to Uršula API via SSE streaming
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
            const res = await fetch(`${API_URL}/api/mart1n/chat/stream`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    session_id: sessionId,
                    company_id: companyId,
                    message: text.trim(),
                }),
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || `HTTP ${res.status}`);
            }

            const reader = res.body?.getReader();
            if (!reader) throw new Error("No stream reader");

            const decoder = new TextDecoder();
            let streamedText = "";
            let streamMsgIndex = -1;
            let buffer = "";

            // Add an empty assistant message for streaming into
            const streamingMsg: Mart1nMessage = {
                role: "assistant",
                content: "",
                bubbles: [],
                progress: 0,
                timestamp: Date.now(),
            };
            setMessages(prev => {
                streamMsgIndex = prev.length;
                return [...prev, streamingMsg];
            });
            setSending(false); // Show the message bubble immediately (streaming)

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });

                // Parse SSE events from buffer
                const lines = buffer.split("\n");
                buffer = lines.pop() || ""; // Keep incomplete line in buffer

                let eventType = "";
                for (const line of lines) {
                    if (line.startsWith("event: ")) {
                        eventType = line.slice(7).trim();
                    } else if (line.startsWith("data: ")) {
                        const data = line.slice(6);

                        if (eventType === "token") {
                            // Streaming text token
                            try {
                                const chunk = JSON.parse(data) as string;
                                streamedText += chunk;
                                setMessages(prev => {
                                    const updated = [...prev];
                                    const idx = streamMsgIndex >= 0 ? streamMsgIndex : updated.length - 1;
                                    if (updated[idx] && updated[idx].role === "assistant") {
                                        updated[idx] = { ...updated[idx], content: streamedText };
                                    }
                                    return updated;
                                });
                            } catch { /* skip malformed token */ }
                        } else if (eventType === "meta") {
                            // Final metadata (bubbles, progress, etc.)
                            try {
                                const meta = JSON.parse(data);

                                // Store bubble overrides
                                if (meta.bubble_overrides && Object.keys(meta.bubble_overrides).length > 0) {
                                    setBubbleOverrides(meta.bubble_overrides);
                                } else {
                                    setBubbleOverrides({});
                                }

                                // Check for Claude multi_messages
                                const claudeMulti = meta.multi_messages || [];
                                if (claudeMulti.length > 0) {
                                    // Replace streamed message with multi_messages
                                    setMessages(prev => {
                                        const updated = [...prev];
                                        const idx = streamMsgIndex >= 0 ? streamMsgIndex : updated.length - 1;
                                        // Replace the streaming message with multi_messages
                                        const multiMsgs: Mart1nMessage[] = claudeMulti.map((mm: MultiMessage, i: number) => ({
                                            role: "assistant" as const,
                                            content: mm.text,
                                            bubbles: (i === claudeMulti.length - 1) ? (mm.bubbles || []) : [],
                                            progress: meta.progress || 0,
                                            timestamp: Date.now() + i,
                                        }));
                                        updated.splice(idx, 1, ...multiMsgs);
                                        return updated;
                                    });
                                } else {
                                    // Update the streamed message with final bubbles/progress
                                    setMessages(prev => {
                                        const updated = [...prev];
                                        const idx = streamMsgIndex >= 0 ? streamMsgIndex : updated.length - 1;
                                        if (updated[idx] && updated[idx].role === "assistant") {
                                            updated[idx] = {
                                                ...updated[idx],
                                                content: streamedText || meta.message || updated[idx].content,
                                                bubbles: meta.bubbles || [],
                                                progress: meta.progress || 0,
                                                isComplete: meta.is_complete || false,
                                            };
                                        }
                                        return updated;
                                    });
                                }

                                // Handle joke messages (prepend before the main message)
                                if (meta.joke_messages && meta.joke_messages.length > 0) {
                                    const jokeInsert = async () => {
                                        for (const joke of meta.joke_messages) {
                                            setSending(true);
                                            await new Promise(r => setTimeout(r, joke.delay_ms || 1500));
                                            setSending(false);
                                            setMessages(prev => {
                                                const updated = [...prev];
                                                const idx = streamMsgIndex >= 0 ? streamMsgIndex : updated.length - 1;
                                                updated.splice(idx, 0, {
                                                    role: "assistant",
                                                    content: joke.text,
                                                    bubbles: [],
                                                    timestamp: Date.now(),
                                                });
                                                streamMsgIndex++;
                                                return updated;
                                            });
                                        }
                                    };
                                    await jokeInsert();
                                }

                                setProgress(meta.progress || 0);
                                if (meta.is_complete) setIsComplete(true);
                            } catch { /* skip malformed meta */ }
                        } else if (eventType === "full") {
                            // Full response (scripted, non-Claude)
                            try {
                                const fullData = JSON.parse(data);
                                setSending(false);

                                if (fullData.bubble_overrides && Object.keys(fullData.bubble_overrides).length > 0) {
                                    setBubbleOverrides(fullData.bubble_overrides);
                                } else {
                                    setBubbleOverrides({});
                                }

                                // Remove the streaming placeholder
                                setMessages(prev => {
                                    const updated = [...prev];
                                    const idx = streamMsgIndex >= 0 ? streamMsgIndex : updated.length - 1;
                                    updated.splice(idx, 1);
                                    return updated;
                                });

                                // Process multi_messages sequentially
                                if (fullData.multi_messages && fullData.multi_messages.length > 0) {
                                    for (let i = 0; i < fullData.multi_messages.length; i++) {
                                        const mm = fullData.multi_messages[i] as MultiMessage;
                                        if (mm.delay_ms > 0) {
                                            setSending(true);
                                            await new Promise(r => setTimeout(r, mm.delay_ms));
                                        }
                                        setSending(false);
                                        setMessages(prev => [...prev, {
                                            role: "assistant",
                                            content: mm.text,
                                            bubbles: mm.bubbles || [],
                                            progress: fullData.progress || 0,
                                            isComplete: i === fullData.multi_messages.length - 1 ? (fullData.is_complete || false) : false,
                                            timestamp: Date.now(),
                                        }]);
                                        if (i < fullData.multi_messages.length - 1) {
                                            setSending(true);
                                            await new Promise(r => setTimeout(r, 600));
                                        }
                                    }
                                } else if (fullData.message) {
                                    setMessages(prev => [...prev, {
                                        role: "assistant",
                                        content: fullData.message,
                                        bubbles: fullData.bubbles || [],
                                        progress: fullData.progress || 0,
                                        isComplete: fullData.is_complete || false,
                                        timestamp: Date.now(),
                                    }]);
                                }

                                setProgress(fullData.progress || 0);
                                if (fullData.is_complete) setIsComplete(true);
                            } catch { /* skip malformed full */ }
                        } else if (eventType === "error") {
                            try {
                                const err = JSON.parse(data);
                                throw new Error(err.detail || "Chyba serveru");
                            } catch (e) {
                                if (e instanceof Error) throw e;
                            }
                        }
                        eventType = "";
                    }
                }
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
        }
    }, [sending, isComplete, sessionId, companyId]);

    // Re-focus input after sending finishes
    useEffect(() => {
        if (!sending && !isComplete && !initLoading) {
            // Small delay to ensure disabled prop is cleared after React render
            const t = setTimeout(() => inputRef.current?.focus(), 50);
            return () => clearTimeout(t);
        }
    }, [sending, isComplete, initLoading]);

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
                            <p className="text-xs text-slate-500">A.I. Asistentka</p>
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
                                placeholder={isComplete ? "Analýza je dokončena" : "Nevidíte správnou odpověď? Napište nám ji."}
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
                    <p className="text-[10px] text-white/90 mt-2 text-center leading-relaxed">
                        Uršula je umělá inteligence (čl. 50 AI Act). Vaše data jsou šifrována a&nbsp;zůstávají pouze mezi Vámi a&nbsp;AIshield — žádná třetí strana k&nbsp;nim nemá přístup. Porušení ochrany osobních údajů dle GDPR (nařízení EU&nbsp;2016/679) podléhá pokutě až&nbsp;20&nbsp;mil.&nbsp;€ nebo 4&nbsp;% ročního obratu.
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
