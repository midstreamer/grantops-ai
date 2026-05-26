# Architecture

GrantOps AI is a monorepo with a Python FastAPI backend and a React (Vite + TypeScript) frontend.

## High-level layout

```
grantops-ai/
├── backend/     # REST API, persistence, agents (future)
├── frontend/    # Web UI
└── docs/        # Project documentation
```

## Backend

- **Framework:** FastAPI served by Uvicorn
- **Configuration:** `pydantic-settings` loads values from `.env`
- **Persistence:** SQLAlchemy with SQLite for local development (`app/db/session.py`)
- **Layers:**
  - `app/main.py` — HTTP routes and middleware (CORS)
  - `app/schemas/` — Pydantic request/response models
  - `app/models/` — SQLAlchemy ORM models (future)
  - `app/services/` — Business logic (future)
  - `app/agents/` — AI orchestration (future)
  - `app/utils/` — Shared helpers

### Current API

| Method | Path     | Description        |
|--------|----------|--------------------|
| GET    | `/health`| Service health JSON |

## Frontend

- **Stack:** React 19, TypeScript, Vite
- **Structure:**
  - `src/pages/` — Route-level views
  - `src/components/` — Reusable UI
  - `src/services/` — API client (`fetch` to backend)
  - `src/types/` — Shared TypeScript types

The home page calls `GET /health` using `VITE_API_BASE_URL` and displays connectivity status.

## Local development flow

1. Start backend on port `8000`.
2. Start frontend on port `5173`.
3. Browser loads the SPA; frontend fetches `/health` with CORS allowed for the dev origin.

## Future (not implemented)

- External grant/data APIs
- Authentication and multi-tenant orgs
- Agent pipelines in `app/agents/`
- Production database (PostgreSQL) and deployment manifests
