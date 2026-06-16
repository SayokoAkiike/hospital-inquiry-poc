from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import NotificationType
from app.models.ticket import Ticket, TicketStatus
from app.services.notification_service import create_notification


async def check_sla_violations(db: AsyncSession):
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Ticket).where(
            Ticket.sla_due_at < now,
            Ticket.status.notin_([TicketStatus.CLOSED]),
        )
    )
    tickets = result.scalars().all()

    for ticket in tickets:
        if ticket.assigned_user_id:
            await create_notification(
                db=db,
                user_id=ticket.assigned_user_id,
                type=NotificationType.SLA_EXCEEDED,
                title="SLA超過アラート",
                body=f"チケット「{ticket.title}」の対応期限を超過しています。",
                resource_id=str(ticket.id),
            )

    return len(tickets)
