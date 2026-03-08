/**
 * AIshield.cz — Shoptet Addon API klient
 * Volání Shoptet endpointů z iframe panelu.
 * BEZ Supabase auth — autorizace přes installation_id.
 */

const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").trim();

// ── Typy — Dotazník v2 ──

export interface QuestionnaireRequest {
    uses_ai_chatbot: string;
    chatbot_providers: string[];
    uses_ai_email_auto: string;
    email_providers: string[];
    uses_chatgpt: string;
    chatgpt_providers: string[];
    chatgpt_purposes: string[];
    uses_ai_content: string;
    content_types: string[];
    uses_ai_images: string;
    image_providers: string[];
    uses_dynamic_pricing: string;
    uses_ai_recommendation: string;
    recommendation_providers: string[];
    uses_ai_search: string;
    search_providers: string[];
    uses_ai_decision: string;
    decision_types: string[];
    uses_ai_for_children: string;
    has_ai_training: string;
    informs_employees: string;
    ai_processes_personal_data: string;
    personal_data_types: string[];
    ai_data_stored_eu: string;
    has_ai_guidelines: string;
    has_ai_register: string;
    has_oversight_person: string;
    can_override_ai: string;
    has_transparency_page: string;
    wants_compliance_page: string;
}

export interface QuestionnaireResponse {
    installation_id: string;
    ai_systems_count: number;
    compliance_score: number;
    score_breakdown: Record<string, number>;
    art50_relevant: number;
    art4_relevant: number;
    risk_areas: Array<{
        area: string;
        severity: string;
        description: string;
        deadline?: string;
    }>;
    recommendations: string[];
    plan: string;
    message: string;
}

// ── Typy — Legacy wizard v1 ──

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

// ── Typy — Dashboard ──

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

export interface UpsellInfo {
    url: string;
    discount_code: string;
    discount_percent: number;
    description: string;
    original_price: number;
    price_after_discount: number;
}

export interface DocumentInfo {
    id: string;
    doc_type: string;
    title: string;
    file_size: number;
    generated_at: string;
    download_url: string;
}

export interface DashboardData {
    installation: InstallationInfo;
    ai_systems: AISystemRecord[];
    compliance_score: number;
    score_breakdown: Record<string, number>;
    compliance_page_published: boolean;
    scan_completed: boolean;
    documents: DocumentInfo[];
    art50_deadline: string;
    art4_active_since: string;
    upsell: UpsellInfo;
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

/** Odešle dotazník v2 (20 otázek) */
export async function submitQuestionnaire(
    installationId: string,
    data: QuestionnaireRequest,
): Promise<QuestionnaireResponse> {
    const resp = await shoptetFetch(`/shoptet/questionnaire/${encodeURIComponent(installationId)}`, {
        method: "POST",
        body: JSON.stringify(data),
    });
    if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `Dotazník chyba: ${resp.status}`);
    }
    return resp.json();
}

/** Odešle wizard odpovědi (legacy v1) */
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

/** Spustí re-scan e-shopu + regeneraci dokumentů */
export async function triggerScan(installationId: string): Promise<Record<string, unknown>> {
    const resp = await shoptetFetch(`/shoptet/scan/${encodeURIComponent(installationId)}`, {
        method: "POST",
    });
    if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `Scan selhal: ${resp.status}`);
    }
    return resp.json();
}
