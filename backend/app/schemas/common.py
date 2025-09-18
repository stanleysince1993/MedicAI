from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4

class Id(BaseModel):
    id: UUID = Field(default_factory=uuid4)

class Timestamped(BaseModel):
    createdAt: datetime = Field(default_factory=datetime.utcnow)

class Consent(BaseModel):
    type: str  # data-processing | devices | notifications | research
    granted: bool
    timestamp: datetime
