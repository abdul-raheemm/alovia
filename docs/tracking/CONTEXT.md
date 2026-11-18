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
- Phase 2 task order (owner, 2026-11-17): 3 dates ✓ → 5 home + month cards → 4 content provider (fetch S1/S2/S3/S6, DEC-042/043) → 6 calendar + appointments → 7 notifications + doctor notes → 8 pregnancy end → 0 Phase 1 follow-ups (doctor/admin consent, 405 code, sign-in audit) → 9 review.
- Task 4 done: `backend/content/prototype_content.yaml` (21 sample items, every content_type, every month; NHS unchanged excerpts with OGL attribution, MedlinePlus public-domain shortened by removal only, OWH values in a fixed "Typical at this stage" frame because the source's own "your baby is/weighs" phrasing is banned by spec §13.1) and `size_reference.yaml` (WHO Table 11, 50th percentile, weeks 14/16/20/24/28/32/36, transcribed 2026-11-17 from the published table image doi:10.1371/journal.pmed.1002220.t011; draft comparison objects await doctor review R2). Icons: `frontend/apps/patient-web/public/icons/fluent/` (7 SVGs + MIT LICENSE).
- OpenStax removed from the Journey spec (owner, 2026-11-18, DEC-051): D9, §7.2, §8.3 and S2 updated; the RAG spec's licence example too.
- Owner decisions 2026-11-18: placeholder month drawings stay for the prototype (DEC-050); appointment/calendar date limits 1900-2999 kept (DEC-052); the agent's interpretations from tasks 6-8 accepted (DEC-053).
- Phase 3 task 4 done: Log page (`/log`), urgent page (`/urgent`), advice screens; bundled warning signs, messages and phone numbers in `apps/patient-web/src/app/symptomBundle.generated.ts` (from `backend/scripts/export_symptom_bundle.py`; a backend test fails if it is stale — re-run the script after any rule-file change); offline urgent check-ins queued in memory (DEC-060).
- Phase 3 tasks 2-3 done: engine (pure) + service + router `/api/v1/patient/symptoms/{vocabulary,checkins,charts}`. Pregnancy week comes from `journey.service.pregnancy_week` (completed weeks; null without a usable due date). Pattern changes stored as `[{code, symptom}]` (symptom null for P5) so the Phase 5 doctor view can name the symptom (§12). Logging closed after the end → 409 (DEC-064). Open: the L1-03/L2-07 example in Symptom spec §10 and API.md §5 contradicts rule L2-07 (owner question).
- Phase 3 started 2026-11-18 (owner: all plan decisions as recommended, DEC-059..066). Task 1 done on `phase-3/rules-data`: migration 0003 (`symptom_checkins`, `symptom_logs`) applied to main; rule files in `backend/rules/symptoms/`; loader + startup checks; `Message`/`Helpline` moved to `app/common/rule_texts.py` (shared by journey and symptoms). PUQE wording is the official sheet's; the sheet's mild band starts at 4, the spec's at 3 (spec followed; flagged for A2). Next: task 2 (engine).
- Owner items (2026-11-18, branch `phase-2/owner-items`): 6 entry wording approved (DEC-054); 7 Telangana helplines in `messages.yaml` on the support screen (DEC-057); 8 PMSMA suggested check-ups on (DEC-056); 10 admins via `scripts/make_admin.py` (DEC-055); 12/13 accepted by the owner for the prototype, doctor sign-off still required before release (DEC-058); doctor review sheet `docs/review/journey_doctor_review.csv` from `scripts/export_review_sheet.py`. Item 9 (legal placeholders) later.
- Follow-up (owner, 2026-11-18): size reference now covers every week 14-40 (WHO Table 11, 50th percentile, same image; 7 more Fluent icons; objects are drafts for R2). Month drawings: womenshealth.gov stage images are ©peggerrity.com (not allowed); Servier has no monthly series — the placeholders stay; owner decision pending.
- Task 9 (agent part) done: patient audit entries (dates changed, appointment created/edited/deleted, pregnancy status changed; `users.service.add_audit`, same transaction, no clinical values — DEC-049); appointment dates and calendar ranges limited to 1900-2999 (date overflow, ERR-042); CREDITS completed; CHANGELOG 0.2.0; version 0.2.0. Phase 2 branches stay unmerged until the owner's review (owner, 2026-11-17).
- Task 0 done (Phase 1 follow-ups): doctor app consent step (`components/ConsentStep.tsx`, gate step `consent`); `METHOD_NOT_ALLOWED` (405) in `app/core/errors.py` and API.md §3; sign-in audit in `users.service.record_sign_in` (called by `GET /me`, once per token `session_id`). **Phase 5 must:** every doctor/admin data route checks the current consent in the backend (as `get_patient` does for patients) — the app gate alone is not enough.
- Task 8 done: `POST /patient/pregnancy-end` `{status: ended_birth|ended_loss|ended_not_specified, inform_doctor: true|false (required, no default)}` and `POST /patient/pregnancy-end/undo` (within `resume_window_days` of `pregnancy_ended_at`; 409 otherwise). Both reply with the home data, which now has `ended: {status, ended_at, undo_until}`. Inbox items are written through `dashboard.service.add_inbox_item` (ref = the `pregnancy_date_history` row). Patient app: More → "My pregnancy has ended" (TODO(OPEN) wording) → 3-step flow; ended home is quiet (no images), shows the §11.4/11.5 message keys (pending approval), My records links (appointments, doctor notes) and the undo button.
- Task 7 done: `GET /patient/notifications` creates due notifications (insert ... on conflict do nothing on the unique constraint) and returns unread ones; `POST /{id}/read|dismiss`; `GET /patient/doctor-notes`. Doctor notes are read through the new `app/modules/dashboard/service.py` (ARCHITECTURE §8: other modules use a module's service, not its models). Patient app: notification bar at the top of home, Doctor notes tab. Notification wording is neutral UI text in `app/journey.ts` (no message keys exist for it in spec §13.2).
- Task 6 done: `GET /patient/journey/calendar?from=&to=` (§6.4 milestones only for an active dated pregnancy; appointments always) and `/patient/appointments` (GET upcoming/past, POST 201, PUT/DELETE own patient-created only: doctor-added → 403, other patient's → 404). Appointment date/time are the patient's local time in the config timezone; the API returns `date` + `time` already local. Patient app: Calendar tab (react-day-picker 9.14.0, own day labels for WCAG 2.5.3), home week strip, Appointments tab with add/edit/delete; shared `TextAreaField`; API client `delete`. TODO(Phase 3): symptom dots, red-flag icons, day check-ins.
- Task 5 done: content provider (§8.2, `app/modules/journey/content.py`; files in `backend/content/` are EMPTY until task 4 — DEC-042/043), home blocks (`months`, `stage_items`, `size`, `next_appointment`), `GET /patient/journey/months/{month}`, bad-date guard; patient app baby card (motion float, reduced-motion safe), This stage with prototype banner, quick log, next appointment, months strip, month detail page; placeholder illustrations `frontend/apps/patient-web/public/illustrations/month_*.svg`; `motion` 14.14.0 installed (owner approval).
- Task 3 done: `PUT /patient/journey/dates` + `GET /patient/journey/home` (shapes in API.md §4.2); `get_patient` in `app/modules/users/service.py` guards every patient data route (role + linked + consent); `rules/journey/messages.yaml` holds every §13.2 key with `text: null` until a doctor approves (DEC-041); patient app has the home header/onboarding and dates screens, nav from the backend config.
- Owner notes: "add a dark and light theme option later" (the theme switch already has Light / Dark / System — clarify if something else is meant). Messages show "[Text pending doctor approval]" until approved (DEC-041).
- Open owner actions: fill legal placeholders (team, supervisor, contact email — kept as `[OPEN]` placeholders until then).
