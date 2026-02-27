"use client";

import { useState, useEffect, useRef } from "react";
import { useAuth } from "@/lib/auth-context";
import { useRouter, usePathname } from "next/navigation";

export default function Header() {
    const { user, loading, signOut } = useAuth();
    const router = useRouter();
    const [mobileOpen, setMobileOpen] = useState(false);
    const pathname = usePathname();
    const menuRef = useRef<HTMLDivElement>(null);

    function isActive(href: string) {
        if (href === "/") return pathname === "/";
        return pathname === href || pathname.startsWith(href + "/");
    }

    async function handleSignOut() {
        setMobileOpen(false);
        await signOut();
        router.push("/");
    }

    // Close menu on route change
    useEffect(() => { setMobileOpen(false); }, [pathname]);

    // Close menu on outside click
    useEffect(() => {
        if (!mobileOpen) return;
        function handleClick(e: MouseEvent) {
            if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMobileOpen(false);
        }
        document.addEventListener("mousedown", handleClick);
        return () => document.removeEventListener("mousedown", handleClick);
    }, [mobileOpen]);

    // Lock body scroll when menu open
    useEffect(() => {
        document.body.style.overflow = mobileOpen ? "hidden" : "";
        return () => { document.body.style.overflow = ""; };
    }, [mobileOpen]);

    // Admin má vlastní UI — hlavní Header tam nepatří
    if (pathname?.startsWith("/admin")) return null;

    const NAV_LINKS = [
        { href: "/pricing", icon: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9.568 3H5.25A2.25 2.25 0 0 0 3 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 0 0 5.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 0 0 9.568 3Z" /><path strokeLinecap="round" strokeLinejoin="round" d="M6 6h.008v.008H6V6Z" /></svg>), label: "Ceník", desc: "Balíčky a ceny služeb" },
        { href: "/about", icon: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 0 0 1.5-.189m-1.5.189a6.01 6.01 0 0 1-1.5-.189m3.75 7.478a12.06 12.06 0 0 1-4.5 0m3.75 2.383a14.406 14.406 0 0 1-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 1 0-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" /></svg>), label: "Jak to funguje", desc: "Postup naší práce" },
    ];

    return (
        <header className="sticky top-0 z-50 border-b border-white/[0.06] bg-dark-900/80 backdrop-blur-xl">
            <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
                <a href="/" className="flex items-center gap-2 group min-h-[44px]">
                    <svg className="w-8 h-8" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M16 1.5C16 1.5 4 6 4 6v10.5c0 4.2 1.8 8.2 4.8 11.1C11.5 30.2 13.9 31.5 16 32c2.1-.5 4.5-1.8 7.2-4.4C26.2 24.7 28 20.7 28 16.5V6L16 1.5z" fill="url(#shield-grad-h)" fillOpacity="0.25" stroke="url(#shield-grad-h)" strokeWidth="2" strokeLinejoin="round" />
                        <path d="M16 5C16 5 7 9 7 9v7.5c0 3.3 1.4 6.5 3.8 8.8C12.9 27.3 14.7 28.3 16 28.7c1.3-.4 3.1-1.4 5.2-3.4C23.6 22.9 25 19.8 25 16.5V9L16 5z" fill="none" stroke="url(#shield-grad-h)" strokeWidth="0.8" opacity="0.4" strokeLinejoin="round" />
                        <path d="M12 16.5l3 3 5.5-6.5" stroke="url(#shield-grad-h)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                        <defs>
                            <linearGradient id="shield-grad-h" x1="4" y1="2" x2="28" y2="30" gradientUnits="userSpaceOnUse">
                                <stop stopColor="#d946ef" />
                                <stop offset="0.5" stopColor="#a855f7" />
                                <stop offset="1" stopColor="#06b6d4" />
                            </linearGradient>
                        </defs>
                    </svg>
                    <span className="text-2xl font-extrabold tracking-tighter" translate="no">
                        <span className="text-white">AI</span>
                        <span className="neon-text">shield</span>
                        <span className="text-slate-500 text-sm font-normal ml-0.5">.cz</span>
                    </span>
                </a>

                {/* Desktop nav */}
                <div className="hidden lg:flex items-center gap-6">
                    <a href="/pricing" className={`text-base transition-colors ${isActive("/pricing") ? "text-neon-fuchsia font-semibold" : "text-slate-300 hover:text-neon-fuchsia"}`}>
                        Ceník
                    </a>
                    <a href="/about" className={`text-base transition-colors ${isActive("/about") ? "text-neon-fuchsia font-semibold" : "text-slate-300 hover:text-neon-fuchsia"}`}>
                        Jak to funguje
                    </a>

                    {loading ? (
                        <div className="h-9 w-24 rounded-xl bg-white/5 animate-pulse" />
                    ) : user ? (
                        <div className="flex items-center gap-4">
                            <a
                                href="/dashboard"
                                className="text-base text-slate-300 hover:text-neon-cyan transition-colors font-medium"
                            >
                                Dashboard
                            </a>
                            <div className="flex items-center gap-3 rounded-xl border border-white/[0.06] bg-white/[0.03] px-3 py-1.5">
                                <div className="h-7 w-7 rounded-full bg-gradient-to-br from-fuchsia-500 to-cyan-500 flex items-center justify-center text-[11px] font-bold text-white">
                                    {(user.user_metadata?.company_name || user.email || "?")
                                        .charAt(0)
                                        .toUpperCase()}
                                </div>
                                <span className="text-sm text-slate-300 max-w-[140px] truncate">
                                    {user.user_metadata?.company_name || user.email}
                                </span>
                                <button
                                    onClick={handleSignOut}
                                    className="text-xs text-slate-500 hover:text-red-400 transition-colors ml-1"
                                    title="Odhlásit se"
                                >
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                            d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                                    </svg>
                                </button>
                            </div>
                        </div>
                    ) : (
                        <>
                            <a href="/login" className="text-sm text-slate-300 hover:text-white transition-colors font-medium">
                                Přihlásit se
                            </a>
                            <a href="/registrace" className="text-sm text-slate-300 hover:text-white transition-colors font-medium">
                                Registrovat se
                            </a>
                        </>
                    )}

                    {/* CTA duo — Helplinka + Scan vedle sebe */}
                    <div className="flex items-center gap-2">
                        <a
                            href="tel:+420732716141"
                            className="inline-flex items-center gap-1.5 rounded-xl border border-fuchsia-500/30 bg-fuchsia-600/15 px-3 py-2.5 text-sm font-semibold text-fuchsia-400 hover:bg-fuchsia-600/25 transition shadow-sm shadow-fuchsia-500/10"
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 0 0 2.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 0 1-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 0 0-1.091-.852H4.5A2.25 2.25 0 0 0 2.25 4.5v2.25Z" />
                            </svg>
                            HELPLINKA
                        </a>
                        <a href="/scan" className="btn-primary cta-pulse text-sm px-5 py-2.5 min-h-[44px] flex items-center whitespace-nowrap">
                            Skenovat ZDARMA
                        </a>
                    </div>
                </div>

                {/* ── Mobile hamburger ── */}
                <button
                    className="lg:hidden relative w-11 h-11 flex items-center justify-center rounded-xl bg-white/5 border border-white/10 text-white hover:bg-white/10 active:scale-95 transition-all"
                    aria-label={mobileOpen ? "Zavřít menu" : "Otevřít menu"}
                    onClick={() => setMobileOpen(!mobileOpen)}
                >
                    <svg className="w-5 h-5 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                        {mobileOpen ? (
                            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                        ) : (
                            <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                        )}
                    </svg>
                </button>
            </nav>

            {/* ── Mobile overlay + slide-down menu ── */}
            <div
                className={`lg:hidden fixed inset-0 top-[73px] z-40 transition-opacity duration-300 ${mobileOpen ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"}`}
            >
                {/* Backdrop */}
                <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />

                {/* Menu panel */}
                <div
                    ref={menuRef}
                    className={`relative bg-[#0d1117] border-b border-white/10 shadow-2xl shadow-black/50 transition-all duration-300 ease-out ${mobileOpen ? "translate-y-0 opacity-100" : "-translate-y-4 opacity-0"}`}
                >
                    {/* Nav links with icons */}
                    <div className="px-4 py-3 space-y-1">
                        {NAV_LINKS.map(link => (
                            <a
                                key={link.href}
                                href={link.href}
                                onClick={() => setMobileOpen(false)}
                                className={`flex items-center gap-4 px-4 py-3.5 rounded-2xl transition-all active:scale-[0.98] ${isActive(link.href)
                                    ? "bg-gradient-to-r from-fuchsia-500/15 to-cyan-500/10 border border-fuchsia-500/20"
                                    : "hover:bg-white/5 border border-transparent"
                                    }`}
                            >
                                <span className={`w-8 h-8 flex items-center justify-center flex-shrink-0 rounded-lg ${isActive(link.href) ? "bg-fuchsia-500/15 text-fuchsia-400" : "bg-white/[0.06] text-slate-400"}`}>{link.icon}</span>
                                <div className="min-w-0">
                                    <div className={`text-[15px] font-semibold ${isActive(link.href) ? "text-fuchsia-400" : "text-white"}`}>{link.label}</div>
                                    <div className="text-xs text-slate-500 mt-0.5">{link.desc}</div>
                                </div>
                                <svg className="w-4 h-4 text-slate-600 ml-auto flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                                </svg>
                            </a>
                        ))}
                    </div>

                    {/* Divider */}
                    <div className="mx-6 border-t border-white/[0.06]" />

                    {/* Helplinka */}
                    <div className="px-4 py-3">
                        <a
                            href="tel:+420732716141"
                            onClick={() => setMobileOpen(false)}
                            className="flex items-center gap-4 px-4 py-3.5 rounded-2xl bg-fuchsia-600/15 border border-fuchsia-500/20 hover:bg-fuchsia-600/25 transition-all active:scale-[0.98]"
                        >
                            <span className="w-8 h-8 flex items-center justify-center flex-shrink-0 rounded-lg bg-fuchsia-500/15 text-fuchsia-400"><svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 0 0 2.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 0 1-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 0 0-1.091-.852H4.5A2.25 2.25 0 0 0 2.25 4.5v2.25Z" /></svg></span>
                            <div className="min-w-0">
                                <div className="text-[15px] font-semibold text-fuchsia-400">HELPLINKA</div>
                                <div className="text-xs text-slate-400 mt-0.5">732 716 141 — volejte kdykoliv</div>
                            </div>
                        </a>
                    </div>

                    {/* Divider */}
                    <div className="mx-6 border-t border-white/[0.06]" />

                    {/* Scan CTA */}
                    <div className="px-4 py-3">
                        <a
                            href="/scan"
                            onClick={() => setMobileOpen(false)}
                            className="flex items-center justify-center gap-2 w-full px-4 py-3.5 rounded-2xl btn-primary cta-pulse text-base font-semibold active:scale-[0.98] transition-all"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
                            </svg>
                            Skenovat ZDARMA
                        </a>
                    </div>

                    {/* Divider */}
                    <div className="mx-6 border-t border-white/[0.06]" />

                    {/* Auth section */}
                    <div className="px-4 py-3 pb-6">
                        {loading ? (
                            <div className="h-12 rounded-2xl bg-white/5 animate-pulse" />
                        ) : user ? (
                            <div className="space-y-2">
                                {/* User card */}
                                <div className="flex items-center gap-3 px-4 py-3 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
                                    <div className="h-9 w-9 rounded-full bg-gradient-to-br from-fuchsia-500 to-cyan-500 flex items-center justify-center text-sm font-bold text-white flex-shrink-0">
                                        {(user.user_metadata?.company_name || user.email || "?").charAt(0).toUpperCase()}
                                    </div>
                                    <div className="min-w-0 flex-1">
                                        <div className="text-sm text-white font-medium truncate">{user.user_metadata?.company_name || user.email}</div>
                                        <div className="text-xs text-slate-500 truncate">{user.email}</div>
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-2">
                                    <a
                                        href="/dashboard"
                                        onClick={() => setMobileOpen(false)}
                                        className="flex items-center justify-center gap-2 px-4 py-3 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 font-semibold text-sm hover:bg-cyan-500/20 transition-all active:scale-[0.98]"
                                    >
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25A2.25 2.25 0 0 1 13.5 18v-2.25Z" /></svg> Dashboard
                                    </a>
                                    <button
                                        onClick={handleSignOut}
                                        className="flex items-center justify-center gap-2 px-4 py-3 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-400 font-semibold text-sm hover:bg-red-500/20 transition-all active:scale-[0.98]"
                                    >
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15m3 0 3-3m0 0-3-3m3 3H9" /></svg> Odhlásit
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <div className="space-y-2">
                                <div className="grid grid-cols-2 gap-3">
                                    <a
                                        href="/login"
                                        onClick={() => setMobileOpen(false)}
                                        className="flex items-center justify-center gap-2 px-4 py-3.5 rounded-2xl bg-white/5 border border-white/10 text-white font-semibold text-sm hover:bg-white/10 transition-all active:scale-[0.98]"
                                    >
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M8.25 9V5.25A2.25 2.25 0 0 1 10.5 3h6a2.25 2.25 0 0 1 2.25 2.25v13.5A2.25 2.25 0 0 1 16.5 21h-6a2.25 2.25 0 0 1-2.25-2.25V15M12 9l3 3m0 0-3 3m3-3H2.25" /></svg> Přihlásit se
                                    </a>
                                    <a
                                        href="/registrace"
                                        onClick={() => setMobileOpen(false)}
                                        className="flex items-center justify-center gap-2 px-4 py-3.5 rounded-2xl bg-white/5 border border-white/10 text-white font-semibold text-sm hover:bg-white/10 transition-all active:scale-[0.98]"
                                    >
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M18 7.5v3m0 0v3m0-3h3m-3 0h-3m-2.25-4.125a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0ZM3 19.235v-.11a6.375 6.375 0 0 1 12.75 0v.109A12.318 12.318 0 0 1 9.374 21c-2.331 0-4.512-.645-6.374-1.766Z" /></svg> Registrovat se
                                    </a>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </header>
    );
}
