# HISTORY — session log

One entry per work session, newest at the **bottom**. The owner copies entries from here into the Claude planning chat for review, so each entry must be complete on its own.

## Entry template (copy exactly)

```
## Session <number> — <YYYY-MM-DD> — <short title>
Who: <person> (+ agent: Claude Code / other)
Phase / task: <phase and task from PROGRESS.md>
Goal: <one line>

Done:
- <what was implemented or changed>

Files changed:
- <path> — <added / modified / deleted> — <why>

Decisions made (with owner approval):
- <decision> → recorded as DEC-0xx (or "none")

Checks run (exact commands and results):
- <command> → <result, e.g. "58 passed, 0 failed">

Errors met: <count> (details in ERROR_LOG.md: ERR-0xx, …) or "none"
Suggestions raised (not implemented): <list or "none">
Docs updated: <list>
Open questions for the owner: <list or "none">
Next step: <one line>
```

---

## Session 0 — 2026-11-16 — Documentation set
Who: Raheem + Claude (planning chat)
Phase / task: Phase 0 — documentation
Goal: create all project documents before coding.

Done:
- Module specs: Genetic (v1.0), Symptom Tracking (v1.0), Journey (v1.1), Dashboard (v1.0), RAG (v1.0), ML models (v1.0).
- Blueprint documents: PRD, UX_FLOWS, DESIGN_SYSTEM, ARCHITECTURE, DATABASE, API, SECURITY, CODE_STYLE, TESTING, AGENTS (pointer), ENVIRONMENT, ERROR_HANDLING, OBSERVABILITY, DEPLOYMENT, DECISIONS, ROADMAP, CHANGELOG, START_PROMPT.
- Legal drafts and compliance checklist; tracking files; CLAUDE.md; README.

Decisions made: DEC-001 … DEC-029. Owner answers the same day: DEC-022 (RLS in Phase 8), DEC-023 (18+), DEC-024 (invite-link sign-up only); ML reference outputs recorded from the old backend; legal details left as placeholders.
Checks run: palette contrast ratios computed (all ≥ 4.5:1).
Errors met: none.
Open questions for the owner: see CONTEXT.md "Open owner actions".
Next step: owner review, then Phase 1 with the start prompt.

## Session 1 — 2026-11-16 — Clean first commit, .gitignore, Python 3.14
Who: Raheem + agent: Claude Code
Phase / task: Phase 1 — .gitignore and first commit
Goal: get the old folders out of git and record the owner's decisions.

Done:
- `.gitignore` added; first commit rewritten without `ml-test/`, `rag/` and `alovia_tree.txt`; force-pushed.
- graphify installed (graphifyy 0.9.111); graph built with the old folders excluded; post-commit hook installed.
- Docs updated for Python 3.14 and the knowledge-base copy task.

Files changed:
- `.gitignore` — added — DEC-019
- `alovia_tree.txt` — deleted — stray folder listing
- docs (see "Docs updated") — modified — owner decisions

Decisions made (with owner approval):
- Backend uses Python 3.14 → DEC-030 (supersedes DEC-018)
- `raw/` NHS and MedlinePlus pages are licence-checked and approved by the owner; licence and attribution details stay with each file → no new DEC
- Knowledge-base copy is a Phase 1 task; the RAG module stays Phase 7 → no new DEC

Checks run (exact commands and results):
- `git ls-files ml-test rag alovia_tree.txt` → 0 files
- `git rev-list --objects HEAD | grep` old-folder paths → 0
- `git check-ignore -v` on 9 paths → all ignored; `backend/.env.example` not ignored
- file counts before/after → ml-test 13921/13921, rag 404/404
- `git push --force-with-lease origin main` → `+ 360ca84...4d29b90 main -> main (forced update)`
- `py -0` → 3.15.2, 3.14.10, 3.13.17
- graphify detect → 0 old-folder files

