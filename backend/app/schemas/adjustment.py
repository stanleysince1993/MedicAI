from pydantic import BaseModel
from datetime import datetime
from uuid import UUID, uuid4

class AdjustmentDecision(BaseModel):
    decidedBy: UUID | None = None
    decidedAt: datetime | None = None
    rationale: str | None = None

class AdjustmentRequest(BaseModel):
    id: UUID = uuid4()
    patientId: UUID
    orderId: UUID | None = None
    fieldPath: str | None = None
    newValue: str | None = None
    reason: str
    status: str = "requested"  # requested|under-review|approved|rejected
    createdAt: datetime = datetime.utcnow()
    decision: AdjustmentDecision | None = None
