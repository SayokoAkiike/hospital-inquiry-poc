import enum
import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class TicketStatus(str, enum.Enum):
    NEW = "NEW"
    NURSE_REVIEW = "NURSE_REVIEW"
    ESCALATED_TO_DOCTOR = "ESCALATED_TO_DOCTOR"
    DOCTOR_REVIEW = "DOCTOR_REVIEW"
    WAITING_PATIENT = "WAITING_PATIENT"
    CLOSED = "CLOSED"


class TicketPriority(str, enum.Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class AICategory(str, enum.Enum):
    APPOINTMENT = "Appointment"
    MEDICATION = "Medication"
    SIDE_EFFECT = "SideEffect"
    BILLING = "Billing"
    TREATMENT = "Treatment"
    OTHER = "Other"


class Ticket(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tickets"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus), nullable=False, default=TicketStatus.NEW
    )
    priority: Mapped[TicketPriority] = mapped_column(
        Enum(TicketPriority), nullable=False, default=TicketPriority.NORMAL
    )
    assigned_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    ai_category: Mapped[AICategory | None] = mapped_column(Enum(AICategory), nullable=True)
    ai_urgency: Mapped[TicketPriority | None] = mapped_column(Enum(TicketPriority), nullable=True)
    sla_due_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    patient: Mapped["Patient"] = relationship("Patient", back_populates="tickets")
    assigned_user: Mapped["User | None"] = relationship(
        "User", back_populates="tickets_assigned", foreign_keys=[assigned_user_id]
    )
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="ticket")
    escalations: Mapped[list["Escalation"]] = relationship("Escalation", back_populates="ticket")
