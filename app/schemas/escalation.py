import uuid
from datetime import datetime

from pydantic import BaseModel


class EscalationCreate(BaseModel):
    to_user_id: uuid.UUID
    reason: str


class EscalationResponse(BaseModel):
    id: uuid.UUID
    ticket_id: uuid.UUID
    from_user_id: uuid.UUID
    to_user_id: uuid.UUID
    reason: str
    created_at: datetime

    model_config = {"from_attributes": True}
