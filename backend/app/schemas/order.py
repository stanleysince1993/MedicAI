from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID, uuid4

class OrderItem(BaseModel):
    kind: str  # MedicationRequest|Lab|Procedure|Instruction|Diet
    description: str
    schedule: str | None = None
    dosage: str | None = None

class Order(BaseModel):
    id: UUID = uuid4()
    encounterId: UUID
    status: str  # draft|issued|acknowledged|fulfilled|revised|cancelled
    version: int = 1
    items: List[OrderItem] = []
    createdAt: datetime = datetime.utcnow()
    revisedFrom: UUID | None = None
