import type { Metadata } from "next";
import "./globals.css";
import Providers from "@/components/providers";
import Header from "@/components/header";
import ConsentBanner from "@/components/consent-banner";

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
        <html lang="cs" translate="no" className="notranslate">
            <head>
                <meta name="theme-color" content="#7c3aed" />
                <meta name="google" content="notranslate" />
                <link
                    href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap"
                    rel="stylesheet"
                />
                {/* Auto-reload on chunk load error (stale deploy cache) */}
                <script dangerouslySetInnerHTML={{
                    __html: `
                    if (typeof window !== 'undefined') {
                        window.addEventListener('error', function(e) {
                            if (e.message && (e.message.indexOf('ChunkLoadError') !== -1 || e.message.indexOf('Loading chunk') !== -1 || e.message.indexOf('Failed to fetch') !== -1)) {
                                if (!sessionStorage.getItem('chunk_reload')) {
                                    sessionStorage.setItem('chunk_reload', '1');
                                    window.location.reload();
                                }
                            }
                        });
                    }
                `}} />
            </head>
            <body className="bg-dark-900 text-slate-100">
                <Providers>
                    {/* ── Header ── */}
                    <Header />

                    {/* ── Main Content ── */}
                    <main className="min-h-screen">{children}</main>

                    {/* ── Footer ── */}
                    <footer className="border-t border-white/[0.06] bg-dark-950">
                        <div className="mx-auto max-w-7xl px-6 py-16">
                            <div className="grid grid-cols-1 gap-10 md:grid-cols-5">
                                {/* Brand */}
                                <div>
                                    <div className="flex items-center gap-2 mb-4">
                                        <svg className="w-7 h-7" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M16 2L4 7v9c0 7.73 5.12 14.95 12 17 6.88-2.05 12-9.27 12-17V7L16 2z" fill="url(#shield-grad-f)" fillOpacity="0.15" stroke="url(#shield-grad-f)" strokeWidth="1.5" />
                                            <path d="M12 16l3 3 5-6" stroke="url(#shield-grad-f)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                            <defs>
                                                <linearGradient id="shield-grad-f" x1="4" y1="2" x2="28" y2="28" gradientUnits="userSpaceOnUse">
                                                    <stop stopColor="#d946ef" />
                                                    <stop offset="1" stopColor="#06b6d4" />
                                                </linearGradient>
                                            </defs>
                                        </svg>
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
                                        <li><a href="/cookies" className="hover:text-neon-fuchsia transition-colors">Cookies</a></li>
                                        <li><a href="/ai-act-souhlas" className="hover:text-neon-fuchsia transition-colors">AI Act souhlas</a></li>
                                    </ul>
                                </div>

                                {/* Legislativa EU */}
                                <div>
                                    <h3 className="font-semibold text-slate-300 mb-4 text-sm uppercase tracking-wider">
                                        <span className="inline-flex items-center gap-1.5">
                                            <svg className="w-4 h-4 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" /></svg>
                                            Legislativa EU
                                        </span>
                                    </h3>
                                    <ul className="space-y-3 text-sm">
                                        <li>
                                            <a href="https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689" target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:text-cyan-300 transition-colors font-medium inline-flex items-center gap-1">
                                                Nařízení EU 2024/1689 (AI Act)
                                                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" /></svg>
                                            </a>
                                        </li>
                                        <li>
                                            <a href="https://www.mpo.gov.cz/cz/podnikani/umela-inteligence/" target="_blank" rel="noopener noreferrer" className="text-slate-500 hover:text-cyan-400 transition-colors inline-flex items-center gap-1">
                                                MPO — Umělá inteligence
                                                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" /></svg>
                                            </a>
                                        </li>
                                        <li>
                                            <a href="https://www.vlada.cz/cz/evropske-zalezitosti/umela-inteligence/narodni-strategie-umele-inteligence-193246/" target="_blank" rel="noopener noreferrer" className="text-slate-500 hover:text-cyan-400 transition-colors inline-flex items-center gap-1">
                                                NAIS — Národní strategie AI
                                                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" /></svg>
                                            </a>
                                        </li>
                                        <li>
                                            <a href="https://digital-strategy.ec.europa.eu/cs/policies/european-approach-artificial-intelligence" target="_blank" rel="noopener noreferrer" className="text-slate-500 hover:text-cyan-400 transition-colors inline-flex items-center gap-1">
                                                EU Digital Strategy — AI
                                                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" /></svg>
                                            </a>
                                        </li>
                                    </ul>
                                </div>

                                {/* Kontakt */}
                                <div>
                                    <h3 className="font-semibold text-slate-300 mb-4 text-sm uppercase tracking-wider">Kontakt</h3>
                                    <ul className="space-y-3 text-sm text-slate-500">
                                        <li className="text-slate-400">Martin Haynes</li>
                                        <li>IČO: 17889251</li>
                                        <li><a href="tel:+420732716141" className="hover:text-neon-cyan transition-colors">+420 732 716 141</a></li>
                                        <li><a href="mailto:info@aishield.cz" className="hover:text-neon-cyan transition-colors">info@aishield.cz</a></li>
                                    </ul>
                                </div>
                            </div>

                            <div className="mt-12 border-t border-white/[0.06] pt-8 text-center text-sm text-slate-600">
                                <p>&copy; {new Date().getFullYear()} AIshield.cz — Provozovatel: Martin Haynes, IČO: 17889251</p>
                                <p className="mt-2">
                                    Vytvořila agentura{" "}
                                    <a
                                        href="https://www.desperados-design.cz"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="font-semibold transition-colors hover:brightness-125"
                                        style={{ color: "#ff2d95" }}
                                    >
                                        Desperados-design.cz
                                    </a>
                                </p>
                            </div>
                        </div>
                    </footer>
                </Providers>
                <ConsentBanner />
            </body>
        </html>
    );
}
