"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { usePathname } from "next/navigation";

/* ─── Types ─── */
interface Message {
    role: "user" | "assistant";
    content: string;
}

/* ─── API config ─── */
const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://api.aishield.cz";

/* ─── Session ID (persistent per browser tab) ─── */
function getSessionId(): string {
    if (typeof window === "undefined") return "";
    let id = sessionStorage.getItem("chat_session_id");
    if (!id) {
        id = crypto.randomUUID();
        sessionStorage.setItem("chat_session_id", id);
    }
    return id;
}

/* ─── Simple markdown-like rendering ─── */
function renderContent(text: string) {
    // Split into paragraphs, handle **bold**, bullet points
    const lines = text.split("\n");
    const elements: React.ReactNode[] = [];
    let listItems: string[] = [];

    const flushList = () => {
        if (listItems.length > 0) {
            elements.push(
                <ul key={`list-${elements.length}`} className="space-y-1 my-1.5">
                    {listItems.map((li, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm">
                            <span className="text-fuchsia-400 mt-0.5 flex-shrink-0">&#8226;</span>
                            <span dangerouslySetInnerHTML={{ __html: boldify(li) }} />
                        </li>
                    ))}
                </ul>
            );
            listItems = [];
        }
    };

    const boldify = (s: string) =>
        s.replace(/\*\*(.+?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
            .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" class="text-fuchsia-400 underline hover:text-fuchsia-300">$1</a>');

    lines.forEach((line, i) => {
        const trimmed = line.trim();
        if (trimmed.match(/^[-•*]\s/)) {
            listItems.push(trimmed.replace(/^[-•*]\s/, ""));
        } else if (trimmed.match(/^\d+[.)]\s/)) {
            listItems.push(trimmed.replace(/^\d+[.)]\s/, ""));
        } else {
            flushList();
            if (trimmed) {
                elements.push(
                    <p key={`p-${i}`} className="text-sm leading-relaxed my-1" dangerouslySetInnerHTML={{ __html: boldify(trimmed) }} />
                );
            }
        }
    });
    flushList();
    return elements;
}

/* ─── Quick reply suggestions ─── */
const QUICK_REPLIES = [
    "Co je AI Act?",
    "Jak funguje skenování?",
    "Jaké jsou ceny?",
    "Jaké dokumenty dostanu?",
];

/* ═══════════════════════════════════════════════
   ChatWidget — floating bubble + chat panel
   ═══════════════════════════════════════════════ */
