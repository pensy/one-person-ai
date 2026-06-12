import type {
  User,
  TokenResponse,
  RegisterRequest,
  LoginRequest,
  Tool,
  ToolCallRequest,
  ToolCallResponse,
} from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("token") : null;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  const data = await res.json();

  if (!res.ok) {
    throw new ApiError(res.status, data.detail || "请求失败");
  }

  return data as T;
}

// Auth API
export const authApi = {
  register: (data: RegisterRequest) =>
    request<TokenResponse>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  login: (data: LoginRequest) =>
    request<TokenResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getMe: () => request<User>("/api/auth/me"),
};

// Tools API
export const toolsApi = {
  list: () => request<Tool[]>("/api/tools/"),

  call: (data: ToolCallRequest) =>
    request<ToolCallResponse>("/api/tools/call", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  history: () => request<ToolCallResponse[]>("/api/tools/history"),
};

export { ApiError };
export default API_BASE;
