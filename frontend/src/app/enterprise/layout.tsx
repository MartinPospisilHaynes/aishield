import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Enterprise AI Act compliance — balíček na míru pro velké firmy",
    description:
        "Enterprise compliance balíček pro velké firmy a korporace. Kompletní AI Act audit, " +
        "právní konzultace, implementace compliance procesů, školení zaměstnanců. " +
        "Individuální přístup, dedicated account manager.",
    alternates: { canonical: "/enterprise" },
    openGraph: {
        title: "Enterprise AI Act compliance — AIshield.cz",
        description: "Compliance balíček na míru pro velké firmy. AI Act audit, právní konzultace, školení.",
        images: [
            {
                url: "https://aishield.cz/og-image.png",
                width: 1200,
                height: 630,
                alt: "AIshield.cz — AI Act compliance scanner pro české firmy",
                type: "image/jpeg",
            },
        ],
    },
};

export default function EnterpriseLayout({ children }: { children: React.ReactNode }) {
    return children;
}
