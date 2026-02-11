"use client";

export default function ScanError({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    return (
        <div className="min-h-screen flex items-center justify-center px-6">
            <div className="max-w-lg w-full bg-white/[0.04] border border-white/10 rounded-2xl p-8 text-center">
                <h2 className="text-xl font-bold text-red-400 mb-4">Nastala chyba</h2>
                <p className="text-sm text-slate-400 mb-2">
                    {error.message || "Neznámá chyba"}
                </p>
                {error.digest && (
                    <p className="text-xs text-slate-600 mb-4">Digest: {error.digest}</p>
                )}
                <pre className="text-xs text-left text-slate-500 bg-black/30 rounded-lg p-4 mb-6 overflow-auto max-h-48">
                    {error.stack || error.toString()}
                </pre>
                <button
                    onClick={reset}
                    className="btn-primary px-6 py-2.5 text-sm"
                >
                    Zkusit znovu
                </button>
            </div>
        </div>
    );
}
