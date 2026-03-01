import Link from "next/link";
import Image from "next/image";

interface Breadcrumb {
    label: string;
    href?: string;
}

interface ContentPageProps {
    breadcrumbs?: Breadcrumb[];
    title: string;
    titleAccent?: string;
    subtitle?: string;
    heroImage?: string;
    heroAlt?: string;
    children: React.ReactNode;
    cta?: boolean;
}

export default function ContentPage({
    breadcrumbs,
    title,
    titleAccent,
    subtitle,
    heroImage,
    heroAlt,
    children,
    cta = true,
}: ContentPageProps) {
    // Generate BreadcrumbList JSON-LD
    const breadcrumbSchema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": breadcrumbs?.map((bc, i) => ({
            "@type": "ListItem",
            "position": i + 1,
            "name": bc.label,
            ...(bc.href ? { "item": `https://aishield.cz${bc.href}` } : {}),
        })),
    };

    return (
        <article className="py-20 sm:py-28">
            <div className="mx-auto max-w-3xl px-4 sm:px-6">
                {breadcrumbs && (
                    <nav aria-label="Breadcrumb" className="mb-8 text-sm text-slate-500">
                        <ol className="flex flex-wrap items-center gap-1.5">
                            {breadcrumbs.map((b, i) => (
                                <li key={i} className="flex items-center gap-1.5">
                                    {i > 0 && <span>/</span>}
                                    {b.href ? (
                                        <Link href={b.href} className="hover:text-fuchsia-400 transition-colors">
                                            {b.label}
                                        </Link>
                                    ) : (
                                        <span className="text-slate-400">{b.label}</span>
                                    )}
                                </li>
                            ))}
                        </ol>
                    </nav>
                )}
                <header className="mb-12">
                    <h1 className="text-3xl font-extrabold sm:text-4xl lg:text-5xl mb-4">
                        {title}{" "}
                        {titleAccent && <span className="neon-text">{titleAccent}</span>}
                    </h1>
                    {subtitle && (
                        <p className="text-lg text-slate-400 max-w-2xl">{subtitle}</p>
                    )}
                </header>
                {heroImage && (
                    <div className="relative w-full aspect-[1200/630] rounded-2xl overflow-hidden mb-12 border border-white/[0.06]">
                        <Image
                            src={heroImage}
                            alt={heroAlt || title}
                            fill
                            className="object-cover"
                            sizes="(max-width: 768px) 100vw, 720px"
                            priority
                        />
                    </div>
                )}
                <div className="space-y-8 text-slate-300 leading-relaxed">
                    {children}
                </div>
                {cta && (
                    <div className="mt-16 rounded-2xl border border-fuchsia-500/20 bg-fuchsia-500/5 p-8 text-center">
                        <p className="text-xl font-semibold text-white mb-2">
                            Chcete vědět, jestli se vás AI Act týká?
                        </p>
                        <p className="text-slate-400 mb-6">
                            Zadejte URL vašeho webu — sken je zdarma a trvá 60 sekund.
                        </p>
                        <Link
                            href="/scan"
                            className="btn-primary cta-pulse text-base px-8 py-3.5 inline-flex items-center justify-center gap-2"
                        >
                            Skenovat web ZDARMA
                        </Link>
                    </div>
                )}
            </div>
        </article>
    );
}
