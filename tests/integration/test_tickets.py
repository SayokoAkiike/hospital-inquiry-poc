"""
チケット関連テスト（既存実装の基本動作確認）。
"""
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient


async def _create_patient(client: AsyncClient, headers: dict, patient_number: str = "P001") -> str:
    resp = await client.post(
        "/api/v1/patients",
        json={"patient_number": patient_number, "name": "テスト患者"},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def test_create_ticket(client: AsyncClient, nurse_headers):
    patient_id = await _create_patient(client, nurse_headers, "P-TICKET-1")
    with patch("app.api.v1.endpoints.tickets.run_ai_classification", new_callable=AsyncMock):
        response = await client.post(
            "/api/v1/tickets",
            json={
                "patient_id": patient_id,
                "title": "頭痛がする",
                "description": "昨日から頭痛が続いています",
                "priority": "NORMAL",
            },
            headers=nurse_headers,
        )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "頭痛がする"
    assert data["status"] == "NEW"


async def test_list_tickets_denied_for_patient(client: AsyncClient, patient_headers):
    response = await client.get("/api/v1/tickets", headers=patient_headers)
    assert response.status_code == 403


async def test_list_tickets_allowed_for_nurse(client: AsyncClient, nurse_headers):
    patient_id = await _create_patient(client, nurse_headers, "P-TICKET-2")
    with patch("app.api.v1.endpoints.tickets.run_ai_classification", new_callable=AsyncMock):
        await client.post(
            "/api/v1/tickets",
            json={"patient_id": patient_id, "title": "発熱", "description": "38度の熱", "priority": "HIGH"},
            headers=nurse_headers,
        )
    response = await client.get("/api/v1/tickets", headers=nurse_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1


async def test_update_ticket_status(client: AsyncClient, nurse_headers):
    patient_id = await _create_patient(client, nurse_headers, "P-TICKET-3")
    with patch("app.api.v1.endpoints.tickets.run_ai_classification", new_callable=AsyncMock):
        create_resp = await client.post(
            "/api/v1/tickets",
            json={"patient_id": patient_id, "title": "腹痛", "description": "お腹が痛い", "priority": "NORMAL"},
            headers=nurse_headers,
        )
    ticket_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/v1/tickets/{ticket_id}",
        json={"status": "NURSE_REVIEW"},
        headers=nurse_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "NURSE_REVIEW"


async def test_update_ticket_denied_for_patient(client: AsyncClient, nurse_headers, patient_headers):
    patient_id = await _create_patient(client, nurse_headers, "P-TICKET-4")
    with patch("app.api.v1.endpoints.tickets.run_ai_classification", new_callable=AsyncMock):
        create_resp = await client.post(
            "/api/v1/tickets",
            json={"patient_id": patient_id, "title": "相談", "description": "本文", "priority": "NORMAL"},
            headers=nurse_headers,
        )
    ticket_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/v1/tickets/{ticket_id}",
        json={"status": "CLOSED"},
        headers=patient_headers,
    )
    assert response.status_code == 403
