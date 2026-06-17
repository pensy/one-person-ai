"use client";

import { useState } from "react";
import { useParams } from "next/navigation";

import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { Alert, Button } from "@/components/ui";

const toolMap: Record<
  string,
  { displayName: string; icon: string; placeholder: string }
> = {
  code_explain: {
    displayName: "代码解释器",
    icon: "💡",
    placeholder:
      "粘贴你想解释的代码...\n\n例如：\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
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
    placeholder:
      "粘贴你想摘要的长文本...\n\nAI 会提取核心信息，控制在 200 字以内",
  },
  sql_generate: {
    displayName: "SQL 生成器",
    icon: "🗄️",
    placeholder:
      "用自然语言描述你的数据查询需求...\n\n例如：\n查询过去30天注册用户中，订单金额超过1000元的用户列表，按金额降序排列",
  },
  regex_generate: {
    displayName: "正则表达式生成器",
    icon: "🔮",
    placeholder:
      "用自然语言描述匹配规则...\n\n例如：\n匹配中国大陆手机号（支持13/15/17/18/19开头）",
  },
  api_doc: {
    displayName: "API 文档生成",
    icon: "📖",
    placeholder:
      "粘贴你的接口代码...\n\nAI 会生成规范的 API 接口文档，包含参数说明、响应格式、示例等",
  },
  json_format: {
    displayName: "JSON 格式化",
    icon: "📦",
    placeholder:
      "粘贴 JSON 数据...\n\nAI 会帮你美化格式、分析结构、解释字段含义",
  },
};

interface CallResponse {
  id: number;
  status: string;
  output_text: string | null;
  credits_used: number;
}

export default function ToolPage() {
  const params = useParams();
  const toolName = params.name as string;
  const tool = toolMap[toolName];
  const { refreshUser } = useAuth();

  const [input, setInput] = useState("");
  const [output, setOutput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  if (!tool) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-20 text-center">
        <p className="text-xl text-gray-600 mb-4">工具不存在</p>
        <a href="/" className="text-gray-900 hover:underline">
          返回首页
        </a>
      </div>
    );
  }

  const handleSubmit = async () => {
    if (!input.trim()) return;
    setLoading(true);
    setOutput("");
    setError("");

    try {
      const data = await api.post<CallResponse>("/api/tools/call", {
        tool_name: toolName,
        input_text: input,
      });
      setOutput(data.output_text || "无输出");
      // 刷新导航栏积分显示
      refreshUser();
    } catch (err) {
      setError(err instanceof Error ? err.message : "调用失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <div className="flex items-center gap-3 mb-8">
        <span className="text-4xl">{tool.icon}</span>
        <h1 className="text-3xl font-bold">{tool.displayName}</h1>
      </div>

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

      <Button
        onClick={handleSubmit}
        disabled={loading || !input.trim()}
        className="w-full py-3"
      >
        {loading ? "AI 思考中..." : `运行 ${tool.displayName}`}
      </Button>

      {error && (
        <div className="mt-4">
          <Alert>{error}</Alert>
        </div>
      )}

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
  );
}
