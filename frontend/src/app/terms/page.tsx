import { Metadata } from "next";

export const metadata: Metadata = {
    title: "Obchodní podmínky — AIshield.cz",
    description:
        "Všeobecné obchodní podmínky služby AIshield.cz — automatizovaný nástroj pro přípravu AI Act compliance dokumentace.",
};

export default function TermsPage() {
    return (
        <section className="py-20 relative">
            <div className="absolute inset-0 -z-10">
                <div className="absolute top-[10%] right-[20%] h-[400px] w-[400px] rounded-full bg-cyan-500/8 blur-[120px]" />
            </div>

            <div className="mx-auto max-w-3xl px-6">
                <h1 className="text-3xl font-bold text-white">
                    Všeobecné obchodní podmínky
                </h1>
                <p className="mt-2 text-sm text-slate-500">
                    Poslední aktualizace: 14. února 2026 &bull; Verze 3.1
                </p>

                <div className="mt-8 space-y-6">
                    {/* ═══ 1. ÚVODNÍ USTANOVENÍ ═══ */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            1. Úvodní ustanovení
                        </h2>
                        <div className="text-slate-400 leading-relaxed space-y-3">
                            <p>
                                1.1. Tyto všeobecné obchodní podmínky (dále jen
                                &bdquo;VOP&ldquo;) upravují vzájemná práva a povinnosti mezi
                                poskytovatelem služby a uživatelem.
                            </p>
                            <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-4">
                                <p>
                                    <strong className="text-white">Poskytovatel:</strong> Martin
                                    Haynes
                                </p>
                                <p>IČO: 17889251</p>
                                <p>Sídlo: Mlýnská 53, 783 53 Velká Bystřice</p>
                                <p>
                                    E-mail:{" "}
                                    <a
                                        href="mailto:info@aishield.cz"
                                        className="text-neon-fuchsia hover:underline"
                                    >
                                        info@aishield.cz
                                    </a>
                                </p>
                                <p>
                                    Tel:{" "}
                                    <a
                                        href="tel:+420732716141"
                                        className="text-neon-cyan hover:underline"
                                    >
                                        +420 732 716 141
                                    </a>
                                </p>
                                <p>Poskytovatel není plátcem DPH.</p>
                            </div>
                            <p>
                                1.2. &bdquo;Uživatelem&ldquo; se rozumí jakákoliv fyzická nebo
                                právnická osoba, která využívá službu AIshield.cz (dále jen
                                &bdquo;Služba&ldquo;).
                            </p>
                            <p>
                                1.3. Registrací, zaplacením nebo využitím Služby Uživatel
                                potvrzuje, že se s těmito VOP seznámil a souhlasí s nimi.
                            </p>
                        </div>
                    </div>

                    {/* ═══ 2. VYMEZENÍ SLUŽBY ═══ */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            2. Vymezení služby
                        </h2>
                        <div className="text-slate-400 leading-relaxed space-y-3">
                            <p>
                                2.1. AIshield.cz je{" "}
                                <strong className="text-white">
                                    automatizovaný technický nástroj
                                </strong>
                                , který na základě uživatelem poskytnutých údajů a veřejně
                                dostupného obsahu webových stránek vytváří orientační výstupy
                                a návrhy dokumentů pro účely interní compliance s Nařízením
                                Evropského parlamentu a Rady (EU) 2024/1689 o umělé inteligenci
                                (dále jen &bdquo;AI Act&ldquo;).
                            </p>
                            <p>2.2. Služba zahrnuje zejména:</p>
                            <ul className="list-disc list-inside space-y-1 ml-2">
                                <li>
                                    Automatizované skenování webových stránek za účelem detekce
                                    AI systémů
                                </li>
                                <li>
                                    Generování dokumentačních šablon a podkladů pro interní
                                    compliance (tzv. AI Act Compliance Kit)
                                </li>
                                <li>
                                    Poskytnutí interaktivního dotazníku pro upřesnění compliance
                                    profilu
                                </li>
                                <li>
                                    U vyšších balíčků: technickou asistenci s implementací
                                    (HTML šablona transparenční stránky, chatbot oznámení)
                                </li>
                            </ul>
                            <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4 mt-3">
                                <p className="text-slate-300">
                                    <strong className="text-white">
                                        2.3. Služba neposkytuje právní služby
                                    </strong>{" "}
                                    ani právní poradenství ve smyslu zákona č. 85/1996 Sb., o
                                    advokacii. Poskytovatel není advokátem ani advokátní kanceláří.
                                </p>
                                <p className="mt-2">
                                    Veškeré výstupy Služby jsou poskytovány výhradně jako{" "}
                                    <strong className="text-white">
                                        automatizovaný technicko-informační podklad
                                    </strong>{" "}
                                    založený na uživatelských vstupech a algoritmickém zpracování.
                                    Výstupy nejsou individuálním právním posouzením konkrétní
                                    situace Uživatele a nemohou nahrazovat právní analýzu
                                    provedenou advokátem.
                                </p>
                            </div>
                            <p>
                                2.4. Výstupy Služby jsou zcela nebo zčásti generovány
                                prostřednictvím{" "}
                                <strong className="text-white">
                                    systémů umělé inteligence
                                </strong>{" "}
                                (dále jen &bdquo;AI&ldquo;). Uživatel bere na vědomí, že
                                AI-generované výstupy mohou obsahovat nepřesnosti, neúplnosti
                                nebo chyby. Každý vygenerovaný dokument je označen informací
                                o tom, že byl vytvořen s využitím AI.
                            </p>
                            <p>
                                2.5. Služba neposkytuje žádnou záruku ani ujištění, že použitím
                                výstupů bude Uživatel v plném souladu s AI Act nebo jinými
                                právními předpisy. Výstupy slouží jako{" "}
                                <strong className="text-white">
                                    podklad pro dosažení souladu
                                </strong>
                                , nikoliv jako garance jeho dosažení.
                            </p>
                        </div>
                    </div>

                    {/* ═══ 3. BEZPLATNÉ SKENOVÁNÍ ═══ */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            3. Bezplatné skenování webu
                        </h2>
                        <div className="text-slate-400 leading-relaxed space-y-3">
                            <p>
                                3.1. Bezplatné skenování webových stránek je dostupné bez
                                registrace a bez platby. Nevzniká jím smluvní vztah.
                            </p>
                            <p>
                                3.2. Výsledky bezplatného skenování jsou{" "}
                                <strong className="text-white">orientační</strong>. Skenování
                                probíhá automatizovaně a nemusí zachytit všechny AI systémy
                                na webu (např. systémy za přihlášením, v mobilních aplikacích
                                nebo systémy bez veřejně viditelných znaků).
                            </p>
                            <p>
                                3.3. Poskytovatel nenese odpovědnost za úplnost ani přesnost
                                výsledků bezplatného skenování.
                            </p>
                        </div>
                    </div>

                    {/* ═══ 4. UZAVŘENÍ SMLOUVY ═══ */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            4. Uzavření smlouvy a cenové podmínky
                        </h2>
                        <div className="text-slate-400 leading-relaxed space-y-3">
                            <p>
                                4.1. Smlouva o poskytování placených služeb vzniká okamžikem
                                úspěšné úhrady zvoleného cenového balíčku.
                            </p>
                            <p>
                                4.2. Aktuální ceny jsou uvedeny na stránce{" "}
                                <a
                                    href="/pricing"
                                    className="text-neon-fuchsia hover:underline"
                                >
                                    Ceník
                                </a>
                                . Všechny ceny jsou konečné. Poskytovatel není plátcem DPH.
                            </p>
                            <p>
                                4.3. Uživatel může uhradit objednávku jedním z&nbsp;následujících
                                způsobů:
                            </p>
                            <ul className="list-disc list-inside space-y-1.5 ml-2">
                                <li>
                                    <strong className="text-white">Online platba</strong>{" "}
                                    — platební kartou (Visa, Mastercard), Apple Pay nebo Google Pay
                                    prostřednictvím zabezpečené platební brány{" "}
                                    <a
                                        href="https://stripe.com"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-neon-fuchsia hover:underline"
                                    >
                                        Stripe
                                    </a>
                                    . Uživatel si zvolí preferovanou platební bránu při objednávce.
                                </li>
                                <li>
                                    <strong className="text-white">Bankovní převod</strong>{" "}
                                    — po registraci Poskytovatel zašle Uživateli e-mail
                                    s&nbsp;platebními údaji. Po připsání platby na účet
                                    Poskytovatele a jejím ručním potvrzení v&nbsp;administraci
                                    se Uživateli zpřístupní dotazník a další kroky služby.
                                </li>
                            </ul>
                            <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-4">
                                <p className="text-sm">
                                    <strong className="text-white">Platební údaje pro bankovní převod:</strong>
                                </p>
                                <p className="text-sm">Číslo účtu: 2503446206/2010 (Fio banka)</p>
                                <p className="text-sm">Zodpovědná osoba: Martin Haynes</p>
                                <p className="text-sm mt-1">
                                    Do poznámky pro příjemce uveďte:{" "}
                                    <strong className="text-white">jméno kontaktní osoby + název projektu</strong>
                                </p>
                            </div>
                            <p>
                                4.4. Po úspěšné platbě (online i převodem) Uživatel obdrží
                                na e-mail potvrzení objednávky a daňový doklad.
                            </p>
                            <p>
                                4.5. Poskytovatel si vyhrazuje právo ceny změnit. Změna cen
                                se nevztahuje na již uhrazené objednávky.
                            </p>
                        </div>
                    </div>

                    {/* ═══ 5. DODÁNÍ SLUŽBY ═══ */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            5. Dodání služby
                        </h2>
                        <div className="text-slate-400 leading-relaxed space-y-3">
                            <p>
                                5.1. Po zaplacení a vyplnění dotazníku Poskytovatel zpracuje
                                a zpřístupní compliance dokumentaci v uživatelském dashboardu,
                                zpravidla do 7 pracovních dnů.
                            </p>
                            <p>
                                5.2. Dokumentace je generována na základě informací
                                poskytnutých Uživatelem v dotazníku a výsledků automatizovaného
                                skenování. Její kvalita a přesnost závisí na správnosti
                                a úplnosti vstupních dat.
                            </p>
                            <p>
                                5.3. U balíčku PRO zahrnuje dodání i technickou asistenci
                                s implementací (nasazení HTML šablony transparenční stránky,
                                úprava chatbot oznámení). Uživatel je povinen poskytnout potřebnou součinnost
                                (přístupové údaje, kontakt na správce webu apod.).
                            </p>
                            <p>
                                5.4. Dokumentace je Uživateli dodána okamžikem jejího
                                zpřístupnění v dashboardu. Uživatel má 7 dní na nahlášení
                                vad dodané dokumentace (nekompletnost, zjevně chybný obsah,
                                nesoulad s objednaným balíčkem).
                            </p>
                        </div>
                    </div>

                    {/* ═══ 6. POVINNOSTI UŽIVATELE ═══ */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            6. Povinnosti uživatele
                        </h2>
                        <div className="text-slate-400 leading-relaxed space-y-3">
                            <p>
                                6.1. Uživatel odpovídá za správnost, úplnost a aktuálnost
                                údajů poskytnutých v dotazníku a při registraci.
                            </p>
                            <p>
                                6.2. Uživatel je povinen výstupy Služby před použitím
                                přiměřeně zkontrolovat a přizpůsobit svému konkrétnímu provozu.
                                V případě pochybností o správnosti výstupů Uživatel zajistí
                                odborné posouzení na vlastní náklady.
                            </p>
                            <p>
                                6.3. Uživatel nesmí vygenerovanou dokumentaci dále prodávat
                                ani zpřístupňovat třetím stranám za účelem komerčního využití.
                                Dokumentace je určena výhradně pro interní potřeby Uživatele
                                a jeho firmy.
                            </p>
                            <p>
                                6.4. Uživatel nesmí prezentovat vygenerované dokumenty jako
                                &bdquo;právně ověřené&ldquo; nebo &bdquo;certifikované&ldquo;,
                                pokud nebyly samostatně posouzeny advokátem.
                            </p>
                        </div>
                    </div>

                    {/* ═══ 7. ODPOVĚDNOST ═══ */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            7. Odpovědnost a omezení
                        </h2>
                        <div className="text-slate-400 leading-relaxed space-y-3">
                            <p>
                                7.1. Poskytovatel prohlašuje, že při tvorbě výstupů postupuje
                                s odbornou péčí a na základě aktuálního znění AI Act
                                a souvisejících předpisů EU.
                            </p>
                            <p>
                                7.2. Uživatel bere na vědomí, že výstupy Služby jsou
                                generovány automatizovaně pomocí systémů umělé inteligence
                                a{" "}
                                <strong className="text-white">
                                    mohou obsahovat nepřesnosti, neúplnosti nebo chyby
                                </strong>
                                . Uživatel je plně odpovědný za implementaci, použití
                                a případné právní posouzení výstupů.
                            </p>
                            <p>
                                7.3. Poskytovatel neodpovídá za jakékoliv přímé ani nepřímé
                                škody, sankce, pokuty, ušlý zisk ani jinou újmu vzniklou
                                v důsledku použití výstupů Služby, zejména za pokuty uložené
                                dozorovými orgány.
                            </p>
                            <p>
                                7.4. Celková odpovědnost Poskytovatele za újmu vzniklou
                                v souvislosti se Službou je omezena na částku skutečně
                                uhrazenou Uživatelem za příslušné plnění; to neplatí v rozsahu,
                                v němž nelze odpovědnost platně omezit dle kogentních ustanovení
                                právních předpisů.
                            </p>
                            <p>
                                7.5. Poskytovatel neodpovídá za nesprávnosti výstupů způsobené
                                nepřesnými, neúplnými nebo nepravdivými údaji poskytnutými
                                Uživatelem.
                            </p>
                            <p>
                                7.6. Poskytovatel neodpovídá za dočasnou nedostupnost Služby
                                způsobenou technickými problémy, údržbou nebo okolnostmi
                                mimo jeho kontrolu (vyšší moc).
                            </p>
                        </div>
                    </div>

                    {/* ═══ 8. ODSTOUPENÍ OD SMLOUVY ═══ */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            8. Odstoupení od smlouvy (spotřebitelé)
                        </h2>
                        <div className="text-slate-400 leading-relaxed space-y-3">
                            <p>
                                8.1. Uživatel, který je spotřebitelem, má právo odstoupit
                                od smlouvy bez udání důvodu do{" "}
                                <strong className="text-white">14 dnů</strong> od uzavření
                                smlouvy dle § 1829 občanského zákoníku.
                            </p>
                            <div className="rounded-xl border border-orange-500/20 bg-orange-500/5 p-4">
                                <p className="text-slate-300">
                                    <strong className="text-white">
                                        8.2. Digitální obsah:
                                    </strong>{" "}
                                    Placená služba zahrnuje dodání digitálního obsahu (PDF a HTML
                                    dokumentů). Před zahájením zpracování objednávky je Uživatel
                                    vyzván k udělení výslovného souhlasu se zahájením plnění
                                    před uplynutím 14denní lhůty pro odstoupení. Udělením tohoto
                                    souhlasu Uživatel bere na vědomí, že ztrácí právo na
                                    odstoupení od smlouvy dle § 1837 písm. l) občanského zákoníku.
                                </p>
                            </div>
                            <p>
                                8.3. Pokud Uživatel výslovný souhlas dle bodu 8.2 neudělí,
                                může odstoupit od smlouvy do 14 dnů. V takovém případě bude
                                zpracování objednávky zahájeno až po uplynutí této lhůty.
                            </p>
                            <p>
                                8.4. Pro odstoupení od smlouvy kontaktujte{" "}
                                <a
                                    href="mailto:info@aishield.cz"
                                    className="text-neon-fuchsia hover:underline"
                                >
                                    info@aishield.cz
                                </a>{" "}
                                s uvedením čísla objednávky.
                            </p>
                            <p>
                                8.5. Vrácení peněz proběhne do 14 dnů od přijetí odstoupení,
                                stejným způsobem, jakým byla platba přijata.
                            </p>
                        </div>
                    </div>

                    {/* ═══ 9. REKLAMACE ═══ */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            9. Reklamace
                        </h2>
                        <div className="text-slate-400 leading-relaxed space-y-3">
                            <p>
                                9.1. Uživatel má právo uplatnit reklamaci v případě, že
                                dodaná dokumentace je nekompletní, obsahuje zjevné chyby
                                nebo neodpovídá objednanému balíčku.
                            </p>
                            <p>
                                9.2. Reklamaci lze uplatnit e-mailem na{" "}
                                <a
                                    href="mailto:info@aishield.cz"
                                    className="text-neon-fuchsia hover:underline"
                                >
                                    info@aishield.cz
                                </a>{" "}
                                do 30 dnů od dodání dokumentace.
                            </p>
                            <p>
                                9.3. Poskytovatel reklamaci vyřídí do 30 dnů, a to opravou
                                dokumentace, novým vygenerováním nebo vrácením ceny dle
                                povahy vady.
                            </p>
                            <p>
                                9.4. Za vadu se nepovažuje nepřesnost výstupu způsobená
                                nesprávnými vstupními údaji ze strany Uživatele ani změna
                                právních předpisů po datu dodání.
                            </p>
                        </div>
                    </div>

                    {/* ═══ 10. AI A TRANSPARENCE ═══ */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            10. Využití umělé inteligence a transparence
                        </h2>
                        <div className="text-slate-400 leading-relaxed space-y-3">
                            <p>
                                10.1. Služba využívá systémy umělé inteligence (OpenAI,
                                Anthropic) k analýze webových stránek a generování compliance
                                dokumentace. Uživatel s tímto využitím AI souhlasí.
                            </p>
                            <p>
                                10.2. Všechny vygenerované dokumenty jsou označeny informací,
                                že byly vytvořeny s využitím AI, v souladu s čl. 50 AI Act.
                            </p>
                            <p>
                                10.3. Do systémů AI nejsou předávány osobní údaje Uživatelů
                                (e-maily, hesla, jména). Předáván je pouze veřejně dostupný
                                obsah skenovaných webových stránek a anonymizované odpovědi
                                z dotazníku.
                            </p>
                            <p>
                                10.4. Poskytovatel průběžně kontroluje kvalitu AI výstupů
                                a aktualizuje systém v souladu s vývojem AI Act a souvisejících
                                předpisů.
                            </p>
                        </div>
                    </div>

                    {/* ═══ 11. DUŠEVNÍ VLASTNICTVÍ ═══ */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            11. Duševní vlastnictví a licence
                        </h2>
                        <div className="text-slate-400 leading-relaxed space-y-3">
                            <p>
                                11.1. Vygenerovaná dokumentace je určena výhradně pro interní
                                použití Uživatele a jeho firmy. Uživatel získává nevýhradní,
                                nepřenosnou licenci k užití dodaných dokumentů pro vlastní
                                provoz.
                            </p>
                            <p>
                                11.2. Uživatel nesmí vygenerovanou dokumentaci dále prodávat,
                                šířit ani zpřístupňovat třetím stranám pro komerční účely.
                            </p>
                            <p>
                                11.3. Webová aplikace AIshield.cz, její design, kód, grafika
                                a obsah jsou chráněny autorskými právy Poskytovatele.
                            </p>
                        </div>
                    </div>

                    {/* ═══ 12. OCHRANA OSOBNÍCH ÚDAJŮ ═══ */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            12. Ochrana osobních údajů
                        </h2>
                        <div className="text-slate-400 leading-relaxed space-y-3">
                            <p>
                                12.1. Zpracování osobních údajů se řídí{" "}
                                <a
                                    href="/privacy"
                                    className="text-neon-fuchsia hover:underline"
                                >
                                    Zásadami ochrany soukromí
                                </a>{" "}
                                a{" "}
                                <a href="/gdpr" className="text-neon-fuchsia hover:underline">
                                    informacemi o GDPR
                                </a>
                                , které jsou nedílnou součástí těchto VOP.
                            </p>
                            <p>
                                12.2. Poskytovatel zpracovává osobní údaje v souladu
                                s Nařízením (EU) 2016/679 (GDPR) a souvisejícími českými
                                právními předpisy.
                            </p>
                        </div>
                    </div>

                    {/* ═══ 13. CENOVÉ BALÍČKY ═══ */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            13. Rozsah služeb dle cenových balíčků
                        </h2>
                        <div className="text-slate-400 leading-relaxed space-y-3">
                            <p>
                                13.1.{" "}
                                <strong className="text-white">BASIC (4 999 Kč)</strong> — automatizované
                                skenování webu a vygenerování AI Act Compliance Kitu obsahujícího
                                až 12 dokumentů podle rizikového profilu klienta:
                                Compliance Report, Akční plán, Registr AI systémů,
                                Transparenční stránka (HTML šablona), texty oznámení pro AI nástroje
                                (chatbot a další), Interní AI politika firmy, Školení —
                                prezentace v PowerPointu, Záznamový list o proškolení,
                                Plán řízení AI incidentů, DPIA šablona (posouzení vlivu
                                na ochranu osobních údajů), Dodavatelský checklist (kontrolní
                                seznam pro smlouvy s dodavateli AI), Monitoring plán AI
                                (plán monitoringu výstupů včetně testování férovosti)
                                a Transparentnost a lidský dohled (záznamy dle čl. 13, 14 a 50 AI Actu).
                                Rozsah se automaticky přizpůsobí na základě výsledků analýzy rizik.
                                Bez implementační podpory.
                            </p>
                            <p>
                                13.2.{" "}
                                <strong className="text-white">PRO (14 999 Kč)</strong> — vše z BASIC
                                a navíc: implementace na klíč — instalace compliance widgetu
                                na web Uživatele, nasazení transparenční stránky, úprava chatbot
                                oznámení a cookie lišty. Podpora platforem WordPress, Shoptet
                                i custom řešení. Prioritní zpracování. Technická podpora po dobu
                                30 dní od dodání.
                            </p>
                            <p>
                                13.3.{" "}
                                <strong className="text-white">ENTERPRISE (39 999 Kč)</strong> —
                                vše z PRO a navíc: 10 hodin on-line konzultací s compliance specialistou
                                (neprávní povahy), metodická kontrola veškeré dokumentace,
                                multi-domain podpora
                                (více webů / e-shopů), 2 roky měsíčního monitoringu v ceně
                                balíčku (po uplynutí možnost prodloužení za příplatek),
                                dedikovaný specialista a SLA 4h odezva v pracovní době.
                            </p>
                            <p>
                                13.4. Volitelný doplněk: měsíční monitoring za příplatek
                                (aktuální cena uvedena na stránce Ceník). Podrobné
                                podmínky monitoringu viz bod 14 a stránka{" "}
                                <a
                                    href="/opakovane-platby"
                                    className="text-neon-fuchsia hover:underline"
                                >
                                    Opakované platby
                                </a>
                                .
                            </p>
                        </div>
                    </div>

                    {/* ═══ 14. MĚSÍČNÍ MONITORING ═══ */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            14. Měsíční monitoring webu
                        </h2>
                        <div className="text-slate-400 leading-relaxed space-y-3">
                            <p>
                                14.1. Měsíční monitoring je{" "}
                                <strong className="text-white">
                                    volitelná doplňková služba
                                </strong>{" "}
                                dostupná ke všem jednorázovým balíčkům. Monitoring
                                vyžaduje předchozí zakoupení jednorázového balíčku
                                (BASIC, PRO nebo ENTERPRISE).
                            </p>
                            <p>
                                14.2. Monitoring zahrnuje pravidelné automatizované
                                skenování webových stránek Uživatele za účelem
                                detekce nových nebo změněných AI systémů.
                                Při nálezu změny Poskytovatel zašle Uživateli
                                emailové upozornění s popisem nálezu
                                a aktualizovaný Compliance Report.
                            </p>
                            <p>
                                14.3. Rozsah monitoringu závisí na zvoleném tarifu
                                (Monitoring / Monitoring Plus). Aktuální rozsah
                                a ceny jsou uvedeny na stránce{" "}
                                <a
                                    href="/pricing"
                                    className="text-neon-fuchsia hover:underline"
                                >
                                    Ceník
                                </a>
                                {" "}a podrobné podmínky opakovaných plateb na stránce{" "}
                                <a
                                    href="/opakovane-platby"
                                    className="text-neon-fuchsia hover:underline"
                                >
                                    Opakované platby
                                </a>
                                .
                            </p>
                            <p>
                                14.4. Smlouva o monitoringu se uzavírá na dobu
                                neurčitou s minimální dobou trvání{" "}
                                <strong className="text-white">3 měsíce</strong>.
                                Po uplynutí minimální doby může kterákoliv strana
                                smlouvu vypovědět s výpovědní lhůtou 1 měsíc
                                ke konci fakturačního období.
                            </p>
                            <p>
                                14.5. Monitoring je hrazen měsíčně předem formou
                                automatické opakované platby přes platební bránu
                                Stripe, nebo ročně předem s uvedenou slevou. Při
                                roční platbě se minimální doba trvání prodlužuje
                                na 12 měsíců.
                            </p>
                            <p>
                                14.6. Monitoring se vztahuje na veřejně dostupnou
                                část webových stránek Uživatele. Poskytovatel
                                neodpovídá za AI systémy skryté za přihlášením,
                                v mobilních aplikacích nebo interních nástrojích,
                                které nejsou veřejně přístupné.
                            </p>
                            <p>
                                14.7. AI systémy se na webových stránkách mohou
                                objevit bez vědomí provozovatele, například v důsledku:
                            </p>
                            <ul className="list-disc list-inside space-y-1 ml-2">
                                <li>Automatické aktualizace pluginů a modulů (WordPress, WooCommerce aj.)</li>
                                <li>Aktivace AI funkcí poskytovatelem chatbotu (Smartsupp, Tidio, LiveChat)</li>
                                <li>Aktualizace e-shopové platformy (Shoptet, Shopify, PrestaShop)</li>
                                <li>Aktivace AI bezpečnostních nástrojů poskytovatelem hostingu (CDN, WAF)</li>
                                <li>Upgradu reklamních systémů na AI varianty (Google Performance Max, Meta Advantage+)</li>
                                <li>Přidání AI predikcí analytickými nástroji (GA4, Hotjar)</li>
                                <li>Aktivace AI fraud detection platební bránou</li>
                                <li>Zásahu třetí strany (agentura, subdodavatel)</li>
                            </ul>
                            <p>
                                14.8. Poskytovatel důrazně doporučuje pravidelný
                                monitoring, protože odpovědnost za soulad s AI Act
                                nese provozovatel webu bez ohledu na to, zda
                                o přítomnosti AI systému věděl.
                            </p>
                        </div>
                    </div>

                    {/* ═══ 15. ZÁVĚREČNÁ USTANOVENÍ ═══ */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            15. Závěrečná ustanovení
                        </h2>
                        <div className="text-slate-400 leading-relaxed space-y-3">
                            <p>
                                15.1. Tyto VOP se řídí právním řádem České republiky, zejména
                                zákonem č. 89/2012 Sb. (občanský zákoník) a zákonem
                                č. 634/1992 Sb. (zákon o ochraně spotřebitele).
                            </p>
                            <p>
                                15.2. Případné spory budou řešeny příslušným soudem v České
                                republice.
                            </p>
                            <p>
                                15.3. Spotřebitel může využít mimosoudní řešení sporu
                                prostřednictvím{" "}
                                <a
                                    href="https://www.coi.cz"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-neon-cyan hover:underline"
                                >
                                    České obchodní inspekce
                                </a>{" "}
                                (ČOI) nebo platformy{" "}
                                <a
                                    href="https://ec.europa.eu/consumers/odr"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-neon-cyan hover:underline"
                                >
                                    ODR
                                </a>
                                .
                            </p>
                            <p>
                                15.4. Poskytovatel si vyhrazuje právo tyto VOP změnit.
                                O změnách bude Uživatel informován e-mailem nebo oznámením
                                na webu nejméně 14 dní před nabytím účinnosti změn. V případě
                                nesouhlasu se změnami má Uživatel právo smlouvu vypovědět.
                            </p>
                            <p>
                                15.5. Je-li nebo stane-li se některé ustanovení těchto VOP
                                neplatným nebo nevymahatelným, nedotýká se to platnosti
                                ostatních ustanovení.
                            </p>
                            <p>
                                15.6. Tyto VOP nabývají účinnosti dne 14. února 2026.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
