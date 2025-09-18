from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4

class Encounter(BaseModel):
    id: UUID = uuid4()
    patientId: UUID
    status: str  # planned|in-progress|completed|cancelled
    reason: Optional[str] = None
    startedAt: datetime
    endedAt: datetime | None = None
