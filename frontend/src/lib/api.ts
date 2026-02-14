/**
 * AIshield.cz — API klient
 * Volání FastAPI backendu z Next.js frontendu.
 */

import { createClient } from "@/lib/supabase-browser";

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").trim();

// ── Auth helper ──
// Získá access token z Supabase session pro Authorization: Bearer header

async function getAuthToken(): Promise<string | null> {
    try {
        const supabase = createClient();
        const { data } = await supabase.auth.getSession();
        return data.session?.access_token ?? null;
    } catch {
        return null;
    }
}

/**
 * Centrální fetch s automatickým Bearer tokenem.
 * Používejte místo raw fetch() pro chráněné endpointy.
 */
async function authFetch(url: string, options: RequestInit = {}): Promise<Response> {
    const token = await getAuthToken();
    const headers: Record<string, string> = {
        ...(options.headers as Record<string, string> || {}),
    };
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }
    return fetch(url, { ...options, headers });
}

// ── Lightweight logger ──
// Logs API calls in dev + stores last N errors for debug panel

const IS_DEV = process.env.NODE_ENV === "development";
const MAX_LOG_ENTRIES = 50;

interface LogEntry {
    ts: string;
    level: "info" | "warn" | "error";
    msg: string;
    detail?: string;
}

const _logs: LogEntry[] = [];

function apiLog(level: LogEntry["level"], msg: string, detail?: string) {
    const entry: LogEntry = { ts: new Date().toISOString(), level, msg, detail };
    _logs.push(entry);
    if (_logs.length > MAX_LOG_ENTRIES) _logs.shift();

    if (IS_DEV || level === "error") {
        const fn = level === "error" ? console.error : level === "warn" ? console.warn : console.log;
        fn(`[AIshield API] ${msg}`, detail || "");
    }
}

/** Get recent API logs (useful for debug panel) */
export function getApiLogs(): LogEntry[] {
    return [..._logs];
}

/** Clear stored logs */
export function clearApiLogs() {
    _logs.length = 0;
}

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
    company_id: string | null;
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
    confirmed_by_client: string | null;
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
    const endpoint = `${API_URL}/api/scan`;
    apiLog("info", `POST ${endpoint}`, `url=${url}`);

    try {
        const res = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url }),
        });

        if (res.status === 429) {
            // Rate limit — may include cached scan results
            const data = await res.json().catch(() => ({ detail: "Příliš mnoho požadavků" }));
            const msg = data.detail || "Příliš mnoho požadavků. Zkuste to později.";
            apiLog("warn", `POST ${endpoint} → 429 (rate limited)`, msg);

            if (data.cached_scan_id) {
                // Return cached scan as if it was a new scan
                return {
                    scan_id: data.cached_scan_id,
                    company_id: data.cached_company_id || "",
                    url,
                    status: "cached",
                    message: msg,
                };
            }

            throw new Error(msg);
        }

        if (!res.ok) {
            const error = await res.json().catch(() => ({ detail: "Neznámá chyba" }));
            const msg = error.detail || `HTTP ${res.status}`;
            apiLog("error", `POST ${endpoint} → ${res.status}`, msg);
            throw new Error(msg);
        }

        const data = await res.json();
        apiLog("info", `POST ${endpoint} → 200`, `scan_id=${data.scan_id}`);
        return data;
    } catch (err) {
        if (err instanceof TypeError) {
            apiLog("error", `POST ${endpoint} → NETWORK ERROR`, err.message);
            throw new Error(`Nepodařilo se spojit s API (${API_URL}). ${err.message}`);
        }
        throw err;
    }
}

/**
 * Zjistí stav skenu — GET /api/scan/{scan_id}
 */
