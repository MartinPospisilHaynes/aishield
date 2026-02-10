import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Obchodní podmínky — AIshield.cz",
  description:
    "Všeobecné obchodní podmínky služby AIshield.cz pro AI Act compliance služby.",
};

export default function TermsPage() {
  const sections = [
    {
      title: "1. Úvodní ustanovení",
      content: (
        <>
          <p>
            Tyto všeobecné obchodní podmínky (dále jen &bdquo;VOP&ldquo;) upravují
            vzájemná práva a povinnosti mezi poskytovatelem služby:
          </p>
          <div className="mt-3 rounded-xl border border-white/[0.08] bg-white/[0.02] p-4">
            <p>
              <strong className="text-white">Martin Haynes</strong>
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
          </div>
          <p className="mt-3">
            (dále jen &bdquo;Poskytovatel&ldquo;) a uživatelem služby AIshield.cz (dále
            jen &bdquo;Uživatel&ldquo;).
          </p>
        </>
      ),
    },
    {
      title: "2. Definice pojmů",
      content: (
        <ul className="space-y-2 list-disc list-inside">
          <li>
            <strong className="text-white">Služba</strong> — webová aplikace
            AIshield.cz umožňující skenování webových stránek na přítomnost AI
            systémů, vyhodnocení souladu s AI Act (Nařízení EU 2024/1689) a
            generování compliance dokumentace.
          </li>
          <li>
            <strong className="text-white">Bezplatný sken</strong> — základní
            skenování webu dostupné bez registrace a platby.
          </li>
          <li>
            <strong className="text-white">Placená služba</strong> — kompletní
            AI Act Compliance Kit včetně vygenerované dokumentace dle zvoleného
            cenového balíčku.
          </li>
          <li>
            <strong className="text-white">Dokumentace</strong> — compliance
            report, akční plán, registr AI systémů, transparenční stránka,
            chatbot oznámení, AI politika firmy a osnova školení zaměstnanců.
          </li>
        </ul>
      ),
    },
    {
      title: "3. Uzavření smlouvy",
      content: (
        <>
          <ol className="space-y-2 list-decimal list-inside">
            <li>
              Smlouva o poskytování služeb vzniká okamžikem úspěšné úhrady
              zvoleného cenového balíčku prostřednictvím platební brány GoPay.
            </li>
            <li>
              Bezplatné skenování webu nezakládá smluvní vztah a je
              poskytováno bez záruky.
            </li>
            <li>
              Registrací uživatel potvrzuje, že se seznámil s těmito VOP a
              souhlasí s nimi.
            </li>
          </ol>
        </>
      ),
    },
    {
      title: "4. Ceny a platební podmínky",
      content: (
        <>
          <ol className="space-y-2 list-decimal list-inside">
            <li>
              Aktuální ceny jsou uvedeny na stránce{" "}
              <a href="/pricing" className="text-neon-fuchsia hover:underline">
                Ceník
              </a>
              . Všechny ceny jsou uvedeny včetně DPH (Poskytovatel není
              plátcem DPH).
            </li>
            <li>
              Platba probíhá jednorázově prostřednictvím platební brány GoPay
              (platební karta, bankovní převod).
            </li>
            <li>
              Po úspěšné platbě Uživatel obdrží potvrzení na e-mail a daňový
              doklad (fakturu).
            </li>
            <li>
              Poskytovatel si vyhrazuje právo ceny jednostranně změnit.
              Změna cen se nevztahuje na již uhrazené objednávky.
            </li>
          </ol>
        </>
      ),
    },
    {
      title: "5. Poskytování služby",
      content: (
        <>
          <ol className="space-y-2 list-decimal list-inside">
            <li>
              Po zaplacení a vyplnění dotazníku Poskytovatel vygeneruje
              compliance dokumentaci do 48 hodin (obvykle do několika hodin).
            </li>
            <li>
              Dokumentace je dostupná ke stažení v uživatelském dashboardu.
            </li>
            <li>
              Dokumentace je generována na základě informací poskytnutých
              Uživatelem. Poskytovatel neodpovídá za nesprávnosti způsobené
              nepřesnými nebo neúplnými údaji ze strany Uživatele.
            </li>
            <li>
              Služba má informativní charakter a{" "}
              <strong className="text-white">
                nenahrazuje právní poradenství
              </strong>
              . Pro právně závazné posouzení doporučujeme konzultaci
              s advokátem.
            </li>
          </ol>
        </>
      ),
    },
    {
      title: "6. Odstoupení od smlouvy",
      content: (
        <>
          <ol className="space-y-2 list-decimal list-inside">
            <li>
              Uživatel — spotřebitel má právo odstoupit od smlouvy bez udání
              důvodu do <strong className="text-white">14 dnů</strong> od
              uzavření smlouvy dle § 1829 občanského zákoníku.
            </li>
            <li>
              Pokud Uživatel požádal o zahájení poskytování služby před
              uplynutím lhůty pro odstoupení a služba byla poskytnuta (dokumenty
              vygenerovány), bere na vědomí, že tím může zaniknout právo
              na odstoupení dle § 1837 písm. a) občanského zákoníku.
            </li>
            <li>
              Pro odstoupení od smlouvy kontaktujte{" "}
              <a
                href="mailto:info@aishield.cz"
                className="text-neon-fuchsia hover:underline"
              >
                info@aishield.cz
              </a>{" "}
              s číslem objednávky.
            </li>
            <li>
              Vrácení peněz proběhne do 14 dnů od přijetí odstoupení, stejným
              způsobem, jakým byla platba přijata.
            </li>
          </ol>
        </>
      ),
    },
    {
      title: "7. Reklamace",
      content: (
        <>
          <ol className="space-y-2 list-decimal list-inside">
            <li>
              Uživatel má právo uplatnit reklamaci služby v případě, že
              vygenerovaná dokumentace je nekompletní, obsahuje zjevné chyby
              nebo neodpovídá objednanému balíčku.
            </li>
            <li>
              Reklamaci lze uplatnit e-mailem na{" "}
              <a
                href="mailto:info@aishield.cz"
                className="text-neon-fuchsia hover:underline"
              >
                info@aishield.cz
              </a>{" "}
              do 30 dnů od dodání dokumentace.
            </li>
            <li>
              Poskytovatel reklamaci vyřídí do 30 dnů od jejího uplatnění,
              a to opravou dokumentace nebo vrácením ceny.
            </li>
          </ol>
        </>
      ),
    },
    {
      title: "8. Odpovědnost a omezení",
      content: (
        <>
          <ol className="space-y-2 list-decimal list-inside">
            <li>
              Poskytovatel prohlašuje, že vygenerovaná dokumentace vychází
              z aktuálního znění AI Act (Nařízení EU 2024/1689) a souvisejících
              předpisů.
            </li>
            <li>
              Služba{" "}
              <strong className="text-white">
                nepředstavuje právní poradenství
              </strong>{" "}
              ve smyslu zákona č. 85/1996 Sb. o advokacii. Jedná se
              o automatizovaný technický nástroj.
            </li>
            <li>
              Poskytovatel neodpovídá za škody vzniklé v důsledku použití
              vygenerované dokumentace, zejména za pokuty uložené dozorovými
              orgány.
            </li>
            <li>
              Celková odpovědnost Poskytovatele je omezena na výši uhrazené
              ceny za službu.
            </li>
          </ol>
        </>
      ),
    },
    {
      title: "9. Duševní vlastnictví",
      content: (
        <>
          <ol className="space-y-2 list-decimal list-inside">
            <li>
              Vygenerovaná dokumentace je určena výhradně pro interní použití
              Uživatele a jeho firmy.
            </li>
            <li>
              Uživatel nesmí vygenerovanou dokumentaci dále prodávat ani
              zpřístupňovat třetím stranám pro komerční účely.
            </li>
            <li>
              Webová aplikace AIshield.cz, její design, kód a obsah jsou
              chráněny autorskými právy Poskytovatele.
            </li>
          </ol>
        </>
      ),
    },
    {
      title: "10. Ochrana osobních údajů",
      content: (
        <p>
          Zpracování osobních údajů se řídí{" "}
          <a href="/privacy" className="text-neon-fuchsia hover:underline">
            Zásadami ochrany soukromí
          </a>{" "}
          a{" "}
          <a href="/gdpr" className="text-neon-fuchsia hover:underline">
            informacemi o GDPR
          </a>
          .
        </p>
      ),
    },
    {
      title: "11. Závěrečná ustanovení",
      content: (
        <>
          <ol className="space-y-2 list-decimal list-inside">
            <li>
              Tyto VOP se řídí právním řádem České republiky, zejména zákonem
              č. 89/2012 Sb. (občanský zákoník) a zákonem č. 634/1992 Sb.
              (zákon o ochraně spotřebitele).
            </li>
            <li>
              Případné spory budou řešeny příslušným soudem v České republice.
            </li>
            <li>
              Spotřebitel může využít mimosoudní řešení sporu prostřednictvím{" "}
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
            </li>
            <li>
              Poskytovatel si vyhrazuje právo tyto VOP jednostranně změnit.
              O změnách bude Uživatel informován e-mailem nebo oznámením na
              webu.
            </li>
          </ol>
        </>
      ),
    },
  ];

  return (
    <section className="py-20 relative">
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-[10%] right-[20%] h-[400px] w-[400px] rounded-full bg-cyan-500/8 blur-[120px]" />
      </div>

      <div className="mx-auto max-w-3xl px-6">
        <h1 className="text-3xl font-bold text-white">Obchodní podmínky</h1>
        <p className="mt-2 text-sm text-slate-500">
          Poslední aktualizace: 10. února 2025
        </p>

        <div className="mt-8 space-y-6">
          {sections.map((s, i) => (
            <div
              key={i}
              className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-6"
            >
              <h2 className="text-lg font-semibold text-white mb-3">
                {s.title}
              </h2>
              <div className="text-slate-400 leading-relaxed">{s.content}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
