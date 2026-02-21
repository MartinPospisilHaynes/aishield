"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { usePathname } from "next/navigation";
import { createClient } from "@/lib/supabase-browser";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ─── Types ─── */
interface ChatMsg {
    role: "user" | "assistant";
    text: string;
    bubbles?: string[];
    ts: number;
}
interface MultiMsg {
    text: string;
    delay_ms: number;
    bubbles?: string[];
}

/* ═══════════════════════════════
   Simple markdown renderer
   ═══════════════════════════════ */
function Md({ text }: { text: string }) {
    const paras = text.split(/\n\n+/);
    return (
        <>
            {paras.map((p, pi) => {
                const lines = p.split("\n");
                // Detect list: standard bullets (-•*) OR emoji-prefixed lines (📋, ✅, 🌐…)
                const emojiLineRe = /^[\p{Emoji_Presentation}\p{Extended_Pictographic}]\s/u;
                const bulletRe = /^[-•*]\s/;
                const isListLine = (l: string) => {
                    const trimmed = l.trim();
                    return bulletRe.test(trimmed) || emojiLineRe.test(trimmed);
                };
                const isList = lines.every(
                    (l) => isListLine(l) || !l.trim()
                );
                if (isList) {
                    const items = lines.filter((l) => isListLine(l));
                    return (
                        <ul
                            key={pi}
                            className="list-none space-y-0.5 my-1 text-[13px] leading-relaxed"
                        >
                            {items.map((it, ii) => {
                                const trimmed = it.trim();
                                // Strip standard bullet prefix, keep emoji prefix as-is
                                const content = bulletRe.test(trimmed)
                                    ? trimmed.replace(/^[-•*]\s/, "")
                                    : trimmed;
                                return (
                                    <li key={ii}>
                                        {boldify(content)}
                                    </li>
                                );
                            })}
                        </ul>
                    );
                }
                return (
                    <p
                        key={pi}
                        className="text-[13px] leading-relaxed mb-1.5 last:mb-0"
                    >
                        {boldify(p.replace(/\n/g, " "))}
                    </p>
                );
            })}
        </>
    );
}

function boldify(t: string) {
    return t.split(/\*\*(.*?)\*\*/g).map((s, i) =>
        i % 2 === 1 ? (
            <strong key={i} className="font-semibold text-white">
                {s}
            </strong>
        ) : (
            <span key={i}>{s}</span>
        )
    );
}

/* ═══════════════════════════════
   Uršula avatar (shield + M)
   ═══════════════════════════════ */
function UAvatar({ s = 28 }: { s?: number }) {
    return (
        <div className="flex-shrink-0" style={{ width: s, height: s }}>
            <svg
                width={s}
                height={s}
                viewBox="0 0 32 32"
                fill="none"
            >
                <path
                    d="M16 2L4 7v9c0 7.5 5.5 14 12 16 6.5-2 12-8.5 12-16V7L16 2z"
                    fill="url(#ug)"
                    fillOpacity=".2"
                    stroke="url(#ug)"
                    strokeWidth="1.5"
                    strokeLinejoin="round"
                />
                <path
                    d="M10 20V12l3 4.5L16 12l3 4.5L22 12v8"
                    stroke="url(#ug)"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    fill="none"
                />
                <defs>
                    <linearGradient
                        id="ug"
                        x1="4"
                        y1="2"
                        x2="28"
                        y2="30"
                        gradientUnits="userSpaceOnUse"
                    >
                        <stop stopColor="#e879f9" />
                        <stop offset=".5" stopColor="#a855f7" />
                        <stop offset="1" stopColor="#22d3ee" />
                    </linearGradient>
                </defs>
            </svg>
        </div>
    );
}

/* ═══════════════════════════════
   Typing dots (3 bouncing dots)
   ═══════════════════════════════ */
function Dots() {
    return (
        <div className="flex items-end gap-2">
            <UAvatar s={24} />
            <div className="bg-white/[0.06] border border-white/[0.08] rounded-2xl rounded-bl-sm px-4 py-3">
                <div className="flex items-center gap-2">
                    <span className="text-[11px] text-slate-500">Uršula si zapisuje vaše odpovědi a přemýšlí nad další otázkou</span>
                    <div className="flex gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-fuchsia-400/60 animate-bounce [animation-delay:0ms]" />
                        <span className="w-1.5 h-1.5 rounded-full bg-purple-400/60 animate-bounce [animation-delay:150ms]" />
                        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400/60 animate-bounce [animation-delay:300ms]" />
                    </div>
                </div>
            </div>
        </div>
    );
}

