import type { Metadata } from "next";
import ContactForm from "@/components/contact-form";

export const metadata: Metadata = {
    title: "Kariéra — Spolupracujte s námi",
    description:
        "Hledáme partnery — webdesignéry, obchodníky, freelancery. " +
        "Férové provize 20–35 %, žádné vstupní náklady. Přidejte se k partnerské síti AIshield.cz.",
    alternates: { canonical: "/kariera" },
    openGraph: {
        title: "Kariéra — Partnerský program AIshield.cz",
        description:
            "Vydělávej s námi. Provize 20–35 % za každého klienta, pasivní příjem z měsíčních služeb. " +
            "Žádné vstupní náklady, žádný závazek. AI Act musí řešit každá firma v EU.",
        url: "https://aishield.cz/kariera",
        images: [
            {
                url: "https://aishield.cz/og-kariera.png",
                width: 1200,
                height: 630,
                alt: "AIshield.cz — Partnerský program",
            },
        ],
    },
    twitter: {
        card: "summary_large_image",
        title: "Kariéra — Partnerský program AIshield.cz",
        description:
            "Vydělávej s námi. Provize 20–35 % za každého klienta. " +
            "Žádné vstupní náklady. AI Act musí řešit každá firma v EU — deadline srpen 2026.",
        images: ["https://aishield.cz/og-kariera.png"],
    },
};

