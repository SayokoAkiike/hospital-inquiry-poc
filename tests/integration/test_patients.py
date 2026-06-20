"""
患者データアクセス制御テスト。

テスト対象:
- 未認証アクセスは拒否されること
- PATIENT ロールは /patients にアクセスできないこと
- NURSE / DOCTOR / ADMIN はアクセスできること
"""
from httpx import AsyncClient


async def _create_patient(client: AsyncClient, headers: dict, patient_number: str = "P001") -> dict:
    resp = await client.post(
        "/api/v1/patients",
        json={"patient_number": patient_number, "name": "テスト患者"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_patient_list_denied_for_unauthenticated(client: AsyncClient):
    response = await client.get("/api/v1/patients")
    assert response.status_code in (401, 403)


async def test_patient_list_denied_for_patient_role(client: AsyncClient, patient_headers):
    response = await client.get("/api/v1/patients", headers=patient_headers)
    assert response.status_code == 403


async def test_patient_create_denied_for_patient_role(client: AsyncClient, patient_headers):
    response = await client.post(
        "/api/v1/patients",
        json={"patient_number": "P999", "name": "不正作成試行"},
        headers=patient_headers,
    )
    assert response.status_code == 403


async def test_patient_list_allowed_for_nurse(client: AsyncClient, nurse_headers):
    await _create_patient(client, nurse_headers, "P-NURSE-1")
    response = await client.get("/api/v1/patients", headers=nurse_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_patient_list_allowed_for_doctor(client: AsyncClient, nurse_headers, doctor_headers):
    # 患者作成は nurse/admin のみ可能なので nurse で作成し、doctor は閲覧のみ確認
    await _create_patient(client, nurse_headers, "P-DOC-1")
    response = await client.get("/api/v1/patients", headers=doctor_headers)
    assert response.status_code == 200


async def test_patient_list_allowed_for_admin(client: AsyncClient, nurse_headers, admin_headers):
    await _create_patient(client, nurse_headers, "P-ADMIN-1")
    response = await client.get("/api/v1/patients", headers=admin_headers)
    assert response.status_code == 200


async def test_patient_create_denied_for_doctor(client: AsyncClient, doctor_headers):
    """doctor は患者作成権限を持たない（admin/nurseのみ）。"""
    response = await client.post(
        "/api/v1/patients",
        json={"patient_number": "P-DOC-CREATE", "name": "医師作成試行"},
        headers=doctor_headers,
    )
    assert response.status_code == 403


async def test_get_patient_detail_allowed_for_nurse(client: AsyncClient, nurse_headers):
    created = await _create_patient(client, nurse_headers, "P-DETAIL-1")
    response = await client.get(f"/api/v1/patients/{created['id']}", headers=nurse_headers)
    assert response.status_code == 200
    assert response.json()["patient_number"] == "P-DETAIL-1"


async def test_get_patient_detail_denied_for_patient_role(client: AsyncClient, nurse_headers, patient_headers):
    created = await _create_patient(client, nurse_headers, "P-DETAIL-2")
    response = await client.get(f"/api/v1/patients/{created['id']}", headers=patient_headers)
    assert response.status_code == 403


async def test_duplicate_patient_number_rejected(client: AsyncClient, nurse_headers):
    await _create_patient(client, nurse_headers, "P-DUP-1")
    response = await client.post(
        "/api/v1/patients",
        json={"patient_number": "P-DUP-1", "name": "重複患者"},
        headers=nurse_headers,
    )
    assert response.status_code == 400
