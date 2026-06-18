"""积分系统单元测试:扣减 / 余额不足 / 变动记录。

工具调用涉及 LLM,这里通过 monkeypatch 把 invoke_llm 打桩,
隔离 LLM 与 Worker,只测积分扣减逻辑。
"""
from models.database import User


def test_credits_initial_balance(client, auth_headers):
    """新注册用户默认 100 积分。"""
    resp = client.get("/api/auth/me", headers=auth_headers)
    assert resp.json()["credits"] == 100


def test_credits_deducted_on_call(client, auth_headers, db_session, monkeypatch):
    """成功调用工具后积分正确扣减,且写入 credit_logs。"""
    from models.database import Tool, CreditLog

    # 注入一个测试工具到 SQLite 库
    db_session.add(
        Tool(
            name="text_polish",
            display_name="文本润色",
            description="润色",
            category="text",
            credits_cost=3,
            is_active=True,
            sort_order=1,
        )
    )
    db_session.commit()

    # 打桩 LLM 调用,不触达真实 Worker / DeepSeek
    monkeypatch.setattr(
        "routes.tools.invoke_llm", lambda tool, inp: "润色后的文本"
    )

    resp = client.post(
        "/api/tools/call",
        json={"tool_name": "text_polish", "input_text": "测试文本"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "success"
    assert resp.json()["credits_used"] == 3

    # 校验积分余额(100 - 3 = 97)
    user = db_session.query(User).filter(User.username == "alice").first()
    assert user.credits == 97

    # 校验积分变动记录
    logs = db_session.query(CreditLog).filter(CreditLog.user_id == user.id).all()
    assert len(logs) == 1
    assert logs[0].change_amount == -3
    assert logs[0].balance_after == 97


def test_credits_insufficient_rejected(client, auth_headers, db_session, monkeypatch):
    """积分不足时调用被拒(403),不扣积分、不调 LLM。"""
    from models.database import Tool

    db_session.add(
        Tool(
            name="code_review",
            display_name="代码审查",
            description="审查",
            category="code",
            credits_cost=2,
            is_active=True,
            sort_order=2,
        )
    )
    # 把用户积分耗到只剩 1,工具要 2
    user = db_session.query(User).filter(User.username == "alice").first()
    user.credits = 1
    db_session.commit()

    # 打桩:若被调用说明逻辑错了,测试会失败
    called = {"n": 0}

    def _should_not_call(tool, inp):
        called["n"] += 1
        return "should not reach"

    monkeypatch.setattr("routes.tools.invoke_llm", _should_not_call)

    resp = client.post(
        "/api/tools/call",
        json={"tool_name": "code_review", "input_text": "x"},
        headers=auth_headers,
    )
    assert resp.status_code == 403
    assert "积分不足" in resp.json()["detail"]
    assert called["n"] == 0  # LLM 未被调用

    # 积分未变
    db_session.refresh(user)
    assert user.credits == 1


def test_credits_not_deducted_on_llm_failure(client, auth_headers, db_session, monkeypatch):
    """LLM 调用失败时:记录 status=failed,但仍扣积分(当前业务设计)。

    注:当前实现无论成功失败都扣积分(调用即消耗资源)。
    此测试固化该行为;若未来改为失败退积分,需同步改这里。
    """
    from models.database import Tool, ToolCall

    db_session.add(
        Tool(
            name="text_summary",
            display_name="摘要",
            description="摘要",
            category="text",
            credits_cost=1,
            is_active=True,
            sort_order=3,
        )
    )
    db_session.commit()

    def _raise(tool, inp):
        raise RuntimeError("LLM 挂了")

    monkeypatch.setattr("routes.tools.invoke_llm", _raise)

    resp = client.post(
        "/api/tools/call",
        json={"tool_name": "text_summary", "input_text": "长文本"},
        headers=auth_headers,
    )
    # 失败时接口仍返回 200(把失败信息包进 response),还是抛 500?
    # 看 tools.py:except 捕获后 status_val=failed,继续走扣积分 + 返回 ToolCallResponse
    assert resp.status_code == 200
    assert resp.json()["status"] == "failed"
    assert resp.json()["credits_used"] == 1

    # 积分照扣(当前业务设计)
    user = db_session.query(User).filter(User.username == "alice").first()
    assert user.credits == 99

    # 调用记录标记为 failed
    call = db_session.query(ToolCall).first()
    assert call.status == "failed"
    assert call.error_msg == "LLM 挂了"
