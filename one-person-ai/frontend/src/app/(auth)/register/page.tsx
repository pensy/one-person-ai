"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { Alert, Button, Input } from "@/components/ui";

export default function RegisterPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      // 注册成功后直接走 login 流程(它会调 /me 拿用户信息)
      await api.post("/api/auth/register", form);
      await login(form.username, form.password);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "注册失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold">注册</h1>
        <p className="text-gray-500 mt-2">注册即送 100 积分</p>
      </div>
      <form
        onSubmit={handleSubmit}
        className="bg-white p-8 rounded-xl border border-gray-200 space-y-4"
      >
        {error && <Alert>{error}</Alert>}
        <Input
          label="用户名"
          type="text"
          value={form.username}
          onChange={(e) => setForm({ ...form, username: e.target.value })}
          required
        />
        <Input
          label="邮箱"
          type="email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          required
        />
        <Input
          label="密码"
          type="password"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          required
          minLength={6}
        />
        <Button type="submit" disabled={loading} className="w-full py-2.5">
          {loading ? "注册中..." : "注册"}
        </Button>
        <p className="text-center text-sm text-gray-500">
          已有账号？{" "}
          <Link
            href="/login"
            className="text-gray-900 font-medium hover:underline"
          >
            登录
          </Link>
        </p>
      </form>
    </>
  );
}
