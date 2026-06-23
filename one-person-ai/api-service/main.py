import sys

import grpc
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from config.settings import settings
from middleware.rate_limit import RateLimitMiddleware
from models.database import Base, engine
from models import User, Tool, ToolCall, CreditLog  # noqa: 触发模型注册

# 生产环境禁止使用默认 JWT_SECRET —— 这是安全底线,不满足直接拒绝启动
if settings.is_production and settings.is_jwt_secret_default:
    print(
        "[FATAL] 生产环境(APP_ENV=production)必须设置非默认的 JWT_SECRET。",
        file=sys.stderr,
    )
    sys.exit(1)

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="One Person AI Company API",
    description="面向开发者的 AI 工具聚合平台",
    version="0.2.0",
)

# CORS —— 从配置读取白名单,生产环境用具体域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 限流:每标识每分钟最多 20 次写操作,防刷爆 LLM 额度
app.add_middleware(RateLimitMiddleware, max_requests=20, window_seconds=60)


@app.get("/")
async def root():
    return {
        "message": "One Person AI Company API is running!",
        "version": "0.2.0",
        "status": "ok",
    }


@app.get("/health")
async def health_check():
    """增强健康检查：检测各依赖服务状态。"""
    checks = {
        "api": {"status": "ok", "version": "0.2.0"},
    }

    # MySQL
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["mysql"] = {"status": "ok"}
    except Exception as e:
        checks["mysql"] = {"status": "error", "message": str(e)}

    # Worker gRPC
    try:
        channel = grpc.insecure_channel(settings.WORKER_ADDR)
        grpc.channel_ready_future(channel).result(timeout=3)
        channel.close()
        checks["worker"] = {"status": "ok"}
    except Exception as e:
        checks["worker"] = {"status": "error", "message": str(e)}

    overall = all(v.get("status") == "ok" for v in checks.values())
    return {"status": "healthy" if overall else "degraded", "checks": checks}


# 注册路由
from routes import auth, tools, workflows, pr_review, admin, github_webhook  # noqa

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(tools.router, prefix="/api/tools", tags=["tools"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["workflows"])
app.include_router(pr_review.router, prefix="/api/pr-review", tags=["pr-review"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(github_webhook.router, prefix="/api/github", tags=["github"])
