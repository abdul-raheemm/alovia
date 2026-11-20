# ERROR LOG — errors met while building, and lessons

Every error the agent meets (failed command, failing test, bug found, wrong assumption, tool problem) gets an entry, even if fixed in a minute. Read the **Lessons** section at the start of every session.

## Lessons (keep short; one line each; newest first)
- A Recharts chart wrapped in `aria-hidden` (data given as text instead) needs `accessibilityLayer={false}`, or axe reports focusable hidden content (ERR-051).
- Times that are compared must come from one clock: write and check expiry with the database's `now()`, never the app server's (ERR-048).
- In Git Bash, never pass a Python regex with backslashes (or a long YAML/text block) through an inline heredoc; write a script or the file with the file tool (ERR-044).
- Free date inputs need a range check at the API: a local date near year 1 or 9999 overflows when converted or shifted, and one stored bad row can break every later read (ERR-042).
- Add every new third-party asset or data source to `docs/legal/CREDITS.md` in the same task that ships it (ERR-043).
- `npm install -w <app> <pkg>` failing with "reading 'location'" (ERR-030, ERR-034): run a plain `npm install` first, then the workspace install.
- A date-only value stored as local midnight must be read in the patient's time zone, never sliced from a UTC timestamp (ERR-036).
- Write multi-file or quote-heavy edits as a script file in the scratchpad and run it; a long inline heredoc chain dies on one unmatched quote (nothing runs) and is unreadable in the transcript.
- Never pipe a check into `tail`/`grep` inside an `&&` chain before a commit; run the check alone and read its exit code.
- On Windows, start frontend tools through the npm scripts (`scripts/run.mjs`), not a shell and not a lowercase `c:\` path.
- Dispose every SQLAlchemy engine you create (tests, scripts, `migrations/env.py`); run tests with `-W error::ResourceWarning`.
- Never chain a commit or push after file edits with `&&` alone: check that the edit step succeeded (git diff) before committing.
- Before the first commit of any repo, write `.gitignore` and read `git status`.

## Error rate tracker (update at the end of each phase)

| Phase | Errors logged | Caused by agent mistake | Caught by tests | Caught by owner review | Repeat of an earlier lesson |
|---|---|---|---|---|---|
| 1 | 27 (ERR-001 … ERR-027) | 24 | 13 | 1 (ERR-001, before the agent started) | 1 (ERR-027 repeats the unchecked-chain pattern of ERR-009) |

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

### ERR-010 — 2026-11-17 — Doubled CHECK constraint names in the migration
Who: Claude Code
Phase / task: Phase 1 — Alembic + Phase 1 migration
What happened: `alembic upgrade head --sql` showed `ck_users_ck_users_role` and similar.
Cause: the metadata naming convention (`ck_%(table_name)s_%(constraint_name)s`) was applied to names already written in full.
Fix: mark full names as final with `op.f(...)`.
Verified by: offline SQL vs models → 17/17 statements identical.
Prevention: compare `--sql` output with the models before running any migration.
Category: logic

### ERR-011 — 2026-11-17 — My SQL comparison script skipped the users table
Who: Claude Code
Phase / task: Phase 1 — Alembic + Phase 1 migration
What happened: the first comparison reported "only in models: CREATE TABLE users".
Cause: the script dropped any statement starting with a `--` comment line; Alembic prints one before the first table.
Fix: strip comment lines before splitting statements.
Verified by: rerun → 17 statements in the migration, 17 in the models.
Prevention: treat check scripts as code: sanity-check their counts.
Category: tooling

### ERR-012 — 2026-11-17 — Tests slowed from 1 s to 23 s
Who: Claude Code
Phase / task: Phase 1 — Alembic + Phase 1 migration
What happened: `pytest` → 27 passed in 23.41 s after `/health` gained the db check.
Cause: every `/health` test tried to connect to the unreachable test URL; refused connections are slow on Windows.
Fix: tests use an in-memory database (`working_engine`) or an engine that fails at once (`down_engine`) from `tests/helpers.py`.
Verified by: `pytest` → about 2 s.
Prevention: tests never depend on network timeouts.
Category: test

### ERR-013 — 2026-11-17 — Unclosed database connections (ResourceWarning)
Who: Claude Code
Phase / task: Phase 1 — Alembic + Phase 1 migration
What happened: `ResourceWarning: unclosed database` (sqlite) and `psycopg.Connection ... was deleted while still open`.
Cause: engines created in a test fixture, in the `/health` database test and in `migrations/env.py` were never disposed.
Fix: dispose each engine when done (fixture teardown, try/finally).
Verified by: `pytest -W error::ResourceWarning -W error::pytest.PytestUnraisableExceptionWarning` → 39 passed.
Prevention: lesson line above.
Category: test

### ERR-014 — 2026-11-17 — mypy found tests/helpers.py twice; scalar_one() returned Any
Who: Claude Code
Phase / task: Phase 1 — Alembic + Phase 1 migration
What happened: `Source file found twice under different module names`; `Returning Any from function declared to return "UUID"`.
Cause: no explicit package base for `tests`; SQLAlchemy `scalar_one()` is untyped.
Fix: `mypy_path = "."` and `explicit_package_bases = true`; typed local variables.
Verified by: `mypy app tests migrations` → Success.
Prevention: run mypy on tests too, in every check.
Category: tooling

### ERR-015 — 2026-11-17 — Weak safety check in the migration tests (found in review)
Who: Claude Code
Phase / task: Phase 1 — Alembic + Phase 1 migration
What happened: the check compared host, user and database name; a Direct URL and a pooler URL of the same project differ in both, so the destructive tests could have run on the main project.
Cause: one Supabase project has two connection-string styles.
Fix: compare the Supabase project id (`postgres.<ref>` user or `db.<ref>.supabase.co` host); refuse unknown URLs; 3 tests for it.
Verified by: `pytest -k project_ref` → 3 passed.
Prevention: a destructive test identifies its target by the most stable id available.
Category: logic

### ERR-016 — 2026-11-17 — Alembic deprecation warning failed the test setup
Who: Claude Code
Phase / task: Phase 1 — Alembic + Phase 1 migration
What happened: `DeprecationWarning: No path_separator found in configuration` → 8 errors when warnings are errors.
Cause: `alembic.ini` lacked `path_separator`.
Fix: added `path_separator = os` (the setting Alembic recommends).
Verified by: full suite → 39 passed.
Prevention: none needed.
Category: dependency

### ERR-017 — 2026-11-17 — Savepoint closed in the wrong order in the constraint tests
Who: Claude Code
Phase / task: Phase 1 — Alembic + Phase 1 migration
What happened: `InFailedSqlTransaction ... RELEASE SAVEPOINT sa_savepoint_1` in 4 tests (the constraints themselves did reject the rows).
Cause: `with conn.begin_nested(), pytest.raises(...)` let pytest catch the error before the savepoint saw it, so it tried to release a failed savepoint.
Fix: order `with pytest.raises(...), conn.begin_nested():`.
Verified by: full suite → 39 passed, twice.
Prevention: when testing for a database error inside a savepoint, the savepoint goes innermost.
Category: test

### ERR-018 — 2026-11-17 — Refactor script's leftover check was too strict
Who: Claude Code
Phase / task: Phase 1 — `/me` + consent (moving shared test fixtures)
What happened: `AssertionError: leftover` from my one-off refactor script.
Cause: the check looked for the text `_project_ref`, which also appears inside the test name `test_project_ref_same_for_direct_and_pooler`.
Fix: check for `def _project_ref` and ` _project_ref(` instead. The script stops before writing, so no file was changed by the failed run.
Verified by: `git status` before the rerun showed only the intended files; rerun → full suite 39 passed.
Prevention: write leftover checks against definitions and calls, not bare names.
Category: tooling

### ERR-019 — 2026-11-17 — npm peer-dependency conflicts while installing the frontend toolchain
Who: Claude Code
Phase / task: Phase 1 — frontend, seed, checks
What happened: `ERESOLVE`: openapi-typescript needs TypeScript ^5; eslint-plugin-jsx-a11y supports ESLint ≤ 9; @eslint/js 10 needs ESLint 10.
Cause: newest major versions do not all fit together yet.
Fix: TypeScript 5.9.3 and ESLint 9.39.5 / @eslint/js 9 (recorded in DEC-037).
Verified by: `npm install` → added 571 packages, no conflicts.
Prevention: check `npm view <pkg> peerDependencies` before choosing majors.
Category: dependency

### ERR-020 — 2026-11-17 — Vitest: "failed to find the current suite"
Who: Claude Code
Phase / task: Phase 1 — frontend, seed, checks
What happened: every test file failed with no tests run, from the Git Bash shell.
Cause: the shell's working directory was `c:\...` while Node resolved packages under `C:\...`, so Vitest was loaded twice.
Fix: `frontend/scripts/run.mjs` starts Vitest/Playwright from the real path spelling; `npm test` and `npm run test:e2e` use it. A config-file `chdir` was tried first and did not help (Vitest loads before its config).
Verified by: `npm test` from the lowercase shell → 23 passed.
Prevention: lesson line above.
Category: tooling

### ERR-021 — 2026-11-17 — "Invalid hook call" in the consent form test
Who: Claude Code
Phase / task: Phase 1 — frontend, seed, checks
What happened: `Invalid hook call` / `Cannot read properties of null (reading 'useMemo')`.
Cause: React was resolved twice: directly and through the `packages/ui` workspace link.
Fix: `resolve.dedupe: ['react', 'react-dom']` in the Vitest config and both app Vite configs.
Verified by: `npm test` → 23 passed; both apps build and run in the E2E tests.
Prevention: keep the dedupe in every Vite config.
Category: tooling

### ERR-022 — 2026-11-17 — Landing page crashed: Button asChild with two children
Who: Claude Code
Phase / task: Phase 1 — frontend, seed, checks
What happened: E2E: `Slot failed to slot onto its children` on `/`.
Cause: the Button passed the (empty) spinner slot plus the link to Radix `Slot`, which needs exactly one child.
Fix: when `asChild` is set, only the child is passed.
Verified by: E2E landing test passes in both projects.
Prevention: E2E covers every public page.
Category: logic

### ERR-023 — 2026-11-17 — Accessibility violations on legal pages
Who: Claude Code
Phase / task: Phase 1 — frontend, seed, checks
What happened: axe: `label` (unlabelled inputs) on `/consent`; `scrollable-region-focusable` on wide tables at 375px.
Cause: Markdown task lists render as `<input type=checkbox>`; tables scroll sideways without being focusable.
Fix: task-list boxes render as ☐/☑ text; tables get `tabindex="0"` (packages/ui Markdown).
Verified by: E2E with axe → 26 passed.
Prevention: axe runs on every E2E page at 375px and 1280px.
Category: logic

### ERR-024 — 2026-11-17 — Launcher passed arguments through cmd.exe
Who: Claude Code
Phase / task: Phase 1 — frontend, seed, checks
What happened: `'about' is not recognized as an internal or external command` when a test filter contained `|`.
Cause: `spawnSync(..., { shell: true })` on Windows let cmd.exe interpret `|`.
Fix: run each tool's JS entry with `node` directly, no shell.
Verified by: `npm test` and filtered Playwright runs work.
Prevention: never use `shell: true` for tool launchers.
Category: tooling

### ERR-025 — 2026-11-17 — Contrast: white text on the dark-mode urgent colour
Who: Claude Code
Phase / task: Phase 1 — frontend, seed, checks
What happened: found in self-review: white on `#F97066` is below 4.5:1.
Cause: only `urgent on bg` was contrast-checked in DESIGN_SYSTEM §3.4.
Fix: dark mode uses `--color-bg` as text on urgent (6.52 / 6.55); added to DESIGN_SYSTEM §3.4.
Verified by: axe colour-contrast passes in the laptop-dark E2E project.
Prevention: check every new colour pair (DESIGN_SYSTEM rule).
Category: logic

### ERR-026 — 2026-11-17 — Seed script: doctor inserted before its user; seed check matched other tests' data
Who: Claude Code
Phase / task: Phase 1 — frontend, seed, checks
What happened: `ForeignKeyViolation ... fk_doctors_user_id_users`; earlier the test hit "already exists" because other tests also create "Test Patient 1".
Cause: no ORM relationships, so SQLAlchemy did not order the inserts; the "already seeded" check used a patient name that is not unique to the seed.
Fix: flush each user right after adding it; detect the seed by its own account domain `seed.alovia.test`.
Verified by: `pytest` → 78 passed.
Prevention: flush parent rows explicitly when models have no relationships.
Category: logic

### ERR-027 — 2026-11-17 — Commit dfea277 included an unformatted `.prettierrc.json`
Who: Claude Code
Phase / task: Phase 1 — frontend, seed, checks
What happened: `format:check` printed a warning, but the chain went on to commit because its output was piped into `tail`.
Cause: a pipe's exit code is the last command's (`tail`), so the failure was hidden.
Fix: formatted the file and committed the fix (cd42fe2); `check_all` runs each step separately and stops on a non-zero exit.
Verified by: `npm run format:check` → exit 0; `check_all.ps1` → All checks passed (and a probe step proves it fails with exit 1).
Prevention: lesson line above.
Category: tooling

### ERR-028 — 2026-11-17 — E2E onboarding test failed: static /home mock
Who: Claude Code
Phase / task: Phase 2 — task 3 (dates)
What happened: after saving dates the test expected the new header, but the page showed the onboarding card again (2 projects failed).
Cause: the test's `/home` mock always returned the "no dates" answer; on arriving at /home, TanStack Query refetches on mount and overwrote the fresh data the save had put in the cache. The app is correct — a real backend returns the saved dates.
Fix: the mock now answers like the real backend (returns the active home after the save succeeded).
Verified by: `npm run test:e2e` → 36 passed.
Prevention: route mocks that model state changes must change state like the backend would.
Category: test

### ERR-029 — 2026-11-17 — Two shell commands failed to parse (unexpected EOF)
Who: Claude Code
Phase / task: Phase 2 — tasks 1-3
What happened: two long inline heredoc chains failed with `unexpected EOF while looking for matching quote`; nothing in them ran (verified with git status both times).
Cause: multi-file edits with nested quotes written as one giant shell command.
Fix: redone as script files in the scratchpad, run with one short command.
Verified by: the reruns applied cleanly; `git diff --stat` matched the intended files.
Prevention: lesson line above.
Category: tooling

### ERR-030 — 2026-11-17 — npm workspace install crashed ("reading 'location'")
Who: Claude Code
Phase / task: Phase 2 — task 5 (installing motion)
What happened: `npm install -w patient-web motion` failed with `Cannot read properties of null (reading 'location')`.
Cause: a stale npm workspace tree state (known npm arborist glitch).
Fix: a plain `npm install` repaired the tree; the motion install then succeeded.
Verified by: `motion 14.14.0` resolves; full E2E suite passes.
Prevention: when a workspace install crashes inside npm itself, repair with a plain install before retrying.
Category: tooling

### ERR-031 — 2026-11-17 — Edit script failed mid-run, leaving a half-edited test file
Who: Claude Code
Phase / task: Phase 2 — task 5 (content tests)
What happened: a multi-substitution script asserted on its third pattern after already writing two files.
Cause: each substitution wrote immediately instead of checking every pattern first (and the pattern had drifted from the file).
Fix: finished the edit with the Edit tool; the later record scripts now assert all patterns before writing anything.
Verified by: `ruff`/`mypy`/`pytest` green afterwards.
Prevention: edit scripts verify every match first, write second (repeat of the ERR-029 lesson class).
Category: tooling

### ERR-032 — 2026-11-17 — Four E2E failures from ambiguous locators
Who: Claude Code
Phase / task: Phase 2 — task 5 (E2E)
What happened: strict-mode violations: the current month's drawing appears twice (baby card + strip) and two role=status elements exist (notice + prototype banner).
Cause: the new blocks made previously unique selectors ambiguous.
Fix: count-based and filtered selectors.
Verified by: `npm run test:e2e` → 42 passed.
Prevention: none needed — strict mode caught exactly what it should.
Category: test

### ERR-033 — 2026-11-17 — Read used the scratchpad path for a file saved under $TEMP
Who: Claude Code
Phase / task: Phase 2 — task 4 (WHO table image)
What happened: the first Read of the downloaded Table 11 image failed ("File does not exist").
Cause: the shell's $TEMP is C:\Users\Engineer\AppData\Local\Temp, not the session scratchpad; the download went to $TEMP\who-s1.
Fix: read the real path after checking `echo $TEMP`.
Verified by: the image opened and the table was transcribed.
Prevention: print the resolved path once before reading downloaded files.
Category: tooling

### ERR-034 — 2026-11-17 — `npm install -w patient-web react-day-picker` failed again with "reading 'location'"
Who: Claude Code
Phase / task: Phase 2 — task 6
What happened: same npm error as ERR-030; nothing was installed.
Cause: npm's workspace install trips on the lockfile tree state (as in ERR-030).
Fix: plain `npm install` first, then the workspace install — worked; `react-day-picker` 9.14.0 pinned.
Verified by: package.json shows the exact version; typecheck and tests pass.
Prevention: second occurrence → Lesson added (always repair with `npm install` first).
Category: tooling

### ERR-035 — 2026-11-17 — Inline heredoc with quotes died again (nothing ran)
Who: Claude Code
Phase / task: Phase 2 — task 6 (service edits)
What happened: a long inline Python heredoc failed with "unexpected EOF while looking for matching `''"; no file was changed.
Cause: the existing Lesson (scratchpad script files for quote-heavy edits) was not followed.
Fix: the same edits written to a scratchpad script that asserts every pattern before writing; applied cleanly.
Verified by: "service ok"; ruff, mypy and tests pass.
Prevention: follow the existing Lesson; no new rule needed.
Category: tooling

### ERR-036 — 2026-11-17 — Date-only appointments would show the previous day on the home card (latent, task 5)
Who: Claude Code
Phase / task: Phase 2 — task 6 (found while reading task 5 code)
What happened: a date-only appointment is stored at local (Asia/Kolkata) midnight; the database returns UTC, and the home card took the day from the first 10 characters of that UTC value — the previous day. No user saw it: no appointment could be created before task 6.
Cause: the API sent the raw UTC moment and the app derived the day from it; the task 5 test stored UTC midnight, which hid the bug.
Fix: the API now sends `date` and `time` already converted to the config timezone; the app shows them as they are. The test now stores local midnight and asserts the day.
Verified by: `test_next_appointment_picks_the_soonest_upcoming` (fails on the old code: no `date` field, and the UTC day would be wrong) and the calendar local-day test pass.
Prevention: Lesson added.
Category: bug

### ERR-037 — 2026-11-17 — E2E: accessibility and test-locator failures on the new calendar screens
Who: Claude Code
Phase / task: Phase 2 — task 6
What happened: (1) axe `label-content-name-mismatch` on the home week strip (aria-label "17 November 2026" did not contain the visible "Tue 17") and on react-day-picker's own day labels ("November 1st" does not contain "1"); (2) axe `color-contrast` on today's day in dark mode; (3) a week-strip test counted 8 links instead of 7.
Cause: (1) labels that replaced the visible text instead of extending it (WCAG 2.5.3); (2) the library stylesheet loads after ours, so its blue accent overrode our token rule of equal specificity; (3) the locator also matched the "Open the calendar" link.
Fix: (1) week strip keeps its visible text and adds screen-reader-only words; calendar days use our own label that starts with the day number ("17 November 2026, Tuesday, today, selected, milestone"); (2) the token rule now targets `.rdp-root.alovia-calendar`; (3) count links inside the list only.
Verified by: `e2e/calendar.spec.ts` and `e2e/journey-home.spec.ts` pass on phone-light and laptop-dark with no axe violations.
Prevention: the axe check on every new screen caught all three; keep it.
Category: accessibility / test

### ERR-038 — 2026-11-17 — Unused import after the week-strip fix; first check_all run failed on lint
Who: Claude Code
Phase / task: Phase 2 — task 6
What happened: `scripts/check_all.sh` stopped at ESLint: `formatDay` unused in JourneyBlocks.tsx. The background-task notice said "exit 0" because that was the exit code of the logging wrapper, not of the checks; the log itself showed exit 1.
Cause: the ERR-037 fix removed the last use of `formatDay`; lint was not re-run after that edit.
Fix: import removed; check_all re-run in the foreground → exit 0.
Verified by: `bash scripts/check_all.sh` → "All checks passed.", exit code 0.
Prevention: existing Lesson (read the check's own exit code); re-run lint after every follow-up fix.
Category: tooling

### ERR-039 — 2026-11-17 — E2E: doctor-notes list locator matched the nav bar too
Who: Claude Code
Phase / task: Phase 2 — task 7
What happened: `getByRole('listitem')` found 8 items instead of 2.
Cause: the 6 main-navigation items are list items as well.
Fix: scope to the page: `getByRole('main').getByRole('listitem')`.
Verified by: `e2e/notifications.spec.ts` 8 passed.
Prevention: scope list locators to `main` or a named region (same kind as ERR-037 (3)).
Category: test

### ERR-040 — 2026-11-17 — Older navigation E2E test failed once Doctor notes became a real page
Who: Claude Code
Phase / task: Phase 2 — task 7
What happened: "navigation shows the six items (DEC-040)" timed out waiting for the "Doctor notes" heading.
Cause: the page now calls `GET /patient/doctor-notes`, which that test did not mock, so it ended in the error state (the placeholder needed no data).
Fix: `signInAsPatient` now also answers `notifications` and `doctor-notes` with empty lists (tests that need data route them again); the test's assertions are unchanged.
Verified by: `bash scripts/check_all.sh` → exit 0 (Playwright 58 passed).
Prevention: when a placeholder page becomes real, add its baseline mock to the shared sign-in helper in the same change.
Category: test

### ERR-041 — 2026-11-17 — Doctor consent E2E failed on the phone project only
Who: Claude Code
Phase / task: Phase 2 — task 0
What happened: after Continue, the check for the "Main" navigation found no element at 375px.
Cause: on phones the doctor shell keeps its navigation inside a closed menu, so the side nav is hidden and not in the accessibility tree; the test, not the app, was wrong.
Fix: check the Home page heading instead, which shows on both sizes.
Verified by: `e2e/doctor.spec.ts` 8 passed (phone-light + laptop-dark).
Prevention: in responsive layouts assert on page content, not on navigation that changes per screen size.
Category: test

### ERR-042 — 2026-11-17 — Appointment dates near year 1 or 9999 could break her appointments (found in the phase review)
Who: Claude Code
Phase / task: Phase 2 — task 9 review (code from task 6)
What happened: `POST /patient/appointments` accepted any date. 0001-01-01 at local midnight (Asia/Kolkata) is before year 1 in UTC, and Python cannot read such a stored value back, so her list, calendar and home would fail afterwards; `GET /calendar?to=9999-12-31` overflowed on `end + 1 day` (500).
Cause: no range check on free dates; the date rules D1-D3 only cover pregnancy dates.
Fix: appointment `date` and calendar `from`/`to` must be within 1900-01-01 .. 2999-12-31 (400 otherwise).
Verified by: new cases in `test_appointment_input_is_validated` and `test_calendar_rejects_a_reversed_range`; reproduced the overflow in Python first.
Prevention: Lesson added.
Category: bug

### ERR-043 — 2026-11-17 — CREDITS.md not updated when icons, placeholder drawings and content sources shipped
Who: Claude Code
Phase / task: Phase 2 — task 9 review (assets from tasks 4-5)
What happened: CREDITS.md says every asset is listed before use; the 7 Fluent icon files, the placeholder month drawings and the WHO / OWH / NHS / MedlinePlus sources were recorded elsewhere (content files, HISTORY) but not here.
Cause: the credits file was not on the task 4/5 checklist.
Fix: CREDITS.md now lists the icon files, the placeholder drawings (own script, no third-party asset, replace before release) and the four content sources with licences.
Verified by: file paths checked on disk; check_all green (the About page renders CREDITS).
Prevention: Lesson added.
Category: process

### ERR-044 — 2026-11-18 — Inline heredocs failed three times (regex escapes, long YAML)
Who: Claude Code
Phase / task: Phase 3 — task 1 (sources and rule files)
What happened: (1) two inline Python heredocs with regex backslashes failed with "missing ), unterminated subpattern"; (2) a long heredoc writing four YAML files failed with "unexpected EOF while looking for matching `''". Nothing was written in any case.
Cause: Git Bash mangles some backslash and quote sequences in long inline commands; the existing Lesson (scratchpad scripts) was not followed for these smaller-looking steps.
Fix: the same code as scratchpad scripts and the YAML files written with the file tool.
Verified by: the extractions ran; the rule files load and 24 rule-file tests pass.
Prevention: Lesson tightened (any regex with backslashes or any long text block → script or file tool).
Category: tooling

### ERR-045 — 2026-11-18 — A check-in's entries came back in random order
Who: Claude Code
Phase / task: Phase 3 — task 4 (found by check_all; code from task 3)
What happened: `test_details_notes_history_and_charts` failed in one full run: the history returned the `other` entry before the nausea entry.
Cause: all entries of a check-in are inserted in one transaction, so they share `created_at`; the tie-break on the random UUID made the order arbitrary. The test had passed by chance before.
Fix: `list_checkins` returns each check-in's entries in form order (warning signs, then everyday symptoms, as in the rule files).
Verified by: the test passed three runs in a row, then check_all exit 0.
Prevention: never rely on `created_at` to order rows written in the same transaction.
Category: bug

### ERR-046 — 2026-11-19 — check_all failed on four database tests: host could not be resolved
Who: Claude Code
Phase / task: Phase 3 — task 5 checks
What happened: one full check run took 8 h 11 min and 4 integration tests (Phase 2 audit and calendar tests) failed with `failed to resolve host 'aws-0-ap-south-1.pooler.supabase.com'`.
Cause: the network/DNS was unavailable during the run (the machine was asleep or offline); not a code change — the failing tests touch none of the task 5 code.
Fix: confirmed the host resolves again, re-ran check_all → exit 0 (334/44/82).
Verified by: the re-run.
Prevention: a database test that fails with a DNS/connection error is re-run after checking the network before looking for a code cause.
Category: environment

### ERR-047 — 2026-11-19 — Inline heredoc writing three test files failed
Who: Claude Code
Phase / task: Phase 5 — task 1 (tests)
What happened: one Bash command appending test helpers and writing two test files through heredocs failed with "unexpected EOF while looking for matching `''"; nothing was written.
Cause: the existing Lesson (ERR-044: long text blocks → file tool) was not followed.
Fix: the same content written with the file tool.
Verified by: the files exist; 491 tests passed.
Prevention: follow the existing Lesson; no new rule needed.
Category: tooling

### ERR-048 — 2026-11-19 — A replaced invite link still checked as valid
Who: Claude Code
Phase / task: Phase 5 — task 2 (found by the new test)
What happened: `test_invite_link_replaces_the_unused_one` failed: after a second link, the first code still checked valid.
Cause: the cancel step set `expires_at` to the app server's clock, while the check compares with the database's `now()`; the two clocks differ by a few seconds, so the old code stayed valid briefly.
Fix: invite create, cancel and link all use database time (`func.now()`).
Verified by: the invite and doctor tests passed (24).
Prevention: Lesson added (compare times on one clock: the database's).
Category: bug

### ERR-049 — 2026-11-19 — `ruff format .` reformatted the owner's notebooks
Who: Claude Code
Phase / task: Phase 5 — decision A
What happened: after moving the notebooks into `backend/`, `ruff format .` rewrote their code cells and `ruff check` reported 35 style errors in them.
Cause: ruff lints and formats `.ipynb` files inside the project by default.
Fix: notebooks restored from the untouched copies, the save cells added again; `extend-exclude = ["ml_training"]` in `pyproject.toml`.
Verified by: ruff clean; notebooks differ from the originals only by the added cell.
Prevention: third-party or owner files placed in the repo are excluded from formatters in the same step.
Category: tooling

### ERR-050 — 2026-11-19 — Prediction route returned 500: deprecated `Result.tuples()`
Who: Claude Code
Phase / task: Phase 5 — task 3 (found by the new tests)
What happened: 9 of 15 new prediction tests failed; the route raised `SADeprecationWarning: The Result.tuples() method is deprecated` (warnings are errors in tests).
Cause: `.tuples()` written from memory; SQLAlchemy 2.1 deprecated it (rows unpack directly).
Fix: unpack the rows in a dict comprehension.
Verified by: 15 passed.
Prevention: tests run with warnings as errors, which caught it; no new rule.
Category: bug

### ERR-051 — 2026-11-19 — axe `aria-hidden-focus` on the doctor charts
Who: Claude Code
Phase / task: Phase 5 — task 3 (E2E)
What happened: the result and trend charts failed axe: focusable elements inside `aria-hidden` wrappers.
Cause: Recharts 3 adds a keyboard accessibility layer (focusable SVG) by default; the charts are hidden from screen readers because a text list/table carries the same data.
Fix: `accessibilityLayer={false}` on both charts.
Verified by: 6 E2E runs passed with axe.
Prevention: Lesson added.
Category: accessibility

### ERR-052 — 2026-11-19 — `npm install -w doctor-web` failed with "reading 'location'" (third time)
Who: Claude Code
Phase / task: Phase 5 — task 3 (Recharts in the doctor app)
What happened: the workspace install failed as in ERR-030 and ERR-034.
Cause: same npm workspace bug; the existing Lesson was not applied first.
Fix: plain `npm install`, then the workspace install.
Verified by: install succeeded; lockfile +2 lines.
Prevention: existing Lesson.
Category: tooling

### ERR-053 — 2026-11-19 — Inline heredoc with apostrophes failed again
Who: Claude Code
Phase / task: Phase 5 — task 4 (journey edits)
What happened: a Bash heredoc holding Python with "can't" strings failed ("unexpected EOF"); nothing was written.
Cause: the ERR-044 Lesson was not applied to a long edit.
Fix: the edit as a scratchpad script.
Verified by: the script ran; tests pass.
Prevention: existing Lesson.
Category: tooling

### ERR-054 — 2026-11-19 — E2E label lookup matched two fields
Who: Claude Code
Phase / task: Phase 5 — task 4 (E2E)
What happened: `getByLabel('Due date')` also matched the radio "Clinician-confirmed due date" (strict-mode violation).
Cause: Playwright label matching is a substring match by default.
Fix: `{ exact: true }`.
Verified by: 6 passed.
Prevention: use exact label matches where a label is part of another label.
Category: test

### ERR-055 — 2026-11-19 — check_all lint failed on an E2E file the agent had not linted
Who: Claude Code
Phase / task: Phase 5 — task 4 checks
What happened: `npm run lint` failed: a non-null assertion (`!`) in `e2e/doctor-care.spec.ts`.
Cause: during the task the agent linted `apps` and `packages` only, not `e2e`.
Fix: `notes.map(...)` instead of `notes[0]!`; all frontend checks re-run → exit 0 (63 unit, 114 E2E).
Verified by: the re-run.
Prevention: lint with `npx eslint .` (whole frontend), as check_all does.
Category: tooling

### ERR-056 — 2026-11-19 — Storage client left an HTTP error response open
Who: Claude Code
Phase / task: Phase 5 — task 5 (found by the storage unit test)
What happened: `ResourceWarning: Implicitly cleaning up <HTTPError 400>` (warnings are errors in tests).
Cause: `urllib`'s `HTTPError` keeps the response open; the client raised a new error without closing it.
Fix: `exc.close()` before raising the 503.
Verified by: 3 storage tests pass with warnings as errors.
Prevention: close `HTTPError` whenever it is caught.
Category: bug
