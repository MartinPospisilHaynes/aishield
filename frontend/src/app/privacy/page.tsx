import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Ochrana soukromí — AIshield.cz",
  description:
    "Zásady ochrany osobních údajů služby AIshield.cz. Jak zpracováváme vaše data v souladu s GDPR.",
};

export default function PrivacyPage() {
  const sections = [
    {
      title: "1. Správce osobních údajů",
      content: (
        <>
          <p>
            Správcem osobních údajů je{" "}
            <strong className="text-white">Martin Haynes</strong>, IČO:
            17889251, se sídlem Mlýnská 53, 783 53 Velká Bystřice (dále jen
            &bdquo;Správce&ldquo;).
          </p>
          <p className="mt-2">
            Kontakt:{" "}
            <a
              href="mailto:info@aishield.cz"
              className="text-neon-fuchsia hover:underline"
            >
              info@aishield.cz
            </a>
            , tel.{" "}
            <a
              href="tel:+420732716141"
              className="text-neon-cyan hover:underline"
            >
              +420 732 716 141
            </a>
          </p>
        </>
      ),
    },
    {
      title: "2. Jaké údaje zpracováváme",
      content: (
        <ul className="space-y-2 list-disc list-inside">
          <li>
            <strong className="text-white">Registrační údaje</strong> — e-mail,
            jméno, název firmy, IČO (při registraci)
          </li>
          <li>
            <strong className="text-white">Údaje z dotazníku</strong> — odpovědi
            o vaší firmě a používání AI systémů (pro přípravu compliance
            dokumentace)
          </li>
          <li>
            <strong className="text-white">Údaje ze skenování</strong> — URL
            adresa a technické informace o AI systémech na vašem webu
          </li>
          <li>
            <strong className="text-white">Platební údaje</strong> — zpracovává
            platební brána GoPay, my neukládáme čísla karet
          </li>
          <li>
            <strong className="text-white">Technické údaje</strong> — IP adresa,
            typ prohlížeče, čas přístupu (logy serveru)
          </li>
        </ul>
      ),
    },
    {
      title: "3. Účel zpracování",
      content: (
        <ul className="space-y-2 list-disc list-inside">
          <li>Poskytování služby skenování webu a přípravy AI Act dokumentace</li>
          <li>Správa uživatelského účtu a komunikace</li>
          <li>Zpracování plateb</li>
          <li>Plnění zákonných povinností (účetní a daňové předpisy)</li>
          <li>Zlepšování služby a oprava chyb</li>
        </ul>
      ),
    },
    {
      title: "4. Právní základ zpracování",
      content: (
        <ul className="space-y-2 list-disc list-inside">
          <li>
            <strong className="text-white">Plnění smlouvy</strong> (čl. 6
            odst. 1 písm. b) GDPR) — pro poskytování objednaných služeb
          </li>
          <li>
            <strong className="text-white">Oprávněný zájem</strong> (čl. 6
            odst. 1 písm. f) GDPR) — pro zabezpečení a zlepšování služby
          </li>
          <li>
            <strong className="text-white">Zákonná povinnost</strong> (čl. 6
            odst. 1 písm. c) GDPR) — pro plnění účetních a daňových předpisů
          </li>
          <li>
            <strong className="text-white">Souhlas</strong> (čl. 6 odst. 1
            písm. a) GDPR) — pro zasílání obchodních sdělení (pokud jste
            souhlasili)
          </li>
        </ul>
      ),
    },
    {
      title: "5. Příjemci údajů",
      content: (
        <>
          <p>Vaše údaje mohou být sdíleny s těmito zpracovateli:</p>
          <ul className="mt-2 space-y-2 list-disc list-inside">
            <li>
              <strong className="text-white">Supabase</strong> — autentizace a
              databáze (servery v EU)
            </li>
            <li>
              <strong className="text-white">Vercel</strong> — hosting
              webové aplikace
            </li>
            <li>
              <strong className="text-white">GoPay</strong> — zpracování
              plateb (česká společnost)
            </li>
            <li>
              <strong className="text-white">Resend</strong> — odesílání
              e-mailů
            </li>
            <li>
              <strong className="text-white">OpenAI</strong> — analýza AI
              systémů a generování dokumentace (bez přenosu osobních údajů
              uživatelů)
            </li>
          </ul>
          <p className="mt-3">
            Vaše údaje neprodáváme a nesdílíme s třetími stranami pro
            marketingové účely.
          </p>
        </>
      ),
    },
    {
      title: "6. Doba uchovávání",
      content: (
        <ul className="space-y-2 list-disc list-inside">
          <li>Registrační údaje — po dobu existence účtu + 3 roky</li>
          <li>Výsledky skenů a dokumentace — po dobu existence účtu + 1 rok</li>
          <li>
            Fakturační údaje — 10 let (zákonná povinnost dle zákona o
            účetnictví)
          </li>
          <li>Logy serveru — 90 dní</li>
        </ul>
      ),
    },
    {
      title: "7. Vaše práva",
      content: (
        <>
          <p>Podle GDPR máte právo:</p>
          <ul className="mt-2 space-y-2 list-disc list-inside">
            <li>
              <strong className="text-white">Na přístup</strong> — získat kopii
              svých údajů
            </li>
            <li>
              <strong className="text-white">Na opravu</strong> — opravit
              nepřesné údaje
            </li>
            <li>
              <strong className="text-white">Na výmaz</strong> — požádat o
              smazání údajů (&quot;právo být zapomenut&quot;)
            </li>
            <li>
              <strong className="text-white">Na omezení zpracování</strong> —
              dočasně omezit zpracování
            </li>
            <li>
              <strong className="text-white">Na přenositelnost</strong> — získat
              údaje ve strojově čitelném formátu
            </li>
            <li>
              <strong className="text-white">Vznést námitku</strong> — proti
              zpracování na základě oprávněného zájmu
            </li>
            <li>
              <strong className="text-white">Odvolat souhlas</strong> — kdykoliv,
              bez udání důvodu
            </li>
          </ul>
          <p className="mt-3">
            Pro výkon svých práv nás kontaktujte na{" "}
            <a
              href="mailto:info@aishield.cz"
              className="text-neon-fuchsia hover:underline"
            >
              info@aishield.cz
            </a>
            . Na vaši žádost odpovíme do 30 dnů.
          </p>
        </>
      ),
    },
    {
      title: "8. Cookies",
      content: (
        <>
          <p>Používáme pouze technicky nezbytné cookies pro:</p>
          <ul className="mt-2 space-y-2 list-disc list-inside">
            <li>Přihlášení a správu relace (session cookies)</li>
            <li>Bezpečnostní tokeny (CSRF ochrana)</li>
          </ul>
          <p className="mt-3">
            Nepoužíváme reklamní ani analytické cookies třetích stran.
          </p>
        </>
      ),
    },
    {
      title: "9. Zabezpečení",
      content: (
        <p>
          Vaše údaje chráníme pomocí šifrování (HTTPS/TLS), bezpečného
          ukládání hesel (bcrypt hashing přes Supabase Auth), řízení přístupu
          a pravidelných bezpečnostních kontrol. Přístup k údajům mají pouze
          oprávněné osoby.
        </p>
      ),
    },
    {
      title: "10. Dozorový úřad",
      content: (
        <p>
          Pokud se domníváte, že vaše osobní údaje zpracováváme v rozporu
          s GDPR, máte právo podat stížnost u{" "}
          <strong className="text-white">
            Úřadu pro ochranu osobních údajů
          </strong>{" "}
          (ÚOOÚ), Pplk. Sochora 27, 170 00 Praha 7,{" "}
          <a
            href="https://www.uoou.cz"
            target="_blank"
            rel="noopener noreferrer"
            className="text-neon-cyan hover:underline"
          >
            www.uoou.cz
          </a>
          .
        </p>
      ),
    },
  ];

  return (
    <section className="py-20 relative">
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-[10%] left-[30%] h-[400px] w-[400px] rounded-full bg-fuchsia-600/8 blur-[120px]" />
      </div>

      <div className="mx-auto max-w-3xl px-6">
        <h1 className="text-3xl font-bold text-white">Ochrana soukromí</h1>
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
