import type { MetadataRoute } from "next";

/**
 * Robots.txt — povolí crawlování celého webu, odkáže na sitemap.
 */
export default function robots(): MetadataRoute.Robots {
    return {
        rules: [
            {
                userAgent: "*",
                allow: "/",
                disallow: ["/api/", "/_next/"],
            },
        ],
        sitemap: "https://aishield.cz/sitemap.xml",
    };
}
