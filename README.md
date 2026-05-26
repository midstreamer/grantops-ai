# GrantOps AI

Full-stack scaffold for a grant operations platform: FastAPI backend, React + TypeScript frontend, and SQLite for local development.

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm

## Project structure

```
grantops-ai/
├── backend/          # FastAPI API
├── frontend/         # React + Vite UI
└── docs/             # Architecture and roadmap
```

## Quick start

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify the API:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok","service":"grantops-ai","version":"0.1.0"}
```

Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Frontend

In a second terminal:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). The home page calls the backend `/health` endpoint and shows whether the API is reachable.

### Environment variables

| Location   | Variable            | Default                    | Purpose                    |
|-----------|---------------------|----------------------------|----------------------------|
| `backend/.env` | `DATABASE_URL` | `sqlite:///./grantops.db`  | SQLAlchemy connection      |
| `backend/.env` | `CORS_ORIGINS` | `http://localhost:5173,...`| Allowed browser origins    |
| `backend/.env` | `GOOGLE_APPLICATION_CREDENTIALS` | — | Path to Google service account JSON |
| `backend/.env` | `GOOGLE_SHEETS_SPREADSHEET_ID` | — | Target spreadsheet ID for export |
| `frontend/.env` | `VITE_API_BASE_URL` | `http://localhost:8000` | Backend URL for API calls |

## Tests

From `backend/` with the virtual environment activated:

```bash
pytest
```

## Scripts reference

| Command | Where      | Description              |
|---------|------------|--------------------------|
| `uvicorn app.main:app --reload` | `backend/` | Run API dev server |
| `pytest` | `backend/` | Run backend tests |
| `npm run dev` | `frontend/` | Run Vite dev server |
| `npm run build` | `frontend/` | Production build |

## Documentation

- [Architecture](docs/architecture.md)
- [Roadmap](docs/roadmap.md)

## License

Private / unlicensed — update as needed for your organization.
