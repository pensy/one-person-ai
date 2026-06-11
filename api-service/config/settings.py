import os
from dotenv import load_dotenv

load_dotenv()

# 数据库配置 - Docker 环境用 mysql，本地用 localhost
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://ai_user:ai_pass@localhost:3306/ai_tools_db?charset=utf8mb4",
)

# JWT 配置
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 服务配置
API_HOST = "0.0.0.0"
API_PORT = 8000

# Worker 服务地址
WORKER_ADDR = os.getenv("WORKER_ADDR", "localhost:50051")
