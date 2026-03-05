"use client";

/**
 * AIshield.cz — Logo Wall
 * Sekce "Důvěřují nám lídři českého trhu" na homepage.
 *
 * Načítá partnery z Supabase tabulky `pioneer_outreach`
 * kde `published_on_web = true`. Pokud žádní nejsou,
 * komponenta se nezobrazí (return null).
 *
 * Design: grayscale → barva on hover, glassmorphism,
 * ScrollReveal stagger animace (bez framer-motion).
 */

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase-browser";
import ScrollReveal from "@/components/scroll-reveal";

interface Partner {
    id: string;
    company_name: string;
    domain: string;
    logo_url: string | null;
    quote_text: string | null;
    contact_name: string | null;
    contact_position: string | null;
}

function get_logo_src(partner: Partner): string {
    if (partner.logo_url) return partner.logo_url;
    return `https://logo.clearbit.com/${partner.domain}?size=160`;
}

export default function LogoWall() {
    const [partners, set_partners] = useState<Partner[]>([]);
    const [loading, set_loading] = useState(true);

    useEffect(() => {
        const supabase = createClient();

        supabase
            .from("pioneer_outreach")
            .select(
                "id, company_name, domain, logo_url, quote_text, contact_name, contact_position",
            )
            .eq("published_on_web", true)
            .order("created_at", { ascending: true })
            .then(({ data, error }) => {
                if (!error && data && data.length > 0) {
                    set_partners(data as Partner[]);
                }
                set_loading(false);
            });
    }, []);

    if (loading || partners.length === 0) return null;

    return (
        <section className="border-t border-white/[0.06] py-12 sm:py-20">
            <div className="mx-auto max-w-7xl px-4 sm:px-6">
                <ScrollReveal variant="fade-up">
                    <div className="text-center mb-10">
                        <div className="neon-divider mb-6" />
                        <h2 className="text-2xl font-extrabold sm:text-3xl">
                            Důvěřují nám{" "}
                            <span className="neon-text">lídři českého trhu</span>
                        </h2>
                        <p className="mt-3 text-slate-400">
                            Součástí Pioneer Programu pro AI Act compliance
                        </p>
                    </div>
                </ScrollReveal>

                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4 sm:gap-6">
                    {partners.map((partner, i) => (
                        <ScrollReveal key={partner.id} variant="fade-up" delay={i + 1}>
                            <div className="group glass rounded-xl p-4 sm:p-6 flex flex-col items-center text-center transition-all duration-300 hover:border-white/20 hover:shadow-[0_0_24px_rgba(217,70,239,0.08)]">
                                <div className="relative h-12 sm:h-16 mb-3 flex items-center justify-center">
                                    <img
                                        src={get_logo_src(partner)}
                                        alt={partner.company_name}
                                        className="max-h-full max-w-[120px] object-contain filter grayscale opacity-60 transition-all duration-300 group-hover:grayscale-0 group-hover:opacity-100"
                                        loading="lazy"
                                        onError={(e) => {
                                            const img = e.target as HTMLImageElement;
                                            if (!img.dataset.fallback) {
                                                img.dataset.fallback = "1";
                                                img.src = `https://www.google.com/s2/favicons?domain=${partner.domain}&sz=64`;
                                            }
                                        }}
                                    />
                                </div>
                                <p className="text-xs sm:text-sm font-semibold text-slate-300 group-hover:text-white transition-colors">
                                    {partner.company_name}
                                </p>
                                {partner.quote_text && (
                                    <p className="mt-2 text-[10px] sm:text-xs text-slate-500 italic leading-relaxed line-clamp-3 group-hover:text-slate-400 transition-colors">
                                        &ldquo;{partner.quote_text}&rdquo;
                                    </p>
                                )}
                                {partner.contact_name && (
                                    <p className="mt-1 text-[10px] text-slate-600">
                                        — {partner.contact_name}
                                        {partner.contact_position && `, ${partner.contact_position}`}
                                    </p>
                                )}
                            </div>
                        </ScrollReveal>
                    ))}
                </div>
            </div>
        </section>
    );
}
