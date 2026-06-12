from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.database import Base, engine
from models import User, Tool, ToolCall, CreditLog  # noqa: 触发模型注册

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="One Person AI Company API",
    description="面向开发者的 AI 工具聚合平台",
    version="0.1.0",
)

# CORS 配置 - 开发阶段允许所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需要限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "One Person AI Company API is running!",
        "version": "0.1.0",
        "status": "ok",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# 注册路由
from routes import auth, tools  # noqa
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(tools.router, prefix="/api/tools", tags=["tools"])
