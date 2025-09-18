from fastapi import APIRouter
from ..schemas.careplan import CarePlan

router = APIRouter()

# For MVP: single CarePlan per patient in memory
_DB: dict[str, CarePlan] = {}

@router.get("/{patientId}", response_model=CarePlan)
def get_careplan(patientId: str):
    cp = _DB.get(patientId)
    if not cp:
        # Return empty draft careplan as placeholder
        cp = CarePlan(patientId=patientId, status="draft", intent="plan", title="Plan inicial", activities=[])
        _DB[patientId] = cp
    return cp
