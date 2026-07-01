import type {
  AuthResponse,
  GraphSnapshot,
  HealthResponse,
  PredictAccepted,
  Prediction,
  PredictionHistory,
  Repository,
  RepositoryList,
  RiskSummary,
  XAIReport,
} from "./types";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";

class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function getToken(): string | null {
  return localStorage.getItem("access_token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, body.detail ?? "Request failed");
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<HealthResponse>("/health"),

  register: (email: string, username: string, password: string) =>
    request<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, username, password }),
    }),

  login: (email: string, password: string) =>
    request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  listRepositories: () => request<RepositoryList>("/repository"),

  createRepository: (payload: {
    name: string;
    url: string;
    default_branch?: string;
    provider?: string;
  }) =>
    request<Repository>("/repository", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  deleteRepository: (id: string) =>
    request<void>(`/repository/${id}`, { method: "DELETE" }),

  syncRepository: (id: string, full_sync = false) =>
    request<{ job_id: string; status: string; message: string }>(`/repository/${id}/sync`, {
      method: "POST",
      body: JSON.stringify({ full_sync }),
    }),

  predict: (repository_id: string, diff: string) =>
    request<PredictAccepted>("/predict", {
      method: "POST",
      body: JSON.stringify({ repository_id, diff }),
    }),

  getPrediction: (id: string) => request<Prediction>(`/prediction/${id}`),

  getPredictionXAI: (id: string) => request<XAIReport>(`/prediction/${id}/xai`),

  getHistory: (repositoryId: string) =>
    request<PredictionHistory>(`/history/${repositoryId}?limit=20`),

  getRiskSummary: (repositoryId: string) =>
    request<RiskSummary>(`/risk/${repositoryId}`),

  getGraph: (repositoryId: string) => request<GraphSnapshot>(`/graph/${repositoryId}`),

  getSubgraph: (repositoryId: string, files: string[]) =>
    request<GraphSnapshot>(
      `/graph/${repositoryId}/subgraph?${files.map((f) => `files=${encodeURIComponent(f)}`).join("&")}`,
    ),
};

export { ApiError };
