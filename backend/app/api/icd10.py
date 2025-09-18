from fastapi import APIRouter
from ..schemas.icd10 import ICD10SuggestionResponse, ICD10Suggestion

router = APIRouter()

@router.post("/suggest", response_model=ICD10SuggestionResponse)
def suggest_icd10(text: dict):
    # Stub: return example suggestions
    return ICD10SuggestionResponse(codes=[ICD10Suggestion(code="J06.9", label="Acute upper respiratory infection, unspecified", confidence=0.61)])