/* ═══════════════════════════════════════════════
   UrsulaChat — floating messenger-style widget
   ═══════════════════════════════════════════════ */
export default function UrsulaChat() {
    const pathname = usePathname();

    /* State */
    const [open, setOpen] = useState(false);
    const [msgs, setMsgs] = useState<ChatMsg[]>([]);
    const [input, setInput] = useState("");
    const [sending, setSending] = useState(false);
    const [sid, setSid] = useState("");
    const [cid, setCid] = useState("");
    const [progress, setProgress] = useState(0);
    const [done, setDone] = useState(false);
    const [loading, setLoading] = useState(false);
    const [inited, setInited] = useState(false);
    const [overrides, setOverrides] = useState<Record<string, string>>({});

    const scrollRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    /* Hide the floating bubble on the full-page dotaznik (fallback page) */
    const onDotaznikPage = pathname === "/dotaznik/mart1n";

    /* ── External trigger: window.dispatchEvent(new CustomEvent("openUrsulaChat")) ── */
    useEffect(() => {
        const handler = (e: Event) => {
            const detail = (e as CustomEvent).detail;
            if (detail?.companyId) setCid(detail.companyId);
            setOpen(true);
        };
        window.addEventListener("openUrsulaChat", handler);
        return () => window.removeEventListener("openUrsulaChat", handler);
    }, []);

    /* ── Auto-scroll to newest message ── */
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [msgs, sending]);

    /* ── Focus input when opened ── */
    useEffect(() => {
        if (open && inputRef.current) {
            setTimeout(() => inputRef.current?.focus(), 250);
        }
    }, [open]);

    /* ── Resolve company_id (Supabase auth → UUID fallback) ── */
    useEffect(() => {
        if (!open || cid) return;
        (async () => {
            try {
                const sb = createClient();
                const {
                    data: { user },
                } = await sb.auth.getUser();
                if (user) {
                    const { data } = await sb
                        .from("companies")
                        .select("id")
                        .eq("email", user.email)
                        .limit(1);
                    if (data?.length) {
                        setCid(data[0].id);
                        return;
                    }
                }
            } catch {
                /* ignore */
            }
            setCid(crypto.randomUUID());
        })();
    }, [open, cid]);

    /* ── Init or resume session ── */
    useEffect(() => {
        if (!open || !cid || inited) return;
        setInited(true);
        setLoading(true);

        (async () => {
            /* Try resuming existing session */
            try {
                const r = await fetch(
                    `${API}/api/mart1n/session/${cid}`
                );
                const d = await r.json();
                if (d.has_session && d.messages?.length) {
                    setSid(d.session_id);
                    setProgress(d.progress || 0);
                    const loaded: ChatMsg[] = d.messages.map(
                        (m: { role: string; content: string }) => ({
                            role: m.role as "user" | "assistant",
                            text: m.content,
                            ts: Date.now(),
                        })
                    );
                    const pct = d.progress || 0;
                    loaded.push({
                        role: "assistant",
                        text:
                            `Vítejte zpět! Váš dotazník je na **${pct}%**. ` +
                            `Chcete pokračovat tam, kde jste skončili?`,
                        bubbles: [
                            "Pokračovat kde jsem skončil/a",
                            "Začít od začátku",
                        ],
                        ts: Date.now(),
                    });
                    setMsgs(loaded);
                    setLoading(false);
                    return;
                }
            } catch {
                /* no existing session — continue to fresh init */
            }

            /* Fresh init */
            try {
                const r = await fetch(`${API}/api/mart1n/init`);
                const d = await r.json();
                setSid(d.session_id || crypto.randomUUID());
                setMsgs([
                    {
                        role: "assistant",
                        text: d.message,
                        bubbles: d.bubbles || [],
                        ts: Date.now(),
                    },
                ]);
            } catch {
                setMsgs([
                    {
                        role: "assistant",
                        text: "Ahoj! Jsem **Uršula**. Omlouvám se, mám technické potíže. Zkuste to prosím za chvíli.",
                        ts: Date.now(),
                    },
                ]);
            } finally {
                setLoading(false);
            }
        })();
    }, [open, cid, inited]);

    /* ── Send message ── */
    const send = useCallback(
        async (text: string, display?: string) => {
            if (!text.trim() || sending || done) return;

            setMsgs((p) => [
                ...p,
                {
                    role: "user",
                    text: (display || text).trim(),
                    ts: Date.now(),
                },
            ]);
            setInput("");
            setSending(true);

            try {
                const r = await fetch(`${API}/api/mart1n/chat`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        session_id: sid,
                        company_id: cid,
                        message: text.trim(),
                    }),
                });
                if (!r.ok) {
                    const err = await r.json().catch(() => ({}));
                    throw new Error(
                        err.detail || `HTTP ${r.status}`
                    );
                }
                const d = await r.json();

                /* Bubble overrides (NE→ANO joke swap etc.) */
                if (
                    d.bubble_overrides &&
                    Object.keys(d.bubble_overrides).length
                ) {
                    setOverrides(d.bubble_overrides);
                } else {
                    setOverrides({});
                }

                /* Multi-message sequential display */
                if (d.multi_messages?.length) {
                    for (
                        let i = 0;
                        i < d.multi_messages.length;
                        i++
                    ) {
                        const mm = d.multi_messages[
                            i
                        ] as MultiMsg;
                        if (mm.delay_ms > 0) {
                            setSending(true);
                            await new Promise((r) =>
                                setTimeout(r, mm.delay_ms)
                            );
                        }
                        setSending(false);
                        setMsgs((p) => [
                            ...p,
                            {
                                role: "assistant",
                                text: mm.text,
                                bubbles: mm.bubbles || [],
                                ts: Date.now(),
                            },
                        ]);
                        if (i < d.multi_messages.length - 1) {
                            setSending(true);
                            await new Promise((r) =>
                                setTimeout(r, 600)
                            );
                        }
                    }
                } else {
                    /* Single message */
                    setSending(false);
                    setMsgs((p) => [
                        ...p,
                        {
                            role: "assistant",
                            text: d.message,
                            bubbles: d.bubbles || [],
                            ts: Date.now(),
                        },
                    ]);
                }

                setProgress(d.progress || 0);
                if (d.is_complete) setDone(true);
            } catch {
                setSending(false);
                setMsgs((p) => [
                    ...p,
                    {
                        role: "assistant",
                        text: "Omlouvám se, něco se pokazilo. Zkuste to prosím znovu.",
                        bubbles: ["Zkusit znovu"],
                        ts: Date.now(),
                    },
                ]);
            } finally {
                setSending(false);
                inputRef.current?.focus();
            }
        },
        [sending, done, sid, cid]
    );

    const onBubble = useCallback(
        (b: string) => send(b, overrides[b] || b),
        [send, overrides]
    );

    /* ═══════════════════
       RENDER
       ═══════════════════ */

    /* Don't show the bubble on the fallback full-page dotaznik */
    if (onDotaznikPage) return null;

    return (
        <>
            {/* ── Floating bubble trigger ── */}
            {!open && (
                <button
                    onClick={() => setOpen(true)}
                    className="fixed bottom-6 right-6 z-50 flex items-center justify-center
                        w-14 h-14 rounded-full
                        bg-gradient-to-br from-fuchsia-600 to-purple-700
                        shadow-lg shadow-fuchsia-500/25 hover:shadow-fuchsia-500/40
                        hover:scale-105 transition-all duration-200"
                    aria-label="Otevřít chat s Uršulou"
                >
                    <svg
                        className="w-6 h-6 text-white"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        strokeWidth={1.5}
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z"
                        />
                    </svg>
                    {/* Online dot */}
                    <span className="absolute top-0 right-0 w-3.5 h-3.5 rounded-full bg-green-400 border-2 border-dark-900" />
                </button>
            )}

            {/* ── Chat panel ── */}
            {open && (
                <div
                    className="fixed z-50
                        inset-0
                        sm:inset-auto sm:bottom-4 sm:right-4
                        sm:w-[440px] sm:h-[680px] sm:max-h-[calc(100vh-2rem)]
                        sm:rounded-2xl sm:border sm:border-white/[0.08]
                        sm:shadow-2xl sm:shadow-black/60
                        flex flex-col bg-dark-950
                        overflow-hidden
                        animate-in slide-in-from-bottom-4 duration-300"
                >
                    {/* ─── Header ─── */}
                    <div className="flex-shrink-0 flex items-center justify-between gap-2 px-4 py-3 border-b border-white/[0.06] bg-dark-900/80 backdrop-blur-xl">
                        <div className="flex items-center gap-3 min-w-0">
                            <div className="relative">
                                <UAvatar s={32} />
                                <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-green-400 border-2 border-dark-900" />
                            </div>
                            <div className="leading-tight min-w-0">
                                <p className="text-sm font-bold text-white truncate">
                                    Uršula
                                </p>
                                <p className="text-[11px] text-slate-500 truncate">
                                    AI Act compliance analýza
                                </p>
                            </div>
                        </div>

                        {/* Progress bar (visible once >0) */}
                        {progress > 0 && (
                            <div className="flex items-center gap-2 flex-shrink-0">
                                <div className="w-16 h-1.5 bg-dark-800 rounded-full overflow-hidden">
                                    <div
                                        className="h-full rounded-full transition-all duration-700"
                                        style={{
                                            width: `${progress}%`,
                                            background:
                                                "linear-gradient(90deg, #e879f9, #a855f7, #22d3ee)",
                                        }}
                                    />
                                </div>
                                <span className="text-[10px] font-mono text-cyan-400 w-7 text-right">
                                    {progress}%
                                </span>
                            </div>
                        )}

                        <button
                            onClick={() => setOpen(false)}
                            className="flex-shrink-0 p-1.5 rounded-lg hover:bg-white/[0.06] transition"
                            aria-label="Zavřít chat"
                        >
                            <svg
                                className="w-5 h-5 text-slate-400"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                                strokeWidth={2}
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    d="M6 18L18 6M6 6l12 12"
                                />
                            </svg>
                        </button>
                    </div>

                    {/* ─── Messages ─── */}
                    <div
                        ref={scrollRef}
                        className="flex-1 overflow-y-auto px-4 py-4 space-y-3 scroll-smooth"
                    >
                        {/* GDPR micro-badge */}
                        <div className="flex items-center justify-center gap-1.5 text-[10px] text-slate-600 pb-1">
                            <svg
                                className="w-3 h-3 text-emerald-500/60"
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                                strokeWidth={2}
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"
                                />
                            </svg>
                            Data šifrována (AES-256) · Servery EU · GDPR
                        </div>

                        {/* Loading state (first load) */}
                        {loading && <Dots />}

                        {/* Messages */}
                        {!loading &&
                            msgs.map((m, i) => {
                                /* Guard: skip empty assistant bubbles */
                                if (m.role === "assistant" && !m.text?.trim()) return null;

                                const isBot =
                                    m.role === "assistant";
                                const showAvatar =
                                    isBot &&
                                    (i === 0 ||
                                        msgs[i - 1].role !== "assistant");
                                const isLast =
                                    i === msgs.length - 1;

                                return (
                                    <div key={i}>
                                        {isBot ? (
                                            /* ── Assistant bubble ── */
                                            <div className="flex items-end gap-2">
                                                {showAvatar ? (
                                                    <UAvatar s={24} />
                                                ) : (
                                                    <div className="w-6" />
                                                )}
                                                <div className="max-w-[85%] bg-white/[0.05] border border-white/[0.07] rounded-2xl rounded-bl-sm px-3.5 py-2.5 text-slate-300">
                                                    <Md
                                                        text={
                                                            m.text
                                                        }
                                                    />
                                                </div>
                                            </div>
                                        ) : (
                                            /* ── User bubble ── */
                                            <div className="flex justify-end">
                                                <div className="max-w-[80%] bg-fuchsia-600/15 border border-fuchsia-500/20 rounded-2xl rounded-br-sm px-3.5 py-2.5">
                                                    <p className="text-[13px] text-slate-200 leading-relaxed">
                                                        {m.text}
                                                    </p>
                                                </div>
                                            </div>
                                        )}

                                        {/* Quick-reply bubbles (only on last assistant msg) */}
                                        {isBot &&
                                            (m.bubbles?.length ?? 0) > 0 &&
                                            isLast &&
                                            !sending && (
                                                <div className="flex flex-wrap gap-1.5 mt-2 ml-8">
                                                    {m.bubbles!.map(
                                                        (
                                                            b,
                                                            bi
                                                        ) => (
                                                            <button
                                                                key={
                                                                    bi
                                                                }
                                                                onClick={() =>
                                                                    onBubble(
                                                                        b
                                                                    )
                                                                }
                                                                disabled={
                                                                    done
                                                                }
                                                                className="px-3 py-1.5 text-xs rounded-full
                                                                    border border-fuchsia-500/25 bg-fuchsia-500/5
                                                                    text-fuchsia-300 hover:bg-fuchsia-500/15
                                                                    hover:border-fuchsia-500/40 transition
                                                                    disabled:opacity-40 disabled:cursor-not-allowed"
                                                            >
                                                                {b}
                                                            </button>
                                                        )
                                                    )}
                                                </div>
                                            )}
                                    </div>
                                );
                            })}

                        {/* Typing indicator */}
                        {sending && <Dots />}

                        {/* Completion card */}
                        {done && (
                            <div className="rounded-xl bg-emerald-500/10 border border-emerald-500/20 p-4 text-center mt-2">
                                <svg
                                    className="w-8 h-8 text-emerald-400 mx-auto mb-2"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                    strokeWidth={2}
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                                    />
                                </svg>
                                <p className="text-sm font-semibold text-white">
                                    Analýza dokončena!
                                </p>
                                <p className="text-xs text-slate-400 mt-1">
                                    Výsledky najdete v dashboardu.
                                </p>
                                <a
                                    href="/dashboard"
                                    className="inline-block mt-3 px-5 py-2 text-sm rounded-xl
                                        bg-gradient-to-r from-fuchsia-600 to-purple-600
                                        text-white font-medium hover:brightness-110 transition"
                                >
                                    Přejít na dashboard →
                                </a>
                            </div>
                        )}
                    </div>

                    {/* ─── Input bar ─── */}
                    <div className="flex-shrink-0 border-t border-white/[0.06] bg-dark-900/80 backdrop-blur-xl px-3 py-3">
                        <form
                            onSubmit={(e) => {
                                e.preventDefault();
                                send(input);
                            }}
                            className="flex items-center gap-2"
                        >
                            <input
                                ref={inputRef}
                                type="text"
                                value={input}
                                onChange={(e) =>
                                    setInput(e.target.value)
                                }
                                placeholder={
                                    done
                                        ? "Analýza dokončena"
                                        : "Napište odpověď…"
                                }
                                disabled={
                                    sending || done || loading
                                }
                                maxLength={1000}
                                className="flex-1 bg-white/[0.04] border border-white/[0.08]
                                    rounded-full px-4 py-2.5 text-sm text-white
                                    placeholder:text-slate-600
                                    focus:outline-none focus:ring-1 focus:ring-fuchsia-500/40
                                    disabled:opacity-50 transition"
                            />
                            <button
                                type="submit"
                                disabled={
                                    !input.trim() ||
                                    sending ||
                                    done ||
                                    loading
                                }
                                className="flex-shrink-0 w-10 h-10 rounded-full
                                    bg-gradient-to-r from-fuchsia-600 to-purple-600
                                    flex items-center justify-center text-white
                                    hover:brightness-110 disabled:opacity-30
                                    disabled:cursor-not-allowed transition"
                            >
                                <svg
                                    className="w-[18px] h-[18px]"
                                    fill="none"
                                    stroke="currentColor"
                                    viewBox="0 0 24 24"
                                    strokeWidth={2}
                                >
                                    <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5"
                                    />
                                </svg>
                            </button>
                        </form>
                        <p className="text-[9px] text-slate-600 text-center mt-1.5">
                            Uršula je umělá inteligence (čl. 50 AI
                            Act). Data chráněna dle GDPR.
                        </p>
                    </div>
                </div>
            )}
        </>
    );
}
