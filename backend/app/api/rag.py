from fastapi import APIRouter
from ..schemas.dxdiff import Source

router = APIRouter()

@router.post("")
def ask(payload: dict):
    q = payload.get("query", "")
    # Stub response
    return {"answer": f"[Stub] No KB indexed yet. Your query: {q}", "sources": [Source(title="KB", url="https://example.org").model_dump()]}