Errors met: 3 (details in ERROR_LOG.md: ERR-001, ERR-002, ERR-003)
Suggestions raised (not implemented): none
Docs updated: DECISIONS, ARCHITECTURE, DEPLOYMENT, CONTEXT, PROGRESS, ROADMAP, knowledge-base/README, HISTORY, ERROR_LOG, CLAUDE.md, README.md
Open questions for the owner: four `rag/` root CSVs; the old `ml-test` venv was built on another PC and cannot run here
Next step: copy the knowledge base into `knowledge-base/` (plan first).

## Session 2 — 2026-11-17 — Knowledge base copy, Supabase project, .env.example
Who: Raheem + agent: Claude Code
Phase / task: Phase 1 — copy the knowledge base; Supabase owner action
Goal: bring the knowledge base into the repo and prepare backend configuration.

Done:
- `rag/alovia-knowledge-base/*`, the 4 root CSVs → `knowledge-base/`; `rag/*.py` → `knowledge-base/tools/`; `rag/archive/*.py` → `knowledge-base/tools/archive/`.
- Option A: one path line changed in `crawl_nhs.py`, `extract_nhs_all.py`, `flags_nhs.py`; old paths in `knowledge-base/PROGRESS.md` updated.
- `.gitattributes`: `raw/` kept byte-identical, `clean/` kept LF.
- graphify skill set to run extraction subagents on Sonnet (owner approved after /usage review).
- Owner created the Supabase project (Mumbai; email confirmation on; JWT signing keys; session pooler connection string).
- `backend/.env.example` created (Phase 1 variables from ENVIRONMENT.md).

