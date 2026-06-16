from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User, UserRole
from app.services.sla_service import check_sla_violations

router = APIRouter()


@router.post("/check-sla")
async def run_sla_check(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="権限がありません")
    count = await check_sla_violations(db)
    return {"violations_found": count}
