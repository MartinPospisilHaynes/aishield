import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Přihlášení do AIshield.cz",
    description:
        "Přihlaste se do svého AIshield účtu. Přístup ke compliance dashboardu, " +
        "výsledkům skenů, AI Act dokumentaci a monitoringu vašeho webu.",
    alternates: { canonical: "/login" },
    robots: { index: false, follow: true },
    openGraph: {
        title: "Přihlášení — AIshield.cz",
        description: "Přihlaste se a spravujte AI Act compliance svého webu.",
        url: "https://aishield.cz/login",
        images: [
            {
                url: "https://aishield.cz/og-image.png",
                width: 1200,
                height: 630,
                alt: "AIshield.cz — Přihlášení",
                type: "image/jpeg",
            },
        ],
    },
};

export default function LoginLayout({ children }: { children: React.ReactNode }) {
    return children;
}
