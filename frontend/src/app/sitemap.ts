import type { MetadataRoute } from "next";
import manifest from "@/data/blog-manifest.json";

/**
 * Dynamická sitemap pro Google Search Console + Bing.
 * Generuje URL pro všechny statické stránky i blogové články.
 */
export default function sitemap(): MetadataRoute.Sitemap {
    const baseUrl = "https://aishield.cz";

    // Statické stránky
    const staticPages: MetadataRoute.Sitemap = [
        { url: baseUrl, lastModified: new Date(), changeFrequency: "weekly", priority: 1.0 },
        { url: `${baseUrl}/scan`, lastModified: new Date(), changeFrequency: "weekly", priority: 0.9 },
        { url: `${baseUrl}/blog`, lastModified: new Date(), changeFrequency: "daily", priority: 0.8 },
        { url: `${baseUrl}/cenik`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.7 },
        { url: `${baseUrl}/kontakt`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.5 },
        { url: `${baseUrl}/ai-act/clanek-50`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.6 },
        { url: `${baseUrl}/ai-act/rizikove-kategorie`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.6 },
        { url: `${baseUrl}/ai-act/checklist`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.6 },
        { url: `${baseUrl}/ai-act/pokuty`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.6 },
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
