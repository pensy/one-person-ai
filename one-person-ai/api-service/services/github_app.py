"""GitHub App 服务端工具。

提供 JWT 生成、安装 token 获取、PR 评论发布等功能。
"""
import time
import logging
from pathlib import Path

import httpx
import jwt

from config.settings import settings

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"


def _load_private_key() -> str:
    """从文件加载 GitHub App 私钥。"""
    path = Path(settings.GITHUB_PRIVATE_KEY_PATH)
    if not path.exists():
        raise FileNotFoundError(f"GitHub App 私钥文件不存在: {path}")
    return path.read_text()


def _generate_jwt() -> str:
    """生成 GitHub App JWT(有效期 10 分钟)。"""
    key = _load_private_key()
    now = int(time.time())
    payload = {
        "iat": now - 60,        # 允许 60 秒时钟偏差
        "exp": now + 600,       # 10 分钟有效期
        "iss": settings.GITHUB_APP_ID,
    }
    return jwt.encode(payload, key, algorithm="RS256")


def get_installation_token(installation_id: int) -> str:
    """获取 GitHub App 安装的访问 token。

    Args:
        installation_id: GitHub App 安装 ID(来自 webhook 事件)
    Returns:
        安装 token 字符串
    """
    jwt_token = _generate_jwt()
    url = f"{GITHUB_API}/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
    }
    try:
        resp = httpx.post(url, headers=headers, timeout=15.0)
        resp.raise_for_status()
        data = resp.json()
        return data["token"]
    except httpx.HTTPError as e:
        logger.error("获取安装 token 失败: %s", e)
        raise


def post_pr_comment(repo: str, pr_number: int, token: str, body: str):
    """在 PR 上发表审查评论。

    Args:
        repo: owner/repo 格式
        pr_number: PR 编号
        token: 安装 token
        body: 评论内容(Markdown)
    """
    url = f"{GITHUB_API}/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }
    try:
        resp = httpx.post(url, headers=headers, json={"body": body}, timeout=15.0)
        resp.raise_for_status()
        logger.info("PR #%d 评论已发布", pr_number)
    except httpx.HTTPError as e:
        logger.error("发布 PR 评论失败: %s", e)
        raise


def get_installation_id(repo: str, token: str) -> int:
    """通过仓库名获取 GitHub App 安装 ID。

    用于已知 repo 但不清楚 installation_id 的场景。
    """
    url = f"{GITHUB_API}/repos/{repo}/installation"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = httpx.get(url, headers=headers, timeout=15.0)
        resp.raise_for_status()
        return resp.json()["id"]
    except httpx.HTTPError as e:
        logger.error("获取安装 ID 失败: %s", e)
        raise
