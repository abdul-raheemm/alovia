# ERROR LOG — errors met while building, and lessons

Every error the agent meets (failed command, failing test, bug found, wrong assumption, tool problem) gets an entry, even if fixed in a minute. Read the **Lessons** section at the start of every session.

## Lessons (keep short; one line each; newest first)
- Never chain a commit or push after file edits with `&&` alone: check that the edit step succeeded (git diff) before committing.
- Before the first commit of any repo, write `.gitignore` and read `git status`.

## Error rate tracker (update at the end of each phase)

| Phase | Errors logged | Caused by agent mistake | Caught by tests | Caught by owner review | Repeat of an earlier lesson |
|---|---|---|---|---|---|
| 1 | | | | | |

## Entry template

```
### ERR-<number> — <YYYY-MM-DD> — <short title>
Who: <person + agent>
Phase / task: <…>
What happened: <exact error message or symptom>
Cause: <root cause, not just the symptom>
Fix: <what was changed; files>
Verified by: <test/command and result>
Prevention: <what changes so it does not happen again — a test, a rule in CLAUDE.md, a lesson line>
Category: <setup / dependency / logic / spec misread / data / test / tooling / other>
```

---
### ERR-001 — 2026-11-16 — Old folders in the first commit
Who: Raheem + Claude Code
Phase / task: Phase 1 — .gitignore
What happened: the first commit, pushed to a public repo, held `ml-test/` (13 files) and `rag/` (404 files).
Cause: the repo was initialised and committed before a `.gitignore` existed.
Fix: `.gitignore` added; commit rewritten (Option B, 360ca84 → 4d29b90) and force-pushed.
Verified by: `git ls-files ml-test rag` → 0; `git rev-list --objects HEAD` → no old-folder paths.
Prevention: lesson line above.
Category: setup

### ERR-002 — 2026-11-16 — Docs assumed a Python version that is not installed
Who: Claude Code
Phase / task: Phase 1 — start-of-session checks
What happened: docs said backend 3.12 and "laptop has 3.14"; `py -0` showed only 3.15 and 3.13.
Cause: the docs were written without checking the machine.
Fix: owner chose Python 3.14 (DEC-030) and installed it.
Verified by: `py -0` → lists 3.14.10.
Prevention: run `py -0` and `node -v` before any task that needs a runtime.
Category: setup

### ERR-003 — 2026-11-16 — graphify not installed
Who: Claude Code
Phase / task: Phase 1 — start of session
What happened: `/graphify` could not run: no `graphify` command or Python module.
Cause: the skill file was present but the pip package was never installed.
Fix: owner approved; `py -3.13 -m pip install graphifyy` (0.9.111).
Verified by: `import graphify` succeeds; detect finds the docs and 0 old-folder files.
Prevention: none needed.
Category: tooling

### ERR-004 — 2026-11-16 — Said rag/archive had data folders; it has only scripts
Who: Claude Code
Phase / task: Phase 1 — start-of-session review of the old folders
What happened: the agent told the owner `rag/archive/` held data folders `international`, `medlineplus`, `nhs`; it holds only 8 `.py` scripts.
Cause: misread interleaved `ls` output — those folders belong to `clean/` and `raw/`.
Fix: corrected PROGRESS, CONTEXT, HISTORY and knowledge-base/README.
Verified by: `find rag/archive` → 8 `.py` files only.
Prevention: check a folder's contents with `find` before naming them.
Category: spec misread

### ERR-005 — 2026-11-17 — `sed -i` rewrote line endings of 3 copied scripts
Who: Claude Code
Phase / task: Phase 1 — copy the knowledge base
What happened: after a one-line `sed -i` edit, `diff` showed every line of `crawl_nhs.py`, `extract_nhs_all.py`, `flags_nhs.py` changed.
Cause: Git Bash `sed -i` writes LF line endings; the originals use CRLF.
Fix: fresh copies from `rag/`, then a byte-safe Python replace of the one line.
Verified by: `diff --strip-trailing-cr` → exactly 1 line per script; SHA-256 check of all other 401 files identical.
Prevention: edit copied files with a byte-safe method and check the diff.
Category: tooling

### ERR-006 — 2026-11-17 — Log tests could not read the app's log output
Who: Claude Code
Phase / task: Phase 1 — backend skeleton
What happened: `test_crash_returns_internal_error_without_details` and `test_request_log_line` failed (StopIteration, then "I/O operation on closed file").
Cause: the log handler keeps the `sys.stdout` object it was created with; pytest swaps `sys.stdout` between test phases, so `capsys` never saw the lines.
Fix: the two tests attach their own in-memory handler (same JSON formatter) via a `log_buffer` fixture; app code unchanged.
Verified by: `pytest` → 11 passed.
Prevention: test logging through an in-memory handler, not stdout capture. Note: three attempts were made; CLAUDE.md §5 says stop and report after two — follow it.
Category: test

### ERR-007 — 2026-11-17 — Request log showed "/health" instead of "/api/v1/health"
Who: Claude Code
Phase / task: Phase 1 — backend skeleton
What happened: `test_request_log_line` → `('GET', '/health', 200) != ('GET', '/api/v1/health', 200)`.
Cause: in FastAPI 0.163 a prefix passed to `include_router()` is not part of the matched route's path (only private telemetry code holds the full path).
Fix: routers declare `prefix=API_PREFIX` themselves (`app/api/__init__.py`); `include_router()` gets no prefix.
Verified by: test passes; live `uvicorn` log shows `"path": "/api/v1/health"`.
Prevention: every new router uses `APIRouter(prefix=API_PREFIX)`; the request-log test guards it.
Category: dependency

### ERR-008 — 2026-11-17 — Test route returned a plain dict instead of the envelope
Who: Claude Code
Phase / task: Phase 1 — auth part 1 (token check)
What happened: `test_valid_token_accepted` → `KeyError: 'data'` although the status was 200.
Cause: the test-only route returned `{"id", "email"}` directly instead of `ok(...)`, so there was no `data` key.
Fix: the test route returns `ok({...})` like real routes.
Verified by: `pytest` → 27 passed.
Prevention: every route, including test-only ones, returns through `app.common.responses.ok`.
Category: test

### ERR-009 — 2026-11-17 — Commit 09393fa pushed without its doc edits
Who: Claude Code
Phase / task: Phase 1 — recording auth part 1
What happened: `.venv_py=backend/.venv/Scripts/python.exe: No such file or directory`; the doc-edit step was skipped but the following lines (HISTORY append, commit, push) still ran, so 09393fa says DECISIONS/ENVIRONMENT/PROGRESS/CONTEXT/ERROR_LOG were updated when they were not.
Cause: an invalid shell variable name (`.venv_py`) at the start of an `&&` chain; the next commands were on new lines, so they ran regardless.
Fix: the doc edits applied in a follow-up commit and pushed.
Verified by: `git show --stat HEAD` lists the five docs; `grep DEC-031 docs/DECISIONS.md` finds the entry.
Prevention: lesson line above — verify `git diff --stat` shows every intended file before committing.
Category: tooling
