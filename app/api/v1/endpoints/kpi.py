from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.escalation import Escalation
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User, UserRole
from app.schemas.kpi import KPIResponse

router = APIRouter()


@router.get("", response_model=KPIResponse)
async def get_kpi(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="権限がありません")

    total = await db.scalar(select(func.count(Ticket.id)))
    closed = await db.scalar(
        select(func.count(Ticket.id)).where(Ticket.status == TicketStatus.CLOSED)
    )
    open_count = total - closed
    escalations = await db.scalar(select(func.count(Escalation.id)))
    escalation_rate = round(escalations / total * 100, 1) if total > 0 else 0.0

    status_rows = await db.execute(
        select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status)
    )
    status_breakdown = {row[0].value: row[1] for row in status_rows}

    priority_rows = await db.execute(
        select(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority)
    )
    priority_breakdown = {row[0].value: row[1] for row in priority_rows}

    return KPIResponse(
        total_tickets=total,
        open_tickets=open_count,
        closed_tickets=closed,
        escalation_count=escalations,
        escalation_rate=escalation_rate,
        status_breakdown=status_breakdown,
        priority_breakdown=priority_breakdown,
    )
