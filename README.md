## MedicAI – Clinical Assistant MVP

Minimal demo app for differential diagnosis suggestions from a clinical case description.

### Stack
- Backend: FastAPI (Python) with optional OpenAI integration
- Frontend: Static HTML/CSS/JS

### Setup
1) Python 3.10+
2) Create and activate venv
```bash
python -m venv .venv
./.venv/Scripts/activate  # Windows PowerShell
```
3) Install deps
```bash
pip install -r requirements.txt
```
4) Configure environment
```bash
copy .env.example .env
# Edit .env and set OPENAI_API_KEY to enable GPT
```

### Run Backend
```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### Open Frontend
Open `frontend/index.html` in your browser. If needed, set `API_BASE_URL` in `.env` and inject it into the page via a small server or by editing `frontend/script.js`.

### API
POST `/analyze`
```json
{ "case_text": "Free-text clinical case..." }
```
Response
```json
{
  "differentials": [{ "condition": "Dengue", "probability": "high", "rationale": "..." }],
  "tests": [{ "name": "Serology Dengue IgM/IgG", "rationale": "..." }],
  "notes": "..."
}
```

### Disclaimer
This is a demo for educational purposes only. Not for clinical use.



