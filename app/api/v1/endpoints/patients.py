import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.schemas.patient import PatientCreate, PatientResponse

router = APIRouter()

# 患者データへアクセス可能なロール。
# PATIENT ロールのユーザーはこのAPI群から除外されている。
# TODO(本番化時): 現状は「医療スタッフなら全患者を閲覧可能」という粗い制御。
#   将来的には patient.assigned_nurse_id / 担当病棟などで
#   nurse/doctor が「自分の担当患者のみ」閲覧できるよう、
#   行レベルのスコープ制御を追加する想定。
_STAFF_ROLES = [UserRole.ADMIN, UserRole.NURSE, UserRole.DOCTOR]


@router.post("", response_model=PatientResponse, status_code=201)
async def create_patient(
    data: PatientCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.role not in [UserRole.ADMIN, UserRole.NURSE]:
        raise HTTPException(status_code=403, detail="権限がありません")

    result = await db.execute(
        select(Patient).where(Patient.patient_number == data.patient_number)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="この患者番号は既に登録されています")

    patient = Patient(**data.model_dump())
    db.add(patient)
    await db.flush()
    await db.refresh(patient)
    return patient


@router.get("", response_model=list[PatientResponse])
async def list_patients(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    患者一覧取得。

    アクセス制御: PATIENT ロールは患者一覧にアクセス不可（403）。
    医療スタッフ（ADMIN/NURSE/DOCTOR）のみアクセス可能。
    """
    if current_user.role not in _STAFF_ROLES:
        raise HTTPException(status_code=403, detail="権限がありません")
    result = await db.execute(select(Patient).order_by(Patient.created_at.desc()))
    return result.scalars().all()


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    患者詳細取得。

    アクセス制御: PATIENT ロールはアクセス不可（403）。
    医療スタッフ（ADMIN/NURSE/DOCTOR）のみアクセス可能。
    """
    if current_user.role not in _STAFF_ROLES:
        raise HTTPException(status_code=403, detail="権限がありません")
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="患者が見つかりません")
    return patient
