from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置。优先级:环境变量 > .env 文件 > 默认值。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 运行环境:development / production
    APP_ENV: str = "development"

    # 数据库(Docker 部署时由 docker-compose 传入)
    DATABASE_URL: str = (
        "mysql+pymysql://root:root@localhost:3306/ai_tools_db?charset=utf8mb4"
    )

    # JWT
    JWT_SECRET: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 服务
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # CORS 白名单(逗号分隔);设为 * 表示全开(仅开发用)
    CORS_ORIGINS: str = "http://localhost:3000"

    # Worker 服务地址(gRPC)
    WORKER_ADDR: str = "localhost:50051"

    # DeepSeek API
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"

    # GitHub App(Phase 2 启用,先占位)
    GITHUB_APP_ID: str = ""
    GITHUB_PRIVATE_KEY_PATH: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_WEBHOOK_SECRET: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        """把逗号分隔的 CORS_ORIGINS 解析为列表。"""
        if not self.CORS_ORIGINS:
            return []
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_jwt_secret_default(self) -> bool:
        """是否仍使用默认 JWT_SECRET(生产环境禁止)。"""
        return self.JWT_SECRET == "dev-secret-key-change-in-production"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache
def get_settings() -> Settings:
    """单例配置,避免重复解析环境变量。"""
    return Settings()


# 模块级实例,供 `from config.settings import settings` 使用
settings = get_settings()
