import type { Metadata, Viewport } from "next";

/**
 * Shoptet Addon — Iframe Layout
 * Minimální layout BEZ hlavičky/patičky AIshield webu.
 * Shoptet načítá tento panel v iframe uvnitř svého adminu.
 */

export const metadata: Metadata = {
    title: "AI Act Compliance — AIshield.cz",
    robots: { index: false, follow: false },
};

export const viewport: Viewport = {
    width: "device-width",
    initialScale: 1,
};

export default function ShoptetLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="min-h-screen bg-dark-900 text-slate-100 p-4 md:p-6">
            {children}
        </div>
    );
}
