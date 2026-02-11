"use client";

export default function GlobalError({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    return (
        <html lang="cs">
            <body style={{ background: "#0f0f14", color: "#e2e8f0", fontFamily: "system-ui, sans-serif" }}>
                <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: "1.5rem" }}>
                    <div style={{ maxWidth: "28rem", width: "100%", textAlign: "center", background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "1rem", padding: "2rem" }}>
                        <h2 style={{ fontSize: "1.25rem", fontWeight: "bold", color: "#f87171", marginBottom: "1rem" }}>
                            Nastala chyba
                        </h2>
                        <p style={{ fontSize: "0.875rem", color: "#94a3b8", marginBottom: "1.5rem" }}>
                            {error.message || "Neočekávaná chyba aplikace"}
                        </p>
                        <div style={{ display: "flex", gap: "0.75rem", justifyContent: "center" }}>
                            <button
                                onClick={reset}
                                style={{ background: "#a855f7", color: "white", padding: "0.625rem 1.5rem", borderRadius: "0.75rem", border: "none", cursor: "pointer", fontWeight: 500 }}
                            >
                                Zkusit znovu
                            </button>
                            <button
                                onClick={() => window.location.reload()}
                                style={{ background: "rgba(255,255,255,0.1)", color: "#e2e8f0", padding: "0.625rem 1.5rem", borderRadius: "0.75rem", border: "1px solid rgba(255,255,255,0.1)", cursor: "pointer", fontWeight: 500 }}
                            >
                                Obnovit stránku
                            </button>
                        </div>
                    </div>
                </div>
            </body>
        </html>
    );
}
