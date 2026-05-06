export const API_BASE = "http://127.0.0.1:8000";

export interface Action {
  id: number | string;
  type?: string;
  task?: string;
  deadline?: string;
  status?: string;
  department?: string;
  priority?: string;
  confidence?: string | number;
  confidence_components?: {
    overall?: number;
    directive_score?: number;
    entity_score?: number;
    deadline_score?: number;
    notes?: string;
  } | null;
  evidence?: {
    text?: string;
    page?: number | string | null;
    sentence_index?: number | null;
    char_start?: number | null;
    char_end?: number | null;
  } | null;
  [key: string]: unknown;
}

export interface ReviewEntry {
  id: number;
  action_id: number;
  reviewer_name: string;
  decision: string;
  comments?: string | null;
  timestamp: string;
}

export interface AuditEntry {
  id: number;
  entity_type: string;
  entity_id: string;
  action: string;
  performed_by: string;
  timestamp: string;
  details?: Record<string, unknown> | null;
}

export interface NotificationItem {
  id: number;
  action_id: number;
  due_at: string;
  sent_at?: string | null;
  channel: string;
  status: string;
  payload?: Record<string, unknown> | null;
  timestamp: string;
}

export interface AlertsResponse {
  due_actions: Action[];
  notifications: NotificationItem[];
  window_hours: number;
}

export interface ActionHistory {
  action: Action;
  reviews: ReviewEntry[];
  audits: AuditEntry[];
}

export interface DashboardSummary {
  total_actions: number;
  pending: number;
  approved: number;
  rejected: number;
  pending_actions?: number;
  approved_actions?: number;
  rejected_actions?: number;
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  async processPdf(file: File): Promise<{ actions?: Action[] } & Record<string, unknown>> {
    const fd = new FormData();
    fd.append("file", file);
    const uploadRes = await fetch(`${API_BASE}/upload`, { method: "POST", body: fd });
    const uploaded = await handle<{ document_id: string } & Record<string, unknown>>(uploadRes);
    const processRes = await fetch(`${API_BASE}/process/${uploaded.document_id}`, { method: "POST" });
    return handle(processRes);
  },
  async getActions(): Promise<Action[]> {
    const res = await fetch(`${API_BASE}/actions`);
    const data = await handle<Action[] | { actions: Action[] }>(res);
    return Array.isArray(data) ? data : data.actions ?? [];
  },
  async review(id: Action["id"], status: "APPROVED" | "REJECTED"): Promise<unknown> {
    const res = await fetch(`${API_BASE}/review/${id}?status=${status}`, { method: "POST" });
    return handle(res);
  },
  async getDashboard(): Promise<DashboardSummary> {
    const res = await fetch(`${API_BASE}/dashboard`);
    return handle<DashboardSummary>(res);
  },
};
