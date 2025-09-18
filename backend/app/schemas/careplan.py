from pydantic import BaseModel
from typing import List
from datetime import datetime
from uuid import UUID, uuid4

class CarePlanActivity(BaseModel):
    kind: str  # MedicationRequest|Observation|Appointment|Instruction|Diet
    description: str
    schedule: str | None = None
    status: str | None = None  # scheduled|in-progress|completed|on-hold|cancelled

class CarePlan(BaseModel):
    id: UUID = uuid4()
    patientId: UUID
    status: str  # draft|active|completed|cancelled
    intent: str  # plan|order
    title: str
    version: int = 1
    activities: List[CarePlanActivity] = []
    createdAt: datetime = datetime.utcnow()
    revisedFrom: UUID | None = None
