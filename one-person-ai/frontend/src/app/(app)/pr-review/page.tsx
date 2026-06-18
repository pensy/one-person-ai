"use client";

import { useState } from "react";

import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { Alert, Button, Card, Input } from "@/components/ui";
import type { PRReviewResponse } from "@/types";

export default function PRReviewPage() {
  const { refreshUser } = useAuth();
  const [repo, setRepo] = useState("");
  const [prNumber, setPrNumber] = useState("");
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PRReviewResponse | null>(null);
  const [error, setError] = useState("");

  const handleReview = async () => {
    if (!repo.trim() || !prNumber.trim() || !token.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await api.post<PRReviewResponse>("/api/pr-review/", {
        repo: repo.trim(),
        pr_number: parseInt(prNumber, 10),
        github_token: token.trim(),
      });
      setResult(data);
      refreshUser();
    } catch (err) {
      setError(err instanceof Error ? err.message : "审查失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <h1 className="text-3xl font-bold mb-2">PR 审查</h1>
      <p className="text-gray-600 mb-8">
        输入 GitHub 仓库和 PR 编号,AI 自动审查代码变更(消耗 3 积分)
      </p>

      <Card className="p-6 mb-6">
        <div className="space-y-4">
          <Input
            label="仓库(owner/repo 格式)"
            placeholder="octocat/Hello-World"
            value={repo}
            onChange={(e) => setRepo(e.target.value)}
          />
          <Input
            label="PR 编号"
            placeholder="1"
            type="number"
            value={prNumber}
            onChange={(e) => setPrNumber(e.target.value)}
          />
          <Input
            label="GitHub Token"
            type="password"
            placeholder="ghp_...(需 repo 或 public_repo 只读权限)"
            value={token}
            onChange={(e) => setToken(e.target.value)}
          />
          <p className="text-xs text-gray-500">
            Token 仅用于本次拉取 diff,不存储。建议使用只读权限的 PAT。
          </p>
        </div>

        <Button
          onClick={handleReview}
          disabled={loading || !repo.trim() || !prNumber.trim() || !token.trim()}
          className="w-full py-3 mt-4"
        >
          {loading ? "审查中..." : "开始审查 (3 积分)"}
        </Button>
      </Card>

      {error && (
        <div className="mb-6">
          <Alert>{error}</Alert>
        </div>
      )}

      {result && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">审查报告</h2>
            <span
              className={`text-sm ${
                result.status === "success" ? "text-green-600" : "text-red-600"
              }`}
            >
              {result.status === "success" ? "成功" : "失败"} · 消耗{" "}
              {result.credits_used} 积分
            </span>
          </div>
          {result.output_text ? (
            <Card className="p-6">
              <pre className="whitespace-pre-wrap text-sm text-gray-800 font-mono">
                {result.output_text}
              </pre>
            </Card>
          ) : (
            <Alert>审查未产出结果</Alert>
          )}
        </div>
      )}
    </div>
  );
}
