"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { createClient } from "@/lib/supabase-browser";
import ContactForm from "@/components/contact-form";
import { useAnalytics } from "@/lib/analytics";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type PaymentGateway = "gopay" | "stripe" | "comgate" | "bank_transfer";

type PaymentStatus = {
    payment_id: string;
    state: string;
    is_paid: boolean;
    order_number: string;
    gateway?: PaymentGateway;
};

const GATEWAY_NAMES: Record<PaymentGateway, string> = {
    gopay: "GoPay",
    stripe: "Stripe",
    comgate: "Comgate",
    bank_transfer: "Bankovní převod",
};

function PaymentStatusContent() {
    const searchParams = useSearchParams();
    const { track } = useAnalytics();
    const gateway = (searchParams.get("gateway") || "gopay") as PaymentGateway;
    const paymentId = searchParams.get("id") || searchParams.get("session_id");
    const isSubscription = searchParams.get("type") === "subscription";
    const [status, setStatus] = useState<PaymentStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [questionnaireComplete, setQuestionnaireComplete] = useState<boolean | null>(null);

    const gatewayName = GATEWAY_NAMES[gateway] || gateway;
    const isBankTransfer = gateway === "bank_transfer";

    // Check questionnaire completeness
    useEffect(() => {
        async function checkQuestionnaire() {
            try {
                const supabase = createClient();
                const { data: { session } } = await supabase.auth.getSession();
                const token = session?.access_token;
                if (!token) {
                    // No auth — can't check, leave null (don't show button)
                    return;
                }
                const res = await fetch(`${API_URL}/api/questionnaire/my-status`, {
                    headers: { "Authorization": `Bearer ${token}` },
                });
                if (res.ok) {
                    const data = await res.json();
                    setQuestionnaireComplete(data.is_complete === true);
                }
                // On error, leave null — don't show the button
            } catch {
                // On error, leave null — don't show the button
            }
        }
        checkQuestionnaire();
    }, []);

    useEffect(() => {
        // Bank transfer — no online gateway to check
        if (isBankTransfer) {
            setLoading(false);
            return;
        }

        if (!paymentId) {
            setError("Chybí ID platby");
            setLoading(false);
            return;
        }

        async function checkStatus() {
            try {
                const res = await fetch(
                    `${API_URL}/api/payments/status/${paymentId}?gateway=${gateway}`
                );
                if (!res.ok) throw new Error("Nelze ověřit platbu");
                const data = await res.json();
                setStatus(data);
                track(data.is_paid ? "payment_completed" : "payment_pending", {
                    gateway, state: data.state, order: data.order_number,
                    is_subscription: isSubscription,
                });
            } catch {
                setError("Nepodařilo se ověřit stav platby. Zkuste to znovu za chvíli.");
            } finally {
                setLoading(false);
            }
        }

        checkStatus();
    }, [paymentId, gateway, isBankTransfer]);

    // Bank transfer — show confirmation immediately
    if (isBankTransfer) {
        return (
            <section className="py-20 relative">
                <div className="absolute inset-0 -z-10">
                    <div className="absolute top-[20%] left-[30%] h-[500px] w-[500px] rounded-full bg-cyan-500/5 blur-[130px]" />
                    <div className="absolute bottom-[20%] right-[30%] h-[300px] w-[300px] rounded-full bg-fuchsia-500/5 blur-[100px]" />
                </div>
                <div className="mx-auto max-w-lg px-6 text-center">
                    <div className="glass py-12">
                        <div className="mx-auto mb-6 w-20 h-20 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
                            <svg className="w-10 h-10 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 9v.906a2.25 2.25 0 01-1.183 1.981l-6.478 3.488M2.25 9v.906a2.25 2.25 0 001.183 1.981l6.478 3.488m8.839 2.51l-4.66-2.51m0 0l-1.023-.55a2.25 2.25 0 00-2.134 0l-1.022.55m0 0l-4.661 2.51m16.5 1.265a2.25 2.25 0 01-2.25 2.25H3.75a2.25 2.25 0 01-2.25-2.25V6.75a2.25 2.25 0 012.25-2.25h16.5a2.25 2.25 0 012.25 2.25v11.5z" />
                            </svg>
                        </div>

                        <h1 className="text-2xl font-extrabold mb-2">
                            Objednávka <span className="text-cyan-400">přijata</span> ✓
                        </h1>

                        {paymentId && (
                            <p className="text-slate-400 text-sm mb-2">
                                Variabilní symbol: <span className="text-white font-mono font-bold">{paymentId.replace("BT-", "")}</span>
                            </p>
                        )}

                        <p className="text-slate-400 text-sm mb-4 leading-relaxed max-w-md mx-auto">
                            Na váš email jsme odeslali fakturu s platebními údaji pro bankovní převod.
                        </p>

                        {/* Steps */}
                        <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 p-4 mb-4 text-left max-w-md mx-auto">
                            <h4 className="text-xs font-semibold text-cyan-300 uppercase tracking-wider mb-3">Co bude následovat</h4>
                            <ul className="space-y-2 text-sm text-slate-300">
                                <li className="flex items-start gap-2">
                                    <span className="text-cyan-400 font-bold mt-0.5">1.</span>
                                    Proveďte převod dle údajů v emailu
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-cyan-400 font-bold mt-0.5">2.</span>
                                    Po přijetí platby vás budeme kontaktovat
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-cyan-400 font-bold mt-0.5">3.</span>
                                    Vyplňte dotazník pro přípravu dokumentů (pokud jste tak již neučinili)
                                </li>
                                <li className="flex items-start gap-2">
                                    <span className="text-cyan-400 font-bold mt-0.5">4.</span>
                                    Veškeré potřebné materiály dodáme <strong className="text-white">do 7 pracovních dní</strong>
                                </li>
                            </ul>
                        </div>

                        {/* Email delay notice */}
                        <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4 mb-6 text-left max-w-md mx-auto">
                            <p className="text-xs text-amber-300/80 leading-relaxed">
                                <strong>Poznámka:</strong> V případě velkého vytížení může e-mail s fakturou dorazit až do 15 minut.
                                Zkontrolujte prosím i složku <strong>spam</strong> nebo <strong>hromadné</strong>.
                                Pokud email ani tak nedorazí, kontaktujte nás prosím přes formulář níže.
                            </p>
                        </div>

                        {/* Contact info */}
                        <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4 mb-6 max-w-md mx-auto">
                            <p className="text-xs font-semibold text-slate-300 mb-2">V případě jakýchkoliv otázek nás neváhejte kontaktovat:</p>
                            <div className="space-y-1.5">
                                <a href="tel:+420732716141" className="flex items-center gap-2 text-sm text-cyan-400 hover:text-cyan-300 transition-colors">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72c.127.96.361 1.903.7 2.81a2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0122 16.92z" /></svg>
                                    +420 732 716 141
                                </a>
                                <a href="mailto:info@aishield.cz" className="flex items-center gap-2 text-sm text-cyan-400 hover:text-cyan-300 transition-colors">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                                    info@aishield.cz
                                </a>
                            </div>
                        </div>

                        <div className="h-px bg-gradient-to-r from-transparent via-white/10 to-transparent mb-6" />

                        <div className="space-y-3">
                            {/* Conditional questionnaire button — only show when explicitly incomplete */}
                            {questionnaireComplete === false && (
                                <a href="/dotaznik" className="btn-primary w-full py-3.5 block text-center">
                                    Vyplnit dotazník
                                </a>
                            )}
                            <a href="/dashboard" className="btn-secondary w-full py-3 block text-center">
                                Přejít na Dashboard
                            </a>
                        </div>
                    </div>

                    {/* Contact form — fallback if email didn't arrive */}
                    <div className="mt-10 max-w-lg mx-auto">
                        <ContactForm />
                    </div>
                </div>
            </section>
        );
    }

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
                            Komunikuji s platební bránou {gatewayName}.
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
        const isCoffee = status.order_number?.startsWith("AS-COFFEE");

        return (
            <section className="py-20 relative">
                <div className="absolute inset-0 -z-10">
                    <div className="absolute top-[20%] left-[30%] h-[500px] w-[500px] rounded-full bg-green-500/5 blur-[130px]" />
                    <div className="absolute bottom-[20%] right-[30%] h-[300px] w-[300px] rounded-full bg-fuchsia-500/5 blur-[100px]" />
                </div>
                <div className="mx-auto max-w-xl px-6 text-center">
                    <div className="glass py-12">
                        {/* Success icon */}
                        <div className={`mx-auto mb-6 w-20 h-20 rounded-2xl flex items-center justify-center ${isCoffee ? "bg-amber-500/10 border border-amber-500/20" : "bg-green-500/10 border border-green-500/20"}`}>
                            {isCoffee ? (
                                <svg className="w-10 h-10 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 8h12v5a4 4 0 0 1-4 4H9a4 4 0 0 1-4-4V8Z" />
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M17 10h1.5a2.5 2.5 0 0 1 0 5H17" />
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M8 4v2m3-2v2m3-2v2" />
                                </svg>
                            ) : (
                                <svg className="w-10 h-10 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                            )}
                        </div>

                        {isCoffee ? (
                            <>
                                <h1 className="text-2xl font-extrabold mb-4">
                                    Hmm.. <span className="text-amber-400">lahodné</span> ☕
                                </h1>
                                <p className="text-slate-300 text-sm mb-2 leading-relaxed">
                                    Moc děkuji za pozvání na kafé!
                                </p>
                                <p className="text-slate-400 text-sm mb-8 leading-relaxed">
                                    Hned se mi bude pracovat lépe. Díky za podporu!
                                </p>
                            </>
                        ) : (
                            <>
                                <h1 className="text-2xl font-extrabold mb-2">
                                    Platba <span className="text-green-400">úspěšná</span>!
                                </h1>
                                <p className="text-slate-400 text-sm mb-2">
                                    Objednávka: <span className="text-slate-300 font-mono">{status.order_number}</span>
                                </p>
                                {isSubscription ? (
                                    <p className="text-slate-400 text-sm mb-8">
                                        Monitoring byl úspěšně aktivován. Platba bude strhávána automaticky každý měsíc.
                                        Stav monitoringu najdete v dashboardu.
                                    </p>
                                ) : (
                                    <p className="text-slate-400 text-sm mb-8">
                                        Faktura vám přijde na email. Nyní vyplňte dotazník,
                                        abychom vám připravili dokumenty na míru.
                                    </p>
                                )}
                            </>
                        )}

                        <div className="h-px bg-gradient-to-r from-transparent via-white/10 to-transparent mb-8" />

                        <div className="space-y-3">
                            {isCoffee ? (
                                <a href="/dashboard" className="btn-primary w-full py-3.5 block text-center">
                                    Přejít na Dashboard
                                </a>
                            ) : isSubscription ? (
                                <a href="/dashboard#monitoring" className="btn-primary w-full py-3.5 block text-center">
                                    Přejít na Dashboard
                                </a>
                            ) : (
                                <>
                                    {questionnaireComplete === false && (
                                        <a href="/dotaznik" className="btn-primary w-full py-3.5 block text-center">
                                            Vyplnit dotazník
                                        </a>
                                    )}
                                    <a href="/dashboard" className={`${questionnaireComplete === false ? "btn-secondary" : "btn-primary"} w-full py-3 block text-center`}>
                                        Přejít na Dashboard
                                    </a>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            </section>
        );
    }

    // ── Platba neúspěšná / zrušená / čekající ──
    const stateLabels: Record<string, { title: string; desc: string; bgBlob: string; bgIcon: string; borderIcon: string; textIcon: string }> = {
        CANCELED: {
            title: "Platba zrušena",
            desc: "Platbu jste zrušili. Můžete to zkusit znovu.",
            bgBlob: "bg-red-500/5",
            bgIcon: "bg-red-500/10",
            borderIcon: "border-red-500/20",
            textIcon: "text-red-400",
        },
        TIMEOUTED: {
            title: "Platba vypršela",
            desc: "Čas na dokončení platby vypršel. Zkuste to znovu.",
            bgBlob: "bg-yellow-500/5",
            bgIcon: "bg-yellow-500/10",
            borderIcon: "border-yellow-500/20",
            textIcon: "text-yellow-400",
        },
        CREATED: {
            title: "Čeká na zaplacení",
            desc: "Platba byla vytvořena, ale ještě nebyla dokončena.",
            bgBlob: "bg-yellow-500/5",
            bgIcon: "bg-yellow-500/10",
            borderIcon: "border-yellow-500/20",
            textIcon: "text-yellow-400",
        },
        PAYMENT_METHOD_CHOSEN: {
            title: "Zpracovává se",
            desc: "Platba se zpracovává. Vyčkejte prosím.",
            bgBlob: "bg-cyan-500/5",
            bgIcon: "bg-cyan-500/10",
            borderIcon: "border-cyan-500/20",
            textIcon: "text-cyan-400",
        },
    };

    const stateInfo = stateLabels[status?.state || ""] || {
        title: "Neznámý stav",
        desc: "Zkuste stránku obnovit nebo nás kontaktujte.",
        bgBlob: "bg-yellow-500/5",
        bgIcon: "bg-yellow-500/10",
        borderIcon: "border-yellow-500/20",
        textIcon: "text-yellow-400",
    };

    return (
        <section className="py-20 relative">
            <div className="absolute inset-0 -z-10">
                <div className={`absolute top-[30%] left-[40%] h-[400px] w-[400px] rounded-full ${stateInfo.bgBlob} blur-[120px]`} />
            </div>
            <div className="mx-auto max-w-md px-6 text-center">
                <div className="glass py-12">
                    <div className={`mx-auto mb-4 w-16 h-16 rounded-2xl ${stateInfo.bgIcon} border ${stateInfo.borderIcon} flex items-center justify-center`}>
                        <svg className={`w-8 h-8 ${stateInfo.textIcon}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
