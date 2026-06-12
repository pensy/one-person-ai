from sqlalchemy import create_engine, Column, Integer, String, Text, Enum, Boolean, DateTime, Index, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from config.settings import DATABASE_URL

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"comment": "用户表"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, nullable=False, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    credits = Column(Integer, nullable=False, default=100, comment="积分余额")
    role = Column(Enum("user", "admin", name="user_role"), nullable=False, default="user")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class Tool(Base):
    __tablename__ = "tools"
    __table_args__ = {"comment": "AI工具表"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, comment="工具名称")
    display_name = Column(String(100), nullable=False, comment="显示名称")
    description = Column(Text, comment="工具描述")
    category = Column(String(30), nullable=False, comment="分类")
    credits_cost = Column(Integer, nullable=False, default=1, comment="单次消耗积分")
    is_active = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class ToolCall(Base):
    __tablename__ = "tool_calls"
    __table_args__ = (
        Index("idx_user_tool", "user_id", "tool_id"),
        Index("idx_created_at", "created_at"),
        {"comment": "工具调用记录表"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tool_id = Column(Integer, ForeignKey("tools.id", ondelete="CASCADE"), nullable=False)
    credits_used = Column(Integer, nullable=False)
    input_text = Column(Text, comment="输入内容")
    output_text = Column(Text, comment="输出内容")
    status = Column(Enum("success", "failed", "pending", name="call_status"), nullable=False, default="pending")
    error_msg = Column(Text, comment="失败原因")
    ip_address = Column(String(45), comment="IP地址")
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class CreditLog(Base):
    __tablename__ = "credit_logs"
    __table_args__ = (
        Index("idx_user_created", "user_id", "created_at"),
        {"comment": "积分变动记录表"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    change_amount = Column(Integer, nullable=False, comment="变动数量，正增负减")
    balance_after = Column(Integer, nullable=False, comment="变动后余额")
    reason = Column(String(200), nullable=False, comment="变动原因")
    related_call_id = Column(Integer, ForeignKey("tool_calls.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


engine = create_engine(DATABASE_URL, echo=True)


def get_engine():
    return engine


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
