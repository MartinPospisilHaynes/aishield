"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type PaymentStatus = {
    payment_id: number;
    state: string;
    is_paid: boolean;
    order_number: string;
};

function PaymentStatusContent() {
    const searchParams = useSearchParams();
    const paymentId = searchParams.get("id");
    const [status, setStatus] = useState<PaymentStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        if (!paymentId) {
            setError("Chybí ID platby");
            setLoading(false);
            return;
        }

        async function checkStatus() {
            try {
                const res = await fetch(`${API_URL}/api/payments/status/${paymentId}`);
                if (!res.ok) throw new Error("Nelze ověřit platbu");
                const data = await res.json();
                setStatus(data);
            } catch {
                setError("Nepodařilo se ověřit stav platby. Zkuste to znovu za chvíli.");
            } finally {
                setLoading(false);
            }
        }

        checkStatus();
    }, [paymentId]);

    if (loading) {
        return (
            <section className="py-20 relative">
                <div className="absolute inset-0 -z-10">
                    <div className="absolute top-[30%] left-[40%] h-[400px] w-[400px] rounded-full bg-cyan-500/8 blur-[120px]" />
                </div>
                <div className="mx-auto max-w-md px-6 text-center">
                    <div className="glass py-16">
                        <div className="mx-auto mb-6 w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center animate-pulse">
                            <svg className="w-8 h-8 text-slate-400 animate-spin" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                            </svg>
                        </div>
                        <h2 className="text-xl font-bold mb-2">Ověřuji platbu...</h2>
                        <p className="text-sm text-slate-400">
                            Komunikuji s platební bránou GoPay.
                        </p>
                    </div>
                </div>
            </section>
        );
    }

    if (error) {
        return (
            <section className="py-20 relative">
                <div className="absolute inset-0 -z-10">
                    <div className="absolute top-[30%] left-[40%] h-[400px] w-[400px] rounded-full bg-red-500/5 blur-[120px]" />
                </div>
                <div className="mx-auto max-w-md px-6 text-center">
                    <div className="glass py-12">
                        <div className="mx-auto mb-4 w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center">
                            <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                            </svg>
                        </div>
                        <h2 className="text-xl font-bold mb-2">Chyba ověření</h2>
                        <p className="text-sm text-slate-400 mb-6">{error}</p>
                        <a href="/pricing" className="btn-primary inline-flex px-6 py-2.5">
                            Zkusit znovu
                        </a>
                    </div>
                </div>
            </section>
        );
    }

    // ── Platba úspěšná ──
    if (status?.is_paid) {
        return (
            <section className="py-20 relative">
                <div className="absolute inset-0 -z-10">
                    <div className="absolute top-[20%] left-[30%] h-[500px] w-[500px] rounded-full bg-green-500/5 blur-[130px]" />
                    <div className="absolute bottom-[20%] right-[30%] h-[300px] w-[300px] rounded-full bg-fuchsia-500/5 blur-[100px]" />
                </div>
                <div className="mx-auto max-w-lg px-6 text-center">
                    <div className="glass py-12">
                        {/* Success icon */}
                        <div className="mx-auto mb-6 w-20 h-20 rounded-2xl bg-green-500/10 border border-green-500/20 flex items-center justify-center">
                            <svg className="w-10 h-10 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                        </div>

                        <h1 className="text-2xl font-extrabold mb-2">
                            Platba <span className="text-green-400">úspěšná</span>!
                        </h1>
                        <p className="text-slate-400 text-sm mb-2">
                            Objednávka: <span className="text-slate-300 font-mono">{status.order_number}</span>
                        </p>
                        <p className="text-slate-400 text-sm mb-8">
                            Faktura vám přijde na email. Nyní vyplňte dotazník,
                            abychom vám připravili dokumenty na míru.
                        </p>

                        <div className="h-px bg-gradient-to-r from-transparent via-white/10 to-transparent mb-8" />

                        <div className="space-y-3">
                            <a href="/dotaznik" className="btn-primary w-full py-3.5 block text-center">
                                Vyplnit dotazník
                            </a>
                            <a href="/dashboard" className="btn-secondary w-full py-3 block text-center">
                                Přejít na Dashboard
                            </a>
                        </div>
                    </div>
                </div>
            </section>
        );
    }

    // ── Platba neúspěšná / zrušená / čekající ──
    const stateLabels: Record<string, { title: string; desc: string; color: string }> = {
        CANCELED: {
            title: "Platba zrušena",
            desc: "Platbu jste zrušili. Můžete to zkusit znovu.",
            color: "red",
        },
        TIMEOUTED: {
            title: "Platba vypršela",
            desc: "Čas na dokončení platby vypršel. Zkuste to znovu.",
            color: "yellow",
        },
        CREATED: {
            title: "Čeká na zaplacení",
            desc: "Platba byla vytvořena, ale ještě nebyla dokončena.",
            color: "yellow",
        },
        PAYMENT_METHOD_CHOSEN: {
            title: "Zpracovává se",
            desc: "Platba se zpracovává. Vyčkejte prosím.",
            color: "cyan",
        },
    };

    const stateInfo = stateLabels[status?.state || ""] || {
        title: "Neznámý stav",
        desc: "Zkuste stránku obnovit nebo nás kontaktujte.",
        color: "yellow",
    };

    return (
        <section className="py-20 relative">
            <div className="absolute inset-0 -z-10">
                <div className={`absolute top-[30%] left-[40%] h-[400px] w-[400px] rounded-full bg-${stateInfo.color}-500/5 blur-[120px]`} />
            </div>
            <div className="mx-auto max-w-md px-6 text-center">
                <div className="glass py-12">
                    <div className={`mx-auto mb-4 w-16 h-16 rounded-2xl bg-${stateInfo.color}-500/10 border border-${stateInfo.color}-500/20 flex items-center justify-center`}>
                        <svg className={`w-8 h-8 text-${stateInfo.color}-400`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <h2 className="text-xl font-bold mb-2">{stateInfo.title}</h2>
                    <p className="text-sm text-slate-400 mb-6">{stateInfo.desc}</p>
                    <div className="space-y-3">
                        <a href="/pricing" className="btn-primary inline-flex px-6 py-2.5">
                            Zkusit znovu
                        </a>
                        <p className="text-xs text-slate-500 mt-4">
                            Problém přetrvává?{" "}
                            <a href="mailto:info@aishield.cz" className="text-neon-fuchsia hover:text-fuchsia-300 transition-colors">
                                Kontaktujte nás
                            </a>
                        </p>
                    </div>
                </div>
            </div>
        </section>
    );
}

export default function PlatbaStavPage() {
    return (
        <Suspense fallback={
            <section className="py-20">
                <div className="mx-auto max-w-md px-6 text-center">
                    <div className="glass py-16 animate-pulse">
                        <p className="text-slate-400">Načítám...</p>
                    </div>
                </div>
            </section>
        }>
            <PaymentStatusContent />
        </Suspense>
    );
}
