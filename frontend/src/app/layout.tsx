import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
    title: "AIshield.cz — Váš štít proti pokutám EU za AI Act",
    description:
        "Automatizovaný AI Act compliance scanner pro české firmy. " +
        "Zjistěte za 60 sekund, jestli váš web splňuje nový zákon EU o umělé inteligenci. " +
        "Deadline: srpen 2026. Pokuta až 35 milionů EUR.",
    keywords: [
        "AI Act",
        "compliance",
        "GDPR",
        "umělá inteligence",
        "zákon EU",
        "scanner",
        "audit",
        "chatbot",
        "transparence",
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
            <body>
                {/* ── Header ── */}
                <header className="sticky top-0 z-50 border-b border-gray-200 bg-white/80 backdrop-blur-sm">
                    <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
                        <a href="/" className="flex items-center gap-2">
                            <span className="text-2xl">🛡️</span>
                            <span className="text-xl font-bold text-shield-900">
                                AI<span className="text-shield-600">shield</span>.cz
                            </span>
                        </a>

                        <div className="hidden md:flex items-center gap-8">
                            <a href="/scan" className="text-sm text-gray-600 hover:text-shield-600 transition-colors">
                                Skenovat web
                            </a>
                            <a href="/pricing" className="text-sm text-gray-600 hover:text-shield-600 transition-colors">
                                Ceník
                            </a>
                            <a href="/about" className="text-sm text-gray-600 hover:text-shield-600 transition-colors">
                                Jak to funguje
                            </a>
                            <a href="/login" className="btn-secondary text-sm px-4 py-2">
                                Přihlásit se
                            </a>
                            <a href="/scan" className="btn-primary text-sm px-4 py-2">
                                Skenovat ZDARMA
                            </a>
                        </div>
                    </nav>
                </header>

                {/* ── Main Content ── */}
                <main className="min-h-screen">{children}</main>

                {/* ── Footer ── */}
                <footer className="border-t border-gray-200 bg-gray-50">
                    <div className="mx-auto max-w-7xl px-6 py-12">
                        <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
                            {/* Brand */}
                            <div>
                                <div className="flex items-center gap-2 mb-4">
                                    <span className="text-xl">🛡️</span>
                                    <span className="font-bold text-shield-900">
                                        AI<span className="text-shield-600">shield</span>.cz
                                    </span>
                                </div>
                                <p className="text-sm text-gray-500">
                                    Váš štít proti pokutám EU za AI Act.
                                    Automatizovaný compliance scanner pro české firmy.
                                </p>
                            </div>

                            {/* Produkt */}
                            <div>
                                <h3 className="font-semibold text-gray-900 mb-3">Produkt</h3>
                                <ul className="space-y-2 text-sm text-gray-500">
                                    <li><a href="/scan" className="hover:text-shield-600">Skenovat web</a></li>
                                    <li><a href="/pricing" className="hover:text-shield-600">Ceník</a></li>
                                    <li><a href="/about" className="hover:text-shield-600">Jak to funguje</a></li>
                                    <li><a href="/faq" className="hover:text-shield-600">Časté otázky</a></li>
                                </ul>
                            </div>

                            {/* Právní */}
                            <div>
                                <h3 className="font-semibold text-gray-900 mb-3">Právní</h3>
                                <ul className="space-y-2 text-sm text-gray-500">
                                    <li><a href="/privacy" className="hover:text-shield-600">Ochrana soukromí</a></li>
                                    <li><a href="/terms" className="hover:text-shield-600">Obchodní podmínky</a></li>
                                    <li><a href="/gdpr" className="hover:text-shield-600">GDPR</a></li>
                                </ul>
                            </div>

                            {/* Kontakt */}
                            <div>
                                <h3 className="font-semibold text-gray-900 mb-3">Kontakt</h3>
                                <ul className="space-y-2 text-sm text-gray-500">
                                    <li>Martin Haynes</li>
                                    <li>IČO: 17889251</li>
                                    <li>Mlýnská 53, 783 53 Velká Bystřice</li>
                                    <li><a href="tel:+420732716141" className="hover:text-shield-600">+420 732 716 141</a></li>
                                    <li><a href="mailto:info@desperados-design.cz" className="hover:text-shield-600">info@desperados-design.cz</a></li>
                                </ul>
                            </div>
                        </div>

                        <div className="mt-8 border-t border-gray-200 pt-8 text-center text-sm text-gray-400">
                            © {new Date().getFullYear()} AIshield.cz — Provozovatel: Martin Haynes, IČO: 17889251
                        </div>
                    </div>
                </footer>
            </body>
        </html>
    );
}
