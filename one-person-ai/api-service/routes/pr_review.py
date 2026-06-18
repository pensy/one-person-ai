"""GitHub PR 审查路由。

用户输入仓库、PR 编号和 GitHub PAT,后端拉取 diff 后提交 PR_REVIEW
任务到 Worker,轮询拿到 LLM 审查报告。Worker 不可达时直接报错
(无 clean 降级,PR 审查强依赖 Worker 的 LLM 调用)。
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.auth import get_current_user
from models.database import Tool, ToolCall, CreditLog, User, get_db
from routes.tools import _wait_for_task
from services import github
from worker_client import submit_task

logger = logging.getLogger(__name__)

router = APIRouter()

# PR 审查固定积分成本(比单次工具贵,因 diff 通常较大、审查更深入)
PR_REVIEW_CREDITS = 3


class PRReviewRequest(BaseModel):
    repo: str  # owner/repo 格式
    pr_number: int
    github_token: str


class PRReviewResponse(BaseModel):
    id: int
    status: str
    output_text: str | None
    credits_used: int


@router.post("/", response_model=PRReviewResponse)
async def review_pr(
    req: PRReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交 PR 审查:拉 diff → Worker PR_REVIEW → 返回审查报告。"""
    # 积分校验
    if current_user.credits < PR_REVIEW_CREDITS:
        raise HTTPException(status_code=403, detail="积分不足")

    # 1. 用 PAT 拉取 PR diff
    try:
        diff = github.get_pr_diff(req.github_token, req.repo, req.pr_number)
    except github.GitHubError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not diff.strip():
        raise HTTPException(status_code=400, detail="该 PR 无 diff 内容")

    # 2. 提交 PR_REVIEW 任务到 Worker
    payload = {
        "diff": diff,
        "repo": req.repo,
        "pr_number": req.pr_number,
    }
    try:
        task_id = submit_task("PR_REVIEW", payload)
        output = _wait_for_task(task_id)
        status_val = "success"
        error_msg = None
    except ConnectionError as e:
        # Worker 不可达,PR 审查无降级路径,直接报错
        logger.error("Worker 不可达,PR 审查失败: %s", e)
        raise HTTPException(
            status_code=503, detail=f"Worker 不可达,请稍后重试: {e}"
        )
    except Exception as e:
        output = None
        status_val = "failed"
        error_msg = str(e)

    # 3. 扣积分 + 记录(沿用 tools.py 模式)
    current_user.credits -= PR_REVIEW_CREDITS

    # PR 审查不关联具体 tool_id,用 0 占位(tool_calls.tool_id 是 FK,
    # 但 SQLite 测试库无约束;生产 MySQL 有 FK —— 这里取一个已存在工具
    # 的 id 避免约束冲突,语义上 PR 审查是独立功能)
    placeholder_tool = db.query(Tool).first()

    tool_call = ToolCall(
        user_id=current_user.id,
        tool_id=placeholder_tool.id if placeholder_tool else 0,
        credits_used=PR_REVIEW_CREDITS,
        input_text=f"{req.repo}#{req.pr_number}"[:500],
        output_text=output,
        status=status_val,
        error_msg=error_msg,
    )
    db.add(tool_call)

    credit_log = CreditLog(
        user_id=current_user.id,
        change_amount=-PR_REVIEW_CREDITS,
        balance_after=current_user.credits,
        reason=f"PR审查: {req.repo}#{req.pr_number}",
        related_call_id=None,
    )
    db.add(credit_log)
    db.commit()
    db.refresh(tool_call)

    credit_log.related_call_id = tool_call.id
    db.commit()

    return PRReviewResponse(
        id=tool_call.id,
        status=tool_call.status,
        output_text=tool_call.output_text,
        credits_used=tool_call.credits_used,
    )
