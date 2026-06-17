"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { Card } from "@/components/ui";
import type { ToolCall } from "@/types";

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const [calls, setCalls] = useState<ToolCall[]>([]);
  const [callsLoading, setCallsLoading] = useState(true);

  useEffect(() => {
    if (!user) {
      setCallsLoading(false);
      return;
    }
    api
      .get<ToolCall[]>("/api/tools/history")
      .then(setCalls)
      .catch(() => {
        // 静默
      })
      .finally(() => setCallsLoading(false));
  }, [user]);

  if (authLoading) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-20 text-center text-gray-500">
        加载中…
      </div>
    );
  }

  if (!user) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-20 text-center">
        <p className="text-xl text-gray-600 mb-4">请先登录</p>
        <Link href="/login" className="text-gray-900 hover:underline">
          去登录
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <h1 className="text-3xl font-bold mb-8">我的工作台</h1>

      {/* 积分卡片 */}
      <Card className="p-6 mb-8">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500">当前积分</p>
            <p className="text-4xl font-bold mt-1">{user.credits}</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">{user.username}</p>
            <p className="text-sm text-gray-400 mt-1">{user.email}</p>
          </div>
        </div>
      </Card>

      {/* 调用历史 */}
      <h2 className="text-xl font-semibold mb-4">最近调用</h2>
      {callsLoading ? (
        <p className="text-gray-500">加载中…</p>
      ) : calls.length === 0 ? (
        <Card className="p-8 text-center text-gray-500">
          还没有调用记录，去{" "}
          <Link href="/" className="text-gray-900 hover:underline">
            试试工具
          </Link>
        </Card>
      ) : (
        <div className="space-y-3">
          {calls.map((call) => (
            <Card key={call.id} className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span
                  className={`text-xs px-2 py-1 rounded ${
                    call.status === "success"
                      ? "bg-green-100 text-green-700"
                      : call.status === "failed"
                        ? "bg-red-100 text-red-700"
                        : "bg-gray-100 text-gray-600"
                  }`}
                >
                  {call.status === "success"
                    ? "成功"
                    : call.status === "failed"
                      ? "失败"
                      : "处理中"}
                </span>
                <span className="text-xs text-gray-400">
                  {call.credits_used} 积分 ·{" "}
                  {new Date(call.created_at).toLocaleString("zh-CN")}
                </span>
              </div>
              <p className="text-sm text-gray-600 line-clamp-2">
                {call.input_text || "(无输入)"}
              </p>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
