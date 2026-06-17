# One Person AI Company

> 一人公司 AI 工具平台 — 面向开发者的 AI 工具聚合平台

集成代码解释/审查、文本润色/摘要、SQL 生成、正则生成、API 文档生成、JSON 格式化等 8 个 AI 工具，基于 DeepSeek 大模型，前端 + API + Worker 三层架构，Docker 一键部署。

## 架构

```
┌─────────────┐    HTTP/REST     ┌──────────────┐   gRPC    ┌─────────────┐
│  Frontend   │ ───────────────▶ │  API Service │ ────────▶ │ Worker Svc  │
│  Next.js 16 │                  │  FastAPI     │           │  Go + gRPC  │
│  :3000      │                  │  :8000       │           │  :50051     │
└─────────────┘                  └──────┬───────┘           └──────┬──────┘
                                        │                          │
                                        │ SQLAlchemy               │ HTTP→DeepSeek
                                        ▼                          ▼
                                 ┌─────────────┐          ┌──────────────┐
                                 │   MySQL 8   │          │  DeepSeek API│
                                 │   :3306     │          │              │
                                 └─────────────┘          └──────────────┘
```

**调用链路**：前端 → API(鉴权/积分/记录) → Worker(gRPC 异步执行 LLM) → DeepSeek。Worker 不可达时 API 自动降级为进程内同步直连，保证可用性。

## 技术栈

| 层 | 技术 | 说明 |
|---|---|---|
| 前端 | Next.js 16 + React 19 + TypeScript + Tailwind v4 | 路由分组 `(app)`/`(auth)`，AppLayout + AuthContext |
| API 服务 | Python 3.11 + FastAPI + SQLAlchemy 2 + Pydantic Settings | JWT 鉴权、积分系统、限流中间件、gRPC 客户端 |
| Worker 服务 | Go 1.25 + gRPC + protobuf | 异步任务执行器，内存任务状态，LLM 调用 |
| 数据库 | MySQL 8.0 | 用户/工具/调用记录/积分日志 |
| 部署 | Docker + docker compose | 四服务编排，健康检查 |

## 项目结构

```
one-person-ai/
├── api-service/            # Python FastAPI 对外 API
│   ├── main.py             # 应用入口(启动检查、CORS、限流、路由注册)
│   ├── config/settings.py  # Pydantic Settings 配置(环境变量 → .env → 默认值)
│   ├── models/             # SQLAlchemy 模型 + JWT 认证 + DeepSeek 封装
│   │   ├── database.py     # User/Tool/ToolCall/CreditLog + get_db
│   │   ├── auth.py         # 密码哈希、JWT 签发/校验、get_current_user
│   │   └── deepseek.py     # TOOL_SPECS 工具规格 + 降级直连
│   ├── routes/             # auth(注册/登录/me) + tools(列表/调用/历史)
│   ├── middleware/rate_limit.py  # 写操作限流(20次/分钟)
│   ├── worker_client.py    # gRPC 客户端(提交任务/轮询状态)
│   └── protos/             # 生成的 Python gRPC stub(构建时生成)
├── worker-service/         # Go gRPC 异步任务执行
│   ├── cmd/main.go         # 入口(--check 健康自检)
│   ├── internal/
│   │   ├── config/         # 环境变量配置
│   │   ├── grpcserver/     # gRPC server(SubmitTask/GetTaskStatus)
│   │   ├── executor/       # 异步任务执行器(LLM_CALL/PR_REVIEW)
│   │   └── llm/            # DeepSeek 客户端
│   └── proto/              # 生成的 Go gRPC stub
├── frontend/               # Next.js 前端
│   └── src/
│       ├── app/(app)/      # 应用区(首页/工作台/工具页)
│       ├── app/(auth)/     # 认证区(登录/注册)
│       ├── context/AuthContext.tsx
│       ├── lib/api.ts      # 统一 fetch 封装(自动 Bearer token、401 跳转)
│       └── components/ui/  # Button/Card/Input/Alert/Badge
├── deploy/                 # Docker 部署
│   ├── docker-compose.yml  # 四服务编排
│   └── mysql/init.sql      # 建表 + 8 个初始工具数据
├── protos/worker.proto     # gRPC 服务定义(共享)
└── scripts/gen_proto.sh    # 一键生成 Python/Go gRPC 代码
```

## 内置工具