Files changed:
- `knowledge-base/` — added (405 files) — collection moved into the repo
- `.gitattributes` — added — line-ending rules for the knowledge base
- `backend/.env.example` — added — owner fills `backend/.env`
- docs/tracking/* — modified — records

Decisions made (with owner approval):
- Copied scripts run from `knowledge-base/` (option A) → no new DEC
- Large MedlinePlus XML (29 MB) committed → no new DEC

Checks run (exact commands and results):
- SHA-256 rag/ vs knowledge-base/ → 404 pairs: 401 identical, 3 intentionally edited, 0 missing, 0 unexpected
- `find rag -type f | wc -l` → 404 (untouched)
- `py -3.13 tools/validate_kb.py .` (in knowledge-base/) → 196 valid, 0 with errors, 10 warnings
- `cmp knowledge-base/manifest.csv rag/alovia-knowledge-base/manifest.csv` → identical
- `git check-ignore` → `backend/.env` ignored; `backend/.env.example` not ignored

Errors met: 2 (ERR-004, ERR-005)
Suggestions raised (not implemented): none
Docs updated: PROGRESS, CONTEXT, HISTORY, ERROR_LOG, knowledge-base/README, knowledge-base/PROGRESS
Open questions for the owner: Data API / RLS options chosen at project creation (not reported yet)
Next step: backend skeleton plan (Python 3.14).

## Session 3 — 2026-11-17 — Backend skeleton
Who: Raheem + agent: Claude Code
Phase / task: Phase 1 — backend skeleton
Goal: FastAPI app factory, settings, logging, error envelope and `/health` on Python 3.14.

Done:
- `backend/.venv` (Python 3.14.10); packages pinned in `requirements.txt` / `requirements-dev.txt`.
- `app/main.py` (`create_app`), `app/core/config.py` (APP_ENV, LOG_LEVEL, CORS_ORIGINS from `backend/.env`), `app/core/logging.py` (JSON logs, request ID, `X-Request-ID`, crash → INTERNAL_ERROR), `app/core/errors.py` (`AppError` + handlers), `app/common/responses.py` (envelope), `app/api/health.py`.
- 11 tests (unit + integration). `httpx` replaced by `httpx2` (Starlette deprecation). `.coverage` git-ignored.

Files changed:
- `backend/**` — added — skeleton and tests
- `.gitignore` — modified — ignore `.coverage`
- docs/tracking/* — modified — records

Decisions made (with owner approval):
- `/health` reports `models_loaded`/`rules_loaded` as false and omits `db` until the database task → no new DEC
- Error code for statuses outside API.md §3 (e.g. 405) left `TODO(OPEN)`; placeholder `VALIDATION_ERROR`

Checks run (exact commands and results):
- `pytest --cov=app` → 11 passed, 0 failed; coverage 100% (124 statements)
- `pytest -W error::DeprecationWarning` → 11 passed (no deprecation warnings)
- `ruff check .` → All checks passed; `ruff format --check .` → 12 files already formatted
- `mypy app tests` (strict) → Success: no issues found in 12 source files
- `uvicorn app.main:app` + `curl /api/v1/health` → 200, envelope, `x-request-id` header; `curl /api/v1/nope` → NOT_FOUND envelope

Errors met: 2 (ERR-006, ERR-007)
Suggestions raised (not implemented): none
Docs updated: PROGRESS, CONTEXT, HISTORY, ERROR_LOG
Open questions for the owner: 405 error code; Data API / RLS setting at project creation; `backend/.env` not filled yet
Next step: ML reference outputs — owner agrees the input set first.

## Session 4 — 2026-11-17 — ML reference outputs
Who: Raheem + agent: Claude Code
Phase / task: Phase 1 — record ML reference outputs before moving ML code
Goal: save the old backend's exact outputs for owner-approved inputs (ml_models_spec.md §6).

Done:
- Datasets found in `Documents\Alovia major project\ml modules\` and copied (not moved) to `C:\Users\Engineer\Desktop\alovia-data` (outside the repo). Model files there are identical to `ml-test`'s.
- Old `ml-test/app` copied to a temporary folder and run in a separate Python 3.14 venv with the old exact versions (xgboost 3.4.1, scikit-learn 1.9.1, shap 0.52.0, numpy 2.5.3, pandas 3.0.5, joblib 1.6.0, scipy 1.18.1, numba 0.67.0, fastapi 0.141.1, pydantic 2.13.5; xlrd 2.0.2 to read CTG.xls).
- 12 owner-approved cases sent through the old `/predict/fetal` and `/predict/maternal` endpoints; saved with inputs, full outputs, package versions and model SHA-256 hashes.

Files changed:
- `backend/tests/fixtures/ml_reference_outputs.json` — added — reference for the ML-move regression tests
- docs/tracking/* — modified — records

Decisions made (with owner approval):
- Input set: fetal CTG.xls "Data" rows 1194 (Normal), 552 (Suspect), 1949 (Pathological); maternal Patient IDs 4442 (Low), 5546 (Mid), 2192 (High), plus all 6 High rows predicted Mid (114, 688, 1463, 2800, 3663, 5186) — the documented misclassification case is among them but cannot be identified without the notebook.
- Maternal CSV columns `Blood Glucose(HbA1c)` and `Blood Glucose(Fasting hour-mg/dl)` map by position to the model's `HbA1c mmol/mol` and `Fasting mmol/L` (renamed only).
- Data API left enabled until Phase 8.

Checks run (exact commands and results):
- SHA-256 of copied datasets vs originals → identical; Documents model files vs ml-test → 8/8 same
- old maternal model on all 6,103 rows → 99.74% agree with labels; 6 High→Mid; 0 High→Low
- old fetal model on all 2,126 rows → 97.88% agree; 0 Pathological→Normal
- `record_reference.py` run twice → `cmp run1.json run2.json` byte-identical
- fixture model hashes vs `ml-test/app/models` → 8/8 match; no names in the fixture
- `pytest` (backend) → 11 passed

Errors met: none
Suggestions raised (not implemented): turn off the Data API before Phase 8 (owner: leave it)
Docs updated: PROGRESS, CONTEXT, HISTORY
Open questions for the owner: `backend/.env` is still empty on disk
Next step: auth dependency + `/me` + consent route (plan first).

## Session 5 — 2026-11-17 — Auth part 1: token check
Who: Raheem + agent: Claude Code
Phase / task: Phase 1 — auth (split approved: token check → migration → `/me` + consent)
Goal: verify the Supabase access token on protected requests (SECURITY.md §0-1).

Done:
- `app/core/auth.py`: `get_current_user` — Bearer token, signature via the project's JWKS (cached), issuer, audience `authenticated`, expiry, subject; ES256/RS256 only; 401 `AUTH_REQUIRED` with the reason logged (never the token); 503 when the key server is unreachable.
- `SUPABASE_JWKS_URL` and `SUPABASE_JWT_ISSUER` required in settings; app built by factory (`uvicorn app.main:create_app --factory`); README updated.
- `PyJWT[crypto]==2.15.1`, `cryptography==50.0.2` pinned.

Files changed:
- `backend/app/core/auth.py`, `backend/tests/integration/test_auth.py` — added
- `backend/app/core/config.py`, `backend/app/core/logging.py`, `backend/app/main.py`, `backend/requirements.txt`, `README.md` — modified
- `backend/tests/unit/test_config_and_logging.py`, `backend/tests/integration/test_app_basics.py` — modified (pass the two new required settings; one new test that they are required; nothing removed or weakened)
- docs: DECISIONS, ENVIRONMENT, tracking/* — modified

Decisions made (with owner approval):
- Task split → token check, then Alembic + migration, then `/me` + consent
- Consent version → DEC-031 (option A); user rows/roles → DEC-032

Checks run (exact commands and results):
- `pytest -W error::DeprecationWarning --cov=app` → 27 passed, 0 failed; coverage 99%
- `ruff check .` → All checks passed; `ruff format --check .` → 14 files already formatted
- `mypy app tests` (strict) → Success: no issues found in 14 source files
- `uvicorn app.main:create_app --factory` with empty `.env` → refused to start ("Field required" for both auth settings)
- `backend/.env` shape check (no values shown) → all keys set and matching the project except `DATABASE_URL` (empty)

Errors met: 2 (ERR-008, ERR-009 — this entry was first committed in 09393fa without the doc edits it lists; they followed in the next commit)
Suggestions raised (not implemented): none
Docs updated: DECISIONS (DEC-031, DEC-032), ENVIRONMENT, README, PROGRESS, CONTEXT, HISTORY, ERROR_LOG
Open questions for the owner: `DATABASE_URL` empty; confirm `aud = "authenticated"` against one real token (needs owner OK for one call to the project's key URL); which flow creates a patient's `users` row (DEC-032 covers admins/owner and doctors)
Next step: Alembic + Phase 1 migration plan.

## Session 6 — 2026-11-17 — Alembic + Phase 1 migration
Who: Raheem + agent: Claude Code
Phase / task: Phase 1 — Alembic setup + Phase 1 migration
Goal: create the 9 Phase 1 tables exactly as DATABASE.md describes, tested on a separate database first.

Done:
- `app/core/database.py` (engine, model base with fixed constraint names); models in `app/modules/users/models.py` (7 tables) and `app/modules/predictions/models.py` (2 tables; Phase 5 columns left out).
- `alembic.ini`, `migrations/env.py`, hand-written migration `0001` with a full downgrade.
- `/health` reports `db: ok|error`. Settings: `DATABASE_URL` (required), `TEST_DATABASE_URL` (optional).
- Tests: shared `tests/helpers.py`; `test_migrations.py` (upgrade/downgrade/upgrade, database == models, every CHECK/unique/partial-unique rule, FK restrict, `/health` db ok, project-id safety check).
- Owner created `alovia-test`; both URLs switched to Session pooler.
- With owner approval, migration applied to the main project.

Files changed:
- `backend/app/core/database.py`, `backend/app/modules/**`, `backend/alembic.ini`, `backend/migrations/**`, `backend/tests/helpers.py`, `backend/tests/integration/test_migrations.py` — added
- `backend/app/api/health.py`, `backend/app/core/config.py`, `backend/app/main.py`, `backend/pyproject.toml`, `backend/requirements.txt`, `backend/.env.example`, three existing test files (moved to the shared settings helper; `/health` expectations gained `db`; nothing removed or weakened) — modified
- docs: DECISIONS, DATABASE, TESTING, ENVIRONMENT, tracking/* — modified

Decisions made (with owner approval):
- No FK from `users.id` to `auth.users` → DEC-033
- Test database = separate Supabase project `alovia-test` → DEC-034
- Packages: SQLAlchemy 2.1.9, alembic 1.20.1, psycopg[binary] 3.3.9

Checks run (exact commands and results):
- `alembic upgrade head --sql` (offline) vs the models' SQL → 17/17 statements identical
- `pytest -W error::DeprecationWarning -W error::ResourceWarning -W error::pytest.PytestUnraisableExceptionWarning --cov=app` → 39 passed (run twice), coverage 100%; `alovia-test` left empty (only `alembic_version`)
- `ruff check .` → All checks passed; `ruff format --check .` → 24 files already formatted; `mypy app tests migrations` → Success: no issues found in 24 source files
- Main project: `alembic current` → (none); `alembic upgrade head`; `alembic current` → `0001 (head)`; tables → the 9 + `alembic_version`; `compare_metadata` → none; `GET /api/v1/health` → 200, `db: ok`

Errors met: 8 (ERR-010 … ERR-017)
Suggestions raised (not implemented): none
Docs updated: DECISIONS (DEC-033, DEC-034), DATABASE, TESTING, ENVIRONMENT, PROGRESS, CONTEXT, HISTORY, ERROR_LOG
Open questions for the owner: separate `patient_id` index on the result tables (DATABASE.md §6) — only the composite index exists
Next step: `/me` + consent + role lookup (plan first).

## Session 7 — 2026-11-17 — /me + consent + role lookup
Who: Raheem + agent: Claude Code
Phase / task: Phase 1 — auth part 2
Goal: `GET /me`, `POST /me/consent`, and the users-row lookup every later route needs.

Done:
- `app/core/database.py`: `get_db` (one session per request; uncommitted work is rolled back).
- `app/modules/users/{schemas,service,router}.py`: `get_account` (403 without an active users row), `get_me`, `record_consent` (current version only, 18+ only, no duplicate rows).
- `CONSENT_VERSION` in `app/core/config.py`, checked against `docs/legal/CONSENT_TEXT.md` by a test (DEC-031).
- Typed `Envelope[T]` response model so OpenAPI shows the data shapes.
- Shared test infrastructure: `tests/conftest.py` (test-database fixtures), token helpers in `tests/helpers.py`.

Files changed:
- `backend/app/core/{config,database,auth}.py`, `backend/app/common/responses.py`, `backend/app/main.py` — modified
- `backend/app/modules/users/{schemas,service,router}.py`, `backend/tests/conftest.py`, `backend/tests/integration/test_me.py` — added
- `backend/tests/helpers.py`, `backend/tests/integration/{test_auth,test_migrations}.py`, `backend/tests/unit/test_config_and_logging.py` — modified (shared helpers; nothing removed or weakened)
- docs: API, DATABASE, DECISIONS, tracking/*

Decisions made (with owner approval):
- 403 `FORBIDDEN` for a signed-in user without an active users row
- Composite index only on result tables → DEC-035; patient users row from `/patient/link` → DEC-036
- Sign-in audit entry stays `TODO(OPEN)` (sign-in happens in Supabase, not the backend)
- Owner permission to finish Phase 1 without per-task approval

Checks run (exact commands and results):
- `pytest -W error::DeprecationWarning -W error::ResourceWarning -W error::pytest.PytestUnraisableExceptionWarning --cov=app` → 51 passed, coverage 100%
- `ruff check .` → All checks passed; `ruff format --check .` → 29 files already formatted; `mypy app tests migrations` → Success: no issues found in 29 source files

Errors met: 1 (ERR-018)
Suggestions raised (not implemented): none
Docs updated: API (`/me`, `/me/consent` shapes), DATABASE §6, DECISIONS (DEC-035, DEC-036), PROGRESS, CONTEXT, HISTORY, ERROR_LOG
Open questions for the owner: none new
Next step: move the ML code with regression tests.
