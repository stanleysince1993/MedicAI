from pydantic import BaseModel
from typing import List

class ICD10Suggestion(BaseModel):
    code: str
    label: str
    confidence: float | None = None
    spans: list[dict] | None = None

class ICD10SuggestionResponse(BaseModel):
    codes: List[ICD10Suggestion] = []
