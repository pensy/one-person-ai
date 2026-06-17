"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import type { User } from "@/types";
import { api, clearToken, getToken, setToken } from "@/lib/api";

interface AuthContextValue {
  user: User | null;
  loading: boolean; // 初始加载用户信息时为 true
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  /** 调用工具后刷新积分,无需重新登录 */
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const loadUser = useCallback(async () => {
    const token = getToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await api.get<User>("/api/auth/me");
      setUser(me);
    } catch {
      // token 无效或网络错误,清掉
      clearToken();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const login = useCallback(async (username: string, password: string) => {
    const res = await api.post<{ access_token: string }>("/api/auth/login", {
      username,
      password,
    });
    setToken(res.access_token);
    const me = await api.get<User>("/api/auth/me");
    setUser(me);
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const me = await api.get<User>("/api/auth/me");
      setUser(me);
    } catch {
      // 忽略,保留旧数据
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, loading, login, logout, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth 必须在 AuthProvider 内部使用");
  }
  return ctx;
}
