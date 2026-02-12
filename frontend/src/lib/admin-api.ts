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

// Helper for admin-authenticated requests
// Uses the Supabase auth token from the regular auth system (the admin user must be in ADMIN_EMAILS)
// Also adds X-Admin-Token header for the CRM login endpoint
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
  // Also try to get Supabase session token since backend's require_admin checks Supabase auth
  try {
    const { createClient } = await import("@/lib/supabase-browser");
    const supabase = createClient();
    const { data } = await supabase.auth.getSession();
    if (data.session?.access_token) {
      headers["Authorization"] = `Bearer ${data.session.access_token}`;
    }
  } catch {}
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

export async function adminLogin(username: string, password: string): Promise<{ token: string }> {
  const res = await fetch(`${API_URL}/api/admin/crm/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
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

// Re-export existing admin functions that we still need
export { getAdminStats, runAdminTask, getAdminEmailLog, getAdminCompanies, getEmailHealth, getAdminAlerts, getAdminDiffs, sendLegislativeAlert, getAgencyClients, startAgencyBatchScan, generateAgencyEmail } from "@/lib/api";
export type { AdminStats, EmailHealth, AgencyClient } from "@/lib/api";
