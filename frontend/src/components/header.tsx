"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useRouter, usePathname } from "next/navigation";

export default function Header() {
    const { user, loading, signOut } = useAuth();
    const router = useRouter();
    const [mobileOpen, setMobileOpen] = useState(false);
    const pathname = usePathname();

    function isActive(href: string) {
        if (href === "/") return pathname === "/";
        return pathname === href || pathname.startsWith(href + "/");
    }

    async function handleSignOut() {
        await signOut();
        router.push("/");
    }

    return (
        <header className="sticky top-0 z-50 border-b border-white/[0.06] bg-dark-900/80 backdrop-blur-xl">
            <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
                <a href="/" className="flex items-center gap-2 group">
                    <svg className="w-8 h-8" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M16 2L4 7v9c0 7.73 5.12 14.95 12 17 6.88-2.05 12-9.27 12-17V7L16 2z" fill="url(#shield-grad)" fillOpacity="0.15" stroke="url(#shield-grad)" strokeWidth="1.5" />
                        <path d="M12 16l3 3 5-6" stroke="url(#shield-grad)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        <defs>
                            <linearGradient id="shield-grad" x1="4" y1="2" x2="28" y2="28" gradientUnits="userSpaceOnUse">
                                <stop stopColor="#d946ef" />
                                <stop offset="1" stopColor="#06b6d4" />
                            </linearGradient>
                        </defs>
                    </svg>
                    <span className="text-2xl font-extrabold tracking-tighter">
                        <span className="text-white">AI</span>
                        <span className="neon-text">shield</span>
                        <span className="text-slate-500 text-sm font-normal ml-0.5">.cz</span>
                    </span>
                </a>

                {/* Desktop nav */}
                <div className="hidden md:flex items-center gap-8">
                    <a href="/scan" className={`text-sm transition-colors ${isActive("/scan") ? "text-neon-fuchsia font-semibold" : "text-slate-400 hover:text-neon-fuchsia"}`}>
                        Skenovat web
                    </a>
                    <a href="/pricing" className={`text-sm transition-colors ${isActive("/pricing") ? "text-neon-fuchsia font-semibold" : "text-slate-400 hover:text-neon-fuchsia"}`}>
                        Ceník
                    </a>
                    <a href="/about" className={`text-sm transition-colors ${isActive("/about") ? "text-neon-fuchsia font-semibold" : "text-slate-400 hover:text-neon-fuchsia"}`}>
                        Jak to funguje
                    </a>

                    {loading ? (
                        <div className="h-9 w-24 rounded-xl bg-white/5 animate-pulse" />
                    ) : user ? (
                        /* ── Přihlášený uživatel ── */
                        <div className="flex items-center gap-4">
                            <a
                                href="/dashboard"
                                className="text-sm text-slate-400 hover:text-neon-cyan transition-colors font-medium"
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
                        /* ── Nepřihlášený ── */
                        <>
                            <a href="/login" className="btn-secondary text-sm px-4 py-2">
                                Přihlásit se
                            </a>
                            <a href="/scan" className="btn-primary text-sm px-4 py-2">
                                Skenovat ZDARMA
                            </a>
                        </>
                    )}
                </div>

                {/* Mobile menu button */}
                <button
                    className="md:hidden text-slate-400 hover:text-white"
                    aria-label="Menu"
                    onClick={() => setMobileOpen(!mobileOpen)}
                >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        {mobileOpen ? (
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        ) : (
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                        )}
                    </svg>
                </button>
            </nav>

            {/* Mobile menu */}
            {mobileOpen && (
                <div className="md:hidden border-t border-white/[0.06] bg-dark-900/95 backdrop-blur-xl px-6 py-4 space-y-3">
                    <a href="/scan" className={`block text-sm transition-colors py-2 ${isActive("/scan") ? "text-neon-fuchsia font-semibold" : "text-slate-400 hover:text-neon-fuchsia"}`}>
                        Skenovat web
                    </a>
                    <a href="/pricing" className={`block text-sm transition-colors py-2 ${isActive("/pricing") ? "text-neon-fuchsia font-semibold" : "text-slate-400 hover:text-neon-fuchsia"}`}>
                        Ceník
                    </a>
                    <a href="/about" className={`block text-sm transition-colors py-2 ${isActive("/about") ? "text-neon-fuchsia font-semibold" : "text-slate-400 hover:text-neon-fuchsia"}`}>
                        Jak to funguje
                    </a>

                    {user ? (
                        <>
                            <a href="/dashboard" className="block text-sm text-neon-cyan font-medium py-2">
                                Dashboard
                            </a>
                            <button onClick={handleSignOut} className="block text-sm text-red-400 py-2">
                                Odhlásit se
                            </button>
                        </>
                    ) : (
                        <>
                            <a href="/login" className="block text-sm text-slate-300 font-medium py-2">
                                Přihlásit se
                            </a>
                            <a href="/scan" className="btn-primary text-sm px-4 py-2 text-center block mt-2">
                                Skenovat ZDARMA
                            </a>
                        </>
                    )}
                </div>
            )}
        </header>
    );
}
