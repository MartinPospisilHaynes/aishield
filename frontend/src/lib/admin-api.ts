const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").trim();

// ── Admin Auth ──

function getAdminToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("admin_token");
}

export function setAdminToken(token: string) {
    localStorage.setItem("admin_token", token);
}

export function clearAdminToken() {
    localStorage.removeItem("admin_token");
}

export function isAdminLoggedIn(): boolean {
    return !!getAdminToken();
}

/** Ověří token proti backendu — vrátí true pokud je platný */
export async function verifyAdminToken(): Promise<boolean> {
    const token = getAdminToken();
    if (!token) return false;
    try {
        const res = await adminFetch(`${API_URL}/api/admin/crm/verify`);
        if (!res.ok) {
            clearAdminToken();
            return false;
        }
        return true;
    } catch {
        return false;
    }
}

// Helper for admin-authenticated requests
// Sends X-Admin-Token header for CRM authentication (no Supabase needed)
async function adminFetch(url: string, options: RequestInit = {}): Promise<Response> {
    const token = getAdminToken();
    const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...(options.headers as Record<string, string> || {}),
    };
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
        headers["X-Admin-Token"] = token;
    }
    return fetch(url, { ...options, headers });
}

// ── Types ──

export interface CrmDashboardStats {
    companies: {
        total: number;
        by_workflow_status: Record<string, number>;
    };
    emails: {
        total: number;
        today: number;
        this_week: number;
        open_rate: number;
        click_rate: number;
    };
    scans: {
        total: number;
        today: number;
        this_week: number;
    };
    questionnaires: { total: number };
    orders: {
        total: number;
        paid_amount: number;
    };
    needing_attention: CompanyBrief[];
    recent_activity: Activity[];
}

export interface CompanyBrief {
    id: string;
    name: string;
    url: string;
    email: string;
    workflow_status: string;
    next_action?: string;
    next_action_at?: string;
}

export interface CompanyDetail {
    company: CompanyFull;
    latest_scan: ScanInfo | null;
    findings_count: number;
    email_log: EmailLogEntry[];
    questionnaire_count: number;
    orders: OrderEntry[];
    activities: Activity[];
}

export interface CompanyFull {
    id: string;
    ico: string;
    name: string;
    url: string;
    email: string;
    phone: string;
    contact_name: string;
    nace_code: string;
    address: string;
    employee_count: number;
    source: string;
    scan_status: string;
    workflow_status: string;
    payment_status: string;
    priority: string;
    assigned_to: string;
    next_action: string;
    next_action_at: string;
    last_contact_at: string;
    lead_score: number;
    lead_tier: string;
    partner: string;
    partner_notes: string;
    notes: string;
    emails_sent: number;
    last_email_at: string;
    total_findings: number;
    created_at: string;
    updated_at: string;
}

export interface ScanInfo {
    id: string;
    url_scanned: string;
    status: string;
    started_at: string;
    finished_at: string;
    duration_seconds: number;
    total_findings: number;
    created_at: string;
}

export interface EmailLogEntry {
    id: string;
    to_email: string;
    subject: string;
    variant: string;
    status: string;
    sent_at: string;
    opened_at: string | null;
    clicked_at: string | null;
}

export interface OrderEntry {
    id: string;
    order_number: string;
    plan: string;
    amount: number;
    status: string;
    paid_at: string | null;
    created_at: string;
}

export interface Activity {
    id: string;
    company_id: string;
    actor: string;
    activity_type: string;
    title: string;
    description: string;
    metadata: Record<string, unknown>;
    created_at: string;
}

export interface PipelineStats {
    total_companies: number;
    by_workflow_status: Record<string, number>;
    by_payment_status: Record<string, number>;
    by_priority: Record<string, number>;
    revenue: {
        total_orders: number;
        paid_amount: number;
        pending_amount: number;
    };
}

// ── Status definitions ──

export const WORKFLOW_STATUSES: Record<string, { label: string; color: string; icon: string }> = {
    new: { label: "Nový", color: "gray", icon: "🆕" },
    contacted: { label: "Kontaktován", color: "blue", icon: "📧" },
    waiting_questionnaire: { label: "Čeká na dotazník", color: "yellow", icon: "📝" },
    questionnaire_received: { label: "Dotazník přijat", color: "cyan", icon: "✅" },
    processing: { label: "Zpracovávám", color: "purple", icon: "⚙️" },
    documents_sent: { label: "Dokumenty odeslány", color: "indigo", icon: "📄" },
    active_client: { label: "Aktivní klient", color: "green", icon: "🤝" },
    churned: { label: "Odešel", color: "red", icon: "👋" },
    not_interested: { label: "Nezájem", color: "gray", icon: "❌" },
    follow_up: { label: "Follow-up", color: "orange", icon: "🔔" },
};

