"""GitHub API 客户端。

用用户提供的 Personal Access Token(PAT,只读 repo 权限)拉取 PR diff。
Token 仅在请求生命周期内使用,不持久化、不落库。
"""
import httpx

GITHUB_API = "https://api.github.com"


class GitHubError(Exception):
    """GitHub API 调用失败。"""


def get_pr_diff(token: str, repo: str, pr_number: int) -> str:
    """拉取 PR 的 diff 文本。

    Args:
        token: GitHub PAT(需 repo 或 public_repo 权限)
        repo: owner/repo 格式,如 "octocat/Hello-World"
        pr_number: PR 编号
    Returns:
        diff 文本(application/vnd.github.v3.diff)
    Raises:
        GitHubError: API 错误(鉴权失败、PR 不存在等)
    """
    url = f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    # token 为空时走未认证(GitHub 允许公开仓库,但限流 60/小时);
    # 有 token 时带认证(5000/小时,且可访问私有仓库)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        resp = httpx.get(url, headers=headers, timeout=30.0)
    except httpx.HTTPError as e:
        raise GitHubError(f"请求 GitHub 失败: {e}") from e

    if resp.status_code == 401:
        raise GitHubError("GitHub PAT 无效或已过期")
    if resp.status_code == 404:
        raise GitHubError(f"PR 不存在: {repo}#{pr_number}(可能无权限访问私有仓库)")
    if resp.status_code != 200:
        raise GitHubError(
            f"GitHub API 返回 {resp.status_code}: {resp.text[:200]}"
        )
    return resp.text


def get_pr_info(token: str, repo: str, pr_number: int) -> dict:
    """拉取 PR 元信息(标题、作者、文件数等),用于上下文。

    Returns:
        {"title": ..., "user": ..., "changed_files": ...}
    """
    url = f"{GITHUB_API}/repos/{repo}/pulls/{pr_number}"
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        resp = httpx.get(url, headers=headers, timeout=30.0)
    except httpx.HTTPError as e:
        raise GitHubError(f"请求 GitHub 失败: {e}") from e

    if resp.status_code != 200:
        raise GitHubError(f"GitHub API 返回 {resp.status_code}")
    data = resp.json()
    return {
        "title": data.get("title", ""),
        "user": data.get("user", {}).get("login", ""),
        "changed_files": data.get("changed_files", 0),
    }
