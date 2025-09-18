from fastapi import APIRouter
from ..schemas.observation import Observation
from typing import List
from pydantic import BaseModel

router = APIRouter()

class ObservationBatch(BaseModel):
    patientId: str
    observations: List[Observation]

_STORAGE: list[Observation] = []

@router.post("/batch", status_code=202)
def ingest_batch(batch: ObservationBatch):
    _STORAGE.extend(batch.observations)
    return {"accepted": len(batch.observations)}
