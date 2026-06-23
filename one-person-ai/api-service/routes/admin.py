"""管理后台路由。"""

import logging

import grpc
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from config.settings import settings
from models.auth import get_current_user
from models.database import Tool, User, get_db, engine

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status")
async def admin_status():
    """返回各服务运行状态。"""
    status = {
        "api": {"status": "ok", "version": "0.2.0"},
        "mysql": {"status": "unknown"},
        "worker": {"status": "unknown"},
    }

    # MySQL 检查
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        status["mysql"] = {"status": "ok"}
    except Exception as e:
        status["mysql"] = {"status": "error", "message": str(e)}

    # Worker gRPC 检查
    try:
        channel = grpc.insecure_channel(settings.WORKER_ADDR)
        # 超时 3 秒看能否连上
        grpc.channel_ready_future(channel).result(timeout=3)
        channel.close()
        status["worker"] = {"status": "ok"}
    except Exception as e:
        status["worker"] = {"status": "error", "message": f"Worker 不可达: {e}"}

    return status


@router.get("/users")
async def admin_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """返回用户列表（仅管理员，暂不设权限校验）。"""
    users = db.query(User).order_by(User.created_at.desc()).limit(100).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "credits": u.credits,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@router.put("/tools/{tool_id}/toggle")
async def admin_toggle_tool(
    tool_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """启用/禁用一个工具。"""
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="工具不存在")

    tool.is_active = not tool.is_active
    db.commit()

    return {
        "id": tool.id,
        "name": tool.name,
        "display_name": tool.display_name,
        "is_active": tool.is_active,
    }
