/**
 * ArticleJsonLd — strukturovaná data pro blog články (schema.org Article)
 * Vkládá JSON-LD do <head> pro lepší indexaci v Google, AI Overviews a News.
 */
interface ArticleJsonLdProps {
    title: string;
    description: string;
    slug: string;
    datePublished: string; // ISO 8601: "2026-02-28"
    dateModified?: string;
    image?: string;
    tags?: string[];
}

export default function ArticleJsonLd({
    title,
    description,
    slug,
    datePublished,
    dateModified,
    image,
    tags = [],
}: ArticleJsonLdProps) {
    const schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "url": `https://aishield.cz/blog/${slug}`,
        "datePublished": datePublished,
        "dateModified": dateModified || datePublished,
        "author": {
            "@type": "Organization",
            "@id": "https://aishield.cz/#organization",
            "name": "AIshield.cz",
        },
        "publisher": {
            "@type": "Organization",
            "@id": "https://aishield.cz/#organization",
            "name": "AIshield.cz",
            "logo": {
                "@type": "ImageObject",
                "url": "https://aishield.cz/icon.png",
            },
        },
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": `https://aishield.cz/blog/${slug}`,
        },
        "inLanguage": "cs",
        ...(image ? { "image": `https://aishield.cz${image}` } : {}),
        ...(tags.length > 0 ? { "keywords": tags.join(", ") } : {}),
    };

    return (
        <script
            type="application/ld+json"
            dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
        />
    );
}
