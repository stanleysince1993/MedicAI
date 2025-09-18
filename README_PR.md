# PR: MVP API skeleton aligned to OpenAPI (canvas)

## What
- Adds FastAPI app with routers/stubs for all MVP endpoints:
  - /patients, /encounters, /encounters/{id}/notes
  - /dx-diff, /ask
  - /orders, /careplan/{patientId}
  - /observations/batch, /dashboard/{patientId}
  - /adjustments, /adjustments/{id}/decision
  - /calculate, /icd10/suggest
- Adds Pydantic schemas mirroring the canvas OpenAPI.
- Adds basic calculators (BMI) as example.

## How to run
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs

## Notes
- In-memory stores used as placeholders; replace with Postgres/Timescale + Alembic migrations.
- RAG, ICD-10, and real rules engine are stubs to be implemented in Sprints 1–2.
- Align `openapi.yaml` by exporting from the running app or replacing with the canvas version.
