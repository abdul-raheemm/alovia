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

## Session 13 — 2026-11-17 — Phase 2 task 4: prototype content and size reference
Who: Raheem + agent: Claude Code (DEC-042/043, option C network fetches approved)
Phase / task: Phase 2 — prototype YAML content + size reference (sourced)
Goal: fill the (previously empty) content files from the approved sources only.

Done:
- Fetched (web-fetch agents, verbatim-quote discipline): OWH "Stages of pregnancy" (page confirms it is free of copyright restrictions; exact values and short exact sentences used) and the OpenStax 28.3 page (NOT used — see licence finding). WHO weights: supplementary files turned out to be figures only, so Table 11 was downloaded as the published PNG and the 50th-percentile column transcribed by reading the image directly (no value estimated).
- `prototype_content.yaml`: 21 items — 9 month items (one per month), week/week-range samples (incl. the §8.1 precedence pair at week 20), NHS unchanged excerpts (indigestion, movements warning signs, dairy foods, exercise) each carrying the OGL attribution line, MedlinePlus public-domain items (guidance, checklist, discuss-with-doctor, trimester overview) shortened by removing words only. Every item: full §8.1 source, is_prototype, unreviewed.
- Spec §13.1 conflict handled: source sentences say "your baby is/weighs" (banned on screens); month-item bodies therefore carry only the sourced values inside the fixed frame "Typical at this stage: …". A unit test now scans every shipped item for the banned phrasings.
- `size_reference.yaml`: weeks 14, 16, 20, 24, 28, 32, 36 = 90/144/330/665/1189/1901/2745 g (WHO Table 11, 50th percentile, CC BY 4.0); lengths none (the chart gives weight only); draft objects lemon/tomato/mango/coconut/pineapple/melon/small watermelon (India-familiar where possible) pending doctor review R2.
- Icons: 7 Fluent Emoji colour SVGs + MIT LICENSE in `public/icons/fluent/`; BabyCard shows the object icon (decorative alt, name stays in the text).
- Tests updated from "files are empty" to sample coverage: all 9 types, all 9 months, banned-phrase scan, WHO values exact and strictly growing, icon file exists per size row, precedence at week 20; home-blocks route tests updated to the filled sample.

Files changed:
- backend: `content/prototype_content.yaml`, `content/size_reference.yaml`, `tests/unit/test_journey_content.py`, `tests/integration/test_journey_home_blocks.py`
- frontend: `components/journey/JourneyBlocks.tsx` (size icon), `public/icons/fluent/*` (8 files)
- docs: PROGRESS, CONTEXT, HISTORY, ERROR_LOG

Decisions made (with owner approval): under DEC-042/043. OpenStax dropped (licence) — owner decision requested on the spec's S2/D9 references.

Checks run (exact commands and results):
- `pytest` (strict warnings) → 187 passed; `ruff check .` / `ruff format --check .` / `mypy app tests migrations scripts` → pass
- frontend typecheck/lint/format/unit (27) → pass; `npm run test:e2e` → 42 passed
- `scripts/check_all.ps1` → All checks passed, exit 0

Errors met: 1 (ERR-033)
Suggestions raised (not implemented): none
Docs updated: PROGRESS, CONTEXT, HISTORY, ERROR_LOG
Open questions for the owner: OpenStax licence (spec S2/D9); doctor review of content items and size objects (R2) before release — tracked for the rule-review flow
Next step: task 6 (calendar + appointments, patient side) — one batched decision pending (react-day-picker install).

## Session 14 — 2026-11-17 — Phase 2 task 6: calendar and appointments (patient side)
Who: Raheem + agent: Claude Code
Phase / task: Phase 2 — calendar + appointments (Journey §6.4, §9.1-9.3, §14.2; UX_FLOWS P7, P8)
Goal: the Calendar and Appointments tabs and the home week strip, with the backend routes in API.md §4.2.

