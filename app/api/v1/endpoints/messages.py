import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.message import Message
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.message import MessageCreate, MessageResponse

router = APIRouter()


@router.post("/{ticket_id}/messages", response_model=MessageResponse, status_code=201)
async def create_message(
    ticket_id: uuid.UUID,
    data: MessageCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="チケットが見つかりません")

    message = Message(
        ticket_id=ticket_id,
        sender_id=current_user.id,
        content=data.content,
    )
    db.add(message)
    await db.flush()
    await db.refresh(message)
    return message


@router.get("/{ticket_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    ticket_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="チケットが見つかりません")

    result = await db.execute(
        select(Message)
        .where(Message.ticket_id == ticket_id)
        .order_by(Message.created_at.asc())
    )
    return result.scalars().all()
