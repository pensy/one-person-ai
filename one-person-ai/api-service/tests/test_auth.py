"""认证流程单元测试:注册 / 登录 / 鉴权 / 边界。"""


def test_register_success(client):
    """正常注册:返回 201,字段齐全,默认积分 100。"""
    resp = client.post(
        "/api/auth/register",
        json={"username": "bob", "email": "bob@test.com", "password": "Secret123!"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["username"] == "bob"
    assert data["email"] == "bob@test.com"
    assert data["credits"] == 100
    assert data["role"] == "user"
    assert "password" not in resp.text  # 密码不应回显


def test_register_duplicate_username(client):
    """重复用户名:400。"""
    payload = {"username": "dup", "email": "dup1@test.com", "password": "Secret123!"}
    client.post("/api/auth/register", json=payload)
    payload["email"] = "dup2@test.com"  # 换邮箱,只测用户名冲突
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 400
    assert "用户名已存在" in resp.json()["detail"]


def test_register_duplicate_email(client):
    """重复邮箱:400。"""
    payload = {"username": "u1", "email": "same@test.com", "password": "Secret123!"}
    client.post("/api/auth/register", json=payload)
    payload["username"] = "u2"  # 换用户名,只测邮箱冲突
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 400
    assert "邮箱已被注册" in resp.json()["detail"]


def test_login_success(client):
    """登录成功:返回 JWT。"""
    client.post(
        "/api/auth/register",
        json={"username": "carol", "email": "carol@test.com", "password": "Secret123!"},
    )
    resp = client.post(
        "/api/auth/login",
        json={"username": "carol", "password": "Secret123!"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    assert token.count(".") == 2  # JWT 三段式
    assert resp.json()["token_type"] == "bearer"


def test_login_with_email(client):
    """用邮箱登录也应成功(支持用户名或邮箱)。"""
    client.post(
        "/api/auth/register",
        json={"username": "dave", "email": "dave@test.com", "password": "Secret123!"},
    )
    resp = client.post(
        "/api/auth/login",
        json={"username": "dave@test.com", "password": "Secret123!"},
    )
    assert resp.status_code == 200


def test_login_wrong_password(client):
    """密码错误:401。"""
    client.post(
        "/api/auth/register",
        json={"username": "eve", "email": "eve@test.com", "password": "Secret123!"},
    )
    resp = client.post(
        "/api/auth/login",
        json={"username": "eve", "password": "WrongPass!"},
    )
    assert resp.status_code == 401
    assert "用户名或密码错误" in resp.json()["detail"]


def test_login_nonexistent_user(client):
    """不存在的用户:401,且不泄露用户是否存在(同一错误信息)。"""
    resp = client.post(
        "/api/auth/login",
        json={"username": "ghost", "password": "anything"},
    )
    assert resp.status_code == 401


def test_me_with_valid_token(client, auth_headers):
    """/me 用合法 token 能拿到当前用户。"""
    resp = client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"


def test_me_without_token(client):
    """无 token 访问 /me:401(HTTPBearer 缺凭证时返回 401)。"""
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_with_invalid_token(client):
    """伪造 token:401。"""
    resp = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert resp.status_code == 401
