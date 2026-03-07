import type { Metadata } from "next";
import ContentPage from "@/components/content-page";
import BlogCta from "@/components/blog-cta";
import Link from "next/link";

export const metadata: Metadata = {
    title: "Zákazy AI systémů: Článek 5 AI Actu vysvětlen | AIshield.cz",
    description: "Článek 5 EU AI Actu zakazuje nejnebezpečnější AI aplikace. Přehled všech zakázaných AI praktik — manipulace, social scoring, prediktivní policie a další.",
    alternates: { canonical: "https://aishield.cz/blog/zakazy-ai-systemu-clanek-5" },
    openGraph: {
        images: [{ url: "/blog/zakazy-ai-systemu-clanek-5.png", width: 1200, height: 630 }],
    },
    keywords: [
        "zákazy AI systémů",
        "článek 5 AI Act",
        "zakázané AI praktiky",
        "social scoring AI",
        "manipulativní AI zákaz",
        "AI Act prohibited practices",
    ],
};

export default function Page() {
    return (
        <>
            <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: `{"@context": "https://schema.org", "@type": "BlogPosting", "headline": "Zákazy AI systémů: Článek 5 AI Actu vysvětlen", "description": "Článek 5 EU AI Actu zakazuje nejnebezpečnější AI aplikace. Přehled všech zakázaných AI praktik.", "datePublished": "2026-02-01", "dateModified": "2026-03-07", "author": {"@type": "Organization", "name": "AIshield.cz", "url": "https://aishield.cz"}, "publisher": {"@type": "Organization", "name": "AIshield.cz", "logo": {"@type": "ImageObject", "url": "https://aishield.cz/icon.png"}}, "mainEntityOfPage": {"@type": "WebPage", "@id": "https://aishield.cz/blog/zakazy-ai-systemu-clanek-5"}, "inLanguage": "cs", "keywords": "zákazy AI systémů, článek 5 AI Act, zakázané AI praktiky", "image": "https://aishield.cz/blog/zakazy-ai-systemu-clanek-5.png"}` }} />
            <ContentPage
                heroImage="/blog/zakazy-ai-systemu-clanek-5.png"
                breadcrumbs={[
                    { label: "Domů", href: "/" },
                    { label: "Blog", href: "/blog" },
                    { label: "Zákazy AI systémů: Článek 5" },
                ]}
                title="Zákazy AI systémů:"
                titleAccent="Článek 5 AI Actu vysvětlen"
                subtitle="1. února 2026 • 6 min čtení"
            >
                <section>
                    <h2 className="text-xl font-semibold text-white mb-3">Co zakazuje článek 5 AI Actu?</h2>
                    <p>EU AI Act (Nařízení 2024/1689) definuje ve svém článku 5 absolutní zákazy — AI praktiky, které jsou považovány za natolik nebezpečné, že jejich používání je v EU zcela nepřípustné. Tyto zákazy vstoupily v platnost jako první část AI Actu, již od 2. února 2025, což podtrhuje jejich naléhavost.</p>
                    <p>Na rozdíl od vysoce rizikových AI systémů, které lze provozovat za splnění přísných podmínek, zakázané AI praktiky nelze legálně používat za žádných okolností. Porušení těchto zákazů představuje nejzávažnější přestupek dle AI Actu s odpovídajícími maximálními sankcemi.</p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold text-white mb-3">Přehled zakázaných AI praktik</h2>
                    <p>Článek 5 AI Actu zakazuje celkem osm kategorií AI aplikací. Jejich společným jmenovatelem je, že všechny představují zásadní ohrožení základních práv a svobod občanů EU.</p>

                    <h3 className="text-lg font-medium text-white mt-6 mb-2">1. Manipulativní a klamavé AI systémy</h3>
                    <p>Zakázány jsou AI systémy, které využívají podprahové techniky, záměrně manipulativní nebo klamavé postupy k podstatnému narušení rozhodování osob. Výsledkem musí být nebo je pravděpodobné, že bude způsobena významná újma. Příkladem může být AI chatbot záměrně navržený k psychologické manipulaci spotřebitelů ke koupi nebezpečných produktů nebo AI systém pro podprahovou reklamu.</p>

                    <h3 className="text-lg font-medium text-white mt-6 mb-2">2. Zneužívání zranitelností</h3>
                    <p>Zakázány jsou AI systémy, které cíleně zneužívají zranitelnosti osob z důvodu jejich věku, zdravotního postižení nebo specifické sociální či ekonomické situace. Jedná se o AI aplikace, které záměrně těží z toho, že oběť není schopna se manipulaci bránit — například AI systém cílící klamavé reklamy na seniory s kognitivním poklesem.</p>

                    <h3 className="text-lg font-medium text-white mt-6 mb-2">3. Sociální bodování (Social Scoring)</h3>
                    <p>Zcela zakázáno je hodnocení nebo klasifikace fyzických osob na základě jejich sociálního chování nebo osobnostních charakteristik (social scoring), pokud vede k znevýhodňujícímu zacházení. Zákaz se vztahuje na systémy, kde je výsledné hodnocení neodůvodněné nebo nepřiměřené kontextu, ve kterém byly údaje shromážděny. Tento zákaz přímo reaguje na praktiky známé z čínského systému sociálního kreditu.</p>

                    <h3 className="text-lg font-medium text-white mt-6 mb-2">4. Predikce kriminality na základě profilování</h3>
                    <p>Zakázány jsou AI systémy pro posuzování nebo predikci rizika, že fyzická osoba spáchá trestný čin, pokud vychází výhradně z profilování osoby nebo z posouzení jejích osobnostních rysů a charakteristik. Policejní predikce založená čistě na tom, kdo osoba je, nikoliv na objektivních faktech, je nepřípustná. Systémy založené na analýze konkrétních důkazů spojených s trestnou činností však zakázány nejsou.</p>

                    <h3 className="text-lg font-medium text-white mt-6 mb-2">5. Plošný scraping obličejových obrázků</h3>
                    <p>AI Act zakazuje vytváření nebo rozšiřování databází pro rozpoznávání obličejů prostřednictvím nelokalizovaného scrapingu obličejových obrázků z internetu nebo CCTV záznamů. Takové praktiky, jaké používala firma Clearview AI, jsou v EU jednoznačně nelegální.</p>

                    <h3 className="text-lg font-medium text-white mt-6 mb-2">6. Rozpoznávání emocí na pracovišti a ve školách</h3>
                    <p>Zakázáno je používání AI systémů pro rozpoznávání emocí zaměstnanců na pracovišti a studentů ve vzdělávacích institucích. Výjimku tvoří systémy využívané z lékařských nebo bezpečnostních důvodů (např. detekce únavy řidiče kamionu).</p>

                    <h3 className="text-lg font-medium text-white mt-6 mb-2">7. Biometrická kategorizace citlivých vlastností</h3>
                    <p>Zakázány jsou AI systémy, které kategorizují osoby na základě biometrických dat za účelem odvození citlivých informací — konkrétně rasy, politických názorů, členství v odborech, náboženského vyznání, sexuální orientace nebo sexuálního života. Výjimku představuje zákonné označování biometrických datových souborů a filtrování v oblasti vymáhání práva.</p>

                    <h3 className="text-lg font-medium text-white mt-6 mb-2">8. Biometrická identifikace v reálném čase ve veřejném prostoru</h3>
                    <p>Použití systémů biometrické identifikace na dálku v reálném čase na veřejně přístupných místech pro účely vymáhání práva je obecně zakázáno. Existují tři úzce vymezené výjimky — hledání obětí únosu, prevence konkrétní bezprostřední teroristické hrozby a lokalizace podezřelých z vážných trestných činů — ale i tyto vyžadují předchozí povolení soudu nebo nezávislého orgánu.</p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold text-white mb-3">Jaké jsou sankce za porušení zákazů?</h2>
                    <p>Porušení zákazů dle článku 5 nese nejvyšší možné pokuty v rámci celého AI Actu. Maximální sankce činí <strong className="text-fuchsia-400">35 milionů EUR nebo 7 % celkového celosvětového ročního obratu</strong> (podle toho, co je vyšší). Pro porovnání — u porušení jiných ustanovení AI Actu jsou maximální pokuty nižší (15 milionů EUR / 3 % obratu). Výše pokut jasně signalizuje, jak vážně EU tyto zákazy bere.</p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold text-white mb-3">Co byste měli udělat?</h2>
                    <p>Zákazy dle článku 5 platí od února 2025 — už teď. Každá firma, která využívá AI, by měla provést interní audit a ověřit, zda žádná z jejích AI aplikací nespadá do zakázaných kategorií. Nevědomost není omluvou a sankce jsou drakonické.</p>
                    <p>Klíčové kroky: (1) Zmapujte všechny AI systémy ve vaší organizaci, (2) Porovnejte je se seznamem zákazů, (3) Pokud máte pochybnosti, konzultujte situaci s odborníkem.</p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold text-white mb-3">Související články</h2>
                    <ul className="list-disc pl-6 space-y-2 text-slate-400">
                        <li><Link href="/blog/vysoko-rizikove-ai-systemy-priloha-iii" className="text-fuchsia-400 hover:text-fuchsia-300 transition-colors">Vysoce rizikové AI systémy: Příloha III</Link></li>
                        <li><Link href="/ai-act/rizikove-kategorie" className="text-fuchsia-400 hover:text-fuchsia-300 transition-colors">Rizikové kategorie AI Actu</Link></li>
                        <li><Link href="/blog/ai-act-pokuty-az-35-milionu-eur" className="text-fuchsia-400 hover:text-fuchsia-300 transition-colors">AI Act pokuty — až 35 milionů EUR</Link></li>
                        <li><Link href="/scan" className="text-fuchsia-400 hover:text-fuchsia-300 transition-colors">Objednejte si AI Act sken</Link></li>
                    </ul>
                </section>

                <BlogCta />
            </ContentPage>
        </>
    );
}
