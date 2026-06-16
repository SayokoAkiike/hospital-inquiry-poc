from pydantic import BaseModel


class KPIResponse(BaseModel):
    total_tickets: int
    open_tickets: int
    closed_tickets: int
    escalation_count: int
    escalation_rate: float
    status_breakdown: dict[str, int]
    priority_breakdown: dict[str, int]
