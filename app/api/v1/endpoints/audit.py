import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.audit_log import AuditAction, AuditLog
from app.models.user import User, UserRole


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    action: AuditAction
    resource_type: str | None
    resource_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


router = APIRouter()


@router.get("", response_model=list[AuditLogResponse])
async def list_audit_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="権限がありません")

    result = await db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(100)
    )
    return result.scalars().all()


async def write_audit_log(
    db: AsyncSession,
    user_id: uuid.UUID | None,
    action: AuditAction,
    resource_type: str | None = None,
    resource_id: str | None = None,
):
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
    )
    db.add(log)
