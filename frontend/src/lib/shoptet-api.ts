/**
 * AIshield.cz — Shoptet Addon API klient
 * Volání Shoptet endpointů z iframe panelu.
 * BEZ Supabase auth — autorizace přes installation_id.
 */

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").trim();

// ── Typy ──

export interface AISystemEntry {
    provider: string;
    ai_type: "chatbot" | "recommendation" | "content" | "pricing" | "search" | "other";
    custom_note: string;
}

export interface WizardRequest {
    chatbots: AISystemEntry[];
    content_ai: AISystemEntry[];
    other_ai: AISystemEntry[];
}

export interface WizardResponse {
    installation_id: string;
    ai_systems_count: number;
    compliance_score: number;
    art50_relevant: number;
    art4_relevant: number;
    compliance_page_url: string | null;
    message: string;
}

export interface AISystemRecord {
    id: string;
    installation_id: string;
    source: string;
    provider: string;
    ai_type: string;
    ai_act_article: string;
    risk_level: string;
    confidence: string;
    is_active: boolean;
    details: Record<string, string>;
}

export interface InstallationInfo {
    id: string;
    eshop_id: number;
    eshop_url: string | null;
    eshop_name: string | null;
    language: string;
    plan: string;
    status: string;
    wizard_completed_at: string | null;
    installed_at: string;
}

export interface DashboardData {
    installation: InstallationInfo;
    ai_systems: AISystemRecord[];
    compliance_score: number;
    compliance_page_published: boolean;
    documents: Record<string, unknown>[];
    art50_deadline: string;
    art4_active_since: string;
}

// ── API funkce ──

async function shoptetFetch(path: string, options: RequestInit = {}): Promise<Response> {
    const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...(options.headers as Record<string, string> || {}),
    };
    return fetch(`${API_URL}${path}`, { ...options, headers });
}

/** Načte dashboard data pro instalaci */
export async function getDashboard(installationId: string): Promise<DashboardData> {
    const resp = await shoptetFetch(`/shoptet/dashboard/${encodeURIComponent(installationId)}`);
    if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `Dashboard chyba: ${resp.status}`);
    }
    return resp.json();
}

/** Odešle wizard odpovědi */
export async function submitWizard(installationId: string, data: WizardRequest): Promise<WizardResponse> {
    const resp = await shoptetFetch(`/shoptet/wizard/${encodeURIComponent(installationId)}`, {
        method: "POST",
        body: JSON.stringify(data),
    });
    if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `Wizard chyba: ${resp.status}`);
    }
    return resp.json();
}

/** Publikuje compliance stránku na eshop */
export async function publishCompliancePage(installationId: string): Promise<Record<string, unknown>> {
    const resp = await shoptetFetch(`/shoptet/compliance-page/${encodeURIComponent(installationId)}`, {
        method: "POST",
    });
    if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `Publikace stránky selhala: ${resp.status}`);
    }
    return resp.json();
}
