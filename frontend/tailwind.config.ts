import type { Config } from "tailwindcss";

const config: Config = {
    content: [
        "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        screens: {
            xs: "375px",
            sm: "640px",
            md: "768px",
            lg: "1024px",
            xl: "1280px",
            "2xl": "1536px",
        },
        extend: {
            colors: {
                // Dark neon glassmorphism palette (desperados-design.cz style)
                dark: {
                    950: "#030712",
                    900: "#0f172a",
                    800: "#1e293b",
                    700: "#334155",
                    600: "#475569",
                },
                neon: {
                    fuchsia: "#e879f9",
                    cyan: "#22d3ee",
                    purple: "#a855f7",
                    pink: "#ec4899",
                },
                // Zachování shield pro kompatibilitu
                shield: {
                    50: "#fdf4ff",
                    100: "#fae8ff",
                    200: "#f5d0fe",
                    300: "#e879f9",
                    400: "#e879f9",
                    500: "#d946ef",
                    600: "#c026d3",
                    700: "#a21caf",
                    800: "#86198f",
                    900: "#701a75",
                    950: "#4a044e",
                },
                danger: {
                    500: "#ef4444",
                    600: "#dc2626",
                },
                success: {
                    500: "#22c55e",
                    600: "#16a34a",
                },
                warning: {
                    500: "#f59e0b",
                    600: "#d97706",
                },
            },
            fontFamily: {
                sans: ["Inter", "system-ui", "sans-serif"],
            },
            backgroundImage: {
                "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
                "neon-glow":
                    "linear-gradient(135deg, rgba(232,121,249,0.15), rgba(34,211,238,0.15))",
            },
            boxShadow: {
                neon: "0 0 20px rgba(232,121,249,0.15), 0 0 60px rgba(34,211,238,0.08)",
                "neon-strong":
                    "0 0 30px rgba(232,121,249,0.25), 0 0 80px rgba(34,211,238,0.15)",
            },
        },
    },
    plugins: [],
};

export default config;
