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

export interface Finding {
    id: string;
    name: string;
    category: string;
    risk_level: string;
    ai_act_article: string;
    action_required: string;
    ai_classification_text: string | null;
    evidence_html: string | null;
    signature_matched: string | null;
    confirmed_by_client: boolean | null;
    source: string;
    created_at: string;
}

export interface FindingsResponse {
    findings: Finding[];
    false_positives: Finding[];
    count: number;
    fp_count: number;
    ai_classified: boolean;
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

/**
 * Načte nálezy (findings) pro daný sken — GET /api/scan/{scan_id}/findings
 */
export async function getScanFindings(scanId: string): Promise<FindingsResponse> {
    const res = await fetch(`${API_URL}/api/scan/${scanId}/findings`);

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: "Neznámá chyba" }));
        throw new Error(error.detail || `HTTP ${res.status}`);
    }

    return res.json();
}

/**
 * Potvrdí nebo zamítne nález — PATCH /api/finding/{finding_id}/confirm
 */
export async function confirmFinding(
    findingId: string,
    confirmed: boolean,
    note: string = ""
): Promise<{ finding_id: string; confirmed_by_client: string; message: string }> {
    const res = await fetch(`${API_URL}/api/finding/${findingId}/confirm`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirmed, note }),
    });

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: "Neznámá chyba" }));
        throw new Error(error.detail || `HTTP ${res.status}`);
    }

    return res.json();
}

// ── Questionnaire API ──

export interface QuestionnaireAnswer {
    question_key: string;
    section: string;
    answer: string;
    details: Record<string, string> | null;
    tool_name: string | null;
}

export interface QuestionnaireSubmission {
    company_id: string;
    scan_id?: string;
    answers: QuestionnaireAnswer[];
}

export interface QuestionnaireResult {
    status: string;
    saved_count: number;
    analysis: {
        total_answers: number;
        ai_systems_declared: number;
        risk_breakdown: Record<string, number>;
        recommendations: Array<{
            question_key: string;
            tool_name: string;
            risk_level: string;
            ai_act_article: string;
            recommendation: string;
            priority: string;
        }>;
    };
}

/**
 * Odešle vyplněný dotazník — POST /api/questionnaire/submit
 */
export async function submitQuestionnaire(
    submission: QuestionnaireSubmission
): Promise<QuestionnaireResult> {
    const res = await fetch(`${API_URL}/api/questionnaire/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(submission),
    });

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: "Neznámá chyba" }));
        throw new Error(error.detail || `HTTP ${res.status}`);
    }

    return res.json();
}

/**
 * Načte kombinovaný report — GET /api/questionnaire/{company_id}/combined-report
 */
export async function getCombinedReport(
    companyId: string,
    scanId?: string
): Promise<any> {
    const params = scanId ? `?scan_id=${scanId}` : "";
    const res = await fetch(
        `${API_URL}/api/questionnaire/${companyId}/combined-report${params}`
    );

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: "Neznámá chyba" }));
        throw new Error(error.detail || `HTTP ${res.status}`);
    }

    return res.json();
}
