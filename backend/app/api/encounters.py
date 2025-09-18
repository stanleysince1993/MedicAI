from fastapi import APIRouter, HTTPException
from ..schemas.encounter import Encounter
from uuid import UUID

router = APIRouter()
_DB = {}

@router.post("/", status_code=201, response_model=Encounter)
def create_encounter(enc: Encounter):
    _DB[str(enc.id)] = enc
    return enc

@router.get("/{id}", response_model=Encounter)
def get_encounter(id: UUID):
    obj = _DB.get(str(id))
    if not obj:
        raise HTTPException(404, "Encounter not found")
    return obj
