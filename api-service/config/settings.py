# 开发环境配置
DATABASE_URL = "mysql+pymysql://root:root@localhost:3306/ai_tools_db?charset=utf8mb4"

# JWT 配置
JWT_SECRET = "dev-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 服务配置
API_HOST = "0.0.0.0"
API_PORT = 8000

# Worker 服务地址
WORKER_ADDR = "localhost:50051"
