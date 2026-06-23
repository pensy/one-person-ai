"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { Card, Alert, Badge } from "@/components/ui";
import type { AdminStatus, AdminUser, Tool, AdminStatusCheck } from "@/types";

export default function AdminPage() {
  const { user, loading: authLoading } = useAuth();

  const [status, setStatus] = useState<AdminStatus | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user) return;
    Promise.all([
      api.get<AdminStatus>("/api/admin/status").catch(() => null),
      api.get<AdminUser[]>("/api/admin/users").catch(() => []),
      api.get<Tool[]>("/api/tools/").catch(() => []),
    ])
      .then(([s, u, t]) => {
        setStatus(s);
        setUsers(u);
        setTools(t);
      })
      .catch(() => setError("加载失败"))
      .finally(() => setLoading(false));
  }, [user]);

  async function toggleTool(toolId: number) {
    try {
      const updated = await api.put<{ id: number; is_active: boolean }>(
        `/api/admin/tools/${toolId}/toggle`,
      );
      setTools((prev) =>
        prev.map((t) =>
          t.id === updated.id ? { ...t, is_active: updated.is_active } : t,
        ),
      );
    } catch {
      setError("操作失败");
    }
  }

  if (authLoading || loading) {
    return (
      <div className="max-w-6xl mx-auto px-6 py-20 text-center text-gray-500">
        加载中…
      </div>
    );
  }

  if (!user) {
    return (
      <div className="max-w-6xl mx-auto px-6 py-20 text-center text-gray-500">
        请先登录
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-10">
      <h1 className="text-3xl font-bold mb-8">管理后台</h1>

      {error && (
        <div className="mb-6">
          <Alert>{error}</Alert>
        </div>
      )}

      {/* 服务状态 */}
      <section className="mb-10">
        <h2 className="text-xl font-semibold mb-4">服务状态</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {([
            {
              name: "API 服务",
              key: "api" as const,
              svc: status?.api,
            },
            {
              name: "MySQL 数据库",
              key: "mysql" as const,
              svc: status?.mysql,
            },
            {
              name: "Worker 服务",
              key: "worker" as const,
              svc: status?.worker,
            },
          ] as { name: string; key: string; svc: AdminStatusCheck | undefined }[]).map((item) => (
            <Card key={item.key} className="p-5">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium">{item.name}</h3>
                <Badge>
                  {item.svc?.status === "ok" ? "正常" : "异常"}
                </Badge>
              </div>
              {item.svc?.message && (
                <p className="text-sm text-red-600 mt-2">{item.svc.message}</p>
              )}
            </Card>
          ))}
        </div>
      </section>

      {/* 工具管理 */}
      <section className="mb-10">
        <h2 className="text-xl font-semibold mb-4">工具管理</h2>
        <div className="space-y-2">
          {tools.map((tool) => (
            <Card key={tool.id} className="p-4 flex items-center justify-between">
              <div>
                <p className="font-medium">{tool.display_name}</p>
                <p className="text-sm text-gray-500">{tool.name}</p>
              </div>
              <button
                onClick={() => toggleTool(tool.id)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  tool.is_active
                    ? "bg-green-100 text-green-700 hover:bg-green-200"
                    : "bg-gray-100 text-gray-500 hover:bg-gray-200"
                }`}
              >
                {tool.is_active ? "已启用" : "已禁用"}
              </button>
            </Card>
          ))}
        </div>
      </section>

      {/* 用户列表 */}
      <section>
        <h2 className="text-xl font-semibold mb-4">用户列表</h2>
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left p-3 font-medium text-gray-600">
                    用户名
                  </th>
                  <th className="text-left p-3 font-medium text-gray-600">
                    邮箱
                  </th>
                  <th className="text-right p-3 font-medium text-gray-600">
                    积分
                  </th>
                  <th className="text-center p-3 font-medium text-gray-600">
                    状态
                  </th>
                  <th className="text-right p-3 font-medium text-gray-600">
                    注册时间
                  </th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-b border-gray-100 last:border-0">
                    <td className="p-3">{u.username}</td>
                    <td className="p-3 text-gray-500">{u.email}</td>
                    <td className="p-3 text-right font-medium">{u.credits}</td>
                    <td className="p-3 text-center">
                      <Badge>{u.is_active ? "正常" : "禁用"}</Badge>
                    </td>
                    <td className="p-3 text-right text-gray-500">
                      {new Date(u.created_at).toLocaleDateString("zh-CN")}
                    </td>
                  </tr>
                ))}
                {users.length === 0 && (
                  <tr>
                    <td colSpan={5} className="p-6 text-center text-gray-400">
                      暂无用户
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </section>
    </div>
  );
}
