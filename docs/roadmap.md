# Roadmap

## Phase 0 — Scaffold (current)

- [x] Monorepo structure (backend, frontend, docs)
- [x] FastAPI app with `/health`
- [x] SQLAlchemy SQLite session setup
- [x] React + Vite frontend with backend connectivity check
- [x] README and architecture docs

## Phase 1 — Core API

- [ ] Domain models (grants, organizations, applications)
- [ ] CRUD endpoints with validation
- [ ] Database migrations (Alembic)
- [ ] Expanded pytest coverage

## Phase 2 — Integrations

- [ ] External grant discovery APIs (httpx clients in `app/services/`)
- [ ] Rate limiting and API key configuration
- [ ] Background jobs for sync

## Phase 3 — AI agents

- [ ] Agent definitions in `app/agents/`
- [ ] Prompt templates and tool routing
- [ ] Audit logging for agent actions

## Phase 4 — Product UI

- [ ] Routing and layout shell
- [ ] Grant search and detail views
- [ ] Auth (session or OAuth)

## Phase 5 — Production

- [ ] PostgreSQL and environment-specific config
- [ ] CI/CD, container images, and deployment docs
