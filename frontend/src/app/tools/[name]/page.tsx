"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import { useAuth } from "@/lib/auth";
import { toolsApi, ApiError } from "@/lib/api";

const toolMap: Record<string, { displayName: string; icon: string; placeholder: string }> = {
  code_explain: {
    displayName: "代码解释器",
    icon: "💡",
    placeholder: "粘贴你想解释的代码...\n\n例如：\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
  },
  code_review: {
    displayName: "代码审查",
    icon: "🔍",
    placeholder: "粘贴你想审查的代码...\n\nAI 会从质量、性能、安全角度审查",
  },
  text_polish: {
    displayName: "文本润色",
    icon: "✍️",
    placeholder: "粘贴你想润色的文本...\n\nAI 会优化表达，保持原意",
  },
  text_summary: {
    displayName: "内容摘要",
    icon: "📋",
    placeholder: "粘贴你想摘要的长文本...\n\nAI 会提取核心信息，控制在 200 字以内",
  },
  sql_generate: {
    displayName: "SQL 生成器",
    icon: "🗄️",
    placeholder: "用自然语言描述你的数据查询需求...\n\n例如：\n查询过去30天注册用户中，订单金额超过1000元的用户列表，按金额降序排列",
  },
  regex_generate: {
    displayName: "正则表达式生成器",
    icon: "🔮",
    placeholder: "用自然语言描述匹配规则...\n\n例如：\n匹配中国大陆手机号（支持13/15/17/18/19开头）",
  },
  api_doc: {
    displayName: "API 文档生成",
    icon: "📖",
    placeholder: "粘贴你的接口代码...\n\nAI 会生成规范的 API 接口文档，包含参数说明、响应格式、示例等",
  },
  json_format: {
    displayName: "JSON 格式化",
    icon: "📦",
    placeholder: "粘贴 JSON 数据...\n\nAI 会帮你美化格式、分析结构、解释字段含义",
  },
};

export default function ToolPage() {
  const params = useParams();
  const router = useRouter();
  const { user, refreshUser } = useAuth();
  const toolName = params.name as string;
  const tool = toolMap[toolName];

  const [input, setInput] = useState("");
  const [output, setOutput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!tool) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-xl text-gray-600 mb-4">工具不存在</p>
          <a href="/" className="text-blue-600 hover:underline">返回首页</a>
        </div>
      </div>
    );
  }

  const handleSubmit = async () => {
    if (!input.trim()) return;

    if (!user) {
      router.push("/login");
      return;
    }

    setLoading(true);
    setOutput("");
    setError("");

    try {
      const res = await toolsApi.call({
        tool_name: toolName,
        input_text: input,
      });
      setOutput(res.output_text || "无输出");
      // 刷新用户信息（积分已变化）
      await refreshUser();
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        router.push("/login");
        return;
      }
      setError(err instanceof Error ? err.message : "调用失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen">
      <Navbar />

      {/* 工具主体 */}
      <div className="max-w-4xl mx-auto px-6 py-10">
        <div className="flex items-center gap-3 mb-8">
          <span className="text-4xl">{tool.icon}</span>
          <h1 className="text-3xl font-bold">{tool.displayName}</h1>
        </div>

        {/* 输入区 */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            输入内容
          </label>
          <textarea
            className="w-full h-64 p-4 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-gray-900 focus:border-transparent resize-none"
            placeholder={tool.placeholder}
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
        </div>

        {/* 提交按钮 */}
        <button
          onClick={handleSubmit}
          disabled={loading || !input.trim()}
          className="w-full bg-gray-900 text-white py-3 rounded-lg font-medium hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "AI 思考中..." : `运行 ${tool.displayName}`}
        </button>

        {/* 错误提示 */}
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {/* 输出区 */}
        {output && (
          <div className="mt-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              AI 输出
            </label>
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <pre className="whitespace-pre-wrap text-sm text-gray-800 font-mono">
                {output}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