export async function getScanStatus(scanId: string): Promise<ScanStatus> {
    const endpoint = `${API_URL}/api/scan/${scanId}`;
    apiLog("info", `GET ${endpoint}`);

    try {
        const res = await fetch(endpoint);

        if (!res.ok) {
            const error = await res.json().catch(() => ({ detail: "Neznámá chyba" }));
            const msg = error.detail || `HTTP ${res.status}`;
            apiLog("error", `GET ${endpoint} → ${res.status}`, msg);
            throw new Error(msg);
        }

        const data = await res.json();
        apiLog("info", `GET ${endpoint} → ${data.status}`);
        return data;
    } catch (err) {
        if (err instanceof TypeError) {
            apiLog("error", `GET ${endpoint} → NETWORK ERROR`, err.message);
            throw new Error(`Nepodařilo se spojit s API. ${err.message}`);
        }
        throw err;
    }
}

/**
 * Health check — GET /api/health
 */
export async function checkHealth(): Promise<HealthResponse> {
    const endpoint = `${API_URL}/api/health`;
    apiLog("info", `GET ${endpoint}`);

    try {
        const res = await fetch(endpoint);

        if (!res.ok) {
            apiLog("error", `GET ${endpoint} → ${res.status}`);
            throw new Error(`API nedostupné (HTTP ${res.status})`);
        }

        const data = await res.json();
        apiLog("info", `GET ${endpoint} → OK`, `db=${data.database}`);
        return data;
    } catch (err) {
        if (err instanceof TypeError) {
            apiLog("error", `GET ${endpoint} → NETWORK ERROR`, err.message);
            throw new Error(`API nedostupné. ${err.message}`);
        }
        throw err;
    }
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
    const res = await authFetch(`${API_URL}/api/finding/${findingId}/confirm`, {
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
    const res = await authFetch(`${API_URL}/api/questionnaire/submit`, {
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
    const res = await authFetch(
        `${API_URL}/api/questionnaire/${companyId}/combined-report${params}`
    );

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: "Neznámá chyba" }));
        throw new Error(error.detail || `HTTP ${res.status}`);
    }

    return res.json();
}

// ── Platby (multi-gateway: GoPay, Stripe, Comgate, Bankovní převod) ──

export type PaymentGateway = "gopay" | "stripe" | "comgate" | "bank_transfer";

export interface CheckoutResponse {
    payment_id: string;
    gateway_url: string;
    order_number: string;
    gateway: PaymentGateway;
}

export interface PaymentStatusResponse {
    payment_id: string;
    state: string;
    is_paid: boolean;
    order_number: string;
    gateway?: PaymentGateway;
}

export interface GatewayInfo {
    id: PaymentGateway | string;
    name: string;
    description: string;
    available: boolean;
    default: boolean;
}

/**
 * Vrátí seznam dostupných platebních bran.
 */
export async function getAvailableGateways(): Promise<GatewayInfo[]> {
    const res = await fetch(`${API_URL}/api/payments/gateways`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.gateways || [];
}

/**
 * Vytvoří platbu přes zvolenou bránu a vrátí URL pro přesměrování.
 */
export async function createCheckout(
    plan: string,
    email: string,
    gateway: PaymentGateway = "gopay",
): Promise<CheckoutResponse> {
    const res = await authFetch(`${API_URL}/api/payments/checkout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan, email, gateway }),
    });

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: "Neznámá chyba" }));
        throw new Error(error.detail || `HTTP ${res.status}`);
    }

    return res.json();
}

/**
 * Guest checkout — platba bez přihlášení (pouze coffee).
 */
export async function createGuestCheckout(
    plan: string,
    email?: string,
    gateway: PaymentGateway = "gopay",
): Promise<CheckoutResponse> {
    const res = await fetch(`${API_URL}/api/payments/checkout-guest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan, email: email || "", gateway }),
    });

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: "Neznámá chyba" }));
        throw new Error(error.detail || `HTTP ${res.status}`);
    }

    return res.json();
}

/**
 * Zkontroluje stav platby (multi-gateway).
 */