export const PAYMENT_STATUSES: Record<string, { label: string; color: string; icon: string }> = {
    none: { label: "Bez platby", color: "gray", icon: "—" },
    pending: { label: "Čeká na platbu", color: "yellow", icon: "⏳" },
    paid: { label: "Zaplaceno", color: "green", icon: "💰" },
    overdue: { label: "Po splatnosti", color: "red", icon: "🚨" },
    refunded: { label: "Vráceno", color: "orange", icon: "↩️" },
    free_trial: { label: "Zkušební", color: "cyan", icon: "🎁" },
};

export const PRIORITIES: Record<string, { label: string; color: string; icon: string }> = {
    low: { label: "Nízká", color: "gray", icon: "⬇️" },
    normal: { label: "Normální", color: "blue", icon: "➡️" },
    high: { label: "Vysoká", color: "orange", icon: "⬆️" },
    urgent: { label: "Urgentní", color: "red", icon: "🔥" },
};

// ── API functions ──

export async function adminLogin(username: string, password: string, website?: string): Promise<{ token: string }> {
    const res = await fetch(`${API_URL}/api/admin/crm/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password, ...(website ? { website } : {}) }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Chyba přihlášení" }));
        throw new Error(err.detail || "Chyba přihlášení");
    }
    const data = await res.json();
    setAdminToken(data.token);
    return data;
}

export async function getCrmDashboardStats(): Promise<CrmDashboardStats> {
    const res = await adminFetch(`${API_URL}/api/admin/crm/dashboard-stats`);
    if (!res.ok) throw new Error("Nepodařilo se načíst statistiky");
    return res.json();
}

export async function getCrmPipeline(): Promise<PipelineStats> {
    const res = await adminFetch(`${API_URL}/api/admin/crm/pipeline`);
    if (!res.ok) throw new Error("Nepodařilo se načíst pipeline");
    return res.json();
}

export async function getCrmCompanyDetail(companyId: string): Promise<CompanyDetail> {
    const res = await adminFetch(`${API_URL}/api/admin/crm/company/${companyId}`);
    if (!res.ok) throw new Error("Firma nenalezena");
    return res.json();
}

export async function updateCompanyStatus(companyId: string, data: {
    workflow_status?: string;
    payment_status?: string;
    priority?: string;
    next_action?: string;
    next_action_at?: string;
    assigned_to?: string;
}): Promise<unknown> {
    const res = await adminFetch(`${API_URL}/api/admin/crm/company/${companyId}/status`, {
        method: "PATCH",
        body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Nepodařilo se aktualizovat status");
    return res.json();
}

export async function addCompanyNote(companyId: string, data: {
    activity_type?: string;
    title: string;
    description?: string;
}): Promise<unknown> {
    const res = await adminFetch(`${API_URL}/api/admin/crm/company/${companyId}/note`, {
        method: "POST",
        body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Nepodařilo se přidat poznámku");
    return res.json();
}

export async function getCompanyTimeline(companyId: string): Promise<{ activities: Activity[] }> {
    const res = await adminFetch(`${API_URL}/api/admin/crm/company/${companyId}/timeline`);
    if (!res.ok) throw new Error("Nepodařilo se načíst timeline");
    return res.json();
}

// ── Admin functions (using adminFetch for CRM token auth) ──

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
    const res = await adminFetch(`${API_URL}/api/admin/stats`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

export async function runAdminTask(taskName: string): Promise<Record<string, unknown>> {
    const res = await adminFetch(`${API_URL}/api/admin/run/${taskName}`, { method: "POST" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

export async function getAdminEmailLog(limit = 50) {
    const res = await adminFetch(`${API_URL}/api/admin/email-log?limit=${limit}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

export async function getAdminCompanies(status = "all", limit = 50) {
    const res = await adminFetch(`${API_URL}/api/admin/companies?status=${status}&limit=${limit}`);
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
    const res = await adminFetch(`${API_URL}/api/admin/email-health`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

export async function getAdminAlerts(limit = 50) {
    const res = await adminFetch(`${API_URL}/api/admin/alerts?limit=${limit}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

export async function getAdminDiffs(limit = 20) {
    const res = await adminFetch(`${API_URL}/api/admin/diffs?limit=${limit}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

export async function sendLegislativeAlert(title: string, bodyText: string) {
    const res = await adminFetch(`${API_URL}/api/admin/legislative-alert`, {
        method: "POST",
        body: JSON.stringify({ title, body_text: bodyText }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

export interface AgencyClient {
    name: string;
    url: string;
    email?: string;
    contact_name?: string;
    notes?: string;
}

export async function startAgencyBatchScan(clients: AgencyClient[]) {
    const res = await adminFetch(`${API_URL}/api/admin/agency/scan-batch`, {
        method: "POST",
        body: JSON.stringify({ clients }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

export async function getAgencyClients() {
    const res = await adminFetch(`${API_URL}/api/admin/agency/clients`);
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
    const res = await adminFetch(`${API_URL}/api/admin/agency/generate-email`, {
        method: "POST",
        body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

// ── Client Detail: Questionnaire + Findings ──

export interface QuestionnaireResponse {
    question_key: string;
    answer: string;
    details: Record<string, string> | null;
    tool_name: string | null;
    submitted_at: string;
}

export interface ClientQuestionnaireData {
    client_id: string;
    total_responses: number;
    sections: Record<string, QuestionnaireResponse[]>;
    responses: Record<string, unknown>[];
}

export async function getClientQuestionnaire(email: string): Promise<ClientQuestionnaireData> {
    const res = await adminFetch(`${API_URL}/api/admin/crm/client/${encodeURIComponent(email)}/questionnaire`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

export interface FindingDetail {
    id: string;
    name: string;
    category: string;
    risk_level: string;
    ai_act_article: string;
    action_required: string;
    ai_classification_text: string;
    evidence_html: string;
    status: string;
    source: string;
    created_at: string;
}

export interface ClientFindingsData {
    company_id: string;
    company_name: string;
    total: number;
    findings: FindingDetail[];
}

export async function getClientFindings(email: string): Promise<ClientFindingsData> {
    const res = await adminFetch(`${API_URL}/api/admin/crm/client/${encodeURIComponent(email)}/findings`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

// ── Client Management types ──

export interface ClientOrder {
    id: string;
    order_number: string;
    plan: string;
    amount: number;
    status: string;
    order_type: string;
    paid_at: string | null;
    created_at: string;
}

export interface ClientSubscription {
    id: string;
    plan: string;
    amount: number;
    status: string;
    cycle: string;
    last_charged_at: string | null;
    next_charge_at: string | null;
    total_charged: number;
    activated_at: string | null;
    payment_ok: boolean;
}

export interface ClientScanDiff {
    has_changes: boolean;
    added: number;
    removed: number;
    changed: number;
    summary: string;
    created_at: string;
}

export interface ClientScanInfo {
    id: string;
    status: string;
    total_findings: number;
    created_at: string;
    finished_at: string | null;
    url_scanned: string;
}

export interface ManagedClient {
    email: string;
    company_name: string;
    company_id: string | null;
    company_url: string;
    plan: string | null;
    orders: ClientOrder[];
    subscription: ClientSubscription | null;
    last_scan: ClientScanInfo | null;
    scan_age_days: number | null;
    documents_count: number;
    documents_last_at: string | null;
    questionnaire_done: boolean;
    last_diff: ClientScanDiff | null;
    fulfillment: "ok" | "no_scan" | "needs_rescan" | "needs_documents";
    needs_rescan: boolean;
}

export interface ClientManagementSummary {
    total_clients: number;
    total_revenue: number;
    active_subscriptions: number;
    overdue_subscriptions: number;
    needs_rescan: number;
}

export interface ClientManagementData {
    clients: ManagedClient[];
    summary: ClientManagementSummary;
}

export interface RescanResult {
    status: string;
    email: string;
    company_name: string;
    scan_id: string;
    changes_detected: boolean;
    added_count: number;
    removed_count: number;
    documents_regenerated: boolean;
    email_sent: boolean;
}

// ── Client Management API ──

export async function getClientManagement(): Promise<ClientManagementData> {
    const res = await adminFetch(`${API_URL}/api/admin/crm/client-management`);
    if (!res.ok) throw new Error("Nepodařilo se načíst správu klientů");
    return res.json();
}

export async function triggerClientRescan(email: string): Promise<RescanResult> {
    const res = await adminFetch(`${API_URL}/api/admin/crm/client/${encodeURIComponent(email)}/rescan`, {
        method: "POST",
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Chyba při rescanu" }));
        throw new Error(err.detail || "Chyba při rescanu");
    }
    return res.json();
}

// ── Business Overview Types ──

export interface RevenueChart {
    date: string;
    amount: number;
}

export interface OrderBreakdown {
    total: number;
    paid: number;
    pending: number;
    canceled: number;
    refunded: number;
}

export interface PlanBreakdown {
    [plan: string]: { count: number; paid: number; revenue: number };
}

export interface DetailedOrder {
    id: string;
    order_number: string;
    plan: string;
    amount: number;
    email: string;
    company_name: string;
    status: string;
    order_type: string;
    gopay_payment_id: string;
    created_at: string;
    paid_at: string | null;
    days_since_order: number;
    days_since_payment: number;
    fulfillment: "delivered" | "pending" | "not_paid" | "subscription";
    deadline_status: "ok" | "warning" | "overdue" | "n/a";
    days_remaining: number | null;
    docs_count: number;
    has_scan: boolean;
    refund_amount: number | null;
    refunded_at: string | null;
}

export interface FulfillmentSummary {
    delivered: number;
    pending: number;
    overdue: number;
    warning: number;
    not_paid: number;
}

export interface ConversionFunnel {
    total_companies: number;
    scanned: number;
    questionnaire_filled: number;
    ordered: number;
    paid: number;
    documents_delivered: number;
}

export interface OutreachStats {
    total_in_database: number;
    emailed: number;
    emails_sent_total: number;
    emails_delivered: number;
    emails_opened: number;
    emails_clicked: number;
    emails_bounced: number;
    unique_recipients: number;
    registered_from_outreach: number;
    purchased_from_outreach: number;
    open_rate: number;
    click_rate: number;
}

export interface SubscriptionSummary {
    total: number;
    active: number;
    cancelled: number;
    monthly_recurring_revenue: number;
    total_charged: number;
}

export interface ScanSummary {
    total: number;
    done: number;
    error: number;
    by_trigger: Record<string, number>;
}

export interface RecentEvent {
    type: "order" | "subscription";
    date: string;
    email: string;
    detail: string;
    status: string;
}

export interface HealthMetrics {
    active_customers: number;
    churn_rate: number;
    cancelled_last_30d: number;
}

export interface BusinessOverview {
    generated_at: string;
    revenue: {
        total: number;
        pending: number;
        refunded: number;
        this_month: number;
        chart: RevenueChart[];
    };
    orders: {
        breakdown: OrderBreakdown;
        by_plan: PlanBreakdown;
        by_type: PlanBreakdown;
        detailed: DetailedOrder[];
    };
    subscriptions: SubscriptionSummary;
    health: HealthMetrics;
    funnel: ConversionFunnel;
    fulfillment: FulfillmentSummary;
    outreach: OutreachStats;
    scans: ScanSummary;
    recent_events: RecentEvent[];
}

// ── Business Overview API ──

export async function getBusinessOverview(): Promise<BusinessOverview> {
    const res = await adminFetch(`${API_URL}/api/admin/crm/business-overview`);
    if (!res.ok) throw new Error("Nepodařilo se načíst obchodní přehled");
    return res.json();
}

// ── Admin Orders (all gateways) ──

export interface AdminOrder {
    id: string;
    order_number: string;
    email: string;
    plan: string;
    amount: number;
    currency: string;
    status: string;
    payment_gateway: string;
    variable_symbol?: string;
    created_at: string;
    paid_at?: string;
}

export interface AdminOrderStats {
    total_orders: number;
    total_revenue: number;
    awaiting_payment: AdminOrder[];
    by_gateway: Record<string, { count: number; revenue: number }>;
}

export async function getAdminOrders(status?: string, gateway?: string): Promise<AdminOrder[]> {
    const params = new URLSearchParams();
    if (status) params.set("status", status);
    if (gateway) params.set("gateway", gateway);
    const res = await adminFetch(`${API_URL}/api/payments/admin/orders?${params}`);
    if (!res.ok) throw new Error("Nepodařilo se načíst objednávky");
    const data = await res.json();
    return data.orders || [];
}

export async function getAdminOrderStats(): Promise<AdminOrderStats> {
    const res = await adminFetch(`${API_URL}/api/payments/admin/orders/stats`);
    if (!res.ok) throw new Error("Nepodařilo se načíst statistiky objednávek");
    return res.json();
}

export async function confirmBankPayment(orderNumber: string): Promise<{ status: string; order_number: string; invoice_sent?: boolean; invoice_number?: string }> {
    const res = await adminFetch(`${API_URL}/api/payments/admin/orders/confirm-payment`, {
        method: "POST",
        body: JSON.stringify({ order_number: orderNumber }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Chyba při potvrzení platby" }));
        throw new Error(err.detail || "Chyba při potvrzení platby");
    }
    return res.json();
}

// ── Analytics ──

export interface AnalyticsStats {
    total_events: number;
    unique_sessions: number;
    funnel: Record<string, number>;
    top_pages: { page: string; views: number }[];
    daily: { date: string; count: number }[];
    event_types: Record<string, number>;
    questionnaire: {
        avg_time_per_question: Record<string, number>;
        changes_per_question: Record<string, number>;
        total_nevim_answers: number;
    };
}

export interface AnalyticsSession {
    session_id: string;
    device: string;
    browser: string;
    os: string;
    first_seen: string;
    last_seen: string;
    user_email: string | null;
    pages: string[];
    page_count: number;
    event_count: number;
}

export interface AnalyticsEvent {
    id: string;
    session_id: string;
    event_name: string;
    properties: Record<string, unknown>;
    page_url: string;
    referrer: string;
    user_email: string | null;
    device: string;
    browser: string;
    os: string;
    duration_ms: number | null;
    created_at: string;
}

export async function getAnalyticsStats(days: number = 30): Promise<AnalyticsStats> {
    const res = await adminFetch(`${API_URL}/api/analytics/stats?days=${days}`);
    if (!res.ok) throw new Error("Chyba při načítání analytiky");
    return res.json();
}

export async function getAnalyticsSessions(limit: number = 50): Promise<{ sessions: AnalyticsSession[]; total: number }> {
    const res = await adminFetch(`${API_URL}/api/analytics/sessions?limit=${limit}`);
    if (!res.ok) throw new Error("Chyba při načítání sessions");
    return res.json();
}

export async function getAnalyticsEvents(limit: number = 100, eventName?: string): Promise<{ events: AnalyticsEvent[]; count: number }> {
    let url = `${API_URL}/api/analytics/events?limit=${limit}`;
    if (eventName) url += `&event_name=${encodeURIComponent(eventName)}`;
    const res = await adminFetch(url);
    if (!res.ok) throw new Error("Chyba při načítání eventů");
    return res.json();
}

// ── Subscriptions ──

export interface SubscriptionInfo {
    id: string;
    company_id: string;
    company_name: string;
    company_email: string;
    plan: string;
    amount: number;
    currency: string;
    status: string;
    started_at: string;
    next_payment_date: string | null;
    last_payment_at: string | null;
    days_overdue: number;
    reminder_sent: boolean;
}

export async function getSubscriptions(): Promise<{ subscriptions: SubscriptionInfo[] }> {
    const res = await adminFetch(`${API_URL}/api/admin/crm/subscriptions`);
    if (!res.ok) throw new Error("Chyba při načítání předplatných");
    return res.json();
}

export async function sendSubscriptionReminder(subscriptionId: string): Promise<{ status: string }> {
    const res = await adminFetch(`${API_URL}/api/admin/crm/subscriptions/${subscriptionId}/reminder`, {
        method: "POST",
    });
    if (!res.ok) throw new Error("Chyba při odesílání upomínky");
    return res.json();
}

// ── Invoices ──

export interface AdminInvoice {
    id: string;
    invoice_number: string;
    order_number: string;
    company_id: string | null;
    email: string;
    plan: string;
    amount: number;
    buyer_name: string;
    buyer_ico: string;
    pdf_url: string;
    pdf_filename: string;
    issued_at: string;
    created_at: string;
}

export async function getAdminInvoices(): Promise<{ invoices: AdminInvoice[] }> {
    const res = await adminFetch(`${API_URL}/api/admin/invoices`);
    if (!res.ok) throw new Error("Chyba při načítání faktur");
    return res.json();
}

// ── Factory Reset ──

export async function factoryReset(confirm: string): Promise<{
    status: string;
    message: string;
    results: {
        auth: string;
        db: { tables: number; deleted: string | string[]; verification: string } | string;
        storage: string;
        errors: string[];
    };
}> {
    const res = await adminFetch(`${API_URL}/api/admin/crm/factory-reset`, {
        method: "POST",
        body: JSON.stringify({ confirm }),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Neznámá chyba" }));
        throw new Error(err.detail || "Chyba při factory resetu");
    }
    return res.json();
}
