import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.escalation import Escalation
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User, UserRole
from app.schemas.escalation import EscalationCreate, EscalationResponse

router = APIRouter()


@router.post("/{ticket_id}/escalate", response_model=EscalationResponse, status_code=201)
async def escalate_ticket(
    ticket_id: uuid.UUID,
    data: EscalationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.role not in [UserRole.NURSE, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="権限がありません")

    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="チケットが見つかりません")

    ticket.status = TicketStatus.ESCALATED_TO_DOCTOR

    escalation = Escalation(
        ticket_id=ticket_id,
        from_user_id=current_user.id,
        to_user_id=data.to_user_id,
        reason=data.reason,
    )
    db.add(escalation)
    await db.flush()
    await db.refresh(escalation)
    return escalation
