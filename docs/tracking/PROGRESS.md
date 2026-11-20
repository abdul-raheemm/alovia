# PROGRESS — task tracker

Status keys: `[ ]` not started · `[~]` in progress · `[x]` done (tests pass + owner approved) · `[!]` blocked (say why).
Update after every task. Each line: status, task, who, date, notes.

## Phase 0 — Documentation
- [x] Module specs (Genetic, Symptoms, Journey, Dashboard, RAG, ML) — Claude (planning chat) — 2026-11-16
- [x] Blueprint documents, legal drafts, tracking files, CLAUDE.md, README — Claude (planning chat) — 2026-11-16
- [ ] Owner review of all documents — Raheem

## Phase 1 — Foundation
- [x] `.gitignore` (`ml-test/`, `rag/`, `.env`, `.venv/`, `node_modules/`, …); first commit rewritten so the old folders were never in it — Raheem + Claude Code — 2026-11-16
- [x] **Owner action:** create GitHub repo; remote added — Raheem — 2026-11-16
- [x] Copy `rag/alovia-knowledge-base/` (`clean/`, `raw/`, CSVs, `PROGRESS.md`) into `knowledge-base/` and `rag/*.py` into `knowledge-base/tools/` (copy only; `rag/` untouched; licence and attribution details stay with each file as `docs/knowledge-base/knowledgebase.md` requires). Ask the owner before copying the four `rag/` root CSVs. Collection continues in `knowledge-base/` afterwards. The RAG module stays in Phase 7. — Raheem + Claude Code — 2026-11-17 (401 identical, 3 scripts one line changed, validator 196/0/10)
- [x] Backend skeleton (Python 3.14 venv, FastAPI app factory, config, logging, error envelope, `/health`) — Raheem + Claude Code — 2026-11-17 (11 tests pass, 100% coverage; `/health` gains `db`, models, rules in later tasks; 405 error code `TODO(OPEN)`)
- [x] Agree ML reference inputs with the owner; run the old `ml-test` backend (from a copy) and save outputs to `backend/tests/fixtures/ml_reference_outputs.json` before any change — Raheem + Claude Code — 2026-11-17 (12 cases: 3 fetal, 3 maternal + 6 High→Mid; two runs byte-identical)
- [x] **Owner action:** create fresh Supabase project (done 2026-11-17, Mumbai); fill `backend/.env` — Raheem — 2026-11-17
- [x] Auth part 1: token check (`app/core/auth.py`, JWKS signature, issuer, audience, expiry) — Raheem + Claude Code — 2026-11-17 (27 tests pass)
- [x] Alembic setup + Phase 1 migration (identity + result tables; no RLS until Phase 8) — ask before applying — Raheem + Claude Code — 2026-11-17 (39 tests pass on alovia-test; applied to the main project with owner approval: `alembic current` = 0001)
- [x] Auth part 2: `/me` + consent route + role lookup (needs the Phase 1 tables; consent version per DEC-031; user rows per DEC-032) — Raheem + Claude Code — 2026-11-17 (51 tests pass; sign-in audit entry `TODO(OPEN)`)
- [x] Move ML code + model files; regression tests identical to reference outputs — Raheem + Claude Code — 2026-11-17 (12/12 reference cases identical; model files byte-identical; routes are Phase 5)
- [x] Frontend workspace: patient-web, doctor-web, packages/ui (tokens, themes, fonts), packages/shared (API client) — Raheem + Claude Code — 2026-11-17 (versions DEC-037)
- [x] Sign-up through invite link only (18+ + consent), sign-in, sign-out; role routing. Note: invite creation UI is Phase 5 — until then the seed script creates invite links for testing — Raheem + Claude Code — 2026-11-17 (backend `/invites/{code}/check`, `/patient/link`; real sign-up needs the owner's frontend `.env` and Supabase redirect URLs)
- [x] App shells: nav bars, urgent button placeholder, theme switch, legal pages, about page — Raheem + Claude Code — 2026-11-17
- [x] Patient app PWA manifest + icons — Raheem + Claude Code — 2026-11-17
- [x] Seed script (synthetic data) — Raheem + Claude Code — 2026-11-17 (Phase 1 tables only; later phases add their rows)
- [x] `scripts/check_all` runs every check — Raheem + Claude Code — 2026-11-17
- [x] Phase 1 review + CHANGELOG 0.1.0 — Raheem — 2026-11-17 (approved; merged into `main`)

## Phase 2 — Pregnancy Journey
- [x] Migration (date history, appointments, notifications, doctor_notes) + inbox_items (DEC-044) — Raheem + Claude Code — 2026-11-17 (migration 0002; tested on alovia-test; applied to the main project: `alembic current` = 0002)
- [x] GA/month/trimester calculations + tests — Raheem + Claude Code — 2026-11-17 (`app/modules/journey/engine.py`, `rules/journey/config.yaml`; 42 engine tests)
- [x] Dates onboarding + validation — Raheem + Claude Code — 2026-11-17 (D1-D3, §5.3 override confirmation, date history; messages.yaml with all §13.2 keys pending approval; home header + onboarding + dates screens; nav from config, DEC-040)
- [x] Content provider interface + prototype YAML content + size reference (sourced) — Raheem + Claude Code — 2026-11-17 (interface built in task 5; 21 items covering all 9 content types and all 9 months from OWH stages page, local NHS unchanged excerpts, local MedlinePlus public-domain text; 7 size rows from WHO Table 11 50th percentile transcribed from the published table image; 7 Fluent Emoji icons (MIT) + LICENSE shipped; OpenStax NOT used — its live licence is CC BY-NC-SA, open question for the owner)
- [x] Home screen blocks; month cards + detail; illustrations (licensed or placeholders) — Raheem + Claude Code — 2026-11-17 (§4.3 order: header, baby card with float, This stage, quick log, next appointment, months strip; month detail; content provider interface with EMPTY files until task 4; placeholder drawings labelled "Placeholder"; defensive bad-date guard)
- [x] Calendar + appointments (patient side) — Raheem + Claude Code — 2026-11-17 (GET /patient/journey/calendar with §6.4 milestones + appointments; /patient/appointments list/create/edit/delete own, doctor-added read-only; Calendar tab (react-day-picker 9.14.0, owner approval), home week strip, Appointments tab; latent UTC-day bug in the task 5 next-appointment block fixed; symptom dots wait for Phase 3, suggested check-ups stay off (R3))
- [x] Notifications bar + doctor notes (patient side) — Raheem + Claude Code — 2026-11-17 (generated on app open: new_week, new_month, appointment_soon, doctor_note; one per (patient, type, target); read/dismiss; baby-stage notices stop and are hidden after the end; Doctor notes tab read-only, newest first; result_available / genetic_reviewed / dates_updated wait for the doctor actions in Phases 4-5)
- [x] Pregnancy-end flow + undo — Raheem + Claude Code — 2026-11-17 (POST /patient/pregnancy-end and /undo; status, time and answer stored; status changes logged in pregnancy_date_history; pregnancy_ended inbox item only on "yes", in the same transaction; quiet ended home with support/safety messages (pending approval), My records links and undo within resume_window_days; entry wording and helpline stay [OPEN])
- [x] Phase 1 follow-ups moved here (task 0): doctor/admin consent, 405 code, sign-in audit — Raheem + Claude Code — 2026-11-17 (doctor app asks for the app-wide consent once before anything else; `METHOD_NOT_ALLOWED` for 405; first `/me` of each Supabase session writes a "signed in" audit row; DEC-046 to DEC-048)
- [ ] E2E + accessibility; review; CHANGELOG 0.2.0 — agent part done 2026-11-17 (full check_all green; §15 map; code review fixed a date-overflow bug; credits completed; patient audit entries added (DEC-049); CHANGELOG 0.2.0 and version 0.2.0 written) — **waiting for the owner's review, then merge to main**

Build order for the rest of Phase 2 (owner, 2026-11-17): home screen + month cards (task 5) **before** the content provider (task 4); then calendar/appointments, notifications, pregnancy end, task 0, review.

## Phase 3 — Symptom Tracking
- [x] Migration; vocabulary YAML; red-flag YAML; PUQE; pattern rules — Raheem + Claude Code — 2026-11-18 (migration 0003 tested on alovia-test and applied to main; `backend/rules/symptoms/` config, symptoms, red_flags (25 rules), puqe (official wording), patterns, messages + helplines; loader `app/modules/symptoms/rules.py` checks and cross-checks at startup; /health reports symptoms rules loaded)
- [x] Engine + one test per rule; API; inbox items — Raheem + Claude Code — 2026-11-18 (`app/modules/symptoms/engine.py`: V1/V2 validation, 25 rules as data, highest level wins, PUQE, P1-P5, V3 fallback; 66 engine tests incl. a guard that every rule ID has a test; routes vocabulary / checkins (POST, GET) / charts; inbox items symptom_l1/l2 + pattern_p1..p5 in the same transaction; 13 API tests)
- [x] Log page, urgent button (bundled advice), result screens, charts, calendar dots, weekly summary — Raheem + Claude Code — 2026-11-18/19 (log + urgent + advice screens; history charts; "logged today", weekly summary, calendar symptom dots and red-flag icons)
- [ ] E2E; review; CHANGELOG 0.3.0 — agent part done 2026-11-19 (full check_all green; §14 map; review fixed the V3 advice text; rule-review sheet + sign-off file; CHANGELOG 0.3.0; version 0.3.0) — **waiting for the owner's review, then merge to main**

## Phase 4 — Genetic Risk
- [x] YAML rules (HBB/HEM/MAR, evidence, conflicts, messages, config) — Raheem + Claude Code — 2026-11-19 (`backend/rules/genetic/` 8 files incl. labels.yaml; strict loader with coverage checks: 45 haemoglobin pairs once, 8 haemophilia form combinations once, 6 Marfan pairs once; /health genetic: true)
- [x] Engine + 45 pair tests + all other tests — Raheem + Claude Code — 2026-11-19 (`app/modules/genetic/engine.py`: E1/E2, evidence handling, conflicts as data, rule tables, §6.4 priority, §9 prompts and the exact risk definition, E3/E4; 112 tests: 45 pairs, every HEM/MAR row, evidence, C1/C2/F1/F2/E3/E4, priority, not assessed, consanguinity, timing, show-before-review, no 0%/no sex field, nudges, validation, rule-coverage guard. Spec test 10 is Phase 5)
- [x] Migration + API + patient forms/results — Raheem + Claude Code — 2026-11-19 (migration 0004 on main; `/patient/genetic/assessments`; inbox items; patient form with consent reminder, entry questions and evidence by status; result screen with boy+girl together, disclaimer and doctor note apart; history; More link; home "Genetic check" card)
- [ ] E2E; review; CHANGELOG 0.4.0 — agent part done 2026-11-19 (full check_all green; §14 tests 1-9 automated, test 10 in Phase 5; rule-review sheet (66 rows) + sign-off file; CHANGELOG 0.4.0; version 0.4.0) — **waiting for the owner's review, then merge to main**

## Phase 5 — Doctor Dashboard + Admin
- [x] Task 1 foundation: migration 0005 (alovia-test, then main), doctor/admin access checks (role + active + consent + assignment), dashboard config + messages — Raheem + Claude Code — 2026-11-19
- [x] Training ranges (decision A): notebooks re-run, range files from the training split — Raheem + Claude Code — 2026-11-19
- [x] Task 2 patient list, inbox, patient tabs (Overview), create/edit, invite links — Raheem + Claude Code — 2026-11-19 (owner approved; range basis DEC-087)
- [x] Task 3 predictions: schema, units, range warnings, limitations, HbA1c note, sharing, trends, patient My results — Raheem + Claude Code — 2026-11-19 (owner approved; DEC-088..091 accepted)
- [x] Task 4 genetic review (queue, confirm, correct, race), symptoms view, notes, appointments, dates/status — Raheem + Claude Code — 2026-11-19 (owner approved; DEC-092..095 accepted) (records = task 5)
- [x] Task 5 medical records: upload (type + signature + size checks), list, 5-minute download links — Raheem + Claude Code — 2026-11-20 (owner approved; DEC-096..098; real-bucket check at the task 7 review, DEC-104)
- [x] Task 6 rule review (sign-off, export, require_signoff), activity log, admin (doctors, invite, assignments), Set password — Raheem + Claude Code — 2026-11-20 (owner approved) (invite links were done in task 2)
- [x] Task 7 E2E (access control on all 41 routes); review; `make_doctor.py`; manual checklist (owner, done 2026-11-20); CHANGELOG 0.5.0 — Raheem + Claude Code — 2026-11-20

**Phase 5 complete — merged into main 2026-11-20 (`d7f16f0`, release 0.5.0).**

## ⏸ Paused 2026-11-20 — resume with Phase 6 planning (see CONTEXT.md "PAUSED HERE")
- [ ] Phase 6 step 0: research free LLM options (limits, data policy) → owner chooses → Phase 6 plan

## Phase 6 — AI drafts · Phase 7 — RAG · Phase 8 — Security · Phase 9 — Deployment
See `docs/ROADMAP.md`; tasks added when the phase starts.
