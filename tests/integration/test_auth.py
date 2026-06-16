import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings

TEST_DATABASE_URL = settings.DATABASE_URL.replace(
    "hospital_poc", "hospital_poc_test"
)

engine = create_async_engine(TEST_DATABASE_URL)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


async def test_register(client):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@hospital.com",
            "password": "password123",
            "full_name": "テストユーザー",
            "role": "nurse",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@hospital.com"
    assert data["role"] == "nurse"


async def test_login(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@hospital.com",
            "password": "password123",
            "full_name": "テストユーザー",
            "role": "nurse",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@hospital.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_wrong_password(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@hospital.com",
            "password": "password123",
            "full_name": "テストユーザー",
            "role": "nurse",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@hospital.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
