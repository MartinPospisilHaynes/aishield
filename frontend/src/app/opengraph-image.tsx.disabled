/* eslint-disable @next/next/no-img-element */
import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "AIshield.cz — AI Act compliance scanner pro české firmy";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function Image() {
    return new ImageResponse(
        (
            <div
                style={{
                    width: "100%",
                    height: "100%",
                    display: "flex",
                    flexDirection: "column",
                    background: "linear-gradient(135deg, #1e1b4b 0%, #0f172a 40%, #164e63 100%)",
                    padding: "60px 80px",
                    fontFamily: "Inter, system-ui, sans-serif",
                    position: "relative",
                    overflow: "hidden",
                }}
            >
                {/* Decorative circles */}
                <div
                    style={{
                        position: "absolute",
                        top: "-100px",
                        right: "-100px",
                        width: "500px",
                        height: "500px",
                        borderRadius: "50%",
                        background: "radial-gradient(circle, rgba(217,70,239,0.15) 0%, transparent 70%)",
                    }}
                />
                <div
                    style={{
                        position: "absolute",
                        bottom: "-150px",
                        left: "-100px",
                        width: "600px",
                        height: "600px",
                        borderRadius: "50%",
                        background: "radial-gradient(circle, rgba(6,182,212,0.12) 0%, transparent 70%)",
                    }}
                />

                {/* Top accent bar */}
                <div
                    style={{
                        position: "absolute",
                        top: 0,
                        left: 0,
                        right: 0,
                        height: "5px",
                        background: "linear-gradient(90deg, #d946ef, #a855f7, #06b6d4)",
                    }}
                />

                {/* Shield + brand */}
                <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
                    <svg width="56" height="56" viewBox="0 0 32 32" fill="none">
                        <path
                            d="M16 1.5C16 1.5 4 6 4 6v10.5c0 4.2 1.8 8.2 4.8 11.1C11.5 30.2 13.9 31.5 16 32c2.1-.5 4.5-1.8 7.2-4.4C26.2 24.7 28 20.7 28 16.5V6L16 1.5z"
                            fill="rgba(217,70,239,0.25)"
                            stroke="url(#sg)"
                            strokeWidth="2"
                            strokeLinejoin="round"
                        />
                        <path
                            d="M12 16.5l3 3 5.5-6.5"
                            stroke="#d946ef"
                            strokeWidth="2.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        />
                        <defs>
                            <linearGradient id="sg" x1="4" y1="2" x2="28" y2="30" gradientUnits="userSpaceOnUse">
                                <stop stopColor="#d946ef" />
                                <stop offset="0.5" stopColor="#a855f7" />
                                <stop offset="1" stopColor="#06b6d4" />
                            </linearGradient>
                        </defs>
                    </svg>
                    <div style={{ display: "flex", fontSize: "32px", fontWeight: 800, letterSpacing: "-0.02em" }}>
                        <span style={{ color: "#ffffff" }}>AI</span>
                        <span style={{ color: "#d946ef" }}>shield</span>
                        <span style={{ color: "#64748b", fontSize: "20px", marginLeft: "4px", alignSelf: "flex-end", paddingBottom: "2px" }}>.cz</span>
                    </div>
                </div>

                {/* Main headline */}
                <div
                    style={{
                        display: "flex",
                        flexDirection: "column",
                        marginTop: "40px",
                        flex: 1,
                    }}
                >
                    <div
                        style={{
                            fontSize: "56px",
                            fontWeight: 800,
                            lineHeight: 1.15,
                            color: "#f1f5f9",
                            maxWidth: "900px",
                        }}
                    >
                        Váš štít proti{" "}
                        <span
                            style={{
                                backgroundImage: "linear-gradient(90deg, #e879f9, #22d3ee)",
                                backgroundClip: "text",
                                color: "transparent",
                            }}
                        >
                            pokutám EU
                        </span>{" "}
                        za AI Act
                    </div>

                    <div
                        style={{
                            fontSize: "24px",
                            color: "#94a3b8",
                            marginTop: "20px",
                            maxWidth: "700px",
                            lineHeight: 1.5,
                        }}
                    >
                        Automatizovaný compliance scanner pro české firmy. Zjistěte za 60 sekund, jestli váš web splňuje zákon.
                    </div>

                    {/* Badge row */}
                    <div style={{ display: "flex", gap: "16px", marginTop: "32px" }}>
                        <div
                            style={{
                                display: "flex",
                                alignItems: "center",
                                gap: "8px",
                                background: "rgba(232,121,249,0.12)",
                                border: "1px solid rgba(232,121,249,0.3)",
                                borderRadius: "24px",
                                padding: "10px 20px",
                                fontSize: "18px",
                                fontWeight: 600,
                                color: "#e879f9",
                            }}
                        >
                            ⚡ Sken za 60 sekund
                        </div>
                        <div
                            style={{
                                display: "flex",
                                alignItems: "center",
                                gap: "8px",
                                background: "rgba(239,68,68,0.12)",
                                border: "1px solid rgba(239,68,68,0.3)",
                                borderRadius: "24px",
                                padding: "10px 20px",
                                fontSize: "18px",
                                fontWeight: 600,
                                color: "#f87171",
                            }}
                        >
                            ⚠️ Pokuta až 35 mil. €
                        </div>
                        <div
                            style={{
                                display: "flex",
                                alignItems: "center",
                                gap: "8px",
                                background: "rgba(34,211,238,0.12)",
                                border: "1px solid rgba(34,211,238,0.3)",
                                borderRadius: "24px",
                                padding: "10px 20px",
                                fontSize: "18px",
                                fontWeight: 600,
                                color: "#22d3ee",
                            }}
                        >
                            📅 Deadline: srpen 2026
                        </div>
                    </div>
                </div>

                {/* Bottom */}
                <div
                    style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        marginTop: "auto",
                    }}
                >
                    <div style={{ fontSize: "18px", color: "#64748b" }}>
                        aishield.cz — Začněte skenovat zdarma
                    </div>
                    <div
                        style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                            background: "linear-gradient(135deg, #d946ef, #a855f7)",
                            borderRadius: "12px",
                            padding: "12px 28px",
                            fontSize: "18px",
                            fontWeight: 700,
                            color: "#ffffff",
                        }}
                    >
                        Skenovat web ZDARMA →
                    </div>
                </div>

                {/* Bottom accent bar */}
                <div
                    style={{
                        position: "absolute",
                        bottom: 0,
                        left: 0,
                        right: 0,
                        height: "5px",
                        background: "linear-gradient(90deg, #06b6d4, #a855f7, #d946ef)",
                    }}
                />
            </div>
        ),
        { ...size }
    );
}
