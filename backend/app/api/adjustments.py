from fastapi import APIRouter, HTTPException
from ..schemas.adjustment import AdjustmentRequest, AdjustmentDecision
from uuid import UUID

router = APIRouter()
_DB: dict[str, AdjustmentRequest] = {}

@router.post("/", status_code=201, response_model=AdjustmentRequest)
def create_adjustment(adj: AdjustmentRequest):
    _DB[str(adj.id)] = adj
    return adj

@router.post("/{id}/decision", response_model=AdjustmentRequest)
def decide_adjustment(id: UUID, payload: dict):
    adj = _DB.get(str(id))
    if not adj:
        raise HTTPException(404, "Adjustment not found")
    status = payload.get("status")
    rationale = payload.get("rationale")
    if status not in {"approved", "rejected"}:
        raise HTTPException(400, "Invalid status")
    decision = AdjustmentDecision(rationale=rationale)
    adj.status = status
    adj.decision = decision
    _DB[str(id)] = adj
    return adj