export default function KarieraPage() {
    return (
        <div className="min-h-screen bg-dark-900 text-white">
            {/* Hero */}
            <section className="relative overflow-hidden pt-28 pb-16 sm:pt-36 sm:pb-20">
                <div className="absolute inset-0 bg-gradient-to-b from-fuchsia-900/20 via-transparent to-transparent pointer-events-none" />
                <div className="relative mx-auto max-w-4xl px-6 text-center">
                    <span className="inline-block rounded-full bg-gradient-to-r from-fuchsia-500 to-violet-600 px-4 py-1.5 text-xs font-bold uppercase tracking-wider mb-6">
                        Partnerský program 2026
                    </span>
                    <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-tight mb-6">
                        Vydělávej s námi.
                        <br />
                        <span className="neon-text">Férově a bez rizika.</span>
                    </h1>
                    <p className="text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed">
                        AI Act je zákon, který <strong className="text-white">musí řešit každá firma v EU</strong> —
                        a většina o tom ještě neví. <strong className="text-white">Deadline: 2.&nbsp;srpna&nbsp;2026.</strong>{" "}
                        Ty jim pomůžeš najít řešení, my se postaráme o vše ostatní.
                        Za každého klienta <strong className="text-white">dostaneš provizi</strong>.
                    </p>
                </div>
            </section>

            {/* Jak spolupráce funguje */}
            <section className="mx-auto max-w-5xl px-6 pb-16">
                <h2 className="text-2xl sm:text-3xl font-bold text-center mb-10">Jak spolupráce funguje?</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="rounded-2xl bg-white/[0.04] border border-white/[0.08] p-6">
                        <h3 className="text-lg font-semibold mb-4 text-fuchsia-400">Tvoje role</h3>
                        <ul className="space-y-2 text-slate-300 text-sm">
                            <li className="flex items-start gap-2"><span className="text-fuchsia-400 mt-0.5">✓</span>Oslovuješ firmy — osobně, e-mailem, telefonem</li>
                            <li className="flex items-start gap-2"><span className="text-fuchsia-400 mt-0.5">✓</span>Představíš AIshield a problém s AI Actem</li>
                            <li className="flex items-start gap-2"><span className="text-fuchsia-400 mt-0.5">✓</span>Domluvíš úvodní schůzku nebo pošleš kontakt</li>
                            <li className="flex items-start gap-2"><span className="text-fuchsia-400 mt-0.5">✓</span>Předáš lead — my se postaráme o zbytek</li>
                        </ul>
                    </div>
                    <div className="rounded-2xl bg-white/[0.04] border border-white/[0.08] p-6">
                        <h3 className="text-lg font-semibold mb-4 text-cyan-400">Naše role</h3>
                        <ul className="space-y-2 text-slate-300 text-sm">
                            <li className="flex items-start gap-2"><span className="text-cyan-400 mt-0.5">✓</span>Zajistíme prezentaci, demo a obchodní jednání</li>
                            <li className="flex items-start gap-2"><span className="text-cyan-400 mt-0.5">✓</span>Provedeme scan webu + vygenerujeme dokumenty</li>
                            <li className="flex items-start gap-2"><span className="text-cyan-400 mt-0.5">✓</span>Řešíme fakturaci, podporu, implementaci</li>
                            <li className="flex items-start gap-2"><span className="text-cyan-400 mt-0.5">✓</span>Vyplatíme ti provizi ihned po zaplacení klientem</li>
                        </ul>
                    </div>
                </div>
            </section>

            {/* Provize z jednorázových balíčků */}
            <section className="mx-auto max-w-5xl px-6 pb-16">
                <h2 className="text-2xl sm:text-3xl font-bold text-center mb-10">Provize z jednorázových balíčků</h2>
                <div className="space-y-4">
                    {[
                        { name: "Basic", desc: "scan + 13 dokumentů", price: "4 999 Kč", pct: "20 %", earn: "1 000 Kč", highlight: false },
                        { name: "Pro", desc: "deep scan + implementace na klíč", price: "14 999 Kč", pct: "20 %", earn: "3 000 Kč", highlight: false },
                        { name: "Enterprise", desc: "konzultace + monitoring", price: "od 39 999 Kč", pct: "25 %", earn: "10 000+ Kč", highlight: true },
                    ].map((b) => (
                        <div key={b.name} className={`rounded-2xl border p-4 sm:p-5 ${b.highlight ? "border-fuchsia-500/30 bg-fuchsia-500/[0.06]" : "border-white/[0.08] bg-white/[0.04]"}`}>
                            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1 mb-3">
                                <span className="text-base font-semibold text-white">{b.name}</span>
                                <span className="text-xs text-slate-500">— {b.desc}</span>
                            </div>
                            <div className="grid grid-cols-3 gap-2 text-center">
                                <div>
                                    <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Cena</div>
                                    <div className="text-sm font-medium text-slate-300">{b.price}</div>
                                </div>
                                <div>
                                    <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Provize</div>
                                    <div className="text-sm font-bold text-fuchsia-400">{b.pct}</div>
                                </div>
                                <div>
                                    <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Výdělek</div>
                                    <div className="text-sm font-bold text-white">{b.earn}</div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/* Měsíční provize */}
            <section className="mx-auto max-w-5xl px-6 pb-16">
                <h2 className="text-2xl sm:text-3xl font-bold text-center mb-4">Měsíční služby — pasivní příjem</h2>
                <p className="text-center text-slate-400 text-sm mb-10">
                    Klienti s měsíčním monitoringem ti generují opakovanou provizi každý měsíc po celou dobu, co platí.
                </p>
                <div className="space-y-4">
                    {[
                        { name: "Monitoring", desc: "auto re-scan webu", price: "299 Kč/měs", pct: "20 %", earn: "60 Kč/měs", year: "720 Kč/rok", highlight: false },
                        { name: "Monitoring Plus", desc: "re-scan + aktualizace dokumentů", price: "599 Kč/měs", pct: "20 %", earn: "120 Kč/měs", year: "1 440 Kč/rok", highlight: true },
                    ].map((b) => (
                        <div key={b.name} className={`rounded-2xl border p-4 sm:p-5 ${b.highlight ? "border-cyan-500/30 bg-cyan-500/[0.06]" : "border-white/[0.08] bg-white/[0.04]"}`}>
                            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1 mb-3">
                                <span className="text-base font-semibold text-white">{b.name}</span>
                                <span className="text-xs text-slate-500">— {b.desc}</span>
                            </div>
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
                                <div>
                                    <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Cena</div>
                                    <div className="text-sm font-medium text-slate-300">{b.price}</div>
                                </div>
                                <div>
                                    <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Provize</div>
                                    <div className="text-sm font-bold text-cyan-400">{b.pct}</div>
                                </div>
                                <div>
                                    <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Výdělek</div>
                                    <div className="text-sm font-bold text-white">{b.earn}</div>
                                </div>
                                <div>
                                    <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Za rok</div>
                                    <div className="text-sm font-bold text-white">{b.year}</div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
                <div className="mt-6 rounded-2xl bg-white/[0.04] border border-white/[0.08] p-5 text-center text-sm text-slate-300">
                    <strong className="text-white">Příklad:</strong> Přivedeš 20 klientů na Monitoring Plus →{" "}
                    <strong className="text-fuchsia-400">2 400 Kč/měsíc pasivně</strong>, aniž bys hnul prstem.
                    Za rok = <strong className="text-white">28 800 Kč</strong>.
                </div>
            </section>

            {/* Bonus za objem */}
            <section className="mx-auto max-w-5xl px-6 pb-16">
                <h2 className="text-2xl sm:text-3xl font-bold text-center mb-10">Bonus za objem — víc dealů = vyšší procento</h2>
                <div className="space-y-4 max-w-lg mx-auto">
                    {[
                        { deals: "1 – 3", bp: "20 %", ent: "25 %", highlight: false },
                        { deals: "4 – 7", bp: "25 %", ent: "30 %", highlight: false },
                        { deals: "8+", bp: "30 %", ent: "35 %", highlight: true },
                    ].map((r) => (
                        <div key={r.deals} className={`rounded-2xl border p-4 ${r.highlight ? "border-violet-500/30 bg-violet-500/[0.06]" : "border-white/[0.08] bg-white/[0.04]"}`}>
                            <div className="text-sm font-semibold text-white mb-2">{r.deals} dealů / měsíc</div>
                            <div className="grid grid-cols-2 gap-2 text-center">
                                <div>
                                    <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Basic &amp; Pro</div>
                                    <div className="text-sm font-bold text-fuchsia-400">{r.bp}</div>
                                </div>
                                <div>
                                    <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Enterprise</div>
                                    <div className="text-sm font-bold text-fuchsia-400">{r.ent}</div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
                <div className="mt-6 rounded-2xl bg-white/[0.04] border border-white/[0.08] p-5 text-center text-sm text-slate-300 max-w-lg mx-auto">
                    Žádné vstupní náklady · Žádný závazek · Provize do 7 dnů · Lead ti patří 90 dní
                </div>
            </section>

            {/* Tržní potenciál */}
            <section className="mx-auto max-w-5xl px-6 pb-16">
                <h2 className="text-2xl sm:text-3xl font-bold text-center mb-4">Proč je to obrovská příležitost?</h2>
                <p className="text-center text-slate-400 text-sm mb-10 max-w-2xl mx-auto">
                    AI Act je povinný zákon, ne volitelný produkt. Každá firma používající AI musí být v souladu do 2.&nbsp;srpna&nbsp;2026.
                    Pokuty: až 35 mil. € nebo 7 % obratu.
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    {[
                        { num: "2,5 mil.", label: "firem v ČR celkem" },
                        { num: "~85 %", label: "firem používá AI" },
                        { num: "< 3 %", label: "má compliance řešeno" },
                        { num: "5 měs.", label: "zbývá do deadline" },
                    ].map((s) => (
                        <div key={s.label} className="rounded-xl bg-white/[0.04] border border-white/[0.08] p-4 text-center">
                            <div className="text-2xl sm:text-3xl font-extrabold mb-1">{s.num}</div>
                            <div className="text-xs text-slate-400">{s.label}</div>
                        </div>
                    ))}
                </div>
            </section>

            {/* Scénáře výdělku */}
            <section className="mx-auto max-w-5xl px-6 pb-16">
                <h2 className="text-2xl sm:text-3xl font-bold text-center mb-10">3 realistické scénáře výdělku</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="rounded-2xl bg-white/[0.04] border border-white/[0.08] p-6 text-center">
                        <div className="text-xs uppercase tracking-wider text-slate-400 mb-2">Opatrný start</div>
                        <div className="text-3xl font-extrabold mb-1">9 700 Kč</div>
                        <div className="text-sm text-slate-400 mb-3">~4 dealy / měsíc</div>
                        <div className="text-xs text-slate-500">+ ~240 Kč recurring</div>
                        <div className="mt-4 pt-4 border-t border-white/[0.06] text-sm text-slate-300">
                            Za 6 měsíců: <strong className="text-white">~61 000 Kč</strong>
                        </div>
                    </div>
                    <div className="rounded-2xl border border-fuchsia-500/30 bg-gradient-to-b from-fuchsia-500/10 to-transparent p-6 text-center relative">
                        <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-fuchsia-500 to-violet-600 px-3 py-0.5 rounded-full text-xs font-bold">
                            Nejoblíbenější
                        </div>
                        <div className="text-xs uppercase tracking-wider text-fuchsia-300 mb-2">Aktivní partner</div>
                        <div className="text-3xl font-extrabold mb-1">28 000 Kč</div>
                        <div className="text-sm text-slate-400 mb-3">~8 dealů / měsíc</div>
                        <div className="text-xs text-slate-500">+ ~960 Kč recurring</div>
                        <div className="mt-4 pt-4 border-t border-fuchsia-500/20 text-sm text-slate-300">
                            Za 6 měsíců: <strong className="text-white">~172 600 Kč</strong>
                        </div>
                    </div>
                    <div className="rounded-2xl bg-white/[0.04] border border-white/[0.08] p-6 text-center">
                        <div className="text-xs uppercase tracking-wider text-slate-400 mb-2">Hustler mód</div>
                        <div className="text-3xl font-extrabold mb-1">67 000 Kč</div>
                        <div className="text-sm text-slate-400 mb-3">~16 dealů / měsíc</div>
                        <div className="text-xs text-slate-500">+ ~1 940 Kč recurring</div>
                        <div className="mt-4 pt-4 border-t border-white/[0.06] text-sm text-slate-300">
                            Za 6 měsíců: <strong className="text-white">~370 400 Kč</strong>
                        </div>
                    </div>
                </div>
            </section>

            {/* Co potřebuješ / nepotřebuješ */}
            <section className="mx-auto max-w-5xl px-6 pb-16">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="rounded-2xl bg-white/[0.04] border border-white/[0.08] p-6">
                        <h3 className="text-lg font-semibold mb-4 text-emerald-400">✅ Co potřebuješ</h3>
                        <ul className="space-y-2 text-slate-300 text-sm">
                            <li className="flex items-start gap-2"><span className="text-emerald-400 mt-0.5">✓</span>Chuť oslovovat firmy</li>
                            <li className="flex items-start gap-2"><span className="text-emerald-400 mt-0.5">✓</span>Základní orientaci v byznysu</li>
                            <li className="flex items-start gap-2"><span className="text-emerald-400 mt-0.5">✓</span>Telefon a notebook</li>
                        </ul>
                    </div>
                    <div className="rounded-2xl bg-white/[0.04] border border-white/[0.08] p-6">
                        <h3 className="text-lg font-semibold mb-4 text-red-400">❌ Co nepotřebuješ</h3>
                        <ul className="space-y-2 text-slate-300 text-sm">
                            <li className="flex items-start gap-2"><span className="text-red-400 mt-0.5">✗</span>Rozumět technologiím</li>
                            <li className="flex items-start gap-2"><span className="text-red-400 mt-0.5">✗</span>Řešit prezentace nebo demo</li>
                            <li className="flex items-start gap-2"><span className="text-red-400 mt-0.5">✗</span>Vstupní náklady ani poplatky</li>
                        </ul>
                    </div>
                </div>
            </section>

            {/* Kontaktní formulář */}
            <section className="mx-auto max-w-2xl px-6 pb-24">
                <h2 className="text-2xl sm:text-3xl font-bold text-center mb-4">Máte zájem spolupracovat?</h2>
                <p className="text-center text-slate-400 text-sm mb-10">
                    Vyplňte formulář a ozveme se vám — zaškolíme vás, dáme materiály a můžete začít hned.
                    Žádné papírování, žádné vstupní náklady.
                </p>
                <ContactForm />
            </section>
        </div>
    );
}
