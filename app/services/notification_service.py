import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType


async def create_notification(
    db: AsyncSession,
    user_id: uuid.UUID,
    type: NotificationType,
    title: str,
    body: str,
    resource_id: str | None = None,
):
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        body=body,
        resource_id=resource_id,
    )
    db.add(notification)
    return notification
