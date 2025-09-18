from pydantic import BaseModel
from datetime import datetime
from uuid import UUID, uuid4

class Observation(BaseModel):
    id: UUID = uuid4()
    patientId: UUID
    code: str  # e.g. glucose
    value: float | str
    unit: str
    effectiveAt: datetime
    source: str | None = None  # apple-healthkit|google-fit|ble-device|manual