export async function getPaymentStatus(
    paymentId: string,
    gateway: PaymentGateway = "gopay",
): Promise<PaymentStatusResponse> {
    const res = await fetch(`${API_URL}/api/payments/status/${paymentId}?gateway=${gateway}`);

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: "Neznámá chyba" }));
        throw new Error(error.detail || `HTTP ${res.status}`);
    }

    return res.json();
}

// ── Monitoring Eligibility + Subscription ──

export interface MonitoringEligibility {
    eligible: boolean;
    reason: string;
    checks: {
        has_paid_order: boolean;
        paid_plan: string | null;
        scan_completed: boolean;
        questionnaire_done: boolean;
        documents_generated: boolean;
        has_active_subscription: boolean;
        active_plan: string | null;
        is_enterprise: boolean;
    };
}

/**
 * Zkontroluje, zda uživatel splňuje podmínky pro aktivaci monitoringu.
 */
export async function getMonitoringEligibility(): Promise<MonitoringEligibility> {
    const res = await authFetch(`${API_URL}/api/payments/monitoring-eligibility`);
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: "Neznámá chyba" }));
        throw new Error(error.detail || `HTTP ${res.status}`);
    }
    return res.json();
}

/**
 * Vytvoří monitoring subscription v GoPay a vrátí URL pro přesměrování.
 */
export async function createSubscription(
    plan: string,
    email: string,
): Promise<CheckoutResponse> {
    const res = await authFetch(`${API_URL}/api/payments/subscribe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan, email }),
    });
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: "Neznámá chyba" }));
        throw new Error(error.detail || `HTTP ${res.status}`);
    }
    return res.json();
}

/**
 * Zruší monitoring subscription.
 */
export async function cancelSubscription(subscriptionId: string): Promise<void> {
    const res = await authFetch(`${API_URL}/api/payments/subscribe/cancel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(subscriptionId),
    });
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: "Neznámá chyba" }));
        throw new Error(error.detail || `HTTP ${res.status}`);
    }
}

// ── Dashboard ──

export interface DashboardCompany {
    id: string;
    name: string;
    url: string;
    created_at: string;
}

export interface DashboardScan {
    id: string;
    url: string;
    status: string;
    total_findings: number;
    created_at: string;
    finished_at: string | null;
}

export interface DashboardFinding {
    id: string;
    name: string;
    category: string;
    risk_level: string;
    ai_act_article: string;
    action_required: string;
    confirmed_by_client: string | null;
    status: string;
}

export interface QuestionnaireFinding {
    question_key: string;
    name: string;
    category: string;
    risk_level: string;
    ai_act_article: string;
    action_required: string;
    priority: string;
    source: "questionnaire";
}

export interface QuestionnaireUnknown {
    question_key: string;
    question_text: string;
    risk_level: string;
    ai_act_article: string;
    recommendation: string;
    priority: string;
    severity: "critical" | "high" | "limited" | "minimal";
    severity_color: "red" | "orange" | "yellow" | "gray";
    severity_label: string;
    checklist: string[];
}

export interface QuestionnaireSummary {
    total_answers: number;
    ai_systems_declared: number;
    unknown_count: number;
    risk_breakdown: Record<string, number>;
}

export interface DashboardDocument {
    id: string;
    template_key: string;
    name: string;
    file_url: string;
    created_at: string;
}

export interface DashboardOrder {
    order_number: string;
    plan: string;
    amount: number;
    status: string;
    created_at: string;
    paid_at: string | null;
}

export interface DashboardData {
    company: DashboardCompany | null;
    scans: DashboardScan[];
    findings: DashboardFinding[];
    documents: DashboardDocument[];
    orders: DashboardOrder[];
    questionnaire_status: string;
    questionnaire_findings: QuestionnaireFinding[];
    questionnaire_unknowns: QuestionnaireUnknown[];
    questionnaire_summary: QuestionnaireSummary | null;
    compliance_score: number | null;
}

/**
 * Načte dashboard data pro přihlášeného uživatele.
 */
