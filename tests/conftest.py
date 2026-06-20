"""
共通テストフィクスチャ。

DBセットアップ・テストクライアント・各ロールの認証ヘルパーを提供する。
"""
import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.main import app
from app.models.user import User, UserRole

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:password@localhost:5432/hospital_poc_test",
)


@pytest.fixture(scope="function")
async def engine():
    _engine = create_async_engine(TEST_DATABASE_URL)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


@pytest.fixture
def session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def client(engine, session_factory):
    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def register_and_login(client: AsyncClient, email: str, password: str, full_name: str) -> dict:
    """患者として自己登録しログインしてAuthorizationヘッダーを返す。"""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
    )
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def create_staff_user(session_factory, email: str, password: str, full_name: str, role: UserRole) -> None:
    """
    register API は role を受け付けないため、医療スタッフ/管理者ユーザーは
    DBへ直接INSERTして用意する（管理者作成APIは本PRのスコープ外）。
    """
    async with session_factory() as session:
        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role=role,
        )
        session.add(user)
        await session.commit()


@pytest.fixture
async def admin_headers(client, session_factory):
    await create_staff_user(session_factory, "admin@hospital.com", "adminpass123", "管理者", UserRole.ADMIN)
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "admin@hospital.com", "password": "adminpass123"}
    )
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
async def nurse_headers(client, session_factory):
    await create_staff_user(session_factory, "nurse@hospital.com", "nursepass123", "看護師", UserRole.NURSE)
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "nurse@hospital.com", "password": "nursepass123"}
    )
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
async def doctor_headers(client, session_factory):
    await create_staff_user(session_factory, "doctor@hospital.com", "doctorpass123", "医師", UserRole.DOCTOR)
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "doctor@hospital.com", "password": "doctorpass123"}
    )
    assert resp.status_code == 200
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
async def patient_headers(client):
    return await register_and_login(client, "patient@hospital.com", "patientpass123", "患者A")
