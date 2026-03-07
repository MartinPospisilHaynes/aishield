import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Registrace — založte si účet zdarma",
    description:
        "Zaregistrujte se do AIshield.cz a získejte přístup ke compliance dashboardu, " +
        "AI Act dokumentaci a monitoringu. Bezplatná registrace, žádné závazky.",
    alternates: { canonical: "/registrace" },
    openGraph: {
        title: "Registrace — AIshield.cz",
        description:
            "Založte si účet zdarma. Bezplatný AI Act sken webu, compliance dashboard, dokumentace.",
        url: "https://aishield.cz/registrace",
        images: [
            {
                url: "https://aishield.cz/og-image.png",
                width: 1200,
                height: 630,
                alt: "AIshield.cz — Registrace zdarma",
                type: "image/jpeg",
            },
        ],
    },
    twitter: {
        card: "summary_large_image",
        title: "Registrace — AIshield.cz",
        description: "Založte si účet zdarma. Bezplatný AI Act sken webu, compliance dashboard.",
        images: ["https://aishield.cz/og-image.png"],
    },
};

export default function RegistraceLayout({ children }: { children: React.ReactNode }) {
    return children;
}
