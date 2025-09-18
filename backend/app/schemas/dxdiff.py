from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class DifferentialDxRequest(BaseModel):
    age: int
    sex: str  # male|female|other|unknown
    symptoms: List[str] = []
    vitals: Dict[str, Any] = {}
    labs: Dict[str, Any] = {}
    note: Optional[str] = None

class Source(BaseModel):
    title: str | None = None
    url: str | None = None
    snippet: str | None = None

class DifferentialItem(BaseModel):
    dx: str
    rationale: str | None = None
    score: float | None = None

class DifferentialDxResponse(BaseModel):
    differentials: List[DifferentialItem] = []
    tests: List[str] = []
    sources: List[Source] = []
    disclaimer: str | None = "This is not a definitive diagnosis."
