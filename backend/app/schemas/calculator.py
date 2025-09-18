from pydantic import BaseModel
from typing import List, Dict, Any

class CalculatorResponse(BaseModel):
    tool: str
    value: float | None = None
    units: str | None = None
    flags: List[str] = []
