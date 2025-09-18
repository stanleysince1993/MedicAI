from fastapi import APIRouter, HTTPException, Path
from ..schemas.note import Note
from uuid import UUID

router = APIRouter()

_DB = {}

@router.post("/encounters/{id}/notes", status_code=201, response_model=Note)
def add_note(id: UUID, note: Note):
    # In MVP stub, trust provided encounterId matches id
    _DB[str(note.id)] = note
    return note
