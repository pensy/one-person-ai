"use client";

import { useEffect, useState } from "react";

import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { Alert, Button, Card } from "@/components/ui";
import type { Workflow, WorkflowRunResponse } from "@/types";

export default function WorkflowPage() {
  const { refreshUser } = useAuth();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selected, setSelected] = useState<Workflow | null>(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<WorkflowRunResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<Workflow[]>("/api/workflows/")
      .then(setWorkflows)
      .catch(() => {});
  }, []);

  const handleRun = async () => {
    if (!selected || !input.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await api.post<WorkflowRunResponse>("/api/workflows/run", {
        workflow_name: selected.name,
        input_text: input,
      });
      setResult(data);
      refreshUser();
    } catch (err) {
      setError(err instanceof Error ? err.message : "调用失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <h1 className="text-3xl font-bold mb-2">工作流</h1>
      <p className="text-gray-600 mb-8">
        多个 AI 工具串联执行,前一步输出自动喂给下一步
      </p>

      {/* 工作流选择 */}
      {!selected && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {workflows.map((wf) => (
            <Card
              key={wf.name}
              className="p-6 cursor-pointer hover:shadow-lg hover:border-gray-300 transition-all"
            >
              <button
                onClick={() => {
                  setSelected(wf);
                  setResult(null);
                  setError("");
                }}
                className="text-left w-full"
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-semibold">
                    {wf.display_name}
                  </h3>
                  <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                    {wf.credits_cost} 积分
                  </span>
                </div>
                <p className="text-gray-600 text-sm mb-3">{wf.description}</p>
                <div className="flex items-center gap-1 text-sm text-gray-500">
                  {wf.steps.map((s, i) => (
                    <span key={s.tool}>
                      {i > 0 && <span className="mx-1">→</span>}
                      {s.label}
                    </span>
                  ))}
                </div>
              </button>
            </Card>
          ))}
        </div>
      )}

      {/* 执行面板 */}
      {selected && (
        <div>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold">{selected.display_name}</h2>
              <div className="flex items-center gap-1 text-sm text-gray-500 mt-1">
                {selected.steps.map((s, i) => (
                  <span key={s.tool}>
                    {i > 0 && <span className="mx-1">→</span>}
                    {s.label}
                  </span>
                ))}
                <span className="ml-3 text-gray-400">
                  {selected.credits_cost} 积分
                </span>
              </div>
            </div>
            <button
              onClick={() => {
                setSelected(null);
                setResult(null);
                setInput("");
              }}
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              ← 换一个
            </button>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              输入内容
            </label>
            <textarea
              className="w-full h-48 p-4 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-gray-900 focus:border-transparent resize-none"
              placeholder="粘贴代码或文本..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
          </div>

          <Button
            onClick={handleRun}
            disabled={loading || !input.trim()}
            className="w-full py-3"
          >
            {loading ? "执行中..." : `运行工作流 (${selected.credits_cost} 积分)`}
          </Button>

          {error && (
            <div className="mt-4">
              <Alert>{error}</Alert>
            </div>
          )}

          {/* 逐步结果 */}
          {result && (
            <div className="mt-8 space-y-4">
              <h3 className="text-lg font-semibold">
                执行结果{" "}
                <span
                  className={`text-sm font-normal ${
                    result.status === "success" ? "text-green-600" : "text-red-600"
                  }`}
                >
                  {result.status === "success" ? "成功" : "失败"} · 消耗{" "}
                  {result.credits_used} 积分
                </span>
              </h3>
              {result.steps.map((step, i) => (
                <Card key={i} className="p-5">
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-medium">
                      {i + 1}. {step.label}
                    </span>
                    <span
                      className={`text-xs px-2 py-1 rounded ${
                        step.status === "success"
                          ? "bg-green-50 text-green-700"
                          : "bg-red-50 text-red-700"
                      }`}
                    >
                      {step.status === "success" ? "成功" : "失败"}
                    </span>
                  </div>
                  {step.error && (
                    <p className="text-sm text-red-600 mb-2">{step.error}</p>
                  )}
                  {step.output && (
                    <pre className="whitespace-pre-wrap text-sm text-gray-800 font-mono bg-gray-50 p-3 rounded">
                      {step.output}
                    </pre>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
