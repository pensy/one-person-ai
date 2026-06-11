from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库
    init_db()
    yield


app = FastAPI(
    title="One Person AI Company API",
    description="面向开发者的 AI 工具聚合平台",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
from routes import auth, tools  # noqa: E402
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(tools.router, prefix="/api/tools", tags=["tools"])
