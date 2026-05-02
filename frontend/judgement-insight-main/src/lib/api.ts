export const API_BASE = "http://127.0.0.1:8000";

export interface Action {
  id: number | string;
  type?: string;
  task?: string;
  deadline?: string;
  status?: string;
  [key: string]: unknown;
}

export interface DashboardSummary {
  total_actions: number;
  pending: number;
  approved: number;
  rejected: number;
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
    const res = await fetch(`${API_BASE}/process`, { method: "POST", body: fd });
    return handle(res);
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
