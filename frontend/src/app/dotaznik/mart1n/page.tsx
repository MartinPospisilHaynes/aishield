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
                    <span className="text-sm text-slate-400">Uršula přemýšlí</span>
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

    // Voice input state
    const [isRecording, setIsRecording] = useState(false);
    const [isTranscribing, setIsTranscribing] = useState(false);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);
    const [audioLevels, setAudioLevels] = useState<number[]>(new Array(24).fill(4));
    const analyserRef = useRef<AnalyserNode | null>(null);
    const animFrameRef = useRef<number>(0);
    const sendMessageRef = useRef<(text: string) => void>(() => {});

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
                            "Opravit některou z předchozích odpovědí",
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
                                    // Replace streamed message with multi_messages.
                                    // If the streamed text has content and differs from the first
                                    // multi_message, keep it as a separate bubble so it's not lost.
                                    setMessages(prev => {
                                        const updated = [...prev];
                                        const idx = streamMsgIndex >= 0 ? streamMsgIndex : updated.length - 1;
                                        const existingText = (updated[idx]?.content || "").trim();
                                        const firstMmText = (claudeMulti[0]?.text || "").trim();

                                        const multiMsgs: Mart1nMessage[] = claudeMulti.map((mm: MultiMessage, i: number) => ({
                                            role: "assistant" as const,
                                            content: mm.text,
                                            bubbles: (i === claudeMulti.length - 1) ? (mm.bubbles || []) : [],
                                            progress: meta.progress || 0,
                                            timestamp: Date.now() + i + 1,
                                        }));

                                        if (existingText && existingText !== firstMmText) {
                                            // Keep the streamed message, update it, then append multi_messages after
                                            updated[idx] = {
                                                ...updated[idx],
                                                bubbles: [],
                                                progress: meta.progress || 0,
                                            };
                                            updated.splice(idx + 1, 0, ...multiMsgs);
                                        } else {
                                            // Streamed text matches first multi_message or is empty — replace
                                            updated.splice(idx, 1, ...multiMsgs);
                                        }
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
            console.warn("[MART1N] Request failed, will auto-retry:", errorMsg);

            // Auto-retry: wait for backend to come back (systemd restarts in ~5s)
            const MAX_RETRIES = 3;
            const RETRY_DELAYS = [5000, 8000, 12000]; // escalating delays

            // Show "thinking" state while retrying
            setMessages(prev => {
                const updated = [...prev];
                // Remove the streaming placeholder if it exists
                const lastIdx = updated.length - 1;
                if (lastIdx >= 0 && updated[lastIdx].role === "assistant" && !updated[lastIdx].content) {
                    updated.splice(lastIdx, 1);
                }
                return [...updated, {
                    role: "assistant",
                    content: "Moment, mám drobné technické potíže...",
                    bubbles: [],
                    timestamp: Date.now(),
                }];
            });

            let retrySuccess = false;
            for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
                await new Promise(r => setTimeout(r, RETRY_DELAYS[attempt]));

                // Check if backend is alive via health endpoint
                try {
                    const healthRes = await fetch(`${API_URL}/health`, { signal: AbortSignal.timeout(3000) });
                    if (!healthRes.ok) continue;
                } catch {
                    continue; // Backend still down, try again
                }

                // Backend is back — retry the original message
                try {
                    const retryRes = await fetch(`${API_URL}/api/mart1n/chat/stream`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            session_id: sessionId,
                            company_id: companyId,
                            message: text.trim(),
                        }),
                    });

                    if (!retryRes.ok) continue;

                    // Success — remove the "technické potíže" message
                    setMessages(prev => {
                        const updated = [...prev];
                        const potizeIdx = updated.findIndex(m =>
                            m.role === "assistant" && m.content === "Moment, mám drobné technické potíže..."
                        );
                        if (potizeIdx >= 0) updated.splice(potizeIdx, 1);
                        return updated;
                    });

                    // Add recovery message + process the retried response
                    setMessages(prev => [...prev, {
                        role: "assistant",
                        content: "Omlouvám se, měla jsem menší technické potíže, ale už jsem zpět a můžeme pokračovat tam, kde jsme skončili.",
                        bubbles: [],
                        timestamp: Date.now(),
                    }]);

                    // Process the retry stream response
                    const retryReader = retryRes.body?.getReader();
                    if (retryReader) {
                        const retryDecoder = new TextDecoder();
                        let retryBuffer = "";
                        let retryStreamedText = "";
                        let retryStreamMsgIndex = -1;

                        // Add streaming placeholder
                        setMessages(prev => {
                            retryStreamMsgIndex = prev.length;
                            return [...prev, { role: "assistant", content: "", bubbles: [], timestamp: Date.now() }];
                        });

                        while (true) {
                            const { done, value } = await retryReader.read();
                            if (done) break;
                            retryBuffer += retryDecoder.decode(value, { stream: true });

                            const lines = retryBuffer.split("\n");
                            retryBuffer = lines.pop() || "";
                            let retryEventType = "";

                            for (const line of lines) {
                                if (line.startsWith("event: ")) {
                                    retryEventType = line.slice(7).trim();
                                } else if (line.startsWith("data: ")) {
                                    const retryData = line.slice(6);
                                    if (retryEventType === "token") {
                                        try {
                                            const t = JSON.parse(retryData);
                                            retryStreamedText += t.token || "";
                                            setMessages(prev => {
                                                const u = [...prev];
                                                const idx = retryStreamMsgIndex >= 0 ? retryStreamMsgIndex : u.length - 1;
                                                if (u[idx] && u[idx].role === "assistant") {
                                                    u[idx] = { ...u[idx], content: retryStreamedText };
                                                }
                                                return u;
                                            });
                                        } catch { /* skip */ }
                                    } else if (retryEventType === "meta") {
                                        try {
                                            const meta = JSON.parse(retryData);
                                            setMessages(prev => {
                                                const u = [...prev];
                                                const idx = retryStreamMsgIndex >= 0 ? retryStreamMsgIndex : u.length - 1;
                                                if (u[idx] && u[idx].role === "assistant") {
                                                    u[idx] = {
                                                        ...u[idx],
                                                        content: retryStreamedText || meta.message || u[idx].content,
                                                        bubbles: meta.bubbles || [],
                                                        progress: meta.progress || 0,
                                                        isComplete: meta.is_complete || false,
                                                    };
                                                }
                                                return u;
                                            });
                                            setProgress(meta.progress || 0);
                                            if (meta.is_complete) setIsComplete(true);
                                        } catch { /* skip */ }
                                    } else if (retryEventType === "full") {
                                        try {
                                            const fullData = JSON.parse(retryData);
                                            // Remove streaming placeholder
                                            setMessages(prev => {
                                                const u = [...prev];
                                                const idx = retryStreamMsgIndex >= 0 ? retryStreamMsgIndex : u.length - 1;
                                                u.splice(idx, 1);
                                                return u;
                                            });
                                            // Show multi_messages
                                            if (fullData.multi_messages?.length > 0) {
                                                for (const mm of fullData.multi_messages) {
                                                    if (mm.delay_ms > 0) await new Promise(r => setTimeout(r, mm.delay_ms));
                                                    setMessages(prev => [...prev, {
                                                        role: "assistant", content: mm.text, bubbles: mm.bubbles || [],
                                                        progress: fullData.progress || 0, timestamp: Date.now(),
                                                    }]);
                                                }
                                            }
                                            setProgress(fullData.progress || 0);
                                            if (fullData.is_complete) setIsComplete(true);
                                        } catch { /* skip */ }
                                    }
                                    retryEventType = "";
                                }
                            }
                        }
                    }

                    retrySuccess = true;
                    break;
                } catch {
                    continue; // Retry failed, try again
                }
            }

            if (!retrySuccess) {
                // All retries exhausted — show manual retry option
                setMessages(prev => {
                    const updated = [...prev];
                    const potizeIdx = updated.findIndex(m =>
                        m.role === "assistant" && m.content === "Moment, mám drobné technické potíže..."
                    );
                    if (potizeIdx >= 0) updated.splice(potizeIdx, 1);
                    return [...updated, {
                        role: "assistant",
                        content: "Omlouvám se, mám delší technický výpadek. Zkuste to prosím za chvilku znovu, nebo zavolejte na **732 716 141**.",
                        bubbles: ["Zkusit znovu"],
                        timestamp: Date.now(),
                    }];
                });
            }
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

    // Keep sendMessageRef in sync for use in MediaRecorder.onstop closure
    sendMessageRef.current = sendMessage;

    // Handle bubble click (with optional text override for NE→ANO swap)
    const handleBubbleClick = useCallback((bubble: string) => {
        const displayText = bubbleOverrides[bubble] || bubble;
        sendMessage(bubble, displayText);
    }, [sendMessage, bubbleOverrides]);

    // Voice recording — start/stop toggle
    const toggleRecording = useCallback(async () => {
        if (isRecording) {
            // Stop recording
            mediaRecorderRef.current?.stop();
            return;
        }

        // Check if browser supports getUserMedia
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            setMessages(prev => {
                const last = prev[prev.length - 1];
                if (last?.content?.includes("Hlasový vstup není podporován")) return prev;
                return [...prev, {
                    role: "assistant" as const,
                    content: "⚠️ **Hlasový vstup není podporován.** Váš prohlížeč nepodporuje nahrávání zvuku. Zkuste Chrome, Edge nebo Safari.",
                    bubbles: [],
                    timestamp: Date.now(),
                }];
            });
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            // ── Audio Visualizer (Web Audio API) ──
            const audioCtx = new AudioContext();
            const source = audioCtx.createMediaStreamSource(stream);
            const analyser = audioCtx.createAnalyser();
            analyser.fftSize = 64;
            analyser.smoothingTimeConstant = 0.6;
            source.connect(analyser);
            analyserRef.current = analyser;

            const dataArray = new Uint8Array(analyser.frequencyBinCount);
            const updateLevels = () => {
                analyser.getByteFrequencyData(dataArray);
                // Pick 24 bars spread across the frequency range
                const bars: number[] = [];
                const step = Math.floor(dataArray.length / 24);
                for (let i = 0; i < 24; i++) {
                    const val = dataArray[i * step] || 0;
                    // Map 0-255 to 4-32 (min 4px height)
                    bars.push(Math.max(4, (val / 255) * 32));
                }
                setAudioLevels(bars);
                animFrameRef.current = requestAnimationFrame(updateLevels);
            };
            animFrameRef.current = requestAnimationFrame(updateLevels);

            // Detect supported mimeType
            let mimeType = "audio/webm";
            if (typeof MediaRecorder.isTypeSupported === "function") {
                if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
                    mimeType = "audio/webm;codecs=opus";
                } else if (MediaRecorder.isTypeSupported("audio/mp4")) {
                    mimeType = "audio/mp4"; // Safari fallback
                } else if (MediaRecorder.isTypeSupported("audio/ogg;codecs=opus")) {
                    mimeType = "audio/ogg;codecs=opus";
                }
            }

            const mediaRecorder = new MediaRecorder(stream, { mimeType });
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) audioChunksRef.current.push(e.data);
            };

            mediaRecorder.onstop = async () => {
                // Stop visualizer
                cancelAnimationFrame(animFrameRef.current);
                analyserRef.current = null;
                audioCtx.close();
                setAudioLevels(new Array(24).fill(4));

                // Stop all tracks so mic indicator disappears
                stream.getTracks().forEach((t) => t.stop());
                setIsRecording(false);

                const blob = new Blob(audioChunksRef.current, { type: mimeType });
                if (blob.size < 100) return; // too short, ignore

                setIsTranscribing(true);
                try {
                    const ext = mimeType.includes("mp4") ? "mp4" : mimeType.includes("ogg") ? "ogg" : "webm";
                    const form = new FormData();
                    form.append("file", blob, `recording.${ext}`);
                    const res = await fetch(`${API_URL}/api/transcribe`, {
                        method: "POST",
                        body: form,
                    });
                    if (!res.ok) {
                        const errData = await res.json().catch(() => ({}));
                        throw new Error(errData.detail || "Transcription failed");
                    }
                    const data = await res.json();
                    if (data.text?.trim()) {
                        // Auto-send transcribed text
                        sendMessageRef.current(data.text.trim());
                    }
                } catch (err) {
                    console.error("Transcription error:", err);
                } finally {
                    setIsTranscribing(false);
                }
            };

            mediaRecorder.start();
            setIsRecording(true);
        } catch (err) {
            console.error("Microphone access error:", err);
            const isDenied = err instanceof DOMException && (err.name === "NotAllowedError" || err.name === "PermissionDeniedError");
            const isNotFound = err instanceof DOMException && err.name === "NotFoundError";
            let micMsg = "⚠️ **Mikrofon není dostupný.**";
            if (isDenied) {
                micMsg = "⚠️ **Přístup k mikrofonu byl zamítnut.** \n\n**Chrome:** Klikněte na ikonu 🔒 vlevo v adresním řádku → \"Nastavení webu\" → Mikrofon → \"Povolit\" → obnovte stránku (F5).\n\n**Safari:** Safari → Nastavení → Webové stránky → Mikrofon → zvolte \"Povolit\".\n\n**macOS:** Nastavení systému → Soukromí a zabezpečení → Mikrofon → zaškrtněte prohlížeč.";
            } else if (isNotFound) {
                micMsg = "⚠️ **Mikrofon nebyl nalezen.** Připojte mikrofon nebo sluchátka s mikrofonem a zkuste to znovu.";
            } else {
                micMsg = "⚠️ **Mikrofon není dostupný.** Povolte přístup k mikrofonu v nastavení prohlížeče a zkuste to znovu.";
            }
            // Don't spam — only add if last message isn't already a mic error
            setMessages(prev => {
                const last = prev[prev.length - 1];
                if (last?.content?.includes("Mikrofon") || last?.content?.includes("mikrofonu")) return prev;
                return [...prev, {
                    role: "assistant" as const,
                    content: micMsg,
                    bubbles: [],
                    timestamp: Date.now(),
                }];
            });
        }
    }, [isRecording]);

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

                    {/* Completion card — "Ukončit Uršulu" */}
                    {isComplete && (
                        <div className="glass border-purple-500/20 bg-purple-500/5 p-6 text-center mt-6">
                            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-purple-500/10 flex items-center justify-center">
                                <svg className="w-8 h-8 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                            <h3 className="text-lg font-bold text-white mb-2">Děkujeme za Váš čas!</h3>
                            <p className="text-sm text-slate-400 mb-4">
                                Všechny odpovědi byly uloženy. Na dashboardu uvidíte průběh zpracování.
                            </p>
                            <button
                                onClick={() => router.push("/dashboard")}
                                className="px-8 py-3 rounded-xl font-semibold text-white
                                           bg-gradient-to-r from-[#a855f7] to-[#7c3aed]
                                           hover:shadow-lg hover:shadow-purple-500/25
                                           transition-all duration-200 text-sm"
                            >
                                Ukončit Uršulu
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* ── Input Area ── */}
            <div className="flex-shrink-0 border-t border-white/[0.06] bg-dark-900/80 backdrop-blur-xl">
                <div className="max-w-3xl mx-auto px-4 py-3">
                    <div className="flex items-center gap-2">
                        <div className="flex-1 relative">
                            {isRecording ? (
                                /* ── Audio Waveform Visualizer ── */
                                <div className="w-full h-[46px] rounded-xl border border-purple-500/30 bg-dark-800 flex items-center justify-center gap-[3px] px-4 overflow-hidden">
                                    {audioLevels.map((h, i) => (
                                        <div
                                            key={i}
                                            className="w-[3px] rounded-full bg-gradient-to-t from-[#a855f7] to-[#c084fc] transition-all duration-75"
                                            style={{ height: `${h}px` }}
                                        />
                                    ))}
                                    <span className="ml-3 text-xs text-purple-400 whitespace-nowrap animate-pulse">● Nahrávám...</span>
                                </div>
                            ) : (
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
                            )}
                        </div>

                        {/* Mic button */}
                        <div className="relative flex-shrink-0">
                            <button
                                onClick={toggleRecording}
                                disabled={isTranscribing || sending || isComplete || initLoading}
                                className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all
                                    ${isRecording
                                        ? "bg-red-500 hover:bg-red-600 shadow-lg shadow-red-500/30"
                                        : isTranscribing
                                            ? "bg-amber-500/30 cursor-wait"
                                            : "bg-gradient-to-r from-[#a855f7] to-[#7c3aed] shadow-lg shadow-purple-500/25 hover:brightness-110"}
                                    disabled:cursor-not-allowed disabled:hover:brightness-100`}
                                title={isRecording ? "Zastavit nahrávání" : "Hlasový vstup"}
                            >
                                {isTranscribing ? (
                                    <svg className="w-4 h-4 text-amber-400 animate-spin" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                                    </svg>
                                ) : (
                                    <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z" />
                                    </svg>
                                )}
                            </button>
                            {/* Info "i" badge — tooltip only on this badge */}
                            <span className="group/info absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full bg-slate-700 border border-slate-600
                                             text-[8px] font-bold text-slate-300 flex items-center justify-center
                                             cursor-help select-none pointer-events-auto z-10">
                                i
                                <span className="absolute bottom-full right-0 mb-2 w-56 p-2.5 rounded-lg bg-dark-800 border border-white/[0.1]
                                                text-[10px] text-slate-400 leading-relaxed shadow-xl font-normal
                                                opacity-0 invisible group-hover/info:opacity-100 group-hover/info:visible transition-all duration-200
                                                pointer-events-none z-50">
                                    🎙 Hlasový vstup — audio se odesílá do&nbsp;OpenAI (USA) k&nbsp;přepisu na text.
                                    Nahrávka se po přepisu okamžitě smaže.
                                </span>
                            </span>
                        </div>

                        {/* Send button — identical styling to mic button */}
                        <button
                            onClick={() => sendMessage(input)}
                            disabled={!input.trim() || sending || isComplete || initLoading}
                            title="Odeslat zprávu"
                            className="w-10 h-10 rounded-xl flex items-center justify-center transition-all
                                       bg-gradient-to-r from-[#a855f7] to-[#7c3aed] shadow-lg shadow-purple-500/25
                                       hover:brightness-110
                                       disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:brightness-100"
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
