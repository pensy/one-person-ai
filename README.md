# One Person AI Company

一人公司 AI 工具平台 — 面向开发者的 AI 工具聚合平台

## 架构概览

```
┌─────────────┐     HTTP/gRPC      ┌─────────────┐
│  Frontend   │ ──────────────────▶│  API Service │
│  (Next.js)  │                    │  (Python)    │
└─────────────┘                    └──────┬──────┘
                                          │
                                          │ gRPC/HTTP
                                          ▼
                                   ┌─────────────┐
                                   │ Worker Svc  │
                                   │  (Go)       │
                                   └──────┬──────┘
                                          │
                                          ▼
                                   ┌─────────────┐
                                   │   MySQL     │
                                   │  (Docker)   │
                                   └─────────────┘
```

## 技术栈

| 组件 | 技术 |
|---|---|
| 前端 | Next.js + TypeScript |
| 对外 API | Python + FastAPI |
| 内部高性能服务 | Go |
| 数据库 | MySQL 8.0 (Docker) |
| 部署 | Docker + 自有服务器 |
| 版本控制 | GitHub |

## 项目结构

```
├── api-service/        # Python FastAPI 对外接口服务
│   ├── handlers/       # 请求处理器
│   ├── models/         # 数据模型
│   ├── routes/         # 路由定义
│   ├── middleware/     # 中间件
│   └── config/         # 配置文件
├── worker-service/     # Go 内部高性能服务
│   ├── cmd/            # 入口
│   ├── internal/       # 内部包
│   └── pkg/            # 可导出包
├── frontend/           # Next.js 前端
├── scripts/            # 部署/工具脚本
├── docs/               # 文档
├── deploy/             # Docker 部署配置
└── README.md
```

## 开发计划

- [ ] MVP: AI 代码解释器（第一个工具）
- [ ] 用户系统（注册/登录/积分）
- [ ] 工具市场（展示所有可用 AI 工具）
- [ ] 更多 AI 工具接入

## 快速启动

```bash
# TODO: 补充启动命令
```

## License

MIT
