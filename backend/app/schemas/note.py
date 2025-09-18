from pydantic import BaseModel
from datetime import datetime
from uuid import UUID, uuid4

class Note(BaseModel):
    id: UUID = uuid4()
    encounterId: UUID
    type: str  # SOAP|free-text
    content: str
    createdAt: datetime = datetime.utcnow()
    authorId: UUID | None = None
