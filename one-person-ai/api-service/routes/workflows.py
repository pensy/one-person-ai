"""多步工作流编排。

把多个单次 LLM 工具按顺序串联:前一步的输出作为后一步的输入。
编排发生在 API 层(Python),复用 routes.tools.invoke_llm,自动享受
Worker gRPC 路径 + 不可达降级。proto / worker 无需改动。
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.auth import get_current_user
from models.database import Tool, ToolCall, CreditLog, User, get_db
from models import deepseek
from routes.tools import invoke_llm

router = APIRouter()


# 工作流模板:每步复用 TOOL_SPECS 里已有的工具。
# 第一步用用户原始输入;后续步骤把上一步输出作为输入。
# credits_cost 取各步工具 credits_cost 之和,在运行时按 DB 实际值核算。
WORKFLOW_SPECS: dict[str, dict] = {
    "code_full_review": {
        "name": "code_full_review",
        "display_name": "代码全流程审查",
        "description": "代码解释 → 代码审查 → 文本润色,一条龙产出可读的审查报告",
        "steps": [
            {"tool": "code_explain", "label": "代码解释"},
            {"tool": "code_review", "label": "代码审查"},
            {"tool": "text_polish", "label": "报告润色"},
        ],
    },
    "doc_pipeline": {
        "name": "doc_pipeline",
        "display_name": "文档生成流水线",
        "description": "内容摘要 → API 文档生成,从需求文本直接产出接口文档",
        "steps": [
            {"tool": "text_summary", "label": "需求摘要"},
            {"tool": "api_doc", "label": "文档生成"},
        ],
    },
}


class WorkflowStepOut(BaseModel):
    label: str
    tool: str
    status: str
    output: str | None
    error: str | None


class WorkflowOut(BaseModel):
    name: str
    display_name: str
    description: str
    steps: list[dict]
    credits_cost: int


class WorkflowRunRequest(BaseModel):
    workflow_name: str
    input_text: str


class WorkflowRunResponse(BaseModel):
    id: int
    status: str
    steps: list[WorkflowStepOut]
    credits_used: int


def _workflow_credits(steps: list[dict], db: Session) -> int:
    """按 DB 里各步工具的 credits_cost 求和。"""
    names = [s["tool"] for s in steps]
    tools = db.query(Tool).filter(Tool.name.in_(names)).all()
    cost_map = {t.name: t.credits_cost for t in tools}
    return sum(cost_map.get(s["tool"], 0) for s in steps)


@router.get("/", response_model=list[WorkflowOut])
async def list_workflows(db: Session = Depends(get_db)):
    """列出可用工作流模板(含每步积分核算)。"""
    result = []
    for spec in WORKFLOW_SPECS.values():
        result.append(
            WorkflowOut(
                name=spec["name"],
                display_name=spec["display_name"],
                description=spec["description"],
                steps=spec["steps"],
                credits_cost=_workflow_credits(spec["steps"], db),
            )
        )
    return result


@router.post("/run", response_model=WorkflowRunResponse)
async def run_workflow(
    req: WorkflowRunRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """运行多步工作流:顺序调用各步工具,链式传递输出。"""
    spec = WORKFLOW_SPECS.get(req.workflow_name)
    if not spec:
        raise HTTPException(status_code=404, detail="工作流不存在")

    total_cost = _workflow_credits(spec["steps"], db)
    if current_user.credits < total_cost:
        raise HTTPException(status_code=403, detail="积分不足")

    # 校验每步工具存在且已实现
    for step in spec["steps"]:
        if step["tool"] not in deepseek.TOOL_SPECS:
            raise HTTPException(
                status_code=400, detail=f"工具 {step['tool']} 暂未实现"
            )

    # 顺序执行各步,前一步输出喂给下一步
    step_results: list[WorkflowStepOut] = []
    current_input = req.input_text
    overall_status = "success"

    for step in spec["steps"]:
        label = step["label"]
        tool_name = step["tool"]
        try:
            out = invoke_llm(tool_name, current_input)
            step_results.append(
                WorkflowStepOut(
                    label=label, tool=tool_name, status="success",
                    output=out, error=None,
                )
            )
            current_input = out  # 链式传递
        except Exception as e:
            step_results.append(
                WorkflowStepOut(
                    label=label, tool=tool_name, status="failed",
                    output=None, error=str(e),
                )
            )
            overall_status = "failed"
            break  # 某步失败,后续不再执行

    # 取第一步工具作为 ToolCall 关联(工作流整体记一条)
    first_tool = db.query(Tool).filter(
        Tool.name == spec["steps"][0]["tool"]
    ).first()

    # 拼接各步输出作为整体 output(失败时含错误)
    if overall_status == "success":
        output_text = current_input  # 最后一步输出
        error_msg = None
    else:
        output_text = None
        error_msg = "; ".join(
            f"{s.label}: {s.error}" for s in step_results if s.error
        )

    # 扣积分(已执行步数 × 各步成本;失败也扣已消耗的)
    executed_cost = sum(
        _step_cost(s.tool, db) for s in step_results
    )
    current_user.credits -= executed_cost

    tool_call = ToolCall(
        user_id=current_user.id,
        tool_id=first_tool.id if first_tool else 0,
        credits_used=executed_cost,
        input_text=req.input_text[:500],
        output_text=output_text,
        status=overall_status,
        error_msg=error_msg,
    )
    db.add(tool_call)

    credit_log = CreditLog(
        user_id=current_user.id,
        change_amount=-executed_cost,
        balance_after=current_user.credits,
        reason=f"工作流: {spec['display_name']}",
        related_call_id=None,
    )
    db.add(credit_log)
    db.commit()
    db.refresh(tool_call)

    credit_log.related_call_id = tool_call.id
    db.commit()

    return WorkflowRunResponse(
        id=tool_call.id,
        status=overall_status,
        steps=step_results,
        credits_used=executed_cost,
    )


def _step_cost(tool_name: str, db: Session) -> int:
    """查单个工具的 credits_cost。"""
    t = db.query(Tool).filter(Tool.name == tool_name).first()
    return t.credits_cost if t else 0
