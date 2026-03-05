import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";

const inter = Inter({
    subsets: ["latin", "latin-ext"],
    display: "swap",
    variable: "--font-inter",
});
import "./globals.css";
import Providers from "@/components/providers";
import HeaderVisibility from "@/components/header-visibility";
import ConsentBanner from "@/components/consent-banner";


/* Viewport: zakázat auto-zoom na mobilních zařízeních při focusu na input */
export const viewport: Viewport = {
    width: "device-width",
    initialScale: 1,
    maximumScale: 5,
    userScalable: true,
};

export const metadata: Metadata = {
    metadataBase: new URL("https://aishield.cz"),
    title: {
        default: "AI Act compliance pro české weby — skenujte zdarma za 60 sekund | AIshield.cz",
        template: "%s | AIshield.cz",
    },
    description:
        "Bezplatný AI Act compliance scanner pro české firmy a e-shopy. " +
        "Zjistěte za 60 sekund, jaké AI systémy na vašem webu běží a co musíte udělat do 2. srpna 2026. " +
        "Pokuta až 35 mil. EUR. Jsme jediný specializovaný nástroj v ČR.",
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
        "AI Act e-shop",
        "AI Act pokuty",
        "AI Act článek 50",
        "transparenční stránka",
        "AI systémy na webu",
        "AI Act Česko",
        "AI Act povinnosti",
    ],
    authors: [{ name: "AIshield.cz" }],
    openGraph: {
        title: {
            default: "AI Act compliance pro české weby — skenujte zdarma za 60 sekund | AIshield.cz",
            template: "%s | AIshield.cz",
        },
        description:
            "Automatizovaný compliance scanner pro české firmy. Zjistěte za 60 sekund, " +
            "jestli váš web splňuje zákon EU o AI. Pokuta až 35 mil. €. Deadline: srpen 2026.",
        url: "https://aishield.cz",
        siteName: "AIshield.cz",
        locale: "cs_CZ",
        type: "website",
        images: [
            {
                url: "/og-image.jpg",
                width: 1200,
                height: 630,
                type: "image/jpeg",
                alt: "AIshield.cz — AI Act compliance scanner pro české firmy",
            },
        ],
    },
    twitter: {
        card: "summary_large_image",
        title: {
            default: "AI Act compliance pro české weby — skenujte zdarma za 60 sekund | AIshield.cz",
            template: "%s | AIshield.cz",
        },
        description:
            "Zjistěte za 60 sekund, jestli váš web splňuje zákon EU o AI. " +
            "Pokuta až 35 mil. €. Deadline: srpen 2026.",
        images: [
            {
                url: "/og-image.jpg",
                width: 1200,
                height: 630,
                alt: "AIshield.cz — AI Act compliance scanner pro české firmy",
            },
        ],
    },
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="cs" className={inter.variable}>
            <head>
                <meta name="theme-color" content="#7c3aed" />
                <link rel="alternate" type="application/rss+xml" title="AIshield.cz Blog" href="/blog/feed.xml" />
                <meta name="google-site-verification" content="yQ-vZanc4EnuKMrENxtiKTKdcAYrTjLoirbcka4rS9s" />
                {/* ── Schema.org JSON-LD ── */}
                <script
                    type="application/ld+json"
                    dangerouslySetInnerHTML={{
                        __html: JSON.stringify({
                            "@context": "https://schema.org",
                            "@graph": [
                                {
                                    "@type": "Organization",
                                    "@id": "https://aishield.cz/#organization",
                                    "name": "AIshield.cz",
                                    "url": "https://aishield.cz",
                                    "logo": "https://aishield.cz/og-image.jpg",
                                    "description": "Automatizovaný AI Act compliance scanner pro české firmy a e-shopy. Skenování AI systémů, riziková klasifikace, generování dokumentace.",
                                    "foundingDate": "2025",
                                    "address": {
                                        "@type": "PostalAddress",
                                        "addressCountry": "CZ",
                                        "addressRegion": "Olomoucký kraj"
                                    },
                                    "contactPoint": {
                                        "@type": "ContactPoint",
                                        "telephone": "+420-732-716-141",
                                        "email": "info@aishield.cz",
                                        "contactType": "customer service",
                                        "availableLanguage": "Czech"
                                    },
                                    "sameAs": []
                                },
                                {
                                    "@type": "WebSite",
                                    "@id": "https://aishield.cz/#website",
                                    "name": "AIshield.cz",
                                    "url": "https://aishield.cz",
                                    "publisher": { "@id": "https://aishield.cz/#organization" },
                                    "inLanguage": "cs",
                                    "potentialAction": {
                                        "@type": "SearchAction",
                                        "target": "https://aishield.cz/scan?url={search_term_string}",
                                        "query-input": "required name=search_term_string"
                                    }
                                },
                                {
                                    "@type": "SoftwareApplication",
                                    "@id": "https://aishield.cz/#software",
                                    "name": "AIshield Scanner",
                                    "applicationCategory": "BusinessApplication",
                                    "operatingSystem": "Web",
                                    "offers": {
                                        "@type": "Offer",
                                        "price": "0",
                                        "priceCurrency": "CZK",
                                        "description": "Bezplatný AI Act sken webu"
                                    },
                                    "description": "Automatizovaný scanner AI systémů na webových stránkách pro splnění EU AI Act (Nařízení 2024/1689). Detekce chatbotů, analytiky, ML modelů a dalších AI nástrojů.",
                                    "creator": { "@id": "https://aishield.cz/#organization" }
                                },
                                {
                                    "@type": "HowTo",
                                    "@id": "https://aishield.cz/#howto",
                                    "name": "Jak splnit AI Act pro váš web",
                                    "description": "4 kroky ke kompletní AI Act compliance pro český web nebo e-shop",
                                    "step": [
                                        {
                                            "@type": "HowToStep",
                                            "position": 1,
                                            "name": "Skenujte web",
                                            "text": "Zadejte URL vašeho webu do AIshield scanneru. Za 60 sekund dostanete přehled všech AI systémů, které na webu běží."
                                        },
                                        {
                                            "@type": "HowToStep",
                                            "position": 2,
                                            "name": "Zjistěte rizika",
                                            "text": "Scanner automaticky klasifikuje nalezené AI systémy podle rizikových kategorií AI Actu a ukáže, jaké povinnosti z nich plynou."
                                        },
                                        {
                                            "@type": "HowToStep",
                                            "position": 3,
                                            "name": "Vyplňte dotazník",
                                            "text": "Krátký dotazník (5 minut) pokryje i interní AI systémy, které sken nevidí — ChatGPT, AI v účetnictví, automatizaci."
                                        },
                                        {
                                            "@type": "HowToStep",
                                            "position": 4,
                                            "name": "Obdržíte dokumenty",
                                            "text": "Do 7 dnů dostanete kompletní compliance dokumentaci: transparenční stránku, registr AI, risk assessment, interní AI politiku a školení."
                                        }
                                    ]
                                }
                            ]
                        })
                    }}
                />
                {/* ── Google Analytics 4 (GA4) s Consent Mode v2 ── */}
                <script
                    async
                    src="https://www.googletagmanager.com/gtag/js?id=G-13DJZ48E3H"
                />
                <script dangerouslySetInnerHTML={{
                    __html: `
                    window.dataLayer = window.dataLayer || [];
                    function gtag(){dataLayer.push(arguments);}
                    // Consent Mode v2 — výchozí stav: denied (GDPR)
                    gtag('consent', 'default', {
                        'analytics_storage': 'denied',
                        'ad_storage': 'denied',
                        'wait_for_update': 500
                    });
                    gtag('js', new Date());
                    gtag('config', 'G-13DJZ48E3H', {
                        send_page_view: true,
                        cookie_flags: 'SameSite=Lax;Secure'
                    });
                    // Po cookie consent aktualizujeme na granted
                    try {
                        var consent = JSON.parse(localStorage.getItem('aishield_consent_v1') || '{}');
                        if (consent.cookies === true) {
                            gtag('consent', 'update', {
                                'analytics_storage': 'granted'
                            });
                        }
                    } catch(e) {}
                `}} />
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
            <body className={`bg-dark-900 text-slate-100 overflow-x-hidden ${inter.className}`}>
                <Providers>
                    {/* ── Header (skrytý v dotazníku — koliduje s progress barem) ── */}
                    <HeaderVisibility />

                    {/* ── Main Content ── */}
                    <main className="min-h-screen overflow-x-hidden">{children}</main>

                    {/* ── Footer ── */}
                    <footer className="border-t border-white/[0.06] bg-dark-950">
                        <div className="mx-auto max-w-7xl px-6 py-16">
                            <div className="grid grid-cols-1 gap-10 sm:grid-cols-2 md:grid-cols-5">
                                {/* Brand */}
                                <div>
                                    <div className="flex items-center gap-2 mb-4">
                                        <svg className="w-7 h-7" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M16 1.5C16 1.5 4 6 4 6v10.5c0 4.2 1.8 8.2 4.8 11.1C11.5 30.2 13.9 31.5 16 32c2.1-.5 4.5-1.8 7.2-4.4C26.2 24.7 28 20.7 28 16.5V6L16 1.5z" fill="url(#shield-grad-ft)" fillOpacity="0.25" stroke="url(#shield-grad-ft)" strokeWidth="2" strokeLinejoin="round" />
                                            <path d="M16 5C16 5 7 9 7 9v7.5c0 3.3 1.4 6.5 3.8 8.8C12.9 27.3 14.7 28.3 16 28.7c1.3-.4 3.1-1.4 5.2-3.4C23.6 22.9 25 19.8 25 16.5V9L16 5z" fill="none" stroke="url(#shield-grad-ft)" strokeWidth="0.8" opacity="0.4" strokeLinejoin="round" />
                                            <path d="M12 16.5l3 3 5.5-6.5" stroke="url(#shield-grad-ft)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                                            <defs>
                                                <linearGradient id="shield-grad-ft" x1="4" y1="2" x2="28" y2="30" gradientUnits="userSpaceOnUse">
                                                    <stop stopColor="#d946ef" />
                                                    <stop offset="0.5" stopColor="#a855f7" />
                                                    <stop offset="1" stopColor="#06b6d4" />
                                                </linearGradient>
                                            </defs>
                                        </svg>
                                        <span className="text-xl font-extrabold tracking-tighter" translate="no">
                                            <span className="text-white">AI</span>
                                            <span className="neon-text">shield</span>
                                            <span className="text-slate-600 text-sm font-normal ml-0.5">.cz</span>
                                        </span>
                                    </div>
                                    <p className="text-sm text-slate-400 leading-relaxed">
                                        Váš štít proti pokutám EU za AI Act.
                                        Automatizovaný compliance scanner pro české firmy.
                                    </p>
                                </div>

                                {/* Produkt */}
                                <div>
                                    <h3 className="font-semibold text-slate-300 mb-4 text-sm uppercase tracking-wider">Produkt</h3>
                                    <ul className="space-y-1 text-sm text-slate-500">
                                        <li><a href="/scan" className="hover:text-neon-fuchsia transition-colors inline-block py-3">Skenovat web</a></li>
                                        <li><a href="/dotaznik" className="hover:text-neon-fuchsia transition-colors inline-block py-3">AI dotazník</a></li>
                                        <li><a href="/pricing" className="hover:text-neon-fuchsia transition-colors inline-block py-3 min-w-[44px]">Ceník</a></li>
                                        <li><a href="/about" className="hover:text-neon-fuchsia transition-colors inline-block py-3">Jak to funguje</a></li>
                                    </ul>
                                </div>

                                {/* Právní */}
                                <div>
                                    <h3 className="font-semibold text-slate-300 mb-4 text-sm uppercase tracking-wider">Právní</h3>
                                    <ul className="space-y-1 text-sm text-slate-500">
                                        <li><a href="/privacy" className="hover:text-neon-fuchsia transition-colors inline-block py-3">Ochrana soukromí</a></li>
                                        <li><a href="/terms" className="hover:text-neon-fuchsia transition-colors inline-block py-3">Obchodní podmínky</a></li>
                                        <li><a href="/gdpr" className="hover:text-neon-fuchsia transition-colors inline-block py-3 min-w-[44px]">GDPR</a></li>
                                        <li><a href="/cookies" className="hover:text-neon-fuchsia transition-colors inline-block py-3">Cookies</a></li>
                                        <li><a href="/ai-act-souhlas" className="hover:text-neon-fuchsia transition-colors inline-block py-3">AI Act souhlas</a></li>
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
                                    <ul className="space-y-0 text-sm">
                                        <li>
                                            <a href="https://eur-lex.europa.eu/legal-content/CS/TXT/?uri=CELEX:32024R1689" target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:text-cyan-300 transition-colors font-medium inline-flex items-center gap-1 py-3">
                                                Nařízení EU 2024/1689 (AI Act)
                                                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" /></svg>
                                            </a>
                                        </li>
                                        <li>
                                            <a href="https://www.mpo.gov.cz/cz/podnikani/digitalni-ekonomika/umela-inteligence/" target="_blank" rel="noopener noreferrer" className="text-slate-500 hover:text-cyan-400 transition-colors inline-flex items-center gap-1 py-3">
                                                MPO — Umělá inteligence
                                                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" /></svg>
                                            </a>
                                        </li>
                                        <li>
                                            <a href="https://www.mpo.gov.cz/assets/cz/podnikani/2024/9/Narodni-strategie-umele-intelience-CR-2030.pdf" target="_blank" rel="noopener noreferrer" className="text-slate-500 hover:text-cyan-400 transition-colors inline-flex items-center gap-1 py-3">
                                                NAIS — Národní strategie AI 2030 (PDF)
                                                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" /></svg>
                                            </a>
                                        </li>
                                        <li>
                                            <a href="https://digital-strategy.ec.europa.eu/cs/policies/european-approach-artificial-intelligence" target="_blank" rel="noopener noreferrer" className="text-slate-500 hover:text-cyan-400 transition-colors inline-flex items-center gap-1 py-3">
                                                EU Digital Strategy — AI
                                                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" /></svg>
                                            </a>
                                        </li>
                                    </ul>
                                </div>

                                {/* Kontakt */}
                                <div>
                                    <h3 className="font-semibold text-slate-300 mb-4 text-sm uppercase tracking-wider">Kontakt</h3>
                                    <ul className="space-y-1 text-sm text-slate-500">
                                        <li className="text-slate-400">Martin Haynes</li>
                                        <li>IČO: 17889251</li>
                                        <li><a href="tel:+420732716141" className="hover:text-neon-cyan transition-colors flex items-center h-11">+420 732 716 141</a></li>
                                        <li><a href="mailto:info@aishield.cz" className="hover:text-neon-cyan transition-colors flex items-center h-11">info@aishield.cz</a></li>
                                    </ul>
                                </div>
                            </div>

                            <div className="mt-12 border-t border-white/[0.06] pt-8">
                                <div className="flex flex-wrap justify-center gap-x-6 gap-y-2 text-xs text-slate-500 mb-6">
                                    <a href="/ai-act" className="hover:text-slate-400 transition-colors">AI Act průvodce</a>
                                    <a href="/ai-act/checklist" className="hover:text-slate-400 transition-colors">AI Act checklist</a>
                                    <a href="/ai-act/pokuty" className="hover:text-slate-400 transition-colors">Pokuty</a>
                                    <a href="/ai-act/clanek-50" className="hover:text-slate-400 transition-colors">Článek 50</a>
                                    <a href="/ai-act/e-shopy" className="hover:text-slate-400 transition-colors">E-shopy a AI Act</a>
                                    <a href="/integrace" className="hover:text-slate-400 transition-colors">Integrace</a>
                                    <a href="/integrace/smartsupp" className="hover:text-slate-400 transition-colors">Smartsupp</a>
                                    <a href="/integrace/google-analytics" className="hover:text-slate-400 transition-colors">Google Analytics</a>
                                    <a href="/integrace/shoptet" className="hover:text-slate-400 transition-colors">Shoptet</a>
                                    <a href="/srovnani" className="hover:text-slate-400 transition-colors">Srovnání</a>
                                    <a href="/blog" className="hover:text-slate-400 transition-colors">Blog</a>
                                    <a href="/metodika" className="hover:text-slate-400 transition-colors">Metodika</a>
                                    <a href="/report" className="hover:text-slate-400 transition-colors">Data report</a>
                                    <a href="/faq" className="hover:text-slate-400 transition-colors">FAQ</a>
                                </div>
                                <div className="text-center text-sm text-slate-500">
                                    <p>&copy; {new Date().getFullYear()} AIshield.cz — Provozovatel: Martin Haynes, IČO: 17889251</p>
                                    <p className="mt-2">
                                        Vytvořila agentura{" "}
                                        <a
                                            href="https://www.desperados-design.cz"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="font-semibold transition-colors hover:brightness-125 inline-block py-3"
                                            style={{ color: "#d946ef" }}
                                        >
                                            Desperados-design.cz
                                        </a>
                                    </p>
                                </div>
                            </div>
                        </div>
                    </footer>
                </Providers>
                <ConsentBanner />
            </body>
        </html>
    );
}
