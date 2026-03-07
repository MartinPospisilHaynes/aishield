"use client";

/**
 * Shoptet Addon — Hlavní stránka (iframe entry point)
 * URL: /shoptet?installation_id=XXX
 * Rozhoduje, zda zobrazit wizard nebo dashboard.
 */

import { useSearchParams } from "next/navigation";
import { useEffect, useState, Suspense } from "react";
import { getDashboard, type DashboardData } from "@/lib/shoptet-api";
import ShoptetWizard from "./wizard";
import ShoptetDashboard from "./dashboard";

function ShoptetContent() {
    const searchParams = useSearchParams();
    const installationId = searchParams.get("installation_id") || "";

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [data, setData] = useState<DashboardData | null>(null);

    useEffect(() => {
        if (!installationId) {
            setError("Chybí installation_id parametr.");
            setLoading(false);
            return;
        }

        getDashboard(installationId)
            .then((d) => {
                setData(d);
                setLoading(false);
            })
            .catch((e) => {
                setError(e.message || "Nepodařilo se načíst data.");
                setLoading(false);
            });
    }, [installationId]);

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="text-center">
                    <div className="w-8 h-8 border-2 border-neon-cyan/30 border-t-neon-cyan rounded-full animate-spin mx-auto mb-3" />
                    <p className="text-slate-400 text-sm">Načítám data...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="glass p-6 text-center max-w-md mx-auto mt-12">
                <div className="text-3xl mb-3">&#x26A0;</div>
                <h2 className="text-lg font-bold text-white mb-2">Chyba</h2>
                <p className="text-slate-400 text-sm">{error}</p>
            </div>
        );
    }

    if (!data) return null;

    // Pokud wizard nebyl dokončen → zobrazit wizard
    if (!data.installation.wizard_completed_at) {
        return (
            <ShoptetWizard
                installationId={installationId}
                eshopName={data.installation.eshop_name || "Váš e-shop"}
                onComplete={() => {
                    // Po dokončení wizardu znovu načíst dashboard
                    setLoading(true);
                    getDashboard(installationId)
                        .then((d) => { setData(d); setLoading(false); })
                        .catch(() => setLoading(false));
                }}
            />
        );
    }

    // Wizard dokončen → zobrazit dashboard
    return (
        <ShoptetDashboard
            data={data}
            installationId={installationId}
            onRefresh={() => {
                setLoading(true);
                getDashboard(installationId)
                    .then((d) => { setData(d); setLoading(false); })
                    .catch(() => setLoading(false));
            }}
        />
    );
}

export default function ShoptetPage() {
    return (
        <Suspense fallback={
            <div className="flex items-center justify-center min-h-[400px]">
                <div className="w-8 h-8 border-2 border-neon-cyan/30 border-t-neon-cyan rounded-full animate-spin" />
            </div>
        }>
            <ShoptetContent />
        </Suspense>
    );
}
