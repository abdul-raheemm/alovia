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
- [~] Phase 1 review + CHANGELOG 0.1.0 — CHANGELOG written 2026-11-17; owner review open

## Phase 2 — Pregnancy Journey
- [ ] Migration (date history, appointments, notifications, doctor_notes)
- [ ] GA/month/trimester calculations + tests
- [ ] Dates onboarding + validation
- [ ] Content provider interface + prototype YAML content + size reference (sourced)
- [ ] Home screen blocks; month cards + detail; illustrations (licensed or placeholders)
- [ ] Calendar + appointments (patient side)
- [ ] Notifications bar
- [ ] Pregnancy-end flow + undo
- [ ] E2E + accessibility; review; CHANGELOG 0.2.0

## Phase 3 — Symptom Tracking
- [ ] Migration; vocabulary YAML; red-flag YAML; PUQE; pattern rules
- [ ] Engine + one test per rule; API; inbox items
- [ ] Log page, urgent button (bundled advice), result screens, charts, calendar dots, weekly summary
- [ ] E2E; review; CHANGELOG 0.3.0

## Phase 4 — Genetic Risk
- [ ] YAML rules (HBB/HEM/MAR, evidence, conflicts, messages, config)
- [ ] Engine + 45 pair tests + all other tests
- [ ] Migration + API + patient forms/results
- [ ] E2E; review; CHANGELOG 0.4.0

## Phase 5 — Doctor Dashboard + Admin
- [ ] Patient list, inbox, patient tabs
- [ ] Predictions UI: units, range file script, warnings, limitations, sharing
- [ ] Genetic review, symptoms view, records, notes, appointments, dates/status
- [ ] Rule review screen; audit log; invite links; admin screens
- [ ] E2E (access control!); review; CHANGELOG 0.5.0

## Phase 6 — AI drafts · Phase 7 — RAG · Phase 8 — Security · Phase 9 — Deployment
See `docs/ROADMAP.md`; tasks added when the phase starts.
