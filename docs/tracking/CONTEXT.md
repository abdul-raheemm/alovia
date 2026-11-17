# CONTEXT — start here (for any new agent, chat or teammate)

**Last updated:** 2026-11-16 by Claude Code (session 1) — update the "Current state" section at the end of every session.

## What Alovia is
A woman-centric pregnancy web app (patient app) with a doctor dashboard (doctor app) and one FastAPI backend. Capstone project of a 3-person team at MJCET (AI & DS), led by Raheem. Research prototype — synthetic/test data only, not for clinical use.

## Modules
| # | Module | State |
|---|---|---|
| 1, 2 | Fetal & maternal ML risk (XGBoost + SHAP) | Trained and working in old `ml-test`; to be moved into the new backend (Phase 1) |
| 4 | Pregnancy Journey (patient home) | Spec done → build Phase 2 |
| 7 | Symptom Tracking | Spec done → Phase 3 |
| 3 | Genetic Risk (rule-based) | Spec done → Phase 4 |
| 6 | Doctor Dashboard + Admin | Spec done → Phase 5 |
| 5 | RAG Knowledge Assistant | Spec done → Phase 7, after the knowledge base is finished (196 of 600+ files collected) |

## Where things are
- Rules for the agent: `/CLAUDE.md`
- What to build: `docs/PRD.md`, `docs/modules/*.md`
- How: `docs/ARCHITECTURE.md`, `docs/DATABASE.md`, `docs/API.md`, `docs/DESIGN_SYSTEM.md`, `docs/UX_FLOWS.md`
- Decisions: `docs/DECISIONS.md` · Plan: `docs/ROADMAP.md`
- Progress: `docs/tracking/PROGRESS.md` · Session log: `docs/tracking/HISTORY.md` · Agent errors: `docs/tracking/ERROR_LOG.md`

## Old material (inside the root folder but git-ignored; read/copy only, do not modify)
- `C:\Users\Engineer\Desktop\Alovia\ml-test` — old prediction backend (`app/main.py`, `app/schemas.py`, `app/models/` with 8 model files, `requirements.txt`, Python 3.14 `.venv`). Deployed earlier on Render; used by a Bolt test frontend with an old Supabase project.
- `C:\Users\Engineer\Desktop\Alovia\rag` — knowledge base collection: scripts (`crawl_nhs*.py`, `extract_*.py`, `validate_kb.py`, …), `alovia-knowledge-base/` (`clean/`, `raw/`, CSV logs, `PROGRESS.md`), `archive/`.

## Environment
Windows, PowerShell, `py` launcher. Backend uses a Python 3.14 virtual environment (DEC-030). Node.js LTS for the frontends.

## Current state
- Phase 0 (documentation) complete — awaiting owner review.
- Phase 1 started: GitHub repo exists (origin = `abdul-raheemm/alovia`, public); first commit holds docs, `CLAUDE.md` and `.gitignore` only; old folders are git-ignored.
- Knowledge base copied into `knowledge-base/` (collection continues there). Supabase project created (Mumbai; email confirmation on; JWT signing keys; session pooler connection).
- Backend skeleton done (`backend/`, venv `backend/.venv` on Python 3.14): app factory, settings, JSON logs with request ID, error envelope, `GET /api/v1/health`.
- ML reference outputs recorded from the old backend: `backend/tests/fixtures/ml_reference_outputs.json` (12 owner-approved cases). Source datasets are kept outside the repo in `C:\Users\Engineer\Desktop\alovia-data` (copies of `Documents\Alovia major project\ml modules\CTG.xls` and `Maternal_Risk.csv`; the maternal file is the raw 6,103-row version).
- Supabase Data API is enabled and exposes tables automatically; no RLS (accepted risk DEC-022, left until Phase 8 by the owner).
- Auth part 1 done: every protected route can use `get_current_user` (Supabase token verified with the project's public keys). The app now starts with `uvicorn app.main:create_app --factory`.
- Database: migration 0001 applied to the main project (9 Phase 1 tables, no RLS — DEC-022). Migration tests run against the separate `alovia-test` project (DEC-034). Both URLs in `backend/.env` are Session pooler URLs.
- Next: `/me` + consent + role lookup (see `PROGRESS.md`).
- Open owner actions: confirm whether result tables also need a separate `patient_id` index (DATABASE.md §6; only the `(patient_id, created_at DESC)` index exists); fill legal placeholders (team, supervisor, contact email — kept as `[OPEN]` placeholders until then).
