import type { MetadataRoute } from "next";
import manifest from "@/data/blog-manifest.json";

/**
 * Dynamická sitemap pro Google Search Console + Bing.
 * Generuje URL pro všechny statické stránky i blogové články.
 */
export default function sitemap(): MetadataRoute.Sitemap {
    const baseUrl = "https://aishield.cz";

    // Statické stránky — všechny veřejné routy
    const staticPages: MetadataRoute.Sitemap = [
        // Hlavní stránky
        { url: baseUrl, lastModified: new Date(), changeFrequency: "weekly", priority: 1.0 },
        { url: `${baseUrl}/scan`, lastModified: new Date(), changeFrequency: "weekly", priority: 0.9 },
        { url: `${baseUrl}/blog`, lastModified: new Date(), changeFrequency: "daily", priority: 0.8 },
        { url: `${baseUrl}/pricing`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.7 },
        { url: `${baseUrl}/enterprise`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.7 },
        { url: `${baseUrl}/about`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        { url: `${baseUrl}/faq`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        { url: `${baseUrl}/kariera`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.4 },
        { url: `${baseUrl}/shoptet`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        // AI Act sekce
        { url: `${baseUrl}/ai-act`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.7 },
        { url: `${baseUrl}/ai-act/clanek-50`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.6 },
        { url: `${baseUrl}/ai-act/rizikove-kategorie`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.6 },
        { url: `${baseUrl}/ai-act/checklist`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.6 },
        { url: `${baseUrl}/ai-act/pokuty`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.6 },
        { url: `${baseUrl}/ai-act/co-je-ai-act`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.6 },
        { url: `${baseUrl}/ai-act/e-shopy`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.6 },
        { url: `${baseUrl}/ai-act-souhlas`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.4 },
        // Pro koho — oborové a městské landing pages
        { url: `${baseUrl}/pro-koho`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.6 },
        { url: `${baseUrl}/pro-koho/praha`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        { url: `${baseUrl}/pro-koho/brno`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        { url: `${baseUrl}/pro-koho/ostrava`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        { url: `${baseUrl}/pro-koho/plzen`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        { url: `${baseUrl}/pro-koho/olomouc`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        { url: `${baseUrl}/pro-koho/liberec`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        { url: `${baseUrl}/pro-koho/hradec-kralove`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        { url: `${baseUrl}/pro-koho/ceske-budejovice`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        { url: `${baseUrl}/pro-koho/male-firmy`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        { url: `${baseUrl}/pro-koho/startupy`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        { url: `${baseUrl}/pro-koho/agentury`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        { url: `${baseUrl}/pro-koho/obce`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        // Integrace
        { url: `${baseUrl}/integrace`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        { url: `${baseUrl}/integrace/openai-chatgpt`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        { url: `${baseUrl}/integrace/google-analytics`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        { url: `${baseUrl}/integrace/meta-pixel`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        { url: `${baseUrl}/integrace/shoptet`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        { url: `${baseUrl}/integrace/smartsupp`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        // Srovnání
        { url: `${baseUrl}/srovnani`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        { url: `${baseUrl}/srovnani/aishield-vs-excel`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        { url: `${baseUrl}/srovnani/aishield-vs-pravnik`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        { url: `${baseUrl}/srovnani/aishield-vs-manualni-audit`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        // Právní
        { url: `${baseUrl}/gdpr`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.3 },
        { url: `${baseUrl}/privacy`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.3 },
        { url: `${baseUrl}/terms`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.3 },
        { url: `${baseUrl}/cookies`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.3 },
        { url: `${baseUrl}/opakovane-platby`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.3 },
        // Metodika / Report
        { url: `${baseUrl}/metodika`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        { url: `${baseUrl}/report`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.4 },
    ];

    // Blogové články z manifestu
    const blogArticles: MetadataRoute.Sitemap = (manifest as Array<{ href: string; date: string }>).map((article) => ({
        url: `${baseUrl}${article.href}`,
        lastModified: new Date(article.date),
        changeFrequency: "monthly" as const,
        priority: 0.7,
    }));

    return [...staticPages, ...blogArticles];
}
