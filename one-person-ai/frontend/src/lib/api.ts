import type { ApiError } from "@/types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const TOKEN_KEY = "token";

/** 获取本地存储的 token(仅客户端可用) */
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
}

/**
 * 统一 API 调用封装。
 * - 自动注入 Bearer token
 * - 统一解析后端错误(抛出 Error,message 为 detail)
 * - 401 时清 token 并跳登录页(避免循环依赖,这里用 window.location)
 */
export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };
  if (token && !headers.Authorization) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  // 尝试解析 JSON(无论成功失败都可能是 JSON)
  let data: unknown = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      // 非 JSON 响应,保留 null
    }
  }

  if (!res.ok) {
    if (res.status === 401) {
      clearToken();
      // 跳登录,避免在多个组件里重复处理
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
    }
    const err = data as ApiError | null;
    const message = err?.detail || `请求失败 (${res.status})`;
    throw new Error(message);
  }

  return data as T;
}

// 常用方法快捷封装
export const api = {
  get: <T>(path: string) => apiFetch<T>(path, { method: "GET" }),
  post: <T>(path: string, body?: unknown) =>
    apiFetch<T>(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),
  put: <T>(path: string, body?: unknown) =>
    apiFetch<T>(path, {
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    }),
  del: <T>(path: string) => apiFetch<T>(path, { method: "DELETE" }),
};
