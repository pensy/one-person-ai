"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { useAuth } from "@/context/AuthContext";
import { Alert, Button, Input } from "@/components/ui";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(username, password);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "登录失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold">登录</h1>
        <p className="text-gray-500 mt-2">One Person AI 开发者工具箱</p>
      </div>
      <form
        onSubmit={handleSubmit}
        className="bg-white p-8 rounded-xl border border-gray-200 space-y-4"
      >
        {error && <Alert>{error}</Alert>}
        <Input
          label="用户名 / 邮箱"
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <Input
          label="密码"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <Button type="submit" disabled={loading} className="w-full py-2.5">
          {loading ? "登录中..." : "登录"}
        </Button>
        <p className="text-center text-sm text-gray-500">
          没有账号？{" "}
          <Link
            href="/register"
            className="text-gray-900 font-medium hover:underline"
          >
            注册
          </Link>
        </p>
      </form>
    </>
  );
}
