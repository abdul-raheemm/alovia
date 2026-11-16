# Architecture — Alovia

**Version:** 3.0 (replaces `archive/TRD_v2.md`) · **Date:** 2026-11-16

---

## 1. System Overview
Two React web apps (patient, doctor+admin) talk to **one FastAPI backend**. The backend is the only component that reads or writes the database and file storage. Supabase provides Postgres (with pgvector), Auth and private Storage. Rule engines (genetic, symptoms, journey) and the ML models run inside the backend. The RAG assistant and AI draft features call external LLM/embedding APIs from the backend only.

## 2. Architecture Pattern
**Modular monolith.** One backend service, one database, one folder per module with clear boundaries.
**Reason:** small team, free hosting, one deploy; modules can still be built and tested one at a time.

## 3. Technology Stack

| Layer | Choice | Notes |
|---|---|---|
| Frontend | React + **TypeScript** + Vite, Tailwind CSS, shadcn/ui (Radix) | Two apps in one npm workspace |
| Frontend libraries | React Router, TanStack Query, React Hook Form + Zod, Recharts, react-day-picker (calendar), `motion` (Framer Motion), lottie-react, vite-plugin-pwa (patient app), Supabase JS (**auth only**) | Exact versions pinned at setup and recorded in `DECISIONS.md` |
| Backend | Python **3.12**, FastAPI, Pydantic v2, SQLAlchemy 2 (async optional), Alembic | Python 3.12 virtual environment (the laptop has 3.14; ML libraries may lag) |
| ML | XGBoost, scikit-learn, SHAP, joblib, pandas, NumPy | Versions must match the saved models (`ml_models_spec.md`) |
| RAG (Phase 7) | LangChain, pgvector, embedding API `[OPEN]`, LLM API `[OPEN]` | |
| Database | Supabase PostgreSQL (fresh project) + `vector` extension | |
| Authentication | Supabase Auth (email + password); backend verifies JWT | |
| Storage | Supabase Storage, **private** bucket | Signed short-lived download links |
| Hosting | Backend: Render (free). Frontends: Vercel Hobby (two projects; free, non-commercial academic use) | See `DEPLOYMENT.md` |
| Payments, email marketing, analytics | **None** | Supabase sends only auth emails |
| Dev tools | Ruff, mypy, pytest (backend); ESLint, Prettier, tsc, Vitest, Playwright + axe (frontend) | |
| Agent tools | Claude Code, graphify (code knowledge graph), Karpathy guidelines and Ponytail plugins | See `CLAUDE.md` |

## 4. System Components

### Frontend — patient app (`frontend/apps/patient-web`)
- Journey home, calendar, appointments, symptom logging, urgent button, genetic forms and results, shared results and doctor notes, pregnancy-end flow, settings, legal pages, assistant (Phase 7).
- Uses Supabase JS **only** to sign in/out and get the token. All data via the backend API.

### Frontend — doctor app (`frontend/apps/doctor-web`)
- Patient list, inbox, patient detail tabs, data entry and predictions, sharing, genetic review, records, notes, appointments, rule review, AI drafts, admin screens (admin role only).

### Backend (`backend/`)
- Verifies tokens, resolves role and assignments, enforces access rules.
- Hosts the modules: patients/users, predictions (ML), journey, symptoms, genetic, dashboard (inbox, sharing, records, notes, appointments, rule review), admin, AI drafts, assistant.
- Loads rule YAML files and ML models at startup.
- Creates signed Storage links.

### Database (Supabase Postgres)
- All application data (`DATABASE.md`), knowledge base tables and vectors.

## 5. Architecture Diagram

```
Patient web app ─┐                    ┌─> Supabase Auth (sign-in only, issues JWT)
Doctor web app ──┼── sign-in only ────┘
                 │
                 └── all data requests (Bearer JWT) ──> FastAPI backend (Render)
                                                         ├─ core: auth, config, errors, logging
                                                         ├─ modules: journey, symptoms, genetic,
                                                         │           predictions, dashboard, admin,
                                                         │           ai_drafts, assistant
                                                         ├─ rules/ (YAML)   ml_models/ (joblib)
                                                         ├──> Supabase Postgres (+pgvector)
                                                         ├──> Supabase Storage (private bucket)
                                                         └──> LLM / embedding APIs (later phases)
```

## 6. Data Flow (example: patient logs a symptom)
1. Patient submits the form in the patient app.
2. Frontend validates field formats (Zod) and sends `POST /api/v1/symptoms/checkins` with the JWT.
3. Backend verifies the JWT and the patient role, finds the patient record.
4. Backend validates values against the symptom vocabulary (V1/V2).
5. Symptom engine computes the red-flag level, PUQE and pattern changes.
6. Check-in and entries are saved; inbox items are created for the doctors if needed.
7. Response returns the level and message keys; the frontend shows the advice.

## 7. Project Structure

