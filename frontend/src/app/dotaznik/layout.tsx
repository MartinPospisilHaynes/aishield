import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "AI Act compliance dotazník — zmapujte všechny AI systémy",
    description:
        "Interaktivní dotazník pro kompletní zmapování AI systémů ve vaší firmě. " +
        "Pokrývá chatboty, analytiku, interní AI nástroje, HR systémy i automatizaci. " +
        "Výsledky slouží jako základ pro compliance dokumentaci dle EU AI Act.",
    alternates: { canonical: "/dotaznik" },
    openGraph: {
        title: "AI Act compliance dotazník — AIshield.cz",
        description: "Zmapujte všechny AI systémy ve firmě. Základ pro compliance dokumentaci.",
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

export default function DotaznikLayout({ children }: { children: React.ReactNode }) {
    return children;
}
