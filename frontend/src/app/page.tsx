"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import { useAuth } from "@/lib/auth";
import { toolsApi } from "@/lib/api";
import type { Tool } from "@/types/api";

const categoryLabels: Record<string, string> = {
  code: "代码工具",
  text: "文本工具",
};

const iconMap: Record<string, string> = {
  code_explain: "💡",
  code_review: "🔍",
  text_polish: "✍️",
  text_summary: "📋",
};

export default function Home() {
  const { user } = useAuth();
  const [tools, setTools] = useState<Tool[]>([]);
  const [toolsLoading, setToolsLoading] = useState(true);

  useEffect(() => {
    toolsApi
      .list()
      .then(setTools)
      .catch(() => {
        // 如果 API 不可用，使用默认数据
        setTools([]);
      })
      .finally(() => setToolsLoading(false));
  }, []);

  // 按分类分组
  const grouped = tools.reduce<Record<string, Tool[]>>((acc, tool) => {
    if (!acc[tool.category]) acc[tool.category] = [];
    acc[tool.category].push(tool);
    return acc;
  }, {});

  return (
    <div className="min-h-screen">
      <Navbar />

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 pt-20 pb-16 text-center">
        <h1 className="text-5xl font-bold tracking-tight text-gray-900 mb-6">
          开发者的 AI 工具箱
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-8">
          代码解释、代码审查、文本润色、内容摘要 — 一个平台搞定你的日常 AI 需求
        </p>
        <div className="flex gap-4 justify-center">
          {!user ? (
            <>
              <Link
                href="/register"
                className="bg-gray-900 text-white px-8 py-3 rounded-lg text-lg font-medium hover:bg-gray-800"
              >
                免费开始
              </Link>
              <a
                href="#tools"
                className="border border-gray-300 text-gray-700 px-8 py-3 rounded-lg text-lg font-medium hover:bg-gray-50"
              >
                查看工具
              </a>
            </>
          ) : (
            <a
              href="#tools"
              className="bg-gray-900 text-white px-8 py-3 rounded-lg text-lg font-medium hover:bg-gray-800"
            >
              开始使用
            </a>
          )}
        </div>
        <p className="text-sm text-gray-500 mt-4">
          注册即送 100 积分，免费体验所有工具
        </p>
      </section>

      {/* 工具列表 */}
      <section id="tools" className="max-w-6xl mx-auto px-6 pb-20">
        <h2 className="text-3xl font-bold text-center mb-12">可用工具</h2>

        {toolsLoading ? (
          <div className="text-center text-gray-400">加载工具列表...</div>
        ) : tools.length === 0 ? (
          <div className="text-center text-gray-400">
            暂无可用工具，请确认后端服务已启动
          </div>
        ) : (
          Object.entries(categoryLabels).map(([category, label]) => {
            const categoryTools = grouped[category];
            if (!categoryTools || categoryTools.length === 0) return null;
            return (
              <div key={category} className="mb-10">
                <h3 className="text-lg font-semibold text-gray-500 mb-4">
                  {label}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {categoryTools.map((tool) => (
                    <Link
                      key={tool.name}
                      href={`/tools/${tool.name}`}
                      className="bg-white border border-gray-200 rounded-xl p-6 hover:shadow-lg hover:border-gray-300 transition-all"
                    >
                      <div className="flex items-start gap-4">
                        <span className="text-3xl">
                          {iconMap[tool.name] || "🔧"}
                        </span>
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="text-lg font-semibold">
                              {tool.display_name}
                            </h4>
                            <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                              {tool.credits_cost} 积分/次
                            </span>
                          </div>
                          <p className="text-gray-600 text-sm">
                            {tool.description}
                          </p>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            );
          })
        )}
      </section>

      {/* 底部 */}
      <footer className="border-t border-gray-200 py-8 text-center text-sm text-gray-500">
        <p>One Person AI &copy; 2025 &middot; 一人公司出品</p>
      </footer>
    </div>
  );
}
