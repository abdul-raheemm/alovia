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
