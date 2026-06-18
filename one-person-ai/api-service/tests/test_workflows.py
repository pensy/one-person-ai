"""工作流编排单元测试:链式执行 / 积分扣减 / 步骤失败中断。"""
from models.database import Tool, User


def _seed_tools(db_session):
    """注入工作流所需的工具到 SQLite 库。"""
    tools = [
        Tool(name="code_explain", display_name="代码解释器", description="d",
             category="code", credits_cost=1, is_active=True, sort_order=1),
        Tool(name="code_review", display_name="代码审查", description="d",
             category="code", credits_cost=2, is_active=True, sort_order=2),
        Tool(name="text_polish", display_name="文本润色", description="d",
             category="text", credits_cost=1, is_active=True, sort_order=3),
        Tool(name="text_summary", display_name="内容摘要", description="d",
             category="text", credits_cost=1, is_active=True, sort_order=4),
        Tool(name="api_doc", display_name="API文档", description="d",
             category="code", credits_cost=2, is_active=True, sort_order=5),
    ]
    for t in tools:
        db_session.add(t)
    db_session.commit()


def test_list_workflows(client, db_session):
    """工作流列表返回模板 + 积分核算。"""
    _seed_tools(db_session)
    resp = client.get("/api/workflows/")
    assert resp.status_code == 200
    data = resp.json()
    names = {w["name"] for w in data}
    assert "code_full_review" in names
    assert "doc_pipeline" in names

    wf = next(w for w in data if w["name"] == "code_full_review")
    assert wf["credits_cost"] == 4  # 1+2+1
    assert len(wf["steps"]) == 3


def test_workflow_chains_outputs(client, auth_headers, db_session, monkeypatch):
    """成功链式执行:前一步输出喂给下一步。"""
    _seed_tools(db_session)

    # 打桩 invoke_llm,记录每步收到的输入,验证链式传递
    calls = []

    def _fake_invoke(tool_name, user_input):
        calls.append((tool_name, user_input))
        return f"[{tool_name}输出] 输入是: {user_input[:20]}"

    monkeypatch.setattr("routes.workflows.invoke_llm", _fake_invoke)

    resp = client.post(
        "/api/workflows/run",
        json={"workflow_name": "code_full_review", "input_text": "def f(): pass"},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "success"
    assert len(data["steps"]) == 3

    # 第一步拿到原始输入
    assert calls[0][0] == "code_explain"
    assert calls[0][1] == "def f(): pass"
    # 第二步拿到第一步的输出
    assert calls[1][0] == "code_review"
    assert calls[1][1].startswith("[code_explain输出]")
    # 第三步拿到第二步的输出
    assert calls[2][0] == "text_polish"
    assert calls[2][1].startswith("[code_review输出]")

    # 积分扣减:100 - 4 = 96
    user = db_session.query(User).filter(User.username == "alice").first()
    assert user.credits == 96


def test_workflow_stops_on_step_failure(client, auth_headers, db_session, monkeypatch):
    """某步失败时中断,后续步骤不执行,仍扣已执行步数积分。"""
    _seed_tools(db_session)

    step_count = {"n": 0}

    def _fake_invoke(tool_name, user_input):
        step_count["n"] += 1
        if step_count["n"] == 2:  # 第二步(code_review)失败
            raise RuntimeError("code_review 挂了")
        return f"[{tool_name}] ok"

    monkeypatch.setattr("routes.workflows.invoke_llm", _fake_invoke)

    resp = client.post(
        "/api/workflows/run",
        json={"workflow_name": "code_full_review", "input_text": "x"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "failed"
    assert len(data["steps"]) == 2  # 只执行了 2 步
    assert data["steps"][0]["status"] == "success"
    assert data["steps"][1]["status"] == "failed"
    assert "code_review 挂了" in data["steps"][1]["error"]

    # 扣已执行步数:code_explain(1) + code_review(2) = 3
    assert data["credits_used"] == 3
    user = db_session.query(User).filter(User.username == "alice").first()
    assert user.credits == 97  # 100 - 3


def test_workflow_insufficient_credits(client, auth_headers, db_session, monkeypatch):
    """积分不足:403,不执行任何步骤。"""
    _seed_tools(db_session)
    user = db_session.query(User).filter(User.username == "alice").first()
    user.credits = 2  # 工作流要 4
    db_session.commit()

    called = {"n": 0}
    monkeypatch.setattr(
        "routes.workflows.invoke_llm",
        lambda *a: called.__setitem__("n", called["n"] + 1) or "x",
    )

    resp = client.post(
        "/api/workflows/run",
        json={"workflow_name": "code_full_review", "input_text": "x"},
        headers=auth_headers,
    )
    assert resp.status_code == 403
    assert "积分不足" in resp.json()["detail"]
    assert called["n"] == 0


def test_workflow_unknown_name(client, auth_headers):
    """未知工作流名:404。"""
    resp = client.post(
        "/api/workflows/run",
        json={"workflow_name": "not_exist", "input_text": "x"},
        headers=auth_headers,
    )
    assert resp.status_code == 404
