import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Ceník AI Act compliance balíčků — od 4 999 Kč",
    description:
        "Ceník AIshield compliance balíčků: BASIC (4 999 Kč), PRO (14 999 Kč), ENTERPRISE (39 999 Kč). " +
        "Transparenční stránka, registr AI systémů, risk assessment, interní politika AI, školení. " +
        "Bezplatný sken webu. Služby pro české firmy a e-shopy v Praze, Brně, Ostravě i Olomouci.",
    alternates: { canonical: "/pricing" },
    openGraph: {
        title: "Ceník AI Act compliance balíčků — AIshield.cz",
        description: "Compliance balíčky od 4 999 Kč. Transparenční stránka, registr AI, risk assessment.",
        images: [
            {
                url: "https://aishield.cz/og-image.jpg",
                width: 1200,
                height: 630,
                alt: "AIshield.cz — AI Act compliance scanner pro české firmy",
                type: "image/jpeg",
            },
        ],
    },
};

function PricingJsonLd() {
    const schema = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        name: "AIshield.cz — AI Act compliance balíčky",
        description: "Ceník služeb pro zajištění souladu s EU AI Act",
        numberOfItems: 3,
        itemListElement: [
            {
                "@type": "ListItem",
                position: 1,
                item: {
                    "@type": "Product",
                    name: "BASIC — AI Act Compliance",
                    description: "Transparenční stránka, registr AI systémů, základní risk assessment pro malé firmy a e-shopy.",
                    offers: {
                        "@type": "Offer",
                        price: "4999",
                        priceCurrency: "CZK",
                        availability: "https://schema.org/InStock",
                        url: "https://aishield.cz/pricing",
                        priceValidUntil: "2026-12-31",
                    },
                },
            },
            {
                "@type": "ListItem",
                position: 2,
                item: {
                    "@type": "Product",
                    name: "PRO — AI Act Compliance",
                    description: "Kompletní compliance dokumentace, interní politika AI, právní šablony, prioritní podpora.",
                    offers: {
                        "@type": "Offer",
                        price: "14999",
                        priceCurrency: "CZK",
                        availability: "https://schema.org/InStock",
                        url: "https://aishield.cz/pricing",
                        priceValidUntil: "2026-12-31",
                    },
                },
            },
            {
                "@type": "ListItem",
                position: 3,
                item: {
                    "@type": "Product",
                    name: "ENTERPRISE — AI Act Compliance",
                    description: "Multi-domain sken, hromadná dokumentace, on-demand konzultace, compliance školení pro tým.",
                    offers: {
                        "@type": "Offer",
                        price: "39999",
                        priceCurrency: "CZK",
                        availability: "https://schema.org/InStock",
                        url: "https://aishield.cz/pricing",
                        priceValidUntil: "2026-12-31",
                    },
                },
            },
        ],
    };
    return (
        <script
            type="application/ld+json"
            dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
        />
    );
}

export default function PricingLayout({ children }: { children: React.ReactNode }) {
    return (
        <>
            <PricingJsonLd />
            {children}
        </>
    );
}
