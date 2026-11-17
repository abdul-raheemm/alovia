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
- `/me` and `/me/consent` done; `get_account` (in `app/modules/users/service.py`) loads the users row for any route that needs the role.
- Owner permission (2026-11-17): finish the rest of Phase 1 without asking per task; normal approvals resume with Phase 2.
- ML moved: `backend/ml_models/` (8 files, byte-identical), `app/modules/predictions/risk_model.py` (logic unchanged), loaded once at startup; `/health` `models_loaded: true`. Prediction routes come in Phase 5.
- Frontend done (`frontend/`): patient-web (port 5173, installable PWA) and doctor-web (port 5174), `packages/ui` (tokens from DESIGN_SYSTEM, components, themes, fonts), `packages/shared` (API client, auth-only Supabase client, generated API types, legal texts from `docs/legal`). Invite-only sign-up with consent, sign-in/out, role routing, shells with placeholders for later phases.
- Seed: `backend/scripts/seed_dev.py` (1 admin, 2 doctors, 5 patients, invite links). Every check: `scripts/check_all.ps1`.
- **Phase 1 approved and merged into `main` (release 0.1.0).** Palette and fonts confirmed (DEC-015).
- **Phase 2 started** (branch `phase-2/migration-and-dates`). Done: migration 0002 (Journey tables + `inbox_items`, applied to the main project) and the date engine (`app/modules/journey/engine.py`, settings in `backend/rules/journey/config.yaml`, loaded at startup; `/health` `rules_loaded.journey: true`).
- Phase 2 task order: 0 Phase 1 follow-ups (doctor/admin consent, 405 code, sign-in audit) → 3 dates/onboarding → 4 content provider (fetch S1/S2/S3/S6, DEC-042/043) → 5 home + month cards → 6 calendar + appointments → 7 notifications + doctor notes → 8 pregnancy end → 9 review. Owner suggestion: strongest model for 3 and 8 (and 2, done).
- Owner notes: "add a dark and light theme option later" (the theme switch already has Light / Dark / System — clarify if something else is meant). Messages show "[Text pending doctor approval]" until approved (DEC-041).
- Open owner actions: fill legal placeholders (team, supervisor, contact email — kept as `[OPEN]` placeholders until then).