```
C:\Users\Engineer\Desktop\Alovia\   # git repository root (new, fresh repo) — no extra alovia/ subfolder
├── ml-test/                         # OLD backend — read/copy only, git-ignored (DEC-019)
├── rag/                             # OLD knowledge-base work — read/copy only, git-ignored (DEC-019)
├── CLAUDE.md                        # agent rules (auto-read by Claude Code)
├── README.md
├── .gitignore
├── docs/                            # all documentation (source of truth)
│   ├── PRD.md  UX_FLOWS.md  DESIGN_SYSTEM.md  ARCHITECTURE.md  DATABASE.md
│   ├── API.md  SECURITY.md  CODE_STYLE.md  TESTING.md  AGENTS.md
│   ├── ENVIRONMENT.md  ERROR_HANDLING.md  OBSERVABILITY.md  DEPLOYMENT.md
│   ├── DECISIONS.md  ROADMAP.md  CHANGELOG.md  START_PROMPT.md
│   ├── modules/                     # module specs
│   ├── legal/                       # privacy, terms, notices, compliance checklist, credits
│   ├── knowledge-base/              # collection guide, KB progress snapshot
│   ├── tracking/                    # CONTEXT, PROGRESS, HISTORY, ERROR_LOG
│   └── archive/                     # superseded documents (read-only)
├── backend/
│   ├── app/
│   │   ├── main.py                  # app factory, routers, startup loading
│   │   ├── core/                    # config.py, database.py, auth.py, errors.py, logging.py
│   │   ├── common/                  # response envelope, pagination, shared schemas
│   │   └── modules/
│   │       ├── users/               # users, doctors, patients, assignments, invites, consents
│   │       ├── predictions/         # ML: model loading, RiskModel, SHAP, results, shares
│   │       ├── journey/             # dates, GA calc, content providers, calendar, notifications
│   │       ├── symptoms/            # vocabulary, red-flag engine, PUQE, patterns
│   │       ├── genetic/             # rule engine, assessments, reviews
│   │       ├── dashboard/           # inbox, records, notes, appointments, rule review, audit
│   │       ├── admin/
│   │       ├── ai_drafts/           # Phase 6
│   │       └── assistant/           # Phase 7 (RAG)
│   │       # each module: router.py, service.py, schemas.py, models.py, (engine.py), tests in backend/tests
│   ├── rules/                       # genetic/, symptoms/, journey/ YAML + messages.yaml per module
│   ├── content/                     # journey prototype_content.yaml, size_reference.yaml
│   ├── ml_models/                   # the 8 model files (+ feature ranges later)
│   ├── migrations/                  # Alembic
│   ├── scripts/                     # feature ranges, seed data, KB indexing (Phase 7)
│   ├── tests/  (unit/, integration/)
│   ├── pyproject.toml  requirements.txt  requirements-dev.txt  .env.example
├── frontend/
│   ├── package.json                 # npm workspaces
│   ├── apps/
│   │   ├── patient-web/  (src/app, src/pages, src/features/<module>, src/components, public/)
│   │   └── doctor-web/   (same layout; admin under src/features/admin)
│   ├── packages/
│   │   ├── ui/                      # tokens.css, Tailwind preset, shadcn components, logo
│   │   └── shared/                  # typed API client, shared types, constants
│   └── e2e/                         # Playwright tests for both apps
├── knowledge-base/                  # moved from old rag/ (clean/, raw/, CSVs, tools/)
└── assets/                          # illustration sources, Lottie files, credits sources
```

Old folders `ml-test/` and `rag/` stay **inside the root folder but git-ignored**, untouched, until the owner confirms the move worked; then the owner deletes them. The first commit must show neither folder in `git status`.

## 8. Dependency Rules
- Frontends never access the database or Storage directly; only Supabase Auth for sign-in.
- The service-role key and database URL exist only in the backend environment.
- Routers call services; services call models/engines; engines never call the database directly (pure functions, easy to test).
- A module may import another module's **service**, never its models or internals.
- Rule numbers, thresholds and wording live in YAML/config, never in code.
- Shared frontend code goes in `packages/`; apps never import from each other.
- No new dependency without asking the owner (CLAUDE.md).

## 9. Key Technical Decisions
Recorded in `DECISIONS.md` (database access only through FastAPI, rules as files, two apps, TypeScript, Python 3.12, fresh Supabase project, hosting, security last, etc.).

## 10. Performance
- Predictions under 1–2 s, dashboard pages under 2 s (demo data, warm service).
- Models and rules loaded once at startup.
- Patient list and inbox paginated (default 25).
- Indexes as listed in `DATABASE.md`.

## 11. Scalability
Demo scale (single-digit concurrent users). No horizontal scaling in v1. Module boundaries allow splitting later.

## 12. Failure Scenarios

| Failure | Expected behaviour |
|---|---|
| Database unavailable | API returns 503 `SERVICE_UNAVAILABLE`; frontend shows error state with Retry; urgent button still works and shows advice from the **bundled** L1/L2 text (no network needed) |
| Backend asleep (Render cold start) | Frontend shows "Connecting…" for up to 60 s, then error state |
| API timeout | Frontend timeout 20 s → error state; no duplicate submission (idempotency key on POSTs that create records) |
| Rule file missing/invalid at startup | Backend refuses to start (fail fast) and logs which file |
| ML model file missing | Backend refuses to start |
| LLM / embedding API fails | Fallback messages per spec; workflow never blocks |
| Auth fails / token expired | 401 → frontend signs out and returns to sign-in, keeping unsaved form input in memory where possible |
| Storage fails | Upload shows error; nothing half-saved (database row only after a successful upload) |
