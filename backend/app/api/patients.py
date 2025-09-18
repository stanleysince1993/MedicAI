from fastapi import APIRouter, HTTPException
from ..schemas.patient import Patient
from uuid import UUID

router = APIRouter()

_DB = {}

@router.get("/", response_model=list[Patient])
def list_patients(q: str | None = None):
    return list(_DB.values())

@router.post("/", status_code=201, response_model=Patient)
def create_patient(patient: Patient):
    _DB[str(patient.id)] = patient
    return patient

@router.get("/{id}", response_model=Patient)
def get_patient(id: UUID):
    obj = _DB.get(str(id))
    if not obj:
        raise HTTPException(404, "Patient not found")
    return obj
