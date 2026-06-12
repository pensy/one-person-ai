import os
from dotenv import load_dotenv

load_dotenv()

# 数据库配置（优先使用环境变量，Docker 部署时由 docker-compose 传入）
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:root@localhost:3306/ai_tools_db?charset=utf8mb4")

# JWT 配置
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# 服务配置
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Worker 服务地址
WORKER_ADDR = os.getenv("WORKER_ADDR", "localhost:50051")
