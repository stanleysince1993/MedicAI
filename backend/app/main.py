from fastapi import FastAPI
from .api import patients, encounters, notes, dxdiff, orders, careplan, observations, dashboard, adjustments, calculators, icd10, rag

app = FastAPI(title="MedicAI MVP API", version="0.1.0")

# Routers
app.include_router(patients.router, prefix="/patients", tags=["patients"])
app.include_router(encounters.router, prefix="/encounters", tags=["encounters"])
app.include_router(notes.router, tags=["notes"])
app.include_router(dxdiff.router, tags=["dx-diff"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(careplan.router, prefix="/careplan", tags=["careplan"])
app.include_router(observations.router, prefix="/observations", tags=["observations"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(adjustments.router, prefix="/adjustments", tags=["adjustments"])
app.include_router(calculators.router, prefix="/calculate", tags=["calculators"])
app.include_router(icd10.router, prefix="/icd10", tags=["icd10"])
app.include_router(rag.router, prefix="/ask", tags=["rag"])
