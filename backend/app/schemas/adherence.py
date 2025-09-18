from pydantic import BaseModel
from datetime import datetime
from uuid import UUID, uuid4

class AdherenceEvent(BaseModel):
    id: UUID = uuid4()
    patientId: UUID
    orderItemId: UUID
    status: str  # taken|skipped|late
    takenAt: datetime
    proofUrl: str | None = None
