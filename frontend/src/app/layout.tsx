import type { Metadata } from "next";
import "./globals.css";
import Providers from "@/components/providers";
import Header from "@/components/header";

export const metadata: Metadata = {
    title: "AIshield.cz — Váš štít proti pokutám EU za AI Act",
    description:
        "Automatizovaný AI Act compliance scanner pro české firmy. " +
        "Zjistěte za 60 sekund, jestli váš web splňuje nový zákon EU o umělé inteligenci. " +
        "Deadline: srpen 2026. Pokuta až 35 milionů EUR.",
    keywords: [
        "AI Act",
        "compliance",
        "umělá inteligence",
        "zákon EU",
        "scanner",
        "audit",
        "chatbot",
        "transparence",
        "české firmy",
    ],
    authors: [{ name: "AIshield.cz" }],
    openGraph: {
        title: "AIshield.cz — Váš štít proti pokutám EU",
        description: "AI Act compliance scanner. Zjistěte stav vašeho webu za 60 sekund.",
        url: "https://aishield.cz",
        siteName: "AIshield.cz",
        locale: "cs_CZ",
        type: "website",
    },
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="cs">
            <head>
                <link
                    href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap"
                    rel="stylesheet"
                />
            </head>
            <body className="bg-dark-900 text-slate-100">
                <Providers>
                    {/* ── Header ── */}
                    <Header />

                    {/* ── Main Content ── */}
                    <main className="min-h-screen overflow-x-hidden">{children}</main>

                    {/* ── Footer ── */}
                    <footer className="border-t border-white/[0.06] bg-dark-950">
                        <div className="mx-auto max-w-7xl px-6 py-16">
                            <div className="grid grid-cols-1 gap-10 md:grid-cols-4">
                                {/* Brand */}
                                <div>
                                    <div className="flex items-center gap-2 mb-4">
                                        <span className="text-xl font-extrabold tracking-tighter">
                                            <span className="text-white">AI</span>
                                            <span className="neon-text">shield</span>
                                            <span className="text-slate-600 text-sm font-normal ml-0.5">.cz</span>
                                        </span>
                                    </div>
                                    <p className="text-sm text-slate-500 leading-relaxed">
                                        Váš štít proti pokutám EU za AI Act.
                                        Automatizovaný compliance scanner pro české firmy.
                                    </p>
                                </div>

                                {/* Produkt */}
                                <div>
                                    <h3 className="font-semibold text-slate-300 mb-4 text-sm uppercase tracking-wider">Produkt</h3>
                                    <ul className="space-y-3 text-sm text-slate-500">
                                        <li><a href="/scan" className="hover:text-neon-fuchsia transition-colors">Skenovat web</a></li>
                                        <li><a href="/dotaznik" className="hover:text-neon-fuchsia transition-colors">AI dotazník</a></li>
                                        <li><a href="/pricing" className="hover:text-neon-fuchsia transition-colors">Ceník</a></li>
                                        <li><a href="/about" className="hover:text-neon-fuchsia transition-colors">Jak to funguje</a></li>
                                    </ul>
                                </div>

                                {/* Právní */}
                                <div>
                                    <h3 className="font-semibold text-slate-300 mb-4 text-sm uppercase tracking-wider">Právní</h3>
                                    <ul className="space-y-3 text-sm text-slate-500">
                                        <li><a href="/privacy" className="hover:text-neon-fuchsia transition-colors">Ochrana soukromí</a></li>
                                        <li><a href="/terms" className="hover:text-neon-fuchsia transition-colors">Obchodní podmínky</a></li>
                                        <li><a href="/gdpr" className="hover:text-neon-fuchsia transition-colors">GDPR</a></li>
                                    </ul>
                                </div>

                                {/* Kontakt */}
                                <div>
                                    <h3 className="font-semibold text-slate-300 mb-4 text-sm uppercase tracking-wider">Kontakt</h3>
                                    <ul className="space-y-3 text-sm text-slate-500">
                                        <li className="text-slate-400">Martin Haynes</li>
                                        <li>IČO: 17889251</li>
                                        <li>Mlýnská 53, 783 53 Velká Bystřice</li>
                                        <li><a href="tel:+420732716141" className="hover:text-neon-cyan transition-colors">+420 732 716 141</a></li>
                                        <li><a href="mailto:info@desperados-design.cz" className="hover:text-neon-cyan transition-colors">info@desperados-design.cz</a></li>
                                    </ul>
                                </div>
                            </div>

                            <div className="mt-12 border-t border-white/[0.06] pt-8 text-center text-sm text-slate-600">
                                &copy; {new Date().getFullYear()} AIshield.cz — Provozovatel: Martin Haynes, IČO: 17889251
                            </div>
                        </div>
                    </footer>
                </Providers>
            </body>
        </html>
    );
}
