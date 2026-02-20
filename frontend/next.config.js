/** @type {import('next').NextConfig} */
const nextConfig = {
    // Povolíme obrázky z externích zdrojů (screenshoty z Supabase Storage)
    images: {
        remotePatterns: [
            {
                protocol: "https",
                hostname: "rsxwqcrkttlfnqbjgpgc.supabase.co",
                pathname: "/storage/v1/object/public/**",
            },
        ],
    },
    // Environment variables pro klienta
    env: {
        NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
        NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL || "",
        NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "",
    },
    // Security headers
    async headers() {
        return [
            {
                source: "/(.*)",
                headers: [
                    { key: "X-Content-Type-Options", value: "nosniff" },
                    { key: "X-Frame-Options", value: "SAMEORIGIN" },
                    { key: "X-XSS-Protection", value: "1; mode=block" },
                    { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
                    { key: "Permissions-Policy", value: "camera=(), microphone=(self), geolocation=()" },
                ],
            },
        ];
    },
    // Redirect /dotaznik/ursula → /dotaznik/mart1n (keeps query params)
    async redirects() {
        return [
            {
                source: "/dotaznik/ursula",
                destination: "/dotaznik/mart1n",
                permanent: true,
            },
        ];
    },
};

module.exports = nextConfig;
