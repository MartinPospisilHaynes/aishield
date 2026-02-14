import { Metadata } from "next";

export const metadata: Metadata = {
    title: "GDPR — AIshield.cz",
    description:
        "Informace o zpracování osobních údajů dle GDPR. Jak AIshield.cz chrání vaše data.",
};

export default function GdprPage() {
    return (
        <section className="py-20 relative">
            <div className="absolute inset-0 -z-10">
                <div className="absolute top-[10%] left-[20%] h-[400px] w-[400px] rounded-full bg-purple-600/8 blur-[120px]" />
            </div>

            <div className="mx-auto max-w-3xl px-6">
                <h1 className="text-3xl font-bold text-white">
                    Informace o zpracování osobních údajů (GDPR)
                </h1>
                <p className="mt-2 text-sm text-slate-500">
                    Dle Nařízení Evropského parlamentu a Rady (EU) 2016/679 (GDPR)
                </p>

                {/* Intro banner */}
                <div className="mt-8 rounded-2xl border border-fuchsia-500/20 bg-gradient-to-br from-fuchsia-500/5 via-purple-500/5 to-cyan-500/5 p-6 text-center">
                    <p className="text-slate-300 leading-relaxed">
                        Ochrana vašich osobních údajů je pro nás prioritou. Jako firma
                        specializovaná na AI Act compliance dbáme na to, abychom sami byli
                        plně v souladu s předpisy o ochraně osobních údajů.
                    </p>
                </div>

                <div className="mt-8 space-y-6">
                    {/* Správce */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            Správce osobních údajů
                        </h2>
                        <div className="text-slate-400 leading-relaxed">
                            <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-4">
                                <p>
                                    <strong className="text-white">Martin Haynes</strong>
                                </p>
                                <p>IČO: 17889251</p>
                                <p>Mlýnská 53, 783 53 Velká Bystřice</p>
                                <p>
                                    E-mail:{" "}
                                    <a
                                        href="mailto:info@aishield.cz"
                                        className="text-neon-fuchsia hover:underline"
                                    >
                                        info@aishield.cz
                                    </a>
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Přehled zpracování */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            Přehled zpracování osobních údajů
                        </h2>
                        <div className="text-slate-400 leading-relaxed">
                            <div className="overflow-x-auto">
                                <table className="w-full text-sm">
                                    <thead>
                                        <tr className="border-b border-white/[0.08]">
                                            <th className="py-3 pr-4 text-left text-slate-300 font-semibold">
                                                Účel
                                            </th>
                                            <th className="py-3 pr-4 text-left text-slate-300 font-semibold">
                                                Údaje
                                            </th>
                                            <th className="py-3 pr-4 text-left text-slate-300 font-semibold">
                                                Právní základ
                                            </th>
                                            <th className="py-3 text-left text-slate-300 font-semibold">
                                                Doba
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-white/[0.06]">
                                        <tr>
                                            <td className="py-3 pr-4">Registrace a účet</td>
                                            <td className="py-3 pr-4">E-mail, jméno, firma</td>
                                            <td className="py-3 pr-4">Plnění smlouvy</td>
                                            <td className="py-3">Existence účtu + 3 roky</td>
                                        </tr>
                                        <tr>
                                            <td className="py-3 pr-4">Skenování webu</td>
                                            <td className="py-3 pr-4">URL, nalezené AI systémy</td>
                                            <td className="py-3 pr-4">Plnění smlouvy</td>
                                            <td className="py-3">Existence účtu + 1 rok</td>
                                        </tr>
                                        <tr>
                                            <td className="py-3 pr-4">Dotazník o firmě</td>
                                            <td className="py-3 pr-4">
                                                Obor, počet zaměstnanců, AI nástroje
                                            </td>
                                            <td className="py-3 pr-4">Plnění smlouvy</td>
                                            <td className="py-3">Existence účtu + 1 rok</td>
                                        </tr>
                                        <tr>
                                            <td className="py-3 pr-4">Platby</td>
                                            <td className="py-3 pr-4">
                                                Fakturační údaje (karta přes GoPay)
                                            </td>
                                            <td className="py-3 pr-4">Zákonná povinnost</td>
                                            <td className="py-3">10 let</td>
                                        </tr>
                                        <tr>
                                            <td className="py-3 pr-4">Bezpečnost webu</td>
                                            <td className="py-3 pr-4">IP adresa, prohlížeč</td>
                                            <td className="py-3 pr-4">Oprávněný zájem</td>
                                            <td className="py-3">90 dní</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    {/* Zpracovatelé */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            Zpracovatelé a příjemci údajů
                        </h2>
                        <div className="text-slate-400 leading-relaxed">
                            <div className="grid gap-3 sm:grid-cols-2">
                                {[
                                    {
                                        name: "Supabase",
                                        role: "Autentizace, databáze",
                                        location: "EU",
                                    },
                                    {
                                        name: "Vercel",
                                        role: "Hosting aplikace",
                                        location: "EU/USA",
                                    },
                                    {
                                        name: "GoPay",
                                        role: "Platební brána",
                                        location: "Česko",
                                    },
                                    {
                                        name: "Resend",
                                        role: "Odesílání e-mailů",
                                        location: "EU/USA",
                                    },
                                    {
                                        name: "OpenAI",
                                        role: "AI analýza (bez os. údajů)",
                                        location: "USA",
                                    },
                                    {
                                        name: "Anthropic (Claude AI)",
                                        role: "AI klasifikace a dokumentace (bez os. údajů)",
                                        location: "USA",
                                    },
                                    {
                                        name: "Hetzner",
                                        role: "Backend server",
                                        location: "Německo",
                                    },
                                ].map((p) => (
                                    <div
                                        key={p.name}
                                        className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-3"
                                    >
                                        <p className="font-semibold text-white text-sm">
                                            {p.name}
                                        </p>
                                        <p className="text-xs text-slate-500">{p.role}</p>
                                        <p className="text-xs text-slate-600">📍 {p.location}</p>
                                    </div>
                                ))}
                            </div>
                            <p className="mt-4 text-sm">
                                U zpracovatelů se sídlem v USA je přenos dat zajištěn na základě
                                standardních smluvních doložek (SCC) dle čl. 46 odst. 2 GDPR.
                            </p>
                        </div>
                    </div>

                    {/* Práva */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            Vaše práva dle GDPR
                        </h2>
                        <div className="text-slate-400 leading-relaxed">
                            <div className="grid gap-3 sm:grid-cols-2">
                                {[
                                    {
                                        right: "Právo na přístup",
                                        article: "čl. 15",
                                        desc: "Získat kopii svých údajů",
                                    },
                                    {
                                        right: "Právo na opravu",
                                        article: "čl. 16",
                                        desc: "Opravit nepřesné údaje",
                                    },
                                    {
                                        right: "Právo na výmaz",
                                        article: "čl. 17",
                                        desc: "Smazání údajů",
                                    },
                                    {
                                        right: "Právo na omezení",
                                        article: "čl. 18",
                                        desc: "Dočasné omezení zpracování",
                                    },
                                    {
                                        right: "Právo na přenositelnost",
                                        article: "čl. 20",
                                        desc: "Strojově čitelný export",
                                    },
                                    {
                                        right: "Právo vznést námitku",
                                        article: "čl. 21",
                                        desc: "Proti oprávněnému zájmu",
                                    },
                                    {
                                        right: "Právo odvolat souhlas",
                                        article: "čl. 7 odst. 3",
                                        desc: "Kdykoliv, bez udání důvodu",
                                    },
                                ].map((r) => (
                                    <div
                                        key={r.right}
                                        className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-3"
                                    >
                                        <p className="font-semibold text-white text-sm">
                                            {r.right}
                                        </p>
                                        <p className="text-xs text-neon-fuchsia">{r.article} GDPR</p>
                                        <p className="text-xs text-slate-500 mt-1">{r.desc}</p>
                                    </div>
                                ))}
                            </div>
                            <p className="mt-4">
                                Pro uplatnění jakéhokoliv práva nás kontaktujte na{" "}
                                <a
                                    href="mailto:info@aishield.cz"
                                    className="text-neon-fuchsia hover:underline"
                                >
                                    info@aishield.cz
                                </a>
                                . Na vaši žádost odpovíme do{" "}
                                <strong className="text-white">30 dnů</strong>.
                            </p>
                        </div>
                    </div>

                    {/* Zabezpečení */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            Technická a organizační opatření
                        </h2>
                        <div className="text-slate-400 leading-relaxed">
                            <ul className="space-y-2 list-disc list-inside">
                                <li>Šifrování přenosu dat (TLS 1.3)</li>
                                <li>Šifrování hesel (bcrypt hashing přes Supabase Auth)</li>
                                <li>
                                    Řízení přístupu — princip nejmenších oprávnění (least
                                    privilege)
                                </li>
                                <li>Pravidelné bezpečnostní kontroly a aktualizace</li>
                                <li>Zálohování dat (automatické zálohy Supabase)</li>
                                <li>Logování přístupů pro detekci neautorizovaných aktivit</li>
                            </ul>
                        </div>
                    </div>

                    {/* Automatizované rozhodování */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            Automatizované rozhodování a profilování
                        </h2>
                        <div className="text-slate-400 leading-relaxed">
                            <p>
                                Naše služba využívá automatizované zpracování (AI/ML modely) pro:
                            </p>
                            <ul className="mt-2 space-y-2 list-disc list-inside">
                                <li>Detekci AI systémů na skenovaných webech</li>
                                <li>Klasifikaci rizik dle AI Act</li>
                                <li>Generování compliance dokumentace</li>
                            </ul>
                            <p className="mt-3">
                                Toto zpracování se{" "}
                                <strong className="text-white">netýká osobních údajů</strong>{" "}
                                uživatelů — analyzujeme pouze veřejně dostupný obsah webových
                                stránek. Výsledky jsou vždy k dispozici k přezkoumání
                                uživatelem.
                            </p>
                        </div>
                    </div>

                    {/* Dozorový úřad */}
                    <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6">
                        <h2 className="text-lg font-semibold text-white mb-3">
                            Dozorový úřad
                        </h2>
                        <div className="text-slate-400 leading-relaxed">
                            <p>
                                Pokud se domníváte, že zpracováváme vaše údaje v rozporu
                                s GDPR, máte právo podat stížnost u:
                            </p>
                            <div className="mt-3 rounded-xl border border-white/[0.08] bg-white/[0.02] p-4">
                                <p className="font-semibold text-white">
                                    Úřad pro ochranu osobních údajů (ÚOOÚ)
                                </p>
                                <p className="text-sm">Pplk. Sochora 27, 170 00 Praha 7</p>
                                <p className="text-sm">
                                    Web:{" "}
                                    <a
                                        href="https://www.uoou.cz"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-neon-cyan hover:underline"
                                    >
                                        www.uoou.cz
                                    </a>
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
