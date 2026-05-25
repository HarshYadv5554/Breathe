const API_BASE = import.meta.env.VITE_API_URL || "/api";

function headers(): HeadersInit {
  const token = localStorage.getItem("token");
  return {
    ...(token ? { Authorization: `Token ${token}` } : {}),
  };
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...headers(),
      ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...options.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

export interface Organization {
  id: number;
  name: string;
  slug: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
}

export interface DataSource {
  id: number;
  source_type: string;
  label: string;
}

export interface DashboardStats {
  total_activities: number;
  pending_review: number;
  flagged: number;
  approved: number;
  locked: number;
  failed_batches: number;
  recent_batches: IngestionBatch[];
}

export interface IngestionBatch {
  id: number;
  filename: string;
  status: string;
  row_count: number;
  success_count: number;
  error_count: number;
  warning_count: number;
  source_type: string;
  data_source_label: string;
  started_at: string;
}

export interface EmissionActivity {
  id: number;
  scope: string;
  category: string;
  subcategory: string;
  activity_date: string;
  period_start: string | null;
  period_end: string | null;
  site_name: string;
  plant_code: string;
  description: string;
  quantity_normalized: string;
  unit_normalized: string;
  quantity_raw: string | null;
  unit_raw: string;
  review_status: string;
  suspicion_flags: string[];
  analyst_notes: string;
  data_source_type: string;
  batch_filename: string;
  source_reference: string;
  audit_logs: { action: string; note: string; user_name: string; created_at: string; field_changes: Record<string, unknown> }[];
}

export const api = {
  login: (username: string, password: string) =>
    request<{ token: string; user: User; organizations: Organization[] }>("/auth/login/", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),

  me: () =>
    request<{ user: User; organizations: Organization[] }>("/auth/me/"),

  dashboard: (orgId: number) =>
    request<DashboardStats>(`/orgs/${orgId}/dashboard/`),

  sources: async (orgId: number) => {
    const data = await request<DataSource[] | { results: DataSource[] }>(
      `/orgs/${orgId}/sources/`
    );
    return Array.isArray(data) ? data : data.results;
  },

  activities: (orgId: number, params?: Record<string, string>) => {
    const q = new URLSearchParams(params).toString();
    return request<{ results: EmissionActivity[]; count: number } | EmissionActivity[]>(
      `/orgs/${orgId}/activities/${q ? `?${q}` : ""}`
    ).then((data) => (Array.isArray(data) ? { results: data, count: data.length } : data));
  },

  upload: (orgId: number, sourceId: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<IngestionBatch>(`/orgs/${orgId}/sources/${sourceId}/upload/`, {
      method: "POST",
      body: form,
    });
  },

  approve: (orgId: number, id: number, note?: string) =>
    request<EmissionActivity>(`/orgs/${orgId}/activities/${id}/approve/`, {
      method: "POST",
      body: JSON.stringify({ note: note || "" }),
    }),

  reject: (orgId: number, id: number, note?: string) =>
    request<EmissionActivity>(`/orgs/${orgId}/activities/${id}/reject/`, {
      method: "POST",
      body: JSON.stringify({ note: note || "" }),
    }),

  lock: (orgId: number, id: number) =>
    request<EmissionActivity>(`/orgs/${orgId}/activities/${id}/lock/`, { method: "POST" }),

  bulkApprove: (orgId: number, ids: number[]) =>
    request<{ updated: number }>(`/orgs/${orgId}/activities/bulk_approve/`, {
      method: "POST",
      body: JSON.stringify({ ids }),
    }),

  updateActivity: (orgId: number, id: number, data: Partial<EmissionActivity>) =>
    request<EmissionActivity>(`/orgs/${orgId}/activities/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
};
