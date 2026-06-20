"""
認証・認可テスト。

このファイルは role escalation 防止を中心にテストする:
- health check
- register / duplicate email
- login success / failure
- refresh token / invalid token
- role escalation prevention（register で role を送ってもPATIENTになること）
"""
import pytest
from httpx import AsyncClient


async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_register_creates_patient(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@hospital.com", "password": "password123", "full_name": "テストユーザー"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@hospital.com"
    assert data["role"] == "patient"


@pytest.mark.parametrize("attempted_role", ["admin", "doctor", "nurse"])
async def test_register_role_escalation_prevented(client: AsyncClient, attempted_role):
    """
    register に role を含めて送っても、UserCreate スキーマに role フィールドが
    存在しないため無視され、常に patient として作成されることを確認する。
    これはセキュリティ上、最も重要なテストの一つ。
    """
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"escalate_{attempted_role}@hospital.com",
            "password": "password123",
            "full_name": "権限昇格試行ユーザー",
            "role": attempted_role,  # 無視されるべき
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "patient", f"role={attempted_role} を送ってもpatientになるべき"


async def test_duplicate_email_rejected(client: AsyncClient):
    payload = {"email": "dup@hospital.com", "password": "password123", "full_name": "重複ユーザー"}
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 400


async def test_login_success(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login@hospital.com", "password": "password123", "full_name": "ログインテスト"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@hospital.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "wrongpw@hospital.com", "password": "password123", "full_name": "テスト"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpw@hospital.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


async def test_login_unknown_user(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "notexist@hospital.com", "password": "password123"},
    )
    assert response.status_code == 401


async def test_refresh_token_success(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "refresh@hospital.com", "password": "password123", "full_name": "リフレッシュテスト"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@hospital.com", "password": "password123"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_refresh_token_invalid(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "this-is-not-a-valid-token"},
    )
    assert response.status_code == 401


async def test_access_protected_endpoint_without_token(client: AsyncClient):
    """トークンなしで認証必須エンドポイントにアクセスすると401になること。"""
    response = await client.get("/api/v1/tickets")
    assert response.status_code in (401, 403)


async def test_access_protected_endpoint_with_invalid_token(client: AsyncClient):
    response = await client.get(
        "/api/v1/tickets",
        headers={"Authorization": "Bearer invalid-token-value"},
    )
    assert response.status_code == 401
