"""GitHub App Webhook 路由。

接收 GitHub 推送的 PR 事件，自动触发 AI 审查。
"""
import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, Request, HTTPException

from config.settings import settings
from services import github, github_app
from services.github import GitHubError
from worker_client import submit_task
from routes.tools import _wait_for_task

logger = logging.getLogger(__name__)

router = APIRouter()


def _verify_signature(payload: bytes, signature_header: str) -> bool:
    """验证 Webhook 签名(X-Hub-Signature-256)。

    用 Webhook Secret 对请求体做 HMAC-SHA256,与 GitHub 发来的签名比对。
    """
    if not settings.GITHUB_WEBHOOK_SECRET:
        logger.warning("GITHUB_WEBHOOK_SECRET 未设置,跳过签名验证")
        return True

    expected = "sha256=" + hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


@router.post("/webhook")
async def github_webhook(request: Request):
    """处理 GitHub 发来的 Webhook 事件。"""
    # 读取原始请求体
    body = await request.body()

    # 签名验证
    sig = request.headers.get("x-hub-signature-256", "")
    if not _verify_signature(body, sig):
        raise HTTPException(status_code=401, detail="签名验证失败")

    # 解析事件
    event = request.headers.get("x-github-event", "")
    if event != "pull_request":
        # 非 PR 事件直接忽略
        return {"status": "ignored", "event": event}

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="无效的请求体")

    action = data.get("action", "")
    if action not in ("opened", "synchronize"):
        return {"status": "ignored", "action": action}

    # 提取 PR 信息
    pr = data.get("pull_request", {})
    repo_full_name = data.get("repository", {}).get("full_name", "")
    pr_number = pr.get("number", 0)
    installation_id = data.get("installation", {}).get("id", 0)
    pr_title = pr.get("title", "")

    if not all([repo_full_name, pr_number, installation_id]):
        raise HTTPException(status_code=400, detail="缺少必要字段")

    logger.info("收到 PR 事件: %s #%d - %s", repo_full_name, pr_number, pr_title)

    # 用安装 token 拉取 diff
    try:
        token = github_app.get_installation_token(installation_id)
        diff = github.get_pr_diff(token, repo_full_name, pr_number)
    except (GitHubError, Exception) as e:
        logger.error("拉取 diff 失败: %s", e)
        return {"status": "error", "message": str(e)}

    if not diff.strip():
        return {"status": "skipped", "reason": "PR 无 diff 内容"}

    # 提交审查任务到 Worker
    try:
        task_id = submit_task("PR_REVIEW", {
            "diff": diff,
            "repo": repo_full_name,
            "pr_number": pr_number,
        })
        result = _wait_for_task(task_id)
    except Exception as e:
        logger.error("审查任务失败: %s", e)
        return {"status": "error", "message": str(e)}

    # 用安装 token 发布审查评论
    try:
        token = github_app.get_installation_token(installation_id)
        comment = f"""## 🤖 AI 代码审查报告

> 仓库: {repo_full_name} | PR #{pr_number}

---

{result}

---
*由 One Person AI 自动审查*"""
        github_app.post_pr_comment(repo_full_name, pr_number, token, comment)
    except Exception as e:
        logger.error("发布评论失败: %s", e)

    return {"status": "success", "pr": f"{repo_full_name}#{pr_number}"}
