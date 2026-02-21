"use client";

import { useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";

/**
 * /dotaznik/mart1n → redirect to /dotaznik (panel questionnaire)
 *
 * The old chatbot (Uršula) has been replaced by a clickable panel-based
 * questionnaire. This page now redirects to preserve any bookmarks or
 * cached links, forwarding all query parameters (company_id, etc.).
 */

function Mart1nRedirect() {
    const searchParams = useSearchParams();
    const router = useRouter();

    useEffect(() => {
        const params = searchParams.toString();
        const target = params ? `/dotaznik?${params}` : "/dotaznik";
        router.replace(target);
    }, [searchParams, router]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-dark-950">
            <div className="text-center">
                <div className="flex justify-center mb-4">
                    <div className="flex gap-1.5">
                        <span className="w-2 h-2 bg-neon-fuchsia/60 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                        <span className="w-2 h-2 bg-neon-purple/60 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                        <span className="w-2 h-2 bg-neon-cyan/60 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                    </div>
                </div>
                <p className="text-slate-400 text-sm">Přesměrování na dotazník…</p>
            </div>
        </div>
    );
}

export default function Mart1nPage() {
    return (
        <Suspense fallback={
            <div className="min-h-screen flex items-center justify-center bg-dark-950">
                <p className="text-slate-400 text-sm">Načítání…</p>
            </div>
        }>
            <Mart1nRedirect />
        </Suspense>
    );
}
