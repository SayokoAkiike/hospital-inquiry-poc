import uuid
from datetime import date, datetime

from pydantic import BaseModel


class PatientCreate(BaseModel):
    patient_number: str
    name: str
    date_of_birth: date | None = None
    phone: str | None = None
    email: str | None = None


class PatientResponse(BaseModel):
    id: uuid.UUID
    patient_number: str
    name: str
    date_of_birth: date | None
    phone: str | None
    email: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
