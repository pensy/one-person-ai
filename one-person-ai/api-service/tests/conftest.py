"""Pytest 公共 fixture。

测试用 SQLite in-memory 隔离数据库,不依赖外部 MySQL。
必须在任何项目模块 import 之前设置 DATABASE_URL,否则 database.py
会在 import 时绑定到生产 MySQL engine。
"""
import os

# 关键:在 import 项目代码前把数据库切到 SQLite 内存库。
# Pydantic Settings 在 import 时读取此变量。
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
# 生产环境校验会拒绝默认 JWT_SECRET,测试环境强制 development
os.environ.setdefault("APP_ENV", "development")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

# 此时 import 才会读到上面的环境变量。
# 但 database.py 模块级 engine 已绑定为 SQLite in-memory,默认每个连接独立
# 会导致建表后连接关闭即丢表。这里替换为 StaticPool 单连接复用引擎,
# 保证 create_all / Session / drop_all 共用同一内存库。
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from config.settings import settings  # noqa: E402
import models.database as _db_mod  # noqa: E402

# 重建一个 StaticPool 的内存引擎覆盖模块级 engine
_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_db_mod.engine = _test_engine
_db_mod.SessionLocal.configure(bind=_test_engine)

from models.database import Base, engine, get_db  # noqa: E402, F811


@pytest.fixture()
def db_session():
    """每个测试独立的数据库会话。建表 → 测试 → 回滚 → 拆表。

    SQLite in-memory 库随 connection 生灭,用同一个 engine 时需保证
    connection 不提前释放(StaticPool 保证单连接复用)。
    """
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    """TestClient,把 get_db 依赖覆盖为返回测试 session。

    这样路由里的 db 操作都走 SQLite 内存库,互不干扰真实数据。
    """
    from main import app

    # 测试关闭限流中间件,避免短时间大量请求触发 429
    app.user_middleware = [
        m for m in app.user_middleware if "RateLimit" not in str(m)
    ]
    app.middleware_stack = app.build_middleware_stack()

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass  # 由 db_session fixture 负责关闭

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_token(client):
    """注册并登录一个测试用户,返回 access_token。"""
    client.post(
        "/api/auth/register",
        json={"username": "alice", "email": "alice@test.com", "password": "Pass1234!"},
    )
    resp = client.post(
        "/api/auth/login",
        json={"username": "alice", "password": "Pass1234!"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture()
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
