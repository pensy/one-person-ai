"""按用户/IP 限流中间件。

防止恶意刷接口导致 LLM API 额度被耗尽。基于内存的滑动窗口计数,
适用于单实例部署;多实例时需替换为 Redis 实现。
"""
import time
from collections import defaultdict
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """简单的内存限流。每个标识(用户 ID 或 IP)在窗口内最多 N 次请求。

    Args:
        max_requests: 窗口内最大请求数
        window_seconds: 窗口大小(秒)
    """

    def __init__(self, app, max_requests: int = 20, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # {identifier: [timestamp, ...]}
        self._hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # 仅对写操作(POST/PUT/DELETE)和调用类接口限流,GET 不限
        if request.method == "GET":
            return await call_next(request)

        identifier = self._get_identifier(request)
        now = time.time()
        window_start = now - self.window_seconds

        # 清理过期记录
        hits = [t for t in self._hits[identifier] if t > window_start]
        if len(hits) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - hits[0]))
            return JSONResponse(
                status_code=429,
                content={"detail": f"请求过于频繁,请 {retry_after} 秒后重试"},
                headers={"Retry-After": str(max(retry_after, 1))},
            )

        hits.append(now)
        self._hits[identifier] = hits
        return await call_next(request)

    def _get_identifier(self, request: Request) -> str:
        """优先用已认证用户 ID,否则用客户端 IP。"""
        # 从 JWT 解析出的 user_id(若 auth 依赖已设置到 request.state)
        user_id = getattr(request.state, "user_id", None)
        if user_id is not None:
            return f"user:{user_id}"
        # 兜底用 IP(考虑反向代理)
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        client = request.client
        return f"ip:{client.host if client else 'unknown'}"
