from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID, uuid4

class Patient(BaseModel):
    id: UUID = uuid4()
    createdAt: datetime = datetime.utcnow()
    givenName: str
    familyName: str
    gender: str | None = None  # male|female|other|unknown
    birthDate: date | None = None
    contact: dict | None = None
    consents: list[dict] | None = None
