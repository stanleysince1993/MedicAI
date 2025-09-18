from fastapi import APIRouter, HTTPException
from ..schemas.order import Order
from uuid import UUID

router = APIRouter()
_DB = {}

@router.post("/", status_code=201, response_model=Order)
def create_order(order: Order):
    _DB[str(order.id)] = order
    return order

@router.get("/{id}", response_model=Order)
def get_order(id: UUID):
    obj = _DB.get(str(id))
    if not obj:
        raise HTTPException(404, "Order not found")
    return obj

@router.post("/{id}/revise", status_code=201, response_model=Order)
def revise_order(id: UUID, changes: dict):
    old = _DB.get(str(id))
    if not old:
        raise HTTPException(404, "Order not found")
    new = old.model_copy(update={"version": old.version + 1, "revisedFrom": old.id})
    _DB[str(new.id)] = new
    return new
