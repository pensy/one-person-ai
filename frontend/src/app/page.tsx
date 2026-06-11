import Link from "next/link";

const tools = [
  {
    name: "code_explain",
    displayName: "代码解释器",
    description: "粘贴代码，AI 帮你逐行解释逻辑、发现潜在问题",
    category: "code",
    icon: "💡",
    creditsCost: 1,
  },
  {
    name: "code_review",
    displayName: "代码审查",
    description: "AI 从质量、性能、安全等角度审查你的代码",
    category: "code",
    icon: "🔍",
    creditsCost: 2,
  },
  {
    name: "text_polish",
    displayName: "文本润色",
    description: "优化文章表达，让文字更流畅专业",
    category: "text",
    icon: "✍️",
    creditsCost: 1,
  },
  {
    name: "text_summary",
    displayName: "内容摘要",
    description: "长文自动摘要，快速获取核心信息",
    category: "text",
    icon: "📋",
    creditsCost: 1,
  },
];

const categoryLabels: Record<string, string> = {
  code: "代码工具",
  text: "文本工具",
};

export default function Home() {
  return (
    <div className="min-h-screen">
      {/* 导航栏 */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="text-xl font-bold text-gray-900">
            One Person AI
          </Link>
          <div className="flex items-center gap-4">
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
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 pt-20 pb-16 text-center">
        <h1 className="text-5xl font-bold tracking-tight text-gray-900 mb-6">
          开发者的 AI 工具箱
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-8">
          代码解释、代码审查、文本润色、内容摘要 — 一个平台搞定你的日常 AI 需求
        </p>
        <div className="flex gap-4 justify-center">
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
        </div>
        <p className="text-sm text-gray-500 mt-4">注册即送 100 积分，免费体验所有工具</p>
      </section>

      {/* 工具列表 */}
      <section id="tools" className="max-w-6xl mx-auto px-6 pb-20">
        <h2 className="text-3xl font-bold text-center mb-12">可用工具</h2>

        {Object.entries(categoryLabels).map(([category, label]) => (
          <div key={category} className="mb-10">
            <h3 className="text-lg font-semibold text-gray-500 mb-4">{label}</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {tools
                .filter((t) => t.category === category)
                .map((tool) => (
                  <Link
                    key={tool.name}
                    href={`/tools/${tool.name}`}
                    className="bg-white border border-gray-200 rounded-xl p-6 hover:shadow-lg hover:border-gray-300 transition-all"
                  >
                    <div className="flex items-start gap-4">
                      <span className="text-3xl">{tool.icon}</span>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="text-lg font-semibold">{tool.displayName}</h4>
                          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                            {tool.creditsCost} 积分/次
                          </span>
                        </div>
                        <p className="text-gray-600 text-sm">{tool.description}</p>
                      </div>
                    </div>
                  </Link>
                ))}
            </div>
          </div>
        ))}
      </section>

      {/* 底部 */}
      <footer className="border-t border-gray-200 py-8 text-center text-sm text-gray-500">
        <p>One Person AI © 2025 · 一人公司出品</p>
      </footer>
    </div>
  );
}
