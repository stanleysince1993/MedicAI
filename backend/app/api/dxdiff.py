from fastapi import APIRouter
from ..schemas.dxdiff import DifferentialDxRequest, DifferentialDxResponse, DifferentialItem, Source

router = APIRouter()

@router.post("/dx-diff", response_model=DifferentialDxResponse)
def dx_diff(payload: DifferentialDxRequest):
    # Stub: return sample structure
    return DifferentialDxResponse(
        differentials=[DifferentialItem(dx="Viral URI", rationale="Common with fever and cough", score=0.62),
                       DifferentialItem(dx="Community-acquired pneumonia", rationale="Fever + tachycardia; consider CXR", score=0.38)],
        tests=["CXR", "CBC", "Pulse oximetry"],
        sources=[Source(title="IDSA CAP Guidelines", url="https://example.org/cap", snippet="Outpatient criteria...")],
    )
