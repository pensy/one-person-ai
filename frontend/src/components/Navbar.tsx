"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth";

export default function Navbar() {
  const { user, loading, logout } = useAuth();

  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link href="/" className="text-xl font-bold text-gray-900">
          One Person AI
        </Link>
        <div className="flex items-center gap-4">
          {loading ? (
            <span className="text-sm text-gray-400">加载中...</span>
          ) : user ? (
            <>
              <span className="text-sm text-gray-600">
                {user.credits} 积分
              </span>
              <span className="text-sm text-gray-600">{user.username}</span>
              <button
                onClick={logout}
                className="text-sm text-gray-600 hover:text-gray-900"
              >
                退出
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="text-sm text-gray-600 hover:text-gray-900"
              >
                登录
              </Link>
              <Link
                href="/register"
                className="text-sm bg-gray-900 text-white px-4 py-2 rounded-lg hover:bg-gray-800"
              >
                注册
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
