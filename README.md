# One Person AI

一人公司 AI 工具平台 — 面向开发者的 AI 工具聚合平台。

所有代码在 [`one-person-ai/`](./one-person-ai) 目录下。

## 快速开始

```bash
cd one-person-ai/deploy
bash quick-start.sh
```

详细文档见 [`one-person-ai/deploy/README.md`](./one-person-ai/deploy/README.md)。

## 架构

```
Frontend (Next.js) → API (FastAPI/Python) → Worker (Go/gRPC) → DeepSeek LLM
                                          ↘ MySQL
```

## 技术栈

- **前端**: Next.js 16 + React 19 + TypeScript + Tailwind v4
- **API**: Python FastAPI + SQLAlchemy + JWT
- **Worker**: Go + gRPC + protobuf
- **数据库**: MySQL 8
- **部署**: Docker Compose
