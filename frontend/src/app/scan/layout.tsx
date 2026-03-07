import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Bezplatný AI Act sken webu — zjistěte AI systémy za 60 sekund",
    description:
        "Zadejte URL vašeho webu a za 60 sekund zjistíte, jaké AI systémy na něm běží. " +
        "Chatboty, analytika, ML modely, doporučovací systémy. Bezplatně, bez registrace. " +
        "Automatizovaný compliance scanner pro české firmy dle EU AI Act (nařízení 2024/1689).",
    alternates: { canonical: "/scan" },
    openGraph: {
        title: "Bezplatný AI Act sken webu — AIshield.cz",
        description: "Zadejte URL a za 60 sekund zjistíte AI systémy na webu. Zdarma, bez registrace.",
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

export default function ScanLayout({ children }: { children: React.ReactNode }) {
    return children;
}
