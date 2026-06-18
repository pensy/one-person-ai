"""工具调用路径单元测试:Worker 不可达时的降级回退。

验证 invoke_llm 的两条路径:
1. Worker 正常 → 走 gRPC 异步轮询
2. Worker 抛 ConnectionError → 降级到 call_tool_directly 同步直连
"""
import pytest


def test_invoke_llm_worker_success(monkeypatch):
    """Worker 路径成功:submit_task + 轮询 get_task_status 返回结果。"""
    import routes.tools as tools

    # 打桩 worker_client 的两个函数
    monkeypatch.setattr(tools, "submit_task", lambda t, p: "task-123")
    monkeypatch.setattr(
        tools,
        "get_task_status",
        lambda tid: {"status": "SUCCEEDED", "result": "Worker 处理结果"},
    )
    # 确保降级路径不被触发
    monkeypatch.setattr(
        tools.deepseek, "call_tool_directly",
        lambda *a, **k: pytest.fail("不应走降级路径"),
    )

    out = tools.invoke_llm("code_explain", "print(1)")
    assert out == "Worker 处理结果"


def test_invoke_llm_worker_unreachable_fallback(monkeypatch):
    """Worker 不可达:submit_task 抛 ConnectionError → 降级同步直连。"""
    import routes.tools as tools

    def _conn_error(task_type, payload):
        raise ConnectionError("Worker 不可达: UNAVAILABLE")

    monkeypatch.setattr(tools, "submit_task", _conn_error)
    monkeypatch.setattr(
        tools.deepseek, "call_tool_directly",
        lambda tool, inp: "降级直连结果",
    )

    out = tools.invoke_llm("text_polish", "测试文本")
    assert out == "降级直连结果"


def test_invoke_llm_worker_running_then_success(monkeypatch):
    """轮询:先 RUNNING,再 SUCCEEDED。"""
    import routes.tools as tools

    states = iter([
        {"status": "RUNNING", "result": ""},
        {"status": "RUNNING", "result": ""},
        {"status": "SUCCEEDED", "result": "最终结果"},
    ])
    monkeypatch.setattr(tools, "submit_task", lambda t, p: "task-456")
    monkeypatch.setattr(tools, "get_task_status", lambda tid: next(states))
    # 加速轮询,避免测试卡 0.5s * 2
    monkeypatch.setattr(tools.time, "sleep", lambda s: None)

    out = tools.invoke_llm("regex_generate", "匹配邮箱")
    assert out == "最终结果"


def test_invoke_llm_worker_failed(monkeypatch):
    """Worker 返回 FAILED:抛 RuntimeError。"""
    import routes.tools as tools

    monkeypatch.setattr(tools, "submit_task", lambda t, p: "task-789")
    monkeypatch.setattr(
        tools,
        "get_task_status",
        lambda tid: {"status": "FAILED", "result": "DeepSeek 鉴权失败"},
    )
    with pytest.raises(RuntimeError, match="DeepSeek 鉴权失败"):
        tools.invoke_llm("code_explain", "x")


def test_invoke_llm_unknown_tool():
    """未知工具名:抛 ValueError(spec 不存在)。"""
    import routes.tools as tools

    with pytest.raises(ValueError, match="未知工具"):
        tools.invoke_llm("not_a_tool", "x")


def test_invoke_llm_payload_uses_max_tokens_spec(monkeypatch):
    """sql_generate 等 max_tokens:3000 的工具,payload 应带上 3000。"""
    import routes.tools as tools

    captured = {}

    def _capture(task_type, payload):
        captured["payload"] = payload
        return "task-spec"

    monkeypatch.setattr(tools, "submit_task", _capture)
    monkeypatch.setattr(
        tools, "get_task_status",
        lambda tid: {"status": "SUCCEEDED", "result": "ok"},
    )

    tools.invoke_llm("sql_generate", "查询所有用户")
    assert captured["payload"]["max_tokens"] == 3000

    tools.invoke_llm("code_explain", "x")
    assert captured["payload"]["max_tokens"] == 2000  # 默认值