| 工具 | 标识 | 分类 | 积分 |
|---|---|---|---|
| 代码解释器 | `code_explain` | 代码 | 1 |
| 代码审查 | `code_review` | 代码 | 2 |
| 正则表达式生成器 | `regex_generate` | 代码 | 1 |
| API 文档生成 | `api_doc` | 代码 | 2 |
| 文本润色 | `text_polish` | 文本 | 1 |
| 内容摘要 | `text_summary` | 文本 | 1 |
| SQL 生成器 | `sql_generate` | 数据 | 2 |
| JSON 格式化 | `json_format` | 数据 | 1 |

新用户注册赠送 100 积分。新增工具时在 `deepseek.py` 的 `TOOL_SPECS` 与 `init.sql` 同步追加即可。

## 快速开始

### 前置条件

- Docker + Docker Compose
- DeepSeek API Key（[申请地址](https://platform.deepseek.com/)，可选；不配置则 LLM 调用会失败，但服务能正常启动）

### 一键启动

```bash
cd one-person-ai/deploy

# 配置环境变量(可选,无 key 也能启动)
export DEEPSEEK_API_KEY=sk-your-key-here

# 构建并启动全部服务
docker compose up -d

# 查看状态(等待 mysql 健康后 api 启动)
docker compose ps
```

启动后访问：
- 前端：http://localhost:3000
- API：http://localhost:8000（健康检查 `/health`）
- Worker gRPC：localhost:50051

### 服务端口

| 服务 | 端口 |
|---|---|
| Frontend | 3000 |
| API Service | 8000 |
| Worker gRPC | 50051 |
| MySQL | 3306（仅容器内） |

## API 接口

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| POST | `/api/auth/register` | 否 | 注册（用户名/邮箱/密码），赠 100 积分 |
| POST | `/api/auth/login` | 否 | 登录，返回 JWT |
| GET | `/api/auth/me` | 是 | 获取当前用户信息 |
| GET | `/api/tools/` | 否 | 工具列表 |
| POST | `/api/tools/call` | 是 | 调用工具（扣积分、记记录） |
| GET | `/api/tools/history` | 是 | 当前用户调用历史 |

调用示例：

```bash
# 注册
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@test.com","password":"secret123"}'

# 登录拿 token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"secret123"}' | python3 -c "import json,sys;print(json.load(sys.stdin)['access_token'])")

# 调用工具
curl -X POST http://localhost:8000/api/tools/call \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"tool_name":"code_explain","input_text":"def f(n): return n if n<2 else f(n-1)+f(n-2)"}'
```

## 配置

核心环境变量（完整见 `api-service/.env.example` 与 `deploy/docker-compose.yml`）：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `APP_ENV` | `development` | 运行环境；`production` 时强制要求非默认 JWT_SECRET |
| `DATABASE_URL` | — | MySQL 连接串（compose 已注入） |
| `JWT_SECRET` | `dev-secret-...` | JWT 签名密钥，**生产必须改** |
| `DEEPSEEK_API_KEY` | 空 | DeepSeek API Key |
| `CORS_ORIGINS` | `http://localhost:3000` | CORS 白名单，逗号分隔 |
| `WORKER_ADDR` | `localhost:50051` | Worker gRPC 地址 |

## 开发

### 重新生成 gRPC 代码

修改 `protos/worker.proto` 后，在仓库根目录运行：

```bash
bash one-person-ai/scripts/gen_proto.sh
```

会同时生成 Python（`api-service/protos/`）和 Go（`worker-service/proto/`）的 stub。Docker 构建时也会自动生成，无需手动提交生成产物。

### 本地开发各服务

```bash
# API(需先装依赖: pip install -r api-service/requirements.txt)
cd one-person-ai/api-service && uvicorn main:app --reload

# Worker(需 Go 1.25+)
cd one-person-ai/worker-service && go run ./cmd/main.go

# 前端(需 pnpm)
cd one-person-ai/frontend && pnpm install && pnpm dev
```

## 路线图

- [x] Phase 0：三层架构打通 + 8 个 AI 工具
- [x] JWT 鉴权 + 积分系统 + 调用记录
- [x] Worker gRPC 异步执行 + API 降级兜底
- [ ] Phase 1：多步工作流编排（复用 Worker executor）
- [ ] Phase 2：GitHub App 集成（PR 自动审查，`PR_REVIEW` 任务类型已预留）

## License

见 [LICENSE](LICENSE)。
