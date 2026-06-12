from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.database import Tool, ToolCall, User, CreditLog, get_db
from models.auth import get_current_user
from models import deepseek
from pydantic import BaseModel
from datetime import datetime

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


# 工具名称 -> 实际调用函数的映射
TOOL_HANDLERS = {
    "code_explain": deepseek.explain_code,
    "code_review": deepseek.review_code,
    "text_polish": deepseek.polish_text,
    "text_summary": deepseek.summarize_text,
}


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

    handler = TOOL_HANDLERS.get(req.tool_name)
    if not handler:
        raise HTTPException(status_code=400, detail=f"工具 {req.tool_name} 暂未实现")

    # 调用 AI
    try:
        output = handler(req.input_text)
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