export async function getDashboardData(
    email: string,
): Promise<DashboardData> {
    const res = await authFetch(`${API_URL}/api/dashboard/${encodeURIComponent(email)}`);

    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: "Neznámá chyba" }));
        throw new Error(error.detail || `HTTP ${res.status}`);
    }

    return res.json();
}

// ── Admin API ──

export interface AdminStats {
    companies_total: number;
    companies_scanned: number;
    emails_today: number;
    emails_total: number;
    orders_paid: number;
    conversion_pct: number;
    recent_logs: Array<{
        id: string;
        task_name: string;
        status: string;
        result: Record<string, unknown> | null;
        error: string | null;
        started_at: string;
    }>;
}

export async function getAdminStats(): Promise<AdminStats> {
    const res = await authFetch(`${API_URL}/api/admin/stats`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

export async function runAdminTask(taskName: string): Promise<Record<string, unknown>> {
    const res = await authFetch(`${API_URL}/api/admin/run/${taskName}`, { method: "POST" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

export async function getAdminEmailLog(limit = 50) {
    const res = await authFetch(`${API_URL}/api/admin/email-log?limit=${limit}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

export async function getAdminCompanies(status = "all", limit = 50) {
    const res = await authFetch(`${API_URL}/api/admin/companies?status=${status}&limit=${limit}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

export interface EmailHealth {
    mode: string;
    adjustment_reason: string;
    days_active: number;
    daily_limit: number;
    sent_today: number;
    remaining_today: number;
    sent_7d: number;
    bounced_7d: number;
    complained_7d: number;
    opened_7d: number;
    bounce_rate: number;
    complaint_rate: number;
    open_rate: number;
    blacklisted_count: number;
    unsubscribed_count: number;
    is_healthy: boolean;
    can_send: boolean;
    warnings: string[];
}

export async function getEmailHealth(): Promise<EmailHealth> {
    const res = await authFetch(`${API_URL}/api/admin/email-health`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

// ── Monitoring / Alerts API ──

export async function getAdminAlerts(limit = 50) {
    const res = await authFetch(`${API_URL}/api/admin/alerts?limit=${limit}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

export async function getAdminDiffs(limit = 20) {
    const res = await authFetch(`${API_URL}/api/admin/diffs?limit=${limit}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

export async function sendLegislativeAlert(title: string, bodyText: string) {
    const res = await authFetch(`${API_URL}/api/admin/legislative-alert`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, body_text: bodyText }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

// ── Agency (Desperados) ──

export interface AgencyClient {
    name: string;
    url: string;
    email?: string;
    contact_name?: string;
    notes?: string;
}

export async function startAgencyBatchScan(clients: AgencyClient[]) {
    const res = await authFetch(`${API_URL}/api/admin/agency/scan-batch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ clients }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

export async function getAgencyBatchStatus(batchId: string) {
    const res = await authFetch(`${API_URL}/api/admin/agency/scan-batch/${batchId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

export async function getAgencyClients() {
    const res = await authFetch(`${API_URL}/api/admin/agency/clients`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

export async function generateAgencyEmail(data: {
    client_name: string;
    contact_name: string;
    url: string;
    email: string;
    findings_count?: number;
    scan_id?: string;
}) {
    const res = await authFetch(`${API_URL}/api/admin/agency/generate-email`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

// ── Questionnaire Progress ──

export interface QuestionnaireProgress {
    company_id: string;
    total_questions: number;
    answered: number;
    unknown_count: number;
    percentage: number;
    status: "nezahajeno" | "rozpracovano" | "dokonceno";
}

export async function getQuestionnaireProgress(companyId: string): Promise<QuestionnaireProgress> {
    apiLog("info", "getQuestionnaireProgress", companyId);
    const res = await authFetch(`${API_URL}/api/questionnaire/${companyId}/progress`);
    if (!res.ok) {
        const text = await res.text().catch(() => "");
        apiLog("error", `getQuestionnaireProgress failed: ${res.status}`, text);
        throw new Error(`HTTP ${res.status}`);
    }
    return res.json();
}
