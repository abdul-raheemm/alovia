# Alovia

A woman-centric pregnancy companion web app with a doctor dashboard.
**Research prototype (academic capstone, MJCET AI & DS). Not for clinical use. Use test data only.**

- **Patient app:** pregnancy journey home, calendar and appointments, symptom tracking with safety prompts, genetic inheritance estimates, shared results and doctor notes; knowledge assistant later.
- **Doctor app:** patient list with urgent-first inbox, CTG/vitals entry with explainable ML predictions, reviews, records, notes; minimal admin area.
- **Backend:** FastAPI (Python 3.14), Supabase (Postgres, Auth, Storage).

## Repository layout
```
CLAUDE.md        agent rules          docs/       all documentation (start with docs/tracking/CONTEXT.md)
backend/         FastAPI service      frontend/   patient-web, doctor-web, shared packages
knowledge-base/  RAG source library   assets/     illustration and animation sources
```
Full structure: `docs/ARCHITECTURE.md` §7.

## Status
See `docs/tracking/PROGRESS.md` and `docs/ROADMAP.md`. Current phase: **0 (documentation) complete → Phase 1 (foundation) next.**

## Requirements (development, Windows)
- Python **3.14** (`py -3.14`)
- Node.js LTS + npm
- Git
- A Supabase project (created by the owner; values go in `.env` files, see `docs/ENVIRONMENT.md`)

## Getting started
_Commands are filled in during Phase 1 and must stay correct._

```powershell
# Backend
cd backend
py -3.14 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
copy .env.example .env      # then fill values (see docs/ENVIRONMENT.md)
alembic upgrade head        # only after the owner approves
uvicorn app.main:create_app --factory --reload

# Frontends (new terminal)
cd frontend
npm install
npm run dev:patient         # http://localhost:5173
npm run dev:doctor          # http://localhost:5174
```

## Checks
See `docs/TESTING.md` §7. Run everything with `scripts\check_all.ps1`.

## Working with Claude Code
Open the repo in Claude Code and paste the prompt in `docs/START_PROMPT.md`. The agent follows `CLAUDE.md`, plans before coding, asks permission, and records its work in `docs/tracking/`.

## Licences and credits
Third-party fonts, icons, illustrations and content sources: `docs/legal/CREDITS.md`.
