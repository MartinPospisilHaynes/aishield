import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "O nás — AIshield.cz, český AI Act compliance scanner",
    description:
        "AIshield.cz je první specializovaný AI Act compliance scanner v České republice. " +
        "Automatizovaná detekce AI systémů na webu, generování compliance dokumentace, " +
        "transparenční stránky. Sídlo v Olomouci, služby pro firmy v celé ČR.",
    alternates: { canonical: "/about" },
    openGraph: {
        title: "O nás — AIshield.cz",
        description: "První český AI Act compliance scanner. Sídlo Olomouc, služby pro celou ČR.",
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

export default function AboutLayout({ children }: { children: React.ReactNode }) {
    return children;
}
