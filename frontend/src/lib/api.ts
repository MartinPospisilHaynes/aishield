/**
 * AIshield.cz — API klient
 * Volání FastAPI backendu z Next.js frontendu.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Typy ──

export interface ScanResponse {
    scan_id: string;
    company_id: string;
    url: string;
    status: string;
    message: string;
}

export interface ScanStatus {
    scan_id: string;
    url: string;
    status: string;
    total_findings: number;
    started_at: string | null;
    finished_at: string | null;
    company_name: string | null;
}

export interface HealthResponse {
    status: string;
    api: string;
    database: string;
    database_message: string;
    timestamp: string;
    version: string;
}

// ── API funkce ──

/**
 * Spustí nový sken webu — POST /api/scan
 */
export async function startScan(url: string): Promise<ScanResponse> {
    const res = await fetch(`${API_URL}/api/scan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
    });

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: "Neznámá chyba" }));
        throw new Error(error.detail || `HTTP ${res.status}`);
    }

    return res.json();
}

/**
 * Zjistí stav skenu — GET /api/scan/{scan_id}
 */
export async function getScanStatus(scanId: string): Promise<ScanStatus> {
    const res = await fetch(`${API_URL}/api/scan/${scanId}`);

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: "Neznámá chyba" }));
        throw new Error(error.detail || `HTTP ${res.status}`);
    }

    return res.json();
}

/**
 * Health check — GET /api/health
 */
export async function checkHealth(): Promise<HealthResponse> {
    const res = await fetch(`${API_URL}/api/health`);

    if (!res.ok) {
        throw new Error(`API nedostupné (HTTP ${res.status})`);
    }

    return res.json();
}
