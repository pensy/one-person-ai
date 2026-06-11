import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models.database import Base

_engine = None
_SessionLocal = None


def init_db():
    """初始化数据库连接，创建所有表"""
    global _engine, _SessionLocal
    database_url = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:root@localhost:3306/ai_tools_db?charset=utf8mb4"
    )
    _engine = create_engine(database_url, echo=False, pool_pre_ping=True)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    Base.metadata.create_all(bind=_engine)


def get_db():
    """FastAPI 依赖注入：获取数据库 session"""
    if _SessionLocal is None:
        init_db()
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
