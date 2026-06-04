import type {
  BoardResponse,
  GeneratedMessage,
  Job,
  SafetyResult,
  Score,
} from "./types";

const BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

const TOKEN_KEY = "jobops_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}/api/v1${path}`, { ...options, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  async login(email: string, password: string): Promise<string> {
    const data = await request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    return data.access_token;
  },

  getProfile: () => request<unknown>("/profile"),

  listJobs: () => request<Job[]>("/jobs"),

  createJob: (payload: Partial<Job>) =>
    request<Job>("/jobs", { method: "POST", body: JSON.stringify(payload) }),

  scoreJob: (jobId: string) =>
    request<Score>(`/jobs/${jobId}/score`, { method: "POST" }),

  createApplication: (jobId: string) =>
    request<{ id: string; state: string }>("/applications", {
      method: "POST",
      body: JSON.stringify({ job_opportunity_id: jobId }),
    }),

  board: () => request<BoardResponse>("/applications/board"),

  changeState: (applicationId: string, to_state: string) =>
    request<{ id: string; state: string }>(
      `/applications/${applicationId}/state`,
      { method: "PATCH", body: JSON.stringify({ to_state }) },
    ),

  generateMessage: (applicationId: string) =>
    request<GeneratedMessage>(`/applications/${applicationId}/messages`, {
      method: "POST",
      body: JSON.stringify({ type: "recruiter_outreach" }),
    }),

  safetyCheck: (payload: {
    message: string;
    email_domain?: string | null;
    has_official_link?: boolean | null;
    company_named?: boolean | null;
  }) =>
    request<SafetyResult>("/safety/check", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};

export { ApiError };
