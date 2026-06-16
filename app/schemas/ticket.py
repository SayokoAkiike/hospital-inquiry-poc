import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.ticket import AICategory, TicketPriority, TicketStatus


class TicketCreate(BaseModel):
    patient_id: uuid.UUID
    title: str
    description: str
    priority: TicketPriority = TicketPriority.NORMAL


class TicketUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    assigned_user_id: uuid.UUID | None = None


class TicketResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    assigned_user_id: uuid.UUID | None
    ai_category: AICategory | None
    ai_urgency: TicketPriority | None
    sla_due_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