Done:
- Backend: `GET /patient/journey/calendar?from=&to=` (milestones from the existing engine, only for an active dated pregnancy; appointments by local day); `/patient/appointments` GET (upcoming/past), POST, PUT, DELETE — own patient-created only (doctor-added 403, another patient's 404). Appointment output carries `date`/`time` already in the config timezone; the home next-appointment block uses the same shape (fixes ERR-036).
- Patient app: Calendar tab (react-day-picker month view, navigation limited to pregnancy start .. due + 2 weeks, flag/clock marker icons with matching screen-reader words, tap a day for its milestones and appointments, `?day=` deep link); home week strip (this week, today marked, links into the calendar); Appointments tab (upcoming/past, add/edit with date, optional time, title ≤100, note ≤500, delete with confirmation, "Added by your doctor" read-only).
- Shared: API client `delete` (never retried), `TextAreaField`, new generated types.
- Milestone labels are neutral markers ("Week 29 begins", "Trimester 3 begins", "37 weeks", "Due date"); no medical wording.

Files changed:
- backend: `app/modules/journey/{schemas,service,router}.py`, `app/main.py`, `tests/integration/test_journey_calendar.py` (new), `tests/integration/test_journey_home_blocks.py`
- frontend: `apps/patient-web/src/pages/{CalendarPage,AppointmentsPage}.tsx` (new), `components/journey/{Appointments,CalendarMarkers}.tsx` (new), `components/journey/JourneyBlocks.tsx`, `pages/HomePage.tsx`, `app/{App.tsx,journey.ts,useAppointments.ts,calendar.test.ts}`, `index.css`, `packages/shared/src/{api.ts,api.test.ts,types.ts,index.ts,api-types.ts}`, `packages/ui/src/{components/Field.tsx,index.ts}`, `e2e/{calendar.spec.ts,helpers.ts,journey-home.spec.ts}`, `package.json`, `package-lock.json`
- docs: API.md, DECISIONS.md (DEC-045), PROGRESS, CONTEXT, HISTORY, ERROR_LOG

Decisions made (with owner approval): react-day-picker install (owner "go ahead", 2026-11-17), pinned 9.14.0 (DEC-045).
Interpretations (spec silent, flagged for review): date/time are entered and shown in the config timezone; milestones hidden after a pregnancy ends; the week strip sits after quick log on the home screen; past appointments listed most recent first.

Checks run (exact commands and results):
- `bash scripts/check_all.sh` → All checks passed, exit 0: pytest (strict warnings) 203 passed; ruff check/format, mypy pass; frontend typecheck, lint, format pass; Vitest 34 passed; Playwright 50 passed (phone-light + laptop-dark, axe on every screen)

Errors met: 5 (ERR-034 to ERR-038)
Suggestions raised (not implemented): none
Docs updated: API, DECISIONS, PROGRESS, CONTEXT, HISTORY, ERROR_LOG
Open questions for the owner: OpenStax licence (spec S2/D9) still open
Next step: task 7 (notifications bar + doctor notes, patient side).

## Session 15 — 2026-11-17 — Phase 2 task 7: notification bar and doctor notes (patient side)
Who: Raheem + agent: Claude Code
Phase / task: Phase 2 — notifications + doctor notes (Journey §4.2, §10.1-10.3, §11.3; UX_FLOWS P10)
Goal: in-app notifications generated on app open, and the read-only Doctor notes tab.

Done:
- Backend: `get_notifications` creates due notifications with one insert that skips existing ones (unique (patient, type, target_ref)), then lists unread; read/dismiss own only; `list_doctor_notes`. New `app/modules/dashboard/service.py` (`shared_notes`) so the journey module reads doctor notes through a service (ARCHITECTURE §8).
- Patient app: notification bar at the top of home (tap = open target + mark read, X = dismiss, hidden when empty or while loading); Doctor notes tab (doctor name, local day, body; empty state).
- Notification wording is neutral and never celebratory ("Week 28 has started", "Your doctor shared a note with you"); a unit test checks there are no exclamation marks.

Files changed:
- backend: `app/modules/journey/{schemas,service,router}.py`, `app/modules/dashboard/service.py` (new), `app/main.py`, `tests/integration/test_journey_notifications.py` (new)
- frontend: `components/journey/NotificationBar.tsx`, `pages/DoctorNotesPage.tsx`, `app/useNotifications.ts`, `app/notifications.test.ts` (new); `app/{App.tsx,journey.ts}`, `pages/HomePage.tsx`, `components/PatientShell.tsx`, `packages/shared/src/{types,index,api-types}.ts`, `e2e/{helpers.ts,notifications.spec.ts}`
- docs: API.md, PROGRESS, CONTEXT, HISTORY, ERROR_LOG

Interpretations (spec silent, flagged for review): new_week/new_month are for the week/month she is in when she opens the app (no back-fill; the first open after entering dates creates them); unread baby-stage notices are hidden after the pregnancy ends; appointment_soon for a date-only appointment counts while its day has not passed; the bar is on the home screen only (§4.2).

Checks run (exact commands and results):
- `bash scripts/check_all.sh` → exit 0: pytest (strict warnings) 211 passed; ruff, mypy pass; frontend typecheck, lint, format pass; Vitest 37 passed; Playwright 58 passed (phone-light + laptop-dark, axe)

Errors met: 2 (ERR-039, ERR-040)
Suggestions raised (not implemented): none
Docs updated: API, PROGRESS, CONTEXT, HISTORY, ERROR_LOG
Open questions for the owner: OpenStax licence (spec S2/D9) still open
Next step: task 8 (pregnancy-end flow + undo).

## Session 16 — 2026-11-17 — Phase 2 task 8: when a pregnancy ends, and undo
Who: Raheem + agent: Claude Code
Phase / task: Phase 2 — pregnancy-end flow + undo (Journey §11.1-11.6, §15 test 9; UX_FLOWS P11)
Goal: the patient can mark her pregnancy as ended (three choices), choose whether her doctor is informed, see a quiet home, and undo within 7 days.

Done:
- Backend: `end_pregnancy` (status, time and answer stored; status change in `pregnancy_date_history`; `pregnancy_ended` inbox item only on "yes", same transaction) and `undo_pregnancy_end` (window from config, logged, inbox item kept). `dashboard.service.add_inbox_item` added (ARCHITECTURE §8). Home data gains `ended`. No migration needed (columns from Phase 1/2).
- Patient app: More → entry (only while active) → choice → "Would you like your doctor to be informed?" (no default) → confirmation; ended home: notification bar, `msg_loss_support` or `msg_birth_congratulations`, `msg_after_pregnancy_danger_signs`, My records links, "I marked this by mistake" with a confirm step while `undo_until` is set. No images and no animation on the ended home.
- No new wording for medical or emotional content: every §11 message is a §13.2 key (pending approval, DEC-041); the step labels are plain UI ("Choose one", "Please confirm", "Inform my doctor: Yes/No").

Files changed:
- backend: `app/modules/journey/{schemas,service,router}.py`, `app/modules/dashboard/service.py`, `app/main.py`, `tests/integration/test_journey_pregnancy_end.py` (new)
- frontend: `pages/PregnancyEndPage.tsx`, `components/journey/EndedHome.tsx` (new); `pages/{HomePage,SimplePages}.tsx`, `app/App.tsx`, `packages/shared/src/{types,index,api-types}.ts`, `e2e/pregnancy-end.spec.ts` (new)
- docs: API.md, PROGRESS, CONTEXT, HISTORY

Open items (TODO(OPEN), unchanged): gentle wording of the entry (§11.1 — the spec's working label "My pregnancy has ended" is used); support helpline number (§13.3); all §11 message texts await doctor approval.
Interpretations (spec silent, flagged for review): the undo does not notify the doctor and does not remove an inbox item already sent; the quiet home's "My records" is a short list of links (appointments, doctor notes) until the records pages exist; the "My pregnancy has ended" entry is hidden once the pregnancy has ended.

Checks run (exact commands and results):
- `bash scripts/check_all.sh` → exit 0: pytest (strict warnings) 224 passed; ruff, mypy pass; frontend typecheck, lint, format pass; Vitest 37 passed; Playwright 64 passed (phone-light + laptop-dark, axe)

Errors met: 0 (one mypy "unused type: ignore" fixed in the same step; not a defect)
Suggestions raised (not implemented): none
Docs updated: API, PROGRESS, CONTEXT, HISTORY
Open questions for the owner: OpenStax licence (spec S2/D9); the interpretations above
Next step: task 0 (doctor/admin consent once at first sign-in, standard 405 code, sign-in audit), then task 9 (phase review, CHANGELOG 0.2.0).

## Session 17 — 2026-11-17 — Phase 2 task 0: Phase 1 follow-ups
Who: Raheem + agent: Claude Code
Phase / task: Phase 2 — task 0 (owner decisions from the Phase 1 review)
Goal: close the three Phase 1 TODO(OPEN) items the owner decided.

Done:
- Doctor/admin consent (DEC-046): the doctor app's gate has a `consent` step; `ConsentStep` shows the consent text word for word with both boxes unticked and posts to the existing `POST /me/consent` (it already accepted every role). Gate unit test and a signed-in doctor E2E test added.
- 405 (DEC-047): `METHOD_NOT_ALLOWED` in the status→code map and API.md §3; TODO(OPEN) removed; integration test.
- Sign-in audit (DEC-048): `CurrentUser` carries the token's `session_id`; `GET /me` calls `record_sign_in`, which writes one "signed in" row per session (patient_id for patients, details `{role}`, never clinical values). Tests: same session twice → one row; a new session → a second row; no session_id → none.

Files changed:
- backend: `app/core/{auth,errors}.py`, `app/modules/users/{service,router}.py`, `tests/integration/{test_me,test_app_basics}.py`
- frontend: `apps/doctor-web/src/components/{ConsentStep,AccountGate}.tsx`, `apps/doctor-web/src/app/{gate,gate.test}.ts`, `e2e/doctor.spec.ts`
- docs: API.md, DECISIONS (DEC-046 to DEC-048), PROGRESS, CONTEXT, HISTORY, ERROR_LOG

Checks run (exact commands and results):
- `bash scripts/check_all.sh` → exit 0: pytest (strict warnings) 227 passed; ruff, mypy pass; frontend typecheck, lint, format pass; Vitest 38 passed; Playwright 66 passed (phone-light + laptop-dark, axe)

Errors met: 1 (ERR-041)
Suggestions raised (not implemented): write audit_log rows for the patient-side changes Dashboard spec §20 lists (appointment created/edited/deleted, dates changed, pregnancy status changed) — asked as a decision in the task report
Docs updated: API, DECISIONS, PROGRESS, CONTEXT, HISTORY, ERROR_LOG
Open questions for the owner: OpenStax licence (spec S2/D9); patient-side audit entries (above); branch merge to main before the phase review
Next step: task 9 (E2E + accessibility review, §15 manual checks, CHANGELOG 0.2.0).

## Session 18 — 2026-11-17 — Phase 2 task 9: phase review (agent part) and patient audit entries
Who: Raheem + agent: Claude Code
Phase / task: Phase 2 — E2E + accessibility review, §15 check, CHANGELOG 0.2.0 (owner: add the audit entries now, merge after review)
Goal: finish everything the agent can do for Phase 2 and list what is left for the owner.

Done:
- Audit entries (DEC-049): `users.service.add_audit`; dates changed, appointment created/edited/deleted, pregnancy status changed (end and undo), each in the change's own transaction, `details` empty. Integration tests: all six actions logged with the patient id; refused or unchanged actions log nothing.
- Review: stale "until task N" comments fixed; scan of code, content and rules for "your baby weighs" / "your baby is", heartbeat, Lottie, confetti → none; §15 map: tests 1-4, 7, 9, 10 automated; 5-6 wait for the Phase 7 knowledge base; 8 for Phase 3; 11 needs the owner's manual check (automated scan clean).
- Bug found and fixed: date overflow on appointment dates / calendar range (ERR-042).
- CREDITS.md completed (ERR-043). CHANGELOG 0.2.0; version 0.2.0 in backend and frontend packages (lockfile workspace entries only); the /health test expects 0.2.0.

Files changed:
- backend: `app/modules/users/service.py`, `app/modules/journey/{service,router,schemas}.py`, `tests/integration/{test_journey_audit.py (new),test_journey_calendar.py,test_journey_notifications.py,test_app_basics.py}`, `app/__init__.py`, `pyproject.toml`
- frontend: package.json files, `package-lock.json` (workspace versions), `JourneyBlocks.tsx`, `MonthDetailPage.tsx` (comments)
- docs: CHANGELOG, legal/CREDITS, API, DECISIONS (DEC-049), PROGRESS, CONTEXT, HISTORY, ERROR_LOG

Checks run (exact commands and results):
- `bash scripts/check_all.sh` → exit 0: pytest (strict warnings) 231 passed; ruff, mypy pass; frontend typecheck, lint, format pass; Vitest 38 passed; Playwright 66 passed (phone-light + laptop-dark, axe)

Errors met: 2 (ERR-042, ERR-043)
Suggestions raised (not implemented): a tighter product rule for appointment dates (for example within the pregnancy and a year after) instead of the technical 1900-2999 range — owner decision
Docs updated: CHANGELOG, CREDITS, API, DECISIONS, PROGRESS, CONTEXT, HISTORY, ERROR_LOG
Open questions for the owner: see the "left for the owner" list in the task 9 report (doctor approvals, [OPEN] items, OpenStax, interpretations, merge)
Next step: owner review of Phase 2 → merge the phase-2 branches into main → Phase 3.

## Session 19 — 2026-11-18 — Phase 2 follow-ups: size weeks 14-40, drawing search
Who: Raheem + agent: Claude Code (owner approved both)
Phase / task: Phase 2 — before the owner's review
Done:
- `size_reference.yaml`: every week 14-40 from WHO Table 11 (50th percentile), read again from the downloaded table image; the 7 earlier values match. Draft objects for the new weeks (orange, apple, capsicum, corn cob, brinjal, bunch of grapes, broccoli; neighbouring weeks share coconut, pineapple, melon, watermelon); 7 more Fluent Emoji SVGs (MIT), checked for scripts/links before use; unit test now checks all 27 values and that every icon file exists.
- Month drawing search: womenshealth.gov has a 9-image stage series, but every image is marked "©peggerrity.com" (third-party copyright) → not allowed; scratch copies deleted, nothing added to the repo. Servier Medical Art (CC BY 4.0) has single images only. Wellcome Collection has public-domain engravings (1818, c.1850) in two different styles. Placeholders stay until the owner decides.
Checks: `bash scripts/check_all.sh` → exit 0: pytest 231 passed; Vitest 38 passed; Playwright 66 passed; ruff, mypy, typecheck, lint, format pass.
Docs updated: CREDITS, CHANGELOG, CONTEXT, HISTORY
Next step: owner review and decisions → merge to main.

## Session 20 — 2026-11-18 — Owner decisions after the Phase 2 report
Who: Raheem + agent: Claude Code
Decisions (owner): 1a keep the placeholder drawings (DEC-050); remove OpenStax (DEC-051); keep the 1900-2999 date limits (DEC-052); interpretations from tasks 6-8 accepted (DEC-053). DEC-042 marked "OpenStax part superseded".
Docs changed: Journey spec (D9, §7.2 weeks before 14, §8.3 sources, the OpenStax conversion note removed, S2 row marked removed with its ID kept), RAG spec licence example, DECISIONS, CONTEXT, `backend/content/prototype_content.yaml` comment.
Checks: `pytest tests/unit/test_journey_content.py` → 12 passed (only a YAML comment changed in code).
Next step: owner reads the explanation of items 6-14, then the merge decision (item 5).

## Session 21 — 2026-11-18 — Owner items 6, 7, 8, 10, 12, 13, review sheet, merge
Who: Raheem + agent: Claude Code
Goal: carry out the owner's answers to the Phase 2 open items; make the doctor review sheet; merge.
Done:
- Merged `phase-2/review` into `main` (fast-forward to 1e3d2bb) after the owner's review; follow-ups on `phase-2/owner-items`.
- 6: "My pregnancy has ended" approved (DEC-054); TODO(OPEN) removed.
- 7: official Telangana State Portal emergency contacts page (checked by download, word for word): "Ambulance | 102,108", "Women Helpline | 181" → `messages.yaml` `helplines` (validated at startup: digits only, https source, date) → home data → tap-to-call list with the source on the §11.4 support screen (not on the birth screen). No official Telangana counselling/mental-health line was found.
- 8: MCP card PDF (S4) downloaded and read: no week-by-week ANC timing ("Have at least 3 antenatal checkups, after registration"). The official NHM Maternal Health page (checked by download) states PMSMA's fixed day; `config.yaml` now holds the schedule with URL, quote and date, and the backend refuses to start with check-ups on but no schedule. Engine `suggested_checkup_days` (9th of each month from week 14 to due + 2 weeks); calendar shows a dashed "suggested" label, an icon, screen-reader words and the source link. The shipped-config test now expects the feature on with its NHM source (the spec default was off only until a schedule existed).
- 10: `scripts/make_admin.py` (refuses another role; idempotent) + ENVIRONMENT.md steps; Dashboard spec §21 [OPEN] closed (DEC-055).
- 12/13: recorded as owner acceptance for the prototype; doctor sign-off stays a release requirement (DEC-058).
- Review sheet: `scripts/export_review_sheet.py` → `docs/review/journey_doctor_review.csv` (72 rows: 11 messages, 21 content items, 27 size objects, 9 month ranges, the check-up schedule, the safety message, 2 helplines; empty verdict/comment columns).
Files changed: backend config/engine/schemas/service/main, rules (config.yaml, messages.yaml), scripts (make_admin, export_review_sheet), tests (engine, calendar, home blocks, make_admin, review sheet); frontend calendar markers/page, week strip, ended home, end page, e2e; docs (Journey + Dashboard specs, API, ENVIRONMENT, DECISIONS DEC-054..058, CHANGELOG, CONTEXT, HISTORY, review CSV).
Errors met: 2 small ones in my own edit scripts (an anchor that did not match — nothing written; an escaped "\n" that became a line break in a test file — fixed before any run). No ERR entry: caught by the scripts' checks and the linter before tests ran.
Checks: `bash scripts/check_all.sh` → exit 0: pytest 238 passed; Vitest 38 passed; Playwright 66 passed; ruff, mypy, typecheck, lint, format pass.
Open: item 9 (legal placeholders) later; doctor review using the sheet.
Next step: owner sends the sheet to a doctor; Phase 3 planning.

## Session 22 — 2026-11-18 — Phase 3 task 1: symptom tables and rule files
Who: Raheem + agent: Claude Code
Phase / task: Phase 3 — migration; vocabulary YAML; red-flag YAML; PUQE; pattern rules (Symptom spec §5, §7-9, §11, §13)
Decisions: owner approved the Phase 3 plan decisions A-H as recommended (DEC-059 to DEC-066).
Done:
- Official sources fetched and checked by download: PUQE-24 sheet (S5) — exact question/answer text read from the PDF's tags (agent summary not trusted alone); PIB (MoHFW) release, 29 May 2024, for Tele MANAS 14416 / 1-800-891-4416. The MCP card's ANC timing was already checked in Session 21.
- Migration 0003: `symptom_checkins`, `symptom_logs` (append-only, CHECKs, indexes); tested on alovia-test (upgrade/downgrade/upgrade, model match, constraint test), then applied to main (`alembic current` = 0003).
- Rule files `backend/rules/symptoms/`: config (§13.2 defaults), symptoms (§5 labels word for word), red_flags (25 rules, spec condition text kept beside each machine-readable condition), puqe (official wording; spec bands), patterns (P1-P5), messages (7 keys, text pending) + helplines (emergency = Telangana Ambulance, mental health = Tele MANAS).
- Loader `app/modules/symptoms/rules.py`: strict models and cross-checks (symptoms, flags, severities, durations, settings, unless-rules, PUQE bands 3-15, P1-P5, exact message keys, both helplines); loaded at startup; /health `symptoms: true`.
- `Message`/`Helpline` moved to `app/common/rule_texts.py` (journey re-uses them; ARCHITECTURE §8).
- Spec correction noted: the plan said 33 rules; the spec has 25 (14 L1 + 11 L2).
Files changed: backend models, migration 0003, rules/symptoms/*, app/common/rule_texts.py, journey config/service imports, main.py, health.py, tests (rule files, migrations, app basics); docs DATABASE, DECISIONS, PROGRESS, CONTEXT, HISTORY, ERROR_LOG.
Checks: `bash scripts/check_all.sh` → exit 0: pytest 254 passed; Vitest 38 passed; Playwright 66 passed; ruff, mypy, typecheck, lint, format pass.
Errors met: 1 (ERR-044)
Open for the rule review: A2 now includes the sheet's "4 - 6" mild band vs the spec's 3-6.
Next step: task 2 (engine: validation, rules, PUQE, patterns, V3 fallback, the 10 §14 tests).

## Session 23 — 2026-11-18 — Phase 3 tasks 2-3: symptom engine, API, inbox items
Who: Raheem + agent: Claude Code
Phase / task: Phase 3 — engine + one test per rule; API; inbox items (Symptom spec §5-10, §14)
Done:
- Engine (pure): V1/V2 validation against the rule files (field named, e.g. entries.0.severity); warning signs offered by week (unknown week offers all, §1.3/DEC-065); the 25 rules read as data with a small fixed set of condition kinds; plain rules, then "unless" rules (L2-07), then the catch-all (L2-11) per entry; highest level wins, all matches kept in spec order; message keys (level, mood support, notes notice); PUQE score/band; P1-P5 (P1 first ever; P2 needs an earlier entry in the window; P3 distinct local days incl. today; P4 vs the previous PUQE band; P5 a plain count of L2 check-ins in the window incl. this one); V3 fallback constant.
- Tests: 66 engine tests — every rule, L1-03 vs L2-07, L1-04 vs L2-02, highest-level-wins, unknown week, boundaries 15/16, 23/24, 36/37, catch-all (back pain, other), PUQE 3/6/7/12/13/15, notes ignored, 20 V1/V2 cases, P1-P5 pass/fail with defaults and a changed setting, and a guard that every rule ID in red_flags.yaml is named in the test file.
- API: vocabulary, POST/GET checkins, charts; one transaction for check-in + entries + inbox items; V3 on any engine exception (logged); 409 after the end; pregnancy week from the journey service. 13 integration tests (§14 tests 8 and 10, inbox items incl. P5, details/notes/charts, consent).
- Interpretations (flagged): pattern changes stored as [{code, symptom}] so §12 can name the symptom (spec §10 shows bare codes); P2 does not fire without an earlier entry in the window; duplicate symptoms in one check-in are refused (except `other`); the urgent button accepts warning signs only.
Conflict found (owner question): Symptom spec §10 and API.md §5 show a severe headache with vision problems matching ["L1-03", "L2-07"], but rule L2-07 excludes an L1-03/L1-04 match and §14 test 1 tests "L1-03 vs L2-07". The rule table was followed (§0 rule 4); the examples need correcting.
Checks: `bash scripts/check_all.sh` → exit 0: pytest 333 passed; Vitest 38 passed; Playwright 66 passed; ruff, mypy, typecheck, lint, format pass.
Errors met: 0 (two line-length lint fixes during writing)
Next step: task 4 (patient screens: log page, result screens, urgent button with bundled advice).

## Session 24 — 2026-11-18 — Phase 3 task 4: log page, urgent button, advice screens
Who: Raheem + agent: Claude Code
Phase / task: Phase 3 — patient screens (Symptom spec §4.1-4.2, §11; UX_FLOWS P5-P6; ERROR_HANDLING bundled advice)
Done:
- Bundle: `backend/scripts/export_symptom_bundle.py` writes the warning signs, the 7 messages and the 2 official helplines to `apps/patient-web/src/app/symptomBundle.generated.ts` (excluded from prettier/eslint); `tests/unit/test_symptom_bundle.py` fails when it is stale.
- Log page: warning signs first, everyday symptoms below with only the details each asks for (severity, duration, body area, flags, PUQE questions with their source, text, choice, optional time and notes); client checks for missing details, backend V1/V2 shown at the field; the not-monitored notice.
- Advice screens: spec level names as headings (DEC-061); L1 large, high contrast, emergency number (tap to call, source shown), "I understand"; L2/L0 calmer; mood support with Tele MANAS; notes notice; role alert/status; no animation.
- Urgent page: "I have an urgent symptom", warning signs only, list from the bundle until the week-filtered list loads; backend unreachable → L1 advice + in-memory queue retried every 30 s and on `online` (DEC-060); after the end → after-pregnancy notice (DEC-064, also on the log page).
- Fix ERR-045 (entry order in history).
- Tests: 5 unit (helpers), 12 E2E (phone-light + laptop-dark, axe): L0 flow with field errors, L1 screen with emergency number, PUQE + mood helpline, urgent flow, urgent with the backend down, after-end notice.
Checks: `bash scripts/check_all.sh` → exit 0: pytest 334 passed; Vitest 43 passed; Playwright 78 passed; ruff, mypy, typecheck, lint, format pass.
Errors met: 1 (ERR-045) plus one test locator ("14416" also matched the 1800 number — exact match).
Next step: task 5 (history charts, Recharts install per DEC-059) and task 6 (Journey links).

## Session 25 — 2026-11-19 — Phase 3 task 5: symptom history charts
Who: Raheem + agent: Claude Code
Phase / task: Phase 3 — history charts (Symptom spec §4.3)
Done:
- Installed recharts 3.10.1 (DEC-059; 3.11.0 was one day old) and react-is 19.3.1 with a root npm override, so Recharts and the test formatter use the react-is that matches React 19 (npm kept a hoisted 17 otherwise). `npm audit`: 4 moderate, all in vite-plugin-pwa's build tooling (glob/minimatch via workbox-build), present before this change — noted for Phase 8.
- `/log/history`: per symptom a stacked bar chart of entries per pregnancy week by severity (mild/moderate/severe/"logged" for entries without one), legend only when there are two or more series, hover tooltips, "Show as a table" with week, count, severities and durations; PUQE score line chart (3-15) with a table. Unknown week grouped last. Links from the log page and the ended home's "My records".
- Colors: severity is ordered, so one hue light -> dark; validated with the dataviz palette validator for the light (#fff) and dark (#221d2e) surfaces — all checks pass. Rendered and looked at in both themes; fixed legend text colour (now text ink) and long PUQE date ticks (now "3 Nov", padded) after the first look.
- Tests: `byWeek` unit test; 4 E2E (history with table and PUQE line, empty state; phone-light + laptop-dark, axe).
Checks: first `bash scripts/check_all.sh` run → exit 1 after 8 h: 4 Phase 2 database tests failed with "failed to resolve host" (network lost while the machine slept; ERR-046); re-run → exit 0: pytest 334 passed; Vitest 44 passed; Playwright 82 passed; ruff, mypy, typecheck, lint, format pass.
Errors met: 0 (two visual issues found by looking, fixed before commit)
Next step: task 6 (Journey links: logged today, weekly summary, calendar dots and red-flag icons).

## Session 26 — 2026-11-19 — Phase 3 task 6: symptoms in the Journey
Who: Raheem + agent: Claude Code
Phase / task: Phase 3 — quick log "logged today", weekly summary, calendar dots and red-flag icons (Journey §4.3, §9.2, §9.4, §15 test 8)
Done:
- Backend: `symptoms.service` gains `symptom_days`, `logged_on`, `week_summary` (read by the journey router, ARCHITECTURE §8; no import cycle). Journey router: one `_home` builder for /home, PUT /dates and the pregnancy-end routes, adding `logged_today` and `weekly_summary` (with the `common_symptoms` content for the content week via `select_for_home`); the calendar adds `symptom_days`. 4 integration tests (strict warnings).
- Patient app: quick log shows "Logged today"; "This week's summary" with "You logged" (days, top symptoms, red-flag days, link to history) and the "Common at this stage" Learn card, apart and never compared; calendar and week strip: a dot for any check-in and a distinct red-flag icon (urgent colour) on L1/L2 days, screen-reader words, legend, and the day's check-ins with their level names in the day details.
- Tests: E2E for the home summary (no "normal"/comparison wording) and the calendar markers (distinct icon and colour), phone-light + laptop-dark, axe.
Checks: `bash scripts/check_all.sh` → exit 0: pytest 338 passed; Vitest 44 passed; Playwright 86 passed; ruff, mypy, typecheck, lint, format pass. Also (owner): the §10 / API.md §5 examples corrected to ["L1-03"] (DEC-067).
Errors met: 0 (a missing import and a shell-escaped apostrophe in a test title, both caught by typecheck/prettier before running)
Next step: task 7 (rule sign-off sheet, review, CHANGELOG 0.3.0).

## Session 27 — 2026-11-19 — Phase 3 task 7: review (agent part), sign-off sheet, 0.3.0
Who: Raheem + agent: Claude Code
Phase / task: Phase 3 — E2E; review; CHANGELOG 0.3.0
Done:
- Symptom spec §14 map: tests 1-7 and 9 (engine unit tests, incl. the rule-coverage guard), test 8 and 10 (API integration), Journey §15 test 8 (calendar E2E). All automated.
- Review fixes: the advice screen showed the L1 text under an L2 heading for a V3 fallback (only `msg_safe_fallback` returned) — fixed with the tested `adviceParts` helper; stale "Phase 3" TODOs updated; `shortcut:` note on the pattern-history query. Sweeps: no "normal / harmless / nothing to worry" wording, no kick counter, no phone number outside the rule files.
- Rule review (§16): `scripts/export_symptom_rule_review.py` → `docs/modules/reviews/symptom_rule_review.csv` (25 rules, PUQE questions + bands with the A2 note, P1-P5 with numbers, week settings, 7 messages, 2 phone numbers, A1-A4; columns per §16) + `symptom_rule_review_signoff.md`; unit test for completeness.
- CREDITS: PUQE-24 wording source. CHANGELOG 0.3.0; version 0.3.0 (backend, 5 package.json, 6 lockfile lines, /health test).
Checks: `bash scripts/check_all.sh` → exit 0: pytest 339 passed; Vitest 46 passed; Playwright 86 passed; ruff, mypy, typecheck, lint, format pass.
Owner decisions this phase: plan A-H (DEC-059..066), examples corrected (DEC-067).
Open for the owner / doctor: doctor rule review and sign-off (A1-A4, PUQE band 3 vs 4), the 7 symptom messages, the Journey review sheet; merge after the owner's review.
Next step: owner review → merge `phase-3/rules-data` into main → Phase 4 (Genetic Risk) planning.

## Session 28 — 2026-11-19 — Phase 4 task 1: genetic rule files
Who: Raheem + agent: Claude Code
Phase / task: Phase 4 — YAML rules (Genetic spec §5-7, §11.4, §12)
Decisions: plan decisions A-H as recommended (DEC-068..075). Merged Phase 3 into main first (992579b).
Done:
- `backend/rules/genetic/`: config (rules_version 1.0.0, show_result_before_review true), haemoglobin_group (9 codes with the spec's meanings, 17 rows listing their exact pairs, A2/A4 tags), haemophilia (mother/father statuses, father_api_only for C2, 7 rows with if-boy and if-girl), marfan (4 rows), evidence (6 kinds, §6.2 handling incl. A1), conflicts (C1, C2, F1, F2 as data, E3/E4), messages (25 §11.4 keys; disclaimer_main from §11.2), labels (the spec's questions §5.5-5.7, outcome and chance words).
- Loader `app/modules/genetic/rules.py`: strict models; coverage checks (45 haemoglobin pairs exactly once; each of the 8 haemophilia form combinations matched by exactly one row; each of the 6 Marfan pairs once); outcomes only on calculated rows and both boy+girl lists together; every message/outcome/evidence reference exists; loaded at startup; /health genetic: true.
- Found: YAML reads a bare `yes` as true — the conflicts file quotes "yes".
- Tests: 15 rule-file tests (every row vs the spec tables, evidence, conflicts, settings, messages; 10 broken-file cases).
Checks: ruff, mypy; rule-file + app-basics tests 24 passed.
Next step: task 2 (engine + the 45 pair tests and all other §14 tests).

## Session 29 — 2026-11-19 — Phase 4 task 2: genetic engine
Who: Raheem + agent: Claude Code
Phase / task: Phase 4 — engine + 45 pair tests + all other tests (Genetic spec §5-9, §14)
Done:
- `app/modules/genetic/engine.py` (pure): validation E1/E2 with the field named (father haemophilia carrier/unknown accepted only for C2, DEC-068; no default father haemophilia answer, DEC-069; evidence only "allowed with" its condition/status; no evidence with unknown; nothing asked after entry "no"); §6.2 evidence handling; conflicts from conflicts.yaml; rule lookup (E3 when no row and no conflict); §6.4 priority; per-condition E4 (never a number); §9.3 nudges; §9.4 risk exactly; consanguinity message (numbers unchanged); timing prompt + priority high; show_result_before_review -> review_with_doctor / results_after_review.
- Output additions (flagged): a top-level `message_keys` for whole-assessment messages (consanguinity, timing, review) — §8.2 has no place for them; `rule_id` names what decided the status (a rule row, or C1/C2/F1/F2/E3/E4).
- Tests (112): the 45 pairs both ways against an independently typed spec table; every haemophilia row (boy+girl together) and Marfan row; every evidence rule; C1, C2 (carrier and unknown), F1, F2, E3, E4; priority; not assessed; consanguinity; risk/timing/priority in 14 cases; show-before-review both ways; no percent 0 and no sex field across all outputs; nudges; 11 validation cases; a guard that every rule/conflict/error ID is named in the test file.
- One test expectation was mine and wrong (family-history-only mother + tested-negative father is HBB-09, not "needs testing"); fixed to the spec row.
Checks: ruff, mypy; 112 engine tests passed.
Next step: task 3 (migration 0004, API, inbox items).

## Session 30 — 2026-11-19 — Phase 4 task 3 (backend): migration 0004, API, inbox, Journey card
Who: Raheem + agent: Claude Code
Done:
- Migration 0004 `genetic_assessments` (append-only; CHECKs; indexes) tested on alovia-test (up/down/up, model match, constraint test), then applied to main (`alembic current` = 0004).
- Service + routes: POST (validate E1/E2 -> 400 with the field; engine; save pending_review; inbox `genetic_pending` + `genetic_high_priority` when high, DEC-071, one transaction; E4 logged), GET list (newest first), GET one (404 for another patient's). Patient view hides numbers while `show_numbers_to_patient` is false (setting off and not reviewed) and shows them with the doctor's note after review (§10.4); no doctor-only priority. Engine now also refuses an `entry` for the haemoglobin group (E2).
- Journey home `genetic_check` for the §10.4 status card (DEC-073), read through `genetic.service`.
- Tests: 10 API integration tests (submit + inbox, normal priority, E1/E2 save nothing, unknown fields and a baby-sex field refused, history/one/404, numbers hidden then shown after a simulated review, the Journey card in all 4 states, consent).
Checks: `bash scripts/check_all.sh` → exit 0: pytest 478 passed; Vitest 46 passed; Playwright 86 passed; ruff, mypy, typecheck, lint, format pass.
Next step: task 3 frontend (form, result screen, history, More link, home card).

## Session 31 — 2026-11-19 — Phase 4 task 3 (frontend): genetic form and results
Who: Raheem + agent: Claude Code
Done:
- Bundle `apps/patient-web/src/app/geneticBundle.generated.ts` from `backend/scripts/export_genetic_bundle.py` (labels, questions, statuses per condition/parent without the API-only values, evidence "allowed with", messages); sync test; excluded from prettier/eslint.
- Helpers `app/genetic.ts` (evidence by status, D14/DEC-069 defaults, missing answers as API paths, request with nothing after entry "no", card labels DEC-073, chance labels) + 6 unit tests.
- `/genetic`: consent reminder (DEC-072) with the consent link; haemoglobin section always, haemophilia/Marfan behind entry questions; status and "How do you know?" selects (evidence filtered by §5.4); previous child; consanguinity; client and server (E1/E2) field errors. Result: disclaimer (spec text), whole-assessment messages, per condition outcomes "Label: 1 in 4 (25%)" / "not expected", haemophilia "If the baby is a boy" and "If the baby is a girl" together, next-step messages, warnings and notes (pending texts), numbers hidden when not shown, doctor's note in a distinct card; earlier checks. More → "Genetic risk"; home "Genetic check: …" card after the next appointment.
- Bug found by E2E and fixed: after submitting, the page waited for the history list to include the new assessment and showed the form again meanwhile; it now shows the returned result at once.
- Tests: 8 E2E (form + exact request, boy/girl + no 0% in visible text, hidden numbers + doctor note, home card; phone-light + laptop-dark, axe).
Checks: `bash scripts/check_all.sh` → exit 0: pytest 479 passed; Vitest 52 passed; Playwright 94 passed; ruff, mypy, typecheck, lint, format pass.
Next step: task 4 (review: rule-review sheet, CHANGELOG 0.4.0).

## Session 32 — 2026-11-19 — Phase 4 task 4: review (agent part), rule-review sheet, 0.4.0
Who: Raheem + agent: Claude Code
Done:
- Genetic spec §14 map: tests 1-9 automated (engine unit tests incl. the 45 pairs and the rule-coverage guard; API integration; E2E for boy+girl together and no 0%); test 10 (doctor correction) is Phase 5 (DEC-074).
- Rule review (§13): `scripts/export_genetic_rule_review.py` → `docs/modules/reviews/genetic_rule_review.csv` (66 rows: 17 haemoglobin rows with their pairs, 7 haemophilia rows with boy/girl outcomes, 4 Marfan rows, 3 evidence rules, C1/C2/F1/F2/E3/E4, 25 messages, A1-A4) + `genetic_rule_review_signoff.md`; completeness test.
- Sweeps: no "will / safe / no risk / 0%" in patient-facing genetic text (only code comments saying "never 0%"); the stale "TODO(Phase 4)" on Doctor notes moved to Phase 5 (the genetic doctor note is written in the doctor review).
- CHANGELOG 0.4.0; version 0.4.0 (backend, 5 package.json, 6 lockfile lines, /health test).
Checks: `bash scripts/check_all.sh` → exit 0: pytest 480 passed; Vitest 52 passed; Playwright 94 passed; ruff, mypy, typecheck, lint, format pass.
Open for the owner / doctor: rule review and sign-off (A1-A4) and the 24 pending genetic messages; merge after the owner's review.
Next step: owner review → merge `phase-4/genetic` into main → Phase 5 (Doctor Dashboard + Admin) planning.

## Session 33 — 2026-11-19 — Phase 4 merged; Phase 5 plan; task 1 foundation
Who: Raheem + agent: Claude Code
Done:
- `phase-4/genetic` fast-forward merged into main and pushed. Phase 5 plan posted; owner approved decisions A-K as recommended (DEC-076..086); branch `phase-5/dashboard`.
- Migration 0005: `entered_values`, `range_warnings` on both result tables; `result_shares` (unique per result), `medical_records`, `rule_signoffs`; tested on alovia-test (up/down/up, model match, constraints), then applied to main with the owner's approval (`alembic current` = 0005).
- Access checks in `users.service`: `get_doctor`, `get_admin`, `assigned_patient`, `get_assigned_patient` (the Phase 2 carry-over: consent checked in the backend for doctor/admin routes).
- `rules/dashboard/config.yaml` (all §23 settings) + `messages.yaml` (12 keys, text null) with a strict startup loader; template classes cross-checked with the models' label files.
- Tests: 3 access tests (test-only router on the real dependencies), 7 dashboard rule-file tests, migration test extended.
Checks (backend): `ruff format .` clean; `ruff check .` pass; `mypy app tests scripts` no issues (91 files); `pytest -q -W error` 491 passed.
Next step: training ranges from the owner's notebooks (decision A), then task 2 (home, patient list, inbox, patient pages).

## Session 34 — 2026-11-19 — Training ranges; Phase 5 task 2 (home, patients, inbox, invites)
Who: Raheem + agent: Claude Code
Done:
- Owner: approved migration 0005 on main (applied, `alembic current` = 0005); added both training notebooks and raw data at the repo root → moved to `backend/ml_training/` (notebooks, committed) and `backend/ml_training/data/` (data, git-ignored), as asked.
- One cell added to each notebook to save the cleaned CSV. Both notebooks executed top to bottom in a scratch virtual environment with the backend's ML versions: retrained models byte-identical to `backend/ml_models/`; all printed results identical to the stored outputs.
- `scripts/compute_feature_ranges.py` → `fetal_risk_feature_ranges.json` (1,692 training rows) and `maternal_risk_feature_ranges.json` (4,846); the split is proven by reproducing the recorded test macro F1 (0.9164 / 0.9909). 6 inputs have a slightly narrower range in the training split than in the whole cleaned file (fetal DS.1, ASTV, MLTV, Median; maternal systolic BP, fasting glucose). Tests: range files cover every input in order; equal to a fresh computation when the data is present.
- Task 2 backend: `/doctor/patients` (list, §6 order), `/doctor/patients/{id}` (overview), POST/PUT patients, POST invite, GET inbox, POST seen; 9 integration tests (order with mixed items = §25 test 3; seen visible to the other doctor = test 4; other doctors' patients 404 = test 1 for these routes; invite replaces the old one; linked patient 409; validation).
- Task 2 doctor app: Home, Patients, New patient, patient page (Overview, invite link + Copy; other tabs placeholders for later tasks); 10 unit tests; 8 E2E (both viewports, axe).
Checks: see the task 2 review report.
Next step: owner review of task 2, then task 3 (predictions).
