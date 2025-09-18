from fastapi import APIRouter
from ..schemas.dashboard import DashboardSummary, TimeseriesSeries, TimeseriesPoint

router = APIRouter()

@router.get("/{patientId}", response_model=DashboardSummary)
def get_dashboard(patientId: str):
    # Stub with dummy timeseries
    ts = TimeseriesSeries(code="heart_rate", points=[TimeseriesPoint(t="2025-09-18T12:00:00Z", v=72)])
    return DashboardSummary(patientId=patientId, lastVitals={"heart_rate": 72}, adherenceRate=0.8, activeAlerts=0, timeseries=[ts])
