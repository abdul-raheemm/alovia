# Changelog — Alovia

User-visible changes per release (one release per finished phase). Work-session details go in `tracking/HISTORY.md`, not here.
Format: newest first. Versions: `0.<phase>.<patch>` until the first full release.

## [0.2.0] — 2026-11-17 — Phase 2: Pregnancy Journey
### Added
- Pregnancy dates: onboarding with three options (last period, doctor's due date, ultrasound), date rules D1–D3, confirmation before an estimate replaces a doctor's or scan date, full date history.
- Journey home: weeks and days, days to go, due date with "estimate" label, baby card with a gentle floating month drawing (placeholder drawings, reduced-motion respected) and a typical-size comparison, "This stage" content, quick-log shortcut, this-week strip, next appointment, nine swipeable month cards and month detail pages.
- Prototype content with sources on every card (Office on Women's Health, NHS under the Open Government Licence, MedlinePlus) and WHO fetal-growth weights for weeks 14–40 with Fluent Emoji comparison icons; a prototype banner on every content screen. All content awaits doctor review.
- Calendar tab: month view with milestone and appointment markers, day details, navigation from pregnancy start to due date plus two weeks; dashed "suggested" PMSMA check-up days (the 9th of each month in the 2nd and 3rd trimesters, from the official NHM page).
- Appointments tab: add, edit and delete her own appointments (date, optional time, title, note); doctor-added appointments are labelled and read-only.
- Notification bar: new week, new month, appointment soon and doctor-note notices, created when the app opens, each once; tap to open, dismiss to hide.
- Doctor notes tab: notes her doctor shared, newest first, read-only.
- "My pregnancy has ended": three choices, a no-default question about informing the doctor, a quiet home with support and safety messages, official Telangana helpline numbers (tap to call), and undo within 7 days.
- A doctor review sheet for every message, content item, size object and rule (`docs/review/journey_doctor_review.csv`), and a script for the owner to create admin accounts.
- Doctor app: doctors and admins accept the app-wide consent once at first sign-in.
- Activity log entries for sign-ins and for patient changes to dates, appointments and pregnancy status (never clinical values).
- Patient-facing messages show "[Text pending doctor approval]" until a doctor approves their wording.
### Changed
- HTTP 405 responses now use the error code `METHOD_NOT_ALLOWED`.

## [0.1.0] — 2026-11-17 — Phase 1: Foundation
### Added
- Backend (FastAPI, Python 3.14): settings, JSON logs with request IDs, `{data, error}` envelope, `GET /api/v1/health` (database, models), Supabase token verification, `GET /me`, `POST /me/consent`, invite check and invite-only patient linking.
- Database: Phase 1 tables (users, consents, doctors, patients, assignments, invites, audit log, fetal and maternal results) via Alembic migration 0001, tested on a separate test project.
- Fetal and maternal risk models moved unchanged; outputs identical to the old backend for 12 approved reference cases.
- Patient web app (installable): landing page with disclaimer, invite-only sign-up with 18+ and consent, sign-in/out, navigation shell with urgent button placeholder, theme switch, legal and about pages.
- Doctor web app: sign-in/out, role check, navigation shell (admin area for admins), theme switch, legal and about pages.
- Shared design tokens (light and dark, patient and doctor), fonts self-hosted, accessible components.
- Development seed data with invite links; one command for every check (`scripts/check_all`).
- Knowledge base collection moved into `knowledge-base/`.

## [0.0.0] — 2026-11-16
### Added
- Complete documentation set (PRD, UX flows, design system, architecture, database, API, security, code style, testing, environment, error handling, observability, deployment, decisions, roadmap), module specs, legal drafts and tracking files.

<!-- Template
## [0.N.0] — YYYY-MM-DD — Phase N: <name>
### Added
- …
### Changed
- …
### Fixed
- …
### Removed
- …
-->
