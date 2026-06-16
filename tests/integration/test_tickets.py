import os
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.main import app
from app.models.ticket import AICategory, TicketPriority

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:password@db:5432/hospital_poc_test",
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
async def client(engine):
    TestSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with TestSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def auth_headers(client):
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "nurse@hospital.com",
            "password": "password123",
            "full_name": "看護師",
            "role": "nurse",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nurse@hospital.com", "password": "password123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def patient_id(client, auth_headers):
    response = await client.post(
        "/api/v1/patients",
        json={"patient_number": "P001", "name": "テスト患者"},
        headers=auth_headers,
    )
    return response.json()["id"]


async def test_create_ticket(client, auth_headers, patient_id):
    with patch(
        "app.api.v1.endpoints.tickets.run_ai_classification",
        new_callable=AsyncMock,
    ):
        response = await client.post(
            "/api/v1/tickets",
            json={
                "patient_id": patient_id,
                "title": "頭痛がする",
                "description": "昨日から頭痛が続いています",
                "priority": "NORMAL",
            },
            headers=auth_headers,
        )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "頭痛がする"
    assert data["status"] == "NEW"
    assert data["priority"] == "NORMAL"


async def test_list_tickets(client, auth_headers, patient_id):
    with patch(
        "app.api.v1.endpoints.tickets.run_ai_classification",
        new_callable=AsyncMock,
    ):
        await client.post(
            "/api/v1/tickets",
            json={
                "patient_id": patient_id,
                "title": "発熱",
                "description": "38度の熱があります",
                "priority": "HIGH",
            },
            headers=auth_headers,
        )
    response = await client.get("/api/v1/tickets", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1


async def test_update_ticket(client, auth_headers, patient_id):
    with patch(
        "app.api.v1.endpoints.tickets.run_ai_classification",
        new_callable=AsyncMock,
    ):
        create_response = await client.post(
            "/api/v1/tickets",
            json={
                "patient_id": patient_id,
                "title": "腹痛",
                "description": "お腹が痛いです",
                "priority": "NORMAL",
            },
            headers=auth_headers,
        )
    ticket_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/tickets/{ticket_id}",
        json={"status": "NURSE_REVIEW"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "NURSE_REVIEW"
