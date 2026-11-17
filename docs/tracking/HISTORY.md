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

## Session 8 — 2026-11-17 — Move the ML code
Who: Raheem + agent: Claude Code (Phase 1 permission, no per-task approval)
Phase / task: Phase 1 — move ML code + model files; regression tests
Goal: the new backend serves the same models with byte-for-byte the same outputs as ml-test.

Done:
- 8 model files copied from `ml-test/app/models/` (read-only source) to `backend/ml_models/`; `.gitattributes`: `backend/ml_models/** -text` so git never changes their bytes.
- `RiskModel` moved to `app/modules/predictions/risk_model.py` token-for-token (only line wrapping and one lint comment differ); `load_models()` loads both models once per process; `create_app` fails fast if a file is missing; `/health` reports `models_loaded`.
- ML packages pinned at the old backend's exact versions; one mypy exception for the unchanged, partly untyped file.
- `tests/unit/test_ml_regression.py`: model-file hashes, ML package versions, and all 12 reference cases (sent through the same input-schema path as the old endpoint).

Files changed:
- `backend/ml_models/*` (8), `backend/app/modules/predictions/risk_model.py`, `backend/tests/unit/test_ml_regression.py` — added
- `backend/app/main.py`, `backend/app/api/health.py`, `backend/requirements.txt`, `backend/pyproject.toml`, `.gitattributes`, `backend/tests/integration/test_app_basics.py` (`models_loaded` now true) — modified
- docs: ml_models_spec, tracking/*

Decisions made (with owner approval): none new (Phase 1 permission)

Checks run (exact commands and results):
- `sha256sum -c` of the copied model files → 8 OK
- token diff of the `RiskModel` class vs `ml-test/app/main.py` → only whitespace and one `# noqa` comment differ
- `pytest -W error::DeprecationWarning -W error::ResourceWarning -W error::pytest.PytestUnraisableExceptionWarning --cov=app` → 65 passed (12/12 ML cases identical), coverage 99% (3 unreachable fallback lines in the unchanged ML code)
- `ruff check .`, `ruff format --check .` → pass; `mypy app tests migrations` → Success: no issues found in 31 source files

Errors met: none (one edit-script assertion fired because the formatter had already wrapped the line; nothing to change)
Suggestions raised (not implemented): none
Docs updated: ml_models_spec §6, PROGRESS, CONTEXT, HISTORY
Open questions for the owner: none
Next step: frontend workspace.

## Session 9 — 2026-11-17 — Sign-up, frontend, seed, check_all, Phase 1 release
Who: Raheem + agent: Claude Code (Phase 1 permission, no per-task approval)
Phase / task: Phase 1 — invite sign-up (backend + frontend), frontend workspace, app shells, PWA, seed, check_all, review
Goal: finish Phase 1.

Done:
- Backend: `GET /invites/{code}/check`, `POST /patient/link` (creates the patient's users row, DEC-036; one transaction; audit entries); invite settings in `backend/rules/dashboard/config.yaml`; `scripts/export_openapi.py`; `scripts/seed_dev.py`.
- Frontend workspace (`frontend/`): `apps/patient-web`, `apps/doctor-web`, `packages/ui` (tokens copied from DESIGN_SYSTEM, Button/Field/Card/Logo/Markdown/SignInForm/ThemeSwitch/states), `packages/shared` (API client with the ERROR_HANDLING retry and timeout rules, user messages, auth-only Supabase client, legal texts read from `docs/legal`, generated API types).
- Patient app: landing with disclaimer and no open sign-up, invite check, sign-up with the exact consent checkboxes (Continue only when both are ticked), check-email page, sign-in, account gate (link → consent → app), shell with bottom/side nav and urgent placeholder, More (theme, legal, sign-out), legal and about pages, PWA manifest and icons.
- Doctor app: sign-in, account gate (doctor/admin only), side bar (Admin only for admins), top bar with theme switch and sign-out, placeholders, legal and about pages.
- `scripts/check_all.ps1` / `.sh`; version 0.1.0; CHANGELOG 0.1.0.

Files changed:
- `backend/app/modules/users/{invites,router,schemas}.py`, `backend/rules/dashboard/config.yaml`, `backend/scripts/*`, `backend/tests/integration/{test_invites,test_seed}.py`, `backend/requirements*.txt`, version files — added/modified
- `frontend/**` — added; `scripts/check_all.*` — added; `.gitignore` — modified
- docs: API, DECISIONS (DEC-037…039), DESIGN_SYSTEM §3.4, DEPLOYMENT, TESTING §7, README, CHANGELOG, tracking/*

Decisions made (with owner approval): 403 for missing accounts and sign-in audit left open (owner, this session); DEC-037, DEC-038, DEC-039 under the owner's Phase 1 permission.

Checks run (exact commands and results):
- `powershell -ExecutionPolicy Bypass -File scripts\check_all.ps1` → backend lint/format/types pass, 78 backend tests passed; frontend format/lint/types pass, 23 unit tests passed, both builds pass (PWA precache 36 entries), 26 E2E tests passed with axe (375px light, 1280px dark) → "All checks passed.", exit code 0
- failure probe (copy of check_all with a failing first step) → stopped, exit code 1

Errors met: 9 (ERR-019 … ERR-027)
Suggestions raised (not implemented): none
Docs updated: API, DECISIONS, DESIGN_SYSTEM, DEPLOYMENT, TESTING, README, CHANGELOG, PROGRESS, CONTEXT, HISTORY, ERROR_LOG
Open questions for the owner: doctor/admin consent; 405 error code; sign-in audit entry; visual review of colours and fonts (DEC-015); legal placeholders
Next step: owner review of Phase 1; then the Phase 2 plan.

## Session 10 — 2026-11-17 — Phase 2 tasks 1-2: migration 0002 and the date engine
Who: Raheem + agent: Claude Code (owner: build tasks 1 and 2 without asking)
Phase / task: Phase 2 — migration; GA/month/trimester calculations
Goal: the Journey tables and the pregnancy-date engine everything else depends on.

Done:
- Phase 1 merged into `main` (fast-forward to 11f1b07) and pushed.
- Phase 2 plan posted; owner answers recorded (DEC-015 confirmed, DEC-040 … DEC-044).
- Column helpers (`uuid_pk`, `created_now`, `fk`) moved to `app/core/database.py` (users models now use them; generated SQL unchanged); `app/models.py` registers every model.
- Models: `app/modules/journey/models.py` (pregnancy_date_history, appointments, notifications with NULLS NOT DISTINCT uniqueness), `app/modules/dashboard/models.py` (doctor_notes, inbox_items).
- Migration `0002` (hand-written, full downgrade); applied to the main project.
- `rules/journey/config.yaml` (Journey §14.4 defaults, month map, six nav items) checked at startup by `app/modules/journey/config.py`.
- `app/modules/journey/engine.py`: GA, completed weeks/days, days to go, content week (stops at 42), trimester, month from config, home states, due date from LMP and ultrasound, local "today" (Asia/Kolkata), calendar range, milestones.
- `tzdata` pinned.

Files changed:
- added: `backend/app/models.py`, `backend/app/modules/{journey,dashboard}/*`, `backend/migrations/versions/20261117_0002_phase2_journey.py`, `backend/rules/journey/config.yaml`, `backend/tests/unit/test_journey_engine.py`
- modified: `backend/app/core/database.py`, `backend/app/modules/users/models.py`, `backend/app/main.py`, `backend/app/api/health.py`, `backend/migrations/env.py`, `backend/requirements.txt`, `backend/tests/integration/{test_migrations,test_app_basics}.py`
- docs: DECISIONS, DATABASE, DESIGN_SYSTEM, PROGRESS, CONTEXT, HISTORY

Decisions made (with owner approval): DEC-015 confirmed; DEC-040 nav items; DEC-041 message placeholder; DEC-042 content option C; DEC-043 size-reference draft; DEC-044 inbox_items moved to Phase 2.

Checks run (exact commands and results):
- users/predictions SQL before vs after the helper refactor → identical
- `alembic upgrade 0001:0002 --sql` vs the models' SQL → 10/10 statements identical; downgrade drops exactly the 5 new tables
- `pytest -W error::DeprecationWarning -W error::ResourceWarning -W error::pytest.PytestUnraisableExceptionWarning --cov=app` → 123 passed; journey and dashboard modules 100% covered (total 99%: the 3 known ML fallback lines)
- migration tests on alovia-test: upgrade → downgrade to 0001 (only Phase 1 tables left) → base → upgrade; database == models; new CHECK, length and NULLS NOT DISTINCT rules reject bad rows
- main project: `alembic current` 0001 → `alembic upgrade head` → `0002 (head)`; tables listed; compare_metadata → none
- `ruff check .`, `ruff format --check .`, `mypy app tests migrations scripts` → pass

Errors met: none
Suggestions raised (not implemented): seed one test patient per home state (no date, 39, 40, 42+)
Docs updated: DECISIONS, DATABASE (§3.6, §13), DESIGN_SYSTEM §11, PROGRESS, CONTEXT, HISTORY
Open questions for the owner: how the home header shows weeks past 42 (the engine stops the content week at 42; the display wording is decided in task 5 with the messages)
Next step: Phase 2 task 0 (Phase 1 follow-ups) or task 3 (dates) — plan first.

## Session 11 — 2026-11-17 — Phase 2 task 3: dates and onboarding
Who: Raheem + agent: Claude Code
Phase / task: Phase 2 — dates onboarding + validation (spec §5; §15 items 2, 10)
Goal: entering and changing pregnancy dates, end to end.

Done:
- Engine: `dates_from_lmp/due_date/ultrasound` with rules D1-D3 (`DateRuleError` carries code + field), `needs_override_confirmation` (§5.3).
- `rules/journey/messages.yaml`: every §13.2 message key with intent copied from the spec and `text: null` (DEC-041); loader validates it at startup.
- `get_patient` dependency (users service): patient role + linked record + current consent, 403 otherwise.
- Routes `GET /patient/journey/home` and `PUT /patient/journey/dates` (shapes now in API.md): home states, derived pregnancy numbers, nav items from config, notices; date changes write `pregnancy_date_history`; same-dates writes nothing.
- Patient app: Home header/onboarding card (estimate label, past-due and 42+ notices, counter stops at 42), Dates screen (3 options, field errors from D-codes, §5.3 confirmation dialog, skip allowed), nav bar driven by the backend's six items (DEC-040), More → Pregnancy dates. `put` added to the shared API client; API types regenerated.
- Pure helpers split from the data hook so they are unit-testable.

Files changed:
- backend: `app/modules/journey/{engine,config,schemas,service,router}.py`, `rules/journey/messages.yaml`, `app/modules/users/service.py`, `app/main.py`, tests (`test_journey_engine.py` +17, new `tests/integration/test_journey_dates.py`, `tests/helpers.py` add_linked_patient)
- frontend: `apps/patient-web/src/app/{journey,useJourneyHome}.ts(+test)`, `pages/{HomePage,DatesPage}.tsx`, `components/PatientShell.tsx`, `pages/SimplePages.tsx`, `app/App.tsx`; `packages/shared` (put, journey types); `e2e/helpers.ts` (fake session + journey mocks), `e2e/journey.spec.ts`
- docs: API, PROGRESS, CONTEXT, ERROR_LOG, HISTORY

Decisions made (with owner approval): build order rest of Phase 2 = 5 → 4 → 6 → 7 → 8 → 0 → 9 (owner, this session); no new DEC numbers.

Checks run (exact commands and results):
- backend `pytest -q` (strict warnings) → 167 passed (59 engine tests incl. D1-D3 boundaries; 27 route tests incl. access, limits-accepted, history rows, 409 flow, no-op saves)
- `ruff check .` / `ruff format --check .` / `mypy app tests migrations scripts` → pass
- frontend `npm test` → 27 passed; `typecheck`, `lint`, `format:check` → pass
- `npm run test:e2e` → 36 passed (onboarding flow, D1 at the field, §5.3 confirm dialog, six nav items, 42+ counter stop; axe on each at 375px light and 1280px dark)
- full `scripts/check_all.ps1` → All checks passed, exit 0 (run before commit)

Errors met: 2 (ERR-028, ERR-029)
Suggestions raised (not implemented): seed one test patient per home state (still open)
Docs updated: API, PROGRESS, CONTEXT, ERROR_LOG, HISTORY
Open questions for the owner: batched task-5 questions (sent in chat)
Next step: review of task 2 (owner request), then task 5 (home screen + month cards).

## Session 12 — 2026-11-17 — Phase 2 task 5: home screen blocks and month cards
Who: Raheem + agent: Claude Code (owner: run task 5 through; decisions a/b/c approved)
Phase / task: Phase 2 — home screen blocks; month cards + detail; illustrations
Goal: the §4.3 home screen and §4.4 month cards, with content plumbing ready for task 4.

Done:
- Content provider (§8): §8.1 `ContentItem`/`SizeReference` models (shape-validated, duplicate ids and double size-weeks refused), `PrototypeContentProvider` reading `backend/content/*.yaml` (EMPTY until task 4), §8.1 home selection rule (week item beats month item of the same type), `provider_for` refusing `knowledge_base` until Phase 7; loaded at startup (fail fast).
- Home payload: `months` (9 cards from the config map; empty when not active/dated or ended §11.3), `stage_items` (fetal_development + body_changes), `size` (null without a sourced row, §15 test 7), `next_appointment` (soonest upcoming; date-only counts all day). Defensive guard (owner decision c): an out-of-range stored due date logs an error and falls back to the onboarding state instead of a 500.
- `GET /patient/journey/months/{month}` (1-9 validated; 404 after the pregnancy ends; `is_current`).
- Patient app: baby card (placeholder drawing, gentle float via `motion`, honours reduced motion, §13.1 "typical" wording with source), This stage cards (Learn marking + source line, D15), prototype banner on every content screen (§8.3), quick log card, next appointment card, months strip (scroll-snap, current highlighted, aria-current), month detail page (banner, items, warning-signs link, typical note). 9 placeholder SVGs (simple shapes labelled "Placeholder", §7.1) + the script that makes them.
- `motion` 14.14.0 (exact pin, owner approval a); API types regenerated; shared exports MonthDetail/JourneyContentItem.

Files changed:
- backend: `app/modules/journey/content.py` (new), `schemas.py`, `service.py`, `router.py`, `app/main.py`, `content/prototype_content.yaml` + `content/size_reference.yaml` (new, empty), tests `unit/test_journey_content.py` (11) + `integration/test_journey_home_blocks.py` (8)
- frontend: `components/journey/JourneyBlocks.tsx`, `pages/MonthDetailPage.tsx` (new), `pages/HomePage.tsx`, `app/{journey,useJourneyHome}.ts`, `app/App.tsx`, `public/illustrations/month_1..9.svg`, `scripts/make-placeholder-illustrations.mjs`, `packages/shared` types, `e2e/helpers.ts`, `e2e/journey-home.spec.ts` (new), `e2e/journey.spec.ts`
- docs: API, PROGRESS, CONTEXT, HISTORY, ERROR_LOG

Decisions made (with owner approval): a) install `motion`; b) empty content files until task 4; c) defensive guard — all recorded this session, no new DEC numbers.

Checks run (exact commands and results):
- backend `pytest` (strict warnings) → 186 passed (content selection/validation, home blocks, guard, month detail, ended-pregnancy 404)
- `ruff check .` / `ruff format --check .` / `mypy app tests migrations scripts` → pass
- frontend `typecheck` exit 0, `lint` exit 0, `npm test` → 27 passed
- `npm run test:e2e` → 42 passed (blocks incl. "never 'your baby'" page check, strip → detail navigation, empty-content state; axe at 375px light and 1280px dark)
- `scripts/check_all.ps1` before commit → All checks passed, exit 0

Errors met: 3 (ERR-030 … ERR-032)
Suggestions raised (not implemented): none new
Docs updated: API, PROGRESS, CONTEXT, HISTORY, ERROR_LOG
Open questions for the owner: none — task 4 (fetch S1/S2/S3/S6 content, DEC-042/043) is next and already approved
Next step: task 4 — fill the content and size files from the approved sources.
