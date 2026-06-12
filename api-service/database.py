from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import DATABASE_URL
from models.database import Base

_engine = None
_SessionLocal = None


def init_db():
    """初始化数据库连接，创建所有表"""
    global _engine, _SessionLocal
    _engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
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
