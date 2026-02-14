import { Metadata } from "next";

export const metadata: Metadata = {
    title: "Opakované platby — AIshield.cz",
    description:
        "Informace o opakovaných platbách (monitoring subscriptions) na AIshield.cz. Podmínky, ceny a zrušení.",
};

export default function OpakovvanePlatbyPage() {
    return (
        <section className="py-20 relative">
            <div className="absolute inset-0 -z-10">
                <div className="absolute top-[10%] right-[20%] h-[400px] w-[400px] rounded-full bg-cyan-500/8 blur-[120px]" />
            </div>

            <div className="mx-auto max-w-3xl px-6">
                <h1 className="text-3xl font-bold text-white">
                    Opakované platby — Monitoring
                </h1>
                <p className="mt-2 text-sm text-slate-500">
                    Poslední aktualizace: 14. února 2026
                </p>

                <div className="mt-8 space-y-6">
                    {/* ═══ 1. CO JSOU OPAKOVANÉ PLATBY ═══ */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            1. Co jsou opakované platby
                        </h2>
                        <div className="text-slate-400 leading-relaxed space-y-3">
                            <p>
                                Služba AIshield.cz nabízí volitelné měsíční monitoring předplatné,
                                které automaticky kontroluje váš web na přítomnost AI systémů
                                a&nbsp;aktualizuje vaši compliance dokumentaci.
                            </p>
                            <p>
                                Při aktivaci monitoringu souhlasíte s&nbsp;pravidelným automatickým
                                strhováním platby z&nbsp;vaší platební karty jednou měsíčně.
                                Platba se provádí přes zabezpečenou platební bránu{" "}
                                <a href="https://www.gopay.cz" target="_blank" rel="noopener noreferrer" className="text-neon-fuchsia hover:underline">GoPay</a>.
                            </p>
                        </div>
                    </div>

                    {/* ═══ 2. DOSTUPNÉ PLÁNY ═══ */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            2. Dostupné plány opakovaných plateb
                        </h2>
                        <div className="text-slate-400 leading-relaxed space-y-3">
                            <div className="overflow-hidden rounded-xl border border-white/[0.06]">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="border-b border-white/[0.06] bg-white/[0.02]">
                                            <th className="text-left px-4 py-3 text-white font-semibold">Plán</th>
                                            <th className="text-right px-4 py-3 text-white font-semibold">Cena/měsíc</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr className="border-b border-white/[0.04]">
                                            <td className="px-4 py-3">
                                                <strong className="text-white">Monitoring</strong>
                                                <p className="text-xs text-slate-500 mt-0.5">1× měsíčně automatický sken webu + compliance report</p>
                                            </td>
                                            <td className="px-4 py-3 text-right font-semibold text-white">299 Kč</td>
                                        </tr>
                                        <tr>
                                            <td className="px-4 py-3">
                                                <strong className="text-white">Monitoring Plus</strong>
                                                <p className="text-xs text-slate-500 mt-0.5">2× měsíčně sken + implementace změn + prioritní podpora</p>
                                            </td>
                                            <td className="px-4 py-3 text-right font-semibold text-white">599 Kč</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                            <p>
                                Uvedené ceny jsou konečné. Poskytovatel není plátcem DPH.
                            </p>
                        </div>
                    </div>

                    {/* ═══ 3. PODMÍNKY AKTIVACE ═══ */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            3. Podmínky aktivace
                        </h2>
                        <div className="text-slate-400 leading-relaxed space-y-3">
                            <p>Monitoring lze aktivovat pouze po splnění těchto podmínek:</p>
                            <ul className="list-disc list-inside space-y-1.5 ml-2">
                                <li>Zakoupený balíček BASIC, PRO nebo ENTERPRISE</li>
                                <li>Provedený sken webu (alespoň jeden dokončený sken)</li>
                                <li>Platné platební údaje (platební karta)</li>
                            </ul>
                            <p>
                                Aktivace se provádí v&nbsp;klientském dashboardu v&nbsp;sekci
                                &bdquo;Monitoring&ldquo;.
                            </p>
                        </div>
                    </div>

                    {/* ═══ 4. FREKVENCE A ZPŮSOB PLATBY ═══ */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            4. Frekvence a způsob platby
                        </h2>
                        <div className="text-slate-400 leading-relaxed space-y-3">
                            <ul className="list-disc list-inside space-y-1.5 ml-2">
                                <li><strong className="text-white">Frekvence strhávání:</strong> 1× měsíčně, vždy ve stejný den jako první platba</li>
                                <li><strong className="text-white">Platební metoda:</strong> Platební karta (Visa, Mastercard, Apple Pay, Google Pay)</li>
                                <li><strong className="text-white">Zpracovatel plateb:</strong> GoPay s.r.o. — certifikovaná platební brána s PCI DSS</li>
                                <li><strong className="text-white">Měna:</strong> CZK (české koruny)</li>
                            </ul>
                            <p>
                                První platba se provede okamžitě při aktivaci monitoringu.
                                Každá další platba se strhne automaticky po 30 dnech.
                            </p>
                        </div>
                    </div>

                    {/* ═══ 5. MINIMÁLNÍ DOBA A VÝPOVĚĎ ═══ */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            5. Minimální doba a výpověď
                        </h2>
                        <div className="text-slate-400 leading-relaxed space-y-3">
                            <ul className="list-disc list-inside space-y-1.5 ml-2">
                                <li><strong className="text-white">Minimální doba trvání:</strong> 3 měsíce od aktivace</li>
                                <li><strong className="text-white">Výpovědní lhůta:</strong> 1 měsíc</li>
                                <li><strong className="text-white">Zrušení:</strong> Kdykoli po uplynutí minimální doby prostřednictvím dashboardu, emailem na info@aishield.cz nebo telefonicky na 732 716 141</li>
                            </ul>
                            <p>
                                Po zrušení se monitoring deaktivuje k&nbsp;poslednímu dni
                                aktuálního zaplaceného období. Žádné další platby se nebudou strhávat.
                            </p>
                            <p>
                                U&nbsp;balíčku ENTERPRISE je 2 roky monitoringu již v&nbsp;ceně
                                balíčku a&nbsp;nepodléhá opakovaným platbám.
                            </p>
                        </div>
                    </div>

                    {/* ═══ 6. CO MONITORING ZAHRNUJE ═══ */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            6. Co monitoring zahrnuje
                        </h2>
                        <div className="text-slate-400 leading-relaxed space-y-3">
                            <p><strong className="text-white">Monitoring (299 Kč/měsíc):</strong></p>
                            <ul className="list-disc list-inside space-y-1 ml-2 mb-3">
                                <li>1× měsíčně automatický sken webu</li>
                                <li>Srovnání s&nbsp;předchozím skenem (diff)</li>
                                <li>Emailové upozornění při nálezu změny</li>
                                <li>Aktualizovaný Compliance Report</li>
                                <li>Aktualizovaný Registr AI systémů</li>
                                <li>Historie skenů v&nbsp;dashboardu</li>
                            </ul>
                            <p><strong className="text-white">Monitoring Plus (599 Kč/měsíc):</strong></p>
                            <ul className="list-disc list-inside space-y-1 ml-2">
                                <li>Vše z&nbsp;Monitoring</li>
                                <li>2× měsíčně automatický sken webu</li>
                                <li>Aktualizace všech 7 compliance dokumentů</li>
                                <li>Implementace změn na webu klienta</li>
                                <li>Prioritní emailová podpora</li>
                                <li>Čtvrtletní souhrnný přehled</li>
                            </ul>
                        </div>
                    </div>

                    {/* ═══ 7. REKLAMACE A VRÁCENÍ PLATBY ═══ */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            7. Reklamace a vrácení platby
                        </h2>
                        <div className="text-slate-400 leading-relaxed space-y-3">
                            <p>
                                V případě neoprávněného stržení platby nebo technické chyby
                                kontaktujte zákaznickou podporu na{" "}
                                <a href="mailto:info@aishield.cz" className="text-neon-fuchsia hover:underline">info@aishield.cz</a>{" "}
                                nebo na telefonním čísle{" "}
                                <a href="tel:+420732716141" className="text-neon-fuchsia hover:underline">732 716 141</a>.
                            </p>
                            <p>
                                Reklamaci vyřídíme do 14 pracovních dnů. V&nbsp;případě oprávněné
                                reklamace vrátíme platbu na původní platební metodu.
                            </p>
                        </div>
                    </div>

                    {/* ═══ 8. KONTAKT ═══ */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            8. Kontakt
                        </h2>
                        <div className="text-slate-400 leading-relaxed space-y-2">
                            <p><strong className="text-white">Poskytovatel:</strong> Martin Haynes, IČO: 17889251</p>
                            <p><strong className="text-white">Sídlo:</strong> Mlýnská 53, 783 53 Velká Bystřice</p>
                            <p>
                                <strong className="text-white">E-mail:</strong>{" "}
                                <a href="mailto:info@aishield.cz" className="text-neon-fuchsia hover:underline">info@aishield.cz</a>
                            </p>
                            <p>
                                <strong className="text-white">Telefon:</strong>{" "}
                                <a href="tel:+420732716141" className="text-neon-fuchsia hover:underline">+420 732 716 141</a>
                            </p>
                            <p>
                                <strong className="text-white">Platební brána:</strong>{" "}
                                <a href="https://www.gopay.cz" target="_blank" rel="noopener noreferrer" className="text-neon-fuchsia hover:underline">GoPay s.r.o.</a>
                            </p>
                        </div>
                    </div>
                </div>

                {/* Back link */}
                <div className="mt-10 text-center space-x-6">
                    <a
                        href="/pricing"
                        className="text-sm text-slate-500 hover:text-neon-fuchsia transition-colors"
                    >
                        ← Zpět na ceník
                    </a>
                    <a
                        href="/terms"
                        className="text-sm text-slate-500 hover:text-neon-fuchsia transition-colors"
                    >
                        Obchodní podmínky →
                    </a>
                </div>
            </div>
        </section>
    );
}
