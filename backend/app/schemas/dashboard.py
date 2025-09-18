from pydantic import BaseModel
from typing import List, Dict, Any

class TimeseriesPoint(BaseModel):
    t: str
    v: float | str

class TimeseriesSeries(BaseModel):
    code: str
    points: List[TimeseriesPoint] = []

class DashboardSummary(BaseModel):
    patientId: str
    lastVitals: Dict[str, Any] = {}
    adherenceRate: float | None = None
    activeAlerts: int = 0
    timeseries: List[TimeseriesSeries] = []
