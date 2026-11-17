# Changelog — Alovia

User-visible changes per release (one release per finished phase). Work-session details go in `tracking/HISTORY.md`, not here.
Format: newest first. Versions: `0.<phase>.<patch>` until the first full release.

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