export default function ChatWidget() {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [hasGreeted, setHasGreeted] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    const pathname = usePathname();

    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, isLoading]);

    // Focus input when opened
    useEffect(() => {
        if (isOpen && inputRef.current) {
            setTimeout(() => inputRef.current?.focus(), 100);
        }
    }, [isOpen]);

    // Send greeting when first opened
    useEffect(() => {
        if (isOpen && !hasGreeted && messages.length === 0) {
            setHasGreeted(true);
            setMessages([
                {
                    role: "assistant",
                    content:
                        "Dobrý den, jsem umělá inteligence těchto webových stránek a pomůžu Vám s čímkoliv budete potřebovat.\n\nMůžete se mě zeptat například na:\n- Co je AI Act a proč se Vás týká\n- Jak funguje skenování webu\n- Jaké dokumenty dostanete\n- Ceny a balíčky služeb",
                },
            ]);
        }
    }, [isOpen, hasGreeted, messages.length]);

    // Send message
    const sendMessage = useCallback(
        async (text: string) => {
            const trimmed = text.trim();
            if (!trimmed || isLoading) return;

            const userMsg: Message = { role: "user", content: trimmed };
            const newMessages = [...messages, userMsg];
            setMessages(newMessages);
            setInput("");
            setIsLoading(true);

            try {
                const res = await fetch(`${API_URL}/api/chat`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        session_id: getSessionId(),
                        messages: newMessages.map((m) => ({
                            role: m.role,
                            content: m.content,
                        })),
                        page_url: pathname,
                    }),
                });

                if (!res.ok) {
                    if (res.status === 429) {
                        setMessages((prev) => [
                            ...prev,
                            {
                                role: "assistant",
                                content: "Posíláte příliš mnoho zpráv najednou. Zkuste to prosím za chvíli.",
                            },
                        ]);
                    } else {
                        throw new Error(`HTTP ${res.status}`);
                    }
                } else {
                    const data = await res.json();
                    setMessages((prev) => [
                        ...prev,
                        { role: "assistant", content: data.reply },
                    ]);
                }
            } catch {
                setMessages((prev) => [
                    ...prev,
                    {
                        role: "assistant",
                        content:
                            "Omlouvám se, momentálně mám technické potíže. Zkuste to prosím za chvíli, nebo nás kontaktujte na info@aishield.cz.",
                    },
                ]);
            } finally {
                setIsLoading(false);
            }
        },
        [messages, isLoading, pathname]
    );

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        sendMessage(input);
    };

    return (
        <>
            {/* ── Floating bubble ── */}
            {!isOpen && (
                <button
                    onClick={() => setIsOpen(true)}
                    className="fixed bottom-6 right-6 z-50 flex items-center justify-center w-14 h-14 rounded-full
                        bg-gradient-to-br from-fuchsia-600 to-purple-700 shadow-lg shadow-fuchsia-500/25
                        hover:shadow-fuchsia-500/40 hover:scale-105 transition-all duration-200
                        animate-[bounce_3s_ease-in-out_infinite]"
                    aria-label="Otevřít chat"
                >
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
                    </svg>
                    {/* Pulse dot */}
                    <span className="absolute top-0 right-0 w-3.5 h-3.5 rounded-full bg-green-400 border-2 border-dark-900" />
                </button>
            )}

            {/* ── Chat panel ── */}
            {isOpen && (
                <div className="fixed bottom-4 right-4 z-50 flex flex-col w-[380px] max-w-[calc(100vw-2rem)] h-[560px] max-h-[calc(100vh-6rem)]
                    rounded-2xl border border-white/[0.08] bg-dark-950/95 backdrop-blur-xl shadow-2xl shadow-black/50
                    overflow-hidden animate-in slide-in-from-bottom-4 duration-300">

                    {/* ── Header ── */}
                    <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-fuchsia-600/10 to-purple-600/10 border-b border-white/[0.06]">
                        <div className="flex items-center gap-3">
                            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-fuchsia-600 to-purple-700 flex items-center justify-center flex-shrink-0">
                                <svg className="w-5 h-5 text-white" viewBox="0 0 32 32" fill="none">
                                    <path d="M16 2L4 7v9c0 7.73 5.12 14.95 12 17 6.88-2.05 12-9.27 12-17V7L16 2z" fill="url(#shg)" fillOpacity="0.3" stroke="url(#shg)" strokeWidth="1.5" />
                                    <path d="M12 16l3 3 5-6" stroke="url(#shg)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                    <defs><linearGradient id="shg" x1="4" y1="2" x2="28" y2="28"><stop stopColor="#d946ef" /><stop offset="1" stopColor="#06b6d4" /></linearGradient></defs>
                                </svg>
                            </div>
                            <div>
                                <p className="text-sm font-semibold text-white">AIshield</p>
                                <p className="text-xs text-slate-400">Umělá inteligence</p>
                            </div>
                        </div>
                        <button
                            onClick={() => setIsOpen(false)}
                            className="p-1.5 rounded-lg hover:bg-white/[0.05] transition-colors"
                            aria-label="Zavřít chat"
                        >
                            <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>

                    {/* ── Messages ── */}
                    <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-4 scrollbar-thin">
                        {messages.map((msg, i) => (
                            <div
                                key={i}
                                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                            >
                                <div
                                    className={`max-w-[85%] rounded-2xl px-4 py-2.5 ${msg.role === "user"
                                            ? "bg-fuchsia-600/20 border border-fuchsia-500/20 text-slate-200"
                                            : "bg-white/[0.04] border border-white/[0.06] text-slate-300"
                                        }`}
                                >
                                    {msg.role === "assistant" ? renderContent(msg.content) : (
                                        <p className="text-sm leading-relaxed">{msg.content}</p>
                                    )}
                                </div>
                            </div>
                        ))}

                        {/* Loading indicator */}
                        {isLoading && (
                            <div className="flex justify-start">
                                <div className="bg-white/[0.04] border border-white/[0.06] rounded-2xl px-4 py-3">
                                    <div className="flex gap-1.5">
                                        <span className="w-2 h-2 rounded-full bg-fuchsia-400/60 animate-bounce [animation-delay:0ms]" />
                                        <span className="w-2 h-2 rounded-full bg-fuchsia-400/60 animate-bounce [animation-delay:150ms]" />
                                        <span className="w-2 h-2 rounded-full bg-fuchsia-400/60 animate-bounce [animation-delay:300ms]" />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Quick replies — show only when just greeting is shown */}
                        {messages.length === 1 && messages[0].role === "assistant" && !isLoading && (
                            <div className="flex flex-wrap gap-2 pt-1">
                                {QUICK_REPLIES.map((qr) => (
                                    <button
                                        key={qr}
                                        onClick={() => sendMessage(qr)}
                                        className="text-xs px-3 py-1.5 rounded-full border border-fuchsia-500/20 bg-fuchsia-500/5
                                            text-fuchsia-300 hover:bg-fuchsia-500/10 hover:border-fuchsia-500/30 transition-all"
                                    >
                                        {qr}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* ── AI disclosure ── */}
                    <div className="px-4 py-1.5 text-center border-t border-white/[0.04]">
                        <p className="text-[10px] text-slate-600">
                            Odpov\u00edd\u00e1 um\u011bl\u00e1 inteligence &middot; Informace maj\u00ed orienta\u010dn\u00ed charakter
                        </p>
                    </div>

                    {/* ── Input ── */}
                    <form onSubmit={handleSubmit} className="flex items-center gap-2 px-3 py-3 border-t border-white/[0.06] bg-dark-950/80">
                        <input
                            ref={inputRef}
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Napište dotaz..."
                            maxLength={500}
                            disabled={isLoading}
                            className="flex-1 bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-2.5 text-sm text-white
                                placeholder:text-slate-500 focus:outline-none focus:ring-1 focus:ring-fuchsia-500/40
                                focus:border-fuchsia-500/30 disabled:opacity-50 transition-all"
                        />
                        <button
                            type="submit"
                            disabled={!input.trim() || isLoading}
                            className="flex-shrink-0 p-2.5 rounded-xl bg-fuchsia-600/20 border border-fuchsia-500/20
                                text-fuchsia-400 hover:bg-fuchsia-600/30 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
                            </svg>
                        </button>
                    </form>
                </div>
            )}
        </>
    );
}
