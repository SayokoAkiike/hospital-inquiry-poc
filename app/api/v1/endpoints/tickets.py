import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.ticket import Ticket, TicketPriority
from app.models.user import User, UserRole
from app.schemas.ticket import TicketCreate, TicketResponse, TicketUpdate

router = APIRouter()

SLA_HOURS = {
    TicketPriority.LOW: settings.SLA_LOW,
    TicketPriority.NORMAL: settings.SLA_NORMAL,
    TicketPriority.HIGH: settings.SLA_HIGH,
    TicketPriority.URGENT: settings.SLA_URGENT,
}


async def run_ai_classification(ticket_id: uuid.UUID, title: str, description: str):
    from app.core.database import AsyncSessionLocal
    from app.services.ai_service import classify_ticket
    try:
        category, urgency = await classify_ticket(title, description)
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
            ticket = result.scalar_one_or_none()
            if ticket:
                ticket.ai_category = category
                ticket.ai_urgency = urgency
                await db.commit()
    except Exception as e:
        print(f"AI classification failed: {e}")


@router.post("", response_model=TicketResponse, status_code=201)
async def create_ticket(
    data: TicketCreate,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    sla_due_at = datetime.now(timezone.utc) + timedelta(
        hours=SLA_HOURS[data.priority]
    )
    ticket = Ticket(
        **data.model_dump(),
        sla_due_at=sla_due_at,
    )
    db.add(ticket)
    await db.flush()
    await db.refresh(ticket)

    if settings.ANTHROPIC_API_KEY:
        background_tasks.add_task(
            run_ai_classification, ticket.id, ticket.title, ticket.description
        )

    return ticket


@router.get("", response_model=list[TicketResponse])
async def list_tickets(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.role == UserRole.PATIENT:
        raise HTTPException(status_code=403, detail="権限がありません")
    result = await db.execute(select(Ticket).order_by(Ticket.created_at.desc()))
    return result.scalars().all()


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="チケットが見つかりません")
    return ticket


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: uuid.UUID,
    data: TicketUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.role not in [UserRole.ADMIN, UserRole.NURSE, UserRole.DOCTOR]:
        raise HTTPException(status_code=403, detail="権限がありません")

    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="チケットが見つかりません")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(ticket, key, value)

    await db.flush()
    await db.refresh(ticket)
    return ticket
