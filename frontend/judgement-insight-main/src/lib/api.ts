export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export interface Action {
  id: number | string;
  type?: string;
  task?: string;
  deadline?: string;
  status?: string;
  department?: string;
  priority?: string;
  confidence?: string | number;
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
  overdue_actions?: number;
  pending_actions?: number;
  approved_actions?: number;
  rejected_actions?: number;
}

export interface AlertEntry {
  id: number;
  action_id: number;
  type: "UPCOMING" | "OVERDUE" | string;
  message: string;
  created_at: string;
  is_read: boolean;
  action?: Action | null;
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    if (!text) {
      throw new Error(`Request failed: ${res.status}`);
    }

    try {
      const parsed = JSON.parse(text) as { detail?: unknown };
      if (typeof parsed.detail === "string") {
        throw new Error(parsed.detail);
      }
    } catch {
      // Fall back to the raw response text below.
    }

    throw new Error(text);
  }
  return res.json() as Promise<T>;
}

async function postForm<T>(path: string, formData: FormData): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { method: "POST", body: formData });
  return handle<T>(res);
}

async function postJson<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  return handle<T>(res);
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  return handle<T>(res);
}

async function putJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return handle<T>(res);
}

export async function uploadFile(file: File): Promise<Record<string, unknown>> {
  const fd = new FormData();
  fd.append("file", file);
  return postForm<Record<string, unknown>>("/upload", fd);
}

export async function uploadBatch(files: File[]): Promise<Record<string, unknown>> {
  const fd = new FormData();
  files.forEach((file) => fd.append("files", file));
  return postForm<Record<string, unknown>>("/upload-batch", fd);
}

export async function processDocument(documentId: string): Promise<Record<string, unknown>> {
  return postJson<Record<string, unknown>>(`/process/${encodeURIComponent(documentId)}`);
}

export async function processPdf(file: File): Promise<Record<string, unknown>> {
  const upload = (await uploadFile(file)) as { document_id?: string };
  if (!upload.document_id) {
    throw new Error("Upload did not return a document_id.");
  }
  return processDocument(upload.document_id);
}

export async function getActions(): Promise<Action[]> {
  const data = await getJson<Action[] | { actions: Action[] }>("/actions");
  return Array.isArray(data) ? data : data.actions ?? [];
}

export async function review(id: Action["id"], status: "APPROVED" | "REJECTED"): Promise<unknown> {
  return postJson(`/review/${encodeURIComponent(String(id))}?status=${encodeURIComponent(status)}`);
}

export async function getActionHistory(id: Action["id"]): Promise<ActionHistory> {
  return getJson<ActionHistory>(`/actions/${encodeURIComponent(String(id))}/history`);
}

export async function updateAction(id: Action["id"], payload: Partial<Pick<Action, "task" | "deadline" | "department" | "priority">>): Promise<Action> {
  return putJson<Action>(`/actions/${encodeURIComponent(String(id))}`, payload);
}

export async function getDashboard(): Promise<DashboardSummary> {
  const data = await getJson<DashboardSummary>("/dashboard");
  return {
    ...data,
    pending: data.pending ?? data.pending_actions ?? 0,
    approved: data.approved ?? data.approved_actions ?? 0,
    rejected: data.rejected ?? data.rejected_actions ?? 0,
  };
}

export async function getAlerts(filter: "all" | "unread" | "overdue" = "all"): Promise<AlertEntry[]> {
  const qs = filter === "all" ? "" : `?filter=${encodeURIComponent(filter)}`;
  return getJson<AlertEntry[]>(`/alerts${qs}`);
}

export async function markAlertRead(id: number): Promise<AlertEntry> {
  return postJson<AlertEntry>(`/alerts/${encodeURIComponent(String(id))}/read`);
}

export const api = {
  uploadFile,
  uploadBatch,
  processDocument,
  processPdf,
  getActions,
  review,
  getActionHistory,
  updateAction,
  getDashboard,
  getAlerts,
  markAlertRead,
};
