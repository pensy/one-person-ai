import logging
import time

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.database import Tool, ToolCall, User, CreditLog, get_db
from models.auth import get_current_user
from models import deepseek
from worker_client import submit_task, get_task_status
from pydantic import BaseModel
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


class ToolOut(BaseModel):
    id: int
    name: str
    display_name: str
    description: str | None
    category: str
    credits_cost: int

    class Config:
        from_attributes = True


class ToolCallRequest(BaseModel):
    tool_name: str
    input_text: str


class ToolCallResponse(BaseModel):
    id: int
    status: str
    output_text: str | None
    credits_used: int


# Worker 轮询配置
WORKER_POLL_INTERVAL = 0.5  # 轮询间隔(秒)
WORKER_TIMEOUT = 60.0  # 同步等待上限(秒),超时按失败处理


def invoke_llm(tool_name: str, user_input: str) -> str:
    """统一 LLM 调用入口:优先走 Worker(gRPC 异步,同步等待结果),
    Worker 不可达时降级为 API 进程内同步直连。

    这样前端接口保持同步语义(一次请求拿到结果),同时把实际 LLM 计算
    卸载到 Worker,API 进程不被阻塞。
    """
    spec = deepseek.TOOL_SPECS.get(tool_name)
    if not spec:
        raise ValueError(f"未知工具: {tool_name}")

    payload = {
        "prompt": spec["prompt_template"].format(input=user_input),
        "system_prompt": spec["system_prompt"],
        "max_tokens": spec.get("max_tokens", 2000),
        "temperature": 0.7,
    }

    try:
        task_id = submit_task("LLM_CALL", payload)
        return _wait_for_task(task_id)
    except ConnectionError as e:
        logger.warning("Worker 不可达,降级同步直连: %s", e)
        return deepseek.call_tool_directly(tool_name, user_input)


def _wait_for_task(task_id: str) -> str:
    """轮询 Worker 任务直到完成或超时。"""
    deadline = time.monotonic() + WORKER_TIMEOUT
    while time.monotonic() < deadline:
        result = get_task_status(task_id)
        task_status = result.get("status", "")
        if task_status == "SUCCEEDED":
            return result.get("result", "")
        if task_status == "FAILED":
            raise RuntimeError(result.get("result", "任务执行失败"))
        # RUNNING / QUEUED —— 继续轮询
        time.sleep(WORKER_POLL_INTERVAL)
    raise TimeoutError(f"Worker 任务 {task_id} 超时({WORKER_TIMEOUT}s)")


@router.get("/", response_model=list[ToolOut])
async def list_tools(db: Session = Depends(get_db)):
    """获取可用工具列表"""
    tools = db.query(Tool).filter(Tool.is_active == True).order_by(Tool.sort_order).all()
    return tools


@router.post("/call", response_model=ToolCallResponse)
async def call_tool(
    req: ToolCallRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """调用 AI 工具"""
    tool = db.query(Tool).filter(
        Tool.name == req.tool_name, Tool.is_active == True
    ).first()
    if not tool:
        raise HTTPException(status_code=404, detail="工具不存在或未启用")

    if current_user.credits < tool.credits_cost:
        raise HTTPException(status_code=403, detail="积分不足")

    if tool.name not in deepseek.TOOL_SPECS:
        raise HTTPException(status_code=400, detail=f"工具 {req.tool_name} 暂未实现")

    # 调用 AI(走 Worker,不可达时降级同步直连)
    try:
        output = invoke_llm(tool.name, req.input_text)
        status_val = "success"
        error_msg = None
    except Exception as e:
        output = None
        status_val = "failed"
        error_msg = str(e)

    # 扣积分 + 记录
    current_user.credits -= tool.credits_cost
    tool_call = ToolCall(
        user_id=current_user.id,
        tool_id=tool.id,
        credits_used=tool.credits_cost,
        input_text=req.input_text[:500],
        output_text=output,
        status=status_val,
        error_msg=error_msg,
    )
    db.add(tool_call)

    # 积分变动记录
    credit_log = CreditLog(
        user_id=current_user.id,
        change_amount=-tool.credits_cost,
        balance_after=current_user.credits,
        reason=f"调用工具: {tool.display_name}",
        related_call_id=None,  # 需要在 commit 后回填
    )
    db.add(credit_log)
    db.commit()
    db.refresh(tool_call)

    # 回填 related_call_id
    credit_log.related_call_id = tool_call.id
    db.commit()

    return ToolCallResponse(
        id=tool_call.id,
        status=tool_call.status,
        output_text=tool_call.output_text,
        credits_used=tool_call.credits_used,
    )


@router.get("/history")
async def get_call_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询当前用户的调用记录"""
    calls = (
        db.query(ToolCall)
        .filter(ToolCall.user_id == current_user.id)
        .order_by(ToolCall.created_at.desc())
        .limit(50)
        .all()
    )
    return calls
